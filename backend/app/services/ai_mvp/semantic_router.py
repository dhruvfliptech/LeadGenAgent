"""
Semantic Router - Routes AI tasks to appropriate models based on complexity.

Achieves 70-85% cost savings by:
1. Simple tasks → Ultra-cheap models ($0.14-0.27/M tokens)
2. Complex tasks → Route by lead value
3. Critical tasks → Always premium

Based on research from Claudes_Updates/03_COST_OPTIMIZATION_GUIDE.md
"""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel
import re


class TaskComplexity(str, Enum):
    """Task complexity levels for routing."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class TaskType(str, Enum):
    """Types of AI tasks in the system."""
    # Simple tasks (route to cheap models)
    CATEGORY_CLASSIFICATION = "category_classification"
    SPAM_DETECTION = "spam_detection"
    EMAIL_SUBJECT = "email_subject"
    SHORT_SUMMARY = "short_summary"

    # Moderate tasks (route based on lead value)
    WEBSITE_ANALYSIS = "website_analysis"
    EMAIL_BODY = "email_body"
    PAIN_POINT_EXTRACTION = "pain_point_extraction"

    # Complex tasks (route to premium if high-value lead)
    DEMO_SITE_PLANNING = "demo_site_planning"
    VIDEO_SCRIPT = "video_script"
    CUSTOM_STRATEGY = "custom_strategy"

    # Critical tasks (always premium)
    CONVERSATION_RESPONSE = "conversation_response"
    OBJECTION_HANDLING = "objection_handling"
    FINAL_EMAIL_APPROVAL = "final_email_approval"


class ModelTier(str, Enum):
    """Model tiers with pricing."""
    ULTRA_CHEAP = "ultra_cheap"  # $0.14-0.27/M tokens (Gemini Flash, Llama 3.1 8B)
    CHEAP = "cheap"              # $0.30-0.60/M tokens (Qwen 2.5 7B, DeepSeek V3)
    MODERATE = "moderate"        # $2.00-3.00/M tokens (GPT-4o-mini, Claude Haiku)
    PREMIUM = "premium"          # $15.00-20.00/M tokens (Claude Sonnet 4, GPT-4o)


class RouteDecision(BaseModel):
    """Routing decision with model and reasoning."""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix

    model_name: str
    model_tier: ModelTier
    task_complexity: TaskComplexity
    reasoning: str
    estimated_cost: float  # Per request estimate


class SemanticRouter:
    """
    Routes AI tasks to appropriate models based on task complexity and lead value.

    Routing Logic:
    - Simple tasks → Always ultra-cheap models
    - Moderate tasks → Cheap models by default, moderate if lead value > $25K
    - Complex tasks → Moderate by default, premium if lead value > $100K
    - Critical tasks → Always premium (customer-facing, high stakes)
    """

    # Model definitions with OpenRouter IDs (verified working)
    MODELS = {
        # Ultra-cheap tier ($0.14-0.27/M tokens)
        ModelTier.ULTRA_CHEAP: {
            "meta-llama/llama-3.1-8b-instruct": {"input": 0.055, "output": 0.14},
            "google/gemini-flash-1.5-8b": {"input": 0.075, "output": 0.30},
        },
        # Cheap tier ($0.30-0.60/M tokens)
        ModelTier.CHEAP: {
            "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
        },
        # Moderate tier ($2-3/M tokens)
        ModelTier.MODERATE: {
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
        },
        # Premium tier ($15-20/M tokens)
        ModelTier.PREMIUM: {
            "anthropic/claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
            "openai/gpt-4o": {"input": 2.50, "output": 10.00},
        },
    }

    # Task complexity mapping
    TASK_COMPLEXITY_MAP = {
        # Simple (always ultra-cheap)
        TaskType.CATEGORY_CLASSIFICATION: TaskComplexity.SIMPLE,
        TaskType.SPAM_DETECTION: TaskComplexity.SIMPLE,
        TaskType.EMAIL_SUBJECT: TaskComplexity.SIMPLE,
        TaskType.SHORT_SUMMARY: TaskComplexity.SIMPLE,

        # Moderate (value-based routing)
        TaskType.WEBSITE_ANALYSIS: TaskComplexity.MODERATE,
        TaskType.EMAIL_BODY: TaskComplexity.MODERATE,
        TaskType.PAIN_POINT_EXTRACTION: TaskComplexity.MODERATE,

        # Complex (value-based routing)
        TaskType.DEMO_SITE_PLANNING: TaskComplexity.COMPLEX,
        TaskType.VIDEO_SCRIPT: TaskComplexity.COMPLEX,
        TaskType.CUSTOM_STRATEGY: TaskComplexity.COMPLEX,

        # Critical (always premium)
        TaskType.CONVERSATION_RESPONSE: TaskComplexity.CRITICAL,
        TaskType.OBJECTION_HANDLING: TaskComplexity.CRITICAL,
        TaskType.FINAL_EMAIL_APPROVAL: TaskComplexity.CRITICAL,
    }

    def __init__(self, default_cheap_model: str = "meta-llama/llama-3.1-8b-instruct"):
        """Initialize router with default model."""
        self.default_cheap_model = default_cheap_model

    def route(
        self,
        task_type: TaskType,
        lead_value: Optional[float] = None,
        force_tier: Optional[ModelTier] = None
    ) -> RouteDecision:
        """
        Route task to appropriate model.

        Args:
            task_type: Type of AI task
            lead_value: Estimated lead value in dollars (for value-based routing)
            force_tier: Force a specific model tier (for testing/overrides)

        Returns:
            RouteDecision with model selection and reasoning
        """
        complexity = self.TASK_COMPLEXITY_MAP[task_type]

        # Forced tier (for testing or user overrides)
        if force_tier:
            model_name = self._get_best_model_in_tier(force_tier)
            return RouteDecision(
                model_name=model_name,
                model_tier=force_tier,
                task_complexity=complexity,
                reasoning=f"User forced {force_tier.value} tier",
                estimated_cost=self._estimate_cost(model_name, 500, 100)
            )

        # Simple tasks → Always ultra-cheap
        if complexity == TaskComplexity.SIMPLE:
            model_name = self.default_cheap_model
            return RouteDecision(
                model_name=model_name,
                model_tier=ModelTier.ULTRA_CHEAP,
                task_complexity=complexity,
                reasoning="Simple task, using ultra-cheap model for cost efficiency",
                estimated_cost=self._estimate_cost(model_name, 200, 50)
            )

        # Critical tasks → Always premium
        if complexity == TaskComplexity.CRITICAL:
            model_name = "anthropic/claude-3.5-sonnet"
            return RouteDecision(
                model_name=model_name,
                model_tier=ModelTier.PREMIUM,
                task_complexity=complexity,
                reasoning="Critical customer-facing task, using premium model",
                estimated_cost=self._estimate_cost(model_name, 800, 300)
            )

        # Moderate tasks → Value-based routing
        if complexity == TaskComplexity.MODERATE:
            if lead_value and lead_value >= 25000:
                model_name = "anthropic/claude-3.5-sonnet"
                tier = ModelTier.MODERATE
                reasoning = f"Lead value ${lead_value:,.0f} justifies moderate-tier model"
            else:
                model_name = "anthropic/claude-3-haiku"
                tier = ModelTier.CHEAP
                reasoning = f"Lead value ${lead_value or 0:,.0f} uses cheap model"

            return RouteDecision(
                model_name=model_name,
                model_tier=tier,
                task_complexity=complexity,
                reasoning=reasoning,
                estimated_cost=self._estimate_cost(model_name, 1000, 300)
            )

        # Complex tasks → Value-based routing
        if complexity == TaskComplexity.COMPLEX:
            if lead_value and lead_value >= 100000:
                model_name = "anthropic/claude-3.5-sonnet"
                tier = ModelTier.PREMIUM
                reasoning = f"High-value lead ${lead_value:,.0f} uses premium model"
            elif lead_value and lead_value >= 25000:
                model_name = "anthropic/claude-3.5-sonnet"
                tier = ModelTier.MODERATE
                reasoning = f"Mid-value lead ${lead_value:,.0f} uses moderate model"
            else:
                model_name = "anthropic/claude-3-haiku"
                tier = ModelTier.CHEAP
                reasoning = f"Standard lead ${lead_value or 0:,.0f} uses cheap model"

            return RouteDecision(
                model_name=model_name,
                model_tier=tier,
                task_complexity=complexity,
                reasoning=reasoning,
                estimated_cost=self._estimate_cost(model_name, 2000, 500)
            )

        # Fallback (should never reach here)
        model_name = self.default_cheap_model
        return RouteDecision(
            model_name=model_name,
            model_tier=ModelTier.ULTRA_CHEAP,
            task_complexity=complexity,
            reasoning="Fallback to cheap model",
            estimated_cost=self._estimate_cost(model_name, 500, 100)
        )

    def _get_best_model_in_tier(self, tier: ModelTier) -> str:
        """Get the best (first) model in a tier."""
        models = list(self.MODELS[tier].keys())
        return models[0] if models else self.default_cheap_model

    def _estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for a request.

        Args:
            model_name: OpenRouter model ID
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens

        Returns:
            Estimated cost in dollars
        """
        # Find model pricing
        for tier_models in self.MODELS.values():
            if model_name in tier_models:
                pricing = tier_models[model_name]
                input_cost = (input_tokens / 1_000_000) * pricing["input"]
                output_cost = (output_tokens / 1_000_000) * pricing["output"]
                return input_cost + output_cost

        # Unknown model, estimate conservatively
        return 0.01

    def get_model_info(self, model_name: str) -> dict:
        """Get pricing info for a model."""
        for tier, models in self.MODELS.items():
            if model_name in models:
                return {
                    "model_name": model_name,
                    "tier": tier.value,
                    "pricing": models[model_name]
                }
        return {"model_name": model_name, "tier": "unknown", "pricing": {}}
