import pytest
from app import create_app
from extensions import db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from datetime import datetime
import os

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application."""
    # Use a separate test database
    if not os.environ.get('DATABASE_URL'):
        raise ValueError("DATABASE_URL environment variable is not set")
        
    test_db_url = os.environ.get('DATABASE_URL').replace('dreamshare', 'dreamshare_test')
    os.environ['TEST_DATABASE_URL'] = test_db_url
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': test_db_url,
        'SERVER_NAME': 'localhost.localdomain'
    })
    
    yield app
    
    # Clean up after all tests
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def setup_database(app):
    """Set up fresh database tables before each test."""
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        yield
        # Clean up after test
        db.session.remove()

@pytest.fixture
def client(app):
    """Test client for the Flask application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test CLI runner for the Flask application."""
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_user_2(app):
    """Create a second test user."""
    with app.app_context():
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('testpass2')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_dream(app, test_user):
    """Create a test dream."""
    with app.app_context():
        dream = Dream(
            user_id=test_user.id,
            title='Test Dream',
            content='Test dream content',
            date=datetime.utcnow(),
            mood='happy',
            tags='test,dream',
            is_public=True,
            lucidity_level=3,
            sleep_quality=4,
            sleep_position='back'
        )
        db.session.add(dream)
        db.session.commit()
        return dream

@pytest.fixture
def test_comment(app, test_user, test_dream):
    """Create a test comment."""
    with app.app_context():
        comment = Comment(
            content='Test comment',
            user_id=test_user.id,
            dream_id=test_dream.id,
            created_at=datetime.utcnow()
        )
        db.session.add(comment)
        db.session.commit()
        return comment

@pytest.fixture
def test_group(app, test_user):
    """Create a test dream group."""
    with app.app_context():
        group = DreamGroup(
            name='Test Group',
            description='Test description',
            created_by=test_user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(group)
        db.session.commit()
        
        membership = GroupMembership(
            user_id=test_user.id,
            group_id=group.id,
            is_admin=True,
            joined_at=datetime.utcnow()
        )
        db.session.add(membership)
        db.session.commit()
        return group

@pytest.fixture
def test_forum_post(app, test_user, test_group):
    """Create a test forum post."""
    with app.app_context():
        post = ForumPost(
            title='Test Post',
            content='Test content',
            user_id=test_user.id,
            group_id=test_group.id,
            created_at=datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()
        return post

@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated client session."""
    with client.session_transaction() as session:
        session['_user_id'] = str(test_user.id)
    return client
