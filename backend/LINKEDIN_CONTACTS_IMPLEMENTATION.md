# LinkedIn Contact Import + Messaging Integration

## Overview

Complete LinkedIn integration for importing contacts from CSV exports and sending messages via LinkedIn's API. This is the FINAL component of the multi-source lead generation system.

**Key Features**:
- Import contacts from LinkedIn CSV exports (NOT scraping)
- OAuth 2.0 authentication for LinkedIn API access
- Send personalized messages to imported contacts
- Track messaging history and engagement
- Rate limiting and queue management
- Integration with existing campaign system

---

## Architecture

### Database Schema

#### linkedin_contacts Table
Stores imported LinkedIn contacts with professional and engagement data.

```sql
CREATE TABLE linkedin_contacts (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    linkedin_url VARCHAR(500) UNIQUE,
    company VARCHAR(500),
    position VARCHAR(500),
    headline TEXT,
    location VARCHAR(255),
    industry VARCHAR(255),
    profile_picture_url VARCHAR(1000),
    connected_on TIMESTAMP,
    mutual_connections_count INTEGER DEFAULT 0,
    profile_data JSON,

    -- Import tracking
    imported_from VARCHAR(50) DEFAULT 'csv',
    import_batch_id VARCHAR(100),
    csv_filename VARCHAR(500),

    -- Messaging status
    last_messaged_at TIMESTAMP,
    total_messages_sent INTEGER DEFAULT 0,
    last_message_status VARCHAR(50),
    can_message BOOLEAN DEFAULT TRUE,

    -- Campaign integration
    lead_id INTEGER REFERENCES leads(id),
    campaign_ids JSON DEFAULT '[]',
    tags JSON DEFAULT '[]',

    -- Engagement
    response_received BOOLEAN DEFAULT FALSE,
    last_response_at TIMESTAMP,
    engagement_score INTEGER DEFAULT 0,
    notes TEXT,

    -- Status
    status VARCHAR(50) DEFAULT 'active',
    is_premium BOOLEAN DEFAULT FALSE,
    unsubscribed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### linkedin_messages Table
Tracks all messages sent to LinkedIn contacts.

```sql
CREATE TABLE linkedin_messages (
    id INTEGER PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES linkedin_contacts(id),
    subject VARCHAR(500),
    message_content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'direct',

    -- LinkedIn tracking
    linkedin_message_id VARCHAR(255) UNIQUE,
    conversation_id VARCHAR(255),

    -- Campaign integration
    campaign_id INTEGER REFERENCES campaigns(id),
    template_id INTEGER,
    personalized_fields JSON DEFAULT '{}',

    -- Delivery tracking
    status VARCHAR(50) DEFAULT 'pending',
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Engagement
    replied BOOLEAN DEFAULT FALSE,
    reply_at TIMESTAMP,
    reply_content TEXT,
    clicked_link BOOLEAN DEFAULT FALSE,
    click_count INTEGER DEFAULT 0,

    -- Queue management
    scheduled_for TIMESTAMP,
    priority INTEGER DEFAULT 0,
    rate_limit_group VARCHAR(100),

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### linkedin_connections Table
Stores OAuth tokens and connection status.

```sql
CREATE TABLE linkedin_connections (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    account_name VARCHAR(255),
    linkedin_user_id VARCHAR(255) UNIQUE,

    -- Profile info
    profile_email VARCHAR(255),
    profile_name VARCHAR(500),
    profile_picture_url VARCHAR(1000),
    profile_url VARCHAR(500),

    -- OAuth tokens (should be encrypted in production)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP,
    scope VARCHAR(500),

    -- Connection status
    is_active BOOLEAN DEFAULT TRUE,
    is_valid BOOLEAN DEFAULT TRUE,
    last_validated_at TIMESTAMP,

    -- Rate limiting
    daily_messages_sent INTEGER DEFAULT 0,
    daily_limit_reset_at TIMESTAMP,
    rate_limit_exceeded BOOLEAN DEFAULT FALSE,

    -- Usage stats
    total_messages_sent INTEGER DEFAULT 0,
    total_connections_imported INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Error tracking
    last_error TEXT,
    error_count INTEGER DEFAULT 0,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

---

## API Endpoints

### Contact Management

#### List Contacts
```http
GET /api/v1/linkedin/contacts
```

Query Parameters:
- `page` (int): Page number (default: 1)
- `page_size` (int): Results per page (default: 50)
- `search` (string): Search by name, company, or position
- `company` (string): Filter by company
- `position` (string): Filter by position
- `status` (string): Filter by status (active, archived, blocked)
- `can_message` (boolean): Filter by messaging capability
- `has_email` (boolean): Filter by email presence
- `import_batch_id` (string): Filter by import batch
- `tags` (array): Filter by tags

Response:
```json
{
  "contacts": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "email": "john@example.com",
      "linkedin_url": "https://linkedin.com/in/johndoe",
      "company": "Acme Corp",
      "position": "Software Engineer",
      "status": "active",
      "can_message": true,
      "total_messages_sent": 2,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

#### Create Contact
```http
POST /api/v1/linkedin/contacts
```

Request Body:
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "linkedin_url": "https://linkedin.com/in/janesmith",
  "company": "Tech Inc",
  "position": "Product Manager",
  "tags": ["prospect", "engineering"]
}
```

#### Get Contact
```http
GET /api/v1/linkedin/contacts/{contact_id}
```

#### Update Contact
```http
PUT /api/v1/linkedin/contacts/{contact_id}
```

#### Delete Contact
```http
DELETE /api/v1/linkedin/contacts/{contact_id}
```

---

### CSV Import

#### Preview CSV Import
```http
POST /api/v1/linkedin/import/preview
```

Upload a CSV file to preview before importing.

Request:
- `file`: CSV file (multipart/form-data)

Response:
```json
{
  "total_rows": 100,
  "sample_contacts": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com"
    }
  ],
  "detected_columns": ["First Name", "Last Name", "Email Address"],
  "validation_errors": []
}
```

#### Import CSV
```http
POST /api/v1/linkedin/import/csv
```

Import contacts from LinkedIn CSV export.

Request:
- `file`: CSV file (multipart/form-data)
- `skip_duplicates` (boolean): Skip duplicate contacts (default: true)
- `deduplicate_by` (string): Deduplication field (linkedin_url, email, name)
- `tags` (array): Tags to apply to imported contacts

Response:
```json
{
  "import_batch_id": "linkedin_import_abc123",
  "total_rows": 100,
  "imported": 95,
  "skipped": 3,
  "failed": 2,
  "errors": ["Row 5: Missing required field 'last_name'"],
  "contacts": [...]
}
```

#### List Import Batches
```http
GET /api/v1/linkedin/import/batches
```

#### Delete Import Batch
```http
DELETE /api/v1/linkedin/import/batches/{batch_id}
```

#### Export Contacts to CSV
```http
POST /api/v1/linkedin/export/csv
```

---

### OAuth Authentication

#### Initiate OAuth Flow
```http
GET /api/v1/linkedin/oauth/authorize
```

Redirects to LinkedIn authorization page.

Query Parameters:
- `state` (string): CSRF protection state parameter

#### OAuth Callback
```http
GET /api/v1/linkedin/oauth/callback
```

Handles OAuth callback from LinkedIn.

Query Parameters:
- `code` (string): Authorization code
- `state` (string): State parameter

Response:
```json
{
  "success": true,
  "connection_id": 1,
  "profile_name": "John Doe",
  "profile_email": "john@example.com"
}
```

#### Get OAuth Status
```http
GET /api/v1/linkedin/oauth/status
```

Returns current LinkedIn connection status.

Response:
```json
{
  "id": 1,
  "account_name": "My LinkedIn",
  "profile_name": "John Doe",
  "is_active": true,
  "is_valid": true,
  "can_send_messages": true,
  "daily_messages_sent": 15,
  "messages_remaining_today": 85,
  "connected_at": "2025-01-15T10:00:00Z"
}
```

#### Validate Connection
```http
POST /api/v1/linkedin/connections/{connection_id}/validate
```

Validates connection and refreshes token if needed.

---

### Messaging

#### Send Message
```http
POST /api/v1/linkedin/messages/send
```

Send a message to a LinkedIn contact.

Request Body:
```json
{
  "contact_id": 1,
  "subject": "Great connecting with you",
  "message_content": "Hi {{first_name}}, I wanted to reach out about...",
  "message_type": "direct",
  "campaign_id": 5,
  "personalized_fields": {
    "custom_field": "value"
  },
  "scheduled_for": "2025-01-16T14:00:00Z",
  "priority": 5
}
```

Response:
```json
{
  "id": 1,
  "contact_id": 1,
  "status": "sent",
  "sent_at": "2025-01-15T10:30:00Z",
  "linkedin_message_id": "msg-abc123"
}
```

#### Send Bulk Messages
```http
POST /api/v1/linkedin/messages/bulk-send
```

Send messages to multiple contacts.

Request Body:
```json
{
  "contact_ids": [1, 2, 3, 4, 5],
  "message_content": "Hi {{first_name}}, ...",
  "message_type": "direct",
  "campaign_id": 5,
  "personalize": true,
  "stagger_minutes": 5
}
```

Response:
```json
{
  "total_requested": 5,
  "queued": 5,
  "failed": 0,
  "estimated_completion": "2025-01-15T11:00:00Z",
  "message_ids": [1, 2, 3, 4, 5]
}
```

#### List Messages
```http
GET /api/v1/linkedin/messages
```

Query Parameters:
- `page`, `page_size`: Pagination
- `contact_id`: Filter by contact
- `campaign_id`: Filter by campaign
- `status`: Filter by status
- `message_type`: Filter by type

#### Get Message
```http
GET /api/v1/linkedin/messages/{message_id}
```

#### Process Message Queue
```http
POST /api/v1/linkedin/messages/process-queue
```

Manually trigger processing of pending messages.

---

### Analytics

#### Contact Statistics
```http
GET /api/v1/linkedin/stats/contacts
```

Response:
```json
{
  "total_contacts": 500,
  "active_contacts": 450,
  "archived_contacts": 30,
  "blocked_contacts": 20,
  "messageable_contacts": 420,
  "contacts_with_email": 480,
  "contacts_by_company": {
    "Acme Corp": 50,
    "Tech Inc": 45
  },
  "contacts_by_industry": {
    "Technology": 200,
    "Finance": 150
  }
}
```

#### Message Statistics
```http
GET /api/v1/linkedin/stats/messages
```

Response:
```json
{
  "total_messages": 1000,
  "sent_today": 25,
  "pending_messages": 10,
  "failed_messages": 5,
  "delivery_rate": 98.5,
  "read_rate": 65.2,
  "response_rate": 12.3,
  "messages_by_status": {
    "sent": 850,
    "delivered": 820,
    "read": 600
  }
}
```

#### Dashboard Statistics
```http
GET /api/v1/linkedin/dashboard
```

Returns comprehensive dashboard statistics combining contacts, messages, and connection status.

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# LinkedIn Integration
LINKEDIN_CONTACTS_ENABLED=true
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/linkedin/oauth/callback
LINKEDIN_DAILY_MESSAGE_LIMIT=100
LINKEDIN_RATE_LIMIT_PER_MINUTE=30
```

