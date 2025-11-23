"""
Memory and context management models for maintaining state across interactions.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class ConversationMemory(Base):
    """Model for storing conversation history and context."""
    
    __tablename__ = "conversation_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Conversation identification
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    
    # Lead context
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    
    # Message content
    message_type = Column(String(50), nullable=False)  # user, assistant, system
    message_content = Column(Text, nullable=False)
    
    # Context at time of message
    context_snapshot = Column(JSON, nullable=True)  # Full context state
    active_leads = Column(JSON, nullable=True)  # List of lead IDs being discussed
    active_templates = Column(JSON, nullable=True)  # List of template IDs in use
    
    # Extracted entities and intents
    entities = Column(JSON, nullable=True)  # Named entities extracted
    intent = Column(String(100), nullable=True)  # Detected user intent
    sentiment = Column(Float, nullable=True)  # Sentiment score (-1 to 1)
    
    # Memory importance
    importance_score = Column(Float, default=0.5)  # 0-1 importance for retrieval
    is_milestone = Column(Boolean, default=False)  # Key decision point
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", backref="conversation_memories")
    
    def __repr__(self):
        return f"<ConversationMemory(id={self.id}, session='{self.session_id}', type='{self.message_type}')>"


class ShortTermMemory(Base):
    """Model for short-term working memory during active sessions."""
    
    __tablename__ = "short_term_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session identification
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(100), nullable=True)
    
    # Current context
    current_leads = Column(JSON, nullable=True)  # Active lead IDs
    current_task = Column(String(200), nullable=True)  # What user is trying to accomplish
    current_step = Column(String(200), nullable=True)  # Current step in task
    
    # Working memory
    working_memory = Column(JSON, nullable=True)  # Key-value pairs of current state
    decision_stack = Column(JSON, nullable=True)  # Stack of pending decisions
    
    # User preferences learned in session
    session_preferences = Column(JSON, nullable=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    decision_count = Column(Integer, default=0)
    leads_processed = Column(Integer, default=0)
    
    # Session state
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ShortTermMemory(id={self.id}, session='{self.session_id}', active={self.is_active})>"


class LongTermMemory(Base):
    """Model for long-term memory storage of important patterns and learnings."""
    
    __tablename__ = "long_term_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification
    user_id = Column(String(100), nullable=True, index=True)
    
    # Memory type
    memory_type = Column(String(50), nullable=False)  # preference, pattern, rule, fact
    memory_category = Column(String(100), nullable=True)  # leads, templates, responses, etc.
    
    # Memory content
    memory_key = Column(String(200), nullable=False)  # Unique identifier for memory
    memory_value = Column(JSON, nullable=False)  # The actual memory content
    
    # Metadata
    confidence = Column(Float, default=0.5)  # Confidence in this memory (0-1)
    frequency = Column(Integer, default=1)  # How often this has been observed
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    
    # Decay and reinforcement
    strength = Column(Float, default=1.0)  # Memory strength (decays over time)
    reinforcement_count = Column(Integer, default=0)  # Times this has been reinforced
    
    # Source tracking
    source_sessions = Column(JSON, nullable=True)  # List of session IDs that contributed
    source_leads = Column(JSON, nullable=True)  # List of lead IDs related to this memory
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Create index for efficient retrieval
    __table_args__ = (
        Index('ix_long_term_memory_user_key', 'user_id', 'memory_key'),
        Index('ix_long_term_memory_type_category', 'memory_type', 'memory_category'),
    )
    
    def __repr__(self):
        return f"<LongTermMemory(id={self.id}, key='{self.memory_key}', strength={self.strength})>"


class SemanticMemory(Base):
    """Model for storing semantic knowledge and embeddings."""
    
    __tablename__ = "semantic_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content identification
    content_type = Column(String(50), nullable=False)  # lead, template, response, conversation
    content_id = Column(String(200), nullable=False)  # ID of the content
    
    # Semantic representation
    content_text = Column(Text, nullable=False)  # Original text
    embedding_vector = Column(JSON, nullable=True)  # Vector embedding
    embedding_model = Column(String(100), nullable=True)  # Model used for embedding
    
    # Semantic metadata
    topics = Column(JSON, nullable=True)  # Extracted topics
    keywords = Column(JSON, nullable=True)  # Key terms
    summary = Column(Text, nullable=True)  # Summarized version
    
    # Relationships
    similar_items = Column(JSON, nullable=True)  # IDs of semantically similar items
    cluster_id = Column(String(100), nullable=True)  # Semantic cluster assignment
    
    # Usage tracking
    retrieval_count = Column(Integer, default=0)
    last_retrieved = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Create index for similarity search
    __table_args__ = (
        Index('ix_semantic_memory_content', 'content_type', 'content_id'),
        Index('ix_semantic_memory_cluster', 'cluster_id'),
    )
    
    def __repr__(self):
        return f"<SemanticMemory(id={self.id}, type='{self.content_type}', cluster='{self.cluster_id}')>"


class EpisodicMemory(Base):
    """Model for storing episodic memories of specific interactions and outcomes."""
    
    __tablename__ = "episodic_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Episode identification
    episode_id = Column(String(100), nullable=False, unique=True)
    session_id = Column(String(100), nullable=False)
    user_id = Column(String(100), nullable=True)
    
    # Episode context
    episode_type = Column(String(50), nullable=False)  # lead_qualification, response_generation, etc.
    lead_ids = Column(JSON, nullable=True)  # Leads involved in episode
    
    # Episode narrative
    episode_start = Column(DateTime(timezone=True), nullable=False)
    episode_end = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Actions and outcomes
    actions_taken = Column(JSON, nullable=False)  # Sequence of actions
    final_outcome = Column(String(100), nullable=True)  # Success, failure, partial
    outcome_details = Column(JSON, nullable=True)
    
    # Learning from episode
    lessons_learned = Column(JSON, nullable=True)  # Key takeaways
    mistakes_made = Column(JSON, nullable=True)  # What went wrong
    successes = Column(JSON, nullable=True)  # What went well
    
    # Emotional and qualitative aspects
    user_satisfaction = Column(Float, nullable=True)  # 0-1 satisfaction score
    complexity_score = Column(Float, nullable=True)  # How complex was this episode
    
    # Retrieval importance
    significance = Column(Float, default=0.5)  # 0-1 importance for future reference
    is_exemplar = Column(Boolean, default=False)  # Is this a good example case
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<EpisodicMemory(id={self.id}, episode='{self.episode_id}', type='{self.episode_type}')>"


class ContextState(Base):
    """Model for maintaining current context state across the system."""
    
    __tablename__ = "context_states"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Context identification
    context_id = Column(String(100), nullable=False, unique=True)
    session_id = Column(String(100), nullable=False)
    
    # Current focus
    primary_lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    secondary_lead_ids = Column(JSON, nullable=True)
    
    # Active entities
    active_entities = Column(JSON, nullable=True)  # Currently relevant entities
    active_topics = Column(JSON, nullable=True)  # Topics being discussed
    
    # Context stack
    context_stack = Column(JSON, nullable=True)  # Stack of context switches
    previous_contexts = Column(JSON, nullable=True)  # History of contexts
    
    # Attention weights
    attention_distribution = Column(JSON, nullable=True)  # What to focus on
    
    # State flags
    requires_clarification = Column(Boolean, default=False)
    has_pending_decisions = Column(Boolean, default=False)
    is_complete = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ContextState(id={self.id}, context='{self.context_id}', session='{self.session_id}')>"