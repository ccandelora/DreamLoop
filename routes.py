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

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        # Extract dream details from form
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = bool(request.form.get('is_public'))
        is_anonymous = bool(request.form.get('is_anonymous'))
        lucidity_level = int(request.form.get('lucidity_level', 1))
        
        # Extract sleep metrics
        bed_time = request.form.get('bed_time')
        wake_time = request.form.get('wake_time')
        sleep_quality = request.form.get('sleep_quality')
        sleep_interruptions = request.form.get('sleep_interruptions', 0)
        sleep_position = request.form.get('sleep_position')
        sleep_duration = request.form.get('sleep_duration')

        # Create new dream with all fields
        dream = Dream(
            user_id=current_user.id,
            title=title,
            content=content,
            mood=mood,
            tags=tags,
            is_public=is_public,
            is_anonymous=is_anonymous,
            lucidity_level=lucidity_level,
            bed_time=datetime.fromisoformat(bed_time) if bed_time else None,
            wake_time=datetime.fromisoformat(wake_time) if wake_time else None,
            sleep_quality=int(sleep_quality) if sleep_quality else None,
            sleep_interruptions=int(sleep_interruptions),
            sleep_position=sleep_position,
            sleep_duration=float(sleep_duration) if sleep_duration else None
        )

        try:
            # Analyze dream content if user has available analyses
            if current_user.subscription_type == 'free':
                if current_user.monthly_ai_analysis_count >= 3:
                    flash('You have reached your monthly limit for AI analyses. Upgrade to Premium for unlimited analyses!')
                else:
                    current_user.monthly_ai_analysis_count += 1
                    analysis, sentiment_info = analyze_dream(content, is_premium=False)
            else:
                analysis, sentiment_info = analyze_dream(content, is_premium=True)

            if analysis and sentiment_info:
                dream.ai_analysis = analysis
                dream.sentiment_score = sentiment_info.get('sentiment_score')
                dream.sentiment_magnitude = sentiment_info.get('sentiment_magnitude')
                dream.dominant_emotions = sentiment_info.get('dominant_emotions')
                if sentiment_info.get('lucidity_level'):
                    dream.lucidity_level = sentiment_info['lucidity_level']

            db.session.add(dream)
            db.session.commit()
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
    if not dream:
        flash('Dream not found.')
        return redirect(url_for('index'))
    
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
