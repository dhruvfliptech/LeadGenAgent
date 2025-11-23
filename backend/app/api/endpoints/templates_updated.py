"""
API endpoints for response template management with structured error handling.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.rate_limiter import (
    templates_read_limiter,
    templates_write_limiter,
    templates_preview_limiter
)
from app.models.response_templates import ResponseTemplate
# TODO: Implement AutoResponse and ResponseVariable models before enabling
# from app.services.auto_responder import auto_responder_service
from pydantic import BaseModel
from app.exceptions import (
    TemplateNotFoundException,
    TemplateValidationException,
    TemplateSecurityException,
    TemplateInUseException,
    DatabaseException,
)

logger = get_logger(__name__)

router = APIRouter()


# Pydantic models
class ResponseTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subject_template: str
    body_template: str
    variables: Optional[dict] = None
    use_ai_enhancement: bool = False
    ai_tone: str = "professional"
    ai_length: str = "medium"
    test_weight: float = 50.0


class ResponseTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    variables: Optional[dict] = None
    use_ai_enhancement: Optional[bool] = None
    ai_tone: Optional[str] = None
    ai_length: Optional[str] = None
    is_active: Optional[bool] = None
    test_weight: Optional[float] = None


class ResponseTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    subject_template: str
    body_template: str
    variables: Optional[dict]
    use_ai_enhancement: bool
    ai_tone: str
    ai_length: str
    is_active: bool
    is_test_variant: bool
    control_template_id: Optional[int]
    test_weight: float
    sent_count: int
    response_count: int
    conversion_count: int
    response_rate: float
    conversion_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutoResponseCreate(BaseModel):
    lead_id: int
    template_id: int
    delay_minutes: int = 0
    personalization_config: Optional[dict] = None


class AutoResponseResponse(BaseModel):
    id: int
    lead_id: int
    template_id: int
    subject: str
    body: str
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delay_minutes: int
    error_message: Optional[str]
    retry_count: int
    email_opened: bool
    email_clicked: bool
    lead_responded: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResponseVariableCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    variable_type: str
    source_field: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = False
    validation_regex: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class ResponseVariableResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    variable_type: str
    source_field: Optional[str]
    default_value: Optional[str]
    is_required: bool
    validation_regex: Optional[str]
    min_length: Optional[int]
    max_length: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Response Template endpoints
@router.get("/", response_model=List[ResponseTemplateResponse], dependencies=[Depends(templates_read_limiter)])
async def get_response_templates(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get response templates with optional filtering."""
    try:
        logger.debug("Fetching response templates", category=category, is_active=is_active, skip=skip, limit=limit)

        query = select(ResponseTemplate)

        if category:
            query = query.where(ResponseTemplate.category == category)
        if is_active is not None:
            query = query.where(ResponseTemplate.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        templates = result.scalars().all()

        logger.info(f"Retrieved {len(templates)} templates", count=len(templates))
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to fetch templates",
            operation="get_templates",
            details={"error": str(e)}
        )


