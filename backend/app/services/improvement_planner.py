"""
Website Improvement Plan Generator - Phase 3 Task 2

Generates actionable, prioritized improvement plans based on website analysis results.
Uses AI to create specific, concrete recommendations with estimated impact.

Features:
- Prioritized improvements (high/medium/low)
- Specific actionable changes with code examples
- Estimated impact and implementation difficulty
- AI-powered creative suggestions via OpenRouter
- Context-aware recommendations based on industry/niche
- Competitor-inspired suggestions
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import structlog
from pydantic import BaseModel, Field

from app.services.ai_mvp.ai_council import AICouncil, Message, TaskType

logger = structlog.get_logger(__name__)


class ImprovementCategory(str, Enum):
    """Categories of website improvements."""
    DESIGN = "design"
    CONTENT = "content"
    TECHNICAL = "technical"
    UX = "ux"
    SEO = "seo"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    CONVERSION = "conversion"


class Priority(str, Enum):
    """Improvement priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


class Difficulty(str, Enum):
    """Implementation difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Improvement(BaseModel):
    """Single improvement recommendation."""
    id: str
    category: ImprovementCategory
    priority: Priority
    title: str
    description: str
    current_state: str
    proposed_change: str
    impact: str
    difficulty: Difficulty
    time_estimate: str
    code_example: Optional[str] = None
    resources: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class ImprovementPlanSummary(BaseModel):
    """Summary statistics for improvement plan."""
    total_improvements: int
    critical_priority: int = 0
    high_priority: int
    medium_priority: int
    low_priority: int
    estimated_total_impact: str
    estimated_total_time: str
    quick_wins: int
    categories: Dict[str, int]


class ImprovementPlan(BaseModel):
    """Complete improvement plan."""
    url: str
    analyzed_at: str
    improvements: List[Improvement]
    summary: ImprovementPlanSummary
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)


class ImprovementPlanner:
    """
    Generate concrete, actionable improvement plans for websites.

    Takes website analysis results and produces prioritized recommendations
    with specific implementation guidance.
    """

    def __init__(self, ai_council: AICouncil):
        """
        Initialize improvement planner.

        Args:
            ai_council: AI Council instance for generating creative improvements
        """
        self.ai_council = ai_council

    async def generate_plan(
        self,
        analysis_result: Dict[str, Any],
        industry: Optional[str] = None,
        competitor_urls: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        lead_value: Optional[float] = None
    ) -> ImprovementPlan:
        """
        Generate comprehensive improvement plan from analysis results.

        Args:
            analysis_result: Website analysis results from WebsiteAnalyzer
            industry: Business industry/niche for context-aware recommendations
            competitor_urls: List of competitor URLs for inspiration
            focus_areas: Specific areas to focus on (e.g., ['conversion', 'performance'])
            lead_value: Estimated lead value for AI routing

        Returns:
            Complete improvement plan with prioritized recommendations
        """
        logger.info(
            "improvement_planner.generating",
            url=analysis_result.get("url"),
            industry=industry,
            focus_areas=focus_areas
        )

        # Extract analysis data
        url = analysis_result.get("url", "")
        ai_analysis = analysis_result.get("ai_analysis", "")
        title = analysis_result.get("title", "")
        meta_description = analysis_result.get("meta_description", "")

        # Generate improvements using different strategies
        improvements: List[Improvement] = []

        # 1. Generate AI-powered improvements
        ai_improvements = await self._generate_ai_improvements(
            url=url,
            analysis=ai_analysis,
            title=title,
            meta_description=meta_description,
            industry=industry,
            focus_areas=focus_areas,
            lead_value=lead_value
        )
        improvements.extend(ai_improvements)

        # 2. Generate rule-based improvements from analysis
        rule_based_improvements = self._generate_rule_based_improvements(
            analysis_result=analysis_result
        )
        improvements.extend(rule_based_improvements)

        # 3. Deduplicate and prioritize
        improvements = self._deduplicate_improvements(improvements)
        improvements = self._reprioritize_improvements(improvements, focus_areas)

        # 4. Generate summary
        summary = self._generate_summary(improvements)

        plan = ImprovementPlan(
            url=url,
            analyzed_at=datetime.now().isoformat(),
            improvements=improvements,
            summary=summary,
            analysis_metadata={
                "industry": industry,
                "focus_areas": focus_areas or [],
                "competitor_urls": competitor_urls or [],
                "ai_model": analysis_result.get("ai_model"),
                "ai_cost": analysis_result.get("ai_cost")
            }
        )

        logger.info(
            "improvement_planner.complete",
            url=url,
            total_improvements=len(improvements),
            high_priority=summary.high_priority
        )

        return plan

    async def _generate_ai_improvements(
        self,
        url: str,
        analysis: str,
        title: str,
        meta_description: str,
        industry: Optional[str],
        focus_areas: Optional[List[str]],
        lead_value: Optional[float]
    ) -> List[Improvement]:
        """
        Use AI to generate creative, context-aware improvement recommendations.

        Args:
            url: Website URL
            analysis: AI analysis results
            title: Page title
            meta_description: Meta description
            industry: Business industry
            focus_areas: Areas to focus on
            lead_value: Lead value for routing

        Returns:
            List of AI-generated improvements
        """
        # Build prompt for AI
        prompt = self._build_improvement_prompt(
            url=url,
            analysis=analysis,
            title=title,
            meta_description=meta_description,
            industry=industry,
            focus_areas=focus_areas
        )

        messages = [
            Message(
                role="system",
                content="""You are an expert website optimization consultant specializing in conversion rate optimization (CRO),
