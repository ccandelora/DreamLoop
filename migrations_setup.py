from flask import Flask
import os
import logging
from flask_migrate import Migrate
from extensions import db
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create a minimal Flask app for database initialization."""
    app = Flask(__name__)
    
    # Configure database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 10
    }
    
    # Initialize database
    db.init_app(app)
    
    return app

def setup_migrations():
    """Set up fresh migrations for the database."""
    try:
        # Create Flask app
        app = create_app()
        
        # Clean up existing migrations directory if it exists
        migrations_dir = Path(__file__).parent / 'migrations'
        if migrations_dir.exists():
            logger.info("Removing existing migrations directory")
            shutil.rmtree(migrations_dir)
        
        with app.app_context():
            # Import models to ensure they are registered with SQLAlchemy
            from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply, UserActivity
            
            # Drop existing tables and alembic version if they exist
            logger.info("Dropping existing tables")
            tables = [
                'forum_reply', 'forum_post', 'comment', 'user_activity',
                'group_membership', 'dream', 'dream_group', 'user', 'alembic_version'
            ]
            
            # Use raw connection for schema operations
            connection = db.engine.raw_connection()
            try:
                connection.autocommit = True
                cursor = connection.cursor()
                
                # Drop tables in reverse order to handle dependencies
                for table in tables:
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                        logger.info(f"Dropped table {table}")
                    except Exception as e:
                        logger.warning(f"Error dropping table {table}: {str(e)}")
                
            finally:
                cursor.close()
                connection.close()
            
            # Initialize Flask-Migrate
            migrate = Migrate(app, db)
            
            # Set FLASK_APP environment variable
            os.environ['FLASK_APP'] = 'app.py'
            
            try:
                # Initialize migrations directory
                logger.info("Initializing migrations directory")
                os.system('flask db init')
                
                # Create initial migration
                logger.info("Creating initial migration")
                os.system('flask db migrate -m "initial schema"')
                
                # Apply migration
                logger.info("Applying migrations")
                os.system('flask db upgrade')
                
                # Verify migration was applied
                connection = db.engine.raw_connection()
                try:
                    connection.autocommit = True
                    cursor = connection.cursor()
                    cursor.execute('SELECT version_num FROM alembic_version')
                    result = cursor.fetchone()
                    if result:
                        logger.info(f"Migration version {result[0]} applied successfully")
                        return True
                    logger.error("No migration version found after upgrade")
                    return False
                finally:
                    cursor.close()
                    connection.close()
                
            except Exception as e:
                logger.error(f"Error during migration process: {str(e)}")
                return False
            
    except Exception as e:
        logger.error(f"Error setting up migrations: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_migrations()
    if not success:
        exit(1)
