"""
Rate limiting middleware for API endpoints.
Implements OWASP recommendations for preventing abuse and DoS attacks.
"""

from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    print("Warning: slowapi not installed. Rate limiting disabled.")

import redis
from app.core.config import settings
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP address, considering proxy headers.
    Implements proper IP extraction per OWASP guidelines.
    """
    # Check for common proxy headers (in order of preference)
    headers_to_check = [
        'X-Real-IP',
        'X-Forwarded-For',
        'X-Client-IP',
        'CF-Connecting-IP',  # Cloudflare
        'True-Client-IP'      # Akamai
    ]

    for header in headers_to_check:
        ip = request.headers.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs
            if header == 'X-Forwarded-For':
                # Get the first IP (original client)
                ip = ip.split(',')[0].strip()

            # Validate it's a valid IP format (basic check)
            if _is_valid_ip(ip):
                return ip

    # Fallback to direct connection IP
    if request.client:
        return request.client.host

    return "unknown"


def _is_valid_ip(ip: str) -> bool:
    """Basic IP validation."""
    import re

    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # Simplified IPv6 pattern (not comprehensive)
    ipv6_pattern = r'^([0-9a-fA-F:]+)$'

    if re.match(ipv4_pattern, ip):
        # Check octets are in valid range
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)
    elif re.match(ipv6_pattern, ip):
        return True

    return False


def create_identifier_for_rate_limit(request: Request) -> str:
    """
    Create a unique identifier for rate limiting.
    Combines IP with optional user ID if authenticated.
    """
    ip = get_real_client_ip(request)

    # If user is authenticated, combine with user ID
    # This prevents users from bypassing limits by changing IPs
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        identifier = f"{ip}:{user_id}"
    else:
        identifier = ip

    # Hash the identifier for privacy
    return hashlib.sha256(identifier.encode()).hexdigest()[:16]


# Rate limiter configurations per endpoint type
RATE_LIMITS = {
    # Critical endpoints - prevent abuse
    "scraper": "5 per hour",  # Scraping is resource-intensive
    "ml_score": "100 per minute",  # ML inference
    "ml_batch_score": "10 per minute",  # Batch ML processing
    "response_generate": "30 per hour",  # AI response generation
    "ml_retrain": "1 per day",  # Model retraining

    # Data modification endpoints
    "lead_create": "60 per minute",  # Lead creation
    "lead_update": "120 per minute",  # Lead updates
    "lead_delete": "30 per minute",  # Lead deletion

    # Query endpoints - more lenient
    "lead_list": "300 per minute",  # Listing leads
    "lead_get": "600 per minute",  # Getting individual leads
    "stats": "60 per minute",  # Statistics

    # Authentication endpoints (when implemented)
    "login": "5 per minute",  # Login attempts
    "register": "3 per minute",  # Registration
    "password_reset": "3 per hour",  # Password reset

    # Template endpoints (/api/v1/templates/*)
    "templates_list": "100 per minute",  # List templates (read)
    "templates_get": "100 per minute",  # Get single template (read)
    "templates_create": "20 per minute",  # Create template (write)
    "templates_update": "20 per minute",  # Update template (write)
    "templates_delete": "20 per minute",  # Delete template (write)
    "templates_preview": "30 per minute",  # Preview template rendering
    "templates_analytics": "60 per minute",  # Template analytics (read)

    # Email tracking endpoints (/api/v1/tracking/*)
    "tracking_open": "1000 per minute",  # Email open tracking (public, high volume)
    "tracking_click": "1000 per minute",  # Email click tracking (public, high volume)
    "tracking_unsubscribe": "50 per hour",  # Unsubscribe (public, limited)

    # Demo sites endpoints (/api/v1/demo-sites/*)
    "demo_sites_list": "100 per minute",  # List demo sites (read)
    "demo_sites_get": "100 per minute",  # Get single demo site (read)
    "demo_sites_generate": "10 per hour",  # Generate new demo site (AI-intensive)
    "demo_sites_create": "20 per minute",  # Create demo site (write)
    "demo_sites_update": "20 per minute",  # Update demo site (write)
    "demo_sites_delete": "20 per minute",  # Delete demo site (write)
    "demo_sites_deploy": "10 per hour",  # Deploy to Vercel (resource-intensive)
    "demo_sites_preview": "60 per minute",  # Preview demo site (read)
    "demo_sites_analytics": "100 per minute",  # Analytics (read)
    "demo_sites_track": "2000 per minute",  # Public analytics tracking (high volume)
    "demo_templates_list": "100 per minute",  # List templates (read)
    "demo_templates_create": "10 per minute",  # Create template (write)
    "demo_components_list": "100 per minute",  # List components (read)
    "demo_components_create": "10 per minute",  # Create component (write)

    # Workflow approval endpoints (/api/v1/workflows/approvals/*)
    "approvals_list": "100 per minute",  # List approvals (read)
    "approvals_get": "100 per minute",  # Get single approval (read)
    "approvals_create": "30 per minute",  # Create approval (write)
    "approvals_decide": "30 per minute",  # Submit decision (write)
    "approvals_escalate": "20 per minute",  # Escalate approval (write)
    "approvals_bulk": "10 per minute",  # Bulk operations (write, intensive)
    "approvals_stats": "60 per minute",  # Statistics (read)
    "approvals_rules_list": "100 per minute",  # List rules (read)
    "approvals_rules_create": "10 per minute",  # Create rule (write)

    # Default for unspecified endpoints
    "default": "200 per minute"
}


class RateLimiter:
    """
    Custom rate limiter with Redis backend for distributed systems.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize rate limiter with Redis client."""
        self.redis_client = redis_client
        if not self.redis_client and settings.REDIS_URL:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        limit: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if request should be rate limited.
        Returns (is_allowed, metadata)
        """
        if not self.redis_client:
            # If Redis is not available, allow all requests
            return True, {"warning": "Rate limiting not active"}

        try:
            key = f"rate_limit:{endpoint}:{identifier}"
            current_time = int(datetime.utcnow().timestamp())
            window_start = current_time - window

            # Use Redis sorted set to track requests
            pipe = self.redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {f"{current_time}:{id(current_time)}": current_time})

            # Set expiry on the key
            pipe.expire(key, window + 1)

            results = pipe.execute()
            request_count = results[1]

            # Check if limit exceeded
            if request_count >= limit:
                # Calculate retry after
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = window - (current_time - int(oldest_request[0][1]))
                else:
                    retry_after = window

                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": window_start + window,
                    "retry_after": max(1, retry_after)
                }

            return True, {
                "limit": limit,
                "remaining": limit - request_count - 1,
                "reset": window_start + window
            }

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request but log it
            return True, {"error": "Rate limit check failed"}

    def get_endpoint_limits(self, endpoint: str) -> tuple[int, int]:
        """
        Get rate limit configuration for an endpoint.
        Returns (limit, window_seconds)
        """
        # Map endpoint to rate limit configuration
        endpoint_key = endpoint.replace("/", "_").replace("-", "_")

        # Check specific endpoint limits
        for key, limit_str in RATE_LIMITS.items():
            if key in endpoint_key:
                return self._parse_limit_string(limit_str)

        # Default limit
        return self._parse_limit_string(RATE_LIMITS["default"])

    def _parse_limit_string(self, limit_str: str) -> tuple[int, int]:
        """
        Parse rate limit string like "100 per minute" to (limit, window_seconds).
        """
        parts = limit_str.split()
        if len(parts) != 3:
            return 100, 60  # Default fallback

        try:
            limit = int(parts[0])
            period = parts[2].lower()

            periods = {
                "second": 1,
                "minute": 60,
                "hour": 3600,
                "day": 86400
            }

            window = periods.get(period, 60)
            return limit, window

        except (ValueError, KeyError):
            return 100, 60  # Default fallback


