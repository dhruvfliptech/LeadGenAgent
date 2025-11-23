"""
ZipRecruiter job board scraper.

ZipRecruiter has aggressive bot detection, so this scraper implements
enhanced anti-detection measures including:
- Extended delays
- More human-like browsing patterns
- Careful handling of their security measures
- Graceful degradation when blocked

WARNING: ZipRecruiter may require residential proxies for consistent access.
"""

import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote_plus, urlencode
import logging

from playwright.async_api import Page, Browser, BrowserContext
from app.scrapers.base_job_scraper import (
    BaseJobScraper,
    RateLimitException,
    CaptchaDetectedException
)


logger = logging.getLogger(__name__)


class ZipRecruiterScraper(BaseJobScraper):
    """
    ZipRecruiter job board scraper.

    Search URL format: https://www.ziprecruiter.com/jobs-search?search={query}&location={location}
    Pagination: &page=2, &page=3, etc.

    IMPORTANT: ZipRecruiter has very aggressive bot detection.
    - Expect higher failure rates without proxies
    - Use longer delays between requests
    - Consider using residential proxies for production
    """

    BASE_URL = "https://www.ziprecruiter.com"
    JOBS_PER_PAGE = 20  # ZipRecruiter typically shows 20 jobs per page

    # Extended delays for ZipRecruiter
    MIN_DELAY = 3.0
    MAX_DELAY = 7.0

    @property
    def source_name(self) -> str:
        return "ziprecruiter"

    async def search_jobs(
        self,
        query: str,
        location: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search ZipRecruiter for jobs.

        Args:
            query: Job search query (e.g., "data analyst")
            location: Location (e.g., "Chicago, IL")
            max_results: Maximum number of jobs to return

        Returns:
            List of standardized job dictionaries

        Note:
            This method uses extended delays and enhanced anti-detection
            measures due to ZipRecruiter's aggressive bot protection.
        """
        jobs = []
        page_num = 1

        # Create page if not exists
        if not self.page:
            self.page = await self.context.new_page()

        logger.info(f"Starting ZipRecruiter search: query='{query}', location='{location}', max_results={max_results}")
        logger.warning("ZipRecruiter has aggressive bot detection - expect potential blocking")

        while len(jobs) < max_results:
            try:
                # Build search URL
                search_url = self._build_search_url(query, location, page_num)

                # Navigate to search page with extra caution
                success = await self._safe_goto(self.page, search_url, wait_until='networkidle')
                if not success:
                    logger.warning("Failed to navigate to ZipRecruiter search page")
                    break

                # Extra delay to let page fully load
                await asyncio.sleep(2)

                # Simulate human-like scrolling
                await self._scroll_page(self.page, scrolls=2)

                # Wait for job cards to load
                await self._wait_for_jobs(self.page)

                # Extract jobs from current page
                page_jobs = await self._extract_jobs_from_page(self.page)

                if not page_jobs:
                    logger.info(f"No more jobs found on page {page_num}")
                    break

                # Add jobs to results
                for job in page_jobs:
                    if len(jobs) >= max_results:
                        break
                    jobs.append(job)
                    self.jobs_scraped += 1

                logger.info(f"Extracted {len(page_jobs)} jobs from page {page_num} (total: {len(jobs)}/{max_results})")

                # Check if we should continue
                if len(page_jobs) < self.JOBS_PER_PAGE or len(jobs) >= max_results:
                    break

                # Move to next page
                page_num += 1

                # Extended delay before next page (ZipRecruiter is sensitive)
                await self._random_delay(self.MIN_DELAY, self.MAX_DELAY)

            except (CaptchaDetectedException, RateLimitException) as e:
                logger.error(f"Blocking detected on ZipRecruiter: {str(e)}")
                logger.warning("Consider using residential proxies for ZipRecruiter")
                break

            except Exception as e:
                self.errors_encountered += 1
                logger.error(f"Error during ZipRecruiter search: {str(e)}")
                break

        logger.info(f"ZipRecruiter search completed: {len(jobs)} jobs scraped")
        return jobs

    def _build_search_url(self, query: str, location: str, page_num: int = 1) -> str:
        """
        Build ZipRecruiter search URL.

        Args:
            query: Search query
            location: Location string
            page_num: Page number (1-indexed)

        Returns:
            Complete search URL
        """
        params = {}
        if query:
            params['search'] = query
        if location:
            params['location'] = location
        if page_num > 1:
            params['page'] = str(page_num)

        # Add filters
        params['refine_by_salary'] = 'true'  # Show salary when available
        params['sort'] = 'relevance'  # Sort by relevance

        query_string = urlencode(params)
        return f"{self.BASE_URL}/jobs-search?{query_string}"

    async def _wait_for_jobs(self, page: Page, timeout: int = 15000):
        """
        Wait for job listings to load on the page.

        Args:
            page: Playwright page
            timeout: Timeout in milliseconds (increased for ZipRecruiter)
        """
        try:
            # ZipRecruiter uses various selectors
            selectors = [
                'article.job_result',
                'div.job_content',
                'li[id^="job_"]',
                'article[data-job-id]'
            ]

            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=timeout, state='visible')
                    logger.debug(f"Jobs loaded using selector: {selector}")
                    return
                except:
                    continue

            # If no selector worked, just wait a bit longer
            await asyncio.sleep(3)

        except Exception as e:
            logger.warning(f"Timeout waiting for jobs to load: {str(e)}")

    async def _extract_jobs_from_page(self, page: Page) -> List[Dict]:
        """
        Extract all job listings from the current page.

        Args:
            page: Playwright page

        Returns:
            List of job dictionaries
        """
        jobs = []

        try:
            # Try different job card selectors
            job_cards = []
            selectors = [
                'article.job_result',
                'div.job_content',
                'li[id^="job_"]',
                'article[data-job-id]'
            ]

            for selector in selectors:
                job_cards = await page.query_selector_all(selector)
                if job_cards:
                    logger.debug(f"Found {len(job_cards)} job cards using selector: {selector}")
                    break

            if not job_cards:
                logger.warning("No job cards found on page")
                return []

            # Extract data from each job card
            for card in job_cards:
                try:
                    job_data = await self._extract_job_from_element(card, self.BASE_URL)
                    if job_data:
                        # Optionally enrich with company info
                        if self.enable_company_lookup and job_data.get('company_name'):
                            company_info = await self.extract_company_info(job_data['company_name'])
                            job_data['company_website'] = company_info.get('website')
                            job_data['company_email'] = company_info.get('email')

                        # Standardize the data
                        standardized = self._standardize_job_data(job_data, self.source_name)
                        jobs.append(standardized)

                except Exception as e:
                    logger.warning(f"Error extracting job from card: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting jobs from page: {str(e)}")

        return jobs

    async def _extract_job_from_element(self, element, base_url: str) -> Optional[Dict]:
        """
        Extract job data from a job card element.

        Args:
            element: Playwright element handle
            base_url: Base URL for resolving links

        Returns:
            Dictionary with job data
        """
        try:
            job_data = {}

            # Extract job ID from data attribute
            job_id = await element.get_attribute('data-job-id')
            if not job_id:
                # Try id attribute
                elem_id = await element.get_attribute('id')
                if elem_id and 'job_' in elem_id:
                    job_id = elem_id.replace('job_', '')

            if job_id:
                job_data['job_id'] = job_id

            # Extract job title and URL
            title_selectors = [
                'h2.job_title a',
                'a.job_link',
                'a[data-job-id]',
                'h2 a',
                'a.title'
            ]

            title_elem = None
            for selector in title_selectors:
                title_elem = await element.query_selector(selector)
                if title_elem:
                    break

            if title_elem:
                job_data['title'] = (await title_elem.text_content() or "").strip()
                job_url = await title_elem.get_attribute('href')
                if job_url:
                    if job_url.startswith('http'):
                        job_data['url'] = job_url
                    else:
                        job_data['url'] = f"{base_url}{job_url}"

            # Extract company name
            company_selectors = [
                'a.company_name',
                'div.hiring_company a',
                'span.company',
                'a[data-tracking="company-name"]'
            ]

            for selector in company_selectors:
                company_elem = await element.query_selector(selector)
                if company_elem:
                    job_data['company_name'] = (await company_elem.text_content() or "").strip()
                    break

            # Extract location
            location_selectors = [
                'a.job_location',
                'li.location',
                'span.location',
                'div.location'
            ]

            for selector in location_selectors:
                location_elem = await element.query_selector(selector)
                if location_elem:
                    job_data['location'] = (await location_elem.text_content() or "").strip()
                    break

            # Extract salary if available
            salary_selectors = [
                'li.salary',
                'span.salary',
                'div.compensation',
                'span[data-tracking="salary"]'
            ]

            for selector in salary_selectors:
                salary_elem = await element.query_selector(selector)
                if salary_elem:
                    salary_text = (await salary_elem.text_content() or "").strip()
                    if salary_text and ('$' in salary_text or 'k' in salary_text.lower()):
                        job_data['salary'] = self._extract_salary_info(salary_text)
                        break

            # Extract job snippet/description preview
            snippet_selectors = [
                'p.job_snippet',
                'div.job_description',
                'p.description',
                'div.snippet'
            ]

            for selector in snippet_selectors:
                snippet_elem = await element.query_selector(selector)
                if snippet_elem:
                    job_data['description'] = (await snippet_elem.text_content() or "").strip()
                    break

            # Extract posted date
            date_selectors = [
                'time',
                'span.posted_time',
                'li.posted',
                'div.posted'
            ]

            for selector in date_selectors:
                date_elem = await element.query_selector(selector)
                if date_elem:
                    # Try datetime attribute first
                    date_text = await date_elem.get_attribute('datetime')
                    if not date_text:
                        date_text = (await date_elem.text_content() or "").strip()
                    job_data['posted_date'] = self._parse_date(date_text)
                    break

            # Check for remote work indicators
            full_text = (await element.text_content() or "").lower()
            job_data['is_remote'] = any(
                keyword in full_text
                for keyword in ['remote', 'work from home', 'wfh', 'telecommute', 'anywhere']
            )

            # Extract job type if available
            type_keywords = {
                'full time': 'full-time',
                'full-time': 'full-time',
                'part time': 'part-time',
                'part-time': 'part-time',
                'contract': 'contract',
                'contractor': 'contract',
                'temporary': 'temporary',
                'temp': 'temporary',
                'internship': 'internship',
                'intern': 'internship',
                'freelance': 'freelance'
            }

            employment_types = []
            for keyword, job_type in type_keywords.items():
                if keyword in full_text:
                    if job_type not in employment_types:
                        employment_types.append(job_type)

            if employment_types:
                job_data['employment_type'] = employment_types

            # Extract job badges/tags
            badges_selectors = [
                'span.job_badge',
                'div.badges span',
                'ul.badges li'
            ]

            badges = []
            for selector in badges_selectors:
                badge_elems = await element.query_selector_all(selector)
                for badge_elem in badge_elems:
                    badge_text = (await badge_elem.text_content() or "").strip().lower()
                    if badge_text:
                        badges.append(badge_text)

            # Update employment type based on badges
            for badge in badges:
                if 'full-time' in badge or 'full time' in badge:
                    if 'employment_type' not in job_data:
                        job_data['employment_type'] = []
                    if 'full-time' not in job_data['employment_type']:
                        job_data['employment_type'].append('full-time')
                elif 'part-time' in badge or 'part time' in badge:
                    if 'employment_type' not in job_data:
                        job_data['employment_type'] = []
                    if 'part-time' not in job_data['employment_type']:
                        job_data['employment_type'].append('part-time')

            # Only return if we have minimum required fields
            if job_data.get('title') and (job_data.get('company_name') or job_data.get('url')):
                return job_data

            return None

        except Exception as e:
            logger.warning(f"Error extracting job data from element: {str(e)}")
            return None

    async def get_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Get full job details from the job posting page.

        Args:
            job_url: URL of the job posting

        Returns:
            Dictionary with full job details

        Note:
            This is particularly challenging on ZipRecruiter due to their
            bot detection. Use sparingly.
        """
        try:
            detail_page = await self.context.new_page()

            # Extra delay before visiting job page
            await asyncio.sleep(2)

            success = await self._safe_goto(detail_page, job_url, wait_until='networkidle')
            if not success:
                await detail_page.close()
                return None

            # Wait for job description
            try:
                await detail_page.wait_for_selector(
                    'div.job_description, div.jobDescriptionSection, div[class*="description"]',
                    timeout=15000
                )
            except:
                logger.warning("Timeout waiting for job description")

            details = {}

            # Extract full job description
            desc_selectors = [
                'div.job_description',
                'div.jobDescriptionSection',
                'div[class*="JobDescription"]',
                'div.description'
            ]

            for selector in desc_selectors:
                desc_elem = await detail_page.query_selector(selector)
                if desc_elem:
                    details['description'] = (await desc_elem.text_content() or "").strip()
                    break

            # Extract job details section
            details_selectors = [
                'div.job_details',
                'div.jobDetailsSection',
                'ul.job_info'
            ]

            for selector in details_selectors:
                details_elem = await detail_page.query_selector(selector)
                if details_elem:
                    details['additional_info'] = (await details_elem.text_content() or "").strip()
                    break

            await detail_page.close()
            return details

        except Exception as e:
            logger.error(f"Error getting job details from {job_url}: {str(e)}")
            return None

    async def _safe_goto(
        self,
        page: Page,
        url: str,
        wait_until: str = 'domcontentloaded',
        timeout: int = 45000  # Increased timeout for ZipRecruiter
    ) -> bool:
        """
        Override with extended timeout for ZipRecruiter.

        ZipRecruiter pages often take longer to load due to their
        security checks.
        """
        return await super()._safe_goto(page, url, wait_until, timeout)


# Example usage
async def main():
    """Example usage of ZipRecruiter scraper."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        scraper = ZipRecruiterScraper(browser=browser, context=context, enable_company_lookup=False)

        try:
            jobs = await scraper.search_jobs(
                query="marketing manager",
                location="Austin, TX",
                max_results=15  # Lower limit due to stricter detection
            )

            print(f"\n=== ZipRecruiter Scraping Results ===")
            print(f"Total jobs found: {len(jobs)}\n")

            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job['title']}")
                print(f"   Company: {job.get('company_name', 'N/A')}")
                print(f"   Location: {job.get('location', 'N/A')}")
                print(f"   Salary: {job.get('compensation', 'N/A')}")
                print(f"   URL: {job.get('url', 'N/A')}")
                print()

            # Print stats
            stats = scraper.get_stats()
            print(f"\n=== Scraping Stats ===")
            for key, value in stats.items():
                print(f"{key}: {value}")

            if stats['captchas_detected'] > 0 or stats['rate_limits_hit'] > 0:
                print("\n⚠️  WARNING: Bot detection triggered!")
                print("Consider using residential proxies for production use.")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
