"""
Email Finder API endpoints.

Endpoints for finding, verifying, and managing emails.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.email_finder import EmailFinderService
from app.models.email_finder import ServiceName, EmailSource
from app.schemas.email_finder import (
    EmailFinderRequest,
    PersonEmailRequest,
    EmailVerificationRequest,
    EmailFinderResponse,
    PersonEmailResponse,
    EmailVerificationResponse,
    QuotaStatusResponse,
    FoundEmailResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-finder", tags=["email-finder"])


@router.post("/find-by-domain", response_model=EmailFinderResponse)
async def find_emails_by_domain(
    request: EmailFinderRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Find all emails for a domain.

    Uses multiple strategies:
    1. Check database cache
    2. Try Hunter.io (if quota available)
    3. Fallback to website scraping

    Args:
        request: Domain and optional filters
        db: Database session

    Returns:
        List of found emails with metadata

    Example:
        POST /api/v1/email-finder/find-by-domain
        {
            "domain": "stripe.com",
            "limit": 10,
            "lead_id": 123
        }

        Response:
        {
            "domain": "stripe.com",
            "emails": [
                {
                    "email": "john@stripe.com",
                    "source": "hunter_io",
                    "confidence_score": 95,
                    "is_generic": false,
                    ...
                }
            ],
            "total_found": 10,
            "sources_used": ["hunter_io", "scraped"]
        }
    """
    try:
        service = EmailFinderService(db)

        emails = await service.find_emails_by_domain(
            domain=request.domain,
            lead_id=request.lead_id,
            limit=request.limit
        )

        await service.close()

        # Get unique sources
        sources_used = list(set(email.source.value for email in emails))

        return EmailFinderResponse(
            domain=request.domain,
            emails=[FoundEmailResponse.from_orm(email) for email in emails],
            total_found=len(emails),
            sources_used=sources_used
        )

    except Exception as e:
        logger.error(f"Error finding emails for {request.domain}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-person", response_model=PersonEmailResponse)
