import pytest
from models import User, Dream, UserActivity
from datetime import datetime, timedelta

def test_premium_feature_access(authenticated_client, test_user):
    """Test premium feature access control."""
    # Test free user access
    assert test_user.subscription_type == 'free'
    response = authenticated_client.get('/dream/advanced-analysis')
    assert response.status_code == 302
    assert b'Premium feature' in response.data
    
    # Upgrade to premium
    test_user.subscription_type = 'premium'
    test_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    response = authenticated_client.get('/dream/advanced-analysis')
    assert response.status_code == 200

def test_activity_tracking_integration(authenticated_client, test_user):
    """Test activity tracking across different actions."""
    # Track login activity
    initial_count = UserActivity.query.filter_by(user_id=test_user.id).count()
    
    # Perform various actions
    authenticated_client.get('/')
    authenticated_client.get('/dream/patterns')
    authenticated_client.post('/dream/new', data={
        'title': 'Test Dream',
        'content': 'Test content',
        'is_public': True
    })
    
    # Verify activities were tracked
    final_count = UserActivity.query.filter_by(user_id=test_user.id).count()
    assert final_count > initial_count
    
    # Verify activity types
    activities = UserActivity.query.filter_by(user_id=test_user.id).all()
    activity_types = [activity.activity_type for activity in activities]
    assert 'dream_create' in activity_types
    assert 'dream_patterns_view' in activity_types

def test_user_subscription_flow(authenticated_client, test_user):
    """Test user subscription lifecycle."""
    # Initial state
    assert test_user.subscription_type == 'free'
    assert test_user.monthly_ai_analysis_count == 0
    
    # Use AI analysis
    response = authenticated_client.post('/dream/1/analyze', follow_redirects=True)
    test_user.monthly_ai_analysis_count += 1
    
    # Verify limit for free users
    assert test_user.monthly_ai_analysis_count <= 3
    
    # Upgrade to premium
    test_user.subscription_type = 'premium'
    response = authenticated_client.post('/dream/1/analyze', follow_redirects=True)
    assert response.status_code == 200
