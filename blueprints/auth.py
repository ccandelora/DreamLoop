from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import session_manager
from activity_tracker import track_user_activity, ACTIVITY_TYPES
from middleware import validate_request_data
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration with enhanced security and error handling."""
    if current_user.is_authenticated:
        return redirect(url_for('dreams.index'))

    if request.method == 'POST':
        try:
            validate_request_data()  # Validate input data
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            with session_manager.session_scope() as session:
                # Check for existing user
                existing_user = session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()

                if existing_user:
                    if existing_user.username == username:
                        flash('Username already exists', 'error')
                    else:
                        flash('Email already registered', 'error')
                    return render_template('register.html'), 400

                # Create new user
                user = User(username=username, email=email)
                user.set_password(password)
                session.add(user)
                session.flush()  # Get the user ID

                # Track registration
                track_user_activity(
                    user.id,
                    ACTIVITY_TYPES['REGISTRATION'],
                    extra_data={'registration_method': 'email'}
                )

                # Log in the user
                if login_user(user):
                    flash('Registration successful!', 'success')
                    return redirect(url_for('dreams.index'))
                else:
                    flash('Registration successful but login failed. Please try logging in.', 'warning')
                    return redirect(url_for('auth.login'))

        except SQLAlchemyError as e:
            logger.error(f"Database error during registration: {str(e)}")
            flash('A system error occurred. Please try again later.', 'error')
            return render_template('register.html'), 500
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('register.html'), 500

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with enhanced security and session management."""
    if current_user.is_authenticated:
        return redirect(url_for('dreams.index'))

    if request.method == 'POST':
        try:
            validate_request_data()  # Validate input data
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('login.html'), 400

            with session_manager.session_scope() as session:
                user = session.query(User).filter_by(username=username).first()

                if user and user.check_password(password):
                    if login_user(user, remember=True):
                        track_user_activity(
                            user.id,
                            ACTIVITY_TYPES['LOGIN'],
                            extra_data={'login_method': 'password'}
                        )
                        
                        # Validate next parameter to prevent open redirect
                        next_page = request.args.get('next')
                        if next_page and not next_page.startswith('/'):
                            next_page = None

                        flash('Login successful!', 'success')
                        return redirect(next_page or url_for('dreams.index'))
                    else:
                        logger.error(f"Failed to login user {username}")
                        flash('Error during login. Please try again.', 'error')
                        return render_template('login.html'), 500
                else:
                    if user:
                        track_user_activity(
                            user.id,
                            ACTIVITY_TYPES['LOGIN'],
                            description="Failed login attempt",
                            extra_data={'reason': 'invalid_password'}
                        )
                    flash('Invalid username or password', 'error')
                    return render_template('login.html'), 401

        except SQLAlchemyError as e:
            logger.error(f"Database error during login: {str(e)}")
            flash('A system error occurred. Please try again later.', 'error')
            return render_template('login.html'), 500
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('login.html'), 500

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout with activity tracking."""
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
            logout_user()
            track_user_activity(user_id, ACTIVITY_TYPES['LOGOUT'])
            flash('You have been logged out successfully.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout.', 'error')
        return redirect(url_for('dreams.index'))
