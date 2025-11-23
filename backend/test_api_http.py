#!/usr/bin/env python3
"""
HTTP-Based API Test Script

Tests API endpoints via HTTP requests (assumes server is running on localhost:8000).
No dependencies on app internals.
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any
import sys


class APITester:
    """HTTP-based API testing utility."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": []
        }
        self.start_time = None

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
        if error and len(error) < 500:
            print(f"      Error: {error}")

    def check_server(self):
        """Check if server is running."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code in [200, 503]
        except Exception:
            return False

    def test_templates_api(self):
        """Test Templates API endpoints."""
        print("\n[1/4] Testing Auto-response Templates API")
        print("-" * 80)

        # CREATE Template
        template_data = {
            "name": f"Test Template {uuid.uuid4().hex[:8]}",
            "description": "Automated test template",
            "category": "job_inquiry",
            "subject_template": "Interested in {{job_title}} position",
            "body_template": "Hi {{contact_name}},\n\nI'm interested in the {{job_title}} role.\n\nBest,\n{{user_name}}",
            "variables": {
                "required": ["job_title"],
                "optional": ["contact_name", "user_name"]
            },
            "use_ai_enhancement": True,
            "ai_tone": "professional",
            "ai_length": "medium",
            "test_weight": 50.0
        }

        try:
            # CREATE
            response = self.session.post(
                f"{self.base_url}/api/v1/templates/",
                json=template_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                template_id = data.get("id")
                self.record_result(
                    "POST /templates/ (Create)",
                    True,
                    f"Created template ID: {template_id}"
                )

                # GET by ID
                response = self.session.get(
                    f"{self.base_url}/api/v1/templates/{template_id}",
                    timeout=10
                )
                self.record_result(
                    "GET /templates/{id} (Read)",
                    response.status_code == 200 and response.json().get("id") == template_id,
                    f"Retrieved template: {response.json().get('name')}"
                )

                # UPDATE
                update_data = {"name": "Updated Template Name", "ai_tone": "casual"}
                response = self.session.put(
                    f"{self.base_url}/api/v1/templates/{template_id}",
                    json=update_data,
                    timeout=10
                )
                self.record_result(
                    "PUT /templates/{id} (Update)",
                    response.status_code == 200,
                    "Template updated successfully"
                )

                # LIST
                response = self.session.get(
                    f"{self.base_url}/api/v1/templates/",
                    timeout=10
                )
                templates = response.json() if response.status_code == 200 else []
                self.record_result(
                    "GET /templates/ (List)",
                    response.status_code == 200 and isinstance(templates, list),
                    f"Retrieved {len(templates)} templates"
                )

                # LIST with filters
                response = self.session.get(
                    f"{self.base_url}/api/v1/templates/?category=job_inquiry&is_active=true",
                    timeout=10
                )
                self.record_result(
                    "GET /templates/?category=X (Filter)",
                    response.status_code == 200,
                    "Filtered list works"
                )

                # A/B Testing Analytics
                response = self.session.get(
                    f"{self.base_url}/api/v1/templates/analytics/ab-testing",
                    timeout=10
                )
                self.record_result(
                    "GET /templates/analytics/ab-testing",
                    response.status_code == 200 and "results" in response.json(),
                    "A/B testing analytics available"
                )

                # DELETE
                response = self.session.delete(
                    f"{self.base_url}/api/v1/templates/{template_id}",
                    timeout=10
                )
                self.record_result(
                    "DELETE /templates/{id}",
                    response.status_code == 200,
                    "Template deleted successfully"
                )

                # Verify deleted
                response = self.session.get(
                    f"{self.base_url}/api/v1/templates/{template_id}",
                    timeout=10
                )
                self.record_result(
                    "GET deleted template returns 404",
                    response.status_code == 404,
                    "Deleted template not found"
                )

            else:
                self.record_result(
                    "POST /templates/ (Create)",
                    False,
                    error=f"Status: {response.status_code}, Body: {response.text[:300]}"
                )

        except Exception as e:
            self.record_result("Templates API", False, error=str(e))

    def test_email_tracking_api(self):
        """Test Email Tracking API endpoints."""
        print("\n[2/4] Testing Email Tracking API")
        print("-" * 80)

        # Track email open
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tracking/open/test_token_123",
                timeout=5
            )
            self.record_result(
                "GET /tracking/open/{token}",
                response.status_code == 200 and response.headers.get("content-type") == "image/gif",
                "Returns 1x1 tracking pixel"
            )
        except Exception as e:
            self.record_result("GET /tracking/open/{token}", False, error=str(e))

        # Track email click
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tracking/click/test_token_123",
                params={"url": "https://example.com"},
                allow_redirects=False,
                timeout=5
            )
            self.record_result(
                "GET /tracking/click/{token}",
                response.status_code == 302,
                "Redirects to target URL"
            )
        except Exception as e:
            self.record_result("GET /tracking/click/{token}", False, error=str(e))

        # Unsubscribe confirmation page
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/tracking/unsubscribe-confirm",
                timeout=5
            )
            self.record_result(
                "GET /tracking/unsubscribe-confirm",
                response.status_code == 200 and "text/html" in response.headers.get("content-type", ""),
                "Returns HTML unsubscribe page"
            )
        except Exception as e:
            self.record_result("GET /tracking/unsubscribe-confirm", False, error=str(e))

    def test_demo_sites_api(self):
        """Test Demo Site Builder API endpoints."""
        print("\n[3/4] Testing Demo Site Builder API")
        print("-" * 80)

        demo_site_data = {
            "site_name": f"Test Demo Site {uuid.uuid4().hex[:8]}",
            "template_type": "portfolio",
            "content_data": {
                "company_name": "Test Company",
                "tagline": "Building amazing things",
                "features": ["Feature 1", "Feature 2"]
            },
            "style_settings": {
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "font_family": "Inter"
            },
            "use_ai_generation": False,
            "auto_deploy": False
        }

        try:
            # CREATE
            response = self.session.post(
                f"{self.base_url}/api/v1/demo-sites/generate",
                json=demo_site_data,
                timeout=15
            )

            if response.status_code in [200, 201]:
                data = response.json()
                site_id = data.get("id")
                self.record_result(
                    "POST /demo-sites/generate",
                    True,
                    f"Created demo site ID: {site_id}"
                )

                # GET by ID
                response = self.session.get(
                    f"{self.base_url}/api/v1/demo-sites/{site_id}",
                    timeout=10
                )
                self.record_result(
                    "GET /demo-sites/{id}",
                    response.status_code == 200,
                    "Retrieved demo site details"
                )

                # LIST
                response = self.session.get(
                    f"{self.base_url}/api/v1/demo-sites/",
                    timeout=10
                )
                data = response.json()
                self.record_result(
                    "GET /demo-sites/ (List)",
                    response.status_code == 200 and "demo_sites" in data,
                    f"Retrieved {data.get('total', 0)} sites"
                )

                # LIST with filters
                response = self.session.get(
                    f"{self.base_url}/api/v1/demo-sites/?status=draft&page=1&page_size=10",
                    timeout=10
                )
                self.record_result(
                    "GET /demo-sites/?status=X (Filter)",
                    response.status_code == 200,
                    "Filtered list works"
                )

                # UPDATE
                update_data = {"site_name": "Updated Site Name"}
                response = self.session.put(
                    f"{self.base_url}/api/v1/demo-sites/{site_id}",
                    json=update_data,
                    timeout=10
                )
                self.record_result(
                    "PUT /demo-sites/{id}",
                    response.status_code == 200,
                    "Demo site updated"
                )

                # PREVIEW
                response = self.session.get(
                    f"{self.base_url}/api/v1/demo-sites/{site_id}/preview",
                    timeout=10
                )
                if response.status_code == 200:
                    self.record_result(
                        "GET /demo-sites/{id}/preview",
                        "html" in response.json() or "css" in response.json(),
                        "Preview available"
                    )
                else:
                    self.record_result(
                        "GET /demo-sites/{id}/preview",
                        False,
                        error=f"Status: {response.status_code}"
                    )

                # EXPORT
                response = self.session.get(
                    f"{self.base_url}/api/v1/demo-sites/{site_id}/export",
                    timeout=10
                )
                if response.status_code == 200:
                    self.record_result(
                        "GET /demo-sites/{id}/export",
                        "files" in response.json(),
                        "Export files available"
                    )
                else:
                    self.record_result(
                        "GET /demo-sites/{id}/export",
                        False,
                        error=f"Status: {response.status_code}"
                    )

                # DELETE
                response = self.session.delete(
                    f"{self.base_url}/api/v1/demo-sites/{site_id}",
                    timeout=10
                )
                self.record_result(
                    "DELETE /demo-sites/{id}",
                    response.status_code == 200,
                    "Demo site deleted"
                )

            else:
                self.record_result(
                    "POST /demo-sites/generate",
                    False,
                    error=f"Status: {response.status_code}, Body: {response.text[:300]}"
                )

            # LIST TEMPLATES
            response = self.session.get(
                f"{self.base_url}/api/v1/demo-sites/templates",
                timeout=10
            )
            data = response.json()
            self.record_result(
                "GET /demo-sites/templates",
                response.status_code == 200 and "templates" in data,
                f"Retrieved {data.get('total', 0)} templates"
            )

        except Exception as e:
            self.record_result("Demo Sites API", False, error=str(e))

    def test_workflows_api(self):
        """Test N8N Workflows API endpoints."""
        print("\n[4/4] Testing N8N Workflows & Approvals API")
        print("-" * 80)

        # Webhook connectivity test
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/webhooks/n8n/n8n/test",
                timeout=5
            )
            data = response.json()
            self.record_result(
                "GET /webhooks/n8n/n8n/test",
                response.status_code == 200 and data.get("status") == "ok",
                "Webhook endpoint reachable"
            )
        except Exception as e:
            self.record_result("GET /webhooks/n8n/n8n/test", False, error=str(e))

        # Receive webhook
        try:
            payload = {
                "event": "test_event",
                "data": {"test": True},
                "timestamp": datetime.utcnow().isoformat()
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/webhooks/n8n/n8n/test_workflow_123",
                json=payload,
                timeout=10
            )
            self.record_result(
                "POST /webhooks/n8n/n8n/{workflow_id}",
                response.status_code == 200 and "status" in response.json(),
                "Webhook received and queued"
            )
        except Exception as e:
            self.record_result("POST /webhooks/n8n/n8n/{workflow_id}", False, error=str(e))

        # Generic webhook
        try:
            payload = {
                "event": "lead_created",
                "data": {"lead_id": 123},
                "source": "n8n"
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/webhooks/n8n/n8n/generic",
                json=payload,
                timeout=10
            )
            self.record_result(
                "POST /webhooks/n8n/n8n/generic",
                response.status_code == 200,
                "Generic webhook received"
            )
        except Exception as e:
            self.record_result("POST /webhooks/n8n/n8n/generic", False, error=str(e))

        # Approval templates
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/workflows/approvals/auto-approval/templates",
                timeout=10
            )
            data = response.json()
            self.record_result(
                "GET /workflows/approvals/auto-approval/templates",
                response.status_code == 200 and "templates" in data,
                f"Retrieved {len(data.get('templates', []))} approval rule templates"
            )
        except Exception as e:
            self.record_result("GET /workflows/approvals/auto-approval/templates", False, error=str(e))

        # Pending approvals
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/workflows/approvals/pending",
                timeout=10
            )
            self.record_result(
                "GET /workflows/approvals/pending",
                response.status_code in [200, 404],  # 404 OK if no approvals
                "Pending approvals endpoint accessible"
            )
        except Exception as e:
            self.record_result("GET /workflows/approvals/pending", False, error=str(e))

        # Approval statistics
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/workflows/approvals/stats",
                timeout=10
            )
            self.record_result(
                "GET /workflows/approvals/stats",
                response.status_code == 200,
                "Approval statistics available"
            )
        except Exception as e:
            self.record_result("GET /workflows/approvals/stats", False, error=str(e))

    def print_summary(self):
        """Print test summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests: {self.results['total']}")

        if self.results['total'] > 0:
            pass_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"Passed: {self.results['passed']} ({pass_rate:.1f}%)")
            print(f"Failed: {self.results['failed']}")
            print(f"Skipped: {self.results['skipped']}")
        else:
            print("No tests executed")

        print(f"\nDuration: {elapsed:.2f} seconds")

        # Coverage summary
        print("\n" + "=" * 80)
        print("ENDPOINT COVERAGE")
        print("=" * 80)
        endpoints = {
            "Templates API": sum(1 for t in self.results["tests"] if "templates" in t["name"].lower() or "POST /templates" in t["name"]),
            "Email Tracking API": sum(1 for t in self.results["tests"] if "tracking" in t["name"].lower()),
            "Demo Sites API": sum(1 for t in self.results["tests"] if "demo-sites" in t["name"].lower() or "demo site" in t["name"].lower()),
            "Workflows API": sum(1 for t in self.results["tests"] if "webhook" in t["name"].lower() or "approval" in t["name"].lower())
        }

        for api, count in endpoints.items():
            print(f"{api}: {count} tests")

        # Failed tests detail
        failed_tests = [t for t in self.results["tests"] if not t["passed"]]
        if failed_tests:
            print("\n" + "=" * 80)
            print("FAILED TESTS")
            print("=" * 80)
            for test in failed_tests:
                print(f"\n✗ {test['name']}")
                if test.get("error"):
                    print(f"  Error: {test['error'][:200]}")

        print("\n" + "=" * 80)
        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all test suites."""
        print("=" * 80)
        print("COMPREHENSIVE API ENDPOINT TEST")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.start_time = datetime.now()

        # Check if server is running
        if not self.check_server():
            print(f"\nERROR: Server not reachable at {self.base_url}")
            print("Please start the backend server with: ./start_backend.sh")
            return False

        print("✓ Server is reachable\n")

        self.test_templates_api()
        self.test_email_tracking_api()
        self.test_demo_sites_api()
        self.test_workflows_api()

        return self.print_summary()


def main():
    """Main entry point."""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    tester = APITester(base_url=base_url)
    success = tester.run_all_tests()

    if success:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
