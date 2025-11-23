"""
Test script for Phase 3 Enhanced Website Analyzer.

This script tests all new analysis methods added to the WebsiteAnalyzer.

Usage:
    python test_phase3_analyzer.py

    Or with custom URL:
    python test_phase3_analyzer.py https://example.com
"""

import asyncio
import sys
import os
import json
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.ai_mvp import (
    WebsiteAnalyzer,
    AICouncil,
    AICouncilConfig
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_score(category: str, score: int):
    """Print a score with color coding."""
    color = "\033[92m" if score >= 80 else "\033[93m" if score >= 60 else "\033[91m"
    reset = "\033[0m"
    print(f"{category}: {color}{score}/100{reset}")


def print_issues_strengths(issues: list, strengths: list):
    """Print issues and strengths."""
    if issues:
        print("\n  Issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"    - {issue}")
        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more issues")

    if strengths:
        print("\n  Strengths:")
        for strength in strengths[:5]:  # Show first 5
            print(f"    + {strength}")
        if len(strengths) > 5:
            print(f"    ... and {len(strengths) - 5} more strengths")


async def test_design_analysis(analyzer: WebsiteAnalyzer, url: str, use_ai: bool = False):
    """Test design quality analysis."""
    print_section("Design Quality Analysis")

    try:
        result = await analyzer.analyze_design_quality(url, use_ai=use_ai)

        print_score("Design Score", result['score'])
        print_issues_strengths(result['issues'], result['strengths'])

        print("\n  Metrics:")
        print(f"    - Layout: {result['metrics']['layout_type']}")
        print(f"    - Colors: {result['metrics']['color_scheme']['color_count']} unique")
        print(f"    - Fonts: {result['metrics']['typography']['font_count']} families")
        print(f"    - Responsive: {result['metrics']['responsiveness']['likely_responsive']}")
        print(f"    - Whitespace: {result['metrics']['whitespace']['estimated_whitespace']}")

        if use_ai and result.get('ai_assessment'):
            print(f"\n  AI Assessment:\n    {result['ai_assessment'][:200]}...")

        return True

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False


async def test_seo_analysis(analyzer: WebsiteAnalyzer, url: str):
    """Test SEO analysis."""
    print_section("SEO Analysis")

    try:
        result = await analyzer.analyze_seo(url)

        print_score("SEO Score", result['score'])
        print_issues_strengths(result['issues'], result['strengths'])

        print("\n  Details:")
        title = result['details']['title']
        print(f"    - Title: '{title['text'][:50]}...' ({title['length']} chars)")

        desc = result['details']['meta_description']
        if desc['text']:
            print(f"    - Description: '{desc['text'][:50]}...' ({desc['length']} chars)")
        else:
            print(f"    - Description: Missing")

        headings = result['details']['headings']
        print(f"    - Headings: H1={headings['h1']}, H2={headings['h2']}, H3={headings['h3']}")

        images = result['details']['images']
        print(f"    - Images: {images['total']} total, {images['alt_coverage']}% with alt text")

        links = result['details']['links']
        print(f"    - Links: {links['internal']} internal, {links['external']} external")

        print(f"    - Mobile-friendly: {result['details']['mobile_friendly']}")
        print(f"    - Schema markup: {result['details']['schema_markup']}")
        print(f"    - Open Graph: {result['details']['open_graph']}")

        return True

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False


async def test_performance_analysis(analyzer: WebsiteAnalyzer, url: str):
    """Test performance analysis."""
    print_section("Performance Analysis")
    print("  Note: This may take 10-30 seconds...\n")

    try:
        result = await analyzer.analyze_performance(url)

        print_score("Performance Score", result['score'])
        print_issues_strengths(result['issues'], result['strengths'])

        print("\n  Metrics:")
        times = result['metrics']['load_times']
        print(f"    - DOM Content Loaded: {times['dom_content_loaded']:.2f}s")
        print(f"    - Full Load: {times['full_load']:.2f}s")

        resources = result['metrics']['resources']
        print(f"    - Total Size: {resources['total_size_mb']:.2f} MB")
        print(f"    - Resources: {resources['total_count']} total")
        print(f"    - Scripts: {resources['scripts']} external + {resources['inline_scripts']} inline")
        print(f"    - Stylesheets: {resources['stylesheets']} external + {resources['inline_styles']} inline")
        print(f"    - Images: {resources['images']}")

        opt = result['metrics']['optimization']
        print(f"    - Large Images: {opt['large_images']} over 500KB")
        print(f"    - Render-blocking: {opt['render_blocking']}")

        return True

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False


async def test_accessibility_analysis(analyzer: WebsiteAnalyzer, url: str):
    """Test accessibility analysis."""
    print_section("Accessibility Analysis")

    try:
        result = await analyzer.analyze_accessibility(url)

        print_score("Accessibility Score", result['score'])
        print_issues_strengths(result['issues'], result['strengths'])

        print("\n  Details:")
        aria = result['details']['aria']
        print(f"    - ARIA Labels: {aria['labels']}")
        print(f"    - ARIA Roles: {aria['roles']}")

        semantic = result['details']['semantic_html']
        used_tags = [tag for tag, count in semantic.items() if count > 0]
        print(f"    - Semantic HTML: {', '.join(used_tags) if used_tags else 'None'}")

        forms = result['details']['forms']
        print(f"    - Form Labels: {forms['with_labels']}/{forms['total_inputs']} ({forms['label_coverage']:.0f}%)")

        images = result['details']['images']
        print(f"    - Image Alt Text: {images['with_alt']}/{images['total']} ({images['alt_coverage']:.0f}%)")

        links = result['details']['links']
        print(f"    - Link Text: {links['with_text']}/{links['total']} ({links['text_coverage']:.0f}%)")

        print(f"    - Language: {result['details']['language'] or 'Not specified'}")
        print(f"    - Skip Link: {result['details']['skip_link']}")
        print(f"    - Keyboard Nav: {result['details']['keyboard_navigation']}")

        return True

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False


async def test_comprehensive_analysis(analyzer: WebsiteAnalyzer, url: str):
    """Test comprehensive analysis."""
    print_section("Comprehensive Analysis")
    print("  Note: This runs all analyses and may take 15-45 seconds...\n")

    try:
        result = await analyzer.analyze_website_comprehensive(
            url=url,
            include_ai_design=False  # Set to True to enable AI assessment
        )

        # Overall score
        overall = result['overall_score']
        color = "\033[92m" if overall >= 80 else "\033[93m" if overall >= 60 else "\033[91m"
        reset = "\033[0m"
        print(f"  Overall Score: {color}{overall:.1f}/100{reset}\n")

        # Individual scores
        print("  Category Scores:")
        print_score("  - Design", result['design']['score'])
        print_score("  - SEO", result['seo']['score'])
        print_score("  - Performance", result['performance']['score'])
        print_score("  - Accessibility", result['accessibility']['score'])

        # Summary
        print("\n  Top Issues Across All Categories:")
        all_issues = (
            result['design']['issues'][:2] +
            result['seo']['issues'][:2] +
            result['performance']['issues'][:2] +
            result['accessibility']['issues'][:2]
        )
        for issue in all_issues[:8]:
            print(f"    - {issue}")

        print("\n  Top Strengths Across All Categories:")
        all_strengths = (
            result['design']['strengths'][:2] +
            result['seo']['strengths'][:2] +
            result['performance']['strengths'][:2] +
            result['accessibility']['strengths'][:2]
        )
        for strength in all_strengths[:8]:
            print(f"    + {strength}")

        return True

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        return False


async def main():
    """Main test function."""
    # Get URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

    print("\n" + "=" * 80)
    print("  Phase 3 Enhanced Website Analyzer - Test Suite")
    print("=" * 80)
    print(f"\n  Testing URL: {url}")
    print(f"  Note: Some tests require browser automation and may take time.\n")

    # Check for OpenRouter API key (optional, only needed for AI assessment)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("  Warning: OPENROUTER_API_KEY not found. AI assessment will be skipped.\n")

    # Initialize AI Council (needed even if not using AI features)
    ai_config = AICouncilConfig(
        openrouter_api_key=api_key or "dummy-key"
    )
    ai_council = AICouncil(ai_config, gym_tracker=None)

    # Run tests
    results = {
        'design': False,
        'seo': False,
        'performance': False,
        'accessibility': False,
        'comprehensive': False
    }

    try:
        async with WebsiteAnalyzer(ai_council) as analyzer:
            # Test each analysis type
            results['design'] = await test_design_analysis(analyzer, url, use_ai=bool(api_key))
            results['seo'] = await test_seo_analysis(analyzer, url)
            results['performance'] = await test_performance_analysis(analyzer, url)
            results['accessibility'] = await test_accessibility_analysis(analyzer, url)
            results['comprehensive'] = await test_comprehensive_analysis(analyzer, url)

    finally:
        await ai_council.close()

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "\033[92mPASSED\033[0m" if passed_test else "\033[91mFAILED\033[0m"
        print(f"  {test_name.capitalize()}: {status}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  \033[92mAll tests passed successfully!\033[0m")
        print("\n  The Phase 3 enhanced website analyzer is working correctly.")
    else:
        print("\n  \033[91mSome tests failed.\033[0m")
        print("\n  Please check the errors above and ensure:")
        print("    1. The backend server is running")
        print("    2. Playwright is properly installed (playwright install)")
        print("    3. The URL is accessible")
        print("    4. Network connectivity is available")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
