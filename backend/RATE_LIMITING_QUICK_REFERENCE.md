# Rate Limiting Quick Reference

## Rate Limit Categories

| Category | Limit | Endpoints | Use Case |
|----------|-------|-----------|----------|
| **Read Operations** | 100/min | GET endpoints | List, view, analytics |
| **Write Operations** | 20-30/min | POST, PUT, DELETE | Create, update, delete |
| **Public Tracking** | 1000-2000/min | Public endpoints | Email tracking, analytics |
| **Resource-Intensive** | 10/hour | AI, deployment | Generation, deployment |
| **Bulk Operations** | 10/min | Bulk endpoints | Batch processing |

## Endpoint Limits by Feature

### Templates API (`/api/v1/templates/*`)
```
GET  /                           → 100/min (templates_read_limiter)
GET  /{id}                       → 100/min (templates_read_limiter)
POST /                           → 20/min  (templates_write_limiter)
PUT  /{id}                       → 20/min  (templates_write_limiter)
DELETE /{id}                     → 20/min  (templates_write_limiter)
POST /test/preview-template      → 30/min  (templates_preview_limiter)
GET  /analytics/*                → 100/min (templates_read_limiter)
```

### Email Tracking API (`/api/v1/tracking/*`)
```
GET /open/{token}                → 1000/min (tracking_public_limiter)
GET /click/{token}               → 1000/min (tracking_public_limiter)
GET /unsubscribe/{token}         → 50/hour  (tracking_unsubscribe_limiter)
GET /unsubscribe-confirm         → 50/hour  (tracking_unsubscribe_limiter)
```

### Demo Sites API (`/api/v1/demo-sites/*`)
```
POST /generate                   → 10/hour  (demo_sites_generate_limiter)
POST /{id}/deploy                → 10/hour  (demo_sites_deploy_limiter)
GET  /                           → 100/min  (demo_sites_read_limiter)
GET  /{id}                       → 100/min  (demo_sites_read_limiter)
POST /                           → 20/min   (demo_sites_write_limiter)
PUT  /{id}                       → 20/min   (demo_sites_write_limiter)
DELETE /{id}                     → 20/min   (demo_sites_write_limiter)
POST /{id}/analytics/track       → 2000/min (demo_sites_track_limiter)
```

### Workflow Approvals API (`/api/v1/workflows/approvals/*`)
```
GET  /pending                    → 100/min (approvals_read_limiter)
GET  /{id}                       → 100/min (approvals_read_limiter)
POST /create                     → 30/min  (approvals_write_limiter)
POST /{id}/decide                → 30/min  (approvals_write_limiter)
POST /bulk-approve               → 10/min  (approvals_bulk_limiter)
POST /auto-approval/rules        → 10/min  (approvals_rules_write_limiter)
```

## Response Headers

Every rate-limited response includes:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1699200000
```

## 429 Response Format

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please slow down and try again later.",
  "timestamp": "2025-11-05T12:00:00.000Z"
}
```

Additional headers:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699200060
```

## Quick Test Commands

### Test Read Endpoint (100/min)
```bash
# Should succeed 100 times, fail on 101st
for i in {1..101}; do
  curl -w "%{http_code}\n" http://localhost:8000/api/v1/templates/
done
```

### Test Write Endpoint (20/min)
```bash
# Should succeed 20 times, fail on 21st
for i in {1..21}; do
  curl -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/templates/ \
    -H "Content-Type: application/json" \
    -d '{"name":"Test","subject_template":"Test","body_template":"Test"}'
done
```

### Check Headers
```bash
curl -i http://localhost:8000/api/v1/templates/ | grep X-RateLimit
```

## Adding Rate Limiting to New Endpoints

### Step 1: Import rate limiters
```python
from app.core.rate_limiter import (
    templates_read_limiter,    # For read operations
    templates_write_limiter,   # For write operations
    # ... or create custom
)
```

### Step 2: Add Request parameter
```python
@router.get("/endpoint")
async def my_endpoint(request: Request):  # Add Request parameter
    pass
