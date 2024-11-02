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
            return redirect(url_for('index'))
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

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry with sentiment analysis."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = bool(request.form.get('is_public'))
        is_anonymous = bool(request.form.get('is_anonymous'))
        lucidity_level = int(request.form.get('lucidity_level', 1))

        dream = Dream(
            title=title,
            content=content,
            mood=mood,
            tags=tags,
            is_public=is_public,
            is_anonymous=is_anonymous,
            lucidity_level=lucidity_level,
            user_id=current_user.id
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

@app.route('/dream/<int:dream_id>', methods=['GET'])
@login_required
def dream_view(dream_id):
    """View an individual dream."""
    dream = Dream.query.get_or_404(dream_id)
    
    # Check if user has access to this dream
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """View dream patterns and analysis."""
    dreams = current_user.dreams.order_by(Dream.date.desc()).all()
    patterns = analyze_dream_patterns(dreams, is_premium=(current_user.subscription_type == 'premium'))
    return render_template('dream_patterns.html', patterns=patterns)

@app.route('/dream/<int:dream_id>/reanalyze', methods=['POST'])
@login_required
def reanalyze_dream(dream_id):
    """Re-analyze a dream using AI."""
    dream = Dream.query.get_or_404(dream_id)
    
    # Check if user owns the dream
    if dream.user_id != current_user.id:
        flash('You can only re-analyze your own dreams.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    # Check if free user has remaining analyses
    if current_user.subscription_type == 'free':
        if current_user.monthly_ai_analysis_count >= 3:
            flash('You have reached your monthly limit for AI analyses. Upgrade to Premium for unlimited analyses!')
            return redirect(url_for('subscription'))
        current_user.monthly_ai_analysis_count += 1
    
    try:
        # Get fresh AI analysis
        analysis, sentiment_info = analyze_dream(dream.content, is_premium=(current_user.subscription_type == 'premium'))
        dream.ai_analysis = analysis
        
        # Update sentiment information
        if sentiment_info:
            dream.sentiment_score = sentiment_info['sentiment_score']
            dream.sentiment_magnitude = sentiment_info['sentiment_magnitude']
            dream.dominant_emotions = sentiment_info['dominant_emotions']
            dream.lucidity_level = sentiment_info['lucidity_level']
        
        db.session.commit()
        flash('Dream successfully re-analyzed!')
    except Exception as e:
        logger.error(f"Error re-analyzing dream: {str(e)}")
        db.session.rollback()
        flash('An error occurred while re-analyzing your dream.')
    
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    try:
        comment = Comment(content=content, user_id=current_user.id, dream_id=dream_id)
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
    comment = Comment.query.get_or_404(comment_id)
    dream = Dream.query.get_or_404(dream_id)
    
    # Check if user has permission to delete the comment
    if comment.user_id != current_user.id and dream.user_id != current_user.id:
        flash('You do not have permission to delete this comment.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!')
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the comment.')
    
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/community')
@login_required
def community_dreams():
    """View shared dreams."""
    sort = request.args.get('sort', 'recent')
    mood = request.args.get('mood')
    
    query = Dream.query.filter_by(is_public=True)
    
    if mood:
        query = query.filter_by(mood=mood)
    
    if sort == 'popular':
        query = query.join(Comment).group_by(Dream.id).order_by(func.count(Comment.id).desc())
    elif sort == 'commented':
        query = query.join(Comment).group_by(Dream.id).order_by(Comment.created_at.desc())
    else:  # recent
        query = query.order_by(Dream.date.desc())
    
    dreams = query.all()
    return render_template('community_dreams.html', dreams=dreams)

@app.route('/subscription')
@login_required
def subscription():
    """Manage premium subscription."""
    stripe_publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
    return render_template('subscription.html', stripe_publishable_key=stripe_publishable_key)

# Group-related routes
@app.route('/groups')
@login_required
def dream_groups():
    """View all dream groups."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)

@app.route('/group/new', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new dream group."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        try:
            group = DreamGroup(name=name, description=description, created_by=current_user.id)
            membership = GroupMembership(user_id=current_user.id, is_admin=True)
            group.members.append(current_user)
            
            db.session.add(group)
            db.session.commit()
            flash('Group created successfully!')
            return redirect(url_for('dream_group', group_id=group.id))
        except Exception as e:
            logger.error(f"Error creating group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating the group.')
    
    return render_template('create_group.html')

@app.route('/group/<int:group_id>')
@login_required
def dream_group(group_id):
    """View a specific dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership:
        flash('You are not a member of this group.')
        return redirect(url_for('dream_groups'))
    
    forum_posts = ForumPost.query.filter_by(group_id=group_id).order_by(ForumPost.created_at.desc()).all()
    return render_template('dream_group.html', group=group, membership=membership, forum_posts=forum_posts)

@app.route('/group/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    
    if current_user in group.members:
        flash('You are already a member of this group.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    try:
        membership = GroupMembership(user_id=current_user.id, group_id=group_id)
        db.session.add(membership)
        db.session.commit()
        flash('Successfully joined the group!')
    except Exception as e:
        logger.error(f"Error joining group: {str(e)}")
        db.session.rollback()
        flash('An error occurred while joining the group.')
    
    return redirect(url_for('dream_group', group_id=group_id))

@app.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership:
        flash('You are not a member of this group.')
        return redirect(url_for('dream_groups'))
    
    if membership.is_admin and group.members.count() > 1:
        flash('Please transfer admin rights before leaving the group.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    try:
        db.session.delete(membership)
        if group.members.count() == 1:  # Last member leaving
            db.session.delete(group)
        db.session.commit()
        flash('Successfully left the group!')
    except Exception as e:
        logger.error(f"Error leaving group: {str(e)}")
        db.session.rollback()
        flash('An error occurred while leaving the group.')
    
    return redirect(url_for('dream_groups'))

@app.route('/group/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership or not membership.is_admin:
        flash('You do not have permission to edit this group.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    if request.method == 'POST':
        try:
            group.name = request.form.get('name')
            group.description = request.form.get('description')
            db.session.commit()
            flash('Group updated successfully!')
            return redirect(url_for('dream_group', group_id=group_id))
        except Exception as e:
            logger.error(f"Error updating group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the group.')
    
    return render_template('edit_group.html', group=group)

@app.route('/group/<int:group_id>/forum/new', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    """Create a new forum post in a group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    
    if not membership:
        flash('You must be a member to create posts.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    if request.method == 'POST':
        try:
            post = ForumPost(
                title=request.form.get('title'),
                content=request.form.get('content'),
                author_id=current_user.id,
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

@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_to_post(post_id):
    """Reply to a forum post."""
    post = ForumPost.query.get_or_404(post_id)
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=post.group_id).first()
    
    if not membership:
        flash('You must be a member to reply to posts.')
        return redirect(url_for('dream_group', group_id=post.group_id))
    
    try:
        reply = ForumReply(
            content=request.form.get('content'),
            author_id=current_user.id,
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
