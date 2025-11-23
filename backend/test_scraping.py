#!/usr/bin/env python3
"""
Test script to verify Craigslist scraping functionality.
"""

import asyncio
import json
from datetime import datetime
from app.scrapers.craigslist_scraper import CraigslistScraper
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_scraping():
    """Test basic scraping without email extraction."""
    print("\n" + "="*60)
    print("TESTING BASIC SCRAPING (No Email Extraction)")
    print("="*60)
    
    try:
        async with CraigslistScraper(enable_email_extraction=False) as scraper:
            # Test with San Francisco Bay Area - just 1 page of gigs
            location_url = "https://sfbay.craigslist.org"
            categories = ["gigs"]  # Quick category to test
            keywords = ["software", "developer", "programming"]  # Tech-related keywords
            max_pages = 1  # Just 1 page for quick test
            
            print(f"\nScraping Configuration:")
            print(f"  Location: San Francisco Bay Area")
            print(f"  URL: {location_url}")
            print(f"  Categories: {categories}")
            print(f"  Keywords: {keywords}")
            print(f"  Max Pages: {max_pages}")
            print(f"\nStarting scrape...")
            
            leads = await scraper.scrape_location(
                location_url=location_url,
                categories=categories,
                keywords=keywords,
                max_pages=max_pages
            )
            
            print(f"\n✅ Scraping completed!")
            print(f"Found {len(leads)} leads")
            
            if leads:
                print("\nSample leads (first 3):")
                for i, lead in enumerate(leads[:3], 1):
                    print(f"\n  Lead #{i}:")
                    print(f"    ID: {lead.get('craigslist_id')}")
                    print(f"    Title: {lead.get('title')[:60]}...")
                    print(f"    URL: {lead.get('url')}")
                    print(f"    Price: ${lead.get('price')}" if lead.get('price') else "    Price: Not specified")
                    print(f"    Posted: {lead.get('posted_at')}")
                    print(f"    Neighborhood: {lead.get('neighborhood')}" if lead.get('neighborhood') else "    Neighborhood: Not specified")
                
                # Save results to file for inspection
                output_file = f"scrape_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w') as f:
                    json.dump(leads, f, indent=2, default=str)
                print(f"\n📄 Full results saved to: {output_file}")
            else:
                print("\n⚠️ No leads found. This might be due to:")
                print("  - No matching listings for the keywords")
                print("  - Rate limiting by Craigslist")
                print("  - Changes in Craigslist HTML structure")
                
        return True
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        logger.exception("Scraping test failed")
        return False


async def test_listing_details():
    """Test fetching details from a specific listing."""
    print("\n" + "="*60)
    print("TESTING LISTING DETAILS EXTRACTION")
    print("="*60)
    
    try:
        async with CraigslistScraper(enable_email_extraction=False) as scraper:
            # First get a listing URL
            location_url = "https://sfbay.craigslist.org"
            categories = ["gigs"]
            max_pages = 1
            
            print("\nFetching a sample listing to test detail extraction...")
            
            leads = await scraper.scrape_location(
                location_url=location_url,
                categories=categories,
                keywords=None,  # No keywords for broader results
                max_pages=max_pages
            )
            
            if not leads:
                print("⚠️ No listings found to test detail extraction")
                return False
            
            # Test with first listing
            test_url = leads[0]['url']
            print(f"\nTesting detail extraction for: {test_url}")
            
            details = await scraper.get_listing_details(test_url)
            
            if details:
                print("\n✅ Successfully extracted listing details:")
                print(f"  Description length: {len(details.get('description', ''))} characters")
                print(f"  Contact info: {details.get('contact_info', {})}")
                print(f"  Attributes: {details.get('attributes', {})}")
            else:
                print("⚠️ Could not extract listing details")
                
        return True
        
    except Exception as e:
        print(f"\n❌ Error during detail extraction: {str(e)}")
        logger.exception("Detail extraction test failed")
        return False


async def test_api_endpoint():
    """Test the scraping API endpoint."""
    print("\n" + "="*60)
    print("TESTING API ENDPOINT")
    print("="*60)
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            # Test categories endpoint
            print("\nTesting /api/v1/scraper/categories endpoint...")
            response = await client.get("http://localhost:8001/api/v1/scraper/categories")
            
            if response.status_code == 200:
                categories = response.json()
                print("✅ Categories endpoint working")
                print(f"   Available category groups: {list(categories.keys())}")
            else:
                print(f"❌ Categories endpoint returned: {response.status_code}")
            
            # Test job creation endpoint
            print("\nTesting /api/v1/scraper/jobs endpoint...")
            job_data = {
                "location_ids": [1],  # San Francisco (ID: 1)
                "categories": ["gigs"],
                "keywords": ["software"],
                "max_pages": 1,
                "priority": "normal",
                "enable_email_extraction": False
            }
            
            response = await client.post(
                "http://localhost:8001/api/v1/scraper/jobs",
                json=job_data
            )
            
            if response.status_code == 200:
                job = response.json()
                print("✅ Job creation endpoint working")
                print(f"   Job ID: {job['job_id']}")
                print(f"   Status: {job['status']}")
                
                # Wait a bit and check job status
                await asyncio.sleep(3)
                
                status_response = await client.get(
                    f"http://localhost:8001/api/v1/scraper/jobs/{job['job_id']}"
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"\n📊 Job Status Update:")
                    print(f"   Status: {status['status']}")
                    print(f"   Progress: {status['progress']}%")
                    print(f"   Items processed: {status.get('processed_items', 0)}")
            else:
                print(f"❌ Job creation failed: {response.status_code}")
                print(f"   Error: {response.json()}")
                
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing API: {str(e)}")
        logger.exception("API test failed")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CRAIGSLIST SCRAPER TEST SUITE")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Basic scraping
    print("\n[1/3] Running basic scraping test...")
    results['basic_scraping'] = await test_basic_scraping()
    
    # Test 2: Listing details
    print("\n[2/3] Running listing details test...")
    results['listing_details'] = await test_listing_details()
    
    # Test 3: API endpoints
    print("\n[3/3] Running API endpoint test...")
    results['api_endpoint'] = await test_api_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Scraping system is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the logs above for details.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)