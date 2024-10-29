from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add debug logging for static file serving
logger.debug(f"Static folder path: {app.static_folder}")

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
