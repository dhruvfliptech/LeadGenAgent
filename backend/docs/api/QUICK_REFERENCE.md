# API Quick Reference Guide

Quick lookup for the 4 new APIs with essential information.

---

## Auto-Response Templates API

**Base URL:** `/api/v1/templates`

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/` | List templates | Required |
| GET | `/{id}` | Get template details | Required |
| POST | `/` | Create template | Required |
| PUT | `/{id}` | Update template | Required |
| DELETE | `/{id}` | Delete template | Required |
| POST | `/responses/` | Send auto-response | Required |
| GET | `/responses/` | List responses | Required |
| POST | `/responses/{id}/track/{event}` | Track engagement | Required |
| GET | `/analytics/templates` | Get analytics | Required |
| GET | `/analytics/ab-testing` | Get A/B results | Required |
| POST | `/test/preview-template` | Preview rendering | Required |

### Key Parameters

**Create Template:**
```json
{
  "name": "string (required)",
  "subject_template": "string (required)",
  "body_template": "string (required)",
  "use_ai_enhancement": boolean,
  "ai_tone": "professional|casual|formal|persuasive",
  "ai_length": "short|medium|long"
}
```

**Send Response:**
```json
{
  "lead_id": integer (required),
  "template_id": integer (required),
  "delay_minutes": integer,
  "personalization_config": object
}
```

### Rate Limits
- 1000 requests/minute
- Burst: 100 requests/second

### Response Codes
- 200: OK
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Server Error

---

## Email Tracking API

**Base URL:** `/api/v1/tracking`

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| GET | `/open/{token}` | Track email open | None |
| GET | `/click/{token}?url=...` | Track click & redirect | None |
| GET | `/unsubscribe/{token}` | Process unsubscribe | None |
| GET | `/unsubscribe-confirm` | Show unsubscribe form | None |

### Token Generation

```python
import hmac, hashlib, base64

def generate_token(campaign_id: int, lead_id: int, secret: str) -> str:
    timestamp = int(datetime.utcnow().timestamp())
    data = f"{campaign_id}:{lead_id}:{timestamp}"
    signature = hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(data.encode() + signature).decode().rstrip('=')
```

### Email Integration

```html
<!-- Open tracking -->
<img src="https://api.example.com/api/v1/tracking/open/TOKEN"
     width="1" height="1" alt="" style="display:none;" />

<!-- Click tracking -->
<a href="https://api.example.com/api/v1/tracking/click/TOKEN?url=https%3A%2F%2Fexample.com">
  Click Here
</a>

<!-- Unsubscribe (required by law) -->
<a href="https://api.example.com/api/v1/tracking/unsubscribe/TOKEN">
  Unsubscribe
</a>
```

### Rate Limits
- 10,000 opens/minute
- 5,000 clicks/minute
- No authentication required

### Response Codes
- 200: OK (pixel or HTML)
- 302: Redirect to URL
- 400: Invalid token/URL
- 404: Token not found

---

## Demo Sites API

**Base URL:** `/api/v1/demo-sites`

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/generate` | Generate demo site | Required |
| GET | `/` | List demo sites | Required |
| GET | `/{id}` | Get site details | Required |
| PUT | `/{id}` | Update site | Required |
| DELETE | `/{id}` | Delete site | Required |
| POST | `/{id}/deploy` | Deploy to Vercel | Required |
| GET | `/{id}/preview` | Get HTML/CSS/JS | Required |
| POST | `/{id}/duplicate` | Clone site | Required |
| GET | `/{id}/export` | Export files | Required |
| GET | `/templates` | List templates | Required |
| POST | `/templates` | Create template | Required |
| GET | `/{id}/analytics/summary` | Get analytics | Required |
| GET | `/{id}/analytics/timeline` | Time-series data | Required |
| POST | `/{id}/analytics/track` | Track event | Required |
| GET | `/components` | List components | Required |

### Key Parameters

**Generate Site:**
```json
{
  "site_name": "string (required)",
  "template_type": "landing|product|case_study|custom",
  "content_data": object (required),
  "style_settings": object,
  "use_ai_generation": boolean,
  "ai_model": "gpt-4|claude-3|gpt-3.5",
  "auto_deploy": boolean,
  "custom_subdomain": "string"
}
```

### Site Status Values
- `draft` - Created, not deployed
- `building` - Currently deploying
- `live` - Deployed and accessible
- `failed` - Deployment failed
- `updating` - Being modified
- `deleted` - Soft deleted

