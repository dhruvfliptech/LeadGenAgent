"""
Test Website Analyzer - Fetch & analyze real websites.

Run with: python test_website_analyzer.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, '/Users/greenmachine2.0/Craigslist/backend')

from app.services.ai_mvp import (
    WebsiteAnalyzer,
    analyze_website_quick,
    AICouncil,
    AICouncilConfig,
    AIGymTracker
)

# Load environment
load_dotenv('/Users/greenmachine2.0/Craigslist/.env')


async def test_single_website():
    """Test analyzing a single website."""
    print("\n" + "=" * 80)
    print("TEST 1: Analyze Single Website (example.com)")
    print("=" * 80)

    # Setup
    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Initialize services
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        # Test website analysis
        url = "https://example.com"
        lead_value = 10000  # $10K lead → cheap model

        print(f"\n🌐 Analyzing: {url}")
        print(f"💰 Lead Value: ${lead_value:,}")

        result = await analyze_website_quick(
            url=url,
            ai_council=council,
            lead_value=lead_value
        )

        print(f"\n✅ Analysis Complete!")
        print(f"   Title: {result['title']}")
        print(f"   Meta: {result['meta_description'][:100]}...")
        print(f"   Content Length: {result['content_length']:,} chars")
        print(f"   AI Model: {result['ai_model']}")
        print(f"   AI Cost: ${result['ai_cost']:.4f}")
        print(f"\n📊 AI Analysis:")
        print("-" * 80)
        print(result['ai_analysis'])
        print("-" * 80)

        await council.close()

    print("\n✅ TEST 1 PASSED!\n")


async def test_multiple_websites():
    """Test analyzing multiple websites concurrently."""
    print("\n" + "=" * 80)
    print("TEST 2: Analyze Multiple Websites (Batch)")
    print("=" * 80)

    # Setup
    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        # Test websites with different lead values
        test_sites = [
            {"url": "https://example.com", "value": 5000},
            {"url": "https://httpbin.org/html", "value": 30000},
        ]

        urls = [site["url"] for site in test_sites]
        values = [site["value"] for site in test_sites]

        print(f"\n🌐 Analyzing {len(urls)} websites concurrently...")
        for site in test_sites:
            print(f"   - {site['url']} (${site['value']:,} lead)")

        async with WebsiteAnalyzer(council) as analyzer:
            results = await analyzer.analyze_multiple_websites(
                urls=urls,
                lead_values=values,
                max_concurrent=2
            )

        print(f"\n✅ Batch Analysis Complete!")
        for i, result in enumerate(results):
            if "error" in result:
                print(f"\n❌ Site {i+1}: {result['url']}")
                print(f"   Error: {result['error']}")
            else:
                print(f"\n✅ Site {i+1}: {result['url']}")
                print(f"   Model: {result['ai_model']}")
                print(f"   Cost: ${result['ai_cost']:.4f}")
                print(f"   Analysis Preview: {result['ai_analysis'][:150]}...")

        # Check total costs
        stats = await gym_tracker.get_cost_summary()
        print(f"\n💰 Total Session Cost: ${stats['total_cost']:.4f}")
        print(f"   Total Requests: {stats['request_count']}")

        await council.close()

    print("\n✅ TEST 2 PASSED!\n")


async def test_real_business_website():
    """Test with a real business website."""
    print("\n" + "=" * 80)
    print("TEST 3: Analyze Real Business Website")
    print("=" * 80)

    # Setup
    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        # Real business website
        url = "https://www.stripe.com"  # Public, well-structured site
        lead_value = 100000  # $100K enterprise lead → premium model

        print(f"\n🌐 Analyzing: {url}")
        print(f"💰 Lead Value: ${lead_value:,} (enterprise)")
        print(f"🎯 Expected Model: Premium (Claude Sonnet)")

        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_website(
                url=url,
                lead_value=lead_value
            )

        print(f"\n✅ Analysis Complete!")
        print(f"   Title: {result['title']}")
        print(f"   Status: {result['status_code']}")
        print(f"   Content: {result['content_length']:,} chars")
        print(f"   AI Model: {result['ai_model']}")
        print(f"   AI Cost: ${result['ai_cost']:.4f}")
        print(f"\n📊 Business Analysis:")
        print("-" * 80)
        print(result['ai_analysis'])
        print("-" * 80)

        await council.close()

    print("\n✅ TEST 3 PASSED!\n")


async def main():
    """Run all website analyzer tests."""
    print("\n" + "=" * 80)
    print("WEBSITE ANALYZER TEST SUITE")
    print("=" * 80)
    print("\nTesting:")
    print("  1. Single website analysis (example.com)")
    print("  2. Batch website analysis (concurrent)")
    print("  3. Real business website (stripe.com)")
    print("\n" + "=" * 80)

    try:
        await test_single_website()
        await test_multiple_websites()
        await test_real_business_website()

        print("\n" + "=" * 80)
        print("✅ SUCCESS: All Website Analyzer tests passed!")
        print("=" * 80)
        print("\n💡 Next: Test the complete workflow (scrape → analyze → email → send)")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
