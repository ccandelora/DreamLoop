from flask import request, current_app
from models import UserActivity, db
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def track_user_activity(user_id, activity_type, description=None, target_type=None, target_id=None, extra_data=None):
    """
    Enhanced user activity tracking with comprehensive error handling and logging.
    
    Args:
        user_id: ID of the user performing the action
        activity_type: Type of activity (e.g., 'login', 'dream_create', 'comment_add')
        description: Optional description of the activity
        target_type: Type of the target object (e.g., 'dream', 'comment', 'group')
        target_id: ID of the target object
        extra_data: Optional dictionary containing additional activity data
    """
    if not user_id or not activity_type:
        logger.error("Missing required parameters: user_id or activity_type")
        return False, "Missing required parameters"

    try:
        # Prepare activity data
        activity_data = {
            'user_id': user_id,
            'activity_type': activity_type,
            'description': description,
            'target_type': target_type,
            'target_id': target_id,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else None
        }

        # Add any extra data as part of description if provided
        if extra_data:
            if description:
                activity_data['description'] = f"{description} | {str(extra_data)}"
            else:
                activity_data['description'] = str(extra_data)

        # Create and save activity
        activity = UserActivity(**activity_data)
        
        try:
            db.session.add(activity)
            db.session.commit()
            logger.info(f"Activity tracked successfully: {activity_type} for user {user_id}")
            return True, None
        except SQLAlchemyError as dbe:
            db.session.rollback()
            error_msg = f"Database error tracking activity: {str(dbe)}"
            logger.error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error tracking activity: {str(e)}"
        logger.error(error_msg)
        if 'db' in locals() and db.session.is_active:
            db.session.rollback()
        return False, error_msg

def track_premium_feature_usage(user_id, feature_type, success=True):
    """
    Track usage of premium features.
    
    Args:
        user_id: ID of the user using the premium feature
        feature_type: Type of premium feature being used
        success: Whether the feature usage was successful
    """
    description = f"Premium feature usage: {feature_type}"
    if not success:
        description += " (Failed - Non-premium user)"
    
    return track_user_activity(
        user_id=user_id,
        activity_type=ACTIVITY_TYPES['PREMIUM_FEATURE_USE'],
        description=description,
        extra_data={'feature_type': feature_type, 'success': success}
    )

def get_user_activity_summary(user_id, days=30):
    """
    Get summary of user's recent activities.
    
    Args:
        user_id: ID of the user
        days: Number of days to look back
    """
    if not user_id:
        logger.error("Missing required parameter: user_id")
        return None, "Missing user_id parameter"

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= cutoff_date
        ).order_by(UserActivity.created_at.desc()).all()
        
        return activities, None
    except SQLAlchemyError as e:
        error_msg = f"Database error fetching activity summary: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error fetching activity summary: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

# Activity Types Dictionary
ACTIVITY_TYPES = {
    # Authentication activities
    'LOGIN': 'login',
    'LOGOUT': 'logout',
    'REGISTRATION': 'registration',
    'PASSWORD_RESET': 'password_reset',
    'EMAIL_VERIFICATION': 'email_verification',
    
    # Dream-related activities
    'DREAM_CREATE': 'dream_create',
    'DREAM_UPDATE': 'dream_update',
    'DREAM_DELETE': 'dream_delete',
    'DREAM_VIEW': 'dream_view',
    'DREAM_SHARE': 'dream_share',
    'DREAM_PATTERNS_VIEW': 'dream_patterns_view',
    'DREAM_ANALYSIS_VIEW': 'dream_analysis_view',
    'DREAM_COMMENTS_VIEW': 'dream_comments_view',
    'DREAM_EXPORT': 'dream_export',
    
    # Comment activities
    'COMMENT_ADD': 'comment_add',
    'COMMENT_DELETE': 'comment_delete',
    'COMMENT_UPDATE': 'comment_update',
    'COMMENT_VIEW': 'comment_view',
    
    # Group activities
    'GROUP_CREATE': 'group_create',
    'GROUP_JOIN': 'group_join',
    'GROUP_LEAVE': 'group_leave',
    'GROUP_UPDATE': 'group_update',
    'GROUP_DELETE': 'group_delete',
    'GROUP_VIEW': 'group_view',
    'DREAM_GROUPS_VIEW': 'dream_groups_view',
    'GROUP_INVITE': 'group_invite',
    
    # Community activities
    'COMMUNITY_DREAMS_VIEW': 'community_dreams_view',
    'COMMUNITY_INTERACTION': 'community_interaction',
    
    # Forum activities
    'FORUM_POST_CREATE': 'forum_post_create',
    'FORUM_POST_UPDATE': 'forum_post_update',
    'FORUM_POST_DELETE': 'forum_post_delete',
    'FORUM_REPLY': 'forum_reply',
    'FORUM_POST_VIEW': 'forum_post_view',
    'FORUM_VIEW': 'forum_view',
    
    # Premium features
    'PREMIUM_FEATURE_USE': 'premium_feature_use',
    'AI_ANALYSIS_USE': 'ai_analysis_use',
    'ADVANCED_ANALYTICS_VIEW': 'advanced_analytics_view',
    
    # Subscription activities
    'SUBSCRIPTION_VIEW': 'subscription_view',
    'SUBSCRIPTION_PURCHASE': 'subscription_purchase',
    'SUBSCRIPTION_CANCEL': 'subscription_cancel',
    'SUBSCRIPTION_CHANGE': 'subscription_change',
    'PAYMENT_PROCESS': 'payment_process',
    
    # Profile activities
    'PROFILE_UPDATE': 'profile_update',
    'SETTINGS_CHANGE': 'settings_change',
    'PREFERENCES_UPDATE': 'preferences_update',
    
    # Data management
    'DATA_EXPORT': 'data_export',
    'DATA_IMPORT': 'data_import',
    'BACKUP_CREATE': 'backup_create',
    'BACKUP_RESTORE': 'backup_restore'
}
