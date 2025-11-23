"""
LinkedIn job scraping API endpoints.

This module provides REST API endpoints for LinkedIn job scraping using:
1. Piloterr API (Recommended) - $49/month, reliable, no ban risk
2. ScraperAPI - $299/month, high volume
3. DIY Selenium - Free but NOT RECOMMENDED (ban risk)

Endpoints:
- POST /api/v1/linkedin/scrape - Start job scraping
- GET /api/v1/linkedin/status/:job_id - Check scraping status
- GET /api/v1/linkedin/services - List available services and pricing
"""

import logging
import asyncio
from typing import Optional, Literal, List, Dict
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.config import settings
from app.models.leads import Lead
from app.models.locations import Location

# Import service clients
try:
    from app.integrations.piloterr_client import (
        create_piloterr_client,
        PiloterrError,
        PiloterrMaintenanceError
    )
except ImportError:
    create_piloterr_client = None
    PiloterrError = Exception
    PiloterrMaintenanceError = Exception

try:
    from app.integrations.scraperapi_client import (
        create_scraperapi_client,
        ScraperAPIError
    )
except ImportError:
    create_scraperapi_client = None
    ScraperAPIError = Exception

try:
    from app.scrapers.linkedin_scraper import (
        create_linkedin_scraper,
        LinkedInBanError,
        LinkedInCaptchaError
    )
except ImportError:
    create_linkedin_scraper = None
    LinkedInBanError = Exception
    LinkedInCaptchaError = Exception


logger = logging.getLogger(__name__)
router = APIRouter()


# In-memory job tracking (in production, use Redis or database)
scraping_jobs: Dict[str, Dict] = {}


# Request/Response Models

class LinkedInScrapeRequest(BaseModel):
    """Request model for LinkedIn job scraping."""

    keywords: List[str] = Field(
        ...,
        description="Job search keywords",
        example=["software engineer", "python developer"]
    )
    location: Optional[str] = Field(
        None,
        description="Job location",
        example="San Francisco, CA"
    )
    experience_level: Optional[Literal[
        "internship", "entry_level", "associate", "mid_senior", "director"
    ]] = Field(
        None,
        description="Filter by experience level"
    )
    job_type: Optional[Literal[
        "full_time", "part_time", "contract", "temporary", "internship", "volunteer"
    ]] = Field(
        None,
        description="Filter by job type"
    )
    max_results: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
    save_to_database: bool = Field(
        True,
        description="Save results to leads table"
    )
    location_id: Optional[int] = Field(
        None,
        description="Location ID to associate with leads (required if save_to_database=True)"
    )


class LinkedInScrapeResponse(BaseModel):
    """Response model for scrape initiation."""

    job_id: str = Field(..., description="Job ID for tracking")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")
    estimated_completion: Optional[str] = Field(
        None,
        description="Estimated completion time (ISO 8601)"
    )
    service_used: str = Field(..., description="Service used for scraping")


class LinkedInJobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str  # started, running, completed, failed
    jobs_found: int
    jobs_saved: int
    duplicates_skipped: int
    errors: int
    credits_used: Optional[int] = None
    cost_usd: Optional[float] = None
    started_at: str
    completed_at: Optional[str] = None
    service_used: str
    error_message: Optional[str] = None
    results_preview: Optional[List[Dict]] = None


class ServiceInfo(BaseModel):
    """Information about a scraping service."""

    name: str
    status: str  # available, unavailable, not_configured
    monthly_cost: Optional[str] = None
    capacity: Optional[str] = None
    reliability: str
    recommendation: str
    warnings: List[str] = []


# Helper Functions

def get_configured_service() -> str:
    """
    Get the configured LinkedIn scraping service.

    Returns:
        Service name: piloterr, scraperapi, selenium
    """
    if not getattr(settings, "LINKEDIN_ENABLED", False):
        raise HTTPException(
            status_code=503,
            detail="LinkedIn integration is not enabled. Set LINKEDIN_ENABLED=true in .env"
        )

    service = getattr(settings, "LINKEDIN_SERVICE", "piloterr").lower()

    # Validate service configuration
    if service == "piloterr":
        if not getattr(settings, "LINKEDIN_API_KEY", ""):
            raise HTTPException(
                status_code=500,
                detail="LINKEDIN_API_KEY not configured for Piloterr"
            )
    elif service == "scraperapi":
        if not getattr(settings, "LINKEDIN_API_KEY", ""):
            raise HTTPException(
                status_code=500,
                detail="LINKEDIN_API_KEY not configured for ScraperAPI"
            )
    elif service == "selenium":
        if not getattr(settings, "LINKEDIN_EMAIL", "") or not getattr(settings, "LINKEDIN_PASSWORD", ""):
            raise HTTPException(
                status_code=500,
                detail="LINKEDIN_EMAIL and LINKEDIN_PASSWORD required for Selenium scraper"
            )
        logger.warning(
            "⚠️ Using Selenium scraper. This is NOT recommended for production. "
            "High ban risk. Use Piloterr or ScraperAPI instead."
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Unknown LinkedIn service: {service}. Options: piloterr, scraperapi, selenium"
        )

    return service