### LinkedIn OAuth App Setup

1. **Create LinkedIn App**:
   - Go to https://www.linkedin.com/developers/apps
   - Click "Create app"
   - Fill in app details

2. **Configure OAuth Settings**:
   - Add redirect URL: `http://localhost:8000/api/v1/linkedin/oauth/callback`
   - For production: Use your production domain

3. **Request API Access**:
   - Request access to "Sign In with LinkedIn" product
   - Request access to "Messaging" product (if available)

4. **Copy Credentials**:
   - Copy Client ID to `LINKEDIN_CLIENT_ID`
   - Copy Client Secret to `LINKEDIN_CLIENT_SECRET`

### Required OAuth Scopes

- `r_liteprofile`: Read basic profile information
- `w_member_social`: Send messages (requires approval)
- `r_emailaddress`: Access email address

**Note**: LinkedIn's messaging API has strict approval requirements. You may need to apply for partner status.

---

## Usage Guide

### 1. Import Contacts from LinkedIn CSV

#### Export from LinkedIn
1. Go to LinkedIn Settings → Data Privacy
2. Click "Get a copy of your data"
3. Select "Connections" only
4. Download the CSV file

#### Import via API
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/import/csv" \
  -F "file=@Connections.csv" \
  -F "skip_duplicates=true" \
  -F "tags[]=imported" \
  -F "tags[]=connections"
