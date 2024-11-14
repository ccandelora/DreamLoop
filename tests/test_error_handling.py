import pytest
from flask import url_for
from models import User, Dream
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

logger = logging.getLogger(__name__)

def test_invalid_dream_access(authenticated_client):
    """Test accessing non-existent dream."""
    try:
        response = authenticated_client.get('/dream/99999')
        assert response.status_code == 404
        assert b'Dream not found' in response.data
    except Exception as e:
        logger.error(f"Error in test_invalid_dream_access: {str(e)}")
        pytest.fail(str(e))

def test_unauthorized_dream_access(_db, authenticated_client, test_user_2, test_dream):
    """Test accessing private dream of another user."""
    try:
        # Make dream private and assign to different user
        test_dream.is_public = False
        test_dream.user_id = test_user_2.id
        _db.session.commit()
        
        response = authenticated_client.get(f'/dream/{test_dream.id}')
        assert response.status_code == 403
        assert b'You do not have permission to view this dream' in response.data
    except SQLAlchemyError as e:
        _db.session.rollback()
        logger.error(f"Database error in test_unauthorized_dream_access: {str(e)}")
        pytest.fail(str(e))

def test_invalid_group_access(authenticated_client):
    """Test accessing non-existent group."""
    try:
        response = authenticated_client.get('/group/99999')
        assert response.status_code == 404
        assert b'Group not found' in response.data
    except Exception as e:
        logger.error(f"Error in test_invalid_group_access: {str(e)}")
        pytest.fail(str(e))

def test_database_error_handling(_db, client, monkeypatch):
    """Test handling of database errors."""
    def mock_db_error(*args, **kwargs):
        raise SQLAlchemyError("Database error")
    
    # Mock the query execution
    monkeypatch.setattr('flask_sqlalchemy._QueryProperty.__get__', mock_db_error)
    
    try:
        response = client.get('/')
        assert response.status_code == 500
        assert b'An error occurred' in response.data
    except Exception as e:
        logger.error(f"Error in test_database_error_handling: {str(e)}")
        pytest.fail(str(e))

def test_form_validation(authenticated_client):
    """Test form validation for dream creation."""
    try:
        # Test empty title
        response = authenticated_client.post('/dream/new', data={
            'title': '',
            'content': 'Test content'
        }, follow_redirects=True)
        assert b'This field is required' in response.data
        
        # Test too long title
        response = authenticated_client.post('/dream/new', data={
            'title': 'a' * 150,
            'content': 'Test content'
        }, follow_redirects=True)
        assert b'Field cannot be longer than 100 characters' in response.data
    except Exception as e:
        logger.error(f"Error in test_form_validation: {str(e)}")
        pytest.fail(str(e))

def test_invalid_json_handling(authenticated_client):
    """Test handling of invalid JSON data."""
    try:
        response = authenticated_client.post('/api/dreams', 
                                        data='invalid json',
                                        content_type='application/json')
        assert response.status_code == 400
        assert b'Invalid JSON data' in response.data
    except Exception as e:
        logger.error(f"Error in test_invalid_json_handling: {str(e)}")
        pytest.fail(str(e))

def test_rate_limiting(_db, client):
    """Test rate limiting for login attempts."""
    try:
        for _ in range(5):
            response = client.post('/login', data={
                'username': 'nonexistent',
                'password': 'wrongpass'
            })
        
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        assert response.status_code == 429
        assert b'Too many login attempts' in response.data
    except Exception as e:
        logger.error(f"Error in test_rate_limiting: {str(e)}")
        pytest.fail(str(e))

def test_duplicate_user_handling(_db):
    """Test handling of duplicate user creation."""
    try:
        # Create first user
        user1 = User(username='testuser', email='test@example.com')
        user1.set_password('password123')
        _db.session.add(user1)
        _db.session.commit()
        
        # Try to create duplicate user
        user2 = User(username='testuser', email='test@example.com')
        user2.set_password('password123')
        _db.session.add(user2)
        
        with pytest.raises(IntegrityError):
            _db.session.commit()
            
    except SQLAlchemyError as e:
        _db.session.rollback()
        logger.error(f"Database error in test_duplicate_user_handling: {str(e)}")
        pytest.fail(str(e))
