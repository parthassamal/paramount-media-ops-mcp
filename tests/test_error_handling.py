"""
Test suite for error handling framework.

Tests custom exceptions, retry logic, circuit breakers, and logging.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from mcp.utils.error_handler import (
    BaseServiceError,
    ServiceError,
    ValidationError,
    ConnectionError,
    TimeoutError,
    RateLimitError,
    ModelNotFoundError,
    DataNotFoundError,
    retry_with_backoff,
    circuit_breaker,
    CircuitBreaker
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_base_service_error(self):
        """Test BaseServiceError with all parameters."""
        error = BaseServiceError(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
            original_error=ValueError("original")
        )
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert isinstance(error.original_error, ValueError)
        assert error.timestamp is not None
    
    def test_service_error(self):
        """Test ServiceError with service name."""
        error = ServiceError("Service failed", service="external_api")
        
        assert error.message == "Service failed"
        assert error.details["service"] == "external_api"
    
    def test_validation_error(self):
        """Test ValidationError with field name."""
        error = ValidationError("Invalid input", field="username")
        
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "username"
    
    def test_connection_error(self):
        """Test ConnectionError."""
        error = ConnectionError("Connection failed", service="database")
        
        assert error.message == "Connection failed"
        assert error.error_code == "CONNECTION_ERROR"
        assert error.details["service"] == "database"
    
    def test_timeout_error(self):
        """Test TimeoutError with timeout value."""
        error = TimeoutError("Operation timed out", timeout_seconds=30.0)
        
        assert error.message == "Operation timed out"
        assert error.error_code == "TIMEOUT_ERROR"
        assert error.details["timeout_seconds"] == 30.0
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        
        assert error.message == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert error.details["retry_after_seconds"] == 60
    
    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("Model not found", model_name="gpt-4")
        
        assert error.message == "Model not found"
        assert error.error_code == "MODEL_NOT_FOUND"
        assert error.details["model_name"] == "gpt-4"
    
    def test_data_not_found_error(self):
        """Test DataNotFoundError."""
        error = DataNotFoundError("Data not found", resource="user")
        
        assert error.message == "Data not found"
        assert error.error_code == "DATA_NOT_FOUND"
        assert error.details["resource"] == "user"
    
    def test_error_to_dict(self):
        """Test error conversion to dictionary."""
        error = ServiceError("Test error", service="api")
        error_dict = error.to_dict()
        
        assert error_dict["error"] == "ServiceError"
        assert error_dict["message"] == "Test error"
        assert "service" in error_dict["details"]
        assert "timestamp" in error_dict


class TestRetryDecorator:
    """Test retry decorator with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_retries=3)
        async def test_func():
            return mock_func()
        
        result = await test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test function succeeds after retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Failed", service="test")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """Test function fails after max retries."""
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        async def test_func():
            raise ConnectionError("Always fails", service="test")
        
        with pytest.raises(ConnectionError):
            await test_func()
    
    def test_retry_sync_function(self):
        """Test retry decorator with sync function."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Failed")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 2


class TestCircuitBreaker:
    """Test circuit breaker pattern."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state (normal operation)."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def test_func():
            return "success"
        
        result = breaker.call(test_func)
        assert result == "success"
        assert breaker._state == "CLOSED"
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise ValueError("Failed")
        
        # First failure
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker._failure_count == 1
        assert breaker._state == "CLOSED"
        
        # Second failure - should open circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        assert breaker._failure_count == 2
        assert breaker._state == "OPEN"
    
    def test_circuit_breaker_open_rejects_calls(self):
        """Test circuit breaker rejects calls when open."""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise ValueError("Failed")
        
        # Trigger failure to open circuit
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        
        # Circuit should be open, calls rejected
        with pytest.raises(ServiceError, match="Circuit breaker is OPEN"):
            breaker.call(lambda: "success")
    
    def test_circuit_breaker_resets_on_success(self):
        """Test circuit breaker resets failure count on success."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def sometimes_fails():
            if breaker._failure_count < 2:
                raise ValueError("Failed")
            return "success"
        
        # Two failures
        with pytest.raises(ValueError):
            breaker.call(sometimes_fails)
        with pytest.raises(ValueError):
            breaker.call(sometimes_fails)
        
        assert breaker._failure_count == 2
        
        # Success should reset
        result = breaker.call(sometimes_fails)
        assert result == "success"
        assert breaker._failure_count == 0
        assert breaker._state == "CLOSED"


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_async(self):
        """Test circuit breaker decorator with async function."""
        call_count = 0
        
        @circuit_breaker(failure_threshold=2, recovery_timeout=0.1)
        async def test_func(should_fail: bool = False):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Failed")
            return "success"
        
        # Successful call
        result = await test_func(should_fail=False)
        assert result == "success"
        
        # Two failures to open circuit
        with pytest.raises(ValueError):
            await test_func(should_fail=True)
        with pytest.raises(ValueError):
            await test_func(should_fail=True)
        
        # Circuit should be open
        with pytest.raises(ServiceError):
            await test_func(should_fail=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
