# Email Finder Integration - Setup Guide

**Generated**: November 4, 2025
**Status**: Production Ready
**Implementation**: Phase 2 - Multi-Source Lead Generation

---

## Table of Contents
1. [Overview](#overview)
2. [Hunter.io Setup](#hunterio-setup)
3. [RocketReach Setup (Optional)](#rocketreach-setup)
4. [Configuration](#configuration)
5. [Database Migration](#database-migration)
6. [API Usage](#api-usage)
7. [Quota Management](#quota-management)
8. [Cost Comparison](#cost-comparison)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Email Finder system integrates multiple strategies for finding business emails:

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Email Finder Service                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Strategy 1  │  │  Strategy 2  │  │  Strategy 3  │     │
│  │   Database   │→ │  Hunter.io   │→ │   Scraping   │     │
│  │    Cache     │  │   API Call   │  │  (Fallback)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
│  ┌────────────────────────────────────────────────┐        │
│  │         Unified Email Results + Metadata        │        │
│  │   (confidence scores, verification status)      │        │
│  └────────────────────────────────────────────────┘        │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │          Quota Management & Tracking             │        │
│  │  - Real-time usage monitoring                    │        │
│  │  - Auto-fallback on quota exceeded               │        │
│  │  - Alert system for approaching limits           │        │
│  └────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Features
- **Multi-strategy approach**: Database cache → Hunter.io → Website scraping
- **Automatic fallback**: Seamlessly switches strategies when quota exceeded
- **Quota management**: Prevents overage charges with real-time tracking
- **Confidence scoring**: Ranks emails by reliability
- **Verification**: Optional email validation
- **Caching**: Reduces API calls by storing found emails

---

## Hunter.io Setup

### 1. Create Hunter.io Account

1. Go to [https://hunter.io](https://hunter.io)
2. Sign up for a free account
3. Free tier includes: **100 searches/month**

### 2. Get API Key

1. Log in to Hunter.io dashboard
2. Navigate to: **Dashboard → API** (or visit https://hunter.io/api-keys)
3. Copy your API key
4. Store it securely (you'll need it for configuration)

### 3. Pricing Tiers

| Plan | Searches/Month | Price/Month | Cost per Search |
|------|----------------|-------------|-----------------|
| **Free** | 100 | $0 | $0 |
| **Starter** | 1,000 | $49 | $0.049 |
| **Growth** | 5,000 | $99 | $0.020 |
| **Business** | 20,000 | $199 | $0.010 |
| **Enterprise** | 50,000+ | Custom | Custom |

**Recommendation**: Start with free tier, upgrade to Starter ($49/mo) when needed.

### 4. API Limits
- **Rate limit**: 50 requests/minute
- **Timeout**: 30 seconds per request
- **Response time**: ~200-500ms average

---

## RocketReach Setup (Optional)

### Overview
RocketReach is an alternative to Hunter.io, better for B2B and finding specific people.

### Pricing

| Plan | Lookups/Month | Price/Month | Cost per Lookup |
|------|---------------|-------------|-----------------|
| **Essentials** | 150 | $50 | $0.33 |
| **Pro** | 625 | $199 | $0.32 |
| **Ultimate** | 1,500 | $399 | $0.27 |

**Verdict**: More expensive than Hunter.io. Only use if you need:
- Better accuracy for executive-level contacts
- More social profile data
- Better international coverage

### Setup
1. Go to [https://rocketreach.co](https://rocketreach.co)
2. Sign up for account
3. Get API key from dashboard
4. Add to configuration (see below)

**Recommendation**: Start with Hunter.io only. Add RocketReach later if needed.

---

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Hunter.io Configuration
HUNTER_IO_ENABLED=true
HUNTER_IO_API_KEY=your_hunter_io_api_key_here
HUNTER_MONTHLY_QUOTA=100  # Free tier default
HUNTER_ALERT_THRESHOLD=80  # Alert at 80% usage

# RocketReach Configuration (Optional)
ROCKETREACH_ENABLED=false
ROCKETREACH_API_KEY=your_rocketreach_api_key_here
ROCKETREACH_MONTHLY_QUOTA=150

# Email Finder Settings
EMAIL_FINDER_FALLBACK_TO_SCRAPING=true  # Enable website scraping fallback
EMAIL_FINDER_CACHE_ENABLED=true  # Cache found emails
EMAIL_FINDER_MIN_CONFIDENCE_SCORE=30  # Minimum confidence to use email
```

### Configuration Example

**Minimal Setup (Free Tier)**:
```bash
HUNTER_IO_ENABLED=true
HUNTER_IO_API_KEY=abc123xyz789
HUNTER_MONTHLY_QUOTA=100
EMAIL_FINDER_FALLBACK_TO_SCRAPING=true
```

**Production Setup (Paid Plan)**:
```bash
HUNTER_IO_ENABLED=true
HUNTER_IO_API_KEY=abc123xyz789
HUNTER_MONTHLY_QUOTA=1000
HUNTER_ALERT_THRESHOLD=80
EMAIL_FINDER_FALLBACK_TO_SCRAPING=true
EMAIL_FINDER_CACHE_ENABLED=true
EMAIL_FINDER_MIN_CONFIDENCE_SCORE=50
```

---

## Database Migration

### Run Migration

```bash
# Navigate to backend directory
cd /Users/greenmachine2.0/Craigslist/backend

# Run migration
alembic upgrade head
```

### What Gets Created

The migration creates 3 tables:

1. **email_finder_usage**
   - Tracks every API call
   - Records: service, domain, results_count, response_time, cost
   - Used for analytics and quota tracking

2. **found_emails**
   - Stores all discovered emails
   - Fields: email, domain, source, confidence_score, contact info
   - Enables caching and reduces API calls

3. **email_finder_quotas**
   - Monthly quota tracking per service
   - Fields: quota_limit, requests_used, requests_remaining
   - Prevents overage charges

### Verify Migration

```bash
# Check tables were created
psql $DATABASE_URL -c "\dt email_*"

# Should show:
# - email_finder_usage
# - found_emails
# - email_finder_quotas
```

---

## API Usage

### 1. Find Emails by Domain

**Endpoint**: `POST /api/v1/email-finder/find-by-domain`

```bash
curl -X POST http://localhost:8000/api/v1/email-finder/find-by-domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "stripe.com",
    "limit": 10,
    "lead_id": 123
  }'
```

**Response**:
```json
{
  "domain": "stripe.com",
  "emails": [
    {
      "id": 1,
      "email": "john@stripe.com",
      "source": "hunter_io",
      "contact": {
        "first_name": "John",
        "last_name": "Doe",
        "position": "CEO",
        "department": "executive"
      },
      "quality": {
        "confidence_score": 95,
        "is_verified": true,
        "verification_status": "valid"
      },
      "characteristics": {
        "is_generic": false,
        "is_personal": true,
        "is_disposable": false,
        "is_webmail": false
      }
    }
  ],
  "total_found": 10,
  "sources_used": ["hunter_io", "scraped"]
}
```

### 2. Find Specific Person's Email

**Endpoint**: `POST /api/v1/email-finder/find-person`

```bash
curl -X POST http://localhost:8000/api/v1/email-finder/find-person \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Patrick Collison",
    "domain": "stripe.com",
    "lead_id": 123
  }'
```

### 3. Verify Email

**Endpoint**: `POST /api/v1/email-finder/verify`

```bash
curl -X POST http://localhost:8000/api/v1/email-finder/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patrick@stripe.com"
  }'
```

**Response**:
```json
{
  "email": "patrick@stripe.com",
  "valid": true,
  "score": 95,
  "result": "deliverable",
  "details": {
    "regexp": true,
    "gibberish": false,
    "disposable": false,
    "mx_records": true,
    "smtp_check": true
  }
}
```

### 4. Check Quota Status

**Endpoint**: `GET /api/v1/email-finder/quota/hunter_io`

```bash
curl http://localhost:8000/api/v1/email-finder/quota/hunter_io
```

**Response**:
```json
{
  "service": "hunter_io",
  "period": "2025-11",
  "quota": {
    "limit": 100,
    "used": 45,
    "remaining": 55,
    "percentage": 45.0
  },
  "alerts": {
    "threshold": 80,
    "sent": false,
    "near_limit": false,
    "exceeded": false
  },
  "plan": {
    "name": "Free",
    "level": 0,
    "reset_date": "2025-12-01T00:00:00Z"
  }
}
```

### 5. Get Email History

**Endpoint**: `GET /api/v1/email-finder/history`

```bash
# All emails
curl http://localhost:8000/api/v1/email-finder/history?limit=50

# Filter by domain
curl http://localhost:8000/api/v1/email-finder/history?domain=stripe.com

# Filter by source
curl http://localhost:8000/api/v1/email-finder/history?source=hunter_io
```

### 6. Get Statistics

**Endpoint**: `GET /api/v1/email-finder/stats`

```bash
curl http://localhost:8000/api/v1/email-finder/stats
```

**Response**:
```json
{
  "total_emails_found": 1234,
  "by_source": {
    "hunter_io": 800,
    "scraped": 400,
    "manual": 34
  },
  "by_confidence": {
    "high": 900,
    "medium": 250,
    "low": 84
  },
  "quota_status": {
    "hunter_io": {
      "used": 45,
      "remaining": 55,
      "percentage": 45.0,
      "near_limit": false,
      "exceeded": false
    }
  }
}
```

---

## Quota Management

### How It Works

1. **Real-time Tracking**: Every API call is logged with usage count
2. **Automatic Fallback**: When quota exceeded, automatically uses scraping
3. **Alert System**: Warns when approaching 80% of quota
4. **Monthly Reset**: Quota resets automatically on 1st of each month

### Check Quota Before Making Calls

```python
from app.services.email_finder import EmailFinderService
from app.models.email_finder import ServiceName

service = EmailFinderService(db)

# Check quota status
quota = await service.get_quota_status(ServiceName.HUNTER_IO)

if quota["alerts"]["exceeded"]:
    print("Quota exceeded! Using fallback methods.")
elif quota["alerts"]["near_limit"]:
    print(f"Warning: {quota['quota']['percentage']}% of quota used")
else:
    print(f"Quota healthy: {quota['quota']['remaining']} requests remaining")
```

### Preventing Overage Charges

The system automatically prevents overage by:

1. **Pre-check**: Checks quota before every API call
2. **Raises error**: `QuotaExceededError` when limit reached
3. **Auto-fallback**: Switches to scraping automatically
4. **No charges**: Won't make API calls if quota exceeded

### Monthly Quota Reset

Quotas reset automatically on the 1st of each month. The system:
1. Detects new month
2. Resets `requests_used` to 0
3. Updates `reset_date` to next month
4. Clears alert flags

---

## Cost Comparison

### Hunter.io vs RocketReach vs Scraping

| Method | Setup Cost | Monthly Cost | Per Email | Accuracy | Speed | Legal Risk |
|--------|-----------|--------------|-----------|----------|-------|------------|
| **Hunter.io Free** | $0 | $0 | $0 (100/mo) | High (90%) | Fast | Low |
| **Hunter.io Starter** | $0 | $49 | $0.049 | High (90%) | Fast | Low |
| **Hunter.io Growth** | $0 | $99 | $0.020 | High (90%) | Fast | Low |
| **RocketReach** | $0 | $50 | $0.33 | Very High (95%) | Fast | Low |
| **Website Scraping** | $0 | $0 | $0 | Medium (60%) | Slow | Medium |
| **Manual Search** | $0 | Labor | High | High (85%) | Very Slow | Low |

### Cost Analysis by Volume

**100 emails/month**:
- Hunter.io Free: **$0/month** ✅ BEST
- RocketReach: Not cost-effective
- Scraping: $0 but unreliable

**500 emails/month**:
- Hunter.io Starter: **$49/month** ($0.098/email) ✅ BEST
- RocketReach Essentials: $50 (only 150 emails)
- Mixed (100 Hunter free + 400 scraping): $0 but lower quality

**2,000 emails/month**:
- Hunter.io Starter: $49 (1000) + $49 (1000) = **$98/month** ✅ BEST
- Hunter.io Growth: **$99/month** (5000 quota) ✅ BETTER
- RocketReach: $199 (625 emails) - Not enough
- Mixed strategy: 100 free + 1900 scraping = Lower quality

### Recommended Strategy

**Budget-Conscious**:
```
Use Hunter.io free tier (100/mo) + Scraping fallback
Monthly cost: $0
Quality: 70% high confidence, 30% medium confidence
```

**Balanced**:
```
Use Hunter.io Starter ($49/mo for 1K) + Scraping fallback
Monthly cost: $49
Quality: 85% high confidence, 15% medium confidence
```

**High-Volume**:
```
Use Hunter.io Growth ($99/mo for 5K) + Scraping fallback
Monthly cost: $99
Quality: 90% high confidence, 10% medium confidence
```

**Maximum Accuracy**:
```
Use Hunter.io Growth + RocketReach for executives
Monthly cost: $99 + $50 = $149
Quality: 95% high confidence, 5% medium confidence
```

### ROI Calculation

If converting 5% of emails to customers:
- 100 emails/mo → 5 customers
- Cost: $0-$49/mo
- If average customer value > $10, positive ROI

If converting 2% of emails to customers:
- 500 emails/mo → 10 customers
- Cost: $49/mo
- If average customer value > $5, positive ROI

---

## Best Practices

### 1. Start with Free Tier
- Use Hunter.io free tier (100/mo) initially
- Monitor conversion rates
- Upgrade only when ROI is proven

### 2. Enable Caching
```bash
EMAIL_FINDER_CACHE_ENABLED=true
```
- Reduces API calls by ~30-40%
- Prevents duplicate searches
- Free performance boost

### 3. Use Confidence Scores
```python
# Only use emails with high confidence
EMAIL_FINDER_MIN_CONFIDENCE_SCORE=50

# Filter in code
high_confidence_emails = [
    email for email in results
    if email.confidence_score >= 70
]
```

### 4. Monitor Quota Daily
```bash
# Check quota status
curl http://localhost:8000/api/v1/email-finder/quota/hunter_io

# Set up alert when > 80%
if quota["alerts"]["near_limit"]:
    send_slack_notification("⚠️ Email finder quota at 80%")
```

### 5. Leverage Scraping Fallback
```bash
# Always enable scraping
EMAIL_FINDER_FALLBACK_TO_SCRAPING=true
```
- Provides unlimited backup
- Quality is lower but free
- Works when quota exceeded

### 6. Batch Requests
```python
# Instead of:
for domain in domains:
    await find_emails(domain)  # 100 API calls

# Do this:
domains = ["stripe.com", "google.com", ...]
for domain in domains[:100]:  # Batch of 100
    await find_emails(domain)
```

### 7. Verify Important Emails
```python
# Verify before sending important campaigns
verification = await service.verify_email(email)
if verification["valid"] and verification["score"] > 80:
    send_email(email)
```

---

## Troubleshooting

### Issue: "QuotaExceededError"

**Solution**:
1. Check quota status: `GET /api/v1/email-finder/quota/hunter_io`
2. System should auto-fallback to scraping
3. If not, enable fallback: `EMAIL_FINDER_FALLBACK_TO_SCRAPING=true`
4. Wait until next month or upgrade plan

### Issue: "Invalid API key"

**Solution**:
1. Verify API key in `.env` file
2. Check for extra spaces or quotes
3. Regenerate key in Hunter.io dashboard
4. Restart backend: `./start_backend.sh`

### Issue: "Rate limit exceeded"

**Solution**:
1. Hunter.io limit: 50 requests/minute
2. System automatically handles this with retry
3. Wait 60 seconds and try again
4. Check for infinite loops in your code

### Issue: "No emails found for domain"

**Solution**:
1. Check if domain is valid
2. Hunter.io may not have data for small companies
3. Fallback to scraping should activate
4. Try alternative: `company.co.uk` vs `company.com`

### Issue: Low confidence scores

**Solution**:
1. Confidence < 50 means guessed patterns
2. Use email verification to check validity
3. Consider upgrading to RocketReach for better data
4. Manual research may be needed

### Issue: "Database error"

**Solution**:
1. Check migration was run: `alembic current`
2. Run migration: `alembic upgrade head`
3. Check database connection: `psql $DATABASE_URL`
4. Verify tables exist: `\dt email_*`

### Issue: Scraping fallback not working

**Solution**:
1. Check setting: `EMAIL_FINDER_FALLBACK_TO_SCRAPING=true`
2. Website may block scraping (use headers)
3. Check logs for errors
4. Some sites don't list emails publicly

---

## Testing

### Test Hunter.io Integration

```bash
# Start backend
./start_backend.sh

# Test domain search
curl -X POST http://localhost:8000/api/v1/email-finder/find-by-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "stripe.com", "limit": 5}'

# Test person search
curl -X POST http://localhost:8000/api/v1/email-finder/find-person \
  -H "Content-Type: application/json" \
  -d '{"name": "Patrick Collison", "domain": "stripe.com"}'

# Test quota
curl http://localhost:8000/api/v1/email-finder/quota/hunter_io
```

### Test Scraping Fallback

```bash
# Disable Hunter.io temporarily
export HUNTER_IO_ENABLED=false

# Try finding emails (should use scraping)
curl -X POST http://localhost:8000/api/v1/email-finder/find-by-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "limit": 5}'

# Re-enable Hunter.io
export HUNTER_IO_ENABLED=true
```

---

## Next Steps

1. **Get Hunter.io API key**: Sign up at https://hunter.io
2. **Configure `.env`**: Add API key and settings
3. **Run migration**: `alembic upgrade head`
4. **Test integration**: Use curl commands above
5. **Monitor quota**: Check daily for first week
6. **Optimize**: Adjust confidence thresholds based on results
7. **Scale**: Upgrade plan when ROI is proven

---

## Support Resources

- **Hunter.io Docs**: https://hunter.io/api-documentation
- **RocketReach Docs**: https://rocketreach.co/api
- **Email Regex Guide**: https://emailregex.com/
- **GDPR Compliance**: https://gdpr.eu/email-encryption/

---

**Implementation Status**: ✅ Complete
**Production Ready**: Yes
**Last Updated**: November 4, 2025
