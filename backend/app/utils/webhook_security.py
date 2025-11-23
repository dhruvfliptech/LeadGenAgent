"""
Webhook security utilities for signature generation and verification.

This module provides security functions for webhook communication,
including HMAC signature generation and verification to ensure
webhook authenticity and integrity.
"""

import hmac
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
import json

logger = logging.getLogger(__name__)


class WebhookSecurity:
    """
    Webhook security utilities for signing and verifying webhooks.

    This class provides methods for generating and verifying HMAC signatures
    to secure webhook communications between services.
    """

    # Signature header names
    SIGNATURE_HEADER = "X-Webhook-Signature"
    SIGNATURE_HEADER_256 = "X-Webhook-Signature-256"
    N8N_SIGNATURE_HEADER = "X-N8N-Signature"
    TIMESTAMP_HEADER = "X-Webhook-Timestamp"

    @staticmethod
    def generate_signature(payload: bytes, secret: str, algorithm: str = "sha256") -> str:
        """
        Generate HMAC signature for outgoing webhooks.

        Args:
            payload: The webhook payload as bytes
            secret: The shared secret key
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            Hexadecimal signature string

        Example:
            >>> payload = b'{"event": "lead_scraped", "data": {...}}'
            >>> secret = "my-secret-key"
            >>> signature = WebhookSecurity.generate_signature(payload, secret)
            >>> print(signature)
            'a3c5f7e9b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c6e8b0d2f4a6'
        """
        if not secret:
            raise ValueError("Secret key is required for signature generation")

        try:
            # Get hash function
            hash_func = getattr(hashlib, algorithm)

            # Generate HMAC signature
            signature = hmac.new(
                key=secret.encode('utf-8'),
                msg=payload,
                digestmod=hash_func
            ).hexdigest()

            return signature

        except AttributeError:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        except Exception as e:
            logger.error(f"Error generating signature: {str(e)}")
            raise

    @staticmethod
    def verify_signature(
        payload: bytes,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
    ) -> bool:
        """
        Verify HMAC signature for incoming webhooks.

        Args:
            payload: The webhook payload as bytes
            signature: The signature to verify
            secret: The shared secret key
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            True if signature is valid, False otherwise

        Example:
            >>> payload = b'{"event": "demo_approved", "data": {...}}'
            >>> signature = "a3c5f7e9b2d4f6a8..."
            >>> secret = "my-secret-key"
            >>> is_valid = WebhookSecurity.verify_signature(payload, signature, secret)
        """
        if not secret:
            logger.warning("No secret key provided for signature verification")
            return False

        if not signature:
            logger.warning("No signature provided for verification")
            return False

        try:
            # Generate expected signature
            expected_signature = WebhookSecurity.generate_signature(
                payload, secret, algorithm
            )

            # Use constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(signature, expected_signature)

            if not is_valid:
                logger.warning(
                    f"Signature verification failed. "
                    f"Expected: {expected_signature[:10]}..., "
                    f"Got: {signature[:10]}..."
                )

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return False

    @staticmethod
    async def verify_n8n_webhook(
        request: Request,
        secret: str,
        signature_header: str = N8N_SIGNATURE_HEADER
    ) -> bool:
        """
        Verify incoming webhook is from n8n.

        Args:
            request: FastAPI request object
            secret: Shared secret key
            signature_header: Header name containing signature

        Returns:
            True if signature is valid

        Raises:
            HTTPException: If signature is missing or invalid

        Example:
            >>> @router.post("/webhook/n8n/callback")
            >>> async def n8n_callback(request: Request):
            >>>     await WebhookSecurity.verify_n8n_webhook(request, settings.WEBHOOK_SECRET)
            >>>     # Process webhook...
        """
        # Get signature from headers
        signature = request.headers.get(signature_header)

        if not signature:
            logger.error(f"Missing signature header: {signature_header}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Missing signature header: {signature_header}"
            )

        # Get request body
        try:
            body = await request.body()
        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request body"
            )

        # Verify signature
        is_valid = WebhookSecurity.verify_signature(body, signature, secret)

        if not is_valid:
            logger.error("Invalid webhook signature from n8n")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        return True

    @staticmethod
    def generate_webhook_secret(length: int = 32) -> str:
        """
        Generate a secure random webhook secret.

        Args:
            length: Length of the secret in bytes (default: 32)

        Returns:
            Hexadecimal secret string

        Example:
            >>> secret = WebhookSecurity.generate_webhook_secret()
            >>> print(secret)
            'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2'
        """
        return secrets.token_hex(length)

    @staticmethod
    def create_signed_payload(
        data: Dict[str, Any],
        secret: str,
        include_timestamp: bool = True
    ) -> Dict[str, Any]:
        """
        Create a signed payload with signature for outgoing webhooks.

        Args:
            data: Payload data to sign
            secret: Secret key for signing
            include_timestamp: Whether to include timestamp (default: True)

        Returns:
            Dictionary containing signed payload and headers

        Example:
            >>> data = {"event": "lead_scraped", "lead_id": 123}
            >>> result = WebhookSecurity.create_signed_payload(data, "secret-key")
            >>> print(result['headers'])
            {'X-Webhook-Signature-256': '...', 'X-Webhook-Timestamp': '...'}
        """
        import time

        # Serialize payload
        payload_json = json.dumps(data, sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')

        # Generate signature
        signature = WebhookSecurity.generate_signature(payload_bytes, secret)

        # Create headers
        headers = {
            WebhookSecurity.SIGNATURE_HEADER_256: signature
        }

        if include_timestamp:
            headers[WebhookSecurity.TIMESTAMP_HEADER] = str(int(time.time()))

        return {
            'payload': data,
            'headers': headers,
            'signature': signature
        }

    @staticmethod
    async def verify_webhook_with_timestamp(
        request: Request,
        secret: str,
        max_age_seconds: int = 300
    ) -> bool:
        """
        Verify webhook signature with timestamp validation.

        This method provides additional protection against replay attacks
        by checking the timestamp of the webhook.

        Args:
            request: FastAPI request object
            secret: Shared secret key
            max_age_seconds: Maximum age of webhook in seconds (default: 300)

        Returns:
            True if signature and timestamp are valid

        Raises:
            HTTPException: If validation fails

        Example:
            >>> @router.post("/webhook/secure")
            >>> async def secure_webhook(request: Request):
            >>>     await WebhookSecurity.verify_webhook_with_timestamp(
            >>>         request,
            >>>         settings.WEBHOOK_SECRET,
            >>>         max_age_seconds=300
            >>>     )
        """
        import time

        # Get signature
        signature = request.headers.get(WebhookSecurity.SIGNATURE_HEADER_256)
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature"
            )

        # Get timestamp
        timestamp_str = request.headers.get(WebhookSecurity.TIMESTAMP_HEADER)
        if not timestamp_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing timestamp"
            )

        # Validate timestamp
        try:
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            age = current_time - timestamp

            if age < 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Webhook timestamp is in the future"
                )

            if age > max_age_seconds:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Webhook is too old (age: {age}s, max: {max_age_seconds}s)"
                )

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format"
            )

        # Verify signature
        body = await request.body()
        is_valid = WebhookSecurity.verify_signature(body, signature, secret)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        return True

    @staticmethod
    def extract_signature_from_header(
        header_value: str,
        prefix: str = "sha256="
    ) -> Optional[str]:
        """
        Extract signature from header value (GitHub-style format).

        Args:
            header_value: Header value (e.g., "sha256=abc123...")
            prefix: Signature prefix (default: "sha256=")

        Returns:
            Extracted signature or None

        Example:
            >>> header = "sha256=a3c5f7e9b2d4f6a8c0e2b4d6f8a0c2e4"
            >>> signature = WebhookSecurity.extract_signature_from_header(header)
            >>> print(signature)
            'a3c5f7e9b2d4f6a8c0e2b4d6f8a0c2e4'
        """
        if not header_value:
            return None

        if header_value.startswith(prefix):
            return header_value[len(prefix):]

        return header_value

    @staticmethod
    def log_webhook_verification(
        event_type: str,
        is_valid: bool,
        source_ip: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log webhook verification result for auditing.

        Args:
            event_type: Type of webhook event
            is_valid: Whether verification succeeded
            source_ip: Source IP address
            error: Error message if validation failed
        """
        if is_valid:
            logger.info(
                f"Webhook verification succeeded: event_type={event_type}, "
                f"source_ip={source_ip}"
            )
        else:
            logger.warning(
                f"Webhook verification failed: event_type={event_type}, "
                f"source_ip={source_ip}, error={error}"
            )
