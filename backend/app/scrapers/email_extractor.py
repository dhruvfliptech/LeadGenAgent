"""
Email extractor for Craigslist listings with CAPTCHA handling.
"""

import asyncio
import re
import logging
from typing import Optional, Dict, List
from playwright.async_api import Page
from urllib.parse import urlparse, parse_qs

from .captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)


class EmailExtractor:
    """Extract email addresses from Craigslist listings with CAPTCHA handling."""
    
    def __init__(self, captcha_solver: CaptchaSolver):
        """
        Initialize the email extractor.
        
        Args:
            captcha_solver: CaptchaSolver instance for handling CAPTCHAs
        """
        self.captcha_solver = captcha_solver
        self.extraction_timeout = 30  # seconds
        self.max_extraction_attempts = 3
        
    async def extract_email_from_listing(self, page: Page, listing_url: str) -> Optional[str]:
        """
        Extract email address from a Craigslist listing.
        
        Args:
            page: Playwright page object
            listing_url: URL of the Craigslist listing
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            logger.info(f"Extracting email from listing: {listing_url}")
            
            # Navigate to the listing page
            await page.goto(listing_url, wait_until='networkidle')
            
            # First, try to find email in the page content directly
            direct_email = await self._find_direct_email(page)
            if direct_email:
                logger.info(f"Found direct email: {direct_email}")
                return direct_email
            
            # Look for reply button/link
            reply_info = await self._find_reply_element(page)
            if not reply_info:
                logger.info("No reply mechanism found")
                return None
            
            # Try to extract email through reply mechanism
            email = await self._extract_email_via_reply(page, reply_info)
            
            if email:
                logger.info(f"Successfully extracted email: {email}")
            else:
                logger.info("Could not extract email from listing")
            
            return email
            
        except Exception as e:
            logger.error(f"Error extracting email from {listing_url}: {str(e)}")
            return None
    
    async def _find_direct_email(self, page: Page) -> Optional[str]:
        """
        Look for email addresses directly in the page content.
        
        Args:
            page: Playwright page object
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Get page text content
            page_text = await page.text_content()
            
            # Email regex pattern
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            
            # Find emails in text
            emails = re.findall(email_pattern, page_text)
            
            if emails:
                # Filter out common non-personal emails
                filtered_emails = [
                    email for email in emails 
                    if not any(domain in email.lower() for domain in [
                        'craigslist.org', 'noreply', 'no-reply', 'example.com'
                    ])
                ]
                
                if filtered_emails:
                    return filtered_emails[0]  # Return first valid email
            
            # Look for mailto links
            mailto_links = await page.query_selector_all('a[href^="mailto:"]')
            for link in mailto_links:
                href = await link.get_attribute('href')
                if href:
                    email = href.replace('mailto:', '').split('?')[0]
                    if self._is_valid_email(email):
                        return email
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding direct email: {str(e)}")
            return None
    
    async def _find_reply_element(self, page: Page) -> Optional[Dict]:
        """
        Find the reply button or link on the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with reply element info, or None if not found
        """
        try:
            # Common reply selectors for Craigslist
            reply_selectors = [
                'a.reply-button',
                'a[href*="reply"]',
                'button[id*="reply"]',
                '.reply-link',
                '#replylink',
                'a.showcontact',
                'button.contact-button'
            ]
            
            for selector in reply_selectors:
                element = await page.query_selector(selector)
                if element:
                    href = await element.get_attribute('href')
                    text = await element.text_content()
                    
                    return {
                        'element': element,
                        'selector': selector,
                        'href': href,
                        'text': text.strip() if text else '',
                        'type': 'link' if href else 'button'
                    }
            
            # Look for any element with "reply" or "contact" text
            reply_elements = await page.query_selector_all('a, button')
            for element in reply_elements:
                text = await element.text_content()
                if text and any(keyword in text.lower() for keyword in ['reply', 'contact', 'email']):
                    href = await element.get_attribute('href')
                    return {
                        'element': element,
                        'selector': 'text-based',
                        'href': href,
                        'text': text.strip(),
                        'type': 'link' if href else 'button'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding reply element: {str(e)}")
            return None
    
    async def _extract_email_via_reply(self, page: Page, reply_info: Dict) -> Optional[str]:
        """
        Extract email by clicking/navigating to reply mechanism.
        
        Args:
            page: Playwright page object
            reply_info: Information about the reply element
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            original_url = page.url
            
            for attempt in range(self.max_extraction_attempts):
                try:
                    logger.info(f"Email extraction attempt {attempt + 1}/{self.max_extraction_attempts}")
                    
                    # Navigate back to original page if needed
                    if page.url != original_url:
                        await page.goto(original_url, wait_until='networkidle')
                        await asyncio.sleep(2)
                    
                    # Re-find the reply element (it might have changed)
                    current_reply_info = await self._find_reply_element(page)
                    if not current_reply_info:
                        logger.warning("Reply element not found on retry")
                        continue
                    
                    # Handle different reply mechanisms
                    if current_reply_info['type'] == 'link' and current_reply_info['href']:
                        email = await self._handle_reply_link(page, current_reply_info['href'])
                    else:
                        email = await self._handle_reply_button(page, current_reply_info['element'])
                    
                    if email:
                        return email
                    
                    # Wait before retry
                    if attempt < self.max_extraction_attempts - 1:
                        await asyncio.sleep(3)
                
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_extraction_attempts - 1:
                        await asyncio.sleep(3)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting email via reply: {str(e)}")
            return None
    
    async def _handle_reply_link(self, page: Page, reply_href: str) -> Optional[str]:
        """
        Handle reply mechanism that uses a link.
        
        Args:
            page: Playwright page object
            reply_href: URL of the reply link
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Check if it's a mailto link
            if reply_href.startswith('mailto:'):
                email = reply_href.replace('mailto:', '').split('?')[0]
                if self._is_valid_email(email):
                    return email
            
            # Navigate to reply page
            await page.goto(reply_href, wait_until='networkidle')
            
            # Check for CAPTCHA
            captcha_info = await self.captcha_solver.detect_captcha_type(page)
            if captcha_info:
                logger.info(f"CAPTCHA detected: {captcha_info['type']}")
                
                # Solve CAPTCHA
                solution = await self.captcha_solver.solve_captcha_with_retry(page, captcha_info)
                if not solution:
                    logger.error("Failed to solve CAPTCHA")
                    return None
                
                # Inject solution
                if not await self.captcha_solver.inject_captcha_solution(page, solution, captcha_info):
                    logger.error("Failed to inject CAPTCHA solution")
                    return None
                
                # Submit form
                await self._submit_captcha_form(page)
            
            # Look for email in the reply page
            return await self._find_email_in_reply_page(page)
            
        except Exception as e:
            logger.error(f"Error handling reply link: {str(e)}")
            return None
    
    async def _handle_reply_button(self, page: Page, reply_element) -> Optional[str]:
        """
        Handle reply mechanism that uses a button.
        
        Args:
            page: Playwright page object
            reply_element: The reply button element
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Click the reply button
            await reply_element.click()
            
            # Wait for potential modal or new content
            await asyncio.sleep(2)
            
            # Check for CAPTCHA
            captcha_info = await self.captcha_solver.detect_captcha_type(page)
            if captcha_info:
                logger.info(f"CAPTCHA detected: {captcha_info['type']}")
                
                # Solve CAPTCHA
                solution = await self.captcha_solver.solve_captcha_with_retry(page, captcha_info)
                if not solution:
                    logger.error("Failed to solve CAPTCHA")
                    return None
                
                # Inject solution
                if not await self.captcha_solver.inject_captcha_solution(page, solution, captcha_info):
                    logger.error("Failed to inject CAPTCHA solution")
                    return None
                
                # Submit form
                await self._submit_captcha_form(page)
            
            # Look for revealed email
            return await self._find_revealed_email(page)
            
        except Exception as e:
            logger.error(f"Error handling reply button: {str(e)}")
            return None
    
    async def _submit_captcha_form(self, page: Page):
        """Submit the form after CAPTCHA solution is injected."""
        try:
            # Look for submit buttons
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button.submit',
                '.submit-button',
                '#submit'
            ]
            
            for selector in submit_selectors:
                submit_button = await page.query_selector(selector)
                if submit_button:
                    await submit_button.click()
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    return
            
            # Try form submission via Enter key
            await page.keyboard.press('Enter')
            await page.wait_for_load_state('networkidle', timeout=10000)
            
        except Exception as e:
            logger.warning(f"Error submitting CAPTCHA form: {str(e)}")
    
    async def _find_email_in_reply_page(self, page: Page) -> Optional[str]:
        """
        Find email address in the reply page after navigation.
        
        Args:
            page: Playwright page object
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Wait for content to load
            await asyncio.sleep(2)
            
            # Look for email in various possible locations
            email_selectors = [
                '.contact-email',
                '.email-address',
                '#email',
                '.reply-email',
                '[data-email]'
            ]
            
            for selector in email_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    data_email = await element.get_attribute('data-email')
                    
                    if data_email and self._is_valid_email(data_email):
                        return data_email
                    if text and self._is_valid_email(text.strip()):
                        return text.strip()
            
            # Look for email in page text
            return await self._find_direct_email(page)
            
        except Exception as e:
            logger.error(f"Error finding email in reply page: {str(e)}")
            return None
    
    async def _find_revealed_email(self, page: Page) -> Optional[str]:
        """
        Find email that was revealed after clicking reply button.
        
        Args:
            page: Playwright page object
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Wait for content to update
            await asyncio.sleep(3)
            
            # Look for dynamically revealed email
            revealed_selectors = [
                '.revealed-email',
                '.contact-info',
                '.email-revealed',
                '#contact-email',
                '.reply-contact'
            ]
            
            for selector in revealed_selectors:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and self._is_valid_email(text.strip()):
                        return text.strip()
            
            # Check if email appeared in the page text
            return await self._find_direct_email(page)
            
        except Exception as e:
            logger.error(f"Error finding revealed email: {str(e)}")
            return None
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        
        # Basic email regex
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        
        # Check format
        if not re.match(pattern, email):
            return False
        
        # Exclude common invalid patterns
        invalid_patterns = [
            '@craigslist.org',
            'noreply@',
            'no-reply@',
            '@example.com',
            '@test.com',
            '@localhost'
        ]
        
        email_lower = email.lower()
        for pattern in invalid_patterns:
            if pattern in email_lower:
                return False
        
        return True
    
    async def batch_extract_emails(
        self, 
        page: Page, 
        listing_urls: List[str],
        max_concurrent: int = 3
    ) -> Dict[str, Optional[str]]:
        """
        Extract emails from multiple listings with concurrency control.
        
        Args:
            page: Playwright page object
            listing_urls: List of listing URLs
            max_concurrent: Maximum number of concurrent extractions
            
        Returns:
            Dictionary mapping URLs to extracted emails (or None)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def extract_single(url: str):
            async with semaphore:
                try:
                    email = await self.extract_email_from_listing(page, url)
                    results[url] = email
                except Exception as e:
                    logger.error(f"Error in batch extraction for {url}: {str(e)}")
                    results[url] = None
        
        # Create tasks for all URLs
        tasks = [extract_single(url) for url in listing_urls]
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results