async def find_person_email(
    request: PersonEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Find a specific person's email address.

    Args:
        request: Person's name and company domain
        db: Database session

    Returns:
        Found email with confidence score

    Example:
        POST /api/v1/email-finder/find-person
        {
            "name": "Patrick Collison",
            "domain": "stripe.com",
            "lead_id": 123
        }

        Response:
        {
            "name": "Patrick Collison",
            "domain": "stripe.com",
            "email": {
                "email": "patrick@stripe.com",
                "source": "hunter_io",
                "confidence_score": 95,
                ...
            },
            "found": true
        }
    """
    try:
        service = EmailFinderService(db)

        email = await service.find_person_email(
            name=request.name,
            domain=request.domain,
            lead_id=request.lead_id
        )

        await service.close()

        return PersonEmailResponse(
            name=request.name,
            domain=request.domain,
            email=FoundEmailResponse.from_orm(email) if email else None,
            found=email is not None
        )

    except Exception as e:
        logger.error(f"Error finding email for {request.name} at {request.domain}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify if an email address is valid and deliverable.

    Uses Hunter.io verification API if available,
    otherwise performs basic format validation.

    Args:
        request: Email to verify
        db: Database session

    Returns:
        Verification result with score

    Example:
        POST /api/v1/email-finder/verify
        {
            "email": "patrick@stripe.com"
        }

        Response:
        {
            "email": "patrick@stripe.com",
            "valid": true,
            "score": 95,
            "result": "deliverable",
            "details": {
                "regexp": true,
                "gibberish": false,
                "disposable": false,
                ...
            }
        }
    """
    try:
        service = EmailFinderService(db)

        verification = await service.verify_email(request.email)

        await service.close()

        return EmailVerificationResponse(**verification)

    except Exception as e:
        logger.error(f"Error verifying email {request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota/{service}", response_model=QuotaStatusResponse)
async def get_quota_status(
    service: ServiceName,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current quota status for an email finding service.

    Args:
        service: Service name (hunter_io, rocketreach)
        db: Database session

    Returns:
        Current quota usage and limits

    Example:
        GET /api/v1/email-finder/quota/hunter_io

        Response:
        {
            "service": "hunter_io",
            "period": "2025-11",
            "quota": {
                "limit": 100,
                "used": 45,
                "remaining": 55,
                "percentage": 45.0
            },
            "alerts": {
                "near_limit": false,
                "exceeded": false
            }
        }
    """
    try:
        email_service = EmailFinderService(db)

        quota_data = await email_service.get_quota_status(service)

        await email_service.close()

        return QuotaStatusResponse(**quota_data)

    except Exception as e:
        logger.error(f"Error getting quota status for {service}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[FoundEmailResponse])
async def get_email_history(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    source: Optional[EmailSource] = Query(None, description="Filter by source"),
    lead_id: Optional[int] = Query(None, description="Filter by lead ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get history of found emails with optional filters.

    Args:
        domain: Filter by domain
        source: Filter by source
        lead_id: Filter by lead ID
        limit: Results per page
        offset: Pagination offset
        db: Database session

    Returns:
        List of found emails

    Example:
        GET /api/v1/email-finder/history?domain=stripe.com&source=hunter_io&limit=20

        Response:
        [
            {
                "email": "john@stripe.com",
                "source": "hunter_io",
                "confidence_score": 95,
                ...
            }
        ]
    """
    try:
        from sqlalchemy import select, and_
        from app.models.email_finder import FoundEmail

        # Build query
        conditions = []
        if domain:
            conditions.append(FoundEmail.domain == domain)
        if source:
            conditions.append(FoundEmail.source == source)
        if lead_id:
            conditions.append(FoundEmail.lead_id == lead_id)

        if conditions:
            stmt = (
                select(FoundEmail)
                .where(and_(*conditions))
                .order_by(FoundEmail.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = (
                select(FoundEmail)
                .order_by(FoundEmail.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

        result = await db.execute(stmt)
        emails = result.scalars().all()

        return [FoundEmailResponse.from_orm(email) for email in emails]

    except Exception as e:
        logger.error(f"Error getting email history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get email finder statistics.

    Returns:
        Statistics about email finding usage

    Example:
        GET /api/v1/email-finder/stats

        Response:
        {
            "total_emails_found": 1234,
            "by_source": {
                "hunter_io": 800,
                "scraped": 400,
                "manual": 34
            },
            "by_confidence": {
                "high": 900,
                "medium": 250,
                "low": 84
            },
            "quota_status": {
                "hunter_io": {
                    "used": 45,
                    "remaining": 55,
                    "percentage": 45.0
                }
            }
        }
    """
    try:
        from sqlalchemy import select, func
        from app.models.email_finder import FoundEmail, EmailFinderQuota

        # Total emails
        total_stmt = select(func.count(FoundEmail.id))
        total_result = await db.execute(total_stmt)
        total_emails = total_result.scalar_one()

        # By source
        source_stmt = select(
            FoundEmail.source,
            func.count(FoundEmail.id)
        ).group_by(FoundEmail.source)
        source_result = await db.execute(source_stmt)
        by_source = {row[0].value: row[1] for row in source_result.all()}

        # By confidence level
        high_stmt = select(func.count(FoundEmail.id)).where(FoundEmail.confidence_score >= 70)
        medium_stmt = select(func.count(FoundEmail.id)).where(
            and_(FoundEmail.confidence_score >= 40, FoundEmail.confidence_score < 70)
        )
        low_stmt = select(func.count(FoundEmail.id)).where(FoundEmail.confidence_score < 40)

        high_result = await db.execute(high_stmt)
        medium_result = await db.execute(medium_stmt)
        low_result = await db.execute(low_stmt)

        by_confidence = {
            "high": high_result.scalar_one(),
            "medium": medium_result.scalar_one(),
            "low": low_result.scalar_one()
        }

        # Quota status
        quota_stmt = select(EmailFinderQuota)
        quota_result = await db.execute(quota_stmt)
        quotas = quota_result.scalars().all()

        quota_status = {}
        for quota in quotas:
            quota_status[quota.service.value] = {
                "used": quota.requests_used,
                "remaining": quota.requests_remaining,
                "percentage": round(quota.usage_percentage, 2),
                "near_limit": quota.is_near_limit,
                "exceeded": quota.is_exceeded
            }

        return {
            "total_emails_found": total_emails,
            "by_source": by_source,
            "by_confidence": by_confidence,
            "quota_status": quota_status
        }

    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
