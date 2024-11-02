from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import logging
import os
import hashlib
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from ai_helper import analyze_dream, analyze_dream_patterns
from stripe_webhook_handler import handle_stripe_webhook
import stripe
import markdown
from sqlalchemy import desc, func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.jinja_env.filters['markdown'] = lambda text: markdown.markdown(text) if text else ''

@app.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        dreams = current_user.dreams.order_by(Dream.date.desc()).limit(5).all()
    else:
        dreams = []
    return render_template('index.html', dreams=dreams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db.session.query(User).filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db.session.query(User).filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        try:
            # Extract form data with proper type conversion and validation
            title = request.form.get('title')
            content = request.form.get('content')
            mood = request.form.get('mood')
            tags = request.form.get('tags')
            is_public = bool(request.form.get('is_public'))
            is_anonymous = bool(request.form.get('is_anonymous'))
            lucidity_level = int(request.form.get('lucidity_level', 1))
            
            # Process sleep metrics with proper error handling
            try:
                bed_time = datetime.fromisoformat(request.form.get('bed_time')) if request.form.get('bed_time') else None
                wake_time = datetime.fromisoformat(request.form.get('wake_time')) if request.form.get('wake_time') else None
                sleep_quality = int(request.form.get('sleep_quality')) if request.form.get('sleep_quality') else None
                sleep_interruptions = int(request.form.get('sleep_interruptions', 0))
                sleep_position = request.form.get('sleep_position')
                sleep_duration = float(request.form.get('sleep_duration')) if request.form.get('sleep_duration') else None
            except ValueError as e:
                logger.error(f"Error processing sleep metrics: {str(e)}")
                flash('Invalid sleep metrics provided')
                return render_template('dream_new.html')

            # Perform AI analysis based on subscription type
            ai_analysis = None
            sentiment_info = None

            if current_user.subscription_type == 'free':
                if current_user.monthly_ai_analysis_count >= 3:
                    flash('You have reached your monthly limit for AI analyses. Upgrade to Premium for unlimited analyses!')
                else:
                    current_user.monthly_ai_analysis_count += 1
                    ai_analysis, sentiment_info = analyze_dream(content, is_premium=False)
            else:
                ai_analysis, sentiment_info = analyze_dream(content, is_premium=True)

            # Create dream with all fields
            dream = Dream(
                user_id=current_user.id,
                title=title,
                content=content,
                mood=mood,
                tags=tags,
                is_public=is_public,
                is_anonymous=is_anonymous,
                lucidity_level=lucidity_level,
                bed_time=bed_time,
                wake_time=wake_time,
                sleep_quality=sleep_quality,
                sleep_interruptions=sleep_interruptions,
                sleep_position=sleep_position,
                sleep_duration=sleep_duration,
                ai_analysis=ai_analysis
            )

            # Update sentiment analysis fields if available
            if sentiment_info:
                dream.sentiment_score = sentiment_info.get('sentiment_score')
                dream.sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
                dream.dominant_emotions = sentiment_info.get('dominant_emotions')
                if sentiment_info.get('lucidity_level'):
                    dream.lucidity_level = sentiment_info['lucidity_level']

            db.session.add(dream)
            db.session.commit()
            
            if ai_analysis:
                flash('Dream logged successfully with AI analysis!')
            else:
                flash('Dream logged successfully!')
                
            return redirect(url_for('dream_view', dream_id=dream.id))

        except Exception as e:
            logger.error(f"Error creating dream: {str(e)}")
            db.session.rollback()
            flash('An error occurred while saving your dream')
            return render_template('dream_new.html')

    return render_template('dream_new.html')

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View an individual dream."""
    dream = db.session.get(Dream, dream_id)
    if not dream:
        flash('Dream not found.')
        return redirect(url_for('index'))
    
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/<int:dream_id>/reanalyze', methods=['POST'])
@login_required
def reanalyze_dream(dream_id):
    """Re-analyze a dream using AI."""
    dream = db.session.get(Dream, dream_id)
    if not dream or dream.user_id != current_user.id:
        flash('Dream not found or unauthorized.')
        return redirect(url_for('index'))
        
    if current_user.subscription_type == 'free' and current_user.monthly_ai_analysis_count >= 3:
        flash('You have reached your monthly limit for AI analyses. Upgrade to Premium for unlimited analyses!')
        return redirect(url_for('dream_view', dream_id=dream_id))
        
    try:
        analysis, sentiment_info = analyze_dream(dream.content, is_premium=(current_user.subscription_type == 'premium'))
        if analysis and sentiment_info:
            dream.ai_analysis = analysis
            dream.sentiment_score = sentiment_info.get('sentiment_score')
            dream.sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
            dream.dominant_emotions = sentiment_info.get('dominant_emotions')
            if sentiment_info.get('lucidity_level'):
                dream.lucidity_level = sentiment_info['lucidity_level']
                
            if current_user.subscription_type == 'free':
                current_user.monthly_ai_analysis_count += 1
                
            db.session.commit()
            flash('Dream successfully re-analyzed!')
        else:
            flash('Error during dream analysis. Please try again.')
    except Exception as e:
        logger.error(f"Error re-analyzing dream: {str(e)}")
        db.session.rollback()
        flash('An error occurred during reanalysis.')
        
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)

    if not dream.is_public and dream.user_id != current_user.id:
        flash('You cannot comment on this dream.')
        return redirect(url_for('index'))

    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))

    try:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            dream_id=dream_id,
            created_at=datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!')
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your comment.')

    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(dream_id, comment_id):
    """Delete a comment."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        dream = Dream.query.get_or_404(dream_id)

        if comment.user_id != current_user.id and dream.user_id != current_user.id:
            flash('You do not have permission to delete this comment.')
            return redirect(url_for('dream_view', dream_id=dream_id))

        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!')

    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the comment.')

    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/subscription')
@login_required
def subscription():
    """Subscription management page."""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template('subscription.html', stripe_publishable_key=stripe_publishable_key)
