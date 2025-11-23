"""
Website Analyzer - Extract and analyze websites for lead generation.

Uses Playwright to scrape websites and AI Council to analyze content.
Integrates with existing Craigslist scraper infrastructure.

Phase 3 Enhancement: Added comprehensive design, SEO, performance, and accessibility analysis.
"""

import asyncio
import re
import json
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import structlog

from app.services.ai_mvp.ai_council import AICouncil, TaskType, Message
from app.core.config import settings

logger = structlog.get_logger(__name__)


class WebsiteAnalyzer:
    """
    Analyze websites using Playwright + AI Council.

    Features:
    - Clean HTML extraction
    - Remove scripts, styles, navigation
    - Extract main content
    - AI-powered business analysis
    - Cost-optimized via semantic routing
    """

    def __init__(self, ai_council: AICouncil, headless: bool = True):
        """Initialize website analyzer."""
        self.ai_council = ai_council
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
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

        logger.info("website_analyzer.started", headless=self.headless)

    async def close(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("website_analyzer.closed")

    async def fetch_website(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """
        Fetch website content using Playwright.

        Args:
            url: Website URL to fetch
            timeout: Timeout in milliseconds (default: 30s)

        Returns:
            Dict with url, html, title, meta_description, cleaned_text
        """
        if not self.browser:
            await self.start()

        logger.info("website_analyzer.fetching", url=url)

        try:
            # Create new page with user agent
            context = await self.browser.new_context(
                user_agent=settings.SCRAPER_USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            # Navigate to URL
            response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            if not response:
                raise Exception(f"Failed to load {url}")

            if response.status >= 400:
                raise Exception(f"HTTP {response.status} for {url}")

            # Wait for page to load
            await page.wait_for_load_state("networkidle", timeout=timeout)

            # Extract metadata
            title = await page.title()

            # Get meta description
            meta_description = await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.getAttribute('content') : '';
                }
            """)

            # Get full HTML
            html = await page.content()

            # Extract cleaned text (remove scripts, styles, nav, footer)
            cleaned_text = await self._extract_clean_text(page)

            await page.close()
            await context.close()

            logger.info(
                "website_analyzer.fetched",
                url=url,
                status=response.status,
                title_length=len(title),
                html_length=len(html),
                text_length=len(cleaned_text)
            )

            return {
                "url": url,
                "html": html,
                "title": title,
                "meta_description": meta_description,
                "cleaned_text": cleaned_text,
                "status_code": response.status
            }

        except Exception as e:
            logger.error("website_analyzer.fetch_failed", url=url, error=str(e))
            raise

    async def _extract_clean_text(self, page: Page) -> str:
        """
        Extract clean text from page (remove scripts, styles, nav, footer).

        Args:
            page: Playwright page object

        Returns:
            Cleaned text content
        """
        cleaned_text = await page.evaluate("""
            () => {
                // Remove unwanted elements
                const unwanted = document.querySelectorAll(
                    'script, style, nav, header, footer, .navigation, .menu, .sidebar, .advertisement, [role="navigation"]'
                );
                unwanted.forEach(el => el.remove());

                // Get main content
                const main = document.querySelector('main, [role="main"], article, .content, .main-content, #content, #main');
                const content = main ? main.innerText : document.body.innerText;

                // Clean up whitespace
                return content
                    .replace(/\\s+/g, ' ')           // Multiple spaces → single space
                    .replace(/\\n\\s*\\n/g, '\\n')   // Multiple newlines → single newline
                    .trim();
            }
        """)

        return cleaned_text

    async def analyze_website(
        self,
        url: str,
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None,
        fetch_timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Fetch and analyze website with AI.

        Args:
            url: Website URL
            lead_id: Associated lead ID (for tracking)
            lead_value: Estimated lead value (for routing)
            fetch_timeout: Fetch timeout in ms

        Returns:
            Dict with website data + AI analysis
        """
        logger.info("website_analyzer.analyzing", url=url, lead_value=lead_value)

        # Step 1: Fetch website
        website_data = await self.fetch_website(url, timeout=fetch_timeout)

        # Step 2: Prepare content for AI (use cleaned_text, limit to ~15K chars)
        content_for_ai = website_data["cleaned_text"][:15000]

        if not content_for_ai.strip():
            # Fallback to HTML if cleaned text is empty
            content_for_ai = self._clean_html(website_data["html"])[:15000]

        # Step 3: Analyze with AI Council
        ai_response = await self.ai_council.analyze_website(
            url=url,
            html_content=content_for_ai,
            lead_id=lead_id,
            lead_value=lead_value
        )

        # Step 4: Combine results
        result = {
            "url": url,
            "title": website_data["title"],
            "meta_description": website_data["meta_description"],
            "status_code": website_data["status_code"],
            "content_length": len(website_data["cleaned_text"]),
            "ai_analysis": ai_response.content,
            "ai_model": ai_response.model_used,
            "ai_cost": ai_response.total_cost,
            "ai_request_id": ai_response.request_id,
            "lead_id": lead_id,
            "lead_value": lead_value
        }

        logger.info(
            "website_analyzer.complete",
            url=url,
            model=ai_response.model_used,
            cost=ai_response.total_cost
        )

        return result

    def _clean_html(self, html: str) -> str:
        """
        Clean HTML by removing tags (simple version for fallback).

        Args:
            html: Raw HTML

        Returns:
            Text without HTML tags
        """
        # Remove script and style tags with content
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        html = re.sub(r'<[^>]+>', ' ', html)

        # Clean up whitespace
        html = re.sub(r'\s+', ' ', html)

        return html.strip()

    async def analyze_multiple_websites(
        self,
        urls: list[str],
        lead_values: Optional[list[float]] = None,
        max_concurrent: int = 3
    ) -> list[Dict[str, Any]]:
        """
        Analyze multiple websites concurrently.

        Args:
            urls: List of URLs to analyze
            lead_values: Optional list of lead values (same order as urls)
            max_concurrent: Max concurrent requests

        Returns:
            List of analysis results
        """
        if lead_values and len(lead_values) != len(urls):
            raise ValueError("lead_values must match urls length")

        logger.info("website_analyzer.batch_start", total=len(urls))

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(url: str, lead_value: Optional[float]):
            async with semaphore:
                try:
                    return await self.analyze_website(url, lead_value=lead_value)
                except Exception as e:
                    logger.error("website_analyzer.batch_error", url=url, error=str(e))
                    return {
                        "url": url,
                        "error": str(e),
                        "lead_value": lead_value
                    }

        # Run analyses
        tasks = [
            analyze_with_semaphore(url, lead_values[i] if lead_values else None)
            for i, url in enumerate(urls)
        ]

        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if "error" not in r)
        logger.info(
            "website_analyzer.batch_complete",
            total=len(urls),
            success=success_count,
            failed=len(urls) - success_count
        )

        return results

    # ==================== PHASE 3: ENHANCED ANALYSIS METHODS ====================

    async def analyze_design_quality(
        self,
        url: str,
        html: Optional[str] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze website design quality.

        Args:
            url: Website URL
            html: Optional pre-fetched HTML (avoids re-fetching)
            use_ai: Use AI for subjective design assessment

        Returns:
            Dict with design score, issues, and strengths
        """
        logger.info("website_analyzer.design_analysis", url=url)

        # Fetch if not provided
        if not html:
            website_data = await self.fetch_website(url)
            html = website_data["html"]

        soup = BeautifulSoup(html, 'html.parser')

        # Technical analysis
        design_metrics = {
            "layout_type": self._detect_layout_type(soup),
            "color_scheme": self._analyze_colors(soup, html),
            "typography": self._analyze_typography(soup),
            "visual_hierarchy": self._analyze_visual_hierarchy(soup),
            "whitespace": self._analyze_whitespace(soup),
            "responsiveness": self._check_responsiveness(soup)
        }

        # Calculate technical score (0-100)
        technical_score = self._calculate_design_score(design_metrics)

        issues = []
        strengths = []

        # Identify issues and strengths
        if not design_metrics["responsiveness"]["has_viewport"]:
            issues.append("Missing viewport meta tag - not mobile optimized")
        else:
            strengths.append("Mobile-responsive viewport configured")

        if design_metrics["typography"]["font_count"] > 4:
            issues.append(f"Too many fonts ({design_metrics['typography']['font_count']}) - reduces consistency")
        elif design_metrics["typography"]["font_count"] >= 2:
            strengths.append("Good font variety without overuse")

        if design_metrics["whitespace"]["density"] > 0.8:
            issues.append("Very dense layout - lacks breathing room")
        elif design_metrics["whitespace"]["density"] < 0.4:
            strengths.append("Good use of whitespace")

        if design_metrics["color_scheme"]["color_count"] > 10:
            issues.append(f"Too many colors ({design_metrics['color_scheme']['color_count']}) - may lack cohesion")

        # AI-powered subjective assessment
        ai_assessment = None
        if use_ai and self.ai_council:
            try:
                # Take screenshot for visual analysis
                if not self.browser:
                    await self.start()

                context = await self.browser.new_context(
                    viewport={"width": 1920, "height": 1080}
                )
                page = await context.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=30000)

                # Get computed styles for AI analysis
                design_context = await page.evaluate("""
                    () => {
                        const styles = window.getComputedStyle(document.body);
                        return {
                            backgroundColor: styles.backgroundColor,
                            fontFamily: styles.fontFamily,
                            fontSize: styles.fontSize,
                            lineHeight: styles.lineHeight
                        };
                    }
                """)

                await page.close()
                await context.close()

                # Ask AI to evaluate design
                ai_response = await self._ai_design_assessment(
                    url, design_metrics, design_context, technical_score
                )
                ai_assessment = ai_response.content

            except Exception as e:
                logger.warning("design_analysis.ai_failed", error=str(e))

        return {
            "score": technical_score,
            "issues": issues,
            "strengths": strengths,
            "metrics": design_metrics,
            "ai_assessment": ai_assessment
        }

    async def analyze_seo(
        self,
        url: str,
        html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive SEO audit.

        Args:
            url: Website URL
            html: Optional pre-fetched HTML

        Returns:
            Dict with SEO score, issues, and strengths
        """
        logger.info("website_analyzer.seo_analysis", url=url)

        if not html:
            website_data = await self.fetch_website(url)
            html = website_data["html"]

        soup = BeautifulSoup(html, 'html.parser')

        # Meta tags analysis
        title_tag = soup.find('title')
        title = title_tag.get_text() if title_tag else None
        title_length = len(title) if title else 0

        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content') if meta_description else None
        description_length = len(description) if description else 0

        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        has_keywords = meta_keywords is not None

        # Heading structure
        headings = {
            'h1': len(soup.find_all('h1')),
            'h2': len(soup.find_all('h2')),
            'h3': len(soup.find_all('h3')),
            'h4': len(soup.find_all('h4')),
            'h5': len(soup.find_all('h5')),
            'h6': len(soup.find_all('h6'))
        }

        # Image analysis
        images = soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt'))
        alt_coverage = (images_with_alt / len(images) * 100) if images else 100

        # Link analysis
        all_links = soup.find_all('a', href=True)
        internal_links = []
        external_links = []

        base_domain = urlparse(url).netloc
        for link in all_links:
            href = link.get('href', '')
            link_domain = urlparse(urljoin(url, href)).netloc
            if link_domain == base_domain or not link_domain:
                internal_links.append(href)
            else:
                external_links.append(href)

        # Mobile-friendliness
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        is_mobile_friendly = viewport is not None

        # Schema markup
        schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
        has_schema = len(schema_scripts) > 0

        # Open Graph tags
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        has_og_tags = len(og_tags) > 0

        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        has_canonical = canonical is not None

        # Calculate SEO score
        score = 0
        issues = []
        strengths = []

        # Title (20 points)
        if not title:
            issues.append("Missing title tag")
        elif title_length < 30:
            issues.append(f"Title too short ({title_length} chars) - recommend 50-60")
            score += 10
        elif title_length > 60:
            issues.append(f"Title too long ({title_length} chars) - may be truncated")
            score += 15
        else:
            strengths.append(f"Good title length ({title_length} chars)")
            score += 20

        # Meta description (20 points)
        if not description:
            issues.append("Missing meta description")
        elif description_length < 120:
            issues.append(f"Meta description too short ({description_length} chars)")
            score += 10
        elif description_length > 160:
            issues.append(f"Meta description too long ({description_length} chars)")
            score += 15
        else:
            strengths.append(f"Good meta description length ({description_length} chars)")
            score += 20

        # H1 tags (15 points)
        if headings['h1'] == 0:
            issues.append("No H1 tag found")
        elif headings['h1'] > 1:
            issues.append(f"Multiple H1 tags ({headings['h1']}) - should have exactly one")
            score += 10
        else:
            strengths.append("Proper H1 usage")
            score += 15

        # Image alt tags (15 points)
        if len(images) > 0:
            if alt_coverage < 50:
                issues.append(f"Poor image alt text coverage ({alt_coverage:.0f}%)")
                score += int(alt_coverage / 100 * 15)
            elif alt_coverage < 100:
                issues.append(f"Some images missing alt text ({alt_coverage:.0f}% coverage)")
                score += int(alt_coverage / 100 * 15)
            else:
                strengths.append("All images have alt text")
                score += 15
        else:
            score += 15  # No images, no problem

        # Mobile-friendly (10 points)
        if is_mobile_friendly:
            strengths.append("Mobile-friendly viewport configured")
            score += 10
        else:
            issues.append("Not mobile-friendly - missing viewport meta tag")

        # Schema markup (10 points)
        if has_schema:
            strengths.append("Schema markup detected")
            score += 10
        else:
            issues.append("No schema markup found - missing rich snippet opportunity")

        # Open Graph (5 points)
        if has_og_tags:
            strengths.append("Open Graph tags present")
            score += 5
        else:
            issues.append("Missing Open Graph tags for social sharing")

        # Canonical URL (5 points)
        if has_canonical:
            strengths.append("Canonical URL specified")
            score += 5
        else:
            issues.append("No canonical URL - may cause duplicate content issues")

        return {
            "score": score,
            "issues": issues,
            "strengths": strengths,
            "details": {
                "title": {
                    "text": title,
                    "length": title_length,
                    "optimal": 50 <= title_length <= 60 if title else False
                },
                "meta_description": {
                    "text": description,
                    "length": description_length,
                    "optimal": 120 <= description_length <= 160 if description else False
                },
                "headings": headings,
                "images": {
                    "total": len(images),
                    "with_alt": images_with_alt,
                    "alt_coverage": round(alt_coverage, 1)
                },
                "links": {
                    "internal": len(internal_links),
                    "external": len(external_links),
                    "total": len(all_links)
                },
                "mobile_friendly": is_mobile_friendly,
                "schema_markup": has_schema,
                "open_graph": has_og_tags,
                "canonical": has_canonical
            }
        }

    async def analyze_performance(
        self,
        url: str,
        html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze website performance metrics.

        Args:
            url: Website URL
            html: Optional pre-fetched HTML

        Returns:
            Dict with performance score, issues, and strengths
        """
        logger.info("website_analyzer.performance_analysis", url=url)

        if not self.browser:
            await self.start()

        # We need to measure real performance with Playwright
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        # Track performance metrics
        metrics = {}

        try:
            # Measure page load time
            start_time = asyncio.get_event_loop().time()
            response = await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            dom_load_time = asyncio.get_event_loop().time() - start_time

            await page.wait_for_load_state("networkidle", timeout=60000)
            full_load_time = asyncio.get_event_loop().time() - start_time

            # Get performance metrics from browser
            performance_timing = await page.evaluate("""
                () => {
                    const perfData = window.performance.timing;
                    const navigation = window.performance.getEntriesByType('navigation')[0];
                    return {
                        domContentLoadedTime: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                        loadCompleteTime: perfData.loadEventEnd - perfData.navigationStart,
                        domInteractive: perfData.domInteractive - perfData.navigationStart,
                        firstPaint: navigation ? navigation.domContentLoadedEventEnd : null
                    };
                }
            """)

            # Analyze resources
            resource_info = await page.evaluate("""
                () => {
                    const resources = window.performance.getEntriesByType('resource');

                    let totalSize = 0;
                    let scripts = [];
                    let stylesheets = [];
                    let images = [];
                    let fonts = [];
                    let renderBlocking = [];

                    resources.forEach(resource => {
                        const size = resource.transferSize || resource.decodedBodySize || 0;
                        totalSize += size;

                        if (resource.initiatorType === 'script' || resource.name.endsWith('.js')) {
                            scripts.push({ name: resource.name, size: size, duration: resource.duration });
                            if (resource.renderBlockingStatus === 'blocking') {
                                renderBlocking.push(resource.name);
                            }
                        } else if (resource.initiatorType === 'link' || resource.name.endsWith('.css')) {
                            stylesheets.push({ name: resource.name, size: size, duration: resource.duration });
                            if (resource.renderBlockingStatus === 'blocking') {
                                renderBlocking.push(resource.name);
                            }
                        } else if (resource.initiatorType === 'img' || /\\.(jpg|jpeg|png|gif|webp|svg)$/i.test(resource.name)) {
                            images.push({ name: resource.name, size: size });
                        } else if (/\\.(woff|woff2|ttf|otf)$/i.test(resource.name)) {
                            fonts.push({ name: resource.name, size: size });
                        }
                    });

                    return {
                        totalSize: totalSize,
                        resourceCount: resources.length,
                        scripts: scripts,
                        stylesheets: stylesheets,
                        images: images,
                        fonts: fonts,
                        renderBlocking: renderBlocking
                    };
                }
            """)

            # Get HTML for static analysis
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Count inline scripts/styles
            inline_scripts = len(soup.find_all('script', src=False))
            inline_styles = len(soup.find_all('style'))

            await page.close()
            await context.close()

            # Calculate scores and issues
            score = 100
            issues = []
            strengths = []

            # Load time scoring (30 points)
            if full_load_time > 5:
                issues.append(f"Slow page load ({full_load_time:.1f}s) - should be under 3s")
                score -= 20
            elif full_load_time > 3:
                issues.append(f"Moderate load time ({full_load_time:.1f}s)")
                score -= 10
            else:
                strengths.append(f"Fast load time ({full_load_time:.1f}s)")

            # Resource size (20 points)
            total_mb = resource_info['totalSize'] / 1024 / 1024
            if total_mb > 5:
                issues.append(f"Large page size ({total_mb:.1f}MB) - should be under 3MB")
                score -= 15
            elif total_mb > 3:
                issues.append(f"Moderate page size ({total_mb:.1f}MB)")
                score -= 7
            else:
                strengths.append(f"Optimized page size ({total_mb:.1f}MB)")

            # Script count (15 points)
            script_count = len(resource_info['scripts']) + inline_scripts
            if script_count > 20:
                issues.append(f"Too many scripts ({script_count}) - reduces performance")
                score -= 12
            elif script_count > 10:
                issues.append(f"Moderate script count ({script_count})")
                score -= 5
            else:
                strengths.append(f"Reasonable script count ({script_count})")

            # Stylesheet count (10 points)
            style_count = len(resource_info['stylesheets']) + inline_styles
            if style_count > 10:
                issues.append(f"Too many stylesheets ({style_count})")
                score -= 8
            elif style_count > 5:
                issues.append(f"Moderate stylesheet count ({style_count})")
                score -= 3
            else:
                strengths.append(f"Minimal stylesheets ({style_count})")

            # Image optimization (15 points)
            large_images = [img for img in resource_info['images'] if img['size'] > 500000]
            if large_images:
                issues.append(f"{len(large_images)} unoptimized images over 500KB")
                score -= min(15, len(large_images) * 3)
            else:
                strengths.append("Images appear optimized")

            # Render-blocking resources (10 points)
            if len(resource_info['renderBlocking']) > 0:
                issues.append(f"{len(resource_info['renderBlocking'])} render-blocking resources")
                score -= 10
            else:
                strengths.append("No render-blocking resources detected")

            metrics = {
                "load_times": {
                    "dom_content_loaded": round(dom_load_time, 2),
                    "full_load": round(full_load_time, 2),
                    "dom_interactive": round(performance_timing.get('domInteractive', 0) / 1000, 2)
                },
                "resources": {
                    "total_size_mb": round(total_mb, 2),
                    "total_count": resource_info['resourceCount'],
                    "scripts": len(resource_info['scripts']),
                    "stylesheets": len(resource_info['stylesheets']),
                    "images": len(resource_info['images']),
                    "fonts": len(resource_info['fonts']),
                    "inline_scripts": inline_scripts,
                    "inline_styles": inline_styles
                },
                "optimization": {
                    "large_images": len(large_images),
                    "render_blocking": len(resource_info['renderBlocking'])
                }
            }

        except Exception as e:
            logger.error("performance_analysis.failed", url=url, error=str(e))
            await page.close()
            await context.close()
            raise

        return {
            "score": max(0, score),
            "issues": issues,
            "strengths": strengths,
            "metrics": metrics
        }

    async def analyze_accessibility(
        self,
        url: str,
        html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze website accessibility (WCAG compliance).

        Args:
            url: Website URL
            html: Optional pre-fetched HTML

        Returns:
            Dict with accessibility score, issues, and strengths
        """
        logger.info("website_analyzer.accessibility_analysis", url=url)

        if not html:
            website_data = await self.fetch_website(url)
            html = website_data["html"]

        soup = BeautifulSoup(html, 'html.parser')

        score = 100
        issues = []
        strengths = []

        # ARIA labels and roles
        elements_with_aria = soup.find_all(attrs={'aria-label': True})
        elements_with_role = soup.find_all(attrs={'role': True})

        # Semantic HTML
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        semantic_usage = {tag: len(soup.find_all(tag)) for tag in semantic_tags}
        uses_semantic_html = any(count > 0 for count in semantic_usage.values())

        # Form labels
        inputs = soup.find_all(['input', 'select', 'textarea'])
        inputs_with_labels = 0
        for inp in inputs:
            input_id = inp.get('id')
            aria_label = inp.get('aria-label')
            if aria_label or (input_id and soup.find('label', attrs={'for': input_id})):
                inputs_with_labels += 1

        label_coverage = (inputs_with_labels / len(inputs) * 100) if inputs else 100

        # Image alt text (already checked in SEO, but critical for accessibility)
        images = soup.find_all('img')
        images_with_alt = sum(1 for img in images if img.get('alt') is not None)
        alt_coverage = (images_with_alt / len(images) * 100) if images else 100

        # Links with descriptive text
        links = soup.find_all('a')
        links_with_text = sum(1 for link in links if link.get_text(strip=True))
        link_text_coverage = (links_with_text / len(links) * 100) if links else 100

        # Lang attribute
        html_tag = soup.find('html')
        has_lang = html_tag.get('lang') if html_tag else None

        # Skip links
        skip_link = soup.find('a', attrs={'href': '#main'}) or soup.find('a', string=re.compile(r'skip', re.I))
        has_skip_link = skip_link is not None

        # Color contrast (basic check - needs page context for accurate measurement)
        # We'll check for inline styles that might indicate issues
        inline_styles_text = str(soup.find_all(attrs={'style': True}))
        potential_contrast_issues = len(re.findall(r'color:\s*#([0-9a-f]{3}|[0-9a-f]{6})', inline_styles_text, re.I))

        # Keyboard navigation support
        elements_with_tabindex = soup.find_all(attrs={'tabindex': True})

        # Scoring
        # ARIA and roles (20 points)
        if len(elements_with_aria) + len(elements_with_role) == 0:
            issues.append("No ARIA labels or roles found")
            score -= 20
        elif len(elements_with_aria) + len(elements_with_role) < 5:
            issues.append("Limited ARIA usage")
            score -= 10
        else:
            strengths.append(f"Good ARIA usage ({len(elements_with_aria)} labels, {len(elements_with_role)} roles)")

        # Semantic HTML (15 points)
        if not uses_semantic_html:
            issues.append("No semantic HTML5 tags used")
            score -= 15
        else:
            used_tags = [tag for tag, count in semantic_usage.items() if count > 0]
            strengths.append(f"Uses semantic HTML: {', '.join(used_tags)}")

        # Form labels (20 points)
        if len(inputs) > 0:
            if label_coverage < 50:
                issues.append(f"Most form inputs lack labels ({label_coverage:.0f}% coverage)")
                score -= 18
            elif label_coverage < 100:
                issues.append(f"Some form inputs lack labels ({label_coverage:.0f}% coverage)")
                score -= int((100 - label_coverage) / 100 * 20)
            else:
                strengths.append("All form inputs have labels")

        # Image alt text (20 points)
        if len(images) > 0:
            if alt_coverage < 50:
                issues.append(f"Most images lack alt text ({alt_coverage:.0f}% coverage)")
                score -= 18
            elif alt_coverage < 100:
                issues.append(f"Some images lack alt text ({alt_coverage:.0f}% coverage)")
                score -= int((100 - alt_coverage) / 100 * 20)
            else:
                strengths.append("All images have alt text")

        # Link text (10 points)
        if link_text_coverage < 100:
            issues.append(f"Some links lack descriptive text ({link_text_coverage:.0f}% coverage)")
            score -= int((100 - link_text_coverage) / 100 * 10)
        else:
            strengths.append("All links have descriptive text")

        # Lang attribute (5 points)
        if not has_lang:
            issues.append("Missing lang attribute on html tag")
            score -= 5
        else:
            strengths.append(f"Language specified: {has_lang}")

        # Skip link (5 points)
        if not has_skip_link:
            issues.append("No skip navigation link found")
            score -= 5
        else:
            strengths.append("Skip navigation link present")

        # Keyboard navigation (5 points)
        if len(elements_with_tabindex) == 0:
            issues.append("No custom tab order defined")
            score -= 5
        else:
            strengths.append("Custom keyboard navigation implemented")

        return {
            "score": max(0, score),
            "issues": issues,
            "strengths": strengths,
            "details": {
                "aria": {
                    "labels": len(elements_with_aria),
                    "roles": len(elements_with_role)
                },
                "semantic_html": semantic_usage,
                "forms": {
                    "total_inputs": len(inputs),
                    "with_labels": inputs_with_labels,
                    "label_coverage": round(label_coverage, 1)
                },
                "images": {
                    "total": len(images),
                    "with_alt": images_with_alt,
                    "alt_coverage": round(alt_coverage, 1)
                },
                "links": {
                    "total": len(links),
                    "with_text": links_with_text,
                    "text_coverage": round(link_text_coverage, 1)
                },
                "language": has_lang,
                "skip_link": has_skip_link,
                "keyboard_navigation": len(elements_with_tabindex) > 0
            }
        }

    async def analyze_website_comprehensive(
        self,
        url: str,
        include_ai_design: bool = False
    ) -> Dict[str, Any]:
        """
        Perform comprehensive website analysis with all metrics.

        Args:
            url: Website URL
            include_ai_design: Include AI-powered design assessment (slower, costs tokens)

        Returns:
            Dict with design, SEO, performance, and accessibility scores
        """
        logger.info("website_analyzer.comprehensive_analysis", url=url)

        # Fetch website once
        website_data = await self.fetch_website(url)
        html = website_data["html"]

        # Run all analyses (some in parallel where possible)
        design_task = self.analyze_design_quality(url, html, use_ai=include_ai_design)
        seo_task = self.analyze_seo(url, html)
        accessibility_task = self.analyze_accessibility(url, html)

        # Performance needs to be separate (requires fresh page load)
        design, seo, accessibility = await asyncio.gather(
            design_task, seo_task, accessibility_task
        )

        performance = await self.analyze_performance(url)

        # Calculate overall score
        overall_score = (
            design["score"] * 0.25 +
            seo["score"] * 0.30 +
            performance["score"] * 0.25 +
            accessibility["score"] * 0.20
        )

        return {
            "url": url,
            "overall_score": round(overall_score, 1),
            "design": design,
            "seo": seo,
            "performance": performance,
            "accessibility": accessibility,
            "analyzed_at": website_data["status_code"],
            "title": website_data["title"],
            "meta_description": website_data["meta_description"]
        }

    # ==================== HELPER METHODS FOR DESIGN ANALYSIS ====================

    def _detect_layout_type(self, soup: BeautifulSoup) -> str:
        """Detect if site uses grid, flexbox, or traditional layout."""
        # Look for CSS classes/inline styles
        html_text = str(soup)

        if 'display: grid' in html_text or 'display:grid' in html_text:
            return "grid"
        elif 'display: flex' in html_text or 'display:flex' in html_text:
            return "flexbox"
        elif 'float:' in html_text or 'float :' in html_text:
            return "float"
        else:
            return "unknown"

    def _analyze_colors(self, soup: BeautifulSoup, html: str) -> Dict[str, Any]:
        """Extract and analyze color scheme."""
        # Find all color declarations
        colors = set()

        # Inline styles
        inline_styles = soup.find_all(attrs={'style': True})
        for element in inline_styles:
            style = element.get('style', '')
            color_matches = re.findall(r'#([0-9a-f]{3}|[0-9a-f]{6})', style, re.I)
            colors.update(color_matches)

        # Style tags
        style_tags = soup.find_all('style')
        for style in style_tags:
            color_matches = re.findall(r'#([0-9a-f]{3}|[0-9a-f]{6})', style.string or '', re.I)
            colors.update(color_matches)

        return {
            "color_count": len(colors),
            "unique_colors": len(colors),
            "colors": list(colors)[:10]  # First 10
        }

    def _analyze_typography(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze typography usage."""
        # Find font families
        fonts = set()

        # Inline styles
        inline_styles = soup.find_all(attrs={'style': True})
        for element in inline_styles:
            style = element.get('style', '')
            font_matches = re.findall(r'font-family:\s*([^;]+)', style, re.I)
            fonts.update(font_matches)

        # Style tags
        style_tags = soup.find_all('style')
        for style in style_tags:
            font_matches = re.findall(r'font-family:\s*([^;}]+)', style.string or '', re.I)
            fonts.update(font_matches)

        return {
            "font_count": len(fonts),
            "fonts": list(fonts)[:5]  # First 5
        }

    def _analyze_visual_hierarchy(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze heading hierarchy."""
        headings = {
            'h1': len(soup.find_all('h1')),
            'h2': len(soup.find_all('h2')),
            'h3': len(soup.find_all('h3')),
            'h4': len(soup.find_all('h4')),
            'h5': len(soup.find_all('h5')),
            'h6': len(soup.find_all('h6'))
        }

        total_headings = sum(headings.values())
        has_proper_hierarchy = (
            headings['h1'] == 1 and
            (headings['h2'] > 0 or total_headings == 1)
        )

        return {
            "headings": headings,
            "total": total_headings,
            "proper_hierarchy": has_proper_hierarchy
        }

    def _analyze_whitespace(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Estimate whitespace usage (rough approximation)."""
        text_content = soup.get_text()
        html_length = len(str(soup))
        text_length = len(text_content)

        # Rough density: ratio of text to HTML
        density = text_length / html_length if html_length > 0 else 0

        return {
            "density": round(density, 2),
            "estimated_whitespace": "good" if density < 0.4 else "moderate" if density < 0.7 else "poor"
        }

    def _check_responsiveness(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check for responsive design indicators."""
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        has_viewport = viewport is not None

        # Check for media queries in style tags
        style_tags = soup.find_all('style')
        media_queries = 0
        for style in style_tags:
            media_queries += len(re.findall(r'@media', style.string or '', re.I))

        return {
            "has_viewport": has_viewport,
            "viewport_content": viewport.get('content') if viewport else None,
            "media_queries": media_queries,
            "likely_responsive": has_viewport and media_queries > 0
        }

    def _calculate_design_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate design score from metrics."""
        score = 100

        # Layout type (10 points)
        if metrics["layout_type"] in ["grid", "flexbox"]:
            pass  # Modern layout, no deduction
        elif metrics["layout_type"] == "float":
            score -= 5  # Older but acceptable
        else:
            score -= 10  # Unknown/table layout

        # Responsiveness (25 points)
        if not metrics["responsiveness"]["likely_responsive"]:
            score -= 25
        elif not metrics["responsiveness"]["has_viewport"]:
            score -= 15

        # Typography (15 points)
        font_count = metrics["typography"]["font_count"]
        if font_count == 0:
            score -= 10
        elif font_count > 5:
            score -= 10

        # Visual hierarchy (20 points)
        if not metrics["visual_hierarchy"]["proper_hierarchy"]:
            score -= 15
        if metrics["visual_hierarchy"]["total"] == 0:
            score -= 5

        # Colors (10 points)
        color_count = metrics["color_scheme"]["color_count"]
        if color_count > 15:
            score -= 10
        elif color_count > 10:
            score -= 5

        # Whitespace (20 points)
        density = metrics["whitespace"]["density"]
        if density > 0.8:
            score -= 15
        elif density > 0.6:
            score -= 8

        return max(0, score)

    async def _ai_design_assessment(
        self,
        url: str,
        design_metrics: Dict[str, Any],
        design_context: Dict[str, Any],
        technical_score: int
    ) -> Any:
        """Use AI to assess design quality subjectively."""
        messages = [
            Message(
                role="system",
                content="""You are an expert web designer and UX specialist. Evaluate website design quality based on technical metrics and provide actionable feedback.

Focus on:
- Visual appeal and professionalism
- User experience and usability
- Brand consistency
- Call-to-action effectiveness
- Overall design trends (modern vs. outdated)

Be specific and constructive."""
            ),
            Message(
                role="user",
                content=f"""Evaluate the design quality of: {url}

Technical Score: {technical_score}/100

Technical Metrics:
- Layout: {design_metrics['layout_type']}
- Responsive: {design_metrics['responsiveness']['likely_responsive']}
- Colors: {design_metrics['color_scheme']['color_count']} unique colors
- Fonts: {design_metrics['typography']['font_count']} font families
- Whitespace density: {design_metrics['whitespace']['density']}

Computed Styles:
- Background: {design_context.get('backgroundColor')}
- Font: {design_context.get('fontFamily')}
- Font Size: {design_context.get('fontSize')}

Provide:
1. Design quality assessment (2-3 sentences)
2. Top 3 design strengths
3. Top 3 design improvements
4. Overall impression (modern/dated/professional/amateur)"""
            )
        ]

        return await self.ai_council.complete(
            task_type=TaskType.WEBSITE_ANALYSIS,
            messages=messages,
            temperature=0.4
        )


# Utility function for quick analysis without context manager
async def analyze_website_quick(
    url: str,
    ai_council: AICouncil,
    lead_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Quick website analysis (auto-manages browser).

    Args:
        url: Website URL
        ai_council: AI Council instance
        lead_value: Optional lead value for routing

    Returns:
        Analysis result
    """
    async with WebsiteAnalyzer(ai_council) as analyzer:
        return await analyzer.analyze_website(url, lead_value=lead_value)
