"""
Base class for job board scrapers with shared functionality.

This provides common methods for:
- Browser management
- Anti-detection measures
- Email extraction
- Company information discovery
- Rate limiting and error handling
"""

import asyncio
import re
import random
from typing import List, Dict, Optional, Set
from datetime import datetime
from abc import ABC, abstractmethod
from playwright.async_api import Page, Browser, BrowserContext
import logging
from urllib.parse import quote_plus, urljoin

from app.core.config import settings


logger = logging.getLogger(__name__)


class JobScraperException(Exception):
    """Base exception for job scraper errors."""
    pass


class RateLimitException(JobScraperException):
    """Raised when rate limiting is detected."""
    pass


class CaptchaDetectedException(JobScraperException):
    """Raised when CAPTCHA is detected."""
    pass


class BaseJobScraper(ABC):
    """
    Abstract base class for job board scrapers.

    Provides common functionality for Indeed, Monster, ZipRecruiter, etc.
    Subclasses must implement search_jobs() and _extract_job_from_element().
    """

    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]

    # Email regex patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    # Common CAPTCHA indicators
    CAPTCHA_INDICATORS = [
        'captcha', 'recaptcha', 'hcaptcha',
        'cloudflare', 'bot detection', 'verify you are human',
        'unusual traffic', 'security check'
    ]

    # Common rate limit indicators
    RATE_LIMIT_INDICATORS = [
        'too many requests', 'rate limit', 'slow down',
        '429', 'service temporarily unavailable', '503'
    ]

    def __init__(
        self,
        browser: Optional[Browser] = None,
        context: Optional[BrowserContext] = None,
        enable_company_lookup: bool = True
    ):
        """
        Initialize job scraper.

        Args:
            browser: Playwright browser instance (optional, will create if not provided)
            context: Browser context (optional, will create if not provided)
            enable_company_lookup: Whether to perform additional company info lookup
        """
        self.browser = browser
        self.context = context
        self.page: Optional[Page] = None
        self.enable_company_lookup = enable_company_lookup
        self._user_agent = random.choice(self.USER_AGENTS)

        # Tracking
        self.jobs_scraped = 0
        self.errors_encountered = 0
        self.captchas_detected = 0
        self.rate_limits_hit = 0

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the job board (e.g., 'indeed', 'monster')."""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        query: str,
        location: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for jobs and return results.

        This method must be implemented by each job board scraper.

        Args:
            query: Job search query (e.g., "software engineer")
            location: Location string (e.g., "San Francisco, CA")
            max_results: Maximum number of results to return

        Returns:
            List of job dictionaries with standardized fields
        """
        pass

    @abstractmethod
    async def _extract_job_from_element(self, element, base_url: str) -> Optional[Dict]:
        """
        Extract job data from a DOM element.

        Args:
            element: Playwright element handle
            base_url: Base URL for resolving relative links

        Returns:
            Dictionary with job data or None if extraction fails
        """
        pass

    async def _random_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        """
        Add random delay to avoid detection.

        Args:
            min_seconds: Minimum delay (defaults to config setting)
            max_seconds: Maximum delay (defaults to config setting)
        """
        min_delay = min_seconds or settings.SCRAPER_DELAY_MIN
        max_delay = max_seconds or settings.SCRAPER_DELAY_MAX
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Delaying for {delay:.2f} seconds")
        await asyncio.sleep(delay)

    async def _check_for_blocking(self, page: Page) -> None:
        """
        Check if page shows signs of blocking/CAPTCHA.

        Args:
            page: Playwright page to check

        Raises:
            CaptchaDetectedException: If CAPTCHA is detected
            RateLimitException: If rate limiting is detected
        """
        page_text = await page.text_content('body') or ""
        page_text_lower = page_text.lower()

        # Check for CAPTCHA
        for indicator in self.CAPTCHA_INDICATORS:
            if indicator in page_text_lower:
                self.captchas_detected += 1
                logger.error(f"CAPTCHA detected on {self.source_name}: {indicator}")
                raise CaptchaDetectedException(f"CAPTCHA detected: {indicator}")

        # Check for rate limiting
        for indicator in self.RATE_LIMIT_INDICATORS:
            if indicator in page_text_lower:
                self.rate_limits_hit += 1
                logger.error(f"Rate limit detected on {self.source_name}: {indicator}")
                raise RateLimitException(f"Rate limit detected: {indicator}")

        # Check HTTP status
        if page.url and ('503' in page.url or '429' in page.url):
            self.rate_limits_hit += 1
            raise RateLimitException(f"HTTP error in URL: {page.url}")

    async def _safe_goto(
        self,
        page: Page,
        url: str,
        wait_until: str = 'domcontentloaded',
        timeout: int = 30000
    ) -> bool:
        """
        Navigate to URL with error handling.

        Args:
            page: Playwright page
            url: URL to navigate to
            wait_until: Wait condition
            timeout: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            await asyncio.sleep(random.uniform(1, 2))  # Let page settle

            # Check for blocking
            await self._check_for_blocking(page)
            return True

        except (CaptchaDetectedException, RateLimitException):
            raise  # Re-raise blocking exceptions
        except Exception as e:
            self.errors_encountered += 1
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    async def extract_company_info(self, company_name: str) -> Dict:
        """
        Extract company information using Google search.

        This method searches for the company and tries to find:
        - Official website
        - Contact email
        - Company description

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with company information
        """
        info = {
            'company_name': company_name,
            'website': None,
            'email': None,
            'description': None,
            'found_via': 'google_search'
        }

        if not self.enable_company_lookup or not company_name:
            return info

        try:
            # Create new page for company lookup
            company_page = await self.context.new_page()

            # Search Google for the company
            search_query = quote_plus(f"{company_name} official website")
            google_url = f"https://www.google.com/search?q={search_query}"

            success = await self._safe_goto(company_page, google_url)
            if not success:
                await company_page.close()
                return info

            # Try to extract website from first organic result
            website = await self._extract_website_from_google(company_page)
            if website:
                info['website'] = website

                # Try to find email on company website
                email = await self.find_email_on_website(website)
                if email:
                    info['email'] = email

            await company_page.close()

        except Exception as e:
            logger.error(f"Error extracting company info for {company_name}: {str(e)}")

        return info

    async def _extract_website_from_google(self, page: Page) -> Optional[str]:
        """
        Extract the first organic result URL from Google search.

        Args:
            page: Playwright page with Google search results

        Returns:
            Website URL or None
        """
        try:
            # Google search result selectors
            selectors = [
                'div#search a[href^="http"]',
                'div.g a[href^="http"]',
                'a[data-ved]'
            ]

            for selector in selectors:
                links = await page.query_selector_all(selector)
                for link in links:
                    href = await link.get_attribute('href')
                    if href and not any(x in href for x in ['google.com', 'youtube.com', 'linkedin.com', 'facebook.com']):
                        # Clean URL (remove tracking parameters)
                        if '&sa=' in href:
                            href = href.split('&sa=')[0]
                        if '/url?q=' in href:
                            href = href.split('/url?q=')[1].split('&')[0]
                        return href

        except Exception as e:
            logger.error(f"Error extracting website from Google: {str(e)}")

        return None

    async def find_email_on_website(self, url: str) -> Optional[str]:
        """
        Find email addresses on a website.

        Checks common pages like /contact, /about for email addresses.

        Args:
            url: Website URL

        Returns:
            Email address or None
        """
        if not url:
            return None

        try:
            email_page = await self.context.new_page()

            # Pages to check
            pages_to_check = [
                url,
                urljoin(url, '/contact'),
                urljoin(url, '/contact-us'),
                urljoin(url, '/about'),
                urljoin(url, '/about-us')
            ]

            for page_url in pages_to_check:
                try:
                    await email_page.goto(page_url, wait_until='domcontentloaded', timeout=10000)
                    page_text = await email_page.text_content('body') or ""

                    # Find emails
                    emails = self.EMAIL_PATTERN.findall(page_text)
                    if emails:
                        # Filter out common non-personal emails
                        valid_emails = [
                            e for e in emails
                            if not any(x in e.lower() for x in ['example.com', 'test.com', 'noreply', 'no-reply'])
                        ]
                        if valid_emails:
                            await email_page.close()
                            return valid_emails[0]

                except Exception as e:
                    logger.debug(f"Could not check {page_url} for email: {str(e)}")
                    continue

            await email_page.close()

        except Exception as e:
            logger.error(f"Error finding email on {url}: {str(e)}")

        return None

    def _standardize_job_data(
        self,
        raw_data: Dict,
        source: str
    ) -> Dict:
        """
        Standardize job data to common format for database storage.

        Args:
            raw_data: Raw job data from scraper
            source: Source name (indeed, monster, ziprecruiter)

        Returns:
            Standardized job dictionary
        """
        # Extract salary if present
        salary = raw_data.get('salary')
        compensation = raw_data.get('compensation')

        return {
            # Core fields
            'title': raw_data.get('title'),
            'url': raw_data.get('url'),
            'description': raw_data.get('description'),

            # Source tracking
            'source': source,
            'external_id': raw_data.get('job_id'),  # Job board's ID

            # Company info
            'company_name': raw_data.get('company_name'),
            'company_website': raw_data.get('company_website'),
            'company_email': raw_data.get('company_email'),

            # Job details
            'compensation': compensation or salary,
            'employment_type': raw_data.get('employment_type', []),
            'location': raw_data.get('location'),
            'is_remote': raw_data.get('is_remote', False),

            # Timestamps
            'posted_date': raw_data.get('posted_date'),
            'scraped_at': datetime.now(),

            # Metadata
            'metadata': {
                'raw_salary': salary,
                'raw_compensation': compensation,
                'job_type': raw_data.get('job_type'),
                'experience_level': raw_data.get('experience_level'),
                'company_description': raw_data.get('company_description'),
                **raw_data.get('metadata', {})
            }
        }

    async def _scroll_page(self, page: Page, scrolls: int = 3):
        """
        Scroll page to load dynamic content.

        Args:
            page: Playwright page
            scrolls: Number of scroll actions
        """
        for i in range(scrolls):
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await asyncio.sleep(random.uniform(0.5, 1.5))

    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse various date formats from job boards.

        Args:
            date_string: Date string to parse

        Returns:
            datetime object or None
        """
        if not date_string:
            return None

        date_string = date_string.lower().strip()

        try:
            # Handle relative dates
            if 'today' in date_string or 'just posted' in date_string:
                return datetime.now()

            if 'yesterday' in date_string:
                return datetime.now() - timedelta(days=1)

            # Handle "X days ago"
            days_match = re.search(r'(\d+)\s*days?\s*ago', date_string)
            if days_match:
                days = int(days_match.group(1))
                return datetime.now() - timedelta(days=days)

            # Handle "X hours ago"
            hours_match = re.search(r'(\d+)\s*hours?\s*ago', date_string)
            if hours_match:
                hours = int(hours_match.group(1))
                return datetime.now() - timedelta(hours=hours)

            # Try ISO format
            from dateutil import parser
            return parser.parse(date_string)

        except Exception as e:
            logger.warning(f"Could not parse date: {date_string} - {str(e)}")
            return None

    def _extract_salary_info(self, text: str) -> Optional[str]:
        """
        Extract salary information from text.

        Args:
            text: Text containing salary info

        Returns:
            Cleaned salary string or None
        """
        if not text:
            return None

        # Common salary patterns
        salary_patterns = [
            r'\$[\d,]+(?:\s*-\s*\$?[\d,]+)?(?:\s*(?:per|/)\s*(?:hour|hr|year|yr|month|mo|week|wk))?',
            r'[\d,]+k?\s*-\s*[\d,]+k?(?:\s*(?:per|/)\s*(?:hour|hr|year|yr|month|mo|week|wk))?',
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    def get_stats(self) -> Dict:
        """
        Get scraping statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'source': self.source_name,
            'jobs_scraped': self.jobs_scraped,
            'errors_encountered': self.errors_encountered,
            'captchas_detected': self.captchas_detected,
            'rate_limits_hit': self.rate_limits_hit,
            'user_agent': self._user_agent
        }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.page:
            await self.page.close()


# Import timedelta for date parsing
from datetime import timedelta
