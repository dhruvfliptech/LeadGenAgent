# Campaign Management System Setup

## Overview

The Campaign Management system provides comprehensive email campaign tracking and analytics. It consists of three main tables:

1. **campaigns** - Main campaign tracking with aggregated metrics
2. **campaign_recipients** - Individual recipient tracking with delivery status
3. **email_tracking** - Granular event tracking for opens, clicks, bounces

## Database Tables

### 1. Campaigns Table

Stores campaign-level information and aggregated metrics.

```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    template_id INTEGER,
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_recipients INTEGER DEFAULT 0 NOT NULL,
    emails_sent INTEGER DEFAULT 0 NOT NULL,
    emails_opened INTEGER DEFAULT 0 NOT NULL,
    emails_clicked INTEGER DEFAULT 0 NOT NULL,
    emails_replied INTEGER DEFAULT 0 NOT NULL,
    emails_bounced INTEGER DEFAULT 0 NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

**Status Values:**
- `draft` - Campaign is being prepared
- `scheduled` - Campaign scheduled for future execution
- `running` - Campaign is actively sending emails
- `paused` - Campaign execution paused
- `completed` - Campaign execution completed
- `failed` - Campaign failed

**Computed Properties (in SQLAlchemy model):**
- `open_rate` - (emails_opened / emails_sent) * 100
- `click_rate` - (emails_clicked / emails_sent) * 100
- `reply_rate` - (emails_replied / emails_sent) * 100
- `bounce_rate` - (emails_bounced / emails_sent) * 100

**Indexes:**
- `ix_campaigns_campaign_id` (UNIQUE) - For campaign lookups
- `ix_campaigns_name` - For searching by name
- `ix_campaigns_status` - For filtering by status
- `ix_campaigns_created_by` - For user campaign queries
- `ix_campaigns_scheduled_at` - For scheduled campaigns
- `ix_campaigns_started_at` - For started campaigns
- `ix_campaigns_created_at` - For timeline queries

### 2. Campaign Recipients Table

Tracks individual recipients and their engagement status.

```sql
CREATE TABLE campaign_recipients (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    email_address VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    replied_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT uq_campaign_recipients_campaign_lead UNIQUE(campaign_id, lead_id)
);
```

**Status Values:**
- `pending` - Email queued for sending
- `queued` - Email in send queue
- `sent` - Email successfully sent
- `failed` - Email send failed
- `bounced` - Email bounced
- `unsubscribed` - Recipient unsubscribed

**Indexes:**
- `ix_campaign_recipients_campaign_id` - For campaign lookups
- `ix_campaign_recipients_lead_id` - For lead lookups
- `ix_campaign_recipients_email_address` - For recipient email searches
- `ix_campaign_recipients_status` - For filtering by status
- `ix_campaign_recipients_sent_at` - For sent emails timeline
- `ix_campaign_recipients_opened_at` - For opened emails
- `ix_campaign_recipients_clicked_at` - For clicked emails
- `ix_campaign_recipients_replied_at` - For replied emails
- `ix_campaign_recipients_bounced_at` - For bounced emails
- `uq_campaign_recipients_campaign_lead` (UNIQUE) - Prevents duplicates
- `ix_campaign_recipients_campaign_status` (COMPOSITE) - For efficient campaign status queries

### 3. Email Tracking Table

Granular event tracking for email interactions (opens, clicks, bounces, etc.).

```sql
CREATE TABLE email_tracking (
    id SERIAL PRIMARY KEY,
    campaign_recipient_id INTEGER NOT NULL REFERENCES campaign_recipients(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);
```

**Event Types:**
- `open` - Email opened
- `click` - Link clicked in email
- `bounce` - Email bounced
- `reply` - Email replied to
- `forward` - Email forwarded
- `unsubscribe` - Recipient unsubscribed
- `complain` - Spam complaint

**Event Data Structure (JSONB):**
```json
{
    "link_url": "https://example.com",
    "bounce_type": "permanent",
    "error_code": 550,
    "error_message": "User does not exist"
}
```

**Indexes:**
- `ix_email_tracking_campaign_recipient_id` - For recipient events
- `ix_email_tracking_event_type` - For event filtering
- `ix_email_tracking_ip_address` - For IP-based analytics
- `ix_email_tracking_created_at` - For timeline queries
- `ix_email_tracking_recipient_event` (COMPOSITE) - For efficient recipient event queries

## SQLAlchemy Models

Three models are defined in `/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`:

### Campaign Model

```python
from app.models import Campaign

# Create new campaign
campaign = Campaign(
    campaign_id="camp_123",
    name="Q4 2025 Outreach",
    template_id=1,
    status="draft",
    created_by=user_id
)
db.add(campaign)
db.commit()

# Access computed properties
print(f"Open rate: {campaign.open_rate}%")
print(f"Click rate: {campaign.click_rate}%")
```

### CampaignRecipient Model

```python
from app.models import CampaignRecipient

# Add recipient to campaign
recipient = CampaignRecipient(
    campaign_id=campaign.id,
    lead_id=lead.id,
    email_address="user@example.com",
    status="pending"
)
db.add(recipient)
db.commit()

# Update on send
recipient.status = "sent"
recipient.sent_at = datetime.now(timezone.utc)
db.commit()

# Update on open
recipient.opened_at = datetime.now(timezone.utc)
db.commit()
```

### EmailTracking Model

```python
from app.models import EmailTracking

# Log open event
tracking = EmailTracking(
    campaign_recipient_id=recipient.id,
    event_type="open",
    event_data={"user_agent": request.headers.get("User-Agent")},
    user_agent=request.headers.get("User-Agent"),
    ip_address=request.remote_addr
)
db.add(tracking)
db.commit()

# Log click event
tracking = EmailTracking(
    campaign_recipient_id=recipient.id,
    event_type="click",
    event_data={"link_url": "https://example.com/offers"},
    user_agent=request.headers.get("User-Agent"),
    ip_address=request.remote_addr
)
db.add(tracking)
db.commit()
```

## Query Examples

### Campaign Performance Analytics

```python
from sqlalchemy import func
from app.models import Campaign, CampaignRecipient

# Get campaign statistics
campaign = db.query(Campaign).filter_by(campaign_id="camp_123").first()
print(f"Total Recipients: {campaign.total_recipients}")
print(f"Emails Sent: {campaign.emails_sent}")
print(f"Open Rate: {campaign.open_rate}%")
print(f"Click Rate: {campaign.click_rate}%")
print(f"Reply Rate: {campaign.reply_rate}%")
print(f"Bounce Rate: {campaign.bounce_rate}%")
```

### Find Unopened Emails

```python
unopened = db.query(CampaignRecipient).filter(
    CampaignRecipient.campaign_id == campaign.id,
    CampaignRecipient.opened_at.is_(None),
    CampaignRecipient.status == "sent"
).all()
```

### Track Email Events

```python
from app.models import EmailTracking

# Get all opens for a recipient
opens = db.query(EmailTracking).filter(
    EmailTracking.campaign_recipient_id == recipient.id,
    EmailTracking.event_type == "open"
).order_by(EmailTracking.created_at).all()

# Get all clicks for a campaign
clicks = db.query(EmailTracking).filter(
    EmailTracking.event_type == "click",
    EmailTracking.campaign_recipient_id.in_(
        db.query(CampaignRecipient.id).filter(
            CampaignRecipient.campaign_id == campaign.id
        )
    )
).all()
```

### Campaign Performance by Status

```python
# Get recipients by status
by_status = db.query(
    CampaignRecipient.status,
    func.count(CampaignRecipient.id).label("count")
).filter(
    CampaignRecipient.campaign_id == campaign.id
).group_by(CampaignRecipient.status).all()

for status, count in by_status:
    print(f"{status}: {count}")
```

## Performance Optimization

### Query Optimization Tips

1. **Use Index on Campaign Status**: When filtering campaigns
   ```python
   campaigns = db.query(Campaign).filter(Campaign.status == "running").all()
   ```

2. **Use Composite Index**: For campaign recipient queries
   ```python
   recipients = db.query(CampaignRecipient).filter(
       CampaignRecipient.campaign_id == 123,
       CampaignRecipient.status == "sent"
   ).all()
   ```

3. **Batch Updates**: Use bulk operations for metric updates
   ```python
   db.query(Campaign).filter(Campaign.id == 123).update({
       Campaign.emails_sent: Campaign.emails_sent + 1,
       Campaign.updated_at: datetime.now(timezone.utc)
   })
   db.commit()
   ```

### Index Maintenance

View all indexes on campaign tables:
```sql
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename IN ('campaigns', 'campaign_recipients', 'email_tracking')
ORDER BY tablename, indexname;
```

Analyze tables for query planning:
```sql
ANALYZE campaigns;
ANALYZE campaign_recipients;
ANALYZE email_tracking;
```

## Migration Status

- Migration File: `021_create_campaign_management_tables.py`
- Status: Created and applied
- Tables Created: campaigns, campaign_recipients, email_tracking
- Models: Campaign, CampaignRecipient, EmailTracking (in `app/models/campaigns.py`)

## Alembic Integration

The migration has been recorded in Alembic for version control:

```bash
# View migration history
alembic history

# Downgrade campaign tables (if needed)
alembic downgrade -1
```

## Usage in API Endpoints

Example endpoint to track email open:

```python
@router.get("/api/v1/campaigns/track/{track_id}/open")
async def track_email_open(
    track_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    recipient = await db.execute(
        select(CampaignRecipient).where(
            CampaignRecipient.id == int(track_id)
        )
    )
    recipient = recipient.scalar_one_or_none()

    if not recipient:
        return {"status": "not_found"}

    # Log open event
    tracking = EmailTracking(
        campaign_recipient_id=recipient.id,
        event_type="open",
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host
    )
    db.add(tracking)

    # Update recipient
    recipient.opened_at = datetime.now(timezone.utc)
    await db.commit()

    return {"status": "tracked"}
```

## Backup and Recovery

### Backup Campaign Data

```bash
pg_dump -U postgres -t campaigns -t campaign_recipients -t email_tracking craigslist_leads > campaigns_backup.sql
```

### Restore Campaign Data

```bash
psql -U postgres -d craigslist_leads < campaigns_backup.sql
```

## Related Documentation

- Database Configuration: `app/core/config.py`
- Models: `app/models/campaigns.py`
- Migration: `migrations/versions/021_create_campaign_management_tables.py`
