from flask import Flask, jsonify, request, render_template
import os
from extensions import db, login_manager, init_db_pool, csrf
from sqlalchemy.exc import SQLAlchemyError
from logging_config import setup_logging, ErrorLogger
from flask_login import current_user
from models import User
from transaction_debugger import init_transaction_debugger
from flask_migrate import Migrate
from health_checks import health_checker
from middleware import setup_request_logging
import atexit
import logging
from routes import register_routes

logger = logging.getLogger(__name__)

def should_show_premium_ads():
    """Determine if premium ads should be shown to the current user."""
    if not current_user or not current_user.is_authenticated:
        return True
    return current_user.subscription_type == 'free'

def create_app():
    """Create and configure the Flask application with enhanced security and error handling."""
    app = Flask(__name__)
    
    # Setup logging first
    setup_logging(app)
    
    # Configure the Flask app with security measures
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token expiry
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configure database
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_size': 8,
        'max_overflow': 20,
        'pool_recycle': 300
    }
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Initialize migrations
    migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
    Migrate(app, db, directory=migrations_dir)
    
    # Initialize transaction debugger
    init_transaction_debugger(app)
    
    # Setup request logging and middleware
    setup_request_logging(app)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 Error: {request.url}")
        if request.is_json:
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Error: {str(error)}")
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        logger.warning(f"403 Error: {request.url}")
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(429)
    def ratelimit_error(error):
        logger.warning(f"429 Error: {request.url}")
        if request.is_json:
            return jsonify({'error': 'Too many requests'}), 429
        return render_template('errors/429.html'), 429
    
    # Register health check endpoint
    @app.route('/health')
    def health_check():
        """Endpoint to check application and database health."""
        try:
            health_status = health_checker.get_health_status()
            return jsonify(health_status)
        except Exception as e:
            logger.error(f"Error in health check endpoint: {str(e)}")
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
    
    # Register all routes
    app = register_routes(app)
    
    # Initialize health checker
    health_checker.init_app(app)
    health_checker.start_monitoring()
    
    @atexit.register
    def cleanup():
        health_checker.stop_monitoring()
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
