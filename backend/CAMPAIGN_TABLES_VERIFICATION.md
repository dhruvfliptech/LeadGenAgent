# Campaign Management Tables - Verification Report

## Creation Status: COMPLETED

Date Created: November 5, 2025
Database: craigslist_leads (PostgreSQL)

## Tables Created

### 1. campaigns
Location: `/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`

**Status**: Created successfully
**Columns**: 17
- Primary Key: id (SERIAL)
- Unique Constraint: campaign_id (VARCHAR(100))
- Foreign Key: created_by -> users(id) [ON DELETE SET NULL]

**Key Fields**:
- campaign_id: Unique campaign identifier
- name: Campaign name
- template_id: Reference to email template
- status: Campaign state (draft, scheduled, running, paused, completed, failed)
- scheduled_at: When campaign is scheduled to run
- started_at: When campaign started sending
- completed_at: When campaign finished
- total_recipients: Total recipients count
- emails_sent: Number of emails sent
- emails_opened: Number of opens
- emails_clicked: Number of clicks
- emails_replied: Number of replies
- emails_bounced: Number of bounces
- created_by: User who created campaign
- created_at: Timestamp
- updated_at: Timestamp

**Indexes (9 total)**:
- campaigns_pkey (PRIMARY KEY)
- campaigns_campaign_id_key (UNIQUE)
- ix_campaigns_campaign_id
- ix_campaigns_name
- ix_campaigns_status
- ix_campaigns_created_by
- ix_campaigns_scheduled_at
- ix_campaigns_started_at
- ix_campaigns_created_at

---

### 2. campaign_recipients
Location: `/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`

**Status**: Created successfully
**Columns**: 13
- Primary Key: id (SERIAL)
- Foreign Keys:
  - campaign_id -> campaigns(id) [ON DELETE CASCADE]
  - lead_id -> leads(id) [ON DELETE CASCADE]
- Unique Constraint: (campaign_id, lead_id)

**Key Fields**:
- campaign_id: Reference to campaign
- lead_id: Reference to lead
- email_address: Recipient email (cached)
- status: Delivery status (pending, queued, sent, failed, bounced, unsubscribed)
- sent_at: When email was sent
- opened_at: When email was opened
- clicked_at: When email was clicked
- replied_at: When email was replied to
- bounced_at: When email bounced
- error_message: Error details if failed
- created_at: Timestamp
- updated_at: Timestamp

**Indexes (11 total)**:
- campaign_recipients_pkey (PRIMARY KEY)
- uq_campaign_recipients_campaign_lead (UNIQUE)
- ix_campaign_recipients_campaign_id
- ix_campaign_recipients_lead_id
- ix_campaign_recipients_email_address
- ix_campaign_recipients_status
- ix_campaign_recipients_sent_at
- ix_campaign_recipients_opened_at
- ix_campaign_recipients_clicked_at
- ix_campaign_recipients_replied_at
- ix_campaign_recipients_bounced_at
- ix_campaign_recipients_campaign_status (COMPOSITE)

---

### 3. email_tracking
Location: `/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`

**Status**: Created successfully
**Columns**: 7
- Primary Key: id (SERIAL)
- Foreign Key: campaign_recipient_id -> campaign_recipients(id) [ON DELETE CASCADE]

**Key Fields**:
- campaign_recipient_id: Reference to recipient
- event_type: Type of event (open, click, bounce, reply, forward, unsubscribe, complain)
- event_data: JSONB with event-specific data
- user_agent: Client user agent string
- ip_address: Client IP address (INET type)
- created_at: When event occurred

**Indexes (6 total)**:
- email_tracking_pkey (PRIMARY KEY)
- ix_email_tracking_campaign_recipient_id
- ix_email_tracking_event_type
- ix_email_tracking_ip_address
- ix_email_tracking_created_at
- ix_email_tracking_recipient_event (COMPOSITE)

---

## Models Integration

### Location
`/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`

### Models Exported
Updated in `/Users/greenmachine2.0/Craigslist/backend/app/models/__init__.py`:
```python
from .campaigns import Campaign, CampaignRecipient, EmailTracking
```

### Model Features

**Campaign Model**:
- Computed properties: open_rate, click_rate, reply_rate, bounce_rate
- to_dict() method for API serialization
- Relationships to CampaignRecipient (one-to-many)

**CampaignRecipient Model**:
- Relationships to Campaign and EmailTracking
- Status tracking for delivery lifecycle
- Event timestamp tracking

**EmailTracking Model**:
- Flexible JSONB event_data for extensibility
- Relationship to CampaignRecipient
- IP address tracking with INET type

---

## Migration File

### Location
`/Users/greenmachine2.0/Craigslist/backend/migrations/versions/021_create_campaign_management_tables.py`

### Migration Details
- Revision ID: 021
- Revises: 020
- Branch: main
- Status: Created and ready for Alembic execution

### Migration Contents
- Creates all three tables with proper constraints
- Creates all indexes for query optimization
- Includes upgrade and downgrade functions

