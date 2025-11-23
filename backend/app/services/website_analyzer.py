"""
Website Analyzer Service - AI-powered website analysis and improvement recommendations.

Uses OpenRouter (GPT-4, Claude, Qwen, Grok) to analyze websites for:
- Design (color scheme, typography, layout, visual hierarchy)
- SEO (meta tags, headers, alt text, linking, mobile-friendly)
- Performance (load time, bundle size, image optimization)
- Accessibility (ARIA, keyboard nav, color contrast, screen reader)

Generates prioritized improvement recommendations with code examples.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.openrouter_client import get_openrouter_client
from app.models.website_analysis import WebsiteAnalysis, AnalysisStatus
from app.schemas.website_analysis import (
    CategoryScore,
    ImprovementRecommendation,
    Priority,
    Difficulty,
    Category,
    TechnicalMetrics,
    SEOMetrics,
)

logger = logging.getLogger(__name__)


class WebsiteAnalyzer:
    """
    Comprehensive website analyzer using AI.

    Flow:
    1. Fetch HTML + screenshot
    2. Extract technical metrics (load time, resource counts)
    3. Parse SEO elements (meta tags, headers, etc.)
    4. Run AI analysis via OpenRouter
    5. Generate structured improvement plan
    6. Calculate overall score
    """

    def __init__(self):
        """Initialize the analyzer."""
        self.openrouter_client = get_openrouter_client()
        self.browser: Optional[Browser] = None

    async def analyze_website(
        self,
        url: str,
        db: AsyncSession,
        depth: str = "comprehensive",
        include_screenshot: bool = True,
        ai_model: Optional[str] = None,
        store_html: bool = False,
    ) -> WebsiteAnalysis:
        """
        Analyze a website and generate improvement recommendations.

        Args:
            url: Website URL to analyze
            db: Database session
            depth: Analysis depth ("quick" or "comprehensive")
            include_screenshot: Whether to capture screenshot
            ai_model: Specific AI model to use (defaults to GPT-4)
            store_html: Whether to store full HTML content

        Returns:
            WebsiteAnalysis object with complete analysis
        """
        start_time = time.time()

        # Create analysis record
        analysis = WebsiteAnalysis(
            url=url,
            domain=urlparse(url).netloc,
            status=AnalysisStatus.PROCESSING,
            depth=depth,
            ai_model=ai_model or settings.AI_MODEL_DEFAULT,
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        try:
            logger.info(f"Starting {depth} analysis for {url}")

            # Step 1: Fetch HTML and metrics
            html_content, page_metrics = await self._fetch_html_with_metrics(url)

            # Step 2: Capture screenshot
            screenshot_path = None
            if include_screenshot:
                screenshot_path = await self._capture_screenshot(url, analysis.id)

            # Step 3: Parse HTML for technical analysis
            soup = BeautifulSoup(html_content, 'html.parser')
            technical_metrics = self._extract_technical_metrics(soup, page_metrics)
            seo_metrics = await self._extract_seo_metrics(url, soup)

            # Step 4: AI Analysis
            logger.info(f"Running AI analysis for {url}")
            ai_analysis = await self._run_ai_analysis(
                url=url,
                html_content=html_content[:50000],  # Limit to avoid token limits
                soup=soup,
                technical_metrics=technical_metrics,
                seo_metrics=seo_metrics,
                depth=depth,
                model=ai_model,
            )

            # Step 5: Update analysis record
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            analysis.processing_time_seconds = time.time() - start_time

            # Store title
            title_tag = soup.find('title')
            analysis.title = title_tag.get_text() if title_tag else None

            # Store scores
            analysis.overall_score = ai_analysis['overall_score']
            analysis.design_score = ai_analysis['design']['score']
            analysis.seo_score = ai_analysis['seo']['score']
            analysis.performance_score = ai_analysis['performance']['score']
            analysis.accessibility_score = ai_analysis['accessibility']['score']

            # Store detailed analysis
            analysis.design_analysis = ai_analysis['design']
            analysis.seo_analysis = ai_analysis['seo']
            analysis.performance_analysis = ai_analysis['performance']
            analysis.accessibility_analysis = ai_analysis['accessibility']

            # Store improvements
            analysis.improvements = ai_analysis['improvements']

            # Store technical metrics
            analysis.page_load_time_ms = technical_metrics.get('page_load_time_ms')
            analysis.page_size_kb = technical_metrics.get('page_size_kb')
            analysis.num_requests = technical_metrics.get('num_requests')
            analysis.num_images = technical_metrics.get('num_images')
            analysis.num_scripts = technical_metrics.get('num_scripts')
            analysis.num_stylesheets = technical_metrics.get('num_stylesheets')
            analysis.word_count = technical_metrics.get('word_count')
            analysis.heading_count = technical_metrics.get('heading_count')
            analysis.link_count = technical_metrics.get('link_count')

            # Store SEO metrics
            analysis.meta_title = seo_metrics.get('meta_title')
            analysis.meta_description = seo_metrics.get('meta_description')
            analysis.has_favicon = seo_metrics.get('has_favicon', False)
            analysis.has_robots_txt = seo_metrics.get('has_robots_txt', False)
            analysis.has_sitemap = seo_metrics.get('has_sitemap', False)
            analysis.is_mobile_friendly = seo_metrics.get('is_mobile_friendly', False)
            analysis.has_ssl = url.startswith('https://')

            # Store screenshot
            if screenshot_path:
                analysis.screenshot_path = screenshot_path
                analysis.screenshot_url = f"/api/v1/website-analysis/{analysis.id}/screenshot"

            # Store HTML if requested
            if store_html:
                analysis.html_content = html_content[:100000]  # Limit size

            # Store AI cost estimate
            analysis.ai_cost = self._estimate_cost(html_content, ai_model)

            await db.commit()
            await db.refresh(analysis)

            logger.info(
                f"Analysis completed for {url}. Overall score: {analysis.overall_score}. "
                f"Time: {analysis.processing_time_seconds:.2f}s"
            )

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed for {url}: {str(e)}", exc_info=True)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            analysis.error_code = type(e).__name__
            analysis.processing_time_seconds = time.time() - start_time
            await db.commit()
            raise

    async def _fetch_html_with_metrics(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Fetch HTML content and measure page metrics using Playwright.

        Returns:
            Tuple of (html_content, metrics)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=settings.SCRAPER_USER_AGENT,
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                start_time = time.time()

                # Navigate to page
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                load_time_ms = int((time.time() - start_time) * 1000)

                # Get HTML content
                html_content = await page.content()

                # Get metrics
                metrics = {
                    'page_load_time_ms': load_time_ms,
                    'status_code': response.status if response else None,
                }

                return html_content, metrics

            except PlaywrightTimeout:
                raise Exception(f"Timeout loading {url}")
            except Exception as e:
                raise Exception(f"Failed to fetch {url}: {str(e)}")
            finally:
                await browser.close()

    async def _capture_screenshot(self, url: str, analysis_id: int) -> str:
        """
        Capture a screenshot of the website.

        Args:
            url: Website URL
            analysis_id: Analysis ID for file naming

        Returns:
            Path to saved screenshot
        """
        import os
        from pathlib import Path

        # Create screenshots directory
        screenshots_dir = Path(settings.EXPORT_DIRECTORY) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshots_dir / f"analysis_{analysis_id}.png"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
                return str(screenshot_path)

            except Exception as e:
                logger.error(f"Screenshot failed for {url}: {str(e)}")
                return None
            finally:
                await browser.close()

    def _extract_technical_metrics(
        self, soup: BeautifulSoup, page_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract technical metrics from parsed HTML.

        Args:
            soup: BeautifulSoup parsed HTML
            page_metrics: Metrics from page load

        Returns:
            Dictionary of technical metrics
        """
        # Count elements
        images = soup.find_all('img')
        scripts = soup.find_all('script')
        stylesheets = soup.find_all('link', rel='stylesheet')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        links = soup.find_all('a')

        # Count words in visible text
        text = soup.get_text()
        words = text.split()
        word_count = len([w for w in words if len(w) > 0])

        # Estimate page size
        html_size_kb = len(str(soup)) // 1024

        return {
            'page_load_time_ms': page_metrics.get('page_load_time_ms'),
            'page_size_kb': html_size_kb,
            'num_requests': len(scripts) + len(stylesheets) + len(images),
            'num_images': len(images),
            'num_scripts': len(scripts),
            'num_stylesheets': len(stylesheets),
            'word_count': word_count,
            'heading_count': len(headings),
            'link_count': len(links),
        }

    async def _extract_seo_metrics(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract SEO-specific metrics.

        Args:
            url: Website URL
            soup: BeautifulSoup parsed HTML

        Returns:
            Dictionary of SEO metrics
        """
        # Meta tags
        meta_title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})

        # Favicon
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')

        # Check for robots.txt and sitemap
        domain = urlparse(url).scheme + "://" + urlparse(url).netloc
        has_robots_txt = False
        has_sitemap = False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                robots_response = await client.get(f"{domain}/robots.txt")
                has_robots_txt = robots_response.status_code == 200

                sitemap_response = await client.get(f"{domain}/sitemap.xml")
                has_sitemap = sitemap_response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to check robots.txt/sitemap: {str(e)}")

        # Mobile-friendly check (basic - check for viewport meta)
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        is_mobile_friendly = viewport is not None

        return {
            'meta_title': meta_title.get_text() if meta_title else None,
            'meta_description': meta_description.get('content') if meta_description else None,
            'has_favicon': favicon is not None,
            'has_robots_txt': has_robots_txt,
            'has_sitemap': has_sitemap,
            'is_mobile_friendly': is_mobile_friendly,
        }

    async def _run_ai_analysis(
        self,
        url: str,
        html_content: str,
        soup: BeautifulSoup,
        technical_metrics: Dict[str, Any],
        seo_metrics: Dict[str, Any],
        depth: str,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run AI analysis using OpenRouter.

        Args:
            url: Website URL
            html_content: Raw HTML content (truncated)
            soup: BeautifulSoup parsed HTML
            technical_metrics: Technical metrics
            seo_metrics: SEO metrics
            depth: Analysis depth
            model: AI model to use

        Returns:
            Structured analysis results
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            url, html_content, soup, technical_metrics, seo_metrics, depth
        )

        # System message
        system_message = """You are an expert website analyst specializing in UX design, SEO, web performance, and accessibility.

Analyze websites and provide actionable improvement recommendations with:
1. Scores (0-100) for design, SEO, performance, and accessibility
2. Specific strengths and weaknesses
3. Prioritized improvements with code examples
4. Realistic difficulty and impact estimates

Return your analysis as valid JSON following this exact structure:
{
  "overall_score": 0-100,
  "design": {
    "score": 0-100,
    "summary": "Brief summary",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "details": {
      "color_scheme": "analysis",
      "typography": "analysis",
      "layout": "analysis",
      "visual_hierarchy": "analysis"
    }
  },
  "seo": {
    "score": 0-100,
    "summary": "Brief summary",
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "details": {
      "meta_tags": "analysis",
      "headers": "analysis",
      "content_structure": "analysis"
    }
  },
  "performance": {
    "score": 0-100,
    "summary": "Brief summary",
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "details": {
      "load_time": "analysis",
      "resource_optimization": "analysis"
    }
  },
  "accessibility": {
    "score": 0-100,
    "summary": "Brief summary",
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "details": {
      "aria": "analysis",
      "keyboard_nav": "analysis",
      "color_contrast": "analysis"
    }
  },
  "improvements": [
    {
      "id": "unique-id",
      "category": "design|seo|performance|accessibility",
      "priority": "high|medium|low",
      "difficulty": "easy|medium|hard",
      "title": "Short title",
      "description": "Detailed description",
      "impact": "Expected impact",
      "code_example": "Code example or null",
      "estimated_time": "Time estimate",
      "resources": ["link1", "link2"]
    }
  ]
}

Be honest, specific, and actionable. Focus on high-impact improvements."""

        try:
            # Call OpenRouter
            response_text = await self.openrouter_client.generate_completion(
                prompt=prompt,
                system_message=system_message,
                model=model or settings.AI_MODEL_DEFAULT,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            # Parse JSON response
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            analysis = json.loads(response_text)

            # Validate and ensure all required fields exist
            analysis = self._validate_analysis_response(analysis)

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:1000]}")
            # Return fallback analysis
            return self._generate_fallback_analysis(technical_metrics, seo_metrics)
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._generate_fallback_analysis(technical_metrics, seo_metrics)

    def _build_analysis_prompt(
        self,
        url: str,
        html_content: str,
        soup: BeautifulSoup,
        technical_metrics: Dict[str, Any],
        seo_metrics: Dict[str, Any],
        depth: str,
    ) -> str:
        """Build the analysis prompt for the AI."""
        # Extract key HTML snippets
        head = soup.find('head')
        head_html = str(head)[:2000] if head else "No <head> found"

        body_sample = str(soup.find('body'))[:3000] if soup.find('body') else "No <body> found"

        prompt = f"""Analyze this website and provide comprehensive feedback:

URL: {url}

TECHNICAL METRICS:
- Load time: {technical_metrics.get('page_load_time_ms', 'Unknown')}ms
- Page size: {technical_metrics.get('page_size_kb', 'Unknown')}KB
- Images: {technical_metrics.get('num_images', 0)}
- Scripts: {technical_metrics.get('num_scripts', 0)}
- Stylesheets: {technical_metrics.get('num_stylesheets', 0)}
- Word count: {technical_metrics.get('word_count', 0)}
- Headings: {technical_metrics.get('heading_count', 0)}
- Links: {technical_metrics.get('link_count', 0)}

SEO METRICS:
- Meta title: {seo_metrics.get('meta_title', 'Missing')}
- Meta description: {seo_metrics.get('meta_description', 'Missing')}
- Has favicon: {seo_metrics.get('has_favicon', False)}
- Has robots.txt: {seo_metrics.get('has_robots_txt', False)}
- Has sitemap: {seo_metrics.get('has_sitemap', False)}
- Mobile-friendly: {seo_metrics.get('is_mobile_friendly', False)}

HTML HEAD:
{head_html}

HTML BODY SAMPLE:
{body_sample}

Please analyze this website for:
1. DESIGN: Color scheme, typography, layout, spacing, visual hierarchy
2. SEO: Meta tags, headers, content structure, mobile-friendliness
3. PERFORMANCE: Load time, resource optimization, image optimization
4. ACCESSIBILITY: ARIA labels, keyboard navigation, color contrast, semantic HTML

Provide 5-10 prioritized improvement recommendations with code examples where applicable.
Focus on {"quick wins and major issues" if depth == "quick" else "comprehensive analysis with detailed recommendations"}.

Return your response as valid JSON matching the specified structure."""

        return prompt

    def _validate_analysis_response(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the AI analysis response."""
        # Ensure all required keys exist
        required_keys = ['overall_score', 'design', 'seo', 'performance', 'accessibility', 'improvements']
        for key in required_keys:
            if key not in analysis:
                logger.warning(f"Missing key in analysis: {key}")
                if key == 'improvements':
                    analysis[key] = []
                elif key == 'overall_score':
                    analysis[key] = 50.0
                else:
                    analysis[key] = {
                        'score': 50.0,
                        'summary': 'Analysis incomplete',
                        'strengths': [],
                        'weaknesses': [],
                        'details': {}
                    }

        # Ensure scores are valid
        for category in ['design', 'seo', 'performance', 'accessibility']:
            if 'score' not in analysis[category]:
                analysis[category]['score'] = 50.0
            else:
                # Clamp to 0-100
                analysis[category]['score'] = max(0, min(100, analysis[category]['score']))

        # Calculate overall score if missing
        if 'overall_score' not in analysis or analysis['overall_score'] is None:
            scores = [
                analysis['design']['score'],
                analysis['seo']['score'],
                analysis['performance']['score'],
                analysis['accessibility']['score'],
            ]
            analysis['overall_score'] = sum(scores) / len(scores)

        return analysis

    def _generate_fallback_analysis(
        self, technical_metrics: Dict[str, Any], seo_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a basic fallback analysis when AI fails.

        Args:
            technical_metrics: Technical metrics
            seo_metrics: SEO metrics

        Returns:
            Basic analysis structure
        """
        # Calculate basic scores based on metrics
        performance_score = self._calculate_performance_score(technical_metrics)
        seo_score = self._calculate_seo_score(seo_metrics)

        return {
            'overall_score': (performance_score + seo_score) / 2,
            'design': {
                'score': 50.0,
                'summary': 'Manual review recommended',
                'strengths': [],
                'weaknesses': ['AI analysis unavailable'],
                'details': {}
            },
            'seo': {
                'score': seo_score,
                'summary': 'Basic SEO check completed',
                'strengths': [k for k, v in seo_metrics.items() if v is True],
                'weaknesses': [k for k, v in seo_metrics.items() if v is False],
                'details': seo_metrics
            },
            'performance': {
                'score': performance_score,
                'summary': 'Basic performance check completed',
                'strengths': [],
                'weaknesses': [],
                'details': technical_metrics
            },
            'accessibility': {
                'score': 50.0,
                'summary': 'Manual review recommended',
                'strengths': [],
                'weaknesses': ['AI analysis unavailable'],
                'details': {}
            },
            'improvements': [
                {
                    'id': 'fallback-1',
                    'category': 'seo',
                    'priority': 'high',
                    'difficulty': 'easy',
                    'title': 'Complete AI analysis',
                    'description': 'AI analysis was unavailable. Please retry for detailed recommendations.',
                    'impact': 'Full analysis will provide actionable improvements',
                    'code_example': None,
                    'estimated_time': 'N/A',
                    'resources': []
                }
            ]
        }

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate basic performance score from metrics."""
        score = 100.0

        # Penalize slow load times
        load_time = metrics.get('page_load_time_ms', 0)
        if load_time > 3000:
            score -= 30
        elif load_time > 1500:
            score -= 15

        # Penalize large page size
        page_size = metrics.get('page_size_kb', 0)
        if page_size > 2000:
            score -= 20
        elif page_size > 1000:
            score -= 10

        return max(0, score)

    def _calculate_seo_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate basic SEO score from metrics."""
        score = 0.0
        checks = [
            'meta_title',
            'meta_description',
            'has_favicon',
            'has_robots_txt',
            'has_sitemap',
            'is_mobile_friendly',
        ]

        for check in checks:
            if metrics.get(check):
                score += 100 / len(checks)

        return score

    def _estimate_cost(self, html_content: str, model: Optional[str]) -> float:
        """
        Estimate the cost of AI analysis.

        Args:
            html_content: HTML content
            model: Model used

        Returns:
            Estimated cost in USD
        """
        # Rough token estimation (1 token ≈ 4 characters)
        input_tokens = len(html_content[:50000]) / 4
        output_tokens = 2000  # Typical output

        # Cost estimates per 1M tokens (as of 2024)
        costs = {
            'openai/gpt-4-turbo-preview': {'input': 10.0, 'output': 30.0},
            'anthropic/claude-3.5-sonnet': {'input': 3.0, 'output': 15.0},
            'qwen/qwen-2.5-72b-instruct': {'input': 0.36, 'output': 0.36},
            'x-ai/grok-beta': {'input': 5.0, 'output': 15.0},
        }

        model = model or settings.AI_MODEL_DEFAULT
        model_costs = costs.get(model, {'input': 5.0, 'output': 15.0})

        input_cost = (input_tokens / 1_000_000) * model_costs['input']
        output_cost = (output_tokens / 1_000_000) * model_costs['output']

        return round(input_cost + output_cost, 4)


# Singleton instance
_analyzer: Optional[WebsiteAnalyzer] = None


def get_website_analyzer() -> WebsiteAnalyzer:
    """Get or create website analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = WebsiteAnalyzer()
    return _analyzer
