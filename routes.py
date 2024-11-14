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
                        extra_data={'login_method': 'registration'}
                    )
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
                with session_manager.session_scope() as session:
                    user = session.query(User).filter_by(username=request.form['username']).first()
                    if user and user.check_password(request.form['password']):
                        if login_user(user):
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
                    if user:
                        track_user_activity(
                            user.id,
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

    return app