async def scrape_with_piloterr(
    job_id: str,
    request: LinkedInScrapeRequest,
    db: AsyncSession
):
    """Background task to scrape using Piloterr."""
    scraping_jobs[job_id]["status"] = "running"

    try:
        async with create_piloterr_client() as client:
            all_jobs = []

            # Search for each keyword
            for keyword in request.keywords:
                try:
                    jobs = await client.search_jobs(
                        keyword=keyword,
                        location=request.location,
                        experience_level=request.experience_level,
                        job_type=request.job_type,
                        max_results=request.max_results
                    )

                    all_jobs.extend(jobs)

                    # Add delay between keyword searches
                    if len(request.keywords) > 1:
                        await asyncio.sleep(2)

                except PiloterrMaintenanceError:
                    scraping_jobs[job_id]["status"] = "failed"
                    scraping_jobs[job_id]["error_message"] = (
                        "LinkedIn Job Search API is under maintenance. "
                        "Please try again later or use an alternative service."
                    )
                    return
                except Exception as e:
                    logger.error(f"Error searching for '{keyword}': {e}")
                    scraping_jobs[job_id]["errors"] += 1

            # Save to database if requested
            jobs_saved = 0
            duplicates_skipped = 0

            if request.save_to_database and request.location_id:
                for job in all_jobs:
                    try:
                        # Check for duplicate
                        linkedin_id = f"linkedin_{job.get('id', job.get('url', '').split('/')[-1])}"

                        existing = await db.execute(
                            select(Lead).where(Lead.craigslist_id == linkedin_id)
                        )
                        if existing.scalar_one_or_none():
                            duplicates_skipped += 1
                            continue

                        # Create lead
                        lead = Lead(
                            craigslist_id=linkedin_id,
                            title=job.get("title", ""),
                            description=job.get("description"),
                            url=job.get("url", ""),
                            location_id=request.location_id,
                            neighborhood=job.get("location"),
                            compensation=job.get("salary"),
                            employment_type=[job.get("job_type")] if job.get("job_type") else None,
                            posted_at=datetime.fromisoformat(job["list_date"]) if job.get("list_date") else None,
                            attributes={
                                "company_name": job.get("company_name"),
                                "company_url": job.get("company_url"),
                                "experience_level": job.get("experience_level"),
                                "linkedin_job_id": job.get("id"),
                                "source": "linkedin"
                            },
                            status="new"
                        )

                        db.add(lead)
                        jobs_saved += 1

                    except Exception as e:
                        logger.error(f"Error saving job: {e}")
                        scraping_jobs[job_id]["errors"] += 1

                await db.commit()

            # Update job status
            scraping_jobs[job_id]["status"] = "completed"
            scraping_jobs[job_id]["jobs_found"] = len(all_jobs)
            scraping_jobs[job_id]["jobs_saved"] = jobs_saved
            scraping_jobs[job_id]["duplicates_skipped"] = duplicates_skipped
            scraping_jobs[job_id]["credits_used"] = client.get_credits_used()
            scraping_jobs[job_id]["cost_usd"] = client.get_estimated_cost()
            scraping_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            scraping_jobs[job_id]["results_preview"] = all_jobs[:5]

    except Exception as e:
        logger.error(f"Piloterr scraping failed: {e}")
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error_message"] = str(e)


