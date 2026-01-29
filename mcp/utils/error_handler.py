"""
Comprehensive error handling framework with custom exceptions, retry logic, and circuit breakers.

This module provides:
- Domain-specific exception classes
- Retry decorators with exponential backoff
- Circuit breaker pattern for external services
- Error context tracking
"""

import functools
import time
import asyncio
from typing import Optional, Dict, Any, Callable, TypeVar, Type
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


# =============================================================================
# Custom Exception Classes
# =============================================================================

class BaseServiceError(Exception):
    """Base exception for all service errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class ServiceError(BaseServiceError):
    """Generic service error."""
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if service:
            details["service"] = service
        super().__init__(message, details=details, **kwargs)


class ValidationError(BaseServiceError):
    """Input validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, **kwargs)


class ConnectionError(BaseServiceError):
    """Connection to external service failed."""
    
    def __init__(self, message: str, service: str, **kwargs):
        details = kwargs.pop("details", {})
        details["service"] = service
        super().__init__(message, error_code="CONNECTION_ERROR", details=details, **kwargs)


class TimeoutError(BaseServiceError):
    """Operation timed out."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        details = kwargs.pop("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, error_code="TIMEOUT_ERROR", details=details, **kwargs)


class RateLimitError(BaseServiceError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details, **kwargs)


class ModelNotFoundError(BaseServiceError):
    """AI model not found or failed to load."""
    
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if model_name:
            details["model_name"] = model_name
        super().__init__(message, error_code="MODEL_NOT_FOUND", details=details, **kwargs)


class DataNotFoundError(BaseServiceError):
    """Requested data not found."""
    
    def __init__(self, message: str, resource: Optional[str] = None, **kwargs):
        details = kwargs.pop("details", {})
        if resource:
            details["resource"] = resource
        super().__init__(message, error_code="DATA_NOT_FOUND", details=details, **kwargs)


# =============================================================================
# Retry Decorator with Exponential Backoff
# =============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    logger_name: Optional[str] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry
        logger_name: Logger name for logging retry attempts
    
    Example:
        @retry_with_backoff(max_retries=3, backoff_factor=2)
        async def fetch_data():
            return await api_call()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            log = structlog.get_logger(logger_name or func.__module__)
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        log.error(
                            "Max retries exceeded",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e)
                        )
                        raise
                    
                    log.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=delay,
                        error=str(e)
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            log = structlog.get_logger(logger_name or func.__module__)
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        log.error(
                            "Max retries exceeded",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e)
                        )
                        raise
                    
                    log.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=delay,
                        error=str(e)
                    )
                    
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
            else:
                raise ServiceError(
                    "Circuit breaker is OPEN - service temporarily unavailable",
                    details={
                        "state": self._state,
                        "failures": self._failure_count,
                        "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None
                    }
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection."""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
            else:
                raise ServiceError(
                    "Circuit breaker is OPEN - service temporarily unavailable",
                    details={
                        "state": self._state,
                        "failures": self._failure_count
                    }
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self._last_failure_time:
            return True
        return (datetime.utcnow() - self._last_failure_time).total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self._failure_count = 0
        self._state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            logger.warning(
                "Circuit breaker opened",
                failures=self._failure_count,
                threshold=self.failure_threshold
            )


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to track for failures
    
    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        async def call_external_api():
            return await api.fetch()
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            return await breaker.call_async(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return breaker.call(func, *args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# =============================================================================
# Error Handling Decorator
# =============================================================================

def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    raise_on_error: bool = True
):
    """
    General purpose error handling decorator.
    
    Args:
        default_return: Value to return on error (if raise_on_error=False)
        log_errors: Whether to log errors
        raise_on_error: Whether to re-raise exceptions
    
    Example:
        @handle_errors(default_return=[], log_errors=True)
        def get_items():
            return fetch_items()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.exception(
                        "Error in function",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                
                if raise_on_error:
                    raise
                return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.exception(
                        "Error in function",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                
                if raise_on_error:
                    raise
                return default_return
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
