import click
from flask.cli import FlaskGroup
from dreamloop import create_app, db
from flask_migrate import Migrate
import os
import shutil
from sqlalchemy import text

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(app)

def create_initial_migration():
    """Create the initial migration file."""
    os.makedirs('migrations/versions', exist_ok=True)
    migration_path = 'migrations/versions/initial_migration.py'
    
    with open(migration_path, 'w') as f:
        f.write('''"""Initial migration

Revision ID: initial
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create all tables
    pass

def downgrade():
    # Drop all tables
    pass
''')

@cli.command("init_db")
@click.confirmation_option(
    prompt='This will create a fresh database. Continue?'
)
def init_db():
    """Initialize the database."""
    click.echo("Initializing fresh database...")
    
    with app.app_context():
        # Drop all tables with CASCADE
        db.session.execute(text('DROP SCHEMA public CASCADE'))
        db.session.execute(text('CREATE SCHEMA public'))
        db.session.commit()
        
        # Create all tables
        db.create_all()
        
        click.echo("Database initialized successfully!")

@cli.command("sync_db")
def sync_db():
    """Sync database with current models."""
    with app.app_context():
        db.create_all()
    click.echo("Database synced with models!")

@cli.command("make_migration")
@click.argument('message')
def make_migration(message):
    """Create a new migration for production."""
    with app.app_context():
        from flask_migrate import migrate
        migrate(message=message)
    click.echo(f"Created migration: {message}")

@cli.command("apply_migrations")
def apply_migrations():
    """Apply pending migrations in production."""
    with app.app_context():
        from flask_migrate import upgrade
        upgrade()
    click.echo("Applied all migrations")

if __name__ == "__main__":
    cli() 