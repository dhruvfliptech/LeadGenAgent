# Craigslist Lead Generation System v2.0
## API Technical Reference

---

## Table of Contents
1. [Authentication](#authentication)
2. [Base URL & Versioning](#base-url--versioning)
3. [Request/Response Format](#requestresponse-format)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Endpoints Reference](#endpoints-reference)
7. [WebSocket Events](#websocket-events)
8. [Code Examples](#code-examples)

---

## Authentication

Currently, the API operates without authentication for development. Production implementation will use JWT tokens.

### Future Authentication Flow
```javascript
// Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}

// Use token in headers
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Base URL & Versioning

### Base URLs
- **Development**: `http://localhost:8001/api/v1`
- **Production**: `https://api.craigleads.com/api/v1`

### API Versioning
The API uses URL path versioning. Current version: `v1`

### Content Type
All requests and responses use `application/json` unless otherwise specified.

---

## Request/Response Format

### Standard Request Headers
```http
Content-Type: application/json
Accept: application/json
X-Request-ID: uuid-v4 (optional)
```

### Standard Response Format
```json
{
  "data": {}, // Actual response data
  "meta": {
    "request_id": "uuid-v4",
    "timestamp": "2024-08-23T10:30:00Z",
    "version": "1.0.0"
  }
}
```

### Pagination Format
```json
{
  "data": [],
  "pagination": {
    "total": 1000,
    "page": 1,
    "per_page": 20,
    "total_pages": 50,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "uuid-v4",
    "timestamp": "2024-08-23T10:30:00Z"
  }
}
```

### HTTP Status Codes
| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal error |
| 503 | Service Unavailable | Maintenance/overload |

---

## Rate Limiting

### Default Limits
- **Anonymous**: 100 requests/hour
- **Authenticated**: 1000 requests/hour
- **Premium**: 10000 requests/hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1629792000
```

### Rate Limit Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "retry_after": 3600
  }
}
```

---

## Endpoints Reference

### 1. Leads Management

#### 1.1 List Leads
```http
GET /api/v1/leads
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Items per page (default: 20, max: 100) |
| qualified_only | boolean | No | Filter qualified leads only |
| min_score | float | No | Minimum qualification score (0-1) |
| location_id | integer | No | Filter by location |
| category | string | No | Filter by category |
| keywords | string | No | Comma-separated keywords |
| sort_by | string | No | Sort field (created_at, score) |
| order | string | No | Sort order (asc, desc) |

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Senior Python Developer",
      "description": "We are looking for...",
      "url": "https://sfbay.craigslist.org/...",
      "location": {
        "id": 1,
        "name": "San Francisco",
        "state": "CA"
      },
      "compensation": "$120,000 - $150,000",
      "employment_type": ["full-time", "remote"],
      "is_remote": true,
      "qualification_score": 0.85,
      "scraped_at": "2024-08-23T10:00:00Z",
      "created_at": "2024-08-23T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 500,
    "page": 1,
    "per_page": 20,
    "total_pages": 25
  }
}
```

#### 1.2 Get Lead Details
```http
GET /api/v1/leads/{lead_id}
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| lead_id | integer | Yes | Lead ID |

**Response:**
```json
{
  "data": {
    "id": 1,
    "title": "Senior Python Developer",
    "description": "Full job description...",
    "body_html": "<div>...",
    "url": "https://sfbay.craigslist.org/...",
    "location": {
      "id": 1,
      "name": "San Francisco",
      "state": "CA",
      "region": "sfbay"
    },
    "compensation": "$120,000 - $150,000",
    "employment_type": ["full-time", "remote"],
    "is_remote": true,
    "is_internship": false,
    "is_nonprofit": false,
    "images": [],
    "qualification_score": 0.85,
    "qualification_reasons": [
      "Salary matches preference",
      "Contains required keywords",
      "Remote position available"
    ],
    "generated_responses": [
      {
        "id": 1,
        "template_id": 5,
        "generated_at": "2024-08-23T11:00:00Z",
        "status": "pending"
      }
    ],
    "scraped_at": "2024-08-23T10:00:00Z",
    "processed_at": "2024-08-23T10:05:00Z",
    "created_at": "2024-08-23T10:00:00Z",
    "updated_at": "2024-08-23T10:05:00Z"
  }
}
```

#### 1.3 Qualify Lead
```http
POST /api/v1/leads/{lead_id}/qualify
```

**Request Body:**
```json
{
  "criteria": {
    "min_salary": 100000,
    "max_salary": 150000,
    "keywords": ["python", "fastapi", "postgresql"],
    "required_keywords": ["python"],
    "location_preference": "remote",
    "experience_level": "senior",
    "company_size_preference": "startup"
  }
}
```

**Response:**
```json
{
  "data": {
    "lead_id": 1,
    "score": 0.85,
    "grade": "A",
    "qualified": true,
    "breakdown": {
      "salary_score": 1.0,
      "keyword_score": 0.8,
      "location_score": 1.0,
      "experience_score": 0.7,
      "company_score": 0.5
    },
    "reasons": [
      "Salary range $120k-$150k matches your preference",
      "Contains 2 of 3 keywords (python, postgresql)",
      "Remote position available",
      "Senior level position"
    ],
    "recommendations": [
      "Strong match - recommend immediate response",
      "Consider mentioning PostgreSQL experience"
    ]
  }
}
```

#### 1.4 Submit Feedback
```http
POST /api/v1/leads/{lead_id}/feedback
```

**Request Body:**
```json
{
  "action": "responded",
  "outcome": "interview_scheduled",
  "feedback_type": "positive",
  "notes": "Great match, scheduled interview for next week",
  "metadata": {
    "response_time_hours": 2,
    "template_used": 5
  }
}
```

**Response:**
```json
{
  "data": {
    "feedback_id": 123,
    "lead_id": 1,
    "reward_applied": 10,
    "learning_updated": true,
    "message": "Thank you for your feedback. The system has learned from this interaction."
  }
}
```

### 2. Scraping Operations

#### 2.1 Create Scraping Job
```http
POST /api/v1/scraper/jobs
```

**Request Body:**
```json
{
  "location_ids": [1, 2, 3],
  "categories": ["gigs", "jobs"],
  "subcategories": ["software", "web"],
  "keywords": ["python", "developer", "remote"],
  "excluded_keywords": ["senior", "lead"],
  "max_pages": 5,
  "max_age_days": 7,
  "priority": "normal",
  "schedule": {
    "type": "immediate",
    "cron": null
  }
}
```

**Response:**
```json
{
  "data": {
    "job_id": "job_123abc",
    "status": "queued",
    "priority": "normal",
    "locations": ["San Francisco", "Los Angeles", "San Diego"],
    "estimated_leads": 150,
    "estimated_time_minutes": 5,
    "created_at": "2024-08-23T10:00:00Z"
  }
}
```

#### 2.2 Get Scraping Job Status
```http
GET /api/v1/scraper/jobs/{job_id}
```

**Response:**
```json
{
  "data": {
    "job_id": "job_123abc",
    "status": "running",
    "progress": 45,
    "leads_found": 67,
    "leads_processed": 65,
    "errors": [],
    "started_at": "2024-08-23T10:00:00Z",
    "estimated_completion": "2024-08-23T10:05:00Z",
    "locations_completed": [1],
    "locations_pending": [2, 3]
  }
}
```

#### 2.3 List Scraping Jobs
```http
GET /api/v1/scraper/jobs
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by status |
| priority | string | No | Filter by priority |
| limit | integer | No | Limit results (default: 20) |

**Response:**
```json
{
  "data": [
    {
      "job_id": "job_123abc",
      "status": "completed",
      "priority": "normal",
      "leads_found": 150,
      "created_at": "2024-08-23T10:00:00Z",
      "completed_at": "2024-08-23T10:05:00Z"
    }
  ]
}
```

#### 2.4 Cancel Scraping Job
```http
DELETE /api/v1/scraper/jobs/{job_id}
```

**Response:**
```json
{
  "data": {
    "job_id": "job_123abc",
    "status": "cancelled",
    "leads_processed": 45,
    "message": "Job cancelled successfully"
  }
}
```

#### 2.5 Get Queue Status
```http
GET /api/v1/scraper/queue/status
```

**Response:**
```json
{
  "data": {
    "queues": {
      "high": 0,
      "normal": 3,
      "low": 5
    },
    "active_jobs": 2,
    "workers": {
      "total": 4,
      "active": 2,
      "idle": 2
    },
    "stats": {
      "jobs_completed_today": 45,
      "leads_scraped_today": 1250,
      "average_job_time_seconds": 180
    }
  }
}
```

### 3. Machine Learning

#### 3.1 Get Predictions
```http
POST /api/v1/ml/predict
```

**Request Body:**
```json
{
  "lead_id": 1,
  "features": {
    "custom_salary_range": [100000, 150000],
    "custom_keywords": ["python", "ai"],
    "user_preferences": {
      "prefer_remote": true,
      "company_size": "startup"
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "predictions": {
      "qualification_score": 0.85,
      "response_probability": 0.72,
      "interview_probability": 0.45,
      "offer_probability": 0.28
    },
    "confidence": 0.89,
    "model_version": "2.0.1",
    "feature_importance": {
      "salary_match": 0.35,
      "keyword_match": 0.25,
      "location_match": 0.20,
      "experience_match": 0.15,
      "company_match": 0.05
    }
  }
}
```

#### 3.2 Train Model with Feedback
```http
POST /api/v1/ml/feedback
```

**Request Body:**
```json
{
  "training_data": [
    {
      "lead_id": 1,
      "action": "qualified_high",
      "outcome": "got_interview",
      "reward": 20
    },
    {
      "lead_id": 2,
      "action": "qualified_low",
      "outcome": "no_response",
      "reward": -5
    }
  ],
  "update_model": true
}
```

**Response:**
```json
{
  "data": {
    "samples_processed": 2,
    "model_updated": true,
    "new_accuracy": 0.87,
    "improvement": 0.02,
    "training_time_ms": 150
  }
}
```

#### 3.3 Get Model Metrics
```http
GET /api/v1/ml/metrics
```

**Response:**
```json
{
  "data": {
    "model_version": "2.0.1",
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89,
    "f1_score": 0.87,
    "training_samples": 5000,
    "last_updated": "2024-08-23T10:00:00Z",
    "performance_trend": [
      {"date": "2024-08-20", "accuracy": 0.83},
      {"date": "2024-08-21", "accuracy": 0.84},
      {"date": "2024-08-22", "accuracy": 0.86},
      {"date": "2024-08-23", "accuracy": 0.87}
    ]
  }
}
```

### 4. Response Management

#### 4.1 Generate Response
```http
POST /api/v1/responses/generate
```

**Request Body:**
```json
{
  "lead_id": 1,
  "template_id": 5,
  "custom_variables": {
    "years_experience": "5",
    "main_skill": "Python",
    "availability": "immediately"
  },
  "tone": "professional",
  "length": "medium"
}
```

**Response:**
```json
{
  "data": {
    "response_id": 456,
    "lead_id": 1,
    "subject": "Re: Senior Python Developer - Experienced Python Developer",
    "body": "Dear Hiring Manager,\n\nI saw your posting...",
    "template_used": 5,
    "variables_replaced": {
      "title": "Senior Python Developer",
      "company": "TechCorp",
      "years_experience": "5"
    },
    "generated_at": "2024-08-23T10:00:00Z",
    "status": "pending_approval"
  }
}
```

#### 4.2 List Response Templates
```http
GET /api/v1/responses/templates
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| category | string | No | Filter by category |
| active_only | boolean | No | Show only active templates |

**Response:**
```json
{
  "data": [
    {
      "id": 5,
      "name": "Technical Role Interest",
      "category": "software_engineering",
      "subject_template": "Re: {{title}} - Experienced {{primary_skill}} Developer",
      "body_template": "Dear {{contact_name|Hiring Manager}},\n\n...",
      "variables": ["title", "contact_name", "primary_skill"],
      "use_count": 145,
      "success_rate": 0.42,
      "avg_response_time_hours": 18,
      "is_active": true
    }
  ]
}
```

#### 4.3 Create Response Template
```http
POST /api/v1/responses/templates
```

**Request Body:**
```json
{
  "name": "Startup Interest",
  "category": "startup",
  "subject_template": "Re: {{title}} - Passionate about {{company}}'s mission",
  "body_template": "Hi {{contact_name}},\n\nI'm excited about...",
  "variables": ["title", "company", "contact_name"],
  "tags": ["startup", "mission-driven"],
  "is_active": true
}
```

**Response:**
```json
{
  "data": {
    "id": 12,
    "name": "Startup Interest",
    "created_at": "2024-08-23T10:00:00Z",
    "message": "Template created successfully"
  }
}
```

### 5. Approval Workflow

#### 5.1 Get Pending Approvals
```http
GET /api/v1/approvals/pending
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| priority | string | No | Filter by priority |
| assignee | string | No | Filter by assignee |

**Response:**
```json
{
  "data": [
    {
      "approval_id": 789,
      "lead_id": 1,
      "response_id": 456,
      "type": "response",
      "priority": "high",
      "content": {
        "subject": "Re: Senior Python Developer",
        "body": "Dear Hiring Manager..."
      },
      "auto_approve_at": "2024-08-23T12:00:00Z",
      "created_at": "2024-08-23T10:00:00Z"
    }
  ]
}
```

#### 5.2 Approve/Reject Response
```http
POST /api/v1/approvals/{approval_id}/review
```

**Request Body:**
```json
{
  "decision": "approved",
  "modifications": {
    "body": "Updated body text..."
  },
  "notes": "Made minor grammar corrections",
  "send_immediately": true
}
```

**Response:**
```json
{
  "data": {
    "approval_id": 789,
    "status": "approved",
    "sent": true,
    "sent_at": "2024-08-23T10:01:00Z",
    "reviewer": "user@example.com"
  }
}
```

### 6. Locations

#### 6.1 List Locations
```http
GET /api/v1/locations
```

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "San Francisco",
      "state": "CA",
      "region": "sfbay",
      "url": "https://sfbay.craigslist.org",
      "is_active": true,
      "lead_count": 1250
    }
  ]
}
```

#### 6.2 Search Locations
```http
GET /api/v1/locations/search
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |
| state | string | No | Filter by state |

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "San Francisco",
      "state": "CA",
      "match_score": 0.95
    }
  ]
}
```

### 7. Analytics

#### 7.1 Get Dashboard Metrics
```http
GET /api/v1/analytics/dashboard
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| period | string | No | Time period (today, week, month) |
| location_id | integer | No | Filter by location |

