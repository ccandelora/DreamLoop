from app import app, db
from models import User, Dream, DreamGroup, GroupMembership, ForumPost, ForumReply, Comment
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text

def reset_database():
    with app.app_context():
        # Drop tables in order respecting foreign key constraints
        tables_to_drop = [
            '"forum_reply"',
            '"forum_post"', 
            '"comment"',
            '"group_membership"',
            '"dream"',
            '"dream_group"',
            '"user"'
        ]
        
        # Drop tables in correct order
        for table in tables_to_drop:
            try:
                db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Error dropping {table}: {str(e)}")
                
        try:
            db.session.commit()
            print("All tables dropped successfully")
        except Exception as e:
            print(f"Error committing table drops: {str(e)}")
            db.session.rollback()
            return
        
        # Create tables in correct order
        try:
            # Create User table first
            db.create_all()
            print("Created all tables successfully")
            
            # Create test user
            test_user = User()
            test_user.username = "testuser"
            test_user.email = "test@example.com"
            test_user.subscription_type = "free"
            test_user.monthly_ai_analysis_count = 0
            test_user.last_analysis_reset = datetime.utcnow()
            test_user.set_password("password123")
            
            # Create premium test user
            premium_user = User()
            premium_user.username = "premium_user"
            premium_user.email = "premium@example.com"
            premium_user.subscription_type = "premium"
            premium_user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
            premium_user.monthly_ai_analysis_count = 0
            premium_user.last_analysis_reset = datetime.utcnow()
            premium_user.set_password("premium123")
            premium_user.is_moderator = True  # Make premium user a moderator
            
            db.session.add(test_user)
            db.session.add(premium_user)
            db.session.commit()
            print("Test users created successfully")

            # Create sample dream group
            dream_group = DreamGroup()
            dream_group.name = "Lucid Dreamers"
            dream_group.description = "A group for sharing and discussing lucid dreaming experiences"
            dream_group.created_by = premium_user.id  # Set the creator
            
            db.session.add(dream_group)
            db.session.flush()

            # Make test user an admin of the group
            membership = GroupMembership()
            membership.user_id = test_user.id
            membership.group_id = dream_group.id
            membership.is_admin = True
            
            db.session.add(membership)
            db.session.commit()
            print("Sample group and membership created successfully")
            
        except Exception as e:
            print(f"Error during database setup: {str(e)}")
            db.session.rollback()
            return
        
        print("Database reset complete. Test users and sample group created.")

if __name__ == "__main__":
    reset_database()
