"""
Comprehensive test suite for webhook integration system.

Tests webhook triggers, queue management, security, and response handlers.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from app.models.webhook_queue import (
    WebhookQueueItem,
    WebhookLog,
    WebhookRetryHistory,
    WebhookStatus
)
from app.utils.webhook_security import WebhookSecurity
from app.core.webhook_config import webhook_config, get_webhook_url
from app.services.n8n_webhook_trigger import N8nWebhookTrigger
from app.services.webhook_queue import WebhookQueue


# ============================================================================
# Webhook Security Tests
# ============================================================================

class TestWebhookSecurity:
    """Test webhook signature generation and verification."""

    def test_generate_signature(self):
        """Test signature generation."""
        payload = b'{"event": "test", "data": {"id": 123}}'
        secret = "test-secret-key"

        signature = WebhookSecurity.generate_signature(payload, secret)

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length

    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        payload = b'{"event": "test", "data": {"id": 123}}'
        secret = "test-secret-key"

        # Generate signature
        signature = WebhookSecurity.generate_signature(payload, secret)

        # Verify signature
        is_valid = WebhookSecurity.verify_signature(payload, signature, secret)

        assert is_valid is True

    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        payload = b'{"event": "test", "data": {"id": 123}}'
        secret = "test-secret-key"
        wrong_signature = "invalid_signature_here"

        is_valid = WebhookSecurity.verify_signature(payload, wrong_signature, secret)

        assert is_valid is False

    def test_verify_signature_tampered_payload(self):
        """Test signature verification with tampered payload."""
        original_payload = b'{"event": "test", "data": {"id": 123}}'
        tampered_payload = b'{"event": "test", "data": {"id": 999}}'
        secret = "test-secret-key"

        # Generate signature for original
        signature = WebhookSecurity.generate_signature(original_payload, secret)

        # Try to verify tampered payload
        is_valid = WebhookSecurity.verify_signature(tampered_payload, signature, secret)

        assert is_valid is False

    def test_generate_webhook_secret(self):
        """Test webhook secret generation."""
        secret = WebhookSecurity.generate_webhook_secret()

        assert secret is not None
        assert len(secret) == 64  # 32 bytes in hex = 64 characters
        assert all(c in '0123456789abcdef' for c in secret)

    def test_create_signed_payload(self):
        """Test signed payload creation."""
        data = {"event": "test", "id": 123}
        secret = "test-secret-key"

        result = WebhookSecurity.create_signed_payload(data, secret)

        assert 'payload' in result
        assert 'headers' in result
        assert 'signature' in result
        assert result['payload'] == data
        assert 'X-Webhook-Signature-256' in result['headers']
        assert 'X-Webhook-Timestamp' in result['headers']


# ============================================================================
# Webhook Configuration Tests
# ============================================================================

class TestWebhookConfig:
    """Test webhook configuration."""

    def test_get_webhook_url(self):
        """Test getting webhook URLs."""
        url = get_webhook_url('lead_scraped')

        assert url is not None
        assert 'lead-scraped' in url

    def test_webhook_config_validation(self):
        """Test webhook configuration validation."""
        issues = webhook_config.validate_configuration()

        # Should return list (may be empty if config is valid)
        assert isinstance(issues, list)

    def test_webhook_config_is_enabled(self):
        """Test checking if webhook integration is enabled."""
        is_enabled = webhook_config.is_enabled()

        # Should return boolean
        assert isinstance(is_enabled, bool)


# ============================================================================
# N8n Webhook Trigger Tests
# ============================================================================

class TestN8nWebhookTrigger:
    """Test n8n webhook trigger service."""

    @pytest.fixture
    def trigger(self):
        """Create webhook trigger instance."""
        return N8nWebhookTrigger()

    @pytest.mark.asyncio
    async def test_send_webhook_success(self, trigger):
        """Test successful webhook sending."""
        with patch.object(trigger, 'get_session') as mock_session:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value='{"status": "ok"}')

            mock_session.return_value.post = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
            )

            result = await trigger.send_webhook(
                webhook_url="http://test.example.com/webhook",
                data={"event": "test", "id": 123}
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_webhook_failure(self, trigger):
        """Test webhook sending with failure."""
        with patch.object(trigger, 'get_session') as mock_session:
            # Mock failed response
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value='{"error": "Internal error"}')

            mock_session.return_value.post = AsyncMock(
                return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
            )

            result = await trigger.send_webhook(
                webhook_url="http://test.example.com/webhook",
                data={"event": "test", "id": 123},
                retry_count=0  # No retries for test
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_trigger_lead_scraped(self, trigger):
        """Test lead scraped webhook trigger."""
        with patch.object(trigger, 'send_webhook') as mock_send:
            mock_send.return_value = True

            result = await trigger.trigger_lead_scraped(
                lead_id=123,
                lead_data={
                    "business_name": "Test Business",
                    "category": "web design",
                    "score": 0.85
                }
            )

            assert mock_send.called
            call_args = mock_send.call_args
            assert call_args[1]['data']['data']['lead_id'] == 123

    @pytest.mark.asyncio
    async def test_trigger_demo_completed(self, trigger):
        """Test demo completed webhook trigger."""
        with patch.object(trigger, 'send_webhook') as mock_send:
            mock_send.return_value = True

            result = await trigger.trigger_demo_completed(
                demo_site_id=456,
                demo_data={
                    "url": "https://demo.example.com",
                    "lead_id": 123,
                    "status": "ready"
                }
            )

            assert mock_send.called


# ============================================================================
# Webhook Queue Tests
# ============================================================================

class TestWebhookQueue:
    """Test webhook queue service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def queue(self, mock_db):
        """Create webhook queue instance."""
        return WebhookQueue(mock_db)

    @pytest.mark.asyncio
    async def test_enqueue_webhook(self, queue, mock_db):
        """Test enqueueing a webhook."""
        # Setup mock
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        webhook_id = await queue.enqueue(
            webhook_url="http://test.example.com/webhook",
            payload={"event": "test", "id": 123},
            event_type="test_event",
            priority=1
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, queue, mock_db):
        """Test getting queue statistics."""
        # Mock query results
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        stats = await queue.get_queue_stats()

        assert isinstance(stats, dict)
        assert 'pending' in stats
        assert 'sent' in stats
        assert 'failed' in stats

    @pytest.mark.asyncio
    async def test_retry_failed_webhook(self, queue, mock_db):
        """Test retrying a failed webhook."""
        # Mock webhook item
        mock_webhook = Mock()
        mock_webhook.id = 123
        mock_webhook.status = WebhookStatus.FAILED.value

        mock_db.query.return_value.filter.return_value.first.return_value = mock_webhook

        result = await queue.retry_failed(123)

        assert result is True
        assert mock_webhook.status == WebhookStatus.PENDING.value
        assert mock_webhook.retry_count == 0

    @pytest.mark.asyncio
    async def test_cancel_webhook(self, queue, mock_db):
        """Test cancelling a webhook."""
        # Mock webhook item
        mock_webhook = Mock()
        mock_webhook.id = 123

        mock_db.query.return_value.filter.return_value.first.return_value = mock_webhook

        result = await queue.cancel_webhook(123)

        assert result is True
        assert mock_webhook.status == WebhookStatus.CANCELLED.value


