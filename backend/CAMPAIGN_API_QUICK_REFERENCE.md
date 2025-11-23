# Campaign API Quick Reference

**Base URL:** `http://localhost:8000/api/v1/campaigns`

---

## Quick Start (5 Commands)

```bash
# 1. Create Campaign
curl -X POST "$BASE/campaigns" -H "Content-Type: application/json" \
  -d '{"name":"My Campaign","template_id":1}'

# 2. Add Recipients (use campaign ID from step 1)
curl -X POST "$BASE/campaigns/1/recipients" -H "Content-Type: application/json" \
  -d '{"lead_ids":[1,2,3,4,5]}'

# 3. Send Test
curl -X POST "$BASE/campaigns/1/test" -H "Content-Type: application/json" \
  -d '{"test_email":"test@example.com"}'

# 4. Launch
curl -X POST "$BASE/campaigns/1/launch" -H "Content-Type: application/json" \
  -d '{"send_immediately":true}'

# 5. Monitor
curl "$BASE/campaigns/1/stats"
```

---

## All Endpoints (19)

### Campaign CRUD (6)
```bash
POST   /campaigns                    # Create campaign
GET    /campaigns                    # List campaigns (paginated)
GET    /campaigns/{id}               # Get campaign details
PUT    /campaigns/{id}               # Update campaign
DELETE /campaigns/{id}               # Delete campaign
GET    /campaigns/health             # Health check
```

### Recipients (3)
```bash
POST   /campaigns/{id}/recipients              # Add recipients
GET    /campaigns/{id}/recipients              # List recipients
DELETE /campaigns/{id}/recipients/{rid}        # Remove recipient
```

### Control (4)
```bash
POST   /campaigns/{id}/launch        # Launch campaign
POST   /campaigns/{id}/pause         # Pause campaign
POST   /campaigns/{id}/resume        # Resume campaign
POST   /campaigns/{id}/test          # Send test email
```

### Analytics (2)
```bash
GET    /campaigns/{id}/stats         # Real-time stats
GET    /campaigns/{id}/analytics     # Detailed analytics
```

### Tracking (4)
```bash
POST   /campaigns/tracking/{rid}/open          # Track open
POST   /campaigns/tracking/{rid}/click         # Track click
POST   /campaigns/tracking/{rid}/bounce        # Track bounce
GET    /campaigns/tracking/{rid}/events        # Get all events
```

---

## Common Query Parameters

### List Campaigns
```
?status=running              # Filter by status
&template_id=1               # Filter by template
&search=keyword              # Search in name
&page=1                      # Page number
&page_size=20                # Items per page
&sort_by=created_at          # Sort field
&sort_order=desc             # asc or desc
```

### List Recipients
```
?status=sent                 # Filter by status
&has_opened=true             # Filter by opened
&has_clicked=true            # Filter by clicked
&has_replied=true            # Filter by replied
&has_bounced=false           # Filter by bounced
&page=1                      # Page number
&page_size=50                # Items per page
```

---

## Request Body Examples

### Create Campaign
```json
{
  "name": "Q4 Campaign",
  "template_id": 1,
  "scheduled_at": "2025-11-15T10:00:00Z"
}
```

### Update Campaign
```json
{
  "name": "Updated Campaign Name",
  "scheduled_at": "2025-11-20T14:00:00Z"
}
```

### Add Recipients
```json
{
  "lead_ids": [1, 2, 3, 4, 5]
}
```

### Launch Campaign
```json
{
  "send_immediately": true,
  "test_mode": false
}
```

### Send Test Email
```json
{
  "test_email": "test@example.com"
}
```

### Track Email Event
```json
{
  "event_type": "open",
  "event_data": {"page": "email"},
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

---

## Response Examples

### Campaign Response
```json
{
  "id": 1,
  "campaign_id": "camp_abc123",
  "name": "Q4 Campaign",
  "template_id": 1,
  "status": "running",
  "scheduled_at": "2025-11-15T10:00:00Z",
  "started_at": "2025-11-05T14:30:00Z",
  "completed_at": null,
  "total_recipients": 5,
  "metrics": {
    "emails_sent": 5,
    "emails_opened": 3,
    "emails_clicked": 1,
    "emails_replied": 0,
    "emails_bounced": 0,
    "open_rate": 60.0,
    "click_rate": 20.0,
    "reply_rate": 0.0,
    "bounce_rate": 0.0
  },
  "created_at": "2025-11-05T14:00:00Z",
  "updated_at": "2025-11-05T14:30:00Z"
}
```

### Campaign Stats
```json
{
  "campaign_id": "camp_abc123",
  "campaign_name": "Q4 Campaign",
  "status": "running",
  "total_recipients": 5,
  "pending": 0,
  "queued": 0,
  "sent": 5,
  "failed": 0,
  "bounced": 0,
  "opened": 3,
  "clicked": 1,
  "replied": 0,
  "metrics": { /* same as above */ },
  "progress_percentage": 100.0,
  "emails_per_hour": 60.0,
  "estimated_completion": null
}
```

### Bulk Operation Response
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

---

## Campaign Status Flow

```
draft → scheduled → running → completed
                       ↓
                    paused → running
                       ↓
                    failed (deleted)
