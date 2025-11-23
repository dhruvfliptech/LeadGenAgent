# Demo Sites API Documentation

## Overview

The Demo Sites API enables AI-powered generation and deployment of personalized landing pages to Vercel. Create, customize, and deploy professional demo sites in seconds with automatic analytics integration.

**Base URL:** `/api/v1/demo-sites`

## Key Features

- AI-powered content generation (GPT-4, Claude)
- Multiple template types (landing, product showcase, case study)
- Automatic Vercel deployment with custom domains
- Built-in analytics and visitor tracking
- Component library for customization
- Mobile-responsive design
- One-click duplication and export

## Authentication

All endpoints require authentication:

```
Authorization: Bearer YOUR_API_TOKEN
```

---

## Core Endpoints

### 1. Generate Demo Site

Create a new AI-powered demo site.

**Endpoint:** `POST /generate`

**Request Schema:**

```json
{
  "site_name": "Acme Corp Demo",
  "lead_id": 42,
  "template_id": 5,
  "template_type": "landing",
  "content_data": {
    "headline": "Transform Your Business",
    "subheadline": "With our innovative platform",
    "description": "Full description of the offering",
    "company_name": "Acme Corp",
    "call_to_action": "Get Started",
    "features": [
      {"title": "Feature 1", "description": "Description"},
      {"title": "Feature 2", "description": "Description"}
    ]
  },
  "style_settings": {
    "primary_color": "#007bff",
    "secondary_color": "#6c757d",
    "font_family": "Inter, sans-serif",
    "layout_style": "modern",
    "button_style": "rounded"
  },
  "use_ai_generation": true,
  "ai_model": "gpt-4",
  "custom_subdomain": "acme-demo",
  "auto_deploy": true,
  "analytics_enabled": true
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| site_name | string | Yes | Display name for demo site |
| lead_id | integer | No | Associated lead ID |
| template_id | integer | No | Specific template to use |
| template_type | string | Yes | landing, product, case_study, custom |
| content_data | object | Yes | Content for the site (varies by template) |
| style_settings | object | No | Color and design preferences |
| use_ai_generation | boolean | No | Enable AI content enhancement (default: true) |
| ai_model | string | No | gpt-4, claude-3, gpt-3.5 (default: gpt-4) |
| custom_subdomain | string | No | Custom subdomain name |
| auto_deploy | boolean | No | Deploy immediately (default: false) |
| analytics_enabled | boolean | No | Enable analytics tracking (default: true) |

**Response Schema:**

```json
{
  "id": 123,
  "lead_id": 42,
  "template_id": 5,
  "site_name": "Acme Corp Demo",
  "project_name": "acme-demo",
  "framework": "html",
  "content_data": {...},
  "style_settings": {...},
  "generated_html": "<html>...</html>",
  "generated_css": "body { ... }",
  "generated_js": "// script",
  "status": "draft",
  "url": null,
  "vercel_url": "https://acme-demo.vercel.app",
  "vercel_project_id": "prj_abc123",
  "vercel_deployment_id": "dpl_abc123",
  "custom_domain": null,
  "analytics_enabled": true,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "deployed_at": null,
  "last_deployed_at": null
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/demo-sites/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "Acme Corp Demo",
    "lead_id": 42,
    "template_type": "landing",
    "content_data": {
      "headline": "Transform Your Business",
      "description": "With our platform"
    },
    "use_ai_generation": true,
    "auto_deploy": true
  }'
