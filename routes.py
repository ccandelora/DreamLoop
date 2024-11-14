from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, session_manager
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, text
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns
from activity_tracker import (
    track_user_activity, 
    track_premium_feature_usage,
    ACTIVITY_TYPES
)

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def check_existing_user(username, email):
    """Check if a user with given username or email already exists."""
    try:
        with session_manager.session_scope() as session:
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            return existing_user
    except Exception as e:
        logger.error(f"Error checking existing user: {str(e)}")
        return None

def create_user(username, email, password):
    """Create a new user in a separate transaction."""
    try:
        with session_manager.session_scope() as session:
            user = User(username=username, email=email)
            user.set_password(password)
            session.add(user)
            session.flush()  # Get the user ID
            return user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

def handle_user_login(user):
    """Handle user login in a separate transaction."""
    try:
        success = login_user(user)
        if success:
            track_user_activity(
                user.id,
                ACTIVITY_TYPES['LOGIN'],
                extra_data={'login_method': 'registration'}
            )
        return success
    except Exception as e:
        logger.error(f"Error during login after registration: {str(e)}")
        return False

def register_routes(app):
    @app.route('/')
    def index():
        """Landing page and user dashboard."""
        try:
            if current_user.is_authenticated:
                success, error = track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_VIEW'],
                    description="Viewed dashboard",
                    extra_data={'page': 'dashboard'}
                )
                if error:
                    logger.warning(f"Failed to track dashboard view: {error}")
                
                dreams = Dream.query.filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                return render_template('index.html', dreams=dreams if dreams else [])
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            return render_template('index.html', dreams=[])

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration with separate transactions."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            try:
                # Check for existing user outside transaction
                existing_user = check_existing_user(username, email)
                
                if existing_user:
                    if existing_user.username == username:
                        flash('Username already exists')
                    else:
                        flash('Email already registered')
                    return render_template('register.html')

                # Create user in separate transaction
                user = create_user(username, email, password)
                if not user:
                    flash('An error occurred during registration')
                    return render_template('register.html')

                # Handle login in separate transaction
                if handle_user_login(user):
                    # Track successful registration
                    track_user_activity(
                        user.id,
                        ACTIVITY_TYPES['REGISTRATION'],
                        extra_data={'registration_method': 'email'}
                    )
                    return redirect(url_for('index'))
                else:
                    flash('Registration successful but login failed. Please try logging in.')
                    return redirect(url_for('login'))

            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                flash('An error occurred during registration')
                return render_template('register.html')

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                user = User.query.filter_by(username=request.form['username']).first()
                if user and user.check_password(request.form['password']):
                    login_user(user)
                    success, error = track_user_activity(
                        user.id, 
                        ACTIVITY_TYPES['LOGIN'],
                        extra_data={'login_method': 'password'}
                    )
                    if error:
                        logger.warning(f"Failed to track login: {error}")
                    
                    next_page = request.args.get('next')
                    return redirect(next_page if next_page else url_for('index'))
                flash('Invalid username or password')
                track_user_activity(
                    user.id if user else None,
                    ACTIVITY_TYPES['LOGIN'],
                    description="Failed login attempt",
                    extra_data={'reason': 'invalid_credentials'}
                )
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                flash('An error occurred during login')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        if current_user.is_authenticated:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['LOGOUT']
            )
            if error:
                logger.warning(f"Failed to track logout: {error}")
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View a dream entry."""
        try:
            dream = Dream.query.get_or_404(dream_id)
            
            if dream.user_id != current_user.id and not dream.is_public:
                logger.warning(f"Unauthorized access attempt to dream {dream_id} by user {current_user.id}")
                flash('You do not have permission to view this dream')
                return redirect(url_for('index'))
            
            success, error = track_user_activity(
                user_id=current_user.id,
                activity_type=ACTIVITY_TYPES['DREAM_VIEW'],
                description=f"Viewed dream: {dream.title}",
                target_type='dream',
                target_id=dream_id,
                extra_data={'is_public': dream.is_public}
            )
            if error:
                logger.warning(f"Failed to track dream view: {error}")
            
            return render_template('dream_view.html', dream=dream)
            
        except Exception as e:
            logger.error(f"Error viewing dream: {str(e)}")
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    @app.route('/dream/patterns')
    @login_required
    def dream_patterns():
        """View dream patterns."""
        try:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_PATTERNS_VIEW'],
                description="Viewed dream patterns"
            )
            if error:
                logger.warning(f"Failed to track dream patterns view: {error}")
            return render_template('dream_patterns.html')
        except Exception as e:
            logger.error(f"Error viewing dream patterns: {str(e)}")
            flash('An error occurred while loading dream patterns')
            return redirect(url_for('index'))

    @app.route('/dream/new', methods=['GET', 'POST'])
    @login_required
    def dream_new():
        """Create a new dream entry."""
        if request.method == 'POST':
            try:
                dream = Dream(
                    title=request.form['title'],
                    content=request.form['content'],
                    is_public=bool(request.form.get('is_public')),
                    is_anonymous=bool(request.form.get('is_anonymous')),
                    user_id=current_user.id,
                    mood=request.form.get('mood'),
                    lucidity_level=request.form.get('lucidity_level'),
                    tags=request.form.get('tags'),
                    sleep_quality=request.form.get('sleep_quality'),
                    sleep_position=request.form.get('sleep_position'),
                    sleep_interruptions=request.form.get('sleep_interruptions', 0),
                    bed_time=datetime.fromisoformat(request.form['bed_time']) if request.form.get('bed_time') else None,
                    wake_time=datetime.fromisoformat(request.form['wake_time']) if request.form.get('wake_time') else None
                )
                
                db.session.add(dream)
                db.session.commit()
                
                # Track dream creation with detailed metadata
                success, error = track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_CREATE'],
                    description=f"Created new dream: {dream.title}",
                    target_type='dream',
                    target_id=dream.id,
                    extra_data={
                        'is_public': dream.is_public,
                        'is_anonymous': dream.is_anonymous,
                        'has_mood': bool(dream.mood),
                        'has_tags': bool(dream.tags),
                        'lucidity_level': dream.lucidity_level
                    }
                )
                
                if error:
                    logger.warning(f"Failed to track dream creation: {error}")
                
                flash('Dream logged successfully!')
                return redirect(url_for('dream_view', dream_id=dream.id))
                
            except Exception as e:
                logger.error(f"Error creating dream: {str(e)}")
                db.session.rollback()
                flash('An error occurred while saving your dream')
                
        return render_template('dream_log.html')

    @app.route('/dream/<int:dream_id>/comment', methods=['POST'])
    @login_required
    def add_comment(dream_id):
        """Add a comment to a dream."""
        try:
            comment = Comment(
                content=request.form['content'],
                user_id=current_user.id,
                dream_id=dream_id
            )
            db.session.add(comment)
            db.session.commit()
            
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['COMMENT_ADD'],
                description=f"Added comment to dream {dream_id}",
                target_type='dream',
                target_id=dream_id
            )
            if error:
                logger.warning(f"Failed to track comment addition: {error}")
            flash('Comment added successfully!')
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            db.session.rollback()
            flash('An error occurred while adding your comment')
        return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/groups')
    @login_required
    def dream_groups():
        """View all dream groups."""
        try:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_GROUPS_VIEW'],
                description="Viewed dream groups"
            )
            if error:
                logger.warning(f"Failed to track dream groups view: {error}")
            groups = DreamGroup.query.all()
            return render_template('dream_groups.html', groups=groups)
        except Exception as e:
            logger.error(f"Error viewing dream groups: {str(e)}")
            flash('An error occurred while loading dream groups')
            return redirect(url_for('index'))

    @app.route('/group/<int:group_id>/join', methods=['POST'])
    @login_required
    def join_group(group_id):
        """Join a dream group."""
        try:
            membership = GroupMembership(
                user_id=current_user.id,
                group_id=group_id
            )
            db.session.add(membership)
            db.session.commit()
            
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['GROUP_JOIN'],
                description=f"Joined group {group_id}",
                target_type='group',
                target_id=group_id
            )
            if error:
                logger.warning(f"Failed to track group join: {error}")
            flash('Successfully joined the group!')
        except Exception as e:
            logger.error(f"Error joining group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while joining the group')
        return redirect(url_for('dream_group', group_id=group_id))

    @app.route('/community')
    @login_required
    def community_dreams():
        """View community shared dreams."""
        try:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['COMMUNITY_DREAMS_VIEW'],
                description="Viewed community dreams"
            )
            if error:
                logger.warning(f"Failed to track community dreams view: {error}")
            
            # Get all public dreams excluding user's own dreams
            dreams = Dream.query.filter_by(is_public=True)\
                .filter(Dream.user_id != current_user.id)\
                .order_by(Dream.date.desc())\
                .all()
                
            logger.info(f"Successfully fetched {len(dreams)} community dreams for user {current_user.id}")
            return render_template('community_dreams.html', dreams=dreams)
            
        except Exception as e:
            logger.error(f"Error viewing community dreams: {str(e)}")
            flash('An error occurred while loading community dreams')
            return redirect(url_for('index'))
    
    @app.route('/subscription')
    @login_required
    def subscription():
        """View subscription page."""
        try:
            success, error = track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['SUBSCRIPTION_VIEW'],
                description="Viewed subscription page"
            )
            if error:
                logger.warning(f"Failed to track subscription page view: {error}")
            return render_template('subscription.html', 
                               stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))
        except Exception as e:
            logger.error(f"Error viewing subscription page: {str(e)}")
            flash('An error occurred while loading the subscription page')
            return redirect(url_for('index'))

    return app