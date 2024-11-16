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
            
            # First create all tables using SQLAlchemy models
            logger.info("Creating tables from models...")
            db.create_all()
            
            # Now execute DO block to ensure table exists and has all required columns
            logger.info("Checking and adding any missing columns...")
            db.session.execute(text('''
                DO $$ 
                BEGIN
                    -- First create or update the dream table
                    CREATE TABLE IF NOT EXISTS dream (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title VARCHAR(100) NOT NULL,
                        content TEXT NOT NULL,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        mood VARCHAR(50),
                        tags VARCHAR(200),
                        is_public BOOLEAN DEFAULT FALSE,
                        is_anonymous BOOLEAN DEFAULT FALSE,
                        ai_analysis TEXT,
                        sentiment_score FLOAT,
                        sentiment_magnitude FLOAT,
                        dominant_emotions VARCHAR(200),
                        lucidity_level INTEGER,
                        sleep_duration FLOAT,
                        sleep_quality INTEGER,
                        bed_time TIMESTAMP,
                        wake_time TIMESTAMP,
                        sleep_interruptions INTEGER DEFAULT 0,
                        sleep_position VARCHAR(50)
                    );

                    -- Drop and recreate forum_post table
                    DROP TABLE IF EXISTS forum_reply;
                    DROP TABLE IF EXISTS forum_post;
                    
                    CREATE TABLE forum_post (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES "user"(id),
                        group_id INTEGER NOT NULL REFERENCES dream_group(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create forum_reply table
                    CREATE TABLE forum_reply (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL REFERENCES "user"(id),
                        post_id INTEGER NOT NULL REFERENCES forum_post(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Add moderator flag to user table
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'user' AND column_name = 'is_moderator') THEN
                        ALTER TABLE "user" ADD COLUMN is_moderator BOOLEAN DEFAULT FALSE;
                    END IF;

                    -- Add moderation columns to comment table
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                 WHERE table_name = 'comment' AND column_name = 'is_hidden') THEN
                        ALTER TABLE comment ADD COLUMN is_hidden BOOLEAN DEFAULT FALSE;
                        ALTER TABLE comment ADD COLUMN moderation_reason VARCHAR(200);
                        ALTER TABLE comment ADD COLUMN moderated_at TIMESTAMP;
                        ALTER TABLE comment ADD COLUMN moderated_by INTEGER REFERENCES "user"(id);
                    END IF;

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