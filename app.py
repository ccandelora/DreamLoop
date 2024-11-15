from flask import Flask, jsonify
import os
from extensions import db, login_manager, init_db_pool
from sqlalchemy.exc import SQLAlchemyError
from logging_config import setup_logging, ErrorLogger
from flask_login import current_user
from models import User
from transaction_debugger import init_transaction_debugger
from flask_migrate import Migrate
from health_checks import health_checker
import atexit

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
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 300
    }
    
    # Initialize database and other extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize migrations with directory configuration
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
    Migrate(app, db, directory=migrations_dir)
    
    # Initialize transaction debugger
    init_transaction_debugger(app)
    
    # Register the health check endpoint
    @app.route('/health')
    def health_check():
        """Endpoint to check application and database health."""
        try:
            health_status = health_checker.get_health_status()
            return jsonify(health_status)
        except Exception as e:
            app.logger.error(f"Error in health check endpoint: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        try:
            return User.query.get(int(user_id))
        except SQLAlchemyError as e:
            ErrorLogger.log_error(e, {'user_id': user_id})
            return None
    
    # Add template context processor
    @app.context_processor
    def utility_processor():
        return {
            'should_show_premium_ads': should_show_premium_ads
        }
    
    # Import and register routes
    with app.app_context():
        try:
            from routes import register_routes
            app = register_routes(app)
            app.logger.info("Routes registered successfully")
            
            # Initialize health checker after all routes are registered
            health_checker.init_app(app)
            # Start health checks
            health_checker.start_monitoring()
            
            @atexit.register
            def cleanup():
                health_checker.stop_monitoring()
                
        except Exception as e:
            app.logger.error(f"Error registering routes: {str(e)}")
            raise
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
