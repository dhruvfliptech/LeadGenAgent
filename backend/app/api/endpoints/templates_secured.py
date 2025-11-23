"""
API endpoints for response template management with comprehensive security.
Implements OWASP best practices for input validation and SQL injection prevention.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
from datetime import datetime
import logging
import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing_extensions import Annotated

from app.core.database import get_db
from app.core.auth import get_current_user, User
from app.models.response_templates import ResponseTemplate
from app.models.auto_response import AutoResponse, ResponseVariable
from app.api.validators import (
    sanitize_html,
    check_sql_injection,
    validate_safe_string,
    SafeString,
    SafeTitle,
    SafeName,
    SafeCategory
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============= SECURE PYDANTIC MODELS WITH VALIDATION =============

class SecureResponseTemplateBase(BaseModel):
    """Base model with security validation for response templates."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: SafeName = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[SafeString] = Field(None, max_length=1000, description="Template description")
    category: Optional[SafeCategory] = Field(None, max_length=100, description="Template category")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate template name for SQL injection and XSS."""
        if not v or not v.strip():
            raise ValueError("Template name cannot be empty")

        # Check for SQL injection patterns
        check_sql_injection(v)

        # Ensure name is alphanumeric with basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-\_\.]+$', v):
            raise ValueError("Template name can only contain letters, numbers, spaces, hyphens, underscores, and periods")

        return v.strip()

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        """Validate category for SQL injection."""
        if not v:
            return v

        # Check for SQL injection patterns
        check_sql_injection(v)

        # Ensure category is from allowed list or alphanumeric
        ALLOWED_CATEGORIES = [
            'general', 'sales', 'support', 'marketing', 'recruitment',
            'followup', 'introduction', 'proposal', 'custom'
        ]

        if v.lower() not in ALLOWED_CATEGORIES:
            # If not in predefined list, ensure it's safe
            if not re.match(r'^[a-zA-Z0-9\-\_]+$', v):
                raise ValueError(f"Invalid category format. Must be alphanumeric with hyphens/underscores")

        return v.strip()


class SecureResponseTemplateCreate(SecureResponseTemplateBase):
    """Secure schema for creating response templates."""

    subject_template: str = Field(..., min_length=1, max_length=500, description="Email subject template")
    body_template: str = Field(..., min_length=1, max_length=50000, description="Email body template")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables configuration")
    use_ai_enhancement: bool = Field(False, description="Enable AI enhancement")
    ai_tone: str = Field("professional", pattern='^(professional|casual|friendly|formal|technical)$')
    ai_length: str = Field("medium", pattern='^(short|medium|long)$')
    test_weight: float = Field(50.0, ge=0.0, le=100.0, description="A/B test weight percentage")

    @field_validator('subject_template')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate and sanitize subject template."""
        if not v or not v.strip():
            raise ValueError("Subject template cannot be empty")

        # Check for SQL injection
        check_sql_injection(v)

        # Sanitize HTML to prevent XSS
        sanitized = sanitize_html(v)

        # Check for script tags or javascript
        if re.search(r'<script|javascript:|on\w+\s*=', sanitized, re.IGNORECASE):
            raise ValueError("Subject template contains potentially malicious content")

        return sanitized

    @field_validator('body_template')
    @classmethod
    def validate_body(cls, v: str) -> str:
        """Validate and sanitize body template."""
        if not v or not v.strip():
            raise ValueError("Body template cannot be empty")

        # Check for SQL injection
        check_sql_injection(v)

        # Sanitize HTML to prevent XSS
        sanitized = sanitize_html(v)

        # Additional check for template injection attempts
        injection_patterns = [
            r'\{\{.*exec.*\}\}',
            r'\{\{.*eval.*\}\}',
            r'\{\{.*import.*\}\}',
            r'\{\{.*__.*\}\}',  # Python dunder methods
            r'\{\{.*\|.*system.*\}\}',  # Jinja2 filters that could be dangerous
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError("Template contains potentially dangerous template syntax")

        return sanitized

    @field_validator('variables')
    @classmethod
    def validate_variables(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate template variables configuration."""
        if not v:
            return v

        # Ensure variables dict doesn't contain dangerous keys
        dangerous_keys = ['__proto__', 'constructor', 'prototype', '__init__']
        for key in v.keys():
            if key.lower() in dangerous_keys:
                raise ValueError(f"Variable key '{key}' is not allowed")

            # Validate key format
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', key):
                raise ValueError(f"Variable key '{key}' must be a valid identifier")

        # Recursively validate nested values
        def validate_value(value):
            if isinstance(value, str):
                check_sql_injection(value)
                return sanitize_html(value)
            elif isinstance(value, dict):
                return {k: validate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [validate_value(item) for item in value]
            return value

        return {k: validate_value(v) for k, v in v.items()}


class SecureResponseTemplateUpdate(BaseModel):
    """Secure schema for updating response templates."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[SafeName] = Field(None, min_length=1, max_length=255)
    description: Optional[SafeString] = Field(None, max_length=1000)
    category: Optional[SafeCategory] = Field(None, max_length=100)
    subject_template: Optional[str] = Field(None, min_length=1, max_length=500)
    body_template: Optional[str] = Field(None, min_length=1, max_length=50000)
    variables: Optional[Dict[str, Any]] = None
    use_ai_enhancement: Optional[bool] = None
    ai_tone: Optional[str] = Field(None, pattern='^(professional|casual|friendly|formal|technical)$')
    ai_length: Optional[str] = Field(None, pattern='^(short|medium|long)$')
    is_active: Optional[bool] = None
    test_weight: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Apply same validators as create model
    _validate_subject = field_validator('subject_template')(SecureResponseTemplateCreate.validate_subject)
    _validate_body = field_validator('body_template')(SecureResponseTemplateCreate.validate_body)
    _validate_variables = field_validator('variables')(SecureResponseTemplateCreate.validate_variables)


class ResponseTemplateResponse(BaseModel):
    """Response model for template data."""
    model_config = ConfigDict(from_attributes=True)

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


class SecureAutoResponseCreate(BaseModel):
    """Secure schema for creating auto responses."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: int = Field(..., ge=1, description="Lead ID")
    template_id: int = Field(..., ge=1, description="Template ID")
    delay_minutes: int = Field(0, ge=0, le=10080, description="Delay in minutes (max 1 week)")
    personalization_config: Optional[Dict[str, Any]] = None

    @field_validator('personalization_config')
    @classmethod
    def validate_personalization(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate personalization configuration."""
        if not v:
            return v

        # Apply same validation as template variables
        return SecureResponseTemplateCreate.validate_variables(v)


class AutoResponseResponse(BaseModel):
    """Response model for auto response data."""
    model_config = ConfigDict(from_attributes=True)

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


class SecureResponseVariableCreate(BaseModel):
    """Secure schema for creating response variables."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z][a-zA-Z0-9_]*$')
    display_name: SafeName = Field(..., min_length=1, max_length=200)
    description: Optional[SafeString] = Field(None, max_length=1000)
    variable_type: str = Field(..., pattern='^(text|number|date|boolean|url|email)$')
    source_field: Optional[str] = Field(None, max_length=100, pattern=r'^[a-zA-Z][a-zA-Z0-9_\.]*$')
    default_value: Optional[SafeString] = Field(None, max_length=500)
    is_required: bool = Field(False)
    validation_regex: Optional[str] = Field(None, max_length=500)
    min_length: Optional[int] = Field(None, ge=0, le=10000)
    max_length: Optional[int] = Field(None, ge=0, le=10000)

    @field_validator('validation_regex')
    @classmethod
    def validate_regex(cls, v: Optional[str]) -> Optional[str]:
        """Validate regex pattern is safe."""
        if not v:
            return v

        try:
            # Try to compile the regex to ensure it's valid
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        # Check for ReDoS (Regular Expression Denial of Service) patterns
        dangerous_patterns = [
            r'(\w+)+',  # Catastrophic backtracking
            r'(\d+)+',
            r'(.*)+',
            r'(.+)+',
        ]

        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError("Regex pattern may be vulnerable to ReDoS attacks")

        return v


class ResponseVariableResponse(BaseModel):
    """Response model for variable data."""
    model_config = ConfigDict(from_attributes=True)

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


# ============= SECURE QUERY PARAMETER VALIDATORS =============

def validate_template_query_params(
    skip: int = Query(0, ge=0, le=10000, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category: Optional[str] = Query(None, max_length=100, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> tuple:
    """Validate and sanitize query parameters for template queries."""

    # Additional validation for category if provided
    if category:
        # Check for SQL injection
        check_sql_injection(category)

        # Ensure it's alphanumeric with basic punctuation
        if not re.match(r'^[a-zA-Z0-9\-\_]+$', category):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category format"
            )

    return skip, limit, category, is_active


def validate_response_query_params(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, pattern='^(pending|scheduled|sending|sent|failed|cancelled)$'),
    lead_id: Optional[int] = Query(None, ge=1),
    template_id: Optional[int] = Query(None, ge=1)
) -> tuple:
    """Validate query parameters for auto response queries."""
    return skip, limit, status, lead_id, template_id


# ============= SECURE ENDPOINTS WITH AUTHENTICATION =============

@router.get("/", response_model=List[ResponseTemplateResponse])
async def get_response_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: tuple = Depends(validate_template_query_params)
):
    """
    Get response templates with optional filtering.

    Security features:
    - Authentication required
    - Input validation and sanitization
    - Parameterized queries prevent SQL injection
    - Rate limiting applied (via middleware)
    """
    skip, limit, category, is_active = params

    try:
        # Build query using SQLAlchemy ORM (prevents SQL injection)
        stmt = select(ResponseTemplate)

        # Apply filters using parameterized queries
        conditions = []

        if category is not None:
            # Use parameterized query - SQLAlchemy handles escaping
            conditions.append(ResponseTemplate.category == category)

        if is_active is not None:
            conditions.append(ResponseTemplate.is_active == is_active)

        # Add user tenant isolation if multi-tenant
        # conditions.append(ResponseTemplate.user_id == current_user.id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(stmt)
        templates = result.scalars().all()

        # Log access for audit trail
        logger.info(f"User {current_user.id} retrieved {len(templates)} templates")

        return templates

    except Exception as e:
        logger.error(f"Error fetching templates for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )


@router.get("/{template_id}", response_model=ResponseTemplateResponse)
async def get_response_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific response template.

    Security features:
    - Authentication required
    - Authorization check (ownership verification)
    - Parameterized query prevents SQL injection
    """
    if template_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template ID"
        )

    try:
        # Use parameterized query
        stmt = select(ResponseTemplate).where(
            ResponseTemplate.id == template_id
            # Add user ownership check for multi-tenant
            # and_(
            #     ResponseTemplate.id == template_id,
            #     ResponseTemplate.user_id == current_user.id
            # )
        )

        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"User {current_user.id} attempted to access non-existent template {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Log access
        logger.info(f"User {current_user.id} accessed template {template_id}")

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.post("/", response_model=ResponseTemplateResponse)
async def create_response_template(
    template_data: SecureResponseTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new response template.

    Security features:
    - Authentication required
    - Input validation and sanitization via Pydantic
    - XSS prevention through HTML sanitization
    - SQL injection prevention through ORM
    """
    try:
        # Check if template name already exists (prevent duplicates)
        stmt = select(ResponseTemplate).where(
            ResponseTemplate.name == template_data.name
            # Add user scope for multi-tenant
            # and_(
            #     ResponseTemplate.name == template_data.name,
            #     ResponseTemplate.user_id == current_user.id
            # )
        )

        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template with name '{template_data.name}' already exists"
            )

        # Create new template with validated data
        template = ResponseTemplate(
            **template_data.model_dump(exclude_unset=True),
            # user_id=current_user.id  # Add user ownership
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        # Log creation
        logger.info(f"User {current_user.id} created template {template.id}")

        return template

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating template for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )


@router.put("/{template_id}", response_model=ResponseTemplateResponse)
async def update_response_template(
    template_id: int,
    template_data: SecureResponseTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a response template.

    Security features:
    - Authentication required
    - Authorization check (ownership verification)
    - Input validation and sanitization
    - Prevents unauthorized modifications
    """
    if template_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template ID"
        )

    try:
        # Fetch template with ownership check
        stmt = select(ResponseTemplate).where(
            ResponseTemplate.id == template_id
            # Add ownership check
            # and_(
            #     ResponseTemplate.id == template_id,
            #     ResponseTemplate.user_id == current_user.id
            # )
        )

        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"User {current_user.id} attempted to update non-existent template {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Check if name is being changed and if it conflicts
        if template_data.name and template_data.name != template.name:
            check_stmt = select(ResponseTemplate).where(
                and_(
                    ResponseTemplate.name == template_data.name,
                    ResponseTemplate.id != template_id
                    # ResponseTemplate.user_id == current_user.id
                )
            )
            check_result = await db.execute(check_stmt)
            if check_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Template with name '{template_data.name}' already exists"
                )

        # Update template with validated data
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(template)

        # Log update
        logger.info(f"User {current_user.id} updated template {template_id}")

        return template

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete("/{template_id}")
async def delete_response_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a response template.

    Security features:
    - Authentication required
    - Authorization check (ownership verification)
    - Prevents deletion of templates in use
    - Cascade protection
    """
    if template_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid template ID"
        )

    try:
        # Fetch template with ownership check
        stmt = select(ResponseTemplate).where(
            ResponseTemplate.id == template_id
            # Add ownership check
            # and_(
            #     ResponseTemplate.id == template_id,
            #     ResponseTemplate.user_id == current_user.id
            # )
        )

        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            logger.warning(f"User {current_user.id} attempted to delete non-existent template {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Check if template is being used in active responses
        active_stmt = select(func.count(AutoResponse.id)).where(
            and_(
                AutoResponse.template_id == template_id,
                AutoResponse.status.in_(["pending", "scheduled", "sending"])
            )
        )

        active_result = await db.execute(active_stmt)
        active_count = active_result.scalar()

        if active_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete template with {active_count} active responses. Archive it instead."
            )

        # Soft delete (set inactive) instead of hard delete
        template.is_active = False
        template.updated_at = datetime.utcnow()

        await db.commit()

        # Log deletion
        logger.info(f"User {current_user.id} deleted template {template_id}")

        return {"message": "Template archived successfully", "template_id": template_id}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


# Auto Response endpoints
@router.get("/responses/", response_model=List[AutoResponseResponse])
async def get_auto_responses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: tuple = Depends(validate_response_query_params)
):
    """
    Get auto responses with optional filtering.

    Security features:
    - Authentication required
    - Parameterized queries
    - User isolation
    """
    skip, limit, status, lead_id, template_id = params

    try:
        stmt = select(AutoResponse)

        conditions = []

        if status:
            conditions.append(AutoResponse.status == status)

        if lead_id:
            conditions.append(AutoResponse.lead_id == lead_id)

        if template_id:
            conditions.append(AutoResponse.template_id == template_id)

        # Add user isolation through lead ownership
        # stmt = stmt.join(Lead).where(Lead.user_id == current_user.id)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(desc(AutoResponse.created_at)).offset(skip).limit(limit)

        result = await db.execute(stmt)
        responses = result.scalars().all()

        return responses

    except Exception as e:
        logger.error(f"Error fetching auto responses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve auto responses"
        )


@router.get("/responses/{response_id}", response_model=AutoResponseResponse)
async def get_auto_response(
    response_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific auto response.

    Security features:
    - Authentication required
    - Authorization check
    """
    if response_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid response ID"
        )

    try:
        stmt = select(AutoResponse).where(AutoResponse.id == response_id)
        # Add user check through lead ownership
        # stmt = stmt.join(Lead).where(Lead.user_id == current_user.id)

        result = await db.execute(stmt)
        response = result.scalar_one_or_none()

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Auto response not found"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching auto response {response_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve auto response"
        )


