"""
Website Analysis models for storing AI-powered website analysis results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.models import Base
from enum import Enum


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"


class AnalysisStatus(str, Enum):
    """Analysis processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WebsiteAnalysis(Base):
    """
    Store comprehensive website analysis results.

    Includes AI-powered analysis of:
    - Design (color scheme, typography, layout)
    - SEO (meta tags, headers, structure)
    - Performance (load time, optimization)
    - Accessibility (ARIA, keyboard nav, contrast)
    """

    __tablename__ = "website_analyses"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Website information
    url = Column(Text, nullable=False, index=True)
    domain = Column(String(255), nullable=True, index=True)
    title = Column(Text, nullable=True)

    # Analysis metadata
    status = Column(String(50), default=AnalysisStatus.PENDING, nullable=False, index=True)
    depth = Column(String(50), default=AnalysisDepth.COMPREHENSIVE, nullable=False)
    ai_model = Column(String(100), nullable=True)  # Model used for analysis

    # Overall scores (0-100)
    overall_score = Column(Float, nullable=True, index=True)
    design_score = Column(Float, nullable=True, index=True)
    seo_score = Column(Float, nullable=True, index=True)
    performance_score = Column(Float, nullable=True, index=True)
    accessibility_score = Column(Float, nullable=True, index=True)

    # Detailed category analysis (JSONB for flexible structure)
    design_analysis = Column(JSONB, nullable=True)  # Color scheme, typography, layout
    seo_analysis = Column(JSONB, nullable=True)  # Meta tags, headers, structure
    performance_analysis = Column(JSONB, nullable=True)  # Load time, bundle size
    accessibility_analysis = Column(JSONB, nullable=True)  # ARIA, keyboard nav

    # Improvement recommendations (array of structured recommendations)
    improvements = Column(JSONB, nullable=True)

    # Technical metrics
    page_load_time_ms = Column(Integer, nullable=True)
    page_size_kb = Column(Integer, nullable=True)
    num_requests = Column(Integer, nullable=True)
    num_images = Column(Integer, nullable=True)
    num_scripts = Column(Integer, nullable=True)
    num_stylesheets = Column(Integer, nullable=True)

    # Content metrics
    word_count = Column(Integer, nullable=True)
    heading_count = Column(Integer, nullable=True)
    link_count = Column(Integer, nullable=True)

    # SEO-specific fields
    meta_title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    has_favicon = Column(Boolean, default=False)
    has_robots_txt = Column(Boolean, default=False)
    has_sitemap = Column(Boolean, default=False)
    is_mobile_friendly = Column(Boolean, default=False)
    has_ssl = Column(Boolean, default=False)

    # Screenshot
    screenshot_url = Column(Text, nullable=True)
    screenshot_path = Column(Text, nullable=True)

    # Raw data (for debugging/re-analysis)
    html_content = Column(Text, nullable=True)  # Stored compressed
    lighthouse_data = Column(JSONB, nullable=True)  # Raw Lighthouse results

    # Error handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)

    # Cost tracking
    ai_cost = Column(Float, nullable=True)  # Cost of AI analysis
    processing_time_seconds = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<WebsiteAnalysis(id={self.id}, url='{self.url[:50]}...', overall_score={self.overall_score}, status='{self.status}')>"

    def to_dict(self):
        """Convert analysis to dictionary for API responses."""
        return {
            'id': self.id,
            'url': self.url,
            'domain': self.domain,
            'title': self.title,
            'status': self.status,
            'depth': self.depth,
            'ai_model': self.ai_model,
            'scores': {
                'overall': self.overall_score,
                'design': self.design_score,
                'seo': self.seo_score,
                'performance': self.performance_score,
                'accessibility': self.accessibility_score
            },
            'analysis': {
                'design': self.design_analysis,
                'seo': self.seo_analysis,
                'performance': self.performance_analysis,
                'accessibility': self.accessibility_analysis
            },
            'improvements': self.improvements or [],
            'metrics': {
                'page_load_time_ms': self.page_load_time_ms,
                'page_size_kb': self.page_size_kb,
                'num_requests': self.num_requests,
                'num_images': self.num_images,
                'num_scripts': self.num_scripts,
                'num_stylesheets': self.num_stylesheets,
                'word_count': self.word_count,
                'heading_count': self.heading_count,
                'link_count': self.link_count
            },
            'seo': {
                'meta_title': self.meta_title,
                'meta_description': self.meta_description,
                'has_favicon': self.has_favicon,
                'has_robots_txt': self.has_robots_txt,
                'has_sitemap': self.has_sitemap,
                'is_mobile_friendly': self.is_mobile_friendly,
                'has_ssl': self.has_ssl
            },
            'screenshot_url': self.screenshot_url,
            'error': {
                'message': self.error_message,
                'code': self.error_code
            } if self.error_message else None,
            'cost': {
                'ai_cost': self.ai_cost,
                'processing_time_seconds': self.processing_time_seconds
            },
            'timestamps': {
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None
            }
        }
