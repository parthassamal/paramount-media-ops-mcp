---
name: error-debugging
description: Expert debugging guidance for Paramount+ platform using structured error handling framework. Use when debugging errors, investigating failures, or improving error handling.
---

# Error Debugging Skill

Comprehensive debugging guidance using the custom error handling framework.

## When to Use

Use this skill when:
- Debugging application errors or exceptions
- Investigating API failures
- Analyzing log output
- Improving error handling
- Adding resilience to services
- Troubleshooting integration issues

## Error Handling Framework

### Custom Exception Classes

Located in `mcp/utils/error_handler.py`:

```python
from mcp.utils.error_handler import (
    BaseServiceError,       # Base for all custom exceptions
    ServiceError,           # Generic service error
    ValidationError,        # Input validation failed
    ConnectionError,        # External service connection failed
    TimeoutError,          # Operation timed out
    RateLimitError,        # Rate limit exceeded
    ModelNotFoundError,    # AI model not available
    DataNotFoundError      # Resource not found
)
```

### When to Use Each Exception

- **ValidationError**: Invalid input (empty, wrong format, out of range)
- **ConnectionError**: Can't reach external service (JIRA, NewRelic, etc.)
- **TimeoutError**: Operation took too long
- **RateLimitError**: API rate limit exceeded
- **ModelNotFoundError**: AI model not loaded or missing
- **DataNotFoundError**: Requested resource doesn't exist
- **ServiceError**: Generic service failure (use when others don't fit)

### Retry Logic

Use `@retry_with_backoff` for transient failures:

```python
from mcp.utils.error_handler import retry_with_backoff

@retry_with_backoff(max_retries=3, backoff_factor=2.0, initial_delay=1.0)
async def call_external_api():
    response = await api.fetch()
    return response
```

**Parameters**:
- `max_retries`: Number of retry attempts (default: 3)
- `backoff_factor`: Multiplier for delay (default: 2.0)
- `initial_delay`: First retry delay in seconds (default: 1.0)
- `max_delay`: Cap on delay (default: 60.0)
- `exceptions`: Tuple of exceptions to catch (default: Exception)

### Circuit Breaker

Use `@circuit_breaker` to prevent cascading failures:

```python
from mcp.utils.error_handler import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60.0)
async def call_unreliable_service():
    return await external_service.call()
```

**How it works**:
- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Too many failures, requests fail immediately (fast-fail)
- **HALF_OPEN**: Testing recovery, limited requests allowed

**Parameters**:
- `failure_threshold`: Failures before opening circuit (default: 5)
- `recovery_timeout`: Seconds before attempting recovery (default: 60)

## Structured Logging

### Basic Usage

```python
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Operation started", user_id="123", action="fetch_data")
logger.warning("Slow query", duration_ms=3000, query="SELECT *")
logger.error("Operation failed", error=str(e), retry_count=3)
logger.exception("Unexpected error")  # Includes stack trace
```

### Performance Tracking

```python
from mcp.utils.logger import log_performance

@log_performance(operation="fetch_users", log_args=True, log_result=True)
async def fetch_users(limit: int = 100):
    users = await db.query().limit(limit).all()
    return users
```

Automatically logs:
- Operation start/completion
- Duration in milliseconds
- Result type and size
- Errors with stack traces

### Context Injection

```python
from mcp.utils.logger import set_request_context, clear_request_context

# At request start
set_request_context(request_id="req-abc-123", user_id="user-456")

# All logs now include request_id and user_id
logger.info("Processing request")  # Includes context

# At request end
clear_request_context()
```

## Debugging Workflow

### Step 1: Check Logs
```bash
# View structured logs
tail -f logs/paramount_ops.log | jq

# Filter by error level
tail -f logs/paramount_ops.log | jq 'select(.level == "error")'

# Filter by operation
tail -f logs/paramount_ops.log | jq 'select(.operation == "rag_search")'
```

### Step 2: Check Health
```bash
# Check all AI services
curl http://localhost:8000/api/ai/health

# Check JIRA connectivity
curl http://localhost:8000/api/jira/health

# Check system status
curl http://localhost:8000/status
```

### Step 3: Review Error Context

All exceptions include rich context:
```python
try:
    result = operation()
except ServiceError as e:
    print(e.to_dict())
    # {
    #   "error": "ServiceError",
    #   "message": "Service unavailable",
    #   "details": {"service": "jira", "retry_count": 3},
    #   "timestamp": "2026-01-29T10:00:00Z"
    # }
```

### Step 4: Enable Debug Logging

In `config.py`:
```python
log_level = "DEBUG"  # More verbose logging
```

## Common Issues & Solutions

### Issue: "Model not found"
**Error**: `ModelNotFoundError: Failed to load model X`

**Solution**:
```bash
# Re-run model installation
./scripts/install_ai_models.sh

# Check specific model
python -c "import spacy; spacy.load('en_core_web_sm')"
```

### Issue: "Circuit breaker is OPEN"
**Error**: `ServiceError: Circuit breaker is OPEN - service temporarily unavailable`

**Solution**:
- Wait for recovery timeout (default 60s)
- Check external service health
- Review failure threshold settings
- Check logs for root cause of failures

### Issue: Rate limit exceeded
**Error**: `RateLimitError: JIRA API rate limit exceeded`

**Solution**:
```python
# Add backoff in integration client
@retry_with_backoff(max_retries=5, backoff_factor=3.0)
def fetch_jira_issues():
    # Will wait longer between retries
```

### Issue: Timeout
**Error**: `TimeoutError: Operation timed out after 30s`

**Solution**:
```python
# Increase timeout in client
client = SomeClient(timeout=60.0)

# Or add timeout handling
import asyncio
try:
    result = await asyncio.wait_for(operation(), timeout=60.0)
except asyncio.TimeoutError:
    logger.error("Operation timeout")
    raise TimeoutError("Operation timed out", timeout_seconds=60.0)
```

## Error Handling Patterns

### API Endpoint Pattern
```python
from fastapi import status
from mcp.utils.error_handler import retry_with_backoff
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

@router.post("/endpoint")
@log_performance(operation="endpoint_operation")
@retry_with_backoff(max_retries=2)
async def endpoint(request: RequestModel):
    # Validate input
    if not request.field:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field is required"
        )
    
    try:
        logger.info("Processing request", field=request.field)
        result = await process(request)
        logger.info("Request completed", result_count=len(result))
        return result
    
    except ModelNotFoundError as e:
        logger.error("Model unavailable", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service unavailable"
        )
    
    except ValidationError as e:
        logger.warning("Invalid input", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Integration Client Pattern
```python
from mcp.utils.error_handler import circuit_breaker, ConnectionError
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

class ExternalClient:
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @retry_with_backoff(max_retries=3)
    async def fetch_data(self):
        try:
            response = await self.http_client.get("/api/data")
            return response.json()
        except httpx.ConnectError as e:
            logger.error("Connection failed", service="external_api")
            raise ConnectionError("Unable to connect", service="external_api") from e
```

## Testing Error Handling

Run the test suite:
```bash
# Test error handling framework
pytest tests/test_error_handling.py -v

# Test specific error scenario
pytest tests/test_error_handling.py::TestCircuitBreaker -v

# Test with coverage
pytest tests/test_error_handling.py --cov=mcp.utils --cov-report=html
```

## Monitoring

### Key Metrics to Track
- Error rate by endpoint
- Retry success rate
- Circuit breaker state changes
- Average response time
- Model loading failures

### Health Check Endpoints
- `/api/ai/health` - All AI services
- `/api/jira/health` - JIRA connectivity
- `/status` - Overall system health

## References

- `mcp/utils/error_handler.py` - Error handling framework
- `mcp/utils/logger.py` - Structured logging
- `tests/test_error_handling.py` - Test examples
- `ERROR_HANDLING_SUMMARY.md` - Complete guide
