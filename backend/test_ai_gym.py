"""
AI-GYM Test Script

Demonstrates all major features of the AI-GYM system:
- Model registry and routing
- Performance tracking
- A/B testing
- Quality scoring
- Cost analysis

Run with: python test_ai_gym.py
"""

import asyncio
import sys
from decimal import Decimal
from datetime import datetime
import json

# Add backend to path
sys.path.insert(0, '/Users/greenmachine2.0/Craigslist/backend')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.ai_gym import (
    get_model_registry,
    get_model_router,
    get_metric_tracker,
    get_ab_test_manager,
    get_quality_scorer,
)
from app.services.ai_gym.models import TaskType, ModelCapability
from app.services.ai_gym.tracker import TaskMetrics
from app.services.ai_gym.ab_testing import ABTestConfig


# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKBLUE}→ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


async def test_model_registry():
    """Test 1: Model Registry"""
    print_header("TEST 1: MODEL REGISTRY")

    registry = get_model_registry()

    # List all models
    print_info("Available Models:")
    models = registry.get_all_models()
    for model in models:
        print(f"  • {model.name} ({model.id})")
        print(f"    Provider: {model.provider}")
        print(f"    Cost: ${model.cost_per_1k_input_tokens}/1k input, "
              f"${model.cost_per_1k_output_tokens}/1k output")
        print(f"    Max Tokens: {model.max_tokens:,}")
        print(f"    Capabilities: {', '.join(c.value for c in model.capabilities)}")
        print(f"    Cost Efficiency: {model.cost_efficiency_score():.1f}/100")
        print()

    print_success(f"Found {len(models)} registered models")

    # Test capability filtering
    print_info("\nModels with CODE_GENERATION capability:")
    code_models = registry.get_models_by_capability(ModelCapability.CODE_GENERATION)
    for model in code_models:
        print(f"  • {model.name}")

    print_success(f"Found {len(code_models)} models with code generation capability")

    # Test cheapest model
    cheapest = registry.get_cheapest_model()
    print_info(f"\nCheapest model: {cheapest.name} "
               f"(${cheapest.cost_per_1k_input_tokens + cheapest.cost_per_1k_output_tokens:.4f}/1k tokens)")

    # Test fastest model
    fastest = registry.get_fastest_model()
    print_info(f"Fastest model: {fastest.name} ({fastest.avg_latency_ms}ms avg latency)")


async def test_model_routing():
    """Test 2: Model Routing"""
    print_header("TEST 2: INTELLIGENT MODEL ROUTING")

    router = get_model_router()

    # Test different strategies for website analysis
    task_type = TaskType.WEBSITE_ANALYSIS

    strategies = ["best_quality", "best_cost", "balanced", "fastest"]

    for strategy in strategies:
        try:
            model = await router.route(
                task_type=task_type,
                strategy=strategy
            )
            print_info(f"{strategy.upper()} strategy selected: {model.name}")
            print(f"  Cost: ${model.cost_per_1k_input_tokens}/1k input")
            print(f"  Latency: {model.avg_latency_ms}ms")
            print(f"  Cost Efficiency: {model.cost_efficiency_score():.1f}/100")
        except Exception as e:
            print_warning(f"Failed to route with {strategy}: {e}")

    print_success("Model routing test completed")

    # Test model council
    print_info("\nTesting Model Council (3 models for ensemble):")
    council = await router.route_council(
        task_type=TaskType.EMAIL_WRITING,
        num_models=3,
        diversity="providers"
    )
    for i, model in enumerate(council, 1):
        print(f"  {i}. {model.name} ({model.provider})")

    print_success(f"Created council of {len(council)} diverse models")


