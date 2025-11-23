# Campaign Management API Guide

Complete guide to the FlipTech Pro Campaign Management API for email campaigns.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Background Tasks](#background-tasks)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Campaign Management API provides a complete solution for creating, managing, and tracking email campaigns with built-in analytics and engagement metrics.

### Key Features

- **Campaign Management**: Create, update, pause, resume, and delete campaigns
- **Recipient Management**: Add leads as recipients, bulk operations
- **Email Tracking**: Track opens, clicks, bounces, and replies
- **Real-time Analytics**: Live campaign statistics and performance metrics
- **Scheduled Sending**: Schedule campaigns for future execution
- **Test Mode**: Send test emails before launching campaigns

### Technology Stack

- **Backend**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Background Tasks**: Celery (ready for integration)
- **Email Tracking**: Pixel tracking, link tracking, webhook events

---

## Architecture

### Database Schema

```
campaigns
├── id (int, PK)
├── campaign_id (varchar, unique)
├── name (varchar)
├── template_id (int, nullable)
├── status (varchar) - draft, scheduled, running, paused, completed, failed
├── scheduled_at (timestamp)
├── started_at (timestamp)
├── completed_at (timestamp)
├── total_recipients (int)
├── emails_sent (int)
├── emails_opened (int)
├── emails_clicked (int)
├── emails_replied (int)
├── emails_bounced (int)
├── created_by (int, FK -> users)
├── created_at (timestamp)
└── updated_at (timestamp)

campaign_recipients
├── id (int, PK)
├── campaign_id (int, FK -> campaigns)
├── lead_id (int, FK -> leads)
├── email_address (varchar)
├── status (varchar) - pending, queued, sent, failed, bounced, unsubscribed
├── sent_at (timestamp)
├── opened_at (timestamp)
├── clicked_at (timestamp)
├── replied_at (timestamp)
├── bounced_at (timestamp)
├── error_message (text)
├── created_at (timestamp)
└── updated_at (timestamp)

email_tracking
├── id (int, PK)
├── campaign_recipient_id (int, FK -> campaign_recipients)
├── event_type (varchar) - open, click, bounce, reply, forward, unsubscribe, complain
├── event_data (json)
├── user_agent (text)
├── ip_address (inet)
└── created_at (timestamp)
```

### Service Layer Architecture

```
app/
├── api/endpoints/campaigns.py       # REST API endpoints
├── services/campaign_service.py     # Business logic
├── schemas/campaigns.py             # Pydantic models
└── models/campaigns.py              # SQLAlchemy models
```

---

## Quick Start

### 1. Create a Campaign

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Outreach Campaign",
    "template_id": 1,
    "scheduled_at": "2025-11-15T10:00:00Z"
  }'
```

Response:
```json
{
  "id": 1,
  "campaign_id": "camp_abc123def456",
  "name": "Q4 Outreach Campaign",
  "template_id": 1,
  "status": "draft",
  "scheduled_at": "2025-11-15T10:00:00Z",
  "total_recipients": 0,
  "metrics": {
    "emails_sent": 0,
    "emails_opened": 0,
    "emails_clicked": 0,
    "emails_replied": 0,
    "emails_bounced": 0,
    "open_rate": 0.0,
    "click_rate": 0.0,
    "reply_rate": 0.0,
    "bounce_rate": 0.0
  },
  "created_at": "2025-11-05T14:30:00Z",
  "updated_at": "2025-11-05T14:30:00Z"
}
```

### 2. Add Recipients

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/1/recipients" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": [1, 2, 3, 4, 5]
  }'
```

Response:
```json
{
  "success": true,
  "total_processed": 5,
  "successful": 5,
  "failed": 0,
  "errors": [],
  "message": "Added 5 recipients to campaign"
}
```

### 3. Send Test Email

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/1/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_email": "test@example.com"
  }'
