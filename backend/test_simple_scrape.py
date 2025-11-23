#!/usr/bin/env python3
"""
Simple test to verify scraping works without keywords.
"""

import asyncio
from app.scrapers.craigslist_scraper import CraigslistScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple_scrape():
    """Test basic scraping without keywords to get more results."""
    print("\n" + "="*60)
    print("SIMPLE SCRAPING TEST")
    print("="*60)
    
    try:
        async with CraigslistScraper(enable_email_extraction=False) as scraper:
            # Test with San Francisco Bay Area - gigs without keywords
            location_url = "https://sfbay.craigslist.org"
            categories = ["gigs"]  # Using gigs category
            keywords = None  # No keywords for broader results
            max_pages = 1  # Just 1 page
            
            print(f"\nScraping Configuration:")
            print(f"  Location: San Francisco Bay Area")
            print(f"  URL: {location_url}")
            print(f"  Categories: {categories}")
            print(f"  Keywords: None (all gigs)")
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
                print("\nFirst 5 leads:")
                for i, lead in enumerate(leads[:5], 1):
                    print(f"\n  Lead #{i}:")
                    print(f"    ID: {lead.get('craigslist_id')}")
                    print(f"    Title: {lead.get('title')[:80] if lead.get('title') else 'No title'}...")
                    print(f"    URL: {lead.get('url')}")
                    print(f"    Price: ${lead.get('price')}" if lead.get('price') else "    Price: Not specified")
                    
                return True
            else:
                print("\n⚠️ No leads found.")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Test failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_scrape())
    exit(0 if success else 1)