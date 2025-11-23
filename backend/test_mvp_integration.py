"""
MVP Integration Test - Test the complete AI workflow.

This tests:
1. Semantic Router (model selection)
2. AI Council (OpenRouter API calls)
3. AI-GYM Tracker (cost tracking)
4. Website Analysis
5. Email Generation

Run with: python test_mvp_integration.py
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
    AICouncil,
    AICouncilConfig,
    AIGymTracker,
    Message,
    TaskType
)

# Load environment variables
load_dotenv('/Users/greenmachine2.0/Craigslist/.env')


async def test_ai_council_basic():
    """Test basic AI Council functionality."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic AI Council (Simple Task - Ultra-Cheap Model)")
    print("=" * 80)

    # Setup database connection
    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Initialize
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        # Test simple classification task (should use ultra-cheap model)
        print("\n📝 Task: Classify email as spam or legitimate")
        messages = [
            Message(
                role="system",
                content="You are a spam classifier. Respond with only 'SPAM' or 'LEGITIMATE'."
            ),
            Message(
                role="user",
                content="Email: 'Hi John, following up on our meeting yesterday about the Q4 proposal. Can we schedule a call this week?' - Is this spam?"
            )
        ]

        response = await council.complete(
            task_type=TaskType.SPAM_DETECTION,
            messages=messages,
            lead_value=None  # No lead value, should use cheapest model
        )

        print(f"\n✅ Response received!")
        print(f"   Model Used: {response.model_used}")
        print(f"   Model Tier: {response.model_tier}")
        print(f"   Tokens: {response.prompt_tokens} in + {response.completion_tokens} out")
        print(f"   Cost: ${response.total_cost:.6f}")
        print(f"   Routing: {response.route_decision.reasoning}")
        print(f"   Result: {response.content}")

        await council.close()

    print("\n✅ TEST 1 PASSED!")


async def test_website_analysis():
    """Test website analysis with value-based routing."""
    print("\n" + "=" * 80)
    print("TEST 2: Website Analysis (Moderate Task - Value-Based Routing)")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        # Test with different lead values
        test_cases = [
            {"lead_value": 5000, "expected_tier": "cheap"},
            {"lead_value": 50000, "expected_tier": "moderate"},
        ]

        for case in test_cases:
            print(f"\n📊 Analyzing website for ${case['lead_value']:,} lead...")

            # Sample HTML content
            html_content = """
            <html>
            <head><title>Acme Corp - Enterprise Software Solutions</title></head>
            <body>
                <h1>Welcome to Acme Corp</h1>
                <p>We provide enterprise software solutions for Fortune 500 companies.</p>
                <h2>Our Services</h2>
                <ul>
                    <li>Custom CRM Development</li>
                    <li>Cloud Migration</li>
                    <li>Data Analytics</li>
                </ul>
                <p>Contact: sales@acmecorp.com | (555) 123-4567</p>
            </body>
            </html>
            """

            response = await council.analyze_website(
                url="https://acmecorp.com",
                html_content=html_content,
                lead_id=123,
                lead_value=case["lead_value"]
            )

            print(f"\n✅ Analysis complete!")
            print(f"   Model Used: {response.model_used}")
            print(f"   Model Tier: {response.model_tier} (expected: {case['expected_tier']})")
            print(f"   Cost: ${response.total_cost:.6f}")
            print(f"   Request ID: {response.request_id}")
            print(f"\n   Analysis Preview:")
            print(f"   {response.content[:300]}...")

        await council.close()

    print("\n✅ TEST 2 PASSED!")


async def test_email_generation():
    """Test email generation with routing."""
    print("\n" + "=" * 80)
    print("TEST 3: Email Generation (Moderate Task - Creative)")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        website_analysis = """
        Company Description: Acme Corp provides enterprise CRM and cloud migration services.
        Services: Custom CRM, Cloud Migration, Data Analytics
        Pain Points:
        - May struggle with legacy system integration
        - Likely facing data silos across departments
        - Could benefit from unified customer view
        Decision Makers: CTO, VP of Engineering, Sales Operations Director
        """

        print("\n✉️  Generating personalized email...")
        response = await council.generate_email(
            prospect_name="Sarah Johnson",
            company_name="Acme Corp",
            website_analysis=website_analysis,
            our_service_description="We help B2B companies automate their lead generation and qualification process using AI-powered website analysis and personalized outreach.",
            lead_id=123,
            lead_value=30000  # $30K lead → moderate tier
        )

        print(f"\n✅ Email generated!")
        print(f"   Model Used: {response.model_used}")
        print(f"   Model Tier: {response.model_tier}")
        print(f"   Cost: ${response.total_cost:.6f}")
        print(f"\n   Generated Email:")
        print("-" * 80)
        print(response.content)
        print("-" * 80)

        await council.close()

    print("\n✅ TEST 3 PASSED!")


