"""
Email Finder models for tracking API usage and found emails.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.models import Base


class EmailSource(str, enum.Enum):
    """Source of email discovery."""
    HUNTER_IO = "hunter_io"
    ROCKETREACH = "rocketreach"
    SCRAPED = "scraped"
    MANUAL = "manual"
    CRAIGSLIST = "craigslist"


class ServiceName(str, enum.Enum):
    """Email finding service names."""
    HUNTER_IO = "hunter_io"
    ROCKETREACH = "rocketreach"


class EmailFinderUsage(Base):
    """
    Track API usage for email finding services.
    Monitor quota consumption and prevent overage charges.
    """

    __tablename__ = "email_finder_usage"

    id = Column(Integer, primary_key=True, index=True)

    # Service details
    service = Column(SQLEnum(ServiceName), nullable=False, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Usage metrics
    requests_used = Column(Integer, default=0, nullable=False)
    quota_remaining = Column(Integer, nullable=True)
    quota_limit = Column(Integer, nullable=True)

    # Cost tracking
    cost = Column(Float, default=0.0, nullable=False)

    # Request details
    endpoint = Column(String(50), nullable=True)  # domain-search, email-finder, verify
    domain = Column(String(255), nullable=True, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Response metadata
    response_time_ms = Column(Integer, nullable=True)
    results_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<EmailFinderUsage(service={self.service}, date={self.date}, requests={self.requests_used}, remaining={self.quota_remaining})>"


class FoundEmail(Base):
    """
    Store emails found through various services.
    Track confidence scores and verification status.
    """

    __tablename__ = "found_emails"

    id = Column(Integer, primary_key=True, index=True)

    # Email details
    email = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)

    # Source information
    source = Column(SQLEnum(EmailSource), nullable=False, index=True)
    source_service_id = Column(Integer, ForeignKey("email_finder_usage.id"), nullable=True)

    # Contact information (if available)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True)
    phone_number = Column(String(50), nullable=True)

    # Quality metrics
    confidence_score = Column(Integer, nullable=True)  # 0-100 from Hunter.io
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_status = Column(String(50), nullable=True)  # valid, invalid, accept_all, etc.
    verification_score = Column(Integer, nullable=True)  # 0-100 from verification

    # Email characteristics
    is_generic = Column(Boolean, default=False, nullable=False)  # info@, contact@, etc.
    is_personal = Column(Boolean, default=False, nullable=False)
    is_disposable = Column(Boolean, default=False, nullable=False)
    is_webmail = Column(Boolean, default=False, nullable=False)

    # Social profiles
    linkedin_url = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)

    # Additional data
    sources = Column(JSON, nullable=True)  # List of sources where email was found
    extra_data = Column(JSON, nullable=True)  # Additional service-specific data (renamed from metadata)

    # Association with leads
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True, index=True)
    lead = relationship("Lead", backref="found_emails")

    # Usage tracking
    times_used = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<FoundEmail(email={self.email}, source={self.source}, confidence={self.confidence_score})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "email": self.email,
            "domain": self.domain,
            "source": self.source.value,
            "contact": {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "full_name": self.full_name,
                "position": self.position,
                "department": self.department,
                "seniority": self.seniority,
                "phone_number": self.phone_number
            },
            "quality": {
                "confidence_score": self.confidence_score,
                "is_verified": self.is_verified,
                "verification_status": self.verification_status,
                "verification_score": self.verification_score
            },
            "characteristics": {
                "is_generic": self.is_generic,
                "is_personal": self.is_personal,
                "is_disposable": self.is_disposable,
                "is_webmail": self.is_webmail
            },
            "social": {
                "linkedin_url": self.linkedin_url,
                "twitter_handle": self.twitter_handle
            },
            "usage": {
                "times_used": self.times_used,
                "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
            },
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
        }


class EmailFinderQuota(Base):
    """
    Track monthly quotas for email finding services.
    Prevent overage charges by monitoring limits.
    """

    __tablename__ = "email_finder_quotas"

    id = Column(Integer, primary_key=True, index=True)

    # Service and period
    service = Column(SQLEnum(ServiceName), nullable=False, unique=True, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12
    year = Column(Integer, nullable=False, index=True)

    # Quota limits
    quota_limit = Column(Integer, nullable=False)
    requests_used = Column(Integer, default=0, nullable=False)
    requests_remaining = Column(Integer, nullable=False)

    # Cost tracking
    total_cost = Column(Float, default=0.0, nullable=False)
    cost_per_request = Column(Float, default=0.0, nullable=False)

    # Alerts
    alert_threshold = Column(Integer, nullable=True)  # Alert when remaining < this
    alert_sent = Column(Boolean, default=False, nullable=False)

    # Plan information
    plan_name = Column(String(100), nullable=True)
    plan_level = Column(Integer, nullable=True)
    reset_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<EmailFinderQuota(service={self.service}, used={self.requests_used}/{self.quota_limit})>"

    @property
    def usage_percentage(self) -> float:
        """Calculate usage as percentage."""
        if self.quota_limit == 0:
            return 0.0
        return (self.requests_used / self.quota_limit) * 100

    @property
    def is_near_limit(self) -> bool:
        """Check if near quota limit (>80%)."""
        return self.usage_percentage >= 80

    @property
    def is_exceeded(self) -> bool:
        """Check if quota is exceeded."""
        return self.requests_used >= self.quota_limit

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "service": self.service.value,
            "period": f"{self.year}-{self.month:02d}",
            "quota": {
                "limit": self.quota_limit,
                "used": self.requests_used,
                "remaining": self.requests_remaining,
                "percentage": round(self.usage_percentage, 2)
            },
            "cost": {
                "total": self.total_cost,
                "per_request": self.cost_per_request
            },
            "alerts": {
                "threshold": self.alert_threshold,
                "sent": self.alert_sent,
                "near_limit": self.is_near_limit,
                "exceeded": self.is_exceeded
            },
            "plan": {
                "name": self.plan_name,
                "level": self.plan_level,
                "reset_date": self.reset_date.isoformat() if self.reset_date else None
            },
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
        }
