"""
Google Maps business scraper using Playwright for reliable browser-based scraping.

This scraper uses headless Chromium to navigate Google Maps and extract business data.
It handles JavaScript rendering, scrolling, and dynamic content loading.
"""

import asyncio
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote_plus
import random

from playwright.async_api import async_playwright, Browser, Page, Playwright, TimeoutError as PlaywrightTimeout

from app.core.config import settings


logger = logging.getLogger(__name__)


class GoogleMapsScraper:
    """
    Scraper for Google Maps business listings using Playwright.

    Features:
    - Browser-based scraping with JavaScript rendering support
    - Automatic scrolling to load more results
    - Extraction of comprehensive business data
    - Rate limiting and anti-detection measures
    - Error handling and retry logic
    - Screenshot capability for debugging
    """

    def __init__(
        self,
        headless: bool = True,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        enable_email_extraction: bool = False,
        screenshots_on_error: bool = True
    ):
        """
        Initialize the Google Maps scraper.

        Args:
            headless: Run browser in headless mode (no visible window)
            proxy: Proxy server URL (format: http://host:port)
            user_agent: Custom user agent string
            enable_email_extraction: Whether to visit business websites to extract emails
            screenshots_on_error: Take screenshots when errors occur for debugging
        """
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent or self._get_random_user_agent()
        self.enable_email_extraction = enable_email_extraction
        self.screenshots_on_error = screenshots_on_error

        # Playwright objects
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context = None

        # Rate limiting settings
        self.min_delay = getattr(settings, 'GOOGLE_MAPS_MIN_DELAY', 1.0)
        self.max_delay = getattr(settings, 'GOOGLE_MAPS_MAX_DELAY', 2.0)

        # Scraping settings
        self.scroll_pause_time = 1.5  # Time to wait after each scroll
        self.max_scroll_attempts = 10  # Maximum number of scroll attempts

    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Initialize the browser and context."""
        try:
            logger.info("Initializing Playwright browser...")

            self.playwright = await async_playwright().start()

            # Browser launch options
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            }

            if self.proxy:
                launch_options['proxy'] = {'server': self.proxy}

            self.browser = await self.playwright.chromium.launch(**launch_options)

            # Create context with settings
            context_options = {
                'user_agent': self.user_agent,
                'viewport': {'width': 1920, 'height': 1080},
                'locale': 'en-US',
                'timezone_id': 'America/New_York',
            }

            self.context = await self.browser.new_context(**context_options)

            # Add stealth measures
            await self.context.add_init_script("""
                // Override navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Override chrome property
                window.chrome = {
                    runtime: {}
                };

                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            logger.info("Google Maps scraper initialized successfully (Playwright mode)")

        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            raise

    async def close(self):
        """Close the browser and cleanup."""
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
        """Add random delay to appear more human-like."""
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)

    async def search_businesses(
        self,
        query: str,
        location: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for businesses on Google Maps using browser automation.

        Args:
            query: Search query (e.g., "restaurants", "plumbers", "dentists")
            location: Location to search in (e.g., "San Francisco, CA", "New York")
            max_results: Maximum number of results to scrape

        Returns:
            List of business dictionaries with extracted data
        """
        businesses = []
        page = None

        try:
            # Create new page
            page = await self.context.new_page()

            # Construct search URL
            search_query = f"{query} in {location}"
            encoded_query = quote_plus(search_query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"

            logger.info(f"Searching Google Maps: {search_query}")
            logger.info(f"URL: {search_url}")

            # Navigate to search page
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)

            # Wait for results to load
            await self._random_delay(2, 3)

            # Wait for the results feed to appear
            try:
                await page.wait_for_selector('div[role="feed"]', timeout=15000)
                logger.info("Results feed loaded successfully")
            except PlaywrightTimeout:
                logger.error("Timeout waiting for results feed")
                if self.screenshots_on_error:
                    await self._take_screenshot(page, "timeout_error")
                return []

            # Scroll and load more results
            await self._scroll_results_panel(page, max_results)

            # Extract business data
            businesses = await self._extract_businesses_from_page(page, query, location, max_results)

            logger.info(f"Successfully extracted {len(businesses)} businesses")

        except Exception as e:
            logger.error(f"Error searching Google Maps: {str(e)}")
            if self.screenshots_on_error and page:
                await self._take_screenshot(page, "search_error")
        finally:
            if page:
                await page.close()

        return businesses

    async def _scroll_results_panel(self, page: Page, target_count: int):
        """
        Scroll the results panel to load more businesses.

        Args:
            page: Playwright page object
            target_count: Target number of results to load
        """
        try:
            # Find the scrollable results container
            results_selector = 'div[role="feed"]'

            logger.info(f"Scrolling to load up to {target_count} results...")

            for i in range(self.max_scroll_attempts):
                # Count current results - using correct selector for business cards
                current_count = await page.locator('div.Nv2PK').count()

                logger.debug(f"Scroll {i+1}: Found {current_count} results")

                if current_count >= target_count:
                    logger.info(f"Reached target of {target_count} results")
                    break

                # Scroll the results panel
                await page.evaluate(f'''
                    const feed = document.querySelector('{results_selector}');
                    if (feed) {{
                        feed.scrollTop = feed.scrollHeight;
                    }}
                ''')

                # Wait for new content to load
                await asyncio.sleep(self.scroll_pause_time)

                # Check if we've reached the end (no new results after scroll)
                new_count = await page.locator('div.Nv2PK').count()
                if new_count == current_count:
                    logger.info(f"No more results loading after scroll {i+1}")
                    break

            final_count = await page.locator('div.Nv2PK').count()
            logger.info(f"Finished scrolling. Total results visible: {final_count}")

        except Exception as e:
            logger.error(f"Error scrolling results panel: {str(e)}")

    async def _extract_businesses_from_page(
        self,
        page: Page,
        query: str,
        location: str,
        max_results: int
    ) -> List[Dict]:
        """
        Extract business data from the loaded page.

        Args:
            page: Playwright page object
            query: Search query
            location: Search location
            max_results: Maximum number of results to extract

        Returns:
            List of business dictionaries
        """
        businesses = []

        try:
            # Get all business result cards using the correct selector
            result_links = await page.locator('a.hfpxzc').all()

            logger.info(f"Found {len(result_links)} business listings to process")

            for idx, link in enumerate(result_links[:max_results]):
                try:
                    # Click on the link to load details in the side panel
                    await link.click()
                    await self._random_delay(0.5, 1.0)

                    # Extract data from the details panel
                    business_data = await self._extract_business_details(page, query, location)

                    if business_data:
                        businesses.append(business_data)
                        logger.debug(f"Extracted business {idx+1}: {business_data.get('name', 'Unknown')}")

                    # Small delay between businesses
                    await self._random_delay(0.3, 0.7)

                except Exception as e:
                    logger.debug(f"Error extracting business {idx+1}: {str(e)}")
                    continue

            return businesses

        except Exception as e:
            logger.error(f"Error extracting businesses from page: {str(e)}")
            return businesses

    async def _extract_business_details(self, page: Page, query: str, location: str) -> Optional[Dict]:
        """
        Extract detailed information from the business details panel.

        Args:
            page: Playwright page object
            query: Search query (used as category fallback)
            location: Search location

        Returns:
            Dictionary with business data or None
        """
        try:
            # Wait for details panel to load
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

            # Extract rating and review count
            try:
                rating_text = await page.locator('div.F7nice span[aria-label*="star"]').first.get_attribute('aria-label', timeout=2000)
                if rating_text:
                    # Parse "4.5 stars" or similar
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        business_data['rating'] = float(rating_match.group(1))
            except:
                business_data['rating'] = None

            try:
                reviews_text = await page.locator('div.F7nice span[aria-label*="review"]').first.get_attribute('aria-label', timeout=2000)
                if reviews_text:
                    # Parse "1,234 reviews" or similar
                    review_match = re.search(r'([\d,]+)', reviews_text)
                    if review_match:
                        review_count_str = review_match.group(1).replace(',', '')
                        business_data['review_count'] = int(review_count_str)
            except:
                business_data['review_count'] = None

            # Extract category/type
            try:
                category = await page.locator('button[jsaction*="category"]').first.inner_text(timeout=2000)
                business_data['category'] = category.strip()
            except:
                business_data['category'] = query  # Use search query as fallback

            # Extract price level
            try:
                price = await page.locator('span[aria-label*="Price"]').first.get_attribute('aria-label', timeout=2000)
                if price:
                    business_data['price_level'] = price
            except:
                business_data['price_level'] = None

            # Extract address
            try:
                address = await page.locator('button[data-item-id="address"]').first.get_attribute('aria-label', timeout=2000)
                if address:
                    # Remove "Address: " prefix if present
                    address = address.replace('Address: ', '')
                    business_data['address'] = address.strip()
            except:
                business_data['address'] = None

            # Extract phone number
            try:
                phone = await page.locator('button[data-item-id*="phone"]').first.get_attribute('aria-label', timeout=2000)
                if phone:
                    # Remove "Phone: " prefix if present
                    phone = phone.replace('Phone: ', '').replace('Copy phone number', '')
                    business_data['phone'] = self._clean_phone(phone.strip())
            except:
                business_data['phone'] = None

            # Extract website
            try:
                website_element = await page.locator('a[data-item-id="authority"]').first.get_attribute('href', timeout=2000)
                if website_element:
                    business_data['website'] = website_element.strip()
            except:
                business_data['website'] = None

            # Get Google Maps URL
            business_data['google_maps_url'] = page.url

            # Extract email from website if enabled
            if self.enable_email_extraction and business_data.get('website'):
                email = await self._extract_email_from_website(business_data['website'])
                business_data['email'] = email

            # Only return if we have at least a name
            if business_data.get('name'):
                return business_data
            else:
                return None

        except Exception as e:
            logger.debug(f"Error extracting business details: {str(e)}")
            return None

    def _clean_phone(self, phone: str) -> str:
        """Clean and format phone number."""
        if not phone:
            return ""
        # Remove extra whitespace
        phone = phone.strip()
        # Remove common artifacts
        phone = phone.replace('Copy phone number', '').strip()
        return phone

    async def _take_screenshot(self, page: Page, error_type: str):
        """Take a screenshot for debugging."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"/tmp/google_maps_{error_type}_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"Screenshot saved to: {screenshot_path}")
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")

    async def _extract_email_from_website(self, website_url: str) -> Optional[str]:
        """
        Visit business website and extract email address.

        Args:
            website_url: URL of the business website

        Returns:
            Email address if found, None otherwise
        """
        page = None
        try:
            if not self.enable_email_extraction:
                return None

            logger.info(f"Extracting email from website: {website_url}")

            page = await self.context.new_page()

            # Visit homepage
            await page.goto(website_url, wait_until='domcontentloaded', timeout=15000)
            content = await page.content()

            email = self._find_email_in_html(content)
            if email:
                logger.info(f"Found email on homepage: {email}")
                return email

            # Try contact page
            contact_paths = ['/contact', '/contact-us', '/about', '/about-us']
            for path in contact_paths:
                try:
                    contact_url = website_url.rstrip('/') + path
                    await page.goto(contact_url, wait_until='domcontentloaded', timeout=10000)
                    content = await page.content()

                    email = self._find_email_in_html(content)
                    if email:
                        logger.info(f"Found email on {path}: {email}")
                        return email

                    await asyncio.sleep(0.5)

                except:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error extracting email from website: {str(e)}")
            return None
        finally:
            if page:
                await page.close()

    def _find_email_in_html(self, html_content: str) -> Optional[str]:
        """
        Find email address in HTML content.

        Args:
            html_content: HTML content as string

        Returns:
            Email address if found, None otherwise
        """
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html_content)

            if not emails:
                return None

            # Filter out common invalid emails
            filtered_emails = []
            for email in emails:
                email_lower = email.lower()

                if any(pattern in email_lower for pattern in [
                    'noreply@', 'no-reply@', 'example.com', 'test.com',
                    'localhost', 'domain.com', 'email.com', 'wixpress.com',
                    'sentry.io', 'google.com', 'facebook.com', 'twitter.com',
                    'linkedin.com', 'instagram.com', 'youtube.com'
                ]):
                    continue

                filtered_emails.append(email)

            if not filtered_emails:
                return None

            # Prioritize contact emails
            priority_prefixes = ['info@', 'contact@', 'sales@', 'hello@', 'support@']
            for email in filtered_emails:
                for prefix in priority_prefixes:
                    if email.lower().startswith(prefix):
                        return email

            return filtered_emails[0]

        except Exception as e:
            logger.error(f"Error finding email in HTML: {str(e)}")
            return None


