# Google Maps Scraper - Quick Integration Guide

This guide walks you through integrating the Google Maps business scraper into your existing lead generation workflow.

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Install Playwright browsers
python -m playwright install chromium

# Verify installation
python -m playwright --version
```

### 2. Update Database Schema

```bash
# Run migration to add 'source' field to leads table
cd /Users/greenmachine2.0/Craigslist/backend
alembic upgrade head
```

### 3. Configure Environment

Add to your `.env` file:

```bash
# Minimum configuration (Playwright mode)
GOOGLE_MAPS_ENABLED=true
GOOGLE_MAPS_MAX_RESULTS=20
GOOGLE_MAPS_ENABLE_EMAIL_EXTRACTION=true
```

### 4. Restart Backend

```bash
# Stop current backend
# Restart with updated code
./start_backend.sh
```

### 5. Test the API

```bash
# Test health check
curl http://localhost:8000/api/v1/google-maps/health

# Start a test scraping job
curl -X POST http://localhost:8000/api/v1/google-maps/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee shops",
    "location": "Seattle, WA",
    "max_results": 5,
    "extract_emails": false
  }'

# Check job status (replace JOB_ID)
curl http://localhost:8000/api/v1/google-maps/status/JOB_ID
```

## Frontend Integration

### 1. Add Google Maps Selector Component

Create `/Users/greenmachine2.0/Craigslist/frontend/src/components/GoogleMapsSelector.tsx`:

```typescript
import React, { useState } from 'react';
import { Card, Form, Input, Button, Switch, InputNumber, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { googleMapsApi } from '../services/googleMapsApi';

export const GoogleMapsSelector: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const response = await googleMapsApi.startScraping({
        query: values.query,
        location: values.location,
        max_results: values.maxResults || 20,
        extract_emails: values.extractEmails || false,
        use_places_api: values.usePlacesApi || false,
      });

      message.success(`Scraping job started! Job ID: ${response.job_id}`);

      // Optionally navigate to job status page
      // navigate(`/google-maps/jobs/${response.job_id}`);

    } catch (error: any) {
      message.error(error.message || 'Failed to start scraping');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Google Maps Business Scraper" className="mb-4">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          maxResults: 20,
          extractEmails: true,
          usePlacesApi: false,
        }}
      >
        <Form.Item
          name="query"
          label="Business Type / Category"
          rules={[{ required: true, message: 'Please enter a search query' }]}
        >
          <Input
            placeholder="e.g., restaurants, dentists, plumbers, coffee shops"
            prefix={<SearchOutlined />}
          />
        </Form.Item>

        <Form.Item
          name="location"
          label="Location"
          rules={[{ required: true, message: 'Please enter a location' }]}
        >
          <Input
            placeholder="e.g., San Francisco, CA or New York, NY"
          />
        </Form.Item>

        <Form.Item
          name="maxResults"
          label="Maximum Results"
          tooltip="Keep at 20 or less to avoid rate limits with Playwright mode"
        >
          <InputNumber min={1} max={100} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="extractEmails"
          label="Extract Emails from Websites"
          valuePropName="checked"
          tooltip="Adds ~5 seconds per business. Success rate: 30-50%"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          name="usePlacesApi"
          label="Use Google Places API"
          valuePropName="checked"
          tooltip="Requires API key. More reliable but costs ~$0.05 per business"
        >
          <Switch />
        </Form.Item>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SearchOutlined />}
          >
            Start Scraping
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

### 2. Create API Service

