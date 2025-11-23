"""
Gmail monitoring service for tracking email replies.
Polls Gmail inbox, matches replies to sent emails, and triggers AI response generation.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.integrations.gmail_client import GmailClient
from app.models.conversation import (
    Conversation, ConversationMessage, AISuggestion,
    ConversationStatus, MessageDirection, SuggestionStatus
)
from app.models.leads import Lead
from app.core.config import settings

logger = logging.getLogger(__name__)


class GmailMonitorService:
    """
    Background service that monitors Gmail for new email replies.
    Matches incoming emails to existing conversations and triggers AI replies.
    """

    def __init__(self):
        self.gmail_client: Optional[GmailClient] = None
        self.is_running = False
        self.last_check: Optional[datetime] = None
        self._monitor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """
        Initialize Gmail client and authenticate.

        Returns:
            bool: True if initialization successful
        """
        try:
            if not settings.GMAIL_ENABLED:
                logger.warning("Gmail monitoring is disabled (GMAIL_ENABLED=False)")
                return False

            if not settings.GMAIL_CREDENTIALS_PATH:
                logger.error("GMAIL_CREDENTIALS_PATH not configured")
                return False

            logger.info("Initializing Gmail client...")
            self.gmail_client = GmailClient(
                credentials_path=settings.GMAIL_CREDENTIALS_PATH,
                token_path=settings.GMAIL_TOKEN_PATH
            )

            # Authenticate
            self.gmail_client.authenticate()

            logger.info("Gmail client initialized and authenticated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Gmail client: {e}")
            return False

    async def start_monitoring(self):
        """
        Start the background monitoring loop.
        Runs continuously, checking for new emails every GMAIL_POLL_INTERVAL seconds.
        """
        if self.is_running:
            logger.warning("Gmail monitoring already running")
            return

        if not await self.initialize():
            logger.error("Cannot start monitoring: initialization failed")
            return

        self.is_running = True
        logger.info(f"Starting Gmail monitoring (poll interval: {settings.GMAIL_POLL_INTERVAL}s)")

        # Create background task
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop the background monitoring loop."""
        if not self.is_running:
            return

        logger.info("Stopping Gmail monitoring...")
        self.is_running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("Gmail monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop that runs in the background."""
        while self.is_running:
            try:
                await self.check_for_new_emails()

                # Sleep until next check
                await asyncio.sleep(settings.GMAIL_POLL_INTERVAL)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                # Continue running even on error
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def check_for_new_emails(self):
        """
        Check Gmail for new emails and process them.
        This is the main entry point called by the monitoring loop.
        """
        try:
            # Determine time window
            since = self.last_check or (datetime.utcnow() - timedelta(minutes=settings.GMAIL_POLL_INTERVAL // 60))

            logger.info(f"Checking for new emails since {since}")

            # Fetch new emails (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                lambda: self.gmail_client.fetch_new_emails(
                    since=since,
                    query=f"to:{self.gmail_client.user_email} is:unread"
                )
            )

            if not emails:
                logger.info("No new emails found")
                self.last_check = datetime.utcnow()
                return

            logger.info(f"Found {len(emails)} new emails, processing...")

            # Process each email
            async for session in get_async_session():
                for email_data in emails:
                    try:
                        await self._process_incoming_email(session, email_data)
                    except Exception as e:
                        logger.error(f"Error processing email {email_data.get('gmail_message_id')}: {e}")

                await session.commit()

            self.last_check = datetime.utcnow()
            logger.info(f"Processed {len(emails)} emails successfully")

        except Exception as e:
            logger.error(f"Error checking for new emails: {e}", exc_info=True)

    async def _process_incoming_email(self, session: AsyncSession, email_data: Dict):
        """
        Process a single incoming email.

        Args:
            session: Database session
            email_data: Parsed email data from Gmail client
        """
        try:
            sender_email = email_data['sender']['email'].lower()
            message_id = email_data['message_id']
            in_reply_to = email_data.get('in_reply_to')

            logger.info(f"Processing email from {sender_email}, Message-ID: {message_id}")

            # Try to match to existing conversation
            conversation = await self._find_conversation(session, sender_email, in_reply_to, email_data)

            if not conversation:
                logger.info(f"No matching conversation found for {sender_email}, creating new conversation")
                conversation = await self._create_conversation_from_email(session, email_data)

                if not conversation:
                    logger.warning(f"Could not create conversation for email from {sender_email}")
                    return

            # Save the incoming message
            message = await self._save_incoming_message(session, conversation, email_data)

            # Update conversation status
            conversation.status = ConversationStatus.NEEDS_REPLY
            conversation.last_message_at = message.sent_at
            conversation.last_inbound_at = message.sent_at
            conversation.message_count += 1

            await session.commit()

            logger.info(f"Saved incoming message for conversation {conversation.id}")

            # Trigger AI reply generation (async, non-blocking)
            asyncio.create_task(self._generate_ai_reply(conversation.id, message.id))

            # Mark as read in Gmail
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.gmail_client.mark_as_read(email_data['gmail_message_id'])
            )

            # Send WebSocket notification
            await self._send_notification(conversation, message)

        except Exception as e:
            logger.error(f"Error processing incoming email: {e}", exc_info=True)
            raise

    async def _find_conversation(
        self,
        session: AsyncSession,
        sender_email: str,
        in_reply_to: str,
        email_data: Dict
    ) -> Optional[Conversation]:
        """
        Find existing conversation for this email.

        Args:
            session: Database session
            sender_email: Sender's email address
            in_reply_to: In-Reply-To header
            email_data: Full email data

        Returns:
            Conversation or None
        """
        # Strategy 1: Match by In-Reply-To header
        if in_reply_to:
            result = await session.execute(
                select(Conversation)
                .join(ConversationMessage)
                .where(ConversationMessage.message_id == in_reply_to)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                logger.info(f"Matched conversation by In-Reply-To header: {conversation.id}")
                return conversation

        # Strategy 2: Match by Gmail thread ID
        gmail_thread_id = email_data.get('gmail_thread_id')
        if gmail_thread_id:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.gmail_thread_id == gmail_thread_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                logger.info(f"Matched conversation by Gmail thread ID: {conversation.id}")
                return conversation

        # Strategy 3: Match by sender email (most recent active conversation)
        result = await session.execute(
            select(Conversation)
            .join(Lead)
            .where(
                and_(
                    or_(
                        Lead.email == sender_email,
                        Lead.reply_email == sender_email
                    ),
                    Conversation.status != ConversationStatus.ARCHIVED
                )
            )
            .order_by(Conversation.last_message_at.desc())
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            logger.info(f"Matched conversation by sender email: {conversation.id}")
            return conversation

        return None

    async def _create_conversation_from_email(
        self,
        session: AsyncSession,
        email_data: Dict
    ) -> Optional[Conversation]:
        """
        Create a new conversation from an incoming email.
        This happens when someone emails us who we haven't contacted yet.

        Args:
            session: Database session
            email_data: Parsed email data

        Returns:
            New Conversation or None if no matching lead
        """
        sender_email = email_data['sender']['email'].lower()

        # Find matching lead
        result = await session.execute(
            select(Lead).where(
                or_(
                    Lead.email == sender_email,
                    Lead.reply_email == sender_email
                )
            )
        )
        lead = result.scalar_one_or_none()

        if not lead:
            logger.warning(f"No lead found for email {sender_email}")
            return None

        # Create conversation
        conversation = Conversation(
            lead_id=lead.id,
            subject=email_data['subject'],
            original_message_id=email_data['message_id'],
            gmail_thread_id=email_data.get('gmail_thread_id'),
            status=ConversationStatus.NEEDS_REPLY,
            last_message_at=email_data['timestamp'],
            last_inbound_at=email_data['timestamp'],
            message_count=0
        )

        session.add(conversation)
        await session.flush()

        logger.info(f"Created new conversation {conversation.id} for lead {lead.id}")
        return conversation

    async def _save_incoming_message(
        self,
        session: AsyncSession,
        conversation: Conversation,
        email_data: Dict
    ) -> ConversationMessage:
        """
        Save incoming email as a conversation message.

        Args:
            session: Database session
            conversation: Conversation to add message to
            email_data: Parsed email data

        Returns:
            ConversationMessage
        """
        message = ConversationMessage(
            conversation_id=conversation.id,
            direction=MessageDirection.INBOUND,
            message_id=email_data['message_id'],
            in_reply_to=email_data.get('in_reply_to'),
            references=email_data.get('references'),
            sender_email=email_data['sender']['email'],
            sender_name=email_data['sender']['name'],
            recipient_email=email_data['recipients']['email'],
            recipient_name=email_data['recipients']['name'],
            subject=email_data['subject'],
            body_text=email_data['body_text'],
            body_html=email_data['body_html'],
            gmail_message_id=email_data['gmail_message_id'],
            gmail_thread_id=email_data.get('gmail_thread_id'),
            sent_at=email_data['timestamp'],
            is_read=False
        )

        session.add(message)
        await session.flush()

        return message

    async def _generate_ai_reply(self, conversation_id: int, message_id: int):
        """
        Generate AI reply suggestion for a new message.
        Runs asynchronously to avoid blocking.

        Args:
            conversation_id: Conversation ID
            message_id: Message ID to reply to
        """
        try:
            logger.info(f"Generating AI reply for conversation {conversation_id}, message {message_id}")

            # Import here to avoid circular dependency
            from app.services.ai_reply_generator import AIReplyGenerator

            async for session in get_async_session():
                generator = AIReplyGenerator()
                suggestion = await generator.generate_reply(
                    session=session,
                    conversation_id=conversation_id,
                    message_id=message_id
                )

                if suggestion:
                    logger.info(f"Generated AI suggestion {suggestion.id} with confidence {suggestion.confidence_score}")

                    # Send WebSocket notification about AI suggestion
                    await self._send_ai_suggestion_notification(conversation_id, suggestion.id)
                else:
                    logger.warning(f"Failed to generate AI reply for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error generating AI reply: {e}", exc_info=True)

    async def _send_notification(self, conversation: Conversation, message: ConversationMessage):
        """
        Send WebSocket notification about new reply.

        Args:
            conversation: Conversation
            message: New message
        """
        try:
            from app.api.endpoints.websocket import manager

            notification = {
                'type': 'conversation:new_reply',
                'data': {
                    'conversation_id': conversation.id,
                    'message_id': message.id,
                    'sender': {
                        'email': message.sender_email,
                        'name': message.sender_name
                    },
                    'subject': conversation.subject,
                    'snippet': message.body_text[:100] if message.body_text else '',
                    'timestamp': message.sent_at.isoformat()
                }
            }

            await manager.broadcast(notification)
            logger.info(f"Sent WebSocket notification for conversation {conversation.id}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def _send_ai_suggestion_notification(self, conversation_id: int, suggestion_id: int):
        """
        Send WebSocket notification about AI suggestion being ready.

        Args:
            conversation_id: Conversation ID
            suggestion_id: AI suggestion ID
        """
        try:
            from app.api.endpoints.websocket import manager

            notification = {
                'type': 'conversation:ai_ready',
                'data': {
                    'conversation_id': conversation_id,
                    'suggestion_id': suggestion_id
                }
            }

            await manager.broadcast(notification)
            logger.info(f"Sent AI suggestion notification for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error sending AI suggestion notification: {e}")

    async def process_sent_email(
        self,
        session: AsyncSession,
        lead_id: int,
        subject: str,
        body: str,
        message_id: str = None,
        postmark_message_id: str = None
    ) -> Conversation:
        """
        Record a sent email as the start of a conversation.
        Called when user sends an email via the Leads page.

        Args:
            session: Database session
            lead_id: Lead ID
            subject: Email subject
            body: Email body
            message_id: Email Message-ID header
            postmark_message_id: Postmark message ID

        Returns:
            Conversation
        """
        try:
            # Get lead
            result = await session.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                raise ValueError(f"Lead {lead_id} not found")

            # Create conversation
            conversation = Conversation(
                lead_id=lead_id,
                subject=subject,
                original_message_id=message_id,
                status=ConversationStatus.WAITING,
                last_message_at=datetime.utcnow(),
                last_outbound_at=datetime.utcnow(),
                message_count=1
            )

            session.add(conversation)
            await session.flush()

            # Create outbound message
            user_email = settings.USER_EMAIL or settings.SMTP_FROM_EMAIL
            message = ConversationMessage(
                conversation_id=conversation.id,
                direction=MessageDirection.OUTBOUND,
                message_id=message_id,
                sender_email=user_email,
                sender_name=settings.USER_NAME or user_email,
                recipient_email=lead.email or lead.reply_email,
                recipient_name=lead.contact_name,
                subject=subject,
                body_text=body,
                postmark_message_id=postmark_message_id,
                sent_at=datetime.utcnow(),
                is_read=True
            )

            session.add(message)
            await session.commit()

            logger.info(f"Created conversation {conversation.id} for sent email to lead {lead_id}")

            return conversation

        except Exception as e:
            logger.error(f"Error processing sent email: {e}", exc_info=True)
            raise


# Global instance
gmail_monitor = GmailMonitorService()
