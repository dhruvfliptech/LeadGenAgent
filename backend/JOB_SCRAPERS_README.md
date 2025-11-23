# Job Board Scrapers - Implementation Guide

**Last Updated**: November 4, 2025
**Phase**: Phase 2 - Multi-Source Lead Generation
**Status**: Production Ready (with caveats)

---

## Overview

This implementation provides robust scrapers for three major job boards:

1. **Indeed** - Largest job board globally
2. **Monster** - Established job board with diverse listings
3. **ZipRecruiter** - Job aggregator with aggressive bot detection

### Features

- Unified API endpoint for all job boards
- Anti-detection measures (user agent rotation, random delays, headless browser stealth)
- Company information discovery (website + email extraction)
- Standardized data format across all sources
- Rate limiting and CAPTCHA detection
- Comprehensive error handling
- Database integration for lead storage

---

## Architecture

```
app/scrapers/
├── base_job_scraper.py      # Base class with shared functionality
├── indeed_scraper.py         # Indeed-specific implementation
├── monster_scraper.py        # Monster-specific implementation
└── ziprecruiter_scraper.py  # ZipRecruiter-specific implementation

app/api/endpoints/
└── job_boards.py            # Unified API endpoint

app/core/
└── config.py                # Configuration settings (updated)
```

### Class Hierarchy

```
BaseJobScraper (ABC)
    ├── IndeedScraper
    ├── MonsterScraper
    └── ZipRecruiterScraper
```

---

## Installation & Setup

### 1. Install Dependencies

The scrapers use Playwright for browser automation:

```bash
cd backend
pip install playwright
playwright install chromium
```

### 2. Configure Settings

Add to your `.env` file:

```bash
# Enable/disable specific job boards
INDEED_ENABLED=true
MONSTER_ENABLED=true
ZIPRECRUITER_ENABLED=true

# Scraping configuration
JOB_SCRAPE_DELAY_SECONDS=3
JOB_MAX_RESULTS_PER_SOURCE=100
JOB_ENABLE_COMPANY_LOOKUP=false  # Set to true for email/website discovery

# Job board specific delays (in seconds)
INDEED_MIN_DELAY=2.0
INDEED_MAX_DELAY=5.0
MONSTER_MIN_DELAY=2.0
MONSTER_MAX_DELAY=5.0
ZIPRECRUITER_MIN_DELAY=3.0  # Longer due to stricter bot detection
ZIPRECRUITER_MAX_DELAY=7.0

# Optional: Proxy settings (recommended for ZipRecruiter)
JOB_SCRAPER_PROXY_ENABLED=false
JOB_SCRAPER_PROXY_URL=  # Format: http://user:pass@host:port

# Bot detection settings
JOB_SCRAPER_WARN_ON_CAPTCHA=true
JOB_SCRAPER_STOP_ON_RATE_LIMIT=true
```

### 3. Register API Endpoint

Add to `backend/app/main.py`:

```python
from app.api.endpoints import job_boards

app.include_router(
    job_boards.router,
    prefix="/api/v1/job-boards",
    tags=["job-boards"]
)
```

---

## API Usage

### Endpoint: `POST /api/v1/job-boards/scrape`

Scrape jobs from one or more job boards.

**Request Body:**

```json
{
  "source": "indeed",  // "indeed", "monster", "ziprecruiter", or "all"
  "query": "python developer",
  "location": "San Francisco, CA",
  "max_results": 100,
  "enable_company_lookup": false,
  "save_to_database": true
}
```

**Response:**

```json
{
  "success": true,
  "message": "Successfully scraped 85 jobs from 1 source(s)",
  "total_jobs_scraped": 85,
  "jobs_by_source": {
    "indeed": 85
  },
  "stats": [
    {
      "source": "indeed",
      "jobs_scraped": 85,
      "errors_encountered": 0,
      "captchas_detected": 0,
      "rate_limits_hit": 0,
      "duration_seconds": 42.5
    }
  ],
  "jobs": [...],  // Array of job objects (if <= 100 total)
  "warnings": []
}
```

### Endpoint: `GET /api/v1/job-boards/sources`

Get list of enabled job board sources.

**Response:**

```json
{
  "sources": [
    {
      "name": "indeed",
      "enabled": true,
      "display_name": "Indeed",
      "description": "One of the largest job boards worldwide"
    },
    // ... more sources
  ],
  "settings": {
    "default_delay_seconds": 3,
    "max_results_per_source": 100,
    "company_lookup_enabled": false
  }
}
```

### Endpoint: `GET /api/v1/job-boards/stats/{source}`

Get statistics for a specific job board source.

**Example:** `GET /api/v1/job-boards/stats/indeed`

**Response:**

