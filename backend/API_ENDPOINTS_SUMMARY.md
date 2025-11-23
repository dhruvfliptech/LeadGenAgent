# API Endpoints Summary: Multi-Source Scraper Integration

## Overview
This document provides a complete summary of all REST API endpoints created for multi-source scraping (Google Maps, LinkedIn, and Job Boards). All endpoints follow REST conventions and are organized by source.

**Base URL**: `/api/v1`

---

## 1. Google Maps Scraper Endpoints

### Endpoint: POST /api/v1/google-maps/scrape
**Purpose**: Start a Google Maps scraping job

**Request Body**:
```json
{
  "query": "restaurants",
  "location": "San Francisco, CA",
  "max_results": 20,
  "extract_emails": true,
  "use_places_api": false,
  "location_id": null
}
```

**Response** (201 Created):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scraping job started for \"restaurants\" in San Francisco, CA",
  "estimated_time_seconds": 160
}
```

**Status Codes**:
- 200: Job started successfully
- 400: Invalid request parameters
- 403: Google Maps scraping disabled
- 500: Server error

---

### Endpoint: GET /api/v1/google-maps/status/{job_id}
**Purpose**: Check the status of a Google Maps scraping job

**Query Parameters**:
- `include_results`: boolean (default: false) - Include full results in response

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {
    "total": 20,
    "completed": 20,
    "current_action": "Completed"
  },
  "results_count": 18,
  "created_at": "2025-11-05T10:30:00Z",
  "completed_at": "2025-11-05T10:35:00Z",
  "error": null,
  "results": null
}
```

**Status Codes**:
- 200: Status retrieved
- 404: Job not found
- 500: Server error

---

### Endpoint: GET /api/v1/google-maps/jobs
**Purpose**: List recent Google Maps scraping jobs

**Query Parameters**:
- `status`: string (optional) - Filter by status: pending, running, completed, failed
- `limit`: integer (default: 10, max: 100)

