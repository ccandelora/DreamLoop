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
    return render_template('index.html')

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
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

        user = User(username=username,
                    email=email,
                    subscription_type='free',
                    monthly_ai_analysis_count=0,
                    last_analysis_reset=datetime.utcnow())
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    return redirect(url_for('index'))

@app.route('/dream/<int:dream_id>')
@login_required
def dream_view(dream_id):
    """View individual dream."""
    dream = Dream.query.get_or_404(dream_id)
    if dream.user_id != current_user.id and not dream.is_public:
        flash('You do not have permission to view this dream.')
        return redirect(url_for('index'))
    return render_template('dream_view.html', dream=dream)

@app.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream entry."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        mood = request.form.get('mood')
        tags = request.form.get('tags')
        is_public = bool(request.form.get('is_public'))
        is_anonymous = bool(request.form.get('is_anonymous'))

        dream = Dream(title=title,
                      content=content,
                      mood=mood,
                      tags=tags,
                      is_public=is_public,
                      is_anonymous=is_anonymous,
                      user_id=current_user.id)

        try:
            if current_user.subscription_type == 'premium' or current_user.monthly_ai_analysis_count < 3:
                is_premium = current_user.subscription_type == 'premium'
                dream.ai_analysis = analyze_dream(content,
                                                  is_premium=is_premium)
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

@app.route('/dream_patterns')
@login_required
def dream_patterns():
    """View dream patterns with enhanced analysis for premium users."""
    dreams = current_user.dreams.all()
    is_premium = current_user.subscription_type == 'premium'
    patterns = analyze_dream_patterns(dreams, is_premium=is_premium) if dreams else None
    return render_template('dream_patterns.html', patterns=patterns)

@app.route('/subscription')
@login_required
def subscription():
    """Subscription management page."""
    stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    return render_template('subscription.html',
                           stripe_publishable_key=stripe_publishable_key)

@app.route('/community_dreams')
@login_required
def community_dreams():
    """View community dreams with sorting and filtering."""
    sort = request.args.get('sort', 'recent')
    mood = request.args.get('mood', '')

    query = Dream.query.filter_by(is_public=True)

    if mood:
        query = query.filter_by(mood=mood)

    if sort == 'recent':
        query = query.order_by(Dream.date.desc())
    elif sort == 'popular':
        query = query.outerjoin(Comment).group_by(Dream.id).order_by(
            desc(func.count(Comment.id)))
    elif sort == 'commented':
        query = query.outerjoin(Comment).group_by(Dream.id).order_by(
            desc(func.max(Comment.created_at)))

    dreams = query.all()
    return render_template('community_dreams.html', dreams=dreams)

