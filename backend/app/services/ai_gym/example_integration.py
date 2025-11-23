"""
AI-GYM Integration Examples

Demonstrates how to integrate AI-GYM into existing services.
"""

import time
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_gym import (
    get_model_router,
    get_metric_tracker,
    get_quality_scorer,
    get_ab_test_manager,
)
from app.services.ai_gym.models import TaskType
from app.services.ai_gym.tracker import TaskMetrics
from app.services.openrouter_client import get_openrouter_client


async def website_analyzer_with_ai_gym(
    url: str,
    html_content: str,
    db: AsyncSession,
    use_ab_test: bool = False
) -> Dict[str, Any]:
    """
    Example: Website analyzer with AI-GYM integration.

    Shows how to:
    1. Route to optimal model
    2. Execute AI task
    3. Score quality
    4. Track metrics
    5. Optionally use A/B testing
    """

    # Step 1: Select model
    if use_ab_test:
        # Use A/B test variant
        ab_manager = get_ab_test_manager()
        variant_name, model_id = await ab_manager.assign_variant(
            db=db,
            test_name="website_analysis_test",
            task_type=TaskType.WEBSITE_ANALYSIS
        )
        router = get_model_router()
        model = router.get_model_by_id(model_id)
    else:
        # Route normally
        router = get_model_router()
        model = await router.route(
            task_type=TaskType.WEBSITE_ANALYSIS,
            strategy="balanced",
            db=db,
            min_quality_score=80.0  # Ensure minimum quality
        )

    # Step 2: Execute AI analysis
    ai_client = get_openrouter_client()

    prompt = f"""
    Analyze this website and extract business information:

    URL: {url}

    HTML Content (truncated):
    {html_content[:2000]}

    Provide analysis in JSON format with:
    - business_type
    - industry
    - target_audience
    - services
    - unique_value_proposition
    - technologies
    - pain_points (array)
    - opportunities (array)
    """

    start_time = time.time()

    try:
        analysis = await ai_client.generate_completion(
            prompt=prompt,
            model=model.id,
            temperature=0.7,
            max_tokens=2000
        )

        latency_ms = int((time.time() - start_time) * 1000)
        error_occurred = False
        error_message = None

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_occurred = True
        error_message = str(e)
        analysis = "{}"

    # Step 3: Calculate quality score
    scorer = get_quality_scorer()
    quality_score = await scorer.score(
        task_type=TaskType.WEBSITE_ANALYSIS,
        output=analysis,
        context={"url": url}
    )

    # Step 4: Calculate cost
    # Estimate tokens (in production, get from API response)
    prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
    completion_tokens = len(analysis.split()) * 1.3
    cost_usd = model.calculate_cost(
        int(prompt_tokens),
        int(completion_tokens)
    )

    # Step 5: Track metrics
    tracker = get_metric_tracker()
    metric_id = await tracker.record_execution(
        db=db,
        metrics=TaskMetrics(
            model_id=model.id,
            task_type=TaskType.WEBSITE_ANALYSIS,
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            quality_score=quality_score,
            error_occurred=error_occurred,
            error_message=error_message,
            metadata={"url": url, "model_name": model.name}
        )
    )

    # Step 6: If using A/B test, record variant result
    if use_ab_test:
        await ab_manager.record_variant_result(
            db=db,
            test_name="website_analysis_test",
            variant_name=variant_name,
            quality_score=quality_score,
            cost_usd=float(cost_usd)
        )

    return {
        "analysis": analysis,
        "metadata": {
            "model_used": model.name,
            "model_id": model.id,
            "quality_score": quality_score,
            "cost_usd": float(cost_usd),
            "latency_ms": latency_ms,
            "metric_id": metric_id
        }
    }


