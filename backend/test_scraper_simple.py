"""
Simple test script for the Playwright-based Google Maps scraper.

This script tests the scraper without requiring the full application settings.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
import random
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, Browser, Page, Playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SimpleGoogleMapsScraper:
    """Simplified Google Maps scraper for testing."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context = None
        self.min_delay = 1.0
        self.max_delay = 2.0
        self.scroll_pause_time = 1.5
        self.max_scroll_attempts = 10

    def _get_random_user_agent(self) -> str:
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        logger.info("Initializing Playwright browser...")
        self.playwright = await async_playwright().start()

        launch_options = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        }

        self.browser = await self.playwright.chromium.launch(**launch_options)

        context_options = {
            'user_agent': self._get_random_user_agent(),
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
        }

        self.context = await self.browser.new_context(**context_options)

        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        logger.info("Google Maps scraper initialized successfully")

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Google Maps scraper closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")

    async def _random_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)

    async def search_businesses(self, query: str, location: str, max_results: int = 20) -> List[Dict]:
        businesses = []
        page = None

        try:
            page = await self.context.new_page()

            search_query = f"{query} in {location}"
            encoded_query = quote_plus(search_query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"

            logger.info(f"Searching Google Maps: {search_query}")
            logger.info(f"URL: {search_url}")

            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await self._random_delay(2, 3)

            try:
                await page.wait_for_selector('div[role="feed"]', timeout=15000)
                logger.info("Results feed loaded successfully")
            except PlaywrightTimeout:
                logger.error("Timeout waiting for results feed")
                return []

            await self._scroll_results_panel(page, max_results)
            businesses = await self._extract_businesses_from_page(page, query, location, max_results)

            logger.info(f"Successfully extracted {len(businesses)} businesses")

        except Exception as e:
            logger.error(f"Error searching Google Maps: {str(e)}")
        finally:
            if page:
                await page.close()

        return businesses

    async def _scroll_results_panel(self, page: Page, target_count: int):
        try:
            results_selector = 'div[role="feed"]'
            logger.info(f"Scrolling to load up to {target_count} results...")

            for i in range(self.max_scroll_attempts):
                current_count = await page.locator('div.Nv2PK').count()
                logger.debug(f"Scroll {i+1}: Found {current_count} results")

                if current_count >= target_count:
                    logger.info(f"Reached target of {target_count} results")
                    break

                await page.evaluate(f'''
                    const feed = document.querySelector('{results_selector}');
                    if (feed) {{
                        feed.scrollTop = feed.scrollHeight;
                    }}
                ''')

                await asyncio.sleep(self.scroll_pause_time)

                new_count = await page.locator('div.Nv2PK').count()
                if new_count == current_count:
                    logger.info(f"No more results loading after scroll {i+1}")
                    break

            final_count = await page.locator('div.Nv2PK').count()
            logger.info(f"Finished scrolling. Total results visible: {final_count}")

        except Exception as e:
            logger.error(f"Error scrolling results panel: {str(e)}")

    async def _extract_businesses_from_page(self, page: Page, query: str, location: str, max_results: int) -> List[Dict]:
        businesses = []

        try:
            result_links = await page.locator('a.hfpxzc').all()
            logger.info(f"Found {len(result_links)} business listings to process")

            for idx, link in enumerate(result_links[:max_results]):
                try:
                    await link.click()
                    await self._random_delay(0.5, 1.0)

                    business_data = await self._extract_business_details(page, query, location)

                    if business_data:
                        businesses.append(business_data)
                        logger.debug(f"Extracted business {idx+1}: {business_data.get('name', 'Unknown')}")

                    await self._random_delay(0.3, 0.7)

                except Exception as e:
                    logger.debug(f"Error extracting business {idx+1}: {str(e)}")
                    continue

            return businesses

        except Exception as e:
            logger.error(f"Error extracting businesses from page: {str(e)}")
            return businesses

    async def _extract_business_details(self, page: Page, query: str, location: str) -> Optional[Dict]:
        try:
            await page.wait_for_selector('h1.DUwDvf', timeout=5000)

            business_data = {
                'scraped_at': datetime.now(),
                'source': 'google_maps_playwright',
                'search_query': query,
                'search_location': location,
            }

            # Extract business name
            try:
                name = await page.locator('h1.DUwDvf').first.inner_text(timeout=2000)
                business_data['name'] = name.strip()
            except:
                business_data['name'] = None

            # Extract rating
            try:
                rating_text = await page.locator('div.F7nice span[aria-label*="star"]').first.get_attribute('aria-label', timeout=2000)
                if rating_text:
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        business_data['rating'] = float(rating_match.group(1))
            except:
                business_data['rating'] = None

            # Extract review count
            try:
                reviews_text = await page.locator('div.F7nice span[aria-label*="review"]').first.get_attribute('aria-label', timeout=2000)
                if reviews_text:
                    review_match = re.search(r'([\d,]+)', reviews_text)
                    if review_match:
                        review_count_str = review_match.group(1).replace(',', '')
                        business_data['review_count'] = int(review_count_str)
            except:
                business_data['review_count'] = None

            # Extract category
            try:
                category = await page.locator('button[jsaction*="category"]').first.inner_text(timeout=2000)
                business_data['category'] = category.strip()
            except:
                business_data['category'] = query

            # Extract address
            try:
                address = await page.locator('button[data-item-id="address"]').first.get_attribute('aria-label', timeout=2000)
                if address:
                    address = address.replace('Address: ', '')
                    business_data['address'] = address.strip()
            except:
                business_data['address'] = None

            # Extract phone
            try:
                phone = await page.locator('button[data-item-id*="phone"]').first.get_attribute('aria-label', timeout=2000)
                if phone:
                    phone = phone.replace('Phone: ', '').replace('Copy phone number', '')
                    business_data['phone'] = phone.strip()
            except:
                business_data['phone'] = None

            # Extract website
            try:
                website_element = await page.locator('a[data-item-id="authority"]').first.get_attribute('href', timeout=2000)
                if website_element:
                    business_data['website'] = website_element.strip()
            except:
                business_data['website'] = None

            business_data['google_maps_url'] = page.url

            if business_data.get('name'):
                return business_data
            else:
                return None

        except Exception as e:
            logger.debug(f"Error extracting business details: {str(e)}")
            return None


async def test_scraper():
    """Test the Google Maps scraper."""

    print("\n" + "="*80)
    print("GOOGLE MAPS SCRAPER TEST (Playwright Edition)")
    print("="*80 + "\n")

    query = "coffee shops"
    location = "San Francisco, CA"
    max_results = 10

    print(f"Test Parameters:")
    print(f"  Query: {query}")
    print(f"  Location: {location}")
    print(f"  Max Results: {max_results}")
    print(f"\n{'-'*80}\n")

    try:
        async with SimpleGoogleMapsScraper(headless=True) as scraper:
            print("Scraper initialized successfully!")
            print("Starting search...\n")

            businesses = await scraper.search_businesses(
                query=query,
                location=location,
                max_results=max_results
            )

            print(f"\n{'-'*80}\n")
            print(f"RESULTS: Found {len(businesses)} businesses\n")
            print("="*80 + "\n")

            if not businesses:
                print("No businesses found.")
                return

            for idx, business in enumerate(businesses, 1):
                print(f"{idx}. {business.get('name', 'N/A')}")
                print(f"   Rating: {business.get('rating', 'N/A')} ({business.get('review_count', 0)} reviews)")
                print(f"   Category: {business.get('category', 'N/A')}")
                print(f"   Address: {business.get('address', 'N/A')}")
                print(f"   Phone: {business.get('phone', 'N/A')}")
                print(f"   Website: {business.get('website', 'N/A')}")
                print()

            print("="*80)
            print(f"\nSUMMARY:")
            print(f"  Total businesses: {len(businesses)}")
            print(f"  With ratings: {sum(1 for b in businesses if b.get('rating'))}")
            print(f"  With phone: {sum(1 for b in businesses if b.get('phone'))}")
            print(f"  With website: {sum(1 for b in businesses if b.get('website'))}")
            print(f"  With address: {sum(1 for b in businesses if b.get('address'))}")
            print("\n" + "="*80)
            print("TEST COMPLETED SUCCESSFULLY!")
            print("="*80 + "\n")

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR: {str(e)}")
        print(f"{'='*80}\n")
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    print("\nStarting Google Maps Scraper Test...")
    print("This may take 30-60 seconds.\n")

    try:
        asyncio.run(test_scraper())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