# Keep the old API scraper for backward compatibility
class GooglePlacesAPIScraper:
    """
    Alternative scraper using Google Places API (paid but more reliable).

    Requires:
    - Google Cloud Platform account
    - Places API enabled
    - API key with sufficient quota

    Pricing (as of 2024):
    - Text Search: $32 per 1000 requests
    - Place Details: $17 per 1000 requests
    - Total: ~$0.049 per business with full details
    """

    def __init__(self, api_key: str, extract_emails: bool = True):
        """
        Initialize the Google Places API scraper.

        Args:
            api_key: Google Cloud API key with Places API enabled
            extract_emails: Whether to extract emails from business websites
        """
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.session = None
        self.extract_emails = extract_emails

    async def __aenter__(self):
        """Async context manager entry."""
        import httpx
        self.session = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()

    async def search_businesses(
        self,
        query: str,
        location: str,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Search for businesses using Google Places API.

        Args:
            query: Search query (e.g., "restaurants", "plumbers")
            location: Location to search in (e.g., "San Francisco, CA")
            max_results: Maximum number of results

        Returns:
            List of business dictionaries
        """
        try:
            # Text Search API
            search_url = f"{self.base_url}/textsearch/json"
            params = {
                'query': f"{query} in {location}",
                'key': self.api_key
            }

            logger.info(f"Searching Google Places API: {query} in {location}")

            response = await self.session.get(search_url, params=params)
            data = response.json()

            if data.get('status') != 'OK':
                logger.error(f"Places API error: {data.get('status')}")
                return []

            results = data.get('results', [])[:max_results]
            logger.info(f"Found {len(results)} businesses via Places API")

            # Get detailed information for each business
            businesses = []
            for result in results:
                place_id = result.get('place_id')
                if not place_id:
                    continue

                # Get place details
                details = await self._get_place_details(place_id)
                if details:
                    business_data = await self._parse_place_details(result, details)
                    businesses.append(business_data)

                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)

            return businesses

        except Exception as e:
            logger.error(f"Error searching Places API: {str(e)}")
            return []

    async def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information for a place."""
        try:
            details_url = f"{self.base_url}/details/json"
            params = {
                'place_id': place_id,
                'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,opening_hours,geometry,types',
                'key': self.api_key
            }

            response = await self.session.get(details_url, params=params)
            data = response.json()

            if data.get('status') == 'OK':
                return data.get('result')

            return None

        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}")
            return None

    async def _parse_place_details(self, search_result: Dict, details: Dict) -> Dict:
        """Parse place details into standard format."""
        geometry = details.get('geometry', {})
        location = geometry.get('location', {})

        opening_hours = details.get('opening_hours', {})
        hours = None
        if opening_hours.get('weekday_text'):
            hours = {'weekday_text': opening_hours['weekday_text']}

        website = details.get('website')
        email = None

        # Extract email from website if enabled and website exists
        if self.extract_emails and website:
            email = await self._extract_email_from_website(website)

        return {
            'name': details.get('name'),
            'address': details.get('formatted_address'),
            'phone': details.get('formatted_phone_number'),
            'website': website,
            'email': email,
            'rating': details.get('rating'),
            'review_count': details.get('user_ratings_total'),
            'category': details.get('types', [None])[0] if details.get('types') else None,
            'latitude': location.get('lat'),
            'longitude': location.get('lng'),
            'business_hours': hours,
            'google_maps_url': f"https://www.google.com/maps/place/?q=place_id:{search_result.get('place_id')}",
            'place_id': search_result.get('place_id'),
            'scraped_at': datetime.now(),
            'source': 'google_places_api'
        }

    async def _extract_email_from_website(self, website_url: str) -> Optional[str]:
        """
        Visit business website and extract email address.

        Args:
            website_url: URL of the business website

        Returns:
            Email address if found, None otherwise
        """
        try:
            logger.info(f"Extracting email from website: {website_url}")

            # Fetch homepage
            response = await self.session.get(website_url, timeout=10.0, follow_redirects=True)
            content = response.text

            email = self._find_email_in_html(content)
            if email:
                logger.info(f"Found email on homepage: {email}")
                return email

            # Try contact page
            contact_paths = ['/contact', '/contact-us', '/about', '/about-us']
            for path in contact_paths:
                try:
                    contact_url = website_url.rstrip('/') + path
                    response = await self.session.get(contact_url, timeout=8.0, follow_redirects=True)
                    content = response.text

                    email = self._find_email_in_html(content)
                    if email:
                        logger.info(f"Found email on {path}: {email}")
                        return email

                except Exception:
                    continue

            return None

        except Exception as e:
            logger.warning(f"Error extracting email from {website_url}: {str(e)}")
            return None

    def _find_email_in_html(self, html_content: str) -> Optional[str]:
        """
        Find email address in HTML content.

        Args:
            html_content: HTML content as string

        Returns:
            Email address if found, None otherwise
        """
        try:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html_content)

            if not emails:
                return None

            # Filter out common invalid emails
            filtered_emails = []
            for email in emails:
                email_lower = email.lower()

                if any(pattern in email_lower for pattern in [
                    'noreply@', 'no-reply@', 'example.com', 'test.com',
                    'localhost', 'domain.com', 'email.com', 'wixpress.com',
                    'sentry.io', 'google.com', 'facebook.com', 'twitter.com',
                    'linkedin.com', 'instagram.com', 'youtube.com', '.png',
                    '.jpg', '.gif', '.svg', 'schema.org', 'w3.org'
                ]):
                    continue

                filtered_emails.append(email)

            if not filtered_emails:
                return None

            # Prioritize contact emails
            priority_prefixes = ['info@', 'contact@', 'sales@', 'hello@', 'support@', 'enquiries@', 'inquiries@']
            for prefix in priority_prefixes:
                for email in filtered_emails:
                    if email.lower().startswith(prefix):
                        return email

            # Return first valid email
            return filtered_emails[0]

        except Exception as e:
            logger.warning(f"Error finding email in HTML: {str(e)}")
            return None
