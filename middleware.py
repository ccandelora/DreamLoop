from flask import request, g
import time
import logging
from uuid import uuid4
from functools import wraps

logger = logging.getLogger(__name__)

def log_request():
    """Log incoming request details."""
    g.start_time = time.time()
    request_id = request.headers.get('X-Request-ID', str(uuid4()))
    g.request_id = request_id
    
    logger.info(
        f"Request started: {request.method} {request.url}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.user_agent.string
        }
    )

def log_response(response):
    """Log response details."""
    if not hasattr(g, 'start_time'):
        return response
    
    request_time = time.time() - g.start_time
    status_code = response.status_code
    request_id = getattr(g, 'request_id', '-')
    
    logger.info(
        f"Request completed: {request.method} {request.url}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status': status_code,
            'duration': f"{request_time:.2f}s",
            'content_length': response.content_length
        }
    )
    
    return response

def setup_request_logging(app):
    """Setup request logging middleware."""
    app.before_request(log_request)
    app.after_request(log_response)

def log_function_execution(f):
    """Decorator to log function execution time and details."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Starting execution of {f.__name__}")
        
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"Completed execution of {f.__name__}",
                extra={
                    'execution_time': f"{execution_time:.2f}s",
                    'success': True
                }
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Error in {f.__name__}: {str(e)}",
                extra={
                    'execution_time': f"{execution_time:.2f}s",
                    'success': False,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
    
    return decorated_function