```

### 4. Launch Campaign

```bash
curl -X POST "http://localhost:8000/api/v1/campaigns/1/launch" \
  -H "Content-Type: application/json" \
  -d '{
    "send_immediately": true,
    "test_mode": false
  }'
```

### 5. Monitor Campaign Stats

```bash
curl "http://localhost:8000/api/v1/campaigns/1/stats"
```

Response:
```json
{
  "campaign_id": "camp_abc123def456",
  "campaign_name": "Q4 Outreach Campaign",
  "status": "running",
  "total_recipients": 5,
  "pending": 0,
  "queued": 2,
  "sent": 3,
  "failed": 0,
  "bounced": 0,
  "opened": 1,
  "clicked": 0,
  "replied": 0,
  "metrics": {
    "emails_sent": 3,
    "emails_opened": 1,
    "emails_clicked": 0,
    "emails_replied": 0,
    "emails_bounced": 0,
    "open_rate": 33.33,
    "click_rate": 0.0,
    "reply_rate": 0.0,
    "bounce_rate": 0.0
  },
  "scheduled_at": "2025-11-15T10:00:00Z",
  "started_at": "2025-11-05T14:35:00Z",
  "completed_at": null,
  "estimated_completion": "2025-11-05T15:00:00Z",
  "progress_percentage": 60.0,
  "emails_per_hour": 36.0
}
```

---

## API Reference

### Campaign CRUD

#### Create Campaign
```http
POST /api/v1/campaigns
```

**Request Body:**
```json
{
  "name": "string",
  "template_id": "int (optional)",
  "scheduled_at": "datetime (optional)"
}
```

**Response:** `201 Created` - `CampaignResponse`

---

#### List Campaigns
```http
GET /api/v1/campaigns?status=running&page=1&page_size=20
```

**Query Parameters:**
- `status` (optional): Filter by status (draft, scheduled, running, paused, completed, failed)
- `template_id` (optional): Filter by template
- `search` (optional): Search in campaign name
- `date_from` (optional): Filter by creation date
- `date_to` (optional): Filter by creation date
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page
- `sort_by` (default: created_at): Sort field
- `sort_order` (default: desc): Sort order (asc/desc)

**Response:** `200 OK` - `CampaignListResponse`

---

#### Get Campaign
```http
GET /api/v1/campaigns/{campaign_id}
```

**Response:** `200 OK` - `CampaignResponse`

---

#### Update Campaign
```http
PUT /api/v1/campaigns/{campaign_id}
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "template_id": "int (optional)",
  "scheduled_at": "datetime (optional)",
  "status": "string (optional)"
}
```

**Response:** `200 OK` - `CampaignResponse`

**Note:** Cannot update campaigns that are running or completed.

---

#### Delete Campaign
```http
DELETE /api/v1/campaigns/{campaign_id}
```

**Response:** `200 OK` - `DeleteCampaignResponse`

**Note:** Cannot delete running campaigns. Pause them first.

---

### Recipient Management

#### Add Recipients
```http
POST /api/v1/campaigns/{campaign_id}/recipients
```

**Request Body:**
```json
{
  "lead_ids": [1, 2, 3]
}
```

**Response:** `200 OK` - `BulkOperationResponse`

---

#### List Recipients
```http
GET /api/v1/campaigns/{campaign_id}/recipients?status=sent&page=1
```

**Query Parameters:**
- `status` (optional): Filter by recipient status
- `has_opened` (optional): Filter by opened status (true/false)
- `has_clicked` (optional): Filter by clicked status (true/false)
- `has_replied` (optional): Filter by replied status (true/false)
- `has_bounced` (optional): Filter by bounced status (true/false)
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 200): Items per page

**Response:** `200 OK` - `RecipientListResponse`

---

#### Remove Recipient
```http
DELETE /api/v1/campaigns/{campaign_id}/recipients/{recipient_id}
```

**Response:** `200 OK` - `SuccessResponse`

---

### Campaign Control

#### Launch Campaign
```http
POST /api/v1/campaigns/{campaign_id}/launch
```

**Request Body:**
```json
{
  "send_immediately": true,
  "test_mode": false,
  "test_email": "test@example.com (required if test_mode=true)"
}
```

**Response:** `200 OK` - `CampaignResponse`

---

#### Pause Campaign
```http
POST /api/v1/campaigns/{campaign_id}/pause
```

**Response:** `200 OK` - `PauseCampaignResponse`

---

#### Resume Campaign
```http
POST /api/v1/campaigns/{campaign_id}/resume
```

**Response:** `200 OK` - `PauseCampaignResponse`

---

#### Send Test Email
```http
POST /api/v1/campaigns/{campaign_id}/test
```

**Request Body:**
```json
{
  "test_email": "test@example.com"
}
```

**Response:** `200 OK` - `SuccessResponse`

---

### Statistics & Analytics

#### Get Campaign Stats
```http
GET /api/v1/campaigns/{campaign_id}/stats
```

**Response:** `200 OK` - `CampaignStatsResponse`

Returns real-time campaign statistics including:
- Recipient counts by status
- Engagement metrics (opens, clicks, replies, bounces)
- Performance rates
- Progress percentage
- Estimated completion time
- Send rate (emails per hour)

---

#### Get Campaign Analytics
```http
GET /api/v1/campaigns/{campaign_id}/analytics
```

**Response:** `200 OK` - `CampaignAnalyticsResponse`

Returns detailed analytics including:
- Time series data (hourly sends, opens, clicks)
- Geographic distribution of opens/clicks
- Device and email client breakdown
- Top performers (most engaged recipients)
- Error analysis (bounce reasons, error messages)

---

### Email Tracking

#### Track Email Open
```http
POST /api/v1/campaigns/tracking/{recipient_id}/open
```

**Request Body:**
```json
{
  "event_type": "open",
  "event_data": {},
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

**Response:** `200 OK` - `EmailTrackingResponse`

**Note:** Typically called via tracking pixel in email HTML.

---

#### Track Email Click
```http
POST /api/v1/campaigns/tracking/{recipient_id}/click
```

**Request Body:**
```json
{
  "event_type": "click",
  "event_data": {
    "link_url": "https://example.com",
    "link_text": "Click here"
  },
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

**Response:** `200 OK` - `EmailTrackingResponse`

---

#### Track Email Bounce
```http
POST /api/v1/campaigns/tracking/{recipient_id}/bounce
```

**Request Body:**
```json
{
  "event_type": "bounce",
  "event_data": {
    "reason": "Mailbox full",
    "bounce_type": "soft"
  },
  "user_agent": null,
  "ip_address": null
}
```

**Response:** `200 OK` - `EmailTrackingResponse`

**Note:** Typically called by email service provider webhooks.

---

#### Get Tracking Events
```http
GET /api/v1/campaigns/tracking/{recipient_id}/events
```

**Response:** `200 OK` - `TrackingEventsListResponse`

Returns all tracking events for a specific recipient.

---

## Usage Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create campaign
campaign = requests.post(
    f"{BASE_URL}/campaigns",
    json={
        "name": "Holiday Campaign",
        "template_id": 1,
        "scheduled_at": "2025-12-01T10:00:00Z"
    }
).json()

campaign_id = campaign["id"]

# Add recipients
requests.post(
    f"{BASE_URL}/campaigns/{campaign_id}/recipients",
    json={"lead_ids": [1, 2, 3, 4, 5]}
)

# Send test email
requests.post(
    f"{BASE_URL}/campaigns/{campaign_id}/test",
    json={"test_email": "test@example.com"}
)

# Launch campaign
requests.post(
    f"{BASE_URL}/campaigns/{campaign_id}/launch",
    json={"send_immediately": True}
)

# Get stats
stats = requests.get(f"{BASE_URL}/campaigns/{campaign_id}/stats").json()
print(f"Campaign progress: {stats['progress_percentage']}%")
print(f"Open rate: {stats['metrics']['open_rate']}%")
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8000/api/v1";

// Create campaign
const campaign = await fetch(`${BASE_URL}/campaigns`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Holiday Campaign",
    template_id: 1,
    scheduled_at: "2025-12-01T10:00:00Z"
  })
}).then(res => res.json());

const campaignId = campaign.id;

// Add recipients
await fetch(`${BASE_URL}/campaigns/${campaignId}/recipients`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ lead_ids: [1, 2, 3, 4, 5] })
});

// Launch campaign
await fetch(`${BASE_URL}/campaigns/${campaignId}/launch`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ send_immediately: true })
});

// Poll for stats
const pollStats = async () => {
  const stats = await fetch(`${BASE_URL}/campaigns/${campaignId}/stats`)
    .then(res => res.json());

  console.log(`Progress: ${stats.progress_percentage}%`);
  console.log(`Open rate: ${stats.metrics.open_rate}%`);

  if (stats.status !== "completed") {
    setTimeout(pollStats, 5000); // Poll every 5 seconds
  }
};

pollStats();
```

### curl Examples

```bash
# Create campaign
CAMPAIGN_ID=$(curl -X POST "http://localhost:8000/api/v1/campaigns" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Campaign","template_id":1}' \
  | jq -r '.id')

# Add recipients
curl -X POST "http://localhost:8000/api/v1/campaigns/$CAMPAIGN_ID/recipients" \
  -H "Content-Type: application/json" \
  -d '{"lead_ids":[1,2,3]}'

# Launch campaign
curl -X POST "http://localhost:8000/api/v1/campaigns/$CAMPAIGN_ID/launch" \
  -H "Content-Type: application/json" \
  -d '{"send_immediately":true}'

# Get stats
curl "http://localhost:8000/api/v1/campaigns/$CAMPAIGN_ID/stats" | jq .

# Pause campaign
curl -X POST "http://localhost:8000/api/v1/campaigns/$CAMPAIGN_ID/pause"

# Resume campaign
curl -X POST "http://localhost:8000/api/v1/campaigns/$CAMPAIGN_ID/resume"
```

---

## Best Practices

### 1. Campaign Creation

- **Use descriptive names**: Make campaigns easy to identify
- **Test first**: Always send test emails before launching
- **Schedule wisely**: Consider timezone and optimal send times
- **Start small**: Test with a small recipient list first

### 2. Recipient Management

- **Validate emails**: Ensure leads have valid email addresses before adding
- **Remove bounces**: Regularly clean up bounced recipients
- **Segment wisely**: Use recipient filters for targeted campaigns
- **Monitor quotas**: Track email sending limits

### 3. Campaign Monitoring

- **Real-time tracking**: Use stats endpoint for live monitoring
- **Set alerts**: Monitor bounce rates and failure rates
- **Analyze engagement**: Review opens, clicks, and replies
- **Iterate**: Use analytics to improve future campaigns

### 4. Error Handling

```python
import requests
from requests.exceptions import RequestException

def create_campaign_safely(campaign_data):
    try:
        response = requests.post(
            f"{BASE_URL}/campaigns",
            json=campaign_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Error creating campaign: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error details: {e.response.json()}")
        return None
```

### 5. Rate Limiting

- Respect API rate limits
- Implement exponential backoff for retries
- Use bulk operations when possible
- Cache campaign data when appropriate

### 6. Data Retention

- Archive completed campaigns regularly
- Export analytics data for long-term storage
- Clean up old tracking events
- Comply with data retention policies

---

## Background Tasks

### Celery Integration (Ready)

The Campaign API is structured for Celery background task integration. When ready to implement:

```python
# app/tasks/campaigns.py

from celery import Celery
from app.services.campaign_service import CampaignService

celery_app = Celery('campaigns')

@celery_app.task
def send_campaign_emails(campaign_id: int):
    """
    Background task to send campaign emails.

    This task:
    1. Fetches all queued recipients
    2. Sends emails in batches
    3. Updates recipient status
    4. Tracks delivery events
    5. Updates campaign metrics
    """
    # Implementation here
    pass

@celery_app.task
def send_test_email_task(campaign_id: int, test_email: str):
    """Send test email for campaign."""
    # Implementation here
    pass

@celery_app.task
def process_bounce_webhook(recipient_id: int, bounce_data: dict):
    """Process bounce webhook from email service provider."""
    # Implementation here
    pass
```

### Task Locations

Current task stubs (marked with TODO):
- `campaign_service.py:launch_campaign()` - Line ~710
- `campaign_service.py:pause_campaign()` - Line ~745
- `campaign_service.py:resume_campaign()` - Line ~765
- `campaigns.py:send_test_email()` - Line ~470

---

## Troubleshooting

### Common Issues

#### 1. Campaign won't launch

**Error:** "Campaign has no recipients"

**Solution:**
```bash
# Check recipient count
curl "http://localhost:8000/api/v1/campaigns/{id}" | jq '.total_recipients'

# Add recipients
curl -X POST "http://localhost:8000/api/v1/campaigns/{id}/recipients" \
  -H "Content-Type: application/json" \
  -d '{"lead_ids":[1,2,3]}'
```

#### 2. Cannot update campaign

**Error:** "Cannot update campaign in 'running' status"

**Solution:**
```bash
# Pause campaign first
curl -X POST "http://localhost:8000/api/v1/campaigns/{id}/pause"

# Then update
curl -X PUT "http://localhost:8000/api/v1/campaigns/{id}" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated Name"}'
```

#### 3. Recipient already added

**Error:** "Lead X already added to campaign"

**Solution:** This is a duplicate prevention. Remove the duplicate lead_id from your request.

#### 4. Tracking not working

**Issue:** Opens/clicks not being tracked

**Solution:**
- Verify tracking pixels are in email HTML
- Check tracking endpoint is accessible
- Verify recipient_id is correct
- Check email client isn't blocking images/tracking

#### 5. Stats not updating

**Issue:** Campaign stats appear stale

**Solution:**
```bash
# Force refresh by getting campaign details
curl "http://localhost:8000/api/v1/campaigns/{id}"

# Check database directly
psql -d craigslist_leads -c "SELECT * FROM campaigns WHERE id={id};"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in .env file
LOG_LEVEL=DEBUG
```

### Health Check

```bash
curl "http://localhost:8000/api/v1/campaigns/health"
```

Expected response:
```json
{
  "success": true,
  "message": "Campaign API is healthy",
  "data": {
    "version": "1.0.0"
  }
}
```

---

## Performance Considerations

### Database Indexes

Key indexes for performance:
- `campaigns.campaign_id` (unique)
- `campaigns.status`
- `campaign_recipients.campaign_id`
- `campaign_recipients.status`
- `email_tracking.campaign_recipient_id`
- `email_tracking.event_type`

### Query Optimization

- Use pagination for large result sets
- Filter early (at database level)
- Cache campaign stats when possible
- Use bulk operations for recipient management

### Scaling Considerations

- **Horizontal scaling**: API is stateless and can be load balanced
- **Database**: Use read replicas for analytics queries
- **Background tasks**: Scale Celery workers independently
- **Email sending**: Use multiple SMTP providers for redundancy

---

## Security Considerations

### Authentication

Currently, the API doesn't enforce authentication. In production:

```python
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Only authenticated users can create campaigns
    pass
```

### Data Privacy

- Encrypt sensitive recipient data
- Implement unsubscribe functionality
- Comply with CAN-SPAM, GDPR, CASL
- Log data access for audit trails

### Rate Limiting

Implement rate limiting per user/IP:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/")
@limiter.limit("10/minute")
async def create_campaign(...):
    pass
```

---

## Support

For issues or questions:
- Check this guide
- Review API documentation at `/docs`
- Check application logs
- Contact: FlipTech Pro Support

---

**Version:** 1.0.0
**Last Updated:** November 5, 2025
**API Version:** v1