### Rate Limits
- 500 requests/minute
- Max 20 concurrent deployments

### Response Codes
- 200: OK
- 201: Created
- 400: Bad Request
- 404: Not Found
- 502: Vercel unavailable

---

## Workflow Approvals API

**Base URL:** `/api/v1/approvals`

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/create` | Create approval | Required |
| GET | `/pending` | Get pending | Required |
| GET | `/{id}` | Get details | Required |
| POST | `/{id}/decide` | Submit decision | Required |
| POST | `/{id}/escalate` | Escalate approval | Required |
| POST | `/bulk-approve` | Approve multiple | Required |
| GET | `/stats` | Get statistics | Required |
| POST | `/check-timeouts` | Check timeouts | Required |
| GET | `/auto-approval/rules` | List rules | Required |
| POST | `/auto-approval/rules` | Create rule | Required |
| GET | `/auto-approval/rules/{id}/performance` | Rule metrics | Required |
| POST | `/auto-approval/rules/{id}/optimize` | Optimize threshold | Required |
| GET | `/auto-approval/templates` | Get templates | Required |
| POST | `/auto-approval/templates/{idx}/apply` | Apply template | Required |

### Key Parameters

**Create Approval:**
```json
{
  "approval_type": "string (required)",
  "resource_id": integer (required),
  "resource_data": object (required),
  "workflow_execution_id": "string (required)",
  "timeout_minutes": integer (5-1440, default: 60),
  "approvers": ["email@example.com"],
  "resume_webhook_url": "https://..."
}
```

**Submit Decision:**
```json
{
  "approved": boolean (required),
  "reviewer_email": "string (required)",
  "comments": "string",
  "modified_data": object
}
```

**Create Rule:**
```json
{
  "name": "string (required)",
  "description": "string (required)",
  "approval_types": ["string"],
  "auto_approve_threshold": 0.85,
  "min_qualification_score": 0.80,
  "required_keywords": ["CEO", "CTO"],
  "excluded_keywords": ["spam"],
  "lead_categories": ["enterprise"],
  "priority": 100
}
```

### Approval Types
- `lead_qualification` - Lead review
- `response_review` - Content review
- `export_approval` - Data export
- `campaign_approval` - Campaign launch
- `custom` - Custom types

### Approval Status
- `pending` - Awaiting decision
- `approved` - Approved
- `rejected` - Rejected
- `escalated` - Escalated
- `timeout` - Timed out

### Rate Limits
- 1000 requests/minute
- Max 50 items per bulk operation

### Response Codes
- 200: OK
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Server Error

---

## Error Response Format

```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123xyz789"
}
```

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| INVALID_REQUEST | 400 | Invalid parameters |
| UNAUTHORIZED | 401 | Missing/invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource doesn't exist |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMITED | 429 | Too many requests |
| VALIDATION_ERROR | 422 | Invalid field values |
| SERVER_ERROR | 500 | Internal error |

---

## Authentication

All endpoints (except tracking) require:

```
Authorization: Bearer YOUR_API_TOKEN
```

**Token Format:** `sk_live_xxxxxxxxxx`

**Token Scopes:**
- `templates.read` - Read templates
- `templates.write` - Create/modify templates
- `tracking.read` - Read tracking data
- `demo-sites.read` - Read demo sites
- `demo-sites.write` - Create/modify demo sites
- `approvals.read` - Read approvals
- `approvals.write` - Create/modify approvals

---

## Common Workflows

### Send Campaign with Tracking

```bash
# 1. Create template
TEMPLATE=$(curl -X POST "https://api.example.com/api/v1/templates/" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"name": "Campaign", "subject_template": "...", "body_template": "..."}'
  | jq '.id')

# 2. Send to leads
for LEAD_ID in 1 2 3; do
  curl -X POST "https://api.example.com/api/v1/templates/responses/" \
    -H "Authorization: Bearer TOKEN" \
    -d "{\"lead_id\": $LEAD_ID, \"template_id\": $TEMPLATE}"
done

# 3. Check analytics
curl "https://api.example.com/api/v1/templates/analytics/templates" \
  -H "Authorization: Bearer TOKEN"
```

### Deploy Demo Site

```bash
# 1. Generate site
SITE=$(curl -X POST "https://api.example.com/api/v1/demo-sites/generate" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"site_name": "Demo", "template_type": "landing", "content_data": {}}'
  | jq '.id')