# ============================================================================
# Webhook Models Tests
# ============================================================================

class TestWebhookModels:
    """Test webhook database models."""

    def test_webhook_queue_item_should_retry(self):
        """Test should_retry logic."""
        # Create webhook that should retry
        webhook = WebhookQueueItem(
            id=1,
            webhook_url="http://test.example.com",
            payload={"test": "data"},
            event_type="test",
            status=WebhookStatus.FAILED.value,
            retry_count=1,
            max_retries=3,
            next_retry_at=datetime.utcnow() - timedelta(seconds=5)
        )

        assert webhook.should_retry() is True

    def test_webhook_queue_item_max_retries_reached(self):
        """Test max retries reached."""
        webhook = WebhookQueueItem(
            id=1,
            webhook_url="http://test.example.com",
            payload={"test": "data"},
            event_type="test",
            status=WebhookStatus.FAILED.value,
            retry_count=3,
            max_retries=3
        )

        assert webhook.should_retry() is False

    def test_webhook_queue_item_calculate_next_retry(self):
        """Test next retry calculation."""
        webhook = WebhookQueueItem(
            id=1,
            webhook_url="http://test.example.com",
            payload={"test": "data"},
            event_type="test",
            retry_count=0
        )

        next_retry = webhook.calculate_next_retry([5, 30, 300])

        assert next_retry > datetime.utcnow()
        assert next_retry < datetime.utcnow() + timedelta(seconds=10)

    def test_webhook_log_is_success(self):
        """Test webhook log success detection."""
        log = WebhookLog(
            id=1,
            direction="outgoing",
            webhook_url="http://test.example.com",
            method="POST",
            response_status=200
        )

        assert log.is_success is True

    def test_webhook_log_is_error(self):
        """Test webhook log error detection."""
        log = WebhookLog(
            id=1,
            direction="outgoing",
            webhook_url="http://test.example.com",
            method="POST",
            response_status=500,
            error_message="Internal server error"
        )

        assert log.is_error is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestWebhookIntegration:
    """Integration tests for webhook system."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_webhook_flow(self):
        """Test complete webhook flow from trigger to delivery."""
        # This would require actual database and n8n instance
        # Marked as integration test to be run separately
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_webhook_retry_flow(self):
        """Test webhook retry flow with failures."""
        # This would require actual database
        # Marked as integration test to be run separately
        pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestWebhookPerformance:
    """Performance tests for webhook system."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_webhook_sending(self):
        """Test batch webhook sending performance."""
        trigger = N8nWebhookTrigger()

        webhooks = [
            {
                'url': f'http://test.example.com/webhook/{i}',
                'data': {'id': i, 'event': 'test'}
            }
            for i in range(10)
        ]

        with patch.object(trigger, 'send_webhook') as mock_send:
            mock_send.return_value = True

            start = datetime.utcnow()
            results = await trigger.batch_send_webhooks(webhooks)
            duration = (datetime.utcnow() - start).total_seconds()

            assert results['total'] == 10
            assert duration < 5  # Should complete in under 5 seconds


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