UX design, SEO, and web performance. You provide specific, actionable recommendations with concrete examples.

You must respond with VALID JSON ONLY. No markdown, no code blocks, no explanations outside the JSON.
Format: {"improvements": [{"title": "...", "category": "...", ...}]}"""
            ),
            Message(role="user", content=prompt)
        ]

        try:
            # Use AI Council for generation
            response = await self.ai_council.complete(
                task_type=TaskType.WEBSITE_ANALYSIS,
                messages=messages,
                lead_value=lead_value,
                temperature=0.7,
                max_tokens=3000
            )

            # Parse AI response
            improvements = self._parse_ai_improvements(response.content)

            logger.info(
                "improvement_planner.ai_generated",
                count=len(improvements),
                model=response.model_used,
                cost=response.total_cost
            )

            return improvements

        except Exception as e:
            logger.error(
                "improvement_planner.ai_generation_failed",
                error=str(e),
                url=url
            )
            return []

    def _build_improvement_prompt(
        self,
        url: str,
        analysis: str,
        title: str,
        meta_description: str,
        industry: Optional[str],
        focus_areas: Optional[List[str]]
    ) -> str:
        """Build detailed prompt for AI improvement generation."""

        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nPRIORITY FOCUS AREAS: {', '.join(focus_areas)}"

        industry_text = ""
        if industry:
            industry_text = f"\n\nINDUSTRY CONTEXT: {industry}"

        prompt = f"""Generate a comprehensive website improvement plan based on this analysis:

WEBSITE: {url}
TITLE: {title}
META DESCRIPTION: {meta_description}
{industry_text}
{focus_text}

ANALYSIS RESULTS:
{analysis[:3000]}

Generate 8-12 specific, actionable improvements. For each improvement, provide:

1. **Category**: design, content, technical, ux, seo, accessibility, performance, or conversion
2. **Priority**: critical, high, medium, or low
3. **Title**: Clear, action-oriented title (e.g., "Improve CTA Button Contrast")
4. **Description**: Detailed explanation of the issue and why it matters (2-3 sentences)
5. **Current State**: What's currently happening/visible
6. **Proposed Change**: Specific recommendation with details
7. **Impact**: Estimated improvement (be specific, e.g., "25% increase in click-through rate")
8. **Difficulty**: easy, medium, or hard
9. **Time Estimate**: Realistic time (e.g., "30 minutes", "2 hours", "1 day")
10. **Code Example**: Concrete HTML/CSS/JavaScript example (when applicable)
11. **Resources**: Helpful links or tools (as list of strings)

GUIDELINES:
- Be specific and actionable (not vague like "improve design")
- Include actual code examples with realistic values
- Consider accessibility, performance, and conversion optimization
- Prioritize high-impact, low-effort improvements (quick wins)
- Reference modern web standards (WCAG 2.1, Core Web Vitals)
- Consider mobile responsiveness
- Think about user psychology and conversion triggers

