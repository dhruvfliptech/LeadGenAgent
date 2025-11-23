"""
Google Maps scraping API endpoints.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, validator
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.leads import Lead
from app.models.locations import Location
from app.scrapers.google_maps_scraper import GoogleMapsScraper, GooglePlacesAPIScraper


logger = logging.getLogger(__name__)

router = APIRouter()


# In-memory job tracking (use Redis in production)
scraping_jobs = {}


class GoogleMapsScrapeRequest(BaseModel):
    """Request schema for Google Maps scraping."""

    query: str = Field(..., description="Search query (e.g., 'restaurants', 'plumbers', 'dentists')")
    location: str = Field(..., description="Location to search in (e.g., 'San Francisco, CA', 'New York, NY')")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results to scrape (1-100)")
    extract_emails: bool = Field(default=True, description="Whether to extract emails from business websites")
    use_places_api: bool = Field(default=False, description="Use Google Places API instead of scraping (requires API key)")
    location_id: Optional[int] = Field(default=None, description="Database location ID to associate leads with")

    @validator('query')
    def validate_query(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Query must be at least 2 characters')
        return v.strip()

    @validator('location')
    def validate_location(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Location must be at least 2 characters')
        return v.strip()


class GoogleMapsScrapeResponse(BaseModel):
    """Response schema for scrape initiation."""

    job_id: str
    status: str
    message: str
    estimated_time_seconds: int


class GoogleMapsJobStatus(BaseModel):
    """Response schema for job status."""

    job_id: str
    status: str  # pending, running, completed, failed
    progress: dict
    results_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Optional[List[dict]] = None


@router.post("/scrape", response_model=GoogleMapsScrapeResponse)
async def start_google_maps_scrape(
    request: GoogleMapsScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a Google Maps scraping job.

    This endpoint initiates an asynchronous scraping job that:
    1. Searches Google Maps for businesses matching the query and location
    2. Extracts business details (name, address, phone, website, rating, reviews)
    3. Optionally visits business websites to extract email addresses
    4. Stores results in the leads database

    **Rate Limiting**: Please be respectful with scraping. Recommended:
    - Max 20 results per request
    - Wait 5-10 minutes between requests
    - Use Google Places API for production use

    **Google Places API**: For production use, we recommend using the Google Places API
    which is more reliable and doesn't face rate limits. Enable with `use_places_api: true`
    and set `GOOGLE_PLACES_API_KEY` in your environment.
    """
    try:
        # Check if Google Maps scraping is enabled
        if not getattr(settings, 'GOOGLE_MAPS_ENABLED', True):
            raise HTTPException(
                status_code=403,
                detail="Google Maps scraping is disabled. Enable it in configuration."
            )

        # Check Places API key if using API mode
        if request.use_places_api:
            api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail="Google Places API key not configured. Set GOOGLE_PLACES_API_KEY in environment."
                )

        # Validate or create location
        location_id = request.location_id
        if not location_id:
            # Try to find or create location based on location string
            location_name = request.location
            location_code = location_name.lower().replace(' ', '_').replace(',', '')

            result = await db.execute(
                select(Location).where(Location.code == location_code)
            )
            location = result.scalar_one_or_none()

            if not location:
                # Create new location
                location = Location(
                    name=location_name,
                    code=location_code,
                    url=f"https://www.google.com/maps/place/{location_name.replace(' ', '+')}"
                )
                db.add(location)
                await db.commit()
                await db.refresh(location)

            location_id = location.id

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Estimate time (rough estimate)
        estimated_seconds = request.max_results * 3  # ~3 seconds per business
        if request.extract_emails:
            estimated_seconds += request.max_results * 5  # +5 seconds per email extraction

        # Create job record
        scraping_jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': {
                'total': request.max_results,
                'completed': 0,
                'current_action': 'Initializing...'
            },
            'results_count': 0,
            'created_at': datetime.now(),
            'completed_at': None,
            'error': None,
            'results': [],
            'request': request.dict()
        }

        # Start background task
        background_tasks.add_task(
            run_google_maps_scraping,
            job_id=job_id,
            request=request,
            location_id=location_id,
            db=db
        )

        logger.info(f"Started Google Maps scraping job: {job_id}")

        return GoogleMapsScrapeResponse(
            job_id=job_id,
            status='pending',
            message=f'Scraping job started for "{request.query}" in {request.location}',
            estimated_time_seconds=estimated_seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Google Maps scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping job: {str(e)}")


@router.get("/status/{job_id}", response_model=GoogleMapsJobStatus)
async def get_scraping_status(job_id: str, include_results: bool = Query(False)):
    """
    Check the status of a Google Maps scraping job.

    Args:
        job_id: The job ID returned from the /scrape endpoint
        include_results: Whether to include full results in response (can be large)

    Returns:
        Job status information including progress and results count
    """
    try:
        if job_id not in scraping_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job_data = scraping_jobs[job_id]

        # Remove results from response if not requested
        response_data = job_data.copy()
        if not include_results:
            response_data['results'] = None

        return GoogleMapsJobStatus(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/jobs", response_model=List[GoogleMapsJobStatus])
async def list_scraping_jobs(
    status: Optional[str] = Query(None, description="Filter by status (pending, running, completed, failed)"),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List recent Google Maps scraping jobs.

    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return

    Returns:
        List of recent scraping jobs
    """
    try:
        jobs = list(scraping_jobs.values())

        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j['status'] == status]

        # Sort by created_at descending
        jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)

        # Limit results
        jobs = jobs[:limit]

        # Remove results from response
        for job in jobs:
            job['results'] = None

        return [GoogleMapsJobStatus(**job) for job in jobs]

    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/{job_id}/results", response_model=List[dict])
async def get_scraping_results(job_id: str):
    """
    Get detailed results from a completed Google Maps scraping job.

    Args:
        job_id: The job ID returned from /scrape endpoint

    Returns:
        List of scraped businesses with full details
    """
    try:
        if job_id not in scraping_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job_data = scraping_jobs[job_id]

        # Only return results if job is completed
        if job_data['status'] != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Job is still {job_data['status']}. Results only available when completed."
            )

        results = job_data.get('results', [])
        if not results:
            return []

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a completed or failed scraping job.

    Args:
        job_id: The job ID to delete

    Returns:
        Success message
    """
    try:
        if job_id not in scraping_jobs:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        job_status = scraping_jobs[job_id]['status']
        if job_status in ['pending', 'running']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete job in '{job_status}' status. Wait for completion or failure."
            )

        del scraping_jobs[job_id]
        logger.info(f"Deleted job: {job_id}")

        return {"message": f"Job {job_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


async def run_google_maps_scraping(
    job_id: str,
    request: GoogleMapsScrapeRequest,
    location_id: int,
    db: AsyncSession
):
    """
    Background task to run Google Maps scraping.

    Args:
        job_id: Unique job identifier
        request: Scraping request parameters
        location_id: Database location ID
        db: Database session
    """
    try:
        # Update job status
        scraping_jobs[job_id]['status'] = 'running'
        scraping_jobs[job_id]['progress']['current_action'] = 'Starting scraper...'

        logger.info(f"Running Google Maps scraping job {job_id}")

        # Choose scraper based on request
        if request.use_places_api:
            # Use Google Places API
            api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '')
            async with GooglePlacesAPIScraper(api_key=api_key) as scraper:
                scraping_jobs[job_id]['progress']['current_action'] = 'Searching via Google Places API...'

                businesses = await scraper.search_businesses(
                    query=request.query,
                    location=request.location,
                    max_results=request.max_results
                )
        else:
            # Use Playwright scraper
            async with GoogleMapsScraper(
                headless=True,
                enable_email_extraction=request.extract_emails
            ) as scraper:
                scraping_jobs[job_id]['progress']['current_action'] = 'Searching Google Maps...'

                businesses = await scraper.search_businesses(
                    query=request.query,
                    location=request.location,
                    max_results=request.max_results
                )

        logger.info(f"Job {job_id}: Found {len(businesses)} businesses")

        # Store businesses in database
        scraping_jobs[job_id]['progress']['current_action'] = 'Saving to database...'

        lead_count = 0
        for idx, business in enumerate(businesses):
            try:
                # Create unique identifier from Google Maps URL or name
                google_maps_url = business.get('google_maps_url', '')
                business_name = business.get('name', '')

                # Generate a unique craigslist_id (reusing field for consistency)
                # Format: gmaps_<hash>
                import hashlib
                unique_string = f"{google_maps_url}_{business_name}_{request.location}"
                unique_hash = hashlib.md5(unique_string.encode()).hexdigest()[:12]
                unique_id = f"gmaps_{unique_hash}"

                # Check if lead already exists
                result = await db.execute(
                    select(Lead).where(Lead.craigslist_id == unique_id)
                )
                existing_lead = result.scalar_one_or_none()

                if existing_lead:
                    logger.info(f"Lead already exists: {business_name}")
                    continue

                # Create new lead
                lead = Lead(
                    craigslist_id=unique_id,
                    title=business_name,
                    description=business.get('category', ''),
                    url=google_maps_url,
                    location_id=location_id,
                    source='google_maps',  # Set proper source
                    category=business.get('category'),
                    email=business.get('email'),
                    phone=business.get('phone'),
                    reply_email=business.get('email'),
                    reply_phone=business.get('phone'),
                    neighborhood=business.get('address'),
                    latitude=business.get('latitude'),
                    longitude=business.get('longitude'),
                    status='new',
                    is_processed=False,
                    is_contacted=False,
                    # Store Google Maps specific data in attributes
                    attributes={
                        'rating': business.get('rating'),
                        'review_count': business.get('review_count'),
                        'business_hours': business.get('business_hours'),
                        'website': business.get('website'),
                        'address': business.get('address'),
                        'place_id': business.get('place_id')
                    },
                    scraped_at=business.get('scraped_at', datetime.now())
                )

                db.add(lead)
                lead_count += 1

                # Update progress
                scraping_jobs[job_id]['progress']['completed'] = idx + 1
                scraping_jobs[job_id]['progress']['current_action'] = f'Saved {lead_count}/{len(businesses)} businesses'

            except Exception as e:
                logger.error(f"Error saving business {business.get('name')}: {str(e)}")
                continue

        # Commit all leads
        await db.commit()

        # Update job status
        scraping_jobs[job_id]['status'] = 'completed'
        scraping_jobs[job_id]['results_count'] = lead_count
        scraping_jobs[job_id]['completed_at'] = datetime.now()
        scraping_jobs[job_id]['progress']['current_action'] = 'Completed'
        scraping_jobs[job_id]['results'] = [
            {
                'name': b.get('name'),
                'phone': b.get('phone'),
                'email': b.get('email'),
                'website': b.get('website'),
                'rating': b.get('rating'),
                'review_count': b.get('review_count')
            }
            for b in businesses
        ]

        logger.info(f"Job {job_id} completed successfully. Saved {lead_count} leads.")

    except Exception as e:
        logger.error(f"Error in scraping job {job_id}: {str(e)}")

        scraping_jobs[job_id]['status'] = 'failed'
        scraping_jobs[job_id]['error'] = str(e)
        scraping_jobs[job_id]['completed_at'] = datetime.now()
        scraping_jobs[job_id]['progress']['current_action'] = f'Failed: {str(e)}'


# Health check endpoint
@router.get("/health")
async def health_check():
    """Check if Google Maps scraping is available."""
    return {
        'status': 'ok',
        'google_maps_enabled': getattr(settings, 'GOOGLE_MAPS_ENABLED', True),
        'places_api_configured': bool(getattr(settings, 'GOOGLE_PLACES_API_KEY', None)),
        'max_results_limit': getattr(settings, 'GOOGLE_MAPS_MAX_RESULTS', 100),
        'scrape_timeout': getattr(settings, 'GOOGLE_MAPS_SCRAPE_TIMEOUT', 300)
    }
