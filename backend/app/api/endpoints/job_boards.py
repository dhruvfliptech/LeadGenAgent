"""
Unified API endpoint for job board scraping.

Supports Indeed, Monster, and ZipRecruiter with a single interface.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import logging
from datetime import datetime

from playwright.async_api import async_playwright
from app.core.config import settings
from app.api.deps import get_db
from app.models.leads import Lead
from app.models.locations import Location
from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.monster_scraper import MonsterScraper
from app.scrapers.ziprecruiter_scraper import ZipRecruiterScraper


logger = logging.getLogger(__name__)
router = APIRouter()


class JobSource(str, Enum):
    """Supported job board sources."""
    INDEED = "indeed"
    MONSTER = "monster"
    ZIPRECRUITER = "ziprecruiter"
    ALL = "all"


class ScrapeJobBoardsRequest(BaseModel):
    """Request model for job board scraping."""

    source: JobSource = Field(
        ...,
        description="Job board to scrape (indeed, monster, ziprecruiter, or all)"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Job search query (e.g., 'python developer')",
        examples=["software engineer", "data analyst", "marketing manager"]
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Location for job search (e.g., 'San Francisco, CA')",
        examples=["San Francisco, CA", "New York, NY", "Remote"]
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of results per source"
    )
    enable_company_lookup: bool = Field(
        default=False,
        description="Enable company website and email discovery (slower but more data)"
    )
    save_to_database: bool = Field(
        default=True,
        description="Save scraped jobs to database as leads"
    )


class JobBoardStats(BaseModel):
    """Statistics for a scraping run."""
    source: str
    jobs_scraped: int
    errors_encountered: int
    captchas_detected: int
    rate_limits_hit: int
    duration_seconds: float


class ScrapeJobBoardsResponse(BaseModel):
    """Response model for job board scraping."""
    success: bool
    message: str
    total_jobs_scraped: int
    jobs_by_source: Dict[str, int]
    stats: List[JobBoardStats]
    jobs: Optional[List[Dict[str, Any]]] = None
    warnings: List[str] = []


@router.post("/scrape", response_model=ScrapeJobBoardsResponse)
async def scrape_job_boards(
    request: ScrapeJobBoardsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Scrape job boards for job postings.

    This endpoint supports scraping from Indeed, Monster, and ZipRecruiter.
    You can scrape a single source or all sources at once.

    **Important Notes:**
    - Job board scraping may trigger anti-bot detection
    - ZipRecruiter has the most aggressive bot protection
    - Consider using proxies for production use
    - Respect rate limits and use appropriate delays

    **Response:**
    - Returns list of scraped jobs
    - Optionally saves to database as leads
    - Includes scraping statistics and warnings
    """
    start_time = datetime.now()
    all_jobs = []
    jobs_by_source = {}
    all_stats = []
    warnings = []

    # Determine which sources to scrape
    sources_to_scrape = []
    if request.source == JobSource.ALL:
        # Check which sources are enabled
        if getattr(settings, 'INDEED_ENABLED', True):
            sources_to_scrape.append(JobSource.INDEED)
        if getattr(settings, 'MONSTER_ENABLED', True):
            sources_to_scrape.append(JobSource.MONSTER)
        if getattr(settings, 'ZIPRECRUITER_ENABLED', True):
            sources_to_scrape.append(JobSource.ZIPRECRUITER)
    else:
        # Check if specific source is enabled
        source_enabled = getattr(settings, f'{request.source.upper()}_ENABLED', True)
        if not source_enabled:
            raise HTTPException(
                status_code=400,
                detail=f"{request.source} is disabled in configuration"
            )
        sources_to_scrape.append(request.source)

    if not sources_to_scrape:
        raise HTTPException(
            status_code=400,
            detail="No job board sources are enabled. Check your configuration."
        )

    logger.info(f"Starting job board scraping: sources={sources_to_scrape}, query='{request.query}', location='{request.location}'")

    # Initialize Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Create browser context with anti-detection settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            # Scrape each source
            for source in sources_to_scrape:
                source_start = datetime.now()

                try:
                    # Create appropriate scraper
                    scraper = None
                    if source == JobSource.INDEED:
                        scraper = IndeedScraper(
                            browser=browser,
                            context=context,
                            enable_company_lookup=request.enable_company_lookup
                        )
                    elif source == JobSource.MONSTER:
                        scraper = MonsterScraper(
                            browser=browser,
                            context=context,
                            enable_company_lookup=request.enable_company_lookup
                        )
                    elif source == JobSource.ZIPRECRUITER:
                        scraper = ZipRecruiterScraper(
                            browser=browser,
                            context=context,
                            enable_company_lookup=request.enable_company_lookup
                        )

                    if not scraper:
                        logger.error(f"Failed to create scraper for {source}")
                        continue

                    # Scrape jobs
                    logger.info(f"Scraping {source}...")
                    jobs = await scraper.search_jobs(
                        query=request.query,
                        location=request.location,
                        max_results=request.max_results
                    )

                    # Collect stats
                    source_duration = (datetime.now() - source_start).total_seconds()
                    scraper_stats = scraper.get_stats()
                    all_stats.append(JobBoardStats(
                        source=source,
                        jobs_scraped=scraper_stats['jobs_scraped'],
                        errors_encountered=scraper_stats['errors_encountered'],
                        captchas_detected=scraper_stats['captchas_detected'],
                        rate_limits_hit=scraper_stats['rate_limits_hit'],
                        duration_seconds=source_duration
                    ))

                    # Add warnings if blocking was detected
                    if scraper_stats['captchas_detected'] > 0:
                        warnings.append(f"{source}: CAPTCHA detected - consider using 2Captcha integration")
                    if scraper_stats['rate_limits_hit'] > 0:
                        warnings.append(f"{source}: Rate limiting detected - reduce scraping frequency")

                    # Store results
                    all_jobs.extend(jobs)
                    jobs_by_source[source] = len(jobs)

                    logger.info(f"Completed {source}: {len(jobs)} jobs scraped")

                except Exception as e:
                    logger.error(f"Error scraping {source}: {str(e)}")
                    jobs_by_source[source] = 0
                    warnings.append(f"{source}: Scraping failed - {str(e)}")

        finally:
            await browser.close()

    # Save to database if requested
    if request.save_to_database and all_jobs:
        try:
            saved_count = await _save_jobs_to_database(db, all_jobs, request.location)
            logger.info(f"Saved {saved_count} jobs to database")
        except Exception as e:
            logger.error(f"Error saving jobs to database: {str(e)}")
            warnings.append(f"Database save failed: {str(e)}")

    # Calculate total duration
    total_duration = (datetime.now() - start_time).total_seconds()

    return ScrapeJobBoardsResponse(
        success=len(all_jobs) > 0,
        message=f"Successfully scraped {len(all_jobs)} jobs from {len(sources_to_scrape)} source(s)",
        total_jobs_scraped=len(all_jobs),
        jobs_by_source=jobs_by_source,
        stats=all_stats,
        jobs=all_jobs if len(all_jobs) <= 100 else None,  # Don't return all jobs if too many
        warnings=warnings
    )


