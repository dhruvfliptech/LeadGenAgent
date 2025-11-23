# LinkedIn Job Scraping Integration Guide

**Last Updated**: November 4, 2025
**Phase**: 2 - Multi-Source Lead Generation
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Service Comparison](#service-comparison)
3. [Recommended Approach](#recommended-approach)
4. [Piloterr Integration](#piloterr-integration)
5. [Alternative Services](#alternative-services)
6. [DIY Selenium Approach](#diy-selenium-approach)
7. [Configuration](#configuration)
8. [API Usage](#api-usage)
9. [Database Schema](#database-schema)
10. [Cost Analysis](#cost-analysis)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers integrating LinkedIn job scraping into your lead generation platform. LinkedIn actively blocks scrapers, so using a professional service is strongly recommended.

### Available Options

1. **Piloterr** (Recommended) - $49/month, 18,000 credits
2. **Bright Data** - Enterprise-focused, ~$0.05/profile
3. **ScraperAPI** - $299/month, 600,000 requests
4. **DIY Selenium** - Free but high ban risk (NOT RECOMMENDED)

---

## Service Comparison

### Decision Matrix

| Feature | Piloterr | Bright Data | ScraperAPI | DIY Selenium |
|---------|----------|-------------|------------|--------------|
| **Monthly Cost** | $49 (Premium) | $499+ (Growth) | $299 (600K req) | $0 + proxies |
| **LinkedIn Support** | ✅ Yes (Maintenance) | ✅ Yes | ✅ Yes | ⚠️ DIY |
| **Reliability** | ✅ High | ⚠️ Moderate | ✅ High | ❌ Low |
| **Ban Protection** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ❌ None |
| **Setup Time** | 10 minutes | 1-2 hours | 30 minutes | 3-5 hours |
| **Maintenance** | ✅ None | ⚠️ Some | ✅ None | ❌ High |
| **Legal Risk** | ✅ Low | ✅ Low | ✅ Low | ⚠️ Gray area |
| **Request Rate** | 5 req/sec | 10+ req/sec | Variable | 1 req/10s |
| **Free Trial** | ✅ 50 credits | ✅ 7 days | ✅ 5,000 req | N/A |
| **Support** | Email | Priority | 24/7 | None |
| **Best For** | Startups | Enterprise | Mid-size | Testing only |

### Pricing Breakdown

#### Piloterr (Recommended for Startups)
```
Premium Plan: $49/month
- 18,000 credits
- 1 credit = standard request
- 2 credits = JS rendering
- 5 requests/second
- Email support
- LinkedIn Job Search API (currently under maintenance)
```

**Estimated Capacity**:
- 18,000 jobs/month (standard requests)
- 600 jobs/day average
- Perfect for small-to-medium lead generation

#### Bright Data (Enterprise)
```
Growth Plan: $499/month
- Pay per record: $0.001-$0.05/profile
- LinkedIn specific: ~$0.05/profile
- 10+ req/sec
- Priority support
- Advanced targeting
```

**Estimated Capacity**:
- ~10,000 profiles at $0.05 each = $500
- Better for high-volume operations

#### ScraperAPI (Mid-Tier)
```
Professional Plan: $299/month
- 600,000 successful requests
- 150+ geolocations
- Structured data endpoints
- JavaScript rendering
- Premium proxies
```

**Estimated Capacity**:
- 600,000 jobs/month
- 20,000 jobs/day
- Best value for high volume

#### DIY Selenium (NOT RECOMMENDED)
```
Costs:
- Residential proxies: $50-200/month
- Selenium Grid hosting: $20-50/month
- Maintenance time: 5-10 hours/month
- CAPTCHA solving: $3/1000 (2Captcha)
- LinkedIn Premium (for better limits): $60/month

Risks:
- Account bans (permanent)
- IP bans (temporary to permanent)
- Legal issues (TOS violation)
- Constant maintenance (selectors change)
- Low success rate (50-70%)
```

---

## Recommended Approach

### For Most Users: Start with Piloterr

**Why Piloterr?**
1. **Lowest cost**: $49/month is accessible for startups
2. **Simple API**: RESTful endpoints, JSON responses
3. **Free trial**: 50 credits to test before paying
4. **No maintenance**: Service handles LinkedIn changes
5. **Legal protection**: Professional service, not TOS violation

**Migration Path**:
```
Month 1-3: Piloterr ($49/month, 18K credits)
  → Test integration, build workflows

Month 4-6: Evaluate usage
  → If < 18K/month: Stay on Piloterr
  → If > 18K/month: Upgrade to Piloterr Premium+ ($99, 40K)

Month 7+: Scale decision
  → If > 40K/month: Migrate to ScraperAPI ($299, 600K)
  → If > 600K/month: Migrate to Bright Data (enterprise)
```

---

## Piloterr Integration

### Step 1: Sign Up and Get API Key

1. Visit [piloterr.com](https://www.piloterr.com)
2. Create account (free, no credit card for trial)
3. Navigate to Dashboard → API Keys
4. Copy your API key

### Step 2: Test the API

**IMPORTANT**: As of Nov 2025, LinkedIn Job Search API is under maintenance. Use this test to check status:

```bash
curl -X GET "https://api.piloterr.com/api/v2/linkedin/job/search?keyword=software%20engineer&location=San%20Francisco" \
  -H "x-api-key: YOUR_API_KEY"
```

**Expected Response** (when service is operational):
```json
[
  {
    "id": "3456789012",
    "title": "Senior Software Engineer",
    "url": "https://www.linkedin.com/jobs/view/3456789012",
    "list_date": "2025-11-01",
    "company_name": "Tech Corp",
    "company_url": "https://www.linkedin.com/company/techcorp",
    "location": "San Francisco, CA",
    "description": "We are looking for...",
    "salary": "$150,000 - $200,000",
    "job_type": "full_time",
    "experience_level": "mid_senior"
  }
]
```

**Maintenance Status Response**:
```json
{
  "error": "Service temporarily unavailable",
  "message": "LinkedIn Job Search API is under maintenance"
}
```

### Step 3: Configure Your Application

Add to `/Users/greenmachine2.0/Craigslist/.env`:

```bash
# LinkedIn Integration Settings
LINKEDIN_ENABLED=true
LINKEDIN_SERVICE=piloterr  # Options: piloterr, scraperapi, brightdata, selenium
LINKEDIN_API_KEY=your_piloterr_api_key_here

# Optional: Advanced Settings
LINKEDIN_MAX_RESULTS_PER_SEARCH=100
LINKEDIN_RATE_LIMIT_PER_MINUTE=60  # Piloterr Premium: 5 req/sec = 300/min
LINKEDIN_TIMEOUT_SECONDS=30
LINKEDIN_RETRY_MAX_ATTEMPTS=3
```

### Step 4: Use the API Endpoints

#### Start LinkedIn Job Scraping

```bash
POST /api/v1/linkedin/scrape
Content-Type: application/json

{
  "keywords": ["software engineer", "python developer"],
  "location": "San Francisco, CA",
  "experience_level": "mid_senior",  # Optional: internship, entry_level, associate, mid_senior, director
  "job_type": "full_time",  # Optional: full_time, part_time, contract, temporary, internship, volunteer
  "max_results": 100
}
```

**Response**:
```json
{
  "job_id": "linkedin_job_abc123",
  "status": "started",
  "estimated_completion": "2025-11-04T10:05:00Z",
  "credits_used": 0,
  "message": "LinkedIn scraping job started"
}
```

#### Check Scraping Status

```bash
GET /api/v1/linkedin/status/linkedin_job_abc123
```

**Response**:
```json
{
  "job_id": "linkedin_job_abc123",
  "status": "completed",
  "jobs_found": 87,
  "jobs_saved": 85,
  "duplicates_skipped": 2,
  "credits_used": 87,
  "started_at": "2025-11-04T10:00:00Z",
  "completed_at": "2025-11-04T10:04:32Z",
  "error": null
}
```

---

## Alternative Services

### ScraperAPI Integration

If you outgrow Piloterr, migrate to ScraperAPI:

**Setup**:
```bash
# .env
LINKEDIN_SERVICE=scraperapi
LINKEDIN_API_KEY=your_scraperapi_key
```

**API Call** (handled automatically by `/backend/app/integrations/scraperapi_client.py`):
```python
import requests

params = {
    'api_key': 'YOUR_API_KEY',
    'url': 'https://www.linkedin.com/jobs/search/?keywords=software%20engineer',
    'render': 'true'  # Enable JavaScript rendering
}

response = requests.get('http://api.scraperapi.com/', params=params)
```

### Bright Data Integration

For enterprise scale:

**Setup**:
```bash
# .env
LINKEDIN_SERVICE=brightdata
LINKEDIN_API_KEY=your_brightdata_token
LINKEDIN_ZONE=linkedin_zone_name
```

**API Call**:
```python
import requests

headers = {
    'Authorization': f'Bearer {api_key}'
}

params = {
    'zone': 'linkedin_zone',
    'url': 'https://www.linkedin.com/jobs/...'
}

response = requests.post('https://api.brightdata.com/datasets/v3/trigger',
                        headers=headers, json=params)
```

---

## DIY Selenium Approach

### WARNING: Not Recommended for Production

**Risks**:
- LinkedIn bans accounts and IPs aggressively
- Requires constant maintenance (selectors change weekly)
- Legal gray area (violates LinkedIn TOS)
- Success rate: 50-70% (many CAPTCHAs, rate limits)
- Requires residential proxies ($50-200/month)

**Use Cases**:
- Testing only
- Very low volume (< 10 jobs/day)
- Backup when services are down

### If You Must Use Selenium

**Prerequisites**:
1. Residential proxy service (Bright Data, Oxylabs, Smartproxy)
2. 2Captcha account ($3/1000 solves)
3. LinkedIn account (risk of permanent ban)
4. Patience and debugging time

**Setup**:
```bash
# .env
LINKEDIN_SERVICE=selenium
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
LINKEDIN_PROXY_URL=http://username:password@proxy-server.com:1234
TWOCAPTCHA_API_KEY=your_2captcha_key
```

**File**: `/backend/app/scrapers/linkedin_scraper.py`

See implementation below for details.

---

## Configuration

### Environment Variables

```bash
# Feature Flag
LINKEDIN_ENABLED=true  # Master switch for LinkedIn integration

# Service Selection
LINKEDIN_SERVICE=piloterr  # Options: piloterr, scraperapi, brightdata, selenium

# API Keys (set based on service)
LINKEDIN_API_KEY=        # For piloterr, scraperapi, brightdata
LINKEDIN_EMAIL=          # For selenium only
LINKEDIN_PASSWORD=       # For selenium only
LINKEDIN_PROXY_URL=      # For selenium only

# Rate Limiting
LINKEDIN_MAX_RESULTS_PER_SEARCH=100
LINKEDIN_RATE_LIMIT_PER_MINUTE=60
LINKEDIN_TIMEOUT_SECONDS=30
LINKEDIN_RETRY_MAX_ATTEMPTS=3
LINKEDIN_BACKOFF_MULTIPLIER=2

# Storage
LINKEDIN_STORE_IN_LEADS_TABLE=true  # Store as source="linkedin"
LINKEDIN_DEDUPE_BY_URL=true  # Skip if URL already exists
```

---

## API Usage

### Endpoint: Start LinkedIn Scrape

**POST** `/api/v1/linkedin/scrape`

**Request Body**:
```json
{
  "keywords": ["software engineer", "python developer"],
  "location": "San Francisco, CA",
  "experience_level": "mid_senior",
  "job_type": "full_time",
  "max_results": 100,
  "extract_company_info": true,
  "save_to_database": true
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "linkedin_job_abc123",
  "status": "started",
  "keywords": ["software engineer", "python developer"],
  "location": "San Francisco, CA",
  "max_results": 100,
  "estimated_completion": "2025-11-04T10:05:00Z",
  "message": "LinkedIn scraping job started"
}
```

### Endpoint: Check Status

**GET** `/api/v1/linkedin/status/:job_id`

**Response** (200 OK):
```json
{
  "job_id": "linkedin_job_abc123",
  "status": "completed",
  "jobs_found": 87,
  "jobs_saved": 85,
  "duplicates_skipped": 2,
  "errors": 0,
  "credits_used": 87,
  "cost_usd": 0.087,
  "started_at": "2025-11-04T10:00:00Z",
  "completed_at": "2025-11-04T10:04:32Z",
  "service_used": "piloterr",
  "results_preview": [
    {
      "id": 12345,
      "title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "location": "San Francisco, CA",
      "url": "https://www.linkedin.com/jobs/view/3456789012"
    }
  ]
}
```

### Endpoint: Get LinkedIn Leads

**GET** `/api/v1/leads?source=linkedin`

Standard leads endpoint filtered by source.

---

## Database Schema

### Storing LinkedIn Jobs in Leads Table

LinkedIn jobs are stored in the existing `leads` table with `source="linkedin"`. We add LinkedIn-specific metadata to existing fields:

**Field Mapping**:
```
LinkedIn Field          → Leads Table Field
────────────────────────────────────────────
job_id                  → craigslist_id (repurposed as external_id)
job_title               → title
job_description         → description
job_url                 → url
company_name            → attributes.company_name (JSON)
company_url             → attributes.company_url (JSON)
posted_date             → posted_at
location                → neighborhood
salary                  → compensation
experience_level        → attributes.experience_level (JSON)
job_type                → employment_type (ARRAY)
is_remote               → is_remote (BOOLEAN)
applicant_count         → attributes.applicant_count (JSON)
```

**Example Lead Record** (LinkedIn job):
```json
{
  "id": 12345,
  "craigslist_id": "linkedin_3456789012",
  "source": "linkedin",
  "title": "Senior Software Engineer",
  "description": "We are looking for an experienced...",
  "url": "https://www.linkedin.com/jobs/view/3456789012",
  "posted_at": "2025-11-01T00:00:00Z",
  "compensation": "$150,000 - $200,000",
  "employment_type": ["full_time"],
  "is_remote": true,
  "neighborhood": "San Francisco, CA",
  "attributes": {
    "company_name": "Tech Corp",
    "company_url": "https://www.linkedin.com/company/techcorp",
    "experience_level": "mid_senior",
    "applicant_count": 127,
    "linkedin_job_id": "3456789012"
  },
  "status": "new"
}
```

### New Migration (if needed)

Add `source` field to leads table:

```sql
ALTER TABLE leads ADD COLUMN source VARCHAR(50) DEFAULT 'craigslist';
CREATE INDEX idx_leads_source ON leads(source);
```

---

## Cost Analysis

### Monthly Cost by Volume

| Jobs/Month | Recommended Service | Monthly Cost | Cost/Job |
|------------|-------------------|--------------|----------|
| < 1,000 | Piloterr Free Trial | $0 | $0.00 |
| 1K - 18K | Piloterr Premium | $49 | $0.0027 |
| 18K - 40K | Piloterr Premium+ | $99 | $0.0025 |
| 40K - 100K | ScraperAPI | $299 | $0.0030 |
| 100K - 600K | ScraperAPI | $299 | $0.0005 |
| 600K+ | Bright Data | $499+ | $0.001-0.05 |

### Annual Cost Projection

**Scenario 1**: Small startup (5,000 jobs/month)
- Service: Piloterr Premium
- Cost: $49/month = $588/year
- Additional: Email finding, AI analysis ~$100/month
- **Total**: ~$1,788/year

**Scenario 2**: Growing company (50,000 jobs/month)
- Service: ScraperAPI
- Cost: $299/month = $3,588/year
- Additional: Email finding, AI analysis ~$200/month
- **Total**: ~$6,000/year

**Scenario 3**: Enterprise (500,000 jobs/month)
- Service: Bright Data
- Cost: $999/month = $11,988/year
- Additional: Email finding, AI analysis ~$500/month
- **Total**: ~$18,000/year

---

## Troubleshooting

### Piloterr Issues

**Problem**: API returns "Service under maintenance"
```
Solution: LinkedIn Job Search endpoint is temporarily unavailable.
- Check Piloterr status page
- Use alternative endpoint (LinkedIn Profile Scraper)
- Fall back to ScraperAPI or wait for service restoration
```

**Problem**: 401 Unauthorized
```
Solution: Invalid API key
- Verify API key in dashboard
- Check for extra spaces/newlines
- Regenerate API key if needed
```

**Problem**: 429 Too Many Requests
```
Solution: Rate limit exceeded
- Piloterr Premium: 5 req/sec (300/min)
- Add delays between requests
- Upgrade to higher tier for more req/sec
```

### Selenium Issues

**Problem**: LinkedIn account banned
```
Solution: Use professional service instead
- Selenium violates LinkedIn TOS
- Bans are often permanent
- No way to recover account
- Use Piloterr/ScraperAPI/Bright Data
```

**Problem**: CAPTCHA on every request
```
Solution: Improve bot detection evasion
- Use residential proxies (not datacenter)
- Add random delays (5-15 seconds)
- Rotate user agents
- Use 2Captcha to solve CAPTCHAs
- Consider switching to professional service
```

**Problem**: Selectors not working
```
Solution: LinkedIn changes HTML frequently
- Update selectors weekly
- Use multiple fallback selectors
- Monitor LinkedIn's DOM changes
- This is why professional services are recommended
```

### General Issues

**Problem**: No email addresses found
```
Solution: LinkedIn doesn't show emails in job posts
- Use company URL to scrape company website
- Integrate Hunter.io or RocketReach
- Check "Apply" button for email reveals
- Visit company LinkedIn page for contact info
```

**Problem**: Duplicate jobs in database
```
Solution: Enable deduplication
- Set LINKEDIN_DEDUPE_BY_URL=true
- Check by linkedin_job_id in attributes
- Use unique constraint on craigslist_id field
```

---

## Support

### Piloterr Support
- Email: hello@piloterr.com
- Documentation: https://www.piloterr.com/docs
- Status Page: (check website for updates)

### ScraperAPI Support
- 24/7 Chat support
- Email: support@scraperapi.com
- Documentation: https://docs.scraperapi.com

### Bright Data Support
- Dedicated account manager (Enterprise+)
- Email: support@brightdata.com
- Knowledge Base: https://docs.brightdata.com

---

## Next Steps

1. **Week 1**: Sign up for Piloterr free trial (50 credits)
2. **Week 2**: Test integration with sample searches
3. **Week 3**: Monitor credit usage and adjust quotas
4. **Month 2**: Evaluate upgrade to Premium ($49/month)
5. **Quarter 2**: Scale to ScraperAPI if needed

**Questions?** See the main IMPLEMENTATION_ROADMAP.md or contact your development team.
