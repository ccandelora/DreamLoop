from flask_migrate import Migrate
from app import create_app
from extensions import db
import os
import logging

logger = logging.getLogger(__name__)

def init_migrations(app=None):
    """Initialize database migrations."""
    if app is None:
        app = create_app()
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    return app, migrate

if __name__ == "__main__":
    app, migrate = init_migrations()
    with app.app_context():
        try:
            # This will create the migrations directory if it doesn't exist
            os.system('flask db init')
            logger.info("Migrations initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing migrations: {str(e)}")
            raise
