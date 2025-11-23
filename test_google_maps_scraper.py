#!/usr/bin/env python3
"""
Test script for Google Maps Business Scraper

Usage:
    python test_google_maps_scraper.py --mode playwright --query "coffee shops" --location "Seattle, WA"
    python test_google_maps_scraper.py --mode api --query "dentists" --location "New York, NY"
"""

import asyncio
import argparse
import sys
import os
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.scrapers.google_maps_scraper import GoogleMapsScraper, GooglePlacesAPIScraper
from app.core.config import settings


async def test_playwright_scraper(
    query: str,
    location: str,
    max_results: int = 5,
    extract_emails: bool = False
):
    """Test the Playwright-based scraper."""
    print(f"\n{'='*60}")
    print(f"Testing Playwright Scraper")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Location: {location}")
    print(f"Max Results: {max_results}")
    print(f"Extract Emails: {extract_emails}")
    print(f"{'='*60}\n")

    try:
        async with GoogleMapsScraper(
            headless=True,
            enable_email_extraction=extract_emails
        ) as scraper:
            print("Starting scraper...")

            businesses = await scraper.search_businesses(
                query=query,
                location=location,
                max_results=max_results
            )

            print(f"\n{'='*60}")
            print(f"Results: {len(businesses)} businesses found")
            print(f"{'='*60}\n")

            for idx, business in enumerate(businesses, 1):
                print(f"\n--- Business #{idx} ---")
                print(f"Name: {business.get('name')}")
                print(f"Rating: {business.get('rating')} ({business.get('review_count')} reviews)")
                print(f"Category: {business.get('category')}")
                print(f"Phone: {business.get('phone')}")
                print(f"Website: {business.get('website')}")
                print(f"Email: {business.get('email')}")
                print(f"Address: {business.get('address')}")
                print(f"Google Maps URL: {business.get('google_maps_url')}")
                print(f"Business Hours: {business.get('business_hours')}")

            return businesses

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def test_places_api_scraper(
    query: str,
    location: str,
    max_results: int = 5,
    api_key: Optional[str] = None
):
    """Test the Google Places API scraper."""
    print(f"\n{'='*60}")
    print(f"Testing Google Places API Scraper")
    print(f"{'='*60}")
    print(f"Query: {query}")
    print(f"Location: {location}")
    print(f"Max Results: {max_results}")
    print(f"{'='*60}\n")

    # Get API key
    if not api_key:
        api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)

    if not api_key:
        print("ERROR: No Google Places API key found!")
        print("Set GOOGLE_PLACES_API_KEY in your .env file or pass --api-key")
        return []

    print(f"API Key: {api_key[:10]}...{api_key[-4:]}\n")

    try:
        async with GooglePlacesAPIScraper(api_key=api_key) as scraper:
            print("Starting Places API search...")

            businesses = await scraper.search_businesses(
                query=query,
                location=location,
                max_results=max_results
            )

            print(f"\n{'='*60}")
            print(f"Results: {len(businesses)} businesses found")
            print(f"{'='*60}\n")

            for idx, business in enumerate(businesses, 1):
                print(f"\n--- Business #{idx} ---")
                print(f"Name: {business.get('name')}")
                print(f"Rating: {business.get('rating')} ({business.get('review_count')} reviews)")
                print(f"Category: {business.get('category')}")
                print(f"Phone: {business.get('phone')}")
                print(f"Website: {business.get('website')}")
                print(f"Address: {business.get('address')}")
                print(f"Coordinates: {business.get('latitude')}, {business.get('longitude')}")
                print(f"Place ID: {business.get('place_id')}")
                print(f"Google Maps URL: {business.get('google_maps_url')}")
                print(f"Business Hours: {business.get('business_hours')}")

            return businesses

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description='Test Google Maps Business Scraper')

    parser.add_argument(
        '--mode',
        choices=['playwright', 'api', 'both'],
        default='playwright',
        help='Scraper mode to test'
    )

    parser.add_argument(
        '--query',
        type=str,
        default='coffee shops',
        help='Search query (e.g., "restaurants", "dentists")'
    )

    parser.add_argument(
        '--location',
        type=str,
        default='Seattle, WA',
        help='Location to search (e.g., "San Francisco, CA")'
    )

    parser.add_argument(
        '--max-results',
        type=int,
        default=5,
        help='Maximum number of results to scrape'
    )

    parser.add_argument(
        '--extract-emails',
        action='store_true',
        help='Extract emails from business websites (Playwright mode only)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        help='Google Places API key (for API mode)'
    )

    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"# Google Maps Business Scraper Test Suite")
    print(f"{'#'*60}\n")

    if args.mode in ['playwright', 'both']:
        results_playwright = await test_playwright_scraper(
            query=args.query,
            location=args.location,
            max_results=args.max_results,
            extract_emails=args.extract_emails
        )

        print(f"\n{'='*60}")
        print(f"Playwright Mode Summary")
        print(f"{'='*60}")
        print(f"Total businesses found: {len(results_playwright)}")
        print(f"Businesses with emails: {sum(1 for b in results_playwright if b.get('email'))}")
        print(f"Businesses with phones: {sum(1 for b in results_playwright if b.get('phone'))}")
        print(f"Businesses with websites: {sum(1 for b in results_playwright if b.get('website'))}")

    if args.mode in ['api', 'both']:
        if args.mode == 'both':
            print("\n" + "="*60)
            input("Press Enter to test Places API mode...")

        results_api = await test_places_api_scraper(
            query=args.query,
            location=args.location,
            max_results=args.max_results,
            api_key=args.api_key
        )

        print(f"\n{'='*60}")
        print(f"Places API Mode Summary")
        print(f"{'='*60}")
        print(f"Total businesses found: {len(results_api)}")
        print(f"Businesses with phones: {sum(1 for b in results_api if b.get('phone'))}")
        print(f"Businesses with websites: {sum(1 for b in results_api if b.get('website'))}")
        print(f"Businesses with coordinates: {sum(1 for b in results_api if b.get('latitude'))}")

    print(f"\n{'#'*60}")
    print(f"# Test Complete!")
    print(f"{'#'*60}\n")


if __name__ == '__main__':
    asyncio.run(main())
