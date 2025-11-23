"""
Video Script Generator - Phase 4, Task 1

Generates AI-powered video scripts from improvement plans for demo sites.
Supports multiple script styles and customization based on lead value.

Features:
- Multi-style script generation (professional, casual, technical, sales)
- Scene-by-scene breakdowns with visual cues
- Timing estimates and word count calculations
- AI-GYM integration for cost-optimized model selection
- Section regeneration for iterative refinement
"""

import time
import re
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import structlog

from app.services.ai_mvp.ai_council import AICouncil, Message, AICouncilResponse
from app.services.ai_mvp.semantic_router import TaskType

logger = structlog.get_logger(__name__)


class SceneType(str, Enum):
    """Types of video scenes."""
    INTRO = "intro"
    PROBLEM = "problem"
    SOLUTION = "solution"
    FEATURE = "feature"
    DEMO = "demo"
    COMPARISON = "comparison"
    CTA = "cta"
    OUTRO = "outro"


class ScriptStyle(str, Enum):
    """Video script styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SALES = "sales"


class ScriptSection(BaseModel):
    """Individual section of a video script."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Voiceover text")
    duration_seconds: int = Field(..., description="Estimated duration in seconds")
    scene_type: SceneType = Field(..., description="Type of scene")
    visual_cues: List[str] = Field(default_factory=list, description="What to show on screen")
    camera_instructions: Optional[str] = Field(None, description="Camera movement instructions")


