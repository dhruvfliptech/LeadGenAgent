"""
Request logging middleware with context tracking and audit trail.

Provides comprehensive request/response logging with timing,
user tracking, and request ID correlation.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger, set_request_context, clear_request_context

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests and responses.

    Features:
    - Generate unique request IDs for tracing
    - Log request details (method, path, headers, client)
    - Log response details (status code, size, timing)
    - Extract user information from headers/JWT
    - Performance timing
    - Audit trail for sensitive operations
    """

    def __init__(self, app: ASGIApp, enable_audit: bool = True):
        super().__init__(app)
        self.enable_audit = enable_audit

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:12]  # Short but unique enough
        start_time = time.time()

        # Extract user information (if available)
        user_id = None
        user_email = None

        # Try to extract from JWT token or custom header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # In production, decode JWT and extract user info
            # For now, just log that auth is present
            pass

        # Custom user header (if using API keys or similar)
        user_email = request.headers.get("x-user-email")
        user_id = request.headers.get("x-user-id")

        # Set request context for logging
        set_request_context(request_id, user_id, user_email)

        # Log request
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(
            f"Request started: {request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params) if request.query_params else None,
            client_host=client_host,
            user_agent=user_agent,
            user_email=user_email
        )

        # Check if this is a sensitive operation that should be audited
        is_write_operation = request.method in ["POST", "PUT", "PATCH", "DELETE"]
        is_sensitive_path = any(
            sensitive in request.url.path.lower()
            for sensitive in ["approval", "template", "user", "admin", "delete"]
        )

        if self.enable_audit and is_write_operation and is_sensitive_path:
            logger.audit(
                "sensitive_operation_started",
                "http_request",
                request_id,
                method=request.method,
                path=request.url.path,
                client_host=client_host
            )

        # Store request ID in request state for access in endpoints
        request.state.request_id = request_id

        # Process request
        try:
            response = await call_next(request)

            # Calculate timing
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                request_id=request_id,
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
                response_size_bytes=int(response.headers.get("content-length", 0))
            )

            # Log slow requests
            if duration > 2.0:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    request_id=request_id,
                    duration_seconds=round(duration, 3),
                    path=request.url.path
                )

            # Add request ID to response headers for client-side tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {type(e).__name__}",
                exc_info=e,
                request_id=request_id,
                duration_seconds=round(duration, 3),
                error_type=type(e).__name__
            )
            raise

        finally:
            # Clear request context
            clear_request_context()


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging performance metrics.

    Tracks request timing and logs slow endpoints.
    """

    def __init__(self, app: ASGIApp, slow_threshold_seconds: float = 1.0):
        super().__init__(app)
        self.slow_threshold = slow_threshold_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request timing."""
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Log performance metrics
        logger.performance(
            f"{request.method} {request.url.path}",
            duration,
            success=response.status_code < 400,
            status_code=response.status_code,
            method=request.method,
            path=request.url.path
        )

        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging security-related events.

    Tracks authentication attempts, authorization failures,
    and suspicious activity.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log security-related events."""
        # Check for authentication header
        has_auth = "authorization" in request.headers

        # Check for suspicious patterns
        suspicious_patterns = ["../", "script>", "union select", "drop table"]
        query_string = str(request.url.query).lower()
        path = request.url.path.lower()

        is_suspicious = any(
            pattern in query_string or pattern in path
            for pattern in suspicious_patterns
        )

        if is_suspicious:
            logger.warning(
                f"Suspicious request detected: {request.method} {request.url.path}",
                path=request.url.path,
                query_params=dict(request.query_params),
                client_host=request.client.host if request.client else "unknown",
                suspicious=True
            )

        response = await call_next(request)

        # Log authentication failures
        if response.status_code == 401:
            logger.warning(
                f"Authentication failed: {request.method} {request.url.path}",
                path=request.url.path,
                status_code=401,
                had_auth_header=has_auth,
                client_host=request.client.host if request.client else "unknown"
            )

        # Log authorization failures
        elif response.status_code == 403:
            logger.warning(
                f"Authorization denied: {request.method} {request.url.path}",
                path=request.url.path,
                status_code=403,
                client_host=request.client.host if request.client else "unknown"
            )

        return response
