"""
AI-GYM Model Registry

Manages the catalog of available AI models with their capabilities,
costs, and performance characteristics.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Dict, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    LONG_CONTEXT = "long_context"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    MULTILINGUAL = "multilingual"
    REASONING = "reasoning"
    CREATIVE = "creative"
    FAST = "fast"


class TaskType(str, Enum):
    """Supported task types for AI operations."""
    WEBSITE_ANALYSIS = "website_analysis"
    CODE_GENERATION = "code_generation"
    EMAIL_WRITING = "email_writing"
    CONVERSATION_RESPONSE = "conversation_response"
    LEAD_SCORING = "lead_scoring"
    CONTENT_SUMMARIZATION = "content_summarization"
    DATA_EXTRACTION = "data_extraction"
    QUALITY_ASSESSMENT = "quality_assessment"


@dataclass
class AIModel:
    """
    AI Model definition with capabilities and cost information.

    Attributes:
        id: Unique model identifier (e.g., "openai/gpt-4-turbo-preview")
        name: Human-readable name
        provider: Provider name (openai, anthropic, etc.)
        cost_per_1k_input_tokens: Cost per 1000 input tokens in USD
        cost_per_1k_output_tokens: Cost per 1000 output tokens in USD
        max_tokens: Maximum context window size
        capabilities: Set of model capabilities
        avg_latency_ms: Average response latency in milliseconds
        supports_streaming: Whether model supports streaming responses
        default_temperature: Default temperature setting
        description: Model description
    """
    id: str
    name: str
    provider: str
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    max_tokens: int
    capabilities: Set[ModelCapability]
    avg_latency_ms: int = 1000
    supports_streaming: bool = True
    default_temperature: float = 0.7
    description: str = ""

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """
        Calculate total cost for a request.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        input_cost = (Decimal(input_tokens) / Decimal(1000)) * self.cost_per_1k_input_tokens
        output_cost = (Decimal(output_tokens) / Decimal(1000)) * self.cost_per_1k_output_tokens
        return input_cost + output_cost

    def has_capability(self, capability: ModelCapability) -> bool:
        """Check if model has a specific capability."""
        return capability in self.capabilities

    def cost_efficiency_score(self) -> float:
        """
        Calculate cost efficiency score (lower cost = higher score).

        Returns:
            Score from 0-100, where 100 is most cost-efficient
        """
        # Average cost per 1k tokens (weighted 60% input, 40% output)
        avg_cost = float(
            (self.cost_per_1k_input_tokens * Decimal("0.6")) +
            (self.cost_per_1k_output_tokens * Decimal("0.4"))
        )

        # Normalize: $0.01/1k tokens = 100, $0.10/1k tokens = 0
        max_cost = 0.10
        min_cost = 0.001

        if avg_cost <= min_cost:
            return 100.0
        if avg_cost >= max_cost:
            return 0.0

        # Linear interpolation
        score = 100 * (1 - (avg_cost - min_cost) / (max_cost - min_cost))
        return max(0.0, min(100.0, score))


