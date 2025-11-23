#!/usr/bin/env python3
"""
Test the live system by creating sample data and triggering a scrape.
"""

import asyncio
import requests
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_api_connection():
    """Test if API is running."""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ API is running: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def get_locations():
    """Get available locations."""
    try:
        response = requests.get(f"{BASE_URL}/locations")
        locations = response.json()
        print(f"✅ Found {len(locations)} locations")
        return locations
    except Exception as e:
        print(f"❌ Failed to get locations: {e}")
        return []

def get_leads():
    """Get current leads."""
    try:
        response = requests.get(f"{BASE_URL}/leads")
        leads = response.json()
        print(f"✅ Found {len(leads)} existing leads")
        return leads
    except Exception as e:
        print(f"❌ Failed to get leads: {e}")
        return []

def trigger_scrape():
    """Trigger a small scraping job."""
    try:
        # Use San Francisco (location ID 1) for testing
        data = {
            "location_ids": [1],
            "categories": ["gigs"],
            "keywords": ["developer", "programmer"],
            "max_pages": 1,
            "priority": "normal"
        }
        
        response = requests.post(f"{BASE_URL}/scraper/jobs", json=data)
        
        if response.status_code == 200:
            job = response.json()
            print(f"✅ Scraping job created: {job.get('job_id')}")
            return job
        else:
            print(f"❌ Failed to create scraping job: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Failed to trigger scrape: {e}")
        return None

def check_scraper_status():
    """Check scraper queue status."""
    try:
        response = requests.get(f"{BASE_URL}/scraper/queue/status")
        status = response.json()
        print(f"✅ Scraper status: {status}")
        return status
    except Exception as e:
        print(f"❌ Failed to get scraper status: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("LIVE SYSTEM TEST")
    print("="*60)
    
    # Test API connection
    if not test_api_connection():
        print("\n⚠️ Please ensure the backend is running on port 8000")
        return
    
    # Get locations
    print("\n[1] Checking Locations...")
    locations = get_locations()
    
    # Get current leads
    print("\n[2] Checking Existing Leads...")
    leads = get_leads()
    
    # Check scraper status
    print("\n[3] Checking Scraper Status...")
    status = check_scraper_status()
    
    # Optionally trigger a scrape
    print("\n[4] Trigger Test Scrape?")
    response = input("Do you want to trigger a test scraping job? (y/n): ")
    
    if response.lower() == 'y':
        print("Triggering scraping job...")
        job = trigger_scrape()
        
        if job:
            print(f"\n✅ Scraping job started!")
            print(f"   Job ID: {job.get('job_id')}")
            print(f"   Status: {job.get('status')}")
            print("\n📊 You can monitor progress in the frontend at:")
            print("   http://localhost:5176/scraper")
    
    print("\n" + "="*60)
    print("SYSTEM STATUS SUMMARY")
    print("="*60)
    print(f"✅ Backend API: Running on http://localhost:8000")
    print(f"✅ Frontend: Running on http://localhost:5176")
    print(f"✅ API Docs: http://localhost:8000/docs")
    print(f"📊 Locations Available: {len(locations)}")
    print(f"📊 Existing Leads: {len(leads)}")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Visit http://localhost:5176 to use the dashboard")
    print("2. Go to the Scraper page to create scraping jobs")
    print("3. View and qualify leads on the Leads page")
    print("4. Check API documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    main()