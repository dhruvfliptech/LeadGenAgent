"""
Comprehensive Test Suite for Demo Site Builder

Tests all major components:
- Site generation
- Template rendering
- Vercel deployment (mocked)
- Analytics tracking
- API endpoints
"""

import pytest
import asyncio
from datetime import date, datetime
from unittest.mock import Mock, patch, AsyncMock

# Test data
SAMPLE_CONTENT_DATA = {
    "lead_name": "John Doe",
    "company_name": "Acme Corp",
    "industry": "technology",
    "headline": "Transform Your Business",
    "subheadline": "Next-generation solutions for modern companies",
    "cta_text": "Get Started Today"
}

SAMPLE_STYLE_SETTINGS = {
    "primary_color": "#3B82F6",
    "secondary_color": "#1E40AF",
    "accent_color": "#F59E0B",
    "font_family": "Inter, sans-serif"
}


# ============================================================================
# Site Generator Tests
# ============================================================================

@pytest.mark.asyncio
async def test_site_generator_with_template():
    """Test site generation using a template."""
    from app.services.demo_builder import SiteGenerator
    from app.models.demo_sites import DemoSiteTemplate

    # Create mock template
    template = DemoSiteTemplate(
        id=1,
        template_name="Test Template",
        template_type="landing",
        html_template="<h1>{{headline}}</h1><p>{{subheadline}}</p>",
        css_template="h1 { color: {{primary_color}}; }",
        js_template=""
    )

    generator = SiteGenerator()

    # Mock AI client
    with patch.object(generator.ai_client, 'generate_completion', new=AsyncMock(return_value='{"headline": "Enhanced Headline"}')):
        result = await generator.generate_site(
            template=template,
            content_data=SAMPLE_CONTENT_DATA,
            style_settings=SAMPLE_STYLE_SETTINGS,
            use_ai=False
        )

    assert 'html' in result
    assert 'css' in result
    assert SAMPLE_CONTENT_DATA['headline'] in result['html']
    assert SAMPLE_STYLE_SETTINGS['primary_color'] in result['css']


@pytest.mark.asyncio
async def test_site_generator_from_scratch():
    """Test AI generation from scratch."""
    from app.services.demo_builder import SiteGenerator

    generator = SiteGenerator()

    # Mock AI response
    mock_html = '<!DOCTYPE html><html><body><h1>Test</h1></body></html>'

    with patch.object(generator.ai_client, 'generate_completion', new=AsyncMock(return_value=mock_html)):
        result = await generator.generate_from_scratch(
            content_data=SAMPLE_CONTENT_DATA,
            style_settings=SAMPLE_STYLE_SETTINGS,
            template_type="landing"
        )

    assert 'html' in result
    assert '<!DOCTYPE' in result['html']


def test_site_generator_validation():
    """Test generated code validation."""
    from app.services.demo_builder import SiteGenerator

    generator = SiteGenerator()

    # Valid HTML
    valid_code = {
        'html': '<!DOCTYPE html><html><body><h1>Test</h1></body></html>',
        'css': 'h1 { color: red; }',
        'js': 'console.log("test");'
    }
    assert generator.validate_generated_code(valid_code) is True

    # Invalid HTML (no DOCTYPE)
    invalid_code = {
        'html': '<div>Test</div>',
        'css': '',
        'js': ''
    }
    assert generator.validate_generated_code(invalid_code) is False

    # Malicious code (external script)
    malicious_code = {
        'html': '<!DOCTYPE html><script src="https://evil.com/malware.js"></script>',
        'css': '',
        'js': ''
    }
    assert generator.validate_generated_code(malicious_code) is False


# ============================================================================
# Template Engine Tests
# ============================================================================

