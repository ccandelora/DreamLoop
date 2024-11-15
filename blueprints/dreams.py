from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import Dream, Comment
from extensions import session_manager
from activity_tracker import track_user_activity, ACTIVITY_TYPES
from middleware import validate_request_data
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

dreams_bp = Blueprint('dreams', __name__)

@dreams_bp.route('/')
def index():
    """Landing page and user dashboard with error handling."""
    try:
        if current_user.is_authenticated:
            with session_manager.session_scope() as session:
                dreams = session.query(Dream)\
                    .filter_by(user_id=current_user.id)\
                    .order_by(Dream.date.desc())\
                    .limit(5)\
                    .all()

                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_VIEW'],
                    description="Viewed dashboard",
                    extra_data={'page': 'dashboard'}
                )

                return render_template('index.html', dreams=dreams)
        return render_template('index.html')
    except SQLAlchemyError as e:
        logger.error(f"Database error in index route: {str(e)}")
        flash('Unable to load dreams. Please try again later.', 'error')
        return render_template('index.html', dreams=[]), 500
    except Exception as e:
        logger.error(f"Unexpected error in index route: {str(e)}")
        return render_template('index.html', dreams=[]), 500

@dreams_bp.route('/dream/new', methods=['GET', 'POST'])
@login_required
def new_dream():
    """Create a new dream with enhanced validation and error handling."""
    if request.method == 'POST':
        try:
            validate_request_data()  # Validate input data
            
            with session_manager.session_scope() as session:
                dream = Dream(
                    user_id=current_user.id,
                    title=request.form['title'],
                    content=request.form['content'],
                    mood=request.form.get('mood'),
                    tags=request.form.get('tags'),
                    is_public=bool(request.form.get('is_public')),
                    is_anonymous=bool(request.form.get('is_anonymous')),
                    lucidity_level=int(request.form.get('lucidity_level', 0)),
                    sleep_quality=int(request.form.get('sleep_quality', 0)),
                    sleep_position=request.form.get('sleep_position'),
                    sleep_interruptions=int(request.form.get('sleep_interruptions', 0))
                )
                session.add(dream)
                session.flush()

                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['DREAM_CREATE'],
                    target_id=dream.id,
                    description=f"Created new dream: {dream.title}"
                )

                flash('Dream logged successfully!', 'success')
                return redirect(url_for('dreams.view_dream', dream_id=dream.id))

        except ValueError as e:
            logger.warning(f"Invalid input data for new dream: {str(e)}")
            flash('Please check your input values.', 'error')
            return render_template('dream_new.html'), 400
        except SQLAlchemyError as e:
            logger.error(f"Database error creating dream: {str(e)}")
            flash('Unable to save your dream. Please try again later.', 'error')
            return render_template('dream_new.html'), 500
        except Exception as e:
            logger.error(f"Unexpected error creating dream: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('dream_new.html'), 500

    return render_template('dream_new.html')

@dreams_bp.route('/dream/<int:dream_id>')
@login_required
def view_dream(dream_id):
    """View a dream with proper access control and error handling."""
    try:
        with session_manager.session_scope() as session:
            dream = session.query(Dream).get_or_404(dream_id)

            # Access control
            if not dream.is_public and dream.user_id != current_user.id:
                logger.warning(f"Unauthorized access attempt to dream {dream_id} by user {current_user.id}")
                abort(403)

            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_VIEW'],
                target_id=dream_id,
                description=f"Viewed dream: {dream.title}"
            )

            return render_template('dream_view.html', dream=dream)

    except SQLAlchemyError as e:
        logger.error(f"Database error viewing dream {dream_id}: {str(e)}")
        flash('Unable to load the dream. Please try again later.', 'error')
        return redirect(url_for('dreams.index')), 500
    except Exception as e:
        logger.error(f"Unexpected error viewing dream {dream_id}: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('dreams.index')), 500

@dreams_bp.route('/dream/<int:dream_id>/comment', methods=['POST'])
@login_required
def add_comment(dream_id):
    """Add a comment to a dream with proper validation and error handling."""
    try:
        validate_request_data()  # Validate input data
        
        with session_manager.session_scope() as session:
            dream = session.query(Dream).get_or_404(dream_id)

            # Access control
            if not dream.is_public and dream.user_id != current_user.id:
                logger.warning(f"Unauthorized comment attempt on dream {dream_id} by user {current_user.id}")
                abort(403)

            comment = Comment(
                content=request.form['content'],
                user_id=current_user.id,
                dream_id=dream_id
            )
            session.add(comment)
            
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['COMMENT_ADD'],
                target_id=dream_id,
                description=f"Added comment to dream: {dream.title}"
            )

            flash('Comment added successfully!', 'success')
            return redirect(url_for('dreams.view_dream', dream_id=dream_id))

    except SQLAlchemyError as e:
        logger.error(f"Database error adding comment to dream {dream_id}: {str(e)}")
        flash('Unable to add comment. Please try again later.', 'error')
        return redirect(url_for('dreams.view_dream', dream_id=dream_id)), 500
    except Exception as e:
        logger.error(f"Unexpected error adding comment to dream {dream_id}: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('dreams.view_dream', dream_id=dream_id)), 500
