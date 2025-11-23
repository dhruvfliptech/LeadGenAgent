# API Endpoint Routing Map

## Complete Endpoint Hierarchy

```
/api/v1/
├── google-maps/
│   ├── POST   /scrape                    - Start scraping job
│   ├── GET    /status/{job_id}           - Check job status
│   ├── GET    /jobs                      - List all jobs
│   ├── GET    /jobs/{job_id}/results     - Get job results
│   ├── DELETE /jobs/{job_id}             - Delete job
│   └── GET    /health                    - Health check
│
├── job-boards/
│   ├── POST   /scrape                    - Start scraping all boards
│   ├── GET    /sources                   - List available sources
│   ├── GET    /jobs                      - List scraped jobs (paginated)
│   ├── GET    /jobs/{job_id}             - Get single job details
│   └── GET    /stats/{source}            - Get statistics by source
│
└── linkedin/
    ├── POST   /scrape                    - Start scraping job
    ├── GET    /status/{job_id}           - Check job status
    ├── GET    /jobs                      - List all scraped jobs
    ├── GET    /jobs/{job_id}             - Get single job details
    ├── GET    /services                  - List available services
    └── DELETE /jobs/{job_id}             - Delete job tracking
```

---

## Endpoint Summary Table

| Method | Path | Handler | Purpose | Status |
|--------|------|---------|---------|--------|
| **GOOGLE MAPS** |
| POST | `/api/v1/google-maps/scrape` | `start_google_maps_scrape()` | Start scraping | Active |
| GET | `/api/v1/google-maps/status/{job_id}` | `get_scraping_status()` | Check job status | Active |
| GET | `/api/v1/google-maps/jobs` | `list_scraping_jobs()` | List jobs | Active |
| GET | `/api/v1/google-maps/jobs/{job_id}/results` | `get_scraping_results()` | Get results | Active |
| DELETE | `/api/v1/google-maps/jobs/{job_id}` | `delete_job()` | Delete job | Active |
| GET | `/api/v1/google-maps/health` | `health_check()` | Health status | Active |
| **JOB BOARDS** |
| POST | `/api/v1/job-boards/scrape` | `scrape_job_boards()` | Start scraping | Active |
| GET | `/api/v1/job-boards/sources` | `get_enabled_sources()` | List sources | Active |
| GET | `/api/v1/job-boards/jobs` | `get_job_board_jobs()` | List jobs | Active |
| GET | `/api/v1/job-boards/jobs/{job_id}` | `get_single_job_board_job()` | Get job details | Active |
| GET | `/api/v1/job-boards/stats/{source}` | `get_source_stats()` | Get statistics | Active |
| **LINKEDIN** |
| POST | `/api/v1/linkedin/scrape` | `start_linkedin_scrape()` | Start scraping | Active |
| GET | `/api/v1/linkedin/status/{job_id}` | `get_scraping_status()` | Check job status | Active |
| GET | `/api/v1/linkedin/jobs` | `get_linkedin_jobs()` | List jobs | Active |
| GET | `/api/v1/linkedin/jobs/{job_id}` | `get_linkedin_job()` | Get job details | Active |
| GET | `/api/v1/linkedin/services` | `list_available_services()` | List services | Active |
| DELETE | `/api/v1/linkedin/jobs/{job_id}` | `delete_scrape_job()` | Delete job | Active |

---

## FastAPI Router Configuration

### In `app/main.py`:

```python
# Job Boards endpoints - Phase 2 (Indeed, Monster, ZipRecruiter)
app.include_router(job_boards.router, prefix="/api/v1/job-boards", tags=["job-boards"])

# LinkedIn endpoints - Phase 2
app.include_router(linkedin.router, prefix="/api/v1/linkedin", tags=["linkedin"])

# Google Maps endpoints - Phase 2
app.include_router(google_maps.router, prefix="/api/v1/google-maps", tags=["google-maps"])
```

---

## Source Code Organization

### File: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/google_maps.py`
- **Total Lines**: 458
- **Router Setup**: Line 24
- **Endpoints**: 6
- **Key Classes**:
  - `GoogleMapsScrapeRequest` - Request validation
  - `GoogleMapsScrapeResponse` - Response schema
  - `GoogleMapsJobStatus` - Job status schema
  - `scraping_jobs` - In-memory job tracking