class VideoScript(BaseModel):
    """Complete video script with all sections."""
    sections: List[ScriptSection] = Field(..., description="Script sections in order")
    total_duration_seconds: int = Field(..., description="Total video duration")
    script_style: str = Field(..., description="Script style used")
    target_audience: str = Field(..., description="Target audience description")
    key_messages: List[str] = Field(default_factory=list, description="Key messages to convey")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ScriptGenerator:
    """
    Generate AI-powered video scripts from improvement plans.

    Uses AI Council for cost-optimized model selection based on lead value.
    Supports multiple script styles and customization options.
    """

    # Words per minute for voiceover (professional speaking rate)
    WORDS_PER_MINUTE = 150

    # Style configurations
    STYLE_CONFIGS = {
        ScriptStyle.PROFESSIONAL: {
            "tone": "formal, polished, corporate",
            "pacing": "moderate",
            "language": "professional terminology, clear explanations",
            "focus": "business value, ROI, strategic improvements"
        },
        ScriptStyle.CASUAL: {
            "tone": "friendly, conversational, approachable",
            "pacing": "relaxed",
            "language": "simple words, everyday language, relatable",
            "focus": "practical benefits, user experience, simplicity"
        },
        ScriptStyle.TECHNICAL: {
            "tone": "detailed, precise, developer-focused",
            "pacing": "slower for technical details",
            "language": "technical terms, code references, specifications",
            "focus": "implementation details, architecture, performance metrics"
        },
        ScriptStyle.SALES: {
            "tone": "persuasive, benefit-driven, energetic",
            "pacing": "dynamic",
            "language": "action-oriented, value propositions, compelling",
            "focus": "pain points, transformations, competitive advantages"
        }
    }

    def __init__(self, ai_council: AICouncil):
        """
        Initialize script generator.

        Args:
            ai_council: AI Council instance for script generation
        """
        self.ai_council = ai_council

    async def generate_script(
        self,
        improvement_plan: Dict[str, Any],
        demo_site_url: str,
        lead_info: Dict[str, Any],
        style: ScriptStyle = ScriptStyle.PROFESSIONAL,
        max_duration_seconds: int = 120,
        include_intro: bool = True,
        include_cta: bool = True,
        custom_instructions: Optional[str] = None
    ) -> VideoScript:
        """
        Generate complete video script from improvement plan.

        Args:
            improvement_plan: Improvement plan from analysis
            demo_site_url: URL of deployed demo site
            lead_info: Lead information (name, company, industry, etc.)
            style: Script style (professional, casual, technical, sales)
            max_duration_seconds: Maximum video duration (default 120s = 2min)
            include_intro: Include intro section
            include_cta: Include call-to-action section
            custom_instructions: Custom instructions for AI

        Returns:
            Complete VideoScript with all sections
        """
        start_time = time.time()

        logger.info(
            "script_generator.starting",
            lead_id=lead_info.get("id"),
            style=style.value,
            max_duration=max_duration_seconds
        )

        # Extract lead value for AI routing
        lead_value = self._extract_lead_value(lead_info)

        # Build comprehensive prompt
        prompt = self._build_script_prompt(
            improvement_plan=improvement_plan,
            demo_site_url=demo_site_url,
            lead_info=lead_info,
            style=style,
            max_duration_seconds=max_duration_seconds,
            include_intro=include_intro,
            include_cta=include_cta,
            custom_instructions=custom_instructions
        )

        # Call AI to generate script
        try:
            response = await self.ai_council.complete(
                task_type=TaskType.DEMO_SITE_PLANNING,  # Complex creative task
                messages=[
                    Message(
                        role="system",
                        content=self._get_system_prompt(style)
                    ),
                    Message(role="user", content=prompt)
                ],
                lead_value=lead_value,
                temperature=0.7,  # Higher creativity for scripts
                max_tokens=3000
            )

            # Parse AI response into VideoScript
            script = self._parse_script_response(
                response=response.content,
                style=style,
                max_duration=max_duration_seconds,
                lead_info=lead_info
            )

            # Validate and adjust timing
            script = self._validate_and_adjust_timing(script, max_duration_seconds)

            # Add metadata
            script.metadata.update({
                "generation_time_seconds": time.time() - start_time,
                "ai_model": response.model_used,
                "ai_cost": response.total_cost,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "improvement_plan_id": improvement_plan.get("id"),
                "demo_site_url": demo_site_url,
                "lead_id": lead_info.get("id"),
                "lead_company": lead_info.get("company_name", lead_info.get("title"))
            })

            logger.info(
                "script_generator.completed",
                lead_id=lead_info.get("id"),
                sections_count=len(script.sections),
                total_duration=script.total_duration_seconds,
                ai_model=response.model_used,
                cost=response.total_cost,
                generation_time=script.metadata["generation_time_seconds"]
            )

            return script

        except Exception as e:
            logger.error(
                "script_generator.failed",
                lead_id=lead_info.get("id"),
                error=str(e)
            )
            raise

    async def regenerate_section(
        self,
        script: VideoScript,
        section_index: int,
        new_instructions: str,
        lead_value: Optional[float] = None
    ) -> ScriptSection:
        """
        Regenerate a specific section with new instructions.

        Args:
            script: Original video script
            section_index: Index of section to regenerate (0-based)
            new_instructions: Instructions for regeneration
            lead_value: Lead value for AI routing

        Returns:
            New ScriptSection
        """
        if section_index < 0 or section_index >= len(script.sections):
            raise ValueError(f"Invalid section index: {section_index}")

        old_section = script.sections[section_index]

        logger.info(
            "script_generator.regenerating_section",
            section_index=section_index,
            section_title=old_section.title
        )

        # Build regeneration prompt
        prompt = f"""Regenerate this video script section with the following instructions:

**INSTRUCTIONS**: {new_instructions}

**ORIGINAL SECTION**:
Title: {old_section.title}
Scene Type: {old_section.scene_type}
Duration: {old_section.duration_seconds} seconds
Content: {old_section.content}
Visual Cues: {', '.join(old_section.visual_cues)}

**CONTEXT** (other sections):
{self._get_script_context(script, section_index)}

**YOUR TASK**:
Regenerate ONLY this section following the instructions above while maintaining:
- Similar duration ({old_section.duration_seconds}s ± 3s)
- Scene type: {old_section.scene_type}
- Consistency with other sections

Respond with VALID JSON:
{{
  "title": "Updated title",
  "content": "New voiceover text...",
  "duration_seconds": {old_section.duration_seconds},
  "visual_cues": ["cue 1", "cue 2", ...],
  "camera_instructions": "Optional camera movement..."
}}"""

        # Call AI
        response = await self.ai_council.complete(
            task_type=TaskType.EMAIL_BODY,  # Short creative task
            messages=[
                Message(
                    role="system",
                    content="You are a video script writer. Regenerate script sections according to user instructions. Respond with VALID JSON only."
                ),
                Message(role="user", content=prompt)
            ],
            lead_value=lead_value,
            temperature=0.8,
            max_tokens=800
        )

        # Parse response
        import json
        cleaned = response.content.strip()
        if cleaned.startswith("```"):
            match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)

        data = json.loads(cleaned)

        new_section = ScriptSection(
            title=data.get("title", old_section.title),
            content=data["content"],
            duration_seconds=data.get("duration_seconds", old_section.duration_seconds),
            scene_type=old_section.scene_type,
            visual_cues=data.get("visual_cues", old_section.visual_cues),
            camera_instructions=data.get("camera_instructions")
        )

        logger.info(
            "script_generator.section_regenerated",
            section_index=section_index,
            old_duration=old_section.duration_seconds,
            new_duration=new_section.duration_seconds
        )

        return new_section

    def estimate_word_count(self, duration_seconds: int) -> int:
        """
        Estimate word count for given duration.

        Args:
            duration_seconds: Duration in seconds

        Returns:
            Estimated word count
        """
        return int((duration_seconds / 60) * self.WORDS_PER_MINUTE)

    def validate_script_timing(self, script: VideoScript) -> Dict[str, Any]:
        """
        Validate script timing and provide warnings.

        Args:
            script: Video script to validate

        Returns:
            Validation results with warnings
        """
        results = {
            "is_valid": True,
            "warnings": [],
            "total_duration": script.total_duration_seconds,
            "sections_count": len(script.sections),
            "average_section_duration": script.total_duration_seconds / len(script.sections) if script.sections else 0
        }

        # Check total duration
        if script.total_duration_seconds < 30:
            results["warnings"].append("Video is very short (<30s) - may not be effective")
        elif script.total_duration_seconds > 180:
            results["warnings"].append("Video is quite long (>3min) - viewer retention may drop")

        # Check individual sections
        for i, section in enumerate(script.sections):
            if section.duration_seconds < 3:
                results["warnings"].append(f"Section {i+1} is very short (<3s)")
            elif section.duration_seconds > 30:
                results["warnings"].append(f"Section {i+1} is quite long (>30s)")

            # Check word count vs duration
            word_count = len(section.content.split())
            expected_words = self.estimate_word_count(section.duration_seconds)

            if word_count > expected_words * 1.3:
                results["warnings"].append(
                    f"Section {i+1} may have too much content ({word_count} words for {section.duration_seconds}s)"
                )
            elif word_count < expected_words * 0.5:
                results["warnings"].append(
                    f"Section {i+1} may have too little content ({word_count} words for {section.duration_seconds}s)"
                )

        if results["warnings"]:
            results["is_valid"] = False

        return results

    def _extract_lead_value(self, lead_info: Dict[str, Any]) -> Optional[float]:
        """Extract lead value for AI routing."""
        # Try multiple field names
        for field in ["value", "estimated_value", "lead_value", "deal_size"]:
            if field in lead_info and lead_info[field]:
                return float(lead_info[field])

        # Default based on company size or industry
        if lead_info.get("company_size", "").lower() in ["enterprise", "large"]:
            return 50000.0
        elif lead_info.get("company_size", "").lower() in ["medium", "mid-market"]:
            return 20000.0

        return 10000.0  # Default

    def _get_system_prompt(self, style: ScriptStyle) -> str:
        """Get system prompt for script generation."""

        style_config = self.STYLE_CONFIGS[style]

        return f"""You are an expert video script writer specializing in demo videos for web development and design services.

**SCRIPT STYLE**: {style.value.upper()}
- Tone: {style_config['tone']}
- Pacing: {style_config['pacing']}
- Language: {style_config['language']}
- Focus: {style_config['focus']}

**YOUR TASK**:
Write compelling video scripts that:
1. Hook viewers in the first 5 seconds
2. Clearly explain the problem and solution
3. Highlight specific improvements with visual examples
4. Build credibility and trust
5. End with a clear call-to-action

**SCRIPT STRUCTURE**:
- Intro (5-8s): Hook + brief context
- Problem sections (8-12s each): Identify specific issues
- Solution sections (10-15s each): Show improvements
- Feature highlights (8-10s each): Showcase key features
- CTA (8-10s): Clear next step

**GUIDELINES**:
- Keep voiceover conversational and natural
- Use specific numbers and data when available
- Include visual cues for each section
- Time sections realistically (150 words/minute speaking rate)
- Make every word count - no fluff

**OUTPUT FORMAT**:
Respond with VALID JSON only (no markdown, no code blocks):
{{
  "sections": [
    {{
      "title": "Hook & Intro",
      "content": "Your voiceover text here...",
      "duration_seconds": 8,
      "scene_type": "intro",
      "visual_cues": ["Show original website", "Fade to demo"],
      "camera_instructions": "Slow zoom on homepage"
    }},
    ...
  ],
  "target_audience": "Small business owners looking to improve their web presence",
  "key_messages": ["Performance matters", "Design builds trust", "SEO drives growth"]
}}"""

    def _build_script_prompt(
        self,
        improvement_plan: Dict[str, Any],
        demo_site_url: str,
        lead_info: Dict[str, Any],
        style: ScriptStyle,
        max_duration_seconds: int,
        include_intro: bool,
        include_cta: bool,
        custom_instructions: Optional[str]
    ) -> str:
        """Build comprehensive prompt for script generation."""

        # Extract key improvements
        improvements = improvement_plan.get("improvements", [])
        top_improvements = improvements[:5]  # Focus on top 5

        improvements_text = "\n".join([
            f"{i+1}. **{imp.get('title', 'Improvement')}** ({imp.get('category', 'general')})\n"
            f"   - Impact: {imp.get('impact', 'N/A')}\n"
            f"   - Current: {imp.get('current_state', 'N/A')}\n"
            f"   - Improved: {imp.get('proposed_change', 'N/A')}"
            for i, imp in enumerate(top_improvements)
        ])

        # Extract lead context
        company_name = lead_info.get("company_name", lead_info.get("title", "this business"))
        industry = lead_info.get("industry", lead_info.get("category", "business"))
        original_url = lead_info.get("url", lead_info.get("website", "their website"))

        # Build prompt
        prompt = f"""Generate a {max_duration_seconds}-second video script for a personalized demo video.

**CONTEXT**:
Company: {company_name}
Industry: {industry}
Original Site: {original_url}
Demo Site: {demo_site_url}

**IMPROVEMENTS MADE**:
{improvements_text}

**OVERALL STRATEGY**:
{improvement_plan.get('overall_strategy', 'Comprehensive website improvements')}

**VIDEO REQUIREMENTS**:
- Duration: {max_duration_seconds} seconds (strict maximum)
- Style: {style.value}
- Include intro: {include_intro}
- Include CTA: {include_cta}
"""

        if custom_instructions:
            prompt += f"\n**CUSTOM INSTRUCTIONS**:\n{custom_instructions}\n"

        prompt += f"""
**YOUR TASK**:
Create a compelling video script that:
1. Opens with a personalized hook mentioning their business
2. Identifies 2-3 key problems from the improvement plan
3. Demonstrates solutions with specific examples
4. Highlights measurable improvements (load time, conversion, etc.)
5. {"Ends with a clear call-to-action" if include_cta else "Ends with summary"}

Focus on the most impactful improvements. Be specific with numbers and examples.
Make it personal - this is FOR {company_name}, not generic.

**OUTPUT**:
Respond with VALID JSON in the exact format specified in the system prompt.
"""

        return prompt

    def _parse_script_response(
        self,
        response: str,
        style: ScriptStyle,
        max_duration: int,
        lead_info: Dict[str, Any]
    ) -> VideoScript:
        """Parse AI response into VideoScript object."""

        import json

        # Clean response
        cleaned = response.strip()
        if cleaned.startswith("```"):
            match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned

        # Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("script_generator.json_parse_failed", error=str(e), response_preview=cleaned[:200])
            # Return fallback script
            return self._create_fallback_script(style, max_duration, lead_info)

        # Parse sections
        sections = []
        for section_data in data.get("sections", []):
            try:
                scene_type = section_data.get("scene_type", "feature").lower()
                if scene_type not in [st.value for st in SceneType]:
                    scene_type = "feature"

                section = ScriptSection(
                    title=section_data.get("title", "Untitled Section"),
                    content=section_data.get("content", ""),
                    duration_seconds=section_data.get("duration_seconds", 10),
                    scene_type=SceneType(scene_type),
                    visual_cues=section_data.get("visual_cues", []),
                    camera_instructions=section_data.get("camera_instructions")
                )
                sections.append(section)
            except Exception as e:
                logger.warning("script_generator.section_parse_failed", error=str(e))
                continue

        # Calculate total duration
        total_duration = sum(s.duration_seconds for s in sections)

        # Create VideoScript
        script = VideoScript(
            sections=sections,
            total_duration_seconds=total_duration,
            script_style=style.value,
            target_audience=data.get("target_audience", f"Decision makers at {lead_info.get('company_name', 'target company')}"),
            key_messages=data.get("key_messages", []),
            metadata={}
        )

        return script

    def _validate_and_adjust_timing(
        self,
        script: VideoScript,
        max_duration: int
    ) -> VideoScript:
        """Validate and adjust script timing to fit within max duration."""

        if script.total_duration_seconds <= max_duration:
            return script

        logger.warning(
            "script_generator.duration_exceeded",
            total=script.total_duration_seconds,
            max=max_duration,
            adjusting=True
        )

        # Proportionally reduce all sections
        scale_factor = max_duration / script.total_duration_seconds

        for section in script.sections:
            section.duration_seconds = max(3, int(section.duration_seconds * scale_factor))

        script.total_duration_seconds = sum(s.duration_seconds for s in script.sections)

        return script

    def _get_script_context(self, script: VideoScript, exclude_index: int) -> str:
        """Get context of other sections for regeneration."""

        context_parts = []
        for i, section in enumerate(script.sections):
            if i == exclude_index:
                context_parts.append(f"Section {i+1}: [REGENERATING THIS SECTION]")
            else:
                context_parts.append(
                    f"Section {i+1}: {section.title} ({section.duration_seconds}s) - {section.content[:100]}..."
                )

        return "\n".join(context_parts)

    def _create_fallback_script(
        self,
        style: ScriptStyle,
        max_duration: int,
        lead_info: Dict[str, Any]
    ) -> VideoScript:
        """Create fallback script when AI parsing fails."""

        company = lead_info.get("company_name", lead_info.get("title", "your business"))

        sections = [
            ScriptSection(
                title="Introduction",
                content=f"Hi, I noticed {company}'s website and created a demo showing what's possible with some improvements.",
                duration_seconds=8,
                scene_type=SceneType.INTRO,
                visual_cues=["Show original website", "Fade to demo site"],
                camera_instructions="Slow zoom on homepage"
            ),
            ScriptSection(
                title="Performance Improvements",
                content=f"I've optimized the site's performance, improving load time significantly. This directly impacts user experience and conversions.",
                duration_seconds=12,
                scene_type=SceneType.SOLUTION,
                visual_cues=["Show PageSpeed comparison", "Highlight metrics"],
                camera_instructions="Focus on performance numbers"
            ),
            ScriptSection(
                title="Design Enhancements",
                content="The updated design is modern, clean, and mobile-responsive. It builds trust and guides visitors to take action.",
                duration_seconds=10,
                scene_type=SceneType.FEATURE,
                visual_cues=["Show responsive design", "Highlight key elements"],
                camera_instructions="Pan across different screen sizes"
            ),
            ScriptSection(
                title="Call to Action",
                content="I'd love to discuss how we can implement these improvements for your live site. Let's schedule a quick call.",
                duration_seconds=8,
                scene_type=SceneType.CTA,
                visual_cues=["Show contact information", "Display calendar link"],
                camera_instructions="Center on CTA button"
            )
        ]

        return VideoScript(
            sections=sections,
            total_duration_seconds=sum(s.duration_seconds for s in sections),
            script_style=style.value,
            target_audience=f"Decision makers at {company}",
            key_messages=[
                "Performance improvements increase conversions",
                "Modern design builds trust",
                "Mobile optimization is essential"
            ],
            metadata={"fallback": True}
        )
