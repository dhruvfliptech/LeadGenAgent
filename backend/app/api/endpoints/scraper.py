"""
Scraper endpoints for managing scraping jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict
from pydantic import BaseModel
import redis
import json
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.locations import Location
import logging

logger = logging.getLogger(__name__)


class ScrapeJobCreate(BaseModel):
    location_ids: List[int]
    locations: Optional[List[Dict]] = None
    categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    max_pages: int = 5
    priority: str = "normal"  # low, normal, high
    enable_email_extraction: bool = False
    captcha_api_key: Optional[str] = None


class ScrapeJobResponse(BaseModel):
    job_id: str
    status: str
    location_ids: List[int]
    categories: Optional[List[str]]
    keywords: Optional[List[str]]
    max_pages: int
    priority: str
    enable_email_extraction: bool
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class ScrapeJobStatus(BaseModel):
    job_id: str
    status: str
    progress: int  # 0-100
    total_items: int
    processed_items: int
    errors: List[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    emails_extracted: int = 0
    captcha_cost: float = 0.0


router = APIRouter()

# Redis connection for job queue - optional for basic functionality
_redis_client = None
_redis_available = None

def get_redis_client():
    """
    Get Redis client, initializing if needed.
    Returns None if Redis is not configured (graceful degradation).
    """
    global _redis_client, _redis_available

    # Check if we already determined Redis is unavailable
    if _redis_available is False:
        return None

    # Try to initialize if not done yet
    if _redis_client is None and _redis_available is None:
        if not settings.REDIS_URL:
            logger.warning("Redis not configured - job queue and caching disabled")
            _redis_available = False
            return None

        try:
            _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            _redis_client.ping()  # Test connection
            _redis_available = True
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Job queue disabled.")
            _redis_available = False
            return None

    return _redis_client


# Safe Redis wrapper functions - handle None gracefully
def redis_get(key: str) -> Optional[str]:
    """Safe Redis GET - returns None if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return None
    try:
        return rc.get(key)
    except Exception as e:
        logger.error(f"Redis GET error for key '{key}': {e}")
        return None


def redis_setex(key: str, seconds: int, value: str) -> bool:
    """Safe Redis SETEX - returns False if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        rc.setex(key, seconds, value)
        return True
    except Exception as e:
        logger.error(f"Redis SETEX error for key '{key}': {e}")
        return False


def redis_hset(name: str, mapping: dict) -> bool:
    """Safe Redis HSET - returns False if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        rc.hset(name, mapping=mapping)
        return True
    except Exception as e:
        logger.error(f"Redis HSET error for '{name}': {e}")
        return False


def redis_hget(name: str, key: str) -> Optional[str]:
    """Safe Redis HGET - returns None if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return None
    try:
        return rc.hget(name, key)
    except Exception as e:
        logger.error(f"Redis HGET error for '{name}':'{key}': {e}")
        return None


def redis_lpush(name: str, *values) -> bool:
    """Safe Redis LPUSH - returns False if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        rc.lpush(name, *values)
        return True
    except Exception as e:
        logger.error(f"Redis LPUSH error for '{name}': {e}")
        return False