### File: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/job_boards.py`
- **Total Lines**: 534
- **Router Setup**: Line 27
- **Endpoints**: 5
- **Key Classes**:
  - `JobSource` - Enum for job sources
  - `ScrapeJobBoardsRequest` - Request validation
  - `ScrapeJobBoardsResponse` - Response schema
  - `JobBoardStats` - Statistics schema
  - Helper: `_save_jobs_to_database()` - Database persistence

### File: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/linkedin.py`
- **Total Lines**: 815
- **Router Setup**: Line 63
- **Endpoints**: 6
- **Key Classes**:
  - `LinkedInScrapeRequest` - Request validation
  - `LinkedInScrapeResponse` - Response schema
  - `LinkedInJobStatusResponse` - Job status schema
  - `ServiceInfo` - Service pricing info
  - Helper functions: `get_configured_service()`, `scrape_with_piloterr()`, etc.

---

## Data Flow Diagrams

### Google Maps Workflow
```
POST /scrape
    ↓
start_google_maps_scrape()
    ↓
Create job ID + metadata
    ↓
Store in scraping_jobs (in-memory)
    ↓
Background: run_google_maps_scraping()
    ↓
GET /status/{job_id} or GET /jobs
    ↓
Return job status + progress
    ↓
GET /jobs/{job_id}/results (when completed)
    ↓
Returns scraped businesses
```

### Job Boards Workflow
```
POST /scrape
    ↓
scrape_job_boards()
    ↓
Initialize Playwright browser
    ↓
Loop through sources (Indeed, Monster, ZipRecruiter)
    ↓
For each: Create scraper → search_jobs() → collect results
    ↓
Save to database (if save_to_database=true)
    ↓
Return statistics + job counts
    ↓
GET /jobs or GET /jobs/{id}
    ↓
Returns paginated job listings from database
```

### LinkedIn Workflow
```
POST /scrape
    ↓
start_linkedin_scrape()
    ↓
Validate service configuration (Piloterr/ScraperAPI/Selenium)
    ↓
Create job ID + metadata
    ↓
Background: scrape_with_piloterr() / scrape_with_scraperapi() / scrape_with_selenium()
    ↓
Search jobs by keywords + location
    ↓
Save to database (if save_to_database=true)
    ↓
GET /status/{job_id}
    ↓
Return job stats + costs + results
```

---

## Integration Points

### Database Models Used
- **Lead** - Stores all scraped jobs across sources
  - Fields: id, title, description, url, location_id, attributes (JSON)
  - Relationships: location_id (foreign key to Location)

- **Location** - Geographic locations for scraping
  - Fields: id, name, code, url, state, country

### External Services
1. **Google Maps/Places API**
   - Playwright-based scraping
   - Optional Google Places API integration

2. **Job Boards**
   - Playwright automation for Indeed, Monster, ZipRecruiter
   - Anti-bot detection evasion

3. **LinkedIn Services**
   - Piloterr API (recommended)
   - ScraperAPI
   - DIY Selenium (not recommended)

---

## Response Codes Summary

### Success Responses
- **200 OK**: Standard successful response
- **201 Created**: Resource created

### Client Error Responses
- **400 Bad Request**: Invalid parameters
- **403 Forbidden**: Feature disabled
- **404 Not Found**: Resource not found

### Server Error Responses
- **500 Internal Server Error**: Unexpected server error
- **503 Service Unavailable**: Service configuration missing

---

## Request/Response Examples by Endpoint

### 1. Google Maps Scraping

**Request**:
```http
POST /api/v1/google-maps/scrape HTTP/1.1
Content-Type: application/json

{
  "query": "plumbers",
  "location": "Seattle, WA",
  "max_results": 30,
  "extract_emails": true
}
```

**Response (200 OK)**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scraping job started for \"plumbers\" in Seattle, WA",
  "estimated_time_seconds": 180
}
```

---

### 2. Job Boards Scraping

**Request**:
```http
POST /api/v1/job-boards/scrape HTTP/1.1
Content-Type: application/json