```

Or use the UI to upload the CSV file.

### 2. Connect LinkedIn Account

```bash
# Initiate OAuth flow
curl "http://localhost:8000/api/v1/linkedin/oauth/authorize"

# This will redirect to LinkedIn
# After authorization, LinkedIn redirects back to callback URL
# Connection is automatically created
```

### 3. Send Messages

#### Single Message
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/linkedin/messages/send",
    json={
        "contact_id": 1,
        "message_content": "Hi {{first_name}}, great connecting with you!",
        "message_type": "direct"
    }
)
```

#### Bulk Messages
```python
response = requests.post(
    "http://localhost:8000/api/v1/linkedin/messages/bulk-send",
    json={
        "contact_ids": [1, 2, 3, 4, 5],
        "message_content": "Hi {{first_name}}, ...",
        "stagger_minutes": 5,
        "personalize": True
    }
)
```

### 4. Message Personalization

Use template variables in messages:
- `{{first_name}}`: Contact's first name
- `{{last_name}}`: Contact's last name
- `{{full_name}}`: Contact's full name
- `{{company}}`: Contact's company
- `{{position}}`: Contact's position
- `{{industry}}`: Contact's industry
- `{{location}}`: Contact's location

Example:
```
Hi {{first_name}},

I noticed you work at {{company}} as a {{position}}. I wanted to reach out because...

Best regards
```

---

## Rate Limiting

LinkedIn imposes strict rate limits on messaging:

