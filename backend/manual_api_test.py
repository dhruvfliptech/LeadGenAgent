#!/usr/bin/env python3
"""
Manual API Test Script

Tests API endpoints without pytest - direct HTTP calls.
"""

import asyncio
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
import uuid

try:
    from httpx import AsyncClient, ASGITransport
except ImportError:
    print("ERROR: httpx not installed. Install with: pip install httpx")
    sys.exit(1)

# Import app
sys.path.insert(0, '/Users/greenmachine2.0/Craigslist/backend')
from app.main import app


class APITester:
    """API testing utility."""

    def __init__(self):
        self.client = None
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": []
        }
        self.start_time = None

    async def setup(self):
        """Setup test client."""
        self.start_time = datetime.now()
        transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=transport, base_url="http://test")

    async def teardown(self):
        """Cleanup."""
        if self.client:
            await self.client.aclose()

    def record_result(self, test_name: str, passed: bool, message: str = "", error: str = ""):
        """Record test result."""
        self.results["total"] += 1
        if passed:
            self.results["passed"] += 1
            status = "PASS"
            symbol = "✓"
        else:
            self.results["failed"] += 1
            status = "FAIL"
            symbol = "✗"

        self.results["tests"].append({
            "name": test_name,
            "passed": passed,
            "message": message,
            "error": error
        })

        print(f"  {symbol} {test_name}: {status}")
        if message:
            print(f"      {message}")
        if error:
            print(f"      Error: {error}")

    async def test_templates_crud(self):
        """Test Templates CRUD operations."""
        print("\n[1/4] Testing Templates API...")

        # CREATE
        template_data = {
            "name": f"Test Template {uuid.uuid4().hex[:8]}",
            "description": "Test template",
            "category": "job_inquiry",
            "subject_template": "Test Subject {{job_title}}",
            "body_template": "Test Body {{job_title}}",
            "use_ai_enhancement": True,
            "ai_tone": "professional",
            "ai_length": "medium"
        }

        try:
            response = await self.client.post("/api/v1/templates/", json=template_data)
            if response.status_code in [200, 201]:
                data = response.json()
                template_id = data.get("id")
                self.record_result(
                    "Create Template",
                    True,
                    f"Created template ID: {template_id}"
                )

                # READ
                response = await self.client.get(f"/api/v1/templates/{template_id}")
                self.record_result(
                    "Get Template by ID",
                    response.status_code == 200,
                    f"Retrieved template: {data.get('name')}"
                )

                # UPDATE
                update_data = {"name": "Updated Template Name"}
                response = await self.client.put(f"/api/v1/templates/{template_id}", json=update_data)
                self.record_result(
                    "Update Template",
                    response.status_code == 200,
                    "Template updated successfully"
                )

                # LIST
                response = await self.client.get("/api/v1/templates/")
                self.record_result(
                    "List Templates",
                    response.status_code == 200 and isinstance(response.json(), list),
                    f"Retrieved {len(response.json())} templates"
                )

                # DELETE
                response = await self.client.delete(f"/api/v1/templates/{template_id}")
                self.record_result(
                    "Delete Template",
                    response.status_code == 200,
                    "Template deleted successfully"
                )
            else:
                self.record_result(
                    "Create Template",
                    False,
                    error=f"Status: {response.status_code}, Body: {response.text[:200]}"
                )
        except Exception as e:
            self.record_result("Templates API", False, error=str(e))

    async def test_email_tracking(self):
        """Test Email Tracking endpoints."""
        print("\n[2/4] Testing Email Tracking API...")

        # Test open tracking
        try:
            response = await self.client.get("/api/v1/tracking/open/test_token_123")
            self.record_result(
                "Track Email Open",
                response.status_code == 200 and response.headers.get("content-type") == "image/gif",
                "Returns tracking pixel"
            )
        except Exception as e:
            self.record_result("Track Email Open", False, error=str(e))

        # Test click tracking
        try:
            response = await self.client.get(
                "/api/v1/tracking/click/test_token_123",
                params={"url": "https://example.com"},
                follow_redirects=False
            )
            self.record_result(
                "Track Email Click",
                response.status_code == 302,
                "Redirects correctly"
            )
        except Exception as e:
            self.record_result("Track Email Click", False, error=str(e))

        # Test unsubscribe page
        try:
            response = await self.client.get("/api/v1/tracking/unsubscribe-confirm")
            self.record_result(
                "Unsubscribe Page",
                response.status_code == 200 and "text/html" in response.headers.get("content-type", ""),
                "Returns HTML page"
            )
        except Exception as e:
            self.record_result("Unsubscribe Page", False, error=str(e))

    async def test_demo_sites(self):
        """Test Demo Sites endpoints."""
        print("\n[3/4] Testing Demo Sites API...")

        demo_site_data = {
            "site_name": f"Test Site {uuid.uuid4().hex[:8]}",
            "template_type": "portfolio",
            "content_data": {
                "company_name": "Test Co",
                "tagline": "Test tagline"
            },
            "style_settings": {
                "primary_color": "#007bff"
            },
            "use_ai_generation": False,
            "auto_deploy": False
        }

        try:
            # CREATE
            response = await self.client.post("/api/v1/demo-sites/generate", json=demo_site_data)
            if response.status_code in [200, 201]:
                data = response.json()
                site_id = data.get("id")
                self.record_result(
                    "Generate Demo Site",
                    True,
                    f"Created site ID: {site_id}"
                )

                # LIST
                response = await self.client.get("/api/v1/demo-sites/")
                self.record_result(
                    "List Demo Sites",
                    response.status_code == 200 and "demo_sites" in response.json(),
                    f"Retrieved sites"
                )

                # GET
                response = await self.client.get(f"/api/v1/demo-sites/{site_id}")
                self.record_result(
                    "Get Demo Site",
                    response.status_code == 200,
                    "Retrieved site details"
                )

                # LIST TEMPLATES
                response = await self.client.get("/api/v1/demo-sites/templates")
                self.record_result(
                    "List Templates",
                    response.status_code == 200,
                    "Retrieved templates"
                )

                # DELETE
                response = await self.client.delete(f"/api/v1/demo-sites/{site_id}")
                self.record_result(
                    "Delete Demo Site",
                    response.status_code == 200,
                    "Site deleted"
                )
            else:
                self.record_result(
                    "Generate Demo Site",
                    False,
                    error=f"Status: {response.status_code}, Body: {response.text[:200]}"
                )
        except Exception as e:
            self.record_result("Demo Sites API", False, error=str(e))

    async def test_workflows(self):
        """Test N8N Workflows endpoints."""
        print("\n[4/4] Testing N8N Workflows API...")

        # Test webhook connectivity
        try:
            response = await self.client.get("/api/v1/webhooks/n8n/n8n/test")
            self.record_result(
                "Webhook Connectivity Test",
                response.status_code == 200 and response.json().get("status") == "ok",
                "Webhook endpoint reachable"
            )
        except Exception as e:
            self.record_result("Webhook Connectivity", False, error=str(e))

        # Test webhook receive
        try:
            payload = {
                "event": "test",
                "data": {"test": True},
                "timestamp": datetime.utcnow().isoformat()
            }
            response = await self.client.post(
                "/api/v1/webhooks/n8n/n8n/test_workflow",
                json=payload
            )
            self.record_result(
                "Receive N8N Webhook",
                response.status_code == 200 and "status" in response.json(),
                "Webhook received"
            )
        except Exception as e:
            self.record_result("Receive N8N Webhook", False, error=str(e))

        # Test approval rules templates
        try:
            response = await self.client.get("/api/v1/workflows/approvals/auto-approval/templates")
            self.record_result(
                "Get Approval Templates",
                response.status_code == 200 and "templates" in response.json(),
                f"Retrieved {len(response.json().get('templates', []))} templates"
            )
        except Exception as e:
            self.record_result("Get Approval Templates", False, error=str(e))

        # Test pending approvals
        try:
            response = await self.client.get("/api/v1/workflows/approvals/pending")
            self.record_result(
                "Get Pending Approvals",
                response.status_code in [200, 404],  # 404 is ok if no approvals
                "Endpoint accessible"
            )
        except Exception as e:
            self.record_result("Get Pending Approvals", False, error=str(e))

    def print_summary(self):
        """Print test summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {self.results['total']}")
        print(f"Passed: {self.results['passed']} ({self.results['passed']/self.results['total']*100:.1f}%)")
        print(f"Failed: {self.results['failed']}")
        print(f"Skipped: {self.results['skipped']}")
        print(f"\nDuration: {elapsed:.2f} seconds")

        # Test breakdown
        print("\n" + "=" * 80)
        print("TEST BREAKDOWN")
        print("=" * 80)

        for test in self.results["tests"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            print(f"{status}: {test['name']}")

        # Failed tests detail
        failed_tests = [t for t in self.results["tests"] if not t["passed"]]
        if failed_tests:
            print("\n" + "=" * 80)
            print("FAILED TESTS DETAIL")
            print("=" * 80)
            for test in failed_tests:
                print(f"\n{test['name']}")
                if test.get("error"):
                    print(f"  Error: {test['error']}")

        print("\n" + "=" * 80)
        return self.results['failed'] == 0

    async def run_all_tests(self):
        """Run all test suites."""
        print("=" * 80)
        print("COMPREHENSIVE API ENDPOINT TEST")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        await self.setup()

        try:
            await self.test_templates_crud()
            await self.test_email_tracking()
            await self.test_demo_sites()
            await self.test_workflows()
        finally:
            await self.teardown()

        return self.print_summary()


async def main():
    """Main entry point."""
    tester = APITester()
    success = await tester.run_all_tests()

    if success:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
