from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from sqlalchemy import text

def update_schema():
    with app.app_context():
        # Drop tables in reverse order to handle dependencies
        db.session.execute(text('DROP TABLE IF EXISTS forum_reply CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS forum_post CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS group_membership CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS dream_group CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS comment CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS dream CASCADE'))
        db.session.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
        
        # Create all tables with proper columns
        db.create_all()
        
        # Add any missing columns if needed
        db.session.execute(text('''
            DO $$ 
            BEGIN
                -- Add sentiment analysis columns to dream table if they don't exist
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
            END $$;
        '''))
        
        db.session.commit()
        print("Schema updated successfully!")

if __name__ == "__main__":
    update_schema()
