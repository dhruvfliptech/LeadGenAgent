"""
Template Security Module

Comprehensive security layer for template rendering with:
- HTML sanitization using bleach
- Template injection prevention
- XSS protection
- Content Security Policy headers
- Sandboxed Jinja2 environment
"""

import re
import logging
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Set, Union
from html import escape
from urllib.parse import urlparse

import bleach
from bleach.css_sanitizer import CSSSanitizer
from jinja2 import Environment, BaseLoader, TemplateError
from jinja2.sandbox import SandboxedEnvironment
from markupsafe import Markup

logger = logging.getLogger(__name__)


class TemplateSanitizer:
    """
    Comprehensive HTML/CSS/JS sanitization for templates.
    Prevents XSS, template injection, and other security vulnerabilities.
    """

    # Safe HTML tags for user content
    ALLOWED_TAGS = [
        'p', 'br', 'span', 'div', 'strong', 'em', 'u', 'i', 'b',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'a', 'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
        'section', 'article', 'header', 'footer', 'nav', 'aside'
    ]

    # Safe HTML attributes
    ALLOWED_ATTRIBUTES = {
        '*': ['class', 'id', 'title', 'data-*'],
        'a': ['href', 'target', 'rel'],
        'img': ['src', 'alt', 'width', 'height'],
        'table': ['border', 'cellspacing', 'cellpadding'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }

    # Safe CSS properties
    ALLOWED_CSS_PROPERTIES = [
        'color', 'background-color', 'font-family', 'font-size',
        'font-weight', 'text-align', 'text-decoration', 'padding',
        'margin', 'border', 'width', 'height', 'max-width', 'max-height',
        'display', 'flex', 'grid', 'position', 'top', 'left', 'right',
        'bottom', 'z-index', 'opacity', 'visibility'
    ]

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'javascript:', r'data:text/html', r'vbscript:', r'onload=',
        r'onerror=', r'onclick=', r'onmouseover=', r'onfocus=',
        r'<script', r'</script>', r'<iframe', r'eval\(',
        r'document\.', r'window\.', r'alert\(', r'prompt\(',
        r'confirm\(', r'\.innerHTML', r'\.outerHTML'
    ]

    def __init__(self):
        """Initialize the sanitizer with custom CSS sanitizer."""
        self.css_sanitizer = CSSSanitizer(
            allowed_css_properties=self.ALLOWED_CSS_PROPERTIES
        )

    def sanitize_html(
        self,
        html: str,
        strip_comments: bool = True,
        strip_tags: bool = False
    ) -> str:
        """
        Sanitize HTML content to prevent XSS attacks.

        Args:
            html: Raw HTML content
            strip_comments: Remove HTML comments
            strip_tags: Remove all tags (text only)

        Returns:
            Sanitized HTML string
        """
        if not html:
            return ""

        try:
            # Check for dangerous patterns first
            if self._contains_dangerous_patterns(html):
                logger.warning("Dangerous patterns detected in HTML, stripping all tags")
                strip_tags = True

            # Sanitize with bleach
            if strip_tags:
                # Strip all HTML tags, return text only
                cleaned = bleach.clean(
                    html,
                    tags=[],
                    strip=True,
                    strip_comments=strip_comments
                )
            else:
                # Allow safe tags and attributes
                cleaned = bleach.clean(
                    html,
                    tags=self.ALLOWED_TAGS,
                    attributes=self.ALLOWED_ATTRIBUTES,
                    strip=True,
                    strip_comments=strip_comments,
                    css_sanitizer=self.css_sanitizer
                )

            # Additional cleanup for template variables
            cleaned = self._sanitize_template_variables(cleaned)

            return cleaned

        except Exception as e:
            logger.error(f"HTML sanitization failed: {e}")
            # Return escaped version on error
            return escape(html)

    def sanitize_css(self, css: str) -> str:
        """
        Sanitize CSS to prevent style-based attacks.

        Args:
            css: Raw CSS content

        Returns:
            Sanitized CSS string
        """
        if not css:
            return ""

        try:
            # Remove dangerous CSS patterns
            dangerous_css_patterns = [
                r'expression\s*\(',
                r'javascript:',
                r'behavior:',
                r'binding:',
                r'-moz-binding:',
                r'@import',
                r'@charset'
            ]

            for pattern in dangerous_css_patterns:
                css = re.sub(pattern, '', css, flags=re.IGNORECASE)

            # Use bleach's CSS sanitizer
            style_tag = f'<style>{css}</style>'
            cleaned = bleach.clean(
                style_tag,
                tags=['style'],
                strip=True,
                css_sanitizer=self.css_sanitizer
            )

            # Extract CSS from cleaned style tag
            cleaned_css = re.sub(r'</?style[^>]*>', '', cleaned)

            return cleaned_css

        except Exception as e:
            logger.error(f"CSS sanitization failed: {e}")
            return ""

    def sanitize_javascript(self, js: str) -> str:
        """
        Sanitize JavaScript code (very restrictive).

        Args:
            js: Raw JavaScript code

        Returns:
            Sanitized JavaScript or empty string if dangerous
        """
        if not js:
            return ""

        try:
            # List of allowed safe patterns
            safe_patterns = [
                r'^console\.log\(',
                r'^var\s+\w+\s*=\s*["\'\d]',
                r'^const\s+\w+\s*=\s*["\'\d]',
                r'^let\s+\w+\s*=\s*["\'\d]'
            ]

            # Check if JavaScript matches any safe pattern
            js_trimmed = js.strip()
            is_safe = any(re.match(pattern, js_trimmed) for pattern in safe_patterns)

            if not is_safe:
                logger.warning("Potentially dangerous JavaScript detected, removing")
                return ""

            # Additional checks for dangerous functions
            dangerous_functions = [
                'eval', 'Function', 'setTimeout', 'setInterval',
                'document.write', 'innerHTML', 'outerHTML',
                'XMLHttpRequest', 'fetch', 'import'
            ]

            for func in dangerous_functions:
                if func in js:
                    logger.warning(f"Dangerous function '{func}' detected in JavaScript")
                    return ""

            return js

        except Exception as e:
            logger.error(f"JavaScript sanitization failed: {e}")
            return ""

    def sanitize_url(self, url: str) -> str:
        """
        Sanitize URLs to prevent JavaScript and data URIs.

        Args:
            url: Raw URL

        Returns:
            Sanitized URL or '#' if dangerous
        """
        if not url:
            return "#"

        try:
            # Parse URL
            parsed = urlparse(url.strip())

            # Check for dangerous schemes
            dangerous_schemes = [
                'javascript', 'data', 'vbscript', 'file', 'about'
            ]

            if parsed.scheme in dangerous_schemes:
                logger.warning(f"Dangerous URL scheme detected: {parsed.scheme}")
                return "#"

            # Allow only http, https, mailto, tel
            allowed_schemes = ['http', 'https', 'mailto', 'tel', '']
            if parsed.scheme not in allowed_schemes:
                return "#"

            return url

        except Exception as e:
            logger.error(f"URL sanitization failed: {e}")
            return "#"

    def _contains_dangerous_patterns(self, content: str) -> bool:
        """Check if content contains dangerous patterns."""
        content_lower = content.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        return False

    def _sanitize_template_variables(self, content: str) -> str:
        """
        Sanitize template variables to prevent template injection.

        Args:
            content: Content with potential template variables

        Returns:
            Content with sanitized variables
        """
        # Remove any Jinja2 template syntax that shouldn't be in user content
        dangerous_template_patterns = [
            r'{%.*?%}',  # Block tags
            r'{{.*?}}',  # Variable tags unless specifically allowed
            r'{#.*?#}'   # Comments
        ]

        for pattern in dangerous_template_patterns:
            content = re.sub(pattern, '', content)

        return content


