from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import Users, Dream, DreamGroup, GroupMembership, Notification
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger('dreamloop')

@bp.route('/')
def index():
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            user_id=current_user.id, 
            read=False
        ).count()
        logger.info(f"Unread notifications count for user {current_user.id}: {unread_count}")
    return render_template('index.html', Dream=Dream)

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@bp.route('/dreams')
@login_required
def dreams():
    user_dreams = Dream.query.filter_by(user_id=current_user.id).all()
    return render_template('dreams.html', dreams=user_dreams)

@bp.route('/groups')
@login_required
def groups():
    # Get groups where the user is a member
    user_groups = current_user.groups
    return render_template('groups.html', groups=user_groups)

@bp.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Group name is required')
            return redirect(url_for('main.create_group'))
            
        new_group = DreamGroup(
            name=name,
            description=description,
            creator_id=current_user.id
        )
        
        # Add the creator as a member
        membership = GroupMembership(
            user_id=current_user.id,
            role='admin'
        )
        new_group.memberships.append(membership)
        
        try:
            db.session.add(new_group)
            db.session.commit()
            flash('Group created successfully!')
            return redirect(url_for('main.groups'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the group')
            return redirect(url_for('main.create_group'))
            
    return render_template('create_group.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if Users.query.filter_by(email=email).first():
            flash('Email address already exists')
            return redirect(url_for('main.register'))
            
        if Users.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.register'))
            
        new_user = Users(email=email, username=username)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.')
            return redirect(url_for('main.register'))
            
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Users.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
            
        flash('Invalid email or password')
        return redirect(url_for('main.login'))
        
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/notifications')
@login_required
def notifications():
    """Show user notifications."""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template(
        'notifications.html',
        notifications=notifications
    )

@bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    notification.read = True
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(
        user_id=current_user.id,
        read=False
    ).update({'read': True})
    
    db.session.commit()
    return jsonify({'success': True})

# Helper function to create notifications
def create_notification(user_id, message, notification_type=None, related_id=None):
    notification = Notification(
        user_id=user_id,
        message=message,
        notification_type=notification_type,
        related_id=related_id
    )
    db.session.add(notification)
    db.session.commit()

@bp.route('/dream/new', methods=['GET', 'POST'])
@login_required
def dream_new():
    """Create a new dream."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_private = request.form.get('is_private', False) == 'true'
        
        if not title or not content:
            flash('Title and content are required.')
            return redirect(url_for('main.dream_new'))
            
        new_dream = Dream(
            title=title,
            content=content,
            user_id=current_user.id,
            is_private=is_private
        )
        
        try:
            db.session.add(new_dream)
            db.session.commit()
            flash('Dream created successfully!')
            return redirect(url_for('main.dreams'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the dream.')
            return redirect(url_for('main.dream_new'))
            
    return render_template('dream_new.html')
