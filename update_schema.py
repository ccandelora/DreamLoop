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
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sleep_duration') THEN
                        ALTER TABLE dream ADD COLUMN sleep_duration FLOAT;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sleep_quality') THEN
                        ALTER TABLE dream ADD COLUMN sleep_quality INTEGER;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'bed_time') THEN
                        ALTER TABLE dream ADD COLUMN bed_time TIMESTAMP;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'wake_time') THEN
                        ALTER TABLE dream ADD COLUMN wake_time TIMESTAMP;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sleep_interruptions') THEN
                        ALTER TABLE dream ADD COLUMN sleep_interruptions INTEGER DEFAULT 0;
                    END IF;
                    
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'dream' AND column_name = 'sleep_position') THEN
                        ALTER TABLE dream ADD COLUMN sleep_position VARCHAR(50);
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
