# n8n Quick Start Guide - CraigLeads Pro

Get n8n up and running in 5 minutes.

## Prerequisites

- Docker installed and running
- Backend API running on port 8000
- Frontend running on port 3000 (optional)

## Installation (5 Steps)

### Step 1: Start n8n

```bash
cd /Users/greenmachine2.0/Craigslist
./scripts/start_n8n.sh
```

Wait for:
```
✓ PostgreSQL is healthy
✓ Redis is healthy
✓ n8n is healthy
```

### Step 2: Access n8n UI

Open browser: http://localhost:5678

Login:
- Username: `admin`
- Password: `changeme`

### Step 3: Change Password

1. Click gear icon (Settings)
2. Go to "Users"
3. Change password
4. Save

### Step 4: Add API Credentials

1. Click "Credentials" in left sidebar
2. Click "Add Credential"
3. Search for "CraigLeads Pro API"
4. Fill in:
   - API URL: `http://host.docker.internal:8000`
   - API Key: Get from backend (see below)
5. Click "Test" then "Save"

**Get API Key from Backend**:
```bash
# Option 1: Check .env file
cat backend/.env | grep API_KEY

# Option 2: Generate new key (if backend supports it)
curl -X POST http://localhost:8000/api/v1/auth/api-keys \
  -H "Content-Type: application/json"
```

### Step 5: Import Workflows

1. Click "Workflows" in left sidebar
2. Click "..." → "Import from File"
3. Select workflow from `n8n/workflows/`
4. Activate workflow (toggle switch)

## Quick Test

### Test Backend Webhook

```bash
curl -X POST http://localhost:8000/api/v1/n8n-webhooks/webhook/lead-scraped \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "test-123",
    "business_name": "Test Corp",
    "category": "contractors",
    "location": "San Francisco",
    "score": 85
  }'
```

Expected output:
```json
{
  "status": "received",
  "lead_id": "test-123",
  "execution_id": "exec_...",
  "message": "Lead processing workflow initiated"
}
```

### Test n8n Node

1. Create new workflow
2. Add "CraigLeads Pro" node
3. Select "Lead" → "Get All"
4. Execute manually
5. Check output

## Common Commands

```bash
# Start n8n
./scripts/start_n8n.sh

# Stop n8n
./scripts/stop_n8n.sh

# View logs
docker-compose -f docker-compose.n8n.yml logs -f n8n

# Restart n8n
docker-compose -f docker-compose.n8n.yml restart n8n

# Check status
docker-compose -f docker-compose.n8n.yml ps

# Database backup
docker-compose -f docker-compose.n8n.yml exec postgres pg_dump -U n8n n8n > backup.sql
```

## Troubleshooting

### n8n won't start

```bash
# Check logs
docker-compose -f docker-compose.n8n.yml logs n8n

# Reset everything
docker-compose -f docker-compose.n8n.yml down -v
./scripts/start_n8n.sh
```

### Can't connect to backend API

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check Docker network
docker-compose -f docker-compose.n8n.yml exec n8n ping host.docker.internal

# Use correct URL in credentials:
# http://host.docker.internal:8000 (NOT localhost)
```

### Webhooks not working

```bash
# Test webhook endpoint
curl http://localhost:5678/webhook/test

# Check workflow activation
# Make sure toggle is ON in workflow list
```

## What's Next?

1. Read full documentation: `/n8n/README.md`
2. Import workflow templates: `/n8n/workflows/`
3. Customize workflows for your needs
4. Set up monitoring and alerts
5. Configure email notifications

## Support

- Full documentation: `/n8n/README.md`
- Implementation report: `/PHASE5_TASK1_IMPLEMENTATION_REPORT.md`
- n8n official docs: https://docs.n8n.io

## Security Checklist

Before production:

- [ ] Changed default password
- [ ] Generated secure encryption key
- [ ] Set up SMTP for emails
- [ ] Enabled HTTPS with reverse proxy
- [ ] Configured backups
- [ ] Set up monitoring
- [ ] Documented API keys

**Done!** You're ready to automate your lead generation pipeline.
