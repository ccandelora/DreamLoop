from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from sqlalchemy.pool import QueuePool
from sqlalchemy import event, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants for database configuration
ISOLATION_LEVEL = 'REPEATABLE READ'
POOL_SIZE = 20
POOL_TIMEOUT = 30
POOL_RECYCLE = 300

# Initialize SQLAlchemy with custom session options
db = SQLAlchemy(engine_options={
    'isolation_level': ISOLATION_LEVEL,
    'pool_size': POOL_SIZE,
    'pool_timeout': POOL_TIMEOUT,
    'pool_recycle': POOL_RECYCLE,
    'pool_pre_ping': True,
    'poolclass': QueuePool,
    'connect_args': {
        'options': f'-c default_transaction_isolation=repeatable read'
    }
})

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# Set up event listeners for database connections
@event.listens_for(db.engine, 'connect', insert=True)
def set_isolation_level(dbapi_connection, connection_record):
    """Set isolation level for each new database connection."""
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    except Exception as e:
        logger.error(f"Failed to set isolation level: {str(e)}")
        raise

@event.listens_for(db.engine, 'begin')
def on_begin(conn):
    """Ensure isolation level is set at the start of each transaction."""
    try:
        conn.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
    except Exception as e:
        logger.error(f"Failed to set transaction isolation level: {str(e)}")
        raise

@event.listens_for(db.engine, 'checkout')
def ensure_isolation_level(dbapi_connection, connection_record, connection_proxy):
    """Verify and maintain isolation level on connection checkout."""
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SHOW transaction_isolation")
            current_level = cursor.fetchone()[0]
            if current_level.lower() != 'repeatable read':
                cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    except Exception as e:
        logger.error(f"Failed to verify isolation level: {str(e)}")
        raise
