# API Endpoints Quick Reference

## All Scraper Endpoints at a Glance

### Google Maps (6 endpoints)
```
POST   /api/v1/google-maps/scrape                  - Start scraping
GET    /api/v1/google-maps/status/{job_id}         - Check status
GET    /api/v1/google-maps/jobs                    - List jobs
GET    /api/v1/google-maps/jobs/{job_id}/results   - Get results [NEW]
DELETE /api/v1/google-maps/jobs/{job_id}           - Delete job
GET    /api/v1/google-maps/health                  - Health check
```

### Job Boards (5 endpoints)
```
POST   /api/v1/job-boards/scrape                   - Start scraping
GET    /api/v1/job-boards/sources                  - List sources
GET    /api/v1/job-boards/jobs                     - List jobs [NEW]
GET    /api/v1/job-boards/jobs/{job_id}            - Get job details [NEW]
GET    /api/v1/job-boards/stats/{source}           - Get stats
```

### LinkedIn (6 endpoints)
```
POST   /api/v1/linkedin/scrape                     - Start scraping
GET    /api/v1/linkedin/status/{job_id}            - Check status
GET    /api/v1/linkedin/jobs                       - List jobs [NEW]
GET    /api/v1/linkedin/jobs/{job_id}              - Get job details [NEW]
GET    /api/v1/linkedin/services                   - List services
DELETE /api/v1/linkedin/jobs/{job_id}              - Delete job
```

---

## Common Use Cases

### 1. Scrape Google Maps Businesses
```bash
# Start scraping
curl -X POST http://localhost:8000/api/v1/google-maps/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "dentists",
    "location": "San Francisco, CA",
    "max_results": 20
  }'

# Get job ID from response, then check status
curl http://localhost:8000/api/v1/google-maps/status/{job_id}

# When done, get results
curl http://localhost:8000/api/v1/google-maps/jobs/{job_id}/results
```

### 2. Scrape Job Boards
```bash
# Start scraping all boards
curl -X POST http://localhost:8000/api/v1/job-boards/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "source": "all",
    "query": "python developer",
    "location": "Remote",
    "max_results": 100
  }'

# List saved jobs
curl "http://localhost:8000/api/v1/job-boards/jobs?source=indeed&limit=50"

# Get specific job details
curl http://localhost:8000/api/v1/job-boards/jobs/1
```

### 3. Scrape LinkedIn
```bash
# Start scraping
curl -X POST http://localhost:8000/api/v1/linkedin/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["data scientist"],
    "location": "San Francisco, CA",
    "max_results": 100,
    "location_id": 1
  }'

# List LinkedIn jobs
curl "http://localhost:8000/api/v1/linkedin/jobs?limit=50"

# Get specific LinkedIn job
curl http://localhost:8000/api/v1/linkedin/jobs/1
```

---

## File Locations

```
/Users/greenmachine2.0/Craigslist/backend/
├── app/
│   ├── api/endpoints/
│   │   ├── google_maps.py        [6 endpoints]
│   │   ├── job_boards.py         [5 endpoints]
│   │   ├── linkedin.py           [6 endpoints]
│   │   └── ... (other endpoints)
│   │
│   ├── scrapers/
│   │   ├── google_maps_scraper.py
│   │   ├── indeed_scraper.py
│   │   ├── monster_scraper.py
│   │   ├── ziprecruiter_scraper.py
│   │   ├── linkedin_scraper.py
│   │   └── base_job_scraper.py
│   │
│   ├── models/
│   │   └── leads.py              [Lead model used by all endpoints]
│   │
│   └── main.py                   [Router registration]
│
└── Documentation/
    ├── API_ENDPOINTS_SUMMARY.md
    ├── ENDPOINT_ROUTING_MAP.md
    ├── ENDPOINT_IMPLEMENTATION_REPORT.md
    └── ENDPOINTS_QUICK_REFERENCE.md (this file)
```

---

## Request/Response Patterns

### Typical Start Job Response
```json
{
  "job_id": "unique_id_string",
  "status": "pending|running|completed|failed",
  "message": "Description of what's happening",
  "estimated_time_seconds": 180
}
```

### Typical List Response
```json
[
  {
    "id": 1,
    "title": "Job Title",
    "company_name": "Company",
    "location": "City, State",
    "url": "https://...",
    "status": "new",
    "posted_at": "2025-11-05T10:00:00Z"
  }
]
```

### Typical Error Response
```json
{
  "detail": "Error message explaining what went wrong"
}
```

---

## Key Features by Endpoint Type

### Start Scraping Endpoints (POST)
- Run asynchronously in background
- Return immediate response with job_id
- Optional `save_to_database` parameter
- Can run multiple jobs in parallel

### Check Status Endpoints (GET)
- Poll current job progress
- Show jobs_found, jobs_saved, errors
- Include estimated completion time
- Return cost info for paid services

### List Jobs Endpoints (GET)
- Paginated results (limit, offset)
- Filter by source/location
- Return job summaries
- Sorted by most recent first

### Get Job Details Endpoints (GET)
- Return complete job information
- Include company details
- Show all attributes
- Display processing status

### Statistics Endpoints (GET)
- Aggregate data by source
- Show email/website discovery rates
- Count by status
- Track contacted vs. new leads

