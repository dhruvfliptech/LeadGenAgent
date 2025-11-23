#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all endpoints and documents which work vs which are broken
"""

import requests
import json
from typing import Dict, List
import time

BASE_URL = "http://localhost:8000"

# Define all endpoints to test
ENDPOINTS = {
    "Core": [
        ("GET", "/", "Root endpoint"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "API documentation"),
    ],
    "Leads": [
        ("GET", "/api/v1/leads/", "List all leads"),
        ("GET", "/api/v1/leads/stats", "Lead statistics"),
    ],
    "Locations": [
        ("GET", "/api/v1/locations/", "List all locations"),
        ("GET", "/api/v1/locations/countries", "List countries"),
    ],
    "Scraper": [
        ("GET", "/api/v1/scraper/status", "Scraper status"),
        ("GET", "/api/v1/scraper/jobs", "List scraper jobs"),
    ],
    "Google Maps": [
        ("GET", "/api/v1/google-maps/status", "Google Maps status"),
    ],
    "Email Finder": [
        ("GET", "/api/v1/email-finder/status", "Email finder status"),
    ],
    "LinkedIn": [
        ("GET", "/api/v1/linkedin/status", "LinkedIn scraper status"),
    ],
    "Job Boards": [
        ("GET", "/api/v1/job-boards/status", "Job boards status"),
    ],
    "Machine Learning": [
        ("GET", "/api/v1/ml/model/status", "ML model status"),
        ("GET", "/api/v1/ml/metrics", "ML metrics"),
    ],
    "Qualification": [
        ("GET", "/api/v1/qualification/criteria", "Qualification criteria"),
    ],
    "Responses": [
        ("GET", "/api/v1/responses/templates", "Response templates"),
    ],
    "Approvals": [
        ("GET", "/api/v1/approvals/queue", "Approval queue"),
    ],
    "AI MVP": [
        ("GET", "/api/v1/ai-mvp/status", "AI MVP status"),
    ],
    "Conversations": [
        ("GET", "/api/v1/conversations/", "List conversations"),
    ],
    "Demo Sites": [
        ("GET", "/api/v1/demo-sites/", "List demo sites"),
    ],
    "Video Scripts": [
        ("GET", "/api/v1/video-scripts/", "List video scripts"),
    ],
    "Voiceovers": [
        ("GET", "/api/v1/voiceovers/", "List voiceovers"),
    ],
    "Screen Recordings": [
        ("GET", "/api/v1/screen-recordings/", "List screen recordings"),
    ],
    "Hosted Videos": [
        ("GET", "/api/v1/hosted-videos/", "List hosted videos"),
    ],
    "Composed Videos": [
        ("GET", "/api/v1/composed-videos/", "List composed videos"),
    ],
    "Webhooks (Phase 5)": [
        ("GET", "/api/v1/webhooks/status", "Webhook status"),
    ],
    "n8n Webhooks (Phase 5)": [
        ("GET", "/api/v1/n8n-webhooks/status", "n8n webhook status"),
    ],
    "Workflow Approvals (Phase 5)": [
        ("GET", "/api/v1/workflow-approvals/queue", "Workflow approval queue"),
    ],
}

def test_endpoint(method: str, path: str, description: str, timeout: int = 3) -> Dict:
    """Test a single endpoint and return results"""
    url = f"{BASE_URL}{path}"
    result = {
        "method": method,
        "path": path,
        "description": description,
        "url": url,
        "status": "UNKNOWN",
        "status_code": None,
        "response_time": None,
        "error": None,
        "response_sample": None
    }

    try:
        start_time = time.time()

        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=timeout)
        else:
            result["error"] = f"Unsupported method: {method}"
            result["status"] = "ERROR"
            return result

        result["response_time"] = round((time.time() - start_time) * 1000, 2)  # ms
        result["status_code"] = response.status_code

        # Determine status
        if response.status_code == 200:
            result["status"] = "PASS"
            # Get first 200 chars of response
            try:
                json_resp = response.json()
                result["response_sample"] = str(json_resp)[:200]
            except:
                result["response_sample"] = response.text[:200]
        elif response.status_code == 404:
            result["status"] = "NOT_FOUND"
        elif response.status_code >= 500:
            result["status"] = "SERVER_ERROR"
            result["error"] = response.text[:500]
        else:
            result["status"] = "FAIL"
            result["error"] = response.text[:500]

    except requests.exceptions.Timeout:
        result["status"] = "TIMEOUT"
        result["error"] = f"Request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        result["status"] = "CONNECTION_ERROR"
        result["error"] = "Could not connect to server"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)[:500]

    return result

def main():
    """Run all endpoint tests and generate report"""
    print("=" * 80)
    print("COMPREHENSIVE API ENDPOINT QA TEST")
    print(f"Target: {BASE_URL}")
    print("=" * 80)
    print()

    all_results = []
    category_summary = {}

    for category, endpoints in ENDPOINTS.items():
        print(f"\n{'=' * 80}")
        print(f"CATEGORY: {category}")
        print(f"{'=' * 80}")

        category_results = []

        for method, path, description in endpoints:
            print(f"\nTesting: {method} {path}")
            print(f"Description: {description}")

            result = test_endpoint(method, path, description)
            category_results.append(result)
            all_results.append(result)

            # Print result
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "🔴",
                "TIMEOUT": "⏱️",
                "CONNECTION_ERROR": "🔌",
                "NOT_FOUND": "❓",
                "SERVER_ERROR": "💥",
                "UNKNOWN": "❔"
            }.get(result["status"], "❔")

            print(f"Status: {status_icon} {result['status']}")
            if result["status_code"]:
                print(f"HTTP Status: {result['status_code']}")
            if result["response_time"]:
                print(f"Response Time: {result['response_time']}ms")
            if result["error"]:
                print(f"Error: {result['error']}")
            if result["response_sample"]:
                print(f"Response Sample: {result['response_sample']}")

        # Category summary
        category_summary[category] = {
            "total": len(category_results),
            "pass": len([r for r in category_results if r["status"] == "PASS"]),
            "fail": len([r for r in category_results if r["status"] in ["FAIL", "ERROR", "SERVER_ERROR"]]),
            "timeout": len([r for r in category_results if r["status"] == "TIMEOUT"]),
            "not_found": len([r for r in category_results if r["status"] == "NOT_FOUND"]),
        }

    # Final summary
    print(f"\n\n{'=' * 80}")
    print("FINAL SUMMARY")
    print(f"{'=' * 80}\n")

    total_tests = len(all_results)
    total_pass = len([r for r in all_results if r["status"] == "PASS"])
    total_fail = len([r for r in all_results if r["status"] in ["FAIL", "ERROR", "SERVER_ERROR"]])
    total_timeout = len([r for r in all_results if r["status"] == "TIMEOUT"])
    total_not_found = len([r for r in all_results if r["status"] == "NOT_FOUND"])

    print(f"Total Endpoints Tested: {total_tests}")
    print(f"✅ Passed: {total_pass} ({round(total_pass/total_tests*100, 1)}%)")
    print(f"❌ Failed: {total_fail} ({round(total_fail/total_tests*100, 1)}%)")
    print(f"⏱️  Timeout: {total_timeout} ({round(total_timeout/total_tests*100, 1)}%)")
    print(f"❓ Not Found: {total_not_found} ({round(total_not_found/total_tests*100, 1)}%)")

    print(f"\n{'=' * 80}")
    print("CATEGORY BREAKDOWN")
    print(f"{'=' * 80}\n")

    for category, summary in category_summary.items():
        pass_rate = round(summary["pass"] / summary["total"] * 100, 1) if summary["total"] > 0 else 0
        status_icon = "✅" if pass_rate == 100 else "⚠️" if pass_rate >= 50 else "❌"
        print(f"{status_icon} {category}: {summary['pass']}/{summary['total']} ({pass_rate}%)")

    # Export to JSON
    with open('qa_endpoint_results.json', 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "base_url": BASE_URL,
            "summary": {
                "total": total_tests,
                "passed": total_pass,
                "failed": total_fail,
                "timeout": total_timeout,
                "not_found": total_not_found
            },
            "category_summary": category_summary,
            "results": all_results
        }, f, indent=2)

    print(f"\n\n✅ Results exported to: qa_endpoint_results.json")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    main()