{
  "source": "all",
  "query": "data scientist",
  "location": "New York, NY",
  "max_results": 200,
  "save_to_database": true
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Successfully scraped 573 jobs from 3 source(s)",
  "total_jobs_scraped": 573,
  "jobs_by_source": {
    "indeed": 198,
    "monster": 187,
    "ziprecruiter": 188
  },
  "stats": [...],
  "warnings": []
}
```

---

### 3. LinkedIn Scraping

**Request**:
```http
POST /api/v1/linkedin/scrape HTTP/1.1
Content-Type: application/json

{
  "keywords": ["machine learning", "AI engineer"],
  "location": "remote",
  "experience_level": "mid_senior",
  "max_results": 500,
  "location_id": 1
}
```

**Response (200 OK)**:
```json
{
  "job_id": "LinkedIn_20251105_110000_8934",
  "status": "started",
  "message": "LinkedIn scraping job started",
  "estimated_completion": "2025-11-05T11:30:00Z",
  "service_used": "piloterr"
}
```

---

## Configuration & Environment Variables

### Google Maps
- `GOOGLE_MAPS_ENABLED` - Enable/disable Google Maps scraping (default: true)
- `GOOGLE_PLACES_API_KEY` - Optional for Google Places API usage
- `GOOGLE_MAPS_MAX_RESULTS` - Maximum results per request (default: 100)
- `GOOGLE_MAPS_SCRAPE_TIMEOUT` - Timeout in seconds (default: 300)

### Job Boards
- `INDEED_ENABLED` - Enable Indeed scraping (default: true)
- `MONSTER_ENABLED` - Enable Monster scraping (default: true)
- `ZIPRECRUITER_ENABLED` - Enable ZipRecruiter scraping (default: true)
- `JOB_SCRAPE_DELAY_SECONDS` - Delay between requests (default: 3)
- `JOB_MAX_RESULTS_PER_SOURCE` - Max results per source (default: 100)

### LinkedIn
- `LINKEDIN_ENABLED` - Enable LinkedIn scraping (default: false)
- `LINKEDIN_SERVICE` - Service to use: piloterr, scraperapi, selenium
- `LINKEDIN_API_KEY` - API key for Piloterr/ScraperAPI
- `LINKEDIN_EMAIL` - Email for Selenium scraper
- `LINKEDIN_PASSWORD` - Password for Selenium scraper

---

## Performance Metrics

### Typical Execution Times
- **Google Maps**: 3-5 seconds per business + email extraction time
- **Indeed**: 45-60 seconds for 100 jobs
- **Monster**: 45-60 seconds for 100 jobs
- **ZipRecruiter**: 60-90 seconds for 100 jobs (more bot detection)
- **LinkedIn (Piloterr)**: Variable (depends on API response)

### Database Operations
- **Job Retrieval**: ~50ms for paginated lists
- **Job Details**: ~10ms for single record
- **Statistics**: ~100-200ms (requires aggregation)

---

## Troubleshooting

### Common Issues

**Job fails with "CAPTCHA detected"**
- Google Maps: Usually recovers after wait
- Job Boards: May need proxy rotation
- LinkedIn: Service-dependent

**Empty results**
- Check location/query parameters
- Verify search terms exist
- Check rate limits not exceeded

**Jobs not saved to database**
- Verify `save_to_database=true` in request
- Check location_id is valid (for LinkedIn)
- Check database connection

**Slow response times**
- Reduce `max_results` parameter
- Check browser resource usage
- Enable result caching (if supported)

---

## Migration from Previous Versions

### Changes in v1.0.0
- Added unified job board scraper with multi-source support
- Added individual job retrieval endpoints (GET /jobs/{id})
- Refactored LinkedIn endpoints for consistency
- Enhanced Google Maps with results endpoint
- Added statistics endpoints for analytics

### Backward Compatibility
- All existing endpoints remain unchanged
- New endpoints add functionality, don't replace existing ones

---

## Next Steps / Future Enhancements

1. **Caching Layer** - Redis integration for job results
2. **Webhook Support** - Notify when scraping completes
3. **Batch Operations** - Scrape multiple locations simultaneously
4. **Advanced Filtering** - Complex query filters for job lists
5. **Export Formats** - CSV, Excel, JSON export endpoints
6. **WebSocket Updates** - Real-time progress streaming
7. **Authentication** - API key and JWT token support
8. **Rate Limiting** - Per-user rate limits
9. **Scheduling** - Cron-based recurring scrapes
10. **Analytics Dashboard** - Metrics and insights

