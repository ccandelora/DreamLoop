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

@app.route('/')
def index():
    """Landing page and user dashboard."""
    if current_user.is_authenticated:
        dreams = current_user.dreams.order_by(Dream.date.desc()).limit(5).all()
        return render_template('index.html', dreams=dreams)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
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
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
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

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """Analyze patterns across user's dreams."""
    dreams = current_user.dreams.all()
    pattern_analysis = analyze_dream_patterns(dreams, is_premium=(current_user.subscription_type == 'premium'))
    return render_template('dream_patterns.html', pattern_analysis=pattern_analysis)

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry with sentiment analysis and sleep metrics."""
    if request.method == 'POST':
        try:
            # Get basic dream details
            title = request.form.get('title')
            content = request.form.get('content')
            mood = request.form.get('mood')
            tags = request.form.get('tags')
            is_public = bool(request.form.get('is_public'))
            is_anonymous = bool(request.form.get('is_anonymous'))
            lucidity_level = int(request.form.get('lucidity_level', 1))
            
            # Get sleep metrics
            bed_time = request.form.get('bed_time')
            wake_time = request.form.get('wake_time')
            sleep_quality = int(request.form.get('sleep_quality')) if request.form.get('sleep_quality') else None
            sleep_interruptions = int(request.form.get('sleep_interruptions', 0))
            sleep_position = request.form.get('sleep_position')
            
            # Calculate sleep duration if both times are provided
            sleep_duration = None
            if bed_time and wake_time:
                try:
                    bed_time = datetime.fromisoformat(bed_time)
                    wake_time = datetime.fromisoformat(wake_time)
                    sleep_duration = (wake_time - bed_time).total_seconds() / 3600  # Convert to hours
                except ValueError:
                    bed_time = None
                    wake_time = None

            # Initialize sentiment values
            sentiment_score = None
            sentiment_magnitude = None
            dominant_emotions = None
            ai_analysis = None

            # Perform AI analysis if eligible
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                is_premium = current_user.subscription_type == 'premium'
                
                # Get AI analysis and sentiment info
                analysis, sentiment_info = analyze_dream(content, is_premium=is_premium)
                
                if analysis:
                    ai_analysis = analysis
                    
                    # Update sentiment information if available
                    if sentiment_info:
                        sentiment_score = sentiment_info.get('sentiment_score')
                        sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
                        dominant_emotions = sentiment_info.get('dominant_emotions')
                        # Only override lucidity level from form if AI provides one
                        if sentiment_info.get('lucidity_level'):
                            lucidity_level = sentiment_info['lucidity_level']
                
                if current_user.subscription_type == 'free':
                    current_user.monthly_ai_analysis_count += 1

            # Create dream object with all fields
            dream = Dream(
                title=title,
                content=content,
                mood=mood,
                tags=tags,
                is_public=is_public,
                is_anonymous=is_anonymous,
                lucidity_level=lucidity_level,
                user_id=current_user.id,
                sleep_duration=sleep_duration,
                sleep_quality=sleep_quality,
                bed_time=bed_time,
                wake_time=wake_time,
                sleep_interruptions=sleep_interruptions,
                sleep_position=sleep_position,
                sentiment_score=sentiment_score,
                sentiment_magnitude=sentiment_magnitude,
                dominant_emotions=dominant_emotions,
                ai_analysis=ai_analysis
            )

            # Save to database
            db.session.add(dream)
            db.session.commit()
            flash('Dream logged successfully!')
            return redirect(url_for('dream_view', dream_id=dream.id))

        except Exception as e:
            logger.error(f"Error creating dream: {str(e)}")
            db.session.rollback()
            flash('An error occurred while saving your dream.')
            return render_template('dream_new.html')

    return render_template('dream_new.html')

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View an individual dream."""
    dream = Dream.query.get_or_404(dream_id)
    
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/<int:dream_id>/reanalyze', methods=['POST'])
@login_required
def reanalyze_dream(dream_id):
    """Re-analyze a dream using AI."""
    dream = Dream.query.get_or_404(dream_id)
    
    if dream.user_id != current_user.id:
        flash('You can only re-analyze your own dreams.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    if current_user.subscription_type == 'free':
        if current_user.monthly_ai_analysis_count >= 3:
            flash('You have reached your monthly limit for AI analyses. Upgrade to Premium for unlimited analyses!')
            return redirect(url_for('subscription'))
        current_user.monthly_ai_analysis_count += 1
    
    try:
        analysis, sentiment_info = analyze_dream(dream.content, is_premium=(current_user.subscription_type == 'premium'))
        if analysis:
            dream.ai_analysis = analysis
            
            if sentiment_info:
                dream.sentiment_score = sentiment_info.get('sentiment_score')
                dream.sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
                dream.dominant_emotions = sentiment_info.get('dominant_emotions')
                if sentiment_info.get('lucidity_level'):
                    dream.lucidity_level = sentiment_info['lucidity_level']
        
        db.session.commit()
        flash('Dream successfully re-analyzed!')
    except Exception as e:
        logger.error(f"Error re-analyzing dream: {str(e)}")
        db.session.rollback()
        flash('An error occurred while re-analyzing your dream.')
    
    return redirect(url_for('dream_view', dream_id=dream_id))