class ModelRegistry:
    """
    Registry of available AI models.

    Manages the catalog of models with their capabilities and costs.
    Provides lookup and filtering functionality.
    """

    def __init__(self):
        """Initialize model registry with available models."""
        self.models: Dict[str, AIModel] = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize the registry with available models and current pricing."""

        # OpenAI GPT-4 Turbo - High quality, expensive, great for complex tasks
        self.register_model(AIModel(
            id="openai/gpt-4-turbo-preview",
            name="GPT-4 Turbo",
            provider="openai",
            cost_per_1k_input_tokens=Decimal("0.01"),
            cost_per_1k_output_tokens=Decimal("0.03"),
            max_tokens=128000,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
                ModelCapability.VISION,
            },
            avg_latency_ms=2000,
            description="Most capable GPT-4 model with 128k context window"
        ))

        # OpenAI GPT-4o - Balanced performance and cost
        self.register_model(AIModel(
            id="openai/gpt-4o",
            name="GPT-4o",
            provider="openai",
            cost_per_1k_input_tokens=Decimal("0.0025"),
            cost_per_1k_output_tokens=Decimal("0.01"),
            max_tokens=128000,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
                ModelCapability.VISION,
                ModelCapability.FAST,
            },
            avg_latency_ms=1200,
            description="Optimized GPT-4 with better speed and cost"
        ))

        # Anthropic Claude 3.5 Sonnet - Best reasoning and analysis
        self.register_model(AIModel(
            id="anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            provider="anthropic",
            cost_per_1k_input_tokens=Decimal("0.003"),
            cost_per_1k_output_tokens=Decimal("0.015"),
            max_tokens=200000,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
                ModelCapability.VISION,
            },
            avg_latency_ms=1800,
            description="Anthropic's most intelligent model with superior reasoning"
        ))

        # Anthropic Claude 3 Haiku - Fast and cheap
        self.register_model(AIModel(
            id="anthropic/claude-3-haiku",
            name="Claude 3 Haiku",
            provider="anthropic",
            cost_per_1k_input_tokens=Decimal("0.00025"),
            cost_per_1k_output_tokens=Decimal("0.00125"),
            max_tokens=200000,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.FAST,
            },
            avg_latency_ms=600,
            description="Fastest Claude model for simple tasks"
        ))

        # Qwen 2.5 72B - Great multilingual, cost-effective
        self.register_model(AIModel(
            id="qwen/qwen-2.5-72b-instruct",
            name="Qwen 2.5 72B",
            provider="qwen",
            cost_per_1k_input_tokens=Decimal("0.0004"),
            cost_per_1k_output_tokens=Decimal("0.0004"),
            max_tokens=32768,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.MULTILINGUAL,
                ModelCapability.REASONING,
            },
            avg_latency_ms=1000,
            description="Alibaba's multilingual model with strong coding abilities"
        ))

        # Grok Beta - Creative and conversational
        self.register_model(AIModel(
            id="x-ai/grok-beta",
            name="Grok Beta",
            provider="x-ai",
            cost_per_1k_input_tokens=Decimal("0.005"),
            cost_per_1k_output_tokens=Decimal("0.015"),
            max_tokens=131072,
            capabilities={
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CREATIVE,
                ModelCapability.LONG_CONTEXT,
                ModelCapability.REASONING,
            },
            avg_latency_ms=1500,
            description="X.AI's creative and conversational model"
        ))

        # DeepSeek Coder - Specialized for code
        self.register_model(AIModel(
            id="deepseek/deepseek-coder",
            name="DeepSeek Coder",
            provider="deepseek",
            cost_per_1k_input_tokens=Decimal("0.00014"),
            cost_per_1k_output_tokens=Decimal("0.00028"),
            max_tokens=16384,
            capabilities={
                ModelCapability.CODE_GENERATION,
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST,
            },
            avg_latency_ms=800,
            description="Specialized for code generation and analysis"
        ))

        # OpenAI Embeddings
        self.register_model(AIModel(
            id="openai/text-embedding-ada-002",
            name="Ada Embeddings",
            provider="openai",
            cost_per_1k_input_tokens=Decimal("0.0001"),
            cost_per_1k_output_tokens=Decimal("0"),
            max_tokens=8191,
            capabilities={
                ModelCapability.EMBEDDINGS,
            },
            avg_latency_ms=300,
            supports_streaming=False,
            description="OpenAI's embedding model for semantic search"
        ))

        logger.info(f"Initialized AI-GYM with {len(self.models)} models")

    def register_model(self, model: AIModel):
        """Register a new model in the registry."""
        self.models[model.id] = model
        logger.debug(f"Registered model: {model.name} ({model.id})")

    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get a model by ID."""
        return self.models.get(model_id)

    def get_all_models(self) -> List[AIModel]:
        """Get all registered models."""
        return list(self.models.values())

    def get_models_by_capability(self, capability: ModelCapability) -> List[AIModel]:
        """Get all models with a specific capability."""
        return [
            model for model in self.models.values()
            if model.has_capability(capability)
        ]

    def get_models_by_provider(self, provider: str) -> List[AIModel]:
        """Get all models from a specific provider."""
        return [
            model for model in self.models.values()
            if model.provider == provider
        ]

    def get_cheapest_model(
        self,
        capability: Optional[ModelCapability] = None
    ) -> Optional[AIModel]:
        """
        Get the cheapest model, optionally filtered by capability.

        Args:
            capability: Optional capability filter

        Returns:
            Cheapest model or None
        """
        models = self.models.values()
        if capability:
            models = [m for m in models if m.has_capability(capability)]

        if not models:
            return None

        return min(
            models,
            key=lambda m: m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens
        )

    def get_fastest_model(
        self,
        capability: Optional[ModelCapability] = None
    ) -> Optional[AIModel]:
        """
        Get the fastest model, optionally filtered by capability.

        Args:
            capability: Optional capability filter

        Returns:
            Fastest model or None
        """
        models = self.models.values()
        if capability:
            models = [m for m in models if m.has_capability(capability)]

        if not models:
            return None

        return min(models, key=lambda m: m.avg_latency_ms)

    def recommend_models_for_task(
        self,
        task_type: TaskType,
        strategy: str = "balanced"
    ) -> List[AIModel]:
        """
        Recommend models for a specific task type.

        Args:
            task_type: Type of task
            strategy: Selection strategy ("best_quality", "best_cost", "balanced", "fastest")

        Returns:
            List of recommended models, ordered by suitability
        """
        # Map task types to required capabilities
        task_capability_map = {
            TaskType.WEBSITE_ANALYSIS: {ModelCapability.REASONING, ModelCapability.TEXT_GENERATION},
            TaskType.CODE_GENERATION: {ModelCapability.CODE_GENERATION},
            TaskType.EMAIL_WRITING: {ModelCapability.TEXT_GENERATION},
            TaskType.CONVERSATION_RESPONSE: {ModelCapability.TEXT_GENERATION},
            TaskType.LEAD_SCORING: {ModelCapability.REASONING, ModelCapability.TEXT_GENERATION},
            TaskType.CONTENT_SUMMARIZATION: {ModelCapability.TEXT_GENERATION},
            TaskType.DATA_EXTRACTION: {ModelCapability.REASONING},
            TaskType.QUALITY_ASSESSMENT: {ModelCapability.REASONING},
        }

        required_capabilities = task_capability_map.get(task_type, {ModelCapability.TEXT_GENERATION})

        # Filter models that have all required capabilities
        suitable_models = [
            model for model in self.models.values()
            if all(model.has_capability(cap) for cap in required_capabilities)
        ]

        if not suitable_models:
            logger.warning(f"No suitable models found for task: {task_type}")
            return []

        # Sort based on strategy
        if strategy == "best_quality":
            # Premium models first (GPT-4, Claude 3.5)
            quality_order = [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4-turbo-preview",
                "openai/gpt-4o",
                "x-ai/grok-beta",
            ]
            suitable_models.sort(
                key=lambda m: quality_order.index(m.id) if m.id in quality_order else 999
            )
        elif strategy == "best_cost":
            # Sort by cost (cheapest first)
            suitable_models.sort(
                key=lambda m: m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens
            )
        elif strategy == "fastest":
            # Sort by latency (fastest first)
            suitable_models.sort(key=lambda m: m.avg_latency_ms)
        else:  # balanced
            # Use cost efficiency score with quality weighting
            def balanced_score(model: AIModel) -> float:
                cost_score = model.cost_efficiency_score()
                speed_score = 100 * (1 - min(model.avg_latency_ms / 3000, 1))

                # Premium models get a quality bonus
                quality_bonus = 0
                if model.id in ["anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo-preview"]:
                    quality_bonus = 20
                elif model.id in ["openai/gpt-4o"]:
                    quality_bonus = 15

                return (cost_score * 0.5) + (speed_score * 0.3) + quality_bonus

            suitable_models.sort(key=balanced_score, reverse=True)

        return suitable_models


# Global registry instance
_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get or create the global model registry singleton."""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry
