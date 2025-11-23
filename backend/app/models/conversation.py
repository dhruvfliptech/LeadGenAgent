"""
Conversation Management Models for Email Reply Handling and AI Conversations.

This module provides SQLAlchemy models for managing email conversations,
messages, and AI-generated suggestions for the lead generation system.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
# from pgvector.sqlalchemy import Vector  # Temporarily disabled for MVP demo

from app.models import Base


# Enum definitions
class ConversationStatus(str, PyEnum):
    """Conversation status states."""
    ACTIVE = "active"  # Ongoing conversation
    NEEDS_REPLY = "needs_reply"  # New message received, user needs to respond
    WAITING = "waiting"  # Waiting for lead's response
    ARCHIVED = "archived"  # Conversation completed or archived


class MessageDirection(str, PyEnum):
    """Message direction indicator."""
    INBOUND = "inbound"  # Message from lead to user
    OUTBOUND = "outbound"  # Message from user to lead


class SuggestionStatus(str, PyEnum):
    """AI suggestion status."""
    PENDING = "pending"  # AI suggestion generated, waiting for user action
    APPROVED = "approved"  # User approved and sent
    REJECTED = "rejected"  # User rejected
    EDITED = "edited"  # User edited before sending


class Conversation(Base):
    """
    Conversation model representing an email thread with a lead.

    A conversation is created when the user first contacts a lead and
    continues until archived. It tracks all messages in the thread and
    maintains conversation state.
    """

    __tablename__ = "conversations"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)

    # Foreign key to lead
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Conversation metadata
    subject = Column(Text, nullable=False)  # Email subject line
    status = Column(
        Enum(ConversationStatus, name="conversation_status"),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True
    )

    # Timestamps
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    lead = relationship("Lead", backref="conversations")
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.sent_at"
    )
    ai_suggestions = relationship(
        "AISuggestion",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AISuggestion.created_at.desc()"
    )

    # Composite indexes defined in migration
    __table_args__ = (
        Index('ix_conversations_lead_status_last_message', 'lead_id', 'status', 'last_message_at'),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, lead_id={self.lead_id}, subject='{self.subject[:30]}...', status={self.status.value})>"

    def add_message(
        self,
        direction: MessageDirection,
        content: str,
        sender_email: str,
        recipient_email: str,
        sent_at: Optional[datetime] = None,
        html_content: Optional[str] = None,
        gmail_message_id: Optional[str] = None,
        postmark_message_id: Optional[str] = None,
        gmail_thread_id: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> "ConversationMessage":
        """
        Add a message to the conversation.

        Args:
            direction: Message direction (inbound/outbound)
            content: Plain text message content
            sender_email: Sender's email address
            recipient_email: Recipient's email address
            sent_at: Message timestamp (defaults to now)
            html_content: HTML version of message
            gmail_message_id: Gmail message ID for tracking
            postmark_message_id: Postmark message ID for tracking
            gmail_thread_id: Gmail thread ID for threading
            headers: Email headers dictionary
            attachments: List of attachment metadata

        Returns:
            Created ConversationMessage instance
        """
        message = ConversationMessage(
            conversation_id=self.id,
            direction=direction,
            content=content,
            html_content=html_content,
            sent_at=sent_at or datetime.utcnow(),
            sender_email=sender_email,
            recipient_email=recipient_email,
            gmail_message_id=gmail_message_id,
            postmark_message_id=postmark_message_id,
            gmail_thread_id=gmail_thread_id,
            headers=headers,
            attachments=attachments,
        )

        # Update conversation timestamps
        self.last_message_at = message.sent_at
        self.updated_at = datetime.utcnow()

        # Update status based on message direction
        if direction == MessageDirection.INBOUND:
            self.status = ConversationStatus.NEEDS_REPLY
        elif direction == MessageDirection.OUTBOUND:
            self.status = ConversationStatus.WAITING

        return message

    def get_latest_message(self) -> Optional["ConversationMessage"]:
        """Get the most recent message in the conversation."""
        if self.messages:
            return max(self.messages, key=lambda m: m.sent_at)
        return None

    def get_latest_inbound_message(self) -> Optional["ConversationMessage"]:
        """Get the most recent inbound message (from lead)."""
        inbound_messages = [m for m in self.messages if m.direction == MessageDirection.INBOUND]
        if inbound_messages:
            return max(inbound_messages, key=lambda m: m.sent_at)
        return None

    def get_message_count(self) -> int:
        """Get total number of messages in conversation."""
        return len(self.messages)

    def get_pending_suggestion(self) -> Optional["AISuggestion"]:
        """Get pending AI suggestion if one exists."""
        for suggestion in self.ai_suggestions:
            if suggestion.status == SuggestionStatus.PENDING:
                return suggestion
        return None

    def archive(self):
        """Archive this conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for API responses."""
        latest_message = self.get_latest_message()
        pending_suggestion = self.get_pending_suggestion()

        return {
            'id': str(self.id),
            'lead_id': self.lead_id,
            'lead': {
                'id': self.lead.id,
                'title': self.lead.title,
                'contact_name': self.lead.contact_name or self.lead.reply_contact_name,
                'email': self.lead.email or self.lead.reply_email,
            } if self.lead else None,
            'subject': self.subject,
            'status': self.status.value,
            'message_count': self.get_message_count(),
            'latest_message': {
                'content': latest_message.content[:100] + '...' if len(latest_message.content) > 100 else latest_message.content,
                'direction': latest_message.direction.value,
                'sent_at': latest_message.sent_at.isoformat(),
            } if latest_message else None,
            'has_pending_suggestion': pending_suggestion is not None,
            'pending_suggestion_confidence': pending_suggestion.confidence_score if pending_suggestion else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class ConversationMessage(Base):
    """
    Individual message within a conversation.

    Represents a single email message, either sent by the user (outbound)
    or received from the lead (inbound). Includes vector embeddings for
    semantic search capabilities.
    """

    __tablename__ = "conversation_messages"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)

    # Foreign key to conversation
    conversation_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message metadata
    direction = Column(
        Enum(MessageDirection, name="message_direction"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)  # Plain text content
    html_content = Column(Text, nullable=True)  # HTML content

    # Email metadata
    sent_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sender_email = Column(Text, nullable=False, index=True)
    recipient_email = Column(Text, nullable=False, index=True)

    # Tracking IDs
    gmail_message_id = Column(Text, nullable=True, index=True)
    postmark_message_id = Column(Text, nullable=True, index=True)
    gmail_thread_id = Column(Text, nullable=True, index=True)

    # Additional metadata
    headers = Column(JSONB, nullable=True)  # Email headers
    attachments = Column(JSONB, nullable=True)  # Attachment metadata

    # Vector embedding for semantic search (OpenAI ada-002: 1536 dimensions)
    # embedding = Column(Vector(1536), nullable=True)  # Temporarily disabled for MVP demo

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    ai_suggestions = relationship(
        "AISuggestion",
        back_populates="in_reply_to_message",
        cascade="all, delete-orphan"
    )

    # Composite indexes defined in migration
    __table_args__ = (
        Index('ix_messages_conversation_sent', 'conversation_id', 'sent_at'),
    )

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, conversation_id={self.conversation_id}, direction={self.direction.value}, sent_at={self.sent_at})>"

    def set_embedding(self, embedding: List[float]):
        """
        Set the vector embedding for semantic search.

        Args:
            embedding: List of floats representing the embedding vector
        """
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API responses."""
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'direction': self.direction.value,
            'content': self.content,
            'html_content': self.html_content,
            'sent_at': self.sent_at.isoformat(),
            'sender_email': self.sender_email,
            'recipient_email': self.recipient_email,
            'gmail_message_id': self.gmail_message_id,
            'postmark_message_id': self.postmark_message_id,
            'gmail_thread_id': self.gmail_thread_id,
            'has_attachments': bool(self.attachments),
            'attachment_count': len(self.attachments) if self.attachments else 0,
            'created_at': self.created_at.isoformat(),
        }


