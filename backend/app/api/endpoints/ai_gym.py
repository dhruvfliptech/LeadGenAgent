"""
AI-GYM API Endpoints

RESTful API for AI model management, performance tracking, A/B testing,
and cost optimization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from decimal import Decimal
import logging

from app.core.database import get_db
from app.schemas.ai_gym import (
    # Model Registry
    AIModelSchema,
    ModelListResponse,
    ModelRecommendationRequest,
    ModelRecommendationResponse,
    # Metrics
    RecordMetricRequest,
    RecordMetricResponse,
    RecordFeedbackRequest,
    ModelStatsRequest,
    ModelStatsSchema,
    TaskComparisonRequest,
    TaskComparisonResponse,
    CostAnalysisRequest,
    CostAnalysisResponse,
    CostByModel,
    CostByTask,
    RecentExecutionsRequest,
    RecentExecutionsResponse,
    RecentExecutionSchema,
    # A/B Testing
    CreateABTestRequest,
    CreateABTestResponse,
    ABTestResultSchema,
    ABTestListResponse,
    ABTestListItem,
    ABTestVariantSchema,
    StopABTestRequest,
    # Quality
    QualityScoreRequest,
    QualityScoreResponse,
    # Dashboard
    DashboardStatsResponse,
)
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

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODEL REGISTRY ENDPOINTS
# ============================================================================

@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    List all available AI models.

    Returns information about all registered models including:
    - Pricing (input/output tokens)
    - Capabilities
    - Performance characteristics
    - Cost efficiency scores
    """
    try:
        registry = get_model_registry()
        models = registry.get_all_models()

        model_schemas = [
            AIModelSchema(
                id=m.id,
                name=m.name,
                provider=m.provider,
                cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
                max_tokens=m.max_tokens,
                capabilities=[c.value for c in m.capabilities],
                avg_latency_ms=m.avg_latency_ms,
                supports_streaming=m.supports_streaming,
                default_temperature=m.default_temperature,
                description=m.description,
                cost_efficiency_score=m.cost_efficiency_score()
            )
            for m in models
        ]

        return ModelListResponse(
            models=model_schemas,
            total=len(model_schemas)
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve models: {str(e)}"
        )


@router.post("/models/recommend", response_model=ModelRecommendationResponse)
async def recommend_model(
    request: ModelRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get model recommendation for a specific task.

    Analyzes historical performance data and selects the optimal model
    based on the specified strategy and constraints.
    """
    try:
        router_service = get_model_router()
        registry = get_model_registry()

        # Convert enum to TaskType
        task_type = TaskType(request.task_type.value)

        # Route to best model
        selected_model = await router_service.route(
            task_type=task_type,
            strategy=request.strategy.value,
            db=db,
            min_quality_score=request.min_quality_score,
            max_cost_per_request=request.max_cost_per_request,
            exclude_models=request.exclude_models or []
        )

        # Get alternatives
        all_candidates = registry.recommend_models_for_task(
            task_type,
            request.strategy.value
        )
        alternatives = [
            m for m in all_candidates[:5]
            if m.id != selected_model.id
        ][:3]

        # Build reasoning
        reasoning = (
            f"Selected {selected_model.name} for {task_type.value} using "
            f"'{request.strategy.value}' strategy. "
            f"Cost: ${selected_model.cost_per_1k_input_tokens}/1k input tokens, "
            f"${selected_model.cost_per_1k_output_tokens}/1k output tokens. "
            f"Avg latency: {selected_model.avg_latency_ms}ms. "
            f"Cost efficiency: {selected_model.cost_efficiency_score():.1f}/100."
        )

        return ModelRecommendationResponse(
            recommended_model=AIModelSchema(
                id=selected_model.id,
                name=selected_model.name,
                provider=selected_model.provider,
                cost_per_1k_input_tokens=selected_model.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=selected_model.cost_per_1k_output_tokens,
                max_tokens=selected_model.max_tokens,
                capabilities=[c.value for c in selected_model.capabilities],
                avg_latency_ms=selected_model.avg_latency_ms,
                supports_streaming=selected_model.supports_streaming,
                default_temperature=selected_model.default_temperature,
                description=selected_model.description,
                cost_efficiency_score=selected_model.cost_efficiency_score()
            ),
            alternatives=[
                AIModelSchema(
                    id=m.id,
                    name=m.name,
                    provider=m.provider,
                    cost_per_1k_input_tokens=m.cost_per_1k_input_tokens,
                    cost_per_1k_output_tokens=m.cost_per_1k_output_tokens,
                    max_tokens=m.max_tokens,
                    capabilities=[c.value for c in m.capabilities],
                    avg_latency_ms=m.avg_latency_ms,
                    supports_streaming=m.supports_streaming,
                    default_temperature=m.default_temperature,
                    description=m.description,
                    cost_efficiency_score=m.cost_efficiency_score()
                )
                for m in alternatives
            ],
            reasoning=reasoning
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to recommend model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recommend model: {str(e)}"
        )


# ============================================================================
# METRIC TRACKING ENDPOINTS
# ============================================================================

@router.post("/metrics", response_model=RecordMetricResponse)
async def record_metric(
    request: RecordMetricRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record execution metrics for an AI task.

    Stores detailed performance data including:
    - Token usage and cost
    - Latency
    - Quality score
    - User feedback
    """
    try:
        tracker = get_metric_tracker()

        # Create metrics object
        metrics = TaskMetrics(
            model_id=request.model_id,
            task_type=TaskType(request.task_type.value),
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            latency_ms=request.latency_ms,
            cost_usd=request.cost_usd,
            quality_score=request.quality_score,
            user_approved=request.user_approved,
            edit_distance=request.edit_distance,
            error_occurred=request.error_occurred,
            error_message=request.error_message,
            metadata=request.metadata
        )

        # Record in database
        metric_id = await tracker.record_execution(db, metrics)

        return RecordMetricResponse(
            metric_id=metric_id,
            message="Metric recorded successfully"
        )

    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record metric: {str(e)}"
        )


