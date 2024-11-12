import logging
from logging.handlers import RotatingFileHandler
import os
from flask import request, has_request_context
import traceback
from datetime import datetime

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.request_id = request.headers.get('X-Request-ID', '-')
        else:
            record.url = None
            record.remote_addr = None
            record.method = None
            record.request_id = None
        
        return super().format(record)

def setup_logging(app):
    """Configure application-wide logging."""
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure formatters
    console_formatter = RequestFormatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    file_formatter = RequestFormatter(
        '%(asctime)s - %(request_id)s - %(remote_addr)s - %(method)s %(url)s\n'
        'Level: %(levelname)s\n'
        'Module: %(module)s\n'
        'Message: %(message)s\n'
    )

    # Configure handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Rotating file handler for all logs
    all_logs_handler = RotatingFileHandler(
        'logs/dreamshare.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    all_logs_handler.setFormatter(file_formatter)
    all_logs_handler.setLevel(logging.INFO)

    # Separate handler for errors
    error_logs_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_logs_handler.setFormatter(file_formatter)
    error_logs_handler.setLevel(logging.ERROR)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(all_logs_handler)
    root_logger.addHandler(error_logs_handler)

    # Configure Flask logger
    app.logger.setLevel(logging.INFO)
    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
    app.logger.addHandler(console_handler)
    app.logger.addHandler(all_logs_handler)
    app.logger.addHandler(error_logs_handler)

class ErrorLogger:
    @staticmethod
    def log_error(error, context=None):
        """Log an error with additional context."""
        logger = logging.getLogger('error_logger')
        error_details = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        if has_request_context():
            error_details.update({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'remote_addr': request.remote_addr
            })
        
        logger.error(f"Application Error: {error_details}")
        return error_details
