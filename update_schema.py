from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from sqlalchemy import text

def update_schema():
    with app.app_context():
        # Drop tables in reverse order to handle dependencies
        tables = [
            'forum_reply',
            'forum_post',
            'group_membership',
            'dream_group',
            'comment',
            'dream',
            'user'  # Add user table to ensure complete schema refresh
        ]
        
        for table in tables:
            db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        
        # Create all tables with proper indexes
        db.create_all()
        
        # Verify the schema creation
        for table in ['dream', 'user', 'comment', 'dream_group', 'group_membership', 'forum_post', 'forum_reply']:
            result = db.session.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"))
            exists = result.scalar()
            if exists:
                print(f"Table {table} created successfully!")
            else:
                print(f"Error: Table {table} was not created!")
        
        print("Schema update completed!")

if __name__ == "__main__":
    update_schema()