class AISuggestion(Base):
    """
    AI-generated reply suggestion for a conversation.

    When a lead replies, the AI analyzes the message and conversation context
    to generate a suggested response. Users can approve, reject, or edit the
    suggestion before sending.
    """

    __tablename__ = "ai_suggestions"

    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)

    # Foreign keys
    conversation_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    in_reply_to_message_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("conversation_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Suggested content
    suggested_content = Column(Text, nullable=False)  # Plain text
    suggested_html_content = Column(Text, nullable=True)  # HTML version

    # AI confidence and analysis
    confidence_score = Column(Float, nullable=False, index=True)  # 0.0 to 1.0
    sentiment_analysis = Column(JSONB, nullable=True)  # Sentiment, intent, tone
    context_used = Column(JSONB, nullable=True)  # What context AI used

    # AI model metadata
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    generation_cost = Column(Float, nullable=True)

    # Status tracking
    status = Column(
        Enum(SuggestionStatus, name="suggestion_status"),
        nullable=False,
        default=SuggestionStatus.PENDING,
        index=True
    )
    user_feedback = Column(Text, nullable=True)  # Why approved/rejected/edited
    edited_content = Column(Text, nullable=True)  # User's edited version

    # Approval metadata
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="ai_suggestions")
    in_reply_to_message = relationship("ConversationMessage", back_populates="ai_suggestions")
    approver = relationship("User", foreign_keys=[approved_by])

    # Composite indexes defined in migration
    __table_args__ = (
        Index('ix_suggestions_conversation_status', 'conversation_id', 'status'),
        # Index(  # Temporarily disabled for MVP demo - enum type issue
        #     'ix_suggestions_unique_pending',
        #     'conversation_id',
        #     'in_reply_to_message_id',
        #     'status',
        #     unique=True,
        #     postgresql_where=Column('status') == 'pending'
        # ),
    )

    def __repr__(self):
        return f"<AISuggestion(id={self.id}, conversation_id={self.conversation_id}, status={self.status.value}, confidence={self.confidence_score:.2f})>"

    def approve(self, user_id: int, feedback: Optional[str] = None):
        """
        Approve the AI suggestion for sending.

        Args:
            user_id: ID of user approving the suggestion
            feedback: Optional feedback about the approval
        """
        self.status = SuggestionStatus.APPROVED
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        if feedback:
            self.user_feedback = feedback
        self.updated_at = datetime.utcnow()

    def reject(self, feedback: Optional[str] = None):
        """
        Reject the AI suggestion.

        Args:
            feedback: Optional feedback about why it was rejected
        """
        self.status = SuggestionStatus.REJECTED
        if feedback:
            self.user_feedback = feedback
        self.updated_at = datetime.utcnow()

    def edit(self, edited_content: str, user_id: int, feedback: Optional[str] = None):
        """
        Mark the suggestion as edited by the user.

        Args:
            edited_content: User's edited version of the content
            user_id: ID of user who edited
            feedback: Optional feedback about the edits
        """
        self.status = SuggestionStatus.EDITED
        self.edited_content = edited_content
        self.approved_by = user_id
        self.approved_at = datetime.utcnow()
        if feedback:
            self.user_feedback = feedback
        self.updated_at = datetime.utcnow()

    def get_confidence_level(self) -> str:
        """
        Get human-readable confidence level.

        Returns:
            String representing confidence level: 'high', 'medium', or 'low'
        """
        if self.confidence_score >= 0.85:
            return 'high'
        elif self.confidence_score >= 0.70:
            return 'medium'
        else:
            return 'low'

    def to_dict(self) -> Dict[str, Any]:
        """Convert AI suggestion to dictionary for API responses."""
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'in_reply_to_message_id': str(self.in_reply_to_message_id),
            'suggested_content': self.suggested_content,
            'suggested_html_content': self.suggested_html_content,
            'confidence_score': self.confidence_score,
            'confidence_level': self.get_confidence_level(),
            'sentiment_analysis': self.sentiment_analysis,
            'context_used': self.context_used,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'generation_cost': self.generation_cost,
            'status': self.status.value,
            'user_feedback': self.user_feedback,
            'edited_content': self.edited_content,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


