# FlipTech Pro API Documentation

Welcome to the FlipTech Pro API documentation. This comprehensive guide covers all API endpoints, authentication, error handling, and integration examples.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Documentation](#api-documentation)
4. [Base URLs](#base-urls)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Webhooks](#webhooks)
8. [SDKs](#sdks)
9. [Support](#support)

---

## Getting Started

### Quick Start

1. **Get API Token**
   - Log in to your FlipTech Pro account
   - Navigate to Settings → API Tokens
   - Create a new token with required scopes

2. **Make First Request**
   ```bash
   curl -X GET "https://api.example.com/api/v1/health" \
     -H "Authorization: Bearer YOUR_API_TOKEN"
   ```

3. **Read Specific API Docs**
   - Choose your feature from [API Documentation](#api-documentation) below
   - Follow the endpoint examples
   - Check error codes and best practices

### Requirements

- API Token with appropriate scopes
- HTTPS connection (required for security)
- Content-Type: application/json for POST/PUT requests
- Valid JSON request bodies

---

## Authentication

### Token-Based Authentication

All API endpoints use Bearer token authentication:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

### Creating API Tokens

1. Go to **Settings → API Tokens**
2. Click **Create New Token**
3. Select required scopes:
   - `templates.read` - Read response templates
   - `templates.write` - Create/update templates
   - `tracking.read` - Read email tracking data
   - `demo-sites.read` - Read demo sites
   - `demo-sites.write` - Create/manage demo sites
   - `approvals.read` - Read approvals
   - `approvals.write` - Create/manage approvals
4. Set expiration date
5. Copy token (shown only once)

### Token Best Practices

- **Never share tokens** - Treat like passwords
- **Use scope limitation** - Only grant necessary scopes
- **Rotate regularly** - Regenerate tokens every 90 days
- **Use environment variables** - Store tokens in `.env`
- **Monitor usage** - Check token activity in Settings

### Environment Variable Setup

```bash
# .env file
FLIPTECHPRO_API_TOKEN=sk_live_abc123xyz789...
FLIPTECHPRO_API_BASE_URL=https://api.example.com
```

---

## API Documentation

### Core Features

#### 1. Auto-Response Templates
**Path:** `/api/v1/templates`

Manage email response templates with AI enhancement, A/B testing, and engagement tracking.

- Create and manage templates
- AI-powered content generation
- Variable substitution for personalization
- A/B testing with analytics
- Engagement tracking (opens, clicks, responses)

**📖 [Full Documentation](./AUTO_RESPONSE_TEMPLATES_API.md)**

**Quick Links:**
- Create template: `POST /`
- List templates: `GET /`
- Get template: `GET /{id}`
- Update template: `PUT /{id}`
- Delete template: `DELETE /{id}`
- Send auto-response: `POST /responses/`
- Get analytics: `GET /analytics/templates`

---

#### 2. Email Tracking
**Path:** `/api/v1/tracking`

Real-time email engagement tracking with open/click detection and unsubscribe management.

- Transparent pixel tracking
- Secure click tracking with URL validation
- Unsubscribe management
- GDPR/CAN-SPAM compliance
- Webhook integration

**📖 [Full Documentation](./EMAIL_TRACKING_API.md)**

**Quick Links:**
- Track email open: `GET /open/{token}`
- Track email click: `GET /click/{token}`
- Unsubscribe: `GET /unsubscribe/{token}`
- Confirmation page: `GET /unsubscribe-confirm`

---

#### 3. Demo Sites
**Path:** `/api/v1/demo-sites`

AI-powered generation and deployment of personalized landing pages to Vercel.

- Generate sites with AI
- Deploy to Vercel automatically
- Built-in analytics tracking
- Template management
- Component library
- Mobile-responsive design

**📖 [Full Documentation](./DEMO_SITES_API.md)**

**Quick Links:**
- Generate site: `POST /generate`
- List sites: `GET /`
- Get site: `GET /{id}`
- Update site: `PUT /{id}`
- Deploy site: `POST /{id}/deploy`
- Get analytics: `GET /{id}/analytics/summary`
- Templates: `GET /templates`
- Components: `GET /components`

---

#### 4. Workflow Approvals
**Path:** `/api/v1/approvals`

Human-in-the-loop approval system for n8n workflows with auto-approval rules and escalation.

- Create approval requests
- Manual and auto-approval workflows
- Approval queue management
- Escalation workflow
- Audit logging
- Slack/Email notifications
- n8n integration

**📖 [Full Documentation](./WORKFLOW_APPROVALS_API.md)**

**Quick Links:**
- Create approval: `POST /create`
- Get pending: `GET /pending`
- Get details: `GET /{id}`
- Submit decision: `POST /{id}/decide`
- Escalate: `POST /{id}/escalate`
- Bulk approve: `POST /bulk-approve`
- Auto-approval rules: `GET /auto-approval/rules`
- Statistics: `GET /stats`

---

## Base URLs

### Production
```
https://api.example.com
```

### Staging
```
https://staging-api.example.com
```

### API Version
Current version: `v1`

All endpoints are prefixed with `/api/v1/`

---

## Error Handling

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content returned |
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions for resource |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Invalid field values |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 502 | Bad Gateway | Service temporarily unavailable |
| 503 | Service Unavailable | Service maintenance |

### Error Response Schema

```json
{
  "detail": "Resource not found",
  "error_code": "RESOURCE_NOT_FOUND",
  "status_code": 404,
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123xyz789"
}
```

### Error Handling Examples

#### Python

```python
import requests
from requests.exceptions import RequestException

def call_api(endpoint, method="GET", data=None):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    try:
        if method == "GET":
            response = requests.get(endpoint, headers=headers)
        elif method == "POST":
            response = requests.post(endpoint, json=data, headers=headers)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        print(f"Error: {error_data['detail']}")
        print(f"Error Code: {error_data['error_code']}")

    except RequestException as e:
        print(f"Request failed: {e}")
```

#### JavaScript

```javascript
async function callAPI(endpoint, options = {}) {
  const headers = {
    "Authorization": `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json"
  };

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`${error.error_code}: ${error.detail}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API Error:", error.message);
    throw error;
  }
}
```

---

## Rate Limiting

### Limits by Endpoint Category

| Category | Requests/Minute | Requests/Hour |
|----------|-----------------|---------------|
| Templates | 1000 | 50,000 |
| Tracking | 10,000 | 100,000 |
| Demo Sites | 500 | 10,000 |
| Approvals | 1000 | 50,000 |

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705331400
Retry-After: 60
```

### Handling Rate Limits

```python
import time
from requests import Response

def handle_rate_limit(response: Response):
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        print(f"Rate limited. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        # Retry request
```

---

## Webhooks

### Webhook Events

The API can send webhooks for various events. Configure webhooks in **Settings → Webhooks**.

#### Templates Events
- `template.created` - New template created
- `template.updated` - Template updated
- `template.deleted` - Template deleted
- `response.sent` - Auto-response sent
- `response.opened` - Email opened
- `response.clicked` - Link clicked

#### Demo Sites Events
- `demo_site.created` - Demo site created
- `demo_site.deployed` - Demo site deployed
- `demo_site.deleted` - Demo site deleted
- `analytics.event` - Analytics event tracked

#### Approvals Events
- `approval.created` - Approval requested
- `approval.approved` - Approval approved
- `approval.rejected` - Approval rejected
- `approval.escalated` - Approval escalated
- `approval.timeout` - Approval timed out

### Webhook Payload Schema

```json
{
  "event": "template.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "webhook_id": "wh_abc123",
  "attempt": 1,
  "data": {
    "id": 123,
    "name": "My Template",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Webhook Verification

All webhooks include HMAC signature in `X-Webhook-Signature` header.

```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## SDKs

### Available SDKs

#### Python SDK

```bash
pip install fliptechpro
```

```python
from fliptechpro import Client

client = Client(api_token="YOUR_TOKEN")

# Create template
template = client.templates.create(
    name="My Template",
    subject_template="Hello {{first_name}}",
    body_template="Welcome to our service"
)

# Send auto-response
response = client.templates.send_auto_response(
    lead_id=42,
    template_id=template.id
)

# Get analytics
analytics = client.templates.get_analytics(template_id=template.id, days=30)
```

#### JavaScript/TypeScript SDK

```bash
npm install fliptechpro
```

```typescript
import { FlipTechPro } from 'fliptechpro';

const client = new FlipTechPro({ apiToken: 'YOUR_TOKEN' });

// Create template
const template = await client.templates.create({
  name: "My Template",
  subject_template: "Hello {{first_name}}",
  body_template: "Welcome to our service"
});

// Send auto-response
const response = await client.templates.sendAutoResponse({
  lead_id: 42,
  template_id: template.id
});

// Get analytics
const analytics = await client.templates.getAnalytics({
  template_id: template.id,
  days: 30
});
```

#### Go SDK

```bash
go get github.com/fliptechpro/go-sdk
```

```go
package main

import (
    "github.com/fliptechpro/go-sdk"
)

func main() {
    client := fliptechpro.NewClient("YOUR_TOKEN")

    // Create template
    template, err := client.Templates.Create(ctx, &fliptechpro.CreateTemplateRequest{
        Name:             "My Template",
        SubjectTemplate:  "Hello {{first_name}}",
        BodyTemplate:     "Welcome to our service",
    })

    // Send auto-response
    response, err := client.Templates.SendAutoResponse(ctx, &fliptechpro.SendAutoResponseRequest{
        LeadID:     42,
        TemplateID: template.ID,
    })
}
```

### Postman Collection

Import the Postman collection to test all endpoints:

1. Download: [FlipTechPro.postman_collection.json](./postman/FlipTechPro.postman_collection.json)
2. Import into Postman
3. Set `base_url` and `api_token` variables
4. Run requests with built-in examples

---

## Common Tasks

### Sending a Campaign with Tracking

```python
from fliptechpro import Client

client = Client(api_token="YOUR_TOKEN")

# 1. Create template
template = client.templates.create(
    name="Campaign Template",
    subject_template="Special offer for {{company_name}}",
    body_template="Hi {{first_name}},\n\nCheck out this offer...",
    use_ai_enhancement=True
)

# 2. Get leads to send to
leads = client.leads.list(status="qualified")

# 3. Send to each lead
for lead in leads:
    response = client.templates.send_auto_response(
        lead_id=lead.id,
        template_id=template.id,
        delay_minutes=0
    )

# 4. Monitor results
analytics = client.templates.get_analytics(
    template_id=template.id,
    days=7
)
print(f"Open rate: {analytics.response_rate}")
print(f"Click rate: {analytics.conversion_rate}")
```

### Creating a Demo Site for a Lead

```python
from fliptechpro import Client

client = Client(api_token="YOUR_TOKEN")

# 1. Create demo site
site = client.demo_sites.generate(
    site_name="Acme Corp Demo",
    lead_id=42,
    template_type="landing",
    content_data={
        "headline": "Transform Your Business",
        "description": "With our innovative platform",
        "company_name": "Acme Corp"
    },
    use_ai_generation=True,
    auto_deploy=True
)

# 2. Wait for deployment
import time
while site.status != "live":
    time.sleep(5)
    site = client.demo_sites.get(site.id)

# 3. Share URL
print(f"Demo site live at: {site.vercel_url}")

# 4. Monitor analytics
analytics = client.demo_sites.get_analytics_summary(
    demo_site_id=site.id,
    days=30
)
print(f"Visitors: {analytics.total_visitors}")
```

### Setting Up Approval Workflow

```python
from fliptechpro import Client

client = Client(api_token="YOUR_TOKEN")

# 1. Create auto-approval rule
rule = client.approvals.create_auto_approval_rule(
    name="High-Quality Leads",
    description="Auto-approve enterprise leads",
    approval_types=["lead_qualification"],
    auto_approve_threshold=0.85,
    min_qualification_score=0.80,
    lead_categories=["enterprise"]
)

# 2. Create approval request
approval = client.approvals.create(
    approval_type="lead_qualification",
    resource_id=42,
    resource_data={
        "company_name": "Acme Corp",
        "opportunity_value": 50000
    },
    timeout_minutes=60
)

# 3. Check if auto-approved
if approval.auto_approved:
    print("Auto-approved!")
else:
    # 4. Get pending approvals
    pending = client.approvals.get_pending(approver_email="manager@example.com")
    print(f"{len(pending)} approvals pending")

    # 5. Reviewer approves
    client.approvals.submit_decision(
        approval_id=approval.id,
        approved=True,
        reviewer_email="manager@example.com",
        comments="Looks good"
    )
```

---

## Glossary

| Term | Definition |
|------|-----------|
| API Token | Unique credential for authenticating API requests |
| Scope | Permission level granted to an API token |
| Endpoint | Specific URL path for an API operation |
| Request | HTTP call made to an API endpoint |
| Response | Data returned by the API in response to a request |
| Webhook | HTTP callback for event notifications |
| Rate Limit | Maximum number of requests allowed in a time period |
| Pagination | Breaking results into pages for easier handling |
| Filter | Query parameter to narrow results |
| Schema | Structure and validation rules for data |

---

## Support & Resources

### Getting Help

1. **Documentation** - Check relevant API docs first
2. **Status Page** - Check system status at https://status.example.com
3. **Email Support** - support@example.com (24/7)
4. **Chat Support** - Available in account dashboard
5. **Community Forum** - https://community.example.com

### Reporting Issues

When reporting issues, include:
- API endpoint called
- Request method (GET, POST, etc.)
- Request body (if applicable)
- Error response
- Request ID (from `X-Request-ID` header)
- Timestamp of issue

### Feature Requests

Submit feature requests at: https://feature-requests.example.com

---

## Changelog

### Version 1.2.0 (January 2024)
- Added webhook retry logic
- Improved error messages
- Added rate limit headers
- Enhanced authentication security

### Version 1.1.0 (December 2023)
- Added auto-approval rules optimization
- Added demo site duplication
- Improved analytics accuracy

### Version 1.0.0 (November 2023)
- Initial release
- Templates API
- Tracking API
- Demo Sites API
- Approvals API

---

## License

FlipTech Pro API documentation is provided under the Creative Commons Attribution 4.0 International License.

---

## Legal

### Terms of Service
By using the FlipTech Pro API, you agree to our [Terms of Service](https://example.com/legal/terms)

### Privacy Policy
See our [Privacy Policy](https://example.com/legal/privacy) for data handling practices

### Data Processing Agreement
DPA available upon request for enterprise customers

---

Last Updated: January 15, 2024
