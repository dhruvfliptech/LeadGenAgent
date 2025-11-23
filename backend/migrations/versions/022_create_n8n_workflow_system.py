"""
Create N8N Workflow System Tables

Revision ID: 022_create_n8n_workflow_system
Revises: 021_create_campaign_management_tables
Create Date: 2025-01-05 20:00:00.000000

Creates comprehensive N8N workflow automation system:
- n8n_workflows: Workflow configuration
- workflow_executions: Execution tracking
- workflow_approvals: Approval management
- webhook_queue: Webhook async processing
- workflow_monitoring: Event and error logging
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


# revision identifiers
revision = '022_create_n8n_workflow_system'
down_revision = '021_create_campaign_management_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create N8N workflow system tables"""

    # Create n8n_workflows table
    op.create_table(
        'n8n_workflows',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workflow_name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('workflow_description', sa.Text(), nullable=True),

        # N8N integration
        sa.Column('n8n_workflow_id', sa.String(100), nullable=True, index=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_secret', sa.String(255), nullable=True),

        # Trigger configuration
        sa.Column('trigger_events', JSONB, nullable=True, server_default='[]'),
        sa.Column('trigger_conditions', JSONB, nullable=True, server_default='{}'),

        # Workflow settings
        sa.Column('is_active', sa.Boolean(), default=True, index=True),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('auto_approval_enabled', sa.Boolean(), default=False),
        sa.Column('timeout_seconds', sa.Integer(), default=300),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('retry_delay_seconds', sa.Integer(), default=60),

        # Metadata
        sa.Column('tags', JSONB, nullable=True, server_default='[]'),
        sa.Column('config_data', JSONB, nullable=True, server_default='{}'),

        # Statistics
        sa.Column('execution_count', sa.Integer(), default=0),
        sa.Column('success_count', sa.Integer(), default=0),
        sa.Column('failure_count', sa.Integer(), default=0),
        sa.Column('last_executed_at', sa.DateTime(), nullable=True),
        sa.Column('average_duration_seconds', sa.Float(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for n8n_workflows
    op.create_index('idx_n8n_workflows_active', 'n8n_workflows', ['is_active', 'created_at'])
    op.create_index('idx_n8n_workflows_execution', 'n8n_workflows', ['execution_count', 'last_executed_at'])

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('n8n_workflows.id', ondelete='CASCADE'), nullable=False, index=True),

        # Execution details
        sa.Column('n8n_execution_id', sa.String(100), nullable=True, index=True),
        sa.Column('trigger_event', sa.String(255), nullable=True, index=True),
        sa.Column('trigger_source', sa.String(100), nullable=True),

        # Data
        sa.Column('input_data', JSONB, nullable=True, server_default='{}'),
        sa.Column('output_data', JSONB, nullable=True, server_default='{}'),
        sa.Column('execution_log', sa.Text(), nullable=True),

        # Status tracking
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('progress_percentage', sa.Integer(), default=0),
        sa.Column('current_step', sa.String(255), nullable=True),

        # Timing
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('is_retryable', sa.Boolean(), default=True),

        # Metadata
        sa.Column('metadata', JSONB, nullable=True, server_default='{}'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for workflow_executions
    op.create_index('idx_workflow_executions_status_created', 'workflow_executions', ['status', 'created_at'])
    op.create_index('idx_workflow_executions_workflow_status', 'workflow_executions', ['workflow_id', 'status'])

    # Create workflow_approvals table
    op.create_table(
        'workflow_approvals',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('execution_id', sa.Integer(), sa.ForeignKey('workflow_executions.id', ondelete='CASCADE'), nullable=False, index=True),

        # Approval details
        sa.Column('approval_type', sa.String(100), nullable=False, index=True),
        sa.Column('approval_title', sa.String(255), nullable=False),
        sa.Column('approval_description', sa.Text(), nullable=True),
        sa.Column('approval_data', JSONB, nullable=True, server_default='{}'),

        # Status
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='pending'),
        sa.Column('priority', sa.String(50), nullable=False, index=True, server_default='medium'),

        # Approval decision
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('approver_name', sa.String(255), nullable=True),
        sa.Column('approval_reason', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),

        # Auto-approval
        sa.Column('requires_manual', sa.Boolean(), default=False),
        sa.Column('auto_approval_enabled', sa.Boolean(), default=True),
        sa.Column('auto_approval_confidence', sa.Float(), nullable=True),
        sa.Column('auto_approval_reason', sa.Text(), nullable=True),

        # Timeout
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),

        # Notifications
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('notification_sent_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for workflow_approvals
    op.create_index('idx_workflow_approvals_pending', 'workflow_approvals', ['status', 'priority', 'created_at'])
    op.create_index('idx_workflow_approvals_expires', 'workflow_approvals', ['status', 'expires_at'])

    # Create webhook_queue table
    op.create_table(
        'webhook_queue',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('n8n_workflows.id', ondelete='CASCADE'), nullable=True, index=True),

        # Webhook details
        sa.Column('webhook_payload', JSONB, nullable=False),
        sa.Column('webhook_headers', JSONB, nullable=True, server_default='{}'),
        sa.Column('source', sa.String(100), nullable=True, index=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),

        # Processing
        sa.Column('status', sa.String(50), nullable=False, index=True, server_default='queued'),
        sa.Column('priority', sa.Integer(), default=0, index=True),

        # Retry logic
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True, index=True),

        # Timing
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),

        # Error handling
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_trace', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )

    # Create indexes for webhook_queue
    op.create_index('idx_webhook_queue_processing', 'webhook_queue', ['status', 'priority', 'created_at'])
    op.create_index('idx_webhook_queue_retry', 'webhook_queue', ['status', 'next_retry_at'])

    # Create workflow_monitoring table
    op.create_table(
        'workflow_monitoring',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('workflow_id', sa.Integer(), sa.ForeignKey('n8n_workflows.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('execution_id', sa.Integer(), sa.ForeignKey('workflow_executions.id', ondelete='CASCADE'), nullable=True, index=True),

        # Event details
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('event_name', sa.String(255), nullable=True),
        sa.Column('event_description', sa.Text(), nullable=True),
        sa.Column('event_data', JSONB, nullable=True, server_default='{}'),

        # Severity
        sa.Column('severity', sa.String(50), nullable=False, index=True, server_default='info'),

        # Context
        sa.Column('step_name', sa.String(255), nullable=True),
        sa.Column('step_number', sa.Integer(), nullable=True),

        # Performance
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('memory_mb', sa.Float(), nullable=True),
        sa.Column('cpu_percent', sa.Float(), nullable=True),

        # Timestamp
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for workflow_monitoring
    op.create_index('idx_workflow_monitoring_workflow_time', 'workflow_monitoring', ['workflow_id', 'timestamp'])
    op.create_index('idx_workflow_monitoring_severity_time', 'workflow_monitoring', ['severity', 'timestamp'])
    op.create_index('idx_workflow_monitoring_execution', 'workflow_monitoring', ['execution_id', 'timestamp'])


def downgrade():
    """Drop N8N workflow system tables"""

    # Drop tables in reverse order (to handle foreign keys)
    op.drop_table('workflow_monitoring')
    op.drop_table('webhook_queue')
    op.drop_table('workflow_approvals')
    op.drop_table('workflow_executions')
    op.drop_table('n8n_workflows')
