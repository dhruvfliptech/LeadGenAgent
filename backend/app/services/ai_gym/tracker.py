"""
AI-GYM Metric Tracker

Records and analyzes performance metrics for every AI model execution.
Tracks costs, latency, quality, and user feedback for continuous optimization.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TaskType

logger = logging.getLogger(__name__)


@dataclass
class TaskMetrics:
    """
    Metrics for a single AI task execution.

    Attributes:
        model_id: Model identifier
        task_type: Type of task performed
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        latency_ms: Response latency in milliseconds
        cost_usd: Total cost in USD
        quality_score: Automated quality score (0-100)
        user_approved: Whether user approved the output (optional)
        edit_distance: Character edit distance if user modified output (optional)
        error_occurred: Whether an error occurred
        error_message: Error message if applicable
        metadata: Additional context data
    """
    model_id: str
    task_type: TaskType
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: Decimal
    quality_score: Optional[float] = None
    user_approved: Optional[bool] = None
    edit_distance: Optional[int] = None
    error_occurred: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelStats:
    """
    Aggregated statistics for a model.

    Attributes:
        model_id: Model identifier
        task_type: Task type filter
        total_executions: Total number of executions
        avg_quality_score: Average quality score
        avg_cost_usd: Average cost per execution
        avg_latency_ms: Average latency
        approval_rate: Percentage of user approvals
        error_rate: Percentage of executions with errors
        total_cost_usd: Total cumulative cost
        last_30_days_executions: Executions in last 30 days
    """
    model_id: str
    task_type: Optional[TaskType]
    total_executions: int
    avg_quality_score: float
    avg_cost_usd: Decimal
    avg_latency_ms: int
    approval_rate: float
    error_rate: float
    total_cost_usd: Decimal
    last_30_days_executions: int


class MetricTracker:
    """
    Performance metric tracking system.

    Records detailed metrics for every AI execution and provides
    analytics for model performance comparison and optimization.
    """

    async def record_execution(
        self,
        db: AsyncSession,
        metrics: TaskMetrics
    ) -> int:
        """
        Record metrics for an AI execution.

        Args:
            db: Database session
            metrics: Task execution metrics

        Returns:
            ID of created metric record
        """
        try:
            from app.models.feedback import ModelMetric

            # Create metric record
            metric = ModelMetric(
                model_id=metrics.model_id,
                task_type=metrics.task_type.value,
                prompt_tokens=metrics.prompt_tokens,
                completion_tokens=metrics.completion_tokens,
                latency_ms=metrics.latency_ms,
                cost_usd=float(metrics.cost_usd),
                quality_score=metrics.quality_score,
                user_approved=metrics.user_approved,
                edit_distance=metrics.edit_distance,
                error_occurred=metrics.error_occurred,
                error_message=metrics.error_message,
                metadata=metrics.metadata or {},
                created_at=datetime.utcnow()
            )

            db.add(metric)
            await db.commit()
            await db.refresh(metric)

            logger.debug(
                f"Recorded metrics for {metrics.model_id} on {metrics.task_type}: "
                f"cost=${metrics.cost_usd:.4f}, latency={metrics.latency_ms}ms, "
                f"quality={metrics.quality_score or 'N/A'}"
            )

            return metric.id

        except Exception as e:
            logger.error(f"Failed to record execution metrics: {e}")
            await db.rollback()
            raise

    async def record_user_feedback(
        self,
        db: AsyncSession,
        metric_id: int,
        approved: bool,
        edit_distance: Optional[int] = None,
        user_rating: Optional[float] = None
    ):
        """
        Record user feedback for a specific execution.

        Args:
            db: Database session
            metric_id: ID of the metric record
            approved: Whether user approved the output
            edit_distance: Number of characters changed (if edited)
            user_rating: Optional user rating (1-5)
        """
        try:
            from app.models.feedback import ModelMetric

            query = select(ModelMetric).where(ModelMetric.id == metric_id)
            result = await db.execute(query)
            metric = result.scalar_one_or_none()

            if not metric:
                logger.warning(f"Metric {metric_id} not found for feedback")
                return

            # Update with user feedback
            metric.user_approved = approved
            if edit_distance is not None:
                metric.edit_distance = edit_distance
            if user_rating is not None:
                metric.metadata = metric.metadata or {}
                metric.metadata['user_rating'] = user_rating

            metric.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(
                f"Updated metric {metric_id} with user feedback: "
                f"approved={approved}, edit_distance={edit_distance}"
            )

        except Exception as e:
            logger.error(f"Failed to record user feedback: {e}")
            await db.rollback()
            raise

    async def get_model_stats(
        self,
        db: AsyncSession,
        model_id: str,
        task_type: Optional[TaskType] = None,
        days: int = 30
    ) -> Optional[ModelStats]:
        """
        Get aggregated statistics for a model.

        Args:
            db: Database session
            model_id: Model identifier
            task_type: Optional task type filter
            days: Number of days to look back

        Returns:
            Model statistics or None
        """
        try:
            from app.models.feedback import ModelMetric

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Build query filters
            filters = [
                ModelMetric.model_id == model_id,
                ModelMetric.created_at >= cutoff_date
            ]
            if task_type:
                filters.append(ModelMetric.task_type == task_type.value)

            # Get aggregated stats
            query = select(
                func.count(ModelMetric.id).label('total_executions'),
                func.avg(ModelMetric.quality_score).label('avg_quality'),
                func.avg(ModelMetric.cost_usd).label('avg_cost'),
                func.avg(ModelMetric.latency_ms).label('avg_latency'),
                func.sum(ModelMetric.cost_usd).label('total_cost'),
                func.avg(
                    func.cast(ModelMetric.user_approved, type_=func.Float)
                ).label('approval_rate'),
                func.avg(
                    func.cast(ModelMetric.error_occurred, type_=func.Float)
                ).label('error_rate')
            ).where(and_(*filters))

            result = await db.execute(query)
            row = result.first()

            if not row or row.total_executions == 0:
                return None

            stats = ModelStats(
                model_id=model_id,
                task_type=task_type,
                total_executions=int(row.total_executions),
                avg_quality_score=float(row.avg_quality or 0),
                avg_cost_usd=Decimal(str(row.avg_cost or 0)),
                avg_latency_ms=int(row.avg_latency or 0),
                approval_rate=float(row.approval_rate or 0) * 100,
                error_rate=float(row.error_rate or 0) * 100,
                total_cost_usd=Decimal(str(row.total_cost or 0)),
                last_30_days_executions=int(row.total_executions)
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get model stats: {e}")
            return None

    async def get_task_comparison(
        self,
        db: AsyncSession,
        task_type: TaskType,
        days: int = 30
    ) -> List[ModelStats]:
        """
        Compare all models for a specific task type.

        Args:
            db: Database session
            task_type: Task type to compare
            days: Number of days to look back

        Returns:
            List of model statistics, sorted by quality
        """
        try:
            from app.models.feedback import ModelMetric

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get stats grouped by model
            query = select(
                ModelMetric.model_id,
                func.count(ModelMetric.id).label('total_executions'),
                func.avg(ModelMetric.quality_score).label('avg_quality'),
                func.avg(ModelMetric.cost_usd).label('avg_cost'),
                func.avg(ModelMetric.latency_ms).label('avg_latency'),
                func.sum(ModelMetric.cost_usd).label('total_cost'),
                func.avg(
                    func.cast(ModelMetric.user_approved, type_=func.Float)
                ).label('approval_rate'),
                func.avg(
                    func.cast(ModelMetric.error_occurred, type_=func.Float)
                ).label('error_rate')
            ).where(
                and_(
                    ModelMetric.task_type == task_type.value,
                    ModelMetric.created_at >= cutoff_date
                )
            ).group_by(ModelMetric.model_id).order_by(desc('avg_quality'))

            result = await db.execute(query)
            rows = result.all()

            stats_list = []
            for row in rows:
                stats = ModelStats(
                    model_id=row.model_id,
                    task_type=task_type,
                    total_executions=int(row.total_executions),
                    avg_quality_score=float(row.avg_quality or 0),
                    avg_cost_usd=Decimal(str(row.avg_cost or 0)),
                    avg_latency_ms=int(row.avg_latency or 0),
                    approval_rate=float(row.approval_rate or 0) * 100,
                    error_rate=float(row.error_rate or 0) * 100,
                    total_cost_usd=Decimal(str(row.total_cost or 0)),
                    last_30_days_executions=int(row.total_executions)
                )
                stats_list.append(stats)

            return stats_list

        except Exception as e:
            logger.error(f"Failed to get task comparison: {e}")
            return []

    async def get_cost_analysis(
        self,
        db: AsyncSession,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost analysis across all models and tasks.

        Args:
            db: Database session
            days: Number of days to analyze

        Returns:
            Cost analysis data
        """
        try:
            from app.models.feedback import ModelMetric

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total cost and executions
            total_query = select(
                func.sum(ModelMetric.cost_usd).label('total_cost'),
                func.count(ModelMetric.id).label('total_executions')
            ).where(ModelMetric.created_at >= cutoff_date)

            total_result = await db.execute(total_query)
            total_row = total_result.first()

            # Cost by model
            model_query = select(
                ModelMetric.model_id,
                func.sum(ModelMetric.cost_usd).label('cost'),
                func.count(ModelMetric.id).label('executions')
            ).where(
                ModelMetric.created_at >= cutoff_date
            ).group_by(
                ModelMetric.model_id
            ).order_by(desc('cost'))

            model_result = await db.execute(model_query)
            model_rows = model_result.all()

            # Cost by task type
            task_query = select(
                ModelMetric.task_type,
                func.sum(ModelMetric.cost_usd).label('cost'),
                func.count(ModelMetric.id).label('executions')
            ).where(
                ModelMetric.created_at >= cutoff_date
            ).group_by(
                ModelMetric.task_type
            ).order_by(desc('cost'))

            task_result = await db.execute(task_query)
            task_rows = task_result.all()

            # Build analysis
            analysis = {
                'period_days': days,
                'total_cost_usd': float(total_row.total_cost or 0),
                'total_executions': int(total_row.total_executions or 0),
                'avg_cost_per_execution': (
                    float(total_row.total_cost or 0) / max(total_row.total_executions, 1)
                ),
                'cost_by_model': [
                    {
                        'model_id': row.model_id,
                        'cost_usd': float(row.cost),
                        'executions': int(row.executions),
                        'avg_cost': float(row.cost) / int(row.executions)
                    }
                    for row in model_rows
                ],
                'cost_by_task': [
                    {
                        'task_type': row.task_type,
                        'cost_usd': float(row.cost),
                        'executions': int(row.executions),
                        'avg_cost': float(row.cost) / int(row.executions)
                    }
                    for row in task_rows
                ]
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to get cost analysis: {e}")
            return {}

    async def get_recent_executions(
        self,
        db: AsyncSession,
        model_id: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent execution details.

        Args:
            db: Database session
            model_id: Optional model filter
            task_type: Optional task type filter
            limit: Maximum number of results

        Returns:
            List of recent execution records
        """
        try:
            from app.models.feedback import ModelMetric

            # Build filters
            filters = []
            if model_id:
                filters.append(ModelMetric.model_id == model_id)
            if task_type:
                filters.append(ModelMetric.task_type == task_type.value)

            # Query recent executions
            query = select(ModelMetric).where(
                and_(*filters) if filters else True
            ).order_by(
                desc(ModelMetric.created_at)
            ).limit(limit)

            result = await db.execute(query)
            metrics = result.scalars().all()

            # Convert to dict
            executions = []
            for metric in metrics:
                executions.append({
                    'id': metric.id,
                    'model_id': metric.model_id,
                    'task_type': metric.task_type,
                    'prompt_tokens': metric.prompt_tokens,
                    'completion_tokens': metric.completion_tokens,
                    'latency_ms': metric.latency_ms,
                    'cost_usd': metric.cost_usd,
                    'quality_score': metric.quality_score,
                    'user_approved': metric.user_approved,
                    'error_occurred': metric.error_occurred,
                    'created_at': metric.created_at.isoformat()
                })

            return executions

        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            return []


# Global tracker instance
_metric_tracker: Optional[MetricTracker] = None


def get_metric_tracker() -> MetricTracker:
    """Get or create the global metric tracker singleton."""
    global _metric_tracker
    if _metric_tracker is None:
        _metric_tracker = MetricTracker()
    return _metric_tracker
