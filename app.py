from flask import Flask
from flask_login import LoginManager
from models import db, User
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    # Import routes here to avoid circular imports
    import routes
    print('Registered routes:', [str(p) for p in app.url_map.iter_rules()])
    app.run(host='0.0.0.0', port=5000)
