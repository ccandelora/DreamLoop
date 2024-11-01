from app import app, db
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply
from sqlalchemy import text, inspect

def verify_columns(inspector, table_name, expected_columns):
    """Verify that all expected columns exist in the table"""
    existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
    missing_columns = [col for col in expected_columns if col not in existing_columns]
    if missing_columns:
        print(f"Warning: Missing columns in {table_name}: {missing_columns}")
    else:
        print(f"All expected columns exist in {table_name}")
    return len(missing_columns) == 0

def update_schema():
    with app.app_context():
        # Drop tables in reverse order to handle dependencies
        tables = [
            'forum_reply',
            'forum_post',
            'group_membership',
            'dream_group',
            'comment',
            'dream',
            'user'
        ]
        
        # Drop existing tables with proper quoting
        for table in tables:
            try:
                db.session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                db.session.commit()
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Error dropping table {table}: {str(e)}")
                db.session.rollback()
        
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
            'lucidity_level',
            'sleep_quality',
            'dream_clarity',
            'recurring_elements',
            'emotional_tone',
            'dream_symbols',
            'dream_archetypes',
            'sleep_duration',
            'bedtime',
            'environmental_factors'
        ]
        
        # Verify the schema creation
        for table in tables:
            if table not in inspector.get_table_names():
                print(f"Error: Table {table} was not created!")
                return False
            print(f"Table {table} exists")
            
            # Special verification for dream table columns
            if table == 'dream':
                if not verify_columns(inspector, table, dream_columns):
                    print("Error: Not all required dream columns were created!")
                    return False
        
        print("Schema update completed successfully!")
        return True

if __name__ == "__main__":
    update_schema()