```json
{
  "source": "indeed",
  "total_leads": 1250,
  "with_email": 320,
  "with_website": 780,
  "remote_jobs": 450,
  "contacted": 125,
  "status_breakdown": {
    "new": 890,
    "qualified": 210,
    "contacted": 125,
    "converted": 25
  },
  "email_discovery_rate": 25.6,
  "website_discovery_rate": 62.4
}
```

---

## Python SDK Usage

### Example 1: Scrape Indeed

```python
from playwright.async_api import async_playwright
from app.scrapers.indeed_scraper import IndeedScraper

async def scrape_indeed_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = IndeedScraper(
            browser=browser,
            context=context,
            enable_company_lookup=False
        )

        try:
            jobs = await scraper.search_jobs(
                query="data scientist",
                location="Boston, MA",
                max_results=50
            )

            print(f"Found {len(jobs)} jobs")

            for job in jobs:
                print(f"- {job['title']} at {job['company_name']}")
                print(f"  {job['location']} | {job.get('compensation', 'N/A')}")

        finally:
            await browser.close()

# Run
import asyncio
asyncio.run(scrape_indeed_jobs())
```

### Example 2: Scrape All Sources

```python
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.monster_scraper import MonsterScraper
from app.scrapers.ziprecruiter_scraper import ZipRecruiterScraper

async def scrape_all_job_boards():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scrapers = {
            'indeed': IndeedScraper(browser, context),
            'monster': MonsterScraper(browser, context),
            'ziprecruiter': ZipRecruiterScraper(browser, context)
        }

        all_jobs = []

        for name, scraper in scrapers.items():
            try:
                jobs = await scraper.search_jobs(
                    query="product manager",
                    location="Seattle, WA",
                    max_results=30
                )
                all_jobs.extend(jobs)
                print(f"{name}: {len(jobs)} jobs")
            except Exception as e:
                print(f"{name}: Error - {str(e)}")

        await browser.close()
        return all_jobs
```

### Example 3: With Company Lookup

```python
scraper = IndeedScraper(
    browser=browser,
    context=context,
    enable_company_lookup=True  # Enables email/website discovery
)

jobs = await scraper.search_jobs(
    query="sales representative",
    location="Austin, TX",
    max_results=20
)

# Check which jobs have contact info
for job in jobs:
    if job.get('company_email'):
        print(f"✓ {job['company_name']}: {job['company_email']}")
```

---

## Job Data Structure

Each job is returned with the following standardized structure:

```python
{
    # Core fields
    "title": "Senior Python Developer",
    "url": "https://www.indeed.com/viewjob?jk=abc123",
    "description": "We are looking for...",

    # Source tracking
    "source": "indeed",  # indeed, monster, ziprecruiter
    "external_id": "abc123",  # Job board's internal ID

    # Company info
    "company_name": "Tech Corp Inc.",
    "company_website": "https://techcorp.com",  # If company_lookup enabled
    "company_email": "jobs@techcorp.com",  # If found

    # Job details
    "compensation": "$120,000 - $150,000 per year",
    "employment_type": ["full-time"],
    "location": "San Francisco, CA",
    "is_remote": False,

    # Timestamps
    "posted_date": "2025-11-01T10:00:00",
    "scraped_at": "2025-11-04T15:30:00",

    # Additional metadata
    "metadata": {
        "raw_salary": "$120k-150k",
        "job_type": "permanent",
        "experience_level": "senior",
        ...
    }
}
```

---

## Anti-Detection Best Practices

### 1. Respect Rate Limits

**Good:**
```python
# Scrape with appropriate delays
jobs = await scraper.search_jobs(
    query="engineer",
    location="NYC",
    max_results=50  # Reasonable limit
)
await asyncio.sleep(60)  # Wait between different searches
```

**Bad:**
```python
# Don't do this
for i in range(100):
    jobs = await scraper.search_jobs(...)  # Instant ban
```

### 2. Use Random User Agents

The base scraper automatically rotates user agents, but you can customize:

```python
scraper._user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
```

### 3. Add Proxies (Recommended for Production)

```python
# In config
JOB_SCRAPER_PROXY_ENABLED=true
JOB_SCRAPER_PROXY_URL=http://user:pass@proxy-server.com:8080

# Or programmatically
context = await browser.new_context(
    proxy={
        "server": "http://proxy-server.com:8080",
        "username": "user",
        "password": "pass"
    }
)
```

### 4. Handle Blocking Gracefully

```python
try:
    jobs = await scraper.search_jobs(...)
except CaptchaDetectedException:
    # Pause scraping, notify admin
    logger.error("CAPTCHA detected - pausing for 1 hour")
    await asyncio.sleep(3600)
except RateLimitException:
    # Back off and retry later
    logger.error("Rate limited - waiting 30 minutes")
    await asyncio.sleep(1800)
```