RESPOND WITH VALID JSON ONLY (no markdown, no code blocks):
{{
  "improvements": [
    {{
      "title": "Improve CTA Button Contrast",
      "category": "design",
      "priority": "high",
      "description": "Current CTA buttons have poor color contrast (2.1:1), making them difficult to see. This violates WCAG AA standards and likely reduces conversion rates.",
      "current_state": "Gray button (#999999) on light gray background (#E5E5E5)",
      "proposed_change": "Use high-contrast blue (#0066CC) on white background (#FFFFFF) with hover state",
      "impact": "25-30% increase in button visibility, estimated 15% increase in click-through rate",
      "difficulty": "easy",
      "time_estimate": "30 minutes",
      "code_example": "<button class=\\"cta\\" style=\\"background: #0066CC; color: white; padding: 12px 24px; border-radius: 6px; font-weight: 600; border: none; cursor: pointer; transition: background 0.2s;\\">Get Started</button>\\n\\n.cta:hover {{ background: #0052A3; }}",
      "resources": ["https://webaim.org/resources/contrastchecker/", "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"]
    }}
  ]
}}"""

        return prompt

    def _parse_ai_improvements(self, ai_response: str) -> List[Improvement]:
        """
        Parse AI-generated improvements from JSON response.

        Args:
            ai_response: Raw AI response text

        Returns:
            List of parsed Improvement objects
        """
        improvements = []

        try:
            # Clean response - remove markdown code blocks if present
            cleaned = ai_response.strip()
            if cleaned.startswith("```"):
                # Extract JSON from code block
                match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
                else:
                    # Try removing first and last lines
                    lines = cleaned.split('\n')
                    cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned

            # Parse JSON
            data = json.loads(cleaned)

            if not isinstance(data, dict) or "improvements" not in data:
                logger.warning("improvement_planner.invalid_ai_response", response_type=type(data))
                return []

            # Parse each improvement
            for idx, item in enumerate(data["improvements"]):
                try:
                    # Generate unique ID
                    improvement_id = f"imp_{idx + 1:03d}"

                    # Validate and normalize category
                    category = item.get("category", "ux").lower()
                    if category not in [c.value for c in ImprovementCategory]:
                        category = "ux"

                    # Validate and normalize priority
                    priority = item.get("priority", "medium").lower()
                    if priority not in [p.value for p in Priority]:
                        priority = "medium"

                    # Validate and normalize difficulty
                    difficulty = item.get("difficulty", "medium").lower()
                    if difficulty not in [d.value for d in Difficulty]:
                        difficulty = "medium"

                    improvement = Improvement(
                        id=improvement_id,
                        category=ImprovementCategory(category),
                        priority=Priority(priority),
                        title=item.get("title", "Untitled Improvement"),
                        description=item.get("description", "No description provided"),
                        current_state=item.get("current_state", "Unknown"),
                        proposed_change=item.get("proposed_change", "See description"),
                        impact=item.get("impact", "Estimated improvement in user experience"),
                        difficulty=Difficulty(difficulty),
                        time_estimate=item.get("time_estimate", "Unknown"),
                        code_example=item.get("code_example"),
                        resources=item.get("resources", []),
                        dependencies=item.get("dependencies", [])
                    )

                    improvements.append(improvement)

                except Exception as e:
                    logger.warning(
                        "improvement_planner.parse_item_failed",
                        error=str(e),
                        item_index=idx
                    )
                    continue

        except json.JSONDecodeError as e:
            logger.error(
                "improvement_planner.json_parse_failed",
                error=str(e),
                response_preview=ai_response[:200]
            )
        except Exception as e:
            logger.error(
                "improvement_planner.parse_failed",
                error=str(e)
            )

        return improvements

    def _generate_rule_based_improvements(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[Improvement]:
        """
        Generate improvements based on rules and analysis data.

        These are deterministic improvements based on known issues
        that can be detected programmatically.

        Args:
            analysis_result: Website analysis results

        Returns:
            List of rule-based improvements
        """
        improvements = []
        ai_analysis = analysis_result.get("ai_analysis", "").lower()
        title = analysis_result.get("title", "")
        meta_description = analysis_result.get("meta_description", "")

        # Rule 1: Missing or short meta description
        if not meta_description or len(meta_description) < 50:
            improvements.append(Improvement(
                id="rule_meta_desc",
                category=ImprovementCategory.SEO,
                priority=Priority.HIGH,
                title="Add Compelling Meta Description",
                description="Meta description is missing or too short. This is crucial for search engine results pages (SERPs) and affects click-through rates from Google.",
                current_state=f"Current: '{meta_description[:50]}...' ({len(meta_description)} chars)",
                proposed_change="Write a compelling 150-160 character meta description that includes primary keywords and a clear value proposition",
                impact="10-30% improvement in SERP click-through rate",
                difficulty=Difficulty.EASY,
                time_estimate="15 minutes",
                code_example='<meta name="description" content="Your compelling 150-160 character description here that includes keywords and value proposition">',
                resources=[
                    "https://moz.com/learn/seo/meta-description",
                    "https://developers.google.com/search/docs/appearance/snippet"
                ]
            ))

        # Rule 2: Title too long or too short
        if title and (len(title) < 30 or len(title) > 60):
            improvements.append(Improvement(
                id="rule_title_length",
                category=ImprovementCategory.SEO,
                priority=Priority.MEDIUM,
                title="Optimize Page Title Length",
                description=f"Page title is {len(title)} characters. Optimal length is 50-60 characters for full display in search results.",
                current_state=f"Current title: '{title}' ({len(title)} chars)",
                proposed_change="Rewrite title to be 50-60 characters, front-loading important keywords",
                impact="5-15% improvement in SERP visibility and CTR",
                difficulty=Difficulty.EASY,
                time_estimate="10 minutes",
                code_example='<title>Your Optimized 50-60 Char Title With Keywords</title>',
                resources=["https://moz.com/learn/seo/title-tag"]
            ))

        # Rule 3: Mobile responsiveness issues
        if "not mobile" in ai_analysis or "mobile issue" in ai_analysis or "viewport" in ai_analysis:
            improvements.append(Improvement(
                id="rule_mobile",
                category=ImprovementCategory.TECHNICAL,
                priority=Priority.HIGH,
                title="Improve Mobile Responsiveness",
                description="Website appears to have mobile responsiveness issues. With 60%+ of traffic from mobile, this is critical for user experience and SEO.",
                current_state="Desktop-focused design with potential mobile issues",
                proposed_change="Implement responsive design with proper viewport meta tag, flexible layouts, and mobile-first CSS",
                impact="30-50% improvement in mobile user engagement and bounce rate",
                difficulty=Difficulty.MEDIUM,
                time_estimate="4-8 hours",
                code_example='<meta name="viewport" content="width=device-width, initial-scale=1.0">\n\n/* CSS */\n.container {\n  max-width: 1200px;\n  margin: 0 auto;\n  padding: 0 16px;\n}\n\n@media (max-width: 768px) {\n  .container { padding: 0 12px; }\n}',
                resources=[
                    "https://web.dev/responsive-web-design-basics/",
                    "https://developers.google.com/search/mobile-sites"
                ]
            ))

        # Rule 4: Slow loading or performance issues
        if "slow" in ai_analysis or "performance" in ai_analysis or "loading" in ai_analysis:
            improvements.append(Improvement(
                id="rule_performance",
                category=ImprovementCategory.PERFORMANCE,
                priority=Priority.HIGH,
                title="Optimize Page Load Speed",
                description="Page appears to have performance issues. Every 1 second delay in load time reduces conversions by 7%.",
                current_state="Potential performance bottlenecks detected",
                proposed_change="Implement lazy loading for images, minify CSS/JS, enable compression, optimize images",
                impact="20-40% improvement in page load time, 10-15% increase in conversion rate",
                difficulty=Difficulty.MEDIUM,
                time_estimate="3-6 hours",
                code_example='<!-- Lazy loading images -->\n<img src="image.jpg" loading="lazy" alt="Description">\n\n<!-- Async JS -->\n<script src="script.js" async></script>',
                resources=[
                    "https://web.dev/fast/",
                    "https://developers.google.com/speed/pagespeed/insights/"
                ]
            ))

        # Rule 5: Missing call-to-action
        if "no cta" in ai_analysis or "unclear cta" in ai_analysis or "call to action" in ai_analysis:
            improvements.append(Improvement(
                id="rule_cta",
                category=ImprovementCategory.CONVERSION,
                priority=Priority.CRITICAL,
                title="Add Clear Call-to-Action",
                description="Website lacks a clear, prominent call-to-action. CTAs are essential for guiding users to conversion.",
                current_state="Missing or unclear primary call-to-action",
                proposed_change="Add prominent, action-oriented CTA button above the fold with clear value proposition",
                impact="40-60% increase in conversion rate",
                difficulty=Difficulty.EASY,
                time_estimate="1 hour",
                code_example='<div class="hero-cta">\n  <h1>Transform Your Business Today</h1>\n  <p>Join 10,000+ satisfied customers</p>\n  <button class="cta-primary">Get Started Free →</button>\n</div>\n\n.cta-primary {\n  background: #FF6B35;\n  color: white;\n  padding: 16px 32px;\n  font-size: 18px;\n  border-radius: 8px;\n  border: none;\n  cursor: pointer;\n  box-shadow: 0 4px 12px rgba(255,107,53,0.3);\n}',
                resources=[
                    "https://www.nngroup.com/articles/call-to-action-buttons/",
                    "https://cxl.com/blog/call-to-action-examples/"
                ]
            ))

        # Rule 6: Accessibility issues
        if "accessibility" in ai_analysis or "wcag" in ai_analysis or "contrast" in ai_analysis:
            improvements.append(Improvement(
                id="rule_accessibility",
                category=ImprovementCategory.ACCESSIBILITY,
                priority=Priority.MEDIUM,
                title="Improve Accessibility Compliance",
                description="Website has accessibility issues. Meeting WCAG 2.1 AA standards is both legally important and improves UX for all users.",
                current_state="Accessibility issues detected (color contrast, alt text, etc.)",
                proposed_change="Implement proper color contrast (4.5:1), add alt text to images, ensure keyboard navigation",
                impact="15-25% improvement in user satisfaction, legal compliance, better SEO",
                difficulty=Difficulty.MEDIUM,
                time_estimate="2-4 hours",
                code_example='<!-- Proper alt text -->\n<img src="product.jpg" alt="Blue running shoes with white stripes">\n\n<!-- ARIA labels -->\n<button aria-label="Close menu">✕</button>\n\n<!-- Proper heading hierarchy -->\n<h1>Main Title</h1>\n<h2>Section Title</h2>',
                resources=[
                    "https://www.w3.org/WAI/WCAG21/quickref/",
                    "https://webaim.org/resources/contrastchecker/"
                ]
            ))

        return improvements

    def _deduplicate_improvements(
        self,
        improvements: List[Improvement]
    ) -> List[Improvement]:
        """
        Remove duplicate improvements based on title similarity.

        Args:
            improvements: List of improvements

        Returns:
            Deduplicated list
        """
        seen_titles = set()
        unique = []

        for imp in improvements:
            # Normalize title for comparison
            normalized = imp.title.lower().strip()

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(imp)

        return unique

    def _reprioritize_improvements(
        self,
        improvements: List[Improvement],
        focus_areas: Optional[List[str]]
    ) -> List[Improvement]:
        """
        Re-prioritize improvements based on focus areas and quick wins.

        Args:
            improvements: List of improvements
            focus_areas: Priority focus areas

        Returns:
            Sorted list with updated priorities
        """
        # Boost priority for focus areas
        if focus_areas:
            focus_categories = [area.lower() for area in focus_areas]
            for imp in improvements:
                if imp.category.value in focus_categories:
                    # Boost priority by one level
                    if imp.priority == Priority.LOW:
                        imp.priority = Priority.MEDIUM
                    elif imp.priority == Priority.MEDIUM:
                        imp.priority = Priority.HIGH

        # Sort by priority (critical > high > medium > low)
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }

        improvements.sort(key=lambda x: priority_order[x.priority])

        # Re-assign IDs based on new order
        for idx, imp in enumerate(improvements):
            imp.id = f"imp_{idx + 1:03d}"

        return improvements

    def _generate_summary(
        self,
        improvements: List[Improvement]
    ) -> ImprovementPlanSummary:
        """
        Generate summary statistics for improvement plan.

        Args:
            improvements: List of improvements

        Returns:
            Summary statistics
        """
        # Count by priority
        critical = sum(1 for i in improvements if i.priority == Priority.CRITICAL)
        high = sum(1 for i in improvements if i.priority == Priority.HIGH)
        medium = sum(1 for i in improvements if i.priority == Priority.MEDIUM)
        low = sum(1 for i in improvements if i.priority == Priority.LOW)

        # Count quick wins (easy + high priority)
        quick_wins = sum(
            1 for i in improvements
            if i.difficulty == Difficulty.EASY and i.priority in [Priority.HIGH, Priority.CRITICAL]
        )

        # Count by category
        categories = {}
        for imp in improvements:
            cat = imp.category.value
            categories[cat] = categories.get(cat, 0) + 1

        # Estimate total time
        total_hours = self._estimate_total_time(improvements)

        # Estimate total impact
        impact_text = self._estimate_total_impact(improvements)

        return ImprovementPlanSummary(
            total_improvements=len(improvements),
            critical_priority=critical,
            high_priority=high,
            medium_priority=medium,
            low_priority=low,
            estimated_total_impact=impact_text,
            estimated_total_time=f"{total_hours} hours",
            quick_wins=quick_wins,
            categories=categories
        )

    def _estimate_total_time(self, improvements: List[Improvement]) -> int:
        """
        Estimate total implementation time in hours.

        Args:
            improvements: List of improvements

        Returns:
            Total hours
        """
        total_hours = 0

        for imp in improvements:
            time_str = imp.time_estimate.lower()

            # Parse time estimate
            if "minute" in time_str:
                # Extract minutes
                match = re.search(r'(\d+)\s*minute', time_str)
                if match:
                    minutes = int(match.group(1))
                    total_hours += minutes / 60
            elif "hour" in time_str:
                # Extract hours (handle ranges like "2-4 hours")
                match = re.search(r'(\d+)(?:-(\d+))?\s*hour', time_str)
                if match:
                    hours = int(match.group(1))
                    if match.group(2):
                        # Use average of range
                        hours = (hours + int(match.group(2))) / 2
                    total_hours += hours
            elif "day" in time_str:
                # Extract days
                match = re.search(r'(\d+)\s*day', time_str)
                if match:
                    days = int(match.group(1))
                    total_hours += days * 8

        return int(total_hours)

    def _estimate_total_impact(self, improvements: List[Improvement]) -> str:
        """
        Generate overall impact estimation text.

        Args:
            improvements: List of improvements

        Returns:
            Impact description
        """
        critical_count = sum(1 for i in improvements if i.priority == Priority.CRITICAL)
        high_count = sum(1 for i in improvements if i.priority == Priority.HIGH)

        if critical_count > 0:
            return f"Critical improvements expected to yield 40-60% overall improvement"
        elif high_count >= 3:
            return f"High-priority improvements expected to yield 30-50% overall improvement"
        elif high_count > 0:
            return f"High-priority improvements expected to yield 20-35% overall improvement"
        else:
            return f"Medium-priority improvements expected to yield 10-25% overall improvement"

    def export_to_json(self, plan: ImprovementPlan) -> str:
        """
        Export improvement plan to JSON.

        Args:
            plan: Improvement plan

        Returns:
            JSON string
        """
        return plan.model_dump_json(indent=2)

    def export_to_markdown(self, plan: ImprovementPlan) -> str:
        """
        Export improvement plan to Markdown format.

        Args:
            plan: Improvement plan

        Returns:
            Markdown string
        """
        md = f"""# Website Improvement Plan

