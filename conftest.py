import pytest
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
import logging
import os
from app import create_app, db as _db
from models import User, Dream, DreamGroup, ForumPost, UserActivity
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from urllib.parse import urlparse, urlunparse
from extensions import ISOLATION_LEVEL

logger = logging.getLogger(__name__)

def create_test_database(db_url):
    """Create a test database if it doesn't exist."""
    try:
        parsed = urlparse(db_url)
        base_db_name = parsed.path.strip('/')
        test_db_name = f"{base_db_name}_test" if not base_db_name.endswith('_test') else base_db_name

        # Connect to default database for admin operations
        admin_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            '/postgres',
            '',
            parsed.query,
            ''
        ))

        engine = create_engine(admin_url)
        
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            
            # Check if database exists
            result = conn.execute(text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            ), {"db_name": test_db_name})
            
            if not result.scalar():
                try:
                    conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
                    logger.info(f"Created test database: {test_db_name}")
                except Exception as e:
                    logger.error(f"Error creating database {test_db_name}: {str(e)}")
                    raise

        # Return complete test database URL
        test_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            f'/{test_db_name}',
            '',
            parsed.query,
            ''
        ))
        return test_url

    except Exception as e:
        logger.error(f"Error creating test database: {str(e)}")
        raise

def reset_db_state(session):
    """Reset database state between tests."""
    try:
        # Get all tables
        result = session.execute(text("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        tables = [row[0] for row in result]
        
        # Disable triggers temporarily
        session.execute(text("SET session_replication_role = 'replica'"))
        
        # Truncate all tables
        for table in tables:
            session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
        
        # Reset sequences
        result = session.execute(text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """))
        sequences = [row[0] for row in result]
        
        for sequence in sequences:
            try:
                session.execute(text(f'ALTER SEQUENCE "{sequence}" RESTART WITH 1'))
            except Exception as e:
                logger.warning(f"Could not reset sequence {sequence}: {str(e)}")
        
        # Re-enable triggers
        session.execute(text("SET session_replication_role = 'origin'"))
        session.commit()
    
    except Exception as e:
        logger.error(f"Error resetting database state: {str(e)}")
        session.rollback()
        raise

def verify_db_schema(db):
    """Verify database schema integrity."""
    try:
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        
        required_tables = {
            'user', 'dream', 'comment', 'dream_group', 'group_membership',
            'forum_post', 'forum_reply', 'user_activity'
        }
        
        missing_tables = required_tables - existing_tables
        if missing_tables:
            raise Exception(f"Missing required tables: {missing_tables}")
        
        logger.info("Database schema verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {str(e)}")
        raise

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application."""
    try:
        # Get database URL and ensure proper format
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
        
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        # Create test database
        test_db_url = create_test_database(db_url)
        
        # Create and configure app
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': test_db_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'WTF_CSRF_ENABLED': False,
            'SERVER_NAME': 'localhost.localdomain'
        })
        
        return app
        
    except Exception as e:
        logger.error(f"Error creating test application: {str(e)}")
        raise

@pytest.fixture(scope='session')
def db(app):
    """Session-wide test database."""
    with app.app_context():
        try:
            _db.drop_all()
            _db.create_all()
            verify_db_schema(_db)
            yield _db
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
        finally:
            _db.session.remove()
            _db.drop_all()

@pytest.fixture(scope='function')
def session(app, db):
    """Create a new database session for each test."""
    # Configure session factory with proper isolation level
    session_factory = sessionmaker(
        bind=db.engine,
        expire_on_commit=False,
    )
    
    # Create a scoped session
    Session = scoped_session(session_factory)
    
    # Create new session
    session = Session()
    
    try:
        # Set isolation level for this session
        session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {ISOLATION_LEVEL}"))
        session.commit()
        
        # Reset database state
        reset_db_state(session)
        
        # Make session available to app
        db.session = session
        
        yield session
        
    except Exception as e:
        logger.error(f"Error in test session: {str(e)}")
        session.rollback()
        raise
    finally:
        # Clean up session
        session.rollback()
        Session.remove()
        session.close()

@pytest.fixture(scope='function')
def test_user(session):
    """Create a test user."""
    try:
        user = User(
            username='testuser',
            email='test@example.com',
            subscription_type='free'
        )
        user.set_password('testpass')
        session.add(user)
        session.commit()
        return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating test user: {str(e)}")
        raise

@pytest.fixture(scope='function')
def test_user_2(session):
    """Create a second test user."""
    try:
        user = User(
            username='testuser2',
            email='test2@example.com',
            subscription_type='free'
        )
        user.set_password('testpass2')
        session.add(user)
        session.commit()
        return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating test user: {str(e)}")
        raise

@pytest.fixture(scope='function')
def test_dream(session, test_user):
    """Create a test dream."""
    try:
        dream = Dream(
            user_id=test_user.id,
            title='Test Dream',
            content='Test dream content',
            is_public=True
        )
        dream.date = datetime.utcnow()
        dream.mood = 'happy'
        dream.tags = 'test,dream'
        dream.lucidity_level = 3
        session.add(dream)
        session.commit()
        return dream
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating test dream: {str(e)}")
        raise

@pytest.fixture(scope='function')
def test_group(session, test_user):
    """Create a test dream group."""
    try:
        group = DreamGroup(
            name='Test Group',
            description='Test group description',
            created_by=test_user.id
        )
        session.add(group)
        session.commit()
        return group
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating test group: {str(e)}")
        raise

@pytest.fixture(scope='function')
def test_forum_post(session, test_user, test_group):
    """Create a test forum post."""
    try:
        post = ForumPost(
            title='Test Post',
            content='Test post content',
            user_id=test_user.id,
            group_id=test_group.id
        )
        session.add(post)
        session.commit()
        return post
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error creating test forum post: {str(e)}")
        raise

@pytest.fixture(scope='function')
def client(app):
    """Test client for the Flask application."""
    return app.test_client()

@pytest.fixture(scope='function')
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    with client:
        response = client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass'
        }, follow_redirects=True)
        if response.status_code != 200 or b'Invalid username or password' in response.data:
            raise Exception("Failed to authenticate test client")
        yield client