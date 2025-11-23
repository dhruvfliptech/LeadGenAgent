"""
Demo Builder Usage Examples

Shows how to use the DemoSiteBuilder service to generate improved websites.
"""

import asyncio
from app.services.demo_builder import (
    DemoSiteBuilder,
    Framework,
    ImprovementPlan,
    OriginalSite,
    build_demo_quick
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker


async def example_1_basic_html_demo():
    """
    Example 1: Generate a basic HTML demo site.

    Use case: Simple landing page improvements.
    """
    print("\n=== Example 1: Basic HTML Demo ===\n")

    # Initialize AI Council
    config = AICouncilConfig(
        openrouter_api_key="your-api-key-here",  # Set in environment
        default_temperature=0.3,
        default_max_tokens=4000
    )
    ai_council = AICouncil(config)

    # Create builder
    builder = DemoSiteBuilder(ai_council)

    # Define original site
    original_site = OriginalSite(
        url="https://oldsite.com",
        html_content="""
        <!DOCTYPE html>
        <html>
        <head><title>Old Site</title></head>
        <body>
            <h1>Welcome to Our Service</h1>
            <p>We offer great products.</p>
            <a href="/contact">Contact Us</a>
        </body>
        </html>
        """,
        title="Old Service Site",
        meta_description="A basic service website"
    )

    # Define improvement plan
    improvement_plan = ImprovementPlan(
        overall_strategy="Modernize design, add clear CTAs, improve mobile experience",
        improvements=[
            {
                "title": "Add Hero Section with Value Proposition",
                "description": "Create compelling hero with headline and CTA button",
                "category": "Design",
                "priority": "high",
                "expected_impact": "30% increase in conversions"
            },
            {
                "title": "Implement Mobile-First Responsive Design",
                "description": "Use flexbox/grid for mobile-responsive layout",
                "category": "Technical",
                "priority": "high",
                "expected_impact": "Better mobile user experience"
            },
            {
                "title": "Add Modern Typography and Color Scheme",
                "description": "Use modern fonts and professional color palette",
                "category": "Design",
                "priority": "medium",
                "expected_impact": "Improved brand perception"
            }
        ],
        priority_order=["Design", "Technical", "Content"],
        estimated_impact="High - Expected 40% increase in engagement"
    )

    # Build demo site
    build = await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=Framework.HTML,
        lead_value=10000.0,  # $10K lead value
        include_comments=True
    )

    # Print results
    print(f"Status: {build.status}")
    print(f"Framework: {build.framework.value}")
    print(f"Files generated: {len(build.files)}")
    print(f"Total lines of code: {build.total_lines_of_code}")
    print(f"Generation time: {build.generation_time_seconds:.2f}s")
    print(f"Improvements applied: {len(build.improvements_applied)}")
    print(f"\nFiles:")
    for file_path in build.files.keys():
        print(f"  - {file_path}")

    # Access specific file content
    if "index.html" in build.files:
        print(f"\nindex.html preview (first 500 chars):")
        print(build.files["index.html"][:500])

    await ai_council.close()
    return build


async def example_2_react_spa():
    """
    Example 2: Generate a React single-page application.

    Use case: Interactive web app with components.
    """
    print("\n=== Example 2: React SPA Demo ===\n")

    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config)
    builder = DemoSiteBuilder(ai_council)

    original_site = OriginalSite(
        url="https://saas-product.com",
        html_content="<html>...</html>",  # Full HTML here
        title="SaaS Product Landing Page"
    )

    improvement_plan = ImprovementPlan(
        overall_strategy="Create modern SaaS landing page with interactive features",
        improvements=[
            {
                "title": "Interactive Product Demo Section",
                "description": "Add interactive product screenshots with tooltips",
                "category": "Interactivity",
                "priority": "high"
            },
            {
                "title": "Animated Statistics Counter",
                "description": "Add counting animation for key metrics",
                "category": "Engagement",
                "priority": "medium"
            },
            {
                "title": "Customer Testimonials Carousel",
                "description": "Auto-rotating testimonials with smooth transitions",
                "category": "Social Proof",
                "priority": "high"
            }
        ],
        priority_order=["Interactivity", "Social Proof", "Engagement"],
        estimated_impact="High - Modern, engaging experience"
    )

    build = await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=Framework.REACT,
        lead_value=50000.0,  # $50K lead
        include_comments=True
    )

    print(f"React app generated with {len(build.files)} files")
    print(f"Components:")
    for file_path in build.files.keys():
        if "components/" in file_path:
            print(f"  - {file_path}")

    # Check deployment config
    print(f"\nDeployment:")
    print(f"  Build: {build.deployment_config.build_command}")
    print(f"  Dev: {build.deployment_config.dev_command}")
    print(f"  Port: {build.deployment_config.port}")

    await ai_council.close()
    return build


