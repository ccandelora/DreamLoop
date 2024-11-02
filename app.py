from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import markdown
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Add markdown filter
def markdown_filter(text):
    return markdown.markdown(text) if text else ''
app.jinja_env.filters['markdown'] = markdown_filter

from models import User
from routes import *

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