@app.route('/dream_groups')
@login_required
def dream_groups():
    """View all dream groups."""
    groups = DreamGroup.query.all()
    return render_template('dream_groups.html', groups=groups)

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new dream group."""
    if current_user.subscription_type == 'free':
        user_groups = DreamGroup.query.filter_by(created_by=current_user.id).count()
        if user_groups >= 2:
            flash('Free users can only create up to 2 groups. Upgrade to Premium for unlimited group creation!')
            return redirect(url_for('subscription'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        try:
            dream_group = DreamGroup(
                name=name,
                description=description,
                created_by=current_user.id
            )
            db.session.add(dream_group)
            db.session.flush()

            group_membership = GroupMembership(
                user_id=current_user.id,
                group_id=dream_group.id,
                is_admin=True,
                joined_at=datetime.utcnow()
            )
            db.session.add(group_membership)
            db.session.commit()

            flash('Dream Group created successfully!')
            return redirect(url_for('dream_group', group_id=dream_group.id))

        except Exception as e:
            logger.error(f"Error creating dream group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating your dream group.')
            return render_template('create_group.html')

    return render_template('create_group.html')

@app.route('/edit_group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    """Edit a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        is_admin=True
    ).first()
    
    if not membership:
        flash('You do not have permission to edit this group.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    if request.method == 'POST':
        group.name = request.form.get('name')
        group.description = request.form.get('description')
        
        try:
            db.session.commit()
            flash('Group updated successfully!')
            return redirect(url_for('dream_group', group_id=group_id))
        except Exception as e:
            logger.error(f"Error updating group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the group.')
            
    return render_template('edit_group.html', group=group)

@app.route('/join_group/<int:group_id>', methods=['POST'])
@login_required
def join_group(group_id):
    """Join a dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    
    existing_membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if existing_membership:
        flash('You are already a member of this group.')
        return redirect(url_for('dream_group', group_id=group_id))
    
    try:
        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group_id,
            is_admin=False,
            joined_at=datetime.utcnow()
        )
        db.session.add(membership)
        db.session.commit()
        flash('Successfully joined the group!')
    except Exception as e:
        logger.error(f"Error joining group: {str(e)}")
        db.session.rollback()
        flash('An error occurred while joining the group.')
        
    return redirect(url_for('dream_group', group_id=group_id))

@app.route('/leave_group/<int:group_id>', methods=['POST'])
@login_required
def leave_group(group_id):
    """Leave a dream group."""
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if not membership:
        flash('You are not a member of this group.')
        return redirect(url_for('dream_groups'))
    
    if membership.is_admin:
        admin_count = GroupMembership.query.filter_by(
            group_id=group_id,
            is_admin=True
        ).count()
        if admin_count <= 1:
            flash('Cannot leave group: you are the last admin. Please assign another admin first.')
            return redirect(url_for('dream_group', group_id=group_id))
    
    try:
        db.session.delete(membership)
        db.session.commit()
        flash('Successfully left the group.')
    except Exception as e:
        logger.error(f"Error leaving group: {str(e)}")
        db.session.rollback()
        flash('An error occurred while leaving the group.')
        
    return redirect(url_for('dream_groups'))

@app.route('/dream_group/<int:group_id>')
@login_required
def dream_group(group_id):
    """View a specific dream group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if not membership:
        flash('You must be a member to view this group.')
        return redirect(url_for('dream_groups'))
    
    forum_posts = ForumPost.query.filter_by(group_id=group_id).order_by(ForumPost.created_at.desc()).all()
    return render_template('dream_group.html', 
                         group=group,
                         membership=membership,
                         forum_posts=forum_posts)

@app.route('/group/<int:group_id>/forum/new', methods=['GET', 'POST'])
@login_required
def create_forum_post(group_id):
    """Create a new forum post in a group."""
    group = DreamGroup.query.get_or_404(group_id)
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if not membership:
        flash('You must be a member to create posts.')
        return redirect(url_for('dream_groups'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        try:
            post = ForumPost(
                title=title,
                content=content,
                author_id=current_user.id,
                group_id=group_id,
                created_at=datetime.utcnow()
            )
            db.session.add(post)
            db.session.commit()
            flash('Post created successfully!')
            return redirect(url_for('dream_group', group_id=group_id))
        except Exception as e:
            logger.error(f"Error creating forum post: {str(e)}")
            db.session.rollback()
            flash('An error occurred while creating your post.')
            
    return render_template('create_forum_post.html', group=group)

@app.route('/forum_post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_to_post(post_id):
    """Reply to a forum post."""
    post = ForumPost.query.get_or_404(post_id)
    membership = GroupMembership.query.filter_by(
        user_id=current_user.id,
        group_id=post.group_id
    ).first()
    
    if not membership:
        flash('You must be a member to reply.')
        return redirect(url_for('dream_groups'))
        
    content = request.form.get('content')
    if not content:
        flash('Reply cannot be empty.')
        return redirect(url_for('forum_post', post_id=post_id))
        
    try:
        reply = ForumReply(
            content=content,
            user_id=current_user.id,
            post_id=post_id,
            created_at=datetime.utcnow()
        )
        db.session.add(reply)
        db.session.commit()
        flash('Reply added successfully!')
    except Exception as e:
        logger.error(f"Error adding reply: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your reply.')
        
    return redirect(url_for('forum_post', post_id=post_id))

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
        comment = Comment(content=content,
                          user_id=current_user.id,
                          dream_id=dream_id,
                          created_at=datetime.utcnow())

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