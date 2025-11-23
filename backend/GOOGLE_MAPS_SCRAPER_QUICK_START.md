# Google Maps Scraper - Quick Start Guide

## Installation

Playwright is already installed. If you need to reinstall the browser:

```bash
cd /Users/greenmachine2.0/Craigslist/backend
source venv/bin/activate
playwright install chromium
```

## Basic Usage

### Method 1: Async Context Manager (Recommended)

```python
from app.scrapers.google_maps_scraper import GoogleMapsScraper

async def search_businesses():
    async with GoogleMapsScraper(headless=True) as scraper:
        businesses = await scraper.search_businesses(
            query="restaurants",
            location="New York, NY",
            max_results=20
        )

        for business in businesses:
            print(f"{business['name']}: {business['rating']} stars")
            print(f"Address: {business['address']}")
            print(f"Phone: {business['phone']}")
            print(f"Website: {business['website']}")
            print()

        return businesses

# Run the async function
import asyncio
results = asyncio.run(search_businesses())
```

### Method 2: Manual Start/Close

```python
from app.scrapers.google_maps_scraper import GoogleMapsScraper

scraper = GoogleMapsScraper(headless=True)

try:
    await scraper.start()

    businesses = await scraper.search_businesses(
        query="coffee shops",
        location="San Francisco, CA",
        max_results=10
    )

    print(f"Found {len(businesses)} businesses")

finally:
    await scraper.close()
```

## Configuration Options

```python
scraper = GoogleMapsScraper(
    headless=True,                      # Run in headless mode (no browser window)
    proxy=None,                         # Optional proxy: "http://host:port"
    user_agent=None,                    # Custom user agent (default: random)
    enable_email_extraction=False,      # Extract emails from websites (slower)
    screenshots_on_error=True           # Take screenshots when errors occur
)
```

## Running the Test Script

```bash
cd /Users/greenmachine2.0/Craigslist/backend
source venv/bin/activate
python test_scraper_simple.py
```

## Expected Output

```
================================================================================
GOOGLE MAPS SCRAPER TEST (Playwright Edition)
================================================================================

Test Parameters:
  Query: coffee shops
  Location: San Francisco, CA
  Max Results: 10

--------------------------------------------------------------------------------

RESULTS: Found 10 businesses

1. The Coffee Berry SF
   Rating: 4.9 (478 reviews)
   Category: Coffee shop
   Address: 1410 Lombard St, San Francisco, CA 94123
   Phone: (415) 800-7073
   Website: http://thecoffeeberrysf.com/

...

SUMMARY:
  Total businesses: 10
  With ratings: 10
  With phone: 9
  With website: 10
  With address: 10

TEST COMPLETED SUCCESSFULLY!
```

## Data Structure

Each business is returned as a dictionary with the following fields:

```python
{
    'name': 'The Coffee Berry SF',
    'address': '1410 Lombard St, San Francisco, CA 94123',
    'phone': '(415) 800-7073',
    'website': 'http://thecoffeeberrysf.com/',
    'rating': 4.9,
    'review_count': 478,
    'category': 'Coffee shop',
    'price_level': None,  # May be None if not available
    'google_maps_url': 'https://www.google.com/maps/place/...',
    'scraped_at': datetime(2025, 11, 5, 15, 27, 34),
    'source': 'google_maps_playwright',
    'search_query': 'coffee shops',
    'search_location': 'San Francisco, CA'
}
```

## Common Use Cases

### 1. Search for Local Businesses

```python
async with GoogleMapsScraper() as scraper:
    plumbers = await scraper.search_businesses(
        query="plumbers",
        location="Boston, MA",
        max_results=50
    )
```

### 2. Extract Restaurants in an Area

```python
async with GoogleMapsScraper() as scraper:
    restaurants = await scraper.search_businesses(
        query="italian restaurants",
        location="Chicago, IL",
        max_results=30
    )
```

### 3. Get Business Contact Information

```python
async with GoogleMapsScraper(enable_email_extraction=True) as scraper:
    businesses = await scraper.search_businesses(
        query="dental clinics",
        location="Seattle, WA",
        max_results=20
    )

    # Filter businesses with phone numbers
    with_phone = [b for b in businesses if b.get('phone')]
    print(f"Found {len(with_phone)} businesses with phone numbers")
```

### 4. Save Results to CSV

```python
import csv
from datetime import datetime

async with GoogleMapsScraper() as scraper:
    businesses = await scraper.search_businesses(
        query="hair salons",
        location="Austin, TX",
        max_results=50
    )

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"businesses_{timestamp}.csv"

    with open(filename, 'w', newline='') as f:
        if businesses:
            writer = csv.DictWriter(f, fieldnames=businesses[0].keys())
            writer.writeheader()
            writer.writerows(businesses)

    print(f"Saved {len(businesses)} businesses to {filename}")
```

