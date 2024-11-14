from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError
from sqlalchemy.orm import scoped_session, sessionmaker
import time
from flask import current_app, g
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants for database configuration
ISOLATION_LEVEL = 'REPEATABLE READ'
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
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

class SQLAlchemySessionManager:
    """Session manager for SQLAlchemy."""
    
    def __init__(self, db):
        self.db = db
        self._session_factory = None
        self._scoped_session = None
    
    def init_session_factory(self, app):
        """Initialize the session factory with application context."""
        if not self._session_factory:
            self._session_factory = sessionmaker(
                bind=self.db.engine,
                expire_on_commit=False
            )
            self._scoped_session = scoped_session(
                self._session_factory,
                scopefunc=lambda: id(current_app.app_context()) if current_app else None
            )
    
    def cleanup_sessions(self):
        """Clean up all sessions."""
        if self._scoped_session:
            try:
                if hasattr(g, 'db_session'):
                    try:
                        if g.db_session.is_active:
                            g.db_session.rollback()
                        g.db_session.close()
                    except Exception as e:
                        logger.error(f"Error cleaning up request session: {str(e)}")
                self._scoped_session.remove()
                logger.debug("All sessions cleaned up")
            except Exception as e:
                logger.error(f"Error during session cleanup: {str(e)}")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        if not self._scoped_session:
            raise RuntimeError("Session factory not initialized. Call init_session_factory first.")
            
        session = self._scoped_session()
        try:
            yield session
            if session.is_active:
                session.commit()
        except Exception as e:
            if session.is_active:
                session.rollback()
            logger.error(f"Session operation failed: {str(e)}")
            raise
        finally:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Error closing session: {str(e)}")

    def get_session(self):
        """Get the current scoped session."""
        if not self._scoped_session:
            raise RuntimeError("Session factory not initialized. Call init_session_factory first.")
        return self._scoped_session()

    def remove_session(self):
        """Safely remove the current session."""
        if self._scoped_session:
            try:
                self._scoped_session.remove()
                return True
            except Exception as e:
                logger.error(f"Error removing session: {str(e)}")
                return False
        return False

session_manager = SQLAlchemySessionManager(db)

def init_db_pool(app):
    """Initialize database pool with application context."""
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'isolation_level': ISOLATION_LEVEL,
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
    
    # Initialize database first
    db.init_app(app)
    
    # Initialize session factory within app context
    with app.app_context():
        session_manager.init_session_factory(app)
        _setup_engine_events(db.engine)
    
    return db

def _setup_engine_events(engine):
    """Set up all engine events."""
    
    @event.listens_for(engine, 'connect', insert=True)
    def set_isolation_level(dbapi_connection, connection_record):
        """Set isolation level and other connection parameters."""
        if dbapi_connection is None:
            return
            
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                cursor.execute("SET statement_timeout = '30s'")
                cursor.execute("SET idle_in_transaction_session_timeout = '60s'")
        except Exception as e:
            logger.error(f"Failed to set connection parameters: {str(e)}")
            raise

    @event.listens_for(engine, 'checkout')
    def connection_checkout(dbapi_connection, connection_record, connection_proxy):
        """Verify connection health on checkout from pool."""
        if dbapi_connection is None:
            raise DisconnectionError("Received null connection on checkout")
            
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SELECT 1")  # Simple connection test
        except Exception as e:
            logger.error(f"Connection checkout failed: {str(e)}")
            raise DisconnectionError("Invalid connection") from e

    @event.listens_for(engine, 'checkin')
    def connection_checkin(dbapi_connection, connection_record):
        """Clean up connection on checkin back to pool."""
        if dbapi_connection is None:
            logger.warning("Received null connection on checkin")
            return
            
        try:
            if not connection_record.connection.closed:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("RESET ALL")
                logger.debug("Connection cleaned up on checkin")
        except Exception as e:
            logger.error(f"Connection checkin cleanup failed: {str(e)}")

def get_db_session():
    """Get a database session from the scoped session."""
    return session_manager.get_session()

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
