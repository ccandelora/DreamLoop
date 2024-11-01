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
            'dream'
        ]
        
        for table in tables:
            db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
        
        # Create all tables
        db.create_all()
        
        print("Schema updated successfully!")

if __name__ == "__main__":
    update_schema()
