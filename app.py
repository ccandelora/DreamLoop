from flask import Flask
import os
from extensions import db, login_manager
from sqlalchemy.exc import SQLAlchemyError
from logging_config import setup_logging, ErrorLogger
from middleware import setup_request_logging


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
        raise ValueError("DATABASE_URL environment variable is not set")

    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 10,
        'echo': True  # Enable SQL query logging in development
    }

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Setup request logging
    #setup_request_logging(app)

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
            db.session.rollback()
            return None

    # Import and register routes
    with app.app_context():
        try:
            # Initialize database
            db.create_all()
            app.logger.info("Database tables created successfully")

            # Register routes after db initialization
            from routes import register_routes
            register_routes(app)
            app.logger.info("Routes registered successfully")
        except SQLAlchemyError as e:
            error_details = ErrorLogger.log_error(e)
            db.session.rollback()
            raise

    return app


# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