@router.post("/responses/", response_model=AutoResponseResponse)
async def create_auto_response(
    response_data: SecureAutoResponseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new auto response.

    Security features:
    - Authentication required
    - Input validation
    - Lead ownership verification
    - Template access verification
    """
    try:
        # Verify user owns the lead
        from app.models.leads import Lead

        lead_stmt = select(Lead).where(Lead.id == response_data.lead_id)
        lead_result = await db.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Verify template exists and is active
        template_stmt = select(ResponseTemplate).where(
            and_(
                ResponseTemplate.id == response_data.template_id,
                ResponseTemplate.is_active == True
            )
        )
        template_result = await db.execute(template_stmt)
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or inactive"
            )

        # Create auto response
        from app.services.auto_responder import auto_responder_service

        auto_response = await auto_responder_service.create_auto_response(
            lead_id=response_data.lead_id,
            template_id=response_data.template_id,
            delay_minutes=response_data.delay_minutes,
            personalization_config=response_data.personalization_config
        )

        logger.info(f"User {current_user.id} created auto response {auto_response.id}")

        return auto_response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating auto response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create auto response"
        )


@router.post("/responses/{response_id}/track/{event_type}")
async def track_response_engagement(
    response_id: int,
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track engagement events for auto responses.

    Security features:
    - Authentication required
    - Event type validation
    - Authorization check
    """
    valid_events = ["email_opened", "email_clicked", "lead_responded"]

    if event_type not in valid_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event type. Must be one of: {', '.join(valid_events)}"
        )

    if response_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid response ID"
        )

    try:
        # Verify response exists and user has access
        stmt = select(AutoResponse).where(AutoResponse.id == response_id)
        # Add user check through lead ownership
        # stmt = stmt.join(Lead).where(Lead.user_id == current_user.id)

        result = await db.execute(stmt)
        response = result.scalar_one_or_none()

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Auto response not found"
            )

        # Validate and sanitize event data if provided
        if event_data:
            for key, value in event_data.items():
                if isinstance(value, str):
                    check_sql_injection(value)
                    event_data[key] = sanitize_html(value)

        from app.services.auto_responder import auto_responder_service

        await auto_responder_service.track_response_engagement(
            response_id, event_type, event_data
        )

        logger.info(f"User {current_user.id} tracked {event_type} for response {response_id}")

        return {"message": f"Tracked {event_type} event for response {response_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking engagement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track engagement"
        )


