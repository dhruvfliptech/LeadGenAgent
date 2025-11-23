"""
LinkedIn Messaging Service

Handles LinkedIn messaging with:
- OAuth 2.0 authentication flow
- Message sending via LinkedIn API
- Rate limiting and queue management
- Message tracking and status updates
- Personalization and templating

Implements LinkedIn's messaging API with proper rate limiting
(~100 messages/day per account).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlencode
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.linkedin_contacts import (
    LinkedInContact,
    LinkedInMessage,
    LinkedInConnection,
)
from app.schemas.linkedin_contacts import (
    LinkedInMessageCreate,
    LinkedInBulkMessageCreate,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkedInMessagingService:
    """
    Service for LinkedIn OAuth authentication and messaging.

    Features:
    - OAuth 2.0 authorization flow
    - Token management and refresh
    - Message sending with rate limiting
    - Queue management for bulk sends
    - Personalization and templating
    """

    # LinkedIn API endpoints
    OAUTH_BASE_URL = "https://www.linkedin.com/oauth/v2"
    API_BASE_URL = "https://api.linkedin.com/v2"

    # OAuth scopes
    DEFAULT_SCOPES = [
        'r_liteprofile',      # Read basic profile
        'w_member_social',     # Send messages
        'r_emailaddress',      # Access email
    ]

    # Rate limiting
    DEFAULT_DAILY_LIMIT = 100
    DEFAULT_RATE_LIMIT_PER_MINUTE = 30

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.client_id = getattr(settings, 'LINKEDIN_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'LINKEDIN_CLIENT_SECRET', None)
        self.redirect_uri = getattr(
            settings,
            'LINKEDIN_REDIRECT_URI',
            'http://localhost:8000/api/v1/linkedin/oauth/callback',
        )
        self.daily_message_limit = getattr(
            settings,
            'LINKEDIN_DAILY_MESSAGE_LIMIT',
            self.DEFAULT_DAILY_LIMIT,
        )
        self.rate_limit_per_minute = getattr(
            settings,
            'LINKEDIN_RATE_LIMIT_PER_MINUTE',
            self.DEFAULT_RATE_LIMIT_PER_MINUTE,
        )

    # ========================================================================
    # OAuth Authentication
    # ========================================================================

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> str:
        """
        Generate LinkedIn OAuth authorization URL.

        Args:
            state: CSRF protection state parameter
            scopes: OAuth scopes to request

        Returns:
            Authorization URL
        """
        if not self.client_id:
            raise ValueError("LINKEDIN_CLIENT_ID not configured")

        if scopes is None:
            scopes = self.DEFAULT_SCOPES

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
        }

        if state:
            params['state'] = state

        return f"{self.OAUTH_BASE_URL}/authorization?{urlencode(params)}"

    async def exchange_code_for_token(
        self,
        code: str,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback

        Returns:
            Token response with access_token, expires_in, etc.
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn OAuth credentials not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.OAUTH_BASE_URL}/accessToken",
                    data={
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': self.redirect_uri,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"Failed to exchange code for token: {str(e)}")
                raise

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn OAuth credentials not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.OAUTH_BASE_URL}/accessToken",
                    data={
                        'grant_type': 'refresh_token',
                        'refresh_token': refresh_token,
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                    },
                    headers={'Content-Type': 'application/x-www-form-urlencoded'},
                )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"Failed to refresh access token: {str(e)}")
                raise

    async def get_profile_info(
        self,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Get LinkedIn profile information.

        Args:
            access_token: LinkedIn access token

        Returns:
            Profile information
        """
        async with httpx.AsyncClient() as client:
            try:
                # Get basic profile
                profile_response = await client.get(
                    f"{self.API_BASE_URL}/me",
                    headers={'Authorization': f'Bearer {access_token}'},
                )
                profile_response.raise_for_status()
                profile = profile_response.json()

                # Get email
                email_response = await client.get(
                    f"{self.API_BASE_URL}/emailAddress?q=members&projection=(elements*(handle~))",
                    headers={'Authorization': f'Bearer {access_token}'},
                )
                email_response.raise_for_status()
                email_data = email_response.json()

                # Extract email
                email = None
                if 'elements' in email_data and email_data['elements']:
                    email = email_data['elements'][0].get('handle~', {}).get('emailAddress')

                return {
                    'id': profile.get('id'),
                    'first_name': profile.get('localizedFirstName'),
                    'last_name': profile.get('localizedLastName'),
                    'email': email,
                    'profile_url': f"https://www.linkedin.com/in/{profile.get('vanityName', '')}",
                }

            except httpx.HTTPError as e:
                logger.error(f"Failed to get profile info: {str(e)}")
                raise

    async def create_connection(
        self,
        code: str,
        account_name: Optional[str] = None,
    ) -> LinkedInConnection:
        """
        Create LinkedIn connection from OAuth callback.

        Args:
            code: Authorization code
            account_name: Optional friendly name

        Returns:
            LinkedInConnection object
        """
        # Exchange code for token
        token_response = await self.exchange_code_for_token(code)

        access_token = token_response['access_token']
        expires_in = token_response.get('expires_in', 5184000)  # Default 60 days
        refresh_token = token_response.get('refresh_token')

        # Get profile info
        profile = await self.get_profile_info(access_token)

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Create connection
        connection = LinkedInConnection(
            linkedin_user_id=profile['id'],
            account_name=account_name or profile.get('email', 'LinkedIn Account'),
            profile_email=profile.get('email'),
            profile_name=f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
            profile_url=profile.get('profile_url'),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='Bearer',
            expires_at=expires_at,
            scope=' '.join(self.DEFAULT_SCOPES),
            is_active=True,
            is_valid=True,
            last_validated_at=datetime.utcnow(),
            connected_at=datetime.utcnow(),
        )

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Created LinkedIn connection: {connection.id}")
        return connection

    async def validate_connection(
        self,
        connection_id: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate LinkedIn connection and token.

        Args:
            connection_id: Connection ID

        Returns:
            Tuple of (is_valid, error_message)
        """
        connection = self.db.query(LinkedInConnection).get(connection_id)
        if not connection:
            return False, "Connection not found"

        # Check if token is expired
        if connection.is_token_expired:
            # Try to refresh
            if connection.refresh_token:
                try:
                    token_response = await self.refresh_access_token(
                        connection.refresh_token
                    )

                    connection.access_token = token_response['access_token']
                    connection.expires_at = datetime.utcnow() + timedelta(
                        seconds=token_response.get('expires_in', 5184000)
                    )
                    connection.is_valid = True
                    connection.last_validated_at = datetime.utcnow()

                    self.db.commit()
                    logger.info(f"Refreshed token for connection {connection_id}")

                except Exception as e:
                    connection.is_valid = False
                    connection.last_error = str(e)
                    self.db.commit()
                    return False, f"Token refresh failed: {str(e)}"
            else:
                connection.is_valid = False
                connection.last_error = "Token expired, no refresh token available"
                self.db.commit()
                return False, "Token expired"

        # Validate by making test API call
        try:
            await self.get_profile_info(connection.access_token)
            connection.is_valid = True
            connection.last_validated_at = datetime.utcnow()
            connection.error_count = 0
            connection.last_error = None
            self.db.commit()
            return True, None

        except Exception as e:
            connection.is_valid = False
            connection.last_error = str(e)
            connection.error_count += 1
            self.db.commit()
            return False, str(e)

    def get_active_connection(self) -> Optional[LinkedInConnection]:
        """
        Get the first active and valid LinkedIn connection.

        Returns:
            LinkedInConnection or None
        """
        return self.db.query(LinkedInConnection).filter(
            and_(
                LinkedInConnection.is_active == True,
                LinkedInConnection.is_valid == True,
            )
        ).first()

    # ========================================================================
    # Message Sending
    # ========================================================================

    async def send_message(
        self,
        contact_id: int,
        message_create: LinkedInMessageCreate,
        connection: Optional[LinkedInConnection] = None,
    ) -> LinkedInMessage:
        """
        Send message to LinkedIn contact.

        Args:
            contact_id: Contact ID
            message_create: Message data
            connection: Optional specific connection to use

        Returns:
            LinkedInMessage object
        """
        # Get contact
        contact = self.db.query(LinkedInContact).get(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        if not contact.can_send_message:
            raise ValueError(f"Cannot send message to contact {contact_id}")

        # Get connection
        if connection is None:
            connection = self.get_active_connection()
            if not connection:
                raise ValueError("No active LinkedIn connection available")

        # Check rate limits
        if not await self._check_rate_limits(connection):
            raise ValueError("Rate limit exceeded")

        # Personalize message
        message_content = self._personalize_message(
            message_create.message_content,
            contact,
            message_create.personalized_fields,
        )

        # Create message record
        message = LinkedInMessage(
            contact_id=contact_id,
            subject=message_create.subject,
            message_content=message_content,
            message_type=message_create.message_type,
            campaign_id=message_create.campaign_id,
            template_id=message_create.template_id,
            personalized_fields=message_create.personalized_fields,
            status='pending',
            scheduled_for=message_create.scheduled_for or datetime.utcnow(),
            priority=message_create.priority,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # Send via LinkedIn API
        try:
            linkedin_message_id = await self._send_via_api(
                connection,
                contact,
                message,
            )

            # Update message status
            message.linkedin_message_id = linkedin_message_id
            message.status = 'sent'
            message.sent_at = datetime.utcnow()

            # Update contact
            contact.last_messaged_at = datetime.utcnow()
            contact.total_messages_sent += 1
            contact.last_message_status = 'sent'

            # Update connection stats
            connection.daily_messages_sent += 1
            connection.total_messages_sent += 1
            connection.last_used_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Sent message {message.id} to contact {contact_id}")
            return message

        except Exception as e:
            # Update message status
            message.status = 'failed'
            message.failed_at = datetime.utcnow()
            message.error_message = str(e)

            contact.last_message_status = 'failed'

            self.db.commit()

            logger.error(f"Failed to send message {message.id}: {str(e)}")
            raise

    async def send_bulk_messages(
        self,
        bulk_request: LinkedInBulkMessageCreate,
    ) -> List[LinkedInMessage]:
        """
        Send messages to multiple contacts.

        Args:
            bulk_request: Bulk message request

        Returns:
            List of created message objects
        """
        messages = []

        for idx, contact_id in enumerate(bulk_request.contact_ids):
            try:
                # Add stagger delay
                if idx > 0:
                    await asyncio.sleep(bulk_request.stagger_minutes * 60)

                # Create message for contact
                message_create = LinkedInMessageCreate(
                    contact_id=contact_id,
                    subject=bulk_request.subject,
                    message_content=bulk_request.message_content,
                    message_type=bulk_request.message_type,
                    campaign_id=bulk_request.campaign_id,
                    template_id=bulk_request.template_id,
                    personalized_fields={},
                    scheduled_for=bulk_request.scheduled_for,
                )

                message = await self.send_message(contact_id, message_create)
                messages.append(message)

            except Exception as e:
                logger.error(f"Failed to send message to contact {contact_id}: {str(e)}")
                # Continue with next contact

        return messages

    async def _send_via_api(
        self,
        connection: LinkedInConnection,
        contact: LinkedInContact,
        message: LinkedInMessage,
    ) -> str:
        """
        Send message via LinkedIn API.

        Args:
            connection: LinkedIn connection
            contact: Contact to message
            message: Message object

        Returns:
            LinkedIn message ID
        """
        # Note: This is a placeholder implementation
        # LinkedIn's messaging API requires specific endpoints and payload format
        # Actual implementation would use LinkedIn's UGC (User Generated Content) API

        async with httpx.AsyncClient() as client:
            try:
                # Example payload structure (adjust based on actual API)
                payload = {
                    'author': f'urn:li:person:{connection.linkedin_user_id}',
                    'lifecycleState': 'PUBLISHED',
                    'specificContent': {
                        'com.linkedin.ugc.ShareContent': {
                            'shareCommentary': {
                                'text': message.message_content,
                            },
                            'shareMediaCategory': 'NONE',
                        }
                    },
                    'visibility': {
                        'com.linkedin.ugc.MemberNetworkVisibility': 'CONNECTIONS'
                    },
                }

                response = await client.post(
                    f"{self.API_BASE_URL}/ugcPosts",
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {connection.access_token}',
                        'Content-Type': 'application/json',
                        'X-Restli-Protocol-Version': '2.0.0',
                    },
                )

                response.raise_for_status()
                result = response.json()

                # Extract message ID from response
                message_id = result.get('id', f'linkedin_{message.id}')
                return message_id

            except httpx.HTTPError as e:
                logger.error(f"LinkedIn API error: {str(e)}")
                raise

    def _personalize_message(
        self,
        template: str,
        contact: LinkedInContact,
        custom_fields: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Personalize message template with contact data.

        Args:
            template: Message template
            contact: Contact object
            custom_fields: Custom personalization fields

        Returns:
            Personalized message
        """
        replacements = {
            '{{first_name}}': contact.first_name,
            '{{last_name}}': contact.last_name,
            '{{full_name}}': contact.full_name,
            '{{company}}': contact.company or '',
            '{{position}}': contact.position or '',
            '{{industry}}': contact.industry or '',
            '{{location}}': contact.location or '',
        }

        # Add custom fields
        if custom_fields:
            for key, value in custom_fields.items():
                replacements[f'{{{{{key}}}}}'] = value

        # Replace all placeholders
        message = template
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)

        return message

    async def _check_rate_limits(
        self,
        connection: LinkedInConnection,
    ) -> bool:
        """
        Check if rate limits allow sending.

        Args:
            connection: LinkedIn connection

        Returns:
            True if can send, False otherwise
        """
        # Reset daily counter if needed
        if connection.daily_limit_reset_at:
            if datetime.utcnow() >= connection.daily_limit_reset_at:
                connection.daily_messages_sent = 0
                connection.daily_limit_reset_at = None
                connection.rate_limit_exceeded = False
                self.db.commit()

        # Check daily limit
        if connection.daily_messages_sent >= self.daily_message_limit:
            connection.rate_limit_exceeded = True
            connection.daily_limit_reset_at = (
                datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1)
            )
            self.db.commit()
            return False

        return True

    # ========================================================================
    # Message Queue Management
    # ========================================================================

    async def get_pending_messages(
        self,
        limit: int = 100,
    ) -> List[LinkedInMessage]:
        """
        Get pending messages ready to send.

        Args:
            limit: Maximum messages to return

        Returns:
            List of pending messages
        """
        now = datetime.utcnow()

        return (
            self.db.query(LinkedInMessage)
            .filter(
                and_(
                    LinkedInMessage.status == 'pending',
                    or_(
                        LinkedInMessage.scheduled_for.is_(None),
                        LinkedInMessage.scheduled_for <= now,
                    ),
                )
            )
            .order_by(
                LinkedInMessage.priority.desc(),
                LinkedInMessage.scheduled_for.asc(),
            )
            .limit(limit)
            .all()
        )

    async def process_message_queue(self) -> Dict[str, int]:
        """
        Process pending message queue.

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'processed': 0,
            'sent': 0,
            'failed': 0,
            'rate_limited': 0,
        }

        connection = self.get_active_connection()
        if not connection:
            logger.warning("No active LinkedIn connection for message processing")
            return stats

        pending_messages = await self.get_pending_messages()

        for message in pending_messages:
            stats['processed'] += 1

            # Check rate limits
            if not await self._check_rate_limits(connection):
                stats['rate_limited'] += 1
                break

            try:
                # Send message
                message_create = LinkedInMessageCreate(
                    contact_id=message.contact_id,
                    subject=message.subject,
                    message_content=message.message_content,
                    message_type=message.message_type,
                    campaign_id=message.campaign_id,
                    template_id=message.template_id,
                    personalized_fields=message.personalized_fields,
                )

                await self.send_message(
                    message.contact_id,
                    message_create,
                    connection=connection,
                )

                stats['sent'] += 1

                # Add delay between messages
                await asyncio.sleep(60 / self.rate_limit_per_minute)

            except Exception as e:
                stats['failed'] += 1
                logger.error(f"Failed to process message {message.id}: {str(e)}")

        logger.info(f"Message queue processing complete: {stats}")
        return stats
