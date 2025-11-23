# Auto-Response Templates API Documentation

## Overview

The Auto-Response Templates API provides comprehensive functionality for managing email response templates with AI enhancement, A/B testing, and engagement tracking. This system enables automated, personalized email responses with variable substitution and analytics.

**Base URL:** `/api/v1/templates`

## Key Features

- Template management with variable placeholders
- AI-powered content generation and enhancement
- A/B testing with statistical analysis
- Engagement tracking (opens, clicks, responses)
- Dynamic content personalization
- Security validation for template content

## Authentication

All endpoints require authentication. Include your API token in the request header:

```
Authorization: Bearer YOUR_API_TOKEN
```

## Rate Limits

- Default: 1000 requests per minute
- Burst: 100 requests per second
- Retry-After header included in 429 responses

---

## Endpoints

### 1. Get Response Templates

Retrieve all response templates with optional filtering.

**Endpoint:** `GET /`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| skip | integer | No | Number of records to skip (default: 0) |
| limit | integer | No | Maximum records to return (default: 100, max: 1000) |
| category | string | No | Filter by template category |
| is_active | boolean | No | Filter by active status |

**Response Schema:**

```json
[
  {
    "id": 1,
    "name": "New Lead Follow-up",
    "description": "Initial follow-up for new leads",
    "category": "leads",
    "subject_template": "Great opportunity for {{company_name}}",
    "body_template": "Hi {{first_name}},\n\nWe have a perfect match...",
    "variables": {
      "company_name": {"required": true, "type": "string"},
      "first_name": {"required": true, "type": "string"},
      "opportunity_value": {"required": false, "type": "number"}
    },
    "use_ai_enhancement": true,
    "ai_tone": "professional",
    "ai_length": "medium",
    "is_active": true,
    "is_test_variant": false,
    "control_template_id": null,
    "test_weight": 50.0,
    "sent_count": 150,
    "response_count": 45,
    "conversion_count": 12,
    "response_rate": 0.30,
    "conversion_rate": 0.08,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/templates/?category=leads&is_active=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 400 | Invalid parameters | Filter parameters are invalid |
| 401 | Unauthorized | Missing or invalid authentication |
| 500 | Server error | Internal server error |

---

### 2. Get Single Template

Retrieve a specific response template.

**Endpoint:** `GET /{template_id}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| template_id | integer | Yes | Template ID |

**Response Schema:**