**URL:** {plan.url}
**Analyzed:** {plan.analyzed_at}

## Summary

- **Total Improvements:** {plan.summary.total_improvements}
- **Critical:** {plan.summary.critical_priority} | **High:** {plan.summary.high_priority} | **Medium:** {plan.summary.medium_priority} | **Low:** {plan.summary.low_priority}
- **Quick Wins:** {plan.summary.quick_wins}
- **Estimated Total Time:** {plan.summary.estimated_total_time}
- **Estimated Impact:** {plan.summary.estimated_total_impact}

### By Category
"""

        for category, count in plan.summary.categories.items():
            md += f"- **{category.title()}:** {count}\n"

        md += "\n---\n\n## Improvements\n\n"

        # Group by priority
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            priority_improvements = [i for i in plan.improvements if i.priority == priority]

            if not priority_improvements:
                continue

            md += f"### {priority.value.upper()} Priority\n\n"

            for imp in priority_improvements:
                md += f"#### {imp.id}. {imp.title}\n\n"
                md += f"**Category:** {imp.category.value} | **Difficulty:** {imp.difficulty.value} | **Time:** {imp.time_estimate}\n\n"
                md += f"**Description:** {imp.description}\n\n"
                md += f"**Current State:** {imp.current_state}\n\n"
                md += f"**Proposed Change:** {imp.proposed_change}\n\n"
                md += f"**Impact:** {imp.impact}\n\n"

                if imp.code_example:
                    md += f"**Code Example:**\n```\n{imp.code_example}\n```\n\n"

                if imp.resources:
                    md += "**Resources:**\n"
                    for resource in imp.resources:
                        md += f"- {resource}\n"
                    md += "\n"

                md += "---\n\n"

        return md