## Error Handling

```python
from playwright.async_api import TimeoutError as PlaywrightTimeout

async with GoogleMapsScraper() as scraper:
    try:
        businesses = await scraper.search_businesses(
            query="dentists",
            location="Miami, FL",
            max_results=25
        )

        if not businesses:
            print("No results found or scraping failed")
        else:
            print(f"Successfully scraped {len(businesses)} businesses")

    except PlaywrightTimeout:
        print("Timeout occurred while loading page")
    except Exception as e:
        print(f"Error: {str(e)}")
        # Check /tmp/google_maps_*.png for debug screenshots
```

## Performance Tips

1. **Batch Requests:** Process multiple locations sequentially in the same browser session
2. **Adjust Delays:** Reduce `min_delay` and `max_delay` in config for faster scraping (but higher risk)
3. **Limit Results:** Request only what you need to reduce scraping time
4. **Use Headless Mode:** Always use `headless=True` for production (faster)

## Troubleshooting

### No Results Found

**Possible causes:**
- Google detected automation
- Network issues
- Selector changes

**Solutions:**
1. Check `/tmp/google_maps_*.png` for screenshots
2. Try with `headless=False` to see browser
3. Add proxy if IP is blocked
4. Increase delays between requests

### Rate Limited

**Symptoms:** Empty results or CAPTCHA

**Solutions:**
1. Add delays between searches
2. Use proxy rotation
3. Reduce max_results
4. Wait before retrying

### Incomplete Data

**Normal behavior:** Not all businesses have all fields

**To improve:**
1. Enable `enable_email_extraction=True` for emails
2. Some businesses don't list phone/website publicly
3. Data completeness varies by business type

## Integration with Existing Code

### With FastAPI Endpoint

```python
from fastapi import APIRouter
from app.scrapers.google_maps_scraper import GoogleMapsScraper

router = APIRouter()

@router.post("/scrape/google-maps")
async def scrape_google_maps(
    query: str,
    location: str,
    max_results: int = 20
):
    async with GoogleMapsScraper(headless=True) as scraper:
        businesses = await scraper.search_businesses(
            query=query,
            location=location,
            max_results=max_results
        )

        return {
            "success": True,
            "count": len(businesses),
            "businesses": businesses
        }
```

### With Database Storage

```python
from app.models.leads import Lead
from app.core.database import get_db

async with GoogleMapsScraper() as scraper:
    businesses = await scraper.search_businesses(
        query="lawyers",
        location="Dallas, TX",
        max_results=30
    )

    # Save to database
    db = next(get_db())
    for business in businesses:
        lead = Lead(
            name=business['name'],
            email=business.get('email'),
            phone=business.get('phone'),
            website=business.get('website'),
            source='google_maps',
            metadata=business
        )
        db.add(lead)

    db.commit()
    print(f"Saved {len(businesses)} leads to database")
```

## Monitoring

### Check Logs

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async with GoogleMapsScraper() as scraper:
    businesses = await scraper.search_businesses(
        query="gyms",
        location="Phoenix, AZ",
        max_results=15
    )
```

### Track Success Rates

```python
from collections import Counter

async with GoogleMapsScraper() as scraper:
    businesses = await scraper.search_businesses(
        query="dentists",
        location="Denver, CO",
        max_results=50
    )

    # Analyze data completeness
    completeness = {
        'name': sum(1 for b in businesses if b.get('name')),
        'phone': sum(1 for b in businesses if b.get('phone')),
        'website': sum(1 for b in businesses if b.get('website')),
        'address': sum(1 for b in businesses if b.get('address')),
        'rating': sum(1 for b in businesses if b.get('rating')),
    }

    print(f"Data completeness out of {len(businesses)} businesses:")
    for field, count in completeness.items():
        percentage = (count / len(businesses) * 100) if businesses else 0
        print(f"  {field}: {count} ({percentage:.1f}%)")
```

## Next Steps

1. **Test with your use case:** Try different queries and locations
2. **Monitor performance:** Track success rates and data quality
3. **Integrate with your workflow:** Add to existing pipelines
4. **Set up monitoring:** Track for selector changes and errors
5. **Consider alternatives:** Evaluate Google Places API for production

## Support

- **Implementation:** `/Users/greenmachine2.0/Craigslist/backend/app/scrapers/google_maps_scraper.py`
- **Tests:** `/Users/greenmachine2.0/Craigslist/backend/test_scraper_simple.py`
- **Debug Tool:** `/Users/greenmachine2.0/Craigslist/backend/test_scraper_debug_headless.py`
- **Documentation:** `GOOGLE_MAPS_SCRAPER_IMPLEMENTATION_SUMMARY.md`
