#!/usr/bin/env python3
"""
API Test Runner with Comprehensive Reporting

Runs all API endpoint tests and generates a detailed report.
"""

import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path


def run_tests():
    """Run pytest and capture results."""
    print("=" * 80)
    print("COMPREHENSIVE API ENDPOINT TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test configuration
    test_file = "tests/test_api_comprehensive.py"
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report = report_dir / f"test_results_{timestamp}.json"
    html_report = report_dir / f"test_results_{timestamp}.html"

    print(f"Test file: {test_file}")
    print(f"JSON report: {json_report}")
    print(f"HTML report: {html_report}")
    print()

    # Run pytest with various reporters
    cmd = [
        "pytest",
        test_file,
        "-v",  # Verbose
        "--tb=short",  # Short traceback
        "-s",  # Show print statements
        "--durations=10",  # Show 10 slowest tests
        f"--json-report",
        f"--json-report-file={json_report}",
        "--json-report-indent=2",
        "--html", str(html_report),
        "--self-contained-html",
        "--color=yes"
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        elapsed = time.time() - start_time

        print("=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print(result.stdout)

        if result.stderr:
            print("\nERRORS:")
            print(result.stderr)

        print(f"\nTotal execution time: {elapsed:.2f} seconds")
        print(f"\nExit code: {result.returncode}")

        # Parse JSON report if available
        if json_report.exists():
            try:
                with open(json_report) as f:
                    report_data = json.load(f)
                    print_summary(report_data)
            except Exception as e:
                print(f"Failed to parse JSON report: {e}")

        return result.returncode

    except subprocess.TimeoutExpired:
        print("\nERROR: Tests timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"\nERROR: Test execution failed: {e}")
        return 1


def print_summary(report_data):
    """Print test summary from JSON report."""
    summary = report_data.get("summary", {})

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    errors = summary.get("error", 0)

    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)" if total > 0 else "Passed: 0")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")

    duration = report_data.get("duration", 0)
    print(f"\nDuration: {duration:.2f} seconds")

    # Test categories
    tests = report_data.get("tests", [])
    if tests:
        print("\n" + "=" * 80)
        print("TEST CATEGORIES")
        print("=" * 80)

        categories = {}
        for test in tests:
            nodeid = test.get("nodeid", "")
            if "::" in nodeid:
                class_name = nodeid.split("::")[1] if "::" in nodeid else "Unknown"
                categories[class_name] = categories.get(class_name, 0) + 1

        for category, count in sorted(categories.items()):
            print(f"{category}: {count} tests")

    # Failed tests detail
    failed_tests = [t for t in tests if t.get("outcome") == "failed"]
    if failed_tests:
        print("\n" + "=" * 80)
        print("FAILED TESTS DETAIL")
        print("=" * 80)

        for test in failed_tests:
            print(f"\n{test.get('nodeid', 'Unknown test')}")
            if "call" in test and "longrepr" in test["call"]:
                print(f"  {test['call']['longrepr'][:200]}...")


def main():
    """Main entry point."""
    exit_code = run_tests()

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 80)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
