import pytest
from datetime import datetime, timedelta
from models import User, Dream, Comment, DreamGroup, UserActivity

def create_test_dream(user, **kwargs):
    """Helper function to create a test dream with default values."""
    default_data = {
        'title': 'Test Dream',
        'content': 'Test dream content',
        'mood': 'happy',
        'is_public': True,
        'tags': 'test,dream',
        'date': datetime.utcnow()
    }
    default_data.update(kwargs)
    return Dream(user_id=user.id, **default_data)

def create_test_activity(user, activity_type, **kwargs):
    """Helper function to create a test activity."""
    default_data = {
        'description': 'Test activity',
        'created_at': datetime.utcnow()
    }
    default_data.update(kwargs)
    return UserActivity(user_id=user.id, activity_type=activity_type, **default_data)

def verify_dream_data(dream, expected_data):
    """Helper function to verify dream data."""
    for key, value in expected_data.items():
        assert getattr(dream, key) == value

def cleanup_test_data(db_session):
    """Helper function to clean up test data."""
    models = [UserActivity, Comment, Dream, DreamGroup, User]
    for model in models:
        db_session.query(model).delete()
    db_session.commit()
