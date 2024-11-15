import logging
from datetime import datetime
from sqlalchemy import text, inspect
from extensions import db, session_manager
import threading
import time
from flask import current_app
import atexit

logger = logging.getLogger(__name__)

class DatabaseHealthCheck:
    def __init__(self, check_interval=60):
        self.check_interval = check_interval
        self.is_running = False
        self.monitoring_thread = None
        self.last_check_time = None
        self.health_status = {
            'status': 'unknown',
            'last_check': None,
            'connection_pool': None,
            'schema_status': None,
            'long_transactions': None,
            'deadlocks': None
        }
        self._app = None

    def init_app(self, app):
        """Initialize the health checker with the Flask app."""
        self._app = app
        self.perform_health_check()  # Initial health check
        atexit.register(self.stop_monitoring)

    def start_monitoring(self):
        """Start the health check monitoring in a background thread."""
        if not self.is_running and self._app:
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("Database health monitoring started")

    def stop_monitoring(self):
        """Stop the health check monitoring."""
        if self.is_running:
            self.is_running = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            logger.info("Database health monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop that runs health checks periodically."""
        while self.is_running:
            try:
                self.perform_health_check()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in health check monitoring loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

    def perform_health_check(self):
        """Perform a comprehensive health check of the database."""
        if not self._app:
            logger.error("Application context not initialized")
            return False

        try:
            with self._app.app_context():
                with session_manager.session_scope() as session:
                    # Basic connectivity check
                    session.execute(text("SELECT 1"))
                    
                    # Check schema status
                    schema_status = self._check_schema_status(session)
                    
                    # Check connection pool status
                    pool_status = self._check_pool_status(session)
                    
                    # Check for long-running transactions
                    long_transactions = self._check_long_transactions(session)
                    
                    # Check for deadlocks
                    deadlocks = self._check_deadlocks(session)
                    
                    # Get database size
                    db_size = self._get_database_size(session)
                    
                    # Get connection info
                    conn_info = self._get_connection_info(session)
                    
                    # Update health status
                    self.health_status = {
                        'status': 'healthy',
                        'last_check': datetime.utcnow().isoformat(),
                        'schema_status': schema_status,
                        'connection_pool': pool_status,
                        'long_transactions': long_transactions,
                        'deadlocks': deadlocks,
                        'database_size': db_size,
                        'connection_info': conn_info
                    }
                    
                    logger.info("Health check completed successfully")
                    return True
                    
        except Exception as e:
            self.health_status = {
                'status': 'unhealthy',
                'last_check': datetime.utcnow().isoformat(),
                'error': str(e)
            }
            logger.error(f"Health check failed: {str(e)}")
            return False

    def _check_schema_status(self, session):
        """Verify database schema status."""
        try:
            engine = session.get_bind()
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            expected_tables = ['user', 'dream', 'comment', 'dream_group', 
                             'group_membership', 'forum_post', 'forum_reply', 
                             'user_activity']
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            table_details = {}
            for table in tables:
                columns = inspector.get_columns(table)
                table_details[table] = {
                    'columns': [column['name'] for column in columns],
                    'primary_key': inspector.get_pk_constraint(table),
                    'foreign_keys': inspector.get_foreign_keys(table),
                    'indexes': inspector.get_indexes(table)
                }
            
            return {
                'status': 'valid' if not missing_tables else 'invalid',
                'missing_tables': missing_tables,
                'existing_tables': tables,
                'table_details': table_details
            }
        except Exception as e:
            logger.error(f"Error checking schema status: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _check_pool_status(self, session):
        """Check the status of the connection pool."""
        try:
            result = session.execute(text("""
                SELECT 
                    sum(case when state = 'active' then 1 else 0 end) as active_connections,
                    count(*) as total_connections,
                    sum(case when state = 'idle' then 1 else 0 end) as idle_connections,
                    sum(case when state = 'idle in transaction' then 1 else 0 end) as idle_in_transaction
                FROM pg_stat_activity 
                WHERE backend_type = 'client backend'
            """))
            stats = result.fetchone()
            
            engine = session.get_bind()
            pool = engine.pool
            
            return {
                'active_connections': stats[0] or 0,
                'total_connections': stats[1] or 0,
                'idle_connections': stats[2] or 0,
                'idle_in_transaction': stats[3] or 0,
                'pool_size': getattr(pool, '_size', 0),
                'overflow': getattr(pool, '_overflow', 0),
                'timeout': getattr(pool, '_timeout', 0)
            }
        except Exception as e:
            logger.error(f"Error checking pool status: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _check_long_transactions(self, session):
        """Check for long-running transactions."""
        try:
            result = session.execute(text("""
                SELECT pid, usename, application_name, 
                       state, query_start, xact_start,
                       EXTRACT(EPOCH FROM (now() - query_start)) as query_duration,
                       query
                FROM pg_stat_activity 
                WHERE state = 'active'
                  AND xact_start IS NOT NULL 
                  AND EXTRACT(EPOCH FROM (now() - xact_start)) > 300
                ORDER BY query_duration DESC
            """))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error checking long transactions: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _check_deadlocks(self, session):
        """Check for deadlocks and blocking queries."""
        try:
            result = session.execute(text("""
                SELECT blocked_locks.pid AS blocked_pid,
                       blocking_locks.pid AS blocking_pid,
                       blocked_activity.usename AS blocked_user,
                       blocking_activity.usename AS blocking_user,
                       blocked_activity.query AS blocked_statement,
                       blocking_activity.query AS blocking_statement,
                       blocked_activity.wait_event_type,
                       blocked_activity.wait_event
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_locks blocking_locks 
                    ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted;
            """))
            return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error checking deadlocks: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _get_database_size(self, session):
        """Get the current database size and related statistics."""
        try:
            result = session.execute(text("""
                SELECT pg_database_size(current_database()) as db_size,
                       pg_size_pretty(pg_database_size(current_database())) as db_size_pretty
            """))
            row = result.fetchone()
            return {
                'size_bytes': row.db_size,
                'size_pretty': row.db_size_pretty
            }
        except Exception as e:
            logger.error(f"Error getting database size: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _get_connection_info(self, session):
        """Get detailed connection information."""
        try:
            result = session.execute(text("""
                SELECT version() as postgresql_version,
                       current_setting('max_connections') as max_connections,
                       current_setting('timezone') as timezone
            """))
            row = result.fetchone()
            return {
                'postgresql_version': row.postgresql_version,
                'max_connections': row.max_connections,
                'timezone': row.timezone
            }
        except Exception as e:
            logger.error(f"Error getting connection info: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def get_health_status(self):
        """Get the current health status."""
        if not self.health_status['last_check']:
            self.perform_health_check()
        return self.health_status

# Create a singleton instance
health_checker = DatabaseHealthCheck()