### 5. Monitor Statistics

```python
stats = scraper.get_stats()
if stats['captchas_detected'] > 0:
    # Consider using 2Captcha service
    print("⚠️  CAPTCHAs detected - consider adding solver")

if stats['rate_limits_hit'] > 0:
    # Reduce frequency
    print("⚠️  Rate limits hit - slow down scraping")
```

---

## Job Board Specific Notes

### Indeed

**Difficulty:** Medium
**Success Rate:** ~85% without proxies
**Best Practices:**
- Use delays of 2-5 seconds between pages
- Avoid scraping more than 100 jobs per session
- Indeed's structure changes frequently - monitor for selector updates

**Known Issues:**
- Sometimes requires JavaScript to render job cards
- May show "sign up" prompts after 20-30 jobs
- Rate limiting kicks in after ~100 requests/hour

### Monster

**Difficulty:** Medium
**Success Rate:** ~75% without proxies
**Best Practices:**
- Dismiss sign-up modals immediately (handled automatically)
- Use delays of 2-5 seconds
- Monster has fewer jobs than Indeed - expect lower results

**Known Issues:**
- Aggressive "create account" pop-ups
- Job cards sometimes load dynamically
- Some jobs redirect to external career sites

### ZipRecruiter

**Difficulty:** HARD
**Success Rate:** ~40% without proxies, ~80% with residential proxies
**Best Practices:**
- **USE PROXIES** - ZipRecruiter has the strictest bot detection
- Use delays of 3-7 seconds minimum
- Limit to 20-30 jobs per session
- Expect CAPTCHAs frequently

**Known Issues:**
- Very aggressive Cloudflare protection
- Often requires residential IPs (datacenter IPs blocked)
- May show CAPTCHAs even with perfect behavior
- Job descriptions sometimes behind login wall

**Recommendation:** For production use with ZipRecruiter, invest in:
- Residential proxy service (e.g., Bright Data, Oxylabs)
- 2Captcha integration for CAPTCHA solving
- Lower scraping frequency (daily instead of hourly)

---

## Proxy Recommendations

### Residential Proxies (Recommended for ZipRecruiter)

1. **Bright Data** (formerly Luminati)
   - Cost: ~$500/month for 40GB
   - Best success rate
   - Residential IPs worldwide

2. **Oxylabs**
   - Cost: ~$300/month for 20GB
   - Good uptime
   - Easy API integration

3. **Smartproxy**
   - Cost: ~$75/month for 5GB
   - Budget-friendly
   - Decent for light usage

### Datacenter Proxies (OK for Indeed/Monster)

1. **IPRoyal**
   - Cost: ~$80/month for 100 IPs
   - Cheap but may get blocked

2. **MyPrivateProxy**
   - Cost: ~$50/month for 50 IPs
   - Reliable for Indeed/Monster

---

## CAPTCHA Solving

If you encounter CAPTCHAs frequently, integrate 2Captcha:

### 1. Install 2Captcha SDK

```bash
pip install 2captcha-python
```

### 2. Update Config

```bash
TWOCAPTCHA_API_KEY=your_api_key_here
```

### 3. Modify Scraper

```python
from twocaptcha import TwoCaptcha

solver = TwoCaptcha('your_api_key')

# When CAPTCHA detected
try:
    result = solver.recaptcha(
        sitekey='6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
        url='https://www.indeed.com/jobs'
    )
    # Submit solution
    await page.evaluate(f'document.getElementById("g-recaptcha-response").value = "{result["code"]}"')
except Exception as e:
    logger.error(f"CAPTCHA solving failed: {e}")
```

**Cost:** ~$3 per 1000 CAPTCHAs

---

## Scraping Schedule Recommendations

### Development/Testing
- **Frequency:** Manual runs only
- **Volume:** 10-20 jobs per test
- **Sources:** One at a time

### Light Production
- **Frequency:** 2-3 times per day
- **Volume:** 50 jobs per source per run
- **Sources:** Indeed + Monster
- **Total:** ~300 jobs/day

### Heavy Production
- **Frequency:** Every 2-4 hours
- **Volume:** 100 jobs per source per run
- **Sources:** All three (with proxies for ZipRecruiter)
- **Total:** ~1,200-1,800 jobs/day
- **Requirements:**
  - Residential proxies
  - CAPTCHA solver
  - Dedicated server

---

## Troubleshooting

### Problem: No jobs returned

**Possible causes:**
1. Selectors changed (job boards update frequently)
2. Rate limited
3. CAPTCHA triggered
4. Invalid search query/location

**Solution:**
- Check scraper logs for specific errors
- Try with a different query
- Wait 1 hour and retry
- Update selectors in scraper code