async def scrape_with_scraperapi(
    job_id: str,
    request: LinkedInScrapeRequest,
    db: AsyncSession
):
    """Background task to scrape using ScraperAPI."""
    scraping_jobs[job_id]["status"] = "running"

    try:
        async with create_scraperapi_client() as client:
            all_jobs = []

            # Search for each keyword
            for keyword in request.keywords:
                keyword_str = " ".join([keyword]) if isinstance(keyword, list) else keyword

                try:
                    jobs = await client.search_linkedin_jobs(
                        keywords=keyword_str,
                        location=request.location,
                        max_results=min(request.max_results, 25)  # LinkedIn page size
                    )

                    all_jobs.extend(jobs)
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"Error searching for '{keyword}': {e}")
                    scraping_jobs[job_id]["errors"] += 1

            # Save to database (similar to Piloterr)
            jobs_saved = 0
            duplicates_skipped = 0

            if request.save_to_database and request.location_id:
                for job in all_jobs:
                    try:
                        linkedin_id = f"linkedin_{job.get('linkedin_job_id', 'unknown')}"

                        existing = await db.execute(
                            select(Lead).where(Lead.craigslist_id == linkedin_id)
                        )
                        if existing.scalar_one_or_none():
                            duplicates_skipped += 1
                            continue

                        lead = Lead(
                            craigslist_id=linkedin_id,
                            title=job.get("title", ""),
                            url=job.get("url", ""),
                            location_id=request.location_id,
                            neighborhood=job.get("location"),
                            attributes={
                                "company_name": job.get("company_name"),
                                "linkedin_job_id": job.get("linkedin_job_id"),
                                "source": "linkedin"
                            },
                            status="new"
                        )

                        db.add(lead)
                        jobs_saved += 1

                    except Exception as e:
                        logger.error(f"Error saving job: {e}")
                        scraping_jobs[job_id]["errors"] += 1

                await db.commit()

            # Update job status
            scraping_jobs[job_id]["status"] = "completed"
            scraping_jobs[job_id]["jobs_found"] = len(all_jobs)
            scraping_jobs[job_id]["jobs_saved"] = jobs_saved
            scraping_jobs[job_id]["duplicates_skipped"] = duplicates_skipped
            scraping_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            scraping_jobs[job_id]["results_preview"] = all_jobs[:5]

            usage = client.get_usage_stats()
            logger.info(f"ScraperAPI usage: {usage}")

    except Exception as e:
        logger.error(f"ScraperAPI scraping failed: {e}")
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error_message"] = str(e)


async def scrape_with_selenium(
    job_id: str,
    request: LinkedInScrapeRequest,
    db: AsyncSession
):
    """Background task to scrape using Selenium."""
    scraping_jobs[job_id]["status"] = "running"

    logger.warning(
        "⚠️ Using Selenium scraper. High ban risk. "
        "Limit to 10-20 jobs per day max."
    )

    try:
        async with create_linkedin_scraper() as scraper:
            all_jobs = []

            # Search for each keyword (limited)
            for keyword in request.keywords[:1]:  # Only first keyword to avoid bans
                keyword_str = " ".join([keyword]) if isinstance(keyword, list) else keyword

                try:
                    jobs = await scraper.search_jobs(
                        keywords=keyword_str,
                        location=request.location,
                        max_results=min(request.max_results, 20)  # Hard limit
                    )

                    all_jobs.extend(jobs)

                except (LinkedInBanError, LinkedInCaptchaError) as e:
                    logger.error(f"LinkedIn ban/captcha error: {e}")
                    scraping_jobs[job_id]["status"] = "failed"
                    scraping_jobs[job_id]["error_message"] = str(e)
                    return
                except Exception as e:
                    logger.error(f"Error searching for '{keyword}': {e}")
                    scraping_jobs[job_id]["errors"] += 1

            # Save to database
            jobs_saved = 0
            duplicates_skipped = 0

            if request.save_to_database and request.location_id:
                for job in all_jobs:
                    try:
                        linkedin_id = job.get("linkedin_job_id", f"linkedin_unknown_{datetime.now().timestamp()}")

                        existing = await db.execute(
                            select(Lead).where(Lead.craigslist_id == linkedin_id)
                        )
                        if existing.scalar_one_or_none():
                            duplicates_skipped += 1
                            continue

                        lead = Lead(
                            craigslist_id=linkedin_id,
                            title=job.get("title", ""),
                            url=job.get("url", ""),
                            location_id=request.location_id,
                            neighborhood=job.get("location"),
                            attributes={
                                "company_name": job.get("company_name"),
                                "linkedin_job_id": job.get("linkedin_job_id"),
                                "source": "linkedin",
                                "scraper": "selenium"
                            },
                            status="new"
                        )

                        db.add(lead)
                        jobs_saved += 1

                    except Exception as e:
                        logger.error(f"Error saving job: {e}")
                        scraping_jobs[job_id]["errors"] += 1

                await db.commit()

            # Update job status
            scraping_jobs[job_id]["status"] = "completed"
            scraping_jobs[job_id]["jobs_found"] = len(all_jobs)
            scraping_jobs[job_id]["jobs_saved"] = jobs_saved
            scraping_jobs[job_id]["duplicates_skipped"] = duplicates_skipped
            scraping_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            scraping_jobs[job_id]["results_preview"] = all_jobs[:5]

            usage = scraper.get_usage_stats()
            logger.warning(f"Selenium usage: {usage}")

    except Exception as e:
        logger.error(f"Selenium scraping failed: {e}")
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error_message"] = str(e)


