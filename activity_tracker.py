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
    # Authentication activities
    'LOGIN': 'login',
    'LOGOUT': 'logout',
    'REGISTRATION': 'registration',
    
    # Dream-related activities
    'DREAM_CREATE': 'dream_create',
    'DREAM_UPDATE': 'dream_update',
    'DREAM_DELETE': 'dream_delete',
    'DREAM_VIEW': 'dream_view',
    'DREAM_PATTERNS_VIEW': 'dream_patterns_view',
    
    # Comment activities
    'COMMENT_ADD': 'comment_add',
    'COMMENT_DELETE': 'comment_delete',
    
    # Group activities
    'GROUP_JOIN': 'group_join',
    'GROUP_JOIN_ATTEMPT': 'group_join_attempt',
    'GROUP_LEAVE': 'group_leave',
    'GROUP_LEAVE_ATTEMPT': 'group_leave_attempt',
    'GROUP_CREATE': 'group_create',
    'GROUP_VIEW': 'group_view',
    'DREAM_GROUPS_VIEW': 'dream_groups_view',
    
    # Community activities
    'COMMUNITY_DREAMS_VIEW': 'community_dreams_view',
    
    # Forum activities
    'FORUM_POST_CREATE': 'forum_post_create',
    'FORUM_POST_CREATE_ATTEMPT': 'forum_post_create_attempt',
    'FORUM_REPLY': 'forum_reply',
    'FORUM_REPLY_ATTEMPT': 'forum_reply_attempt',
    'FORUM_POST_VIEW': 'forum_post_view',
    'FORUM_VIEW': 'forum_view',
    
    # Subscription activities
    'SUBSCRIPTION_VIEW': 'subscription_view',
    'SUBSCRIPTION_PURCHASE_ATTEMPT': 'subscription_purchase_attempt',
    'SUBSCRIPTION_CANCEL_ATTEMPT': 'subscription_cancel_attempt',
    'SUBSCRIPTION_CHANGE': 'subscription_change'
}