```

### Status Transitions
- **draft**: Can update, add recipients, delete
- **scheduled**: Can update, add recipients, pause, delete
- **running**: Can pause, view stats, track events
- **paused**: Can resume, delete
- **completed**: Read-only, view analytics
- **failed**: Read-only (soft deleted)

---

## Recipient Status Flow

```
pending → queued → sent → opened → clicked
                     ↓        ↓
                  failed   bounced
```

---

## Error Codes

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Campaign created
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Common Errors

**Cannot update running campaign:**
```json
{
  "detail": "Cannot update campaign in 'running' status"
}
```

**Campaign has no recipients:**
```json
{
  "detail": "Campaign has no recipients"
}
```

**Lead already added:**
```json
{
  "errors": [
    {"message": "Lead 1 already added to campaign"}
  ]
}
```

---

## Python Client Example

```python
import requests

class CampaignClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url

    def create_campaign(self, name, template_id=None, scheduled_at=None):
        return requests.post(
            f"{self.base_url}/campaigns",
            json={
                "name": name,
                "template_id": template_id,
                "scheduled_at": scheduled_at,
            }
        ).json()

    def add_recipients(self, campaign_id, lead_ids):
        return requests.post(
            f"{self.base_url}/campaigns/{campaign_id}/recipients",
            json={"lead_ids": lead_ids}
        ).json()

    def launch(self, campaign_id):
        return requests.post(
            f"{self.base_url}/campaigns/{campaign_id}/launch",
            json={"send_immediately": True}
        ).json()

    def get_stats(self, campaign_id):
        return requests.get(
            f"{self.base_url}/campaigns/{campaign_id}/stats"
        ).json()

# Usage
client = CampaignClient()
campaign = client.create_campaign("My Campaign", template_id=1)
client.add_recipients(campaign["id"], [1, 2, 3])
client.launch(campaign["id"])
stats = client.get_stats(campaign["id"])
print(f"Open rate: {stats['metrics']['open_rate']}%")
```

---

## JavaScript Client Example

```javascript
class CampaignClient {
  constructor(baseUrl = "http://localhost:8000/api/v1") {
    this.baseUrl = baseUrl;
  }

  async createCampaign(name, templateId = null, scheduledAt = null) {
    const response = await fetch(`${this.baseUrl}/campaigns`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, template_id: templateId, scheduled_at: scheduledAt })
    });
    return response.json();
  }

  async addRecipients(campaignId, leadIds) {
    const response = await fetch(`${this.baseUrl}/campaigns/${campaignId}/recipients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lead_ids: leadIds })
    });
    return response.json();
  }

  async launch(campaignId) {
    const response = await fetch(`${this.baseUrl}/campaigns/${campaignId}/launch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ send_immediately: true })
    });
    return response.json();
  }

  async getStats(campaignId) {
    const response = await fetch(`${this.baseUrl}/campaigns/${campaignId}/stats`);
    return response.json();
  }
}

// Usage
const client = new CampaignClient();
const campaign = await client.createCampaign("My Campaign", 1);
await client.addRecipients(campaign.id, [1, 2, 3]);
await client.launch(campaign.id);
const stats = await client.getStats(campaign.id);
console.log(`Open rate: ${stats.metrics.open_rate}%`);
```

---

## Environment Variables

```bash
# Email Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@yourcompany.com

# Postmark (Alternative)
POSTMARK_SERVER_TOKEN=your-token-here

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/craigslist_leads

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

---

## Testing Commands

```bash
# Health Check
curl http://localhost:8000/api/v1/campaigns/health

# List All Campaigns
curl http://localhost:8000/api/v1/campaigns

# Get Campaign by ID
curl http://localhost:8000/api/v1/campaigns/1

# Filter Running Campaigns
curl "http://localhost:8000/api/v1/campaigns?status=running"

# Get Campaign Stats
curl http://localhost:8000/api/v1/campaigns/1/stats

# Get Campaign Analytics
curl http://localhost:8000/api/v1/campaigns/1/analytics

# List Recipients
curl http://localhost:8000/api/v1/campaigns/1/recipients

# Filter Opened Emails
curl "http://localhost:8000/api/v1/campaigns/1/recipients?has_opened=true"
```

---

## Important Notes

### Before Launch
1. Add at least one recipient
2. Test email template works
3. Send test email and verify
4. Check campaign stats endpoint
5. Verify tracking pixels work

### During Campaign
1. Monitor stats in real-time
2. Watch for high bounce rates
3. Check error logs
4. Pause if issues detected
5. Track engagement metrics

### After Campaign
1. Review analytics
2. Export data for reporting
3. Clean up bounced emails
4. Archive completed campaign
5. Plan next campaign improvements

---

## File Locations

```
backend/
├── app/
│   ├── api/endpoints/campaigns.py           # API endpoints
│   ├── services/campaign_service.py         # Business logic
│   ├── schemas/campaigns.py                 # Pydantic schemas
│   └── models/campaigns.py                  # Database models
├── CAMPAIGN_API_GUIDE.md                    # Full documentation
├── CAMPAIGN_API_QUICK_REFERENCE.md          # This file
└── CAMPAIGN_API_IMPLEMENTATION_SUMMARY.md   # Implementation details
```

---

## Support

- **Full Documentation:** `/backend/CAMPAIGN_API_GUIDE.md`
- **API Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

**Version:** 1.0.0 | **Updated:** November 5, 2025
