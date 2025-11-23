# Job Board Scrapers - Quick Start Guide

Get up and running with Indeed, Monster, and ZipRecruiter scrapers in 5 minutes.

---

## 1. Installation (1 minute)

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Install Playwright
pip install playwright
playwright install chromium
```

---

## 2. Configuration (2 minutes)

Add to `.env` file:

```bash
# Enable job boards
INDEED_ENABLED=true
MONSTER_ENABLED=true
ZIPRECRUITER_ENABLED=false  # Set to false initially (requires proxies)

# Basic settings
JOB_SCRAPE_DELAY_SECONDS=3
JOB_MAX_RESULTS_PER_SOURCE=50
JOB_ENABLE_COMPANY_LOOKUP=false
```

---

## 3. Register API Endpoint (30 seconds)

In `backend/app/main.py`, add:

```python
from app.api.endpoints import job_boards

app.include_router(
    job_boards.router,
    prefix="/api/v1/job-boards",
    tags=["job-boards"]
)
```

---

## 4. Test the Scrapers (1 minute)

### Option A: Via API (Recommended)

Start your backend:
```bash
python start_backend.sh
```

Make a request:
```bash
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "indeed",
    "query": "python developer",
    "location": "San Francisco, CA",
    "max_results": 10,
    "save_to_database": true
  }'
```

### Option B: Direct Python Test

```python
cd /Users/greenmachine2.0/Craigslist/backend
python -c "
import asyncio
from app.scrapers.indeed_scraper import IndeedScraper
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        scraper = IndeedScraper(browser=browser, context=context)
        jobs = await scraper.search_jobs('software engineer', 'New York, NY', max_results=5)
        print(f'Found {len(jobs)} jobs!')
        for job in jobs[:3]:
            print(f'- {job[\"title\"]} at {job[\"company_name\"]}')
        await browser.close()

asyncio.run(test())
"
```

### Option C: Run Tests

```bash
cd /Users/greenmachine2.0/Craigslist/backend
python -m pytest tests/test_job_scrapers.py::test_indeed_scraper -v
```

---

## 5. View Results

### In Database

```sql
SELECT
    title,
    attributes->>'company_name' as company,
    attributes->>'source' as source,
    created_at
FROM leads
WHERE attributes->>'source' IN ('indeed', 'monster', 'ziprecruiter')
ORDER BY created_at DESC
LIMIT 10;
```

### Via API

```bash
# Get stats
curl "http://localhost:8000/api/v1/job-boards/stats/indeed"

# Get enabled sources
curl "http://localhost:8000/api/v1/job-boards/sources"
```

---

## Common Use Cases

### 1. Scrape Indeed for Remote Python Jobs

```bash
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "indeed",
    "query": "python developer remote",
    "location": "United States",
    "max_results": 50,
    "save_to_database": true
  }'
```

### 2. Scrape All Sources (Except ZipRecruiter)

```bash
# Set in .env first
INDEED_ENABLED=true
MONSTER_ENABLED=true
ZIPRECRUITER_ENABLED=false

# Then scrape
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "all",
    "query": "data analyst",
    "location": "Chicago, IL",
    "max_results": 30,
    "save_to_database": true
  }'
```

### 3. Get Company Emails (Slow but Thorough)

```bash
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "indeed",
    "query": "sales",
    "location": "Austin, TX",
    "max_results": 10,
    "enable_company_lookup": true,
    "save_to_database": true
  }'
```

---

## Troubleshooting

### Issue: No jobs returned

**Fix:**
```bash
# Check if source is enabled
curl "http://localhost:8000/api/v1/job-boards/sources"

# Try with a simple query
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "indeed",
    "query": "engineer",
    "location": "New York",
    "max_results": 5
  }'
```

### Issue: CAPTCHA detected

**Fix:**
```bash
# In .env, increase delays
JOB_SCRAPE_DELAY_SECONDS=5
INDEED_MIN_DELAY=3.0
INDEED_MAX_DELAY=7.0

# Or disable the problematic source temporarily
ZIPRECRUITER_ENABLED=false
```

### Issue: Rate limited

**Fix:**
- Wait 30-60 minutes before retrying
- Reduce `max_results` to 20-30
- Enable proxies (see main README)

---

## Next Steps

1. **Read Full Documentation**: See `JOB_SCRAPERS_README.md` for detailed guide
2. **Set Up Proxies**: Required for production use with ZipRecruiter
3. **Schedule Scraping**: Use cron or scheduled tasks to run periodically
4. **Monitor Results**: Check database and API stats regularly

---

## Important Warnings

- **Indeed**: Works well, but don't scrape more than 100 jobs per hour
- **Monster**: Moderate success rate, has sign-up pop-ups (handled automatically)
- **ZipRecruiter**: REQUIRES proxies for reliable access (very aggressive bot detection)

**Legal Notice**: These scrapers may violate job boards' Terms of Service. Use at your own risk.

---

## Quick Reference Commands

```bash
# Test Indeed scraper
python -m pytest tests/test_job_scrapers.py::test_indeed_scraper -v

# Test Monster scraper
python -m pytest tests/test_job_scrapers.py::test_monster_scraper -v

# Scrape via API
curl -X POST "http://localhost:8000/api/v1/job-boards/scrape" \
  -H "Content-Type: application/json" \
  -d '{"source":"indeed","query":"developer","location":"SF","max_results":10}'

# Get stats
curl "http://localhost:8000/api/v1/job-boards/stats/indeed"

# Check configuration
curl "http://localhost:8000/api/v1/job-boards/sources"
```

---

**Ready to scrape?** Start with Indeed, test with 10 jobs, then scale up!
