"""
Example usage of Screen Recording service.

This file demonstrates how to use the screen recording automation
for capturing demo site interactions.
"""

import asyncio
from app.services.video.screen_recorder import (
    ScreenRecorder,
    RecordingConfig,
    Interaction,
    InteractionSequence,
    RecordingQualityPresets
)
from app.services.video.interaction_generator import (
    InteractionGenerator,
    InteractionTemplates
)


async def example_basic_recording():
    """Example 1: Basic recording with default settings."""
    print("\n=== Example 1: Basic Recording ===")

    recorder = ScreenRecorder()
    config = RecordingQualityPresets.high_quality()

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        recording_config=config
    )

    if result.success:
        print(f"Recording successful!")
        print(f"Video path: {result.video_file_path}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"File size: {result.file_size_bytes / 1024 / 1024:.2f} MB")
    else:
        print(f"Recording failed: {result.error_message}")


async def example_custom_interactions():
    """Example 2: Recording with custom interactions."""
    print("\n=== Example 2: Custom Interactions ===")

    # Define custom interactions
    interactions = InteractionSequence(
        interactions=[
            Interaction(type="wait", duration_ms=2000),
            Interaction(type="scroll", selector="header", duration_ms=1500),
            Interaction(type="hover", selector=".cta-button", duration_ms=1000),
            Interaction(type="highlight", selector=".cta-button", duration_ms=2000),
            Interaction(type="scroll", scroll_amount=500, duration_ms=2000),
            Interaction(type="wait", duration_ms=1000)
        ]
    )
    interactions.calculate_duration()

    print(f"Total interaction duration: {interactions.total_duration_seconds}s")

    recorder = ScreenRecorder()
    config = RecordingConfig(
        resolution="1280x720",
        frame_rate=30,
        quality="medium",
        highlight_clicks=True
    )

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        interactions=interactions,
        recording_config=config
    )

    print(f"Recording completed: {result.success}")


async def example_hero_section_showcase():
    """Example 3: Use pre-built interaction template for hero section."""
    print("\n=== Example 3: Hero Section Showcase ===")

    # Use pre-built template
    template_interactions = InteractionTemplates.hero_section_showcase(duration_seconds=10.0)

    sequence = InteractionSequence(interactions=template_interactions)
    sequence.calculate_duration()

    recorder = ScreenRecorder()
    config = RecordingQualityPresets.medium_quality()

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        interactions=sequence,
        recording_config=config
    )

    print(f"Hero showcase recording: {result.success}")


async def example_full_page_tour():
    """Example 4: Full page scroll tour."""
    print("\n=== Example 4: Full Page Tour ===")

    # Use full page scroll template
    template_interactions = InteractionTemplates.full_page_scroll(duration_seconds=20.0)

    sequence = InteractionSequence(interactions=template_interactions)
    sequence.calculate_duration()

    recorder = ScreenRecorder()
    config = RecordingQualityPresets.high_quality()

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        interactions=sequence,
        recording_config=config
    )

    print(f"Full page tour recording: {result.success}")
    print(f"Segments: {result.segments_count}")


async def example_interaction_generator():
    """Example 5: Use InteractionGenerator to auto-generate interactions."""
    print("\n=== Example 5: Auto-Generated Interactions ===")

    from playwright.async_api import async_playwright

    # Initialize browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to page
    await page.goto("https://example.com")

    # Generate interactions automatically
    generator = InteractionGenerator()
    interactions = await generator.generate_default_interactions(
        page=page,
        duration_seconds=15.0
    )

    print(f"Generated {len(interactions.interactions)} interactions")
    print(f"Total duration: {interactions.total_duration_seconds}s")

    # Close browser
    await page.close()
    await context.close()
    await browser.close()

    # Now use generated interactions for recording
    recorder = ScreenRecorder()
    config = RecordingQualityPresets.high_quality()

    result = await recorder.record_demo_site(
        demo_site_url="https://example.com",
        interactions=interactions,
        recording_config=config
    )

    print(f"Auto-generated recording: {result.success}")


async def example_quality_presets():
    """Example 6: Compare different quality presets."""
    print("\n=== Example 6: Quality Presets Comparison ===")

    presets = [
        ("Low Quality", RecordingQualityPresets.low_quality()),
        ("Medium Quality", RecordingQualityPresets.medium_quality()),
        ("High Quality", RecordingQualityPresets.high_quality()),
    ]

    for name, config in presets:
        print(f"\n{name}:")
        print(f"  Resolution: {config.resolution}")
        print(f"  Frame Rate: {config.frame_rate}")
        print(f"  Bitrate: {config.get_video_bitrate()} kbps")
        print(f"  Viewport: {config.get_viewport()}")


async def example_smooth_mouse_movement():
    """Example 7: Create smooth mouse movements."""
    print("\n=== Example 7: Smooth Mouse Movements ===")

    generator = InteractionGenerator()

    # Create smooth path from (0, 0) to (1920, 1080)
    path = generator.create_smooth_mouse_path(
        start_x=0,
        start_y=0,
        end_x=1920,
        end_y=1080,
        steps=30
    )

    print(f"Generated {len(path)} points for smooth movement")
    print(f"Start: {path[0]}")
    print(f"End: {path[-1]}")
    print(f"Sample points: {path[::10]}")  # Show every 10th point


async def example_form_interaction():
    """Example 8: Form filling interactions."""
    print("\n=== Example 8: Form Filling ===")

    generator = InteractionGenerator()

    form_fields = {
        "#name": "John Doe",
        "#email": "john@example.com",
        "#message": "Hello, I'm interested in your services!"
    }

    interactions = generator.create_form_fill_sequence(
        form_fields=form_fields,
        duration_per_field_ms=1500
    )

    print(f"Created {len(interactions)} form interactions")
    for i, interaction in enumerate(interactions):
        print(f"  {i+1}. {interaction.type} - {interaction.selector}")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Screen Recording Service - Example Usage")
    print("="*60)

    try:
        # Run examples (comment out those you don't want to run)
        # await example_basic_recording()
        # await example_custom_interactions()
        # await example_hero_section_showcase()
        # await example_full_page_tour()
        # await example_interaction_generator()
        await example_quality_presets()
        await example_smooth_mouse_movement()
        await example_form_interaction()

        print("\n" + "="*60)
        print("Examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
