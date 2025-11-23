"""
AI MVP API Endpoints - Expose AI-powered lead generation services.

Endpoints:
- POST /api/v1/ai-mvp/analyze-website - Analyze website with AI
- POST /api/v1/ai-mvp/generate-email - Generate personalized email
- POST /api/v1/ai-mvp/send-email - Send email via Postmark
- GET /api/v1/ai-mvp/stats - AI-GYM cost statistics
- GET /api/v1/ai-mvp/performance - Model performance comparison
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl, Field
import os

from app.core.database import get_db
from app.services.ai_mvp import (
    WebsiteAnalyzer,
    AICouncil,
    AICouncilConfig,
    AIGymTracker,
    EmailSender,
    EmailSenderConfig,
    analyze_website_quick
)
from app.services.improvement_planner import (
    ImprovementPlanner,
    ImprovementPlan,
    Improvement as ImprovementModel,
    ImprovementPlanSummary
)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeWebsiteRequest(BaseModel):
    """Request to analyze a website."""
    url: HttpUrl
    lead_id: Optional[int] = None
    lead_value: Optional[float] = Field(None, description="Estimated lead value in dollars")
    fetch_timeout: int = Field(30000, description="Fetch timeout in milliseconds")


class AnalyzeWebsiteResponse(BaseModel):
    """Website analysis response."""
    url: str
    title: str
    meta_description: str
    content_length: int
    ai_analysis: str
    ai_model: str
    ai_cost: float
    ai_request_id: Optional[int]
    lead_id: Optional[int]
    lead_value: Optional[float]


class GenerateEmailRequest(BaseModel):
    """Request to generate personalized email."""
    prospect_name: str = Field(..., description="Name of prospect")
    company_name: str = Field(..., description="Company name")
    website_analysis: str = Field(..., description="Website analysis from analyze-website endpoint")
    our_service_description: str = Field(..., description="Description of our service/product")
    lead_id: Optional[int] = None
    lead_value: Optional[float] = Field(None, description="Estimated lead value in dollars")


class GenerateEmailResponse(BaseModel):
    """Email generation response."""
    subject: str
    body: str
    ai_model: str
    ai_cost: float
    ai_request_id: Optional[int]
    lead_id: Optional[int]
    lead_value: Optional[float]


class SendEmailRequest(BaseModel):
    """Request to send email via Postmark."""
    to_email: str = Field(..., description="Recipient email address")
    subject: str
    html_body: str
    text_body: Optional[str] = None
    track_opens: bool = True
    track_links: bool = True
    tag: Optional[str] = None
    lead_id: Optional[int] = None


class SendEmailResponse(BaseModel):
    """Email send response."""
    success: bool
    message_id: Optional[str]
    status: str
    error: Optional[str] = None


class AIGymStatsResponse(BaseModel):
    """AI-GYM cost statistics."""
    request_count: int
    total_cost: float
    avg_cost: float
    total_tokens: int
    avg_duration_seconds: Optional[float]
    avg_quality_score: Optional[float]


class ModelPerformance(BaseModel):
    """Model performance metrics."""
    model_name: str
    task_type: str
    request_count: int
    avg_cost: float
    avg_duration_seconds: Optional[float]
    avg_quality_score: Optional[float]
    total_cost: float


class AIGymPerformanceResponse(BaseModel):
    """AI-GYM performance comparison."""
    models: List[ModelPerformance]
    total_models: int


class GenerateImprovementPlanRequest(BaseModel):
    """Request to generate website improvement plan."""
    url: HttpUrl = Field(..., description="Website URL (must already be analyzed)")
    analysis_result: dict = Field(..., description="Analysis result from analyze-website endpoint")
    industry: Optional[str] = Field(None, description="Business industry/niche for context")
    competitor_urls: Optional[List[str]] = Field(None, description="Competitor URLs for inspiration")
    focus_areas: Optional[List[str]] = Field(None, description="Areas to prioritize (e.g., ['conversion', 'performance'])")
    lead_value: Optional[float] = Field(None, description="Estimated lead value for AI routing")


class ImprovementResponse(BaseModel):
    """Single improvement recommendation."""
    id: str
    category: str
    priority: str
    title: str
    description: str
    current_state: str
    proposed_change: str
    impact: str
    difficulty: str
    time_estimate: str
    code_example: Optional[str] = None
    resources: List[str] = []
    dependencies: List[str] = []


class ImprovementPlanSummaryResponse(BaseModel):
    """Summary statistics for improvement plan."""
    total_improvements: int
    critical_priority: int = 0
    high_priority: int
    medium_priority: int
    low_priority: int
    estimated_total_impact: str
    estimated_total_time: str
    quick_wins: int
    categories: dict


class GenerateImprovementPlanResponse(BaseModel):
    """Complete improvement plan response."""
    url: str
    analyzed_at: str
    improvements: List[ImprovementResponse]
    summary: ImprovementPlanSummaryResponse
    analysis_metadata: dict


# ============================================================================
# Dependencies
# ============================================================================

async def get_ai_council(db: AsyncSession = Depends(get_db)) -> AICouncil:
    """Get AI Council instance with dependency injection."""
    # Validate API key exists
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured - OPENROUTER_API_KEY missing. Please set the environment variable."
        )

    gym_tracker = AIGymTracker(db)
    ai_config = AICouncilConfig(
        openrouter_api_key=api_key
    )
    council = AICouncil(ai_config, gym_tracker)
    try:
        yield council
    finally:
        await council.close()


def get_email_sender() -> EmailSender:
    """Get Email Sender instance."""
    # Validate Postmark token exists
    token = os.getenv("POSTMARK_SERVER_TOKEN")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured - POSTMARK_SERVER_TOKEN missing. Please set the environment variable."
        )

    config = EmailSenderConfig(
        postmark_server_token=token,
        from_email=os.getenv("POSTMARK_FROM_EMAIL", "sales@yourcompany.com"),
        from_name="Sales Team"
    )
    return EmailSender(config)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze-website", response_model=AnalyzeWebsiteResponse, status_code=status.HTTP_200_OK)
async def analyze_website(
    request: AnalyzeWebsiteRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Analyze a website with AI to extract business insights.

    **Cost**: $0.0003-0.012 depending on lead value and content size
    - Low-value leads ($0-25K): Cheap models (~$0.0003)
    - Mid-value leads ($25K-100K): Moderate models (~$0.005)
    - High-value leads ($100K+): Premium models (~$0.012)

    **Example**:
    ```json
    {
        "url": "https://example.com",
        "lead_value": 50000,
        "lead_id": 123
    }
    ```
    """
    try:
        # Analyze website
        result = await analyze_website_quick(
            url=str(request.url),
            ai_council=council,
            lead_value=request.lead_value
        )

        return AnalyzeWebsiteResponse(
            url=result["url"],
            title=result["title"],
            meta_description=result["meta_description"],
            content_length=result["content_length"],
            ai_analysis=result["ai_analysis"],
            ai_model=result["ai_model"],
            ai_cost=result["ai_cost"],
            ai_request_id=result["ai_request_id"],
            lead_id=request.lead_id,
            lead_value=request.lead_value
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Website analysis failed: {str(e)}"
        )


