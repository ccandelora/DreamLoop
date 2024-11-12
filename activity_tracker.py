from flask import request
from models import UserActivity, db
import logging

logger = logging.getLogger(__name__)

def track_user_activity(user_id, activity_type, description=None, target_type=None, target_id=None):
    """
    Track user activity in the system.
    
    Args:
        user_id: ID of the user performing the action
        activity_type: Type of activity (e.g., 'login', 'dream_create', 'comment_add')
        description: Optional description of the activity
        target_type: Type of the target object (e.g., 'dream', 'comment', 'group')
        target_id: ID of the target object
    """
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            target_type=target_type,
            target_id=target_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        
        db.session.add(activity)
        db.session.commit()
        logger.info(f"Activity tracked: {activity_type} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error tracking activity: {str(e)}")
        db.session.rollback()

# Activity type constants
ACTIVITY_TYPES = {
    'LOGIN': 'login',
    'LOGOUT': 'logout',
    'DREAM_CREATE': 'dream_create',
    'DREAM_UPDATE': 'dream_update',
    'DREAM_DELETE': 'dream_delete',
    'COMMENT_ADD': 'comment_add',
    'COMMENT_DELETE': 'comment_delete',
    'GROUP_JOIN': 'group_join',
    'GROUP_LEAVE': 'group_leave',
    'GROUP_CREATE': 'group_create',
    'POST_CREATE': 'post_create',
    'REPLY_CREATE': 'reply_create',
    'SUBSCRIPTION_CHANGE': 'subscription_change'
}
