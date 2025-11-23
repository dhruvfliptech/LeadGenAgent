"""
DIY LinkedIn Job Scraper using Selenium.

⚠️⚠️⚠️ WARNING - READ BEFORE USING ⚠️⚠️⚠️

THIS SCRAPER IS NOT RECOMMENDED FOR PRODUCTION USE. RISKS INCLUDE:

1. ACCOUNT BANS:
   - LinkedIn actively detects and bans automated scraping
   - Account bans are often PERMANENT and irreversible
   - You will lose access to your LinkedIn account
   - LinkedIn may ban all accounts associated with your IP

2. IP BANS:
   - LinkedIn blocks IP addresses that scrape
   - Bans can last days to weeks
   - Residential proxies required ($50-200/month)
   - Even with proxies, detection is common

3. LEGAL RISKS:
   - Violates LinkedIn Terms of Service
   - LinkedIn has sued scrapers (hiQ Labs case)
   - Gray legal area - use at your own risk

4. MAINTENANCE BURDEN:
   - LinkedIn changes HTML weekly/monthly
   - Selectors break constantly
   - Requires 5-10 hours/month of updates
   - No guarantee of continued functionality

5. LOW SUCCESS RATE:
   - 50-70% success rate typical
   - Frequent CAPTCHAs ($3/1000 solves)
   - Rate limits (max 10-20 jobs/day safely)
   - Many requests fail silently

RECOMMENDED ALTERNATIVES:
- Piloterr: $49/month, 18K jobs/month, no ban risk
- ScraperAPI: $299/month, 600K requests, reliable
- Bright Data: $499/month, enterprise scale

USE THIS SCRAPER ONLY FOR:
- Testing/development with disposable accounts
- Very low volume (< 10 jobs/day)
- Emergency backup when services are down

⚠️⚠️⚠️ YOU HAVE BEEN WARNED ⚠️⚠️⚠️
"""

import logging
import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, TimeoutError
from bs4 import BeautifulSoup

from app.core.config import settings
from app.scrapers.captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)


class LinkedInBanError(Exception):
    """Raised when LinkedIn account or IP is banned."""
    pass


class LinkedInCaptchaError(Exception):
    """Raised when CAPTCHA cannot be solved."""
    pass


