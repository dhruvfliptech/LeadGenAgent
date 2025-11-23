"""
Tests for Video Script Generator - Phase 4, Task 1

Comprehensive test suite for script generation, validation, and API endpoints.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from app.services.video.script_generator import (
    ScriptGenerator,
    VideoScript,
    ScriptSection,
    ScriptStyle,
    SceneType
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilResponse, Message, RouteDecision
from app.services.ai_mvp.semantic_router import ModelTier


# Fixtures
@pytest.fixture
def mock_ai_council():
    """Create mock AI Council."""
    council = Mock(spec=AICouncil)

    # Mock complete method
    async def mock_complete(*args, **kwargs):
        return AICouncilResponse(
            content="""
{
  "sections": [
    {
      "title": "Introduction",
      "content": "Hi, I noticed your website and created a demo showing what's possible.",
      "duration_seconds": 8,
      "scene_type": "intro",
      "visual_cues": ["Show original website", "Fade to demo"],
      "camera_instructions": "Slow zoom on homepage"
    },
    {
      "title": "Performance Issue",
      "content": "Your current site takes 4.2 seconds to load. That's losing you 40% of visitors.",
      "duration_seconds": 10,
      "scene_type": "problem",
      "visual_cues": ["Show PageSpeed score", "Highlight slow load time"],
      "camera_instructions": "Focus on performance metrics"
    },
    {
      "title": "Performance Solution",
      "content": "In the demo, I've optimized load time to 1.1 seconds. Watch how fast it loads now.",
      "duration_seconds": 12,
      "scene_type": "solution",
      "visual_cues": ["Show demo loading", "Show new PageSpeed score"],
      "camera_instructions": "Side-by-side comparison"
    },
    {
      "title": "Call to Action",
      "content": "Let's schedule a quick call to discuss implementing these improvements.",
      "duration_seconds": 8,
      "scene_type": "cta",
      "visual_cues": ["Show contact info", "Display calendar link"],
      "camera_instructions": "Center on CTA"
    }
  ],
  "target_audience": "Small business owners looking to improve web performance",
  "key_messages": ["Performance matters", "Speed increases conversions", "Easy to implement"]
}
""",
            model_used="anthropic/claude-sonnet-4",
            model_tier="premium",
            prompt_tokens=500,
            completion_tokens=300,
            total_cost=0.008,
            route_decision=RouteDecision(
                model_name="anthropic/claude-sonnet-4",
                model_tier=ModelTier.PREMIUM,
                task_complexity="complex",
                reasoning="High-value lead",
                estimated_cost=0.01
            )
        )

    council.complete = AsyncMock(side_effect=mock_complete)
    return council


@pytest.fixture
def sample_improvement_plan() -> Dict[str, Any]:
    """Create sample improvement plan."""
    return {
        "id": "plan_001",
        "overall_strategy": "Comprehensive performance and design improvements",
        "improvements": [
            {
                "title": "Optimize Page Load Speed",
                "category": "performance",
                "priority": "high",
                "current_state": "4.2s load time",
                "proposed_change": "Reduce to 1.1s with image optimization and code minification",
                "impact": "40% reduction in bounce rate, 25% increase in conversions",
                "difficulty": "medium",
                "time_estimate": "4 hours"
            },
            {
                "title": "Improve Mobile Responsiveness",
                "category": "design",
                "priority": "high",
                "current_state": "Not mobile-friendly",
                "proposed_change": "Implement responsive design with mobile-first approach",
                "impact": "50% improvement in mobile user engagement",
                "difficulty": "medium",
                "time_estimate": "6 hours"
            },
            {
                "title": "Add Clear Call-to-Action",
                "category": "conversion",
                "priority": "critical",
                "current_state": "No prominent CTA",
                "proposed_change": "Add above-fold CTA with high contrast button",
                "impact": "60% increase in conversion rate",
                "difficulty": "easy",
                "time_estimate": "1 hour"
            }
        ]
    }


@pytest.fixture
def sample_lead_info() -> Dict[str, Any]:
    """Create sample lead info."""
    return {
        "id": 123,
        "company_name": "Acme Corp",
        "title": "Acme Corp - Web Design Services",
        "url": "https://acmecorp.example.com",
        "category": "web-design",
        "industry": "web-design",
        "value": 15000.0
    }


# Unit Tests - ScriptGenerator
class TestScriptGenerator:
    """Test suite for ScriptGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_script_success(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test successful script generation."""
        generator = ScriptGenerator(mock_ai_council)

        script = await generator.generate_script(
            improvement_plan=sample_improvement_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info,
            style=ScriptStyle.PROFESSIONAL,
            max_duration_seconds=120
        )

        assert isinstance(script, VideoScript)
        assert len(script.sections) == 4
        assert script.script_style == "professional"
        assert script.total_duration_seconds == 38  # 8+10+12+8
        assert script.total_duration_seconds <= 120
        assert len(script.key_messages) > 0

        # Verify metadata
        assert "generation_time_seconds" in script.metadata
        assert "ai_model" in script.metadata
        assert "ai_cost" in script.metadata
        assert script.metadata["ai_model"] == "anthropic/claude-sonnet-4"
        assert script.metadata["ai_cost"] == 0.008

    @pytest.mark.asyncio
    async def test_generate_script_different_styles(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test script generation with different styles."""
        generator = ScriptGenerator(mock_ai_council)

        styles = [
            ScriptStyle.PROFESSIONAL,
            ScriptStyle.CASUAL,
            ScriptStyle.TECHNICAL,
            ScriptStyle.SALES
        ]

        for style in styles:
            script = await generator.generate_script(
                improvement_plan=sample_improvement_plan,
                demo_site_url="https://demo.vercel.app",
                lead_info=sample_lead_info,
                style=style
            )

            assert script.script_style == style.value
            assert len(script.sections) > 0

    @pytest.mark.asyncio
    async def test_generate_script_respects_max_duration(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test that script respects max duration."""
        generator = ScriptGenerator(mock_ai_council)

        max_duration = 30  # Very short

        script = await generator.generate_script(
            improvement_plan=sample_improvement_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info,
            max_duration_seconds=max_duration
        )

        # Script should be adjusted to fit within max duration
        assert script.total_duration_seconds <= max_duration

    @pytest.mark.asyncio
    async def test_regenerate_section(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test section regeneration."""
        # Mock regeneration response
        async def mock_regenerate(*args, **kwargs):
            return AICouncilResponse(
                content="""
{
  "title": "Updated Introduction",
  "content": "Hi there! I've analyzed your website and created an exciting demo.",
  "duration_seconds": 8,
  "visual_cues": ["Animated intro", "Smooth transition"],
  "camera_instructions": "Quick zoom"
}
""",
                model_used="anthropic/claude-haiku",
                model_tier="budget",
                prompt_tokens=200,
                completion_tokens=100,
                total_cost=0.001,
                route_decision=Mock()
            )

        mock_ai_council.complete = AsyncMock(side_effect=mock_regenerate)

        generator = ScriptGenerator(mock_ai_council)

        # Create a script first
        original_script = VideoScript(
            sections=[
                ScriptSection(
                    title="Introduction",
                    content="Original intro content",
                    duration_seconds=8,
                    scene_type=SceneType.INTRO,
                    visual_cues=["Original visuals"]
                )
            ],
            total_duration_seconds=8,
            script_style="professional",
            target_audience="Business owners",
            key_messages=["Message 1"]
        )

        # Regenerate first section
        new_section = await generator.regenerate_section(
            script=original_script,
            section_index=0,
            new_instructions="Make it more exciting and energetic"
        )

        assert isinstance(new_section, ScriptSection)
        assert new_section.title == "Updated Introduction"
        assert "exciting" in new_section.content.lower()
        assert new_section.duration_seconds == 8

    def test_estimate_word_count(self, mock_ai_council):
        """Test word count estimation."""
        generator = ScriptGenerator(mock_ai_council)

        # At 150 words/minute
        assert generator.estimate_word_count(60) == 150  # 1 minute
        assert generator.estimate_word_count(30) == 75   # 30 seconds
        assert generator.estimate_word_count(120) == 300  # 2 minutes

    def test_validate_script_timing_success(self, mock_ai_council):
        """Test script timing validation - valid script."""
        generator = ScriptGenerator(mock_ai_council)

        script = VideoScript(
            sections=[
                ScriptSection(
                    title="Intro",
                    content="This is a proper intro with enough content for eight seconds of voiceover.",
                    duration_seconds=8,
                    scene_type=SceneType.INTRO,
                    visual_cues=["Visual 1"]
                ),
                ScriptSection(
                    title="Main",
                    content="This is the main section with appropriate content length for fifteen seconds.",
                    duration_seconds=15,
                    scene_type=SceneType.FEATURE,
                    visual_cues=["Visual 2"]
                )
            ],
            total_duration_seconds=23,
            script_style="professional",
            target_audience="Business owners",
            key_messages=[]
        )

        validation = generator.validate_script_timing(script)

        assert "total_duration" in validation
        assert "sections_count" in validation
        assert validation["total_duration"] == 23
        assert validation["sections_count"] == 2

    def test_validate_script_timing_warnings(self, mock_ai_council):
        """Test script timing validation - with warnings."""
        generator = ScriptGenerator(mock_ai_council)

        script = VideoScript(
            sections=[
                ScriptSection(
                    title="Too Short",
                    content="Short",
                    duration_seconds=2,  # Too short
                    scene_type=SceneType.INTRO,
                    visual_cues=[]
                ),
                ScriptSection(
                    title="Too Long",
                    content="Very long section " * 100,
                    duration_seconds=45,  # Too long
                    scene_type=SceneType.FEATURE,
                    visual_cues=[]
                )
            ],
            total_duration_seconds=47,
            script_style="professional",
            target_audience="Business owners",
            key_messages=[]
        )

        validation = generator.validate_script_timing(script)

        assert len(validation["warnings"]) > 0
        assert any("short" in w.lower() for w in validation["warnings"])
        assert any("long" in w.lower() for w in validation["warnings"])


# Integration Tests
class TestScriptGeneratorIntegration:
    """Integration tests for script generator with real-ish scenarios."""

    @pytest.mark.asyncio
    async def test_full_generation_workflow(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test complete generation workflow."""
        generator = ScriptGenerator(mock_ai_council)

        # Step 1: Generate initial script
        script = await generator.generate_script(
            improvement_plan=sample_improvement_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info,
            style=ScriptStyle.PROFESSIONAL,
            max_duration_seconds=120,
            include_intro=True,
            include_cta=True
        )

        assert len(script.sections) >= 2  # At least intro and one content section
        assert script.total_duration_seconds <= 120

        # Step 2: Validate timing
        validation = generator.validate_script_timing(script)
        assert "total_duration" in validation

        # Step 3: Check sections have proper types
        has_intro = any(s.scene_type == SceneType.INTRO for s in script.sections)
        has_cta = any(s.scene_type == SceneType.CTA for s in script.sections)

        assert has_intro or has_cta  # Should have at least one

    @pytest.mark.asyncio
    async def test_lead_value_routing(self, mock_ai_council):
        """Test that lead value affects AI model routing."""
        generator = ScriptGenerator(mock_ai_council)

        # High-value lead
        high_value_lead = {
            "id": 1,
            "company_name": "Enterprise Corp",
            "value": 75000.0,
            "url": "https://enterprise.com"
        }

        plan = {"improvements": [{"title": "Test"}], "overall_strategy": "Test"}

        await generator.generate_script(
            improvement_plan=plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=high_value_lead
        )

        # Verify AI Council was called with lead value
        assert mock_ai_council.complete.called
        call_kwargs = mock_ai_council.complete.call_args[1]
        assert "lead_value" in call_kwargs
        assert call_kwargs["lead_value"] == 75000.0


# Performance Tests
class TestScriptGeneratorPerformance:
    """Performance tests for script generator."""

    @pytest.mark.asyncio
    async def test_generation_speed(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test that generation completes within reasonable time."""
        import time

        generator = ScriptGenerator(mock_ai_council)

        start = time.time()

        await generator.generate_script(
            improvement_plan=sample_improvement_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info
        )

        duration = time.time() - start

        # Should complete quickly with mocked AI
        assert duration < 1.0  # Less than 1 second with mock

    @pytest.mark.asyncio
    async def test_concurrent_generation(
        self,
        mock_ai_council,
        sample_improvement_plan,
        sample_lead_info
    ):
        """Test concurrent script generation."""
        generator = ScriptGenerator(mock_ai_council)

        # Generate 5 scripts concurrently
        tasks = [
            generator.generate_script(
                improvement_plan=sample_improvement_plan,
                demo_site_url=f"https://demo{i}.vercel.app",
                lead_info={**sample_lead_info, "id": i}
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(isinstance(r, VideoScript) for r in results)


# Edge Cases
class TestScriptGeneratorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_improvement_plan(
        self,
        mock_ai_council,
        sample_lead_info
    ):
        """Test with empty improvement plan."""
        generator = ScriptGenerator(mock_ai_council)

        empty_plan = {
            "improvements": [],
            "overall_strategy": "No improvements"
        }

        # Should still generate a script (fallback behavior)
        script = await generator.generate_script(
            improvement_plan=empty_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info
        )

        assert isinstance(script, VideoScript)
        assert len(script.sections) > 0

    @pytest.mark.asyncio
    async def test_invalid_section_index_regeneration(
        self,
        mock_ai_council
    ):
        """Test regeneration with invalid section index."""
        generator = ScriptGenerator(mock_ai_council)

        script = VideoScript(
            sections=[
                ScriptSection(
                    title="Only Section",
                    content="Content",
                    duration_seconds=10,
                    scene_type=SceneType.INTRO,
                    visual_cues=[]
                )
            ],
            total_duration_seconds=10,
            script_style="professional",
            target_audience="Test",
            key_messages=[]
        )

        # Try to regenerate non-existent section
        with pytest.raises(ValueError):
            await generator.regenerate_section(
                script=script,
                section_index=5,  # Invalid index
                new_instructions="Test"
            )

    @pytest.mark.asyncio
    async def test_malformed_ai_response(self, sample_improvement_plan, sample_lead_info):
        """Test handling of malformed AI response."""
        # Create council that returns invalid JSON
        mock_council = Mock(spec=AICouncil)

        async def mock_invalid_response(*args, **kwargs):
            return AICouncilResponse(
                content="This is not valid JSON",
                model_used="test-model",
                model_tier="budget",
                prompt_tokens=100,
                completion_tokens=50,
                total_cost=0.001,
                route_decision=Mock()
            )

        mock_council.complete = AsyncMock(side_effect=mock_invalid_response)

        generator = ScriptGenerator(mock_council)

        # Should fall back to default script
        script = await generator.generate_script(
            improvement_plan=sample_improvement_plan,
            demo_site_url="https://demo.vercel.app",
            lead_info=sample_lead_info
        )

        assert isinstance(script, VideoScript)
        assert script.metadata.get("fallback") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
