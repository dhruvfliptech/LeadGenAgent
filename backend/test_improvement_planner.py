"""
Test script for ImprovementPlanner service.

Demonstrates how to use the improvement planner with sample website analysis data.
"""

import asyncio
import os
from app.services.improvement_planner import ImprovementPlanner
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker


# Sample website analysis result (from WebsiteAnalyzer)
SAMPLE_ANALYSIS = {
    "url": "https://example-business.com",
    "title": "ABC Web Design - Professional Website Development Services in NYC",
    "meta_description": "We build websites.",
    "status_code": 200,
    "content_length": 5432,
    "ai_analysis": """
    BUSINESS ANALYSIS:
    - Company: ABC Web Design
    - Industry: Web Development Services
    - Location: New York City
    - Target Market: Small businesses looking for website development

    STRENGTHS:
    - Clean, professional design
    - Clear service offerings
    - Good portfolio section

    ISSUES IDENTIFIED:
    - Meta description is too short (only 17 characters)
    - No clear call-to-action above the fold
    - Mobile responsiveness issues on tablet devices
    - Slow page load time (4.2 seconds)
    - Poor color contrast on CTA buttons (2.3:1 ratio)
    - Missing alt text on several images
    - No structured data for SEO
    - Contact form is below the fold and hard to find

    CONVERSION OPPORTUNITIES:
    - Add prominent "Get Free Quote" CTA above the fold
    - Add social proof (testimonials, client logos)
    - Improve trust signals (certifications, awards)
    - Add live chat for immediate engagement

    TECHNICAL OBSERVATIONS:
    - Built with WordPress
    - Not using lazy loading for images
    - Large uncompressed images (500KB+)
    - No caching headers
    - Mixed HTTP/HTTPS content
    """,
    "ai_model": "anthropic/claude-sonnet-4",
    "ai_cost": 0.015,
    "ai_request_id": 1,
    "lead_id": None,
    "lead_value": 500.0
}


