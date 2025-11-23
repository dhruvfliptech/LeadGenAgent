"""
ScraperAPI Client for LinkedIn Job Scraping.

ScraperAPI is a web scraping API that provides:
- Automatic proxy rotation (40M+ IPs)
- CAPTCHA solving
- JavaScript rendering
- Geotargeting (150+ countries)
- 99.9% uptime guarantee

Pricing: Starting at $49/month (Hobby plan)
- $299/month (Professional): 600,000 requests
- Flat monthly pricing (no credit system)
- Pay only for successful requests
- JS rendering included

Documentation: https://docs.scraperapi.com
"""

import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperAPIError(Exception):
    """Base exception for ScraperAPI errors."""
    pass


class ScraperAPIClient:
    """
    Async client for ScraperAPI.

    ScraperAPI doesn't provide structured LinkedIn endpoints like Piloterr,
    but it can scrape LinkedIn pages with better reliability than DIY.

    Usage:
        1. Scrape LinkedIn job search results page
        2. Parse HTML to extract job listings
        3. Scrape individual job pages for details
    """

    BASE_URL = "http://api.scraperapi.com/"

    def __init__(
        self,
        api_key: str,
        timeout: int = 60,
        max_retries: int = 3,
        render_js: bool = True,
        country_code: str = "us"
    ):
        """
        Initialize ScraperAPI client.

        Args:
            api_key: Your ScraperAPI key
            timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts (default: 3)
            render_js: Enable JavaScript rendering (default: True)
            country_code: Geolocation country code (default: "us")
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.render_js = render_js
        self.country_code = country_code

        # Usage tracking
        self.total_requests_made = 0
        self.successful_requests = 0
        self.failed_requests = 0

        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def scrape_url(
        self,
        url: str,
        render_js: Optional[bool] = None,
        premium: bool = False,
        country_code: Optional[str] = None
    ) -> str:
        """
        Scrape a URL using ScraperAPI.

        Args:
            url: Target URL to scrape
            render_js: Enable JavaScript rendering (default: instance setting)
            premium: Use premium proxies (costs more)
            country_code: Override country code

        Returns:
            HTML content as string

        Raises:
            ScraperAPIError: On scraping errors
        """
        params = {
            "api_key": self.api_key,
            "url": url,
            "render": "true" if (render_js if render_js is not None else self.render_js) else "false",
            "country_code": country_code or self.country_code
        }

        if premium:
            params["premium"] = "true"

        for attempt in range(self.max_retries):
            try:
                self.total_requests_made += 1

                response = await self.client.get(self.BASE_URL, params=params)

                if response.status_code == 200:
                    self.successful_requests += 1
                    return response.text

                elif response.status_code == 401:
                    raise ScraperAPIError("Invalid API key")

                elif response.status_code == 429:
                    # Rate limit - wait and retry
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit hit. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"Scrape failed with status {response.status_code}")
                    if attempt == self.max_retries - 1:
                        self.failed_requests += 1
                        raise ScraperAPIError(
                            f"Failed to scrape URL after {self.max_retries} attempts"
                        )
                    await asyncio.sleep(2 ** attempt)

            except httpx.TimeoutException:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    self.failed_requests += 1
                    raise ScraperAPIError("Request timed out")
                await asyncio.sleep(2 ** attempt)

        self.failed_requests += 1
        raise ScraperAPIError("Maximum retries exceeded")

    async def search_linkedin_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_results: int = 25
    ) -> list[Dict]:
        """
        Search LinkedIn jobs by scraping the job search page.

        Args:
            keywords: Job search keywords
            location: Job location
            max_results: Maximum results to return (LinkedIn shows 25 per page)

        Returns:
            List of job dictionaries

        Note: This parses LinkedIn HTML which can change. Use with caution.
        """
        # Build LinkedIn job search URL
        search_url = "https://www.linkedin.com/jobs/search/?"
        params = []

        if keywords:
            params.append(f"keywords={keywords.replace(' ', '%20')}")
        if location:
            params.append(f"location={location.replace(' ', '%20')}")

        search_url += "&".join(params)

        logger.info(f"Scraping LinkedIn jobs: {search_url}")

        try:
            html = await self.scrape_url(search_url, render_js=True)
            jobs = self._parse_job_search_results(html, max_results)

            logger.info(f"Extracted {len(jobs)} jobs from LinkedIn")
            return jobs

        except Exception as e:
            logger.error(f"Failed to search LinkedIn jobs: {e}")
            return []

    def _parse_job_search_results(self, html: str, max_results: int) -> list[Dict]:
        """
        Parse LinkedIn job search results HTML.

        WARNING: LinkedIn's HTML structure changes frequently.
        This is a best-effort parser and may need updates.

        Args:
            html: HTML content from LinkedIn job search
            max_results: Maximum results to extract

        Returns:
            List of job dictionaries
        """
        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        # LinkedIn job cards - selector may need updating
        job_cards = soup.find_all("div", class_="base-card")[:max_results]

        for card in job_cards:
            try:
                # Extract job data (selectors may need updating)
                title_elem = card.find("h3", class_="base-search-card__title")
                company_elem = card.find("h4", class_="base-search-card__subtitle")
                location_elem = card.find("span", class_="job-search-card__location")
                link_elem = card.find("a", class_="base-card__full-link")

                if not title_elem or not link_elem:
                    continue

                job = {
                    "title": title_elem.text.strip(),
                    "company_name": company_elem.text.strip() if company_elem else None,
                    "location": location_elem.text.strip() if location_elem else None,
                    "url": link_elem.get("href", "").split("?")[0],  # Clean URL
                    "source": "linkedin",
                    "scraped_at": datetime.now().isoformat()
                }

                # Extract job ID from URL
                if "/jobs/view/" in job["url"]:
                    job_id = job["url"].split("/jobs/view/")[1].split("/")[0]
                    job["linkedin_job_id"] = job_id

                jobs.append(job)

            except Exception as e:
                logger.warning(f"Failed to parse job card: {e}")
                continue

        return jobs

    def get_usage_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests_made,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": (
                self.successful_requests / self.total_requests_made * 100
                if self.total_requests_made > 0 else 0
            )
        }


def create_scraperapi_client(
    api_key: Optional[str] = None,
    timeout: Optional[int] = None,
    render_js: bool = True
) -> ScraperAPIClient:
    """Create ScraperAPI client from settings."""
    return ScraperAPIClient(
        api_key=api_key or getattr(settings, "LINKEDIN_API_KEY", ""),
        timeout=timeout or getattr(settings, "LINKEDIN_TIMEOUT_SECONDS", 60),
        render_js=render_js
    )
