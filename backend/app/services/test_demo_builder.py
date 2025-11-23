"""
Tests for Demo Site Builder service.

Tests code generation, validation, and framework support.
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from app.services.demo_builder import (
    DemoSiteBuilder,
    Framework,
    BuildStatus,
    ImprovementPlan,
    OriginalSite,
    DemoSiteBuild,
    build_demo_quick
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilResponse, Message
from app.services.ai_mvp.semantic_router import RouteDecision, ModelTier, TaskComplexity


@pytest.fixture
def mock_ai_council():
    """Create mock AI Council."""
    council = Mock(spec=AICouncil)
    council.complete = AsyncMock()
    return council


@pytest.fixture
def sample_original_site() -> OriginalSite:
    """Sample original website data."""
    return OriginalSite(
        url="https://example.com",
        html_content="""
        <!DOCTYPE html>
        <html>
        <head><title>Example Site</title></head>
        <body>
            <h1>Welcome</h1>
            <p>This is an example site.</p>
        </body>
        </html>
        """,
        title="Example Site",
        meta_description="An example website"
    )


@pytest.fixture
def sample_improvement_plan() -> ImprovementPlan:
    """Sample improvement plan."""
    return ImprovementPlan(
        overall_strategy="Modernize design and improve performance",
        improvements=[
            {
                "title": "Improve Hero Section",
                "description": "Add compelling headline and CTA",
                "category": "Design",
                "priority": "high"
            },
            {
                "title": "Add Mobile Responsiveness",
                "description": "Implement responsive CSS",
                "category": "Technical",
                "priority": "high"
            },
            {
                "title": "Optimize Page Speed",
                "description": "Lazy load images and minify assets",
                "category": "Performance",
                "priority": "medium"
            }
        ],
        priority_order=["Design", "Technical", "Performance"],
        estimated_impact="High - 40% increase in conversion rate"
    )


@pytest.fixture
def mock_ai_response() -> AICouncilResponse:
    """Mock AI response with generated code."""
    return AICouncilResponse(
        content="""
```html
<!-- FILE: index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Improved Site</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- IMPROVEMENT: Added compelling hero section -->
    <section class="hero">
        <h1>Transform Your Business</h1>
        <button class="cta">Get Started</button>
    </section>
    <script src="script.js"></script>
</body>
</html>
```

```css
/* FILE: styles.css */
/* IMPROVEMENT: Mobile-responsive styles */
.hero {
    padding: 4rem 2rem;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

@media (max-width: 768px) {
    .hero {
        padding: 2rem 1rem;
    }
}
```

