import shutil
import os
from app import create_app
from flask_migrate import Migrate
from extensions import db

def init_migrations():
    # Remove existing migrations directory if it exists
    if os.path.exists('migrations'):
        shutil.rmtree('migrations')
    
    # Create Flask app
    app = create_app()
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    with app.app_context():
        os.system('flask db init')
        os.system('flask db migrate -m "initial migration"')
        os.system('flask db upgrade')

if __name__ == '__main__':
    init_migrations()
