"""
Website Analysis API Endpoints.

Provides REST API for analyzing websites with AI-powered recommendations.
"""

import logging
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.website_analysis import WebsiteAnalysis, AnalysisStatus as ModelAnalysisStatus
from app.schemas.website_analysis import (
    AnalysisRequest,
    ComprehensiveAnalysis,
    AnalysisSummary,
    AnalysisListResponse,
    ErrorResponse,
    AnalysisStatus,
    AnalysisDepth,
    CategoryScore,
    ImprovementRecommendation,
    TechnicalMetrics,
    SEOMetrics,
    CostTracking,
)
from app.services.website_analyzer import get_website_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=ComprehensiveAnalysis,
    summary="Analyze a website",
    description="Run comprehensive AI-powered analysis on a website",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Analysis failed", "model": ErrorResponse},
    },
)
async def analyze_website(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> ComprehensiveAnalysis:
    """
    Analyze a website and generate AI-powered improvement recommendations.

    This endpoint:
    1. Fetches the website HTML and captures a screenshot
    2. Extracts technical metrics (load time, resource counts, etc.)
    3. Runs AI analysis for design, SEO, performance, and accessibility
    4. Generates prioritized improvement recommendations with code examples
    5. Calculates overall quality score

    The analysis is stored in the database and can be retrieved later.
    """
    try:
        logger.info(f"Starting analysis for {request.url}")

        analyzer = get_website_analyzer()

        # Run analysis
        analysis = await analyzer.analyze_website(
            url=str(request.url),
            db=db,
            depth=request.depth.value,
            include_screenshot=request.include_screenshot,
            ai_model=request.ai_model,
            store_html=request.store_html,
        )

        # Convert to response schema
        return _convert_to_response(analysis)

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AnalysisFailed",
                "message": str(e),
                "code": type(e).__name__,
            },
        )


@router.get(
    "/analysis/{analysis_id}",
    response_model=ComprehensiveAnalysis,
    summary="Get analysis by ID",
    description="Retrieve a previously run website analysis",
    responses={
        200: {"description": "Analysis found"},
        404: {"description": "Analysis not found", "model": ErrorResponse},
    },
)
async def get_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
) -> ComprehensiveAnalysis:
    """
    Retrieve a website analysis by ID.

    Returns the complete analysis including:
    - Overall and category scores
    - Detailed analysis for each category
    - Prioritized improvement recommendations
    - Technical and SEO metrics
    - Screenshot URL
    """
    # Query analysis
    result = await db.execute(
        select(WebsiteAnalysis).where(WebsiteAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NotFound",
                "message": f"Analysis {analysis_id} not found",
                "code": "ANALYSIS_NOT_FOUND",
            },
        )

    return _convert_to_response(analysis)


