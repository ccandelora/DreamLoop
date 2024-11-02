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
                        lucidity_level INTEGER
                    );

                    -- Create or update forum_post table
                    CREATE TABLE IF NOT EXISTS forum_post (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create or update forum_reply table
                    CREATE TABLE IF NOT EXISTS forum_reply (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    -- Add missing columns to dream table if they don't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sentiment_score') THEN
                        ALTER TABLE dream ADD COLUMN sentiment_score FLOAT;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sentiment_magnitude') THEN
                        ALTER TABLE dream ADD COLUMN sentiment_magnitude FLOAT;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'dominant_emotions') THEN
                        ALTER TABLE dream ADD COLUMN dominant_emotions VARCHAR(200);
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'lucidity_level') THEN
                        ALTER TABLE dream ADD COLUMN lucidity_level INTEGER;
                    END IF;

                    -- Add missing columns to forum_post table if they don't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forum_post' AND column_name = 'created_at') THEN
                        ALTER TABLE forum_post ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forum_post' AND column_name = 'user_id') THEN
                        ALTER TABLE forum_post ADD COLUMN user_id INTEGER NOT NULL;
                    END IF;

                    -- Add missing columns to forum_reply table if they don't exist
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forum_reply' AND column_name = 'created_at') THEN
                        ALTER TABLE forum_reply ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    END IF;

                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'forum_reply' AND column_name = 'user_id') THEN
                        ALTER TABLE forum_reply ADD COLUMN user_id INTEGER NOT NULL;
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