# Global rate limiter instance
rate_limiter = RateLimiter()


def create_rate_limit_exceeded_response(request: Request, exc: Exception) -> JSONResponse:
    """
    Create a standardized rate limit exceeded response.
    Follows OWASP guidelines for error responses.
    """
    response_data = {
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please slow down and try again later.",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Add retry-after header if available
    retry_after = getattr(exc, 'retry_after', 60)

    headers = {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(getattr(exc, 'limit', 'N/A')),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(getattr(exc, 'reset', 'N/A'))
    }

    # Log the rate limit violation
    client_id = get_real_client_ip(request)
    logger.warning(
        f"Rate limit exceeded for {client_id} on {request.url.path}",
        extra={
            "client_ip": client_id,
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=response_data,
        headers=headers
    )


# Create limiter instance for slowapi if available
if SLOWAPI_AVAILABLE:
    # Use custom key function that includes user ID if authenticated
    limiter = Limiter(
        key_func=create_identifier_for_rate_limit,
        default_limits=["200 per minute"],
        headers_enabled=True,
        strategy="fixed-window",
        storage_uri=settings.REDIS_URL if settings.REDIS_URL else None
    )
else:
    limiter = None


def rate_limit_middleware(endpoint_limit: str = None):
    """
    Decorator for applying rate limits to specific endpoints.
    Can be used with or without slowapi.
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            # Get client identifier
            identifier = create_identifier_for_rate_limit(request)
            endpoint = request.url.path

            # Determine rate limit for this endpoint
            if endpoint_limit:
                limit, window = rate_limiter._parse_limit_string(endpoint_limit)
            else:
                limit, window = rate_limiter.get_endpoint_limits(endpoint)

            # Check rate limit
            is_allowed, metadata = rate_limiter.check_rate_limit(
                identifier, endpoint, limit, window
            )

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": metadata.get("retry_after", 60)
                    },
                    headers={
                        "Retry-After": str(metadata.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0"
                    }
                )

            # Add rate limit info to response headers
            response = await func(request, *args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(metadata.get("reset", 0))

            return response

        return wrapper
    return decorator


# Specific rate limiters for different endpoint types
scraper_limiter = rate_limit_middleware("5 per hour")
ml_limiter = rate_limit_middleware("100 per minute")
auth_limiter = rate_limit_middleware("5 per minute")
data_limiter = rate_limit_middleware("60 per minute")

# New feature rate limiters
# Templates
templates_read_limiter = rate_limit_middleware("100 per minute")
templates_write_limiter = rate_limit_middleware("20 per minute")
templates_preview_limiter = rate_limit_middleware("30 per minute")

# Email tracking (public endpoints - high volume)
tracking_public_limiter = rate_limit_middleware("1000 per minute")
tracking_unsubscribe_limiter = rate_limit_middleware("50 per hour")

# Demo sites
demo_sites_read_limiter = rate_limit_middleware("100 per minute")
demo_sites_write_limiter = rate_limit_middleware("20 per minute")
demo_sites_generate_limiter = rate_limit_middleware("10 per hour")
demo_sites_deploy_limiter = rate_limit_middleware("10 per hour")
demo_sites_track_limiter = rate_limit_middleware("2000 per minute")

# Workflow approvals
approvals_read_limiter = rate_limit_middleware("100 per minute")
approvals_write_limiter = rate_limit_middleware("30 per minute")
approvals_bulk_limiter = rate_limit_middleware("10 per minute")
approvals_rules_write_limiter = rate_limit_middleware("10 per minute")


__all__ = [
    'RateLimiter',
    'rate_limiter',
    'rate_limit_middleware',
    'scraper_limiter',
    'ml_limiter',
    'auth_limiter',
    'data_limiter',
    'templates_read_limiter',
    'templates_write_limiter',
    'templates_preview_limiter',
    'tracking_public_limiter',
    'tracking_unsubscribe_limiter',
    'demo_sites_read_limiter',
    'demo_sites_write_limiter',
    'demo_sites_generate_limiter',
    'demo_sites_deploy_limiter',
    'demo_sites_track_limiter',
    'approvals_read_limiter',
    'approvals_write_limiter',
    'approvals_bulk_limiter',
    'approvals_rules_write_limiter',
    'create_rate_limit_exceeded_response',
    'get_real_client_ip',
    'limiter'
]