@router.get(
    "/analyses",
    response_model=AnalysisListResponse,
    summary="List all analyses",
    description="List all website analyses with pagination and filtering",
)
async def list_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum overall score"),
    max_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum overall score"),
    status: Optional[AnalysisStatus] = Query(None, description="Filter by status"),
    depth: Optional[AnalysisDepth] = Query(None, description="Filter by depth"),
    db: AsyncSession = Depends(get_db),
) -> AnalysisListResponse:
    """
    List all website analyses with pagination and filtering.

    Supports filtering by:
    - Domain
    - Score range
    - Status (pending, processing, completed, failed)
    - Analysis depth (quick, comprehensive)

    Returns paginated list of analysis summaries.
    """
    # Build query
    query = select(WebsiteAnalysis)

    # Apply filters
    filters = []
    if domain:
        filters.append(WebsiteAnalysis.domain.ilike(f"%{domain}%"))
    if min_score is not None:
        filters.append(WebsiteAnalysis.overall_score >= min_score)
    if max_score is not None:
        filters.append(WebsiteAnalysis.overall_score <= max_score)
    if status:
        filters.append(WebsiteAnalysis.status == status.value)
    if depth:
        filters.append(WebsiteAnalysis.depth == depth.value)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(WebsiteAnalysis)
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(WebsiteAnalysis.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    analyses = result.scalars().all()

    # Convert to summaries
    summaries = [_convert_to_summary(analysis) for analysis in analyses]

    return AnalysisListResponse(
        total=total,
        page=page,
        page_size=page_size,
        analyses=summaries,
    )


@router.get(
    "/analysis/{analysis_id}/screenshot",
    summary="Get screenshot",
    description="Retrieve the screenshot for a website analysis",
    responses={
        200: {"description": "Screenshot image"},
        404: {"description": "Screenshot not found"},
    },
)
async def get_screenshot(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    Retrieve the screenshot for a website analysis.

    Returns the screenshot image file (PNG format).
    """
    # Query analysis
    result = await db.execute(
        select(WebsiteAnalysis).where(WebsiteAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    if not analysis.screenshot_path:
        raise HTTPException(
            status_code=404,
            detail="Screenshot not available for this analysis",
        )

    screenshot_path = Path(analysis.screenshot_path)
    if not screenshot_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Screenshot file not found",
        )

    return FileResponse(
        screenshot_path,
        media_type="image/png",
        filename=f"analysis_{analysis_id}_screenshot.png",
    )


@router.delete(
    "/analysis/{analysis_id}",
    summary="Delete analysis",
    description="Delete a website analysis",
    responses={
        200: {"description": "Analysis deleted"},
        404: {"description": "Analysis not found"},
    },
)
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete a website analysis and its associated files.
    """
    # Query analysis
    result = await db.execute(
        select(WebsiteAnalysis).where(WebsiteAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    # Delete screenshot file if exists
    if analysis.screenshot_path:
        screenshot_path = Path(analysis.screenshot_path)
        if screenshot_path.exists():
            screenshot_path.unlink()

    # Delete from database
    await db.delete(analysis)
    await db.commit()

    return {
        "success": True,
        "message": f"Analysis {analysis_id} deleted successfully",
    }


@router.get(
    "/stats",
    summary="Get analysis statistics",
    description="Get overall statistics about website analyses",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get overall statistics about website analyses.

    Returns:
    - Total number of analyses
    - Average scores
    - Status distribution
    - Recent analyses
    """
    # Total count
    total_result = await db.execute(select(func.count()).select_from(WebsiteAnalysis))
    total = total_result.scalar()

    # Average scores
    avg_result = await db.execute(
        select(
            func.avg(WebsiteAnalysis.overall_score),
            func.avg(WebsiteAnalysis.design_score),
            func.avg(WebsiteAnalysis.seo_score),
            func.avg(WebsiteAnalysis.performance_score),
            func.avg(WebsiteAnalysis.accessibility_score),
        ).where(WebsiteAnalysis.status == ModelAnalysisStatus.COMPLETED)
    )
    avg_scores = avg_result.first()

    # Status distribution
    status_result = await db.execute(
        select(WebsiteAnalysis.status, func.count())
        .group_by(WebsiteAnalysis.status)
    )
    status_distribution = {row[0]: row[1] for row in status_result.all()}

    # Recent analyses
    recent_result = await db.execute(
        select(WebsiteAnalysis)
        .order_by(WebsiteAnalysis.created_at.desc())
        .limit(5)
    )
    recent_analyses = [_convert_to_summary(a) for a in recent_result.scalars().all()]

    return {
        "total_analyses": total,
        "average_scores": {
            "overall": round(avg_scores[0], 2) if avg_scores[0] else None,
            "design": round(avg_scores[1], 2) if avg_scores[1] else None,
            "seo": round(avg_scores[2], 2) if avg_scores[2] else None,
            "performance": round(avg_scores[3], 2) if avg_scores[3] else None,
            "accessibility": round(avg_scores[4], 2) if avg_scores[4] else None,
        },
        "status_distribution": status_distribution,
        "recent_analyses": recent_analyses,
    }


# Helper functions
def _convert_to_response(analysis: WebsiteAnalysis) -> ComprehensiveAnalysis:
    """Convert database model to API response schema."""
    return ComprehensiveAnalysis(
        id=analysis.id,
        url=analysis.url,
        domain=analysis.domain,
        title=analysis.title,
        status=AnalysisStatus(analysis.status),
        depth=AnalysisDepth(analysis.depth),
        ai_model=analysis.ai_model,
        overall_score=analysis.overall_score,
        design=CategoryScore(**analysis.design_analysis) if analysis.design_analysis else None,
        seo=CategoryScore(**analysis.seo_analysis) if analysis.seo_analysis else None,
        performance=CategoryScore(**analysis.performance_analysis) if analysis.performance_analysis else None,
        accessibility=CategoryScore(**analysis.accessibility_analysis) if analysis.accessibility_analysis else None,
        improvements=[
            ImprovementRecommendation(**imp) for imp in (analysis.improvements or [])
        ],
        technical_metrics=TechnicalMetrics(
            page_load_time_ms=analysis.page_load_time_ms,
            page_size_kb=analysis.page_size_kb,
            num_requests=analysis.num_requests,
            num_images=analysis.num_images,
            num_scripts=analysis.num_scripts,
            num_stylesheets=analysis.num_stylesheets,
            word_count=analysis.word_count,
            heading_count=analysis.heading_count,
            link_count=analysis.link_count,
        ),
        seo_metrics=SEOMetrics(
            meta_title=analysis.meta_title,
            meta_description=analysis.meta_description,
            has_favicon=analysis.has_favicon,
            has_robots_txt=analysis.has_robots_txt,
            has_sitemap=analysis.has_sitemap,
            is_mobile_friendly=analysis.is_mobile_friendly,
            has_ssl=analysis.has_ssl,
        ),
        screenshot_url=analysis.screenshot_url,
        cost=CostTracking(
            ai_cost=analysis.ai_cost,
            processing_time_seconds=analysis.processing_time_seconds,
        ),
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        completed_at=analysis.completed_at,
    )


def _convert_to_summary(analysis: WebsiteAnalysis) -> AnalysisSummary:
    """Convert database model to summary schema."""
    num_improvements = len(analysis.improvements) if analysis.improvements else 0

    return AnalysisSummary(
        id=analysis.id,
        url=analysis.url,
        domain=analysis.domain,
        status=AnalysisStatus(analysis.status),
        overall_score=analysis.overall_score,
        num_improvements=num_improvements,
        screenshot_url=analysis.screenshot_url,
        created_at=analysis.created_at,
    )
