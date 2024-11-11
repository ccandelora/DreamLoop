from app import app, db
from models import User, DreamGroup, GroupMembership
from datetime import datetime, timedelta
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            logger.info("All tables dropped successfully")

            # Create tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                subscription_type="free"
            )
            test_user.set_password("password123")
            db.session.add(test_user)
            
            # Create premium user
            premium_user = User(
                username="premium_user",
                email="premium@example.com",
                subscription_type="premium"
            )
            premium_user.set_password("premium123")
            premium_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            db.session.add(premium_user)
            
            # Commit users first to get their IDs
            db.session.commit()
            logger.info("Test users created successfully")
            
            # Create sample dream group
            dream_group = DreamGroup(
                name="Lucid Dreamers",
                description="A group for sharing and discussing lucid dreaming experiences",
                created_by=test_user.id
            )
            db.session.add(dream_group)
            db.session.flush()
            
            # Create group membership
            membership = GroupMembership(
                user_id=test_user.id,
                group_id=dream_group.id,
                is_admin=True
            )
            db.session.add(membership)
            
            # Final commit
            db.session.commit()
            logger.info("Sample dream group and membership created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during database reset: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = reset_database()
    if not success:
        exit(1)