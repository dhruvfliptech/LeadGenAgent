"""
Template Engine for Demo Sites

This service handles template rendering, customization, and preview generation.
Supports Jinja2-style templates with variable substitution.
Enhanced with comprehensive security measures.
"""

import os
import re
from typing import Dict, Any, Optional, List
from jinja2 import Template, Environment, BaseLoader, TemplateError
from jinja2.sandbox import SandboxedEnvironment
import logging

# Import security module
from app.core.template_security import (
    TemplateSanitizer,
    SecureTemplateEngine,
    ContentSecurityPolicy,
    TemplateSecurityValidator
)

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Template rendering and customization engine with enhanced security.

    Handles template processing, variable substitution,
    and style customization with XSS and injection prevention.
    """

    def __init__(self):
        """Initialize the template engine with security features."""
        # Use sandboxed environment for security
        self.jinja_env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=True,  # Security: escape HTML by default
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Initialize security components
        self.sanitizer = TemplateSanitizer()
        self.secure_engine = SecureTemplateEngine()
        self.validator = TemplateSecurityValidator()
        self.csp = ContentSecurityPolicy()

    def render_template(
        self,
        html_template: str,
        css_template: str,
        js_template: Optional[str],
        variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Render a template with the provided variables (with security).

        Args:
            html_template: HTML template string with {{variables}}
            css_template: CSS template string
            js_template: Optional JS template string
            variables: Dictionary of variables to substitute

        Returns:
            Dict with 'html', 'css', 'js' keys
        """
        try:
            # Validate templates first
            html_valid, html_error = self.validator.validate_template(html_template, "html")
            if not html_valid:
                logger.error(f"HTML template validation failed: {html_error}")
                raise ValueError(f"Invalid HTML template: {html_error}")

            css_valid, css_error = self.validator.validate_template(css_template, "css")
            if not css_valid:
                logger.error(f"CSS template validation failed: {css_error}")
                raise ValueError(f"Invalid CSS template: {css_error}")

            # Use secure template engine for rendering
            html = self.secure_engine.render_template_safe(html_template, variables, sanitize_output=True)
            css = self.secure_engine.render_template_safe(css_template, variables, sanitize_output=False)

            # Sanitize CSS separately
            css = self.sanitizer.sanitize_css(css)

            # Handle JavaScript with strict sanitization
            js = ""
            if js_template:
                js_valid, js_error = self.validator.validate_template(js_template, "js")
                if js_valid:
                    js = self.secure_engine.render_template_safe(js_template, variables, sanitize_output=False)
                    js = self.sanitizer.sanitize_javascript(js)
                else:
                    logger.warning(f"JavaScript template rejected: {js_error}")

            return {
                'html': html,
                'css': css,
                'js': js
            }

        except Exception as e:
            logger.error(f"Template rendering failed: {str(e)}")
            raise

    def _render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render a single template string with security."""
        try:
            # Use secure engine instead of direct rendering
            return self.secure_engine.render_template_safe(template_string, variables)
        except TemplateError as e:
            logger.error(f"Template error: {str(e)}")
            raise

    def apply_style_settings(
        self,
        css: str,
        style_settings: Dict[str, Any]
    ) -> str:
        """
        Apply style settings to CSS.

        Replaces CSS variables and color values.
        """
        try:
            # Replace CSS variables
            if 'primary_color' in style_settings:
                css = css.replace('var(--primary-color)', style_settings['primary_color'])
                css = css.replace('--primary-color:', f"--primary-color: {style_settings['primary_color']};")

            if 'secondary_color' in style_settings:
                css = css.replace('var(--secondary-color)', style_settings['secondary_color'])

            if 'accent_color' in style_settings:
                css = css.replace('var(--accent-color)', style_settings['accent_color'])

            if 'font_family' in style_settings:
                css = css.replace('var(--font-family)', style_settings['font_family'])

            # Add custom CSS if provided
            if 'custom_css' in style_settings and style_settings['custom_css']:
                css += f"\n\n/* Custom CSS */\n{style_settings['custom_css']}"

            return css

        except Exception as e:
            logger.error(f"Style application failed: {str(e)}")
            return css

    def generate_preview(
        self,
        html: str,
        css: str,
        js: Optional[str] = None
    ) -> str:
        """
        Generate a complete HTML preview page with security headers.

        Combines HTML, CSS, and JS into a single file with CSP.
        """
        try:
            # Sanitize inputs
            html = self.sanitizer.sanitize_html(html)
            css = self.sanitizer.sanitize_css(css)

            # Generate CSP nonce for inline scripts
            nonce = self.csp.generate_nonce() if js else None

            # Build complete HTML document with security meta tags
            preview = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'{f" 'nonce-{nonce}'" if nonce else ''}">
    <title>Preview</title>
    <style>
        {css}
    </style>
</head>
<body>
    {html}
    {f'<script nonce="{nonce}">{js}</script>' if js and nonce else ''}
</body>
</html>"""

            return preview

        except Exception as e:
            logger.error(f"Preview generation failed: {str(e)}")
            raise

    def extract_variables(self, template_string: str) -> List[str]:
        """
        Extract all variable names from a template.

        Finds all {{variable}} patterns.
        """
        try:
            # Find all {{variable}} patterns
            pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}'
            matches = re.findall(pattern, template_string)

            # Remove duplicates and sort
            variables = sorted(set(matches))

            return variables

        except Exception as e:
            logger.error(f"Variable extraction failed: {str(e)}")
            return []

    def validate_template(self, template_string: str) -> tuple[bool, Optional[str]]:
        """
        Validate a template for syntax errors and security issues.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # First check for security issues
            is_valid, security_error = self.validator.validate_template(template_string, "html")
            if not is_valid:
                return False, f"Security validation failed: {security_error}"

            # Try to parse the template in sandbox
            template = self.jinja_env.from_string(template_string)

            # Try to render with empty variables
            template.render()

            return True, None

        except TemplateError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def merge_templates(
        self,
        base_template: str,
        components: List[str]
    ) -> str:
        """
        Merge multiple template components into one.

        Useful for building templates from reusable components.
        """
        try:
            # Simple concatenation for now
            # Could be enhanced with more sophisticated merging
            merged = base_template

            for component in components:
                merged += "\n\n" + component

            return merged

        except Exception as e:
            logger.error(f"Template merging failed: {str(e)}")
            raise

    def customize_colors(
        self,
        html: str,
        css: str,
        color_scheme: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Customize the color scheme of a rendered template.

        Args:
            html: Rendered HTML
            css: Rendered CSS
            color_scheme: Dict with color values

        Returns:
            Dict with updated HTML and CSS
        """
        try:
            # Update CSS with new colors
            updated_css = css

            for color_name, color_value in color_scheme.items():
                # Replace in CSS custom properties
                pattern = f"--{color_name}:\\s*#[0-9A-Fa-f]{{6}}"
                replacement = f"--{color_name}: {color_value}"
                updated_css = re.sub(pattern, replacement, updated_css)

                # Replace direct color references
                # This is a simple approach - could be more sophisticated
                if 'primary' in color_name:
                    updated_css = updated_css.replace(
                        'var(--primary-color)',
                        color_value
                    )

            return {
                'html': html,
                'css': updated_css
            }

        except Exception as e:
            logger.error(f"Color customization failed: {str(e)}")
            return {'html': html, 'css': css}

    def inject_analytics(
        self,
        html: str,
        demo_site_id: int,
        analytics_endpoint: str
    ) -> str:
        """
        Inject analytics tracking code into HTML.

        Adds lightweight tracking pixel and click tracking.
        """
        try:
            # Analytics tracking script
            tracking_script = f"""
    <script>
        // Demo Site Analytics Tracker
        (function() {{
            const DEMO_SITE_ID = {demo_site_id};
            const ANALYTICS_ENDPOINT = '{analytics_endpoint}';
            const VISITOR_ID = localStorage.getItem('demo_visitor_id') ||
                               'visitor_' + Math.random().toString(36).substr(2, 9);

            localStorage.setItem('demo_visitor_id', VISITOR_ID);

            // Track page view
            const startTime = Date.now();

            fetch(ANALYTICS_ENDPOINT + '/track', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    demo_site_id: DEMO_SITE_ID,
                    event_type: 'page_view',
                    visitor_id: VISITOR_ID,
                    event_data: {{
                        url: window.location.href,
                        referrer: document.referrer,
                        screen: window.screen.width + 'x' + window.screen.height,
                        timestamp: new Date().toISOString()
                    }}
                }})
            }}).catch(err => console.debug('Analytics:', err));

            // Track time on page
            window.addEventListener('beforeunload', function() {{
                const timeOnPage = Math.round((Date.now() - startTime) / 1000);
                navigator.sendBeacon(ANALYTICS_ENDPOINT + '/track', JSON.stringify({{
                    demo_site_id: DEMO_SITE_ID,
                    event_type: 'time_on_page',
                    visitor_id: VISITOR_ID,
                    event_data: {{time_seconds: timeOnPage}}
                }}));
            }});

            // Track CTA clicks
            document.addEventListener('click', function(e) {{
                const target = e.target.closest('a, button, [data-cta]');
                if (target) {{
                    fetch(ANALYTICS_ENDPOINT + '/track', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            demo_site_id: DEMO_SITE_ID,
                            event_type: 'cta_click',
                            visitor_id: VISITOR_ID,
                            event_data: {{
                                element: target.tagName,
                                text: target.textContent.substring(0, 50),
                                href: target.href || ''
                            }}
                        }})
                    }}).catch(err => console.debug('Analytics:', err));
                }}
            }});
        }})();
    </script>
"""

            # Inject before closing </body> tag
            if '</body>' in html:
                html = html.replace('</body>', tracking_script + '\n</body>')
            else:
                html += tracking_script

            return html

        except Exception as e:
            logger.error(f"Analytics injection failed: {str(e)}")
            return html

    def optimize_for_mobile(self, html: str, css: str) -> Dict[str, str]:
        """
        Add mobile optimization to the template.

        Ensures responsive design and mobile-friendly elements.
        """
        try:
            # Add viewport meta tag if missing
            if 'viewport' not in html:
                viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                if '<head>' in html:
                    html = html.replace('<head>', f'<head>\n    {viewport_meta}')

            # Add mobile-friendly CSS if not present
            mobile_css = """
/* Mobile Optimization */
@media (max-width: 768px) {
    body {
        font-size: 14px;
        padding: 0 15px;
    }

    h1 {
        font-size: 1.8em;
    }

    h2 {
        font-size: 1.5em;
    }

    .container {
        width: 100% !important;
        padding: 0 15px !important;
    }

    .grid, .features, .columns {
        grid-template-columns: 1fr !important;
        flex-direction: column !important;
    }

    button, .btn, .cta {
        width: 100%;
        padding: 15px;
    }
}
"""
            if '@media (max-width: 768px)' not in css:
                css += "\n" + mobile_css

            return {
                'html': html,
                'css': css
            }

        except Exception as e:
            logger.error(f"Mobile optimization failed: {str(e)}")
            return {'html': html, 'css': css}
