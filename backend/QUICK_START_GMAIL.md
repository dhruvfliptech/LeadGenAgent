# Gmail Integration Quick Start

**Time Required**: 30 minutes
**Prerequisites**: Google Account, Backend running

---

## Fast Track Setup (5 Steps)

### Step 1: Google Cloud Console (10 min)

1. Go to https://console.cloud.google.com/
2. Create new project: "CraigLeads Email"
3. Enable Gmail API: APIs & Services → Library → Search "Gmail API" → Enable
4. Create OAuth credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Name: "CraigLeads Gmail Client"
   - Download JSON
5. Configure consent screen:
   - External user type
   - App name: "CraigLeads Pro"
   - Add your email as test user

### Step 2: Install Dependencies (2 min)

```bash
cd /Users/greenmachine2.0/Craigslist/backend
source venv/bin/activate  # or your virtual env

pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Step 3: Configure Credentials (2 min)

```bash
# Create credentials directory
mkdir -p credentials
chmod 700 credentials

# Move downloaded credentials
mv ~/Downloads/client_secret_*.json credentials/gmail_credentials.json

# Add to .gitignore
echo "credentials/" >> .gitignore
```

### Step 4: Set Environment Variables (2 min)

Add to `/Users/greenmachine2.0/Craigslist/backend/.env`:

```bash
# Gmail Integration
GMAIL_ENABLED=true
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.pickle
GMAIL_POLL_INTERVAL=300

# User Profile (REQUIRED for email sending)
USER_NAME="Your Full Name"
USER_EMAIL="your-email@gmail.com"
USER_PHONE="+1234567890"

# AI Provider (for reply generation)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...  # Your OpenAI API key
```

### Step 5: Run & Authenticate (5 min)

```bash
# Start backend
python -m uvicorn app.main:app --reload

# Watch for OAuth flow
# Browser window opens automatically
# Sign in with Gmail
# Grant permissions
# Done! Token saved to credentials/gmail_token.pickle
```

**Verify**:
```bash
# Check logs
tail -f logs/app.log | grep Gmail

# Should see:
# ✓ Gmail client initialized and authenticated successfully
# ✓ Gmail monitoring service started
```

---

## Test the Integration (10 min)

### Test 1: Send Email to Lead

1. Open frontend: http://localhost:3000/leads
2. Click "Send Email" on any lead
3. Send a test email

**Expected**:
- Email sent via Postmark/SMTP
- Conversation created in database
- Check: `curl http://localhost:8000/api/v1/conversations/`

### Test 2: Reply as Lead

1. Check your email inbox
2. Find the email you just sent
3. **Reply to it** (simulate lead replying)

**Expected (within 5 minutes)**:
- Gmail polling fetches your reply
- Conversation updated with inbound message
- AI generates reply suggestion
- WebSocket notification sent

**Verify**:
```bash
# Check conversations
curl http://localhost:8000/api/v1/conversations/

# Should show:
# {
#   "id": 1,
#   "status": "needs_reply",
#   "has_pending_suggestion": true,
#   ...
# }

# Get conversation details
curl http://localhost:8000/api/v1/conversations/1

# Should include:
# - messages array (your email + reply)
# - pending_suggestions array (AI suggestion)
```

### Test 3: Approve AI Suggestion

```bash
# Get suggestion ID from previous response
curl -X POST http://localhost:8000/api/v1/conversations/1/approve \
  -H "Content-Type: application/json" \
  -d '{"suggestion_id": 1}'

# Expected response:
# {
#   "success": true,
#   "message": "Reply sent successfully",
#   "message_id": 2
# }
```

**Verify**:
- Conversation status changes to "waiting"
- New outbound message created
- Email sent (check your inbox)

---

## Quick Troubleshooting

### Problem: "GMAIL_CREDENTIALS_PATH not configured"
```bash
# Check .env file
cat .env | grep GMAIL_CREDENTIALS_PATH

# Should output:
# GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json

# Verify file exists
ls -la credentials/gmail_credentials.json
```

### Problem: "OAuth flow not opening browser"
```bash
# Check credentials file is valid JSON
cat credentials/gmail_credentials.json | python -m json.tool

# Manually trigger OAuth (if needed)
python -c "
from app.integrations.gmail_client import GmailClient
client = GmailClient('credentials/gmail_credentials.json')
client.authenticate()
"
```

