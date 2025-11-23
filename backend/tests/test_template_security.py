"""
Test Template Security Module

Comprehensive tests for XSS prevention, template injection protection,
and input sanitization.
"""

import pytest
from app.core.template_security import (
    TemplateSanitizer,
    SecureTemplateEngine,
    ContentSecurityPolicy,
    TemplateSecurityValidator
)


class TestTemplateSanitizer:
    """Test the TemplateSanitizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = TemplateSanitizer()

    def test_sanitize_html_removes_script_tags(self):
        """Test that script tags are removed."""
        html = '<p>Hello</p><script>alert("XSS")</script><p>World</p>'
        result = self.sanitizer.sanitize_html(html)
        assert '<script>' not in result
        assert 'alert' not in result
        assert '<p>Hello</p>' in result
        assert '<p>World</p>' in result

    def test_sanitize_html_removes_event_handlers(self):
        """Test that event handlers are removed."""
        html = '<div onclick="alert(\'XSS\')">Click me</div>'
        result = self.sanitizer.sanitize_html(html)
        assert 'onclick' not in result
        assert 'alert' not in result
        assert '<div>Click me</div>' in result

    def test_sanitize_html_removes_javascript_urls(self):
        """Test that javascript: URLs are sanitized."""
        html = '<a href="javascript:alert(\'XSS\')">Link</a>'
        result = self.sanitizer.sanitize_html(html)
        assert 'javascript:' not in result
        assert 'alert' not in result

    def test_sanitize_css_removes_expressions(self):
        """Test that CSS expressions are removed."""
        css = 'body { background: expression(alert("XSS")); color: red; }'
        result = self.sanitizer.sanitize_css(css)
        assert 'expression' not in result
        assert 'alert' not in result
        assert 'color: red' in result or 'color' in result

    def test_sanitize_css_removes_javascript_urls(self):
        """Test that javascript: URLs in CSS are removed."""
        css = 'body { background: url("javascript:alert(1)"); }'
        result = self.sanitizer.sanitize_css(css)
        assert 'javascript:' not in result

    def test_sanitize_javascript_blocks_dangerous_functions(self):
        """Test that dangerous JavaScript functions are blocked."""
        js = 'eval("alert(1)")'
        result = self.sanitizer.sanitize_javascript(js)
        assert result == ""

    def test_sanitize_javascript_allows_safe_code(self):
        """Test that safe JavaScript is allowed."""
        js = 'console.log("Hello")'
        result = self.sanitizer.sanitize_javascript(js)
        assert result == js

    def test_sanitize_url_blocks_javascript_protocol(self):
        """Test that javascript: protocol URLs are blocked."""
        url = 'javascript:alert(1)'
        result = self.sanitizer.sanitize_url(url)
        assert result == "#"

    def test_sanitize_url_allows_http_https(self):
        """Test that HTTP/HTTPS URLs are allowed."""
        urls = [
            'https://example.com',
            'http://example.com',
            'mailto:test@example.com',
            'tel:+1234567890'
        ]
        for url in urls:
            result = self.sanitizer.sanitize_url(url)
            assert result == url


class TestSecureTemplateEngine:
    """Test the SecureTemplateEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = SecureTemplateEngine()

    def test_render_template_safe_escapes_html(self):
        """Test that HTML is escaped by default."""
        template = "Hello {{ name }}!"
        context = {"name": "<script>alert('XSS')</script>"}
        result = self.engine.render_template_safe(template, context)
        assert '<script>' not in result
        assert '&lt;script&gt;' in result or 'alert' not in result

    def test_render_template_safe_blocks_dangerous_constructs(self):
        """Test that dangerous Jinja2 constructs are blocked."""
        template = "{% import os %}{{ os.system('ls') }}"
        context = {}
        result = self.engine.render_template_safe(template, context)
        assert 'import' not in result
        assert 'os.system' not in result

    def test_render_template_safe_sanitizes_output(self):
        """Test that output is sanitized when requested."""
        template = "<div>{{ content }}</div>"
        context = {"content": "Hello <script>alert(1)</script> World"}
        result = self.engine.render_template_safe(template, context, sanitize_output=True)
        assert '<script>' not in result

    def test_context_sanitization(self):
        """Test that context values are sanitized."""
        template = "{{ user_input }}"
        context = {
            "user_input": "<img src=x onerror=alert(1)>",
            "safe_value": "Hello World"
        }
        result = self.engine.render_template_safe(template, context)
        assert 'onerror' not in result
        assert 'alert' not in result