async def _save_jobs_to_database(
    db: Session,
    jobs: List[Dict[str, Any]],
    location_name: str
) -> int:
    """
    Save scraped jobs to database as leads.

    Args:
        db: Database session
        jobs: List of job dictionaries
        location_name: Location name for lead association

    Returns:
        Number of jobs saved
    """
    saved_count = 0

    # Get or create location
    location = db.query(Location).filter(Location.name == location_name).first()
    if not location:
        location = Location(
            name=location_name,
            url="",  # Job boards don't have a single URL
            enabled=True
        )
        db.add(location)
        db.flush()

    for job in jobs:
        try:
            # Check if job already exists (by external_id and source)
            external_id = job.get('external_id')
            source = job.get('source')

            if external_id and source:
                existing = db.query(Lead).filter(
                    Lead.attributes.op('->>')('external_id') == external_id,
                    Lead.attributes.op('->>')('source') == source
                ).first()

                if existing:
                    logger.debug(f"Job {external_id} from {source} already exists, skipping")
                    continue

            # Create lead from job data
            lead = Lead(
                craigslist_id=f"{source}_{external_id or job.get('url', '')[:50]}",  # Unique ID
                url=job.get('url', ''),
                title=job.get('title', ''),
                description=job.get('description', ''),
                location_id=location.id,
                compensation=job.get('compensation'),
                employment_type=job.get('employment_type', []),
                is_remote=job.get('is_remote', False),
                posted_at=job.get('posted_date'),
                attributes={
                    'source': source,
                    'external_id': external_id,
                    'company_name': job.get('company_name'),
                    'company_website': job.get('company_website'),
                    'company_email': job.get('company_email'),
                    'job_location': job.get('location'),
                    **job.get('metadata', {})
                }
            )

            db.add(lead)
            saved_count += 1

        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            continue

    db.commit()
    return saved_count


