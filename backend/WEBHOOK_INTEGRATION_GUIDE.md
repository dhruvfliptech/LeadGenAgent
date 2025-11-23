# Webhook Integration Guide
## Phase 5, Task 3: Bidirectional Webhook Communication with n8n

**Version:** 1.0
**Created:** 2025-11-04
**Author:** Backend System Architect

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [Webhook Events](#webhook-events)
5. [Security](#security)
6. [API Endpoints](#api-endpoints)
7. [Queue Management](#queue-management)
8. [Testing](#testing)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)

---

## Overview

The webhook integration system provides bidirectional communication between the Craigslist Lead Generation backend and n8n workflows. This enables:

- **Automatic event triggering**: Database changes automatically trigger n8n workflows
- **Reliable delivery**: Webhook queue with retry logic ensures no events are lost
- **Security**: HMAC signature verification protects against unauthorized access
- **Auditability**: Comprehensive logging of all webhook activity
- **Real-time updates**: n8n can send status updates back to the backend

### Key Features

- ✅ Automatic webhook triggers on database events
- ✅ Persistent queue with retry logic
- ✅ HMAC-SHA256 signature verification
- ✅ Priority-based processing
- ✅ Comprehensive audit logging
- ✅ Background processing
- ✅ Error tracking and alerting

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Backend Application                      │
│                                                               │
│  ┌─────────────────┐      ┌──────────────────┐             │
│  │  Event Emitter  │─────▶│  Webhook Trigger │             │
│  │   Middleware    │      │     Service      │             │
│  └─────────────────┘      └──────────────────┘             │
│          │                         │                         │
│          │                         ▼                         │
│          │                 ┌──────────────────┐             │
│          │                 │  Webhook Queue   │             │
│          │                 │     Service      │             │
│          │                 └──────────────────┘             │
│          │                         │                         │
│          ▼                         ▼                         │
│  ┌──────────────────────────────────────────┐               │
│  │         Database Tables                   │               │
│  │  • webhook_queue                         │               │
│  │  • webhook_logs                          │               │
│  │  • webhook_retry_history                 │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS + HMAC
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      n8n Workflows                           │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Lead Processing │  │ Demo Deployment  │                │
│  │    Pipeline      │  │    Pipeline      │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Video Generation │  │ Email Outreach   │                │
│  │    Pipeline      │  │    Pipeline      │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTPS + HMAC
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend Webhook Response Handlers               │
│                                                               │
│  /api/v1/webhooks/n8n/demo-approval                         │
│  /api/v1/webhooks/n8n/video-approval                        │
│  /api/v1/webhooks/n8n/workflow-completed                    │
│  /api/v1/webhooks/n8n/workflow-status                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Backend → n8n (Outgoing)**
   - Database event occurs (lead created, demo completed, etc.)
   - Event emitter middleware detects change
   - Webhook trigger service creates webhook
   - Webhook added to queue
   - Queue processor sends webhook to n8n
   - Response logged for auditing

2. **n8n → Backend (Incoming)**
   - n8n workflow requires input (approval, status update, etc.)
   - n8n sends POST request to backend endpoint
   - Backend verifies HMAC signature
   - Request processed and database updated
   - Response logged for auditing

---

## Setup Instructions

### 1. Environment Configuration

Add these variables to your `.env` file:

```bash
# n8n Connection
N8N_ENABLED=true
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_BASE_URL=http://localhost:5678  # Optional: if different from base URL
N8N_API_KEY=your_n8n_api_key_here  # Optional: for authenticated requests

# Webhook Security
WEBHOOK_SECRET=your-secure-webhook-secret-here
N8N_WEBHOOK_SECRET=your-n8n-webhook-secret-here

# Queue Configuration
WEBHOOK_QUEUE_ENABLED=true
WEBHOOK_QUEUE_BATCH_SIZE=10
WEBHOOK_QUEUE_PROCESSING_INTERVAL=5

# Retry Configuration
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_DELAYS=5,30,300  # 5s, 30s, 5m
WEBHOOK_TIMEOUT_SECONDS=30
```

### 2. Generate Webhook Secrets

```bash
# Generate secure webhook secrets
python -c "import secrets; print(secrets.token_hex(32))"
```

Use the output for `WEBHOOK_SECRET` and `N8N_WEBHOOK_SECRET`.

### 3. Run Database Migration

```bash
# Apply webhook tables migration
psql -U postgres -d craigslist_leads -f migrations/005_webhook_tables.sql

# Verify tables were created
psql -U postgres -d craigslist_leads -c "\dt webhook*"
```

### 4. Initialize Event Listeners

The event listeners are automatically set up during application startup. No manual initialization required.

### 5. Configure n8n Webhooks

In your n8n workflows, configure webhook nodes to use the backend URLs:

**Outgoing webhooks from backend:**
- `http://your-n8n-instance:5678/webhook/lead-scraped`
- `http://your-n8n-instance:5678/webhook/demo-completed`
- `http://your-n8n-instance:5678/webhook/video-completed`
- etc.

**Incoming webhooks to backend:**
- `http://your-backend:8000/api/v1/webhooks/n8n/demo-approval`
- `http://your-backend:8000/api/v1/webhooks/n8n/video-approval`
- `http://your-backend:8000/api/v1/webhooks/n8n/workflow-completed`
- etc.

---

## Webhook Events

### Outgoing Events (Backend → n8n)

| Event Type | Trigger | Payload Example |
|-----------|---------|-----------------|
| `lead_scraped` | New lead created | `{"lead_id": 123, "business_name": "Acme Inc", ...}` |
| `lead_qualified` | Lead passes qualification | `{"lead_id": 123, "score": 0.85, ...}` |
| `demo_completed` | Demo deployment succeeds | `{"demo_site_id": 456, "url": "...", ...}` |
| `demo_failed` | Demo deployment fails | `{"demo_site_id": 456, "error": "...", ...}` |
| `video_completed` | Video generation succeeds | `{"video_id": 789, "url": "...", ...}` |
| `video_failed` | Video generation fails | `{"video_id": 789, "error": "...", ...}` |
| `email_sent` | Email sent to lead | `{"lead_id": 123, "subject": "...", ...}` |
| `email_failed` | Email sending fails | `{"lead_id": 123, "error": "...", ...}` |
| `lead_responded` | Lead responds to outreach | `{"lead_id": 123, "message": "...", ...}` |
| `approval_requested` | Approval required | `{"approval_type": "demo", "entity_id": 456, ...}` |
| `workflow_error` | Workflow encounters error | `{"workflow_name": "...", "error": "...", ...}` |

### Incoming Events (n8n → Backend)

| Endpoint | Purpose | Expected Payload |
|----------|---------|------------------|
| `/api/v1/webhooks/n8n/demo-approval` | Demo approval decision | `{"demo_id": 456, "approved": true, ...}` |
| `/api/v1/webhooks/n8n/video-approval` | Video approval decision | `{"video_id": 789, "approved": true, ...}` |
| `/api/v1/webhooks/n8n/workflow-completed` | Workflow completion | `{"workflow_id": "...", "status": "success", ...}` |
| `/api/v1/webhooks/n8n/workflow-status` | Workflow status update | `{"workflow_id": "...", "current_step": "...", ...}` |
| `/api/v1/webhooks/n8n/error-notification` | Error notification | `{"workflow_id": "...", "error": "...", ...}` |

---

## Security

### HMAC Signature Verification

All webhooks use HMAC-SHA256 signatures for authentication.

#### Generating Signatures (Outgoing)

```python
from app.utils.webhook_security import WebhookSecurity

payload = {"event": "lead_scraped", "lead_id": 123}
secret = "your-webhook-secret"

# Create signed payload
signed = WebhookSecurity.create_signed_payload(payload, secret)

# Headers will include:
# X-Webhook-Signature-256: <signature>
# X-Webhook-Timestamp: <timestamp>
```

#### Verifying Signatures (Incoming)

```python
from fastapi import Request, Depends
from app.utils.webhook_security import WebhookSecurity

async def verify_webhook(request: Request):
    secret = "your-webhook-secret"
    await WebhookSecurity.verify_n8n_webhook(request, secret)
    return True

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    _verified: bool = Depends(verify_webhook)
):
    # Process webhook
    pass
```

### Signature Header Format

```
X-Webhook-Signature-256: <hex-encoded-hmac-sha256-signature>
X-Webhook-Timestamp: <unix-timestamp>
```

### Replay Attack Prevention

Webhooks include timestamps and have a maximum age (default: 5 minutes). Webhooks older than the maximum age are rejected.

---

## API Endpoints

### Webhook Response Handlers

#### POST `/api/v1/webhooks/n8n/demo-approval`

Handle demo approval decision from n8n.

**Request:**
```json
{
  "demo_id": 456,
  "approved": true,
  "reviewer": "admin@example.com",
  "notes": "Looks great, proceed with video"
}
```

**Response:**
```json
{
  "status": "approved",
  "demo_id": 456,
  "lead_id": 123,
  "action": "continue",
  "next_step": "video_generation",
  "message": "Demo approved, triggering video generation"
}
```

#### POST `/api/v1/webhooks/n8n/video-approval`

Handle video approval decision from n8n.

**Request:**
```json
{
  "video_id": 789,
  "approved": true,
  "reviewer": "admin@example.com",
  "notes": "Perfect, send the email"
}
```

**Response:**
```json
{
  "status": "approved",
  "video_id": 789,
  "lead_id": 123,
  "action": "continue",
  "next_step": "email_outreach",
  "message": "Video approved, triggering email outreach"
}
```

#### POST `/api/v1/webhooks/n8n/workflow-completed`

Receive workflow completion notification.

**Request:**
```json
{
  "workflow_id": "lead-processing-pipeline",
  "execution_id": "exec_123",
  "lead_id": 123,
  "status": "success",
  "duration_ms": 45000
}
```

**Response:**
```json
{
  "status": "received",
  "workflow_id": "lead-processing-pipeline",
  "execution_id": "exec_123",
  "message": "Workflow completion logged successfully"
}
```

#### GET `/api/v1/webhooks/n8n/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "webhook-responses",
  "timestamp": "2025-11-04T12:00:00Z",
  "webhook_config": {
    "enabled": true,
    "base_url": "http://localhost:5678",
    "security_enabled": true
  }
}
```

---

## Queue Management

### Webhook Queue Service

The webhook queue ensures reliable delivery with automatic retries.

```python
from app.services.webhook_queue import WebhookQueue
from app.db.session import get_db

# Create queue instance
db = next(get_db())
queue = WebhookQueue(db)

# Enqueue webhook
webhook_id = await queue.enqueue(
    webhook_url="http://n8n.example.com/webhook/lead-scraped",
    payload={"lead_id": 123, "name": "Acme Inc"},
    event_type="lead_scraped",
    entity_type="lead",
    entity_id=123,
    priority=0  # 0=normal, higher=more important
)

# Get queue statistics
stats = await queue.get_queue_stats()
print(stats)
# {
#   "pending": 5,
#   "sending": 2,
#   "sent": 150,
#   "failed": 3,
#   "cancelled": 0,
#   "total": 160
# }

# Retry failed webhook
await queue.retry_failed(webhook_id)

# Cancel webhook
await queue.cancel_webhook(webhook_id)

# Clean up old webhooks
await queue.cleanup_old_webhooks(days=30)
```

### Queue Processing

The queue processor runs in the background and automatically processes pending webhooks.

**Retry Strategy:**
- Retry delay: 5s → 30s → 5m (exponential backoff)
- Max retries: 3 (configurable)
- Priority-based processing

**Status Flow:**
```
pending → sending → sent
   │         │         │
   │         ▼         │
   │      failed ──────┘
   │         │
   └─────────┴──→ (retry if count < max_retries)
```

---

## Testing

### Run Test Suite

```bash
# Run all webhook tests
pytest tests/test_webhooks.py -v

# Run specific test class
pytest tests/test_webhooks.py::TestWebhookSecurity -v

# Run with coverage
pytest tests/test_webhooks.py --cov=app.services --cov=app.utils

# Skip slow tests
pytest tests/test_webhooks.py -m "not slow"

# Skip integration tests
pytest tests/test_webhooks.py -m "not integration"
```

### Manual Testing

#### Test Outgoing Webhook

```bash
# Start n8n webhook receiver (or use RequestBin)
# Then trigger webhook from backend:

curl -X POST http://localhost:8000/api/v1/test/trigger-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "lead_scraped",
    "lead_id": 123,
    "data": {"name": "Test Lead"}
  }'
```

#### Test Incoming Webhook

```bash
# Generate signature
python -c "
import hmac, hashlib, json
payload = json.dumps({'demo_id': 456, 'approved': True})
secret = 'your-webhook-secret'
sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
print(f'Signature: {sig}')
"

# Send request with signature
curl -X POST http://localhost:8000/api/v1/webhooks/n8n/demo-approval \
  -H "Content-Type: application/json" \
  -H "X-N8N-Signature: <signature-from-above>" \
  -d '{"demo_id": 456, "approved": true}'
```

---

## Monitoring

### Database Queries

#### Check Webhook Queue Status

```sql
SELECT
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries,
    MAX(retry_count) as max_retries
FROM webhook_queue
GROUP BY status;
```

#### Recent Webhook Activity

```sql
SELECT
    direction,
    event_type,
    response_status,
    COUNT(*) as count,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms
FROM webhook_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY direction, event_type, response_status
ORDER BY count DESC;
```

#### Failed Webhooks

```sql
SELECT
    wq.*,
    COUNT(wrh.id) as retry_attempts
FROM webhook_queue wq
LEFT JOIN webhook_retry_history wrh ON wq.id = wrh.webhook_queue_id
WHERE wq.status = 'failed'
GROUP BY wq.id
ORDER BY wq.created_at DESC
LIMIT 20;
```

### Application Logs

```bash
# Watch webhook logs
tail -f logs/app.log | grep -i webhook

# Check for errors
grep -i "webhook.*error" logs/app.log | tail -20

# Monitor queue processing
grep -i "webhook queue" logs/app.log | tail -20
```

---

## Troubleshooting

### Common Issues

#### 1. Webhooks Not Being Sent

**Symptoms:** No webhooks in queue, events not triggering n8n

**Solution:**
1. Check if n8n integration is enabled: `N8N_ENABLED=true`
2. Verify event listeners are set up (check logs on startup)
3. Check database triggers are working
4. Verify webhook URLs are configured correctly

```bash
# Check webhook configuration
python -c "
from app.core.webhook_config import webhook_config
print(f'Enabled: {webhook_config.n8n.enabled}')
print(f'Base URL: {webhook_config.n8n.base_url}')
"
```

#### 2. Signature Verification Failing

**Symptoms:** 401 Unauthorized errors on incoming webhooks

**Solution:**
1. Verify webhook secret matches between backend and n8n
2. Check payload is not being modified in transit
3. Ensure timestamp is within valid range (5 minutes)
4. Verify signature header is present

```bash
# Test signature generation
python -c "
from app.utils.webhook_security import WebhookSecurity
payload = b'{\"test\": \"data\"}'
secret = 'your-secret'
sig = WebhookSecurity.generate_signature(payload, secret)
print(f'Signature: {sig}')
"
```

#### 3. Webhooks Getting Stuck in Queue

**Symptoms:** Webhooks remain in "pending" or "sending" status

**Solution:**
1. Check queue processor is running
2. Verify n8n is accessible from backend
3. Check for network issues
4. Review error messages in webhook_queue table

```sql
-- Check stuck webhooks
SELECT * FROM webhook_queue
WHERE status = 'sending'
  AND updated_at < NOW() - INTERVAL '5 minutes';
```

#### 4. High Retry Rates

**Symptoms:** Many webhooks reaching max retries

**Solution:**
1. Check n8n availability and performance
2. Review n8n logs for errors
3. Verify webhook URLs are correct
4. Check network connectivity
5. Consider increasing retry delays

```sql
-- Identify problematic webhooks
SELECT
    event_type,
    webhook_url,
    COUNT(*) as failure_count,
    MAX(last_error) as common_error
FROM webhook_queue
WHERE status = 'failed'
  AND retry_count >= max_retries
GROUP BY event_type, webhook_url
ORDER BY failure_count DESC;
```

### Debug Mode

Enable debug logging for webhooks:

```python
import logging

# Set webhook logger to DEBUG
logging.getLogger('app.services.n8n_webhook_trigger').setLevel(logging.DEBUG)
logging.getLogger('app.services.webhook_queue').setLevel(logging.DEBUG)
logging.getLogger('app.middleware.event_emitter').setLevel(logging.DEBUG)
```

---

## Examples

### Example 1: Trigger Webhook Manually

```python
from app.services.n8n_webhook_trigger import get_webhook_trigger

# Get trigger instance
trigger = get_webhook_trigger()

# Trigger lead scraped webhook
await trigger.trigger_lead_scraped(
    lead_id=123,
    lead_data={
        "business_name": "Acme Inc",
        "category": "web design",
        "location": "San Francisco",
        "score": 0.85
    }
)

# Trigger demo completed webhook
await trigger.trigger_demo_completed(
    demo_site_id=456,
    demo_data={
        "url": "https://demo.example.com",
        "lead_id": 123,
        "framework": "nextjs",
        "deployed_at": "2025-11-04T12:00:00Z"
    }
)
```

### Example 2: Process Webhook Queue Manually

```python
from app.services.webhook_queue import WebhookQueue
from app.db.session import get_db

db = next(get_db())
queue = WebhookQueue(db)

# Process pending webhooks once
pending_webhooks = queue._get_pending_webhooks()
await queue._process_webhooks(pending_webhooks)

# Or start background processing
queue.start_processing()

# Stop when done
await queue.stop_processing()
```

### Example 3: Create Custom Webhook Handler

```python
from fastapi import APIRouter, Request, Depends
from app.utils.webhook_security import WebhookSecurity
from app.core.webhook_config import webhook_config

router = APIRouter()

async def verify_webhook(request: Request):
    """Verify webhook signature."""
    secret = webhook_config.security.n8n_webhook_secret
    await WebhookSecurity.verify_n8n_webhook(request, secret)
    return True

@router.post("/my-custom-webhook")
async def custom_webhook_handler(
    request: Request,
    _verified: bool = Depends(verify_webhook)
):
    """Handle custom webhook from n8n."""
    data = await request.json()

    # Process webhook data
    # ... your logic here ...

    return {
        "status": "received",
        "message": "Custom webhook processed"
    }
```

### Example 4: Query Webhook Logs

```python
from app.models.webhook_queue import WebhookLog
from app.db.session import get_db
from datetime import datetime, timedelta

db = next(get_db())

# Get recent outgoing webhooks
recent_outgoing = db.query(WebhookLog).filter(
    WebhookLog.direction == "outgoing",
    WebhookLog.created_at > datetime.utcnow() - timedelta(hours=24)
).all()

for log in recent_outgoing:
    print(f"Event: {log.event_type}, Status: {log.response_status}, "
          f"Duration: {log.duration_ms}ms")

# Get failed webhooks
failed_webhooks = db.query(WebhookLog).filter(
    WebhookLog.response_status >= 400
).order_by(WebhookLog.created_at.desc()).limit(10).all()

for log in failed_webhooks:
    print(f"Failed: {log.event_type}, Error: {log.error_message}")
```

---

## Additional Resources

### Related Documentation
- [n8n Documentation](https://docs.n8n.io/)
- [HMAC Authentication](https://en.wikipedia.org/wiki/HMAC)
- [Webhook Best Practices](https://docs.github.com/en/webhooks/webhook-best-practices)

### API Reference
- [Webhook Response Handlers](/api/v1/webhooks/docs)
- [Webhook Security Utils](/docs/api/webhook-security)
- [Queue Service](/docs/api/webhook-queue)

### Support
- Report issues: [GitHub Issues](https://github.com/your-repo/issues)
- Slack channel: #webhook-integration
- Email: support@example.com

---

**Last Updated:** 2025-11-04
**Version:** 1.0
