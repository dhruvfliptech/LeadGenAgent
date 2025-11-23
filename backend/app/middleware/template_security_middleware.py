"""
Template Security Middleware

Applies Content Security Policy and other security headers
to template-related endpoints.
"""

import logging
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.template_security import ContentSecurityPolicy

logger = logging.getLogger(__name__)


class TemplateSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to template responses.
    """

    def __init__(self, app, strict_csp: bool = True):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application
            strict_csp: Use strict CSP policy
        """
        super().__init__(app)
        self.csp = ContentSecurityPolicy()
        self.strict_csp = strict_csp

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to response.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response with security headers
        """
        # Process the request
        response = await call_next(request)

        # Check if this is a template-related endpoint
        path = request.url.path
        is_template_endpoint = any([
            "/templates" in path,
            "/demo-sites" in path,
            "/preview" in path,
            "/export" in path,
            "/responses" in path
        ])

        # Add security headers for template endpoints
        if is_template_endpoint:
            # Generate nonce for inline scripts if needed
            nonce = None
            if isinstance(response, HTMLResponse):
                nonce = self.csp.generate_nonce()

            # Get CSP headers
            headers = self.csp.generate_csp_header(
                nonce=nonce,
                strict=self.strict_csp
            )

            # Apply headers to response
            for header_name, header_value in headers.items():
                response.headers[header_name] = header_value

            # Note: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection,
            # Referrer-Policy, and Permissions-Policy are already set by
            # SecurityHeadersMiddleware to avoid duplicate/conflicting headers

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to sanitize input data for template endpoints.
    """

    def __init__(self, app):
        """Initialize the middleware."""
        super().__init__(app)
        from app.core.template_security import TemplateSanitizer
        self.sanitizer = TemplateSanitizer()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and sanitize input data.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response after processing
        """
        # Check if this is a template-related POST/PUT request
        path = request.url.path
        method = request.method

        is_template_mutation = (
            method in ["POST", "PUT", "PATCH"] and
            any([
                "/templates" in path,
                "/demo-sites" in path,
                "/responses" in path
            ])
        )

        if is_template_mutation:
            # Log that we're sanitizing input
            logger.debug(f"Sanitizing input for {method} {path}")

            # Note: Actual sanitization happens in the endpoint handlers
            # This middleware just adds logging and monitoring

        # Process the request
        response = await call_next(request)

        return response


def setup_template_security(app, strict_csp: bool = True):
    """
    Setup template security middleware for the application.

    Args:
        app: FastAPI application instance
        strict_csp: Use strict CSP policy (default: True)
    """
    # Add security middleware
    app.add_middleware(
        TemplateSecurityMiddleware,
        strict_csp=strict_csp
    )

    # Add input sanitization middleware
    app.add_middleware(InputSanitizationMiddleware)

    logger.info("Template security middleware configured")