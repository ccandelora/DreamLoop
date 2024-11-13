import click
from backup_manager import BackupManager
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/backup.log')
    ]
)

logger = logging.getLogger(__name__)
backup_manager = BackupManager()

@click.group()
def cli():
    """DreamShare backup management CLI"""
    pass

@cli.command()
@click.option('--include-logs/--no-logs', default=True, help='Include log files in backup')
def create(include_logs):
    """Create a new backup"""
    success, result = backup_manager.create_backup(include_logs)
    if success:
        click.echo(f"Backup created successfully at: {result}")
    else:
        click.echo(f"Backup failed: {result}", err=True)

@cli.command()
@click.argument('backup_path')
def restore(backup_path):
    """Restore from a backup"""
    if click.confirm('This will overwrite the current database. Are you sure?'):
        success, error = backup_manager.restore_backup(backup_path)
        if success:
            click.echo("Backup restored successfully")
        else:
            click.echo(f"Restore failed: {error}", err=True)

@cli.command()
def list():
    """List all available backups"""
    backups = backup_manager.list_backups()
    if not backups:
        click.echo("No backups found")
        return

    for backup in backups:
        metadata = backup['metadata']
        click.echo(f"\nBackup: {backup['path']}")
        click.echo(f"Created: {metadata['timestamp']}")
        click.echo(f"Includes logs: {metadata.get('includes_logs', False)}")
        click.echo(f"Version: {metadata.get('version', 'unknown')}")

@cli.command()
@click.option('--keep-last', default=5, help='Number of recent backups to keep')
def cleanup(keep_last):
    """Clean up old backups"""
    if click.confirm(f'This will remove all but the {keep_last} most recent backups. Continue?'):
        success, error = backup_manager.cleanup_old_backups(keep_last)
        if success:
            click.echo("Old backups cleaned up successfully")
        else:
            click.echo(f"Cleanup failed: {error}", err=True)

if __name__ == '__main__':
    cli()