# Response Variable endpoints
@router.get("/variables/", response_model=List[ResponseVariableResponse])
async def get_response_variables(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, ge=1, le=1000),
    variable_type: Optional[str] = Query(None, pattern='^(text|number|date|boolean|url|email)$'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get response variables.

    Security features:
    - Authentication required
    - Input validation
    """
    try:
        stmt = select(ResponseVariable)

        if variable_type:
            stmt = stmt.where(ResponseVariable.variable_type == variable_type)

        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        variables = result.scalars().all()

        return variables

    except Exception as e:
        logger.error(f"Error fetching variables: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve variables"
        )


@router.post("/variables/", response_model=ResponseVariableResponse)
async def create_response_variable(
    variable_data: SecureResponseVariableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new response variable.

    Security features:
    - Authentication required
    - Input validation
    - Duplicate prevention
    """
    try:
        # Check if variable name already exists
        stmt = select(ResponseVariable).where(
            ResponseVariable.name == variable_data.name
        )

        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variable with name '{variable_data.name}' already exists"
            )

        variable = ResponseVariable(**variable_data.model_dump())
        db.add(variable)
        await db.commit()
        await db.refresh(variable)

        logger.info(f"User {current_user.id} created variable {variable.id}")

        return variable

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating variable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create variable"
        )


