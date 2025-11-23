"""
Security middleware for FastAPI application.
Implements OWASP security headers and protection mechanisms.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import hashlib
import secrets
import logging
import json
import re
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add comprehensive security headers to all responses.
    Based on OWASP Secure Headers Project recommendations.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate nonce for CSP
        csp_nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = csp_nonce

        # Process the request
        response = await call_next(request)

        # Add security headers
        headers = self._get_security_headers(request, csp_nonce)
        for header, value in headers.items():
            response.headers[header] = value

        return response

    def _get_security_headers(self, request: Request, nonce: str) -> dict:
        """
        Get security headers based on environment and request context.
        """
        headers = {}

        # X-Frame-Options - Prevent clickjacking
        headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options - Prevent MIME sniffing
        headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Enable browser XSS protection (legacy but still useful)
        headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy - Control referrer information
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy - Control browser features
        headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Content-Security-Policy - Prevent XSS and other injection attacks
        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # Allow Google Fonts CSS
            "img-src 'self' data: https:",
            "font-src 'self' https://fonts.gstatic.com",  # Allow Google Fonts files
            "connect-src 'self' ws: wss: https:",  # Allow WebSocket and HTTPS connections for API calls
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]

        headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Strict-Transport-Security - Force HTTPS (only in production)
        if settings.ENVIRONMENT == "production":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # X-Permitted-Cross-Domain-Policies - Control Adobe products
        headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # Clear-Site-Data - Clear browser data on logout (if applicable)
        if request.url.path == "/api/v1/auth/logout":
            headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'

        return headers


class SensitiveDataProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect sensitive data in requests and responses.
    - Masks sensitive fields in logs
    - Prevents sensitive data leakage in errors
    - Sanitizes output
    """

    SENSITIVE_FIELDS = {
        "password", "token", "secret", "api_key", "apikey",
        "authorization", "cookie", "session", "credit_card",
        "ssn", "tax_id", "passport", "license", "account_number"
    }

    SENSITIVE_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),  # Phone
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]'),  # Credit card
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),  # SSN
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Store original body for later use
        request.state.original_body = await self._get_body_safely(request)

        try:
            response = await call_next(request)

            # Sanitize response if it's JSON
            if response.headers.get("content-type", "").startswith("application/json"):
                response = await self._sanitize_json_response(response)

            return response

        except Exception as e:
            # Sanitize error messages to prevent information leakage
            return self._create_safe_error_response(e)

    async def _get_body_safely(self, request: Request) -> bytes:
        """Safely get request body without consuming it."""
        try:
            body = await request.body()
            # Create a new receive function that returns the cached body
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive
            return body
        except:
            return b""

    async def _sanitize_json_response(self, response: Response) -> Response:
        """Sanitize JSON response to mask sensitive data."""
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Parse JSON
            data = json.loads(body)

            # Sanitize the data
            sanitized = self._mask_sensitive_data(data)

            # Create new response with sanitized data
            return JSONResponse(
                content=sanitized,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except:
            # If sanitization fails, return original response
            return response

    def _mask_sensitive_data(self, data):
        """Recursively mask sensitive data in a dictionary or list."""
        if isinstance(data, dict):
            return {
                key: "[REDACTED]" if self._is_sensitive_field(key) else self._mask_sensitive_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Apply pattern-based masking
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
            return data
        else:
            return data

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field name is sensitive."""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELDS)

    def _create_safe_error_response(self, error: Exception) -> JSONResponse:
        """Create a safe error response without leaking sensitive information."""
        # Log the full error internally
        logger.error(f"Internal error: {type(error).__name__}: {str(error)}")

        # Return generic error to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.utcnow().isoformat(),
                "reference": hashlib.sha256(str(error).encode()).hexdigest()[:8]
            }
        )


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for additional request validation.
    - Check for common attack patterns
    - Validate content types
    - Enforce size limits
    """

    MAX_BODY_SIZE = 10 * 1024 * 1024  # 10MB
    BLOCKED_PATHS = [
        ".env", ".git", ".svn", "wp-admin", "phpmyadmin",
        ".php", ".asp", ".jsp", "../", "..\\", "%2e%2e"
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for blocked paths
        path_lower = request.url.path.lower()
        for blocked in self.BLOCKED_PATHS:
            if blocked in path_lower:
                logger.warning(f"Blocked request to suspicious path: {request.url.path}")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Forbidden", "message": "Access denied"}
                )

        # Check content type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            # Ensure content-type is specified
            if not content_type:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Bad Request", "message": "Content-Type header is required"}
                )

            # Check for content-type attacks
            if len(content_type) > 255:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Bad Request", "message": "Invalid Content-Type header"}
                )

        # Check body size
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.MAX_BODY_SIZE:
                        return JSONResponse(
                            status_code=413,
                            content={"error": "Payload Too Large", "message": f"Request body exceeds {self.MAX_BODY_SIZE} bytes"}
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Bad Request", "message": "Invalid Content-Length header"}
                    )

        # Check for SQL injection attempts in URL parameters
        if request.url.query:
            if self._contains_sql_injection(request.url.query):
                logger.warning(f"Potential SQL injection in query: {request.url.query}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Bad Request", "message": "Invalid query parameters"}
                )

        return await call_next(request)

    def _contains_sql_injection(self, text: str) -> bool:
        """Check for common SQL injection patterns."""
        patterns = [
            r"(\bunion\b.*\bselect\b|\bselect\b.*\bunion\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bdrop\b|\bdelete\b|\btruncate\b|\balter\b)\s+(table|database)",
            r"(xp_|sp_|0x)",
            r"(\bexec\b|\bexecute\b)\s*\(",
            r"<script|javascript:|onerror=|onclick="
        ]

        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security audit logging.
    Logs all security-relevant events.
    """

    SECURITY_EVENTS = {
        "/api/v1/auth/login": "LOGIN_ATTEMPT",
        "/api/v1/auth/logout": "LOGOUT",
        "/api/v1/auth/register": "REGISTRATION",
        "/api/v1/auth/password-reset": "PASSWORD_RESET",
        "/api/v1/users": "USER_MANAGEMENT",
        "/api/v1/ml/retrain": "MODEL_RETRAIN",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Capture request details
        start_time = datetime.utcnow()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")

        # Get user info if authenticated
        user_id = getattr(request.state, "user_id", None)

        # Process request
        response = await call_next(request)

        # Log security events
        if any(request.url.path.startswith(path) for path in self.SECURITY_EVENTS):
            duration = (datetime.utcnow() - start_time).total_seconds()

            event_type = self.SECURITY_EVENTS.get(
                request.url.path,
                "SECURITY_EVENT"
            )

            log_entry = {
                "timestamp": start_time.isoformat(),
                "event_type": event_type,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id,
                "success": 200 <= response.status_code < 400
            }

            # Log based on response status
            if response.status_code >= 500:
                logger.error(f"Security event error: {json.dumps(log_entry)}")
            elif response.status_code >= 400:
                logger.warning(f"Security event failure: {json.dumps(log_entry)}")
            else:
                logger.info(f"Security event: {json.dumps(log_entry)}")

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxy headers."""
        # Check proxy headers
        for header in ["X-Real-IP", "X-Forwarded-For"]:
            ip = request.headers.get(header)
            if ip:
                # For X-Forwarded-For, get the first IP
                return ip.split(",")[0].strip()

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "unknown"


__all__ = [
    'SecurityHeadersMiddleware',
    'SensitiveDataProtectionMiddleware',
    'RequestValidationMiddleware',
    'AuditLoggingMiddleware'
]