class SecureTemplateEngine:
    """
    Secure template engine using sandboxed Jinja2 environment.
    Prevents template injection and code execution.
    """

    def __init__(self):
        """Initialize secure template engine with sandboxed environment."""
        self.sanitizer = TemplateSanitizer()

        # Create sandboxed Jinja2 environment
        self.env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=True,  # Auto-escape HTML
            trim_blocks=True,
            lstrip_blocks=True,
            # Block dangerous functions
            undefined=None,
            finalize=None,
            # Set max string length to prevent DoS
            max_string_length=100000
        )

        # Add safe filters
        self.env.filters['sanitize'] = self.sanitizer.sanitize_html
        self.env.filters['escape'] = escape
        self.env.filters['safe_url'] = self.sanitizer.sanitize_url

        # Block access to dangerous attributes
        self._setup_sandbox_restrictions()

    def _setup_sandbox_restrictions(self):
        """Configure sandbox restrictions."""
        # Block access to private attributes
        self.env.sandboxed = True

        # Restrict callable attributes
        unsafe_attrs = {
            'gi_frame', 'gi_code', 'gi_running', '__class__',
            '__delattr__', '__dict__', '__getattribute__',
            '__init__', '__module__', '__repr__', '__setattr__',
            '__weakref__', '__subclasshook__', '__format__',
            '__sizeof__', '__reduce__', '__reduce_ex__'
        }

        for attr in unsafe_attrs:
            if hasattr(self.env, 'unsafe_attrs'):
                self.env.unsafe_attrs.add(attr)

    def render_template_safe(
        self,
        template_string: str,
        context: Dict[str, Any],
        sanitize_output: bool = True
    ) -> str:
        """
        Safely render a template with context.

        Args:
            template_string: Template string
            context: Template context variables
            sanitize_output: Sanitize final output

        Returns:
            Rendered and sanitized template
        """
        try:
            # Sanitize template string first
            template_string = self._preprocess_template(template_string)

            # Sanitize context values
            safe_context = self._sanitize_context(context)

            # Render template in sandbox
            template = self.env.from_string(template_string)
            rendered = template.render(**safe_context)

            # Sanitize output if requested
            if sanitize_output:
                rendered = self.sanitizer.sanitize_html(rendered)

            return rendered

        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Invalid template: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected template error: {e}")
            raise ValueError("Template rendering failed")

    def _preprocess_template(self, template_string: str) -> str:
        """
        Preprocess template to remove dangerous constructs.

        Args:
            template_string: Raw template string

        Returns:
            Preprocessed template string
        """
        # Remove dangerous Jinja2 constructs
        dangerous_constructs = [
            r'{%\s*import\s+.*?%}',
            r'{%\s*include\s+.*?%}',
            r'{%\s*extends\s+.*?%}',
            r'{%\s*block\s+.*?%}',
            r'{%\s*macro\s+.*?%}',
            r'{%\s*call\s+.*?%}',
            r'{%\s*filter\s+.*?%}',
            r'{%\s*set\s+.*?=.*?%}'
        ]

        for pattern in dangerous_constructs:
            template_string = re.sub(pattern, '', template_string, flags=re.IGNORECASE)

        return template_string

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize template context values.

        Args:
            context: Template context

        Returns:
            Sanitized context
        """
        safe_context = {}

        for key, value in context.items():
            # Sanitize key
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                logger.warning(f"Skipping invalid context key: {key}")
                continue

            # Sanitize value based on type
            if isinstance(value, str):
                # Escape HTML in string values by default
                safe_context[key] = escape(value)
            elif isinstance(value, (int, float, bool)):
                safe_context[key] = value
            elif isinstance(value, (list, tuple)):
                # Recursively sanitize list items
                safe_context[key] = [
                    escape(item) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursively sanitize dict values
                safe_context[key] = self._sanitize_context(value)
            else:
                # Skip complex objects
                logger.warning(f"Skipping complex object in context: {key}")

        return safe_context


class ContentSecurityPolicy:
    """
    Generate and manage Content Security Policy headers.
    """

    @staticmethod
    def generate_csp_header(
        nonce: Optional[str] = None,
        strict: bool = True
    ) -> Dict[str, str]:
        """
        Generate CSP header for template responses.

        Args:
            nonce: Optional nonce for inline scripts
            strict: Use strict policy

        Returns:
            Dictionary of CSP headers
        """
        if strict:
            # Strict CSP policy
            directives = [
                "default-src 'self'",
                "script-src 'self'" + (f" 'nonce-{nonce}'" if nonce else ""),
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles for templates
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
        else:
            # Relaxed CSP for demo sites
            directives = [
                "default-src 'self' https:",
                "script-src 'self' 'unsafe-inline' https:",
                "style-src 'self' 'unsafe-inline' https:",
                "img-src * data:",
                "font-src 'self' https:",
                "connect-src 'self' https:"
            ]

        csp = "; ".join(directives)

        return {
            "Content-Security-Policy": csp,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

    @staticmethod
    def generate_nonce() -> str:
        """Generate a secure nonce for CSP."""
        return secrets.token_urlsafe(16)


class TemplateSecurityValidator:
    """
    Validate templates and user input for security issues.
    """

    def __init__(self):
        """Initialize the validator."""
        self.sanitizer = TemplateSanitizer()

    def validate_template(
        self,
        template_string: str,
        template_type: str = "html"
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a template for security issues.

        Args:
            template_string: Template to validate
            template_type: Type of template (html, css, js)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if template_type == "html":
                return self._validate_html_template(template_string)
            elif template_type == "css":
                return self._validate_css_template(template_string)
            elif template_type == "js":
                return self._validate_js_template(template_string)
            else:
                return False, f"Unknown template type: {template_type}"

        except Exception as e:
            logger.error(f"Template validation failed: {e}")
            return False, str(e)

    def _validate_html_template(self, html: str) -> tuple[bool, Optional[str]]:
        """Validate HTML template."""
        # Check for dangerous patterns
        if self.sanitizer._contains_dangerous_patterns(html):
            return False, "Template contains dangerous patterns (XSS attempt)"

        # Check for template injection attempts
        injection_patterns = [
            r'{{.*(__class__|__globals__|__import__|exec|eval).*}}',
            r'{%.*(__class__|__globals__|__import__|exec|eval).*%}'
        ]

        for pattern in injection_patterns:
            if re.search(pattern, html, re.IGNORECASE):
                return False, "Template injection attempt detected"

        return True, None

    def _validate_css_template(self, css: str) -> tuple[bool, Optional[str]]:
        """Validate CSS template."""
        dangerous_css = [
            'expression', 'javascript:', 'behavior:', '@import'
        ]

        css_lower = css.lower()
        for danger in dangerous_css:
            if danger in css_lower:
                return False, f"CSS contains dangerous property: {danger}"

        return True, None

    def _validate_js_template(self, js: str) -> tuple[bool, Optional[str]]:
        """Validate JavaScript template."""
        # Very restrictive for user-provided JavaScript
        dangerous_js = [
            'eval', 'Function', 'setTimeout', 'setInterval',
            'document.cookie', 'localStorage', 'sessionStorage'
        ]

        for danger in dangerous_js:
            if danger in js:
                return False, f"JavaScript contains dangerous function: {danger}"

        return True, None


# Export main classes
__all__ = [
    'TemplateSanitizer',
    'SecureTemplateEngine',
    'ContentSecurityPolicy',
    'TemplateSecurityValidator'
]