# Utility functions for common queries
def get_conversations_needing_reply(db: Session, limit: int = 50) -> List[Conversation]:
    """
    Get all conversations that need a reply from the user.

    Args:
        db: Database session
        limit: Maximum number of conversations to return

    Returns:
        List of conversations with status 'needs_reply'
    """
    return db.query(Conversation)\
        .filter(Conversation.status == ConversationStatus.NEEDS_REPLY)\
        .order_by(Conversation.last_message_at.desc())\
        .limit(limit)\
        .all()


def get_pending_ai_suggestions(db: Session, limit: int = 50) -> List[AISuggestion]:
    """
    Get all pending AI suggestions awaiting user approval.

    Args:
        db: Database session
        limit: Maximum number of suggestions to return

    Returns:
        List of pending AI suggestions ordered by creation time
    """
    return db.query(AISuggestion)\
        .filter(AISuggestion.status == SuggestionStatus.PENDING)\
        .order_by(AISuggestion.created_at.desc())\
        .limit(limit)\
        .all()


def find_similar_messages(
    db: Session,
    embedding: List[float],
    limit: int = 10,
    min_similarity: float = 0.7
) -> List[ConversationMessage]:
    """
    Find messages similar to the given embedding using vector similarity.

    Args:
        db: Database session
        embedding: Query embedding vector
        limit: Maximum number of results
        min_similarity: Minimum cosine similarity threshold (0-1)

    Returns:
        List of similar messages ordered by similarity
    """
    # Using cosine distance (1 - cosine_similarity)
    # Lower distance = more similar
    max_distance = 1 - min_similarity

    return db.query(ConversationMessage)\
        .filter(ConversationMessage.embedding.isnot(None))\
        .order_by(ConversationMessage.embedding.cosine_distance(embedding))\
        .filter(ConversationMessage.embedding.cosine_distance(embedding) <= max_distance)\
        .limit(limit)\
        .all()
