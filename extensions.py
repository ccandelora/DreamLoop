from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text
from sqlalchemy.exc import DisconnectionError, SQLAlchemyError
import time
from flask import current_app

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

def _setup_engine_events(engine):
    """Set up all engine events."""
    
    @event.listens_for(engine, 'connect', insert=True)
    def set_isolation_level(dbapi_connection, connection_record):
        """Set isolation level and other connection parameters."""
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
        try:
            # Verify the connection is still alive
            if not connection_record.connection.is_valid:
                connection_record.connection = connection_record.get_connection()
                logger.info("Replaced invalid connection in pool")
            
            # Ensure proper isolation level
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SHOW transaction_isolation")
                current_level = cursor.fetchone()[0]
                if current_level.lower() != 'repeatable read':
                    cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        except Exception as e:
            logger.error(f"Connection checkout failed: {str(e)}")
            raise DisconnectionError("Invalid connection") from e

    @event.listens_for(engine, 'checkin')
    def connection_checkin(dbapi_connection, connection_record):
        """Clean up connection on checkin back to pool."""
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute("RESET ALL")
            logger.debug("Connection cleaned up on checkin")
        except Exception as e:
            logger.error(f"Connection checkin cleanup failed: {str(e)}")
            raise

    @event.listens_for(engine, 'reset')
    def connection_reset(dbapi_connection, connection_record):
        """Handle connection reset events."""
        try:
            dbapi_connection.rollback()
            logger.debug("Connection state reset")
        except Exception as e:
            logger.error(f"Connection reset failed: {str(e)}")
            raise

    @event.listens_for(engine, 'begin')
    def on_begin(conn):
        """Ensure isolation level is set at the start of each transaction."""
        try:
            conn.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        except Exception as e:
            logger.error(f"Failed to set transaction isolation level: {str(e)}")
            raise

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
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }
    
    db.init_app(app)
    return db

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
