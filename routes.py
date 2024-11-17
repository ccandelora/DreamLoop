import os
from flask import render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply, Notification
from datetime import datetime
import logging
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
        dreams = Dream.query.filter_by(user_id=current_user.id).order_by(Dream.date.desc()).all()
    else:
        dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).limit(5).all()
    return render_template('index.html', dreams=dreams)

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        dream = Dream()
        dream.user_id = current_user.id
        dream.title = request.form.get('title')
        dream.content = request.form.get('content')
        dream.mood = request.form.get('mood')
        dream.tags = request.form.get('tags')
        dream.is_public = bool(request.form.get('is_public'))
        dream.is_anonymous = bool(request.form.get('is_anonymous'))
        dream.lucidity_level = int(request.form.get('lucidity_level', 1))
        
        # Handle sleep metrics
        dream.bed_time = datetime.strptime(request.form.get('bed_time'), '%Y-%m-%dT%H:%M') if request.form.get('bed_time') else None
        dream.wake_time = datetime.strptime(request.form.get('wake_time'), '%Y-%m-%dT%H:%M') if request.form.get('wake_time') else None
        dream.sleep_quality = int(request.form.get('sleep_quality')) if request.form.get('sleep_quality') else None
        dream.sleep_interruptions = int(request.form.get('sleep_interruptions', 0))
        dream.sleep_position = request.form.get('sleep_position')
        
        if dream.bed_time and dream.wake_time:
            dream.sleep_duration = (dream.wake_time - dream.bed_time).total_seconds() / 3600
        
        try:
            db.session.add(dream)
            db.session.commit()
            flash('Dream logged successfully!')
            return redirect(url_for('dream_view', dream_id=dream.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating dream: {str(e)}")
            flash('An error occurred while saving your dream')
            
    return render_template('dream_new.html')

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
            
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful!')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration')
            
    return render_template('register.html')

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

@app.route('/notifications')
@login_required
def notifications():
    """View all notifications."""
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/notification/<int:notification_id>/read')
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id == current_user.id:
        notification.read = True
        db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/notifications/read-all')
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    current_user.notifications.update({Notification.read: True})
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """View dream patterns and analysis."""
    user_dreams = Dream.query.filter_by(user_id=current_user.id).order_by(Dream.date.desc()).all()
    patterns = analyze_dream_patterns(user_dreams)
    return render_template('dream_patterns.html', patterns=patterns)

@app.route('/comment/<int:comment_id>/moderate', methods=['POST'])
@login_required
def moderate_comment(comment_id):
    """Moderate a comment (hide/unhide)."""
    if not current_user.can_moderate():
        flash('Unauthorized access.')
        return redirect(url_for('index'))
    
    comment = Comment.query.get_or_404(comment_id)
    
    try:
        action = request.form.get('action')
        
        if action == 'hide':
            reason = request.form.get('reason')
            if not reason:
                flash('Moderation reason is required.')
                return redirect(url_for('dream_view', dream_id=comment.dream_id))
                
            comment.hide(current_user, reason)
            flash('Comment hidden successfully.')
            
        elif action == 'unhide':
            comment.unhide(current_user)
            flash('Comment restored successfully.')
            
        else:
            flash('Invalid moderation action.')
            return redirect(url_for('dream_view', dream_id=comment.dream_id))
            
        db.session.commit()
        
    except ValueError as e:
        logger.error(f"Moderation error: {str(e)}")
        flash(str(e))
    except Exception as e:
        logger.error(f"Error moderating comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while moderating the comment.')
    
    return redirect(url_for('dream_view', dream_id=comment.dream_id))

@app.route('/admin/toggle_moderator/<int:user_id>', methods=['POST'])
@login_required
def toggle_moderator(user_id):
    """Toggle moderator status for a user."""
    if not current_user.can_moderate():
        flash('You do not have permission to manage moderators.')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    
    try:
        user.is_moderator = not user.is_moderator
        db.session.commit()
        flash(f'Moderator status {"granted to" if user.is_moderator else "removed from"} {user.username}.')
    except Exception as e:
        logger.error(f"Error toggling moderator status: {str(e)}")
        db.session.rollback()
        flash('An error occurred while updating moderator status.')
        
    return redirect(url_for('index'))

@app.route('/community')
@login_required
def community_dreams():
    """View all public dreams from the community."""
    public_dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).all()
    return render_template('community_dreams.html', dreams=public_dreams)

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View a specific dream."""
    dream = Dream.query.get_or_404(dream_id)
    
    # Only allow viewing if dream is public or user is the author
    if not dream.is_public and dream.user_id != current_user.id:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
        
    # Get all comments for this dream
    comments = Comment.query.filter_by(dream_id=dream_id, parent_id=None).all()
    threaded_comments = []
    
    for comment in comments:
        thread = {
            'comment': comment,
            'replies': comment.replies.all() if comment.replies else []
        }
        threaded_comments.append(thread)
        
    return render_template('dream_view.html', dream=dream, threaded_comments=threaded_comments)

@app.route('/dream/groups')
@login_required
def dream_groups():
    """View all dream groups."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)

# Add template context processor for moderation UI
@app.context_processor
def inject_moderation_utils():
    """Inject moderation utilities into all templates."""
    def can_moderate():
        return current_user.is_authenticated and current_user.can_moderate()
    return {'can_moderate': can_moderate}

# Add template context processor for dream author
@app.context_processor
def inject_dream_utils():
    """Inject dream utilities into all templates."""
    def is_dream_author(dream):
        return current_user.is_authenticated and dream.user_id == current_user.id
    return {'is_dream_author': is_dream_author}

# Add template context processor for unread notifications count
@app.context_processor
def inject_unread_notifications_count():
    """Inject unread notifications count into all templates."""
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