**Response** (200 OK):
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": {
      "total": 20,
      "completed": 20,
      "current_action": "Completed"
    },
    "results_count": 18,
    "created_at": "2025-11-05T10:30:00Z",
    "completed_at": "2025-11-05T10:35:00Z",
    "error": null,
    "results": null
  }
]
```

**Status Codes**:
- 200: Jobs retrieved
- 500: Server error

---

### Endpoint: GET /api/v1/google-maps/jobs/{job_id}/results
**Purpose**: Get detailed results from a completed Google Maps scraping job

**Response** (200 OK):
```json
[
  {
    "name": "Chez Panisse",
    "phone": "+1-510-548-5525",
    "email": "info@chezpanisse.com",
    "website": "https://www.chezpanisse.com",
    "rating": 4.7,
    "review_count": 1245,
    "address": "1517 Shattuck Ave, Berkeley, CA 94709"
  }
]
```

**Status Codes**:
- 200: Results retrieved
- 400: Job not completed yet
- 404: Job not found
- 500: Server error

---

### Endpoint: DELETE /api/v1/google-maps/jobs/{job_id}
**Purpose**: Delete a completed or failed scraping job

**Response** (200 OK):
```json
{
  "message": "Job 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

**Status Codes**:
- 200: Job deleted
- 400: Cannot delete job in pending/running status
- 404: Job not found
- 500: Server error

---

### Endpoint: GET /api/v1/google-maps/health
**Purpose**: Check Google Maps scraping service health

**Response** (200 OK):
```json
{
  "status": "ok",
  "google_maps_enabled": true,
  "places_api_configured": false,
  "max_results_limit": 100,
  "scrape_timeout": 300
}
```

---

## 2. Job Boards Scraper Endpoints

### Endpoint: POST /api/v1/job-boards/scrape
**Purpose**: Scrape job board listings (Indeed, Monster, ZipRecruiter)

**Request Body**:
```json
{
  "source": "all",
  "query": "python developer",
  "location": "San Francisco, CA",
  "max_results": 100,
  "enable_company_lookup": false,
  "save_to_database": true
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Successfully scraped 287 jobs from 3 source(s)",
  "total_jobs_scraped": 287,
  "jobs_by_source": {
    "indeed": 95,
    "monster": 87,
    "ziprecruiter": 105
  },
  "stats": [
    {
      "source": "indeed",
      "jobs_scraped": 95,
      "errors_encountered": 0,
      "captchas_detected": 0,
      "rate_limits_hit": 0,
      "duration_seconds": 45.2
    }
  ],
  "jobs": null,
  "warnings": []
}
```

**Status Codes**:
- 200: Scraping completed
- 400: Invalid source or missing configuration
- 500: Server error

---

### Endpoint: GET /api/v1/job-boards/sources
**Purpose**: Get list of enabled job board sources and configuration

**Response** (200 OK):
```json
{
  "sources": [
    {
      "name": "indeed",
      "enabled": true,
      "display_name": "Indeed",
      "description": "One of the largest job boards worldwide"
    },
    {
      "name": "monster",
      "enabled": true,
      "display_name": "Monster",
      "description": "Major job board with diverse listings"
    },
    {
      "name": "ziprecruiter",
      "enabled": true,
      "display_name": "ZipRecruiter",
      "description": "Job aggregator with aggressive bot detection - use with caution"
    }
  ],
  "settings": {
    "default_delay_seconds": 3,
    "max_results_per_source": 100,
    "company_lookup_enabled": true
  }
}
```

---

### Endpoint: GET /api/v1/job-boards/jobs
**Purpose**: Get paginated list of scraped job board jobs

**Query Parameters**:
- `source`: string (optional) - Filter by source (indeed, monster, ziprecruiter)
- `limit`: integer (default: 50, max: 100)
- `offset`: integer (default: 0)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "Senior Python Developer",
    "company_name": "TechCorp Inc.",
    "location": "San Francisco, CA",
    "url": "https://indeed.com/jobs/view/abc123",
    "description": "We are looking for a senior Python developer...",
    "salary": "$150,000 - $200,000",
    "employment_type": ["Full-time"],
    "is_remote": true,
    "posted_at": "2025-11-05T10:00:00Z",
    "source": "indeed",
    "status": "new",
    "is_contacted": false,
    "attributes": {
      "source": "indeed",
      "external_id": "abc123",
      "company_website": "https://techcorp.com"
    }
  }
]
```

**Status Codes**:
- 200: Jobs retrieved
- 500: Server error

---

### Endpoint: GET /api/v1/job-boards/jobs/{job_id}
**Purpose**: Get details of a single job board job

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Senior Python Developer",
  "company_name": "TechCorp Inc.",
  "company_email": "careers@techcorp.com",
  "company_website": "https://techcorp.com",
  "location": "San Francisco, CA",
  "url": "https://indeed.com/jobs/view/abc123",
  "description": "We are looking for a senior Python developer with 5+ years experience",
  "salary": "$150,000 - $200,000",
  "employment_type": ["Full-time"],
  "is_remote": true,
  "posted_at": "2025-11-05T10:00:00Z",
  "source": "indeed",
  "external_id": "abc123",
  "status": "new",
  "is_contacted": false,
  "is_processed": false,
  "attributes": {
    "source": "indeed",
    "external_id": "abc123",
    "company_name": "TechCorp Inc.",
    "company_website": "https://techcorp.com",
    "company_email": "careers@techcorp.com"
  },
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Status Codes**:
- 200: Job retrieved
- 400: Job not from a job board source
- 404: Job not found
- 500: Server error

---

### Endpoint: GET /api/v1/job-boards/stats/{source}
**Purpose**: Get statistics for jobs from a specific source

**Path Parameters**:
- `source`: string - indeed, monster, or ziprecruiter

**Response** (200 OK):
```json
{
  "source": "indeed",
  "total_leads": 95,
  "with_email": 34,
  "with_website": 67,
  "remote_jobs": 45,
  "contacted": 12,
  "status_breakdown": {
    "new": 60,
    "in_progress": 25,
    "contacted": 10
  },
  "email_discovery_rate": 35.79,
  "website_discovery_rate": 70.53
}
```

**Status Codes**:
- 200: Stats retrieved
- 400: Invalid or wildcard source
- 500: Server error

---

## 3. LinkedIn Scraper Endpoints

### Endpoint: POST /api/v1/linkedin/scrape
**Purpose**: Start a LinkedIn job scraping job

**Request Body**:
```json
{
  "keywords": ["python developer", "machine learning engineer"],
  "location": "San Francisco, CA",
  "experience_level": "mid_senior",
  "job_type": "full_time",
  "max_results": 100,
  "save_to_database": true,
  "location_id": 1
}
```

**Response** (200 OK):
```json
{
  "job_id": "LinkedIn_20251105_103000_5432",
  "status": "started",
  "message": "LinkedIn scraping job started",
  "estimated_completion": "2025-11-05T11:00:00Z",
  "service_used": "piloterr"
}
```

**Status Codes**:
- 200: Job started
- 400: Invalid parameters
- 500: Service configuration error
- 503: LinkedIn integration disabled

---

### Endpoint: GET /api/v1/linkedin/status/{job_id}
**Purpose**: Check the status of a LinkedIn scraping job

**Response** (200 OK):
```json
{
  "job_id": "LinkedIn_20251105_103000_5432",
  "status": "completed",
  "jobs_found": 142,
  "jobs_saved": 136,
  "duplicates_skipped": 6,
  "errors": 0,
  "credits_used": 142,
  "cost_usd": 0.71,
  "started_at": "2025-11-05T10:30:00Z",
  "completed_at": "2025-11-05T10:45:00Z",
  "service_used": "piloterr",
  "error_message": null,
  "results_preview": null
}
```

**Status Codes**:
- 200: Status retrieved
- 404: Job not found
- 500: Server error

---

### Endpoint: GET /api/v1/linkedin/jobs
**Purpose**: Get all LinkedIn jobs from database

**Query Parameters**:
- `limit`: integer (default: 50, max: 100)
- `offset`: integer (default: 0)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "title": "Senior Machine Learning Engineer",
    "company_name": "OpenAI",
    "company_url": "https://openai.com",
    "location": "San Francisco, CA",
    "url": "https://linkedin.com/jobs/view/3829504856",
    "description": "We are seeking an experienced ML engineer...",
    "salary": "$200,000 - $350,000",
    "employment_type": ["Full-time"],
    "is_remote": true,
    "posted_at": "2025-11-01T10:00:00Z",
    "experience_level": "mid_senior",
    "status": "new",
    "is_contacted": false,
    "linkedin_job_id": "3829504856"
  }
]
```

