"""
Interaction Generator for Screen Recordings.

Automatically generates interaction sequences from scripts and demo sites.
Detects key elements and creates smooth, realistic interactions.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
from pydantic import BaseModel

from app.services.video.screen_recorder import Interaction, InteractionSequence

logger = logging.getLogger(__name__)


class ElementInfo(BaseModel):
    """Information about a detected element."""

    selector: str
    tag_name: str
    text: Optional[str] = None
    x: int
    y: int
    width: int
    height: int
    visible: bool
    importance_score: float = 0.0


class ScriptSection(BaseModel):
    """Represents a section of a video script."""

    name: str
    duration_seconds: float
    visual_cues: List[str] = []
    target_elements: List[str] = []
    actions: List[str] = []


class VideoScript(BaseModel):
    """Complete video script with sections."""

    title: str
    total_duration_seconds: float
    sections: List[ScriptSection]


class InteractionGenerator:
    """
    Generate interaction sequences from video scripts and demo sites.

    Analyzes demo site structure and creates realistic interaction
    patterns based on script requirements and improvement plans.
    """

    def __init__(self):
        self.importance_weights = {
            "button": 1.0,
            "a": 0.9,
            "input": 0.8,
            "form": 0.8,
            "nav": 0.7,
            "h1": 0.9,
            "h2": 0.8,
            "h3": 0.7,
            "img": 0.6,
            "video": 0.9,
            "section": 0.5
        }

    async def generate_interactions_from_script(
        self,
        page: Page,
        script: VideoScript,
        demo_site_url: str
    ) -> InteractionSequence:
        """
        Generate complete interaction sequence from video script.

        Args:
            page: Playwright page object
            script: Video script with sections
            demo_site_url: URL of demo site

        Returns:
            Complete interaction sequence
        """
        all_interactions: List[Interaction] = []

        # Initial wait for page load
        all_interactions.append(
            Interaction(type="wait", duration_ms=2000)
        )

        # Process each script section
        for section in script.sections:
            section_interactions = await self._generate_section_interactions(
                page, section
            )
            all_interactions.extend(section_interactions)

        # Final wait
        all_interactions.append(
            Interaction(type="wait", duration_ms=1000)
        )

        sequence = InteractionSequence(interactions=all_interactions)
        sequence.calculate_duration()

        logger.info(f"Generated {len(all_interactions)} interactions for {len(script.sections)} sections")
        return sequence

    async def _generate_section_interactions(
        self,
        page: Page,
        section: ScriptSection
    ) -> List[Interaction]:
        """Generate interactions for a single script section."""
        interactions: List[Interaction] = []

        # Detect key elements for this section
        elements = await self.detect_key_elements(page, {
            "target_selectors": section.target_elements,
            "visual_cues": section.visual_cues
        })

        if not elements:
            # Fallback: just scroll and wait
            interactions.append(
                Interaction(type="scroll", scroll_amount=300, duration_ms=1500)
            )
            interactions.append(
                Interaction(type="wait", duration_ms=int(section.duration_seconds * 1000))
            )
            return interactions

        # Calculate time per element
        time_per_element = (section.duration_seconds * 1000) / max(len(elements), 1)

        # Create interactions for each element
        for i, element in enumerate(elements[:5]):  # Limit to top 5 elements
            # Scroll to element
            interactions.append(
                Interaction(
                    type="scroll",
                    selector=element["selector"],
                    duration_ms=int(time_per_element * 0.3)
                )
            )

            # Hover over element
            interactions.append(
                Interaction(
                    type="hover",
                    selector=element["selector"],
                    duration_ms=int(time_per_element * 0.2)
                )
            )

            # Highlight if important
            if element.get("importance", 0) > 0.7:
                interactions.append(
                    Interaction(
                        type="highlight",
                        selector=element["selector"],
                        duration_ms=int(time_per_element * 0.3)
                    )
                )

            # Wait
            interactions.append(
                Interaction(
                    type="wait",
                    duration_ms=int(time_per_element * 0.2)
                )
            )

        return interactions

    async def detect_key_elements(
        self,
        page: Page,
        improvement_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect key elements on the page based on improvement plan.

        Args:
            page: Playwright page object
            improvement_plan: Dictionary with target selectors and visual cues

        Returns:
            List of element information dictionaries
        """
        elements = []

        try:
            # Get all interactive elements
            interactive_selectors = [
                "button",
                "a[href]",
                "input",
                "textarea",
                "select",
                ".cta",
                ".btn",
                "[role='button']",
                "h1",
                "h2",
                "h3",
                "img",
                "video",
                ".hero",
                ".testimonial",
                ".feature",
                ".pricing",
                "nav"
            ]

            # Add custom selectors from improvement plan
            if "target_selectors" in improvement_plan:
                interactive_selectors.extend(improvement_plan["target_selectors"])

            # Evaluate all elements in browser
            elements_data = await page.evaluate("""
                (selectors) => {
                    const results = [];
                    selectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach((el, index) => {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    results.push({
                                        selector: selector + (elements.length > 1 ? `:nth-of-type(${index + 1})` : ''),
                                        tag_name: el.tagName.toLowerCase(),
                                        text: el.textContent?.trim().substring(0, 50) || null,
                                        x: Math.round(rect.left + rect.width / 2),
                                        y: Math.round(rect.top + rect.height / 2),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height),
                                        visible: rect.top >= 0 && rect.top < window.innerHeight
                                    });
                                }
                            });
                        } catch (e) {
                            // Ignore invalid selectors
                        }
                    });
                    return results;
                }
            """, interactive_selectors)

            # Score elements by importance
            for element in elements_data:
                importance = self._calculate_element_importance(element)
                element["importance"] = importance

            # Sort by importance and visibility
            elements_data.sort(
                key=lambda e: (e.get("visible", False), e.get("importance", 0)),
                reverse=True
            )

            elements = elements_data[:10]  # Return top 10 elements

            logger.info(f"Detected {len(elements)} key elements")

        except Exception as e:
            logger.error(f"Failed to detect elements: {str(e)}", exc_info=True)

        return elements

    def _calculate_element_importance(self, element: Dict[str, Any]) -> float:
        """Calculate importance score for an element."""
        score = 0.0

        # Base score from element type
        tag_name = element.get("tag_name", "")
        score += self.importance_weights.get(tag_name, 0.3)

        # Boost for CTAs and buttons
        text = (element.get("text") or "").lower()
        cta_keywords = ["buy", "sign up", "get started", "learn more", "contact", "demo", "free trial"]
        if any(keyword in text for keyword in cta_keywords):
            score += 0.3

        # Boost for visible elements
        if element.get("visible", False):
            score += 0.2

        # Boost for larger elements (likely more important)
        area = element.get("width", 0) * element.get("height", 0)
        if area > 10000:
            score += 0.1

        return min(score, 1.0)

    def create_smooth_mouse_path(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        steps: int = 20
    ) -> List[Tuple[int, int]]:
        """
        Create smooth mouse movement path using Bezier curve.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            steps: Number of intermediate steps

        Returns:
            List of (x, y) coordinate tuples
        """
        path = []

        # Calculate control point for curve (offset perpendicular to direct line)
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2

        # Add slight curve by offsetting control point
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            # Perpendicular offset (20% of distance)
            offset = distance * 0.2
            control_x = mid_x - dy / distance * offset
            control_y = mid_y + dx / distance * offset
        else:
            control_x = mid_x
            control_y = mid_y

        # Generate points along quadratic Bezier curve
        for i in range(steps + 1):
            t = i / steps

            # Quadratic Bezier formula: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * end_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * end_y

            path.append((int(x), int(y)))

        return path

    def generate_scroll_interaction(
        self,
        target_element: str,
        scroll_speed: int = 1000
    ) -> Interaction:
        """
        Generate smooth scroll interaction to target element.

        Args:
            target_element: CSS selector of target element
            scroll_speed: Scroll speed in pixels per second

        Returns:
            Scroll interaction
        """
        # Estimate duration based on typical scroll distance
        estimated_distance = 500  # pixels
        duration_ms = int((estimated_distance / scroll_speed) * 1000)

        return Interaction(
            type="scroll",
            selector=target_element,
            duration_ms=max(duration_ms, 500),  # Minimum 500ms
            smooth=True
        )

    async def generate_default_interactions(
        self,
        page: Page,
        duration_seconds: float = 30.0
    ) -> InteractionSequence:
        """
        Generate default interaction sequence for a page.

        Creates a natural browsing pattern with scrolling, hovering,
        and highlighting key elements.

        Args:
            page: Playwright page object
            duration_seconds: Target duration in seconds

        Returns:
            Generated interaction sequence
        """
        interactions: List[Interaction] = []

        # Initial wait
        interactions.append(
            Interaction(type="wait", duration_ms=2000)
        )

        # Detect key elements
        elements = await self.detect_key_elements(page, {})

        if elements:
            # Calculate time budget
            time_per_element = (duration_seconds - 4) * 1000 / len(elements)

            # Create interactions for each element
            for element in elements[:8]:  # Limit to 8 elements
                # Scroll to element
                interactions.append(
                    Interaction(
                        type="scroll",
                        selector=element["selector"],
                        duration_ms=int(time_per_element * 0.4),
                        smooth=True
                    )
                )

                # Hover
                interactions.append(
                    Interaction(
                        type="hover",
                        selector=element["selector"],
                        duration_ms=int(time_per_element * 0.3)
                    )
                )

                # Highlight important elements
                if element.get("importance", 0) > 0.7:
                    interactions.append(
                        Interaction(
                            type="highlight",
                            selector=element["selector"],
                            duration_ms=int(time_per_element * 0.2)
                        )
                    )

                # Wait
                interactions.append(
                    Interaction(
                        type="wait",
                        duration_ms=int(time_per_element * 0.1)
                    )
                )
        else:
            # Fallback: simple scrolling
            num_scrolls = int(duration_seconds / 3)
            for i in range(num_scrolls):
                interactions.append(
                    Interaction(
                        type="scroll",
                        scroll_amount=400,
                        duration_ms=2000,
                        smooth=True
                    )
                )
                interactions.append(
                    Interaction(type="wait", duration_ms=1000)
                )

        # Scroll back to top
        interactions.append(
            Interaction(
                type="scroll",
                scroll_amount=-10000,  # Scroll to top
                duration_ms=2000
            )
        )

        # Final wait
        interactions.append(
            Interaction(type="wait", duration_ms=2000)
        )

        sequence = InteractionSequence(interactions=interactions)
        sequence.calculate_duration()

        logger.info(f"Generated default sequence with {len(interactions)} interactions")
        return sequence

    def create_click_sequence(
        self,
        elements: List[str],
        duration_per_click_ms: int = 1000
    ) -> List[Interaction]:
        """
        Create a sequence of click interactions.

        Args:
            elements: List of CSS selectors to click
            duration_per_click_ms: Duration to wait after each click

        Returns:
            List of click interactions
        """
        interactions = []

        for selector in elements:
            interactions.append(
                Interaction(
                    type="scroll",
                    selector=selector,
                    duration_ms=500
                )
            )
            interactions.append(
                Interaction(
                    type="click",
                    selector=selector,
                    duration_ms=duration_per_click_ms
                )
            )

        return interactions

    def create_form_fill_sequence(
        self,
        form_fields: Dict[str, str],
        duration_per_field_ms: int = 1500
    ) -> List[Interaction]:
        """
        Create a sequence for filling out a form.

        Args:
            form_fields: Dictionary of {selector: text_value}
            duration_per_field_ms: Duration per field

        Returns:
            List of form fill interactions
        """
        interactions = []

        for selector, text in form_fields.items():
            interactions.append(
                Interaction(
                    type="scroll",
                    selector=selector,
                    duration_ms=300
                )
            )
            interactions.append(
                Interaction(
                    type="click",
                    selector=selector,
                    duration_ms=200
                )
            )
            interactions.append(
                Interaction(
                    type="type",
                    selector=selector,
                    text=text,
                    duration_ms=duration_per_field_ms
                )
            )

        return interactions