**Response:**
```json
{
  "data": {
    "summary": {
      "total_leads": 5000,
      "qualified_leads": 1250,
      "responses_sent": 750,
      "interviews_scheduled": 125,
      "offers_received": 25
    },
    "trends": {
      "leads_growth": 0.15,
      "qualification_rate": 0.25,
      "response_rate": 0.42,
      "conversion_rate": 0.033
    },
    "top_locations": [
      {"name": "San Francisco", "leads": 1500},
      {"name": "New York", "leads": 1200},
      {"name": "Austin", "leads": 800}
    ],
    "top_keywords": [
      {"keyword": "python", "count": 450},
      {"keyword": "remote", "count": 380},
      {"keyword": "senior", "count": 290}
    ]
  }
}
```

#### 7.2 Export Data
```http
POST /api/v1/analytics/export
```

**Request Body:**
```json
{
  "format": "csv",
  "data_type": "leads",
  "filters": {
    "date_range": {
      "start": "2024-08-01",
      "end": "2024-08-23"
    },
    "qualified_only": true,
    "min_score": 0.7
  },
  "fields": ["id", "title", "score", "location", "created_at"]
}
```

**Response:**
```json
{
  "data": {
    "export_id": "export_abc123",
    "status": "processing",
    "download_url": null,
    "expires_at": "2024-08-24T10:00:00Z"
  }
}
```