**Status Codes**:
- 200: Jobs retrieved
- 500: Server error

---

### Endpoint: GET /api/v1/linkedin/jobs/{job_id}
**Purpose**: Get details of a single LinkedIn job

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Senior Machine Learning Engineer",
  "company_name": "OpenAI",
  "company_url": "https://openai.com",
  "location": "San Francisco, CA",
  "url": "https://linkedin.com/jobs/view/3829504856",
  "description": "We are seeking an experienced ML engineer with 5+ years in production systems",
  "salary": "$200,000 - $350,000",
  "employment_type": ["Full-time"],
  "is_remote": true,
  "posted_at": "2025-11-01T10:00:00Z",
  "experience_level": "mid_senior",
  "status": "new",
  "is_contacted": false,
  "is_processed": false,
  "linkedin_job_id": "3829504856",
  "attributes": {
    "company_name": "OpenAI",
    "company_url": "https://openai.com",
    "experience_level": "mid_senior",
    "linkedin_job_id": "3829504856",
    "source": "linkedin"
  },
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Status Codes**:
- 200: Job retrieved
- 400: Job not from LinkedIn
- 404: Job not found
- 500: Server error

---

### Endpoint: GET /api/v1/linkedin/services
**Purpose**: List available LinkedIn scraping services with pricing

**Response** (200 OK):
```json
[
  {
    "name": "Piloterr",
    "status": "available",
    "monthly_cost": "$49 (Premium: 18K credits)",
    "capacity": "18,000 jobs/month",
    "reliability": "High",
    "recommendation": "Best for startups and small businesses",
    "warnings": []
  },
  {
    "name": "ScraperAPI",
    "status": "not_configured",
    "monthly_cost": "$299 (Professional: 600K requests)",
    "capacity": "600,000 jobs/month",
    "reliability": "Very High",
    "recommendation": "Best for medium-to-large businesses with high volume",
    "warnings": [
      "Not configured: Set LINKEDIN_SERVICE=scraperapi and LINKEDIN_API_KEY in .env"
    ]
  },
  {
    "name": "Selenium (DIY)",
    "status": "not_configured",
    "monthly_cost": "$50-200 (proxies + maintenance)",
    "capacity": "10-20 jobs/day safely",
    "reliability": "Low (50-70% success rate)",
    "recommendation": "NOT RECOMMENDED - Use Piloterr or ScraperAPI instead",
    "warnings": [
      "⚠️ HIGH BAN RISK: LinkedIn actively blocks automated scraping",
      "⚠️ Account bans are often PERMANENT",
      "⚠️ Violates LinkedIn Terms of Service"
    ]
  }
]
```