class TestContentSecurityPolicy:
    """Test the ContentSecurityPolicy class."""

    def test_generate_csp_header_strict(self):
        """Test strict CSP header generation."""
        csp = ContentSecurityPolicy()
        headers = csp.generate_csp_header(strict=True)

        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_generate_csp_header_with_nonce(self):
        """Test CSP header with nonce for inline scripts."""
        csp = ContentSecurityPolicy()
        nonce = csp.generate_nonce()
        headers = csp.generate_csp_header(nonce=nonce, strict=True)

        assert f"'nonce-{nonce}'" in headers["Content-Security-Policy"]

    def test_generate_nonce_is_unique(self):
        """Test that nonces are unique."""
        csp = ContentSecurityPolicy()
        nonces = [csp.generate_nonce() for _ in range(10)]
        assert len(set(nonces)) == 10


class TestTemplateSecurityValidator:
    """Test the TemplateSecurityValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TemplateSecurityValidator()

    def test_validate_html_template_detects_xss(self):
        """Test that XSS attempts are detected."""
        template = '<div>{{ user }}<script>alert(1)</script></div>'
        is_valid, error = self.validator.validate_template(template, "html")
        assert not is_valid
        assert "dangerous patterns" in error.lower()

    def test_validate_html_template_detects_injection(self):
        """Test that template injection is detected."""
        template = '{{ __class__.__mro__[1].__subclasses__() }}'
        is_valid, error = self.validator.validate_template(template, "html")
        assert not is_valid
        assert "injection" in error.lower()

    def test_validate_html_template_allows_safe(self):
        """Test that safe templates pass validation."""
        template = '<div>Hello {{ username }}, welcome!</div>'
        is_valid, error = self.validator.validate_template(template, "html")
        assert is_valid
        assert error is None

    def test_validate_css_template_detects_dangerous(self):
        """Test that dangerous CSS is detected."""
        css = 'body { background: expression(alert(1)); }'
        is_valid, error = self.validator.validate_template(css, "css")
        assert not is_valid
        assert "expression" in error.lower()

    def test_validate_css_template_allows_safe(self):
        """Test that safe CSS passes validation."""
        css = 'body { background: #fff; color: #000; }'
        is_valid, error = self.validator.validate_template(css, "css")
        assert is_valid
        assert error is None

    def test_validate_js_template_detects_eval(self):
        """Test that eval() is detected in JavaScript."""
        js = 'eval("alert(1)")'
        is_valid, error = self.validator.validate_template(js, "js")
        assert not is_valid
        assert "eval" in error.lower()

    def test_validate_js_template_detects_dangerous_functions(self):
        """Test that dangerous functions are detected."""
        dangerous_js = [
            'setTimeout("alert(1)", 1000)',
            'document.cookie = "stolen"',
            'localStorage.setItem("key", "value")'
        ]
        for js in dangerous_js:
            is_valid, error = self.validator.validate_template(js, "js")
            assert not is_valid


class TestIntegration:
    """Integration tests for the security module."""

    def test_full_template_rendering_pipeline(self):
        """Test the complete template rendering pipeline with security."""
        # Create engine
        engine = SecureTemplateEngine()
        validator = TemplateSecurityValidator()

        # Template with potential XSS
        template = """
        <h1>Welcome {{ name }}</h1>
        <p>Your message: {{ message }}</p>
        <a href="{{ link }}">Click here</a>
        """

        # Context with malicious input
        context = {
            "name": "<script>alert('XSS')</script>",
            "message": "Hello <img src=x onerror=alert(1)>",
            "link": "javascript:alert('XSS')"
        }

        # Validate template
        is_valid, error = validator.validate_template(template, "html")
        assert is_valid

        # Render with security
        result = engine.render_template_safe(template, context, sanitize_output=True)

        # Verify XSS is prevented
        assert '<script>' not in result
        assert 'onerror' not in result
        assert 'javascript:' not in result

    def test_email_template_security(self):
        """Test email template rendering with tracking injection."""
        from app.services.email_template_service import EmailTemplateService

        service = EmailTemplateService()

        # Template with potential XSS
        template = """
        <html>
        <body>
            <h1>Hello {{ name }}</h1>
            <p>{{ content }}</p>
        </body>
        </html>
        """

        # Malicious context
        context = {
            "name": "<script>alert('XSS')</script>",
            "content": "<iframe src='evil.com'></iframe>"
        }

        # Render template
        result = service.render_template(template, context)

        # Verify security
        assert '<script>' not in result
        assert '<iframe' not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])