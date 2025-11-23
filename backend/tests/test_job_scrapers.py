"""
Test suite for job board scrapers.

This file contains example usage and test cases for Indeed, Monster,
and ZipRecruiter scrapers.

Run individual scrapers:
    python -m pytest tests/test_job_scrapers.py::test_indeed_scraper -v
    python -m pytest tests/test_job_scrapers.py::test_monster_scraper -v
    python -m pytest tests/test_job_scrapers.py::test_ziprecruiter_scraper -v

Run all scraper tests:
    python -m pytest tests/test_job_scrapers.py -v

Note: These tests make real network requests and may be rate limited.
Use with caution and respect each site's robots.txt.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict

from app.scrapers.indeed_scraper import IndeedScraper
from app.scrapers.monster_scraper import MonsterScraper
from app.scrapers.ziprecruiter_scraper import ZipRecruiterScraper


@pytest.fixture
async def browser_context():
    """Create browser context for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        yield browser, context
        await browser.close()


@pytest.mark.asyncio
async def test_indeed_scraper():
    """Test Indeed scraper functionality."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = IndeedScraper(
            browser=browser,
            context=context,
            enable_company_lookup=False  # Faster for testing
        )

        try:
            # Test search
            jobs = await scraper.search_jobs(
                query="python developer",
                location="San Francisco, CA",
                max_results=10
            )

            # Assertions
            assert isinstance(jobs, list), "Should return a list"
            assert len(jobs) > 0, "Should find at least some jobs"

            # Check job structure
            for job in jobs:
                assert 'title' in job, "Job should have title"
                assert 'url' in job, "Job should have URL"
                assert 'source' in job, "Job should have source"
                assert job['source'] == 'indeed', "Source should be 'indeed'"

            # Check stats
            stats = scraper.get_stats()
            assert stats['jobs_scraped'] == len(jobs)
            assert stats['source'] == 'indeed'

            print(f"\n=== Indeed Test Results ===")
            print(f"Jobs scraped: {len(jobs)}")
            print(f"Stats: {stats}")

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_monster_scraper():
    """Test Monster scraper functionality."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = MonsterScraper(
            browser=browser,
            context=context,
            enable_company_lookup=False
        )

        try:
            jobs = await scraper.search_jobs(
                query="software engineer",
                location="New York, NY",
                max_results=10
            )

            assert isinstance(jobs, list)
            assert len(jobs) > 0, "Should find jobs on Monster"

            for job in jobs:
                assert 'title' in job
                assert 'source' in job
                assert job['source'] == 'monster'

            stats = scraper.get_stats()
            print(f"\n=== Monster Test Results ===")
            print(f"Jobs scraped: {len(jobs)}")
            print(f"Stats: {stats}")

        finally:
            await browser.close()


@pytest.mark.asyncio
@pytest.mark.slow  # Mark as slow due to aggressive detection
async def test_ziprecruiter_scraper():
    """Test ZipRecruiter scraper functionality."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = ZipRecruiterScraper(
            browser=browser,
            context=context,
            enable_company_lookup=False
        )

        try:
            jobs = await scraper.search_jobs(
                query="data analyst",
                location="Chicago, IL",
                max_results=5  # Lower limit due to strict detection
            )

            # ZipRecruiter may block, so just check for list
            assert isinstance(jobs, list)

            stats = scraper.get_stats()
            print(f"\n=== ZipRecruiter Test Results ===")
            print(f"Jobs scraped: {len(jobs)}")
            print(f"Stats: {stats}")

            if stats['captchas_detected'] > 0:
                print("⚠️  CAPTCHA detected - consider using proxies")
            if stats['rate_limits_hit'] > 0:
                print("⚠️  Rate limit hit - reduce scraping frequency")

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_company_info_extraction():
    """Test company information extraction."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = IndeedScraper(
            browser=browser,
            context=context,
            enable_company_lookup=True
        )

        try:
            # Extract company info
            company_info = await scraper.extract_company_info("OpenAI")

            assert 'company_name' in company_info
            assert company_info['company_name'] == "OpenAI"

            print(f"\n=== Company Info Extraction Test ===")
            print(f"Company: {company_info['company_name']}")
            print(f"Website: {company_info.get('website', 'Not found')}")
            print(f"Email: {company_info.get('email', 'Not found')}")

        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_date_parsing():
    """Test date parsing functionality."""
    from app.scrapers.base_job_scraper import BaseJobScraper
    from app.scrapers.indeed_scraper import IndeedScraper

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = IndeedScraper(browser=browser, context=context)

        # Test various date formats
        test_dates = [
            "today",
            "yesterday",
            "2 days ago",
            "1 hour ago",
            "Just posted",
            "30+ days ago"
        ]

        print(f"\n=== Date Parsing Test ===")
        for date_str in test_dates:
            parsed = scraper._parse_date(date_str)
            print(f"{date_str:20} -> {parsed}")

        await browser.close()


@pytest.mark.asyncio
async def test_salary_extraction():
    """Test salary information extraction."""
    from app.scrapers.indeed_scraper import IndeedScraper

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        scraper = IndeedScraper(browser=browser, context=context)

        # Test various salary formats
        test_salaries = [
            "$100,000 - $150,000 per year",
            "$50/hour",
            "80k - 120k",
            "$75K/yr",
            "Competitive salary"
        ]

        print(f"\n=== Salary Extraction Test ===")
        for salary_str in test_salaries:
            extracted = scraper._extract_salary_info(salary_str)
            print(f"{salary_str:35} -> {extracted}")

        await browser.close()


def test_scraper_configuration():
    """Test scraper configuration and settings."""
    from app.core.config import settings

    print(f"\n=== Scraper Configuration ===")
    print(f"Indeed enabled: {getattr(settings, 'INDEED_ENABLED', True)}")
    print(f"Monster enabled: {getattr(settings, 'MONSTER_ENABLED', True)}")
    print(f"ZipRecruiter enabled: {getattr(settings, 'ZIPRECRUITER_ENABLED', True)}")
    print(f"Default delay: {getattr(settings, 'JOB_SCRAPE_DELAY_SECONDS', 3)}s")
    print(f"Max results: {getattr(settings, 'JOB_MAX_RESULTS_PER_SOURCE', 100)}")
    print(f"Company lookup: {getattr(settings, 'JOB_ENABLE_COMPANY_LOOKUP', False)}")


if __name__ == "__main__":
    # Run tests directly
    print("Running job scraper tests...\n")

    # Test configuration
    test_scraper_configuration()

    # Run async tests
    asyncio.run(test_indeed_scraper())
    asyncio.run(test_monster_scraper())
    # asyncio.run(test_ziprecruiter_scraper())  # Uncomment with caution
    asyncio.run(test_date_parsing())
    asyncio.run(test_salary_extraction())
