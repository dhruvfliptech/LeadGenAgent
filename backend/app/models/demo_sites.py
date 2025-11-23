"""
Demo Sites Models for AI-Powered Demo Site Builder

This module contains SQLAlchemy models for the demo site builder system:
- DemoSite: Main demo site records with deployment info
- DemoSiteTemplate: Pre-built and custom templates
- DemoSiteAnalytics: Analytics and tracking data
- DemoSiteComponent: Reusable UI components
- DeploymentHistory: Deployment event tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
import enum


class DeploymentStatus(str, enum.Enum):
    """Deployment status values."""
    QUEUED = "queued"
    BUILDING = "building"
    READY = "ready"
    ERROR = "error"
    CANCELLED = "cancelled"


class DeploymentFramework(str, enum.Enum):
    """Supported deployment frameworks."""
    HTML = "html"
    REACT = "react"
    NEXTJS = "nextjs"
    VUE = "vue"
    SVELTE = "svelte"


class DemoSite(Base):
    """
    DemoSite model for tracking Vercel deployments.

    Stores information about demo sites deployed to Vercel for leads,
    including deployment metadata, URLs, and performance metrics.
    """

    __tablename__ = "demo_sites"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    lead = relationship("Lead", backref="demo_sites")

    # Template reference
    template_id = Column(Integer, ForeignKey("demo_site_templates.id"), nullable=True, index=True)
    template = relationship("DemoSiteTemplate", back_populates="demo_sites")

    # Vercel identifiers
    vercel_project_id = Column(String(255), nullable=True, index=True)
    vercel_deployment_id = Column(String(255), nullable=True, index=True)
    vercel_team_id = Column(String(255), nullable=True)  # For team accounts

    # Project details
    project_name = Column(String(255), nullable=False, index=True)
    framework = Column(String(50), nullable=False, index=True)  # html, react, nextjs, vue, svelte

    # Content and styling (AI-generated personalization)
    content_data = Column(JSON, nullable=True)  # Personalized content for the site
    style_settings = Column(JSON, nullable=True)  # Color scheme, fonts, etc.
    generated_html = Column(Text, nullable=True)  # Full AI-generated HTML
    generated_css = Column(Text, nullable=True)  # Full AI-generated CSS
    generated_js = Column(Text, nullable=True)  # Full AI-generated JS

    # URLs
    url = Column(Text, nullable=True)  # Production URL (e.g., demo-site-xxx.vercel.app)
    preview_url = Column(Text, nullable=True)  # Preview URL (e.g., demo-site-xxx-git-main.vercel.app)
    custom_domain = Column(String(255), nullable=True, index=True)  # Optional custom domain

    # Deployment status
    status = Column(String(50), default="queued", nullable=False, index=True)
    # Status values: queued, building, ready, error, cancelled

    # Build information
    build_time = Column(Float, nullable=True)  # Build time in seconds
    build_output = Column(Text, nullable=True)  # Build logs
    error_message = Column(Text, nullable=True)  # Error message if failed

    # Framework detection
    framework_detected = Column(String(50), nullable=True)  # Auto-detected framework

    # Deployment regions
    regions = Column(JSON, nullable=True)  # List of regions where deployed (e.g., ["sfo1", "iad1"])

    # Environment variables
    env_vars = Column(JSON, nullable=True)  # Environment variables used in deployment

    # Files metadata
    files_count = Column(Integer, nullable=True)  # Number of files deployed
    total_size_bytes = Column(Integer, nullable=True)  # Total size of deployed files

    # SSL/Security
    ssl_enabled = Column(Boolean, default=True, nullable=False)
    ssl_issued_at = Column(DateTime(timezone=True), nullable=True)

    # Performance metrics
    deployment_duration = Column(Float, nullable=True)  # Total deployment duration in seconds
    lambda_invocations = Column(Integer, default=0, nullable=False)  # Number of serverless invocations
    bandwidth_bytes = Column(Integer, default=0, nullable=False)  # Bandwidth used

    # Cost tracking
    estimated_cost = Column(Float, nullable=True)  # Estimated cost in USD
    actual_cost = Column(Float, nullable=True)  # Actual cost from Vercel billing

    # Analytics (summary counters)
    page_views = Column(Integer, default=0, nullable=False)
    unique_visitors = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships (analytics details in separate table)
    analytics = relationship("DemoSiteAnalytics", back_populates="demo_site", cascade="all, delete-orphan")

    # Deployment metadata
    deployment_metadata = Column(JSON, nullable=True)  # Additional metadata from Vercel
    build_metadata = Column(JSON, nullable=True)  # Build configuration and settings

    # Versioning
    version = Column(Integer, default=1, nullable=False)  # Deployment version number
    parent_deployment_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=True)  # Previous deployment

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)  # Soft delete

    # Flags
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    auto_deploy = Column(Boolean, default=False, nullable=False)  # Auto-redeploy on changes

    def __repr__(self):
        return f"<DemoSite(id={self.id}, lead_id={self.lead_id}, project_name='{self.project_name}', status='{self.status}')>"

    def to_dict(self):
        """Convert demo site to dictionary for API responses."""
        return {
            'id': self.id,
            'lead_id': self.lead_id,
            'vercel_project_id': self.vercel_project_id,
            'vercel_deployment_id': self.vercel_deployment_id,
            'vercel_team_id': self.vercel_team_id,
            'project_name': self.project_name,
            'framework': self.framework,
            'urls': {
                'url': self.url,
                'preview_url': self.preview_url,
                'custom_domain': self.custom_domain
            },
            'status': self.status,
            'build': {
                'build_time': self.build_time,
                'framework_detected': self.framework_detected,
                'files_count': self.files_count,
                'total_size_bytes': self.total_size_bytes,
                'deployment_duration': self.deployment_duration
            },
            'regions': self.regions or [],
            'ssl': {
                'enabled': self.ssl_enabled,
                'issued_at': self.ssl_issued_at.isoformat() if self.ssl_issued_at else None
            },
            'performance': {
                'lambda_invocations': self.lambda_invocations,
                'bandwidth_bytes': self.bandwidth_bytes,
                'page_views': self.page_views,
                'unique_visitors': self.unique_visitors,
                'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
            },
            'cost': {
                'estimated_cost': self.estimated_cost,
                'actual_cost': self.actual_cost
            },
            'version': self.version,
            'parent_deployment_id': self.parent_deployment_id,
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
                'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
            },
            'flags': {
                'is_active': self.is_active,
                'is_deleted': self.is_deleted,
                'auto_deploy': self.auto_deploy
            },
            'error_message': self.error_message if self.status == 'error' else None
        }


class DeploymentHistory(Base):
    """
    DeploymentHistory model for tracking deployment events and changes.

    Stores a log of all deployment events, status changes, and actions
    for audit and analytics purposes.
    """

    __tablename__ = "deployment_history"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)
    demo_site = relationship("DemoSite", backref="history")

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    # Event types: created, status_change, redeployed, updated, deleted, error

    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)

    # Event metadata
    event_data = Column(JSON, nullable=True)  # Additional event data
    error_details = Column(Text, nullable=True)  # Error details if applicable

    # User tracking (if applicable)
    user_id = Column(Integer, nullable=True)  # User who triggered the event

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<DeploymentHistory(id={self.id}, demo_site_id={self.demo_site_id}, event_type='{self.event_type}')>"

    def to_dict(self):
        """Convert deployment history to dictionary for API responses."""
        return {
            'id': self.id,
            'demo_site_id': self.demo_site_id,
            'event_type': self.event_type,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'event_data': self.event_data or {},
            'error_details': self.error_details,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DemoSiteTemplate(Base):
    """
    Templates for demo site generation.

    Templates contain HTML/CSS/JS code with placeholders for personalization.
    Supports multiple template types for different use cases.
    """
    __tablename__ = "demo_site_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template info
    template_name = Column(String(255), nullable=False, unique=True, index=True)
    template_type = Column(String(50), nullable=False, index=True)  # landing, portfolio, saas, custom
    description = Column(Text, nullable=True)

    # Template code (with Jinja2-style variables)
    html_template = Column(Text, nullable=False)  # HTML with {{variables}}
    css_template = Column(Text, nullable=False)  # CSS with variables
    js_template = Column(Text, nullable=True)  # Optional JavaScript

    # Preview and customization
    preview_image_url = Column(String(512), nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    customization_options = Column(JSON, nullable=False, default={})  # Available customization fields

    # Template metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)

    # SEO and meta
    default_meta_title = Column(String(255), nullable=True)
    default_meta_description = Column(Text, nullable=True)
    default_meta_keywords = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    demo_sites = relationship("DemoSite", back_populates="template")

    def __repr__(self):
        return f"<DemoSiteTemplate(id={self.id}, name='{self.template_name}', type='{self.template_type}')>"

    def to_dict(self):
        """Convert template to dictionary for API responses."""
        return {
            'id': self.id,
            'template_name': self.template_name,
            'template_type': self.template_type,
            'description': self.description,
            'preview_image_url': self.preview_image_url,
            'thumbnail_url': self.thumbnail_url,
            'customization_options': self.customization_options or {},
            'is_active': self.is_active,
            'is_default': self.is_default,
            'usage_count': self.usage_count,
            'default_meta_title': self.default_meta_title,
            'default_meta_description': self.default_meta_description,
            'default_meta_keywords': self.default_meta_keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DemoSiteAnalytics(Base):
    """
    Analytics data for demo sites.

    Tracks page views, engagement metrics, and conversions.
    Data is aggregated daily for efficient querying.
    """
    __tablename__ = "demo_site_analytics"

    id = Column(Integer, primary_key=True, index=True)
    demo_site_id = Column(Integer, ForeignKey("demo_sites.id"), nullable=False, index=True)

    # Date for daily aggregation
    date = Column(Date, nullable=False, index=True)

    # Basic metrics
    page_views = Column(Integer, default=0, nullable=False)
    unique_visitors = Column(Integer, default=0, nullable=False)

    # Engagement metrics
    avg_time_on_page = Column(Float, default=0.0, nullable=False)  # In seconds
    bounce_rate = Column(Float, default=0.0, nullable=False)  # Percentage

    # Conversion metrics
    cta_clicks = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    conversion_rate = Column(Float, default=0.0, nullable=False)  # Percentage

    # Detailed analytics data (JSON for flexibility)
    analytics_data = Column(JSON, nullable=False, default={})  # Referrers, devices, browsers, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    demo_site = relationship("DemoSite", back_populates="analytics")

    # Indexes for performance
    __table_args__ = (
        Index('idx_demo_analytics_site_date', 'demo_site_id', 'date'),
        Index('idx_demo_analytics_date_desc', date.desc()),
    )

    def __repr__(self):
        return f"<DemoSiteAnalytics(id={self.id}, demo_site_id={self.demo_site_id}, date={self.date}, views={self.page_views})>"

    def to_dict(self):
        """Convert analytics to dictionary for API responses."""
        return {
            'id': self.id,
            'demo_site_id': self.demo_site_id,
            'date': self.date.isoformat() if self.date else None,
            'page_views': self.page_views,
            'unique_visitors': self.unique_visitors,
            'avg_time_on_page': self.avg_time_on_page,
            'bounce_rate': self.bounce_rate,
            'cta_clicks': self.cta_clicks,
            'conversions': self.conversions,
            'conversion_rate': self.conversion_rate,
            'analytics_data': self.analytics_data or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DemoSiteComponent(Base):
    """
    Reusable UI components for building demo sites.

    Components are modular pieces (hero, features, testimonials, etc.)
    that can be mixed and matched in templates.
    """
    __tablename__ = "demo_site_components"

    id = Column(Integer, primary_key=True, index=True)

    # Component info
    component_name = Column(String(255), nullable=False, unique=True, index=True)
    component_type = Column(String(50), nullable=False, index=True)  # hero, features, testimonials, cta, footer, etc.
    description = Column(Text, nullable=True)

    # Component code
    html_code = Column(Text, nullable=False)  # HTML with variables
    css_code = Column(Text, nullable=True)  # Scoped CSS
    js_code = Column(Text, nullable=True)  # Optional JavaScript

    # Preview
    preview_image = Column(String(512), nullable=True)
    preview_html = Column(Text, nullable=True)  # Rendered preview

    # Component metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    category = Column(String(100), nullable=True, index=True)  # header, content, footer, form, etc.
    tags = Column(JSON, nullable=False, default=[])  # Search tags

    # Customization
    required_data_fields = Column(JSON, nullable=False, default=[])  # Required data fields
    optional_data_fields = Column(JSON, nullable=False, default=[])  # Optional data fields

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<DemoSiteComponent(id={self.id}, name='{self.component_name}', type='{self.component_type}')>"

    def to_dict(self):
        """Convert component to dictionary for API responses."""
        return {
            'id': self.id,
            'component_name': self.component_name,
            'component_type': self.component_type,
            'description': self.description,
            'preview_image': self.preview_image,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'category': self.category,
            'tags': self.tags or [],
            'required_data_fields': self.required_data_fields or [],
            'optional_data_fields': self.optional_data_fields or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
