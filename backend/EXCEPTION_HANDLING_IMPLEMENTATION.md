# Exception Handling & Structured Logging Implementation

## Overview

This document describes the comprehensive exception handling and structured logging system implemented across the backend application. The system provides consistent error handling, detailed logging with context tracking, and proper audit trails.

## Files Created/Modified

### New Files Created

1. **`/app/exceptions/__init__.py`**
   - Custom exception classes for domain-specific errors
   - Base exception class with status code mapping
   - Detailed error information with structured data

2. **`/app/core/logging_config.py`**
   - Structured logging with JSON formatting (production)
   - Colored console logging (development)
   - Context tracking (request ID, user email)
   - Performance logging utilities
   - Audit trail logging

3. **`/app/middleware/exception_handlers.py`**
   - Global exception handlers for all exception types
   - Sanitized error messages for security
   - Structured error responses
   - Database exception handling

4. **`/app/middleware/logging_middleware.py`**
   - Request/response logging with timing
   - Performance monitoring
   - Security event logging
   - Suspicious activity detection

### Files Updated

1. **`/app/api/endpoints/workflow_approvals.py`**
   - Replaced generic exceptions with custom exceptions
   - Added structured logging with context
   - Added performance timing logs
   - Added audit trail for user actions
   - Replaced print statements with proper logging

2. **`/app/api/endpoints/templates.py`** (new version in templates_updated.py)
   - Custom exceptions for template operations
   - Structured logging throughout
   - Audit trail for template CRUD operations
   - Performance monitoring

3. **`/app/services/approval_system.py`**
   - Custom exceptions for approval operations
   - Structured logging with context
   - Better error handling for webhook failures

4. **`/app/main.py`**
   - Integrated structured logging setup
   - Registered exception handlers
   - Added logging middleware stack
   - Updated startup/shutdown logging

## Custom Exception Classes

### Approval System Exceptions

- **`ApprovalNotFoundException`** (404)
  - Raised when approval request not found
  - Includes approval ID in details

- **`ApprovalAlreadyProcessedException`** (409)
  - Raised when trying to process already-processed approval
  - Includes current status and decided timestamp

- **`ApprovalTimeoutException`** (410)
  - Raised when approval request has timed out
  - Includes timeout timestamp

- **`ApprovalValidationException`** (422)
  - Raised when approval data fails validation
  - Includes validation error details

### Template Exceptions

- **`TemplateNotFoundException`** (404)
  - Raised when template not found
  - Includes template ID

- **`TemplateValidationException`** (400)
  - Raised when template content fails validation
  - Includes field name and validation errors

- **`TemplateSecurityException`** (400)
  - Raised when template contains security violations
  - Includes list of security issues

- **`TemplateInUseException`** (409)
  - Raised when trying to delete template in use
  - Includes count of active responses

### Workflow Exceptions

- **`WorkflowExecutionException`** (500)
  - Raised when workflow execution fails
  - Includes workflow ID and error details

- **`WorkflowWebhookException`** (502)
  - Raised when webhook communication fails
  - Includes webhook URL and response data

### General Exceptions

- **`RateLimitExceededException`** (429)
  - Raised when rate limit exceeded
  - Includes retry-after information

- **`DatabaseException`** (500)
  - Raised when database operations fail
  - Sanitized messages for security

- **`ResourceNotFoundException`** (404)
  - Generic resource not found exception
  - Includes resource type and ID

- **`ExternalServiceException`** (503)
  - Raised when external service fails
  - Includes service name and status code

- **`AuthenticationException`** (401)
  - Authentication failures

- **`AuthorizationException`** (403)
  - Authorization/permission failures

## Structured Logging Features

### Context Tracking

All log entries include:
- **Request ID**: Unique identifier for request tracing
- **User ID/Email**: From authentication headers
- **Timestamp**: ISO 8601 format
- **Module/Function**: Code location
- **Log Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Log Types

1. **Standard Logs**
   ```python
   logger.info("Operation completed", param1="value", param2=123)
   ```

2. **Audit Logs**
   ```python
   logger.audit(
       "approval_created",
       "approval_request",
       approval_id,
       approval_type="demo_site_review"
   )
   ```