```

**Status Values:**

| Status | Description |
|--------|-------------|
| draft | Created but not deployed |
| building | Currently deploying to Vercel |
| live | Successfully deployed |
| failed | Deployment failed |
| updating | Being updated |
| deleted | Soft deleted |

---

### 2. List Demo Sites

Retrieve all demo sites with pagination and filtering.

**Endpoint:** `GET /`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Items per page (default: 20, max: 100) |
| status | string | No | Filter by status |
| lead_id | integer | No | Filter by lead ID |
| template_type | string | No | Filter by template type |

**Response Schema:**

```json
{
  "total": 42,
  "page": 1,
  "page_size": 20,
  "demo_sites": [
    {
      "id": 123,
      "site_name": "Acme Corp Demo",
      "status": "live",
      "vercel_url": "https://acme-demo.vercel.app",
      "lead_id": 42,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/demo-sites/?status=live&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Get Demo Site Details

Retrieve detailed information about a specific demo site.

**Endpoint:** `GET /{demo_site_id}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| demo_site_id | integer | Yes | Demo site ID |

**Response Schema:**

```json
{
  "id": 123,
  "lead_id": 42,
  "template_id": 5,
  "site_name": "Acme Corp Demo",
  "project_name": "acme-demo",
  "framework": "html",
  "content_data": {
    "headline": "Transform Your Business",
    "description": "With our platform",
    "features": []
  },
  "style_settings": {
    "primary_color": "#007bff",
    "secondary_color": "#6c757d"
  },
  "generated_html": "<html>...</html>",
  "generated_css": "body { ... }",
  "generated_js": "// script",
  "status": "live",
  "url": "https://acme-demo.example.com",
  "vercel_url": "https://acme-demo.vercel.app",
  "vercel_project_id": "prj_abc123",
  "vercel_deployment_id": "dpl_abc123",
  "custom_domain": "acme-demo.example.com",
  "analytics_enabled": true,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "deployed_at": "2024-01-15T10:45:00Z",
  "last_deployed_at": "2024-01-15T10:45:00Z"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/demo-sites/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. Update Demo Site

Update site configuration and content.

**Endpoint:** `PUT /{demo_site_id}`

**Request Schema:**

```json
{
  "site_name": "Updated Name",
  "content_data": {
    "headline": "Updated headline"
  },
  "style_settings": {
    "primary_color": "#ff6b6b"
  },
  "custom_domain": "new-domain.example.com",
  "analytics_enabled": true,
  "is_active": true
}
```

**Response Schema:**

Same as Get Demo Site Details

**Example Request:**

```bash
curl -X PUT "https://api.example.com/api/v1/demo-sites/123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "Updated Demo",
    "content_data": {"headline": "New headline"}
  }'
```

---

### 5. Delete Demo Site

Delete a demo site (soft delete).

**Endpoint:** `DELETE /{demo_site_id}`

**Response Schema:**

```json
{
  "message": "Demo site deleted successfully",
  "id": 123
}
```

**Example Request:**

```bash
curl -X DELETE "https://api.example.com/api/v1/demo-sites/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 6. Deploy Demo Site

Deploy a demo site to Vercel.

**Endpoint:** `POST /{demo_site_id}/deploy`

**Request Schema:**

```json
{
  "force": false
}
```

**Response Schema:**

```json
{
  "demo_site_id": 123,
  "deployment_status": "building",
  "progress": 10,
  "message": "Deployment started",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/demo-sites/123/deploy" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Polling for Status:**

```bash
# Poll every 5 seconds
for i in {1..60}; do
  curl -X GET "https://api.example.com/api/v1/demo-sites/123" \
    -H "Authorization: Bearer YOUR_TOKEN" | jq '.status'

  if [ "$(curl ...)" == '"live"' ]; then
    echo "Deployment complete!"
    break
  fi
  sleep 5
done
```

---

### 7. Preview Demo Site

Get preview of the generated site.

**Endpoint:** `GET /{demo_site_id}/preview`

**Response Schema:**

```json
{
  "html": "<html>...</html>",
  "css": "body { ... }",
  "js": "// script",
  "preview_url": "https://acme-demo.vercel.app"
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/demo-sites/123/preview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 8. Duplicate Demo Site

Create a copy of an existing demo site.

**Endpoint:** `POST /{demo_site_id}/duplicate`

**Request Schema:**

```json
{
  "new_site_name": "Acme Corp Demo v2",
  "new_lead_id": 43,
  "copy_content": true,
  "copy_style": true
}
```

**Response Schema:**

```json
{
  "id": 124,
  "site_name": "Acme Corp Demo v2",
  "status": "draft",
  "created_at": "2024-01-15T11:00:00Z"
}
```

**Example Request:**

```bash
curl -X POST "https://api.example.com/api/v1/demo-sites/123/duplicate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_site_name": "Acme Corp Demo v2",
    "copy_content": true,
    "copy_style": true
  }'
```

---

### 9. Export Demo Site

Export demo site files (HTML, CSS, JS).

**Endpoint:** `GET /{demo_site_id}/export`

**Response Schema:**

```json
{
  "files": [
    {
      "filename": "index.html",
      "content": "<html>...</html>"
    },
    {
      "filename": "styles.css",
      "content": "body { ... }"
    },
    {
      "filename": "script.js",
      "content": "// script"
    }
  ]
}
```

**Example Request:**

```bash
# Download files
curl -X GET "https://api.example.com/api/v1/demo-sites/123/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | jq '.files[] | "\(.filename): \(.content)"'
```

---

## Template Endpoints

### 10. List Templates

Retrieve all available templates.

**Endpoint:** `GET /templates`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| template_type | string | No | landing, product, case_study |
| is_active | boolean | No | Filter by active status |

**Response Schema:**

```json
{
  "total": 12,
  "templates": [
    {
      "id": 5,
      "template_name": "Modern Landing",
      "template_type": "landing",
      "description": "Modern landing page template",
      "preview_image_url": "https://...",
      "thumbnail_url": "https://...",
      "is_active": true,
      "is_default": true,
      "usage_count": 156,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/demo-sites/templates?template_type=landing" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 11. Get Template Details

Retrieve specific template details.

**Endpoint:** `GET /templates/{template_id}`

**Response Schema:**

```json
{
  "id": 5,
  "template_name": "Modern Landing",
  "template_type": "landing",
  "description": "Modern landing page template",
  "html_template": "<html>...</html>",
  "css_template": "body { ... }",
  "js_template": "// script",
  "preview_image_url": "https://...",
  "thumbnail_url": "https://...",
  "customization_options": {
    "colors": ["primary_color", "secondary_color"],
    "fonts": ["font_family"],
    "layouts": ["layout_style"]
  },
  "is_active": true,
  "is_default": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 12. Create Template

Create a new custom template.

**Endpoint:** `POST /templates`

**Request Schema:**

```json
{
  "template_name": "Custom Template",
  "template_type": "landing",
  "description": "My custom template",
  "html_template": "<html>...</html>",
  "css_template": "body { ... }",
  "js_template": "// script",
  "preview_image_url": "https://...",
  "thumbnail_url": "https://...",
  "customization_options": {},
  "is_active": true,
  "is_default": false
}
```

**Response Schema:**

Same as Get Template Details

---

## Analytics Endpoints

### 13. Get Analytics Summary

Get overall analytics for a demo site.

**Endpoint:** `GET /{demo_site_id}/analytics/summary`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| days | integer | No | Days to analyze (default: 30, max: 365) |

**Response Schema:**

```json
{
  "demo_site_id": 123,
  "period_days": 30,
  "total_visitors": 1234,
  "unique_visitors": 890,
  "page_views": 3456,
  "bounce_rate": 0.32,
  "average_time_on_page": 45.5,
  "conversion_rate": 0.08,
  "conversions": 98,
  "top_referrers": [
    {"source": "google.com", "visitors": 234},
    {"source": "direct", "visitors": 189}
  ],
  "top_pages": [
    {"page": "/", "views": 1234},
    {"page": "/features", "views": 567}
  ]
}
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/demo-sites/123/analytics/summary?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 14. Get Analytics Timeline

Get time-series analytics data.

**Endpoint:** `GET /{demo_site_id}/analytics/timeline`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| days | integer | No | Days to analyze (default: 30) |

**Response Schema:**

```json
{
  "demo_site_id": 123,
  "date_range": {
    "start": "2023-12-16",
    "end": "2024-01-15"
  },
  "timeline": [
    {
      "date": "2024-01-15",
      "visitors": 45,
      "page_views": 120,
      "conversions": 3,
      "bounce_rate": 0.30
    }
  ]
}
```

---

### 15. Track Analytics Event

Track custom analytics events.

**Endpoint:** `POST /{demo_site_id}/analytics/track`

**Request Schema:**

```json
{
  "event_type": "button_click",
  "visitor_id": "visitor_abc123",
  "event_data": {
    "button_name": "CTA Button",
    "page": "/",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response Schema:**

```json
{
  "message": "Event tracked successfully"
}
```

---

## Component Library Endpoints

### 16. List Components

Get available components.

**Endpoint:** `GET /components`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| component_type | string | No | hero, features, testimonials, cta |
| category | string | No | Component category |
| is_active | boolean | No | Filter by active status |

**Response Schema:**

```json
{
  "total": 24,
  "components": [
    {
      "id": 1,
      "component_name": "Hero Section",
      "component_type": "hero",
      "category": "sections",
      "description": "Large hero section with headline",
      "html_code": "<section>...</section>",
      "css_code": ".hero { ... }",
      "js_code": "// script",
      "usage_count": 456
    }
  ]
}
```

---

## Integration Examples

### Python SDK

```python
from demo_sites_client import DemoSitesClient

client = DemoSitesClient("https://api.example.com", "YOUR_TOKEN")

# Generate demo site
site = client.generate(
    site_name="Acme Corp Demo",
    lead_id=42,
    template_type="landing",
    content_data={
        "headline": "Transform Your Business",
        "description": "With our platform"
    },
    auto_deploy=True
)

# Wait for deployment
import time
while site['status'] != 'live':
    time.sleep(5)
    site = client.get(site['id'])

print(f"Live at: {site['vercel_url']}")

# Get analytics
analytics = client.get_analytics_summary(site['id'], days=30)
print(f"Visitors: {analytics['total_visitors']}")
```

### JavaScript SDK

```javascript
const client = new DemoSitesClient({
  baseUrl: "https://api.example.com",
  apiToken: "YOUR_TOKEN"
});

// Generate demo site
const site = await client.generate({
  siteName: "Acme Corp Demo",
  leadId: 42,
  templateType: "landing",
  contentData: {
    headline: "Transform Your Business",
    description: "With our platform"
  },
  autoDeploy: true
});

// Poll for status
await client.waitForDeployment(site.id);

console.log(`Live at: ${site.vercelUrl}`);

// Get analytics
const analytics = await client.getAnalyticsSummary(site.id, { days: 30 });
console.log(`Visitors: ${analytics.totalVisitors}`);
```

---

## Error Codes

| Code | Status | Description | Solution |
|------|--------|-------------|----------|
| 400 | Bad Request | Invalid template type | Check available template types |
| 400 | Bad Request | Missing required content | Provide all required fields |
| 404 | Not Found | Demo site not found | Verify site ID exists |
| 500 | Server Error | Generation failed | Check error message, retry |
| 502 | Bad Gateway | Vercel deployment failed | Check Vercel status, retry |

---

## Use Cases

### Use Case 1: Generate and Deploy Demo for Lead

```bash
# Generate demo site
SITE_ID=$(curl -X POST "https://api.example.com/api/v1/demo-sites/generate" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "site_name": "Lead Demo",
    "lead_id": 42,
    "template_type": "landing",
    "content_data": {"headline": "Custom Demo"},
    "auto_deploy": true
  }' | jq -r '.id')

# Wait for deployment
while sleep 5; do
  STATUS=$(curl "https://api.example.com/api/v1/demo-sites/$SITE_ID" \
    -H "Authorization: Bearer TOKEN" | jq -r '.status')

  if [ "$STATUS" = "live" ]; then
    echo "Deployed!"
    break
  fi
done
```

---

## Best Practices

1. **Use Templates** - Start with templates for faster generation
2. **Enable Analytics** - Track visitor engagement
3. **Monitor Deployment** - Poll status before sharing URL
4. **Custom Domains** - Set custom domains for branding
5. **Duplicate for Variants** - Test variations with duplication
6. **Export Regularly** - Keep backups of important sites

---

## Support

For issues:
- Email: support@example.com
- Docs: https://docs.example.com
