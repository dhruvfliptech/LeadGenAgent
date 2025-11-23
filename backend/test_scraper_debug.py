"""
Debug script to inspect Google Maps HTML structure.
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
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
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

        # Try to find the results container
        try:
            await page.wait_for_selector('div[role="feed"]', timeout=10000)
            logger.info("Found div[role='feed']")

            # Get the HTML of the feed
            feed_html = await page.locator('div[role="feed"]').first.inner_html()
            with open('/tmp/google_maps_feed.html', 'w') as f:
                f.write(feed_html)
            logger.info("Feed HTML saved to /tmp/google_maps_feed.html")

            # Try different selectors
            selectors = [
                'div[role="feed"] > div',
                'div[role="feed"] a',
                'div[role="article"]',
                'div.Nv2PK',
                'a[href*="/maps/place/"]',
            ]

            for selector in selectors:
                count = await page.locator(selector).count()
                logger.info(f"Selector '{selector}': found {count} elements")

        except Exception as e:
            logger.error(f"Error: {str(e)}")

        # Keep browser open for inspection
        logger.info("Browser will stay open for 30 seconds for inspection...")
        await asyncio.sleep(30)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_google_maps())
