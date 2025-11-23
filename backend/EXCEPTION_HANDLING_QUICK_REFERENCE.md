# Exception Handling & Logging Quick Reference

## Quick Start

### Import Required Modules

```python
from app.exceptions import (
    ApprovalNotFoundException,
    TemplateValidationException,
    DatabaseException
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)
```

## Common Patterns

### 1. Endpoint with Exception Handling

```python
@router.post("/items/{item_id}")
async def update_item(
    item_id: int,
    data: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    start_time = datetime.utcnow()

    try:
        # Log operation start
        logger.info(f"Updating item {item_id}", item_id=item_id)

        # Fetch resource
        item = await get_item(db, item_id)
        if not item:
            raise ResourceNotFoundException("item", item_id)

        # Update
        updated_item = await update_item_data(db, item, data)

        # Performance log
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.performance("update_item", duration, item_id=item_id)

        # Audit log
        logger.audit("item_updated", "item", item_id)

        return updated_item

    except (ResourceNotFoundException, ValidationError):
        # Known exceptions - let handler deal with them
        raise
    except Exception as e:
        # Unexpected error
        logger.error(f"Failed to update item: {str(e)}", exc_info=e, item_id=item_id)
        raise DatabaseException(
            message="Failed to update item",
            operation="update_item",
            details={"item_id": item_id, "error": str(e)}
        )
```

### 2. Service with Custom Exceptions

```python
class ItemService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger(__name__)

    async def create_item(self, data: ItemCreate) -> Item:
        try:
            self.logger.info("Creating item", name=data.name)

            # Validate
            if not self._validate_data(data):
                raise ValidationException(
                    "Invalid item data",
                    validation_errors={"name": "Name already exists"}
                )

            # Create
            item = Item(**data.dict())
            self.db.add(item)
            await self.db.commit()

            self.logger.audit("item_created", "item", item.id, name=item.name)
            return item

        except ValidationException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error("Failed to create item", exc_info=e)
            raise DatabaseException(
                message="Failed to create item",
                operation="create_item"
            )
```

## Exception Reference

### Quick Exception Table