3. **Performance Logs**
   ```python
   logger.performance(
       "create_approval",
       duration_seconds,
       approval_id=123,
       success=True
   )
   ```

### Log Formats

**Development**: Colored console output
```
[2025-11-05 21:30:45] INFO [app.api.endpoints.workflow_approvals] Creating approval request [req=abc123, user=user@example.com]
```

**Production**: JSON format
```json
{
  "timestamp": "2025-11-05T21:30:45.123456",
  "level": "INFO",
  "logger": "app.api.endpoints.workflow_approvals",
  "message": "Creating approval request",
  "request_id": "abc123",
  "user_email": "user@example.com",
  "extra": {
    "approval_type": "demo_site_review",
    "resource_id": 456
  }
}
```

### Log Files (Production)

- **`logs/app.log`**: General application logs (INFO+)
- **`logs/error.log`**: Error logs only (ERROR+)
- **`logs/audit.log`**: Audit trail logs
- Rotation: 10MB max size, 5-10 backups

## Middleware Stack

The middleware is applied in this order (last added = first executed):

1. **SecurityLoggingMiddleware**
   - Logs authentication failures (401)
   - Logs authorization failures (403)
   - Detects suspicious patterns (SQL injection, XSS, path traversal)

2. **PerformanceLoggingMiddleware**
   - Tracks request duration
   - Logs slow requests (>1s threshold)
   - Performance metrics per endpoint

3. **RequestLoggingMiddleware**
   - Generates unique request IDs
   - Logs request start/completion
   - Tracks user information
   - Audit trail for sensitive operations
   - Adds X-Request-ID header to responses

## Exception Handler Flow

```
Request → Middleware → Endpoint → Exception?
                                      ↓
                          ┌──────────────────────┐
                          │ Custom Exception?    │
                          │ (BaseAppException)   │
                          └──────────────────────┘
                                      ↓ Yes
                          ┌──────────────────────┐
                          │ Custom Exception     │
                          │ Handler              │
                          │ - Structured response│
                          │ - Appropriate status │
                          └──────────────────────┘
                                      ↓ No
                          ┌──────────────────────┐
                          │ Validation Error?    │
                          │ (Pydantic)           │
                          └──────────────────────┘
                                      ↓ Yes
                          ┌──────────────────────┐
                          │ Validation Handler   │
                          │ - Field-level errors │
                          │ - 422 status         │
                          └──────────────────────┘
                                      ↓ No
                          ┌──────────────────────┐
                          │ Database Error?      │
                          │ (SQLAlchemy)         │
                          └──────────────────────┘
                                      ↓ Yes
                          ┌──────────────────────┐
                          │ Database Handler     │
                          │ - Sanitized messages │
                          │ - 500/503 status     │
                          └──────────────────────┘
                                      ↓ No
                          ┌──────────────────────┐
                          │ Generic Handler      │
                          │ - Safe error message │
                          │ - 500 status         │
                          │ - Full error logged  │
                          └──────────────────────┘
```

## Error Response Format

All errors return this consistent structure:

```json
{
  "error": {
    "code": "APPROVAL_NOT_FOUND",
    "message": "Approval with ID 123 not found",
    "details": {
      "approval_id": 123
    }
  },
  "request_id": "abc123def",
  "timestamp": "2025-11-05T21:30:45.123456",
  "path": "/api/v1/workflows/approvals/123"
}
```

## Usage Examples

### Raising Custom Exceptions

```python
from app.exceptions import ApprovalNotFoundException

# In your endpoint or service
if not approval:
    raise ApprovalNotFoundException(approval_id)
```

### Structured Logging

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Info log with context
logger.info("Processing approval", approval_id=123, approval_type="demo_site")

# Error log with exception
try:
    result = await process_approval()
except Exception as e:
    logger.error("Failed to process approval", exc_info=e, approval_id=123)
    raise

# Performance log
start_time = datetime.utcnow()
result = await expensive_operation()
duration = (datetime.utcnow() - start_time).total_seconds()
logger.performance("expensive_operation", duration, success=True)