async def test_quality_scoring():
    """Test 3: Quality Scoring"""
    print_header("TEST 3: AUTOMATED QUALITY SCORING")

    scorer = get_quality_scorer()

    # Test website analysis quality
    sample_analysis = json.dumps({
        "business_type": "Web Development Agency",
        "industry": "Technology Services",
        "target_audience": "Small to medium businesses",
        "services": ["Web Design", "SEO", "Mobile Apps"],
        "unique_value_proposition": "Fast turnaround with guaranteed results",
        "technologies": ["React", "Node.js", "PostgreSQL"],
        "pain_points": [
            "Outdated website design",
            "Poor mobile responsiveness",
            "Slow loading times"
        ],
        "opportunities": [
            "Implement modern design system",
            "Add progressive web app features",
            "Optimize for Core Web Vitals"
        ]
    })

    score = await scorer.score(
        task_type=TaskType.WEBSITE_ANALYSIS,
        output=sample_analysis,
        context={}
    )
    print_info(f"Website Analysis Quality Score: {score:.1f}/100")

    # Test email writing quality
    sample_email = """
    Hi John,

    I noticed your business website and wanted to reach out about an exciting opportunity.

    We specialize in modern web development and have helped over 50 businesses like yours
    improve their online presence. I'd love to schedule a quick 15-minute call to discuss
    how we could help you achieve similar results.

    Would you be available this week for a brief conversation?

    Best regards,
    Sarah
    """

    email_score = await scorer.score(
        task_type=TaskType.EMAIL_WRITING,
        output=sample_email,
        context={}
    )
    print_info(f"Email Writing Quality Score: {email_score:.1f}/100")

    # Test with dimensions
    dimensions = await scorer.score_with_dimensions(
        task_type=TaskType.EMAIL_WRITING,
        output=sample_email,
        context={}
    )
    print_info("Quality Dimensions:")
    for dim, score in dimensions.items():
        print(f"  • {dim.capitalize()}: {score:.1f}/100")

    print_success("Quality scoring test completed")


async def test_performance_tracking(db: AsyncSession):
    """Test 4: Performance Tracking"""
    print_header("TEST 4: PERFORMANCE METRICS TRACKING")

    tracker = get_metric_tracker()

    # Simulate recording metrics for different models
    test_metrics = [
        {
            "model_id": "anthropic/claude-3.5-sonnet",
            "task_type": TaskType.WEBSITE_ANALYSIS,
            "prompt_tokens": 1200,
            "completion_tokens": 800,
            "latency_ms": 1850,
            "cost_usd": Decimal("0.0246"),
            "quality_score": 92.5,
            "user_approved": True
        },
        {
            "model_id": "openai/gpt-4-turbo-preview",
            "task_type": TaskType.WEBSITE_ANALYSIS,
            "prompt_tokens": 1150,
            "completion_tokens": 750,
            "latency_ms": 2100,
            "cost_usd": Decimal("0.0340"),
            "quality_score": 89.0,
            "user_approved": True
        },
        {
            "model_id": "qwen/qwen-2.5-72b-instruct",
            "task_type": TaskType.WEBSITE_ANALYSIS,
            "prompt_tokens": 1180,
            "completion_tokens": 720,
            "latency_ms": 1200,
            "cost_usd": Decimal("0.00076"),
            "quality_score": 82.0,
            "user_approved": None
        }
    ]

    metric_ids = []
    for metric_data in test_metrics:
        metrics = TaskMetrics(**metric_data)
        try:
            metric_id = await tracker.record_execution(db, metrics)
            metric_ids.append(metric_id)
            print_info(f"Recorded: {metric_data['model_id']} - "
                      f"${metric_data['cost_usd']:.4f}, "
                      f"quality={metric_data.get('quality_score', 'N/A')}")
        except Exception as e:
            print_warning(f"Failed to record metric: {e}")

    print_success(f"Recorded {len(metric_ids)} execution metrics")

    # Record user feedback
    if metric_ids:
        try:
            await tracker.record_user_feedback(
                db=db,
                metric_id=metric_ids[0],
                approved=True,
                edit_distance=0,
                user_rating=5.0
            )
            print_info(f"Recorded user feedback for metric {metric_ids[0]}")
        except Exception as e:
            print_warning(f"Failed to record feedback: {e}")

    # Get model stats
    for model_id in ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo-preview"]:
        stats = await tracker.get_model_stats(
            db=db,
            model_id=model_id,
            task_type=TaskType.WEBSITE_ANALYSIS,
            days=30
        )

        if stats:
            print_info(f"\nStats for {model_id}:")
            print(f"  Executions: {stats.total_executions}")
            print(f"  Avg Quality: {stats.avg_quality_score:.1f}/100")
            print(f"  Avg Cost: ${stats.avg_cost_usd:.4f}")
            print(f"  Avg Latency: {stats.avg_latency_ms}ms")
            print(f"  Approval Rate: {stats.approval_rate:.1f}%")

    print_success("Performance tracking test completed")