@router.get("/{template_id}", response_model=ResponseTemplateResponse, dependencies=[Depends(templates_read_limiter)])
async def get_response_template(request: Request, template_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific response template."""
    try:
        logger.debug(f"Fetching template {template_id}")

        query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"Template not found: {template_id}")
            raise TemplateNotFoundException(template_id)

        return template
    except TemplateNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {str(e)}", exc_info=e, template_id=template_id)
        raise DatabaseException(
            message="Failed to fetch template",
            operation="get_template",
            details={"template_id": template_id, "error": str(e)}
        )


@router.post("/", response_model=ResponseTemplateResponse, dependencies=[Depends(templates_write_limiter)])
async def create_response_template(
    request: Request,
    template_data: ResponseTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new response template with security validation."""
    start_time = datetime.utcnow()

    try:
        logger.info("Creating new response template", template_name=template_data.name, category=template_data.category)

        # Import security modules
        from app.core.template_security import TemplateSanitizer, TemplateSecurityValidator

        sanitizer = TemplateSanitizer()
        validator = TemplateSecurityValidator()

        # Validate subject and body templates for security issues
        subject_valid, subject_error = validator.validate_template(template_data.subject_template, "html")
        if not subject_valid:
            logger.warning(f"Subject template validation failed: {subject_error}")
            raise TemplateValidationException(
                message=f"Invalid subject template: {subject_error}",
                field="subject_template",
                validation_errors={"subject_template": subject_error}
            )

        body_valid, body_error = validator.validate_template(template_data.body_template, "html")
        if not body_valid:
            logger.warning(f"Body template validation failed: {body_error}")
            raise TemplateValidationException(
                message=f"Invalid body template: {body_error}",
                field="body_template",
                validation_errors={"body_template": body_error}
            )

        # Sanitize template content
        template_dict = template_data.dict()
        template_dict['subject_template'] = sanitizer.sanitize_html(template_data.subject_template, strip_tags=True)
        template_dict['body_template'] = sanitizer.sanitize_html(template_data.body_template, strip_tags=False)

        template = ResponseTemplate(**template_dict)
        db.add(template)
        await db.commit()
        await db.refresh(template)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.performance("create_template", duration, template_id=template.id)

        logger.audit(
            "template_created",
            "response_template",
            template.id,
            template_name=template.name
        )

        return template
    except (TemplateValidationException, TemplateSecurityException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating template: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to create template",
            operation="create_template",
            details={"error": str(e)}
        )


@router.put("/{template_id}", response_model=ResponseTemplateResponse, dependencies=[Depends(templates_write_limiter)])
async def update_response_template(
    request: Request,
    template_id: int,
    template_data: ResponseTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a response template with security validation."""
    start_time = datetime.utcnow()

    try:
        logger.info(f"Updating template {template_id}")

        query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"Template not found for update: {template_id}")
            raise TemplateNotFoundException(template_id)

        # Import security modules
        from app.core.template_security import TemplateSanitizer, TemplateSecurityValidator
        sanitizer = TemplateSanitizer()
        validator = TemplateSecurityValidator()

        update_data = template_data.dict(exclude_unset=True)

        # Validate and sanitize subject template if provided
        if 'subject_template' in update_data and update_data['subject_template']:
            subject_valid, subject_error = validator.validate_template(update_data['subject_template'], "html")
            if not subject_valid:
                logger.warning(f"Subject template validation failed for template {template_id}: {subject_error}")
                raise TemplateValidationException(
                    message=f"Invalid subject template: {subject_error}",
                    template_id=template_id,
                    field="subject_template",
                    validation_errors={"subject_template": subject_error}
                )
            update_data['subject_template'] = sanitizer.sanitize_html(update_data['subject_template'], strip_tags=True)

        # Validate and sanitize body template if provided
        if 'body_template' in update_data and update_data['body_template']:
            body_valid, body_error = validator.validate_template(update_data['body_template'], "html")
            if not body_valid:
                logger.warning(f"Body template validation failed for template {template_id}: {body_error}")
                raise TemplateValidationException(
                    message=f"Invalid body template: {body_error}",
                    template_id=template_id,
                    field="body_template",
                    validation_errors={"body_template": body_error}
                )
            update_data['body_template'] = sanitizer.sanitize_html(update_data['body_template'], strip_tags=False)

        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(template)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.performance("update_template", duration, template_id=template_id)

        logger.audit(
            "template_updated",
            "response_template",
            template_id,
            updated_fields=list(update_data.keys())
        )

        return template
    except (TemplateNotFoundException, TemplateValidationException, TemplateSecurityException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating template {template_id}: {str(e)}", exc_info=e, template_id=template_id)
        raise DatabaseException(
            message="Failed to update template",
            operation="update_template",
            details={"template_id": template_id, "error": str(e)}
        )


@router.delete("/{template_id}", dependencies=[Depends(templates_write_limiter)])
async def delete_response_template(request: Request, template_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a response template."""
    try:
        logger.info(f"Deleting template {template_id}")

        query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
        result = await db.execute(query)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"Template not found for deletion: {template_id}")
            raise TemplateNotFoundException(template_id)

        # Check if template is being used
        active_query = select(AutoResponse).where(
            and_(
                AutoResponse.template_id == template_id,
                AutoResponse.status.in_(["pending", "sent"])
            )
        )
        active_result = await db.execute(active_query)
        active_responses = active_result.scalars().all()

        if active_responses:
            logger.warning(
                f"Cannot delete template {template_id} - has {len(active_responses)} active responses"
            )
            raise TemplateInUseException(template_id, len(active_responses))

        await db.delete(template)
        await db.commit()

        logger.audit(
            "template_deleted",
            "response_template",
            template_id,
            template_name=template.name
        )

        return {"message": "Template deleted successfully"}
    except (TemplateNotFoundException, TemplateInUseException):
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template {template_id}: {str(e)}", exc_info=e, template_id=template_id)
        raise DatabaseException(
            message="Failed to delete template",
            operation="delete_template",
            details={"template_id": template_id, "error": str(e)}
        )


# Auto Response endpoints
@router.get("/responses/", response_model=List[AutoResponseResponse], dependencies=[Depends(templates_read_limiter)])
async def get_auto_responses(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    template_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get auto responses with optional filtering."""
    try:
        logger.debug("Fetching auto responses", status=status, lead_id=lead_id, template_id=template_id)

        query = select(AutoResponse)

        if status:
            query = query.where(AutoResponse.status == status)
        if lead_id:
            query = query.where(AutoResponse.lead_id == lead_id)
        if template_id:
            query = query.where(AutoResponse.template_id == template_id)

        query = query.order_by(desc(AutoResponse.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        responses = result.scalars().all()

        logger.info(f"Retrieved {len(responses)} auto responses", count=len(responses))
        return responses
    except Exception as e:
        logger.error(f"Error fetching auto responses: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to fetch auto responses",
            operation="get_auto_responses",
            details={"error": str(e)}
        )


@router.get("/responses/{response_id}", response_model=AutoResponseResponse, dependencies=[Depends(templates_read_limiter)])
async def get_auto_response(request: Request, response_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific auto response."""
    try:
        logger.debug(f"Fetching auto response {response_id}")

        query = select(AutoResponse).where(AutoResponse.id == response_id)
        result = await db.execute(query)
        response = result.scalar_one_or_none()

        if not response:
            logger.warning(f"Auto response not found: {response_id}")
            raise HTTPException(status_code=404, detail="Auto response not found")

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching auto response {response_id}: {str(e)}", exc_info=e, response_id=response_id)
        raise DatabaseException(
            message="Failed to fetch auto response",
            operation="get_auto_response",
            details={"response_id": response_id, "error": str(e)}
        )


@router.post("/responses/", response_model=AutoResponseResponse, dependencies=[Depends(templates_write_limiter)])
async def create_auto_response(
    request: Request,
    response_data: AutoResponseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new auto response."""
    try:
        logger.info("Creating auto response", lead_id=response_data.lead_id, template_id=response_data.template_id)

        auto_response = await auto_responder_service.create_auto_response(
            lead_id=response_data.lead_id,
            template_id=response_data.template_id,
            delay_minutes=response_data.delay_minutes,
            personalization_config=response_data.personalization_config
        )

        logger.audit(
            "auto_response_created",
            "auto_response",
            auto_response.id,
            lead_id=response_data.lead_id,
            template_id=response_data.template_id
        )

        return auto_response
    except ValueError as e:
        logger.warning(f"Auto response creation validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating auto response: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to create auto response",
            operation="create_auto_response",
            details={"error": str(e)}
        )


@router.post("/responses/{response_id}/track/{event_type}", dependencies=[Depends(templates_write_limiter)])
async def track_response_engagement(
    request: Request,
    response_id: int,
    event_type: str,
    event_data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db)
):
    """Track engagement events for auto responses."""
    valid_events = ["email_opened", "email_clicked", "lead_responded"]
    if event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type. Must be one of: {valid_events}"
        )

    try:
        logger.info(f"Tracking engagement event", response_id=response_id, event_type=event_type)

        await auto_responder_service.track_response_engagement(
            response_id, event_type, event_data
        )

        logger.audit(
            f"engagement_tracked_{event_type}",
            "auto_response",
            response_id,
            event_type=event_type
        )

        return {"message": f"Tracked {event_type} event for response {response_id}"}
    except Exception as e:
        logger.error(f"Error tracking engagement: {str(e)}", exc_info=e, response_id=response_id)
        raise DatabaseException(
            message="Failed to track engagement",
            operation="track_engagement",
            details={"response_id": response_id, "event_type": event_type, "error": str(e)}
        )


# Response Variable endpoints
@router.get("/variables/", response_model=List[ResponseVariableResponse], dependencies=[Depends(templates_read_limiter)])
async def get_response_variables(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    variable_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get response variables."""
    try:
        logger.debug("Fetching response variables", variable_type=variable_type)

        query = select(ResponseVariable)

        if variable_type:
            query = query.where(ResponseVariable.variable_type == variable_type)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        variables = result.scalars().all()

        logger.info(f"Retrieved {len(variables)} response variables", count=len(variables))
        return variables
    except Exception as e:
        logger.error(f"Error fetching variables: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to fetch response variables",
            operation="get_variables",
            details={"error": str(e)}
        )


@router.post("/variables/", response_model=ResponseVariableResponse, dependencies=[Depends(templates_write_limiter)])
async def create_response_variable(
    request: Request,
    variable_data: ResponseVariableCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new response variable."""
    try:
        logger.info("Creating response variable", variable_name=variable_data.name, variable_type=variable_data.variable_type)

        variable = ResponseVariable(**variable_data.dict())
        db.add(variable)
        await db.commit()
        await db.refresh(variable)

        logger.audit(
            "variable_created",
            "response_variable",
            variable.id,
            variable_name=variable.name
        )

        return variable
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating variable: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to create response variable",
            operation="create_variable",
            details={"error": str(e)}
        )


# Analytics endpoints
@router.get("/analytics/templates", dependencies=[Depends(templates_read_limiter)])
async def get_template_analytics(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get template performance analytics."""
    try:
        logger.debug(f"Fetching template analytics for last {days} days")

        analytics = auto_responder_service.get_response_analytics(days)

        return analytics
    except Exception as e:
        logger.error(f"Error fetching template analytics: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to fetch template analytics",
            operation="get_analytics",
            details={"error": str(e)}
        )


@router.get("/analytics/ab-testing", dependencies=[Depends(templates_read_limiter)])
async def get_ab_testing_results(
    request: Request,
    template_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get A/B testing results for templates."""
    try:
        logger.debug("Fetching A/B testing results", template_id=template_id)

        query = select(ResponseTemplate).where(ResponseTemplate.sent_count > 0)

        if template_id:
            query = query.where(ResponseTemplate.id == template_id)

        result = await db.execute(query)
        templates = result.scalars().all()

        results = []
        for template in templates:
            results.append({
                "template_id": template.id,
                "template_name": template.name,
                "is_test_variant": template.is_test_variant,
                "control_template_id": template.control_template_id,
                "sent_count": template.sent_count,
                "response_count": template.response_count,
                "conversion_count": template.conversion_count,
                "response_rate": template.response_rate,
                "conversion_rate": template.conversion_rate,
                "test_weight": template.test_weight
            })

        logger.info(f"Retrieved A/B test results for {len(results)} templates", count=len(results))
        return {"results": results}
    except Exception as e:
        logger.error(f"Error fetching A/B testing results: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to fetch A/B testing results",
            operation="get_ab_testing_results",
            details={"error": str(e)}
        )


@router.post("/test/preview-template", dependencies=[Depends(templates_preview_limiter)])
async def preview_template_rendering(
    request: Request,
    template_id: int,
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Preview how a template would render for a specific lead."""
    try:
        logger.info(f"Previewing template rendering", template_id=template_id, lead_id=lead_id)

        from app.models.leads import Lead
        from app.services.auto_responder import TemplateEngine

        # Fetch template
        template_query = select(ResponseTemplate).where(ResponseTemplate.id == template_id)
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()

        if not template:
            logger.warning(f"Template not found for preview: {template_id}")
            raise TemplateNotFoundException(template_id)

        # Fetch lead
        lead_query = select(Lead).where(Lead.id == lead_id)
        lead_result = await db.execute(lead_query)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            logger.warning(f"Lead not found for template preview: {lead_id}")
            raise HTTPException(status_code=404, detail="Lead not found")

        template_engine = TemplateEngine(db)
        lead_data = template_engine.extract_lead_data(lead)

        rendered_subject = template_engine.render_template(template.subject_template, lead_data)
        rendered_body = template_engine.render_template(template.body_template, lead_data)

        logger.info("Template preview generated successfully", template_id=template_id, lead_id=lead_id)

        return {
            "template_id": template_id,
            "lead_id": lead_id,
            "rendered_subject": rendered_subject,
            "rendered_body": rendered_body,
            "available_variables": lead_data
        }
    except (TemplateNotFoundException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}", exc_info=e, template_id=template_id, lead_id=lead_id)
        raise DatabaseException(
            message="Failed to preview template",
            operation="preview_template",
            details={"template_id": template_id, "lead_id": lead_id, "error": str(e)}
        )
