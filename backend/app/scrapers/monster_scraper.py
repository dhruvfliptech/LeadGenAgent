"""
Monster job board scraper.

Monster.com is a major job board with a different structure than Indeed.
This scraper handles:
- Job search with query and location
- Pagination through results
- Job detail extraction
- Handling "sign up" walls
- Company information discovery
"""

import asyncio
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote_plus
import logging

from playwright.async_api import Page, Browser, BrowserContext
from app.scrapers.base_job_scraper import (
    BaseJobScraper,
    RateLimitException,
    CaptchaDetectedException
)


logger = logging.getLogger(__name__)


class MonsterScraper(BaseJobScraper):
    """
    Monster.com job board scraper.

    Search URL format: https://www.monster.com/jobs/search/?q={query}&where={location}
    Pagination: &page=2, &page=3, etc.
    """

    BASE_URL = "https://www.monster.com"
    JOBS_PER_PAGE = 25  # Monster typically shows 25 jobs per page

    @property
    def source_name(self) -> str:
        return "monster"

    async def search_jobs(
        self,
        query: str,
        location: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search Monster for jobs.

        Args:
            query: Job search query (e.g., "software engineer")
            location: Location (e.g., "San Francisco, CA")
            max_results: Maximum number of jobs to return

        Returns:
            List of standardized job dictionaries
        """
        jobs = []
        page_num = 1

        # Create page if not exists
        if not self.page:
            self.page = await self.context.new_page()

        logger.info(f"Starting Monster search: query='{query}', location='{location}', max_results={max_results}")

        while len(jobs) < max_results:
            try:
                # Build search URL
                search_url = self._build_search_url(query, location, page_num)

                # Navigate to search page
                success = await self._safe_goto(self.page, search_url)
                if not success:
                    logger.warning("Failed to navigate to Monster search page")
                    break

                # Handle potential sign-up modal
                await self._dismiss_modals(self.page)

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

                # Random delay before next page
                await self._random_delay(2, 5)

            except (CaptchaDetectedException, RateLimitException) as e:
                logger.error(f"Blocking detected on Monster: {str(e)}")
                break

            except Exception as e:
                self.errors_encountered += 1
                logger.error(f"Error during Monster search: {str(e)}")
                break

        logger.info(f"Monster search completed: {len(jobs)} jobs scraped")
        return jobs

    def _build_search_url(self, query: str, location: str, page_num: int = 1) -> str:
        """
        Build Monster search URL.

        Args:
            query: Search query
            location: Location string
            page_num: Page number (1-indexed)

        Returns:
            Complete search URL
        """
        params = []
        if query:
            params.append(f"q={quote_plus(query)}")
        if location:
            params.append(f"where={quote_plus(location)}")
        if page_num > 1:
            params.append(f"page={page_num}")

        # Add filters
        params.append("stpage=1")
        params.append("sort=dt.rv.di")  # Sort by relevance/date

        return f"{self.BASE_URL}/jobs/search?{'&'.join(params)}"

    async def _dismiss_modals(self, page: Page):
        """
        Dismiss sign-up modals and other pop-ups.

        Args:
            page: Playwright page
        """
        try:
            # Common Monster modal selectors
            close_selectors = [
                'button[aria-label="Close"]',
                'button.modal-close',
                '.close-button',
                '[data-testid="close-button"]',
                'button:has-text("No Thanks")',
                'button:has-text("Skip")'
            ]

            for selector in close_selectors:
                try:
                    close_button = await page.query_selector(selector)
                    if close_button:
                        await close_button.click()
                        await asyncio.sleep(0.5)
                        logger.debug(f"Dismissed modal using selector: {selector}")
                except:
                    continue

            # Press Escape key as fallback
            await page.keyboard.press('Escape')
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.debug(f"Error dismissing modals: {str(e)}")

    async def _wait_for_jobs(self, page: Page, timeout: int = 10000):
        """
        Wait for job listings to load on the page.

        Args:
            page: Playwright page
            timeout: Timeout in milliseconds
        """
        try:
            # Monster uses various selectors
            selectors = [
                'div.job-card',
                'article[data-testid="job-card"]',
                'div[data-testid="svx-job-card"]',
                'div.card-content'
            ]

            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=timeout, state='visible')
                    logger.debug(f"Jobs loaded using selector: {selector}")
                    return
                except:
                    continue

            # If no selector worked, just wait a bit
            await asyncio.sleep(2)

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
                'div.job-card',
                'article[data-testid="job-card"]',
                'div[data-testid="svx-job-card"]',
                'div.card-content'
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

            # Extract job title and URL
            title_selectors = [
                'a[data-testid="job-card-title"]',
                'h2 a',
                'a.job-title',
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

                    # Extract job ID from URL
                    match = re.search(r'/job-opening/([a-zA-Z0-9-]+)', job_url)
                    if not match:
                        match = re.search(r'/job/([a-zA-Z0-9-]+)', job_url)
                    if match:
                        job_data['job_id'] = match.group(1)

            # Extract company name
            company_selectors = [
                'span[data-testid="company-name"]',
                'div.company-name',
                'span.company',
                'div.job-specs-item-label:has-text("Company") + div',
                'a.company'
            ]

            for selector in company_selectors:
                company_elem = await element.query_selector(selector)
                if company_elem:
                    job_data['company_name'] = (await company_elem.text_content() or "").strip()
                    break

            # Extract location
            location_selectors = [
                'span[data-testid="job-location"]',
                'div.location',
                'span.location',
                'div.job-specs-item-label:has-text("Location") + div'
            ]

            for selector in location_selectors:
                location_elem = await element.query_selector(selector)
                if location_elem:
                    job_data['location'] = (await location_elem.text_content() or "").strip()
                    break

            # Extract salary if available
            salary_selectors = [
                'span[data-testid="job-salary"]',
                'div.salary',
                'span.salary',
                'div.job-specs-item-label:has-text("Salary") + div'
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
                'div[data-testid="job-description"]',
                'div.summary',
                'div.job-description',
                'p.description'
            ]

            for selector in snippet_selectors:
                snippet_elem = await element.query_selector(selector)
                if snippet_elem:
                    job_data['description'] = (await snippet_elem.text_content() or "").strip()
                    break

            # Extract posted date
            date_selectors = [
                'span[data-testid="job-posted-date"]',
                'time',
                'span.date',
                'div.job-specs-item-label:has-text("Posted") + div'
            ]

            for selector in date_selectors:
                date_elem = await element.query_selector(selector)
                if date_elem:
                    date_text = (await date_elem.text_content() or "").strip()
                    job_data['posted_date'] = self._parse_date(date_text)
                    break

            # Check for remote work indicators
            full_text = (await element.text_content() or "").lower()
            job_data['is_remote'] = any(
                keyword in full_text
                for keyword in ['remote', 'work from home', 'wfh', 'telecommute', 'virtual']
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

            # Extract job type from dedicated field if available
            type_selectors = [
                'span[data-testid="job-type"]',
                'div.job-type',
                'div.job-specs-item-label:has-text("Type") + div'
            ]

            for selector in type_selectors:
                type_elem = await element.query_selector(selector)
                if type_elem:
                    type_text = (await type_elem.text_content() or "").strip().lower()
                    for keyword, job_type in type_keywords.items():
                        if keyword in type_text:
                            if 'employment_type' not in job_data:
                                job_data['employment_type'] = []
                            if job_type not in job_data['employment_type']:
                                job_data['employment_type'].append(job_type)
                    break

            # Only return if we have minimum required fields
            if job_data.get('title') and job_data.get('company_name'):
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
        """
        try:
            detail_page = await self.context.new_page()

            success = await self._safe_goto(detail_page, job_url)
            if not success:
                await detail_page.close()
                return None

            # Dismiss modals on detail page
            await self._dismiss_modals(detail_page)

            # Wait for job description
            try:
                await detail_page.wait_for_selector(
                    'div[data-testid="job-description"], div.job-description, div.description',
                    timeout=10000
                )
            except:
                logger.warning("Timeout waiting for job description")

            details = {}

            # Extract full job description
            desc_selectors = [
                'div[data-testid="job-description"]',
                'div.job-description',
                'div.description',
                'div#JobDescription'
            ]

            for selector in desc_selectors:
                desc_elem = await detail_page.query_selector(selector)
                if desc_elem:
                    details['description'] = (await desc_elem.text_content() or "").strip()
                    break

            # Extract additional details
            # Job requirements
            req_selectors = [
                'div.requirements',
                'div.qualifications',
                'div:has-text("Requirements")'
            ]

            for selector in req_selectors:
                req_elem = await detail_page.query_selector(selector)
                if req_elem:
                    details['requirements'] = (await req_elem.text_content() or "").strip()
                    break

            # Benefits
            benefits_selectors = [
                'div.benefits',
                'div:has-text("Benefits")'
            ]

            for selector in benefits_selectors:
                benefits_elem = await detail_page.query_selector(selector)
                if benefits_elem:
                    details['benefits'] = (await benefits_elem.text_content() or "").strip()
                    break

            await detail_page.close()
            return details

        except Exception as e:
            logger.error(f"Error getting job details from {job_url}: {str(e)}")
            return None


# Example usage
async def main():
    """Example usage of Monster scraper."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        scraper = MonsterScraper(browser=browser, context=context, enable_company_lookup=False)

        try:
            jobs = await scraper.search_jobs(
                query="software engineer",
                location="New York, NY",
                max_results=20
            )

            print(f"\n=== Monster Scraping Results ===")
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

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
