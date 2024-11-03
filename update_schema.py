from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    with app.app_context():
        try:
            # Start transaction
            db.session.begin()
            
            # Create all tables using SQLAlchemy models
            logger.info("Creating tables from models...")
            db.create_all()
            
            # Execute the schema updates
            logger.info("Updating forum tables...")
            db.session.execute(text('''
                DO $$ 
                BEGIN
                    -- Recreate forum tables with correct column names
                    DROP TABLE IF EXISTS forum_reply CASCADE;
                    DROP TABLE IF EXISTS forum_post CASCADE;
                    
                    -- Create forum_post table with user_id
                    CREATE TABLE forum_post (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES "user"(id),
                        group_id INTEGER NOT NULL REFERENCES dream_group(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create forum_reply table with user_id
                    CREATE TABLE forum_reply (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES "user"(id),
                        post_id INTEGER NOT NULL REFERENCES forum_post(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                END $$;
            '''))
            
            # Commit transaction
            db.session.commit()
            logger.info("Schema updated successfully!")
            return True
            
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            logger.error(f"Error updating schema: {str(e)}")
            return False

if __name__ == "__main__":
    success = update_schema()
    if not success:
        exit(1)
