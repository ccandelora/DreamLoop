from flask.cli import FlaskGroup
from app import create_app
from migrations_manager import init_migrations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_cli_app():
    app = create_app()
    app, migrate = init_migrations(app)
    return app

cli = FlaskGroup(create_app=create_cli_app)

if __name__ == '__main__':
    cli()
