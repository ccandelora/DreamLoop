from flask import render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply, Notification
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

@app.context_processor
def inject_unread_notifications():
    """Inject unread notifications count into all templates."""
    if current_user.is_authenticated:
        # Use eager loading to optimize the query
        unread_count = (
            Notification.query
            .filter_by(user_id=current_user.id, read=False)
            .count()
        )
        logger.info(f"Unread notifications count for user {current_user.id}: {unread_count}")
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}

@app.route('/')
def index():
    """Landing page and user dashboard."""
    return render_template('index.html', Dream=Dream)

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

@app.route('/notifications')
@login_required
def notifications():
    """View all notifications."""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        flash('Unauthorized access.')
        return redirect(url_for('notifications'))
    
    notification.read = True
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/notifications/mark_all_read')
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(user_id=current_user.id).update({'read': True})
    db.session.commit()
    return redirect(url_for('notifications'))

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

        try:
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

@app.route('/dream/<int:dream_id>', methods=['GET', 'POST'])
@login_required
def dream_view(dream_id):
    """View a dream entry and its comments."""
    dream = db.session.get(Dream, dream_id)
    if not dream:
        flash('Dream not found.')
        return redirect(url_for('index'))

    # Fetch all comments for this dream with eager loading of authors
    comments = Comment.query.options(
        db.joinedload(Comment.author),
        db.joinedload(Comment.moderator)
    ).filter_by(dream_id=dream_id).all()
    
    # Organize comments into a threaded structure
    threaded_comments = []
    comment_dict = {}
    
    # First pass: create a dictionary of comments
    for comment in comments:
        comment_dict[comment.id] = {
            'comment': comment,
            'replies': []
        }
    
    # Second pass: organize into threads
    for comment in comments:
        if comment.parent_id is None:
            # This is a top-level comment
            threaded_comments.append(comment_dict[comment.id])
        else:
            # This is a reply
            if comment.parent_id in comment_dict:
                comment_dict[comment.parent_id]['replies'].append(comment_dict[comment.id])

    return render_template('dream_view.html', dream=dream, threaded_comments=threaded_comments)

@app.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream."""
    logger.info(f"Adding comment to dream {dream_id}")
    dream = db.session.get(Dream, dream_id)
    if not dream:
        flash('Dream not found.')
        return redirect(url_for('index'))
        
    content = request.form.get('content')
    parent_id = request.form.get('parent_id')
    
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    try:
        # Create the comment
        comment = Comment(
            content=content,
            user_id=current_user.id,
            dream_id=dream_id,
            created_at=datetime.utcnow(),
            parent_id=int(parent_id) if parent_id else None
        )
        db.session.add(comment)
        logger.info(f"Created comment with ID {comment.id} by user {current_user.id}")
        
        # Create notification for dream owner if it's not their own comment
        if dream.user_id != current_user.id:
            notification_type = 'reply' if parent_id else 'comment'
            notification_title = f"New {notification_type} on your dream: {dream.title}"
            notification_content = f"{current_user.username} {notification_type}d: {content[:100]}{'...' if len(content) > 100 else ''}"
            
            notification = Notification(
                user_id=dream.user_id,
                title=notification_title,
                content=notification_content,
                type=notification_type,
                reference_id=dream_id,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            logger.info(f"Created dream owner notification: {notification_title} for user {dream.user_id}")
            
            # If this is a reply, also notify the parent comment author
            if parent_id:
                parent_comment = db.session.get(Comment, int(parent_id))
                if parent_comment and parent_comment.user_id != current_user.id:
                    reply_notification = Notification(
                        user_id=parent_comment.user_id,
                        title=f"New reply to your comment on: {dream.title}",
                        content=f"{current_user.username} replied to your comment: {content[:100]}{'...' if len(content) > 100 else ''}",
                        type='reply',
                        reference_id=dream_id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(reply_notification)
                    logger.info(f"Created reply notification for user {parent_comment.user_id}")
        
        db.session.commit()
        flash('Comment added successfully!')
        logger.info("Successfully saved comment and notifications")
    except Exception as e:
        logger.error(f"Error adding comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while adding your comment.')
    
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(dream_id, comment_id):
    """Edit a comment."""
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        flash('You can only edit your own comments.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    content = request.form.get('content')
    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('dream_view', dream_id=dream_id))
    
    try:
        comment.content = content
        comment.edited_at = datetime.utcnow()
        db.session.commit()
        flash('Comment updated successfully!')
    except Exception as e:
        logger.error(f"Error updating comment: {str(e)}")
        db.session.rollback()
        flash('An error occurred while updating your comment.')
    
    return redirect(url_for('dream_view', dream_id=dream_id))

@app.route('/dream/<int:dream_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(dream_id, comment_id):
    """Delete a comment from a dream."""
    comment = Comment.query.get_or_404(comment_id)
    dream = Dream.query.get_or_404(dream_id)
    
    # Only allow comment author or dream owner to delete comments
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

@app.route('/subscription')
@login_required
def subscription():
    """Show subscription page."""
    return render_template('subscription.html', 
                         stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe Checkout session for premium subscription."""
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=current_user.id,
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 499,  # $4.99
                    'product_data': {
                        'name': 'DreamLoop Premium Subscription',
                        'description': 'Monthly subscription for premium features',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('subscription', success='true', _external=True),
            cancel_url=url_for('subscription', canceled='true', _external=True),
        )
        return jsonify({'url': checkout_session.url})
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events."""
    if request.content_length > 65535:
        return jsonify({'error': 'Payload too large'}), 400
        
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
        handle_stripe_webhook(event)
        return jsonify({'status': 'success'})
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel premium subscription."""
    try:
        # Reset subscription status
        current_user.subscription_type = 'free'
        current_user.subscription_end_date = None
        db.session.commit()
        flash('Your subscription has been canceled.')
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        flash('An error occurred while canceling your subscription.')
    
    return redirect(url_for('subscription'))

# Add these routes to the end of routes.py (keeping all existing routes)

@app.route('/admin/assign_moderator/<int:user_id>', methods=['POST'])
@login_required
def assign_moderator(user_id):
    """Assign moderator role to a user."""
    if not current_user.is_moderator:
        flash('Unauthorized access.')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    
    try:
        if action == 'assign':
            user.is_moderator = True
            flash(f'Moderator role assigned to {user.username}')
        elif action == 'remove':
            user.is_moderator = False
            flash(f'Moderator role removed from {user.username}')
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Error modifying moderator status: {str(e)}")
        db.session.rollback()
        flash('An error occurred while updating moderator status.')
    
    return redirect(url_for('index'))

@app.route('/comment/<int:comment_id>/moderate', methods=['POST'])
@login_required
def moderate_comment(comment_id):
    """Moderate a comment (hide/unhide)."""
    if not current_user.can_moderate():
        flash('Unauthorized access.')
        return redirect(url_for('index'))
    
    try:
        comment = Comment.query.get_or_404(comment_id)
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