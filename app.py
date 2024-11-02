from flask import Flask
from flask_login import LoginManager
from extensions import db, login_manager
import os
import logging
import markdown

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Add markdown filter
def markdown_filter(text):
    return markdown.markdown(text) if text else ''
app.jinja_env.filters['markdown'] = markdown_filter

# Create tables within app context
with app.app_context():
    from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
    db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

# Import routes at the end to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
