from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
import os
import stripe
from ai_helper import analyze_dream, analyze_dream_patterns
from activity_tracker import track_user_activity, ACTIVITY_TYPES

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def register_routes(app):
    @app.route('/')
    def index():
        """Landing page and user dashboard."""
        try:
            if current_user.is_authenticated:
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_VIEW'],
                    description="Viewed dashboard"
                )
                dreams = Dream.query.filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()
                logger.info(f"Successfully fetched {len(dreams) if dreams else 0} dreams for user {current_user.id}")
                return render_template('index.html', dreams=dreams if dreams else [])
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            db.session.rollback()
            return render_template('index.html', dreams=[])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            try:
                user = User.query.filter_by(username=request.form['username']).first()
                if user and user.check_password(request.form['password']):
                    login_user(user)
                    track_user_activity(user.id, ACTIVITY_TYPES['LOGIN'])
                    next_page = request.args.get('next')
                    return redirect(next_page if next_page else url_for('index'))
                flash('Invalid username or password')
            except Exception as e:
                logger.error(f"Login error: {str(e)}")
                flash('An error occurred during login')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            try:
                if User.query.filter_by(username=request.form['username']).first():
                    flash('Username already exists')
                    return render_template('register.html')
                    
                if User.query.filter_by(email=request.form['email']).first():
                    flash('Email already registered')
                    return render_template('register.html')
                    
                user = User(
                    username=request.form['username'],
                    email=request.form['email']
                )
                user.set_password(request.form['password'])
                db.session.add(user)
                db.session.commit()
                
                track_user_activity(user.id, ACTIVITY_TYPES['REGISTRATION'])
                login_user(user)
                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                db.session.rollback()
                flash('An error occurred during registration')
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        if current_user.is_authenticated:
            track_user_activity(current_user.id, ACTIVITY_TYPES['LOGOUT'])
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
            
            track_user_activity(
                user_id=current_user.id,
                activity_type=ACTIVITY_TYPES['DREAM_VIEW'],
                description=f"Viewed dream: {dream.title}",
                target_type='dream',
                target_id=dream_id
            )
            
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
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_PATTERNS_VIEW'],
                description="Viewed dream patterns"
            )
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
                    user_id=current_user.id
                )
                
                # Optional fields
                if 'mood' in request.form:
                    dream.mood = request.form['mood']
                if 'tags' in request.form:
                    dream.tags = request.form['tags']
                    
                db.session.add(dream)
                db.session.commit()
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_CREATE'],
                    description=f"Created new dream: {dream.title}",
                    target_type='dream',
                    target_id=dream.id
                )
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
            
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['COMMENT_ADD'],
                description=f"Added comment to dream {dream_id}",
                target_type='dream',
                target_id=dream_id
            )
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
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_GROUPS_VIEW'],
                description="Viewed dream groups"
            )
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
            
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['GROUP_JOIN'],
                description=f"Joined group {group_id}",
                target_type='group',
                target_id=group_id
            )
            flash('Successfully joined the group!')
        except Exception as e:
            logger.error(f"Error joining group: {str(e)}")
            db.session.rollback()
            flash('An error occurred while joining the group')
        return redirect(url_for('dream_group', group_id=group_id))

    @app.route('/subscription')
    @login_required
    def subscription():
        """View subscription page."""
        try:
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['SUBSCRIPTION_VIEW'],
                description="Viewed subscription page"
            )
            return render_template('subscription.html', 
                               stripe_publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY'))
        except Exception as e:
            logger.error(f"Error viewing subscription page: {str(e)}")
            flash('An error occurred while loading the subscription page')
            return redirect(url_for('index'))

    return app