```javascript
// FILE: script.js
// IMPROVEMENT: Lazy loading for performance
document.addEventListener('DOMContentLoaded', () => {
    console.log('Demo site loaded');
});
```
        """,
        model_used="anthropic/claude-3-haiku",
        model_tier="cheap",
        prompt_tokens=1000,
        completion_tokens=500,
        total_cost=0.002,
        request_id=123,
        route_decision=RouteDecision(
            model_name="anthropic/claude-3-haiku",
            model_tier=ModelTier.CHEAP,
            task_complexity=TaskComplexity.COMPLEX,
            reasoning="Test routing",
            estimated_cost=0.002
        )
    )


class TestDemoSiteBuilder:
    """Test DemoSiteBuilder class."""

    @pytest.mark.asyncio
    async def test_init(self, mock_ai_council):
        """Test builder initialization."""
        builder = DemoSiteBuilder(mock_ai_council)
        assert builder.ai_council == mock_ai_council

    @pytest.mark.asyncio
    async def test_plan_file_structure_html(self, mock_ai_council):
        """Test file structure planning for HTML."""
        builder = DemoSiteBuilder(mock_ai_council)

        structure = await builder._plan_file_structure(
            framework=Framework.HTML,
            improvement_plan=Mock()
        )

        assert "index.html" in structure
        assert "styles.css" in structure
        assert "script.js" in structure
        assert "README.md" in structure

    @pytest.mark.asyncio
    async def test_plan_file_structure_react(self, mock_ai_council):
        """Test file structure planning for React."""
        builder = DemoSiteBuilder(mock_ai_council)

        structure = await builder._plan_file_structure(
            framework=Framework.REACT,
            improvement_plan=Mock()
        )

        assert "package.json" in structure
        assert "src/App.tsx" in structure
        assert "src/components/Hero.tsx" in structure
        assert "README.md" in structure

    @pytest.mark.asyncio
    async def test_plan_file_structure_nextjs(self, mock_ai_council):
        """Test file structure planning for Next.js."""
        builder = DemoSiteBuilder(mock_ai_council)

        structure = await builder._plan_file_structure(
            framework=Framework.NEXTJS,
            improvement_plan=Mock()
        )

        assert "package.json" in structure
        assert "app/page.tsx" in structure
        assert "app/layout.tsx" in structure
        assert "next.config.js" in structure

    def test_parse_ai_code_response(self, mock_ai_council, mock_ai_response):
        """Test parsing AI response into files."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = builder._parse_ai_code_response(
            mock_ai_response.content,
            Framework.HTML
        )

        assert "index.html" in files
        assert "styles.css" in files
        assert "script.js" in files

        # Check content was parsed correctly
        assert "<!DOCTYPE html>" in files["index.html"]
        assert ".hero" in files["styles.css"]
        assert "DOMContentLoaded" in files["script.js"]

    def test_parse_ai_code_response_with_tsx(self, mock_ai_council):
        """Test parsing React/TypeScript code."""
        builder = DemoSiteBuilder(mock_ai_council)

        response = """
```tsx
// FILE: src/App.tsx
import React from 'react';

export default function App() {
    return <div>Hello World</div>;
}
```
        """

        files = builder._parse_ai_code_response(response, Framework.REACT)

        assert "src/App.tsx" in files
        assert "import React" in files["src/App.tsx"]

    def test_fallback_parse_code_blocks(self, mock_ai_council):
        """Test fallback parsing when FILE comments are missing."""
        builder = DemoSiteBuilder(mock_ai_council)

        response = """
```html
<!DOCTYPE html>
<html><body>Test</body></html>
```

```css
body { margin: 0; }
```
        """

        files = builder._fallback_parse_code_blocks(response, Framework.HTML)

        assert len(files) >= 2
        assert any("html" in path for path in files.keys())
        assert any("css" in path for path in files.keys())

    def test_get_react_config_files(self, mock_ai_council):
        """Test React configuration file generation."""
        builder = DemoSiteBuilder(mock_ai_council)

        config_files = builder._get_react_config_files()

        assert "package.json" in config_files
        assert "tsconfig.json" in config_files
        assert "vite.config.ts" in config_files
        assert ".gitignore" in config_files

        # Validate package.json is valid JSON
        import json
        json.loads(config_files["package.json"])

    def test_get_nextjs_config_files(self, mock_ai_council):
        """Test Next.js configuration file generation."""
        builder = DemoSiteBuilder(mock_ai_council)

        config_files = builder._get_nextjs_config_files()

        assert "package.json" in config_files
        assert "tsconfig.json" in config_files
        assert "next.config.js" in config_files
        assert "tailwind.config.js" in config_files

        # Validate package.json is valid JSON
        import json
        json.loads(config_files["package.json"])

    def test_generate_readme_html(self, mock_ai_council, sample_improvement_plan):
        """Test README generation for HTML."""
        builder = DemoSiteBuilder(mock_ai_council)

        readme = builder._generate_readme(
            Framework.HTML,
            sample_improvement_plan,
            "https://example.com"
        )

        assert "# Demo Site" in readme
        assert "https://example.com" in readme
        assert "Improve Hero Section" in readme
        assert "Open `index.html`" in readme

    def test_generate_readme_react(self, mock_ai_council, sample_improvement_plan):
        """Test README generation for React."""
        builder = DemoSiteBuilder(mock_ai_council)

        readme = builder._generate_readme(
            Framework.REACT,
            sample_improvement_plan,
            "https://example.com"
        )

        assert "npm install" in readme
        assert "npm run dev" in readme
        assert "REACT" in readme.upper()

    def test_generate_readme_nextjs(self, mock_ai_council, sample_improvement_plan):
        """Test README generation for Next.js."""
        builder = DemoSiteBuilder(mock_ai_council)

        readme = builder._generate_readme(
            Framework.NEXTJS,
            sample_improvement_plan,
            "https://example.com"
        )

        assert "npm install" in readme
        assert "npm run dev" in readme
        assert "NEXTJS" in readme.upper() or "NEXT.JS" in readme.upper()

    @pytest.mark.asyncio
    async def test_validate_code_valid(self, mock_ai_council):
        """Test code validation with valid files."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = {
            "index.html": "<!DOCTYPE html><html><body>Test</body></html>",
            "styles.css": "body { margin: 0; }",
            "package.json": '{"name": "test", "version": "1.0.0"}'
        }

        results = await builder._validate_code(files, Framework.HTML)

        assert results["is_valid"] is True
        assert results["file_count"] == 3
        assert len(results["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_code_invalid_json(self, mock_ai_council):
        """Test code validation with invalid JSON."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = {
            "package.json": '{"name": "test", invalid json}'
        }

        results = await builder._validate_code(files, Framework.REACT)

        assert results["is_valid"] is False
        assert len(results["errors"]) > 0
        assert any("Invalid JSON" in error for error in results["errors"])

    @pytest.mark.asyncio
    async def test_validate_code_empty_file(self, mock_ai_council):
        """Test code validation with empty file."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = {
            "index.html": "",
            "styles.css": "   "
        }

        results = await builder._validate_code(files, Framework.HTML)

        assert results["is_valid"] is False
        assert len(results["errors"]) >= 2

    @pytest.mark.asyncio
    async def test_validate_code_placeholders(self, mock_ai_council):
        """Test code validation detects placeholders."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = {
            "index.html": "<!DOCTYPE html><html><body>TODO: Add content here</body></html>"
        }

        results = await builder._validate_code(files, Framework.HTML)

        assert len(results["warnings"]) > 0
        assert any("TODO" in warning for warning in results["warnings"])

    @pytest.mark.asyncio
    async def test_validate_code_missing_required_files(self, mock_ai_council):
        """Test validation catches missing required files."""
        builder = DemoSiteBuilder(mock_ai_council)

        # HTML without index.html
        files = {"styles.css": "body { margin: 0; }"}
        results = await builder._validate_code(files, Framework.HTML)
        assert results["is_valid"] is False

        # React without package.json
        files = {"src/App.tsx": "export default function App() {}"}
        results = await builder._validate_code(files, Framework.REACT)
        assert results["is_valid"] is False

    def test_create_deployment_config_html(self, mock_ai_council):
        """Test deployment config for HTML."""
        builder = DemoSiteBuilder(mock_ai_council)

        config = builder._create_deployment_config(Framework.HTML)

        assert config.framework == Framework.HTML
        assert config.port == 8000
        assert "http.server" in config.dev_command

    def test_create_deployment_config_react(self, mock_ai_council):
        """Test deployment config for React."""
        builder = DemoSiteBuilder(mock_ai_council)

        config = builder._create_deployment_config(Framework.REACT)

        assert config.framework == Framework.REACT
        assert config.output_directory == "dist"
        assert "npm run build" in config.build_command
        assert config.port == 5173

    def test_create_deployment_config_nextjs(self, mock_ai_council):
        """Test deployment config for Next.js."""
        builder = DemoSiteBuilder(mock_ai_council)

        config = builder._create_deployment_config(Framework.NEXTJS)

        assert config.framework == Framework.NEXTJS
        assert config.output_directory == ".next"
        assert "npm run build" in config.build_command
        assert config.port == 3000

    def test_get_system_prompt_html(self, mock_ai_council):
        """Test system prompt generation for HTML."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._get_system_prompt("html")

        assert "HTML" in prompt or "html" in prompt
        assert "FILE:" in prompt
        assert "production-ready" in prompt.lower()

    def test_get_system_prompt_react(self, mock_ai_council):
        """Test system prompt generation for React."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._get_system_prompt("react")

        assert "React" in prompt
        assert "TypeScript" in prompt
        assert "hooks" in prompt.lower()

    def test_get_system_prompt_nextjs(self, mock_ai_council):
        """Test system prompt generation for Next.js."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._get_system_prompt("nextjs")

        assert "Next.js" in prompt
        assert "App Router" in prompt

    def test_build_html_generation_prompt(
        self,
        mock_ai_council,
        sample_original_site,
        sample_improvement_plan
    ):
        """Test HTML generation prompt building."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._build_html_generation_prompt(
            sample_original_site,
            sample_improvement_plan,
            include_comments=True
        )

        assert sample_original_site.url in prompt
        assert sample_original_site.title in prompt
        assert sample_improvement_plan.overall_strategy in prompt
        assert "Improve Hero Section" in prompt
        assert "inline comments" in prompt.lower()

    def test_build_react_generation_prompt(
        self,
        mock_ai_council,
        sample_original_site,
        sample_improvement_plan
    ):
        """Test React generation prompt building."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._build_react_generation_prompt(
            sample_original_site,
            sample_improvement_plan,
            include_comments=True
        )

        assert "React" in prompt
        assert "TypeScript" in prompt
        assert sample_original_site.url in prompt
        assert "src/App.tsx" in prompt

    def test_build_nextjs_generation_prompt(
        self,
        mock_ai_council,
        sample_original_site,
        sample_improvement_plan
    ):
        """Test Next.js generation prompt building."""
        builder = DemoSiteBuilder(mock_ai_council)

        prompt = builder._build_nextjs_generation_prompt(
            sample_original_site,
            sample_improvement_plan,
            include_comments=True
        )

        assert "Next.js" in prompt
        assert "App Router" in prompt
        assert "app/page.tsx" in prompt

    @pytest.mark.asyncio
    async def test_generate_html_site(
        self,
        mock_ai_council,
        sample_original_site,
        sample_improvement_plan,
        mock_ai_response
    ):
        """Test HTML site generation."""
        mock_ai_council.complete.return_value = mock_ai_response

        builder = DemoSiteBuilder(mock_ai_council)

        files = await builder._generate_html_site(
            sample_original_site,
            sample_improvement_plan,
            lead_value=None,
            include_comments=True
        )

        # Verify AI was called
        mock_ai_council.complete.assert_called_once()

        # Verify files were generated
        assert "index.html" in files
        assert "styles.css" in files
        assert "script.js" in files
        assert "README.md" in files

    @pytest.mark.asyncio
    async def test_build_demo_site_complete(
        self,
        mock_ai_council,
        sample_original_site,
        sample_improvement_plan,
        mock_ai_response
    ):
        """Test complete demo site build process."""
        mock_ai_council.complete.return_value = mock_ai_response

        builder = DemoSiteBuilder(mock_ai_council)

        build = await builder.build_demo_site(
            original_site=sample_original_site,
            improvement_plan=sample_improvement_plan,
            framework=Framework.HTML,
            lead_value=50000.0,
            include_comments=True
        )

        # Verify build completed
        assert isinstance(build, DemoSiteBuild)
        assert build.status == BuildStatus.COMPLETED
        assert build.framework == Framework.HTML
        assert len(build.files) > 0
        assert build.total_lines_of_code > 0
        assert build.generation_time_seconds > 0
        assert len(build.improvements_applied) > 0

        # Verify deployment config
        assert build.deployment_config.framework == Framework.HTML

        # Verify validation was run
        assert "is_valid" in build.validation_results


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.mark.asyncio
    async def test_build_demo_quick(self, mock_ai_council, mock_ai_response):
        """Test quick demo build utility function."""
        mock_ai_council.complete.return_value = mock_ai_response

        improvement_dict = {
            "overall_strategy": "Test strategy",
            "improvements": [
                {"title": "Test", "description": "Test improvement"}
            ],
            "priority_order": ["Test"],
            "estimated_impact": "High"
        }

        build = await build_demo_quick(
            url="https://example.com",
            html_content="<html><body>Test</body></html>",
            improvement_plan_dict=improvement_dict,
            ai_council=mock_ai_council,
            framework=Framework.HTML
        )

        assert isinstance(build, DemoSiteBuild)
        assert build.framework == Framework.HTML


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_build_with_no_improvements(
        self,
        mock_ai_council,
        sample_original_site,
        mock_ai_response
    ):
        """Test build with empty improvement plan."""
        mock_ai_council.complete.return_value = mock_ai_response

        builder = DemoSiteBuilder(mock_ai_council)

        empty_plan = ImprovementPlan(
            overall_strategy="No changes",
            improvements=[],
            priority_order=[],
            estimated_impact="None"
        )

        build = await builder.build_demo_site(
            original_site=sample_original_site,
            improvement_plan=empty_plan,
            framework=Framework.HTML
        )

        assert build.status == BuildStatus.COMPLETED
        assert len(build.improvements_applied) == 0

    @pytest.mark.asyncio
    async def test_build_with_large_html(
        self,
        mock_ai_council,
        sample_improvement_plan,
        mock_ai_response
    ):
        """Test build with very large HTML content."""
        mock_ai_council.complete.return_value = mock_ai_response

        builder = DemoSiteBuilder(mock_ai_council)

        large_site = OriginalSite(
            url="https://example.com",
            html_content="<div>" + ("test " * 10000) + "</div>",
            title="Large Site"
        )

        build = await builder.build_demo_site(
            original_site=large_site,
            improvement_plan=sample_improvement_plan,
            framework=Framework.HTML
        )

        assert build.status == BuildStatus.COMPLETED

    def test_parse_malformed_ai_response(self, mock_ai_council):
        """Test parsing malformed AI response."""
        builder = DemoSiteBuilder(mock_ai_council)

        # Missing closing code fence
        malformed = """
```html
<html><body>Test</body></html>
        """

        files = builder._parse_ai_code_response(malformed, Framework.HTML)

        # Should fallback to alternative parsing
        assert isinstance(files, dict)

    def test_parse_empty_ai_response(self, mock_ai_council):
        """Test parsing empty AI response."""
        builder = DemoSiteBuilder(mock_ai_council)

        files = builder._parse_ai_code_response("", Framework.HTML)

        assert isinstance(files, dict)
        assert len(files) == 0


# Pytest configuration
pytest_plugins = []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
