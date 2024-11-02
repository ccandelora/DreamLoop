from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import markdown
import os

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db = SQLAlchemy()
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add markdown filter
def markdown_filter(text):
    return markdown.markdown(text) if text else ''
app.jinja_env.filters['markdown'] = markdown_filter

# Import models and routes after initialization
with app.app_context():
    from models import User
    from routes import *

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
