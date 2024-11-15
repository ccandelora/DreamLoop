from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import ForumPost, ForumReply, DreamGroup
from extensions import session_manager
from activity_tracker import track_user_activity, ACTIVITY_TYPES
from middleware import validate_request_data
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/forum/post/<int:post_id>')
@login_required
def view_post(post_id):
    """View a forum post with proper access control and error handling."""
    try:
        with session_manager.session_scope() as session:
            post = session.query(ForumPost).get_or_404(post_id)
            
            # Check if user is a member of the group
            membership = session.query(DreamGroup)\
                .filter(DreamGroup.id == post.group_id)\
                .filter(DreamGroup.members.any(id=current_user.id))\
                .first()
                
            if not membership:
                logger.warning(f"Unauthorized access attempt to forum post {post_id} by user {current_user.id}")
                abort(403)

            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['FORUM_POST_VIEW'],
                target_id=post_id,
                description=f"Viewed forum post: {post.title}"
            )

            return render_template('forum_post.html', post=post, is_member=True)

    except SQLAlchemyError as e:
        logger.error(f"Database error viewing forum post {post_id}: {str(e)}")
        flash('Unable to load the forum post. Please try again later.', 'error')
        return redirect(url_for('groups.view_group', group_id=post.group_id)), 500
    except Exception as e:
        logger.error(f"Unexpected error viewing forum post {post_id}: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('groups.index')), 500

@forum_bp.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def add_reply(post_id):
    """Add a reply to a forum post with proper validation and error handling."""
    try:
        validate_request_data()
        
        with session_manager.session_scope() as session:
            post = session.query(ForumPost).get_or_404(post_id)
            
            # Check if user is a member of the group
            membership = session.query(DreamGroup)\
                .filter(DreamGroup.id == post.group_id)\
                .filter(DreamGroup.members.any(id=current_user.id))\
                .first()
                
            if not membership:
                logger.warning(f"Unauthorized reply attempt to forum post {post_id} by user {current_user.id}")
                abort(403)

            reply = ForumReply(
                content=request.form['content'],
                user_id=current_user.id,
                post_id=post_id
            )
            session.add(reply)
            
            track_user_activity(
                current_user.id,
                ACTIVITY_TYPES['FORUM_REPLY'],
                target_id=post_id,
                description=f"Added reply to forum post: {post.title}"
            )

            flash('Reply added successfully!', 'success')
            return redirect(url_for('forum.view_post', post_id=post_id))

    except SQLAlchemyError as e:
        logger.error(f"Database error adding reply to forum post {post_id}: {str(e)}")
        flash('Unable to add reply. Please try again later.', 'error')
        return redirect(url_for('forum.view_post', post_id=post_id)), 500
    except Exception as e:
        logger.error(f"Unexpected error adding reply to forum post {post_id}: {str(e)}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('forum.view_post', post_id=post_id)), 500