```json
{
  "id": 1,
  "name": "New Lead Follow-up",
  "description": "Initial follow-up for new leads",
  "category": "leads",
  "subject_template": "Great opportunity for {{company_name}}",
  "body_template": "Hi {{first_name}},\n\nWe have a perfect match...",
  "variables": {
    "company_name": {"required": true, "type": "string"},
    "first_name": {"required": true, "type": "string"}
  },
  "use_ai_enhancement": true,
  "ai_tone": "professional",
  "ai_length": "medium",
  "is_active": true,
  "is_test_variant": false,
  "control_template_id": null,
  "test_weight": 50.0,
  "sent_count": 150,
  "response_count": 45,
  "conversion_count": 12,
  "response_rate": 0.30,
  "conversion_rate": 0.08,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/templates/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 404 | Template not found | Template ID does not exist |
| 401 | Unauthorized | Missing or invalid authentication |
| 500 | Server error | Internal server error |

---

### 3. Create Response Template

Create a new response template with optional AI enhancement.

**Endpoint:** `POST /`

**Request Schema:**

```json
{
  "name": "New Lead Follow-up",
  "description": "Initial follow-up for new leads",
  "category": "leads",
  "subject_template": "Great opportunity for {{company_name}}",
  "body_template": "Hi {{first_name}},\n\nWe have identified a perfect opportunity...",
  "variables": {
    "company_name": {"required": true, "type": "string"},
    "first_name": {"required": true, "type": "string"},
    "opportunity_value": {"required": false, "type": "number"}
  },
  "use_ai_enhancement": true,
  "ai_tone": "professional",
  "ai_length": "medium",
  "test_weight": 50.0
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-----------|-------------|
| name | string | Yes | Max 255 chars | Template name |
| description | string | No | Max 1000 chars | Template description |
| category | string | No | - | Template category for organization |
| subject_template | string | Yes | Max 500 chars | Email subject with {{placeholders}} |
| body_template | string | Yes | Max 10000 chars | Email body with {{placeholders}} |
| variables | object | No | - | Variable definitions and validation rules |
| use_ai_enhancement | boolean | No | - | Enable AI content enhancement |
| ai_tone | string | No | professional, casual, formal, persuasive | AI tone preference |
| ai_length | string | No | short, medium, long | AI content length |
| test_weight | number | No | 0-100 | Weight for A/B test distribution |

**Response Schema:**

```json
{
  "id": 123,
  "name": "New Lead Follow-up",
  "description": "Initial follow-up for new leads",
  "category": "leads",
  "subject_template": "Great opportunity for {{company_name}}",
  "body_template": "Hi {{first_name}},\n\nWe have identified a perfect opportunity...",
  "variables": {
    "company_name": {"required": true, "type": "string"},
    "first_name": {"required": true, "type": "string"},
    "opportunity_value": {"required": false, "type": "number"}
  },
  "use_ai_enhancement": true,
  "ai_tone": "professional",
  "ai_length": "medium",
  "is_active": true,
  "is_test_variant": false,
  "control_template_id": null,
  "test_weight": 50.0,
  "sent_count": 0,
  "response_count": 0,
  "conversion_count": 0,
  "response_rate": 0.0,
  "conversion_rate": 0.0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/templates/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Lead Follow-up",
    "description": "Initial follow-up for new leads",
    "category": "leads",
    "subject_template": "Great opportunity for {{company_name}}",
    "body_template": "Hi {{first_name}},\n\nWe have identified...",
    "use_ai_enhancement": true,
    "ai_tone": "professional",
    "ai_length": "medium"
  }'
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 400 | Invalid template content | Template failed security validation |
| 400 | Subject/body too long | Template content exceeds limits |
| 401 | Unauthorized | Missing or invalid authentication |
| 500 | Server error | Internal server error |

---

### 4. Update Response Template

Update an existing response template.

**Endpoint:** `PUT /{template_id}`

**Request Schema:**

```json
{
  "name": "Updated Lead Follow-up",
  "description": "Updated description",
  "category": "leads",
  "subject_template": "Updated subject template",
  "body_template": "Updated body template",
  "variables": {},
  "use_ai_enhancement": false,
  "ai_tone": "professional",
  "ai_length": "medium",
  "is_active": true,
  "test_weight": 60.0
}
```

**Response Schema:**

Same as Create Response Template

**Example Request:**

```bash
curl -X PUT "https://api.example.com/api/v1/templates/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Lead Follow-up",
    "ai_tone": "casual"
  }'
```

---

### 5. Delete Response Template

Delete a response template.

**Endpoint:** `DELETE /{template_id}`

**Response Schema:**

```json
{
  "message": "Template deleted successfully"
}
```

**Constraints:**

- Cannot delete templates with active pending or sent auto-responses
- Will return 400 error if template is in use

**Example Request:**

```bash
curl -X DELETE "https://api.example.com/api/v1/templates/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 400 | Cannot delete template with X active responses | Template has pending/sent responses |
| 404 | Template not found | Template ID does not exist |
| 401 | Unauthorized | Missing or invalid authentication |
| 500 | Server error | Internal server error |

---

## Auto-Response Endpoints

### 6. Get Auto-Responses

Retrieve auto-responses with filtering.

**Endpoint:** `GET /responses/`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| skip | integer | No | Number of records to skip |
| limit | integer | No | Maximum records (default: 100, max: 1000) |
| status | string | No | pending, sent, failed, opened, clicked |
| lead_id | integer | No | Filter by lead ID |
| template_id | integer | No | Filter by template ID |

**Response Schema:**

