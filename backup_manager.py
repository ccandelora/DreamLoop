import os
import json
import shutil
from datetime import datetime
import logging
from sqlalchemy import create_engine, MetaData, Table
import psycopg2
from models import User, Dream, Comment, DreamGroup, GroupMembership, ForumPost, ForumReply, UserActivity
from extensions import db
import gzip

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_dir='backups'):
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Ensure backup subdirectories exist
        self.db_backup_dir = os.path.join(backup_dir, 'database')
        self.logs_backup_dir = os.path.join(backup_dir, 'logs')
        
        for directory in [self.db_backup_dir, self.logs_backup_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def create_backup(self, include_logs=True):
        """Create a complete backup of the application."""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}')
            os.makedirs(backup_path, exist_ok=True)

            # Backup database
            db_backup_file = os.path.join(backup_path, 'database.sql.gz')
            self._backup_database(db_backup_file)

            # Backup logs if requested
            if include_logs:
                logs_backup_dir = os.path.join(backup_path, 'logs')
                os.makedirs(logs_backup_dir, exist_ok=True)
                self._backup_logs(logs_backup_dir)

            # Create backup metadata
            metadata = {
                'timestamp': timestamp,
                'includes_logs': include_logs,
                'database_file': 'database.sql.gz',
                'version': '1.0'
            }
            
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Backup created successfully at {backup_path}")
            return True, backup_path

        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def restore_backup(self, backup_path):
        """Restore the application from a backup."""
        try:
            # Verify backup integrity
            if not self._verify_backup(backup_path):
                raise ValueError("Invalid or corrupted backup")

            # Read metadata
            with open(os.path.join(backup_path, 'metadata.json'), 'r') as f:
                metadata = json.load(f)

            # Restore database
            db_backup_file = os.path.join(backup_path, metadata['database_file'])
            self._restore_database(db_backup_file)

            # Restore logs if they were included
            if metadata.get('includes_logs', False):
                logs_backup_dir = os.path.join(backup_path, 'logs')
                if os.path.exists(logs_backup_dir):
                    self._restore_logs(logs_backup_dir)

            logger.info(f"Backup restored successfully from {backup_path}")
            return True, None

        except Exception as e:
            error_msg = f"Error restoring backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def list_backups(self):
        """List all available backups with their metadata."""
        backups = []
        try:
            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    metadata_file = os.path.join(backup_path, 'metadata.json')
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            backups.append({
                                'path': backup_path,
                                'metadata': metadata
                            })
            return sorted(backups, key=lambda x: x['metadata']['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []

    def cleanup_old_backups(self, keep_last=5):
        """Remove old backups keeping only the specified number of recent ones."""
        try:
            backups = self.list_backups()
            if len(backups) > keep_last:
                for backup in backups[keep_last:]:
                    backup_path = backup['path']
                    shutil.rmtree(backup_path)
                    logger.info(f"Removed old backup: {backup_path}")
            return True, None
        except Exception as e:
            error_msg = f"Error cleaning up old backups: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _backup_database(self, output_file):
        """Create a compressed database backup."""
        try:
            db_url = os.environ['DATABASE_URL']
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)

            # Create a database dump
            with gzip.open(output_file, 'wt') as f:
                engine = create_engine(db_url)
                metadata = MetaData()
                metadata.reflect(bind=engine)
                
                # Export schema
                for table in metadata.sorted_tables:
                    schema = str(CreateTable(table).compile(engine))
                    f.write(f"{schema}\n")
                
                # Export data
                with engine.connect() as conn:
                    for table in metadata.sorted_tables:
                        result = conn.execute(table.select())
                        for row in result:
                            insert = table.insert().values(row._mapping)
                            f.write(f"{str(insert.compile(engine))}\n")

            logger.info(f"Database backup created at {output_file}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise

    def _restore_database(self, backup_file):
        """Restore database from a compressed backup."""
        try:
            db_url = os.environ['DATABASE_URL']
            if db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)

            engine = create_engine(db_url)
            
            # Drop all existing tables
            metadata = MetaData()
            metadata.reflect(bind=engine)
            metadata.drop_all(engine)

            # Restore from backup
            with gzip.open(backup_file, 'rt') as f:
                statements = f.read().split('\n')
                with engine.begin() as conn:
                    for statement in statements:
                        if statement.strip():
                            conn.execute(text(statement))

            logger.info("Database restored successfully")
            return True

        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            raise

    def _backup_logs(self, backup_dir):
        """Backup log files."""
        try:
            log_dir = 'logs'
            if os.path.exists(log_dir):
                for log_file in os.listdir(log_dir):
                    src = os.path.join(log_dir, log_file)
                    dst = os.path.join(backup_dir, log_file)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Error backing up logs: {str(e)}")
            raise

    def _restore_logs(self, backup_dir):
        """Restore log files."""
        try:
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            for log_file in os.listdir(backup_dir):
                src = os.path.join(backup_dir, log_file)
                dst = os.path.join(log_dir, log_file)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"Error restoring logs: {str(e)}")
            raise

    def _verify_backup(self, backup_path):
        """Verify backup integrity."""
        try:
            # Check if metadata exists
            metadata_file = os.path.join(backup_path, 'metadata.json')
            if not os.path.exists(metadata_file):
                return False

            # Read and validate metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                required_fields = ['timestamp', 'database_file', 'version']
                if not all(field in metadata for field in required_fields):
                    return False

            # Verify database backup exists
            db_backup_file = os.path.join(backup_path, metadata['database_file'])
            if not os.path.exists(db_backup_file):
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            return False