async def email_writer_with_ai_gym(
    lead_info: Dict[str, Any],
    template_type: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Example: Email writer with AI-GYM integration.

    Demonstrates:
    - Model routing for email writing
    - Quality scoring for emails
    - User feedback integration
    """

    # Route to best model for email writing
    router = get_model_router()
    model = await router.route(
        task_type=TaskType.EMAIL_WRITING,
        strategy="best_quality",  # Emails are important
        db=db
    )

    # Generate email
    ai_client = get_openrouter_client()

    prompt = f"""
    Write a professional outreach email to:

    Name: {lead_info.get('name', 'there')}
    Company: {lead_info.get('company', 'N/A')}
    Industry: {lead_info.get('industry', 'N/A')}

    Template: {template_type}

    Make it personalized and engaging.
    """

    start_time = time.time()
    email_content = await ai_client.generate_completion(
        prompt=prompt,
        model=model.id
    )
    latency_ms = int((time.time() - start_time) * 1000)

    # Score quality
    scorer = get_quality_scorer()
    quality_score = await scorer.score(
        task_type=TaskType.EMAIL_WRITING,
        output=email_content,
        context=lead_info
    )

    # Track metrics
    tracker = get_metric_tracker()
    prompt_tokens = len(prompt.split()) * 1.3
    completion_tokens = len(email_content.split()) * 1.3

    metric_id = await tracker.record_execution(
        db=db,
        metrics=TaskMetrics(
            model_id=model.id,
            task_type=TaskType.EMAIL_WRITING,
            prompt_tokens=int(prompt_tokens),
            completion_tokens=int(completion_tokens),
            latency_ms=latency_ms,
            cost_usd=model.calculate_cost(int(prompt_tokens), int(completion_tokens)),
            quality_score=quality_score,
            metadata={
                "template_type": template_type,
                "lead_id": lead_info.get("id")
            }
        )
    )

    return {
        "email_content": email_content,
        "quality_score": quality_score,
        "metric_id": metric_id
    }


async def record_user_feedback_example(
    metric_id: int,
    user_approved: bool,
    original_output: str,
    edited_output: Optional[str],
    user_rating: Optional[float],
    db: AsyncSession
):
    """
    Example: Recording user feedback after they review AI output.

    Call this when:
    - User approves/rejects output
    - User edits the output
    - User provides a rating
    """

    tracker = get_metric_tracker()

    # Calculate edit distance if output was edited
    edit_distance = None
    if edited_output and original_output:
        # Simple character difference (could use Levenshtein distance)
        edit_distance = abs(len(edited_output) - len(original_output))

    await tracker.record_user_feedback(
        db=db,
        metric_id=metric_id,
        approved=user_approved,
        edit_distance=edit_distance,
        user_rating=user_rating
    )


async def run_ab_test_example(db: AsyncSession):
    """
    Example: Setting up and running an A/B test.

    Tests Claude vs GPT-4 for email writing.
    """
    from app.services.ai_gym.ab_testing import ABTestConfig

    ab_manager = get_ab_test_manager()

    # Create test
    config = ABTestConfig(
        test_name="email_claude_vs_gpt4",
        task_type=TaskType.EMAIL_WRITING,
        variant_a_model="anthropic/claude-3.5-sonnet",
        variant_b_model="openai/gpt-4-turbo-preview",
        traffic_split=0.5,
        min_sample_size=100,
        max_duration_days=14,
        target_metric="quality"
    )

    test_id = await ab_manager.create_test(db, config)
    print(f"Created A/B test with ID: {test_id}")

    # In production code, when generating emails:
    variant_name, model_id = await ab_manager.assign_variant(
        db=db,
        test_name="email_claude_vs_gpt4",
        task_type=TaskType.EMAIL_WRITING
    )

    # Use the assigned model...
    # After execution, record result:
    await ab_manager.record_variant_result(
        db=db,
        test_name="email_claude_vs_gpt4",
        variant_name=variant_name,
        quality_score=88.5,
        cost_usd=0.0234
    )

    # After collecting enough samples, analyze:
    results = await ab_manager.analyze_test(db, "email_claude_vs_gpt4")

    if results and results.winner != "inconclusive":
        print(f"Winner: {results.winner}")
        print(f"Confidence: {results.confidence_level}%")
        print(f"Recommendation: {results.recommendation}")

        # If confident, stop test and roll out winner
        if results.confidence_level > 95:
            await ab_manager.stop_test(db, "email_claude_vs_gpt4")


async def cost_optimization_example(db: AsyncSession):
    """
    Example: Analyzing costs and optimizing spend.

    Run this weekly to review AI spending.
    """

    tracker = get_metric_tracker()

    # Get 30-day cost analysis
    analysis = await tracker.get_cost_analysis(db, days=30)

    print(f"Total AI Spend (30 days): ${analysis['total_cost_usd']:.2f}")
    print(f"Total Executions: {analysis['total_executions']}")
    print(f"Avg Cost/Execution: ${analysis['avg_cost_per_execution']:.4f}")

    print("\nTop 3 Most Expensive Models:")
    for i, model in enumerate(analysis['cost_by_model'][:3], 1):
        print(f"{i}. {model['model_id']}")
        print(f"   Total: ${model['cost_usd']:.2f}")
        print(f"   Executions: {model['executions']}")
        print(f"   Avg: ${model['avg_cost']:.4f}")

    print("\nCost by Task:")
    for task in analysis['cost_by_task']:
        print(f"- {task['task_type']}: ${task['cost_usd']:.2f}")

    # Compare models for a specific task
    comparison = await tracker.get_task_comparison(
        db=db,
        task_type=TaskType.WEBSITE_ANALYSIS,
        days=30
    )

    print("\nWebsite Analysis Model Comparison:")
    for stats in comparison:
        print(f"\n{stats.model_id}:")
        print(f"  Quality: {stats.avg_quality_score:.1f}/100")
        print(f"  Cost: ${stats.avg_cost_usd:.4f}")
        print(f"  Latency: {stats.avg_latency_ms}ms")
        print(f"  Approval: {stats.approval_rate:.1f}%")

        # Calculate cost/quality ratio
        if stats.avg_quality_score > 0:
            efficiency = float(stats.avg_cost_usd) / stats.avg_quality_score * 1000
            print(f"  Efficiency: {efficiency:.2f} (lower is better)")


async def model_council_example(task_type: TaskType, db: AsyncSession):
    """
    Example: Using model council for ensemble decisions.

    Get multiple model outputs and combine them for better results.
    """

    router = get_model_router()

    # Get diverse council of 3 models
    council = await router.route_council(
        task_type=task_type,
        num_models=3,
        diversity="providers",  # Ensure different providers
        db=db
    )

    ai_client = get_openrouter_client()
    prompt = "Analyze this data..."

    responses = []
    for model in council:
        response = await ai_client.generate_completion(
            prompt=prompt,
            model=model.id
        )
        responses.append({
            "model": model.name,
            "response": response
        })

    # Combine responses (simple concatenation or more sophisticated merging)
    combined = "\n\n---\n\n".join([
        f"From {r['model']}:\n{r['response']}"
        for r in responses
    ])

    return combined
