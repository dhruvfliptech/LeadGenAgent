"""
API endpoints for AI-Powered Demo Site Builder.

Comprehensive endpoints for:
- Demo site generation with AI
- Template management
- Component library
- Analytics tracking
- Vercel deployment
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date
import logging

# Database and models
from app.core.database import get_db
from app.core.rate_limiter import (
    demo_sites_read_limiter,
    demo_sites_write_limiter,
    demo_sites_generate_limiter,
    demo_sites_deploy_limiter,
    demo_sites_track_limiter
)
from app.models.demo_sites import (
    DemoSite, DemoSiteTemplate, DemoSiteAnalytics,
    DemoSiteComponent, DeploymentHistory
)
from app.models.leads import Lead

# Services
from app.services.demo_builder import (
    SiteGenerator, TemplateEngine, VercelDeployer,
    AnalyticsTracker, ContentPersonalizer
)

# Schemas
from app.schemas.demo_sites import *

# Legacy integration (if exists)
try:
    from app.integrations.vercel_deployer import VercelDeployer as LegacyVercelDeployer
except ImportError:
    LegacyVercelDeployer = None

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# DEMO SITE GENERATION ENDPOINTS (AI-Powered)
# ============================================================================

@router.post("/generate", response_model=DemoSiteResponse, status_code=201)
@demo_sites_generate_limiter
async def generate_demo_site(
    request: Request,
    generate_generate_request: DemoSiteGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new demo site using AI.

    This endpoint creates a personalized demo site using:
    - AI content generation (GPT-4, Claude, etc.)
    - Template rendering
    - Style customization
    - Optional auto-deployment to Vercel

    The site is generated based on lead data and can be automatically
    deployed or saved as draft for review.
    """
    try:
        # Verify lead if provided
        lead = None
        if generate_request.lead_id:
            result = await db.execute(select(Lead).where(Lead.id == generate_request.lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                raise HTTPException(status_code=404, detail=f"Lead {generate_request.lead_id} not found")

        # Get template if specified
        template = None
        if generate_request.template_id:
            result = await db.execute(
                select(DemoSiteTemplate).where(DemoSiteTemplate.id == generate_request.template_id)
            )
            template = result.scalar_one_or_none()
            if not template:
                raise HTTPException(status_code=404, detail=f"Template {generate_request.template_id} not found")
        else:
            # Get default template for this type
            result = await db.execute(
                select(DemoSiteTemplate).where(
                    and_(
                        DemoSiteTemplate.template_type == generate_request.template_type,
                        DemoSiteTemplate.is_active == True
                    )
                ).order_by(DemoSiteTemplate.is_default.desc())
            )
            template = result.scalars().first()

        # Initialize services
        site_generator = SiteGenerator()
        template_engine = TemplateEngine()
        personalizer = ContentPersonalizer()

        # Personalize content with AI
        if generate_request.use_ai_generation and lead:
            content_data_dict = await personalizer.personalize_content(
                lead=lead,
                template_type=generate_request.template_type,
                base_content=generate_request.content_data.dict(),
                ai_model=generate_request.ai_model
            )
            # Merge with request content
            content_data_dict = {**content_data_dict, **generate_request.content_data.dict(exclude_unset=True)}
        else:
            content_data_dict = generate_request.content_data.dict()

        # Generate site code
        if template:
            generated = await site_generator.generate_site(
                template=template,
                content_data=content_data_dict,
                style_settings=generate_request.style_settings.dict(),
                ai_model=generate_request.ai_model,
                use_ai=generate_request.use_ai_generation
            )
        else:
            # Generate from scratch if no template
            generated = await site_generator.generate_from_scratch(
                content_data=content_data_dict,
                style_settings=generate_request.style_settings.dict(),
                template_type=generate_request.template_type,
                ai_model=generate_request.ai_model
            )

        # Validate generated code
        if not site_generator.validate_generated_code(generated):
            raise HTTPException(status_code=400, detail="Generated code failed validation")

        # Inject analytics tracking
        if generate_request.auto_deploy:
            demo_site_id = 0  # Will be set after creation
            generated['html'] = template_engine.inject_analytics(
                html=generated['html'],
                demo_site_id=demo_site_id,
                analytics_endpoint="/api/v1/demo-sites"
            )

        # Optimize for mobile
        optimized = template_engine.optimize_for_mobile(generated['html'], generated['css'])
        generated.update(optimized)

        # Create demo site record
        subdomain = generate_request.custom_subdomain or f"{generate_request.site_name.lower().replace(' ', '-')}-{datetime.utcnow().timestamp():.0f}"

        demo_site = DemoSite(
            lead_id=generate_request.lead_id,
            template_id=template.id if template else None,
            site_name=generate_request.site_name,
            project_name=subdomain,  # Using subdomain as project_name
            framework="html",
            content_data=content_data_dict,
            style_settings=generate_request.style_settings.dict(),
            generated_html=generated['html'],
            generated_css=generated['css'],
            generated_js=generated.get('js'),
            status="draft",
            analytics_enabled=True,
            is_active=True
        )

        db.add(demo_site)
        await db.commit()
        await db.refresh(demo_site)

        # Update analytics injection with real ID
        demo_site.generated_html = template_engine.inject_analytics(
            html=generated['html'],
            demo_site_id=demo_site.id,
            analytics_endpoint="/api/v1/demo-sites"
        )
        await db.commit()

        # Auto-deploy if requested
        if generate_request.auto_deploy:
            background_tasks.add_task(
                _deploy_demo_site_bg,
                demo_site.id,
                db
            )
            demo_site.status = "building"
            await db.commit()

        return DemoSiteResponse.from_orm(demo_site)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Demo site generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/", response_model=DemoSiteListResponse)
@demo_sites_read_limiter
async def list_demo_sites(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    template_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all demo sites with filtering and pagination."""
    try:
        query = select(DemoSite).where(DemoSite.is_active == True)

        # Apply filters
        if status:
            query = query.where(DemoSite.status == status)
        if lead_id:
            query = query.where(DemoSite.lead_id == lead_id)
        if template_type:
            query = query.join(DemoSiteTemplate).where(
                DemoSiteTemplate.template_type == template_type
            )

        # Count total
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()

        # Paginate
        query = query.order_by(desc(DemoSite.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        demo_sites = result.scalars().all()

        return DemoSiteListResponse(
            total=total,
            page=page,
            page_size=page_size,
            demo_sites=[DemoSiteResponse.from_orm(site) for site in demo_sites]
        )

    except Exception as e:
        logger.error(f"List demo sites failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{demo_site_id}", response_model=DemoSiteResponse)
@demo_sites_read_limiter
async def get_demo_site(
    request: Request,
    demo_site_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get demo site details by ID."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        return DemoSiteResponse.from_orm(demo_site)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{demo_site_id}", response_model=DemoSiteResponse)
@demo_sites_write_limiter
async def update_demo_site(
    request: Request,
    demo_site_id: int,
    update_request: DemoSiteUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update demo site configuration."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        # Update fields
        if update_request.site_name:
            demo_site.site_name = update_request.site_name
        if update_request.template_id is not None:
            demo_site.template_id = update_request.template_id
        if update_request.content_data:
            demo_site.content_data = {**demo_site.content_data, **update_request.content_data.dict()}
        if update_request.style_settings:
            demo_site.style_settings = {**demo_site.style_settings, **update_request.style_settings.dict()}
        if update_request.custom_domain:
            demo_site.custom_domain = update_request.custom_domain
        if update_request.analytics_enabled is not None:
            demo_site.analytics_enabled = update_request.analytics_enabled
        if update_request.is_active is not None:
            demo_site.is_active = update_request.is_active

        demo_site.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(demo_site)

        return DemoSiteResponse.from_orm(demo_site)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{demo_site_id}")
@demo_sites_write_limiter
async def delete_demo_site(
    request: Request,
    demo_site_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a demo site (soft delete)."""
    try:
        result = await db.execute(
            select(DemoSite).where(DemoSite.id == demo_site_id)
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        demo_site.is_active = False
        demo_site.updated_at = datetime.utcnow()
        await db.commit()

        return {"message": "Demo site deleted successfully", "id": demo_site_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{demo_site_id}/deploy", response_model=DeploymentStatusResponse)
@demo_sites_deploy_limiter
async def deploy_demo_site(
    request: Request,
    demo_site_id: int,
    deploy_request: DemoSiteDeployRequest = Body(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """Deploy demo site to Vercel."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        if not demo_site.generated_html:
            raise HTTPException(status_code=400, detail="Demo site not generated yet")

        # Start deployment in background
        demo_site.status = "building"
        await db.commit()

        if background_tasks:
            background_tasks.add_task(_deploy_demo_site_bg, demo_site_id, db)

        return DeploymentStatusResponse(
            demo_site_id=demo_site.id,
            deployment_status="building",
            progress=10,
            message="Deployment started",
            last_updated=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{demo_site_id}/preview", response_model=DemoSitePreviewResponse)
@demo_sites_read_limiter
async def preview_demo_site(
    request: Request,
    demo_site_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get preview of demo site (HTML/CSS/JS)."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        if not demo_site.generated_html:
            raise HTTPException(status_code=400, detail="Demo site not generated yet")

        # Generate complete preview HTML
        template_engine = TemplateEngine()
        preview_html = template_engine.generate_preview(
            html=demo_site.generated_html,
            css=demo_site.generated_css or "",
            js=demo_site.generated_js
        )

        return DemoSitePreviewResponse(
            html=demo_site.generated_html,
            css=demo_site.generated_css or "",
            js=demo_site.generated_js,
            preview_url=demo_site.vercel_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{demo_site_id}/duplicate", response_model=DemoSiteResponse)
@demo_sites_write_limiter
async def duplicate_demo_site(
    request: Request,
    demo_site_id: int,
    duplicate_request: DemoSiteDuplicateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing demo site."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        original = result.scalar_one_or_none()

        if not original:
            raise HTTPException(status_code=404, detail="Demo site not found")

        # Create duplicate
        duplicate = DemoSite(
            lead_id=duplicate_request.new_lead_id or original.lead_id,
            template_id=original.template_id,
            site_name=duplicate_request.new_site_name,
            project_name=f"{duplicate_request.new_site_name.lower().replace(' ', '-')}-{datetime.utcnow().timestamp():.0f}",
            framework=original.framework,
            content_data=original.content_data if duplicate_request.copy_content else {},
            style_settings=original.style_settings if duplicate_request.copy_style else {},
            generated_html=original.generated_html if duplicate_request.copy_content else None,
            generated_css=original.generated_css if duplicate_request.copy_style else None,
            generated_js=original.generated_js if duplicate_request.copy_content else None,
            status="draft",
            analytics_enabled=original.analytics_enabled,
            is_active=True
        )

        db.add(duplicate)
        await db.commit()
        await db.refresh(duplicate)

        return DemoSiteResponse.from_orm(duplicate)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Duplicate demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{demo_site_id}/export", response_model=DemoSiteExportResponse)
@demo_sites_read_limiter
async def export_demo_site(
    request: Request,
    demo_site_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Export demo site files."""
    try:
        result = await db.execute(
            select(DemoSite).where(
                and_(DemoSite.id == demo_site_id, DemoSite.is_active == True)
            )
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        files = []

        if demo_site.generated_html:
            files.append({
                "filename": "index.html",
                "content": demo_site.generated_html
            })

        if demo_site.generated_css:
            files.append({
                "filename": "styles.css",
                "content": demo_site.generated_css
            })

        if demo_site.generated_js:
            files.append({
                "filename": "script.js",
                "content": demo_site.generated_js
            })

        return DemoSiteExportResponse(files=files)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export demo site failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEMPLATE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/templates", response_model=DemoSiteTemplateListResponse, tags=["templates"])
@demo_sites_read_limiter
async def list_templates(
    request: Request,
    template_type: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List all available templates."""
    try:
        query = select(DemoSiteTemplate).where(DemoSiteTemplate.is_active == is_active)

        if template_type:
            query = query.where(DemoSiteTemplate.template_type == template_type)

        query = query.order_by(DemoSiteTemplate.is_default.desc(), DemoSiteTemplate.usage_count.desc())

        result = await db.execute(query)
        templates = result.scalars().all()

        return DemoSiteTemplateListResponse(
            total=len(templates),
            templates=[DemoSiteTemplateResponse.from_orm(t) for t in templates]
        )

    except Exception as e:
        logger.error(f"List templates failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=DemoSiteTemplateResponse, tags=["templates"])
@demo_sites_read_limiter
async def get_template(
    request: Request,
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get template details."""
    try:
        result = await db.execute(
            select(DemoSiteTemplate).where(DemoSiteTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return DemoSiteTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get template failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates", response_model=DemoSiteTemplateResponse, status_code=201, tags=["templates"])
@demo_sites_write_limiter
async def create_template(
    request: Request,
    template_request: DemoSiteTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new template."""
    try:
        # Validate and sanitize template code
        template_engine = TemplateEngine()
        is_valid, error = template_engine.validate_template(template_request.html_template)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid template: {error}")

        # Sanitize template content before storing
        from app.core.template_security import TemplateSanitizer
        sanitizer = TemplateSanitizer()

        html_template = sanitizer.sanitize_html(template_request.html_template, strip_tags=False)
        css_template = sanitizer.sanitize_css(template_request.css_template) if template_request.css_template else None
        js_template = sanitizer.sanitize_javascript(template_request.js_template) if template_request.js_template else None

        template = DemoSiteTemplate(
            template_name=template_request.template_name,
            template_type=template_request.template_type,
            description=template_request.description,
            html_template=html_template,  # Use sanitized version
            css_template=css_template,     # Use sanitized version
            js_template=js_template,       # Use sanitized version
            preview_image_url=template_request.preview_image_url,
            thumbnail_url=template_request.thumbnail_url,
            customization_options=template_request.customization_options,
            default_meta_title=template_request.default_meta_title,
            default_meta_description=template_request.default_meta_description,
            default_meta_keywords=template_request.default_meta_keywords,
            is_active=template_request.is_active,
            is_default=template_request.is_default
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        return DemoSiteTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create template failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/templates/{template_id}", response_model=DemoSiteTemplateResponse, tags=["templates"])
@demo_sites_write_limiter
async def update_template(
    request: Request,
    template_id: int,
    template_update: DemoSiteTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a template."""
    try:
        result = await db.execute(
            select(DemoSiteTemplate).where(DemoSiteTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Update fields
        update_data = template_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(template)

        return DemoSiteTemplateResponse.from_orm(template)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update template failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}", tags=["templates"])
@demo_sites_write_limiter
async def delete_template(
    request: Request,
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a template."""
    try:
        result = await db.execute(
            select(DemoSiteTemplate).where(DemoSiteTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        template.is_active = False
        await db.commit()

        return {"message": "Template deleted successfully", "id": template_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete template failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/{demo_site_id}/analytics/summary", response_model=DemoSiteAnalyticsSummaryResponse, tags=["analytics"])
@demo_sites_read_limiter
async def get_analytics_summary(
    request: Request,
    demo_site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics summary for a demo site."""
    try:
        # Verify demo site exists
        result = await db.execute(
            select(DemoSite).where(DemoSite.id == demo_site_id)
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        # Get analytics
        tracker = AnalyticsTracker(db)
        summary = await tracker.get_analytics_summary(
            demo_site_id=demo_site_id,
            start_date=date.today() - timedelta(days=days),
            end_date=date.today()
        )

        return DemoSiteAnalyticsSummaryResponse(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{demo_site_id}/analytics/timeline", response_model=DemoSiteAnalyticsTimelineResponse, tags=["analytics"])
@demo_sites_read_limiter
async def get_analytics_timeline(
    request: Request,
    demo_site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics timeline for a demo site."""
    try:
        result = await db.execute(
            select(DemoSite).where(DemoSite.id == demo_site_id)
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            raise HTTPException(status_code=404, detail="Demo site not found")

        tracker = AnalyticsTracker(db)
        timeline = await tracker.get_analytics_timeline(
            demo_site_id=demo_site_id,
            days=days
        )

        return DemoSiteAnalyticsTimelineResponse(
            demo_site_id=demo_site_id,
            timeline=[DemoSiteAnalyticsResponse(**t) for t in timeline],
            date_range={
                "start": date.today() - timedelta(days=days),
                "end": date.today()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analytics timeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{demo_site_id}/analytics/track", tags=["analytics"])
@demo_sites_track_limiter
async def track_analytics_event(
    request: Request,
    demo_site_id: int,
    track_request: DemoSiteAnalyticsTrackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Track an analytics event (public endpoint for demo sites)."""
    try:
        tracker = AnalyticsTracker(db)
        success = await tracker.track_event(
            demo_site_id=demo_site_id,
            event_type=track_request.event_type,
            visitor_id=track_request.visitor_id or "anonymous",
            event_data=track_request.event_data
        )

        if success:
            return {"message": "Event tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track event")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Track analytics event failed: {str(e)}")
        # Don't fail on analytics errors
        return {"message": "Event tracking failed", "error": str(e)}


# ============================================================================
# COMPONENT LIBRARY ENDPOINTS
# ============================================================================

@router.get("/components", response_model=DemoSiteComponentListResponse, tags=["components"])
@demo_sites_read_limiter
async def list_components(
    request: Request,
    component_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """List all available components."""
    try:
        query = select(DemoSiteComponent).where(DemoSiteComponent.is_active == is_active)

        if component_type:
            query = query.where(DemoSiteComponent.component_type == component_type)
        if category:
            query = query.where(DemoSiteComponent.category == category)

        query = query.order_by(DemoSiteComponent.usage_count.desc())

        result = await db.execute(query)
        components = result.scalars().all()

        return DemoSiteComponentListResponse(
            total=len(components),
            components=[DemoSiteComponentResponse.from_orm(c) for c in components]
        )

    except Exception as e:
        logger.error(f"List components failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components/{component_id}", response_model=DemoSiteComponentResponse, tags=["components"])
@demo_sites_read_limiter
async def get_component(
    request: Request,
    component_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get component details."""
    try:
        result = await db.execute(
            select(DemoSiteComponent).where(DemoSiteComponent.id == component_id)
        )
        component = result.scalar_one_or_none()

        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        return DemoSiteComponentResponse.from_orm(component)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get component failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components", response_model=DemoSiteComponentResponse, status_code=201, tags=["components"])
@demo_sites_write_limiter
async def create_component(
    request: Request,
    component_request: DemoSiteComponentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new component."""
    try:
        component = DemoSiteComponent(
            component_name=component_request.component_name,
            component_type=component_request.component_type,
            description=component_request.description,
            html_code=component_request.html_code,
            css_code=component_request.css_code,
            js_code=component_request.js_code,
            preview_image=component_request.preview_image,
            preview_html=component_request.preview_html,
            category=component_request.category,
            tags=component_request.tags,
            required_data_fields=component_request.required_data_fields,
            optional_data_fields=component_request.optional_data_fields,
            is_active=component_request.is_active
        )

        db.add(component)
        await db.commit()
        await db.refresh(component)

        return DemoSiteComponentResponse.from_orm(component)

    except Exception as e:
        logger.error(f"Create component failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/components/{component_id}", response_model=DemoSiteComponentResponse, tags=["components"])
@demo_sites_write_limiter
async def update_component(
    request: Request,
    component_id: int,
    component_update: DemoSiteComponentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a component."""
    try:
        result = await db.execute(
            select(DemoSiteComponent).where(DemoSiteComponent.id == component_id)
        )
        component = result.scalar_one_or_none()

        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        update_data = component_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)

        component.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(component)

        return DemoSiteComponentResponse.from_orm(component)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update component failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKGROUND TASKS AND HELPERS
# ============================================================================

async def _deploy_demo_site_bg(demo_site_id: int, db: AsyncSession):
    """Background task to deploy demo site to Vercel."""
    try:
        result = await db.execute(
            select(DemoSite).where(DemoSite.id == demo_site_id)
        )
        demo_site = result.scalar_one_or_none()

        if not demo_site:
            return

        deployer = VercelDeployer()

        deployment = await deployer.deploy_site(
            site_name=demo_site.project_name,
            html=demo_site.generated_html,
            css=demo_site.generated_css or "",
            js=demo_site.generated_js
        )

        # Update demo site with deployment info
        demo_site.vercel_deployment_id = deployment['deployment_id']
        demo_site.vercel_project_id = deployment['vercel_project_id']
        demo_site.url = deployment['url']
        demo_site.vercel_url = deployment['preview_url']
        demo_site.status = deployment['status']
        demo_site.deployed_at = datetime.utcnow()
        demo_site.last_deployed_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Demo site {demo_site_id} deployed successfully to {deployment['preview_url']}")

    except Exception as e:
        logger.error(f"Background deployment failed for demo site {demo_site_id}: {str(e)}")

        # Update status to failed
        try:
            result = await db.execute(
                select(DemoSite).where(DemoSite.id == demo_site_id)
            )
            demo_site = result.scalar_one_or_none()
            if demo_site:
                demo_site.status = "failed"
                demo_site.error_message = str(e)
                await db.commit()
        except:
            pass


# Keep existing legacy endpoints below for backward compatibility
# ============================================================================
# LEGACY DEPLOYMENT ENDPOINTS (Backward Compatibility)
# ============================================================================

# Pydantic schemas for request/response validation
from pydantic import BaseModel, Field


class DeploymentRequest(BaseModel):
    """Request model for deploying a demo site."""
    lead_id: int = Field(..., description="Lead ID to deploy demo site for")
    framework: str = Field(..., description="Framework type (html, react, nextjs, vue, svelte)")
    files: Dict[str, str] = Field(..., description="Dictionary of file paths to contents")
    project_name: Optional[str] = Field(None, description="Custom project name (auto-generated if not provided)")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    custom_domain: Optional[str] = Field(None, description="Custom domain (optional)")


class RedeploymentRequest(BaseModel):
    """Request model for redeploying an existing demo site."""
    force: bool = Field(False, description="Force redeployment even if no changes")


class DeploymentResponse(BaseModel):
    """Response model for deployment operations."""
    id: int
    lead_id: int
    vercel_project_id: Optional[str]
    vercel_deployment_id: Optional[str]
    project_name: str
    framework: str
    url: Optional[str]
    preview_url: Optional[str]
    status: str
    build_time: Optional[float]
    created_at: str
    deployed_at: Optional[str]
    error_message: Optional[str] = None


class DeploymentListResponse(BaseModel):
    """Response model for listing deployments."""
    total: int
    deployments: List[DeploymentResponse]
    page: int
    page_size: int


class DeploymentStatsResponse(BaseModel):
    """Response model for deployment statistics."""
    total_deployments: int
    active_deployments: int
    failed_deployments: int
    total_page_views: int
    total_bandwidth_gb: float
    estimated_monthly_cost: float
    deployments_by_status: Dict[str, int]
    deployments_by_framework: Dict[str, int]


async def _generate_project_name(lead_id: int, framework: str) -> str:
    """Generate a unique project name for a demo site."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"demo-{framework}-lead-{lead_id}-{timestamp}"


async def _save_deployment(
    db: AsyncSession,
    lead_id: int,
    project_name: str,
    framework: str,
    deployment_result: DeploymentResult,
    files: Dict[str, str],
    parent_deployment_id: Optional[int] = None
) -> DemoSite:
    """Save deployment information to database."""

    total_size = sum(len(content.encode('utf-8')) for content in files.values())

    demo_site = DemoSite(
        lead_id=lead_id,
        vercel_project_id=deployment_result.project_id,
        vercel_deployment_id=deployment_result.deployment_id,
        project_name=project_name,
        framework=framework,
        url=deployment_result.url,
        preview_url=deployment_result.preview_url,
        status=deployment_result.status or "error",
        build_time=deployment_result.build_time,
        framework_detected=deployment_result.framework_detected,
        regions=deployment_result.regions,
        files_count=len(files),
        total_size_bytes=total_size,
        deployment_duration=deployment_result.build_time,
        ssl_enabled=True,
        ssl_issued_at=datetime.now(timezone.utc) if deployment_result.success else None,
        deployed_at=datetime.now(timezone.utc) if deployment_result.success else None,
        is_active=deployment_result.success,
        error_message=deployment_result.error_message,
        deployment_metadata=deployment_result.metadata,
        parent_deployment_id=parent_deployment_id
    )

    db.add(demo_site)
    await db.commit()
    await db.refresh(demo_site)

    # Log deployment event
    history = DeploymentHistory(
        demo_site_id=demo_site.id,
        event_type="created" if deployment_result.success else "error",
        new_status=demo_site.status,
        event_data=deployment_result.metadata,
        error_details=deployment_result.error_message
    )
    db.add(history)
    await db.commit()

    return demo_site


@router.post("/deploy", response_model=DeploymentResponse, status_code=201)
async def deploy_demo_site(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Deploy a demo site to Vercel.

    This endpoint deploys a demo site for a specific lead. The deployment
    is processed asynchronously, and the response includes the initial
    deployment information. Use GET /demo-sites/{id} to check deployment status.

    Args:
        request: Deployment request with files and configuration
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        DeploymentResponse with deployment information

    Raises:
        HTTPException: If lead not found or deployment fails
    """
    # Verify lead exists
    result = await db.execute(select(Lead).where(Lead.id == request.lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")

    # Generate project name if not provided
    project_name = request.project_name or await _generate_project_name(
        request.lead_id,
        request.framework
    )

    try:
        # Initialize Vercel deployer
        deployer = VercelDeployer()

        # Deploy to Vercel
        logger.info(f"Deploying demo site for lead {request.lead_id}: {project_name}")

        deployment_result = await deployer.deploy_demo_site(
            files=request.files,
            framework=request.framework,
            project_name=project_name,
            lead_id=request.lead_id,
            env_vars=request.env_vars
        )

        # Save deployment to database
        demo_site = await _save_deployment(
            db=db,
            lead_id=request.lead_id,
            project_name=project_name,
            framework=request.framework,
            deployment_result=deployment_result,
            files=request.files
        )

        # Add custom domain if provided
        if request.custom_domain and deployment_result.success:
            background_tasks.add_task(
                _add_custom_domain,
                demo_site.id,
                deployment_result.project_id,
                request.custom_domain
            )

        return DeploymentResponse(
            id=demo_site.id,
            lead_id=demo_site.lead_id,
            vercel_project_id=demo_site.vercel_project_id,
            vercel_deployment_id=demo_site.vercel_deployment_id,
            project_name=demo_site.project_name,
            framework=demo_site.framework,
            url=demo_site.url,
            preview_url=demo_site.preview_url,
            status=demo_site.status,
            build_time=demo_site.build_time,
            created_at=demo_site.created_at.isoformat(),
            deployed_at=demo_site.deployed_at.isoformat() if demo_site.deployed_at else None,
            error_message=demo_site.error_message
        )

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get deployment information.

    Args:
        deployment_id: Deployment ID
        db: Database session

    Returns:
        DeploymentResponse with deployment information

    Raises:
        HTTPException: If deployment not found
    """
    result = await db.execute(
        select(DemoSite).where(
            and_(
                DemoSite.id == deployment_id,
                DemoSite.is_deleted == False
            )
        )
    )
    demo_site = result.scalar_one_or_none()

    if not demo_site:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

    return DeploymentResponse(
        id=demo_site.id,
        lead_id=demo_site.lead_id,
        vercel_project_id=demo_site.vercel_project_id,
        vercel_deployment_id=demo_site.vercel_deployment_id,
        project_name=demo_site.project_name,
        framework=demo_site.framework,
        url=demo_site.url,
        preview_url=demo_site.preview_url,
        status=demo_site.status,
        build_time=demo_site.build_time,
        created_at=demo_site.created_at.isoformat(),
        deployed_at=demo_site.deployed_at.isoformat() if demo_site.deployed_at else None,
        error_message=demo_site.error_message
    )


@router.get("/lead/{lead_id}", response_model=DeploymentListResponse)
async def get_deployments_for_lead(
    lead_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_deleted: bool = Query(False, description="Include deleted deployments"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all deployments for a specific lead.

    Args:
        lead_id: Lead ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        include_deleted: Include deleted deployments
        db: Database session

    Returns:
        DeploymentListResponse with paginated deployments

    Raises:
        HTTPException: If lead not found
    """
    # Verify lead exists
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")

    # Build query
    query = select(DemoSite).where(DemoSite.lead_id == lead_id)

    if not include_deleted:
        query = query.where(DemoSite.is_deleted == False)

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # Get paginated results
    query = query.order_by(desc(DemoSite.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    demo_sites = result.scalars().all()

    deployments = [
        DeploymentResponse(
            id=site.id,
            lead_id=site.lead_id,
            vercel_project_id=site.vercel_project_id,
            vercel_deployment_id=site.vercel_deployment_id,
            project_name=site.project_name,
            framework=site.framework,
            url=site.url,
            preview_url=site.preview_url,
            status=site.status,
            build_time=site.build_time,
            created_at=site.created_at.isoformat(),
            deployed_at=site.deployed_at.isoformat() if site.deployed_at else None,
            error_message=site.error_message
        )
        for site in demo_sites
    ]

    return DeploymentListResponse(
        total=total,
        deployments=deployments,
        page=page,
        page_size=page_size
    )


@router.post("/{deployment_id}/redeploy", response_model=DeploymentResponse)
async def redeploy_demo_site(
    deployment_id: int,
    request: RedeploymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Redeploy an existing demo site.

    This creates a new deployment using the same configuration as the
    original deployment.

    Args:
        deployment_id: Original deployment ID
        request: Redeployment request
        db: Database session

    Returns:
        DeploymentResponse with new deployment information

    Raises:
        HTTPException: If deployment not found or redeployment fails
    """
    # Get original deployment
    result = await db.execute(
        select(DemoSite).where(DemoSite.id == deployment_id)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

    try:
        # Note: We don't have the original files stored, so this is a placeholder
        # In a real implementation, you'd need to store the files or regenerate them
        raise HTTPException(
            status_code=501,
            detail="Redeployment requires original files. Use POST /deploy with new files instead."
        )

    except Exception as e:
        logger.error(f"Redeployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Redeployment failed: {str(e)}")


@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    permanent: bool = Query(False, description="Permanently delete from Vercel (default: soft delete)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a deployment.

    By default, this performs a soft delete (marks as deleted in database).
    Use permanent=true to also delete from Vercel.

    Args:
        deployment_id: Deployment ID
        permanent: Whether to permanently delete from Vercel
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If deployment not found or deletion fails
    """
    result = await db.execute(
        select(DemoSite).where(DemoSite.id == deployment_id)
    )
    demo_site = result.scalar_one_or_none()

    if not demo_site:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

    if demo_site.is_deleted:
        raise HTTPException(status_code=400, detail="Deployment already deleted")

    try:
        # Soft delete
        demo_site.is_deleted = True
        demo_site.is_active = False
        demo_site.deleted_at = datetime.now(timezone.utc)

        # Permanent delete from Vercel
        if permanent and demo_site.vercel_deployment_id:
            deployer = VercelDeployer()
            success, error = await deployer.delete_deployment(demo_site.vercel_deployment_id)

            if not success:
                logger.warning(f"Failed to delete from Vercel: {error}")
                # Continue with soft delete even if Vercel deletion fails

        await db.commit()

        # Log deletion event
        history = DeploymentHistory(
            demo_site_id=demo_site.id,
            event_type="deleted",
            previous_status=demo_site.status,
            new_status="deleted",
            event_data={"permanent": permanent}
        )
        db.add(history)
        await db.commit()

        return {
            "message": "Deployment deleted successfully",
            "id": deployment_id,
            "permanent": permanent
        }

    except Exception as e:
        logger.error(f"Deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/", response_model=DeploymentListResponse)
async def list_deployments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    include_deleted: bool = Query(False, description="Include deleted deployments"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all deployments with filtering and pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by deployment status
        framework: Filter by framework
        include_deleted: Include deleted deployments
        db: Database session

    Returns:
        DeploymentListResponse with paginated deployments
    """
    # Build query
    query = select(DemoSite)

    if not include_deleted:
        query = query.where(DemoSite.is_deleted == False)

    if status:
        query = query.where(DemoSite.status == status)

    if framework:
        query = query.where(DemoSite.framework == framework)

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # Get paginated results
    query = query.order_by(desc(DemoSite.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    demo_sites = result.scalars().all()

    deployments = [
        DeploymentResponse(
            id=site.id,
            lead_id=site.lead_id,
            vercel_project_id=site.vercel_project_id,
            vercel_deployment_id=site.vercel_deployment_id,
            project_name=site.project_name,
            framework=site.framework,
            url=site.url,
            preview_url=site.preview_url,
            status=site.status,
            build_time=site.build_time,
            created_at=site.created_at.isoformat(),
            deployed_at=site.deployed_at.isoformat() if site.deployed_at else None,
            error_message=site.error_message
        )
        for site in demo_sites
    ]

    return DeploymentListResponse(
        total=total,
        deployments=deployments,
        page=page,
        page_size=page_size
    )


@router.get("/stats/overview", response_model=DeploymentStatsResponse)
async def get_deployment_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in stats"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get deployment statistics and analytics.

    Args:
        days: Number of days to include in statistics
        db: Database session

    Returns:
        DeploymentStatsResponse with statistics
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Get total deployments
    total_result = await db.execute(
        select(func.count()).select_from(DemoSite).where(DemoSite.created_at >= cutoff_date)
    )
    total_deployments = total_result.scalar()

    # Get active deployments
    active_result = await db.execute(
        select(func.count()).select_from(DemoSite).where(
            and_(
                DemoSite.is_active == True,
                DemoSite.is_deleted == False,
                DemoSite.created_at >= cutoff_date
            )
        )
    )
    active_deployments = active_result.scalar()

    # Get failed deployments
    failed_result = await db.execute(
        select(func.count()).select_from(DemoSite).where(
            and_(
                DemoSite.status == "error",
                DemoSite.created_at >= cutoff_date
            )
        )
    )
    failed_deployments = failed_result.scalar()

    # Get page views and bandwidth
    stats_result = await db.execute(
        select(
            func.sum(DemoSite.page_views),
            func.sum(DemoSite.bandwidth_bytes)
        ).where(DemoSite.created_at >= cutoff_date)
    )
    total_page_views, total_bandwidth_bytes = stats_result.one()
    total_page_views = total_page_views or 0
    total_bandwidth_bytes = total_bandwidth_bytes or 0
    total_bandwidth_gb = total_bandwidth_bytes / (1024 ** 3)

    # Get deployments by status
    status_result = await db.execute(
        select(DemoSite.status, func.count()).where(
            DemoSite.created_at >= cutoff_date
        ).group_by(DemoSite.status)
    )
    deployments_by_status = dict(status_result.all())

    # Get deployments by framework
    framework_result = await db.execute(
        select(DemoSite.framework, func.count()).where(
            DemoSite.created_at >= cutoff_date
        ).group_by(DemoSite.framework)
    )
    deployments_by_framework = dict(framework_result.all())

    # Estimate monthly cost
    # This is a simplified calculation
    estimated_monthly_cost = (total_bandwidth_gb / 100) * 40 + 20  # $20 base + bandwidth overage

    return DeploymentStatsResponse(
        total_deployments=total_deployments,
        active_deployments=active_deployments,
        failed_deployments=failed_deployments,
        total_page_views=total_page_views,
        total_bandwidth_gb=round(total_bandwidth_gb, 2),
        estimated_monthly_cost=round(estimated_monthly_cost, 2),
        deployments_by_status=deployments_by_status,
        deployments_by_framework=deployments_by_framework
    )


# Background task helper functions

async def _add_custom_domain(demo_site_id: int, project_id: str, domain: str):
    """Background task to add custom domain to deployment."""
    try:
        deployer = VercelDeployer()
        success, error = await deployer.add_domain(project_id, domain)

        if success:
            logger.info(f"Added custom domain {domain} to deployment {demo_site_id}")
            # Update database
            # Note: This would need a database session in a real implementation
        else:
            logger.error(f"Failed to add custom domain: {error}")

    except Exception as e:
        logger.error(f"Error adding custom domain: {str(e)}")
