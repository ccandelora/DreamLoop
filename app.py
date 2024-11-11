from flask import Flask
import markdown
import os
from extensions import db, login_manager
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
import logging
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure the Flask app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 5
    }

    # Initialize extensions with app context
    with app.app_context():
        db.init_app(app)
        login_manager.init_app(app)

        # Configure login manager
        login_manager.login_view = 'login'
        login_manager.login_message = 'Please log in to access this page.'
        login_manager.login_message_category = 'info'
        login_manager.session_protection = 'strong'

        # Add markdown filter
        def markdown_filter(text):
            return markdown.markdown(text) if text else ''
        app.jinja_env.filters['markdown'] = markdown_filter

        @login_manager.user_loader
        def load_user(user_id):
            if not user_id:
                return None
            try:
                return User.query.filter_by(id=int(user_id)).first()
            except (SQLAlchemyError, ValueError) as e:
                logger.error(f"Error loading user {user_id}: {str(e)}")
                return None

        try:
            # Import routes after app creation to avoid circular imports
            from routes import register_routes
            
            # Create database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Register routes
            app = register_routes(app)
            logger.info("Routes registered successfully")

            return app

        except Exception as e:
            logger.error(f"Error during app initialization: {str(e)}")
            raise

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