async def example_3_nextjs_full_stack():
    """
    Example 3: Generate a Next.js full-stack application.

    Use case: SEO-optimized site with server-side rendering.
    """
    print("\n=== Example 3: Next.js Full Stack Demo ===\n")

    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config)
    builder = DemoSiteBuilder(ai_council)

    original_site = OriginalSite(
        url="https://ecommerce-store.com",
        html_content="<html>...</html>",
        title="E-commerce Store",
        meta_description="Shop our amazing products"
    )

    improvement_plan = ImprovementPlan(
        overall_strategy="Build SEO-optimized e-commerce experience with Next.js",
        improvements=[
            {
                "title": "Server-Side Rendering for SEO",
                "description": "Use Next.js SSR for better search rankings",
                "category": "Technical",
                "priority": "critical"
            },
            {
                "title": "Optimized Image Loading",
                "description": "Use Next.js Image component for performance",
                "category": "Performance",
                "priority": "high"
            },
            {
                "title": "Dynamic Meta Tags",
                "description": "Generate meta tags based on page content",
                "category": "SEO",
                "priority": "high"
            }
        ],
        priority_order=["Technical", "SEO", "Performance"],
        estimated_impact="High - 50% better SEO, faster load times"
    )

    build = await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=Framework.NEXTJS,
        lead_value=100000.0,  # $100K lead - uses premium AI model
        include_comments=True
    )

    print(f"Next.js app generated")
    print(f"App Router pages:")
    for file_path in build.files.keys():
        if "app/" in file_path:
            print(f"  - {file_path}")

    print(f"\nValidation:")
    print(f"  Valid: {build.validation_results['is_valid']}")
    print(f"  Errors: {len(build.validation_results['errors'])}")
    print(f"  Warnings: {len(build.validation_results['warnings'])}")

    await ai_council.close()
    return build


async def example_4_quick_builder():
    """
    Example 4: Use the quick builder utility function.

    Use case: Fast demo generation with minimal setup.
    """
    print("\n=== Example 4: Quick Builder ===\n")

    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config)

    # Simple improvement plan
    improvement_dict = {
        "overall_strategy": "Quick modernization",
        "improvements": [
            {
                "title": "Modern Design",
                "description": "Apply modern CSS and layout"
            }
        ],
        "priority_order": ["Design"],
        "estimated_impact": "Medium"
    }

    # Quick build
    build = await build_demo_quick(
        url="https://example.com",
        html_content="<html><body>Old site</body></html>",
        improvement_plan_dict=improvement_dict,
        ai_council=ai_council,
        framework=Framework.HTML
    )

    print(f"Quick build completed in {build.generation_time_seconds:.2f}s")
    print(f"Files: {list(build.files.keys())}")

    await ai_council.close()
    return build


async def example_5_with_ai_gym_tracking():
    """
    Example 5: Track AI costs and performance with AI-GYM.

    Use case: Monitor AI spending and model performance.
    """
    print("\n=== Example 5: With AI-GYM Tracking ===\n")

    # Initialize AI-GYM tracker
    gym_tracker = AIGymTracker()

    # Initialize AI Council with tracking
    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config, gym_tracker=gym_tracker)

    builder = DemoSiteBuilder(ai_council)

    original_site = OriginalSite(
        url="https://example.com",
        html_content="<html>...</html>",
        title="Example Site"
    )

    improvement_plan = ImprovementPlan(
        overall_strategy="Test improvements",
        improvements=[{"title": "Test", "description": "Test improvement"}],
        priority_order=["Test"],
        estimated_impact="Test"
    )

    # Build with tracking
    build = await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=Framework.REACT,
        lead_value=25000.0
    )

    # Get AI-GYM metrics
    print(f"AI Cost: ${build.ai_cost:.4f}")
    print(f"AI Model Used: {build.ai_model_used}")

    await ai_council.close()
    return build