| Exception | Status Code | When to Use |
|-----------|-------------|-------------|
| `ApprovalNotFoundException` | 404 | Approval not found |
| `ApprovalAlreadyProcessedException` | 409 | Approval already processed |
| `ApprovalTimeoutException` | 410 | Approval timed out |
| `ApprovalValidationException` | 422 | Approval data invalid |
| `TemplateNotFoundException` | 404 | Template not found |
| `TemplateValidationException` | 400 | Template content invalid |
| `TemplateSecurityException` | 400 | Template security violation |
| `TemplateInUseException` | 409 | Template in use (can't delete) |
| `WorkflowExecutionException` | 500 | Workflow execution failed |
| `WorkflowWebhookException` | 502 | Webhook communication failed |
| `RateLimitExceededException` | 429 | Rate limit exceeded |
| `DatabaseException` | 500 | Database operation failed |
| `ResourceNotFoundException` | 404 | Generic resource not found |
| `ExternalServiceException` | 503 | External service failed |
| `AuthenticationException` | 401 | Authentication failed |
| `AuthorizationException` | 403 | Access denied |

### Exception Usage Examples

```python
# Not found
if not approval:
    raise ApprovalNotFoundException(approval_id)

# Already processed
if approval.status != "pending":
    raise ApprovalAlreadyProcessedException(
        approval_id,
        approval.status,
        details={"decided_at": approval.decided_at}
    )

# Timeout
if datetime.utcnow() > approval.timeout_at:
    raise ApprovalTimeoutException(
        approval_id,
        timeout_at=approval.timeout_at.isoformat()
    )

# Validation error
if not is_valid:
    raise TemplateValidationException(
        "Template body is invalid",
        template_id=template_id,
        field="body_template",
        validation_errors={"body": "Contains forbidden tags"}
    )

# Database error
try:
    await db.commit()
except SQLAlchemyError as e:
    raise DatabaseException(
        "Failed to commit transaction",
        operation="commit",
        details={"error": str(e)}
    )

# Rate limit
if rate_exceeded:
    raise RateLimitExceededException(
        limit=100,
        window="1 hour",
        retry_after=3600
    )
```

## Logging Reference

### Log Levels

```python
logger.debug("Detailed debug info", var1="value")     # Development only
logger.info("Normal operation", operation="start")     # Informational
logger.warning("Something unexpected", issue="minor")  # Warning
logger.error("Error occurred", exc_info=e)            # Error with exception
logger.critical("System failure", system="database")  # Critical failure
```

### Special Log Types

```python
# Audit log (tracks user actions)
logger.audit(
    action="approval_created",
    resource_type="approval_request",
    resource_id=approval_id,
    extra_key="extra_value"
)

# Performance log (tracks timing)
start = datetime.utcnow()
result = await operation()
duration = (datetime.utcnow() - start).total_seconds()

logger.performance(
    operation="operation_name",
    duration_seconds=duration,
    success=True,
    extra_metric=123
)
```

### Logging Best Practices

```python
# ✅ Good: Structured data
logger.info("User logged in", user_id=user.id, username=user.name)

# ❌ Bad: String interpolation
logger.info(f"User {user.name} with ID {user.id} logged in")

# ✅ Good: Log exception
try:
    result = await operation()
except Exception as e:
    logger.error("Operation failed", exc_info=e, context="value")
    raise

# ❌ Bad: String exception
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    raise

# ✅ Good: Context data
logger.info("Processing", item_id=item_id, status="pending", count=len(items))

# ❌ Bad: No context
logger.info("Processing items")
```

## Response Format

### Success Response

```json
{
  "id": 123,
  "status": "approved",
  "data": { ... }
}
```

### Error Response

```json
{
  "error": {
    "code": "APPROVAL_NOT_FOUND",
    "message": "Approval with ID 123 not found",
    "details": {
      "approval_id": 123
    }
  },
  "request_id": "abc123def456",
  "timestamp": "2025-11-05T21:30:45.123456Z",
  "path": "/api/v1/workflows/approvals/123"
}
```

## Request Headers

```
X-Request-ID: abc123def456    # Added by middleware
X-User-Email: user@example.com  # Optional: for user tracking
X-User-ID: 12345                # Optional: for user tracking
```

## Testing

### Test Exception

```python
def test_custom_exception():
    with pytest.raises(ApprovalNotFoundException) as exc_info:
        raise ApprovalNotFoundException(123)

    assert exc_info.value.status_code == 404
    assert exc_info.value.approval_id == 123
```

### Test Endpoint Error Response

```python
def test_not_found_response(client):
    response = client.get("/api/v1/items/999999")

    assert response.status_code == 404
    data = response.json()

    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "request_id" in data
    assert "timestamp" in data
```

### Test Logging

```python
def test_logging(caplog):
    logger = get_logger("test")
    logger.info("Test", param="value")

    record = caplog.records[0]
    assert "Test" in record.message
    assert record.extra_data["param"] == "value"
```

## Environment Setup

### Development

```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

### Production

```bash
export LOG_LEVEL=INFO
export ENVIRONMENT=production
export LOG_FORMAT=json
```

## Monitoring

### Log Files

- `logs/app.log` - All logs (INFO+)
- `logs/error.log` - Errors only (ERROR+)
- `logs/audit.log` - Audit trail
- Rotation: 10MB max, 5-10 backups

### Metrics to Monitor

1. **Error Rate**: Count of 5xx responses
2. **Response Time**: P50, P95, P99 latency
3. **Authentication Failures**: Count of 401s
4. **Rate Limit Hits**: Count of 429s
5. **Slow Requests**: Requests >1s

## Common Pitfalls

### ❌ Don't

```python
# Don't use print
print(f"Processing item {item_id}")

# Don't expose internal errors
raise HTTPException(500, detail=str(internal_error))

# Don't log sensitive data
logger.info(f"User password: {password}")

# Don't catch and ignore
try:
    await operation()
except Exception:
    pass
```

### ✅ Do

```python
# Use structured logging
logger.info("Processing item", item_id=item_id)

# Use custom exceptions
raise DatabaseException("Operation failed", operation="update")

# Redact sensitive data
logger.info("User authenticated", user_id=user.id)

# Log and re-raise
try:
    await operation()
except Exception as e:
    logger.error("Operation failed", exc_info=e)
    raise
```

## Key Files

- **Exceptions**: `/app/exceptions/__init__.py`
- **Logging**: `/app/core/logging_config.py`
- **Handlers**: `/app/middleware/exception_handlers.py`
- **Middleware**: `/app/middleware/logging_middleware.py`
- **Main**: `/app/main.py`

## Need Help?

See full documentation: `EXCEPTION_HANDLING_IMPLEMENTATION.md`
