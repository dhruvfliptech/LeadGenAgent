"""
Craigslist scraper using Playwright for reliable data extraction.
"""

import asyncio
import re
import random
from typing import List, Dict, Optional
from datetime import datetime
import json
from playwright.async_api import async_playwright, Page, Browser
from urllib.parse import urljoin, urlparse
import logging

from app.core.config import settings
from .captcha_solver import CaptchaSolver
from .email_extractor import EmailExtractor


logger = logging.getLogger(__name__)


class CraigslistScraper:
    """Async Craigslist scraper using Playwright with CAPTCHA solving and email extraction."""
    
    def __init__(self, captcha_api_key: Optional[str] = None, enable_email_extraction: bool = False):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.base_delay = settings.SCRAPER_DELAY_MIN
        self.max_delay = settings.SCRAPER_DELAY_MAX
        
        # CAPTCHA and email extraction components
        self.enable_email_extraction = enable_email_extraction
        self.captcha_solver: Optional[CaptchaSolver] = None
        self.email_extractor: Optional[EmailExtractor] = None
        
        if self.enable_email_extraction and captcha_api_key:
            self.captcha_solver = CaptchaSolver(captcha_api_key)
            self.email_extractor = EmailExtractor(self.captcha_solver)
        elif self.enable_email_extraction:
            logger.warning("Email extraction enabled but no CAPTCHA API key provided")
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        
    async def start(self):
        """Initialize the browser and page."""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        # Create page with user agent and viewport settings
        context = await self.browser.new_context(
            user_agent=settings.SCRAPER_USER_AGENT,
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()
        
    async def close(self):
        """Close the browser."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
            
    async def _random_delay(self):
        """Add random delay between requests."""
        import random
        delay = random.uniform(self.base_delay, self.max_delay)
        await asyncio.sleep(delay)
        
    async def scrape_location(
        self,
        location_url: str,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        max_pages: int = 5
    ) -> List[Dict]:
        """
        Scrape leads from a specific Craigslist location.
        
        Args:
            location_url: Base URL for the location (e.g., https://sfbay.craigslist.org)
            categories: List of categories to scrape (e.g., ['for-sale/cta', 'jobs/acc'])
            keywords: List of keywords to search for
            max_pages: Maximum number of pages to scrape per category
            
        Returns:
            List of lead dictionaries
        """
        leads = []
        
        if not categories:
            categories = ['for-sale', 'jobs', 'services', 'gigs']
            
        for category in categories:
            try:
                category_leads = await self._scrape_category(
                    location_url, category, keywords, max_pages
                )
                leads.extend(category_leads)
                
                # Delay between categories
                await self._random_delay()
                
            except Exception as e:
                logger.error(f"Error scraping category {category}: {str(e)}")
                continue
                
        return leads
        
    async def _scrape_category(
        self,
        location_url: str,
        category: str,
        keywords: Optional[List[str]],
        max_pages: int
    ) -> List[Dict]:
        """Scrape a specific category."""
        leads = []
        
        # Map common category names to Craigslist codes
        category_map = {
            'gigs': 'ggg',
            'jobs': 'jjj',
            'for-sale': 'sss',
            'services': 'bbb',
            'housing': 'hhh',
            'community': 'ccc',
            'resumes': 'rrr'
        }
        
        # Use mapped code if available, otherwise use as-is
        category_code = category_map.get(category.lower(), category)
        
        for page_num in range(max_pages):
            try:
                # Construct search URL
                if keywords:
                    # Use search with keywords
                    search_url = f"{location_url}/search/{category_code}"
                    query_params = "?query=" + "+".join(keywords)
                    if page_num > 0:
                        query_params += f"&s={page_num * 120}"
                    url = search_url + query_params
                else:
                    # Browse category
                    url = f"{location_url}/search/{category_code}"
                    if page_num > 0:
                        url += f"?s={page_num * 120}"
                
                page_leads = await self._scrape_listings_page(url, location_url)
                
                if not page_leads:
                    logger.info(f"No more leads found on page {page_num + 1} for category {category}")
                    break
                    
                leads.extend(page_leads)
                
                # Delay between pages
                await self._random_delay()
                
            except Exception as e:
                logger.error(f"Error scraping page {page_num + 1} of category {category}: {str(e)}")
                continue
                
        return leads
        
    async def _scrape_listings_page(self, url: str, base_url: str) -> List[Dict]:
        """Scrape individual listings from a search/category page."""
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for content to load
            await self.page.wait_for_timeout(2000)
            
            # Try multiple selectors - Craigslist uses different ones depending on the page
            selectors = ['.cl-search-result', '.result-row', '.result-node']
            listings = []
            
            for selector in selectors:
                listings = await self.page.query_selector_all(selector)
                if listings:
                    logger.info(f"Found {len(listings)} listings using selector: {selector}")
                    break
            
            if not listings:
                logger.warning(f"No listings found on page: {url}")
                return []
            
            leads = []
            
            for listing in listings:
                try:
                    lead = await self._extract_listing_data(listing, base_url)
                    if lead:
                        leads.append(lead)
                except Exception as e:
                    logger.warning(f"Error extracting listing data: {str(e)}")
                    continue
                    
            return leads
            
        except Exception as e:
            logger.error(f"Error scraping listings page {url}: {str(e)}")
            return []
            
    async def _extract_listing_data(self, listing_element, base_url: str) -> Optional[Dict]:
        """Extract data from a single listing element."""
        try:
            # Try multiple selectors for title/URL based on Craigslist's current structure
            title_selectors = ['a.posting-title', 'a.result-title', '.titlestring a', 'a.cl-app-anchor', 'a']
            title_element = None
            
            for selector in title_selectors:
                title_element = await listing_element.query_selector(selector)
                if title_element:
                    # Make sure it has href attribute
                    href = await title_element.get_attribute('href')
                    if href:
                        break
            
            if not title_element:
                return None
                
            title = await title_element.text_content()
            relative_url = await title_element.get_attribute('href')
            
            if not title or not relative_url:
                return None
                
            # Construct full URL
            if relative_url.startswith('http'):
                full_url = relative_url
            else:
                full_url = urljoin(base_url, relative_url)
            
            # Extract Craigslist ID from URL
            craigslist_id = self._extract_id_from_url(full_url)
            if not craigslist_id:
                # Try to extract from relative URL
                craigslist_id = self._extract_id_from_url(relative_url)
            if not craigslist_id:
                logger.warning(f"Could not extract ID from URL: {full_url}")
                return None
                
            # Get price
            price = None
            price_selectors = ['.priceinfo', '.result-price']
            for selector in price_selectors:
                price_element = await listing_element.query_selector(selector)
                if price_element:
                    price_text = await price_element.text_content()
                    price = self._extract_price(price_text)
                    break
                
            # Get posting date
            posted_at = None
            date_selectors = ['.meta .separator+ span', '.result-date', 'time', '.meta span']
            for selector in date_selectors:
                date_element = await listing_element.query_selector(selector)
                if date_element:
                    date_text = await date_element.get_attribute('datetime')
                    if not date_text:
                        date_text = await date_element.text_content()
                    posted_at = self._parse_date(date_text)
                    if posted_at:
                        break
                
            # Get location/neighborhood
            location_text = None
            location_selectors = ['.location', '.result-hood', '.meta .location']
            for selector in location_selectors:
                location_element = await listing_element.query_selector(selector)
                if location_element:
                    location_text = await location_element.text_content()
                    location_text = location_text.strip('() ')
                    break
                
            return {
                'craigslist_id': craigslist_id,
                'title': title.strip(),
                'url': full_url,
                'price': price,
                'posted_at': posted_at,
                'neighborhood': location_text,
                'scraped_at': datetime.now()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting listing data: {str(e)}")
            return None
            
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract Craigslist posting ID from URL."""
        # Pattern: /abc/d/category/1234567890.html
        pattern = r'/(\d+)\.html'
        match = re.search(pattern, url)
        return match.group(1) if match else None
        
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from price text."""
        if not price_text:
            return None
            
        # Remove currency symbols and extract number
        price_pattern = r'[\$]?([0-9,]+\.?[0-9]*)'
        match = re.search(price_pattern, price_text.replace(',', ''))
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
                
        return None
        
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse date from various Craigslist date formats.

        Supports:
        - ISO format: 2024-11-26T10:30:00
        - Relative minutes: 14m ago, 45m ago
        - Relative hours: 2h ago, 5h ago
        - Short date: 11/25, 11/24 (MM/DD format, assumes current year)

        Returns None if date cannot be parsed.
        """
        if not date_text:
            return None

        date_text = date_text.strip()

        try:
            # ISO format (from datetime attribute)
            if 'T' in date_text:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))

            # Relative minutes ago (e.g., "14m ago", "45m ago")
            minutes_match = re.match(r'^(\d+)m\s*ago$', date_text, re.IGNORECASE)
            if minutes_match:
                minutes = int(minutes_match.group(1))
                from datetime import timedelta
                return datetime.now() - timedelta(minutes=minutes)

            # Relative hours ago (e.g., "2h ago", "5h ago")
            hours_match = re.match(r'^(\d+)h\s*ago$', date_text, re.IGNORECASE)
            if hours_match:
                hours = int(hours_match.group(1))
                from datetime import timedelta
                return datetime.now() - timedelta(hours=hours)

            # Relative days ago (e.g., "2d ago", "5d ago")
            days_match = re.match(r'^(\d+)d\s*ago$', date_text, re.IGNORECASE)
            if days_match:
                days = int(days_match.group(1))
                from datetime import timedelta
                return datetime.now() - timedelta(days=days)

            # Short date format MM/DD (e.g., "11/25", "11/24")
            short_date_match = re.match(r'^(\d{1,2})/(\d{1,2})$', date_text)
            if short_date_match:
                month = int(short_date_match.group(1))
                day = int(short_date_match.group(2))
                year = datetime.now().year
                # If the date is in the future, assume it's from last year
                parsed_date = datetime(year, month, day)
                if parsed_date > datetime.now():
                    parsed_date = datetime(year - 1, month, day)
                return parsed_date

            # Full date format MM/DD/YYYY or MM/DD/YY
            full_date_match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2,4})$', date_text)
            if full_date_match:
                month = int(full_date_match.group(1))
                day = int(full_date_match.group(2))
                year = int(full_date_match.group(3))
                if year < 100:
                    year += 2000
                return datetime(year, month, day)

            # If we can't parse it, log and return None
            logger.warning(f"Unable to parse date format: {date_text}")
            return None

        except Exception as e:
            logger.warning(f"Date parsing error for '{date_text}': {e}")
            return None
            
    async def get_listing_details(self, listing_url: str) -> Optional[Dict]:
        """
        Get detailed information from a specific listing page.
        
        Args:
            listing_url: Full URL to the listing page
            
        Returns:
            Dictionary with detailed listing information
        """
        try:
            await self.page.goto(listing_url, wait_until='domcontentloaded', timeout=30000)
            await self.page.wait_for_timeout(1000)  # Let page settle
            
            # Get full HTML content
            body_html = await self.page.content()
            
            # Extract description
            description = None
            desc_element = await self.page.query_selector('#postingbody, .userbody, section.body')
            if desc_element:
                description = await desc_element.text_content()
                description = description.strip()
                # Remove "QR Code Link to This Post" text if present
                description = description.replace('QR Code Link to This Post', '').strip()
            
            # Extract enhanced contact information
            contact_info = await self._extract_enhanced_contact_info()
            
            # Extract email if enabled
            if self.enable_email_extraction and self.email_extractor:
                try:
                    email = await self.email_extractor.extract_email_from_listing(self.page, listing_url)
                    if email:
                        contact_info['reply_email'] = email
                        logger.info(f"Extracted email for listing {listing_url}: {email}")
                except Exception as e:
                    logger.error(f"Error extracting email from {listing_url}: {str(e)}")
            
            # Extract all attributes
            attributes = await self._extract_enhanced_attributes()
            
            # Extract compensation details
            compensation_info = await self._extract_compensation_info()
            
            # Extract location details with coordinates
            location_details = await self._extract_location_details()
            
            # Extract images
            image_urls = await self._extract_image_urls()
            
            # Extract employment type flags
            employment_flags = await self._extract_employment_flags()
            
            return {
                'body_html': body_html,
                'description': description,
                'contact_info': contact_info,
                'attributes': attributes,
                'compensation': compensation_info.get('compensation'),
                'employment_type': compensation_info.get('employment_type'),
                'location_details': location_details,
                'image_urls': image_urls,
                **employment_flags  # is_remote, is_internship, is_nonprofit
            }
            
        except Exception as e:
            logger.error(f"Error getting listing details from {listing_url}: {str(e)}")
            return None
            
    async def _extract_contact_info(self) -> Dict:
        """Extract contact information from listing page."""
        contact_info = {}
        
        # Look for email (often hidden behind "reply" button)
        reply_element = await self.page.query_selector('a[href*="mailto:"], .reply-email')
        if reply_element:
            href = await reply_element.get_attribute('href')
            if href and 'mailto:' in href:
                email = href.replace('mailto:', '').split('?')[0]
                contact_info['email'] = email
                
        # Look for phone numbers in text
        page_text = await self.page.text_content()
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        phone_matches = re.findall(phone_pattern, page_text)
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
            
        return contact_info
        
    async def _extract_attributes(self) -> Dict:
        """Extract listing attributes."""
        attributes = {}
        
        # Look for attribute groups
        attr_elements = await self.page.query_selector_all('.attrgroup span, .attrs span')
        
        for element in attr_elements:
            text = await element.text_content()
            if text and ':' in text:
                key, value = text.split(':', 1)
                attributes[key.strip()] = value.strip()
                
        return attributes
    
    async def _extract_enhanced_contact_info(self) -> Dict:
        """Extract enhanced contact information from listing page."""
        contact_info = {}
        
        # Look for reply button/email
        reply_button = await self.page.query_selector('button.reply-button, a.reply-button')
        if reply_button:
            # Click to reveal email if needed
            try:
                await reply_button.click()
                await self.page.wait_for_timeout(500)
            except:
                pass
        
        # Look for email in various places
        email_selectors = [
            'a[href*="mailto:"]',
            '.reply-email-address',
            '.anonemail'
        ]
        for selector in email_selectors:
            elem = await self.page.query_selector(selector)
            if elem:
                href = await elem.get_attribute('href')
                if href and 'mailto:' in href:
                    contact_info['reply_email'] = href.replace('mailto:', '').split('?')[0]
                else:
                    text = await elem.text_content()
                    if text and '@' in text:
                        contact_info['reply_email'] = text.strip()
                break
        
        # Look for phone numbers
        page_text = await self.page.text_content('body')
        if page_text:
            phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
            phone_matches = re.findall(phone_pattern, page_text)
            if phone_matches:
                contact_info['reply_phone'] = phone_matches[0]
        
        # Look for contact name
        contact_name_elem = await self.page.query_selector('.reply-contact-name, .contact-name')
        if contact_name_elem:
            contact_info['reply_contact_name'] = await contact_name_elem.text_content()
        
        return contact_info
    
    async def _extract_enhanced_attributes(self) -> Dict:
        """Extract all listing attributes with better parsing."""
        attributes = {}
        
        # Look for all attribute groups
        attr_groups = await self.page.query_selector_all('.attrgroup')
        
        for group in attr_groups:
            # Get all spans within the group
            spans = await group.query_selector_all('span')
            for span in spans:
                text = await span.text_content()
                if text:
                    # Handle different formats
                    if ':' in text:
                        key, value = text.split(':', 1)
                        attributes[key.strip().lower().replace(' ', '_')] = value.strip()
                    else:
                        # Some attributes are just text without colons
                        attributes[text.strip().lower().replace(' ', '_')] = True
        
        return attributes
    
    async def _extract_compensation_info(self) -> Dict:
        """Extract compensation and employment type information."""
        info = {
            'compensation': None,
            'employment_type': []
        }
        
        # Look for compensation
        comp_selectors = [
            '.compensation',
            'b:has-text("compensation:")',
            'p.attrgroup span:has-text("compensation")'
        ]
        
        for selector in comp_selectors:
            try:
                elem = await self.page.query_selector(selector)
                if elem:
                    text = await elem.text_content()
                    if text:
                        # Clean up compensation text
                        text = text.replace('compensation:', '').strip()
                        info['compensation'] = text
                        break
            except:
                continue
        
        # Look for employment type
        employment_types = []
        type_keywords = {
            'full-time': 'full-time',
            'part-time': 'part-time',
            'contract': 'contract',
            'temporary': 'temporary',
            'internship': 'internship',
            'freelance': 'freelance',
            'per diem': 'per-diem',
            'commission': 'commission'
        }
        
        # Check attributes for employment type
        attrs = await self._extract_enhanced_attributes()
        for key, value in attrs.items():
            lower_key = key.lower()
            if 'employment' in lower_key or 'type' in lower_key:
                if isinstance(value, str):
                    for keyword, emp_type in type_keywords.items():
                        if keyword in value.lower():
                            employment_types.append(emp_type)
        
        # Also check in the full text
        full_text = await self.page.text_content('body')
        if full_text:
            lower_text = full_text.lower()
            for keyword, emp_type in type_keywords.items():
                if keyword in lower_text and emp_type not in employment_types:
                    employment_types.append(emp_type)
        
        info['employment_type'] = employment_types if employment_types else None
        
        return info
    
    async def _extract_location_details(self) -> Dict:
        """Extract detailed location information including coordinates."""
        location = {
            'neighborhood': None,
            'latitude': None,
            'longitude': None
        }
        
        # Look for neighborhood
        hood_elem = await self.page.query_selector('.neighborhood, .hood')
        if hood_elem:
            location['neighborhood'] = await hood_elem.text_content()
        
        # Look for map data (coordinates)
        map_elem = await self.page.query_selector('#map, .viewposting-map')
        if map_elem:
            # Try to get data attributes
            lat = await map_elem.get_attribute('data-latitude')
            lon = await map_elem.get_attribute('data-longitude')
            if lat and lon:
                try:
                    location['latitude'] = float(lat)
                    location['longitude'] = float(lon)
                except:
                    pass
        
        # Alternative: look in page scripts for coordinates
        if not location['latitude']:
            scripts = await self.page.query_selector_all('script')
            for script in scripts:
                content = await script.text_content()
                if content and 'latitude' in content:
                    # Try to extract coordinates from JavaScript
                    import json
                    try:
                        # Look for JSON-like structures
                        lat_match = re.search(r'"latitude"\s*:\s*([-\d.]+)', content)
                        lon_match = re.search(r'"longitude"\s*:\s*([-\d.]+)', content)
                        if lat_match and lon_match:
                            location['latitude'] = float(lat_match.group(1))
                            location['longitude'] = float(lon_match.group(1))
                            break
                    except:
                        pass
        
        return location
    
    async def _extract_image_urls(self) -> List[str]:
        """Extract all image URLs from the listing."""
        image_urls = []
        
        # Look for images in gallery
        img_selectors = [
            '.gallery img',
            '.swipe-wrap img',
            '.thumb img',
            'img.preview'
        ]
        
        for selector in img_selectors:
            images = await self.page.query_selector_all(selector)
            for img in images:
                src = await img.get_attribute('src')
                if src and src.startswith('http'):
                    if src not in image_urls:
                        image_urls.append(src)
        
        return image_urls
    
    async def _extract_employment_flags(self) -> Dict:
        """Extract boolean employment flags."""
        flags = {
            'is_remote': False,
            'is_internship': False,
            'is_nonprofit': False
        }
        
        # Get full text to search
        full_text = await self.page.text_content('body')
        if full_text:
            lower_text = full_text.lower()
            
            # Check for remote work
            remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute', 'telework']
            flags['is_remote'] = any(keyword in lower_text for keyword in remote_keywords)
            
            # Check for internship
            internship_keywords = ['internship', 'intern']
            flags['is_internship'] = any(keyword in lower_text for keyword in internship_keywords)
            
            # Check for nonprofit
            nonprofit_keywords = ['non-profit', 'nonprofit', 'non profit', '501c3', '501(c)(3)']
            flags['is_nonprofit'] = any(keyword in lower_text for keyword in nonprofit_keywords)
        
        return flags
    
    async def extract_emails_from_leads(
        self, 
        leads: List[Dict], 
        max_concurrent: int = 2
    ) -> List[Dict]:
        """
        Extract emails from a list of leads with CAPTCHA handling.
        
        Args:
            leads: List of lead dictionaries with 'url' field
            max_concurrent: Maximum number of concurrent email extractions
            
        Returns:
            Updated leads list with email information
        """
        if not self.enable_email_extraction or not self.email_extractor:
            logger.warning("Email extraction not enabled or configured")
            return leads
        
        try:
            # Extract URLs from leads
            urls = [lead.get('url') for lead in leads if lead.get('url')]
            
            if not urls:
                logger.info("No URLs found in leads for email extraction")
                return leads
            
            logger.info(f"Starting email extraction for {len(urls)} leads")
            
            # Extract emails in batches
            email_results = await self.email_extractor.batch_extract_emails(
                self.page, urls, max_concurrent
            )
            
            # Update leads with extracted emails
            updated_leads = []
            for lead in leads:
                url = lead.get('url')
                if url and url in email_results:
                    email = email_results[url]
                    if email:
                        lead['email'] = email
                        logger.info(f"Added email to lead {lead.get('craigslist_id', 'unknown')}: {email}")
                
                updated_leads.append(lead)
            
            # Log extraction statistics
            extracted_count = sum(1 for result in email_results.values() if result)
            logger.info(f"Email extraction completed: {extracted_count}/{len(urls)} emails extracted")
            
            if self.captcha_solver:
                cost = self.captcha_solver.get_total_cost()
                logger.info(f"Total CAPTCHA solving cost: ${cost:.4f}")
            
            return updated_leads
            
        except Exception as e:
            logger.error(f"Error in batch email extraction: {str(e)}")
            return leads
    
    async def scrape_location_with_emails(
        self,
        location_url: str,
        categories: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        max_pages: int = 5,
        extract_emails: bool = None,
        extract_contact_details: bool = True
    ) -> List[Dict]:
        """
        Scrape leads from a location with optional email extraction and contact details.

        Args:
            location_url: Base URL for the location
            categories: List of categories to scrape
            keywords: List of keywords to search for
            max_pages: Maximum number of pages to scrape per category
            extract_emails: Override email extraction setting for this call (requires CAPTCHA API key)
            extract_contact_details: If True, visit each listing to extract phone numbers and descriptions

        Returns:
            List of lead dictionaries with contact information
        """
        # Get basic leads first
        leads = await self.scrape_location(location_url, categories, keywords, max_pages)

        logger.info(f"scrape_location_with_emails: Got {len(leads)} leads, extract_contact_details={extract_contact_details}")

        # Extract basic contact details (phone, description) from each listing - no CAPTCHA needed
        if extract_contact_details and leads:
            leads = await self.extract_contact_details_from_leads(leads)

        # Extract emails if enabled (requires CAPTCHA solving)
        should_extract_emails = extract_emails if extract_emails is not None else self.enable_email_extraction

        if should_extract_emails and leads:
            leads = await self.extract_emails_from_leads(leads)

        return leads

    async def extract_contact_details_from_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Extract basic contact details (phone, description) from each listing page.
        This does NOT require CAPTCHA solving - it just visits the listing pages
        to get phone numbers from the text and description.

        Args:
            leads: List of lead dictionaries with 'url' field

        Returns:
            Updated list of leads with contact details
        """
        updated_leads = []
        total = len(leads)

        for i, lead in enumerate(leads):
            try:
                listing_url = lead.get('url')
                if not listing_url:
                    updated_leads.append(lead)
                    continue

                logger.info(f"Extracting contact details from listing {i+1}/{total}: {listing_url}")

                # Navigate to listing page
                await self.page.goto(listing_url, wait_until='domcontentloaded', timeout=30000)
                await self.page.wait_for_timeout(500)  # Brief delay

                # Extract description
                description = None
                desc_element = await self.page.query_selector('#postingbody, .userbody, section.body')
                if desc_element:
                    description = await desc_element.text_content()
                    if description:
                        description = description.strip()
                        description = description.replace('QR Code Link to This Post', '').strip()

                # Extract phone numbers from page text
                phone = None
                page_text = await self.page.text_content('body')
                if page_text:
                    phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
                    phone_matches = re.findall(phone_pattern, page_text)
                    if phone_matches:
                        phone = phone_matches[0]
                        logger.info(f"Found phone number: {phone}")

                # Look for visible email (some posters include it in description)
                email = None
                if page_text:
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_matches = re.findall(email_pattern, page_text)
                    # Filter out craigslist system emails
                    for match in email_matches:
                        if 'craigslist' not in match.lower() and 'reply' not in match.lower():
                            email = match
                            logger.info(f"Found email in text: {email}")
                            break

                # Extract compensation info
                compensation = None
                comp_elem = await self.page.query_selector('.attrgroup span:has-text("compensation"), p:has-text("compensation")')
                if comp_elem:
                    comp_text = await comp_elem.text_content()
                    if comp_text:
                        compensation = comp_text.replace('compensation:', '').strip()

                # Update lead with extracted info
                lead['description'] = description
                if phone:
                    lead['reply_phone'] = phone
                if email:
                    lead['email'] = email
                if compensation:
                    lead['compensation'] = compensation

                updated_leads.append(lead)

                # Rate limiting delay
                await self.page.wait_for_timeout(random.randint(500, 1500))

            except Exception as e:
                logger.warning(f"Error extracting contact details from {lead.get('url')}: {str(e)}")
                updated_leads.append(lead)
                continue

        logger.info(f"Extracted contact details from {len(updated_leads)} leads")
        return updated_leads
    
    def get_captcha_cost(self) -> float:
        """
        Get the total cost spent on CAPTCHA solving.
        
        Returns:
            Total cost in USD
        """
        if self.captcha_solver:
            return self.captcha_solver.get_total_cost()
        return 0.0
    
    def reset_captcha_cost(self):
        """Reset the CAPTCHA cost tracking."""
        if self.captcha_solver:
            self.captcha_solver.reset_cost_tracking()