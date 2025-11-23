"""
CAPTCHA solver using 2captcha service for handling various CAPTCHA types.
"""

import asyncio
import base64
import logging
from typing import Optional, Dict, Any
from twocaptcha import TwoCaptcha
from playwright.async_api import Page
import os
from app.core.config import settings

logger = logging.getLogger(__name__)


class CaptchaSolver:
    """2captcha integration for solving CAPTCHAs in Craigslist scraping."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the CAPTCHA solver.
        
        Args:
            api_key: 2captcha API key. If not provided, will use environment variable.
        """
        self.api_key = api_key or os.getenv("TWOCAPTCHA_API_KEY")
        if not self.api_key:
            raise ValueError("2captcha API key not provided. Set TWOCAPTCHA_API_KEY environment variable.")
        
        self.solver = TwoCaptcha(self.api_key)
        self.solve_cost = 0.0  # Track total cost for CAPTCHA solving
        
        # Timeouts and retry settings
        self.default_timeout = 120  # 2 minutes
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
    async def solve_recaptcha_v2(
        self, 
        page: Page, 
        site_key: str, 
        page_url: str,
        invisible: bool = False
    ) -> Optional[str]:
        """
        Solve reCAPTCHA v2 challenge.
        
        Args:
            page: Playwright page object
            site_key: reCAPTCHA site key
            page_url: URL of the page containing the CAPTCHA
            invisible: Whether it's invisible reCAPTCHA
            
        Returns:
            CAPTCHA solution token or None if failed
        """
        try:
            logger.info(f"Solving reCAPTCHA v2 for site: {page_url}")
            
            # Submit CAPTCHA to 2captcha
            result = await asyncio.to_thread(
                self.solver.recaptcha,
                sitekey=site_key,
                url=page_url,
                invisible=1 if invisible else 0
            )
            
            if result and 'code' in result:
                solution = result['code']
                logger.info("reCAPTCHA v2 solved successfully")
                
                # Update cost tracking (approximate cost for reCAPTCHA v2)
                self.solve_cost += 0.002
                
                return solution
            else:
                logger.error("Failed to solve reCAPTCHA v2")
                return None
                
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA v2: {str(e)}")
            return None
    
    async def solve_image_captcha(self, page: Page, image_selector: str) -> Optional[str]:
        """
        Solve image-based CAPTCHA.
        
        Args:
            page: Playwright page object
            image_selector: CSS selector for the CAPTCHA image
            
        Returns:
            CAPTCHA solution text or None if failed
        """
        try:
            logger.info("Solving image CAPTCHA")
            
            # Take screenshot of the CAPTCHA image
            image_element = await page.query_selector(image_selector)
            if not image_element:
                logger.error(f"CAPTCHA image not found with selector: {image_selector}")
                return None
            
            # Get image as base64
            image_bytes = await image_element.screenshot()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Submit to 2captcha
            result = await asyncio.to_thread(
                self.solver.normal,
                image_base64
            )
            
            if result and 'code' in result:
                solution = result['code']
                logger.info(f"Image CAPTCHA solved: {solution}")
                
                # Update cost tracking (approximate cost for image CAPTCHA)
                self.solve_cost += 0.001
                
                return solution
            else:
                logger.error("Failed to solve image CAPTCHA")
                return None
                
        except Exception as e:
            logger.error(f"Error solving image CAPTCHA: {str(e)}")
            return None
    
    async def solve_hcaptcha(self, page: Page, site_key: str, page_url: str) -> Optional[str]:
        """
        Solve hCaptcha challenge.
        
        Args:
            page: Playwright page object
            site_key: hCaptcha site key
            page_url: URL of the page containing the CAPTCHA
            
        Returns:
            CAPTCHA solution token or None if failed
        """
        try:
            logger.info(f"Solving hCaptcha for site: {page_url}")
            
            result = await asyncio.to_thread(
                self.solver.hcaptcha,
                sitekey=site_key,
                url=page_url
            )
            
            if result and 'code' in result:
                solution = result['code']
                logger.info("hCaptcha solved successfully")
                
                # Update cost tracking (approximate cost for hCaptcha)
                self.solve_cost += 0.002
                
                return solution
            else:
                logger.error("Failed to solve hCaptcha")
                return None
                
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {str(e)}")
            return None
    
    async def detect_captcha_type(self, page: Page) -> Optional[Dict[str, Any]]:
        """
        Detect what type of CAPTCHA is present on the page.
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with CAPTCHA type and relevant data, or None if no CAPTCHA detected
        """
        try:
            # Check for reCAPTCHA v2
            recaptcha_element = await page.query_selector('[data-sitekey]')
            if recaptcha_element:
                site_key = await recaptcha_element.get_attribute('data-sitekey')
                if site_key:
                    # Check if it's invisible
                    invisible = await recaptcha_element.get_attribute('data-size') == 'invisible'
                    return {
                        'type': 'recaptcha_v2',
                        'site_key': site_key,
                        'invisible': invisible,
                        'element': recaptcha_element
                    }
            
            # Check for hCaptcha
            hcaptcha_element = await page.query_selector('.h-captcha[data-sitekey]')
            if hcaptcha_element:
                site_key = await hcaptcha_element.get_attribute('data-sitekey')
                if site_key:
                    return {
                        'type': 'hcaptcha',
                        'site_key': site_key,
                        'element': hcaptcha_element
                    }
            
            # Check for image CAPTCHA
            image_captcha_selectors = [
                'img[src*="captcha"]',
                'img[alt*="captcha"]',
                '.captcha img',
                '#captcha img'
            ]
            
            for selector in image_captcha_selectors:
                element = await page.query_selector(selector)
                if element:
                    return {
                        'type': 'image',
                        'selector': selector,
                        'element': element
                    }
            
            # Check for other common CAPTCHA indicators
            captcha_indicators = [
                '[id*="captcha"]',
                '[class*="captcha"]',
                '[name*="captcha"]'
            ]
            
            for selector in captcha_indicators:
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Potential CAPTCHA detected with selector: {selector}")
                    return {
                        'type': 'unknown',
                        'selector': selector,
                        'element': element
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA type: {str(e)}")
            return None
    
    async def solve_captcha_with_retry(
        self, 
        page: Page, 
        captcha_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        Solve CAPTCHA with retry logic.
        
        Args:
            page: Playwright page object
            captcha_info: CAPTCHA information from detect_captcha_type
            
        Returns:
            CAPTCHA solution or None if all attempts failed
        """
        page_url = page.url
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"CAPTCHA solve attempt {attempt + 1}/{self.max_retries}")
                
                solution = None
                
                if captcha_info['type'] == 'recaptcha_v2':
                    solution = await self.solve_recaptcha_v2(
                        page=page,
                        site_key=captcha_info['site_key'],
                        page_url=page_url,
                        invisible=captcha_info.get('invisible', False)
                    )
                elif captcha_info['type'] == 'hcaptcha':
                    solution = await self.solve_hcaptcha(
                        page=page,
                        site_key=captcha_info['site_key'],
                        page_url=page_url
                    )
                elif captcha_info['type'] == 'image':
                    solution = await self.solve_image_captcha(
                        page=page,
                        image_selector=captcha_info['selector']
                    )
                
                if solution:
                    return solution
                
                # Wait before retry
                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying CAPTCHA solve in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Error in CAPTCHA solve attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        logger.error("All CAPTCHA solve attempts failed")
        return None
    
    async def inject_captcha_solution(
        self, 
        page: Page, 
        solution: str, 
        captcha_info: Dict[str, Any]
    ) -> bool:
        """
        Inject the CAPTCHA solution into the page.
        
        Args:
            page: Playwright page object
            solution: CAPTCHA solution token/text
            captcha_info: CAPTCHA information from detect_captcha_type
            
        Returns:
            True if injection was successful, False otherwise
        """
        try:
            if captcha_info['type'] in ['recaptcha_v2', 'hcaptcha']:
                # Inject token into the response field
                response_field = 'g-recaptcha-response' if captcha_info['type'] == 'recaptcha_v2' else 'h-captcha-response'
                
                await page.evaluate(f"""
                    document.getElementById('{response_field}').innerHTML = '{solution}';
                    document.getElementById('{response_field}').value = '{solution}';
                """)
                
                # Trigger callback if it exists
                if captcha_info['type'] == 'recaptcha_v2':
                    await page.evaluate(f"""
                        if (window.grecaptcha && window.grecaptcha.getResponse) {{
                            window.grecaptcha.getResponse = function() {{ return '{solution}'; }};
                        }}
                    """)
                
                logger.info(f"Injected {captcha_info['type']} solution")
                return True
                
            elif captcha_info['type'] == 'image':
                # Find the input field for image CAPTCHA
                input_selectors = [
                    'input[name*="captcha"]',
                    'input[id*="captcha"]',
                    '#captcha_input',
                    '.captcha-input'
                ]
                
                for selector in input_selectors:
                    input_element = await page.query_selector(selector)
                    if input_element:
                        await input_element.fill(solution)
                        logger.info("Injected image CAPTCHA solution")
                        return True
                
                logger.error("Could not find input field for image CAPTCHA")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error injecting CAPTCHA solution: {str(e)}")
            return False
    
    def get_total_cost(self) -> float:
        """Get the total cost spent on CAPTCHA solving."""
        return self.solve_cost
    
    def reset_cost_tracking(self):
        """Reset the cost tracking counter."""
        self.solve_cost = 0.0