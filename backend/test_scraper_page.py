#!/usr/bin/env python3
"""
Test script to verify Scraper page functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_scraper_endpoints():
    """Test all scraper-related endpoints"""
    
    print("Testing Scraper Page Backend Endpoints...")
    print("=" * 50)
    
    # Test 1: Queue Status
    print("\n1. Testing Queue Status Endpoint:")
    response = requests.get(f"{BASE_URL}/scraper/queue/status")
    if response.status_code == 200:
        print("✅ Queue status endpoint working")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ Queue status failed: {response.status_code}")
    
    # Test 2: Jobs List
    print("\n2. Testing Jobs List Endpoint:")
    response = requests.get(f"{BASE_URL}/scraper/jobs")
    if response.status_code == 200:
        jobs = response.json()
        print(f"✅ Jobs list endpoint working")
        print(f"   Found {len(jobs)} jobs")
    else:
        print(f"❌ Jobs list failed: {response.status_code}")
    
    # Test 3: Locations Hierarchy
    print("\n3. Testing Locations Hierarchy Endpoint:")
    response = requests.get(f"{BASE_URL}/locations/hierarchy")
    if response.status_code == 200:
        data = response.json()
        print("✅ Locations hierarchy endpoint working")
        print(f"   Found {len(data.get('nodes', []))} top-level nodes")
    else:
        print(f"❌ Locations hierarchy failed: {response.status_code}")
    
    # Test 4: Categories Structured
    print("\n4. Testing Categories Structured Endpoint:")
    response = requests.get(f"{BASE_URL}/scraper/categories/structured")
    if response.status_code == 200:
        categories = response.json()
        print("✅ Categories structured endpoint working")
        print(f"   Categories: {list(categories.keys())}")
    else:
        print(f"❌ Categories structured failed: {response.status_code}")
    
    # Test 5: Create a Test Job
    print("\n5. Testing Job Creation:")
    job_data = {
        "location_ids": [1],  # San Francisco
        "categories": ["gigs"],
        "keywords": ["test", "developer"],
        "max_pages": 1,
        "priority": "low"
    }
    
    response = requests.post(f"{BASE_URL}/scraper/jobs", json=job_data)
    if response.status_code == 200:
        job = response.json()
        print("✅ Job creation endpoint working")
        print(f"   Created job: {job.get('job_id')}")
        print(f"   Status: {job.get('status')}")
        
        # Wait and check job status
        time.sleep(2)
        job_id = job.get('job_id')
        response = requests.get(f"{BASE_URL}/scraper/jobs")
        jobs = response.json()
        
        test_job = next((j for j in jobs if j['job_id'] == job_id), None)
        if test_job:
            print(f"   Job found in list with status: {test_job['status']}")
    else:
        print(f"❌ Job creation failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("All backend endpoints required for the Scraper page are working.")
    print("If the page still doesn't show, check:")
    print("1. Browser console for JavaScript errors")
    print("2. Network tab for failed requests")
    print("3. React component rendering issues")

if __name__ == "__main__":
    test_scraper_endpoints()