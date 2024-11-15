from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import DreamGroup, GroupMembership, ForumPost
from extensions import session_manager
from activity_tracker import track_user_activity, ACTIVITY_TYPES
from middleware import validate_request_data
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups')
@login_required
def index():
    """List all dream groups with proper error handling."""
    try:
        with session_manager.session_scope() as session:
            groups = session.query(DreamGroup).all()
            
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['DREAM_GROUPS_VIEW'],
                description="Viewed dream groups list"
            )

            return render_template('dream_groups.html', groups=groups)

    except SQLAlchemyError as e:
        logger.error(f"Database error listing groups: {str(e)}")
        flash('Unable to load dream groups. Please try again later.', 'error')
        return render_template('dream_groups.html', groups=[]), 500
    except Exception as e:
        logger.error(f"Unexpected error listing groups: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return render_template('dream_groups.html', groups=[]), 500

@groups_bp.route('/groups/new', methods=['GET', 'POST'])
@login_required
def create_group():
    """Create a new dream group with proper validation and error handling."""
    if request.method == 'POST':
        try:
            validate_request_data()
            
            with session_manager.session_scope() as session:
                group = DreamGroup(
                    name=request.form['name'],
                    description=request.form.get('description'),
                    created_by=current_user.id
                )
                session.add(group)
                session.flush()

                # Add creator as member and admin
                membership = GroupMembership(
                    user_id=current_user.id,
                    group_id=group.id,
                    is_admin=True
                )
                session.add(membership)
                
                track_user_activity(
                    current_user.id,
                    ACTIVITY_TYPES['GROUP_CREATE'],
                    target_id=group.id,
                    description=f"Created dream group: {group.name}"
                )

                flash('Dream group created successfully!', 'success')
                return redirect(url_for('groups.view_group', group_id=group.id))

        except SQLAlchemyError as e:
            logger.error(f"Database error creating group: {str(e)}")
            flash('Unable to create group. Please try again later.', 'error')
            return render_template('create_group.html'), 500
        except Exception as e:
            logger.error(f"Unexpected error creating group: {str(e)}")
            flash('An unexpected error occurred.', 'error')
            return render_template('create_group.html'), 500

    return render_template('create_group.html')

@groups_bp.route('/groups/<int:group_id>')
@login_required
def view_group(group_id):
    """View a dream group with proper access control and error handling."""
    try:
        with session_manager.session_scope() as session:
            group = session.query(DreamGroup).get_or_404(group_id)
            
            # Check if user is a member
            is_member = session.query(GroupMembership)\
                .filter_by(user_id=current_user.id, group_id=group_id)\
                .first() is not None

            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['GROUP_VIEW'],
                target_id=group_id,
                description=f"Viewed dream group: {group.name}"
            )

            return render_template('group_detail.html', group=group, is_member=is_member)

    except SQLAlchemyError as e:
        logger.error(f"Database error viewing group {group_id}: {str(e)}")
        flash('Unable to load the group. Please try again later.', 'error')
        return redirect(url_for('groups.index')), 500
    except Exception as e:
        logger.error(f"Unexpected error viewing group {group_id}: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('groups.index')), 500
