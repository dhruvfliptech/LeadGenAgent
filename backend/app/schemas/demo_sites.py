"""
Pydantic Schemas for Demo Site Builder

This module contains all request and response schemas for the demo site builder API.
Includes schemas for:
- Demo sites (generation, deployment, management)
- Templates (CRUD operations)
- Components (reusable UI elements)
- Analytics (tracking and reporting)
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, validator


# ============================================================================
# Demo Site Schemas
# ============================================================================

class DemoSiteContentData(BaseModel):
    """Content data for personalized demo site."""
    lead_name: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    headline: Optional[str] = None
    subheadline: Optional[str] = None
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    features: Optional[List[Dict[str, str]]] = None
    testimonials: Optional[List[Dict[str, str]]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class DemoSiteStyleSettings(BaseModel):
    """Style settings for demo site customization."""
    primary_color: Optional[str] = "#3B82F6"
    secondary_color: Optional[str] = "#1E40AF"
    accent_color: Optional[str] = "#F59E0B"
    font_family: Optional[str] = "Inter, sans-serif"
    font_size_base: Optional[str] = "16px"
    border_radius: Optional[str] = "8px"
    custom_css: Optional[str] = None


class DemoSiteGenerateRequest(BaseModel):
    """Request to generate a new demo site using AI."""
    lead_id: Optional[int] = Field(None, description="ID of the lead this demo site is for")
    site_name: str = Field(..., min_length=1, max_length=255, description="Name of the demo site")
    template_id: Optional[int] = Field(None, description="Template ID to use (or AI will choose)")
    template_type: Optional[str] = Field("landing", description="Template type: landing, portfolio, saas")

    # Content personalization
    content_data: DemoSiteContentData = Field(default_factory=DemoSiteContentData)
    style_settings: DemoSiteStyleSettings = Field(default_factory=DemoSiteStyleSettings)

    # AI generation options
    use_ai_generation: bool = Field(True, description="Use AI to generate content")
    ai_model: Optional[str] = Field("gpt-4", description="AI model to use for generation")
    ai_prompt: Optional[str] = Field(None, description="Custom prompt for AI generation")

    # Deployment options
    auto_deploy: bool = Field(False, description="Automatically deploy after generation")
    custom_subdomain: Optional[str] = Field(None, description="Custom subdomain (auto-generated if not provided)")


class DemoSiteUpdateRequest(BaseModel):
    """Request to update an existing demo site."""
    site_name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_id: Optional[int] = None
    content_data: Optional[DemoSiteContentData] = None
    style_settings: Optional[DemoSiteStyleSettings] = None
    custom_domain: Optional[str] = None
    analytics_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class DemoSiteDeployRequest(BaseModel):
    """Request to deploy a demo site to Vercel."""
    environment: str = Field("production", description="Deployment environment")
    regions: Optional[List[str]] = Field(None, description="Deployment regions")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class DemoSiteResponse(BaseModel):
    """Response schema for demo site details."""
    id: int
    lead_id: Optional[int] = None
    template_id: Optional[int] = None

    # Site info
    site_name: str
    subdomain: str = Field(..., alias="project_name")
    custom_domain: Optional[str] = None

    # Content and styling
    content_data: Optional[Dict[str, Any]] = None
    style_settings: Optional[Dict[str, Any]] = None

    # Deployment info
    deployment_status: str = Field(..., alias="status")
    vercel_deployment_id: Optional[str] = None
    vercel_url: Optional[str] = Field(None, alias="url")
    vercel_project_id: Optional[str] = None

    # Generated code
    generated_html: Optional[str] = None
    generated_css: Optional[str] = None
    generated_js: Optional[str] = None

    # Analytics
    analytics_enabled: bool = True
    total_views: int = Field(0, alias="page_views")
    total_conversions: int = 0

    # Metadata
    is_active: bool = True
    error_message: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_deployed_at: Optional[datetime] = Field(None, alias="deployed_at")

    class Config:
        from_attributes = True
        populate_by_name = True


class DemoSiteListResponse(BaseModel):
    """Response for list of demo sites."""
    total: int
    page: int
    page_size: int
    demo_sites: List[DemoSiteResponse]


class DemoSitePreviewResponse(BaseModel):
    """Response for demo site preview (HTML/CSS/JS)."""
    html: str
    css: str
    js: Optional[str] = None
    preview_url: Optional[str] = None


class DemoSiteExportResponse(BaseModel):
    """Response for exporting demo site files."""
    files: List[Dict[str, str]]  # [{"filename": "index.html", "content": "..."}]
    zip_url: Optional[str] = None


# ============================================================================
# Template Schemas
# ============================================================================

class TemplateCustomizationOptions(BaseModel):
    """Customization options for a template."""
    colors: Optional[List[str]] = Field(default_factory=list)
    fonts: Optional[List[str]] = Field(default_factory=list)
    layouts: Optional[List[str]] = Field(default_factory=list)
    sections: Optional[List[str]] = Field(default_factory=list)


class DemoSiteTemplateCreate(BaseModel):
    """Request to create a new template."""
    template_name: str = Field(..., min_length=1, max_length=255)
    template_type: str = Field(..., description="landing, portfolio, saas, custom")
    description: Optional[str] = None

    # Template code
    html_template: str = Field(..., min_length=1)
    css_template: str = Field(..., min_length=1)
    js_template: Optional[str] = None

    # Preview and customization
    preview_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    customization_options: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # SEO
    default_meta_title: Optional[str] = None
    default_meta_description: Optional[str] = None
    default_meta_keywords: Optional[str] = None

    # Flags
    is_active: bool = True
    is_default: bool = False


class DemoSiteTemplateUpdate(BaseModel):
    """Request to update a template."""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_type: Optional[str] = None
    description: Optional[str] = None
    html_template: Optional[str] = None
    css_template: Optional[str] = None
    js_template: Optional[str] = None
    preview_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    customization_options: Optional[Dict[str, Any]] = None
    default_meta_title: Optional[str] = None
    default_meta_description: Optional[str] = None
    default_meta_keywords: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DemoSiteTemplateResponse(BaseModel):
    """Response schema for template details."""
    id: int
    template_name: str
    template_type: str
    description: Optional[str] = None

    # Template code (optionally excluded for list views)
    html_template: Optional[str] = None
    css_template: Optional[str] = None
    js_template: Optional[str] = None

    # Preview
    preview_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    customization_options: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    is_active: bool
    is_default: bool
    usage_count: int = 0

    # SEO
    default_meta_title: Optional[str] = None
    default_meta_description: Optional[str] = None
    default_meta_keywords: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DemoSiteTemplateListResponse(BaseModel):
    """Response for list of templates."""
    total: int
    templates: List[DemoSiteTemplateResponse]


# ============================================================================
# Component Schemas
# ============================================================================

class DemoSiteComponentCreate(BaseModel):
    """Request to create a new component."""
    component_name: str = Field(..., min_length=1, max_length=255)
    component_type: str = Field(..., description="hero, features, testimonials, cta, footer, etc.")
    description: Optional[str] = None

    # Component code
    html_code: str = Field(..., min_length=1)
    css_code: Optional[str] = None
    js_code: Optional[str] = None

    # Preview
    preview_image: Optional[str] = None
    preview_html: Optional[str] = None

    # Metadata
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Customization
    required_data_fields: List[str] = Field(default_factory=list)
    optional_data_fields: List[str] = Field(default_factory=list)

    is_active: bool = True


class DemoSiteComponentUpdate(BaseModel):
    """Request to update a component."""
    component_name: Optional[str] = Field(None, min_length=1, max_length=255)
    component_type: Optional[str] = None
    description: Optional[str] = None
    html_code: Optional[str] = None
    css_code: Optional[str] = None
    js_code: Optional[str] = None
    preview_image: Optional[str] = None
    preview_html: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    required_data_fields: Optional[List[str]] = None
    optional_data_fields: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DemoSiteComponentResponse(BaseModel):
    """Response schema for component details."""
    id: int
    component_name: str
    component_type: str
    description: Optional[str] = None

    # Component code (optionally excluded for list views)
    html_code: Optional[str] = None
    css_code: Optional[str] = None
    js_code: Optional[str] = None

    # Preview
    preview_image: Optional[str] = None
    preview_html: Optional[str] = None

    # Metadata
    is_active: bool
    usage_count: int = 0
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Customization
    required_data_fields: List[str] = Field(default_factory=list)
    optional_data_fields: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DemoSiteComponentListResponse(BaseModel):
    """Response for list of components."""
    total: int
    components: List[DemoSiteComponentResponse]


# ============================================================================
# Analytics Schemas
# ============================================================================

class DemoSiteAnalyticsTrackRequest(BaseModel):
    """Request to track an analytics event (public endpoint)."""
    event_type: str = Field(..., description="page_view, cta_click, conversion, etc.")
    visitor_id: Optional[str] = None  # Anonymous visitor ID
    event_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DemoSiteAnalyticsResponse(BaseModel):
    """Response schema for daily analytics."""
    id: int
    demo_site_id: int
    date: date

    # Basic metrics
    page_views: int = 0
    unique_visitors: int = 0

    # Engagement
    avg_time_on_page: float = 0.0
    bounce_rate: float = 0.0

    # Conversions
    cta_clicks: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0

    # Detailed data
    analytics_data: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DemoSiteAnalyticsSummaryResponse(BaseModel):
    """Summary analytics for a demo site."""
    demo_site_id: int
    total_page_views: int
    total_unique_visitors: int
    total_cta_clicks: int
    total_conversions: int
    overall_conversion_rate: float
    avg_time_on_page: float
    avg_bounce_rate: float
    date_range: Dict[str, date]  # {"start": date, "end": date}
    daily_data: List[DemoSiteAnalyticsResponse]


class DemoSiteAnalyticsTimelineResponse(BaseModel):
    """Timeline analytics for a demo site."""
    demo_site_id: int
    timeline: List[DemoSiteAnalyticsResponse]
    date_range: Dict[str, date]


# ============================================================================
# Deployment Status Schema
# ============================================================================

class DeploymentStatusResponse(BaseModel):
    """Response for deployment status."""
    demo_site_id: int
    deployment_status: str
    vercel_deployment_id: Optional[str] = None
    vercel_url: Optional[str] = None
    progress: int = Field(0, ge=0, le=100, description="Deployment progress percentage")
    message: Optional[str] = None
    error_message: Optional[str] = None
    last_updated: datetime


# ============================================================================
# Bulk Operations Schemas
# ============================================================================

class DemoSiteDuplicateRequest(BaseModel):
    """Request to duplicate a demo site."""
    new_site_name: str = Field(..., min_length=1, max_length=255)
    new_lead_id: Optional[int] = None
    copy_content: bool = True
    copy_style: bool = True


class DemoSiteBulkDeleteRequest(BaseModel):
    """Request to delete multiple demo sites."""
    demo_site_ids: List[int] = Field(..., min_items=1)


class DemoSiteBulkStatusResponse(BaseModel):
    """Response for bulk operations."""
    success_count: int
    failure_count: int
    results: List[Dict[str, Any]]


# ============================================================================
# Deployment Schemas
# ============================================================================

class DeploymentResult(BaseModel):
    """Result of a demo site deployment operation."""
    success: bool
    deployment_url: Optional[str] = None
    deployment_id: Optional[str] = None
    deployment_domain: Optional[str] = None
    framework: Optional[str] = None  # vercel, netlify, github-pages, etc.

    # Deployment details
    build_time: Optional[int] = None  # Seconds
    deployment_time: Optional[int] = None  # Seconds
    total_files: Optional[int] = None
    total_size_bytes: Optional[int] = None

    # Status information
    status: Optional[str] = None  # building, ready, error, cancelled
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Environment details
    environment: Optional[str] = None  # production, preview, development
    branch: Optional[str] = None
    commit_sha: Optional[str] = None

    # Platform-specific metadata
    platform_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
