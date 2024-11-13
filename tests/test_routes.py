import pytest
from flask import url_for
from flask_login import current_user
from models import User, Dream, Comment, DreamGroup, ForumPost

def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'DreamShare' in response.data

def test_login_route(client, test_user):
    """Test login functionality."""
    # Test GET request
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    
    # Test successful login
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' not in response.data
    
    # Test invalid credentials
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_register_route(client):
    """Test registration functionality."""
    # Test GET request
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data
    
    # Test successful registration
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Test duplicate username
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'another@example.com',
        'password': 'anotherpass'
    }, follow_redirects=True)
    assert b'Username already exists' in response.data

def test_dream_creation(authenticated_client, test_user):
    """Test dream creation functionality."""
    response = authenticated_client.post('/dream/new', data={
        'title': 'New Dream',
        'content': 'Dream content',
        'is_public': True,
        'mood': 'happy',
        'tags': 'test,dream',
        'lucidity_level': '3'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dream logged successfully!' in response.data

def test_dream_viewing(authenticated_client, test_dream):
    """Test dream viewing functionality."""
    response = authenticated_client.get(f'/dream/{test_dream.id}')
    assert response.status_code == 200
    assert test_dream.title.encode() in response.data

def test_dream_patterns(authenticated_client):
    """Test dream patterns page."""
    response = authenticated_client.get('/dream/patterns')
    assert response.status_code == 200
    assert b'Dream Patterns' in response.data

def test_comment_creation(authenticated_client, test_dream):
    """Test comment creation functionality."""
    response = authenticated_client.post(f'/dream/{test_dream.id}/comment', data={
        'content': 'Test comment'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Comment added successfully!' in response.data

def test_group_creation(authenticated_client):
    """Test group creation functionality."""
    response = authenticated_client.post('/group/new', data={
        'name': 'New Group',
        'description': 'Test description'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_protected_routes(client):
    """Test routes that require authentication."""
    protected_routes = [
        '/dream/new',
        '/dream/patterns',
        '/groups',
        '/community'
    ]
    
    for route in protected_routes:
        response = client.get(route, follow_redirects=True)
        assert b'Please log in to access this page' in response.data

def test_logout(authenticated_client):
    """Test logout functionality."""
    response = authenticated_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data
