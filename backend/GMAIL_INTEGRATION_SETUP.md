# Gmail API Integration Setup Guide

This guide walks you through setting up Gmail API integration for the conversation monitoring system.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Google Cloud Console Setup](#google-cloud-console-setup)
4. [Credential Configuration](#credential-configuration)
5. [Environment Variables](#environment-variables)
6. [First-Time Authentication](#first-time-authentication)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Gmail integration monitors your Gmail inbox for email replies from leads, automatically:
- Matches incoming emails to existing conversations
- Extracts email content and metadata
- Generates AI-powered reply suggestions
- Sends WebSocket notifications to the frontend
- Tracks conversation threads and history

**Architecture:**
```
Gmail API (Poll every 5 min)
    ↓
GmailClient (OAuth2)
    ↓
GmailMonitorService (Background Task)
    ↓
Database (Conversations, Messages)
    ↓
AIReplyGenerator (OpenAI/Claude)
    ↓
WebSocket Notification → Frontend
```

---

## Prerequisites

- Google Account with Gmail access
- Google Cloud Platform account (free tier works)
- Backend server running Python 3.11+
- PostgreSQL database

---

## Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Create Project**
3. Name your project (e.g., "CraigLeads Email Integration")
4. Note your **Project ID**

### Step 2: Enable Gmail API

1. In your project, go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click **Gmail API**
4. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** user type (unless you have a Google Workspace)
3. Fill in required fields:
   - **App name**: CraigLeads Pro
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **Save and Continue**
5. **Scopes**: Skip for now (we'll add them in credentials)
6. **Test users**: Add your Gmail address
7. Click **Save and Continue**

### Step 4: Create OAuth2 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Application type: Desktop app**
4. Name it: "CraigLeads Gmail Client"
5. Click **Create**
6. **Download JSON** - This is your `credentials.json` file
7. Save it securely (never commit to git!)

---

## Credential Configuration

### Step 1: Create Credentials Directory

```bash
# From backend directory
mkdir -p credentials
chmod 700 credentials  # Secure permissions
```

### Step 2: Move Credentials File

```bash
# Move downloaded credentials
mv ~/Downloads/client_secret_*.json credentials/gmail_credentials.json
```

### Step 3: Add to .gitignore

Ensure your `.gitignore` includes:
```
credentials/
*.pickle
gmail_token.pickle
```

---

## Environment Variables

Add to your `.env` file:

```bash
# Gmail API Integration
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.pickle
GMAIL_POLL_INTERVAL=300  # 5 minutes in seconds
GMAIL_MAX_EMAILS_PER_POLL=50
GMAIL_RATE_LIMIT_PER_MINUTE=30

# Required for sending emails
USER_NAME="Your Name"
USER_EMAIL="your-email@gmail.com"
USER_PHONE="+1234567890"  # Optional

# AI Provider (for reply generation)
AI_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-...  # If using OpenAI
ANTHROPIC_API_KEY=sk-ant-...  # If using Claude
```

---

## First-Time Authentication

### Step 1: Start Backend Server

```bash
cd backend
source venv/bin/activate  # Or your virtual environment
python -m uvicorn app.main:app --reload
```

### Step 2: OAuth Flow

On first startup, if `GMAIL_ENABLED=true`:

1. Server logs will show: `Starting OAuth2 flow`
2. A browser window opens automatically
3. Sign in with your Gmail account
4. Grant permissions:
   - Read emails
   - Send emails
   - Modify labels (mark as read/unread)
5. Click **Allow**
6. Browser shows: "Authentication successful, you may close this window"
7. Server logs: `Successfully authenticated as your-email@gmail.com`

### Step 3: Verify Token

```bash
ls -la credentials/
# Should show:
# gmail_credentials.json  (your OAuth client credentials)
# gmail_token.pickle      (your access/refresh token)
```

**Important**:
- `gmail_token.pickle` is created automatically after OAuth
- Never commit this file to version control
- Token auto-refreshes when expired

---

## Testing

### Test 1: Manual Email Check

```bash
curl http://localhost:8000/api/v1/conversations/stats/summary
```

Expected response:
```json
{
  "conversations": {
    "active": 0,
    "needs_reply": 0,
    "waiting": 0,
    "archived": 0,
    "total": 0
  },
  "ai_suggestions": {
    "pending": 0,
    "approval_rate": 0,
    "total_processed": 0
  }
}
```

### Test 2: Send Test Email

1. Send an email to a lead from the Leads page
2. Have someone reply to that email (or reply to yourself)
3. Wait up to 5 minutes (poll interval)
4. Check logs for:
   ```
   INFO: Found 1 new emails, processing...
   INFO: Processing email from sender@example.com
   INFO: Saved incoming message for conversation 1
   INFO: Generated AI suggestion 1 with confidence 0.85
   ```

### Test 3: Check Conversation API

```bash
curl http://localhost:8000/api/v1/conversations/
```

Should show the conversation with `status: "needs_reply"`.

### Test 4: WebSocket Notification

1. Open browser console on frontend
2. Connect to WebSocket: `ws://localhost:8000/ws/notifications`
3. When email arrives, you should receive:
   ```json
   {
     "type": "conversation:new_reply",
     "data": {
       "conversation_id": 1,
       "sender": {"email": "...", "name": "..."},
       "snippet": "..."
     }
   }
   ```

---

## API Endpoints

### List Conversations
```bash
GET /api/v1/conversations/
Query Params:
  - status: active|needs_reply|waiting|archived
  - search: text search
  - limit: 50 (default)
  - offset: 0 (default)
```

### Get Conversation Detail
```bash
GET /api/v1/conversations/{conversation_id}
```

### Approve AI Suggestion
```bash
POST /api/v1/conversations/{conversation_id}/approve
Body:
{
  "suggestion_id": 1,
  "edited_body": "optional edited text",
  "edit_notes": "why I edited it"
}
```

### Reject AI Suggestion
```bash
POST /api/v1/conversations/{conversation_id}/reject
Body:
{
  "suggestion_id": 1,
  "feedback_notes": "why I rejected it"
}
```

### Send Custom Reply
```bash
POST /api/v1/conversations/{conversation_id}/reply
Body:
{
  "subject": "Re: Your question",
  "body": "Thanks for reaching out..."
}
```

### Archive Conversation
```bash
PATCH /api/v1/conversations/{conversation_id}/archive
```

### Get Stats
```bash
GET /api/v1/conversations/stats/summary
```

---

## Troubleshooting

### Issue: "GMAIL_CREDENTIALS_PATH not configured"

**Solution**:
- Ensure `.env` has `GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json`
- Verify file exists: `ls credentials/gmail_credentials.json`

### Issue: "OAuth2 flow fails - credentials file not found"

**Solution**:
- Download credentials from Google Cloud Console
- Rename to `gmail_credentials.json`
- Move to `credentials/` directory

### Issue: "Token expired" or "Invalid credentials"

**Solution**:
```bash
# Delete token and re-authenticate
rm credentials/gmail_token.pickle
# Restart server - OAuth flow will run again
```

### Issue: "No new emails found" but I sent a test email

**Possible causes**:
1. **Poll interval**: Wait 5 minutes for next check
2. **Email not in inbox**: Check if email is in Spam or other folder
3. **Query filter**: Only fetches emails `to:your-email@gmail.com is:unread`

**Manual trigger** (for testing):
```python
# In Python shell
from app.services.gmail_monitor import gmail_monitor
import asyncio

async def test():
    await gmail_monitor.initialize()
    await gmail_monitor.check_for_new_emails()

asyncio.run(test())
```

### Issue: "Rate limit exceeded"

**Solution**:
- Default: 30 requests/minute
- Increase in `.env`: `GMAIL_RATE_LIMIT_PER_MINUTE=60`
- Or decrease poll frequency: `GMAIL_POLL_INTERVAL=600` (10 minutes)

### Issue: AI suggestions not generating

**Check**:
1. AI provider configured: `AI_PROVIDER=openai` or `anthropic`
2. API key set: `OPENAI_API_KEY=sk-...`
3. Check logs for AI errors:
   ```
   ERROR: OpenAI API error: ...
   ERROR: Error generating AI reply: ...
   ```

### Issue: WebSocket notifications not received

**Check**:
1. Frontend connected to WebSocket: `ws://localhost:8000/ws/notifications`
2. Check browser console for connection errors
3. Verify WebSocket endpoint in FastAPI logs

---

## Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    subject TEXT NOT NULL,
    original_message_id VARCHAR(500),
    gmail_thread_id VARCHAR(500),
    status VARCHAR(50) NOT NULL,  -- active, needs_reply, waiting, archived
    last_message_at TIMESTAMP WITH TIME ZONE,
    last_inbound_at TIMESTAMP WITH TIME ZONE,
    last_outbound_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Conversation Messages Table
```sql
CREATE TABLE conversation_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    direction VARCHAR(50) NOT NULL,  -- inbound, outbound
    message_id VARCHAR(500),  -- Email Message-ID header
    in_reply_to VARCHAR(500),
    references TEXT,
    sender_email VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255),
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    subject TEXT NOT NULL,
    body_text TEXT,
    body_html TEXT,
    gmail_message_id VARCHAR(100),
    gmail_thread_id VARCHAR(100),
    postmark_message_id VARCHAR(100),
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### AI Suggestions Table
```sql
CREATE TABLE ai_suggestions (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id),
    reply_to_message_id INTEGER REFERENCES conversation_messages(id),
    suggested_subject TEXT,
    suggested_body TEXT NOT NULL,
    confidence_score FLOAT NOT NULL,
    sentiment_analysis JSONB,
    context_used JSONB,
    ai_reasoning TEXT,
    ai_provider VARCHAR(50),
    ai_model VARCHAR(100),
    tokens_used INTEGER,
    ai_cost FLOAT,
    status VARCHAR(50) NOT NULL,  -- pending, approved, rejected, edited
    edited_body TEXT,
    edit_notes TEXT,
    sent_message_id INTEGER REFERENCES conversation_messages(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    user_rating INTEGER,
    feedback_notes TEXT
);
```

---

## Security Best Practices

1. **Never commit credentials**:
   - Add `credentials/` to `.gitignore`
   - Never commit `gmail_token.pickle`

2. **Restrict OAuth scopes**:
   - Only use necessary scopes (readonly, send, modify)
   - Don't request `gmail.full-access`

3. **Secure token storage**:
   - `credentials/` directory should be `chmod 700`
   - Token file should be `chmod 600`

4. **Production considerations**:
   - Use environment variables for all secrets
   - Consider service account if available
   - Implement token encryption at rest
   - Monitor API usage and quotas

5. **Rate limiting**:
   - Respect Gmail API quotas (250 quota units/user/second)
   - Current implementation: 30 requests/minute (well within limits)
   - Polling every 5 minutes = 288 checks/day

---

## Monitoring and Maintenance

### Health Check

```bash
curl http://localhost:8000/health
```

Should include:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"}
  },
  "features": {
    "auto_responder": false,
    "rule_engine": true,
    "notifications": true
  }
}
```

### Logs to Monitor

```bash
# Gmail authentication
grep "Gmail" logs/app.log | tail -20

# Email processing
grep "Processing email" logs/app.log | tail -20

# AI generation
grep "Generated AI suggestion" logs/app.log | tail -20

# Errors
grep "ERROR" logs/app.log | grep -i gmail | tail -20
```

### Performance Metrics

- **Poll frequency**: 5 minutes (configurable)
- **Emails per poll**: Up to 50
- **Processing time**: ~2-5 seconds per email
- **AI generation**: ~3-7 seconds per suggestion
- **Database writes**: 1 conversation + 1 message + 1 suggestion per email

---

## Next Steps

After setup is complete:

1. **Test end-to-end flow**:
   - Send email to lead
   - Reply as lead
   - Verify AI suggestion appears
   - Approve and send reply

2. **Configure AI preferences**:
   - Set confidence threshold for auto-approval
   - Customize AI prompts
   - Add response templates

3. **Monitor performance**:
   - Check API quota usage in Google Cloud Console
   - Monitor AI costs
   - Review conversation statistics

4. **Production deployment**:
   - See `DEPLOYMENT_OPERATIONS_GUIDE.md`
   - Configure environment variables
   - Set up monitoring and alerting

---

## Support

For issues or questions:

1. Check logs: `tail -f logs/app.log`
2. Review FastAPI docs: `http://localhost:8000/docs`
3. Check database: Connect to PostgreSQL and query `conversations` table
4. GitHub issues: [Your repo URL]

---

**Last Updated**: November 4, 2025
**Version**: 1.0.0
