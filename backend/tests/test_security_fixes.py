"""
Security Vulnerability Test Suite

Tests for SSRF and open redirect vulnerability fixes.
Verifies that malicious URLs are properly blocked.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.core.url_validator import (
    URLValidator,
    URLSecurityError,
    validate_email_tracking_redirect,
    validate_webhook_endpoint
)


class TestURLValidator:
    """Test URL validation security measures."""

    def test_blocks_private_ips(self):
        """Test that private IP addresses are blocked."""
        validator = URLValidator(allow_private_ips=False)

        # Test various private IP formats
        private_ips = [
            "http://192.168.1.1/webhook",
            "http://10.0.0.1:8080/hook",
            "http://172.16.0.1/",
            "http://127.0.0.1/admin",
            "http://localhost/internal",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://[::1]/ipv6",  # IPv6 loopback
            "http://[fe80::1]/link-local",  # IPv6 link-local
        ]

        for url in private_ips:
            with pytest.raises(URLSecurityError) as exc_info:
                validator.validate_webhook_url(url)
            assert "private" in str(exc_info.value).lower() or "blocked" in str(exc_info.value).lower()

    def test_blocks_metadata_endpoints(self):
        """Test that cloud metadata endpoints are blocked."""
        validator = URLValidator(allow_private_ips=False)

        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://metadata.aws/",
            "http://100.100.100.200/latest/meta-data/",  # Alibaba
        ]

        for url in metadata_urls:
            with pytest.raises(URLSecurityError) as exc_info:
                validator.validate_webhook_url(url)
            assert "blocked" in str(exc_info.value).lower() or "metadata" in str(exc_info.value).lower()

    def test_validates_allowed_domains(self):
        """Test domain allowlisting."""
        validator = URLValidator(
            allowed_domains=["n8n.cloud", "hooks.slack.com"],
            allow_private_ips=False
        )

        # Should pass
        valid_urls = [
            "https://n8n.cloud/webhook/abc123",
            "https://hooks.slack.com/services/T00000000/B00000000/xxxx",
            "https://subdomain.n8n.cloud/hook",
        ]

        for url in valid_urls:
            validated = validator.validate_webhook_url(url)
            assert validated == url or validated == url.rstrip('/')

        # Should fail
        invalid_urls = [
            "https://evil.com/webhook",
            "https://n8n.evil.com/hook",  # Not a subdomain of n8n.cloud
            "https://slack.com/hook",  # Wrong slack domain
        ]

        for url in invalid_urls:
            with pytest.raises(URLSecurityError) as exc_info:
                validator.validate_webhook_url(url)
            assert "not in the allowed domains" in str(exc_info.value)

    def test_blocks_javascript_urls(self):
        """Test that JavaScript and data URLs are blocked."""
        validator = URLValidator()

        malicious_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "vbscript:msgbox('XSS')",
        ]

        for url in malicious_urls:
            with pytest.raises(URLSecurityError) as exc_info:
                validator.validate_redirect_url(url)
            assert "not allowed for security reasons" in str(exc_info.value)

    def test_blocks_protocol_relative_urls(self):
        """Test that protocol-relative URLs are blocked for redirects."""
        validator = URLValidator()

        with pytest.raises(URLSecurityError) as exc_info:
            validator.validate_redirect_url("//evil.com/redirect")
        assert "Protocol-relative URLs are not allowed" in str(exc_info.value)

    def test_normalizes_urls(self):
        """Test URL normalization."""
        validator = URLValidator(
            allowed_domains=["example.com"],
            allow_private_ips=False
        )

        # Test path traversal normalization
        url = "https://example.com/path/../admin/secret"
        normalized = validator.validate_webhook_url(url)
        assert "/.." not in normalized
        assert normalized == "https://example.com/admin/secret"

        # Test trailing slash removal
        url = "https://example.com/webhook/"
        normalized = validator.validate_webhook_url(url)
        assert normalized == "https://example.com/webhook"

    def test_blocks_encoded_attacks(self):
        """Test that URL encoding attacks are detected."""
        validator = URLValidator(strict_mode=True)

        encoded_attacks = [
            "http://example.com/%2e%2e/admin",  # Encoded ../
            "http://example.com/test%00.php",  # Null byte
            "http://example.com/test%0d%0aSet-Cookie:%20test",  # CRLF injection
        ]

        for url in encoded_attacks:
            with pytest.raises(URLSecurityError) as exc_info:
                validator.validate_webhook_url(url)
            assert "suspicious" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


class TestEmailTrackingRedirect:
    """Test email tracking redirect validation."""

    def test_validates_email_redirect_domains(self):
        """Test email tracking redirect domain validation."""
        allowed = ["fliptechpro.com", "linkedin.com"]

        # Valid redirects
        assert validate_email_tracking_redirect("https://fliptechpro.com/page", allowed)
        assert validate_email_tracking_redirect("https://linkedin.com/profile", allowed)

        # Invalid redirects
        with pytest.raises(URLSecurityError):
            validate_email_tracking_redirect("https://evil.com/phishing", allowed)

        with pytest.raises(URLSecurityError):
            validate_email_tracking_redirect("http://192.168.1.1/internal", allowed)

    def test_blocks_open_redirect_attacks(self):
        """Test common open redirect attack patterns."""
        allowed = ["trusted.com"]

        attack_urls = [
            "https://trusted.com@evil.com",  # @ character bypass
            "https://evil.com#https://trusted.com",  # Fragment bypass
            "https://evil.com?redirect=https://trusted.com",  # Query bypass
            "//evil.com",  # Protocol-relative
            "https://trusted.com.evil.com",  # Subdomain bypass
        ]

        for url in attack_urls:
            with pytest.raises(URLSecurityError):
                validate_email_tracking_redirect(url, allowed)


class TestWebhookValidation:
    """Test webhook URL validation."""

    def test_validates_webhook_domains(self):
        """Test webhook domain validation."""
        allowed = ["n8n.cloud", "hooks.slack.com"]

        # Valid webhooks
        assert validate_webhook_endpoint("https://n8n.cloud/webhook/123", allowed)
        assert validate_webhook_endpoint("https://hooks.slack.com/services/xyz", allowed)

        # Invalid webhooks
        with pytest.raises(URLSecurityError):
            validate_webhook_endpoint("https://attacker.com/steal", allowed)

    def test_blocks_ssrf_attacks(self):
        """Test SSRF attack prevention."""
        allowed = ["webhook.site"]

        ssrf_urls = [
            "http://169.254.169.254/latest/meta-data/",
            "http://localhost:8080/admin",
            "http://127.0.0.1:22/ssh",
            "file:///etc/passwd",
            "gopher://localhost:9000/_test",
            "dict://localhost:11211/stats",
        ]

        for url in ssrf_urls:
            with pytest.raises(URLSecurityError):
                validate_webhook_endpoint(url, allowed)


class TestIntegrationSecurity:
    """Integration tests for security fixes in endpoints."""

    @patch('app.core.database.get_db')
    def test_workflow_approval_blocks_ssrf(self, mock_db):
        """Test that workflow approval endpoint blocks SSRF attempts."""
        from app.api.endpoints.workflow_approvals import CreateApprovalRequest

        # Test with malicious webhook URL
        with pytest.raises(ValueError) as exc_info:
            request = CreateApprovalRequest(
                approval_type="demo_site_review",
                resource_id=1,
                resource_data={},
                workflow_execution_id="test123",
                resume_webhook_url="http://169.254.169.254/latest/meta-data/"
            )
        assert "Invalid webhook URL" in str(exc_info.value)

        # Test with localhost
        with pytest.raises(ValueError) as exc_info:
            request = CreateApprovalRequest(
                approval_type="demo_site_review",
                resource_id=1,
                resource_data={},
                workflow_execution_id="test123",
                resume_webhook_url="http://localhost:8080/webhook"
            )
        assert "Invalid webhook URL" in str(exc_info.value)

    @patch('app.services.email_service.EmailService')
    @patch('app.core.database.get_db')
    def test_email_tracking_blocks_open_redirect(self, mock_db, mock_email_service):
        """Test that email tracking endpoint blocks open redirect attempts."""
        from fastapi import HTTPException
        from app.api.endpoints.email_tracking import track_email_click

        # Mock dependencies
        mock_db_session = Mock()
        mock_db.return_value = mock_db_session

        # Test with malicious redirect
        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.run(track_email_click(
                tracking_token="test123",
                url="https://evil.com/phishing",
                db=mock_db_session
            ))
        assert exc_info.value.status_code == 400
        assert "Invalid redirect URL" in exc_info.value.detail


class TestSecurityConfig:
    """Test security configuration."""

    def test_security_config_loads(self):
        """Test that security configuration loads correctly."""
        from app.core.security_config import (
            get_webhook_allowed_domains,
            get_email_redirect_allowed_domains,
            security_settings
        )

        # Check webhook domains
        webhook_domains = get_webhook_allowed_domains()
        assert isinstance(webhook_domains, list)
        assert len(webhook_domains) > 0
        assert 'n8n.cloud' in webhook_domains

        # Check email redirect domains
        email_domains = get_email_redirect_allowed_domains()
        assert isinstance(email_domains, list)
        assert len(email_domains) > 0

        # Check security flags
        assert isinstance(security_settings.ALLOW_PRIVATE_IPS, bool)
        assert isinstance(security_settings.ENABLE_STRICT_URL_VALIDATION, bool)

    def test_development_mode_detection(self):
        """Test development mode detection."""
        from app.core.security_config import is_development_mode

        # Should detect development mode based on localhost in CORS
        is_dev = is_development_mode()
        assert isinstance(is_dev, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])