from flask.cli import FlaskGroup
from app import create_app
from flask_migrate import Migrate
from extensions import db
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_cli_app():
    app = create_app()
    migrate = Migrate(app, db)
    return app

cli = FlaskGroup(create_app=create_cli_app)

def print_usage():
    print("""
Usage: python manage_migrations.py <command>

Commands:
  migrate   - Create a new migration
  upgrade  - Apply all pending migrations
  downgrade - Revert last migration
  history  - Show migration history
    """)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
    else:
        cli()
