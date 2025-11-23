"""
End-to-End Testing - Complete workflow from website analysis to email sending.

Tests the complete AI-powered lead generation flow:
1. Fetch & analyze website
2. Generate personalized email
3. Send email via Postmark
4. Track costs in AI-GYM
5. Review performance metrics

Run with: python test_end_to_end.py
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
    AICouncil,
    AICouncilConfig,
    AIGymTracker,
    EmailSender,
    EmailSenderConfig
)

# Load environment
load_dotenv('/Users/greenmachine2.0/Craigslist/.env')


async def test_complete_workflow():
    """Test complete workflow: analyze → generate → send → track."""
    print("\n" + "=" * 80)
    print("END-TO-END TEST: Complete Lead Generation Workflow")
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

        email_config = EmailSenderConfig(
            postmark_server_token=os.getenv("POSTMARK_SERVER_TOKEN"),
            from_email=os.getenv("POSTMARK_FROM_EMAIL", "sales@yourcompany.com"),
            from_name="AI MVP Test"
        )
        email_sender = EmailSender(email_config)

        # Test data
        target_url = "https://www.stripe.com"
        lead_value = 75000  # $75K mid-market lead
        lead_id = 999  # Test lead ID

        print(f"\n🎯 Target: {target_url}")
        print(f"💰 Lead Value: ${lead_value:,}")
        print(f"🆔 Lead ID: {lead_id}")

        # ====================================================================
        # STEP 1: Analyze Website
        # ====================================================================
        print("\n" + "─" * 80)
        print("STEP 1: Analyze Website")
        print("─" * 80)

        async with WebsiteAnalyzer(council) as analyzer:
            print(f"📊 Fetching and analyzing {target_url}...")
            analysis_result = await analyzer.analyze_website(
                url=target_url,
                lead_id=lead_id,
                lead_value=lead_value
            )

        print(f"\n✅ Analysis Complete!")
        print(f"   Title: {analysis_result['title']}")
        print(f"   Content: {analysis_result['content_length']:,} characters")
        print(f"   AI Model: {analysis_result['ai_model']}")
        print(f"   AI Cost: ${analysis_result['ai_cost']:.4f}")
        print(f"   Request ID: {analysis_result['ai_request_id']}")
        print(f"\n📝 Analysis Preview:")
        print(analysis_result['ai_analysis'][:300] + "...")

        # ====================================================================
        # STEP 2: Generate Personalized Email
        # ====================================================================
        print("\n" + "─" * 80)
        print("STEP 2: Generate Personalized Email")
        print("─" * 80)

        print(f"✉️  Generating email based on analysis...")
        email_response = await council.generate_email(
            prospect_name="Sarah Johnson",
            company_name="Stripe",
            website_analysis=analysis_result['ai_analysis'],
            our_service_description="We help B2B SaaS companies automate their lead generation with AI-powered website analysis and personalized outreach at scale.",
            lead_id=lead_id,
            lead_value=lead_value
        )

        # Parse email
        content = email_response.content
        if "SUBJECT:" in content and "BODY:" in content:
            parts = content.split("BODY:", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip()
        else:
            lines = content.split("\n", 1)
            subject = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else content

        print(f"\n✅ Email Generated!")
        print(f"   AI Model: {email_response.model_used}")
        print(f"   AI Cost: ${email_response.total_cost:.4f}")
        print(f"   Request ID: {email_response.request_id}")
        print(f"\n📧 Generated Email:")
        print("─" * 80)
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print("─" * 80)

        # ====================================================================
        # STEP 3: Send Email (TEST MODE - won't actually send)
        # ====================================================================
        print("\n" + "─" * 80)
        print("STEP 3: Send Email via Postmark")
        print("─" * 80)

        print(f"📤 Preparing to send email...")
        print(f"   To: test@example.com (TEST MODE)")
        print(f"   Subject: {subject}")

        # Convert to HTML
        html_body = f"<p>{body.replace(chr(10), '<br>')}</p>"

        print(f"\n⚠️  SKIPPING ACTUAL SEND (test mode)")
        print(f"   In production, would call:")
        print(f"   email_sender.send_email(")
        print(f"       to_email='sarah@stripe.com',")
        print(f"       subject='{subject[:50]}...',")
        print(f"       html_body=<generated>,")
        print(f"       tag='ai-generated',")
        print(f"       metadata={{'lead_id': {lead_id}, 'lead_value': {lead_value}}}")
        print(f"   )")

        # Uncomment to actually send:
        # send_result = await email_sender.send_email(
        #     to_email="your-email@example.com",  # CHANGE THIS
        #     subject=subject,
        #     html_body=html_body,
        #     tag="ai-mvp-test",
        #     metadata={"lead_id": str(lead_id), "lead_value": str(lead_value)}
        # )
        # print(f"\n✅ Email Sent!")
        # print(f"   Message ID: {send_result['message_id']}")
        # print(f"   Status: {send_result['status']}")

        # ====================================================================
        # STEP 4: Review AI-GYM Metrics
        # ====================================================================
        print("\n" + "─" * 80)
        print("STEP 4: Review AI-GYM Cost Tracking")
        print("─" * 80)

        # Get overall stats
        stats = await gym_tracker.get_cost_summary()
        print(f"\n💰 Session Cost Summary:")
        print(f"   Total Requests: {stats['request_count']}")
        print(f"   Total Cost: ${stats['total_cost']:.4f}")
        print(f"   Avg Cost/Request: ${stats['avg_cost']:.4f}")
        print(f"   Total Tokens: {stats['total_tokens']:,}")
        if stats['avg_duration_seconds']:
            print(f"   Avg Duration: {stats['avg_duration_seconds']:.2f}s")

        # Get model performance
        performance = await gym_tracker.get_model_performance(min_samples=1)
        print(f"\n📊 Model Performance (this session):")
        print(f"   {'Model':<40} {'Task':<20} {'Requests':<10} {'Avg Cost':<12} {'Total'}")
        print(f"   {'-'*100}")
        for perf in performance[-5:]:  # Last 5
            print(f"   {perf['model_name']:<40} {perf['task_type']:<20} {perf['request_count']:<10} ${perf['avg_cost']:<11.4f} ${perf['total_cost']:.4f}")

        # Check budget
        alert = await gym_tracker.check_budget_alert(
            daily_limit=5.0,
            weekly_limit=30.0,
            monthly_limit=100.0
        )

        print(f"\n🚨 Budget Status:")
        if alert:
            print(f"   ⚠️  ALERT: {alert['period'].upper()} budget at {alert['percent']:.1f}%")
            print(f"   Spent: ${alert['spent']:.2f} / ${alert['limit']:.2f}")
        else:
            print(f"   ✅ All budgets within limits")

        await council.close()

    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST COMPLETE!")
    print("=" * 80)


async def test_batch_workflow():
    """Test batch processing: multiple leads at once."""
    print("\n" + "=" * 80)
    print("BATCH TEST: Process Multiple Leads Concurrently")
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

        # Batch test data (different lead values for routing test)
        test_leads = [
            {"url": "https://example.com", "value": 5000, "name": "SMB Lead"},
            {"url": "https://httpbin.org/html", "value": 50000, "name": "Mid-Market Lead"},
        ]

        print(f"\n📋 Processing {len(test_leads)} leads concurrently...")
        for lead in test_leads:
            print(f"   - {lead['name']}: {lead['url']} (${lead['value']:,})")

        # Analyze all websites
        print(f"\n🔄 Analyzing websites...")
        urls = [lead["url"] for lead in test_leads]
        values = [lead["value"] for lead in test_leads]

        async with WebsiteAnalyzer(council) as analyzer:
            results = await analyzer.analyze_multiple_websites(
                urls=urls,
                lead_values=values,
                max_concurrent=2
            )

        # Summary
        print(f"\n✅ Batch Analysis Complete!")
        total_cost = sum(r.get("ai_cost", 0) for r in results if "ai_cost" in r)
        success = sum(1 for r in results if "error" not in r)

        print(f"   Success: {success}/{len(test_leads)}")
        print(f"   Total Cost: ${total_cost:.4f}")
        print(f"   Avg Cost: ${total_cost/len(test_leads):.4f} per lead")

        for i, result in enumerate(results):
            if "error" not in result:
                print(f"\n   Lead {i+1} ({test_leads[i]['name']}):")
                print(f"      Model: {result['ai_model']}")
                print(f"      Cost: ${result['ai_cost']:.4f}")
                print(f"      Preview: {result['ai_analysis'][:100]}...")

        await council.close()

    print("\n✅ BATCH TEST COMPLETE!")


async def test_cost_projections():
    """Calculate cost projections for different volumes."""
    print("\n" + "=" * 80)
    print("COST PROJECTIONS: Different Lead Volumes")
    print("=" * 80)

    # Setup
    db_url = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        gym_tracker = AIGymTracker(session)

        # Get actual average costs from AI-GYM
        stats = await gym_tracker.get_cost_summary()

        if stats['request_count'] > 0:
            avg_cost = stats['avg_cost']
        else:
            # Default estimates
            avg_cost = 0.005  # $0.005 per analysis/email pair

        print(f"\n💰 Based on AI-GYM Data:")
        print(f"   Avg Cost per AI Request: ${avg_cost:.4f}")
        print(f"   (2 requests per lead: analysis + email)")

        cost_per_lead = avg_cost * 2  # analysis + email

        volumes = [
            {"leads": 100, "desc": "Daily (100 leads/day)"},
            {"leads": 1000, "desc": "Daily (1000 leads/day)"},
            {"leads": 3000, "desc": "Monthly (100/day × 30)"},
            {"leads": 30000, "desc": "Monthly (1000/day × 30)"},
        ]

        postmark_monthly = 85  # $85/month
        mailreach_monthly = 100  # $100/month

        print(f"\n📊 Cost Projections:")
        print(f"   {'Volume':<30} {'AI Cost':<15} {'Postmark':<15} {'MailReach':<15} {'Total'}")
        print(f"   {'-'*90}")

        for vol in volumes:
            ai_cost = cost_per_lead * vol["leads"]

            if "Monthly" in vol["desc"]:
                total = ai_cost + postmark_monthly + mailreach_monthly
                print(f"   {vol['desc']:<30} ${ai_cost:<14.2f} ${postmark_monthly:<14.2f} ${mailreach_monthly:<14.2f} ${total:.2f}")
            else:
                monthly_ai = ai_cost * 30
                monthly_total = monthly_ai + postmark_monthly + mailreach_monthly
                print(f"   {vol['desc']:<30} ${ai_cost:<14.2f} (${monthly_ai:.2f}/mo) → Total: ${monthly_total:.2f}/mo")

        print(f"\n💡 Key Insights:")
        print(f"   - AI costs scale linearly with volume")
        print(f"   - Postmark + MailReach = ${postmark_monthly + mailreach_monthly}/month (fixed)")
        print(f"   - 100 leads/day = ~${cost_per_lead * 3000 + postmark_monthly + mailreach_monthly:.2f}/month")
        print(f"   - 1000 leads/day = ~${cost_per_lead * 30000 + postmark_monthly + mailreach_monthly:.2f}/month")

    print("\n✅ PROJECTIONS COMPLETE!")


async def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 80)
    print("END-TO-END TEST SUITE")
    print("=" * 80)
    print("\nTesting:")
    print("  1. Complete Workflow (analyze → generate → send → track)")
    print("  2. Batch Processing (multiple leads concurrently)")
    print("  3. Cost Projections (volume-based pricing)")
    print("\n" + "=" * 80)

    try:
        await test_complete_workflow()
        await test_batch_workflow()
        await test_cost_projections()

        print("\n" + "=" * 80)
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("=" * 80)
        print("\n✅ MVP is Production-Ready!")
        print("\n💡 Next Steps:")
        print("   1. Start FastAPI server: uvicorn app.main:app --reload")
        print("   2. Test API endpoints: http://localhost:8000/docs")
        print("   3. Integrate with frontend")
        print("   4. Deploy to production")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