# API Endpoints

@router.post("/scrape", response_model=LinkedInScrapeResponse)
async def start_linkedin_scrape(
    request: LinkedInScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start LinkedIn job scraping.

    This endpoint initiates a background job to scrape LinkedIn for job postings
    based on the provided search criteria.

    **Supported Services:**
    - Piloterr (Recommended): $49/month, 18K credits, no ban risk
    - ScraperAPI: $299/month, 600K requests, high reliability
    - Selenium (NOT RECOMMENDED): Free but high ban risk

    **Rate Limits:**
    - Piloterr: 5 requests/second (300/min)
    - ScraperAPI: Variable based on plan
    - Selenium: Max 10-20 jobs/day safely

    **Returns:**
    - job_id: Use this to check status via GET /status/:job_id
    """
    # Get configured service
    service = get_configured_service()

    # Validate location_id if saving to database
    if request.save_to_database and not request.location_id:
        raise HTTPException(
            status_code=400,
            detail="location_id is required when save_to_database=True"
        )

    # Verify location exists
    if request.location_id:
        location_result = await db.execute(
            select(Location).where(Location.id == request.location_id)
        )
        if not location_result.scalar_one_or_none():
            raise HTTPException(
                status_code=404,
                detail=f"Location with id={request.location_id} not found"
            )

    # Generate job ID
    import uuid
    job_id = f"linkedin_job_{uuid.uuid4().hex[:12]}"

    # Initialize job tracking
    scraping_jobs[job_id] = {
        "status": "started",
        "jobs_found": 0,
        "jobs_saved": 0,
        "duplicates_skipped": 0,
        "errors": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "service_used": service,
        "error_message": None
    }

    # Start background scraping task
    if service == "piloterr":
        background_tasks.add_task(scrape_with_piloterr, job_id, request, db)
    elif service == "scraperapi":
        background_tasks.add_task(scrape_with_scraperapi, job_id, request, db)
    elif service == "selenium":
        background_tasks.add_task(scrape_with_selenium, job_id, request, db)

    return LinkedInScrapeResponse(
        job_id=job_id,
        status="started",
        message=f"LinkedIn scraping job started using {service}",
        estimated_completion=(
            datetime.now().isoformat()
            if service == "selenium"
            else None
        ),
        service_used=service
    )


@router.get("/status/{job_id}", response_model=LinkedInJobStatusResponse)
async def get_scrape_status(job_id: str):
    """
    Get LinkedIn scraping job status.

    **Status values:**
    - started: Job has been queued
    - running: Job is actively scraping
    - completed: Job finished successfully
    - failed: Job encountered an error

    **Returns:**
    - Detailed job status including results count, errors, and cost
    """
    if job_id not in scraping_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id={job_id} not found"
        )

    job = scraping_jobs[job_id]

    return LinkedInJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        jobs_found=job["jobs_found"],
        jobs_saved=job["jobs_saved"],
        duplicates_skipped=job["duplicates_skipped"],
        errors=job["errors"],
        credits_used=job.get("credits_used"),
        cost_usd=job.get("cost_usd"),
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        service_used=job["service_used"],
        error_message=job.get("error_message"),
        results_preview=job.get("results_preview")
    )


@router.get("/services", response_model=List[ServiceInfo])
async def list_available_services():
    """
    List available LinkedIn scraping services with pricing and status.

    This endpoint helps you understand which services are configured and available,
    along with recommendations for each use case.
    """
    services = []

    # Piloterr
    piloterr_configured = bool(getattr(settings, "LINKEDIN_API_KEY", "") and
                                getattr(settings, "LINKEDIN_SERVICE", "") == "piloterr")

    services.append(ServiceInfo(
        name="Piloterr",
        status="available" if piloterr_configured else "not_configured",
        monthly_cost="$49 (Premium: 18K credits)",
        capacity="18,000 jobs/month",
        reliability="High",
        recommendation="Best for startups and small businesses",
        warnings=["LinkedIn Job Search API may be under maintenance"] if piloterr_configured else [
            "Not configured: Set LINKEDIN_SERVICE=piloterr and LINKEDIN_API_KEY in .env"
        ]
    ))

    # ScraperAPI
    scraperapi_configured = bool(getattr(settings, "LINKEDIN_API_KEY", "") and
                                  getattr(settings, "LINKEDIN_SERVICE", "") == "scraperapi")

    services.append(ServiceInfo(
        name="ScraperAPI",
        status="available" if scraperapi_configured else "not_configured",
        monthly_cost="$299 (Professional: 600K requests)",
        capacity="600,000 jobs/month",
        reliability="Very High",
        recommendation="Best for medium-to-large businesses with high volume",
        warnings=[] if scraperapi_configured else [
            "Not configured: Set LINKEDIN_SERVICE=scraperapi and LINKEDIN_API_KEY in .env"
        ]
    ))

    # Selenium
    selenium_configured = bool(
        getattr(settings, "LINKEDIN_EMAIL", "") and
        getattr(settings, "LINKEDIN_PASSWORD", "") and
        getattr(settings, "LINKEDIN_SERVICE", "") == "selenium"
    )

    services.append(ServiceInfo(
        name="Selenium (DIY)",
        status="available" if selenium_configured else "not_configured",
        monthly_cost="$50-200 (proxies + maintenance)",
        capacity="10-20 jobs/day safely",
        reliability="Low (50-70% success rate)",
        recommendation="NOT RECOMMENDED - Use Piloterr or ScraperAPI instead",
        warnings=[
            "⚠️ HIGH BAN RISK: LinkedIn actively blocks automated scraping",
            "⚠️ Account bans are often PERMANENT",
            "⚠️ Violates LinkedIn Terms of Service",
            "⚠️ Requires constant maintenance (HTML changes weekly)",
            "⚠️ Only use for testing or emergency backup",
            "⚠️ Max 10-20 jobs/day to avoid detection"
        ]
    ))

    return services


@router.get("/jobs", response_model=List[Dict])
async def get_linkedin_jobs(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    Get all LinkedIn jobs from database.

    Returns all jobs that were scraped from LinkedIn and stored as leads.

    Args:
        db: Database session
        limit: Maximum number of jobs to return (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        List of LinkedIn job leads
    """
    limit = min(limit, 100)  # Cap at 100

    # Query LinkedIn jobs from leads table
    query = select(Lead).where(
        Lead.attributes[("source")].astext == "linkedin"
    )

    # Get total count
    count_result = await db.execute(select(func.count()).select_from(Lead).where(
        Lead.attributes[("source")].astext == "linkedin"
    ))
    total_count = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    response = []
    for job in jobs:
        response.append({
            "id": job.id,
            "title": job.title,
            "company_name": job.attributes.get('company_name') if job.attributes else None,
            "company_url": job.attributes.get('company_url') if job.attributes else None,
            "location": job.neighborhood,
            "url": job.url,
            "description": job.description,
            "salary": job.compensation,
            "employment_type": job.employment_type,
            "is_remote": job.is_remote,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "experience_level": job.attributes.get('experience_level') if job.attributes else None,
            "status": job.status,
            "is_contacted": job.is_contacted,
            "linkedin_job_id": job.attributes.get('linkedin_job_id') if job.attributes else None
        })

    return response


@router.get("/jobs/{job_id}", response_model=Dict)
async def get_linkedin_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a single LinkedIn job.

    Args:
        job_id: Job ID from database
        db: Database session

    Returns:
        Detailed job information
    """
    result = await db.execute(select(Lead).where(Lead.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id={job_id} not found"
        )

    # Verify it's a LinkedIn job
    if not job.attributes or job.attributes.get('source') != 'linkedin':
        raise HTTPException(
            status_code=400,
            detail="This lead is not from LinkedIn"
        )

    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.attributes.get('company_name') if job.attributes else None,
        "company_url": job.attributes.get('company_url') if job.attributes else None,
        "location": job.neighborhood,
        "url": job.url,
        "description": job.description,
        "salary": job.compensation,
        "employment_type": job.employment_type,
        "is_remote": job.is_remote,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "experience_level": job.attributes.get('experience_level') if job.attributes else None,
        "status": job.status,
        "is_contacted": job.is_contacted,
        "is_processed": job.is_processed,
        "linkedin_job_id": job.attributes.get('linkedin_job_id') if job.attributes else None,
        "attributes": job.attributes,
        "created_at": job.created_at.isoformat() if hasattr(job, 'created_at') and job.created_at else None
    }


@router.delete("/jobs/{job_id}")
async def delete_scrape_job(job_id: str):
    """
    Delete a scraping job from tracking.

    This clears the job from memory but does NOT delete scraped leads from database.
    """
    if job_id not in scraping_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id={job_id} not found"
        )

    del scraping_jobs[job_id]

    return {"message": f"Job {job_id} deleted successfully"}
