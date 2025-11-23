"""
Add memory and context management tables.

Revision ID: 010
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010'
down_revision = '009'


def upgrade():
    """Create memory and context tables."""
    
    # Create conversation_memory table
    op.create_table(
        'conversation_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Conversation identification
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        
        # Lead context
        sa.Column('lead_id', sa.Integer(), nullable=True),
        
        # Message content
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('message_content', sa.Text(), nullable=False),
        
        # Context at time of message
        sa.Column('context_snapshot', postgresql.JSON(), nullable=True),
        sa.Column('active_leads', postgresql.JSON(), nullable=True),
        sa.Column('active_templates', postgresql.JSON(), nullable=True),
        
        # Extracted entities and intents
        sa.Column('entities', postgresql.JSON(), nullable=True),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('sentiment', sa.Float(), nullable=True),
        
        # Memory importance
        sa.Column('importance_score', sa.Float(), default=0.5),
        sa.Column('is_milestone', sa.Boolean(), default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], )
    )
    
    # Create indexes for conversation_memory
    op.create_index('ix_conversation_memory_session_id', 'conversation_memory', ['session_id'])
    op.create_index('ix_conversation_memory_user_id', 'conversation_memory', ['user_id'])
    op.create_index('ix_conversation_memory_created_at', 'conversation_memory', ['created_at'])
    
    # Create short_term_memory table
    op.create_table(
        'short_term_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Session identification
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        
        # Current context
        sa.Column('current_leads', postgresql.JSON(), nullable=True),
        sa.Column('current_task', sa.String(200), nullable=True),
        sa.Column('current_step', sa.String(200), nullable=True),
        
        # Working memory
        sa.Column('working_memory', postgresql.JSON(), nullable=True),
        sa.Column('decision_stack', postgresql.JSON(), nullable=True),
        
        # User preferences learned in session
        sa.Column('session_preferences', postgresql.JSON(), nullable=True),
        
        # Statistics
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('decision_count', sa.Integer(), default=0),
        sa.Column('leads_processed', sa.Integer(), default=0),
        
        # Session state
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create indexes for short_term_memory
    op.create_index('ix_short_term_memory_session_id', 'short_term_memory', ['session_id'])
    op.create_index('ix_short_term_memory_is_active', 'short_term_memory', ['is_active'])
    
    # Create long_term_memory table
    op.create_table(
        'long_term_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # User identification
        sa.Column('user_id', sa.String(100), nullable=True),
        
        # Memory type
        sa.Column('memory_type', sa.String(50), nullable=False),
        sa.Column('memory_category', sa.String(100), nullable=True),
        
        # Memory content
        sa.Column('memory_key', sa.String(200), nullable=False),
        sa.Column('memory_value', postgresql.JSON(), nullable=False),
        
        # Metadata
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('frequency', sa.Integer(), default=1),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_count', sa.Integer(), default=0),
        
        # Decay and reinforcement
        sa.Column('strength', sa.Float(), default=1.0),
        sa.Column('reinforcement_count', sa.Integer(), default=0),
        
        # Source tracking
        sa.Column('source_sessions', postgresql.JSON(), nullable=True),
        sa.Column('source_leads', postgresql.JSON(), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for long_term_memory
    op.create_index('ix_long_term_memory_user_key', 'long_term_memory', ['user_id', 'memory_key'])
    op.create_index('ix_long_term_memory_type_category', 'long_term_memory', ['memory_type', 'memory_category'])
    op.create_index('ix_long_term_memory_is_active', 'long_term_memory', ['is_active'])
    
    # Create semantic_memory table
    op.create_table(
        'semantic_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Content identification
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', sa.String(200), nullable=False),
        
        # Semantic representation
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('embedding_vector', postgresql.JSON(), nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        
        # Semantic metadata
        sa.Column('topics', postgresql.JSON(), nullable=True),
        sa.Column('keywords', postgresql.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        
        # Relationships
        sa.Column('similar_items', postgresql.JSON(), nullable=True),
        sa.Column('cluster_id', sa.String(100), nullable=True),
        
        # Usage tracking
        sa.Column('retrieval_count', sa.Integer(), default=0),
        sa.Column('last_retrieved', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for semantic_memory
    op.create_index('ix_semantic_memory_content', 'semantic_memory', ['content_type', 'content_id'])
    op.create_index('ix_semantic_memory_cluster', 'semantic_memory', ['cluster_id'])
    
    # Create episodic_memory table
    op.create_table(
        'episodic_memory',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Episode identification
        sa.Column('episode_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=True),
        
        # Episode context
        sa.Column('episode_type', sa.String(50), nullable=False),
        sa.Column('lead_ids', postgresql.JSON(), nullable=True),
        
        # Episode narrative
        sa.Column('episode_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('episode_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        
        # Actions and outcomes
        sa.Column('actions_taken', postgresql.JSON(), nullable=False),
        sa.Column('final_outcome', sa.String(100), nullable=True),
        sa.Column('outcome_details', postgresql.JSON(), nullable=True),
        
        # Learning from episode
        sa.Column('lessons_learned', postgresql.JSON(), nullable=True),
        sa.Column('mistakes_made', postgresql.JSON(), nullable=True),
        sa.Column('successes', postgresql.JSON(), nullable=True),
        
        # Emotional and qualitative aspects
        sa.Column('user_satisfaction', sa.Float(), nullable=True),
        sa.Column('complexity_score', sa.Float(), nullable=True),
        
        # Retrieval importance
        sa.Column('significance', sa.Float(), default=0.5),
        sa.Column('is_exemplar', sa.Boolean(), default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('episode_id')
    )
    
    # Create indexes for episodic_memory
    op.create_index('ix_episodic_memory_episode_id', 'episodic_memory', ['episode_id'])
    op.create_index('ix_episodic_memory_session_id', 'episodic_memory', ['session_id'])
    op.create_index('ix_episodic_memory_user_id', 'episodic_memory', ['user_id'])
    
    # Create context_states table
    op.create_table(
        'context_states',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Context identification
        sa.Column('context_id', sa.String(100), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        
        # Current focus
        sa.Column('primary_lead_id', sa.Integer(), nullable=True),
        sa.Column('secondary_lead_ids', postgresql.JSON(), nullable=True),
        
        # Active entities
        sa.Column('active_entities', postgresql.JSON(), nullable=True),
        sa.Column('active_topics', postgresql.JSON(), nullable=True),
        
        # Context stack
        sa.Column('context_stack', postgresql.JSON(), nullable=True),
        sa.Column('previous_contexts', postgresql.JSON(), nullable=True),
        
        # Attention weights
        sa.Column('attention_distribution', postgresql.JSON(), nullable=True),
        
        # State flags
        sa.Column('requires_clarification', sa.Boolean(), default=False),
        sa.Column('has_pending_decisions', sa.Boolean(), default=False),
        sa.Column('is_complete', sa.Boolean(), default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['primary_lead_id'], ['leads.id'], ),
        sa.UniqueConstraint('context_id')
    )
    
    # Create indexes for context_states
    op.create_index('ix_context_states_context_id', 'context_states', ['context_id'])
    op.create_index('ix_context_states_session_id', 'context_states', ['session_id'])


def downgrade():
    """Drop memory and context tables."""
    
    # Drop indexes and tables in reverse order
    op.drop_index('ix_context_states_session_id', 'context_states')
    op.drop_index('ix_context_states_context_id', 'context_states')
    op.drop_table('context_states')
    
    op.drop_index('ix_episodic_memory_user_id', 'episodic_memory')
    op.drop_index('ix_episodic_memory_session_id', 'episodic_memory')
    op.drop_index('ix_episodic_memory_episode_id', 'episodic_memory')
    op.drop_table('episodic_memory')
    
    op.drop_index('ix_semantic_memory_cluster', 'semantic_memory')
    op.drop_index('ix_semantic_memory_content', 'semantic_memory')
    op.drop_table('semantic_memory')
    
    op.drop_index('ix_long_term_memory_is_active', 'long_term_memory')
    op.drop_index('ix_long_term_memory_type_category', 'long_term_memory')
    op.drop_index('ix_long_term_memory_user_key', 'long_term_memory')
    op.drop_table('long_term_memory')
    
    op.drop_index('ix_short_term_memory_is_active', 'short_term_memory')
    op.drop_index('ix_short_term_memory_session_id', 'short_term_memory')
    op.drop_table('short_term_memory')
    
    op.drop_index('ix_conversation_memory_created_at', 'conversation_memory')
    op.drop_index('ix_conversation_memory_user_id', 'conversation_memory')
    op.drop_index('ix_conversation_memory_session_id', 'conversation_memory')
    op.drop_table('conversation_memory')