class InteractionTemplates:
    """Pre-built interaction templates for common scenarios."""

    @staticmethod
    def hero_section_showcase(duration_seconds: float = 10.0) -> List[Interaction]:
        """Showcase hero section with scrolling and highlighting."""
        return [
            Interaction(type="wait", duration_ms=2000),
            Interaction(type="scroll", selector="header", duration_ms=1000),
            Interaction(type="highlight", selector="h1", duration_ms=2000),
            Interaction(type="wait", duration_ms=1000),
            Interaction(type="hover", selector=".cta-button", duration_ms=2000),
            Interaction(type="highlight", selector=".cta-button", duration_ms=2000),
        ]

    @staticmethod
    def features_tour(duration_seconds: float = 15.0) -> List[Interaction]:
        """Tour through features section."""
        return [
            Interaction(type="scroll", selector=".features", duration_ms=1500),
            Interaction(type="wait", duration_ms=1000),
            Interaction(type="highlight", selector=".feature:nth-child(1)", duration_ms=2000),
            Interaction(type="highlight", selector=".feature:nth-child(2)", duration_ms=2000),
            Interaction(type="highlight", selector=".feature:nth-child(3)", duration_ms=2000),
            Interaction(type="wait", duration_ms=2000),
        ]

    @staticmethod
    def full_page_scroll(duration_seconds: float = 20.0) -> List[Interaction]:
        """Complete page scroll from top to bottom."""
        num_scrolls = int(duration_seconds / 2)
        interactions = [Interaction(type="wait", duration_ms=2000)]

        for i in range(num_scrolls):
            interactions.append(
                Interaction(type="scroll", scroll_amount=400, duration_ms=1500)
            )
            interactions.append(
                Interaction(type="wait", duration_ms=500)
            )

        interactions.append(
            Interaction(type="scroll", scroll_amount=-10000, duration_ms=2000)
        )

        return interactions
