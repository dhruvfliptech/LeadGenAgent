"""
AI-GYM Model Router

Intelligent routing system that selects the optimal AI model for each task
based on historical performance data, cost constraints, and quality requirements.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
import random
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AIModel, ModelRegistry, TaskType, get_model_registry

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Intelligent model routing system.

    Selects the optimal model for each task based on:
    - Historical performance metrics
    - Cost constraints
    - Quality requirements
    - Task-specific characteristics
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        """
        Initialize model router.

        Args:
            registry: Model registry (uses global if not provided)
        """
        self.registry = registry or get_model_registry()

    async def route(
        self,
        task_type: TaskType,
        strategy: str = "balanced",
        db: Optional[AsyncSession] = None,
        min_quality_score: Optional[float] = None,
        max_cost_per_request: Optional[Decimal] = None,
        exclude_models: Optional[List[str]] = None
    ) -> AIModel:
        """
        Route to the best model for a given task.

        Args:
            task_type: Type of task to perform
            strategy: Routing strategy ("best_quality", "best_cost", "balanced", "fastest")
            db: Database session for historical data (optional)
            min_quality_score: Minimum quality score threshold (0-100)
            max_cost_per_request: Maximum cost per request in USD
            exclude_models: Model IDs to exclude from selection

        Returns:
            Selected AI model

        Raises:
            ValueError: If no suitable model found
        """
        exclude_models = exclude_models or []

        # Get recommended models from registry
        candidates = self.registry.recommend_models_for_task(task_type, strategy)

        # Filter out excluded models
        candidates = [m for m in candidates if m.id not in exclude_models]

        if not candidates:
            raise ValueError(f"No suitable models found for task: {task_type}")

        # If we have database access, enhance selection with historical data
        if db:
            candidates = await self._rank_by_historical_performance(
                candidates,
                task_type,
                strategy,
                db
            )

        # Apply quality filter
        if min_quality_score is not None and db:
            candidates = await self._filter_by_quality(
                candidates,
                task_type,
                min_quality_score,
                db
            )

        # Apply cost filter (rough estimate)
        if max_cost_per_request is not None:
            # Assume average request: 1000 input tokens, 500 output tokens
            candidates = [
                m for m in candidates
                if m.calculate_cost(1000, 500) <= max_cost_per_request
            ]

        if not candidates:
            raise ValueError(
                f"No models meet constraints for task: {task_type} "
                f"(quality>={min_quality_score}, cost<=${max_cost_per_request})"
            )

        # Return top candidate
        selected_model = candidates[0]
        logger.info(
            f"Routed {task_type} to {selected_model.name} "
            f"(strategy={strategy}, cost_efficiency={selected_model.cost_efficiency_score():.1f})"
        )
        return selected_model

    async def route_council(
        self,
        task_type: TaskType,
        num_models: int = 3,
        diversity: str = "balanced",
        db: Optional[AsyncSession] = None
    ) -> List[AIModel]:
        """
        Select multiple models for ensemble/council decision making.

        Args:
            task_type: Type of task
            num_models: Number of models to select
            diversity: How to diversify selection ("providers", "balanced", "quality_tiers")
            db: Database session for historical data

        Returns:
            List of selected models for council
        """
        # Get suitable models
        candidates = self.registry.recommend_models_for_task(task_type, "balanced")

        if len(candidates) < num_models:
            logger.warning(
                f"Only {len(candidates)} models available for council, requested {num_models}"
            )
            num_models = len(candidates)

        selected: List[AIModel] = []

        if diversity == "providers":
            # Select models from different providers
            providers_used = set()
            for model in candidates:
                if model.provider not in providers_used:
                    selected.append(model)
                    providers_used.add(model.provider)
                    if len(selected) >= num_models:
                        break

            # Fill remaining slots if needed
            remaining = [m for m in candidates if m not in selected]
            selected.extend(remaining[:num_models - len(selected)])

        elif diversity == "quality_tiers":
            # Select from different quality/cost tiers
            # Tier 1: Premium (Claude 3.5, GPT-4)
            tier1 = [m for m in candidates if m.cost_per_1k_input_tokens > Decimal("0.002")]
            # Tier 2: Mid-range
            tier2 = [m for m in candidates if Decimal("0.0005") <= m.cost_per_1k_input_tokens <= Decimal("0.002")]
            # Tier 3: Budget
            tier3 = [m for m in candidates if m.cost_per_1k_input_tokens < Decimal("0.0005")]

            # Take from each tier
            if tier1:
                selected.append(tier1[0])
            if tier2 and len(selected) < num_models:
                selected.append(tier2[0])
            if tier3 and len(selected) < num_models:
                selected.append(tier3[0])

            # Fill remaining
            remaining = [m for m in candidates if m not in selected]
            selected.extend(remaining[:num_models - len(selected)])

        else:  # balanced
            # Select top N from balanced ranking
            selected = candidates[:num_models]

        logger.info(
            f"Created council of {len(selected)} models for {task_type}: "
            f"{[m.name for m in selected]}"
        )
        return selected

    async def _rank_by_historical_performance(
        self,
        candidates: List[AIModel],
        task_type: TaskType,
        strategy: str,
        db: AsyncSession
    ) -> List[AIModel]:
        """
        Rank models based on historical performance data.

        Args:
            candidates: Candidate models
            task_type: Task type
            strategy: Routing strategy
            db: Database session

        Returns:
            Re-ranked list of models
        """
        try:
            from app.models.feedback import ModelMetric

            # Get performance stats for each model in the last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            model_stats = {}
            for model in candidates:
                # Query historical metrics
                query = select(
                    func.avg(ModelMetric.quality_score).label('avg_quality'),
                    func.avg(ModelMetric.cost_usd).label('avg_cost'),
                    func.avg(ModelMetric.latency_ms).label('avg_latency'),
                    func.count(ModelMetric.id).label('sample_count')
                ).where(
                    and_(
                        ModelMetric.model_id == model.id,
                        ModelMetric.task_type == task_type.value,
                        ModelMetric.created_at >= cutoff_date
                    )
                )

                result = await db.execute(query)
                row = result.first()

                if row and row.sample_count > 0:
                    model_stats[model.id] = {
                        'avg_quality': float(row.avg_quality or 0),
                        'avg_cost': float(row.avg_cost or 0),
                        'avg_latency': float(row.avg_latency or 0),
                        'sample_count': int(row.sample_count)
                    }
                else:
                    # No historical data - use defaults
                    model_stats[model.id] = {
                        'avg_quality': 70.0,  # Neutral default
                        'avg_cost': float(model.calculate_cost(1000, 500)),
                        'avg_latency': model.avg_latency_ms,
                        'sample_count': 0
                    }

            # Rank based on strategy with historical data
            def ranking_score(model: AIModel) -> float:
                stats = model_stats.get(model.id, {})
                quality = stats.get('avg_quality', 70.0)
                cost = stats.get('avg_cost', 1.0)
                latency = stats.get('avg_latency', 1000)
                sample_count = stats.get('sample_count', 0)

                # Confidence factor (more samples = more confident)
                confidence = min(sample_count / 100, 1.0)

                if strategy == "best_quality":
                    # Prioritize quality
                    base_score = quality
                elif strategy == "best_cost":
                    # Prioritize low cost (normalize to 0-100 scale)
                    base_score = max(0, 100 - (cost * 100))
                elif strategy == "fastest":
                    # Prioritize low latency
                    base_score = max(0, 100 - (latency / 30))
                else:  # balanced
                    # Weighted combination
                    quality_score = quality
                    cost_score = max(0, 100 - (cost * 50))
                    speed_score = max(0, 100 - (latency / 30))
                    base_score = (quality_score * 0.5) + (cost_score * 0.3) + (speed_score * 0.2)

                # Blend with default score based on confidence
                default_score = 70.0
                return (base_score * confidence) + (default_score * (1 - confidence))

            candidates.sort(key=ranking_score, reverse=True)
            logger.debug(
                f"Re-ranked {len(candidates)} models by historical performance for {task_type}"
            )

        except Exception as e:
            logger.warning(f"Failed to rank by historical performance: {e}")

        return candidates

    async def _filter_by_quality(
        self,
        candidates: List[AIModel],
        task_type: TaskType,
        min_quality_score: float,
        db: AsyncSession
    ) -> List[AIModel]:
        """
        Filter models by minimum quality score from historical data.

        Args:
            candidates: Candidate models
            task_type: Task type
            min_quality_score: Minimum quality threshold
            db: Database session

        Returns:
            Filtered list of models
        """
        try:
            from app.models.feedback import ModelMetric

            cutoff_date = datetime.utcnow() - timedelta(days=30)
            qualified_models = []

            for model in candidates:
                # Get average quality score
                query = select(
                    func.avg(ModelMetric.quality_score).label('avg_quality'),
                    func.count(ModelMetric.id).label('sample_count')
                ).where(
                    and_(
                        ModelMetric.model_id == model.id,
                        ModelMetric.task_type == task_type.value,
                        ModelMetric.created_at >= cutoff_date
                    )
                )

                result = await db.execute(query)
                row = result.first()

                # Include if meets threshold or no historical data yet
                if not row or row.sample_count == 0:
                    # No data - give it a chance
                    qualified_models.append(model)
                elif row.avg_quality >= min_quality_score:
                    qualified_models.append(model)

            return qualified_models

        except Exception as e:
            logger.warning(f"Failed to filter by quality: {e}")
            return candidates

    async def route_with_fallback(
        self,
        task_type: TaskType,
        preferred_strategy: str = "balanced",
        fallback_strategy: str = "best_cost",
        db: Optional[AsyncSession] = None,
        **kwargs
    ) -> AIModel:
        """
        Route with fallback strategy if primary fails.

        Args:
            task_type: Task type
            preferred_strategy: Primary routing strategy
            fallback_strategy: Fallback strategy if primary fails
            db: Database session
            **kwargs: Additional routing parameters

        Returns:
            Selected model
        """
        try:
            return await self.route(task_type, preferred_strategy, db, **kwargs)
        except ValueError as e:
            logger.warning(
                f"Primary routing failed ({preferred_strategy}): {e}. "
                f"Trying fallback ({fallback_strategy})"
            )
            # Remove constraints for fallback
            return await self.route(
                task_type,
                fallback_strategy,
                db,
                min_quality_score=None,
                max_cost_per_request=None
            )

    def get_model_by_id(self, model_id: str) -> Optional[AIModel]:
        """Get a specific model by ID."""
        return self.registry.get_model(model_id)

    def list_all_models(self) -> List[AIModel]:
        """List all available models."""
        return self.registry.get_all_models()


# Global router instance
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create the global model router singleton."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router
