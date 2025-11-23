"""
Add reinforcement learning tables for feedback tracking and learning.

Revision ID: 009
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'


def upgrade():
    """Create reinforcement learning tables."""
    
    # Create interaction_feedback table
    op.create_table(
        'interaction_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # References
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('approval_id', sa.Integer(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        
        # Interaction type
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('action_taken', sa.String(100), nullable=True),
        
        # Feedback signals
        sa.Column('explicit_rating', sa.Float(), nullable=True),
        sa.Column('implicit_signal', sa.String(50), nullable=True),
        sa.Column('response_received', sa.Boolean(), default=False, nullable=False),
        sa.Column('response_positive', sa.Boolean(), nullable=True),
        
        # Time tracking
        sa.Column('time_to_action', sa.Float(), nullable=True),
        sa.Column('dwell_time', sa.Float(), nullable=True),
        
        # Outcome tracking
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('outcome_value', sa.Float(), nullable=True),
        
        # Context
        sa.Column('user_context', postgresql.JSON(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['approval_id'], ['response_approvals.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['response_templates.id'], )
    )
    
    # Create indexes for interaction_feedback
    op.create_index('ix_interaction_feedback_lead_id', 'interaction_feedback', ['lead_id'])
    op.create_index('ix_interaction_feedback_interaction_type', 'interaction_feedback', ['interaction_type'])
    op.create_index('ix_interaction_feedback_created_at', 'interaction_feedback', ['created_at'])
    
    # Create learning_states table
    op.create_table(
        'learning_states',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Model identification
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),
        
        # State representation
        sa.Column('state_vector', postgresql.JSON(), nullable=True),
        sa.Column('q_values', postgresql.JSON(), nullable=True),
        sa.Column('policy_weights', postgresql.JSON(), nullable=True),
        
        # Learning parameters
        sa.Column('learning_rate', sa.Float(), default=0.01, nullable=False),
        sa.Column('discount_factor', sa.Float(), default=0.95, nullable=False),
        sa.Column('exploration_rate', sa.Float(), default=0.1, nullable=False),
        
        # Training statistics
        sa.Column('episodes_trained', sa.Integer(), default=0, nullable=False),
        sa.Column('total_reward', sa.Float(), default=0.0, nullable=False),
        sa.Column('average_reward', sa.Float(), nullable=True),
        sa.Column('last_loss', sa.Float(), nullable=True),
        
        # Performance metrics
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        
        # Buffer for experience replay
        sa.Column('experience_buffer', postgresql.JSON(), nullable=True),
        sa.Column('buffer_size', sa.Integer(), default=1000, nullable=False),
        
        # Status
        sa.Column('is_training', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_trained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name')
    )
    
    # Create indexes for learning_states
    op.create_index('ix_learning_states_model_name', 'learning_states', ['model_name'])
    op.create_index('ix_learning_states_is_active', 'learning_states', ['is_active'])
    
    # Create reward_signals table
    op.create_table(
        'reward_signals',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Context
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_details', postgresql.JSON(), nullable=True),
        
        # State at time of action
        sa.Column('state_features', postgresql.JSON(), nullable=False),
        sa.Column('action_taken', sa.String(100), nullable=False),
        
        # Reward components
        sa.Column('immediate_reward', sa.Float(), nullable=False),
        sa.Column('delayed_reward', sa.Float(), nullable=True),
        sa.Column('total_reward', sa.Float(), nullable=True),
        
        # Reward breakdown
        sa.Column('reward_components', postgresql.JSON(), nullable=True),
        
        # Learning context
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('episode_id', sa.String(100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], )
    )
    
    # Create indexes for reward_signals
    op.create_index('ix_reward_signals_lead_id', 'reward_signals', ['lead_id'])
    op.create_index('ix_reward_signals_model_name', 'reward_signals', ['model_name'])
    op.create_index('ix_reward_signals_created_at', 'reward_signals', ['created_at'])
    
    # Create feature_importance table
    op.create_table(
        'feature_importance',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Model context
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        
        # Feature information
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('feature_category', sa.String(50), nullable=True),
        
        # Importance metrics
        sa.Column('importance_score', sa.Float(), nullable=False),
        sa.Column('correlation_with_success', sa.Float(), nullable=True),
        sa.Column('usage_frequency', sa.Float(), nullable=True),
        
        # Statistical measures
        sa.Column('mean_value', sa.Float(), nullable=True),
        sa.Column('std_deviation', sa.Float(), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        
        # Impact analysis
        sa.Column('positive_impact_count', sa.Integer(), default=0, nullable=False),
        sa.Column('negative_impact_count', sa.Integer(), default=0, nullable=False),
        sa.Column('neutral_impact_count', sa.Integer(), default=0, nullable=False),
        
        # Timestamps
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feature_importance
    op.create_index('ix_feature_importance_model_name', 'feature_importance', ['model_name'])
    op.create_index('ix_feature_importance_feature_name', 'feature_importance', ['feature_name'])
    op.create_index('ix_feature_importance_importance_score', 'feature_importance', ['importance_score'])
    
    # Create policy_history table
    op.create_table(
        'policy_history',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Policy identification
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('policy_version', sa.Integer(), nullable=False),
        
        # Policy representation
        sa.Column('policy_type', sa.String(50), nullable=False),
        sa.Column('policy_parameters', postgresql.JSON(), nullable=False),
        sa.Column('action_probabilities', postgresql.JSON(), nullable=True),
        
        # Performance at time of policy
        sa.Column('performance_metrics', postgresql.JSON(), nullable=False),
        sa.Column('training_episodes', sa.Integer(), nullable=False),
        sa.Column('total_reward', sa.Float(), nullable=False),
        
        # Changes from previous
        sa.Column('changes_from_previous', postgresql.JSON(), nullable=True),
        sa.Column('improvement_rate', sa.Float(), nullable=True),
        
        # Deployment status
        sa.Column('is_deployed', sa.Boolean(), default=False, nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for policy_history
    op.create_index('ix_policy_history_model_name', 'policy_history', ['model_name'])
    op.create_index('ix_policy_history_policy_version', 'policy_history', ['policy_version'])
    op.create_index('ix_policy_history_is_deployed', 'policy_history', ['is_deployed'])


def downgrade():
    """Drop reinforcement learning tables."""
    
    # Drop indexes for policy_history
    op.drop_index('ix_policy_history_is_deployed', 'policy_history')
    op.drop_index('ix_policy_history_policy_version', 'policy_history')
    op.drop_index('ix_policy_history_model_name', 'policy_history')
    op.drop_table('policy_history')
    
    # Drop indexes for feature_importance
    op.drop_index('ix_feature_importance_importance_score', 'feature_importance')
    op.drop_index('ix_feature_importance_feature_name', 'feature_importance')
    op.drop_index('ix_feature_importance_model_name', 'feature_importance')
    op.drop_table('feature_importance')
    
    # Drop indexes for reward_signals
    op.drop_index('ix_reward_signals_created_at', 'reward_signals')
    op.drop_index('ix_reward_signals_model_name', 'reward_signals')
    op.drop_index('ix_reward_signals_lead_id', 'reward_signals')
    op.drop_table('reward_signals')
    
    # Drop indexes for learning_states
    op.drop_index('ix_learning_states_is_active', 'learning_states')
    op.drop_index('ix_learning_states_model_name', 'learning_states')
    op.drop_table('learning_states')
    
    # Drop indexes for interaction_feedback
    op.drop_index('ix_interaction_feedback_created_at', 'interaction_feedback')
    op.drop_index('ix_interaction_feedback_interaction_type', 'interaction_feedback')
    op.drop_index('ix_interaction_feedback_lead_id', 'interaction_feedback')
    op.drop_table('interaction_feedback')