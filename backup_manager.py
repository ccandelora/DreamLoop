import os
import json
import shutil
from datetime import datetime
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import gzip
import subprocess

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_dir='backups'):
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Ensure backup subdirectories exist
        self.db_backup_dir = os.path.join(backup_dir, 'database')
        self.logs_backup_dir = os.path.join(backup_dir, 'logs')
        self.schema_backup_dir = os.path.join(backup_dir, 'schema')
        
        for directory in [self.db_backup_dir, self.logs_backup_dir, self.schema_backup_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def create_backup(self, include_logs=True):
        """Create a complete backup of the application."""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}')
            os.makedirs(backup_path, exist_ok=True)

            # Backup database schema and data
            db_backup_file = os.path.join(backup_path, 'database.sql.gz')
            schema_backup_file = os.path.join(backup_path, 'schema.sql.gz')
            
            # Create schema-only backup first
            self._backup_schema(schema_backup_file)
            # Then create complete backup
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
                'schema_file': 'schema.sql.gz',
                'version': '1.1'
            }
            
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Backup created successfully at {backup_path}")
            return True, backup_path

        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _backup_schema(self, output_file):
        """Create a schema-only backup."""
        try:
            conn_string = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(
                user=os.environ['PGUSER'],
                password=os.environ['PGPASSWORD'],
                host=os.environ['PGHOST'],
                port=os.environ['PGPORT'],
                dbname=os.environ['PGDATABASE']
            )

            with gzip.open(output_file, 'wb') as f:
                # Use psql to dump schema only
                process = subprocess.Popen([
                    'psql',
                    conn_string,
                    '-X',  # No .psqlrc
                    '-q',  # Quiet mode
                    '-A',  # Unaligned output mode
                    '-t',  # Print rows only
                    '-c', '\dt'  # List tables
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                tables = process.communicate()[0].decode().strip().split('\n')
                
                for table in tables:
                    if not table:
                        continue
                    
                    # Get schema for each table
                    schema_process = subprocess.Popen([
                        'psql',
                        conn_string,
                        '-X',
                        '-q',
                        '-c', f'\\d+ {table}'
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    schema = schema_process.communicate()[0]
                    if schema:
                        f.write(schema)

            logger.info(f"Schema backup created at {output_file}")
            return True
        except Exception as e:
            logger.error(f"Schema backup failed: {str(e)}")
            raise

    def _backup_database(self, output_file):
        """Create a complete database backup."""
        try:
            with gzip.open(output_file, 'wb') as f:
                # Use psql to dump complete database
                process = subprocess.Popen([
                    'psql',
                    '--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                        user=os.environ['PGUSER'],
                        password=os.environ['PGPASSWORD'],
                        host=os.environ['PGHOST'],
                        port=os.environ['PGPORT'],
                        dbname=os.environ['PGDATABASE']
                    ),
                    '-X',  # No .psqlrc
                    '-c', 'SELECT pg_catalog.pg_export_snapshot();'  # Create a snapshot
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Get the snapshot ID
                snapshot_id = process.communicate()[0].decode().strip()
                
                if process.returncode != 0:
                    raise Exception("Failed to create database snapshot")

                # Dump using the snapshot
                dump_process = subprocess.Popen([
                    'psql',
                    '--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                        user=os.environ['PGUSER'],
                        password=os.environ['PGPASSWORD'],
                        host=os.environ['PGHOST'],
                        port=os.environ['PGPORT'],
                        dbname=os.environ['PGDATABASE']
                    ),
                    '-X',  # No .psqlrc
                    '-c', f'\\copy (SELECT * FROM pg_catalog.pg_dump_all_tables(true)) TO STDOUT'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Stream output to gzipped file
                for line in dump_process.stdout:
                    f.write(line)

                dump_process.wait()
                if dump_process.returncode != 0:
                    error = dump_process.stderr.read().decode()
                    raise Exception(f"Database dump failed: {error}")

            logger.info(f"Database backup created at {output_file}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
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

    def restore_backup(self, backup_path):
        """Restore the application from a backup."""
        try:
            if not self._verify_backup(backup_path):
                raise ValueError("Invalid or corrupted backup")

            with open(os.path.join(backup_path, 'metadata.json'), 'r') as f:
                metadata = json.load(f)

            # First restore schema
            schema_backup_file = os.path.join(backup_path, metadata.get('schema_file'))
            if os.path.exists(schema_backup_file):
                self._restore_schema(schema_backup_file)

            # Then restore data
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

    def _restore_schema(self, backup_file):
        """Restore database schema from backup."""
        try:
            with gzip.open(backup_file, 'rb') as f:
                process = subprocess.Popen([
                    'psql',
                    '--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                        user=os.environ['PGUSER'],
                        password=os.environ['PGPASSWORD'],
                        host=os.environ['PGHOST'],
                        port=os.environ['PGPORT'],
                        dbname=os.environ['PGDATABASE']
                    ),
                    '-X',  # No .psqlrc
                    '-q'   # Quiet mode
                ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                
                process.communicate(input=f.read())
                
                if process.returncode != 0:
                    raise Exception("Schema restore failed")

            logger.info("Database schema restored successfully")
            return True

        except Exception as e:
            logger.error(f"Schema restore failed: {str(e)}")
            raise

    def _restore_database(self, backup_file):
        """Restore database from backup."""
        try:
            with gzip.open(backup_file, 'rb') as f:
                process = subprocess.Popen([
                    'psql',
                    '--dbname=postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                        user=os.environ['PGUSER'],
                        password=os.environ['PGPASSWORD'],
                        host=os.environ['PGHOST'],
                        port=os.environ['PGPORT'],
                        dbname=os.environ['PGDATABASE']
                    ),
                    '-X',  # No .psqlrc
                    '-q'   # Quiet mode
                ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                
                process.communicate(input=f.read())
                
                if process.returncode != 0:
                    raise Exception("Database restore failed")

            logger.info("Database restored successfully")
            return True

        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
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

            # Verify schema backup if it exists in metadata
            if 'schema_file' in metadata:
                schema_backup_file = os.path.join(backup_path, metadata['schema_file'])
                if not os.path.exists(schema_backup_file):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error verifying backup: {str(e)}")
            return False
