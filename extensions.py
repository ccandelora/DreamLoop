from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
import time
from flask import current_app
import psycopg2
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants for database configuration
POOL_SIZE = 20
MAX_OVERFLOW = 10
POOL_TIMEOUT = 30
POOL_RECYCLE = 300
POOL_PRE_PING = True
MAX_RETRIES = 3
RETRY_INTERVAL = 1

# Initialize SQLAlchemy without immediate engine binding
db = SQLAlchemy()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

class SessionManager:
    def __init__(self):
        self._session = None

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = db.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

session_manager = SessionManager()

def configure_connection_settings(dbapi_connection):
    """Configure connection parameters outside of any transaction."""
    if not isinstance(dbapi_connection, psycopg2.extensions.connection):
        logger.error("Invalid connection type")
        return False
        
    try:
        cursor = dbapi_connection.cursor()
        try:
            # Configure only timezone
            cursor.execute("SET timezone = 'UTC'")
            logger.info("Connection parameters configured successfully")
            return True
        except Exception as e:
            logger.error(f"Error executing connection configuration: {str(e)}")
            return False
        finally:
            cursor.close()
    except Exception as e:
        logger.error(f"Failed to configure connection parameters: {str(e)}")
        return False

def init_db_pool(app):
    """Initialize database pool with application context."""
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': POOL_SIZE,
        'max_overflow': MAX_OVERFLOW,
        'pool_timeout': POOL_TIMEOUT,
        'pool_recycle': POOL_RECYCLE,
        'pool_pre_ping': POOL_PRE_PING,
        'poolclass': QueuePool,
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'DreamShare',
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }
    
    # Initialize database
    db.init_app(app)
    
    # Set up engine events
    _setup_engine_events(db.engine)
    
    return db

def _setup_engine_events(engine):
    """Set up all engine events."""
    
    @event.listens_for(engine, 'connect')
    def on_connect(dbapi_connection, connection_record):
        """Configure connection on connect."""
        success = configure_connection_settings(dbapi_connection)
        if not success:
            logger.error("Failed to configure connection settings")
            raise DisconnectionError("Could not configure connection")

    @event.listens_for(engine, 'checkout')
    def connection_checkout(dbapi_connection, connection_record, connection_proxy):
        """Verify connection health on checkout from pool."""
        if dbapi_connection is None:
            raise DisconnectionError("Received null connection on checkout")
        try:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            finally:
                cursor.close()
        except Exception as e:
            logger.error(f"Connection checkout failed: {str(e)}")
            raise DisconnectionError("Invalid connection") from e

def get_db_connection(retries=MAX_RETRIES):
    """Get a database connection with retry logic."""
    for attempt in range(retries):
        try:
            return db.engine.connect()
        except SQLAlchemyError as e:
            if attempt == retries - 1:
                logger.error(f"Failed to get database connection after {retries} attempts: {str(e)}")
                raise
            time.sleep(RETRY_INTERVAL)