async def main():
    """Run improvement planner test."""

    # Check for OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY not set. Using rule-based improvements only.")
        print("Set OPENROUTER_API_KEY to enable AI-powered improvements.\n")
        use_ai = False
    else:
        print(f"✓ OpenRouter API key found: {openrouter_key[:10]}...")
        use_ai = True

    # Initialize AI Council (if API key available)
    if use_ai:
        config = AICouncilConfig(
            openrouter_api_key=openrouter_key,
            default_temperature=0.7,
            default_max_tokens=3000,
            timeout_seconds=30
        )

        # Optional: Initialize AI-GYM tracker (requires database)
        # For testing, we'll skip it
        gym_tracker = None

        ai_council = AICouncil(config=config, gym_tracker=gym_tracker)
    else:
        # Create a mock AI Council that won't make API calls
        ai_council = None

    # Initialize ImprovementPlanner
    print("🚀 Initializing Improvement Planner...\n")

    if ai_council:
        planner = ImprovementPlanner(ai_council=ai_council)

        # Generate improvement plan with AI
        print("📊 Generating AI-powered improvement plan...")
        print(f"   URL: {SAMPLE_ANALYSIS['url']}")
        print(f"   Industry: Web Development")
        print(f"   Focus Areas: conversion, performance\n")

        try:
            plan = await planner.generate_plan(
                analysis_result=SAMPLE_ANALYSIS,
                industry="Web Development Services",
                focus_areas=["conversion", "performance"],
                lead_value=500.0
            )

            print("✅ Plan generated successfully!\n")

            # Display summary
            print("=" * 70)
            print("IMPROVEMENT PLAN SUMMARY")
            print("=" * 70)
            print(f"URL: {plan.url}")
            print(f"Total Improvements: {plan.summary.total_improvements}")
            print(f"  - Critical: {plan.summary.critical_priority}")
            print(f"  - High: {plan.summary.high_priority}")
            print(f"  - Medium: {plan.summary.medium_priority}")
            print(f"  - Low: {plan.summary.low_priority}")
            print(f"\nQuick Wins: {plan.summary.quick_wins}")
            print(f"Estimated Time: {plan.summary.estimated_total_time}")
            print(f"Estimated Impact: {plan.summary.estimated_total_impact}")
            print(f"\nCategories:")
            for category, count in plan.summary.categories.items():
                print(f"  - {category}: {count}")

            # Display improvements
            print("\n" + "=" * 70)
            print("TOP IMPROVEMENTS")
            print("=" * 70)

            for i, imp in enumerate(plan.improvements[:5], 1):
                print(f"\n{i}. [{imp.priority.value.upper()}] {imp.title}")
                print(f"   Category: {imp.category.value} | Difficulty: {imp.difficulty.value} | Time: {imp.time_estimate}")
                print(f"   Impact: {imp.impact}")
                print(f"   Description: {imp.description[:150]}...")

                if imp.code_example and len(imp.code_example) < 200:
                    print(f"   Code Example: {imp.code_example[:100]}...")

            # Export to files
            print("\n" + "=" * 70)
            print("EXPORTING RESULTS")
            print("=" * 70)

            # Export to JSON
            json_output = planner.export_to_json(plan)
            with open("improvement_plan.json", "w") as f:
                f.write(json_output)
            print("✓ Exported to: improvement_plan.json")

            # Export to Markdown
            md_output = planner.export_to_markdown(plan)
            with open("improvement_plan.md", "w") as f:
                f.write(md_output)
            print("✓ Exported to: improvement_plan.md")

            # Close AI Council
            await ai_council.close()

        except Exception as e:
            print(f"❌ Error generating plan: {e}")
            import traceback
            traceback.print_exc()

            if ai_council:
                await ai_council.close()

    else:
        # Rule-based only (no AI)
        print("📊 Generating rule-based improvement plan (no AI)...")

        # Create a minimal planner that can work without AI
        # We'll just use the rule-based improvements
        from app.services.improvement_planner import ImprovementPlanner

        # Mock AI Council that returns empty improvements
        class MockAICouncil:
            async def complete(self, *args, **kwargs):
                from app.services.ai_mvp.ai_council import AICouncilResponse
                from app.services.ai_mvp.semantic_router import RouteDecision, ModelTier, TaskComplexity

                return AICouncilResponse(
                    content='{"improvements": []}',
                    model_used="mock",
                    model_tier="mock",
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_cost=0.0,
                    route_decision=RouteDecision(
                        model_name="mock",
                        model_tier=ModelTier.ULTRA_CHEAP,
                        task_complexity=TaskComplexity.SIMPLE,
                        reasoning="Mock",
                        estimated_cost=0.0
                    )
                )

        mock_council = MockAICouncil()
        planner = ImprovementPlanner(ai_council=mock_council)

        plan = await planner.generate_plan(
            analysis_result=SAMPLE_ANALYSIS,
            industry="Web Development Services",
            focus_areas=["conversion", "performance"],
            lead_value=500.0
        )

        print("✅ Rule-based plan generated!\n")

        # Display summary
        print("=" * 70)
        print("IMPROVEMENT PLAN SUMMARY")
        print("=" * 70)
        print(f"URL: {plan.url}")
        print(f"Total Improvements: {plan.summary.total_improvements}")
        print(f"  - High: {plan.summary.high_priority}")
        print(f"  - Medium: {plan.summary.medium_priority}")
        print(f"  - Low: {plan.summary.low_priority}")
        print(f"\nQuick Wins: {plan.summary.quick_wins}")
        print(f"Estimated Time: {plan.summary.estimated_total_time}")

        # Display improvements
        print("\n" + "=" * 70)
        print("IMPROVEMENTS")
        print("=" * 70)

        for i, imp in enumerate(plan.improvements, 1):
            print(f"\n{i}. [{imp.priority.value.upper()}] {imp.title}")
            print(f"   Category: {imp.category.value} | Difficulty: {imp.difficulty.value}")
            print(f"   Impact: {imp.impact}")


if __name__ == "__main__":
    print("=" * 70)
    print("IMPROVEMENT PLANNER TEST")
    print("=" * 70)
    print()

    asyncio.run(main())

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