# 2. Wait for deployment
while sleep 5; do
  STATUS=$(curl "https://api.example.com/api/v1/demo-sites/$SITE" \
    -H "Authorization: Bearer TOKEN" | jq -r '.status')
  if [ "$STATUS" = "live" ]; then break; fi
done

# 3. Get analytics
curl "https://api.example.com/api/v1/demo-sites/$SITE/analytics/summary" \
  -H "Authorization: Bearer TOKEN"
```

### Approval Workflow

```bash
# 1. Create approval
APPROVAL=$(curl -X POST "https://api.example.com/api/v1/approvals/create" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"approval_type": "lead_qualification", "resource_id": 42, "resource_data": {}}'
  | jq '.approval_id')

# 2. Get pending
curl "https://api.example.com/api/v1/approvals/pending" \
  -H "Authorization: Bearer TOKEN"

# 3. Submit decision
curl -X POST "https://api.example.com/api/v1/approvals/$APPROVAL/decide" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"approved": true, "reviewer_email": "user@example.com"}'
```

---

## SDKs

### Python

```bash
pip install fliptechpro
```

```python
from fliptechpro import Client

client = Client(api_token="YOUR_TOKEN")

# Templates
template = client.templates.create(name="My Template", ...)
client.templates.send_auto_response(lead_id=42, template_id=1)

# Demo Sites
site = client.demo_sites.generate(site_name="Demo", ...)
analytics = client.demo_sites.get_analytics_summary(site_id=1)

# Approvals
approval = client.approvals.create(approval_type="lead_qualification", ...)
client.approvals.submit_decision(approval_id=1, approved=True, ...)
```

### JavaScript

```bash
npm install fliptechpro
```

```javascript
const { FlipTechPro } = require('fliptechpro');

const client = new FlipTechPro({ apiToken: 'YOUR_TOKEN' });

// Templates
const template = await client.templates.create({...});
await client.templates.sendAutoResponse(leadId, templateId);

// Demo Sites
const site = await client.demoSites.generate({...});
const analytics = await client.demoSites.getAnalyticsSummary(siteId);

// Approvals
const approval = await client.approvals.create({...});
await client.approvals.submitDecision(approvalId, {...});
```

---

## Rate Limit Handling

Check headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705331400
Retry-After: 60
```

Retry on 429:
```python
import time

response = requests.get(url, headers=headers)
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    # Retry request
```

---

## Testing with cURL

### Template Operations

```bash
# Create template
curl -X POST "https://api.example.com/api/v1/templates/" \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Template",
    "subject_template": "Hello {{first_name}}",
    "body_template": "Welcome to our service"
  }'

# List templates
curl "https://api.example.com/api/v1/templates/" \
  -H "Authorization: Bearer sk_live_..."

# Get specific template
curl "https://api.example.com/api/v1/templates/1" \
  -H "Authorization: Bearer sk_live_..."

# Update template
curl -X PUT "https://api.example.com/api/v1/templates/1" \
  -H "Authorization: Bearer sk_live_..." \
  -d '{"name": "Updated Name"}'

# Delete template
curl -X DELETE "https://api.example.com/api/v1/templates/1" \
  -H "Authorization: Bearer sk_live_..."
```

---

## OpenAPI Specification

OpenAPI 3.0.3 specification available at:
**File:** `openapi.json`

**Import into:**
- Swagger UI: http://petstore.swagger.io
- Postman: File → Import → Raw text
- Stoplight: https://stoplight.io
- ReDoc: Generate HTML documentation

---

## Documentation Files

| File | Purpose |
|------|---------|
| README.md | Main API index and overview |
| AUTO_RESPONSE_TEMPLATES_API.md | Templates API detailed docs |
| EMAIL_TRACKING_API.md | Tracking API detailed docs |
| DEMO_SITES_API.md | Demo Sites API detailed docs |
| WORKFLOW_APPROVALS_API.md | Approvals API detailed docs |
| openapi.json | OpenAPI 3.0.3 specification |
| DOCUMENTATION_SUMMARY.md | Complete documentation overview |
| QUICK_REFERENCE.md | This file |

---

## Support

- Docs: https://docs.example.com
- Status: https://status.example.com
- Email: support@example.com
- Chat: In account dashboard

---

## Version Info

- API Version: 1.2.0
- Documentation Version: 1.0.0
- Last Updated: January 15, 2024

---
