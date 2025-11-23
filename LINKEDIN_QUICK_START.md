# LinkedIn Integration - Quick Start Guide

**5-Minute Setup** for LinkedIn job scraping using Piloterr.

---

## Step 1: Sign Up for Piloterr (2 minutes)

1. Visit: https://www.piloterr.com
2. Create account (no credit card needed)
3. Get **50 free credits**
4. Copy your API key from dashboard

---

## Step 2: Configure Environment (1 minute)

```bash
cd /Users/greenmachine2.0/Craigslist

# Edit .env file
nano .env

# Add these 3 lines:
LINKEDIN_ENABLED=true
LINKEDIN_SERVICE=piloterr
LINKEDIN_API_KEY=your_piloterr_key_here
```

Save and exit (Ctrl+X, Y, Enter)

---

## Step 3: Run Migration (1 minute)

```bash
cd backend
alembic upgrade head
cd ..
```

---

## Step 4: Start Backend (30 seconds)

```bash
./start_backend.sh
```

Wait for: "✓ All health checks passed"

---

## Step 5: Test It! (30 seconds)

```bash
# Scrape 5 LinkedIn jobs
curl -X POST "http://localhost:8000/api/v1/linkedin/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["software engineer"],
    "location": "San Francisco, CA",
    "max_results": 5,
    "save_to_database": true,
    "location_id": 1
  }'

# Save the job_id from response, then check status:
curl "http://localhost:8000/api/v1/linkedin/status/YOUR_JOB_ID"
```

---

## You're Done!

**API Docs**: http://localhost:8000/docs
**Full Guide**: `/Users/greenmachine2.0/Craigslist/backend/LINKEDIN_INTEGRATION_GUIDE.md`

---

## Pricing

- **Free Trial**: 50 credits (50 jobs)
- **Premium**: $49/month (18,000 jobs)
- **Premium+**: $99/month (40,000 jobs)

**Recommendation**: Start with free trial, upgrade when needed.

---

## Troubleshooting

**Problem**: "LinkedIn integration is not enabled"
```bash
# Make sure .env has:
LINKEDIN_ENABLED=true
```

**Problem**: "LINKEDIN_API_KEY not configured"
```bash
# Add your Piloterr key to .env:
LINKEDIN_API_KEY=your_actual_key_here
```

**Problem**: "location_id is required"
```bash
# Create a location first via API or use existing location_id
# Check available locations:
curl "http://localhost:8000/api/v1/locations"
```

**Problem**: "Service under maintenance"
```bash
# LinkedIn Job Search API is temporarily down
# Try again later or use ScraperAPI:
LINKEDIN_SERVICE=scraperapi
LINKEDIN_API_KEY=your_scraperapi_key
```

---

## Next Steps

1. **Week 1**: Test with free credits (50 jobs)
2. **Week 2**: Decide on paid plan based on volume
3. **Month 1**: Upgrade to Premium ($49/month) if needed
4. **Quarter 1**: Scale to ScraperAPI if >40K jobs/month

**Questions?** See `LINKEDIN_INTEGRATION_GUIDE.md` for detailed documentation.
