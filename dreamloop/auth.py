from flask_login import LoginManager
from .models import Users
from .extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    if user_id is not None:
        return Users.query.get(int(user_id))
    return None

def init_login_manager(app):
    """Initialize the login manager."""
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # Specify the login view endpoint
    login_manager.login_message_category = 'info' 