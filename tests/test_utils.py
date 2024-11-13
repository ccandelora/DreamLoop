import pytest
from activity_tracker import track_user_activity, track_premium_feature_usage, ACTIVITY_TYPES
from logging_config import ErrorLogger
from datetime import datetime
from flask import request

def test_activity_tracking(app, test_user):
    """Test user activity tracking."""
    with app.app_context():
        # Test basic activity tracking
        success, error = track_user_activity(
            test_user.id,
            ACTIVITY_TYPES['LOGIN'],
            description="Test login"
        )
        assert success is True
        assert error is None

        # Test activity tracking with target
        success, error = track_user_activity(
            test_user.id,
            ACTIVITY_TYPES['DREAM_CREATE'],
            description="Created new dream",
            target_type="dream",
            target_id=1
        )
        assert success is True
        assert error is None

def test_premium_feature_tracking(app, test_user):
    """Test premium feature usage tracking."""
    with app.app_context():
        # Test successful premium feature usage
        success, error = track_premium_feature_usage(
            test_user.id,
            "ai_analysis",
            success=True
        )
        assert success is True
        assert error is None

        # Test failed premium feature usage
        success, error = track_premium_feature_usage(
            test_user.id,
            "ai_analysis",
            success=False
        )
        assert success is True
        assert error is None

def test_error_logging(app):
    """Test error logging functionality."""
    with app.app_context():
        # Test basic error logging
        test_error = ValueError("Test error")
        error_details = ErrorLogger.log_error(
            test_error,
            context={'test': 'context'}
        )
        assert error_details['error_type'] == 'ValueError'
        assert error_details['error_message'] == 'Test error'
        assert error_details['context'] == {'test': 'context'}

        # Test error logging with additional context
        complex_error = Exception("Complex error")
        error_details = ErrorLogger.log_error(
            complex_error,
            context={
                'user_id': 1,
                'action': 'test_action',
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        assert error_details['error_type'] == 'Exception'
        assert error_details['error_message'] == 'Complex error'
        assert 'user_id' in error_details['context']
        assert 'action' in error_details['context']
        assert 'timestamp' in error_details['context']

def test_activity_types_consistency():
    """Test activity types constant."""
    # Verify essential activity types exist
    essential_types = [
        'LOGIN', 'LOGOUT', 'REGISTRATION',
        'DREAM_CREATE', 'DREAM_UPDATE', 'DREAM_DELETE',
        'COMMENT_ADD', 'GROUP_CREATE', 'FORUM_POST_CREATE'
    ]
    
    for activity_type in essential_types:
        assert activity_type in ACTIVITY_TYPES
        assert isinstance(ACTIVITY_TYPES[activity_type], str)
        assert len(ACTIVITY_TYPES[activity_type]) > 0