Create `/Users/greenmachine2.0/Craigslist/frontend/src/services/googleMapsApi.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface GoogleMapsScrapeRequest {
  query: string;
  location: string;
  max_results?: number;
  extract_emails?: boolean;
  use_places_api?: boolean;
  location_id?: number;
}

export interface GoogleMapsScrapeResponse {
  job_id: string;
  status: string;
  message: string;
  estimated_time_seconds: number;
}

export interface GoogleMapsJobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: {
    total: number;
    completed: number;
    current_action: string;
  };
  results_count: number;
  created_at: string;
  completed_at?: string;
  error?: string;
  results?: any[];
}

export const googleMapsApi = {
  async startScraping(request: GoogleMapsScrapeRequest): Promise<GoogleMapsScrapeResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/google-maps/scrape`, request);
    return response.data;
  },

  async getJobStatus(jobId: string, includeResults = false): Promise<GoogleMapsJobStatus> {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/google-maps/status/${jobId}`,
      { params: { include_results: includeResults } }
    );
    return response.data;
  },

  async listJobs(status?: string, limit = 10): Promise<GoogleMapsJobStatus[]> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/google-maps/jobs`, {
      params: { status, limit }
    });
    return response.data;
  },

  async deleteJob(jobId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/api/v1/google-maps/jobs/${jobId}`);
  },

  async healthCheck(): Promise<any> {
    const response = await axios.get(`${API_BASE_URL}/api/v1/google-maps/health`);
    return response.data;
  },
};
```

### 3. Add to Scraper Page

Update `/Users/greenmachine2.0/Craigslist/frontend/src/pages/Scraper.tsx`:

```typescript
import { GoogleMapsSelector } from '../components/GoogleMapsSelector';

// In your component:
<Tabs defaultActiveKey="craigslist">
  <Tabs.TabPane tab="Craigslist" key="craigslist">
    {/* Existing Craigslist scraper */}
  </Tabs.TabPane>

  <Tabs.TabPane tab="Google Maps" key="google-maps">
    <GoogleMapsSelector />
  </Tabs.TabPane>
</Tabs>
```

## Workflow Integration

### Filter Leads by Source

Update your leads API calls to filter by source:

```typescript
// Get only Google Maps leads
const googleLeads = await api.get('/api/v1/leads?source=google_maps');

// Get all leads
const allLeads = await api.get('/api/v1/leads');

// Get non-Craigslist leads
const otherLeads = await api.get('/api/v1/leads?source_not=craigslist');
```

### Update Lead Display

Show source badge in lead cards:

```typescript
const getSourceBadge = (source: string) => {
  switch (source) {
    case 'google_maps':
      return <Tag color="blue">Google Maps</Tag>;
    case 'google_places_api':
      return <Tag color="green">Places API</Tag>;
    case 'craigslist':
      return <Tag color="orange">Craigslist</Tag>;
    default:
      return <Tag>{source}</Tag>;
  }
};

// In your lead card:
<div>
  {getSourceBadge(lead.source)}
  <h3>{lead.title}</h3>
</div>
```

### Analytics by Source

Track conversion rates by source:

```typescript
const analyticsBySource = await api.get('/api/v1/analytics/by-source');

// Returns:
// [
//   { source: 'craigslist', total: 1234, qualified: 567, conversion_rate: 0.46 },
//   { source: 'google_maps', total: 456, qualified: 234, conversion_rate: 0.51 },
// ]
```

## Production Checklist

Before deploying to production:

- [ ] Set up Google Places API key (recommended)
- [ ] Configure Hunter.io or RocketReach for email finding
- [ ] Set appropriate rate limits in config
- [ ] Enable monitoring/logging
- [ ] Test error handling (rate limits, CAPTCHAs)
- [ ] Set up scheduled scraping (optional)
- [ ] Configure proxy rotation (optional)
- [ ] Test with real-world queries
- [ ] Monitor costs (Places API + email finders)
- [ ] Set up alerts for quota limits

## Cost Management

### Monitor API Usage

```python
# Track Google Places API costs
from app.models.leads import Lead
from sqlalchemy import func

# Count leads by source this month
google_api_leads = session.query(func.count(Lead.id)).filter(
    Lead.source == 'google_places_api',
    Lead.scraped_at >= start_of_month
).scalar()

estimated_cost = google_api_leads * 0.049  # $0.049 per business
print(f"This month's Places API cost: ${estimated_cost:.2f}")
```

### Set Quota Limits

Add to your configuration:

```python
# In config.py
GOOGLE_MAPS_DAILY_QUOTA = 100  # Max businesses per day
GOOGLE_MAPS_MONTHLY_BUDGET = 100.00  # Max $ per month
```

Implement quota checking:

```python
# In google_maps.py endpoint
async def check_quota(db: AsyncSession):
    today_count = await db.execute(
        select(func.count(Lead.id)).where(
            and_(
                Lead.source.in_(['google_maps', 'google_places_api']),
                Lead.scraped_at >= datetime.now().replace(hour=0, minute=0)
            )
        )
    )
    count = today_count.scalar()

    if count >= settings.GOOGLE_MAPS_DAILY_QUOTA:
        raise HTTPException(
            status_code=429,
            detail=f"Daily quota exceeded ({count}/{settings.GOOGLE_MAPS_DAILY_QUOTA})"
        )
```

## Troubleshooting

### Common Issues

1. **Playwright browser not found**
   ```bash
   python -m playwright install chromium
   ```

2. **Rate limited by Google**
   - Reduce max_results to 10-20
   - Increase delays (5-10 seconds)
   - Use Places API instead

3. **No emails found**
   - Normal - many businesses don't list emails
   - Consider Hunter.io/RocketReach
   - Use phone numbers instead

4. **Job stuck in running**
   - Increase GOOGLE_MAPS_SCRAPE_TIMEOUT
   - Check backend logs
   - Delete job and retry

### Debugging

Enable debug logging:

```python
# In config.py
LOG_LEVEL = "DEBUG"

# Or via environment
LOG_LEVEL=DEBUG python app/main.py
```

Check scraper logs:

```bash
tail -f backend/logs/google_maps_scraper.log
```

## Next Steps

1. **Add more sources**: LinkedIn, Indeed, Monster (Phase 2 continuation)
2. **Email enrichment**: Integrate Hunter.io, RocketReach
3. **Scheduled scraping**: Run daily/weekly for fresh leads
4. **Advanced filtering**: Category-specific qualifications
5. **Duplicate detection**: Cross-source deduplication
6. **Export features**: CSV/JSON exports by source

## Support

For issues or questions:
- Check logs: `backend/logs/`
- Review API docs: `http://localhost:8000/docs`
- Test with script: `python test_google_maps_scraper.py`

---

**Last Updated**: November 4, 2025