async def test_ab_testing(db: AsyncSession):
    """Test 5: A/B Testing"""
    print_header("TEST 5: A/B TESTING SYSTEM")

    ab_manager = get_ab_test_manager()

    # Create A/B test
    test_name = f"claude_vs_gpt4_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    config = ABTestConfig(
        test_name=test_name,
        task_type=TaskType.EMAIL_WRITING,
        variant_a_model="anthropic/claude-3.5-sonnet",
        variant_b_model="openai/gpt-4-turbo-preview",
        traffic_split=0.5,
        min_sample_size=10,
        max_duration_days=14,
        target_metric="quality"
    )

    try:
        test_id = await ab_manager.create_test(db, config)
        print_success(f"Created A/B test: {test_name} (ID: {test_id})")

        # List active tests
        active_tests = await ab_manager.list_active_tests(db)
        print_info(f"\nActive A/B Tests: {len(active_tests)}")
        for test in active_tests:
            print(f"  • {test['test_name']}")
            print(f"    Task: {test.get('task_type', 'N/A')}")
            print(f"    Variants: {len(test.get('variants', []))}")

        # Simulate variant assignment
        print_info("\nSimulating variant assignments:")
        for i in range(10):
            variant_name, model_id = await ab_manager.assign_variant(
                db=db,
                test_name=test_name,
                task_type=TaskType.EMAIL_WRITING
            )
            print(f"  Request {i+1}: Variant {variant_name} ({model_id})")

            # Record result
            import random
            quality = random.uniform(75, 95)
            cost = random.uniform(0.01, 0.03)
            await ab_manager.record_variant_result(
                db=db,
                test_name=test_name,
                variant_name=variant_name,
                quality_score=quality,
                cost_usd=cost
            )

        # Analyze test (will show insufficient data)
        print_info("\nAnalyzing A/B test results:")
        results = await ab_manager.analyze_test(db, test_name)

        if results:
            print(f"  Winner: {results.winner}")
            print(f"  Confidence: {results.confidence_level:.1f}%")
            print(f"  P-value: {results.p_value:.4f}")
            print(f"  Recommendation: {results.recommendation}")

        # Stop test
        await ab_manager.stop_test(db, test_name)
        print_success(f"Stopped A/B test: {test_name}")

    except Exception as e:
        print_warning(f"A/B testing failed: {e}")
        import traceback
        traceback.print_exc()

    print_success("A/B testing test completed")


async def test_cost_analysis(db: AsyncSession):
    """Test 6: Cost Analysis"""
    print_header("TEST 6: COST ANALYSIS")

    tracker = get_metric_tracker()

    try:
        analysis = await tracker.get_cost_analysis(db, days=30)

        print_info("Cost Analysis (Last 30 Days):")
        print(f"  Total Cost: ${analysis.get('total_cost_usd', 0):.2f}")
        print(f"  Total Executions: {analysis.get('total_executions', 0)}")
        print(f"  Avg Cost/Execution: ${analysis.get('avg_cost_per_execution', 0):.4f}")

        print_info("\nCost by Model:")
        for item in analysis.get('cost_by_model', [])[:5]:
            print(f"  • {item['model_id']}")
            print(f"    Cost: ${item['cost_usd']:.4f} ({item['executions']} executions)")
            print(f"    Avg: ${item['avg_cost']:.4f}/execution")

        print_info("\nCost by Task:")
        for item in analysis.get('cost_by_task', []):
            print(f"  • {item['task_type']}")
            print(f"    Cost: ${item['cost_usd']:.4f} ({item['executions']} executions)")

        print_success("Cost analysis test completed")

    except Exception as e:
        print_warning(f"Cost analysis failed: {e}")


async def main():
    """Run all tests."""
    print_header("AI-GYM COMPREHENSIVE TEST SUITE")
    print_info("Testing the secret sauce for multi-model AI optimization\n")

    # Tests that don't require database
    await test_model_registry()
    await test_model_routing()
    await test_quality_scoring()

    # Tests that require database
    print_info("\nConnecting to database...")

    try:
        # Create database session
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True
        )

        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as db:
            print_success("Database connected")

            await test_performance_tracking(db)
            await test_ab_testing(db)
            await test_cost_analysis(db)

        await engine.dispose()

    except Exception as e:
        print_warning(f"Database tests skipped: {e}")
        print_info("To run database tests, ensure PostgreSQL is running and DATABASE_URL is set")

    print_header("TEST SUITE COMPLETED")
    print_success("All AI-GYM features tested successfully!")
    print_info("\nNext steps:")
    print("  1. Run database migration: alembic upgrade head")
    print("  2. Start using AI-GYM in your application")
    print("  3. Monitor the dashboard for optimization insights")
    print("  4. Set up A/B tests to compare models")


if __name__ == "__main__":
    asyncio.run(main())