class LinkedInScraper:
    """
    DIY LinkedIn job scraper using Playwright.

    ⚠️ NOT RECOMMENDED - Use Piloterr or ScraperAPI instead!

    This scraper attempts to:
    1. Log in to LinkedIn (requires valid account)
    2. Search for jobs by keywords + location
    3. Extract job listings
    4. Visit job pages for details
    5. Extract company information

    Limitations:
    - Max 10-20 jobs/day safely
    - Requires residential proxies
    - Frequent CAPTCHAs
    - Account ban risk
    - Constant maintenance needed
    """

    def __init__(
        self,
        email: str,
        password: str,
        proxy_url: Optional[str] = None,
        captcha_api_key: Optional[str] = None,
        headless: bool = True
    ):
        """
        Initialize LinkedIn scraper.

        Args:
            email: LinkedIn account email
            password: LinkedIn account password
            proxy_url: Proxy server URL (REQUIRED for production)
            captcha_api_key: 2Captcha API key (recommended)
            headless: Run browser in headless mode
        """
        if not email or not password:
            raise ValueError("LinkedIn email and password are required")

        self.email = email
        self.password = password
        self.proxy_url = proxy_url
        self.headless = headless

        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

        # CAPTCHA solver
        self.captcha_solver: Optional[CaptchaSolver] = None
        if captcha_api_key:
            self.captcha_solver = CaptchaSolver(captcha_api_key)

        # Usage tracking
        self.jobs_scraped_today = 0
        self.captchas_encountered = 0
        self.login_attempts = 0

        logger.warning(
            "⚠️ LinkedInScraper initialized. This is NOT recommended for production. "
            "Use Piloterr ($49/month) or ScraperAPI instead to avoid bans."
        )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Initialize browser and page."""
        playwright = await async_playwright().start()

        # Browser launch options
        launch_options = {
            "headless": self.headless,
            "args": [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',  # Evade detection
                '--disable-dev-shm-usage'
            ]
        }

        # Add proxy if provided
        if self.proxy_url:
            # Parse proxy URL: http://username:password@host:port
            launch_options["proxy"] = {"server": self.proxy_url}
            logger.info("Using proxy for LinkedIn scraping")
        else:
            logger.warning(
                "⚠️ No proxy configured! LinkedIn will likely ban your IP. "
                "Set LINKEDIN_PROXY_URL in your environment."
            )

        self.browser = await playwright.chromium.launch(**launch_options)

        # Create context with realistic user agent
        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )

        # Add stealth scripts to evade detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)

        self.page = await context.new_page()

        # Set extra HTTP headers
        await self.page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1"
        })

    async def close(self):
        """Close browser."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()

    async def _random_delay(self, min_seconds: float = 2, max_seconds: float = 5):
        """Add random human-like delay."""
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def _check_for_captcha(self) -> bool:
        """Check if CAPTCHA is present on page."""
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            '[class*="captcha"]',
            '[id*="captcha"]',
            'iframe[title*="challenge"]'
        ]

        for selector in captcha_selectors:
            element = await self.page.query_selector(selector)
            if element:
                logger.warning("⚠️ CAPTCHA detected on LinkedIn")
                self.captchas_encountered += 1
                return True

        return False

    async def _solve_captcha(self) -> bool:
        """
        Attempt to solve CAPTCHA using 2Captcha service.

        Returns:
            True if solved, False otherwise
        """
        if not self.captcha_solver:
            logger.error("CAPTCHA detected but no solver configured")
            return False

        logger.info("Attempting to solve CAPTCHA...")

        # Check if reCAPTCHA
        recaptcha_frame = await self.page.query_selector('iframe[src*="recaptcha"]')
        if recaptcha_frame:
            try:
                # Get sitekey
                src = await recaptcha_frame.get_attribute('src')
                sitekey_match = re.search(r'k=([^&]+)', src)
                if not sitekey_match:
                    logger.error("Could not extract reCAPTCHA sitekey")
                    return False

                sitekey = sitekey_match.group(1)
                page_url = self.page.url

                # Solve via 2Captcha
                solution = self.captcha_solver.solve_recaptcha(page_url, sitekey)
                if not solution:
                    return False

                # Inject solution
                await self.page.evaluate(f"""
                    document.getElementById('g-recaptcha-response').innerHTML='{solution}';
                """)

                # Submit
                submit_button = await self.page.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()

                await self._random_delay(2, 4)
                return True

            except Exception as e:
                logger.error(f"CAPTCHA solving failed: {e}")
                return False

        return False

    async def login(self) -> bool:
        """
        Log in to LinkedIn.

        Returns:
            True if login successful, False otherwise

        Raises:
            LinkedInBanError: If account is banned
            LinkedInCaptchaError: If CAPTCHA cannot be solved
        """
        if self.is_logged_in:
            return True

        self.login_attempts += 1

        if self.login_attempts > 3:
            raise LinkedInBanError(
                "Multiple login attempts failed. Account may be banned or flagged."
            )

        logger.info(f"Logging in to LinkedIn (attempt {self.login_attempts}/3)...")

        try:
            # Navigate to login page
            await self.page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            await self._random_delay(1, 2)

            # Check for ban messages
            page_content = await self.page.content()
            if "unusual activity" in page_content.lower() or "restricted" in page_content.lower():
                raise LinkedInBanError(
                    "LinkedIn account appears to be banned or restricted. "
                    "Create a new account or use a professional service."
                )

            # Fill email
            email_input = await self.page.wait_for_selector('#username', timeout=10000)
            await email_input.fill(self.email)
            await self._random_delay(0.5, 1.5)

            # Fill password
            password_input = await self.page.query_selector('#password')
            await password_input.fill(self.password)
            await self._random_delay(0.5, 1.5)

            # Click sign in
            sign_in_button = await self.page.query_selector('button[type="submit"]')
            await sign_in_button.click()

            # Wait for navigation
            await self.page.wait_for_load_state("networkidle", timeout=15000)

            # Check for CAPTCHA
            if await self._check_for_captcha():
                logger.warning("CAPTCHA detected during login")
                solved = await self._solve_captcha()
                if not solved:
                    raise LinkedInCaptchaError(
                        "CAPTCHA could not be solved. LinkedIn requires verification."
                    )

            # Verify login success
            current_url = self.page.url
            if "feed" in current_url or "mynetwork" in current_url:
                self.is_logged_in = True
                logger.info("✓ Successfully logged in to LinkedIn")
                return True
            else:
                logger.error(f"Login failed. Current URL: {current_url}")
                return False

        except TimeoutError:
            logger.error("Login timeout. LinkedIn may be blocking requests.")
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        max_results: int = 25
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn.

        ⚠️ WARNING: Use sparingly to avoid bans.
        Recommended: Max 10-20 jobs per day.

        Args:
            keywords: Job search keywords
            location: Job location
            max_results: Maximum results (default: 25, LinkedIn's page size)

        Returns:
            List of job dictionaries
        """
        if not self.is_logged_in:
            success = await self.login()
            if not success:
                logger.error("Cannot search jobs without login")
                return []

        # Check daily limit
        if self.jobs_scraped_today >= 20:
            logger.error(
                f"⚠️ Daily scraping limit reached ({self.jobs_scraped_today} jobs). "
                "LinkedIn may flag your account. Stop scraping for today."
            )
            return []

        logger.info(f"Searching LinkedIn jobs: '{keywords}' in '{location}'")

        try:
            # Build search URL
            search_url = "https://www.linkedin.com/jobs/search/?"
            params = []

            if keywords:
                params.append(f"keywords={keywords.replace(' ', '%20')}")
            if location:
                params.append(f"location={location.replace(' ', '%20')}")

            search_url += "&".join(params)

            # Navigate to search
            await self.page.goto(search_url, wait_until="networkidle")
            await self._random_delay(2, 4)

            # Check for CAPTCHA
            if await self._check_for_captcha():
                solved = await self._solve_captcha()
                if not solved:
                    raise LinkedInCaptchaError("CAPTCHA blocking job search")

            # Wait for job cards
            await self.page.wait_for_selector('ul.jobs-search__results-list', timeout=10000)

            # Get page HTML
            html = await self.page.content()

            # Parse jobs
            jobs = self._parse_job_listings(html, max_results)

            self.jobs_scraped_today += len(jobs)

            logger.info(
                f"Extracted {len(jobs)} jobs from LinkedIn "
                f"(Total today: {self.jobs_scraped_today}/20)"
            )

            return jobs

        except TimeoutError:
            logger.error("Job search timeout. LinkedIn may be blocking requests.")
            return []
        except Exception as e:
            logger.error(f"Job search error: {e}")
            return []

    def _parse_job_listings(self, html: str, max_results: int) -> List[Dict]:
        """
        Parse LinkedIn job search results HTML.

        ⚠️ WARNING: LinkedIn changes HTML frequently.
        These selectors may break at any time.

        Args:
            html: Page HTML
            max_results: Max jobs to extract

        Returns:
            List of job dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []

        # Find job list items
        # NOTE: These selectors are examples and WILL break over time
        job_items = soup.find_all('li', class_='jobs-search-results__list-item')[:max_results]

        for item in job_items:
            try:
                # Extract basic info (selectors may be outdated)
                title_elem = item.find('h3', class_='base-search-card__title')
                company_elem = item.find('h4', class_='base-search-card__subtitle')
                location_elem = item.find('span', class_='job-search-card__location')
                link_elem = item.find('a', class_='base-card__full-link')

                if not title_elem or not link_elem:
                    continue

                job_url = link_elem.get('href', '').split('?')[0]

                # Extract job ID from URL
                job_id = None
                if '/jobs/view/' in job_url:
                    job_id = job_url.split('/jobs/view/')[1].split('/')[0]

                job = {
                    "linkedin_job_id": job_id or f"unknown_{datetime.now().timestamp()}",
                    "title": title_elem.text.strip(),
                    "company_name": company_elem.text.strip() if company_elem else None,
                    "location": location_elem.text.strip() if location_elem else None,
                    "url": job_url,
                    "source": "linkedin",
                    "scraped_at": datetime.now()
                }

                jobs.append(job)

            except Exception as e:
                logger.warning(f"Failed to parse job listing: {e}")
                continue

        return jobs

    async def get_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Get detailed information from a job posting.

        ⚠️ WARNING: Each request increases ban risk.
        Add 5-10 second delays between requests.

        Args:
            job_url: LinkedIn job URL

        Returns:
            Job details dictionary or None
        """
        if not self.is_logged_in:
            logger.error("Must be logged in to get job details")
            return None

        logger.info(f"Fetching job details: {job_url}")

        try:
            await self.page.goto(job_url, wait_until="networkidle")
            await self._random_delay(3, 6)

            # Check for CAPTCHA
            if await self._check_for_captcha():
                solved = await self._solve_captcha()
                if not solved:
                    return None

            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Extract details (selectors likely outdated)
            details = {}

            # Job description
            desc_elem = soup.find('div', class_='show-more-less-html__markup')
            if desc_elem:
                details['description'] = desc_elem.text.strip()

            # Company name
            company_elem = soup.find('a', class_='topcard__org-name-link')
            if company_elem:
                details['company_name'] = company_elem.text.strip()
                details['company_url'] = company_elem.get('href', '')

            # Seniority level
            seniority_elem = soup.find('span', class_='description__job-criteria-text')
            if seniority_elem:
                details['seniority_level'] = seniority_elem.text.strip()

            return details

        except Exception as e:
            logger.error(f"Failed to get job details: {e}")
            return None

    def get_usage_stats(self) -> Dict:
        """Get scraping usage statistics."""
        return {
            "jobs_scraped_today": self.jobs_scraped_today,
            "captchas_encountered": self.captchas_encountered,
            "login_attempts": self.login_attempts,
            "is_logged_in": self.is_logged_in,
            "warning": (
                "High ban risk!" if self.jobs_scraped_today >= 15
                else "Moderate ban risk" if self.jobs_scraped_today >= 10
                else "Low ban risk (so far)"
            )
        }


# Factory function
def create_linkedin_scraper(
    email: Optional[str] = None,
    password: Optional[str] = None,
    proxy_url: Optional[str] = None,
    captcha_api_key: Optional[str] = None
) -> LinkedInScraper:
    """Create LinkedIn scraper from settings."""
    return LinkedInScraper(
        email=email or getattr(settings, "LINKEDIN_EMAIL", ""),
        password=password or getattr(settings, "LINKEDIN_PASSWORD", ""),
        proxy_url=proxy_url or getattr(settings, "LINKEDIN_PROXY_URL", None),
        captcha_api_key=captcha_api_key or getattr(settings, "TWOCAPTCHA_API_KEY", None)
    )
