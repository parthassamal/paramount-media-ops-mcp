"""
Structured logging utilities with context injection and performance tracking.

This module provides:
- Structured JSON logging with context
- Request ID correlation
- Performance tracking
- Log level filtering
- Error correlation
"""

import functools
import time
import uuid
from typing import Optional, Dict, Any, Callable, TypeVar
from contextvars import ContextVar
import structlog
from datetime import datetime

T = TypeVar('T')

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


# =============================================================================
# Logger Configuration
# =============================================================================

def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
    include_timestamp: bool = True
):
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output JSON format (vs. console format)
        include_timestamp: Whether to include timestamps in logs
    """
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if include_timestamp:
        processors.insert(0, structlog.processors.TimeStamper(fmt="iso"))
    
    # Add context injection
    processors.append(inject_context)
    
    # Choose renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog.stdlib.logging, log_level, structlog.stdlib.logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def inject_context(logger, method_name, event_dict):
    """Inject request context into log entries."""
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    
    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id
    
    return event_dict


# =============================================================================
# Logger Functions
# =============================================================================

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Configured structured logger
    
    Example:
        logger = get_logger(__name__)
        logger.info("Operation started", operation="data_fetch", count=100)
    """
    return structlog.get_logger(name)


def set_request_context(request_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Set request context for correlation.
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier
    
    Example:
        set_request_context(request_id="req-123", user_id="user-456")
    """
    if request_id:
        request_id_var.set(request_id)
    else:
        request_id_var.set(str(uuid.uuid4()))
    
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context."""
    request_id_var.set(None)
    user_id_var.set(None)


# =============================================================================
# Performance Tracking
# =============================================================================

def log_performance(
    operation: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    level: str = "info"
):
    """
    Decorator to log function performance metrics.
    
    Args:
        operation: Operation name (defaults to function name)
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        level: Log level (debug, info, warning, error)
    
    Example:
        @log_performance(operation="fetch_users", log_args=True)
        async def fetch_users(limit: int = 100):
            return await db.query(User).limit(limit).all()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__
        logger = get_logger(func.__module__)
        log_func = getattr(logger, level, logger.info)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            log_data = {
                "operation": op_name,
                "status": "started"
            }
            
            if log_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)
            
            log_func("Operation started", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                
                elapsed = time.perf_counter() - start_time
                log_data.update({
                    "status": "completed",
                    "duration_ms": round(elapsed * 1000, 2)
                })
                
                if log_result:
                    log_data["result_type"] = type(result).__name__
                    if isinstance(result, (list, dict, set)):
                        log_data["result_size"] = len(result)
                
                log_func("Operation completed", **log_data)
                
                return result
            
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    "Operation failed",
                    operation=op_name,
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            log_data = {
                "operation": op_name,
                "status": "started"
            }
            
            if log_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)
            
            log_func("Operation started", **log_data)
            
            try:
                result = func(*args, **kwargs)
                
                elapsed = time.perf_counter() - start_time
                log_data.update({
                    "status": "completed",
                    "duration_ms": round(elapsed * 1000, 2)
                })
                
                if log_result:
                    log_data["result_type"] = type(result).__name__
                    if isinstance(result, (list, dict, set)):
                        log_data["result_size"] = len(result)
                
                log_func("Operation completed", **log_data)
                
                return result
            
            except Exception as e:
                elapsed = time.perf_counter() - start_time
                logger.error(
                    "Operation failed",
                    operation=op_name,
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        return async_wrapper if callable(getattr(func, '__await__', None)) else sync_wrapper
    
    return decorator


# =============================================================================
# Contextual Logging
# =============================================================================

class LogContext:
    """
    Context manager for adding structured context to logs.
    
    Example:
        with LogContext(operation="data_import", source="s3"):
            logger.info("Starting import")
            process_data()
            logger.info("Import complete")
    """
    
    def __init__(self, **context):
        self.context = context
        self.logger = get_logger("context")
        self.bound_logger = None
    
    def __enter__(self):
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.bound_logger.error(
                "Context exited with error",
                error=str(exc_val),
                error_type=exc_type.__name__
            )
        return False


# =============================================================================
# Audit Logging
# =============================================================================

def audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Create audit log entry for important actions.
    
    Args:
        action: Action performed (create, update, delete, access)
        resource_type: Type of resource (user, document, config)
        resource_id: Unique identifier for the resource
        details: Additional details about the action
    
    Example:
        audit_log("delete", "jira_ticket", "TICKET-123", {"reason": "duplicate"})
    """
    logger = get_logger("audit")
    
    log_data = {
        "audit": True,
        "action": action,
        "resource_type": resource_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if resource_id:
        log_data["resource_id"] = resource_id
    
    if details:
        log_data["details"] = details
    
    # Add request context
    request_id = request_id_var.get()
    if request_id:
        log_data["request_id"] = request_id
    
    user_id = user_id_var.get()
    if user_id:
        log_data["user_id"] = user_id
    
    logger.info("Audit log entry", **log_data)


# Initialize default logging configuration
configure_logging()
