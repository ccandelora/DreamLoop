from app import app, db
from sqlalchemy import text
from models import *

with app.app_context():
    # Add created_by column to dream_group table if it doesn't exist
    db.session.execute(text('ALTER TABLE dream_group ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES "user"(id)'))
    db.session.commit()
    
    # Add any missing comments table columns
    db.session.execute(text('''
        CREATE TABLE IF NOT EXISTS comment (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES "user"(id) NOT NULL,
            dream_id INTEGER REFERENCES dream(id) NOT NULL
        )
    '''))
    db.session.commit()
    print("Schema updated successfully!")
