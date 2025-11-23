"""
AI-GYM Pydantic Schemas

Request and response schemas for AI-GYM API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


# Enums
class TaskTypeEnum(str, Enum):
    """Task types for AI operations."""
    WEBSITE_ANALYSIS = "website_analysis"
    CODE_GENERATION = "code_generation"
    EMAIL_WRITING = "email_writing"
    CONVERSATION_RESPONSE = "conversation_response"
    LEAD_SCORING = "lead_scoring"
    CONTENT_SUMMARIZATION = "content_summarization"
    DATA_EXTRACTION = "data_extraction"
    QUALITY_ASSESSMENT = "quality_assessment"


class RoutingStrategy(str, Enum):
    """Model routing strategies."""
    BEST_QUALITY = "best_quality"
    BEST_COST = "best_cost"
    BALANCED = "balanced"
    FASTEST = "fastest"


class ModelCapabilityEnum(str, Enum):
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


# Model Registry Schemas
class AIModelSchema(BaseModel):
    """AI Model information schema."""
    id: str
    name: str
    provider: str
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    max_tokens: int
    capabilities: List[ModelCapabilityEnum]
    avg_latency_ms: int
    supports_streaming: bool
    default_temperature: float
    description: str
    cost_efficiency_score: float

    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Response for listing all models."""
    models: List[AIModelSchema]
    total: int


class ModelRecommendationRequest(BaseModel):
    """Request for model recommendation."""
    task_type: TaskTypeEnum
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    min_quality_score: Optional[float] = Field(None, ge=0, le=100)
    max_cost_per_request: Optional[Decimal] = Field(None, ge=0)
    exclude_models: Optional[List[str]] = None


class ModelRecommendationResponse(BaseModel):
    """Response with model recommendations."""
    recommended_model: AIModelSchema
    alternatives: List[AIModelSchema]
    reasoning: str


# Metric Tracking Schemas
class RecordMetricRequest(BaseModel):
    """Request to record execution metrics."""
    model_id: str
    task_type: TaskTypeEnum
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    cost_usd: Decimal = Field(ge=0)
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    user_approved: Optional[bool] = None
    edit_distance: Optional[int] = Field(None, ge=0)
    error_occurred: bool = False
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RecordMetricResponse(BaseModel):
    """Response after recording metric."""
    metric_id: int
    message: str


class RecordFeedbackRequest(BaseModel):
    """Request to record user feedback."""
    metric_id: int
    approved: bool
    edit_distance: Optional[int] = Field(None, ge=0)
    user_rating: Optional[float] = Field(None, ge=1, le=5)


class ModelStatsSchema(BaseModel):
    """Model statistics schema."""
    model_id: str
    task_type: Optional[TaskTypeEnum]
    total_executions: int
    avg_quality_score: float
    avg_cost_usd: Decimal
    avg_latency_ms: int
    approval_rate: float
    error_rate: float
    total_cost_usd: Decimal
    last_30_days_executions: int


class ModelStatsRequest(BaseModel):
    """Request for model statistics."""
    model_id: str
    task_type: Optional[TaskTypeEnum] = None
    days: int = Field(default=30, ge=1, le=365)


class TaskComparisonRequest(BaseModel):
    """Request for task comparison across models."""
    task_type: TaskTypeEnum
    days: int = Field(default=30, ge=1, le=365)


class TaskComparisonResponse(BaseModel):
    """Response with task comparison data."""
    task_type: TaskTypeEnum
    models: List[ModelStatsSchema]
    winner: Optional[str] = None
    summary: str


class CostAnalysisRequest(BaseModel):
    """Request for cost analysis."""
    days: int = Field(default=30, ge=1, le=365)


class CostByModel(BaseModel):
    """Cost breakdown by model."""
    model_id: str
    cost_usd: float
    executions: int
    avg_cost: float


class CostByTask(BaseModel):
    """Cost breakdown by task type."""
    task_type: str
    cost_usd: float
    executions: int
    avg_cost: float