### Problem: "No emails found" after replying
```bash
# Check poll interval (default 5 minutes)
# Force manual check:
python -c "
import asyncio
from app.services.gmail_monitor import gmail_monitor

async def test():
    await gmail_monitor.initialize()
    await gmail_monitor.check_for_new_emails()

asyncio.run(test())
"
```

### Problem: "AI suggestion not generating"
```bash
# Check AI provider configured
cat .env | grep AI_PROVIDER
# Should be: AI_PROVIDER=openai

# Check API key
cat .env | grep OPENAI_API_KEY
# Should be: OPENAI_API_KEY=sk-...

# Check logs for AI errors
tail -f logs/app.log | grep "AI"
```

---

## Architecture Overview

```
Gmail Inbox
    ↓ (poll every 5 min)
GmailClient (OAuth2)
    ↓
GmailMonitorService (background task)
    ↓
Match to Conversation (3 strategies)
    ↓
Save Message to Database
    ↓
Trigger AI Reply Generation
    ↓
OpenAI/Claude API
    ↓
Save AI Suggestion (pending approval)
    ↓
WebSocket Notification → Frontend
    ↓
User approves → Send Reply via Gmail API
```

---

## API Endpoints Reference

```bash
# List conversations
GET /api/v1/conversations/
  ?status=needs_reply
  &search=john
  &limit=50

# Get conversation
GET /api/v1/conversations/{id}

# Approve AI suggestion
POST /api/v1/conversations/{id}/approve
{
  "suggestion_id": 1,
  "edited_body": "optional edited text"
}

# Reject AI suggestion
POST /api/v1/conversations/{id}/reject
{
  "suggestion_id": 1,
  "feedback_notes": "too formal"
}

# Send custom reply
POST /api/v1/conversations/{id}/reply
{
  "subject": "Re: Your question",
  "body": "Thanks for reaching out..."
}

# Archive conversation
PATCH /api/v1/conversations/{id}/archive

# Get stats
GET /api/v1/conversations/stats/summary
```

---

## Next Steps

After successful test:

1. **Configure Frontend**:
   - Add Conversations page route
   - Create conversation list component
   - Build AI suggestion approval UI

2. **Customize AI Behavior**:
   - Edit prompts in `app/services/ai_reply_generator.py`
   - Adjust confidence thresholds
   - Add response templates

3. **Production Deployment**:
   - See `DEPLOYMENT_OPERATIONS_GUIDE.md`
   - Set up monitoring and alerts
   - Configure error notifications

4. **Monitor Usage**:
   - Google Cloud Console → API quotas
   - OpenAI dashboard → Token usage
   - Database → Conversation metrics

---

## Files Created

```
backend/
├── app/
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── gmail_client.py          # NEW: Gmail API wrapper
│   ├── services/
│   │   ├── gmail_monitor.py         # NEW: Background monitoring
│   │   └── ai_reply_generator.py    # NEW: AI reply service
│   ├── api/endpoints/
│   │   └── conversations.py         # NEW: Conversations API
│   ├── core/
│   │   └── config.py                # MODIFIED: Added Gmail settings
│   ├── main.py                      # MODIFIED: Integrated Gmail monitor
│   └── models/
│       └── conversation.py          # EXISTS: Database models
├── credentials/                     # NEW: Created during setup
│   ├── gmail_credentials.json       # OAuth client credentials
│   └── gmail_token.pickle           # Access/refresh token
├── GMAIL_INTEGRATION_SETUP.md       # NEW: Full setup guide
├── GMAIL_IMPLEMENTATION_SUMMARY.md  # NEW: Technical details
├── QUICK_START_GMAIL.md             # NEW: This file
└── requirements_gmail.txt           # NEW: Dependencies
```

---

## Support

**Documentation**:
- Full setup: `GMAIL_INTEGRATION_SETUP.md`
- Technical details: `GMAIL_IMPLEMENTATION_SUMMARY.md`
- API docs: http://localhost:8000/docs

**Debugging**:
```bash
# Check logs
tail -f logs/app.log

# Check database
psql $DATABASE_URL -c "SELECT COUNT(*) FROM conversations;"

# Check Gmail monitoring status
curl http://localhost:8000/health | jq
```

**Common Issues**:
1. Token expired → Delete `gmail_token.pickle`, restart server
2. Rate limit → Increase `GMAIL_POLL_INTERVAL`
3. No AI suggestions → Check `OPENAI_API_KEY` in `.env`

---

**Setup Time**: ~30 minutes
**Ready for Production**: After testing
**Next**: Configure frontend conversation page