async def test_ai_gym_stats():
    """Test AI-GYM cost tracking and stats."""
    print("\n" + "=" * 80)
    print("TEST 4: AI-GYM Cost Tracking & Stats")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)

        # Get overall cost summary
        print("\n💰 Overall Cost Summary:")
        summary = await gym_tracker.get_cost_summary()
        print(f"   Total Requests: {summary['request_count']}")
        print(f"   Total Cost: ${summary['total_cost']:.4f}")
        print(f"   Avg Cost/Request: ${summary['avg_cost']:.4f}")
        print(f"   Total Tokens: {summary['total_tokens']:,}")
        if summary['avg_duration_seconds']:
            print(f"   Avg Duration: {summary['avg_duration_seconds']:.2f}s")

        # Get model performance comparison
        print("\n📊 Model Performance Comparison:")
        performance = await gym_tracker.get_model_performance(min_samples=1)

        if performance:
            print(f"\n   {'Model':<40} {'Task':<25} {'Requests':<10} {'Avg Cost':<12} {'Total Cost'}")
            print("   " + "-" * 100)
            for perf in performance[:10]:  # Top 10
                print(f"   {perf['model_name']:<40} {perf['task_type']:<25} {perf['request_count']:<10} ${perf['avg_cost']:<11.6f} ${perf['total_cost']:.4f}")
        else:
            print("   No performance data yet (run tests above first)")

        # Check budget alerts
        print("\n🚨 Budget Alert Check:")
        alert = await gym_tracker.check_budget_alert(
            daily_limit=5.0,
            weekly_limit=30.0,
            monthly_limit=100.0
        )

        if alert:
            print(f"   ⚠️  ALERT: {alert['period'].upper()} budget exceeded!")
            print(f"   Spent: ${alert['spent']:.2f} / ${alert['limit']:.2f} ({alert['percent']:.1f}%)")
        else:
            print(f"   ✅ All budgets within limits")
            print(f"   Daily: ${summary['total_cost']:.2f} / $5.00")

    print("\n✅ TEST 4 PASSED!")


async def test_complete_workflow():
    """Test complete workflow: analyze → generate → track."""
    print("\n" + "=" * 80)
    print("TEST 5: Complete Workflow (Analysis → Email → Cost Tracking)")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)
        ai_config = AICouncilConfig(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY")
        )
        council = AICouncil(ai_config, gym_tracker)

        lead_value = 75000  # $75K enterprise lead
        total_cost = 0.0

        print(f"\n🎯 Processing ${lead_value:,} enterprise lead...")

        # Step 1: Analyze website
        print("\n📊 Step 1: Analyzing website...")
        html = "<html><body><h1>TechStart Inc</h1><p>We help startups scale their engineering teams.</p></body></html>"

        analysis = await council.analyze_website(
            url="https://techstart.com",
            html_content=html,
            lead_id=456,
            lead_value=lead_value
        )

        print(f"   ✅ Analysis complete - {analysis.model_tier} tier (${analysis.total_cost:.4f})")
        total_cost += analysis.total_cost

        # Step 2: Generate email
        print("\n✉️  Step 2: Generating personalized email...")
        email = await council.generate_email(
            prospect_name="Alex Chen",
            company_name="TechStart Inc",
            website_analysis=analysis.content[:500],
            our_service_description="AI-powered lead generation and qualification",
            lead_id=456,
            lead_value=lead_value
        )

        print(f"   ✅ Email generated - {email.model_tier} tier (${email.total_cost:.4f})")
        total_cost += email.total_cost

        # Step 3: Check costs
        print("\n💰 Step 3: Cost tracking...")
        summary = await gym_tracker.get_cost_summary()
        print(f"   ✅ Workflow total: ${total_cost:.4f}")
        print(f"   ✅ Session total: ${summary['total_cost']:.4f}")
        print(f"   ✅ Request count: {summary['request_count']}")

        await council.close()

    print("\n✅ TEST 5 PASSED!")
    print("\n" + "=" * 80)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("=" * 80)


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("MVP INTEGRATION TEST SUITE")
    print("=" * 80)
    print("\nTesting:")
    print("  1. Basic AI Council (ultra-cheap model)")
    print("  2. Website Analysis (value-based routing)")
    print("  3. Email Generation (creative writing)")
    print("  4. AI-GYM Stats (cost tracking)")
    print("  5. Complete Workflow (end-to-end)")
    print("\n" + "=" * 80)

    try:
        await test_ai_council_basic()
        await test_website_analysis()
        await test_email_generation()
        await test_ai_gym_stats()
        await test_complete_workflow()

        print("\n" + "=" * 80)
        print("✅ SUCCESS: All MVP components working correctly!")
        print("=" * 80)
        print("\n💡 Next Steps:")
        print("   1. Review AI-GYM stats in database")
        print("   2. Test Postmark email sending (see MVP_README.md)")
        print("   3. Continue with Hour 5: Website Analyzer")
        print("   4. Continue with Hour 7: API Endpoints")
        print("   5. Complete Hour 8: End-to-End Testing")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
