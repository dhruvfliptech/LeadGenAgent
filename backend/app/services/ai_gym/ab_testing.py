"""
AI-GYM A/B Testing System

Manages controlled experiments comparing different AI models
to determine which performs better for specific tasks.
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import random
import logging
from scipy import stats
import numpy as np

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .models import TaskType, AIModel, get_model_registry

logger = logging.getLogger(__name__)


@dataclass
class ABTestConfig:
    """
    Configuration for an A/B test.

    Attributes:
        test_name: Unique name for the test
        task_type: Task type to test
        variant_a_model: Model ID for variant A
        variant_b_model: Model ID for variant B
        traffic_split: Traffic allocation (0.0-1.0 for variant A, rest for B)
        min_sample_size: Minimum samples before analysis
        max_duration_days: Maximum test duration
        target_metric: Primary metric to optimize ("quality", "cost", "latency")
    """
    test_name: str
    task_type: TaskType
    variant_a_model: str
    variant_b_model: str
    traffic_split: float = 0.5
    min_sample_size: int = 100
    max_duration_days: int = 14
    target_metric: str = "quality"


@dataclass
class ABTestResult:
    """
    Results of an A/B test.

    Attributes:
        test_id: Test identifier
        test_name: Test name
        variant_a: Variant A statistics
        variant_b: Variant B statistics
        winner: Which variant won ("A", "B", or "inconclusive")
        confidence_level: Statistical confidence (0-100)
        p_value: Statistical significance p-value
        effect_size: Magnitude of difference
        recommendation: Human-readable recommendation
    """
    test_id: int
    test_name: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    winner: str
    confidence_level: float
    p_value: float
    effect_size: float
    recommendation: str


class ABTestManager:
    """
    A/B test management system.

    Creates and manages controlled experiments comparing AI models,
    handles traffic splitting, and provides statistical analysis.
    """

    def __init__(self):
        """Initialize A/B test manager."""
        self.registry = get_model_registry()

    async def create_test(
        self,
        db: AsyncSession,
        config: ABTestConfig
    ) -> int:
        """
        Create a new A/B test.

        Args:
            db: Database session
            config: Test configuration

        Returns:
            Test ID

        Raises:
            ValueError: If models are invalid or test already exists
        """
        # Validate models exist
        model_a = self.registry.get_model(config.variant_a_model)
        model_b = self.registry.get_model(config.variant_b_model)

        if not model_a:
            raise ValueError(f"Model not found: {config.variant_a_model}")
        if not model_b:
            raise ValueError(f"Model not found: {config.variant_b_model}")

        # Check for existing active test with same name
        from app.models.feedback import ABTestVariant

        existing_query = select(ABTestVariant).where(
            and_(
                ABTestVariant.test_name == config.test_name,
                ABTestVariant.is_active == True
            )
        )
        result = await db.execute(existing_query)
        if result.first():
            raise ValueError(f"Active test already exists: {config.test_name}")

        try:
            # Create variant A
            variant_a = ABTestVariant(
                test_name=config.test_name,
                variant_name="A",
                model_id=config.variant_a_model,
                traffic_percentage=config.traffic_split * 100,
                is_control=True,
                is_active=True,
                sample_size=0,
                start_date=datetime.utcnow(),
                metadata={
                    'task_type': config.task_type.value,
                    'target_metric': config.target_metric,
                    'min_sample_size': config.min_sample_size,
                    'max_duration_days': config.max_duration_days
                }
            )

            # Create variant B
            variant_b = ABTestVariant(
                test_name=config.test_name,
                variant_name="B",
                model_id=config.variant_b_model,
                traffic_percentage=(1 - config.traffic_split) * 100,
                is_control=False,
                is_active=True,
                sample_size=0,
                start_date=datetime.utcnow(),
                metadata={
                    'task_type': config.task_type.value,
                    'target_metric': config.target_metric,
                    'min_sample_size': config.min_sample_size,
                    'max_duration_days': config.max_duration_days
                }
            )

            db.add(variant_a)
            db.add(variant_b)
            await db.commit()
            await db.refresh(variant_a)

            logger.info(
                f"Created A/B test '{config.test_name}': "
                f"{model_a.name} vs {model_b.name} for {config.task_type}"
            )

            return variant_a.id

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create A/B test: {e}")
            raise

    async def assign_variant(
        self,
        db: AsyncSession,
        test_name: str,
        task_type: TaskType
    ) -> Tuple[str, str]:
        """
        Assign a variant for a new request.

        Args:
            db: Database session
            test_name: Name of the test
            task_type: Task type

        Returns:
            Tuple of (variant_name, model_id)

        Raises:
            ValueError: If no active test found
        """
        try:
            from app.models.feedback import ABTestVariant

            # Get active variants for this test
            query = select(ABTestVariant).where(
                and_(
                    ABTestVariant.test_name == test_name,
                    ABTestVariant.is_active == True
                )
            )
            result = await db.execute(query)
            variants = result.scalars().all()

            if not variants:
                raise ValueError(f"No active test found: {test_name}")

            # Verify task type matches
            for variant in variants:
                metadata = variant.metadata or {}
                if metadata.get('task_type') != task_type.value:
                    raise ValueError(
                        f"Test {test_name} is for {metadata.get('task_type')}, "
                        f"not {task_type.value}"
                    )

            # Random assignment based on traffic split
            rand = random.random() * 100
            cumulative = 0.0

            for variant in variants:
                cumulative += variant.traffic_percentage
                if rand < cumulative:
                    # Increment sample count
                    variant.sample_size += 1
                    await db.commit()

                    return (variant.variant_name, variant.model_id)

            # Fallback to last variant
            last_variant = variants[-1]
            last_variant.sample_size += 1
            await db.commit()

            return (last_variant.variant_name, last_variant.model_id)

        except Exception as e:
            logger.error(f"Failed to assign variant: {e}")
            raise

    async def record_variant_result(
        self,
        db: AsyncSession,
        test_name: str,
        variant_name: str,
        quality_score: float,
        cost_usd: float
    ):
        """
        Record a result for a variant.

        Args:
            db: Database session
            test_name: Test name
            variant_name: Variant name
            quality_score: Quality score
            cost_usd: Cost in USD
        """
        try:
            from app.models.feedback import ABTestVariant

            query = select(ABTestVariant).where(
                and_(
                    ABTestVariant.test_name == test_name,
                    ABTestVariant.variant_name == variant_name,
                    ABTestVariant.is_active == True
                )
            )
            result = await db.execute(query)
            variant = result.scalar_one_or_none()

            if not variant:
                logger.warning(
                    f"Variant not found: {test_name}/{variant_name}"
                )
                return

            # Update running averages
            n = variant.sample_size
            if n > 0:
                # Running average formula
                old_avg_quality = variant.avg_quality_score or 0
                old_avg_cost = variant.avg_cost_usd or 0

                variant.avg_quality_score = (
                    (old_avg_quality * (n - 1) + quality_score) / n
                )
                variant.avg_cost_usd = (
                    (old_avg_cost * (n - 1) + cost_usd) / n
                )

                await db.commit()

        except Exception as e:
            logger.error(f"Failed to record variant result: {e}")

    async def analyze_test(
        self,
        db: AsyncSession,
        test_name: str
    ) -> Optional[ABTestResult]:
        """
        Perform statistical analysis of A/B test.

        Args:
            db: Database session
            test_name: Test name

        Returns:
            Test results or None if insufficient data
        """
        try:
            from app.models.feedback import ABTestVariant, ModelMetric

            # Get test variants
            variant_query = select(ABTestVariant).where(
                ABTestVariant.test_name == test_name
            ).order_by(ABTestVariant.variant_name)

            result = await db.execute(variant_query)
            variants = result.scalars().all()

            if len(variants) != 2:
                logger.warning(f"Test {test_name} does not have 2 variants")
                return None

            variant_a, variant_b = variants

            # Get metadata
            metadata_a = variant_a.metadata or {}
            task_type = metadata_a.get('task_type')
            target_metric = metadata_a.get('target_metric', 'quality')
            min_sample_size = metadata_a.get('min_sample_size', 100)

            # Check if we have enough data
            if variant_a.sample_size < min_sample_size or variant_b.sample_size < min_sample_size:
                return ABTestResult(
                    test_id=variant_a.id,
                    test_name=test_name,
                    variant_a={
                        'model_id': variant_a.model_id,
                        'sample_size': variant_a.sample_size,
                        'required_samples': min_sample_size
                    },
                    variant_b={
                        'model_id': variant_b.model_id,
                        'sample_size': variant_b.sample_size,
                        'required_samples': min_sample_size
                    },
                    winner="inconclusive",
                    confidence_level=0,
                    p_value=1.0,
                    effect_size=0,
                    recommendation="Insufficient data. Continue collecting samples."
                )

            # Get detailed metrics for each variant
            metrics_a = await self._get_variant_metrics(
                db, variant_a.model_id, task_type
            )
            metrics_b = await self._get_variant_metrics(
                db, variant_b.model_id, task_type
            )

            # Perform statistical test based on target metric
            if target_metric == "quality":
                metric_a = metrics_a['quality_scores']
                metric_b = metrics_b['quality_scores']
                higher_is_better = True
            elif target_metric == "cost":
                metric_a = metrics_a['costs']
                metric_b = metrics_b['costs']
                higher_is_better = False
            else:  # latency
                metric_a = metrics_a['latencies']
                metric_b = metrics_b['latencies']
                higher_is_better = False

            # Two-sample t-test
            t_stat, p_value = stats.ttest_ind(metric_a, metric_b)

            # Calculate effect size (Cohen's d)
            mean_a = np.mean(metric_a)
            mean_b = np.mean(metric_b)
            pooled_std = np.sqrt(
                (np.var(metric_a) + np.var(metric_b)) / 2
            )
            effect_size = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0

            # Determine winner
            confidence_level = (1 - p_value) * 100
            significant = p_value < 0.05

            if not significant:
                winner = "inconclusive"
                recommendation = (
                    f"No significant difference detected (p={p_value:.3f}). "
                    f"Continue testing or consider them equivalent."
                )
            else:
                if higher_is_better:
                    winner = "A" if mean_a > mean_b else "B"
                else:
                    winner = "A" if mean_a < mean_b else "B"

                winner_model = variant_a.model_id if winner == "A" else variant_b.model_id
                improvement = abs(effect_size) * 100

                recommendation = (
                    f"Variant {winner} ({winner_model}) is significantly better "
                    f"for {target_metric} with {improvement:.1f}% improvement "
                    f"(p={p_value:.3f}, confidence={confidence_level:.1f}%). "
                    f"Recommend rolling out to 100% traffic."
                )

            # Build result
            result = ABTestResult(
                test_id=variant_a.id,
                test_name=test_name,
                variant_a={
                    'model_id': variant_a.model_id,
                    'sample_size': variant_a.sample_size,
                    'avg_quality': variant_a.avg_quality_score,
                    'avg_cost': variant_a.avg_cost_usd,
                    'mean_metric': float(mean_a),
                    'std_metric': float(np.std(metric_a))
                },
                variant_b={
                    'model_id': variant_b.model_id,
                    'sample_size': variant_b.sample_size,
                    'avg_quality': variant_b.avg_quality_score,
                    'avg_cost': variant_b.avg_cost_usd,
                    'mean_metric': float(mean_b),
                    'std_metric': float(np.std(metric_b))
                },
                winner=winner,
                confidence_level=confidence_level,
                p_value=p_value,
                effect_size=effect_size,
                recommendation=recommendation
            )

            # Update variant statistics
            variant_a.statistical_significance = p_value
            variant_b.statistical_significance = p_value
            await db.commit()

            return result

        except Exception as e:
            logger.error(f"Failed to analyze test: {e}")
            return None

    async def _get_variant_metrics(
        self,
        db: AsyncSession,
        model_id: str,
        task_type: str
    ) -> Dict[str, List[float]]:
        """
        Get raw metrics for a variant.

        Args:
            db: Database session
            model_id: Model ID
            task_type: Task type

        Returns:
            Dictionary of metric arrays
        """
        from app.models.feedback import ModelMetric

        query = select(
            ModelMetric.quality_score,
            ModelMetric.cost_usd,
            ModelMetric.latency_ms
        ).where(
            and_(
                ModelMetric.model_id == model_id,
                ModelMetric.task_type == task_type
            )
        ).limit(1000)  # Limit for performance

        result = await db.execute(query)
        rows = result.all()

        metrics = {
            'quality_scores': [float(r.quality_score or 0) for r in rows],
            'costs': [float(r.cost_usd) for r in rows],
            'latencies': [float(r.latency_ms) for r in rows]
        }

        return metrics

    async def stop_test(
        self,
        db: AsyncSession,
        test_name: str
    ):
        """
        Stop an active A/B test.

        Args:
            db: Database session
            test_name: Test name
        """
        try:
            from app.models.feedback import ABTestVariant

            query = select(ABTestVariant).where(
                ABTestVariant.test_name == test_name
            )
            result = await db.execute(query)
            variants = result.scalars().all()

            for variant in variants:
                variant.is_active = False
                variant.end_date = datetime.utcnow()

            await db.commit()

            logger.info(f"Stopped A/B test: {test_name}")

        except Exception as e:
            logger.error(f"Failed to stop test: {e}")
            await db.rollback()
            raise

    async def list_active_tests(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        List all active A/B tests.

        Args:
            db: Database session

        Returns:
            List of active tests
        """
        try:
            from app.models.feedback import ABTestVariant

            query = select(ABTestVariant).where(
                ABTestVariant.is_active == True
            ).order_by(ABTestVariant.test_name, ABTestVariant.variant_name)

            result = await db.execute(query)
            variants = result.scalars().all()

            # Group by test name
            tests = {}
            for variant in variants:
                test_name = variant.test_name
                if test_name not in tests:
                    metadata = variant.metadata or {}
                    tests[test_name] = {
                        'test_name': test_name,
                        'task_type': metadata.get('task_type'),
                        'target_metric': metadata.get('target_metric'),
                        'start_date': variant.start_date.isoformat() if variant.start_date else None,
                        'variants': []
                    }

                tests[test_name]['variants'].append({
                    'name': variant.variant_name,
                    'model_id': variant.model_id,
                    'traffic_pct': variant.traffic_percentage,
                    'sample_size': variant.sample_size,
                    'avg_quality': variant.avg_quality_score,
                    'avg_cost': variant.avg_cost_usd
                })

            return list(tests.values())

        except Exception as e:
            logger.error(f"Failed to list active tests: {e}")
            return []


# Global manager instance
_ab_test_manager: Optional[ABTestManager] = None


def get_ab_test_manager() -> ABTestManager:
    """Get or create the global A/B test manager singleton."""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager
