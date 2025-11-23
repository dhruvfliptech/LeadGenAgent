"""
Email Configuration
Centralized email settings loaded from environment variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class EmailConfig(BaseSettings):
    """Email configuration settings"""

    # Provider selection
    EMAIL_PROVIDER: str = "smtp"  # smtp, sendgrid, mailgun, resend

    # SMTP Settings (for Gmail, Outlook, or custom SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # API Keys for third-party providers
    SENDGRID_API_KEY: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    MAILGUN_DOMAIN: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None

    # Email sender settings
    EMAIL_FROM: str = "noreply@fliptechpro.com"
    EMAIL_FROM_NAME: str = "FlipTech Pro"
    EMAIL_REPLY_TO: str = "support@fliptechpro.com"

    # Tracking settings
    TRACKING_DOMAIN: str = "http://localhost:8000"
    TRACKING_PIXEL_ENABLED: bool = True
    LINK_TRACKING_ENABLED: bool = True

    # Rate limiting
    MAX_EMAILS_PER_HOUR: int = 100
    MAX_EMAILS_PER_DAY: int = 1000
    BATCH_SIZE: int = 50
    BATCH_DELAY_SECONDS: int = 1

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5

    # Testing and debugging
    TEST_MODE: bool = False  # If True, log emails instead of sending
    DEBUG_EMAIL_OVERRIDE: Optional[str] = None  # Override all recipients in dev

    # Bounce handling
    BOUNCE_CHECK_ENABLED: bool = True
    MAX_BOUNCE_COUNT: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env

    @field_validator('EMAIL_PROVIDER')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate email provider selection"""
        valid_providers = ['smtp', 'sendgrid', 'mailgun', 'resend']
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid email provider. Must be one of: {', '.join(valid_providers)}")
        return v.lower()

    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate that required settings are present for selected provider
        Returns: (is_valid, error_messages)
        """
        errors = []

        if self.TEST_MODE:
            return True, []  # Skip validation in test mode

        # Validate based on provider
        if self.EMAIL_PROVIDER == 'smtp':
            if not self.SMTP_HOST:
                errors.append("SMTP_HOST is required for SMTP provider")
            if not self.SMTP_USERNAME:
                errors.append("SMTP_USERNAME is required for SMTP provider")
            if not self.SMTP_PASSWORD:
                errors.append("SMTP_PASSWORD is required for SMTP provider")

        elif self.EMAIL_PROVIDER == 'sendgrid':
            if not self.SENDGRID_API_KEY:
                errors.append("SENDGRID_API_KEY is required for SendGrid provider")

        elif self.EMAIL_PROVIDER == 'mailgun':
            if not self.MAILGUN_API_KEY:
                errors.append("MAILGUN_API_KEY is required for Mailgun provider")
            if not self.MAILGUN_DOMAIN:
                errors.append("MAILGUN_DOMAIN is required for Mailgun provider")

        elif self.EMAIL_PROVIDER == 'resend':
            if not self.RESEND_API_KEY:
                errors.append("RESEND_API_KEY is required for Resend provider")

        # Common validation
        if not self.EMAIL_FROM:
            errors.append("EMAIL_FROM is required")

        if not self.TRACKING_DOMAIN:
            errors.append("TRACKING_DOMAIN is required for email tracking")

        return len(errors) == 0, errors


# Global email configuration instance
email_config = EmailConfig()
