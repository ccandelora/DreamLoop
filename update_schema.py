from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from sqlalchemy import text, inspect

def update_schema():
    with app.app_context():
        # Drop all tables to ensure clean slate
        db.drop_all()
        db.session.commit()
        
        # Create all tables with proper indexes
        try:
            db.create_all()
            db.session.commit()
            print("Created all tables")
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            db.session.rollback()
            return False
        
        # Verify table creation and columns
        inspector = inspect(db.engine)
        
        # Verify dream table columns
        dream_columns = [
            'id', 'user_id', 'title', 'content', 'date', 'mood', 'tags',
            'is_public', 'is_anonymous', 'ai_analysis', 'lucidity_level',
            'sleep_quality', 'dream_clarity', 'recurring_elements',
            'emotional_tone', 'dream_symbols', 'dream_archetypes',
            'sleep_duration', 'bedtime', 'environmental_factors'
        ]
        
        # Verify the schema creation
        tables = ['user', 'dream', 'comment', 'dream_group', 'group_membership', 'forum_post', 'forum_reply']
        for table in tables:
            if table not in inspector.get_table_names():
                print(f"Error: Table {table} was not created!")
                return False
            print(f"Table {table} exists")
            
            # Special verification for dream table columns
            if table == 'dream':
                existing_columns = [col['name'] for col in inspector.get_columns(table)]
                missing_columns = [col for col in dream_columns if col not in existing_columns]
                if missing_columns:
                    print(f"Error: Missing dream columns: {missing_columns}")
                    return False
                print("All dream columns verified")
        
        print("Schema update completed successfully!")
        return True

if __name__ == "__main__":
    update_schema()
