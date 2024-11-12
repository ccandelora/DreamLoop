from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'
