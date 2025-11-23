"""
Webhook configuration for n8n integration.

This module provides configuration settings for webhook communications
between the backend and n8n workflows.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
import os
from app.core.config import settings


class WebhookEndpoints(BaseModel):
    """n8n webhook endpoint URLs."""

    # Outgoing webhook URLs (backend -> n8n)
    lead_scraped: str = "/webhook/lead-scraped"
    lead_qualified: str = "/webhook/lead-qualified"
    demo_completed: str = "/webhook/demo-completed"
    demo_failed: str = "/webhook/demo-failed"
    video_completed: str = "/webhook/video-completed"
    video_failed: str = "/webhook/video-failed"
    email_sent: str = "/webhook/email-sent"
    email_failed: str = "/webhook/email-failed"
    lead_responded: str = "/webhook/lead-responded"
    approval_requested: str = "/webhook/approval-requested"
    workflow_error: str = "/webhook/workflow-error"

    # Incoming webhook URLs (n8n -> backend)
    demo_approval_response: str = "/api/v1/webhooks/n8n/demo-approval"
    video_approval_response: str = "/api/v1/webhooks/n8n/video-approval"
    workflow_completed: str = "/api/v1/webhooks/n8n/workflow-completed"
    workflow_status: str = "/api/v1/webhooks/n8n/workflow-status"

    def get_full_url(self, endpoint_name: str, base_url: str) -> str:
        """Get full URL for an endpoint."""
        endpoint = getattr(self, endpoint_name, None)
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")

        # Remove trailing slash from base_url
        base_url = base_url.rstrip('/')

        # Ensure endpoint starts with /
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        return f"{base_url}{endpoint}"


class WebhookRetryConfig(BaseModel):
    """Webhook retry configuration."""

    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delays: List[int] = Field(
        default=[5, 30, 300],
        description="Retry delays in seconds (exponential backoff)"
    )
    timeout_seconds: int = Field(default=30, ge=5, le=300, description="Request timeout")
    max_age_seconds: int = Field(
        default=300,
        description="Maximum age for timestamp validation (replay attack prevention)"
    )

    @field_validator('retry_delays')
    @classmethod
    def validate_retry_delays(cls, v, info):
        """Ensure retry delays match max_retries."""
        max_retries = info.data.get('max_retries', 3)
        if len(v) < max_retries:
            # Extend with last value
            last_delay = v[-1] if v else 300
            v.extend([last_delay] * (max_retries - len(v)))
        return v[:max_retries]


class WebhookSecurityConfig(BaseModel):
    """Webhook security configuration."""

    webhook_secret: str = Field(
        default_factory=lambda: os.getenv("WEBHOOK_SECRET", ""),
        description="Shared secret for webhook signatures"
    )
    n8n_webhook_secret: str = Field(
        default_factory=lambda: os.getenv("N8N_WEBHOOK_SECRET", ""),
        description="Shared secret for n8n webhooks"
    )
    signature_algorithm: str = Field(default="sha256", description="HMAC algorithm")
    require_signature: bool = Field(
        default=True,
        description="Require signature verification for incoming webhooks"
    )
    require_timestamp: bool = Field(
        default=True,
        description="Require timestamp validation"
    )

    @field_validator('webhook_secret', 'n8n_webhook_secret')
    @classmethod
    def validate_secrets(cls, v, info):
        """Warn if secrets are not set in production."""
        if not v and os.getenv("ENVIRONMENT") == "production":
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"{info.field_name} is not set in production environment. "
                "Webhook security is compromised!"
            )
        return v


class N8nConnectionConfig(BaseModel):
    """n8n connection configuration."""

    enabled: bool = Field(
        default_factory=lambda: os.getenv("N8N_ENABLED", "false").lower() == "true",
        description="Enable n8n integration"
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv("N8N_BASE_URL", "http://localhost:5678"),
        description="n8n base URL"
    )
    api_key: str = Field(
        default_factory=lambda: os.getenv("N8N_API_KEY", ""),
        description="n8n API key (optional)"
    )
    webhook_base_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("N8N_WEBHOOK_BASE_URL", None),
        description="Override webhook base URL (if different from base_url)"
    )

    @field_validator('webhook_base_url')
    @classmethod
    def set_webhook_base_url(cls, v, info):
        """Set webhook base URL from base_url if not specified."""
        if not v:
            return info.data.get('base_url', 'http://localhost:5678')
        return v


class WebhookQueueConfig(BaseModel):
    """Webhook queue configuration."""

    enabled: bool = Field(default=True, description="Enable webhook queue")
    batch_size: int = Field(default=10, ge=1, le=100, description="Queue processing batch size")
    processing_interval: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Queue processing interval in seconds"
    )
    priority_enabled: bool = Field(default=True, description="Enable priority processing")
    max_queue_size: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum queue size"
    )
    cleanup_after_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Clean up old webhook logs after N days"
    )


class WebhookMonitoringConfig(BaseModel):
    """Webhook monitoring configuration."""

    log_all_requests: bool = Field(default=True, description="Log all webhook requests")
    log_request_body: bool = Field(default=True, description="Log request payloads")
    log_response_body: bool = Field(default=True, description="Log response payloads")
    alert_on_failure: bool = Field(default=True, description="Send alerts on webhook failures")
    failure_threshold: int = Field(
        default=5,
        ge=1,
        description="Alert after N consecutive failures"
    )
    monitoring_enabled: bool = Field(default=True, description="Enable webhook monitoring")


class WebhookConfig(BaseModel):
    """
    Complete webhook configuration.

    This is the main configuration class that combines all webhook-related
    settings for the application.
    """

    # Connection settings
    n8n: N8nConnectionConfig = Field(default_factory=N8nConnectionConfig)

    # Endpoint definitions
    endpoints: WebhookEndpoints = Field(default_factory=WebhookEndpoints)

    # Retry configuration
    retry: WebhookRetryConfig = Field(default_factory=WebhookRetryConfig)

    # Security configuration
    security: WebhookSecurityConfig = Field(default_factory=WebhookSecurityConfig)

    # Queue configuration
    queue: WebhookQueueConfig = Field(default_factory=WebhookQueueConfig)

    # Monitoring configuration
    monitoring: WebhookMonitoringConfig = Field(default_factory=WebhookMonitoringConfig)

    def get_webhook_url(self, event_type: str) -> str:
        """
        Get full webhook URL for an event type.

        Args:
            event_type: Type of webhook event (e.g., 'lead_scraped')

        Returns:
            Full webhook URL

        Example:
            >>> config = WebhookConfig()
            >>> url = config.get_webhook_url('lead_scraped')
            >>> print(url)
            'http://localhost:5678/webhook/lead-scraped'
        """
        endpoint = getattr(self.endpoints, event_type, None)
        if not endpoint:
            raise ValueError(f"Unknown webhook event type: {event_type}")

        base_url = self.n8n.webhook_base_url.rstrip('/')
        if not endpoint.startswith('/'):
            endpoint = f'/{endpoint}'

        return f"{base_url}{endpoint}"

    def is_enabled(self) -> bool:
        """Check if webhook integration is enabled."""
        return self.n8n.enabled

    def validate_configuration(self) -> List[str]:
        """
        Validate webhook configuration and return list of issues.

        Returns:
            List of configuration issues (empty if valid)
        """
        issues = []

        # Check if n8n is enabled
        if not self.n8n.enabled:
            issues.append("n8n integration is disabled")
            return issues

        # Check n8n URL
        if not self.n8n.base_url:
            issues.append("n8n base URL is not set")

        # Check security in production
        if os.getenv("ENVIRONMENT") == "production":
            if not self.security.webhook_secret:
                issues.append("Webhook secret is not set in production")
            if not self.security.n8n_webhook_secret:
                issues.append("n8n webhook secret is not set in production")

        # Check retry configuration
        if self.retry.max_retries < 1:
            issues.append("max_retries must be at least 1")

        if len(self.retry.retry_delays) < self.retry.max_retries:
            issues.append(
                f"retry_delays must have at least {self.retry.max_retries} values"
            )

        return issues

    class Config:
        """Pydantic config."""
        env_prefix = "WEBHOOK_"
        case_sensitive = False


# Create global webhook configuration instance
webhook_config = WebhookConfig()


# Validation on import
def validate_webhook_config():
    """Validate webhook configuration on import."""
    import logging
    logger = logging.getLogger(__name__)

    if webhook_config.n8n.enabled:
        issues = webhook_config.validate_configuration()
        if issues:
            logger.warning(
                f"Webhook configuration issues found: {', '.join(issues)}"
            )
        else:
            logger.info(
                f"Webhook configuration validated successfully. "
                f"n8n URL: {webhook_config.n8n.base_url}"
            )
    else:
        logger.info("n8n webhook integration is disabled")


# Run validation
validate_webhook_config()


# Convenience function to get webhook URL
def get_webhook_url(event_type: str) -> str:
    """
    Get webhook URL for an event type.

    Args:
        event_type: Type of webhook event

    Returns:
        Full webhook URL

    Example:
        >>> from app.core.webhook_config import get_webhook_url
        >>> url = get_webhook_url('lead_scraped')
    """
    return webhook_config.get_webhook_url(event_type)