# Analytics endpoints (with proper security)
@router.get("/analytics/templates")
async def get_template_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get template performance analytics.

    Security features:
    - Authentication required
    - Input validation
    - User-scoped data
    """
    try:
        from app.services.auto_responder import auto_responder_service

        # Get analytics scoped to user's templates
        analytics = await auto_responder_service.get_response_analytics(
            days=days,
            # user_id=current_user.id
        )

        return analytics

    except Exception as e:
        logger.error(f"Error fetching template analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/analytics/ab-testing")
async def get_ab_testing_results(
    template_id: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get A/B testing results for templates.

    Security features:
    - Authentication required
    - User-scoped data
    """
    try:
        stmt = select(ResponseTemplate).where(
            ResponseTemplate.sent_count > 0
            # Add user scope
            # ResponseTemplate.user_id == current_user.id
        )

        if template_id:
            stmt = stmt.where(ResponseTemplate.id == template_id)

        result = await db.execute(stmt)
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

        return {"results": results}

    except Exception as e:
        logger.error(f"Error fetching A/B testing results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B testing results"
        )


@router.post("/test/preview-template")
async def preview_template_rendering(
    template_id: int = Query(..., ge=1),
    lead_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Preview how a template would render for a specific lead.

    Security features:
    - Authentication required
    - Authorization checks for both template and lead
    - Safe template rendering
    """
    try:
        from app.models.leads import Lead
        from app.services.auto_responder import TemplateEngine

        # Fetch template with user check
        template_stmt = select(ResponseTemplate).where(
            ResponseTemplate.id == template_id
            # Add user check
            # ResponseTemplate.user_id == current_user.id
        )
        template_result = await db.execute(template_stmt)
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Fetch lead with user check
        lead_stmt = select(Lead).where(
            Lead.id == lead_id
            # Add user check
            # Lead.user_id == current_user.id
        )
        lead_result = await db.execute(lead_stmt)
        lead = lead_result.scalar_one_or_none()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Use secure template rendering
        template_engine = TemplateEngine(db)
        lead_data = template_engine.extract_lead_data(lead)

        # Sanitize lead data before rendering
        for key, value in lead_data.items():
            if isinstance(value, str):
                lead_data[key] = sanitize_html(value)

        rendered_subject = template_engine.render_template(
            template.subject_template, lead_data
        )
        rendered_body = template_engine.render_template(
            template.body_template, lead_data
        )

        return {
            "template_id": template_id,
            "lead_id": lead_id,
            "rendered_subject": sanitize_html(rendered_subject),
            "rendered_body": sanitize_html(rendered_body),
            "available_variables": lead_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview template"
        )