---

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your-jwt-token'
  }));
};
```

### Event Types

#### Lead Events
```javascript
// New lead created
{
  "type": "lead.created",
  "data": {
    "lead_id": 123,
    "title": "Python Developer",
    "location": "San Francisco"
  }
}

// Lead qualified
{
  "type": "lead.qualified",
  "data": {
    "lead_id": 123,
    "score": 0.85,
    "grade": "A"
  }
}

// Response sent
{
  "type": "lead.response_sent",
  "data": {
    "lead_id": 123,
    "response_id": 456,
    "sent_at": "2024-08-23T10:00:00Z"
  }
}
```

#### Scraper Events
```javascript
// Job started
{
  "type": "scraper.job_started",
  "data": {
    "job_id": "job_123",
    "locations": ["San Francisco"]
  }
}

// Progress update
{
  "type": "scraper.progress",
  "data": {
    "job_id": "job_123",
    "progress": 45,
    "leads_found": 67
  }
}

// Job completed
{
  "type": "scraper.job_completed",
  "data": {
    "job_id": "job_123",
    "total_leads": 150,
    "duration_seconds": 300
  }
}
```

---

## Code Examples

### Python (using httpx)
```python
import httpx
import asyncio

class CraigleadsAPI:
    def __init__(self, base_url="http://localhost:8001/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def create_scraping_job(self, locations, keywords):
        response = await self.client.post(
            f"{self.base_url}/scraper/jobs",
            json={
                "location_ids": locations,
                "keywords": keywords,
                "max_pages": 5,
                "priority": "normal"
            }
        )
        return response.json()
    
    async def qualify_lead(self, lead_id, criteria):
        response = await self.client.post(
            f"{self.base_url}/leads/{lead_id}/qualify",
            json={"criteria": criteria}
        )
        return response.json()

# Usage
async def main():
    api = CraigleadsAPI()
    
    # Create scraping job
    job = await api.create_scraping_job([1, 2], ["python", "remote"])
    print(f"Job created: {job['data']['job_id']}")
    
    # Qualify lead
    result = await api.qualify_lead(
        123,
        {"min_salary": 100000, "keywords": ["python"]}
    )
    print(f"Score: {result['data']['score']}")

asyncio.run(main())
```

### JavaScript/TypeScript
```typescript
import axios from 'axios';

class CraigleadsAPI {
  private baseURL: string;
  
  constructor(baseURL = 'http://localhost:8001/api/v1') {
    this.baseURL = baseURL;
  }
  
  async createScrapingJob(
    locationIds: number[],
    keywords: string[]
  ): Promise<any> {
    const response = await axios.post(
      `${this.baseURL}/scraper/jobs`,
      {
        location_ids: locationIds,
        keywords: keywords,
        max_pages: 5,
        priority: 'normal'
      }
    );
    return response.data;
  }
  
  async qualifyLead(
    leadId: number,
    criteria: any
  ): Promise<any> {
    const response = await axios.post(
      `${this.baseURL}/leads/${leadId}/qualify`,
      { criteria }
    );
    return response.data;
  }
}

// Usage
const api = new CraigleadsAPI();

// Create scraping job
api.createScrapingJob([1, 2], ['python', 'remote'])
  .then(result => {
    console.log(`Job created: ${result.data.job_id}`);
  });

// Qualify lead
api.qualifyLead(123, {
  min_salary: 100000,
  keywords: ['python']
}).then(result => {
  console.log(`Score: ${result.data.score}`);
});
```

### cURL Examples
```bash
# Create scraping job
curl -X POST http://localhost:8000/api/v1/scraper/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "location_ids": [1],
    "keywords": ["python", "developer"],
    "max_pages": 5,
    "priority": "normal"
  }'