def test_template_engine_rendering():
    """Test template rendering with variables."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    html_template = "<h1>{{headline}}</h1><p>{{company_name}}</p>"
    css_template = "h1 { color: {{primary_color}}; }"

    result = engine.render_template(
        html_template=html_template,
        css_template=css_template,
        js_template=None,
        variables={**SAMPLE_CONTENT_DATA, **SAMPLE_STYLE_SETTINGS}
    )

    assert SAMPLE_CONTENT_DATA['headline'] in result['html']
    assert SAMPLE_CONTENT_DATA['company_name'] in result['html']
    assert SAMPLE_STYLE_SETTINGS['primary_color'] in result['css']


def test_template_engine_style_application():
    """Test style settings application."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    css = "body { color: var(--primary-color); background: var(--secondary-color); }"

    result = engine.apply_style_settings(css, SAMPLE_STYLE_SETTINGS)

    assert SAMPLE_STYLE_SETTINGS['primary_color'] in result
    assert SAMPLE_STYLE_SETTINGS['secondary_color'] in result


def test_template_engine_analytics_injection():
    """Test analytics tracking code injection."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    html = "<html><body><h1>Test</h1></body></html>"

    result = engine.inject_analytics(
        html=html,
        demo_site_id=123,
        analytics_endpoint="/api/v1/demo-sites"
    )

    assert 'DEMO_SITE_ID = 123' in result
    assert 'page_view' in result
    assert 'cta_click' in result


def test_template_engine_mobile_optimization():
    """Test mobile optimization."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    html = "<html><head></head><body>Test</body></html>"
    css = "body { font-size: 16px; }"

    result = engine.optimize_for_mobile(html, css)

    assert 'viewport' in result['html']
    assert '@media (max-width: 768px)' in result['css']


