import logging
from datetime import datetime
from functools import wraps
from flask import g, current_app
from sqlalchemy import text
from extensions import db, session_manager
from logging_config import ErrorLogger

logger = logging.getLogger(__name__)

class TransactionDebugger:
    def __init__(self):
        self.transaction_history = []
        self.active_transactions = {}

    def log_transaction_start(self, session_id, info=None):
        """Log the start of a transaction."""
        start_time = datetime.utcnow()
        self.active_transactions[session_id] = {
            'start_time': start_time,
            'info': info or {},
            'queries': []
        }
        logger.debug(f"Transaction started - Session ID: {session_id}")

    def log_transaction_end(self, session_id, status='committed'):
        """Log the end of a transaction."""
        if session_id in self.active_transactions:
            transaction = self.active_transactions[session_id]
            duration = datetime.utcnow() - transaction['start_time']
            self.transaction_history.append({
                'session_id': session_id,
                'start_time': transaction['start_time'],
                'end_time': datetime.utcnow(),
                'duration': duration.total_seconds(),
                'status': status,
                'queries': transaction['queries']
            })
            del self.active_transactions[session_id]
            logger.debug(f"Transaction {status} - Session ID: {session_id}, Duration: {duration.total_seconds()}s")

    def log_query(self, session_id, query, params=None):
        """Log a query within a transaction."""
        if session_id in self.active_transactions:
            self.active_transactions[session_id]['queries'].append({
                'timestamp': datetime.utcnow(),
                'query': str(query),
                'params': params
            })

    def get_active_transactions(self):
        """Get currently active transactions."""
        try:
            with session_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT pid, usename, application_name, client_addr, 
                           backend_start, xact_start, query_start, query,
                           state, wait_event_type
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                    AND xact_start IS NOT NULL;
                """))
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting active transactions: {str(e)}")
            return []

    def check_for_locks(self):
        """Check for locks and potential deadlocks."""
        try:
            with session_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT blocked_locks.pid AS blocked_pid,
                           blocking_locks.pid AS blocking_pid,
                           blocked_activity.usename AS blocked_user,
                           blocking_activity.usename AS blocking_user,
                           blocked_activity.query AS blocked_statement,
                           blocking_activity.query AS blocking_statement
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
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error checking for locks: {str(e)}")
            return []

    def get_transaction_stats(self):
        """Get transaction statistics."""
        try:
            with session_manager.session_scope() as session:
                result = session.execute(text("""
                    SELECT datname, numbackends, xact_commit, xact_rollback,
                           blks_read, blks_hit, tup_returned, tup_fetched,
                           tup_inserted, tup_updated, tup_deleted
                    FROM pg_stat_database
                    WHERE datname = current_database();
                """))
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting transaction stats: {str(e)}")
            return []

def debug_transaction(f):
    """Decorator to debug database transactions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        debugger = current_app.transaction_debugger
        session_id = id(g.get('db_session', None))
        
        try:
            debugger.log_transaction_start(session_id, {
                'function': f.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            })
            
            result = f(*args, **kwargs)
            
            debugger.log_transaction_end(session_id, 'committed')
            return result
            
        except Exception as e:
            debugger.log_transaction_end(session_id, 'rolled_back')
            ErrorLogger.log_error(e, {
                'transaction_id': session_id,
                'function': f.__name__
            })
            raise
            
    return decorated_function

def init_transaction_debugger(app):
    """Initialize the transaction debugger for the application."""
    app.transaction_debugger = TransactionDebugger()
    logger.info("Transaction debugger initialized")
