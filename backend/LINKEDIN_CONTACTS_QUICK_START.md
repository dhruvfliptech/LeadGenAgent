# LinkedIn Contacts Integration - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (Already in requirements.txt)
```bash
cd backend
pip install -r requirements.txt
```

Dependencies already included:
- `sqlalchemy` - Database ORM
- `fastapi` - API framework
- `pydantic` - Data validation
- `httpx` - HTTP client for OAuth

### Step 2: Configure Environment
Add to `/Users/greenmachine2.0/Craigslist/backend/.env`:

```bash
# LinkedIn Integration
LINKEDIN_CONTACTS_ENABLED=true
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/linkedin/oauth/callback
LINKEDIN_DAILY_MESSAGE_LIMIT=100
LINKEDIN_RATE_LIMIT_PER_MINUTE=30
```

### Step 3: Run Database Migration
```bash
cd backend
alembic upgrade head
```

This creates 3 tables:
- `linkedin_contacts`
- `linkedin_messages`
- `linkedin_connections`

### Step 4: Start Backend
```bash
cd /Users/greenmachine2.0/Craigslist
./start_backend.sh
```

Backend runs on: http://localhost:8000

### Step 5: Test API
Visit: http://localhost:8000/docs

Look for "linkedin-contacts" tag with 21 endpoints.

---

## First Contact Import (Without OAuth)

### 1. Export Contacts from LinkedIn
1. Go to LinkedIn → Settings & Privacy → Data Privacy
2. Request "Download your data"
3. Select "Connections" only
4. Download `Connections.csv`

### 2. Import via API
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/import/csv" \
  -F "file=@Connections.csv" \
  -F "skip_duplicates=true" \
  -F "tags[]=imported"
```

Response:
```json
{
  "import_batch_id": "linkedin_import_abc123",
  "total_rows": 500,
  "imported": 495,
  "skipped": 5,
  "failed": 0
}
```

### 3. List Contacts
```bash
curl "http://localhost:8000/api/v1/linkedin/contacts?page=1&page_size=10"
```

---

## OAuth Setup (For Messaging)

### Create LinkedIn App
1. Go to: https://www.linkedin.com/developers/apps
2. Click "Create app"
3. Fill in:
   - App name: Your App Name
   - LinkedIn Page: Your company page
   - Privacy policy URL: https://yoursite.com/privacy
4. Click "Create app"

### Configure OAuth
1. Go to "Auth" tab
2. Add Redirect URL:
   ```
   http://localhost:8000/api/v1/linkedin/oauth/callback
   ```
3. Copy:
   - Client ID → `LINKEDIN_CLIENT_ID`
   - Client Secret → `LINKEDIN_CLIENT_SECRET`

### Connect Account
1. Visit: http://localhost:8000/api/v1/linkedin/oauth/authorize
2. Authorize on LinkedIn
3. Check status:
   ```bash
   curl "http://localhost:8000/api/v1/linkedin/oauth/status"
   ```

---

## Send Your First Message

### Single Message
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/messages/send" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 1,
    "message_content": "Hi {{first_name}}, great connecting with you!",
    "message_type": "direct"
  }'
```

### Bulk Messages
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/messages/bulk-send" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_ids": [1, 2, 3, 4, 5],
    "message_content": "Hi {{first_name}}, I noticed you work at {{company}}...",
    "stagger_minutes": 5,
    "personalize": true
  }'
```

---

## Personalization Variables

Use in your message templates:
- `{{first_name}}` - Contact's first name
- `{{last_name}}` - Contact's last name
- `{{full_name}}` - Contact's full name
- `{{company}}` - Contact's company
- `{{position}}` - Contact's position
- `{{industry}}` - Contact's industry
- `{{location}}` - Contact's location

Example:
```
Hi {{first_name}},

I noticed you work at {{company}} as a {{position}}.
I wanted to reach out because I'm working on...

