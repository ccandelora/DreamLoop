from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply

def update_schema():
    with app.app_context():
        # Drop tables in reverse order to handle dependencies
        db.session.execute('DROP TABLE IF EXISTS forum_reply CASCADE')
        db.session.execute('DROP TABLE IF EXISTS forum_post CASCADE')
        db.session.execute('DROP TABLE IF EXISTS group_membership CASCADE')
        db.session.execute('DROP TABLE IF EXISTS dream_group CASCADE')
        db.session.execute('DROP TABLE IF EXISTS comment CASCADE')
        db.session.execute('DROP TABLE IF EXISTS dream CASCADE')
        
        # Create all tables
        db.create_all()
        
        print("Schema updated successfully!")

if __name__ == "__main__":
    update_schema()
