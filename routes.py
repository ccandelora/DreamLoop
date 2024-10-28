import os
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from ai_helper import analyze_dream, analyze_dream_patterns
from google_ads_helper import track_premium_conversion, show_premium_ads, validate_google_ads_credentials
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Constants
GROUP_THEMES = [
    "Lucid Dreams", "Nightmares", "Flying Dreams", "Adventure",
    "Spiritual", "Recurring Dreams", "Prophetic Dreams", "Nature Dreams"
]

@app.route('/')
def index():
    """Handle the main landing page."""
    return redirect(url_for('dream_log'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
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
            
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dream/new', methods=['GET', 'POST'])
@app.route('/dream/log', methods=['GET', 'POST'])
@login_required
def dream_log():
    """Handle dream logging form display and submission."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = bool(request.form.get('is_public'))
        
        if not title or not content:
            flash('Title and content are required!')
            return render_template('dream_log.html')
        
        dream = Dream()
        dream.user_id = current_user.id
        dream.title = title
        dream.content = content
        dream.mood = mood
        dream.tags = tags
        dream.is_public = is_public
        dream.date = datetime.utcnow()
        
        # If user can use AI analysis, analyze the dream
        if current_user.can_use_ai_analysis():
            try:
                dream.ai_analysis = analyze_dream(content)
                current_user.increment_ai_analysis_count()
            except Exception as e:
                logger.error(f"Error analyzing dream: {str(e)}")
                flash('Could not analyze dream at this time.')
        else:
            flash('You have reached your monthly limit for AI analysis. Upgrade to premium for unlimited analysis!')
        
        db.session.add(dream)
        db.session.commit()
        
        flash('Dream logged successfully!')
        return redirect(url_for('dream_view', dream_id=dream.id))
        
    return render_template('dream_log.html')

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View a specific dream."""
    dream = Dream.query.get_or_404(dream_id)
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    dream = Dream.query.get_or_404(dream_id)
    if not dream.is_public:
        flash('Cannot comment on private dreams.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    comment = Comment()
    comment.dream_id = dream_id
    comment.author_id = current_user.id
    comment.content = content
    comment.date = datetime.utcnow()
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added successfully!')
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/patterns')
@login_required
def dream_patterns():
    """View patterns across all dreams."""
    dreams = current_user.dreams.all()
    if not dreams:
        flash('Log some dreams first to see patterns!')
        return redirect(url_for('dream_log'))
        
    patterns = analyze_dream_patterns(dreams)
    return render_template('dream_patterns.html', dreams=dreams, patterns=patterns)

@app.route('/community')
@login_required
def community():
    """View public dreams from the community."""
    dreams = Dream.query.filter_by(is_public=True).order_by(Dream.date.desc()).all()
    return render_template('community.html', dreams=dreams)

@app.route('/groups')
@login_required
def dream_groups():
    theme = request.args.get('theme')
    if theme:
        groups = DreamGroup.query.filter_by(theme=theme).all()
    else:
        groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups, theme=theme, themes=GROUP_THEMES)

@app.route('/groups/create', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new dream group."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        theme = request.form.get('theme')
        
        if not name or not theme:
            flash('Name and theme are required!')
            return render_template('create_group.html', themes=GROUP_THEMES)
        
        group = DreamGroup()
        group.name = name
        group.description = description
        group.theme = theme
        
        db.session.add(group)
        db.session.flush()
        
        # Make creator an admin member
        membership = GroupMembership()
        membership.user_id = current_user.id
        membership.group_id = group.id
        membership.is_admin = True
        
        db.session.add(membership)
        db.session.commit()
        
        flash('Group created successfully!')
        return redirect(url_for('group_detail', group_id=group.id))
    
    return render_template('create_group.html', themes=GROUP_THEMES)

@app.route('/groups/<int:group_id>')
@login_required
def group_detail(group_id):
    """View a specific group."""
    group = DreamGroup.query.get_or_404(group_id)
    is_member = current_user in [m.user for m in group.members]
    is_admin = any(m.is_admin for m in group.members if m.user_id == current_user.id)
    user_dreams = current_user.dreams.all() if is_member else []
    
    return render_template('group_detail.html', group=group, is_member=is_member,
                         is_admin=is_admin, user_dreams=user_dreams)

@app.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    if not any(m.is_admin for m in group.members if m.user_id == current_user.id):
        flash('Only group admins can edit the group.')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description')
        group.theme = request.form.get('theme')
        db.session.commit()
        flash('Group updated successfully!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    return render_template('edit_group.html', group=group, themes=GROUP_THEMES)

@app.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    if current_user in [m.user for m in group.members]:
        flash('You are already a member of this group!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    membership = GroupMembership()
    membership.user_id = current_user.id
    membership.group_id = group_id
    
    db.session.add(membership)
    db.session.commit()
    flash('Successfully joined the group!')
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/forum/post/<int:post_id>')
@login_required
def forum_post(post_id):
    """View a specific forum post."""
    post = ForumPost.query.get_or_404(post_id)
    is_member = current_user in [m.user for m in post.dream_group.members]
    return render_template('forum_post.html', post=post, is_member=is_member)

@app.route('/forum/post/create/<int:group_id>', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    """Create a new forum post."""
    group = DreamGroup.query.get_or_404(group_id)
    if current_user not in [m.user for m in group.members]:
        flash('Only group members can create posts!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if request.method == 'POST':
        post = ForumPost()
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.author_id = current_user.id
        post.group_id = group_id
        
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!')
        return redirect(url_for('forum_post', post_id=post.id))
    
    return render_template('create_forum_post.html', group=group)

@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def add_forum_reply(post_id):
    """Add a reply to a forum post."""
    post = ForumPost.query.get_or_404(post_id)
    if current_user not in [m.user for m in post.dream_group.members]:
        flash('Only group members can reply to posts!')
        return redirect(url_for('forum_post', post_id=post_id))
    
    content = request.form.get('content')
    if not content:
        flash('Reply content cannot be empty!')
        return redirect(url_for('forum_post', post_id=post_id))
    
    reply = ForumReply()
    reply.content = content
    reply.author_id = current_user.id
    reply.post_id = post_id
    
    db.session.add(reply)
    db.session.commit()
    flash('Reply added successfully!')
    return redirect(url_for('forum_post', post_id=post_id))

@app.route('/dream/<int:dream_id>/share/<int:group_id>', methods=['POST'])
@login_required
def share_dream(dream_id, group_id):
    """Share a dream with a group."""
    dream = Dream.query.get_or_404(dream_id)
    group = DreamGroup.query.get_or_404(group_id)
    
    if dream.user_id != current_user.id:
        flash('You can only share your own dreams!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if current_user not in [m.user for m in group.members]:
        flash('You must be a group member to share dreams!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    if dream.dream_group_id:
        flash('This dream has already been shared with a group!')
        return redirect(url_for('group_detail', group_id=group_id))
    
    dream.dream_group_id = group_id
    db.session.commit()
    flash('Dream shared successfully with the group!')
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    try:
        if current_user.subscription_type == 'premium':
            flash('You are already a premium member!')
            return redirect(url_for('subscription'))
        
        # Update user subscription
        current_user.subscription_type = 'premium'
        current_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
        
        # Track the conversion in Google Ads
        if validate_google_ads_credentials():
            if track_premium_conversion(current_user.id):
                logger.info(f"Successfully tracked premium conversion for user {current_user.id}")
            else:
                logger.warning(f"Failed to track premium conversion for user {current_user.id}")
        else:
            logger.info("Skipping conversion tracking due to missing credentials")
        
        flash('Successfully upgraded to premium! Enjoy unlimited AI analysis.')
        return redirect(url_for('subscription'))
        
    except Exception as e:
        logger.error(f"Error during subscription upgrade: {str(e)}")
        db.session.rollback()
        flash('An error occurred during the upgrade. Please try again or contact support.')
        return redirect(url_for('subscription'))

@app.route('/subscription')
@login_required
def subscription():
    return render_template('subscription.html')

@app.context_processor
def inject_ad_context():
    def should_show_premium_ads():
        return show_premium_ads(current_user) if current_user.is_authenticated else False
    
    return {
        'should_show_premium_ads': should_show_premium_ads,
        'validate_google_ads_credentials': validate_google_ads_credentials,
        'google_ads_client_id': os.environ.get('GOOGLE_ADS_CLIENT_ID', '')
    }
