# CAPTCHA Integration and Email Extraction Guide

## Overview

This implementation adds 2captcha integration to the Craigslist scraper for handling CAPTCHA challenges during email extraction. The system can automatically solve reCAPTCHA v2, hCAPTCHA, and image-based CAPTCHAs.

## Features

- **Multiple CAPTCHA Types**: Supports reCAPTCHA v2, hCAPTCHA, and image CAPTCHAs
- **Email Extraction**: Automatically extracts email addresses from job postings
- **Cost Tracking**: Monitors CAPTCHA solving costs
- **Retry Logic**: Automatic retry for failed CAPTCHA attempts
- **Batch Processing**: Concurrent email extraction with rate limiting
- **Database Integration**: Stores extracted emails in the leads table

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following new package has been added:
- `2captcha-python==1.1.3`

### 2. Get 2captcha API Key

1. Sign up at [2captcha.com](https://2captcha.com/)
2. Add funds to your account (typical costs: $0.001-$0.002 per CAPTCHA)
3. Get your API key from the dashboard

### 3. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Update your `.env` file with:
```env
# CAPTCHA Settings
TWOCAPTCHA_API_KEY=your_2captcha_api_key_here
ENABLE_EMAIL_EXTRACTION=true
EMAIL_EXTRACTION_MAX_CONCURRENT=2
CAPTCHA_TIMEOUT=120
CAPTCHA_MAX_RETRIES=3
```

## Usage

### API Usage

Create a scraping job with email extraction:

```bash
curl -X POST "http://localhost:8000/api/v1/scraper/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "location_ids": [1, 2],
    "categories": ["jobs/acc", "jobs/eng"],
    "keywords": ["developer", "engineer"],
    "max_pages": 3,
    "enable_email_extraction": true,
    "captcha_api_key": "your_2captcha_api_key"
  }'
```

### Direct Scraper Usage

```python
from app.scrapers.craigslist_scraper import CraigslistScraper

# With email extraction
async with CraigslistScraper(
    captcha_api_key="your_2captcha_api_key",
    enable_email_extraction=True
) as scraper:
    leads = await scraper.scrape_location_with_emails(
        location_url="https://sfbay.craigslist.org",
        categories=["jobs/eng"],
        keywords=["python", "developer"],
        max_pages=2
    )
    
    # Check costs
    total_cost = scraper.get_captcha_cost()
    print(f"CAPTCHA solving cost: ${total_cost:.4f}")
```

### Email Extraction Only

```python
from app.scrapers.captcha_solver import CaptchaSolver
from app.scrapers.email_extractor import EmailExtractor

# Initialize components
captcha_solver = CaptchaSolver("your_2captcha_api_key")
email_extractor = EmailExtractor(captcha_solver)

# Extract email from specific listing
async with scraper:
    email = await email_extractor.extract_email_from_listing(
        page=scraper.page,
        listing_url="https://sfbay.craigslist.org/job/123456789.html"
    )
    print(f"Extracted email: {email}")
```

## Architecture

### Components

1. **CaptchaSolver** (`app/scrapers/captcha_solver.py`)
   - Handles 2captcha API integration
   - Supports multiple CAPTCHA types
   - Tracks costs and provides retry logic

2. **EmailExtractor** (`app/scrapers/email_extractor.py`)
   - Extracts emails from Craigslist listings
   - Handles "reply" buttons and forms
   - Integrates with CAPTCHA solver

3. **CraigslistScraper** (`app/scrapers/craigslist_scraper.py`)
   - Updated to support email extraction
   - Batch processing capabilities
   - Cost tracking integration

### Database Schema

The `leads` table already includes an `email` field:

```sql
email VARCHAR(255) NULL INDEX
```

### API Endpoints

New fields added to scraping job models:

- `enable_email_extraction`: Enable/disable email extraction
- `captcha_api_key`: Optional override for CAPTCHA API key
- `emails_extracted`: Count of extracted emails
- `captcha_cost`: Total cost of CAPTCHA solving

## Email Extraction Workflow

1. **Navigate to listing page**
2. **Check for direct email** (in page content, mailto links)
3. **Find reply mechanism** (button or link)
4. **Click reply button/navigate to reply page**
5. **Detect CAPTCHA presence**
6. **Solve CAPTCHA** if present:
   - Submit to 2captcha
   - Wait for solution
   - Inject solution into page
   - Submit form
7. **Extract revealed email address**
8. **Store in database**

## CAPTCHA Types Supported

### reCAPTCHA v2
- Standard checkbox CAPTCHA
- Invisible reCAPTCHA
- Image selection challenges
- Cost: ~$0.002 per solve

### hCAPTCHA
- Similar to reCAPTCHA v2
- Image selection challenges
- Cost: ~$0.002 per solve

### Image CAPTCHA
- Text-based image CAPTCHAs
- Distorted text recognition
- Cost: ~$0.001 per solve

## Error Handling

The system includes comprehensive error handling:

- **CAPTCHA solving failures**: Automatic retry with exponential backoff
- **Missing reply elements**: Graceful degradation
- **Network timeouts**: Configurable timeouts with retries
- **Rate limiting**: Built-in delays and concurrency controls
- **Cost monitoring**: Automatic cost tracking and limits

## Cost Management

### Typical Costs (as of 2024)
- Image CAPTCHA: $0.001 per solve
- reCAPTCHA v2: $0.002 per solve
- hCAPTCHA: $0.002 per solve

### Cost Tracking
```python
# Check current session costs
cost = scraper.get_captcha_cost()
print(f"Session cost: ${cost:.4f}")

# Reset cost tracking
scraper.reset_captcha_cost()
```

### Budget Controls
Set environment variables to control spending:
```env
MAX_CAPTCHA_COST_PER_JOB=1.00
CAPTCHA_BUDGET_WARNING_THRESHOLD=0.50
```

## Performance Considerations

- **Concurrency**: Max 2 concurrent email extractions by default
- **Rate Limiting**: Built-in delays between requests
- **Timeouts**: 30-second timeout per email extraction
- **Batch Processing**: Process multiple leads efficiently

## Monitoring and Logging

Enable detailed logging:
```env
LOG_LEVEL=INFO
```

Key log messages:
- CAPTCHA detection and solving
- Email extraction attempts
- Cost tracking updates
- Error conditions

## Testing

Run the integration test:
```bash
python test_captcha_integration.py
```

This tests:
- Component initialization
- Configuration loading
- Dependency availability
- Basic functionality

## Troubleshooting

### Common Issues

1. **"2captcha API key not provided"**
   - Set `TWOCAPTCHA_API_KEY` in environment
   - Or pass `captcha_api_key` parameter

2. **"CAPTCHA solving timeout"**
   - Increase `CAPTCHA_TIMEOUT` setting
   - Check 2captcha service status

3. **"Email extraction failed"**
   - Check if listing has reply mechanism
   - Verify CAPTCHA solving is working
   - Check for rate limiting

4. **High CAPTCHA costs**
   - Reduce `EMAIL_EXTRACTION_MAX_CONCURRENT`
   - Implement cost limits
   - Monitor usage patterns

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

This provides detailed information about:
- CAPTCHA detection process
- Email extraction steps
- API communication
- Cost calculations

## Security Considerations

- **API Key Protection**: Store API keys securely
- **Rate Limiting**: Respect Craigslist's rate limits
- **User Agent**: Use realistic user agents
- **Session Management**: Implement proper session handling

## Future Enhancements

Potential improvements:
- Support for additional CAPTCHA types
- Machine learning for email pattern recognition
- Advanced cost optimization
- Real-time cost monitoring dashboard
- Email validation and verification