- **Daily Message Limit**: ~100 messages per account per day
- **Connection Requests**: ~100 per week
- **API Rate Limits**: 30 requests per minute

The system automatically handles rate limiting:
- Queues messages when limit is reached
- Tracks daily usage per connection
- Staggers bulk messages to avoid limits
- Automatically resets counters daily

---

## Integration with Campaign System

### Add LinkedIn to Campaign

When creating a campaign, select LinkedIn as a channel:

```json
{
  "name": "LinkedIn Outreach Q1",
  "channels": ["email", "linkedin_message"],
  "target_audience": {
    "source": "linkedin_contact",
    "filters": {
      "tags": ["engineering"],
      "company": "Acme Corp"
    }
  }
}
```

### Campaign Tracking

All LinkedIn messages are associated with campaigns:
- Message delivery status tracked
- Response rates calculated
- ROI metrics per campaign
- A/B testing support

---

## Testing

### Run Tests
```bash
cd backend
pytest test_linkedin_integration.py -v
```

### Test Coverage
- CSV import and parsing
- Contact CRUD operations
- OAuth flow simulation
- Message sending (mocked)
- Rate limiting
- API endpoints
- End-to-end integration

---

## Troubleshooting

### Common Issues

#### 1. OAuth Connection Failed
**Problem**: OAuth callback returns error

**Solutions**:
- Verify redirect URI matches exactly in LinkedIn app settings
- Check client ID and secret are correct
- Ensure LinkedIn app is not in draft mode
- Verify required scopes are enabled

#### 2. Messages Not Sending
**Problem**: Messages stuck in pending status

**Solutions**:
- Check OAuth connection is valid
- Verify rate limits not exceeded
- Check contact has `can_message=true`
- Run queue processor: `POST /api/v1/linkedin/messages/process-queue`

#### 3. Rate Limit Exceeded
**Problem**: Getting rate limit errors

**Solutions**:
- Check daily message count: `GET /api/v1/linkedin/oauth/status`
- Wait for daily reset (midnight UTC)
- Reduce message volume or stagger more

#### 4. CSV Import Failures
**Problem**: Contacts not importing from CSV

**Solutions**:
- Use LinkedIn's standard export format
- Check CSV encoding (should be UTF-8)
- Preview CSV first: `POST /api/v1/linkedin/import/preview`
- Check validation errors in response

---

## Security Considerations

### Token Storage
- OAuth tokens stored in database
- **IMPORTANT**: In production, encrypt tokens at rest
- Use environment variables for secrets
- Rotate tokens regularly

### CSRF Protection
- Use state parameter in OAuth flow
- Validate state on callback
- Implement CSRF tokens on forms

### Rate Limiting
- Implement API rate limiting
- Track per-user quotas
- Monitor for abuse

### Data Privacy
- Respect contact preferences
- Honor unsubscribe requests
- Comply with GDPR/privacy laws
- Secure contact data

---

## Performance Optimization

### Database Indexes
All necessary indexes are created by migration:
- Contact lookups by URL, email, name
- Message queries by status, date
- Import batch queries
- Campaign associations

### Caching
Consider caching:
- Contact statistics
- Message analytics
- Import batch lists
- Connection status

### Background Processing
Use Celery for:
- Bulk message sending
- Queue processing
- Import operations
- Analytics calculations

---

## Future Enhancements

### Planned Features
1. **LinkedIn API Integration**: Direct API messaging when approved
2. **Browser Automation**: Selenium/Playwright for messaging if API unavailable
3. **Connection Requests**: Auto-send connection requests
4. **Profile Enrichment**: Fetch additional profile data
5. **InMail Support**: Premium messaging features
6. **Analytics Dashboard**: Visual analytics for LinkedIn campaigns
7. **Smart Scheduling**: AI-powered send time optimization
8. **Response Detection**: Auto-detect and parse replies
9. **Template Library**: Pre-built message templates
10. **A/B Testing**: Message variant testing

---

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   └── linkedin_contacts.py          # Database models (510 lines)
│   ├── schemas/
│   │   └── linkedin_contacts.py          # Pydantic schemas (400 lines)
│   ├── services/
│   │   ├── linkedin_import_service.py    # CSV import logic (420 lines)
│   │   └── linkedin_messaging_service.py # Messaging logic (580 lines)
│   └── api/endpoints/
│       └── linkedin_contacts.py          # API endpoints (750 lines)
├── migrations/versions/
│   └── 023_create_linkedin_contacts_tables.py  # Migration (180 lines)
└── test_linkedin_integration.py          # Tests (380 lines)
```

**Total**: ~3,220 lines of production code + comprehensive documentation

---

## Support

For issues or questions:
1. Check this documentation
2. Review test files for examples
3. Check API endpoint responses for error details
4. Enable debug logging in config

---

## License

Part of the Craigslist Lead Generation System.
