from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy with session options
db = SQLAlchemy(session_options={
    'autocommit': False,
    'autoflush': False,
    'expire_on_commit': False
})

# Initialize LoginManager
login_manager = LoginManager()