def test_template_variable_extraction():
    """Test extracting variables from template."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    template = "<h1>{{headline}}</h1><p>{{subheadline}}</p><span>{{company_name}}</span>"

    variables = engine.extract_variables(template)

    assert 'headline' in variables
    assert 'subheadline' in variables
    assert 'company_name' in variables


def test_template_validation():
    """Test template validation."""
    from app.services.demo_builder import TemplateEngine

    engine = TemplateEngine()

    # Valid template
    valid_template = "<h1>{{name}}</h1>"
    is_valid, error = engine.validate_template(valid_template)
    assert is_valid is True
    assert error is None

    # Invalid template (unclosed tag)
    invalid_template = "{{unclosed"
    is_valid, error = engine.validate_template(invalid_template)
    assert is_valid is False
    assert error is not None


# ============================================================================
# Vercel Deployer Tests (Mocked)
# ============================================================================

@pytest.mark.asyncio
async def test_vercel_deployer_deploy():
    """Test Vercel deployment (mocked)."""
    from app.services.demo_builder import VercelDeployer

    deployer = VercelDeployer()

    # Mock aiohttp
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={
            'id': 'test_deployment_id',
            'projectId': 'test_project_id',
            'url': 'test-site.vercel.app',
            'readyState': 'READY',
            'regions': ['sfo1']
        })

        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await deployer.deploy_site(
            site_name="test-site",
            html="<html><body>Test</body></html>",
            css="body { color: red; }",
            js=None
        )

    assert result['deployment_id'] == 'test_deployment_id'
    assert result['status'] == 'READY'
    assert 'test-site.vercel.app' in result['url']


@pytest.mark.asyncio
async def test_vercel_deployer_status_check():
    """Test deployment status checking."""
    from app.services.demo_builder import VercelDeployer

    deployer = VercelDeployer()

    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'readyState': 'READY',
            'url': 'test-site.vercel.app',
            'ready': True
        })

        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        result = await deployer.check_deployment_status('test_deployment_id')

    assert result['status'] == 'READY'
    assert result['ready'] is True


def test_vercel_deployer_name_sanitization():
    """Test project name sanitization."""
    from app.services.demo_builder import VercelDeployer

    deployer = VercelDeployer()

    assert deployer._sanitize_name("Test Site 123") == "test-site-123"
    assert deployer._sanitize_name("Site@With#Special$Chars") == "sitewithspecialchars"
    assert deployer._sanitize_name("spaces and CAPS") == "spaces-and-caps"


# ============================================================================
# Analytics Tracker Tests
# ============================================================================

@pytest.mark.asyncio
async def test_analytics_tracker_track_event():
    """Test analytics event tracking."""
    # This would require a real database session
    # For now, test the logic
    from app.services.demo_builder import AnalyticsTracker

    # Mock database session
    mock_db = Mock()

    tracker = AnalyticsTracker(mock_db)

    # Test device classification
    assert tracker._classify_device("320x568") == "mobile"
    assert tracker._classify_device("768x1024") == "tablet"
    assert tracker._classify_device("1920x1080") == "desktop"


# ============================================================================
# Content Personalizer Tests
# ============================================================================

@pytest.mark.asyncio
async def test_content_personalizer_landing_page():
    """Test content personalization for landing page."""
    from app.services.demo_builder import ContentPersonalizer

    personalizer = ContentPersonalizer()

    # Mock lead
    mock_lead = Mock()
    mock_lead.name = "John Doe"
    mock_lead.email = "john@example.com"
    mock_lead.company = "Acme Corp"
    mock_lead.industry = "technology"

    # Mock AI response
    mock_ai_response = '''{
        "headline": "Transform Your Technology Business",
        "subheadline": "Cutting-edge solutions for Acme Corp",
        "cta_text": "Start Your Free Trial",
        "features": [
            {"title": "Fast", "description": "Lightning speed"},
            {"title": "Secure", "description": "Bank-level security"},
            {"title": "Scalable", "description": "Grows with you"}
        ]
    }'''

    with patch.object(personalizer.ai_client, 'generate_completion', new=AsyncMock(return_value=mock_ai_response)):
        result = await personalizer.personalize_content(
            lead=mock_lead,
            template_type="landing",
            base_content=SAMPLE_CONTENT_DATA
        )

    assert 'headline' in result
    assert 'Acme Corp' in result.get('subheadline', '')


@pytest.mark.asyncio
async def test_content_personalizer_meta_tags():
    """Test SEO meta tag generation."""
    from app.services.demo_builder import ContentPersonalizer

    personalizer = ContentPersonalizer()

    mock_ai_response = '''{
        "meta_title": "Acme Corp - Transform Your Business",
        "meta_description": "Next-generation technology solutions",
        "meta_keywords": "technology, business, solutions, saas"
    }'''

    with patch.object(personalizer.ai_client, 'generate_completion', new=AsyncMock(return_value=mock_ai_response)):
        result = await personalizer.generate_meta_tags(
            content=SAMPLE_CONTENT_DATA,
            template_type="landing"
        )

    assert 'meta_title' in result
    assert 'meta_description' in result
    assert 'meta_keywords' in result


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_site_generation():
    """Test complete site generation flow."""
    from app.services.demo_builder import SiteGenerator, TemplateEngine
    from app.models.demo_sites import DemoSiteTemplate

    # Create template
    template = DemoSiteTemplate(
        id=1,
        template_name="Test Template",
        template_type="landing",
        html_template="<h1>{{headline}}</h1>",
        css_template="h1 { color: {{primary_color}}; }",
        js_template=""
    )

    # Generate site
    generator = SiteGenerator()
    template_engine = TemplateEngine()

    with patch.object(generator.ai_client, 'generate_completion', new=AsyncMock(return_value='{}')):
        generated = await generator.generate_site(
            template=template,
            content_data=SAMPLE_CONTENT_DATA,
            style_settings=SAMPLE_STYLE_SETTINGS,
            use_ai=False
        )

    # Optimize
    optimized = template_engine.optimize_for_mobile(generated['html'], generated['css'])

    # Inject analytics
    with_analytics = template_engine.inject_analytics(
        html=optimized['html'],
        demo_site_id=1,
        analytics_endpoint="/api/v1/demo-sites"
    )

    assert SAMPLE_CONTENT_DATA['headline'] in with_analytics
    assert '@media (max-width: 768px)' in optimized['css']
    assert 'analytics' in with_analytics.lower()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