def redis_llen(name: str) -> int:
    """Safe Redis LLEN - returns 0 if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return 0
    try:
        return rc.llen(name)
    except Exception as e:
        logger.error(f"Redis LLEN error for '{name}': {e}")
        return 0


def redis_keys(pattern: str) -> List[str]:
    """Safe Redis KEYS - returns empty list if Redis unavailable."""
    rc = get_redis_client()
    if rc is None:
        return []
    try:
        return rc.keys(pattern)
    except Exception as e:
        logger.error(f"Redis KEYS error for pattern '{pattern}': {e}")
        return []


@router.get("/categories")
async def get_categories(
    location_id: Optional[int] = Query(None),
    refresh: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Discover Craigslist categories for a location and cache in Redis.
    If location_id is missing, return a global template.
    """
    cache_key = f"categories:location:{location_id or 'global'}"
    if not refresh:
        try:
            rc = get_redis_client()
            cached = rc.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass
        except HTTPException:
            # Redis not available, skip cache
            pass

    # Basic global fallback
    global_template: Dict[str, List[str]] = {
        "community": [
            "activities","artists","childcare","classes","events","general","groups","local news","lost & found","missed connections","musicians","pets","politics","rants & raves","rideshare","volunteers"
        ],
        "for sale": [
            "antiques","appliances","arts+crafts","atvs, utvs, snowmobiles","auto parts","aviation","baby+kid","barter","bicycle parts","bicycles","boat parts","boats","books","business","cars+trucks","cds/dvd/vhs","cell phones","clothing+acc","collectibles","computer parts","computers","electronics","farm+garden","free","furniture","garage sale","general","heavy equipment","household","jewelry","materials","motorcycle parts","motorcycles","music instr","photo+video","rvs+camp","sporting","tickets","tools","toys+games","trailers","video gaming","wanted","wheels+tires"
        ],
        "services": [
            "automotive","beauty","cell/mobile","computer","creative","cycle","event","farm+garden","financial","health/well","household","labor/move","legal","lessons","marine","pet","real estate","skilled trade","sm biz ads","travel/vac","write/ed/tran"
        ],
        "housing": [
            "apts / housing","housing swap","housing wanted","office / commercial","parking / storage","real estate for sale","rooms / shared","rooms wanted","sublets / temporary","vacation rentals"
        ],
        "jobs": [
            "accounting+finance","admin / office","arch / engineering","art / media / design","biotech / science","business / mgmt","customer service","education","etc / misc","food / bev / hosp","general labor","government","human resources","legal / paralegal","manufacturing","marketing / pr / ad","medical / health","nonprofit sector","real estate","retail / wholesale","sales / biz dev","salon/spa/fitness","security","skilled trade / craft","software / qa / dba","systems / network","technical support","transport","tv / film / video","web / info design","writing / editing"
        ],
        "gigs": [
            "computer","creative","crew","domestic","event","labor","talent","writing"
        ],
        "resumes": []
    }

    # For now return global; later we can fetch real per-location categories
    # Try to cache if Redis available
    redis_setex(cache_key, 86400, json.dumps(global_template))
    return global_template


@router.get("/categories/structured")
async def get_categories_structured():
    """Return human-readable categories organized like Craigslist sections.
    Each subcategory includes a slug suitable for directory browsing ("/d/{slug}").
    """
    def slugify(label: str) -> str:
        s = label.lower().strip()
        # normalize common separators
        s = s.replace(" & ", " and ")
        s = s.replace("/", " ")
        s = s.replace("+", " ")
        s = s.replace("'", "")
        # collapse spaces to hyphens
        s = "-".join([p for p in s.split() if p])
        return s

    data = {
        "community": [
            "activities","artists","childcare","classes","events","general","groups","local news",
            "lost+found","missed connections","musicians","pets","politics","rants & raves","rideshare","volunteers"
        ],
        "housing": [
            "apts / housing","housing swap","housing wanted","office / commercial","parking / storage",
            "real estate for sale","rooms / shared","rooms wanted","sublets / temporary","vacation rentals"
        ],
        "jobs": [
            "accounting+finance","admin / office","arch / engineering","art / media / design","biotech / science",
            "business / mgmt","customer service","education","etc / misc","food / bev / hosp","general labor",
            "government","human resources","legal / paralegal","manufacturing","marketing / pr / ad","medical / health",
            "nonprofit sector","real estate","retail / wholesale","sales / biz dev","salon / spa / fitness","security",
            "skilled trade / craft","software / qa / dba","systems / network","technical support","transport",
            "tv / film / video","web / info design","writing / editing"
        ],
        "services": [
            "automotive","beauty","cell/mobile","computer","creative","cycle","event","farm+garden","financial",
            "health/well","household","labor/move","legal","lessons","marine","pet","real estate","skilled trade",
            "sm biz ads","travel/vac","write/ed/tran"
        ],
        "for sale": [
            "antiques","appliances","arts+crafts","atv/utv/sno","auto parts","aviation","baby+kid","barter",
            "beauty+hlth","bike parts","bikes","boat parts","boats","books","business","cars+trucks",
            "cds/dvd/vhs","cell phones","clothes+acc","collectibles","computer parts","computers","electronics",
            "farm+garden","free","furniture","garage sale","general","heavy equip","household","jewelry",
            "materials","motorcycle parts","motorcycles","music instr","photo+video","rvs+camp","sporting","tickets",
            "tools","toys+games","trailers","video gaming","wanted","wheels+tires"
        ],
        "gigs": ["computer","creative","crew","domestic","event","labor","talent","writing"],
        "resumes": []
    }

    structured = {
        group: [{"name": label, "slug": slugify(label)} for label in labels]
        for group, labels in data.items()
    }
    return structured


