"""
Debug script to inspect Google Maps HTML structure (headless mode).
"""

import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote_plus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_google_maps():
    """Debug script to inspect Google Maps structure."""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        query = "coffee shops in San Francisco, CA"
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/maps/search/{encoded_query}"

        logger.info(f"Navigating to: {url}")
        await page.goto(url, wait_until='domcontentloaded')

        # Wait for page to load
        await asyncio.sleep(5)

        # Take screenshot
        await page.screenshot(path='/tmp/google_maps_debug.png', full_page=True)
        logger.info("Screenshot saved to /tmp/google_maps_debug.png")

        # Get page content
        content = await page.content()
        with open('/tmp/google_maps_page.html', 'w') as f:
            f.write(content)
        logger.info("Page HTML saved to /tmp/google_maps_page.html")

        # Try to find the results container
        try:
            await page.wait_for_selector('div[role="feed"]', timeout=10000)
            logger.info("✓ Found div[role='feed']")

            # Get the HTML of the feed
            feed_html = await page.locator('div[role="feed"]').first.inner_html()
            with open('/tmp/google_maps_feed.html', 'w') as f:
                f.write(feed_html)
            logger.info("Feed HTML saved to /tmp/google_maps_feed.html")

            # Try different selectors
            selectors = [
                'div[role="feed"] > div',
                'div[role="feed"] > div[jsaction]',
                'div[role="feed"] a',
                'div[role="article"]',
                'div.Nv2PK',
                'a[href*="/maps/place/"]',
                '[data-result-index]',
                'div.m6QErb',
                'div.hfpxzc',
            ]

            logger.info("\nTesting selectors:")
            logger.info("-" * 60)
            for selector in selectors:
                count = await page.locator(selector).count()
                logger.info(f"  '{selector}': {count} elements")

        except Exception as e:
            logger.error(f"✗ Error finding feed: {str(e)}")

        await browser.close()
        logger.info("\nDebug complete. Check /tmp/google_maps_*.png and /tmp/google_maps_*.html")


if __name__ == "__main__":
    asyncio.run(debug_google_maps())