async def example_6_error_handling():
    """
    Example 6: Handle errors and validation issues.

    Use case: Production-ready error handling.
    """
    print("\n=== Example 6: Error Handling ===\n")

    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config)
    builder = DemoSiteBuilder(ai_council)

    try:
        original_site = OriginalSite(
            url="https://example.com",
            html_content="<html>...</html>",
            title="Test Site"
        )

        improvement_plan = ImprovementPlan(
            overall_strategy="Test",
            improvements=[],
            priority_order=[],
            estimated_impact="None"
        )

        build = await builder.build_demo_site(
            original_site=original_site,
            improvement_plan=improvement_plan,
            framework=Framework.HTML
        )

        # Check validation
        if not build.validation_results["is_valid"]:
            print("WARNING: Code validation failed!")
            print(f"Errors: {build.validation_results['errors']}")

        if build.validation_results["warnings"]:
            print("Warnings:")
            for warning in build.validation_results["warnings"]:
                print(f"  - {warning}")

        print(f"Build status: {build.status}")

    except Exception as e:
        print(f"Error during build: {e}")

    finally:
        await ai_council.close()


async def example_7_save_files_to_disk():
    """
    Example 7: Save generated files to disk for deployment.

    Use case: Export demo site for actual deployment.
    """
    print("\n=== Example 7: Save Files to Disk ===\n")

    import os
    from pathlib import Path

    config = AICouncilConfig(openrouter_api_key="your-api-key-here")
    ai_council = AICouncil(config)
    builder = DemoSiteBuilder(ai_council)

    # Build demo
    original_site = OriginalSite(
        url="https://example.com",
        html_content="<html>...</html>",
        title="Example"
    )

    improvement_plan = ImprovementPlan(
        overall_strategy="Test",
        improvements=[{"title": "Test", "description": "Test"}],
        priority_order=["Test"],
        estimated_impact="Test"
    )

    build = await builder.build_demo_site(
        original_site=original_site,
        improvement_plan=improvement_plan,
        framework=Framework.REACT
    )

    # Save to disk
    output_dir = Path("/tmp/demo-site-output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path, content in build.files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'w') as f:
            f.write(content)

        print(f"Saved: {full_path}")

    # Create deployment instructions
    instructions = f"""
# Demo Site Deployment Instructions

## Generated: {build.framework.value}

## Setup:
{build.deployment_config.install_command}

## Development:
{build.deployment_config.dev_command}

## Production Build:
{build.deployment_config.build_command}

## Output Directory:
{build.deployment_config.output_directory}

## Improvements Applied:
{chr(10).join('- ' + imp for imp in build.improvements_applied)}
"""

    instructions_path = output_dir / "DEPLOYMENT.md"
    with open(instructions_path, 'w') as f:
        f.write(instructions)

    print(f"\nAll files saved to: {output_dir}")
    print(f"Deployment instructions: {instructions_path}")

    await ai_council.close()


# Main execution
async def main():
    """Run all examples."""
    print("=" * 60)
    print("Demo Site Builder - Usage Examples")
    print("=" * 60)

    # Run examples (commented out to avoid actual API calls)
    # await example_1_basic_html_demo()
    # await example_2_react_spa()
    # await example_3_nextjs_full_stack()
    # await example_4_quick_builder()
    # await example_5_with_ai_gym_tracking()
    # await example_6_error_handling()
    # await example_7_save_files_to_disk()

    print("\nExamples defined. Uncomment in main() to run.")


if __name__ == "__main__":
    asyncio.run(main())
