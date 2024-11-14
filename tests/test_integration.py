import pytest
from models import User, Dream, UserActivity
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def test_activity_tracking_integration(app, session, authenticated_client, test_user):
    """Test activity tracking across different actions."""
    with app.app_context():
        try:
            # Track initial activity count
            initial_count = session.query(UserActivity).filter_by(user_id=test_user.id).count()
            
            # Create a new dream
            dream_data = {
                'title': 'Integration Test Dream',
                'content': 'Test content',
                'is_public': 'true',  # Changed to string as form data
                'mood': 'happy',
                'tags': 'test,integration',
                'lucidity_level': '3',
                'sleep_quality': '4',
                'sleep_position': 'back'
            }
            response = authenticated_client.post('/dream/new', data=dream_data, follow_redirects=True)
            assert response.status_code == 200
            
            # Verify activities were tracked
            final_count = session.query(UserActivity).filter_by(user_id=test_user.id).count()
            assert final_count > initial_count
            
            # Verify specific activity types
            activities = session.query(UserActivity).filter_by(user_id=test_user.id).all()
            activity_types = [activity.activity_type for activity in activities]
            
            assert any('dream_create' in activity_type.lower() for activity_type in activity_types)
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_activity_tracking_integration: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_premium_feature_access(app, session, authenticated_client, test_user):
    """Test premium feature access control."""
    with app.app_context():
        try:
            # Test free user access to premium route
            response = authenticated_client.get('/dream/patterns')
            assert response.status_code == 200
            assert b'Premium Features' in response.data
            
            # Upgrade to premium
            test_user.subscription_type = 'premium'
            test_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            session.commit()
            
            # Test premium feature access
            response = authenticated_client.get('/dream/patterns')
            assert response.status_code == 200
            assert b'Advanced Dream Analysis' in response.data
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_premium_feature_access: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")

def test_user_subscription_flow(app, session, authenticated_client, test_user, test_dream):
    """Test user subscription lifecycle."""
    with app.app_context():
        try:
            # Initial state verification
            assert test_user.subscription_type == 'free'
            assert test_user.monthly_ai_analysis_count == 0
            
            # Create a dream for analysis
            dream = Dream(
                user_id=test_user.id,
                title='Subscription Test Dream',
                content='Test content for AI analysis',
                is_public=True  # Set is_public during initialization
            )
            session.add(dream)
            session.commit()
            
            # Test free user analysis limit
            for _ in range(3):  # Free tier limit
                response = authenticated_client.post(
                    f'/dream/{dream.id}/analyze', 
                    follow_redirects=True
                )
                assert response.status_code == 200
                session.refresh(test_user)
            
            # Verify limit reached
            assert test_user.monthly_ai_analysis_count == 3
            
            # Upgrade to premium
            test_user.subscription_type = 'premium'
            test_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            session.commit()
            
            # Test premium analysis access
            response = authenticated_client.post(
                f'/dream/{dream.id}/analyze', 
                follow_redirects=True
            )
            assert response.status_code == 200
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in test_user_subscription_flow: {str(e)}")
            pytest.fail(f"Database error: {str(e)}")