**Status Codes**:
- 200: Services retrieved
- 500: Server error

---

### Endpoint: DELETE /api/v1/linkedin/jobs/{job_id}
**Purpose**: Delete a scraping job from tracking (does not delete database records)

**Response** (200 OK):
```json
{
  "message": "Job LinkedIn_20251105_103000_5432 deleted successfully"
}
```

**Status Codes**:
- 200: Job deleted
- 404: Job not found
- 500: Server error

---

## Request/Response Patterns

### Common Query Parameters
- `limit`: Maximum number of results to return (default: 50, max: 100)
- `offset`: Pagination offset for list endpoints (default: 0)
- `status`: Filter by status (pending, running, completed, failed)

### Common Response Fields
- `id`: Unique identifier (integer for database records, UUID for jobs)
- `status`: Current status string
- `created_at`: ISO 8601 timestamp
- `updated_at`: ISO 8601 timestamp (if applicable)

### Error Responses
All endpoints return error responses in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Pagination

List endpoints support pagination through query parameters:
- `limit`: Number of results per page (default: 50, max: 100)
- `offset`: Number of results to skip (default: 0)

**Example**:
```
GET /api/v1/job-boards/jobs?source=indeed&limit=25&offset=50
```

---

## Rate Limiting Notes

- Google Maps: ~3 seconds per business, +5 seconds if extracting emails
- Indeed: Respects job board rate limits; errors logged
- Monster: Respects job board rate limits; errors logged
- ZipRecruiter: Aggressive bot detection; recommended max 20 results
- LinkedIn: Service-dependent (Piloterr: 18K/month, ScraperAPI: 600K/month)

---

## Authentication

Currently, all endpoints are public. For production, implement:
- API key validation
- JWT token verification
- Rate limiting per user/API key

---

## Implementation Details

### File Locations
- **Job Boards**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/job_boards.py`
- **Google Maps**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/google_maps.py`
- **LinkedIn**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/linkedin.py`
- **Main App**: `/Users/greenmachine2.0/Craigslist/backend/app/main.py`

### Scraper Modules
- **Google Maps**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/google_maps_scraper.py`
- **Indeed**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/indeed_scraper.py`
- **Monster**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/monster_scraper.py`
- **ZipRecruiter**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/ziprecruiter_scraper.py`
- **LinkedIn**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/linkedin_scraper.py`
- **Base**: `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/base_job_scraper.py`

### Database Models
Jobs are stored in the `Lead` model with source tracking via the `attributes` JSON field:
```json
{
  "source": "indeed|monster|ziprecruiter|linkedin|google_maps",
  "external_id": "unique_id_from_source",
  "company_name": "Company Name",
  "company_website": "https://company.com",
  "company_email": "email@company.com"
}
```

---

## Testing

### Example cURL Commands

**Start Google Maps Scrape**:
```bash
curl -X POST http://localhost:8000/api/v1/google-maps/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "restaurants",
    "location": "San Francisco, CA",
    "max_results": 20
  }'
```

**Start Job Boards Scrape**:
```bash
curl -X POST http://localhost:8000/api/v1/job-boards/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "source": "all",
    "query": "python developer",
    "location": "San Francisco, CA",
    "max_results": 100
  }'
```

**Start LinkedIn Scrape**:
```bash
curl -X POST http://localhost:8000/api/v1/linkedin/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python developer"],
    "location": "San Francisco, CA",
    "max_results": 100,
    "location_id": 1
  }'
```

**Get Job List**:
```bash
curl http://localhost:8000/api/v1/job-boards/jobs?source=indeed&limit=50
```

---

## Version History

- **v1.0.0** (2025-11-05): Initial release with Google Maps, Job Boards, and LinkedIn endpoints