@router.post("/generate-email", response_model=GenerateEmailResponse, status_code=status.HTTP_200_OK)
async def generate_email(
    request: GenerateEmailRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Generate personalized email based on website analysis.

    **Cost**: $0.003-0.008 depending on lead value
    - Uses moderate creativity (temperature=0.8) for natural tone
    - Value-based model routing for cost optimization

    **Example**:
    ```json
    {
        "prospect_name": "John Doe",
        "company_name": "Example Corp",
        "website_analysis": "Company provides enterprise CRM...",
        "our_service_description": "AI-powered lead generation",
        "lead_value": 30000
    }
    ```
    """
    try:
        # Generate email
        response = await council.generate_email(
            prospect_name=request.prospect_name,
            company_name=request.company_name,
            website_analysis=request.website_analysis,
            our_service_description=request.our_service_description,
            lead_id=request.lead_id,
            lead_value=request.lead_value
        )

        # Parse subject and body
        content = response.content
        if "SUBJECT:" in content and "BODY:" in content:
            parts = content.split("BODY:", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip()
        else:
            # Fallback if format is different
            lines = content.split("\n", 1)
            subject = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else content

        return GenerateEmailResponse(
            subject=subject,
            body=body,
            ai_model=response.model_used,
            ai_cost=response.total_cost,
            ai_request_id=response.request_id,
            lead_id=request.lead_id,
            lead_value=request.lead_value
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {str(e)}"
        )


@router.post("/send-email", response_model=SendEmailResponse, status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest,
    sender: EmailSender = Depends(get_email_sender)
):
    """
    Send email via Postmark.

    **Cost**: Included in Postmark plan ($85/month for 125K emails)
    - Professional deliverability (99.99% uptime)
    - Open/click tracking available
    - Bounce/spam handling

    **Example**:
    ```json
    {
        "to_email": "prospect@example.com",
        "subject": "Quick question about your CRM",
        "html_body": "<p>Hi John...</p>",
        "track_opens": true,
        "tag": "ai-generated"
    }
    ```
    """
    try:
        result = await sender.send_email(
            to_email=request.to_email,
            subject=request.subject,
            html_body=request.html_body,
            text_body=request.text_body,
            track_opens=request.track_opens,
            track_links=request.track_links,
            tag=request.tag,
            metadata={"lead_id": str(request.lead_id)} if request.lead_id else None
        )

        return SendEmailResponse(
            success=result["success"],
            message_id=result.get("message_id"),
            status=result["status"],
            error=result.get("error")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email send failed: {str(e)}"
        )


@router.get("/stats", response_model=AIGymStatsResponse, status_code=status.HTTP_200_OK)
async def get_ai_gym_stats(
    db: AsyncSession = Depends(get_db),
    task_type: Optional[str] = None
):
    """
    Get AI-GYM cost statistics.

    **Query Parameters**:
    - `task_type`: Filter by specific task type (optional)

    **Returns**:
    - Total requests and cost
    - Average cost per request
    - Total tokens used
    - Average duration and quality scores

    **Example**: `GET /api/v1/ai-mvp/stats?task_type=website_analysis`
    """
    try:
        tracker = AIGymTracker(db)
        stats = await tracker.get_cost_summary(task_type=task_type)

        return AIGymStatsResponse(
            request_count=stats["request_count"],
            total_cost=stats["total_cost"],
            avg_cost=stats["avg_cost"],
            total_tokens=stats["total_tokens"],
            avg_duration_seconds=stats["avg_duration_seconds"],
            avg_quality_score=stats["avg_quality_score"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}"
        )


@router.get("/performance", response_model=AIGymPerformanceResponse, status_code=status.HTTP_200_OK)
async def get_model_performance(
    db: AsyncSession = Depends(get_db),
    task_type: Optional[str] = None,
    min_samples: int = 1
):
    """
    Get model performance comparison from AI-GYM.

    **Query Parameters**:
    - `task_type`: Filter by specific task type (optional)
    - `min_samples`: Minimum samples required for comparison (default: 1)

    **Returns**:
    - Performance metrics per model and task type
    - Average cost, duration, and quality scores
    - Total cost per model

    **Example**: `GET /api/v1/ai-mvp/performance?task_type=email_body&min_samples=5`
    """
    try:
        tracker = AIGymTracker(db)
        performance = await tracker.get_model_performance(
            task_type=task_type,
            min_samples=min_samples
        )

        models = [
            ModelPerformance(
                model_name=perf["model_name"],
                task_type=perf["task_type"],
                request_count=perf["request_count"],
                avg_cost=perf["avg_cost"],
                avg_duration_seconds=perf["avg_duration_seconds"],
                avg_quality_score=perf["avg_quality_score"],
                total_cost=perf["total_cost"]
            )
            for perf in performance
        ]

        return AIGymPerformanceResponse(
            models=models,
            total_models=len(models)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance: {str(e)}"
        )


@router.post("/generate-improvement-plan", response_model=GenerateImprovementPlanResponse, status_code=status.HTTP_200_OK)
async def generate_improvement_plan(
    request: GenerateImprovementPlanRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Generate a comprehensive, actionable improvement plan from website analysis.

    **Phase 3 Task 2: Improvement Plan Generator**

    Takes the output from `/analyze-website` and generates:
    - 8-12 prioritized improvements (critical/high/medium/low)
    - Specific actionable changes with code examples
    - Estimated impact and implementation difficulty
    - Time estimates for each improvement
    - Quick win identification (high impact + easy implementation)

    **Cost**: $0.003-0.015 depending on lead value
    - Uses AI to generate creative, context-aware recommendations
    - Includes rule-based improvements (free)
    - Deduplicates and prioritizes based on focus areas

    **Example Request**:
    ```json
    {
        "url": "https://example.com",
        "analysis_result": {
            "url": "https://example.com",
            "title": "Example Corp - Web Services",
            "ai_analysis": "...analysis from analyze-website...",
            "ai_model": "anthropic/claude-sonnet-4",
            "ai_cost": 0.012
        },
        "industry": "Web Development Services",
        "focus_areas": ["conversion", "performance"],
        "lead_value": 50000
    }
    ```

    **Response**: Complete improvement plan with:
    - Prioritized list of improvements
    - Summary statistics (total improvements, by priority, by category)
    - Quick wins count
    - Total time estimate
    - Estimated overall impact
    """
    try:
        # Initialize improvement planner
        planner = ImprovementPlanner(ai_council=council)

        # Generate plan
        plan = await planner.generate_plan(
            analysis_result=request.analysis_result,
            industry=request.industry,
            competitor_urls=request.competitor_urls,
            focus_areas=request.focus_areas,
            lead_value=request.lead_value
        )

        # Convert to response format
        improvements = [
            ImprovementResponse(
                id=imp.id,
                category=imp.category.value,
                priority=imp.priority.value,
                title=imp.title,
                description=imp.description,
                current_state=imp.current_state,
                proposed_change=imp.proposed_change,
                impact=imp.impact,
                difficulty=imp.difficulty.value,
                time_estimate=imp.time_estimate,
                code_example=imp.code_example,
                resources=imp.resources,
                dependencies=imp.dependencies
            )
            for imp in plan.improvements
        ]

        summary = ImprovementPlanSummaryResponse(
            total_improvements=plan.summary.total_improvements,
            critical_priority=plan.summary.critical_priority,
            high_priority=plan.summary.high_priority,
            medium_priority=plan.summary.medium_priority,
            low_priority=plan.summary.low_priority,
            estimated_total_impact=plan.summary.estimated_total_impact,
            estimated_total_time=plan.summary.estimated_total_time,
            quick_wins=plan.summary.quick_wins,
            categories=plan.summary.categories
        )

        return GenerateImprovementPlanResponse(
            url=plan.url,
            analyzed_at=plan.analyzed_at,
            improvements=improvements,
            summary=summary,
            analysis_metadata=plan.analysis_metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Improvement plan generation failed: {str(e)}"
        )


# ============================================================================
# Phase 3: Enhanced Website Analysis Models
# ============================================================================

class AnalyzeDesignRequest(BaseModel):
    """Request to analyze website design quality."""
    url: HttpUrl
    use_ai: bool = Field(False, description="Use AI for subjective design assessment (costs tokens)")


class DesignAnalysisResponse(BaseModel):
    """Design analysis response."""
    score: int
    issues: List[str]
    strengths: List[str]
    metrics: dict
    ai_assessment: Optional[str] = None


class AnalyzeSEORequest(BaseModel):
    """Request to analyze website SEO."""
    url: HttpUrl


class SEOAnalysisResponse(BaseModel):
    """SEO analysis response."""
    score: int
    issues: List[str]
    strengths: List[str]
    details: dict


class AnalyzePerformanceRequest(BaseModel):
    """Request to analyze website performance."""
    url: HttpUrl


class PerformanceAnalysisResponse(BaseModel):
    """Performance analysis response."""
    score: int
    issues: List[str]
    strengths: List[str]
    metrics: dict


class AnalyzeAccessibilityRequest(BaseModel):
    """Request to analyze website accessibility."""
    url: HttpUrl


class AccessibilityAnalysisResponse(BaseModel):
    """Accessibility analysis response."""
    score: int
    issues: List[str]
    strengths: List[str]
    details: dict


class ComprehensiveAnalysisRequest(BaseModel):
    """Request for comprehensive website analysis."""
    url: HttpUrl
    include_ai_design: bool = Field(False, description="Include AI-powered design assessment")


class ComprehensiveAnalysisResponse(BaseModel):
    """Comprehensive analysis response with all metrics."""
    url: str
    overall_score: float
    design: DesignAnalysisResponse
    seo: SEOAnalysisResponse
    performance: PerformanceAnalysisResponse
    accessibility: AccessibilityAnalysisResponse
    title: str
    meta_description: str


# ============================================================================
# Phase 3: Enhanced Website Analysis Endpoints
# ============================================================================

@router.post("/analyze-design", response_model=DesignAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_design(
    request: AnalyzeDesignRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Analyze website design quality.

    **Analyzes**:
    - Layout type (grid, flexbox, float)
    - Color scheme consistency
    - Typography usage
    - Visual hierarchy
    - Whitespace utilization
    - Mobile responsiveness

    **Optional AI Assessment** (use_ai=true):
    - Subjective design quality evaluation
    - Professional appearance rating
    - Modern vs. dated assessment
    - Costs ~$0.002-0.005 in tokens

    **Example**:
    ```json
    {
        "url": "https://example.com",
        "use_ai": false
    }
    ```
    """
    try:
        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_design_quality(
                url=str(request.url),
                use_ai=request.use_ai
            )

            return DesignAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Design analysis failed: {str(e)}"
        )


@router.post("/analyze-seo", response_model=SEOAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_seo(
    request: AnalyzeSEORequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Comprehensive SEO audit.

    **Analyzes**:
    - Meta tags (title, description, keywords)
    - Heading structure (H1-H6)
    - Image alt text coverage
    - Internal/external links
    - Mobile-friendliness
    - Schema markup
    - Open Graph tags
    - Canonical URLs

    **Scoring**: 0-100 based on SEO best practices
    - Title: 20 points
    - Meta description: 20 points
    - H1 usage: 15 points
    - Image alt tags: 15 points
    - Mobile-friendly: 10 points
    - Schema markup: 10 points
    - Open Graph: 5 points
    - Canonical URL: 5 points

    **Example**:
    ```json
    {
        "url": "https://example.com"
    }
    ```
    """
    try:
        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_seo(url=str(request.url))

            return SEOAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SEO analysis failed: {str(e)}"
        )


@router.post("/analyze-performance", response_model=PerformanceAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_performance(
    request: AnalyzePerformanceRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Analyze website performance metrics.

    **Measures**:
    - Page load times (DOM content loaded, full load)
    - Resource sizes (total MB, individual resources)
    - Script/stylesheet counts
    - Image optimization status
    - Render-blocking resources

    **Scoring**: 0-100 based on performance benchmarks
    - Load time: 30 points (fast < 3s, moderate < 5s)
    - Resource size: 20 points (optimized < 3MB, moderate < 5MB)
    - Script count: 15 points (good < 10, moderate < 20)
    - Stylesheet count: 10 points (good < 5, moderate < 10)
    - Image optimization: 15 points
    - Render-blocking: 10 points

    **Note**: This endpoint performs real page loads, so it may take 10-30 seconds.

    **Example**:
    ```json
    {
        "url": "https://example.com"
    }
    ```
    """
    try:
        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_performance(url=str(request.url))

            return PerformanceAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance analysis failed: {str(e)}"
        )


@router.post("/analyze-accessibility", response_model=AccessibilityAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_accessibility(
    request: AnalyzeAccessibilityRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Analyze website accessibility (WCAG compliance).

    **Checks**:
    - ARIA labels and roles
    - Semantic HTML usage (header, nav, main, article, etc.)
    - Form input labels
    - Image alt text
    - Link descriptive text
    - Language attribute
    - Skip navigation links
    - Keyboard navigation support

    **Scoring**: 0-100 based on accessibility standards
    - ARIA usage: 20 points
    - Semantic HTML: 15 points
    - Form labels: 20 points
    - Image alt text: 20 points
    - Link text: 10 points
    - Lang attribute: 5 points
    - Skip links: 5 points
    - Keyboard nav: 5 points

    **Example**:
    ```json
    {
        "url": "https://example.com"
    }
    ```
    """
    try:
        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_accessibility(url=str(request.url))

            return AccessibilityAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Accessibility analysis failed: {str(e)}"
        )


@router.post("/analyze-comprehensive", response_model=ComprehensiveAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_comprehensive(
    request: ComprehensiveAnalysisRequest,
    council: AICouncil = Depends(get_ai_council)
):
    """
    Perform comprehensive website analysis with ALL metrics.

    **Includes**:
    - Design quality (25% weight)
    - SEO audit (30% weight)
    - Performance metrics (25% weight)
    - Accessibility compliance (20% weight)

    **Overall Score**: Weighted average of all categories (0-100)

    **Optional AI Design Assessment** (include_ai_design=true):
    - Adds subjective design evaluation
    - Costs ~$0.002-0.005 in tokens

    **Note**: This is the MOST comprehensive analysis endpoint.
    - Takes 15-45 seconds to complete
    - Performs real page loads for performance testing
    - Returns detailed metrics for each category
    - Provides actionable issues and strengths

    **Use Case**: Perfect for generating detailed website audit reports.

    **Example**:
    ```json
    {
        "url": "https://example.com",
        "include_ai_design": false
    }
    ```

    **Response Format**:
    ```json
    {
        "url": "https://example.com",
        "overall_score": 72.5,
        "design": {
            "score": 75,
            "issues": ["Poor color contrast on CTA"],
            "strengths": ["Good typography", "Clean layout"],
            "metrics": {...}
        },
        "seo": {
            "score": 85,
            "issues": ["Missing meta description"],
            "strengths": ["Good image alt texts"],
            "details": {...}
        },
        "performance": {
            "score": 60,
            "issues": ["Slow page load (4.2s)"],
            "strengths": ["Optimized page size (2.1MB)"],
            "metrics": {...}
        },
        "accessibility": {
            "score": 70,
            "issues": ["Some form inputs lack labels"],
            "strengths": ["Uses semantic HTML"],
            "details": {...}
        },
        "title": "Example Corp - Web Services",
        "meta_description": "We provide..."
    }
    ```
    """
    try:
        async with WebsiteAnalyzer(council) as analyzer:
            result = await analyzer.analyze_website_comprehensive(
                url=str(request.url),
                include_ai_design=request.include_ai_design
            )

            return ComprehensiveAnalysisResponse(
                url=result["url"],
                overall_score=result["overall_score"],
                design=DesignAnalysisResponse(**result["design"]),
                seo=SEOAnalysisResponse(**result["seo"]),
                performance=PerformanceAnalysisResponse(**result["performance"]),
                accessibility=AccessibilityAnalysisResponse(**result["accessibility"]),
                title=result["title"],
                meta_description=result["meta_description"]
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comprehensive analysis failed: {str(e)}"
        )