```json
[
  {
    "id": 1,
    "lead_id": 42,
    "template_id": 5,
    "subject": "Great opportunity for Acme Corp",
    "body": "Hi John,\n\nWe have identified...",
    "status": "sent",
    "scheduled_at": "2024-01-15T10:30:00Z",
    "sent_at": "2024-01-15T10:32:00Z",
    "delay_minutes": 5,
    "error_message": null,
    "retry_count": 0,
    "email_opened": true,
    "email_clicked": true,
    "lead_responded": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 7. Create Auto-Response

Create an auto-response to send based on a template.

**Endpoint:** `POST /responses/`

**Request Schema:**

```json
{
  "lead_id": 42,
  "template_id": 5,
  "delay_minutes": 5,
  "personalization_config": {
    "company_name": "Acme Corp",
    "first_name": "John",
    "opportunity_value": 50000
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lead_id | integer | Yes | Lead to send response to |
| template_id | integer | Yes | Template to use |
| delay_minutes | integer | No | Delay before sending (default: 0) |
| personalization_config | object | No | Variable values for personalization |

**Response Schema:**

```json
{
  "id": 1,
  "lead_id": 42,
  "template_id": 5,
  "subject": "Great opportunity for Acme Corp",
  "body": "Hi John,\n\nWe have identified...",
  "status": "pending",
  "scheduled_at": "2024-01-15T10:35:00Z",
  "sent_at": null,
  "delay_minutes": 5,
  "error_message": null,
  "retry_count": 0,
  "email_opened": false,
  "email_clicked": false,
  "lead_responded": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/templates/responses/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 42,
    "template_id": 5,
    "delay_minutes": 5,
    "personalization_config": {
      "company_name": "Acme Corp",
      "first_name": "John"
    }
  }'
```

---

### 8. Track Response Engagement

Track engagement events for auto-responses.

**Endpoint:** `POST /responses/{response_id}/track/{event_type}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| response_id | integer | Yes | Auto-response ID |
| event_type | string | Yes | email_opened, email_clicked, lead_responded |
| event_data | object | No | Additional event data |

**Response Schema:**

```json
{
  "message": "Tracked email_opened event for response 1"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/templates/responses/1/track/email_opened" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Analytics Endpoints

### 9. Get Template Analytics

Get performance analytics for templates.

**Endpoint:** `GET /analytics/templates`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| days | integer | No | Days to analyze (default: 30, max: 365) |

**Response Schema:**

```json
{
  "period_days": 30,
  "total_templates": 15,
  "active_templates": 12,
  "total_sends": 2500,
  "total_responses": 625,
  "average_response_rate": 0.25,
  "top_performers": [
    {
      "template_id": 1,
      "template_name": "New Lead Follow-up",
      "response_rate": 0.35,
      "conversion_rate": 0.12,
      "sent_count": 450
    }
  ]
}
```

---

### 10. Get A/B Testing Results

Get A/B test results and statistics.

**Endpoint:** `GET /analytics/ab-testing`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| template_id | integer | No | Filter by specific template |

**Response Schema:**

```json
{
  "results": [
    {
      "template_id": 5,
      "template_name": "Lead Follow-up",
      "is_test_variant": false,
      "control_template_id": null,
      "sent_count": 250,
      "response_count": 75,
      "conversion_count": 20,
      "response_rate": 0.30,
      "conversion_rate": 0.08,
      "test_weight": 100.0
    },
    {
      "template_id": 6,
      "template_name": "Lead Follow-up (Variant B)",
      "is_test_variant": true,
      "control_template_id": 5,
      "sent_count": 250,
      "response_count": 90,
      "conversion_count": 25,
      "response_rate": 0.36,
      "conversion_rate": 0.10,
      "test_weight": 100.0
    }
  ]
}
```

---

## Preview Endpoint

### 11. Preview Template Rendering

Preview how a template renders for a specific lead.

**Endpoint:** `POST /test/preview-template`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| template_id | integer | Yes | Template ID to preview |
| lead_id | integer | Yes | Lead ID for variable substitution |

**Response Schema:**

```json
{
  "template_id": 5,
  "lead_id": 42,
  "rendered_subject": "Great opportunity for Acme Corp",
  "rendered_body": "Hi John,\n\nWe have identified a perfect match...",
  "available_variables": {
    "company_name": "Acme Corp",
    "first_name": "John",
    "email": "john@acme.com",
    "phone": "555-1234",
    "opportunity_value": 50000
  }
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/templates/test/preview-template" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 5,
    "lead_id": 42
  }'
```

---

## Use Cases

### Use Case 1: Create and Deploy a Lead Follow-up Template

```bash
# Step 1: Create template
curl -X POST "https://api.example.com/api/v1/templates/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Qualified Lead Follow-up",
    "category": "leads",
    "subject_template": "Exclusive opportunity for {{company_name}}",
    "body_template": "Hi {{first_name}},\n\nWe found a match...",
    "use_ai_enhancement": true,
    "ai_tone": "professional"
  }'
# Returns: template_id = 123

# Step 2: Preview for a lead
curl -X POST "https://api.example.com/api/v1/templates/test/preview-template" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 123,
    "lead_id": 42
  }'

# Step 3: Send auto-response
curl -X POST "https://api.example.com/api/v1/templates/responses/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 42,
    "template_id": 123,
    "delay_minutes": 0
  }'
```

### Use Case 2: A/B Test Two Templates

```bash
# Create control template
curl -X POST "https://api.example.com/api/v1/templates/" \
  -d '{"name": "Follow-up A", "category": "leads", ...}'
# Returns: template_id = 10

# Create variant template with control_template_id = 10
curl -X POST "https://api.example.com/api/v1/templates/" \
  -d '{
    "name": "Follow-up B (Variant)",
    "category": "leads",
    "is_test_variant": true,
    "control_template_id": 10,
    "test_weight": 50.0,
    ...
  }'
# Returns: template_id = 11

# Later: Get A/B test results
curl "https://api.example.com/api/v1/templates/analytics/ab-testing?template_id=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Codes Reference

| Code | Status | Description | Solution |
|------|--------|-------------|----------|
| 400 | Bad Request | Invalid template content | Check template syntax and constraints |
| 400 | Bad Request | Subject/body exceeds limit | Reduce template length |
| 400 | Bad Request | Template with active responses | Cancel pending responses first |
| 401 | Unauthorized | Missing authentication | Include Authorization header |
| 404 | Not Found | Template/Lead not found | Verify IDs exist |
| 500 | Server Error | Internal error | Check server logs, retry later |

---

## SDK Examples

### Python

```python
import requests

class TemplateClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def create_template(self, name, subject, body, **kwargs):
        """Create a new response template."""
        payload = {
            "name": name,
            "subject_template": subject,
            "body_template": body,
            **kwargs
        }
        response = requests.post(
            f"{self.base_url}/api/v1/templates/",
            json=payload,
            headers=self.headers
        )
        return response.json()

    def send_auto_response(self, lead_id, template_id, personalization=None):
        """Send an auto-response based on template."""
        payload = {
            "lead_id": lead_id,
            "template_id": template_id,
            "personalization_config": personalization or {}
        }
        response = requests.post(
            f"{self.base_url}/api/v1/templates/responses/",
            json=payload,
            headers=self.headers
        )
        return response.json()

# Usage
client = TemplateClient("https://api.example.com", "YOUR_TOKEN")
template = client.create_template(
    name="Lead Follow-up",
    subject="Opportunity for {{company_name}}",
    body="Hi {{first_name}},..."
)
```

### JavaScript

```javascript
class TemplateClient {
  constructor(baseUrl, apiToken) {
    this.baseUrl = baseUrl;
    this.apiToken = apiToken;
  }

  async createTemplate(data) {
    const response = await fetch(`${this.baseUrl}/api/v1/templates/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async sendAutoResponse(leadId, templateId, personalization = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/templates/responses/`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${this.apiToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        lead_id: leadId,
        template_id: templateId,
        personalization_config: personalization
      })
    });
    return response.json();
  }
}

// Usage
const client = new TemplateClient("https://api.example.com", "YOUR_TOKEN");
const template = await client.createTemplate({
  name: "Lead Follow-up",
  subject_template: "Opportunity for {{company_name}}",
  body_template: "Hi {{first_name}},..."
});
```

---

## Webhooks

### Template Events

Templates system can trigger webhooks for:
- `template.created` - New template created
- `template.updated` - Template updated
- `template.deleted` - Template deleted
- `response.sent` - Auto-response sent
- `response.opened` - Email opened
- `response.clicked` - Link clicked

Configure webhooks in your account settings.

---

## Best Practices

1. **Use Variables Consistently** - Always use consistent variable names across templates
2. **Test Before Deploy** - Use preview endpoint to test rendering
3. **Monitor A/B Tests** - Check analytics regularly during A/B tests
4. **Handle Delays** - Use delay_minutes for strategic timing
5. **Track Engagement** - Log tracking events for analytics
6. **Validate Content** - Ensure template variables match lead data
7. **Version Templates** - Use description field to track template versions

---

## Support

For issues or questions:
- Email: support@example.com
- Docs: https://docs.example.com
- Status: https://status.example.com
