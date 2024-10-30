from app import app, db
from sqlalchemy import text
from models import *

with app.app_context():
    # Drop all tables to ensure clean slate
    db.session.execute(text('DROP TABLE IF EXISTS comment CASCADE'))
    db.session.execute(text('DROP TABLE IF EXISTS group_membership CASCADE'))
    db.session.execute(text('DROP TABLE IF EXISTS dream_group CASCADE'))
    db.session.execute(text('DROP TABLE IF EXISTS dream CASCADE'))
    db.session.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
    db.session.commit()
    
    # Create all tables from models
    db.create_all()
    print("Schema updated successfully!")
