from app import app, db
from models import User, Dream, DreamGroup, GroupMembership, ForumPost, ForumReply, Comment
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text

def reset_database():
    with app.app_context():
        # Drop tables in order respecting foreign key constraints
        tables_to_drop = [
            'forum_reply',
            'forum_post', 
            'comment',
            'group_membership',
            'dream',
            'dream_group',
            'user'
        ]
        
        # Drop tables in correct order
        for table in tables_to_drop:
            try:
                db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Error dropping {table}: {str(e)}")
                
        db.session.commit()
        
        # Create all tables
        db.create_all()
        print("Created all tables")
        
        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            subscription_type="free",
            monthly_ai_analysis_count=0,
            last_analysis_reset=datetime.utcnow()
        )
        test_user.set_password("password123")
        
        # Create premium test user
        premium_user = User(
            username="premium_user",
            email="premium@example.com",
            subscription_type="premium",
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_ai_analysis_count=0,
            last_analysis_reset=datetime.utcnow()
        )
        premium_user.set_password("premium123")
        
        db.session.add(test_user)
        db.session.add(premium_user)
        db.session.commit()

        # Create sample dream group
        dream_group = DreamGroup(
            name="Lucid Dreamers",
            description="A group for sharing and discussing lucid dreaming experiences",
            theme="Lucid Dreams"
        )
        db.session.add(dream_group)
        db.session.flush()

        # Make test user an admin of the group
        membership = GroupMembership(
            user_id=test_user.id,
            group_id=dream_group.id,
            is_admin=True
        )
        db.session.add(membership)
        db.session.commit()
        
        print("Database reset complete. Test users and sample group created.")

if __name__ == "__main__":
    reset_database()
