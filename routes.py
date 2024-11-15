from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, session_manager
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime, timedelta  # Added import for timedelta
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, text, or_, func
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns
from activity_tracker import (track_user_activity, track_premium_feature_usage,
                              ACTIVITY_TYPES)
import csv
from io import StringIO
import json

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def check_existing_user(username, email):
    """Check if a user with given username or email already exists."""
    try:
        with session_manager.session_scope() as session:
            existing_user = session.query(User).filter((
                User.username == username) | (User.email == email)).first()
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
            return user.id  # Return the user ID instead of user object
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None


def handle_user_login(user_id):
    """Handle user login in a separate transaction."""
    try:
        with session_manager.session_scope() as session:
            user = session.query(User).get(user_id)
            if user:
                if login_user(user):
                    track_user_activity(
                        user.id,
                        ACTIVITY_TYPES['LOGIN'],
                        extra_data={'login_method': 'registration'})
                    return True
        return False
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
                    extra_data={'page': 'dashboard'})
                if error:
                    logger.warning(f"Failed to track dashboard view: {error}")

                dreams = Dream.query.filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                return render_template('index.html',
                                       dreams=dreams if dreams else [])
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

                # Create user in separate transaction and get user_id
                user_id = create_user(username, email, password)
                if not user_id:
                    flash('An error occurred during registration')
                    return render_template('register.html')

                # Handle login in separate transaction using user_id
                if handle_user_login(user_id):
                    # Track successful registration
                    track_user_activity(
                        user_id,
                        ACTIVITY_TYPES['REGISTRATION'],
                        extra_data={'registration_method': 'email'})
                    return redirect(url_for('index'))
                else:
                    flash(
                        'Registration successful but login failed. Please try logging in.'
                    )
                    return redirect(url_for('login'))

            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                flash('An error occurred during registration')
                return render_template('register.html')

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login with enhanced error handling and session management."""
        # Redirect if user is already logged in
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            # Validate form data
            if not username or not password:
                flash('Username and password are required', 'error')
                logger.warning('Login attempt with missing credentials')
                return render_template('login.html')

            try:
                with session_manager.session_scope() as session:
                    # Find user and verify password
                    user = session.query(User).filter_by(
                        username=username).first()

                    if user and user.check_password(password):
                        # Initialize session with user data
                        if login_user(user, remember=True):
                            # Track successful login
                            success, error = track_user_activity(
                                user.id,
                                ACTIVITY_TYPES['LOGIN'],
                                extra_data={'login_method': 'password'})
                            if error:
                                logger.warning(
                                    f"Failed to track login: {error}")

                            # Get the next page from query parameters
                            next_page = request.args.get('next')
                            # Validate the next page URL to prevent open redirect
                            if next_page and not next_page.startswith('/'):
                                next_page = None

                            flash('Login successful!', 'success')
                            return redirect(next_page or url_for('index'))
                        else:
                            logger.error(
                                f"Failed to login user {username}: login_user() returned False"
                            )
                            flash('Error during login. Please try again.',
                                  'error')
                    else:
                        # Track failed login attempt
                        if user:
                            track_user_activity(
                                user.id,
                                ACTIVITY_TYPES['LOGIN'],
                                description="Failed login attempt",
                                extra_data={'reason': 'invalid_password'})
                            logger.warning(
                                f"Failed login attempt for user {username}: invalid password"
                            )
                        else:
                            logger.warning(
                                f"Failed login attempt: user {username} not found"
                            )

                        # Use a generic error message to prevent user enumeration
                        flash('Invalid username or password', 'error')

            except SQLAlchemyError as e:
                logger.error(f"Database error during login: {str(e)}")
                flash('A system error occurred. Please try again later.',
                      'error')
                db.session.rollback()
            except Exception as e:
                logger.error(f"Unexpected error during login: {str(e)}")
                flash('An unexpected error occurred. Please try again.',
                      'error')
                if 'db' in locals() and db.session.is_active:
                    db.session.rollback()

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        if current_user.is_authenticated:
            success, error = track_user_activity(current_user.id,
                                                 ACTIVITY_TYPES['LOGOUT'])
            if error:
                logger.warning(f"Failed to track logout: {error}")
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dream/new', methods=['GET', 'POST'])
    @login_required
    def dream_new():
        """Create a new dream entry."""
        if request.method == 'POST':
            try:
                with session_manager.session_scope() as session:
                    dream = Dream(
                        user_id=current_user.id,
                        title=request.form['title'],
                        content=request.form['content'],
                        mood=request.form.get('mood'),
                        tags=request.form.get('tags'),
                        is_public=bool(request.form.get('is_public')),
                        is_anonymous=bool(request.form.get('is_anonymous')),
                        lucidity_level=int(
                            request.form.get('lucidity_level', 0)),
                        sleep_quality=int(request.form.get('sleep_quality',
                                                           0)),
                        sleep_position=request.form.get('sleep_position'),
                        sleep_interruptions=int(
                            request.form.get('sleep_interruptions', 0)))
                    session.add(dream)
                    session.flush()

                    track_user_activity(
                        current_user.id,
                        ACTIVITY_TYPES['DREAM_CREATE'],
                        target_id=dream.id,
                        description=f"Created new dream: {dream.title}")

                    flash('Dream logged successfully!')
                    return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error creating dream: {str(e)}")
                flash('An error occurred while saving your dream')

        return render_template('dream_new.html')

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View an individual dream and its comments."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)

                # Check if user has permission to view this dream
                if dream.user_id != current_user.id and not dream.is_public:
                    abort(403)

                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['DREAM_VIEW'],
                                    target_id=dream.id,
                                    description=f"Viewed dream: {dream.title}")

                return render_template('dream_view.html', dream=dream)
        except Exception as e:
            logger.error(f"Error viewing dream {dream_id}: {str(e)}")
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    @app.route('/dream/<int:dream_id>/edit', methods=['GET', 'POST'])
    @login_required
    def dream_edit(dream_id):
        """Edit an existing dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)

                # Check if user owns this dream
                if dream.user_id != current_user.id:
                    abort(403)

                if request.method == 'POST':
                    dream.title = request.form['title']
                    dream.content = request.form['content']
                    dream.mood = request.form.get('mood')
                    dream.tags = request.form.get('tags')
                    dream.is_public = bool(request.form.get('is_public'))
                    dream.is_anonymous = bool(request.form.get('is_anonymous'))
                    dream.lucidity_level = int(
                        request.form.get('lucidity_level', 0))
                    dream.sleep_quality = int(
                        request.form.get('sleep_quality', 0))
                    dream.sleep_position = request.form.get('sleep_position')
                    dream.sleep_interruptions = int(
                        request.form.get('sleep_interruptions', 0))

                    track_user_activity(
                        current_user.id,
                        ACTIVITY_TYPES['DREAM_EDIT'],
                        target_id=dream.id,
                        description=f"Edited dream: {dream.title}")

                    flash('Dream updated successfully!')
                    return redirect(url_for('dream_view', dream_id=dream.id))

                return render_template('dream_edit.html', dream=dream)
        except Exception as e:
            logger.error(f"Error editing dream {dream_id}: {str(e)}")
            flash('An error occurred while updating the dream')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream/<int:dream_id>/delete', methods=['POST'])
    @login_required
    def dream_delete(dream_id):
        """Delete a dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)

                # Check if user owns this dream
                if dream.user_id != current_user.id:
                    abort(403)

                title = dream.title
                session.delete(dream)

                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['DREAM_DELETE'],
                                    description=f"Deleted dream: {title}")

                flash('Dream deleted successfully!')
                return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Error deleting dream {dream_id}: {str(e)}")
            flash('An error occurred while deleting the dream')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream/<int:dream_id>/comment', methods=['POST'])
    @login_required
    def add_comment(dream_id):
        """Add a comment to a dream."""
        try:
            with session_manager.session_scope() as session:
                dream = session.query(Dream).get_or_404(dream_id)

                # Check if dream is public or user owns it
                if not dream.is_public and dream.user_id != current_user.id:
                    abort(403)

                comment = Comment(content=request.form['content'],
                                  user_id=current_user.id,
                                  dream_id=dream_id)
                session.add(comment)

                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['COMMENT_ADD'],
                    target_id=dream.id,
                    description=f"Added comment on dream: {dream.title}")

                flash('Comment added successfully!')
                return redirect(url_for('dream_view', dream_id=dream_id))
        except Exception as e:
            logger.error(f"Error adding comment to dream {dream_id}: {str(e)}")
            flash('An error occurred while adding your comment')
            return redirect(url_for('dream_view', dream_id=dream_id))

    @app.route('/dream_patterns')
    @login_required
    def dream_patterns():
        """Analyze patterns across user's dreams."""
        try:
            with session_manager.session_scope() as session:
                # Get user's dreams from the last 30 days
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                dreams = session.query(Dream).filter(
                    Dream.user_id == current_user.id, Dream.date
                    >= thirty_days_ago).all()

                if not dreams:
                    flash('Start logging dreams to see patterns and insights.')
                    return render_template('dream_patterns.html',
                                           patterns=None)

                # Track pattern analysis view
                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['DREAM_PATTERNS_VIEW'],
                                    description="Viewed dream patterns")

                # Get patterns analysis
                is_premium = current_user.subscription_type == 'premium'
                patterns = analyze_dream_patterns(dreams, is_premium)

                return render_template('dream_patterns.html',
                                       patterns=patterns)
        except Exception as e:
            logger.error(f"Error analyzing dream patterns: {str(e)}")
            flash('An error occurred while analyzing dream patterns')
            return redirect(url_for('index'))

    @app.route('/community_dreams')
    @login_required
    def community_dreams():
        """View community dreams feed."""
        try:
            with session_manager.session_scope() as session:
                page = request.args.get('page', 1, type=int)
                per_page = 10

                # Get public dreams with user info, ordered by date
                dreams = session.query(Dream).filter(
                    Dream.is_public == True).order_by(
                        Dream.date.desc()).paginate(page=page,
                                                    per_page=per_page,
                                                    error_out=False)

                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['COMMUNITY_DREAMS_VIEW'],
                                    description="Viewed community dreams")

                return render_template('community_dreams.html', dreams=dreams)
        except Exception as e:
            logger.error(f"Error viewing community dreams: {str(e)}")
            flash('An error occurred while loading community dreams')
            return redirect(url_for('index'))

    @app.route('/dream_groups')
    @login_required
    def dream_groups():
        """List all dream groups."""
        try:
            with session_manager.session_scope() as session:
                # Get all groups with their member counts
                groups = session.query(DreamGroup).all()

                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['DREAM_GROUPS_VIEW'],
                                    description="Viewed dream groups")

                return render_template('dream_groups.html', groups=groups)
        except Exception as e:
            logger.error(f"Error viewing dream groups: {str(e)}")
            flash('An error occurred while loading dream groups')
            return redirect(url_for('index'))

    @app.route('/forum')
    @login_required
    def forum():
        """View dream discussion forum."""
        try:
            with session_manager.session_scope() as session:
                page = request.args.get('page', 1, type=int)
                per_page = 20

                # Get forum posts with user info and reply counts
                posts = session.query(ForumPost).order_by(
                    ForumPost.created_at.desc()).paginate(page=page,
                                                          per_page=per_page,
                                                          error_out=False)

                track_user_activity(current_user.id,
                                    ACTIVITY_TYPES['FORUM_VIEW'],
                                    description="Viewed dream forum")

                return render_template('forum.html', posts=posts)
        except Exception as e:
            logger.error(f"Error viewing forum: {str(e)}")
            flash('An error occurred while loading the forum')
            return redirect(url_for('index'))

    @app.route('/subscription', methods=['GET', 'POST'])
    @login_required
    def subscription():
        return render_template('subscription.html')

    return app
