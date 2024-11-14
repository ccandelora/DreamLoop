from flask import Flask
import os
from extensions import db, login_manager, init_db_pool
from sqlalchemy.exc import SQLAlchemyError
from logging_config import setup_logging, ErrorLogger
from middleware import setup_request_logging
from flask_login import current_user
from datetime import datetime

def should_show_premium_ads():
    """Determine if premium ads should be shown to the current user."""
    if not current_user or not current_user.is_authenticated:
        return True
    return current_user.subscription_type == 'free'

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Setup logging first
    setup_logging(app)

    # Configure the Flask app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

    # Configure database URL using environment variables
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"

    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Setup request logging with session cleanup
    setup_request_logging(app)

    # Initialize extensions
    login_manager.init_app(app)
    
    # Initialize database with connection pooling
    with app.app_context():
        init_db_pool(app)

        try:
            # Initialize database tables
            db.create_all()
            app.logger.info("Database tables created successfully")

            # Import and register routes
            from routes import register_routes
            register_routes(app)
            app.logger.info("Routes registered successfully")

        except SQLAlchemyError as e:
            error_details = ErrorLogger.log_error(e)
            raise

    # Add template context processor
    @app.context_processor
    def utility_processor():
        return {
            'should_show_premium_ads': should_show_premium_ads
        }

    # Import models and set up user loader
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        try:
            return User.query.get(int(user_id))
        except SQLAlchemyError as e:
            ErrorLogger.log_error(e, {'user_id': user_id})
            return None

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
