"""
Pydantic schemas for Email Finder API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator


class EmailFinderRequest(BaseModel):
    """Request to find emails for a domain."""
    domain: str = Field(..., description="Domain name (e.g., 'stripe.com')")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of emails to return")
    lead_id: Optional[int] = Field(None, description="Associate emails with this lead ID")


class PersonEmailRequest(BaseModel):
    """Request to find a specific person's email."""
    name: str = Field(..., description="Person's full name")
    domain: str = Field(..., description="Company domain")
    lead_id: Optional[int] = Field(None, description="Associate email with this lead ID")


class EmailVerificationRequest(BaseModel):
    """Request to verify an email address."""
    email: EmailStr = Field(..., description="Email address to verify")


class ContactInfo(BaseModel):
    """Contact information for an email."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    seniority: Optional[str] = None
    phone_number: Optional[str] = None


class QualityMetrics(BaseModel):
    """Quality metrics for an email."""
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Confidence score (0-100)")
    is_verified: bool = Field(False, description="Whether email has been verified")
    verification_status: Optional[str] = Field(None, description="Verification status")
    verification_score: Optional[int] = Field(None, ge=0, le=100, description="Verification score (0-100)")


class EmailCharacteristics(BaseModel):
    """Email characteristics."""
    is_generic: bool = Field(False, description="Generic email (info@, contact@, etc.)")
    is_personal: bool = Field(False, description="Personal email")
    is_disposable: bool = Field(False, description="Disposable email")
    is_webmail: bool = Field(False, description="Webmail (gmail, yahoo, etc.)")


class SocialProfiles(BaseModel):
    """Social media profiles."""
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None


class UsageInfo(BaseModel):
    """Usage information."""
    times_used: int = Field(0, description="Number of times this email was used")
    last_used_at: Optional[datetime] = Field(None, description="Last time this email was used")


class FoundEmailResponse(BaseModel):
    """Response for a found email."""
    id: int
    email: str
    domain: str
    source: str
    contact: ContactInfo
    quality: QualityMetrics
    characteristics: EmailCharacteristics
    social: SocialProfiles
    usage: UsageInfo
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True

    @classmethod
    def from_orm(cls, found_email):
        """Create from ORM model."""
        return cls(
            id=found_email.id,
            email=found_email.email,
            domain=found_email.domain,
            source=found_email.source.value,
            contact=ContactInfo(
                first_name=found_email.first_name,
                last_name=found_email.last_name,
                full_name=found_email.full_name,
                position=found_email.position,
                department=found_email.department,
                seniority=found_email.seniority,
                phone_number=found_email.phone_number
            ),
            quality=QualityMetrics(
                confidence_score=found_email.confidence_score,
                is_verified=found_email.is_verified,
                verification_status=found_email.verification_status,
                verification_score=found_email.verification_score
            ),
            characteristics=EmailCharacteristics(
                is_generic=found_email.is_generic,
                is_personal=found_email.is_personal,
                is_disposable=found_email.is_disposable,
                is_webmail=found_email.is_webmail
            ),
            social=SocialProfiles(
                linkedin_url=found_email.linkedin_url,
                twitter_handle=found_email.twitter_handle
            ),
            usage=UsageInfo(
                times_used=found_email.times_used,
                last_used_at=found_email.last_used_at
            ),
            created_at=found_email.created_at,
            updated_at=found_email.updated_at
        )


class EmailFinderResponse(BaseModel):
    """Response for domain email search."""
    domain: str
    emails: List[FoundEmailResponse]
    total_found: int
    sources_used: List[str]


class PersonEmailResponse(BaseModel):
    """Response for person email search."""
    name: str
    domain: str
    email: Optional[FoundEmailResponse]
    found: bool


class EmailVerificationResponse(BaseModel):
    """Response for email verification."""
    email: str
    valid: bool
    score: Optional[int] = Field(None, ge=0, le=100)
    result: Optional[str] = None
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class QuotaInfo(BaseModel):
    """Quota information."""
    limit: int
    used: int
    remaining: int
    percentage: float


class AlertInfo(BaseModel):
    """Alert information."""
    threshold: Optional[int] = None
    sent: bool = False
    near_limit: bool = False
    exceeded: bool = False


class PlanInfo(BaseModel):
    """Plan information."""
    name: Optional[str] = None
    level: Optional[int] = None
    reset_date: Optional[datetime] = None


class QuotaStatusResponse(BaseModel):
    """Response for quota status."""
    service: str
    period: Optional[str] = None
    quota: Optional[QuotaInfo] = None
    cost: Optional[Dict[str, float]] = None
    alerts: Optional[AlertInfo] = None
    plan: Optional[PlanInfo] = None
    configured: bool = True
    message: Optional[str] = None


class EmailFinderUsageStats(BaseModel):
    """Statistics for email finder usage."""
    total_emails_found: int
    by_source: Dict[str, int]
    by_confidence: Dict[str, int]
    quota_status: Dict[str, Dict[str, Any]]