```

### Step 3: Apply decorator
```python
@router.get("/endpoint")
@templates_read_limiter  # Add decorator
async def my_endpoint(request: Request):
    pass
```

### Custom Rate Limiter
```python
from app.core.rate_limiter import rate_limit_middleware

custom_limiter = rate_limit_middleware("50 per minute")

@router.get("/endpoint")
@custom_limiter
async def my_endpoint(request: Request):
    pass
```

## Configuration

### Environment Variables
```bash
# .env file
REDIS_URL=redis://localhost:6379/0  # Required for rate limiting
```

### Adjust Limits
Edit `/Users/greenmachine2.0/Craigslist/backend/app/core/rate_limiter.py`:
```python
RATE_LIMITS = {
    "templates_list": "100 per minute",  # Change here
    # ...
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Rate limits not working | Check Redis connection, ensure REDIS_URL is set |
| Rate limits too strict | Increase limits in `RATE_LIMITS` dict |
| Rate limits not resetting | Check Redis key expiration (automatic) |
| Different instances not syncing | Ensure all instances use same Redis URL |

## Monitoring

### Redis Commands
```bash
# Connect to Redis
redis-cli

# View all rate limit keys
KEYS rate_limit:*

# View specific endpoint
ZRANGE rate_limit:/api/v1/templates/:hash123 0 -1 WITHSCORES

# Monitor live activity
MONITOR
```

### Python Code
```python
from app.core.rate_limiter import rate_limiter

# Check rate limit status
is_allowed, metadata = rate_limiter.check_rate_limit(
    identifier="user-hash",
    endpoint="/api/v1/templates/",
    limit=100,
    window=60
)

print(f"Allowed: {is_allowed}")
print(f"Remaining: {metadata['remaining']}")
print(f"Reset: {metadata['reset']}")
```

## Best Practices

1. **Choose Appropriate Limits**
   - Read: 100-300/min
   - Write: 20-30/min
   - Public: 1000-2000/min
   - Resource-intensive: 5-10/hour

2. **Always Add Request Parameter**
   ```python
   async def endpoint(request: Request):  # Required!
   ```

3. **Apply Decorator After @router**
   ```python
   @router.get("/endpoint")    # First
   @read_limiter               # Second
   async def endpoint(...):    # Third
   ```

4. **Test Rate Limits**
   - Test at 100% limit
   - Test at 101% limit (should fail)
   - Check headers
   - Verify 429 format

5. **Monitor in Production**
   - Track rate limit violations
   - Adjust based on usage patterns
   - Alert on excessive 429s

## Common Patterns

### CRUD Endpoints
```python
@router.get("/resources")
@read_limiter  # 100/min
async def list_resources(request: Request): pass

@router.get("/resources/{id}")
@read_limiter  # 100/min
async def get_resource(request: Request, id: int): pass

@router.post("/resources")
@write_limiter  # 20/min
async def create_resource(request: Request): pass

@router.put("/resources/{id}")
@write_limiter  # 20/min
async def update_resource(request: Request, id: int): pass

@router.delete("/resources/{id}")
@write_limiter  # 20/min
async def delete_resource(request: Request, id: int): pass
```

### Public Tracking Endpoint
```python
@router.get("/track/{token}")
@tracking_public_limiter  # 1000/min
async def track_event(request: Request, token: str): pass
```

### Resource-Intensive Operation
```python
@router.post("/generate")
@resource_intensive_limiter  # 10/hour
async def generate_content(request: Request): pass
```

## Files Modified

- `/Users/greenmachine2.0/Craigslist/backend/app/core/rate_limiter.py`
- `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/templates.py`
- `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/email_tracking.py`
- `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/demo_sites.py`
- `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/workflow_approvals.py`

## Total Coverage

- **55 endpoints** protected across 4 feature areas
- **11 rate limiter types** configured
- **44 rate limit configurations** added

## See Also

- Full documentation: `RATE_LIMITING_IMPLEMENTATION.md`
- Rate limiter code: `app/core/rate_limiter.py`
- Test suite: `tests/test_rate_limiting.py`
