from flask import render_template, redirect, url_for, flash, request, jsonify
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

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/')
def index():
    """Landing page and user dashboard."""
    return render_template('index.html')

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

@app.route('/subscription')
@login_required
def subscription():
    """View and manage subscription."""
    return render_template('subscription.html', 
                         stripe_public_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
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

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
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
        
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags', '').strip()
        is_public = bool(request.form.get('is_public'))
        is_anonymous = bool(request.form.get('is_anonymous'))
        lucidity_level = int(request.form.get('lucidity_level', 1))
        
        bed_time = request.form.get('bed_time')
        wake_time = request.form.get('wake_time')
        sleep_quality = int(request.form.get('sleep_quality')) if request.form.get('sleep_quality') else None
        sleep_interruptions = int(request.form.get('sleep_interruptions', 0))
        sleep_position = request.form.get('sleep_position')
        
        sleep_duration = None
        if bed_time and wake_time:
            try:
                bed_time = datetime.fromisoformat(bed_time)
                wake_time = datetime.fromisoformat(wake_time)
                sleep_duration = (wake_time - bed_time).total_seconds() / 3600
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
        
        db.session.add(dream)
        db.session.commit()
        
        # Get AI analysis if user has available analyses
        if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
            is_premium = current_user.subscription_type == 'premium'
            
            analysis, sentiment_info = analyze_dream(content, is_premium=is_premium)
            dream.ai_analysis = analysis
            
            if sentiment_info:
                dream.sentiment_score = sentiment_info['sentiment_score']
                dream.sentiment_magnitude = sentiment_info['sentiment_magnitude']
                dream.dominant_emotions = sentiment_info['dominant_emotions']
                dream.lucidity_level = sentiment_info['lucidity_level']
            
            if current_user.subscription_type == 'free':
                current_user.monthly_ai_analysis_count += 1
                
            db.session.commit()
            
        return redirect(url_for('dream_view', dream_id=dream.id))
    return render_template('dream_new.html')

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View a specific dream."""
    dream = Dream.query.get_or_404(dream_id)
    if not dream.is_public and dream.user_id != current_user.id:
        flash('You do not have permission to view this dream')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, user_id=current_user.id, dream_id=dream_id)
        db.session.add(comment)
        db.session.commit()
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
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/reanalyze', methods=['POST'])
@login_required
def reanalyze_dream(dream_id):
    """Re-analyze a dream using AI."""
    dream = Dream.query.get_or_404(dream_id)
    if dream.user_id != current_user.id:
        flash('You do not have permission to reanalyze this dream')
        return redirect(url_for('dream_view', dream_id=dream_id))
        
    if current_user.subscription_type == 'free' and current_user.monthly_ai_analysis_count >= 3:
        flash('You have reached your monthly AI analysis limit')
        return redirect(url_for('dream_view', dream_id=dream_id))
        
    is_premium = current_user.subscription_type == 'premium'
    analysis, sentiment_info = analyze_dream(dream.content, is_premium=is_premium)
    
    dream.ai_analysis = analysis
    if sentiment_info:
        dream.sentiment_score = sentiment_info['sentiment_score']
        dream.sentiment_magnitude = sentiment_info['sentiment_magnitude']
        dream.dominant_emotions = sentiment_info['dominant_emotions']
        dream.lucidity_level = sentiment_info['lucidity_level']
        
    if current_user.subscription_type == 'free':
        current_user.monthly_ai_analysis_count += 1
        
    db.session.commit()
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/group/new', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new dream group."""
    # Check if user can create more groups
    if current_user.subscription_type != 'premium' and len(current_user.groups) >= 2:
        flash('Free users can only create up to 2 groups. Upgrade to premium for unlimited groups.')
        return redirect(url_for('dream_groups'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        group = DreamGroup(
            name=name,
            description=description,
            created_by=current_user.id
        )
        db.session.add(group)
        db.session.commit()
        
        # Add creator as member and admin
        membership = GroupMembership(user_id=current_user.id, group_id=group.id, is_admin=True)
        db.session.add(membership)
        db.session.commit()
        
        return redirect(url_for('dream_group', group_id=group.id))
    return render_template('create_group.html')

@app.route('/group/<int:group_id>')
@login_required
def dream_group(group_id):
    """View a specific dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You must be a member to view this group')
        return redirect(url_for('dream_groups'))
    forum_posts = ForumPost.query.filter_by(group_id=group_id).order_by(ForumPost.created_at.desc()).all()
    return render_template('dream_group.html',
                         group=group,
                         membership=membership,
                         forum_posts=forum_posts)

@app.route('/group/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        membership = GroupMembership(user_id=current_user.id, group_id=group_id)
        db.session.add(membership)
        db.session.commit()
    return redirect(url_for('dream_group', group_id=group_id))

@app.route('/group/<int:group_id>/forum/new', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    """Create a new forum post."""
    group = DreamGroup.query.get_or_404(group_id)
    if current_user not in group.members:
        flash('You must be a member to create posts')
        return redirect(url_for('dream_groups'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        post = ForumPost(
            title=title,
            content=content,
            user_id=current_user.id,
            group_id=group_id
        )
        db.session.add(post)
        db.session.commit()
        
        return redirect(url_for('dream_group', group_id=group_id))
    return render_template('create_forum_post.html', group=group)

@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_to_post(post_id):
    """Add a reply to a forum post."""
    post = ForumPost.query.get_or_404(post_id)
    
    if current_user not in post.group.members:
        flash('You must be a member to reply')
        return redirect(url_for('dream_groups'))
        
    content = request.form.get('content')
    if content:
        reply = ForumReply(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(reply)
        db.session.commit()
    
    return redirect(url_for('dream_group', group_id=post.group_id))
