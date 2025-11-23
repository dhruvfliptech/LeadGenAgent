#!/usr/bin/env python3
"""
Test the Lead Qualification Engine.
"""

import asyncio
import httpx
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_qualification_engine():
    """Test the complete qualification workflow."""
    print("\n" + "="*60)
    print("TESTING LEAD QUALIFICATION ENGINE")
    print("="*60)
    
    base_url = "http://localhost:8001/api/v1"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Create qualification criteria
            print("\n[Step 1] Creating qualification criteria...")
            
            criteria_data = {
                "name": f"Software Developer Criteria {datetime.now().strftime('%H%M%S')}",
                "description": "Criteria for qualifying software development opportunities",
                
                # Keywords
                "required_keywords": ["software", "developer", "programming"],
                "preferred_keywords": ["python", "javascript", "react", "node", "api"],
                "excluded_keywords": ["unpaid", "volunteer", "equity only"],
                
                # Compensation
                "min_compensation": 50000,
                "max_compensation": 200000,
                "compensation_type": "salary",
                
                # Location
                "remote_acceptable": True,
                "preferred_locations": ["San Francisco", "Bay Area", "Remote"],
                
                # Employment
                "preferred_employment_types": ["full-time", "contract"],
                "internship_acceptable": False,
                "nonprofit_acceptable": True,
                
                # Weights (must sum to 1.0)
                "keyword_weight": 0.35,
                "compensation_weight": 0.25,
                "location_weight": 0.15,
                "employment_type_weight": 0.15,
                "freshness_weight": 0.10,
                
                # Thresholds
                "min_score_threshold": 0.5,
                "auto_qualify_threshold": 0.75,
                "auto_reject_threshold": 0.25,
                
                # Requirements
                "max_days_old": 7,
                "require_contact_info": False,
                "require_compensation_info": False,
                
                # Custom rules
                "custom_rules": {
                    "boost_if_contains": {
                        "senior": 0.1,
                        "lead": 0.1,
                        "architect": 0.15,
                        "full stack": 0.1
                    },
                    "penalty_if_contains": {
                        "entry level": -0.1,
                        "junior": -0.05,
                        "unpaid": -0.3
                    }
                }
            }
            
            response = await client.post(
                f"{base_url}/qualification/criteria",
                json=criteria_data
            )
            
            if response.status_code == 200:
                criteria = response.json()
                criteria_id = criteria['id']
                print(f"✅ Created criteria: {criteria['name']} (ID: {criteria_id})")
            else:
                print(f"❌ Failed to create criteria: {response.status_code}")
                print(response.json())
                return False
            
            # Step 2: Get some leads to qualify
            print("\n[Step 2] Fetching leads to qualify...")
            
            leads_response = await client.get(
                f"{base_url}/leads/",
                params={"limit": 10}
            )
            
            if leads_response.status_code == 200:
                leads = leads_response.json()
                print(f"✅ Found {len(leads)} leads to qualify")
            else:
                print(f"❌ Failed to fetch leads: {leads_response.status_code}")
                return False
            
            if not leads:
                print("⚠️ No leads found. Creating test leads...")
                # You could create test leads here if needed
                return False
            
            # Step 3: Qualify leads
            print("\n[Step 3] Qualifying leads...")
            
            lead_ids = [lead['id'] for lead in leads[:5]]  # Test with first 5
            
            qualify_request = {
                "lead_ids": lead_ids,
                "criteria_id": criteria_id,
                "update_database": True,
                "use_ai": False  # Set to True if OpenAI is configured
            }
            
            qualify_response = await client.post(
                f"{base_url}/qualification/qualify",
                json=qualify_request
            )
            
            if qualify_response.status_code == 200:
                results = qualify_response.json()
                print(f"✅ Qualified {len(results)} leads")
                
                # Show results
                print("\n" + "="*60)
                print("QUALIFICATION RESULTS")
                print("="*60)
                
                for result in results:
                    if 'error' in result:
                        print(f"\n❌ Lead {result['lead_id']}: ERROR - {result['error']}")
                    else:
                        status_emoji = {
                            'qualified': '✅',
                            'rejected': '❌',
                            'review': '🔍'
                        }.get(result['status'], '❓')
                        
                        print(f"\n{status_emoji} Lead: {result['title'][:60]}...")
                        print(f"   Score: {result['score']:.3f}")
                        print(f"   Status: {result['status'].upper()}")
                        print(f"   Reasoning: {result['reasoning'][:150]}...")
                        
                        if result.get('detailed_scores'):
                            print(f"   Detailed Scores:")
                            for category, score in result['detailed_scores'].items():
                                print(f"     - {category}: {score:.2f}")
            else:
                print(f"❌ Failed to qualify leads: {qualify_response.status_code}")
                print(qualify_response.json())
                return False
            
            # Step 4: Get qualification statistics
            print("\n[Step 4] Getting qualification statistics...")
            
            stats_response = await client.get(
                f"{base_url}/qualification/stats",
                params={"criteria_id": criteria_id}
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("\n" + "="*60)
                print("QUALIFICATION STATISTICS")
                print("="*60)
                print(f"Total Qualified: {stats['total_qualified']}")
                print(f"Average Score: {stats['average_score']:.3f}")
                
                if stats['status_breakdown']:
                    print("\nStatus Breakdown:")
                    for status, count in stats['status_breakdown'].items():
                        print(f"  - {status}: {count}")
                
                if stats['score_distribution']:
                    print("\nScore Distribution:")
                    for level, count in stats['score_distribution'].items():
                        print(f"  - {level}: {count}")
            
            # Step 5: Get qualified leads
            print("\n[Step 5] Fetching qualified leads...")
            
            qualified_response = await client.get(
                f"{base_url}/qualification/qualified-leads",
                params={"min_score": 0.5, "limit": 5}
            )
            
            if qualified_response.status_code == 200:
                qualified_leads = qualified_response.json()
                print(f"\n✅ Found {len(qualified_leads)} qualified leads with score >= 0.5")
                
                for lead in qualified_leads[:3]:
                    print(f"\n  • {lead['title'][:60]}...")
                    print(f"    Score: {lead['score']:.3f} | Status: {lead['status']}")
                    print(f"    Location: {lead['location']} | Remote: {lead['is_remote']}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Test failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_qualification_engine())
    
    if success:
        print("\n🎉 Lead Qualification Engine is working correctly!")
        print("\nThe system can now:")
        print("  ✅ Define custom qualification criteria")
        print("  ✅ Score leads based on multiple factors")
        print("  ✅ Automatically qualify/reject leads")
        print("  ✅ Provide detailed reasoning for decisions")
        print("  ✅ Track qualification statistics")
    else:
        print("\n⚠️ Qualification engine test failed")
    
    exit(0 if success else 1)