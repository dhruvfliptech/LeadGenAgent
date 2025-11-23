#!/usr/bin/env python3
"""
Test enhanced metadata capture from Craigslist listings.
"""

import asyncio
import json
from datetime import datetime
from app.scrapers.craigslist_scraper import CraigslistScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_enhanced_data_capture():
    """Test that we're capturing all enhanced metadata fields."""
    print("\n" + "="*60)
    print("TESTING ENHANCED DATA CAPTURE")
    print("="*60)
    
    try:
        async with CraigslistScraper(enable_email_extraction=False) as scraper:
            # First, get a few listings
            location_url = "https://sfbay.craigslist.org"
            categories = ["jobs"]  # Jobs category for better metadata
            max_pages = 1
            
            print(f"\nStep 1: Getting listings from {location_url}")
            
            leads = await scraper.scrape_location(
                location_url=location_url,
                categories=categories,
                keywords=None,
                max_pages=max_pages
            )
            
            if not leads or len(leads) < 1:
                print("❌ No leads found to test enhanced capture")
                return False
            
            print(f"✅ Found {len(leads)} leads")
            
            # Test enhanced capture on first 3 leads
            test_leads = leads[:3]
            enhanced_leads = []
            
            print(f"\nStep 2: Testing enhanced capture on {len(test_leads)} leads...")
            
            for i, lead in enumerate(test_leads, 1):
                print(f"\n  Testing lead #{i}: {lead['title'][:50]}...")
                
                # Get enhanced details for this listing
                details = await scraper.get_listing_details(lead['url'])
                
                if details:
                    # Merge with basic lead data
                    enhanced_lead = {**lead, **details}
                    enhanced_leads.append(enhanced_lead)
                    
                    print(f"    ✅ Enhanced capture successful!")
                    print(f"    - Has body_html: {'body_html' in details and bool(details['body_html'])}")
                    print(f"    - Has description: {'description' in details and bool(details['description'])}")
                    print(f"    - Has compensation: {details.get('compensation') is not None}")
                    print(f"    - Employment types: {details.get('employment_type')}")
                    print(f"    - Is remote: {details.get('is_remote', False)}")
                    print(f"    - Is internship: {details.get('is_internship', False)}")
                    print(f"    - Is nonprofit: {details.get('is_nonprofit', False)}")
                    print(f"    - Contact info: {bool(details.get('contact_info', {}))}")
                    print(f"    - Location details: {bool(details.get('location_details', {}))}")
                    print(f"    - Attributes: {len(details.get('attributes', {})) if details.get('attributes') else 0} fields")
                    print(f"    - Image URLs: {len(details.get('image_urls', [])) if details.get('image_urls') else 0} images")
                else:
                    print(f"    ⚠️ Could not get enhanced details")
            
            # Save enhanced data for inspection
            if enhanced_leads:
                output_file = f"enhanced_capture_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w') as f:
                    json.dump(enhanced_leads, f, indent=2, default=str)
                print(f"\n📄 Enhanced data saved to: {output_file}")
                
                # Show summary statistics
                print("\n" + "="*60)
                print("CAPTURE STATISTICS")
                print("="*60)
                
                stats = {
                    'total_tested': len(enhanced_leads),
                    'with_compensation': sum(1 for l in enhanced_leads if l.get('compensation')),
                    'with_employment_type': sum(1 for l in enhanced_leads if l.get('employment_type')),
                    'remote_jobs': sum(1 for l in enhanced_leads if l.get('is_remote')),
                    'internships': sum(1 for l in enhanced_leads if l.get('is_internship')),
                    'nonprofits': sum(1 for l in enhanced_leads if l.get('is_nonprofit')),
                    'with_coordinates': sum(1 for l in enhanced_leads if l.get('location_details', {}).get('latitude')),
                    'with_images': sum(1 for l in enhanced_leads if l.get('image_urls')),
                    'with_attributes': sum(1 for l in enhanced_leads if l.get('attributes'))
                }
                
                for key, value in stats.items():
                    percentage = (value / stats['total_tested']) * 100 if stats['total_tested'] > 0 else 0
                    print(f"  {key.replace('_', ' ').title()}: {value}/{stats['total_tested']} ({percentage:.1f}%)")
                
                return True
            else:
                print("\n⚠️ No enhanced data captured")
                return False
                
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.exception("Test failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_data_capture())
    
    if success:
        print("\n🎉 Enhanced data capture is working correctly!")
    else:
        print("\n⚠️ Enhanced data capture test failed")
    
    exit(0 if success else 1)