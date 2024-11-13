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

logging.basicConfig(level=logging.INFO)
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
        except SQLAlchemyError as e:
            logger.error(f"Error in index route: {str(e)}")
            db.session.rollback()
            return render_template('index.html', dreams=[])

    @app.route('/dream/<int:dream_id>')
    @login_required
    def dream_view(dream_id):
        """View a dream entry."""
        try:
            # Fetch dream with error handling
            dream = Dream.query.get_or_404(dream_id)
            
            # Check permissions
            if dream.user_id != current_user.id and not dream.is_public:
                logger.warning(f"Unauthorized access attempt to dream {dream_id} by user {current_user.id}")
                flash('You do not have permission to view this dream')
                return redirect(url_for('index'))
            
            # Track view activity with error handling
            try:
                track_user_activity(
                    user_id=current_user.id,
                    activity_type=ACTIVITY_TYPES['DREAM_VIEW'],
                    description=f"Viewed dream: {dream.title}",
                    target_type='dream',
                    target_id=dream_id
                )
                logger.info(f"Dream view activity tracked for dream {dream_id} by user {current_user.id}")
            except Exception as e:
                logger.error(f"Failed to track dream view activity: {str(e)}")
                # Continue with the request even if activity tracking fails
            
            return render_template('dream_view.html', dream=dream)
            
        except SQLAlchemyError as e:
            error_context = {
                'dream_id': dream_id,
                'user_id': current_user.id,
                'request_path': request.path
            }
            logger.error(f"Database error in dream_view route: {str(e)}", extra=error_context)
            db.session.rollback()
            flash('An error occurred while loading the dream')
            return redirect(url_for('index'))

    # Add other routes here...
    
    return app