### Problem: CAPTCHAs appearing

**Solution:**
1. Add delays: Increase `JOB_SCRAPE_DELAY_SECONDS`
2. Use proxies: Enable `JOB_SCRAPER_PROXY_ENABLED`
3. Reduce frequency: Scrape less often
4. Add 2Captcha integration

### Problem: Rate limits

**Solution:**
1. Reduce `max_results` parameter
2. Increase delays between requests
3. Space out scraping sessions
4. Use rotating proxies

### Problem: Database save failures

**Solution:**
1. Check database connection
2. Ensure location exists in database
3. Check for unique constraint violations
4. Review logs for specific SQL errors

---

## Performance Optimization

### 1. Disable Company Lookup for Speed

```python
# Fast (2-3 seconds per job)
enable_company_lookup=False

# Slow (10-15 seconds per job)
enable_company_lookup=True
```

### 2. Parallel Scraping

```python
async def scrape_parallel():
    tasks = [
        scraper1.search_jobs(...),
        scraper2.search_jobs(...),
        scraper3.search_jobs(...)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. Cache Results

```python
# Use Redis to cache job listings
import redis
r = redis.Redis()

cache_key = f"jobs:{source}:{query}:{location}"
cached = r.get(cache_key)

if cached:
    return json.loads(cached)

# Scrape and cache
jobs = await scraper.search_jobs(...)
r.setex(cache_key, 3600, json.dumps(jobs))  # Cache for 1 hour
```

---

## Legal & Ethical Considerations

### Terms of Service

- **Indeed:** Explicitly prohibits automated access without permission
- **Monster:** Similar restrictions in ToS
- **ZipRecruiter:** Very strict about scraping

**Recommendation:**
- Use official APIs when available (Indeed has a paid API)
- Limit scraping to reasonable volumes
- Respect robots.txt
- Add contact info in user agent

### robots.txt Compliance

Check each site's robots.txt:
- https://www.indeed.com/robots.txt
- https://www.monster.com/robots.txt
- https://www.ziprecruiter.com/robots.txt

Most job boards disallow scraping in robots.txt, so use at your own risk.

### Best Practices

1. **Add contact info to user agent:**
   ```python
   user_agent = "JobScraper/1.0 (contact@yourdomain.com)"
   ```

2. **Implement polite delays:**
   - Minimum 2-3 seconds between requests
   - Respect Crawl-delay directive if present

3. **Handle errors gracefully:**
   - Don't retry immediately on failure
   - Back off exponentially

4. **Consider alternatives:**
   - Indeed API (paid but legal)
   - Google Jobs API
   - LinkedIn API (via Piloterr service)

---

## Monitoring & Alerts

### Key Metrics to Track

```python
{
    "daily_jobs_scraped": 850,
    "success_rate": 0.82,
    "captcha_rate": 0.05,
    "rate_limit_rate": 0.02,
    "avg_scrape_duration": 45.2,
    "email_discovery_rate": 0.28,
    "by_source": {
        "indeed": {"jobs": 450, "success": 0.95},
        "monster": {"jobs": 320, "success": 0.78},
        "ziprecruiter": {"jobs": 80, "success": 0.40}
    }
}
```

### Alert Conditions

- Success rate < 50% → Switch to proxies
- CAPTCHA rate > 10% → Add solver
- Rate limit rate > 5% → Reduce frequency
- Zero jobs for 3 consecutive runs → Check selectors

---

## Future Enhancements

### Planned
- [ ] LinkedIn scraper (via Piloterr API)
- [ ] Glassdoor company reviews integration
- [ ] Indeed API integration (official)
- [ ] Advanced salary parsing (ranges, hourly vs yearly)
- [ ] Skills extraction from job descriptions
- [ ] Duplicate job detection across sources

### Under Consideration
- [ ] AI-powered job matching scores
- [ ] Automatic application submission
- [ ] Salary prediction ML model
- [ ] Job trend analysis dashboard

---

## Support & Contributing

### Reporting Issues

Found a bug or selector issue? Please report:

1. Which job board (Indeed/Monster/ZipRecruiter)
2. Search query and location used
3. Error message or unexpected behavior
4. Scraper logs (if available)

### Updating Selectors

Job boards change frequently. To update selectors:

1. Inspect the job board HTML
2. Update selectors in `_extract_job_from_element()`
3. Test thoroughly
4. Submit PR with before/after examples

---

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [2Captcha API Docs](https://2captcha.com/api-docs)
- [Bright Data Proxy Setup](https://brightdata.com/proxy-solutions)
- [Indeed API (Official)](https://indeed.com/api)

---

**Questions?** Contact the development team or check the main project README.

**Warning:** Use these scrapers responsibly and in compliance with applicable laws and terms of service.
