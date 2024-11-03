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
    return render_template('index.html', Dream=Dream)

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

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

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

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """View dream patterns and analysis."""
    dreams = current_user.dreams.order_by(Dream.date.desc()).all()
    patterns = analyze_dream_patterns(dreams, is_premium=(current_user.subscription_type == 'premium'))
    return render_template('dream_patterns.html', patterns=patterns)

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry with sentiment analysis and sleep metrics."""
    if request.method == 'POST':
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
            sleep_position=sleep_position
        )

        try:
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                is_premium = current_user.subscription_type == 'premium'
                
                # Get AI analysis and sentiment info
                analysis, sentiment_info = analyze_dream(content, is_premium=is_premium)
                dream.ai_analysis = analysis
                
                # Update sentiment information
                if sentiment_info:
                    dream.sentiment_score = sentiment_info['sentiment_score']
                    dream.sentiment_magnitude = sentiment_info['sentiment_magnitude']
                    dream.dominant_emotions = sentiment_info['dominant_emotions']
                    dream.lucidity_level = sentiment_info['lucidity_level']
                
                if current_user.subscription_type == 'free':
                    current_user.monthly_ai_analysis_count += 1

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

@app.route('/group/<int:group_id>/forum/new', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    """Create a new forum post in a group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership:
        flash('You must be a member to create posts.')
        return redirect(url_for('dream_groups'))
    
    if request.method == 'POST':
        try:
            post = ForumPost(
                title=request.form.get('title'),
                content=request.form.get('content'),
                user_id=current_user.id,
                group_id=group_id
            )
            
            db.session.add(post)
            db.session.commit()
            flash('Post created successfully!')
            return redirect(url_for('dream_group', group_id=group_id))
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating the post.')
            return render_template('create_forum_post.html', group=group)
    
    return render_template('create_forum_post.html', group=group)

@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_to_post(post_id):
    """Reply to a forum post."""
    post = ForumPost.query.get_or_404(post_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=post.group_id).first()
    
    if not membership:
        flash('You must be a member to reply to posts.')
        return redirect(url_for('dream_groups'))
    
    content = request.form.get('content')
    if not content:
        flash('Reply cannot be empty.')
        return redirect(url_for('dream_group', group_id=post.group_id))
    
    try:
        reply = ForumReply(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(reply)
        db.session.commit()
        flash('Reply added successfully!')
    except Exception as e:
        logger.error(f"Error adding reply: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your reply.')
    
    return redirect(url_for('dream_group', group_id=post.group_id))
