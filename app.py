from flask import Flask
import markdown
import os
from extensions import db, login_manager

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add markdown filter
def markdown_filter(text):
    return markdown.markdown(text) if text else ''
app.jinja_env.filters['markdown'] = markdown_filter

# Import models and routes after initialization
from models import User
from routes import *

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