# Get lead details
curl http://localhost:8000/api/v1/leads/123

# Qualify lead
curl -X POST http://localhost:8000/api/v1/leads/123/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": {
      "min_salary": 100000,
      "keywords": ["python"],
      "location_preference": "remote"
    }
  }'

# Get ML metrics
curl http://localhost:8000/api/v1/ml/metrics
```

---

## Testing the API

### Using Swagger UI
Navigate to `http://localhost:8001/docs` for interactive API documentation.

### Using ReDoc
Navigate to `http://localhost:8001/redoc` for alternative API documentation.

### Postman Collection
Import the following collection for testing:

```json
{
  "info": {
    "name": "Craigleads API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Leads",
      "item": [
        {
          "name": "List Leads",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{base_url}}/leads",
              "host": ["{{base_url}}"],
              "path": ["leads"]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8001/api/v1"
    }
  ]
}
```

---

## Migration Guide

### From v1 to v2

#### Breaking Changes
1. **Lead Model**: Additional fields added
   - Migrate: Run database migration 005_enhanced_lead_fields.py
   
2. **Qualification API**: New endpoint structure
   - Old: `POST /api/v1/leads/qualify`
   - New: `POST /api/v1/leads/{lead_id}/qualify`

3. **Response Format**: Standardized wrapper
   - Old: Direct data response
   - New: `{ "data": {}, "meta": {} }` format

#### New Features
- Machine Learning endpoints
- Response template management
- Approval workflow
- WebSocket support
- Advanced analytics

---

## Support

For API support and questions:
- **Documentation**: http://localhost:8001/docs
- **GitHub Issues**: https://github.com/craigleads/api/issues
- **Email**: api-support@craigleads.com

---

*Last Updated: August 23, 2024*
*API Version: 2.0.0*