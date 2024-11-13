import pytest
from flask import url_for
from models import User, Dream

def test_invalid_dream_access(authenticated_client):
    """Test accessing non-existent dream."""
    response = authenticated_client.get('/dream/99999')
    assert response.status_code == 404

def test_unauthorized_dream_access(authenticated_client, test_user_2, test_dream):
    """Test accessing private dream of another user."""
    # Make dream private
    test_dream.is_public = False
    test_dream.user_id = test_user_2.id
    
    response = authenticated_client.get(f'/dream/{test_dream.id}')
    assert response.status_code == 302
    assert b'You do not have permission to view this dream' in response.data

def test_invalid_group_access(authenticated_client):
    """Test accessing non-existent group."""
    response = authenticated_client.get('/group/99999')
    assert response.status_code == 404

def test_database_error_handling(client, monkeypatch):
    """Test handling of database errors."""
    def mock_db_error(*args, **kwargs):
        raise Exception("Database error")
    
    monkeypatch.setattr('flask_sqlalchemy._QueryProperty.__get__', mock_db_error)
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Error' in response.data

def test_form_validation(authenticated_client):
    """Test form validation for dream creation."""
    # Test empty title
    response = authenticated_client.post('/dream/new', data={
        'title': '',
        'content': 'Test content'
    }, follow_redirects=True)
    assert b'This field is required' in response.data
    
    # Test too long title
    response = authenticated_client.post('/dream/new', data={
        'title': 'a' * 150,  # Title longer than 100 chars
        'content': 'Test content'
    }, follow_redirects=True)
    assert b'error' in response.data.lower()