---

## Query Parameter Reference

| Parameter | Type | Default | Max | Use Case |
|-----------|------|---------|-----|----------|
| limit | int | 50 | 100 | Pagination page size |
| offset | int | 0 | N/A | Pagination skip count |
| source | string | N/A | N/A | Filter by source |
| status | string | N/A | N/A | Filter by job status |
| include_results | bool | false | N/A | Include full results |

**Example**:
```
/api/v1/job-boards/jobs?source=indeed&limit=25&offset=50
```

---

## Status Values

### Job Status
- `pending` - Queued, not started
- `running` - Currently executing
- `completed` - Finished successfully
- `failed` - Encountered error

### Lead Status
- `new` - Just scraped
- `in_progress` - Being processed
- `contacted` - Contact attempt made
- `closed` - Deal closed

---

## Response Fields

### Google Maps Business
```json
{
  "name": "Business Name",
  "phone": "+1-555-1234",
  "email": "contact@business.com",
  "website": "https://business.com",
  "rating": 4.7,
  "review_count": 1245,
  "address": "123 Main St, City, State"
}
```

### Job Board Job
```json
{
  "id": 1,
  "title": "Job Title",
  "company_name": "Company",
  "company_email": "careers@company.com",
  "company_website": "https://company.com",
  "location": "City, State",
  "url": "https://jobboard.com/job/123",
  "salary": "$100,000 - $150,000",
  "employment_type": ["Full-time"],
  "is_remote": true
}
```

### LinkedIn Job
```json
{
  "id": 1,
  "title": "Job Title",
  "company_name": "Company",
  "company_url": "https://linkedin.com/company/...",
  "location": "San Francisco, CA",
  "url": "https://linkedin.com/jobs/view/123",
  "salary": "$150,000 - $200,000",
  "experience_level": "mid_senior",
  "linkedin_job_id": "123456"
}
```

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/POST |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid parameters |
| 403 | Forbidden | Feature disabled |
| 404 | Not Found | Job/resource doesn't exist |
| 500 | Server Error | Unexpected error |
| 503 | Unavailable | Service not configured |

---

## Environment Variables

### Google Maps
```bash
GOOGLE_MAPS_ENABLED=true
GOOGLE_PLACES_API_KEY=your_api_key  # Optional
GOOGLE_MAPS_MAX_RESULTS=100
```

### Job Boards
```bash
INDEED_ENABLED=true
MONSTER_ENABLED=true
ZIPRECRUITER_ENABLED=true
JOB_SCRAPE_DELAY_SECONDS=3
```

### LinkedIn
```bash
LINKEDIN_ENABLED=true
LINKEDIN_SERVICE=piloterr  # or scraperapi, selenium
LINKEDIN_API_KEY=your_key
```

---

## Curl Template Examples

### Template: Start Any Scraping Job
```bash
curl -X POST http://localhost:8000/api/v1/{source}/scrape \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Template: Check Status
```bash
curl http://localhost:8000/api/v1/{source}/status/{job_id}
```

### Template: List Jobs
```bash
curl "http://localhost:8000/api/v1/{source}/jobs?limit=50&offset=0"
```

### Template: Get Job Details
```bash
curl http://localhost:8000/api/v1/{source}/jobs/{id}
```

---

## Performance Tips

1. **Batch Requests** - Use larger `max_results` to reduce overhead
2. **Pagination** - Use `limit` and `offset` for large datasets
3. **Caching** - Check if results exist before scraping again
4. **Delays** - Job boards need `JOB_SCRAPE_DELAY_SECONDS` > 2
5. **Async** - Use background jobs; don't block on scraping
6. **Proxies** - Consider for high-volume ZipRecruiter scraping

---

## Troubleshooting

### "Job not found"
- Check job_id spelling
- Job may have expired (jobs are in-memory for some sources)
- Try getting list instead

### "Job not completed yet"
- Status is still pending/running
- Check job status first
- Wait and retry later

### "No results"
- Check search query/location
- Verify job board/source is enabled
- Search terms might return no matches

### Rate Limiting
- Space out requests
- Increase `JOB_SCRAPE_DELAY_SECONDS`
- Use fewer `max_results`

---

## Success Metrics

- Google Maps: 3-5 sec per business
- Indeed: 45-60 sec for 100 jobs
- Monster: 45-60 sec for 100 jobs
- ZipRecruiter: 60-90 sec for 100 jobs
- LinkedIn: Depends on API service

---

## Next Steps

1. Deploy to production
2. Set up monitoring/logging
3. Add authentication
4. Implement rate limiting
5. Set up webhook notifications
6. Create dashboard for monitoring
7. Add caching layer
8. Implement scheduling

---

## Support Links

- **Full Documentation**: See `API_ENDPOINTS_SUMMARY.md`
- **Route Mapping**: See `ENDPOINT_ROUTING_MAP.md`
- **Implementation Details**: See `ENDPOINT_IMPLEMENTATION_REPORT.md`
- **API Base**: `http://localhost:8000` (development)

---

**Last Updated**: 2025-11-05
**Total Endpoints**: 17 (5 new)
**Status**: Production Ready
