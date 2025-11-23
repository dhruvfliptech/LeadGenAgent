"""
Piloterr API Client for LinkedIn Job Scraping.

Piloterr is a web scraping API service that provides:
- LinkedIn job search scraping
- Built-in proxy rotation
- CAPTCHA handling
- Rate limiting management
- No ban risk

Pricing: Starting at $49/month (Premium plan)
- 18,000 credits/month
- 1 credit = 1 standard request
- 5 requests/second
- Email support

Documentation: https://www.piloterr.com/library/linkedin-job-search
"""

import logging
import asyncio
from typing import List, Dict, Optional, Literal
from datetime import datetime
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class PiloterrError(Exception):
    """Base exception for Piloterr API errors."""
    pass


class PiloterrRateLimitError(PiloterrError):
    """Raised when rate limit is exceeded."""
    pass


class PiloterrMaintenanceError(PiloterrError):
    """Raised when service is under maintenance."""
    pass


class PiloterrClient:
    """
    Async client for Piloterr LinkedIn scraping API.

    Features:
    - LinkedIn job search with filters
    - Company profile extraction
    - Automatic rate limiting
    - Quota management
    - Retry logic with exponential backoff
    """

    BASE_URL = "https://api.piloterr.com"

    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_per_minute: int = 60
    ):
        """
        Initialize Piloterr client.

        Args:
            api_key: Your Piloterr API key
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
            rate_limit_per_minute: Max requests per minute (default: 60)
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_per_minute = rate_limit_per_minute

        # Rate limiting state
        self._request_timestamps: List[float] = []

        # Usage tracking
        self.total_credits_used = 0
        self.total_requests_made = 0

        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": self.api_key,
                "User-Agent": "CraigLeads-Pro/2.0"
            }
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _check_rate_limit(self):
        """
        Check and enforce rate limiting.

        Implements a sliding window rate limiter to ensure we don't exceed
        the allowed requests per minute.
        """
        now = datetime.now().timestamp()

        # Remove timestamps older than 1 minute
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if now - ts < 60
        ]

        # Check if we've hit the limit
        if len(self._request_timestamps) >= self.rate_limit_per_minute:
            # Calculate how long to wait
            oldest_timestamp = self._request_timestamps[0]
            wait_time = 60 - (now - oldest_timestamp)

            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached. Waiting {wait_time:.2f} seconds..."
                )
                await asyncio.sleep(wait_time)

        # Add current timestamp
        self._request_timestamps.append(now)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        credits_per_request: int = 1
    ) -> Dict:
        """
        Make an API request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data
            credits_per_request: Expected credits consumed per request

        Returns:
            API response as dictionary

        Raises:
            PiloterrError: On API errors
            PiloterrRateLimitError: On rate limit exceeded
            PiloterrMaintenanceError: On service maintenance
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                # Check rate limit before making request
                await self._check_rate_limit()

                # Make request
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await self.client.post(url, params=params, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Track request
                self.total_requests_made += 1

                # Handle response
                if response.status_code == 200:
                    self.total_credits_used += credits_per_request
                    return response.json()

                elif response.status_code == 401:
                    raise PiloterrError("Invalid API key. Check your credentials.")

                elif response.status_code == 429:
                    # Rate limit exceeded on server side
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Server rate limit exceeded. Retrying after {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    continue

                elif response.status_code == 503:
                    # Service unavailable (maintenance)
                    error_msg = "LinkedIn Job Search API is currently under maintenance"
                    logger.error(error_msg)
                    raise PiloterrMaintenanceError(error_msg)

                else:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("message", response.text)
                    raise PiloterrError(
                        f"API request failed with status {response.status_code}: {error_msg}"
                    )

            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise PiloterrError("Request timed out after maximum retries")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                if attempt == self.max_retries - 1:
                    raise PiloterrError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)

        raise PiloterrError("Maximum retries exceeded")

    async def search_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        experience_level: Optional[Literal[
            "internship", "entry_level", "associate", "mid_senior", "director"
        ]] = None,
        job_type: Optional[Literal[
            "full_time", "part_time", "contract", "temporary", "internship", "volunteer"
        ]] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for LinkedIn jobs.

        NOTE: As of Nov 2025, this endpoint may be under maintenance.
        Check API status before relying on this in production.

        Args:
            keyword: Job search keyword (required)
            location: Job location (optional)
            experience_level: Filter by experience level
            job_type: Filter by job type
            max_results: Maximum number of results to return (default: 100)

        Returns:
            List of job dictionaries with fields:
                - id: LinkedIn job ID
                - title: Job title
                - url: LinkedIn job URL
                - list_date: Posting date
                - company_name: Company name
                - company_url: Company LinkedIn profile URL
                - location: Job location
                - description: Job description (if available)
                - salary: Salary information (if available)
                - job_type: Job type
                - experience_level: Experience level required

        Raises:
            PiloterrError: On API errors
            PiloterrMaintenanceError: If service is under maintenance
        """
        logger.info(f"Searching LinkedIn jobs: keyword='{keyword}', location='{location}'")

        params = {
            "keyword": keyword
        }

        if location:
            params["location"] = location
        if experience_level:
            params["experience_level"] = experience_level
        if job_type:
            params["job_type"] = job_type

        try:
            results = await self._make_request(
                method="GET",
                endpoint="/api/v2/linkedin/job/search",
                params=params,
                credits_per_request=1
            )

            # Piloterr returns an array of job objects
            if not isinstance(results, list):
                logger.warning(f"Unexpected response format: {type(results)}")
                return []

            # Limit results
            results = results[:max_results]

            logger.info(f"Found {len(results)} LinkedIn jobs")
            return results

        except PiloterrMaintenanceError:
            logger.error(
                "LinkedIn Job Search API is under maintenance. "
                "Please try again later or use an alternative service."
            )
            raise

    async def get_company_info(self, company_url: str) -> Optional[Dict]:
        """
        Get company information from LinkedIn company profile.

        NOTE: This uses the LinkedIn Company Scraper endpoint which may
        have different pricing (check Piloterr docs).

        Args:
            company_url: LinkedIn company profile URL

        Returns:
            Company information dictionary or None

        Example return:
            {
                "name": "Tech Corp",
                "description": "Leading tech company...",
                "website": "https://techcorp.com",
                "industry": "Technology",
                "company_size": "1000-5000 employees",
                "headquarters": "San Francisco, CA",
                "founded": 2010,
                "specialties": ["AI", "Cloud", "SaaS"]
            }
        """
        logger.info(f"Fetching company info: {company_url}")

        # Note: This endpoint path is hypothetical - update based on actual Piloterr API
        # You may need to use a different endpoint or service
        try:
            result = await self._make_request(
                method="GET",
                endpoint="/api/v2/linkedin/company",
                params={"url": company_url},
                credits_per_request=1
            )

            return result

        except Exception as e:
            logger.warning(f"Failed to fetch company info: {e}")
            return None

    async def extract_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Extract information from a LinkedIn profile.

        NOTE: This endpoint may be under maintenance. Check Piloterr status.
        Also note: This is typically more expensive (10 credits vs 1).

        Args:
            profile_url: LinkedIn profile URL

        Returns:
            Profile information dictionary or None

        Example return:
            {
                "name": "John Doe",
                "headline": "Senior Software Engineer at Tech Corp",
                "location": "San Francisco Bay Area",
                "current_company": "Tech Corp",
                "current_title": "Senior Software Engineer",
                "email": "john@techcorp.com",  # If available
                "phone": "+1-555-0123",  # If available
                "summary": "Experienced software engineer...",
                "experience": [...],
                "education": [...],
                "skills": [...]
            }
        """
        logger.info(f"Extracting profile: {profile_url}")

        try:
            result = await self._make_request(
                method="GET",
                endpoint="/api/v2/linkedin/profile",
                params={"url": profile_url},
                credits_per_request=10  # Profile scraping costs more
            )

            return result

        except PiloterrMaintenanceError:
            logger.warning("LinkedIn Profile scraper is under maintenance")
            return None
        except Exception as e:
            logger.warning(f"Failed to extract profile: {e}")
            return None

    def get_credits_used(self) -> int:
        """Get total credits used in this session."""
        return self.total_credits_used

    def get_requests_made(self) -> int:
        """Get total requests made in this session."""
        return self.total_requests_made

    def get_estimated_cost(self, plan: str = "premium") -> float:
        """
        Get estimated cost based on credits used.

        Args:
            plan: Piloterr plan name (premium, premium_plus, etc.)

        Returns:
            Estimated cost in USD
        """
        plan_costs = {
            "premium": {"monthly": 49, "credits": 18000},
            "premium_plus": {"monthly": 99, "credits": 40000},
            "startup": {"monthly": 249, "credits": 110000},
            "startup_plus": {"monthly": 499, "credits": 230000},
            "enterprise": {"monthly": 799, "credits": 390000},
            "enterprise_plus": {"monthly": 999, "credits": 530000}
        }

        if plan not in plan_costs:
            plan = "premium"

        cost_per_credit = plan_costs[plan]["monthly"] / plan_costs[plan]["credits"]
        return self.total_credits_used * cost_per_credit

    def reset_usage_tracking(self):
        """Reset usage tracking counters."""
        self.total_credits_used = 0
        self.total_requests_made = 0
        logger.info("Usage tracking reset")


# Factory function for easy instantiation
def create_piloterr_client(
    api_key: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
    rate_limit: Optional[int] = None
) -> PiloterrClient:
    """
    Create a Piloterr client with settings from config.

    Args:
        api_key: Override API key from settings
        timeout: Override timeout from settings
        max_retries: Override max retries from settings
        rate_limit: Override rate limit from settings

    Returns:
        Configured PiloterrClient instance
    """
    return PiloterrClient(
        api_key=api_key or getattr(settings, "LINKEDIN_API_KEY", ""),
        timeout=timeout or getattr(settings, "LINKEDIN_TIMEOUT_SECONDS", 30),
        max_retries=max_retries or getattr(settings, "LINKEDIN_RETRY_MAX_ATTEMPTS", 3),
        rate_limit_per_minute=rate_limit or getattr(settings, "LINKEDIN_RATE_LIMIT_PER_MINUTE", 60)
    )