---

## Database Verification

### Table Counts
```
Table                  | Columns | Indexes
campaigns              | 17      | 9
campaign_recipients    | 13      | 11
email_tracking         | 7       | 6
```

### Row Counts (Current)
```
campaigns: 0
campaign_recipients: 0
email_tracking: 0
```

### Foreign Key Relationships
- campaigns -> users (created_by)
- campaign_recipients -> campaigns (ON DELETE CASCADE)
- campaign_recipients -> leads (ON DELETE CASCADE)
- email_tracking -> campaign_recipients (ON DELETE CASCADE)

---

## Performance Optimization

### Composite Indexes Created
1. **ix_campaign_recipients_campaign_status**
   - Columns: (campaign_id, status)
   - Use Case: Filter recipients by campaign and delivery status

2. **ix_email_tracking_recipient_event**
   - Columns: (campaign_recipient_id, event_type)
   - Use Case: Get specific event types for a recipient

### Query Recommendations

**Get campaign metrics**:
```sql
SELECT campaign_id, status, COUNT(*) as count
FROM campaign_recipients
WHERE campaign_id = ?
GROUP BY campaign_id, status;
```

**Get email events**:
```sql
SELECT event_type, COUNT(*) as count
FROM email_tracking
WHERE campaign_recipient_id IN (...)
GROUP BY event_type;
```

**Find unopened emails**:
```sql
SELECT cr.id, cr.email_address
FROM campaign_recipients cr
WHERE cr.campaign_id = ? 
  AND cr.opened_at IS NULL
  AND cr.status = 'sent';
```

---

## Usage Examples

### Create Campaign
```python
from app.models import Campaign
from app.core.database import AsyncSessionLocal

campaign = Campaign(
    campaign_id="camp_q4_2025",
    name="Q4 2025 Outreach",
    status="draft",
    template_id=1,
    created_by=user_id
)
db.add(campaign)
await db.commit()
```

### Add Recipients
```python
from app.models import CampaignRecipient

recipient = CampaignRecipient(
    campaign_id=campaign.id,
    lead_id=lead.id,
    email_address="contact@example.com",
    status="pending"
)
db.add(recipient)
await db.commit()
```

### Track Events
```python
from app.models import EmailTracking

event = EmailTracking(
    campaign_recipient_id=recipient.id,
    event_type="open",
    event_data={"client": "Gmail"},
    user_agent=request.headers.get("User-Agent"),
    ip_address=request.client.host
)
db.add(event)
await db.commit()
```

---

## Files Created/Modified

### New Files
1. `/Users/greenmachine2.0/Craigslist/backend/app/models/campaigns.py`
2. `/Users/greenmachine2.0/Craigslist/backend/migrations/versions/021_create_campaign_management_tables.py`
3. `/Users/greenmachine2.0/Craigslist/backend/CAMPAIGN_MANAGEMENT_SETUP.md`
4. `/Users/greenmachine2.0/Craigslist/backend/test_campaign_models.py`
5. `/Users/greenmachine2.0/Craigslist/backend/create_campaign_tables.py`

### Modified Files
1. `/Users/greenmachine2.0/Craigslist/backend/app/models/__init__.py`
   - Added imports for Campaign, CampaignRecipient, EmailTracking
   - Updated __all__ export list

2. `/Users/greenmachine2.0/Craigslist/backend/app/models/knowledge_base.py`
   - Fixed SQLAlchemy reserved attribute issue (metadata -> metadata_json)

---

## Next Steps

1. **API Endpoints**: Create REST endpoints for campaign management
   - POST /api/v1/campaigns - Create campaign
   - GET /api/v1/campaigns/{id} - Get campaign
   - PUT /api/v1/campaigns/{id} - Update campaign
   - DELETE /api/v1/campaigns/{id} - Delete campaign

2. **Tracking Endpoints**: Create webhook endpoints
   - GET /api/v1/campaigns/track/{id}/open - Log opens
   - GET /api/v1/campaigns/track/{id}/click - Log clicks
   - GET /api/v1/campaigns/track/{id}/bounce - Log bounces

3. **Analytics Endpoints**: Create reporting endpoints
   - GET /api/v1/campaigns/{id}/analytics - Campaign metrics
   - GET /api/v1/campaigns/{id}/recipients - Recipients status
   - GET /api/v1/campaigns/{id}/events - Event log

4. **Background Tasks**: Implement with Celery/APScheduler
   - Campaign scheduler
   - Email sending queue
   - Event aggregation

---

## Validation Checklist

- [x] Tables created in database
- [x] All columns present with correct types
- [x] All constraints (FK, UNIQUE) enforced
- [x] All indexes created
- [x] SQLAlchemy models defined
- [x] Models exported from __init__.py
- [x] Migration file created
- [x] Documentation complete
- [ ] API endpoints implemented
- [ ] Integration tests written

---

Status: READY FOR API DEVELOPMENT
