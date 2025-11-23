"""
Add approval workflow tables for human-in-the-loop review.

Revision ID: 008
Create Date: 2024-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'


def upgrade():
    """Create approval workflow tables."""
    
    # Create response_approvals table
    op.create_table(
        'response_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Lead and Template references
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        
        # Generated response
        sa.Column('generated_subject', sa.String(500), nullable=True),
        sa.Column('generated_body', sa.Text(), nullable=False),
        
        # Modified response
        sa.Column('modified_subject', sa.String(500), nullable=True),
        sa.Column('modified_body', sa.Text(), nullable=True),
        
        # Approval status
        sa.Column('status', sa.String(50), default='pending', nullable=False),
        sa.Column('approval_method', sa.String(50), nullable=True),
        
        # Reviewer information
        sa.Column('reviewer_id', sa.String(100), nullable=True),
        sa.Column('reviewer_name', sa.String(255), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        
        # Scoring
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        
        # Auto-approval
        sa.Column('auto_approval_score', sa.Float(), nullable=True),
        sa.Column('auto_approval_reason', sa.Text(), nullable=True),
        
        # Notification settings
        sa.Column('slack_channel', sa.String(100), nullable=True),
        sa.Column('slack_message_ts', sa.String(100), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), default=False, nullable=False),
        
        # Response tracking
        sa.Column('response_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_status', sa.String(50), nullable=True),
        
        # Metadata
        sa.Column('variables_used', postgresql.JSON(), nullable=True),
        sa.Column('generation_metadata', postgresql.JSON(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['response_templates.id'], )
    )
    
    # Create indexes for response_approvals
    op.create_index('ix_response_approvals_lead_id', 'response_approvals', ['lead_id'])
    op.create_index('ix_response_approvals_status', 'response_approvals', ['status'])
    op.create_index('ix_response_approvals_created_at', 'response_approvals', ['created_at'])
    
    # Create approval_rules table
    op.create_table(
        'approval_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Rule conditions
        sa.Column('min_qualification_score', sa.Float(), nullable=True),
        sa.Column('required_keywords', postgresql.JSON(), nullable=True),
        sa.Column('excluded_keywords', postgresql.JSON(), nullable=True),
        
        # Lead criteria
        sa.Column('lead_categories', postgresql.JSON(), nullable=True),
        sa.Column('compensation_min', sa.Float(), nullable=True),
        sa.Column('compensation_max', sa.Float(), nullable=True),
        
        # Template criteria
        sa.Column('template_types', postgresql.JSON(), nullable=True),
        
        # Auto-approval settings
        sa.Column('auto_approve', sa.Boolean(), default=False, nullable=False),
        sa.Column('auto_approve_threshold', sa.Float(), default=0.9, nullable=False),
        
        # Notification settings
        sa.Column('require_slack_review', sa.Boolean(), default=True, nullable=False),
        sa.Column('slack_channels', postgresql.JSON(), nullable=True),
        sa.Column('notification_priority', sa.String(50), default='normal', nullable=False),
        
        # Rule configuration
        sa.Column('priority', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        
        # Statistics
        sa.Column('times_triggered', sa.Integer(), default=0, nullable=False),
        sa.Column('auto_approved_count', sa.Integer(), default=0, nullable=False),
        sa.Column('manual_review_count', sa.Integer(), default=0, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for approval_rules
    op.create_index('ix_approval_rules_name', 'approval_rules', ['name'])
    op.create_index('ix_approval_rules_is_active', 'approval_rules', ['is_active'])
    op.create_index('ix_approval_rules_priority', 'approval_rules', ['priority'])
    
    # Create approval_queue table
    op.create_table(
        'approval_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('approval_id', sa.Integer(), nullable=False),
        
        # Queue management
        sa.Column('priority', sa.String(50), default='normal', nullable=False),
        sa.Column('queue_position', sa.Integer(), nullable=True),
        
        # Assignment
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        
        # SLA tracking
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_status', sa.String(50), default='on_track', nullable=False),
        
        # Reminder settings
        sa.Column('reminder_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('reminder_count', sa.Integer(), default=0, nullable=False),
        sa.Column('last_reminder_at', sa.DateTime(timezone=True), nullable=True),
        
        # Status
        sa.Column('status', sa.String(50), default='queued', nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['approval_id'], ['response_approvals.id'], )
    )
    
    # Create indexes for approval_queue
    op.create_index('ix_approval_queue_approval_id', 'approval_queue', ['approval_id'])
    op.create_index('ix_approval_queue_status', 'approval_queue', ['status'])
    op.create_index('ix_approval_queue_priority', 'approval_queue', ['priority'])
    op.create_index('ix_approval_queue_sla_deadline', 'approval_queue', ['sla_deadline'])


def downgrade():
    """Drop approval workflow tables."""
    
    # Drop indexes for approval_queue
    op.drop_index('ix_approval_queue_sla_deadline', 'approval_queue')
    op.drop_index('ix_approval_queue_priority', 'approval_queue')
    op.drop_index('ix_approval_queue_status', 'approval_queue')
    op.drop_index('ix_approval_queue_approval_id', 'approval_queue')
    op.drop_table('approval_queue')
    
    # Drop indexes for approval_rules
    op.drop_index('ix_approval_rules_priority', 'approval_rules')
    op.drop_index('ix_approval_rules_is_active', 'approval_rules')
    op.drop_index('ix_approval_rules_name', 'approval_rules')
    op.drop_table('approval_rules')
    
    # Drop indexes for response_approvals
    op.drop_index('ix_response_approvals_created_at', 'response_approvals')
    op.drop_index('ix_response_approvals_status', 'response_approvals')
    op.drop_index('ix_response_approvals_lead_id', 'response_approvals')
    op.drop_table('response_approvals')