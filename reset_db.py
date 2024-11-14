from flask import Flask
from extensions import db, init_db_pool, session_manager
from models import User, DreamGroup, GroupMembership
from datetime import datetime, timedelta
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_init_app():
    """Create a minimal Flask app for database initialization."""
    app = Flask(__name__)
    
    # Configure database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        db_url = f"postgresql://{os.environ['PGUSER']}:{os.environ['PGPASSWORD']}@{os.environ['PGHOST']}:{os.environ['PGPORT']}/{os.environ['PGDATABASE']}"
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db = init_db_pool(app)
    return app

def reset_database():
    """Reset and initialize the database with initial data."""
    app = create_init_app()
    
    with app.app_context():
        try:
            # Drop existing tables
            db.drop_all()
            logger.info("All tables dropped successfully")
            
            # Create new tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create test data using session manager
            with session_manager.session_scope() as session:
                # Create test user
                test_user = User(
                    username="testuser",
                    email="test@example.com",
                    subscription_type="free"
                )
                test_user.set_password("password123")
                session.add(test_user)
                
                # Create premium user
                premium_user = User(
                    username="premium_user",
                    email="premium@example.com",
                    subscription_type="premium"
                )
                premium_user.set_password("premium123")
                premium_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
                session.add(premium_user)
                
                # Flush to get user IDs
                session.flush()
                
                # Create sample dream group
                dream_group = DreamGroup(
                    name="Lucid Dreamers",
                    description="A group for sharing and discussing lucid dreaming experiences",
                    created_by=test_user.id
                )
                session.add(dream_group)
                session.flush()
                
                # Create group membership
                membership = GroupMembership(
                    user_id=test_user.id,
                    group_id=dream_group.id,
                    is_admin=True
                )
                session.add(membership)
                
            logger.info("Sample data created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during database reset: {str(e)}")
            return False

if __name__ == "__main__":
    success = reset_database()
    if not success:
        exit(1)
