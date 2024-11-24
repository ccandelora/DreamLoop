from flask import Flask
from dotenv import load_dotenv
from dreamloop.extensions import db, migrate, login_manager
from config import Config

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    # Import models here to avoid circular imports
    from dreamloop.models import Users, Notification
    
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))
    
    # Add context processor for notifications
    @app.context_processor
    def utility_processor():
        def get_unread_notifications_count():
            if not hasattr(utility_processor, '_current_user'):
                from flask_login import current_user
                utility_processor._current_user = current_user
            
            if utility_processor._current_user.is_authenticated:
                return Notification.query.filter_by(
                    user_id=utility_processor._current_user.id,
                    read=False
                ).count()
            return 0
            
        return {
            'unread_notifications_count': get_unread_notifications_count()
        }
    
    # Register blueprints
    from dreamloop.routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    return app 