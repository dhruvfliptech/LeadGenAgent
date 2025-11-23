#!/usr/bin/env python3
"""
Debug script to inspect Craigslist HTML structure.
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_craigslist_structure():
    """Debug Craigslist page structure to understand the HTML."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Test 1: Check gigs page structure
            print("\n" + "="*60)
            print("CHECKING GIGS PAGE STRUCTURE")
            print("="*60)
            
            url = "https://sfbay.craigslist.org/search/ggg"  # ggg is the category code for gigs
            print(f"\nNavigating to: {url}")
            
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Check for different possible selectors
            selectors_to_check = [
                '.result-row',
                '.cl-search-result', 
                '.result-info',
                '.gallery-card',
                'li.cl-search-result',
                'div.result-node',
                'article',
                '.search-result'
            ]
            
            print("\nChecking for listing selectors:")
            for selector in selectors_to_check:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  ✅ Found {len(elements)} elements with selector: {selector}")
                else:
                    print(f"  ❌ No elements found with selector: {selector}")
            
            # Get page HTML for inspection
            print("\n" + "="*60)
            print("PAGE HTML STRUCTURE (first 2000 chars)")
            print("="*60)
            
            html = await page.content()
            print(html[:2000])
            
            # Test 2: Check search with keywords
            print("\n" + "="*60)
            print("CHECKING SEARCH WITH KEYWORDS")
            print("="*60)
            
            search_url = "https://sfbay.craigslist.org/search/ggg?query=software"
            print(f"\nNavigating to: {search_url}")
            
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Check for results
            for selector in selectors_to_check:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"  ✅ Found {len(elements)} search results with selector: {selector}")
                    
                    # Get first result details
                    if len(elements) > 0:
                        first_result = elements[0]
                        
                        # Try to get title
                        title_selectors = ['a.posting-title', '.titlestring', 'a', 'h3', '.title']
                        for title_sel in title_selectors:
                            title_elem = await first_result.query_selector(title_sel)
                            if title_elem:
                                title_text = await title_elem.text_content()
                                if title_text:
                                    print(f"\n  First result title (using {title_sel}): {title_text[:100]}")
                                    break
                        
                        # Try to get link
                        link_elem = await first_result.query_selector('a')
                        if link_elem:
                            href = await link_elem.get_attribute('href')
                            print(f"  First result link: {href}")
                    
                    break
            
            # Save full HTML for inspection
            with open('craigslist_debug.html', 'w') as f:
                f.write(html)
            print(f"\n📄 Full HTML saved to: craigslist_debug.html")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Debug failed")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_craigslist_structure())