"""Create conversation management tables

Revision ID: 014
Revises: 013
Create Date: 2025-11-04 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    """Create conversation management tables."""

    # Create enum types for conversations
    conversation_status_enum = sa.Enum(
        'active', 'needs_reply', 'waiting', 'archived',
        name='conversation_status',
        create_type=True
    )

    message_direction_enum = sa.Enum(
        'inbound', 'outbound',
        name='message_direction',
        create_type=True
    )

    suggestion_status_enum = sa.Enum(
        'pending', 'approved', 'rejected', 'edited',
        name='suggestion_status',
        create_type=True
    )

    # 1. Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('status', conversation_status_enum, nullable=False, server_default='active'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for conversations
    op.create_index('ix_conversations_lead_id', 'conversations', ['lead_id'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])

    # Composite index for common query patterns
    op.create_index(
        'ix_conversations_lead_status_last_message',
        'conversations',
        ['lead_id', 'status', 'last_message_at']
    )

    # 2. Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False),
        sa.Column('direction', message_direction_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sender_email', sa.Text(), nullable=False),
        sa.Column('recipient_email', sa.Text(), nullable=False),

        # Email tracking IDs
        sa.Column('gmail_message_id', sa.Text(), nullable=True),
        sa.Column('postmark_message_id', sa.Text(), nullable=True),
        sa.Column('gmail_thread_id', sa.Text(), nullable=True),

        # Metadata
        sa.Column('headers', JSONB, nullable=True),  # Email headers for tracking
        sa.Column('attachments', JSONB, nullable=True),  # Array of attachment metadata

        # Vector embedding for semantic search (using pgvector)
        sa.Column('embedding', Vector(1536), nullable=True),  # OpenAI ada-002 embeddings are 1536 dimensions

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        # Foreign key constraint
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for conversation_messages
    op.create_index('ix_messages_conversation_id', 'conversation_messages', ['conversation_id'])
    op.create_index('ix_messages_sent_at', 'conversation_messages', ['sent_at'])
    op.create_index('ix_messages_direction', 'conversation_messages', ['direction'])
    op.create_index('ix_messages_sender_email', 'conversation_messages', ['sender_email'])
    op.create_index('ix_messages_recipient_email', 'conversation_messages', ['recipient_email'])
    op.create_index('ix_messages_gmail_message_id', 'conversation_messages', ['gmail_message_id'])
    op.create_index('ix_messages_postmark_message_id', 'conversation_messages', ['postmark_message_id'])
    op.create_index('ix_messages_gmail_thread_id', 'conversation_messages', ['gmail_thread_id'])

    # Composite index for common query patterns
    op.create_index(
        'ix_messages_conversation_sent',
        'conversation_messages',
        ['conversation_id', 'sent_at']
    )

    # Vector similarity search index (IVFFlat for better performance on large datasets)
    # Using cosine distance as it's normalized and works well for embeddings
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_messages_embedding_cosine '
        'ON conversation_messages USING ivfflat (embedding vector_cosine_ops) '
        'WITH (lists = 100)'
    )

    # 3. Create ai_suggestions table
    op.create_table(
        'ai_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=False),
        sa.Column('in_reply_to_message_id', UUID(as_uuid=True), nullable=False),
        sa.Column('suggested_content', sa.Text(), nullable=False),
        sa.Column('suggested_html_content', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),  # 0.0 to 1.0

        # AI analysis metadata
        sa.Column('sentiment_analysis', JSONB, nullable=True),  # Sentiment, intent, tone analysis
        sa.Column('context_used', JSONB, nullable=True),  # What context AI used to generate
        sa.Column('model_used', sa.String(100), nullable=True),  # AI model identifier
        sa.Column('tokens_used', sa.Integer(), nullable=True),  # Token usage tracking
        sa.Column('generation_cost', sa.Float(), nullable=True),  # Cost in USD

        # Status tracking
        sa.Column('status', suggestion_status_enum, nullable=False, server_default='pending'),
        sa.Column('user_feedback', sa.Text(), nullable=True),  # Why approved/rejected/edited
        sa.Column('edited_content', sa.Text(), nullable=True),  # User's edited version
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),  # User ID who approved

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Foreign key constraints
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['in_reply_to_message_id'], ['conversation_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ai_suggestions
    op.create_index('ix_suggestions_conversation_id', 'ai_suggestions', ['conversation_id'])
    op.create_index('ix_suggestions_in_reply_to', 'ai_suggestions', ['in_reply_to_message_id'])
    op.create_index('ix_suggestions_status', 'ai_suggestions', ['status'])
    op.create_index('ix_suggestions_confidence_score', 'ai_suggestions', ['confidence_score'])
    op.create_index('ix_suggestions_created_at', 'ai_suggestions', ['created_at'])
    op.create_index('ix_suggestions_approved_by', 'ai_suggestions', ['approved_by'])

    # Composite index for common query patterns
    op.create_index(
        'ix_suggestions_conversation_status',
        'ai_suggestions',
        ['conversation_id', 'status']
    )

    # Add unique constraint to prevent duplicate pending suggestions
    op.create_index(
        'ix_suggestions_unique_pending',
        'ai_suggestions',
        ['conversation_id', 'in_reply_to_message_id', 'status'],
        unique=True,
        postgresql_where=sa.text("status = 'pending'")
    )


def downgrade():
    """Drop conversation management tables."""
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('ai_suggestions')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')

    # Drop enum types
    sa.Enum(name='suggestion_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='message_direction').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='conversation_status').drop(op.get_bind(), checkfirst=True)