class CostAnalysisResponse(BaseModel):
    """Response with cost analysis."""
    period_days: int
    total_cost_usd: float
    total_executions: int
    avg_cost_per_execution: float
    cost_by_model: List[CostByModel]
    cost_by_task: List[CostByTask]
    potential_savings: Optional[float] = None
    recommendations: List[str]


class RecentExecutionSchema(BaseModel):
    """Recent execution record."""
    id: int
    model_id: str
    task_type: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float
    quality_score: Optional[float]
    user_approved: Optional[bool]
    error_occurred: bool
    created_at: str


class RecentExecutionsRequest(BaseModel):
    """Request for recent executions."""
    model_id: Optional[str] = None
    task_type: Optional[TaskTypeEnum] = None
    limit: int = Field(default=50, ge=1, le=200)


class RecentExecutionsResponse(BaseModel):
    """Response with recent executions."""
    executions: List[RecentExecutionSchema]
    total: int


# A/B Testing Schemas
class CreateABTestRequest(BaseModel):
    """Request to create an A/B test."""
    test_name: str = Field(min_length=1, max_length=100)
    task_type: TaskTypeEnum
    variant_a_model: str
    variant_b_model: str
    traffic_split: float = Field(default=0.5, ge=0.1, le=0.9)
    min_sample_size: int = Field(default=100, ge=10)
    max_duration_days: int = Field(default=14, ge=1, le=90)
    target_metric: str = Field(default="quality", pattern="^(quality|cost|latency)$")

    @validator('variant_a_model', 'variant_b_model')
    def validate_model_ids(cls, v):
        if not v:
            raise ValueError("Model ID cannot be empty")
        return v


class CreateABTestResponse(BaseModel):
    """Response after creating A/B test."""
    test_id: int
    test_name: str
    message: str


class ABTestVariantSchema(BaseModel):
    """A/B test variant information."""
    name: str
    model_id: str
    traffic_pct: float
    sample_size: int
    avg_quality: Optional[float]
    avg_cost: Optional[float]
    mean_metric: Optional[float]
    std_metric: Optional[float]


class ABTestResultSchema(BaseModel):
    """A/B test results."""
    test_id: int
    test_name: str
    variant_a: ABTestVariantSchema
    variant_b: ABTestVariantSchema
    winner: str  # "A", "B", or "inconclusive"
    confidence_level: float
    p_value: float
    effect_size: float
    recommendation: str


class ABTestListItem(BaseModel):
    """A/B test list item."""
    test_name: str
    task_type: Optional[str]
    target_metric: Optional[str]
    start_date: Optional[str]
    variants: List[Dict[str, Any]]


class ABTestListResponse(BaseModel):
    """Response with list of A/B tests."""
    tests: List[ABTestListItem]
    total: int


class StopABTestRequest(BaseModel):
    """Request to stop an A/B test."""
    test_name: str


# Quality Scoring Schemas
class QualityScoreRequest(BaseModel):
    """Request to calculate quality score."""
    task_type: TaskTypeEnum
    output: str
    context: Optional[Dict[str, Any]] = None


class QualityScoreResponse(BaseModel):
    """Response with quality score."""
    quality_score: float
    dimensions: Optional[Dict[str, float]] = None
    details: str


# Dashboard/Analytics Schemas
class DashboardStatsResponse(BaseModel):
    """Dashboard overview statistics."""
    total_executions: int
    total_cost_usd: float
    avg_quality_score: float
    active_ab_tests: int
    top_model: Optional[str]
    cost_trend: str  # "increasing", "stable", "decreasing"
    quality_trend: str
    recommendations: List[str]


class ModelPerformanceTrend(BaseModel):
    """Model performance over time."""
    date: str
    executions: int
    avg_quality: float
    avg_cost: float
    avg_latency: int


class ModelTrendsRequest(BaseModel):
    """Request for model performance trends."""
    model_id: str
    task_type: Optional[TaskTypeEnum] = None
    days: int = Field(default=30, ge=7, le=90)


class ModelTrendsResponse(BaseModel):
    """Response with model performance trends."""
    model_id: str
    task_type: Optional[str]
    trends: List[ModelPerformanceTrend]
    summary: str
