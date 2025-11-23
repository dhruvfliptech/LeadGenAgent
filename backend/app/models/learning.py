"""
Learning models for reinforcement learning and feedback tracking.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base


class InteractionFeedback(Base):
    """Model for tracking user interactions and feedback on leads and responses."""
    
    __tablename__ = "interaction_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    approval_id = Column(Integer, ForeignKey("response_approvals.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("response_templates.id"), nullable=True)
    
    # Interaction type
    interaction_type = Column(String(50), nullable=False)  # view, generate, approve, reject, send, reply
    action_taken = Column(String(100), nullable=True)  # specific action details
    
    # Feedback signals
    explicit_rating = Column(Float, nullable=True)  # 1-5 star rating
    implicit_signal = Column(String(50), nullable=True)  # clicked, ignored, deleted, bookmarked
    response_received = Column(Boolean, default=False)
    response_positive = Column(Boolean, nullable=True)
    
    # Time tracking
    time_to_action = Column(Float, nullable=True)  # seconds from presentation to action
    dwell_time = Column(Float, nullable=True)  # seconds spent viewing
    
    # Outcome tracking
    outcome = Column(String(50), nullable=True)  # hired, interviewed, rejected, no_response
    outcome_value = Column(Float, nullable=True)  # monetary value if applicable
    
    # Context
    user_context = Column(JSON, nullable=True)  # user state at time of interaction
    session_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    lead = relationship("Lead", backref="feedback_interactions")
    
    def __repr__(self):
        return f"<InteractionFeedback(id={self.id}, lead_id={self.lead_id}, type='{self.interaction_type}')>"


class LearningState(Base):
    """Model for tracking the learning state of the reinforcement learning system."""
    
    __tablename__ = "learning_states"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model identification
    model_name = Column(String(100), nullable=False, unique=True)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # qualification, response, ranking
    
    # State representation
    state_vector = Column(JSON, nullable=True)  # Current state representation
    q_values = Column(JSON, nullable=True)  # Q-values for state-action pairs
    policy_weights = Column(JSON, nullable=True)  # Policy network weights
    
    # Learning parameters
    learning_rate = Column(Float, default=0.01)
    discount_factor = Column(Float, default=0.95)
    exploration_rate = Column(Float, default=0.1)
    
    # Training statistics
    episodes_trained = Column(Integer, default=0)
    total_reward = Column(Float, default=0.0)
    average_reward = Column(Float, nullable=True)
    last_loss = Column(Float, nullable=True)
    
    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Buffer for experience replay
    experience_buffer = Column(JSON, nullable=True)
    buffer_size = Column(Integer, default=1000)
    
    # Status
    is_training = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_trained_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<LearningState(id={self.id}, model='{self.model_name}', version='{self.model_version}')>"


class RewardSignal(Base):
    """Model for tracking reward signals for reinforcement learning."""
    
    __tablename__ = "reward_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Context
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # qualify, generate, send
    action_details = Column(JSON, nullable=True)
    
    # State at time of action
    state_features = Column(JSON, nullable=False)  # Features used for decision
    action_taken = Column(String(100), nullable=False)  # Specific action
    
    # Reward components
    immediate_reward = Column(Float, nullable=False)  # Immediate feedback
    delayed_reward = Column(Float, nullable=True)  # Long-term outcome
    total_reward = Column(Float, nullable=True)  # Combined reward
    
    # Reward breakdown
    reward_components = Column(JSON, nullable=True)  # Individual reward factors
    
    # Learning context
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    episode_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<RewardSignal(id={self.id}, lead_id={self.lead_id}, reward={self.total_reward})>"


class FeatureImportance(Base):
    """Model for tracking feature importance learned by the system."""
    
    __tablename__ = "feature_importance"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model context
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Feature information
    feature_name = Column(String(100), nullable=False)
    feature_category = Column(String(50), nullable=True)  # lead, template, user, context
    
    # Importance metrics
    importance_score = Column(Float, nullable=False)
    correlation_with_success = Column(Float, nullable=True)
    usage_frequency = Column(Float, nullable=True)
    
    # Statistical measures
    mean_value = Column(Float, nullable=True)
    std_deviation = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Impact analysis
    positive_impact_count = Column(Integer, default=0)
    negative_impact_count = Column(Integer, default=0)
    neutral_impact_count = Column(Integer, default=0)
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<FeatureImportance(id={self.id}, feature='{self.feature_name}', score={self.importance_score})>"


class PolicyHistory(Base):
    """Model for tracking policy changes over time."""
    
    __tablename__ = "policy_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Policy identification
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    policy_version = Column(Integer, nullable=False)
    
    # Policy representation
    policy_type = Column(String(50), nullable=False)  # epsilon_greedy, softmax, ucb
    policy_parameters = Column(JSON, nullable=False)
    action_probabilities = Column(JSON, nullable=True)
    
    # Performance at time of policy
    performance_metrics = Column(JSON, nullable=False)
    training_episodes = Column(Integer, nullable=False)
    total_reward = Column(Float, nullable=False)
    
    # Changes from previous
    changes_from_previous = Column(JSON, nullable=True)
    improvement_rate = Column(Float, nullable=True)
    
    # Deployment status
    is_deployed = Column(Boolean, default=False)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PolicyHistory(id={self.id}, model='{self.model_name}', version={self.policy_version})>"