"""
Test script for Website Analysis Agent.

Tests the complete website analysis pipeline:
1. Database model creation
2. HTML fetching and metrics extraction
3. AI analysis via OpenRouter
4. Improvement recommendation generation
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import get_db
from app.services.website_analyzer import get_website_analyzer
from app.models.website_analysis import WebsiteAnalysis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_website_analysis():
    """Test website analysis with example.com."""

    logger.info("="*60)
    logger.info("Testing Website Analysis Agent")
    logger.info("="*60)

    # Get analyzer
    analyzer = get_website_analyzer()

    # Get database session
    async for db in get_db():
        try:
            # Test URL
            test_url = "https://example.com"

            logger.info(f"\n1. Analyzing {test_url}...")

            # Run analysis
            analysis = await analyzer.analyze_website(
                url=test_url,
                db=db,
                depth="comprehensive",
                include_screenshot=True,
                store_html=False,
            )

            logger.info(f"\n2. Analysis completed!")
            logger.info(f"   Analysis ID: {analysis.id}")
            logger.info(f"   Status: {analysis.status}")
            logger.info(f"   Overall Score: {analysis.overall_score}/100")
            logger.info(f"   Design Score: {analysis.design_score}/100")
            logger.info(f"   SEO Score: {analysis.seo_score}/100")
            logger.info(f"   Performance Score: {analysis.performance_score}/100")
            logger.info(f"   Accessibility Score: {analysis.accessibility_score}/100")

            logger.info(f"\n3. Technical Metrics:")
            logger.info(f"   Load Time: {analysis.page_load_time_ms}ms")
            logger.info(f"   Page Size: {analysis.page_size_kb}KB")
            logger.info(f"   Images: {analysis.num_images}")
            logger.info(f"   Scripts: {analysis.num_scripts}")
            logger.info(f"   Stylesheets: {analysis.num_stylesheets}")

            logger.info(f"\n4. SEO Metrics:")
            logger.info(f"   Title: {analysis.meta_title}")
            logger.info(f"   Description: {analysis.meta_description}")
            logger.info(f"   Has Favicon: {analysis.has_favicon}")
            logger.info(f"   Has Robots.txt: {analysis.has_robots_txt}")
            logger.info(f"   Has Sitemap: {analysis.has_sitemap}")
            logger.info(f"   Mobile Friendly: {analysis.is_mobile_friendly}")
            logger.info(f"   SSL: {analysis.has_ssl}")

            logger.info(f"\n5. Improvement Recommendations:")
            if analysis.improvements:
                for i, improvement in enumerate(analysis.improvements[:5], 1):
                    logger.info(f"\n   [{i}] {improvement.get('title', 'Unknown')}")
                    logger.info(f"       Category: {improvement.get('category', 'Unknown')}")
                    logger.info(f"       Priority: {improvement.get('priority', 'Unknown')}")
                    logger.info(f"       Difficulty: {improvement.get('difficulty', 'Unknown')}")
                    logger.info(f"       Impact: {improvement.get('impact', 'Unknown')[:100]}...")

                if len(analysis.improvements) > 5:
                    logger.info(f"\n   ... and {len(analysis.improvements) - 5} more recommendations")
            else:
                logger.info("   No recommendations generated")

            logger.info(f"\n6. Cost & Performance:")
            logger.info(f"   AI Cost: ${analysis.ai_cost:.4f}" if analysis.ai_cost else "   AI Cost: N/A")
            logger.info(f"   Processing Time: {analysis.processing_time_seconds:.2f}s" if analysis.processing_time_seconds else "   Processing Time: N/A")

            logger.info(f"\n7. Screenshot:")
            logger.info(f"   Path: {analysis.screenshot_path}")
            logger.info(f"   URL: {analysis.screenshot_url}")

            # Test retrieval
            logger.info(f"\n8. Testing retrieval...")
            result = await db.execute(
                select(WebsiteAnalysis).where(WebsiteAnalysis.id == analysis.id)
            )
            retrieved = result.scalar_one()
            logger.info(f"   Successfully retrieved analysis {retrieved.id}")

            logger.info("\n" + "="*60)
            logger.info("All tests passed!")
            logger.info("="*60)

            return analysis

        except Exception as e:
            logger.error(f"\nTest failed: {str(e)}", exc_info=True)
            raise
        finally:
            break  # Exit the async generator


if __name__ == "__main__":
    asyncio.run(test_website_analysis())
