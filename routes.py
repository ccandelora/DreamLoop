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
from werkzeug.security import check_password_hash

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
            return redirect(next_page if next_page else url_for('index'))
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
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)
    content = request.form.get('content')
    
    if content:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            dream_id=dream_id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!')
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(dream_id, comment_id):
    """Delete a comment."""
    comment = Comment.query.get_or_404(comment_id)
    dream = Dream.query.get_or_404(dream_id)
    
    if comment.user_id == current_user.id or dream.user_id == current_user.id:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!')
    else:
        flash('You do not have permission to delete this comment.')
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/community')
@login_required
def community_dreams():
    """View all public dreams from the community."""
    public_dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).all()
    return render_template('community_dreams.html', dreams=public_dreams)

@app.route('/groups')
@login_required
def dream_groups():
    """View all dream groups."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)

@app.route('/group/<int:group_id>')
@login_required
def dream_group(group_id):
    """View individual dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership:
        flash('You must be a member to view this group.')
        return redirect(url_for('dream_groups'))
    
    forum_posts = ForumPost.query.filter_by(group_id=group_id).order_by(ForumPost.created_at.desc()).all()
    return render_template('dream_group.html', group=group, membership=membership, forum_posts=forum_posts)

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

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View a single dream."""
    dream = Dream.query.get_or_404(dream_id)
    if not dream.is_public and dream.user_id != current_user.id:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        try:
            # Extract dream details from form
            dream = Dream(
                title=request.form.get('title'),
                content=request.form.get('content'),
                mood=request.form.get('mood'),
                tags=request.form.get('tags'),
                is_public=bool(request.form.get('is_public')),
                is_anonymous=bool(request.form.get('is_anonymous')),
                lucidity_level=int(request.form.get('lucidity_level')),
                user_id=current_user.id,
                sleep_quality=request.form.get('sleep_quality'),
                sleep_position=request.form.get('sleep_position'),
                sleep_interruptions=int(request.form.get('sleep_interruptions') or 0),
                bed_time=datetime.strptime(request.form.get('bed_time'), '%Y-%m-%dT%H:%M') if request.form.get('bed_time') else None,
                wake_time=datetime.strptime(request.form.get('wake_time'), '%Y-%m-%dT%H:%M') if request.form.get('wake_time') else None
            )
            
            # Calculate sleep duration if both times are provided
            if dream.bed_time and dream.wake_time:
                duration = (dream.wake_time - dream.bed_time).total_seconds() / 3600
                dream.sleep_duration = round(duration, 2)
            
            # Perform AI analysis if user has available analyses
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                analysis, sentiment_info = analyze_dream(dream.content, current_user.subscription_type == 'premium')
                if sentiment_info:
                    dream.sentiment_score = sentiment_info['sentiment_score']
                    dream.sentiment_magnitude = sentiment_info['sentiment_magnitude']
                    dream.dominant_emotions = sentiment_info['dominant_emotions']
                    dream.lucidity_level = sentiment_info['lucidity_level']
                dream.ai_analysis = analysis
                
                if current_user.subscription_type == 'free':
                    current_user.monthly_ai_analysis_count += 1
            
            db.session.add(dream)
            db.session.commit()
            flash('Dream logged successfully!')
            return redirect(url_for('dream_view', dream_id=dream.id))
            
        except Exception as e:
            logger.error(f"Error creating dream: {str(e)}")
            db.session.rollback()
            flash('An error occurred while logging your dream.')
            return render_template('dream_new.html')
    
    return render_template('dream_new.html')
