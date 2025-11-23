"""
Security Configuration Module

Central configuration for security settings including URL validation,
allowed domains, and other security parameters.
"""

from typing import List, Set
from pydantic import BaseSettings


class SecuritySettings(BaseSettings):
    """Security-related configuration settings."""

    # Webhook allowed domains
    WEBHOOK_ALLOWED_DOMAINS: List[str] = [
        'n8n.cloud',
        'hooks.slack.com',
        'discord.com',
        'webhook.site',  # Remove in production
        # Add your n8n instance domain if self-hosted
        # 'n8n.yourdomain.com',
    ]

    # Email tracking redirect allowed domains
    EMAIL_REDIRECT_ALLOWED_DOMAINS: List[str] = [
        'fliptechpro.com',
        'www.fliptechpro.com',
        # Trusted external sites
        'linkedin.com',
        'www.linkedin.com',
        'github.com',
        'www.github.com',
        'twitter.com',
        'x.com',
        # Add your application domains
    ]

    # General redirect allowed domains (for OAuth, etc.)
    REDIRECT_ALLOWED_DOMAINS: List[str] = [
        'fliptechpro.com',
        'www.fliptechpro.com',
        'localhost',  # For development only
        '127.0.0.1',  # For development only
        # Add OAuth provider domains
        'accounts.google.com',
        'login.microsoftonline.com',
        'github.com',
    ]

    # Security flags
    ALLOW_PRIVATE_IPS: bool = False  # Never allow in production
    ENABLE_STRICT_URL_VALIDATION: bool = True
    REQUIRE_WEBHOOK_SIGNATURE: bool = True
    WEBHOOK_SECRET: str = ""  # Set via environment variable

    # Rate limiting
    WEBHOOK_RATE_LIMIT_PER_MINUTE: int = 60
    EMAIL_TRACKING_RATE_LIMIT_PER_MINUTE: int = 100

    # CORS settings
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:5173",  # Vite dev
        "https://fliptechpro.com",
        "https://www.fliptechpro.com",
    ]

    # Security headers
    ENABLE_SECURITY_HEADERS: bool = True
    CSP_POLICY: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.fliptechpro.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Session security
    SESSION_COOKIE_SECURE: bool = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


# Global instance
security_settings = SecuritySettings()


def get_webhook_allowed_domains() -> List[str]:
    """Get list of allowed domains for webhooks."""
    return security_settings.WEBHOOK_ALLOWED_DOMAINS


def get_email_redirect_allowed_domains() -> List[str]:
    """Get list of allowed domains for email tracking redirects."""
    return security_settings.EMAIL_REDIRECT_ALLOWED_DOMAINS


def get_redirect_allowed_domains() -> List[str]:
    """Get list of allowed domains for general redirects."""
    return security_settings.REDIRECT_ALLOWED_DOMAINS


def is_development_mode() -> bool:
    """Check if running in development mode."""
    # Check if localhost/127.0.0.1 is in allowed origins
    return any(
        'localhost' in origin or '127.0.0.1' in origin
        for origin in security_settings.CORS_ALLOWED_ORIGINS
    )