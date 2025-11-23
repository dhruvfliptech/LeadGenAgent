"""
Email Template Service
Handles template rendering, tracking pixel injection, and link wrapping
Enhanced with comprehensive security measures
"""
import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from bs4 import BeautifulSoup
from jinja2 import Template, Environment, BaseLoader, TemplateError, SandboxedEnvironment

from app.core.email_config import email_config
from app.core.template_security import (
    TemplateSanitizer,
    SecureTemplateEngine,
    TemplateSecurityValidator
)

logger = logging.getLogger(__name__)


class EmailTemplateService:
    """
    Service for rendering email templates with variable substitution,
    tracking injection, and security features
    """

    def __init__(self):
        """Initialize template service with security"""
        self.config = email_config
        # Use sandboxed environment for security
        self.jinja_env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=True  # Auto-escape HTML
        )
        # Initialize security components
        self.sanitizer = TemplateSanitizer()
        self.secure_engine = SecureTemplateEngine()
        self.validator = TemplateSecurityValidator()

    def render_template(
        self,
        template_html: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Render HTML template with variable substitution and security

        Args:
            template_html: HTML template with {{ variable }} syntax
            variables: Dictionary of variables to substitute

        Returns:
            Rendered and sanitized HTML string

        Example:
            template = "<h1>Hello {{ name }}</h1>"
            variables = {"name": "John"}
            result = render_template(template, variables)
            # Returns: "<h1>Hello John</h1>"
        """
        try:
            # Validate template for security issues
            is_valid, error = self.validator.validate_template(template_html, "html")
            if not is_valid:
                logger.error(f"Template validation failed: {error}")
                raise ValueError(f"Template security validation failed: {error}")

            # Use secure template engine for rendering
            rendered = self.secure_engine.render_template_safe(
                template_html,
                variables,
                sanitize_output=True  # Always sanitize email templates
            )

            return rendered
        except TemplateError as e:
            logger.error(f"Template rendering error: {str(e)}")
            raise ValueError(f"Failed to render template: {str(e)}")

    def add_tracking_pixel(
        self,
        html_body: str,
        tracking_token: str
    ) -> str:
        """
        Inject 1x1 transparent tracking pixel into HTML email

        Args:
            html_body: HTML email body
            tracking_token: Unique tracking token

        Returns:
            HTML with tracking pixel injected before </body> tag
        """
        tracking_url = f"{self.config.TRACKING_DOMAIN}/api/v1/tracking/open/{tracking_token}"
        tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;" />'

        # Try to inject before </body> tag
        if '</body>' in html_body.lower():
            # Find the last occurrence of </body>
            parts = html_body.lower().rsplit('</body>', 1)
            insert_index = len(parts[0])
            return html_body[:insert_index] + tracking_pixel + html_body[insert_index:]
        else:
            # No body tag, append to end
            return html_body + tracking_pixel

    def wrap_links_for_tracking(
        self,
        html_body: str,
        tracking_token: str
    ) -> str:
        """
        Wrap all links in HTML for click tracking

        Args:
            html_body: HTML email body
            tracking_token: Unique tracking token

        Returns:
            HTML with all links wrapped for tracking

        Example:
            Original: <a href="https://example.com">Click</a>
            Wrapped: <a href="/api/v1/tracking/click/TOKEN?url=https%3A%2F%2Fexample.com">Click</a>
        """
        try:
            soup = BeautifulSoup(html_body, 'html.parser')

            # Find all <a> tags with href
            for link in soup.find_all('a', href=True):
                original_url = link['href']

                # Skip mailto:, tel:, and anchor links
                if original_url.startswith(('mailto:', 'tel:', '#')):
                    continue

                # Skip unsubscribe links (they have their own tracking)
                if 'unsubscribe' in original_url.lower():
                    continue

                # Create tracking URL
                encoded_url = quote(original_url, safe='')
                tracking_url = (
                    f"{self.config.TRACKING_DOMAIN}/api/v1/tracking/click/{tracking_token}"
                    f"?url={encoded_url}"
                )

                link['href'] = tracking_url

            return str(soup)

        except Exception as e:
            logger.error(f"Failed to wrap links for tracking: {str(e)}")
            # Return original HTML if parsing fails
            return html_body

    def generate_text_version(self, html_body: str) -> str:
        """
        Convert HTML email to plain text version

        Args:
            html_body: HTML email body

        Returns:
            Plain text version
        """
        try:
            soup = BeautifulSoup(html_body, 'html.parser')

            # Remove script and style tags
            for script in soup(['script', 'style']):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.error(f"Failed to generate text version: {str(e)}")
            # Return simple text extraction as fallback
            return re.sub('<[^<]+?>', '', html_body)

    def validate_variables(
        self,
        template_html: str,
        variables: Dict[str, Any],
        required_variables: Optional[List[str]] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate that all required variables are present

        Args:
            template_html: HTML template
            variables: Dictionary of variables
            required_variables: Optional list of required variable names

        Returns:
            (is_valid, missing_variables)
        """
        try:
            # Extract variables from template using Jinja2
            template = self.jinja_env.from_string(template_html)
            template_vars = set(
                var for var in template.module.__dict__.keys()
                if not var.startswith('_')
            )

            # If required_variables not specified, find all variables in template
            if required_variables is None:
                # Parse template for {{ variable }} patterns
                pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
                template_vars = set(re.findall(pattern, template_html))

            required = set(required_variables) if required_variables else template_vars
            provided = set(variables.keys())

            missing = required - provided

            return len(missing) == 0, list(missing)

        except Exception as e:
            logger.error(f"Variable validation error: {str(e)}")
            return False, []

    def add_unsubscribe_link(
        self,
        html_body: str,
        tracking_token: str,
        link_text: str = "Unsubscribe"
    ) -> str:
        """
        Add unsubscribe link to email footer

        Args:
            html_body: HTML email body
            tracking_token: Unique tracking token
            link_text: Text for unsubscribe link

        Returns:
            HTML with unsubscribe link added
        """
        unsubscribe_url = f"{self.config.TRACKING_DOMAIN}/api/v1/tracking/unsubscribe/{tracking_token}"

        unsubscribe_html = f'''
        <div style="text-align: center; padding: 20px; color: #666; font-size: 12px; border-top: 1px solid #ddd; margin-top: 20px;">
            <p>
                Don't want to receive these emails?
                <a href="{unsubscribe_url}" style="color: #666; text-decoration: underline;">
                    {link_text}
                </a>
            </p>
        </div>
        '''

        # Try to inject before </body> tag
        if '</body>' in html_body.lower():
            parts = html_body.lower().rsplit('</body>', 1)
            insert_index = len(parts[0])
            return html_body[:insert_index] + unsubscribe_html + html_body[insert_index:]
        else:
            # No body tag, append to end
            return html_body + unsubscribe_html

    def build_email_template(
        self,
        subject: str,
        heading: str,
        body_content: str,
        cta_text: Optional[str] = None,
        cta_url: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> str:
        """
        Build a complete HTML email from components

        Args:
            subject: Email subject (for reference)
            heading: Main heading
            body_content: HTML body content
            cta_text: Call-to-action button text
            cta_url: Call-to-action button URL
            footer_text: Footer text

        Returns:
            Complete HTML email
        """
        cta_html = ""
        if cta_text and cta_url:
            cta_html = f'''
            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                <tr>
                    <td align="center">
                        <a href="{cta_url}" style="
                            display: inline-block;
                            padding: 15px 30px;
                            background-color: #007bff;
                            color: #ffffff;
                            text-decoration: none;
                            border-radius: 5px;
                            font-weight: bold;
                        ">{cta_text}</a>
                    </td>
                </tr>
            </table>
            '''

        footer_html = ""
        if footer_text:
            footer_html = f'''
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                {footer_text}
            </div>
            '''

        html_template = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 40px 40px 20px 40px;">
                                    <h1 style="margin: 0; color: #333; font-size: 28px;">{heading}</h1>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="padding: 20px 40px;">
                                    {body_content}
                                </td>
                            </tr>

                            <!-- CTA Button -->
                            {cta_html}

                            <!-- Footer -->
                            <tr>
                                <td style="padding: 20px 40px 40px 40px;">
                                    {footer_html}
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        '''

        return html_template


# Helper function for quick template rendering
def render_email_template(
    template_html: str,
    variables: Dict[str, Any],
    tracking_token: Optional[str] = None,
    add_unsubscribe: bool = True
) -> tuple[str, str]:
    """
    Helper function to render template with all tracking

    Args:
        template_html: HTML template
        variables: Template variables
        tracking_token: Optional tracking token
        add_unsubscribe: Whether to add unsubscribe link

    Returns:
        (html_body, text_body)
    """
    service = EmailTemplateService()

    # Render template
    html_body = service.render_template(template_html, variables)

    # Add tracking if token provided
    if tracking_token:
        html_body = service.add_tracking_pixel(html_body, tracking_token)
        html_body = service.wrap_links_for_tracking(html_body, tracking_token)

        if add_unsubscribe:
            html_body = service.add_unsubscribe_link(html_body, tracking_token)

    # Generate text version
    text_body = service.generate_text_version(html_body)

    return html_body, text_body