@router.get("/sources")
async def get_enabled_sources():
    """
    Get list of enabled job board sources.

    Returns configuration status for each job board.
    """
    return {
        "sources": [
            {
                "name": "indeed",
                "enabled": getattr(settings, 'INDEED_ENABLED', True),
                "display_name": "Indeed",
                "description": "One of the largest job boards worldwide"
            },
            {
                "name": "monster",
                "enabled": getattr(settings, 'MONSTER_ENABLED', True),
                "display_name": "Monster",
                "description": "Major job board with diverse listings"
            },
            {
                "name": "ziprecruiter",
                "enabled": getattr(settings, 'ZIPRECRUITER_ENABLED', True),
                "display_name": "ZipRecruiter",
                "description": "Job aggregator with aggressive bot detection - use with caution"
            }
        ],
        "settings": {
            "default_delay_seconds": getattr(settings, 'JOB_SCRAPE_DELAY_SECONDS', 3),
            "max_results_per_source": getattr(settings, 'JOB_MAX_RESULTS_PER_SOURCE', 100),
            "company_lookup_enabled": getattr(settings, 'JOB_ENABLE_COMPANY_LOOKUP', True)
        }
    }


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_job_board_jobs(
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get scraped job board jobs from database.

    Args:
        source: Filter by source (indeed, monster, ziprecruiter) - optional
        limit: Maximum number of jobs to return (default: 50, max: 100)
        offset: Pagination offset (default: 0)
        db: Database session

    Returns:
        List of job board jobs with details
    """
    limit = min(limit, 100)  # Cap at 100

    query = db.query(Lead).filter(
        Lead.attributes.op('->>')('source').in_(
            [source] if source else ['indeed', 'monster', 'ziprecruiter']
        )
    )

    # Get total count
    total_count = query.count()

    # Get paginated results
    jobs = query.offset(offset).limit(limit).all()

    result = []
    for job in jobs:
        result.append({
            "id": job.id,
            "title": job.title,
            "company_name": job.attributes.get('company_name') if job.attributes else None,
            "location": job.neighborhood,
            "url": job.url,
            "description": job.description,
            "salary": job.compensation,
            "employment_type": job.employment_type,
            "is_remote": job.is_remote,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "source": job.attributes.get('source') if job.attributes else None,
            "status": job.status,
            "is_contacted": job.is_contacted,
            "attributes": job.attributes
        })

    return result


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_single_job_board_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get details of a single job board job.

    Args:
        job_id: Job ID from database
        db: Database session

    Returns:
        Detailed job information
    """
    job = db.query(Lead).filter(Lead.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job with id={job_id} not found"
        )

    # Verify it's a job board job (has source attribute)
    if not job.attributes or job.attributes.get('source') not in ['indeed', 'monster', 'ziprecruiter']:
        raise HTTPException(
            status_code=400,
            detail="This lead is not from a job board source"
        )

    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.attributes.get('company_name') if job.attributes else None,
        "company_email": job.attributes.get('company_email') if job.attributes else None,
        "company_website": job.attributes.get('company_website') if job.attributes else None,
        "location": job.neighborhood,
        "url": job.url,
        "description": job.description,
        "salary": job.compensation,
        "employment_type": job.employment_type,
        "is_remote": job.is_remote,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "source": job.attributes.get('source') if job.attributes else None,
        "external_id": job.attributes.get('external_id') if job.attributes else None,
        "status": job.status,
        "is_contacted": job.is_contacted,
        "is_processed": job.is_processed,
        "attributes": job.attributes,
        "created_at": job.created_at.isoformat() if hasattr(job, 'created_at') and job.created_at else None
    }


@router.get("/stats/{source}")
async def get_source_stats(source: JobSource, db: Session = Depends(get_db)):
    """
    Get statistics for jobs scraped from a specific source.

    Args:
        source: Job board source (indeed, monster, ziprecruiter)

    Returns:
        Statistics about scraped jobs from this source
    """
    if source == JobSource.ALL:
        raise HTTPException(status_code=400, detail="Please specify a specific source")

    # Query leads with this source
    leads = db.query(Lead).filter(
        Lead.attributes.op('->>')('source') == source
    ).all()

    # Calculate stats
    total_leads = len(leads)
    with_email = sum(1 for lead in leads if lead.attributes and lead.attributes.get('company_email'))
    with_website = sum(1 for lead in leads if lead.attributes and lead.attributes.get('company_website'))
    remote_jobs = sum(1 for lead in leads if lead.is_remote)
    contacted = sum(1 for lead in leads if lead.is_contacted)

    # Group by status
    status_counts = {}
    for lead in leads:
        status = lead.status
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "source": source,
        "total_leads": total_leads,
        "with_email": with_email,
        "with_website": with_website,
        "remote_jobs": remote_jobs,
        "contacted": contacted,
        "status_breakdown": status_counts,
        "email_discovery_rate": round(with_email / total_leads * 100, 2) if total_leads > 0 else 0,
        "website_discovery_rate": round(with_website / total_leads * 100, 2) if total_leads > 0 else 0
    }