# Audit log
logger.audit(
    "approval_decision",
    "approval_request",
    approval_id,
    approved=True,
    reviewer_email="reviewer@example.com"
)
```

### Adding Context to Requests

The middleware automatically sets request context, but you can also set it manually:

```python
from app.core.logging_config import set_request_context

set_request_context(
    request_id="abc123",
    user_id="user_456",
    user_email="user@example.com"
)
```

## Security Features

### 1. Error Message Sanitization
- Database errors: Generic messages, detailed logs
- Never expose stack traces to clients
- Sanitize SQL errors to prevent information leakage

### 2. Suspicious Activity Detection
- SQL injection patterns
- XSS attempts
- Path traversal attempts
- Logged with client IP and details

### 3. Authentication Tracking
- Failed login attempts
- Missing/invalid tokens
- Authorization failures
- All logged for security audit

## Performance Considerations

### 1. Logging Overhead
- JSON formatting only in production
- Async logging (non-blocking)
- Log rotation to manage disk space

### 2. Context Storage
- Uses Python contextvars (thread-safe)
- Automatic cleanup after request
- Minimal memory overhead

### 3. Exception Handling
- Fast exception mapping
- Minimal object creation
- Efficient JSON serialization

## Testing

### Test Custom Exceptions

```python
from app.exceptions import ApprovalNotFoundException

def test_approval_not_found_exception():
    exc = ApprovalNotFoundException(123)
    assert exc.status_code == 404
    assert exc.error_code == "APPROVAL_NOT_FOUND"
    assert exc.approval_id == 123

    response_dict = exc.to_dict()
    assert response_dict["message"] == "Approval with ID 123 not found"
```

### Test Exception Handlers

```python
from fastapi.testclient import TestClient

def test_approval_not_found_response(client: TestClient):
    response = client.get("/api/v1/workflows/approvals/999999")
    assert response.status_code == 404

    data = response.json()
    assert data["error"]["code"] == "APPROVAL_NOT_FOUND"
    assert "request_id" in data
    assert "timestamp" in data
```

### Test Logging

```python
from app.core.logging_config import get_logger

def test_structured_logging(caplog):
    logger = get_logger("test")
    logger.info("Test message", param1="value1", param2=123)

    # Check log record
    record = caplog.records[0]
    assert hasattr(record, "extra_data")
    assert record.extra_data["param1"] == "value1"
```

## Migration Guide

### Before (Generic Exceptions)

```python
try:
    result = await operation()
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### After (Custom Exceptions)

```python
from app.exceptions import DatabaseException
from app.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    logger.info("Starting operation", param1="value")
    result = await operation()
    logger.audit("operation_completed", "resource_type", resource_id)
except SomeSpecificError as e:
    logger.error("Operation failed", exc_info=e)
    raise DatabaseException(
        message="Operation failed",
        operation="operation_name",
        details={"error": str(e)}
    )
```

## Benefits

1. **Consistency**: All errors follow same format
2. **Traceability**: Request IDs for debugging
3. **Security**: Sanitized error messages
4. **Auditability**: Complete audit trail
5. **Debugging**: Structured logs with context
6. **Monitoring**: Easy to parse JSON logs
7. **Performance**: Timing logs for bottlenecks
8. **Compliance**: Audit logs for regulations

## Future Enhancements

1. **Centralized Logging**: Send logs to ELK/Splunk
2. **Metrics**: Export performance metrics to Prometheus
3. **Alerting**: Alert on error rates/slow requests
4. **Distributed Tracing**: OpenTelemetry integration
5. **Log Sampling**: Sample high-volume logs
6. **Log Levels by Module**: Fine-grained control

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json             # json or colored
ENVIRONMENT=production      # development or production

# Security
ENABLE_SECURITY_LOGGING=true
ENABLE_AUDIT_LOGGING=true
```

### Settings

```python
# app/core/config.py
class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENVIRONMENT: str = "production"
```

## Conclusion

This implementation provides enterprise-grade error handling and logging with:
- ✅ Custom domain-specific exceptions
- ✅ Structured logging with context
- ✅ Global exception handlers
- ✅ Request/response logging
- ✅ Performance monitoring
- ✅ Security event logging
- ✅ Audit trail
- ✅ Sanitized error messages

All endpoints now have consistent error handling, detailed logging, and proper audit trails.