@router.post("/jobs", response_model=ScrapeJobResponse)
async def create_scrape_job(
    job_data: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scraping job."""
    # Resolve locations: either IDs provided, or raw locations to upsert
    target_location_ids: List[int] = list(job_data.location_ids or [])
    
    if (not target_location_ids) and job_data.locations:
        # upsert by code
        codes = [str(loc.get('code')) for loc in job_data.locations if loc.get('code')]
        existing_result = await db.execute(select(Location).where(Location.code.in_(codes)))
        existing = {loc.code: loc for loc in existing_result.scalars().all()}
        to_create: List[Location] = []
        for loc in job_data.locations:
            code = str(loc.get('code'))
            if not code:
                continue
            if code in existing:
                continue
            to_create.append(Location(
                name=loc.get('name') or loc.get('label') or code,
                code=code,
                url=loc.get('url'),
                state=loc.get('state'),
                country=loc.get('country') or 'US',
                region=loc.get('region'),
                is_active=True,
            ))
        if to_create:
            db.add_all(to_create)
            await db.commit()
        # Re-fetch to ensure IDs
        final_result = await db.execute(select(Location).where(Location.code.in_(codes)))
        final_locs = final_result.scalars().all()
        target_location_ids = [l.id for l in final_locs]

    # Validate resulting IDs
    if not target_location_ids:
        raise HTTPException(status_code=400, detail="No valid locations provided")
    result = await db.execute(select(Location.id).where(Location.id.in_(target_location_ids)))
    found_ids = {row[0] for row in result.all()}
    if len(found_ids) != len(target_location_ids):
        raise HTTPException(status_code=400, detail="One or more invalid location IDs")
    
    # Create job ID
    job_id = f"scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(job_data.location_ids)) % 10000}"
    
    # Validate CAPTCHA API key if email extraction is enabled
    if job_data.enable_email_extraction and not job_data.captcha_api_key:
        if not settings.TWOCAPTCHA_API_KEY:
            raise HTTPException(
                status_code=400, 
                detail="CAPTCHA API key required for email extraction. Provide captcha_api_key or set TWOCAPTCHA_API_KEY environment variable."
            )
    
    # Create job data
    job_info = {
        "job_id": job_id,
        "status": "queued",
        "location_ids": target_location_ids,
        "categories": job_data.categories,
        "keywords": job_data.keywords,
        "max_pages": job_data.max_pages,
        "priority": job_data.priority,
        "enable_email_extraction": job_data.enable_email_extraction,
        "captcha_api_key": job_data.captcha_api_key or settings.TWOCAPTCHA_API_KEY,
        "created_at": datetime.now().isoformat(),
        "progress": 0,
        "total_items": 0,
        "processed_items": 0,
        "emails_extracted": 0,
        "captcha_cost": 0.0,
        "errors": []
    }
    
    # Store job in Redis
    redis_hset(f"scrape_job:{job_id}", mapping={
        "data": json.dumps(job_info, default=str)
    })
    
    # Add to job queue (priority queue based on priority)
    queue_name = f"scrape_queue:{job_data.priority}"
    redis_lpush(queue_name, job_id)
    
    # Start background processing (in a real implementation, this would be handled by Celery or RQ)
    # Pass a copy of job_data with resolved location_ids
    updated_job = ScrapeJobCreate(
        location_ids=target_location_ids,
        locations=None,
        categories=job_data.categories,
        keywords=job_data.keywords,
        max_pages=job_data.max_pages,
        priority=job_data.priority,
        enable_email_extraction=job_data.enable_email_extraction,
        captcha_api_key=job_data.captcha_api_key,
    )
    # Don't pass db session to background task - it will create its own
    background_tasks.add_task(process_scrape_job, job_id, updated_job)
    
    return ScrapeJobResponse(**job_info)


@router.get("/jobs/{job_id}", response_model=ScrapeJobStatus)
async def get_scrape_job_status(job_id: str):
    """Get status of a specific scraping job."""
    job_data = redis_hget(f"scrape_job:{job_id}", "data")
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = json.loads(job_data)
    # Ensure all required fields are present with defaults
    job_info.setdefault('errors', [])
    job_info.setdefault('started_at', None)
    job_info.setdefault('completed_at', None)
    job_info.setdefault('emails_extracted', 0)
    job_info.setdefault('captcha_cost', 0.0)
    job_info.setdefault('progress', 0)
    job_info.setdefault('total_items', 0)
    job_info.setdefault('processed_items', 0)
    return ScrapeJobStatus(**job_info)


@router.get("/jobs", response_model=List[ScrapeJobStatus])
async def get_scrape_jobs(
    status: Optional[str] = None,
    limit: int = 50
):
    """Get list of scraping jobs."""
    # Get all job keys
    job_keys = redis_keys("scrape_job:*")
    jobs = []
    
    for key in job_keys[:limit]:
        job_data = redis_hget(key, "data")
        if job_data:
            job_info = json.loads(job_data)
            if status is None or job_info.get("status") == status:
                # Ensure all required fields are present with defaults
                job_info.setdefault('errors', [])
                job_info.setdefault('started_at', None)
                job_info.setdefault('completed_at', None)
                job_info.setdefault('emails_extracted', 0)
                job_info.setdefault('captcha_cost', 0.0)
                job_info.setdefault('progress', 0)
                job_info.setdefault('total_items', 0)
                job_info.setdefault('processed_items', 0)
                jobs.append(ScrapeJobStatus(**job_info))
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.min, reverse=True)
    
    return jobs


@router.delete("/jobs/{job_id}")
async def cancel_scrape_job(job_id: str):
    """Cancel a scraping job."""
    job_data = redis_hget(f"scrape_job:{job_id}", "data")
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = json.loads(job_data)
    
    if job_info.get("status") in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel job in current status")
    
    # Update job status
    job_info["status"] = "cancelled"
    redis_hset(f"scrape_job:{job_id}", mapping={
        "data": json.dumps(job_info, default=str)
    })
    
    return {"message": "Job cancelled successfully"}


@router.get("/queue/status")
async def get_queue_status():
    """Get status of scraping queues."""
    queues = ["high", "normal", "low"]
    status = {}
    
    for queue in queues:
        queue_name = f"scrape_queue:{queue}"
        length = redis_llen(queue_name)
        status[queue] = length
    
    # Get active jobs
    active_jobs = redis_keys("scrape_job:*")
    active_count = 0
    
    for key in active_jobs:
        job_data = redis_hget(key, "data")
        if job_data:
            job_info = json.loads(job_data)
            if job_info.get("status") == "running":
                active_count += 1
    
    return {
        "queues": status,
        "active_jobs": active_count,
        "total_queued": sum(status.values())
    }


async def process_scrape_job(job_id: str, job_data: ScrapeJobCreate):
    """
    Background task to process scraping job.

    Creates its own database session (request session would be closed by the time this runs).
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # Load existing job_info from Redis to preserve all fields
            existing_job_data = redis_hget(f"scrape_job:{job_id}", "data")
            if existing_job_data:
                job_info = json.loads(existing_job_data)
            else:
                # Fallback if not found - reconstruct from job_data
                job_info = {
                    "job_id": job_id,
                    "location_ids": job_data.location_ids,
                    "categories": job_data.categories,
                    "keywords": job_data.keywords,
                    "max_pages": job_data.max_pages,
                    "enable_email_extraction": job_data.enable_email_extraction,
                    "captcha_api_key": job_data.captcha_api_key,
                    "errors": [],
                    "total_items": 0,
                    "processed_items": 0,
                    "emails_extracted": 0,
                    "captcha_cost": 0.0
                }

            # Update status fields only (preserve all other fields)
            job_info["status"] = "running"
            job_info["started_at"] = datetime.now().isoformat()
            job_info["progress"] = 0

            redis_hset(f"scrape_job:{job_id}", mapping={
                "data": json.dumps(job_info, default=str)
            })

            # Implement actual scraping logic
            from app.scrapers.craigslist_scraper import CraigslistScraper
            from app.models.locations import Location
            from app.models.leads import Lead
            from sqlalchemy import select

            # Get locations
            query = select(Location).where(Location.id.in_(job_data.location_ids))
            result = await db.execute(query)
            locations = result.scalars().all()

            total_leads = 0
            emails_extracted = 0
            captcha_cost = 0.0

            # Initialize scraper with email extraction if enabled
            captcha_api_key = job_info.get("captcha_api_key") if job_data.enable_email_extraction else None

            async with CraigslistScraper(
                captcha_api_key=captcha_api_key,
                enable_email_extraction=job_data.enable_email_extraction
            ) as scraper:

                for i, location in enumerate(locations):
                    try:
                        logger.info(f"Scraping location {location.name} ({location.url})")

                        # Update progress
                        progress = int((i / len(locations)) * 90)  # Reserve 10% for final processing
                        job_info["progress"] = progress
                        redis_hset(f"scrape_job:{job_id}", mapping={
                            "data": json.dumps(job_info, default=str)
                        })

                        # Scrape location with optional email extraction
                        leads_data = await scraper.scrape_location_with_emails(
                            location_url=location.url,
                            categories=job_data.categories,
                            keywords=job_data.keywords,
                            max_pages=job_data.max_pages,
                            extract_emails=job_data.enable_email_extraction
                        )

                        # Save leads to database
                        for lead_data in leads_data:
                            try:
                                # Check if lead already exists
                                existing_query = select(Lead).where(Lead.craigslist_id == lead_data.get('craigslist_id'))
                                existing_result = await db.execute(existing_query)
                                existing_lead = existing_result.scalar_one_or_none()

                                if existing_lead:
                                    # Update existing lead with email if extracted
                                    if lead_data.get('email') and not existing_lead.email:
                                        existing_lead.email = lead_data['email']
                                        emails_extracted += 1
                                        logger.info(f"Updated existing lead {existing_lead.id} with email")
                                else:
                                    # Create new lead with enhanced metadata
                                    lead = Lead(
                                        craigslist_id=lead_data.get('craigslist_id'),
                                        title=lead_data.get('title', ''),
                                        description=lead_data.get('description'),
                                        body_html=lead_data.get('body_html'),
                                        price=lead_data.get('price'),
                                        url=lead_data.get('url'),
                                        # Contact info
                                        email=lead_data.get('email'),
                                        phone=lead_data.get('phone'),
                                        contact_name=lead_data.get('contact_name'),
                                        reply_email=lead_data.get('reply_email'),
                                        reply_phone=lead_data.get('reply_phone'),
                                        reply_contact_name=lead_data.get('reply_contact_name'),
                                        # Location
                                        location_id=location.id,
                                        neighborhood=lead_data.get('neighborhood'),
                                        latitude=lead_data.get('latitude'),
                                        longitude=lead_data.get('longitude'),
                                        # Job details
                                        compensation=lead_data.get('compensation'),
                                        employment_type=lead_data.get('employment_type'),
                                        is_remote=lead_data.get('is_remote', False),
                                        is_internship=lead_data.get('is_internship', False),
                                        is_nonprofit=lead_data.get('is_nonprofit', False),
                                        # Media and attributes
                                        image_urls=lead_data.get('image_urls'),
                                        attributes=lead_data.get('attributes'),
                                        # Category
                                        category=job_data.categories[0] if job_data.categories else None,
                                        # Timestamps
                                        posted_at=lead_data.get('posted_at'),
                                        scraped_at=lead_data.get('scraped_at')
                                    )

                                    db.add(lead)
                                    total_leads += 1

                                    if lead_data.get('email') or lead_data.get('reply_email'):
                                        emails_extracted += 1

                                    logger.info(f"Created new lead: {lead.craigslist_id}")

                            except Exception as e:
                                logger.error(f"Error saving lead {lead_data.get('craigslist_id')}: {str(e)}")
                                job_info["errors"].append(f"Error saving lead: {str(e)}")

                        # Commit batch
                        await db.commit()

                        # Update statistics
                        job_info["total_items"] = total_leads
                        job_info["emails_extracted"] = emails_extracted

                        if job_data.enable_email_extraction:
                            captcha_cost = scraper.get_captcha_cost()
                            job_info["captcha_cost"] = captcha_cost

                    except Exception as e:
                        logger.error(f"Error scraping location {location.name}: {str(e)}")
                        job_info["errors"].append(f"Error scraping {location.name}: {str(e)}")

            # Final progress update
            job_info["progress"] = 100
            job_info["processed_items"] = total_leads

            # Mark as completed
            job_info["status"] = "completed"
            job_info["completed_at"] = datetime.now().isoformat()
            job_info["progress"] = 100

            redis_hset(f"scrape_job:{job_id}", mapping={
                "data": json.dumps(job_info, default=str)
            })

        except Exception as e:
            # Rollback on error
            await db.rollback()
            logger.error(f"Scrape job {job_id} failed: {e}")

            # Load existing job_info to preserve fields, or use fallback
            existing_job_data = redis_hget(f"scrape_job:{job_id}", "data")
            if existing_job_data:
                job_info = json.loads(existing_job_data)
            else:
                # Fallback if job_info was never loaded in try block
                job_info = {
                    "job_id": job_id,
                    "errors": []
                }

            # Update status fields to mark as failed
            job_info["status"] = "failed"
            job_info["error"] = str(e)
            job_info["completed_at"] = datetime.now().isoformat()
            # Add to errors list if it exists
            if "errors" in job_info:
                job_info["errors"].append(f"Fatal error: {str(e)}")

            redis_hset(f"scrape_job:{job_id}", mapping={
                "data": json.dumps(job_info, default=str)
            })