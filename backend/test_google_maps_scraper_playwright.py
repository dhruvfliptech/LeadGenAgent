"""
Test script for the Playwright-based Google Maps scraper.

This script tests the scraper with a simple search query and displays the results.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.scrapers.google_maps_scraper import GoogleMapsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scraper():
    """Test the Google Maps scraper with a sample search."""

    print("\n" + "="*80)
    print("GOOGLE MAPS SCRAPER TEST (Playwright Edition)")
    print("="*80 + "\n")

    # Test parameters
    query = "coffee shops"
    location = "San Francisco, CA"
    max_results = 10

    print(f"Test Parameters:")
    print(f"  Query: {query}")
    print(f"  Location: {location}")
    print(f"  Max Results: {max_results}")
    print(f"\n{'-'*80}\n")

    try:
        # Initialize scraper
        async with GoogleMapsScraper(
            headless=True,  # Run in headless mode
            screenshots_on_error=True
        ) as scraper:

            print("Scraper initialized successfully!")
            print("Starting search...\n")

            # Search for businesses
            businesses = await scraper.search_businesses(
                query=query,
                location=location,
                max_results=max_results
            )

            # Display results
            print(f"\n{'-'*80}\n")
            print(f"RESULTS: Found {len(businesses)} businesses\n")
            print("="*80 + "\n")

            if not businesses:
                print("No businesses found. This might be due to:")
                print("  - Google detecting automated access")
                print("  - Network issues")
                print("  - Changes in Google Maps HTML structure")
                print("\nCheck the logs above for more details.")
                return

            for idx, business in enumerate(businesses, 1):
                print(f"{idx}. {business.get('name', 'N/A')}")
                print(f"   Rating: {business.get('rating', 'N/A')} ({business.get('review_count', 0)} reviews)")
                print(f"   Category: {business.get('category', 'N/A')}")
                print(f"   Address: {business.get('address', 'N/A')}")
                print(f"   Phone: {business.get('phone', 'N/A')}")
                print(f"   Website: {business.get('website', 'N/A')}")
                print(f"   Price Level: {business.get('price_level', 'N/A')}")
                print(f"   Google Maps URL: {business.get('google_maps_url', 'N/A')}")
                print(f"   Source: {business.get('source', 'N/A')}")
                print(f"   Scraped At: {business.get('scraped_at', 'N/A')}")
                print()

            # Summary
            print("="*80)
            print(f"\nSUMMARY:")
            print(f"  Total businesses extracted: {len(businesses)}")
            print(f"  Businesses with ratings: {sum(1 for b in businesses if b.get('rating'))}")
            print(f"  Businesses with phone: {sum(1 for b in businesses if b.get('phone'))}")
            print(f"  Businesses with website: {sum(1 for b in businesses if b.get('website'))}")
            print(f"  Businesses with address: {sum(1 for b in businesses if b.get('address'))}")

            print("\n" + "="*80)
            print("TEST COMPLETED SUCCESSFULLY!")
            print("="*80 + "\n")

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR: {str(e)}")
        print(f"{'='*80}\n")
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    print("\nStarting Google Maps Scraper Test...")
    print("This may take 30-60 seconds depending on the number of results.\n")

    try:
        asyncio.run(test_scraper())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        sys.exit(1)