@router.post("/metrics/feedback")
async def record_feedback(
    request: RecordFeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Record user feedback for a specific execution.

    Updates metrics with user approval, edits, and ratings.
    """
    try:
        tracker = get_metric_tracker()

        await tracker.record_user_feedback(
            db=db,
            metric_id=request.metric_id,
            approved=request.approved,
            edit_distance=request.edit_distance,
            user_rating=request.user_rating
        )

        return {"message": "Feedback recorded successfully"}

    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )


@router.post("/metrics/stats", response_model=Optional[ModelStatsSchema])
async def get_model_stats(
    request: ModelStatsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated statistics for a model.

    Returns performance metrics including:
    - Average quality, cost, latency
    - Approval rate
    - Error rate
    - Total executions and cost
    """
    try:
        tracker = get_metric_tracker()

        task_type = TaskType(request.task_type.value) if request.task_type else None

        stats = await tracker.get_model_stats(
            db=db,
            model_id=request.model_id,
            task_type=task_type,
            days=request.days
        )

        if not stats:
            return None

        return ModelStatsSchema(
            model_id=stats.model_id,
            task_type=stats.task_type.value if stats.task_type else None,
            total_executions=stats.total_executions,
            avg_quality_score=stats.avg_quality_score,
            avg_cost_usd=stats.avg_cost_usd,
            avg_latency_ms=stats.avg_latency_ms,
            approval_rate=stats.approval_rate,
            error_rate=stats.error_rate,
            total_cost_usd=stats.total_cost_usd,
            last_30_days_executions=stats.last_30_days_executions
        )

    except Exception as e:
        logger.error(f"Failed to get model stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model stats: {str(e)}"
        )


@router.post("/metrics/comparison", response_model=TaskComparisonResponse)
async def compare_models_for_task(
    request: TaskComparisonRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare all models for a specific task type.

    Returns performance comparison across models to identify
    the best performer.
    """
    try:
        tracker = get_metric_tracker()

        task_type = TaskType(request.task_type.value)

        stats_list = await tracker.get_task_comparison(
            db=db,
            task_type=task_type,
            days=request.days
        )

        # Determine winner
        winner = None
        if stats_list:
            best_model = max(stats_list, key=lambda s: s.avg_quality_score)
            winner = best_model.model_id

            summary = (
                f"{winner} is the top performer for {task_type.value} "
                f"with avg quality {best_model.avg_quality_score:.1f}/100, "
                f"${best_model.avg_cost_usd:.4f} per execution, "
                f"and {best_model.approval_rate:.1f}% approval rate."
            )
        else:
            summary = f"No execution data available for {task_type.value}"

        return TaskComparisonResponse(
            task_type=request.task_type,
            models=[
                ModelStatsSchema(
                    model_id=s.model_id,
                    task_type=s.task_type.value if s.task_type else None,
                    total_executions=s.total_executions,
                    avg_quality_score=s.avg_quality_score,
                    avg_cost_usd=s.avg_cost_usd,
                    avg_latency_ms=s.avg_latency_ms,
                    approval_rate=s.approval_rate,
                    error_rate=s.error_rate,
                    total_cost_usd=s.total_cost_usd,
                    last_30_days_executions=s.last_30_days_executions
                )
                for s in stats_list
            ],
            winner=winner,
            summary=summary
        )

    except Exception as e:
        logger.error(f"Failed to compare models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare models: {str(e)}"
        )


@router.post("/metrics/cost-analysis", response_model=CostAnalysisResponse)
async def analyze_costs(
    request: CostAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed cost analysis across all models and tasks.

    Provides insights into:
    - Total spending
    - Cost breakdown by model and task
    - Potential savings opportunities
    """
    try:
        tracker = get_metric_tracker()

        analysis = await tracker.get_cost_analysis(db=db, days=request.days)

        # Calculate potential savings
        cost_by_model = analysis.get('cost_by_model', [])
        if len(cost_by_model) >= 2:
            highest_cost_model = max(cost_by_model, key=lambda x: x['avg_cost'])
            lowest_cost_model = min(cost_by_model, key=lambda x: x['avg_cost'])

            savings_per_execution = highest_cost_model['avg_cost'] - lowest_cost_model['avg_cost']
            potential_savings = savings_per_execution * highest_cost_model['executions']
        else:
            potential_savings = None

        # Generate recommendations
        recommendations = []
        if potential_savings and potential_savings > 1.0:
            recommendations.append(
                f"Switching to more cost-effective models could save "
                f"${potential_savings:.2f} over {request.days} days"
            )

        total_cost = analysis.get('total_cost_usd', 0)
        if total_cost > 100:
            recommendations.append(
                "Consider implementing A/B tests to find optimal cost/quality balance"
            )

        if not recommendations:
            recommendations.append("Cost optimization looks good. Continue monitoring.")

        return CostAnalysisResponse(
            period_days=analysis.get('period_days', request.days),
            total_cost_usd=analysis.get('total_cost_usd', 0),
            total_executions=analysis.get('total_executions', 0),
            avg_cost_per_execution=analysis.get('avg_cost_per_execution', 0),
            cost_by_model=[
                CostByModel(**item) for item in analysis.get('cost_by_model', [])
            ],
            cost_by_task=[
                CostByTask(**item) for item in analysis.get('cost_by_task', [])
            ],
            potential_savings=potential_savings,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Failed to analyze costs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze costs: {str(e)}"
        )


@router.post("/metrics/recent", response_model=RecentExecutionsResponse)
async def get_recent_executions(
    request: RecentExecutionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent execution history.

    Returns detailed records of recent AI executions for debugging
    and monitoring.
    """
    try:
        tracker = get_metric_tracker()

        task_type = TaskType(request.task_type.value) if request.task_type else None

        executions = await tracker.get_recent_executions(
            db=db,
            model_id=request.model_id,
            task_type=task_type,
            limit=request.limit
        )

        return RecentExecutionsResponse(
            executions=[RecentExecutionSchema(**e) for e in executions],
            total=len(executions)
        )

    except Exception as e:
        logger.error(f"Failed to get recent executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent executions: {str(e)}"
        )


# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@router.post("/ab-tests", response_model=CreateABTestResponse)
async def create_ab_test(
    request: CreateABTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new A/B test to compare two models.

    Sets up controlled experiment with traffic splitting to determine
    which model performs better for a specific task.
    """
    try:
        ab_manager = get_ab_test_manager()

        config = ABTestConfig(
            test_name=request.test_name,
            task_type=TaskType(request.task_type.value),
            variant_a_model=request.variant_a_model,
            variant_b_model=request.variant_b_model,
            traffic_split=request.traffic_split,
            min_sample_size=request.min_sample_size,
            max_duration_days=request.max_duration_days,
            target_metric=request.target_metric
        )

        test_id = await ab_manager.create_test(db, config)

        return CreateABTestResponse(
            test_id=test_id,
            test_name=request.test_name,
            message=f"A/B test '{request.test_name}' created successfully"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create A/B test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}"
        )


@router.get("/ab-tests", response_model=ABTestListResponse)
async def list_ab_tests(db: AsyncSession = Depends(get_db)):
    """
    List all active A/B tests.

    Returns current status and sample counts for all running experiments.
    """
    try:
        ab_manager = get_ab_test_manager()

        tests = await ab_manager.list_active_tests(db)

        return ABTestListResponse(
            tests=[ABTestListItem(**test) for test in tests],
            total=len(tests)
        )

    except Exception as e:
        logger.error(f"Failed to list A/B tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list A/B tests: {str(e)}"
        )


@router.get("/ab-tests/{test_name}/results", response_model=Optional[ABTestResultSchema])
async def get_ab_test_results(
    test_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get results and analysis for an A/B test.

    Returns statistical analysis including:
    - Variant performance comparison
    - Winner determination
    - Confidence level
    - Recommendations
    """
    try:
        ab_manager = get_ab_test_manager()

        results = await ab_manager.analyze_test(db, test_name)

        if not results:
            return None

        return ABTestResultSchema(
            test_id=results.test_id,
            test_name=results.test_name,
            variant_a=ABTestVariantSchema(
                name="A",
                model_id=results.variant_a['model_id'],
                traffic_pct=0.0,  # Not needed in results
                sample_size=results.variant_a['sample_size'],
                avg_quality=results.variant_a.get('avg_quality'),
                avg_cost=results.variant_a.get('avg_cost'),
                mean_metric=results.variant_a.get('mean_metric'),
                std_metric=results.variant_a.get('std_metric')
            ),
            variant_b=ABTestVariantSchema(
                name="B",
                model_id=results.variant_b['model_id'],
                traffic_pct=0.0,
                sample_size=results.variant_b['sample_size'],
                avg_quality=results.variant_b.get('avg_quality'),
                avg_cost=results.variant_b.get('avg_cost'),
                mean_metric=results.variant_b.get('mean_metric'),
                std_metric=results.variant_b.get('std_metric')
            ),
            winner=results.winner,
            confidence_level=results.confidence_level,
            p_value=results.p_value,
            effect_size=results.effect_size,
            recommendation=results.recommendation
        )

    except Exception as e:
        logger.error(f"Failed to get A/B test results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get A/B test results: {str(e)}"
        )


@router.post("/ab-tests/{test_name}/stop")
async def stop_ab_test(
    test_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Stop an active A/B test.

    Ends the experiment and prevents further traffic allocation.
    """
    try:
        ab_manager = get_ab_test_manager()

        await ab_manager.stop_test(db, test_name)

        return {"message": f"A/B test '{test_name}' stopped successfully"}

    except Exception as e:
        logger.error(f"Failed to stop A/B test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop A/B test: {str(e)}"
        )


# ============================================================================
# QUALITY SCORING ENDPOINTS
# ============================================================================

@router.post("/quality/score", response_model=QualityScoreResponse)
async def calculate_quality_score(request: QualityScoreRequest):
    """
    Calculate quality score for AI output.

    Evaluates output based on task-specific criteria and returns
    objective quality score (0-100).
    """
    try:
        scorer = get_quality_scorer()

        task_type = TaskType(request.task_type.value)

        score = await scorer.score(
            task_type=task_type,
            output=request.output,
            context=request.context
        )

        dimensions = await scorer.score_with_dimensions(
            task_type=task_type,
            output=request.output,
            context=request.context
        )

        details = f"Quality score calculated using {task_type.value} criteria"

        return QualityScoreResponse(
            quality_score=score,
            dimensions=dimensions,
            details=details
        )

    except Exception as e:
        logger.error(f"Failed to calculate quality score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate quality score: {str(e)}"
        )


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Get overview statistics for AI-GYM dashboard.

    Returns high-level metrics and recommendations for optimization.
    """
    try:
        tracker = get_metric_tracker()
        ab_manager = get_ab_test_manager()

        # Get cost analysis
        cost_analysis = await tracker.get_cost_analysis(db, days=30)

        # Get active tests
        active_tests = await ab_manager.list_active_tests(db)

        # Simple recommendations
        recommendations = []
        if cost_analysis.get('total_cost_usd', 0) > 50:
            recommendations.append("Review cost-effective model alternatives")
        if len(active_tests) == 0:
            recommendations.append("Consider starting A/B tests to optimize performance")
        if not recommendations:
            recommendations.append("System performance looks optimal")

        return DashboardStatsResponse(
            total_executions=cost_analysis.get('total_executions', 0),
            total_cost_usd=cost_analysis.get('total_cost_usd', 0),
            avg_quality_score=75.0,  # Would need to calculate from all metrics
            active_ab_tests=len(active_tests),
            top_model=cost_analysis.get('cost_by_model', [{}])[0].get('model_id'),
            cost_trend="stable",
            quality_trend="stable",
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )
