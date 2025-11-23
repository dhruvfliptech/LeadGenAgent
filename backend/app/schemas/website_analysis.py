"""
Pydantic schemas for Website Analysis API.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisDepth(str, Enum):
    """Analysis depth options."""
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"


class Priority(str, Enum):
    """Improvement priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Difficulty(str, Enum):
    """Implementation difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Category(str, Enum):
    """Analysis categories."""
    DESIGN = "design"
    SEO = "seo"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    CONTENT = "content"
    SECURITY = "security"


class AnalysisStatus(str, Enum):
    """Analysis processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Schemas
class AnalysisRequest(BaseModel):
    """Request to analyze a website."""
    url: HttpUrl = Field(..., description="Website URL to analyze")
    depth: AnalysisDepth = Field(
        default=AnalysisDepth.COMPREHENSIVE,
        description="Analysis depth: quick or comprehensive"
    )
    include_screenshot: bool = Field(
        default=True,
        description="Whether to capture a screenshot"
    )
    ai_model: Optional[str] = Field(
        default=None,
        description="Specific AI model to use (defaults to GPT-4)"
    )
    store_html: bool = Field(
        default=False,
        description="Whether to store full HTML content"
    )

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid and accessible."""
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


# Response Schemas
class CategoryScore(BaseModel):
    """Score and analysis for a specific category."""
    score: float = Field(..., ge=0, le=100, description="Score from 0-100")
    summary: str = Field(..., description="Brief summary of findings")
    strengths: List[str] = Field(default_factory=list, description="What's working well")
    weaknesses: List[str] = Field(default_factory=list, description="What needs improvement")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed findings")


class ImprovementRecommendation(BaseModel):
    """A single improvement recommendation."""
    id: str = Field(..., description="Unique identifier for this recommendation")
    category: Category = Field(..., description="Category of improvement")
    priority: Priority = Field(..., description="Priority level")
    difficulty: Difficulty = Field(..., description="Implementation difficulty")
    title: str = Field(..., description="Short title of the improvement")
    description: str = Field(..., description="Detailed description")
    impact: str = Field(..., description="Expected impact of implementing this")
    code_example: Optional[str] = Field(None, description="Code example if applicable")
    estimated_time: Optional[str] = Field(None, description="Estimated implementation time")
    resources: List[str] = Field(default_factory=list, description="Helpful resources/links")


class TechnicalMetrics(BaseModel):
    """Technical performance metrics."""
    page_load_time_ms: Optional[int] = Field(None, description="Page load time in milliseconds")
    page_size_kb: Optional[int] = Field(None, description="Total page size in KB")
    num_requests: Optional[int] = Field(None, description="Number of HTTP requests")
    num_images: Optional[int] = Field(None, description="Number of images")
    num_scripts: Optional[int] = Field(None, description="Number of JavaScript files")
    num_stylesheets: Optional[int] = Field(None, description="Number of CSS files")
    word_count: Optional[int] = Field(None, description="Total word count")
    heading_count: Optional[int] = Field(None, description="Number of headings")
    link_count: Optional[int] = Field(None, description="Number of links")


class SEOMetrics(BaseModel):
    """SEO-specific metrics."""
    meta_title: Optional[str] = Field(None, description="Page meta title")
    meta_description: Optional[str] = Field(None, description="Page meta description")
    has_favicon: bool = Field(default=False, description="Has favicon")
    has_robots_txt: bool = Field(default=False, description="Has robots.txt")
    has_sitemap: bool = Field(default=False, description="Has sitemap.xml")
    is_mobile_friendly: bool = Field(default=False, description="Is mobile-friendly")
    has_ssl: bool = Field(default=False, description="Has SSL certificate")


class CostTracking(BaseModel):
    """Cost tracking information."""
    ai_cost: Optional[float] = Field(None, description="Cost of AI analysis in USD")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")


class ComprehensiveAnalysis(BaseModel):
    """Complete website analysis results."""
    id: int = Field(..., description="Analysis ID")
    url: str = Field(..., description="Analyzed URL")
    domain: Optional[str] = Field(None, description="Domain name")
    title: Optional[str] = Field(None, description="Page title")
    status: AnalysisStatus = Field(..., description="Analysis status")
    depth: AnalysisDepth = Field(..., description="Analysis depth")
    ai_model: Optional[str] = Field(None, description="AI model used")

    # Scores
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="Overall score")
    design: Optional[CategoryScore] = Field(None, description="Design analysis")
    seo: Optional[CategoryScore] = Field(None, description="SEO analysis")
    performance: Optional[CategoryScore] = Field(None, description="Performance analysis")
    accessibility: Optional[CategoryScore] = Field(None, description="Accessibility analysis")

    # Improvements
    improvements: List[ImprovementRecommendation] = Field(
        default_factory=list,
        description="Prioritized improvement recommendations"
    )

    # Metrics
    technical_metrics: Optional[TechnicalMetrics] = Field(None, description="Technical metrics")
    seo_metrics: Optional[SEOMetrics] = Field(None, description="SEO metrics")

    # Media
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")

    # Cost
    cost: Optional[CostTracking] = Field(None, description="Cost information")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        from_attributes = True


class AnalysisSummary(BaseModel):
    """Summary of a website analysis (for list views)."""
    id: int = Field(..., description="Analysis ID")
    url: str = Field(..., description="Analyzed URL")
    domain: Optional[str] = Field(None, description="Domain name")
    status: AnalysisStatus = Field(..., description="Analysis status")
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="Overall score")
    num_improvements: int = Field(default=0, description="Number of improvements found")
    screenshot_url: Optional[str] = Field(None, description="Screenshot URL")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""
    total: int = Field(..., description="Total number of analyses")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    analyses: List[AnalysisSummary] = Field(..., description="List of analyses")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Filter Schemas
class AnalysisFilters(BaseModel):
    """Filters for listing analyses."""
    domain: Optional[str] = Field(None, description="Filter by domain")
    min_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum overall score")
    max_score: Optional[float] = Field(None, ge=0, le=100, description="Maximum overall score")
    status: Optional[AnalysisStatus] = Field(None, description="Filter by status")
    depth: Optional[AnalysisDepth] = Field(None, description="Filter by depth")
    created_after: Optional[datetime] = Field(None, description="Created after this date")
    created_before: Optional[datetime] = Field(None, description="Created before this date")