Best regards
```

---

## View Statistics

### Contact Stats
```bash
curl "http://localhost:8000/api/v1/linkedin/stats/contacts"
```

Returns:
- Total contacts
- Active/archived/blocked counts
- Contacts by company
- Contacts by industry
- Recent imports

### Message Stats
```bash
curl "http://localhost:8000/api/v1/linkedin/stats/messages"
```

Returns:
- Total messages
- Sent today
- Delivery rate
- Read rate
- Response rate

### Dashboard
```bash
curl "http://localhost:8000/api/v1/linkedin/dashboard"
```

Returns combined stats + connection status + recent activity.

---

## Common Tasks

### Filter Contacts
```bash
# By company
curl "http://localhost:8000/api/v1/linkedin/contacts?company=Acme%20Corp"

# By status
curl "http://localhost:8000/api/v1/linkedin/contacts?status=active"

# Can message
curl "http://localhost:8000/api/v1/linkedin/contacts?can_message=true"

# Multiple filters
curl "http://localhost:8000/api/v1/linkedin/contacts?company=Acme&status=active&can_message=true"
```

### Export to CSV
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/export/csv" \
  -H "Content-Type: application/json" \
  -d '{"format": "csv"}' \
  -o contacts_export.csv
```

### List Messages
```bash
# All messages
curl "http://localhost:8000/api/v1/linkedin/messages"

# By contact
curl "http://localhost:8000/api/v1/linkedin/messages?contact_id=1"

# By status
curl "http://localhost:8000/api/v1/linkedin/messages?status=sent"
```

### Process Message Queue
```bash
curl -X POST "http://localhost:8000/api/v1/linkedin/messages/process-queue"
```

---

## Rate Limits

LinkedIn limits:
- **Messages**: ~100 per day per account
- **Connections**: ~100 per week
- **API calls**: 30 per minute

Check remaining:
```bash
curl "http://localhost:8000/api/v1/linkedin/oauth/status" | jq '.messages_remaining_today'
```

---

## Troubleshooting

### Import Failed
```bash
# Preview first
curl -X POST "http://localhost:8000/api/v1/linkedin/import/preview" \
  -F "file=@Connections.csv"

# Check validation errors in response
```

### Messages Not Sending
```bash
# Check connection
curl "http://localhost:8000/api/v1/linkedin/oauth/status"

# Validate connection
curl -X POST "http://localhost:8000/api/v1/linkedin/connections/1/validate"

# Check pending messages
curl "http://localhost:8000/api/v1/linkedin/messages?status=pending"

# Process queue manually
curl -X POST "http://localhost:8000/api/v1/linkedin/messages/process-queue"
```

### Rate Limit Hit
```bash
# Check status
curl "http://localhost:8000/api/v1/linkedin/oauth/status" | jq '{
  daily_sent: .daily_messages_sent,
  remaining: .messages_remaining_today,
  rate_limited: .rate_limit_exceeded
}'

# Wait for reset (midnight UTC) or reduce volume
```

---

## Testing

### Run Tests
```bash
cd backend
pytest test_linkedin_integration.py -v
```

### Run Specific Tests
```bash
# CSV import
pytest test_linkedin_integration.py::TestCSVImport -v

# Messaging
pytest test_linkedin_integration.py::TestMessaging -v

# API endpoints
pytest test_linkedin_integration.py::TestAPIEndpoints -v
```

---

## API Documentation

Full API docs: http://localhost:8000/docs

Filter by "linkedin-contacts" tag to see all 21 endpoints.

---

## Files Reference

All files in `/Users/greenmachine2.0/Craigslist/backend/`:

**Models**: `app/models/linkedin_contacts.py`
**Schemas**: `app/schemas/linkedin_contacts.py`
**Services**:
- `app/services/linkedin_import_service.py`
- `app/services/linkedin_messaging_service.py`
**Endpoints**: `app/api/endpoints/linkedin_contacts.py`
**Migration**: `migrations/versions/023_create_linkedin_contacts_tables.py`
**Tests**: `test_linkedin_integration.py`
**Docs**: `LINKEDIN_CONTACTS_IMPLEMENTATION.md`

---

## Next Steps

1. Set up LinkedIn OAuth credentials
2. Run database migration
3. Import your LinkedIn connections
4. Connect your LinkedIn account
5. Send test messages
6. Monitor analytics

For detailed documentation, see:
- `LINKEDIN_CONTACTS_IMPLEMENTATION.md` - Full implementation guide
- `LINKEDIN_CONTACTS_INTEGRATION_SUMMARY.md` - Complete summary

---

**Ready to use!** All code is production-ready with comprehensive error handling and testing.
