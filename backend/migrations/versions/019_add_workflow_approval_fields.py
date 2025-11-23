"""Add workflow approval fields for n8n integration

Revision ID: 019_workflow_approvals
Revises: 018
Create Date: 2025-11-04

This migration extends the approval system for n8n workflow integration:
- Adds workflow execution tracking fields
- Adds approval history table
- Adds approval settings table
- Enhances existing approval tables with workflow support
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019_workflow_approvals'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema for workflow approvals."""

    # Add new fields to response_approvals table
    op.add_column('response_approvals',
        sa.Column('approval_type', sa.String(100), nullable=True, index=True)
    )
    op.add_column('response_approvals',
        sa.Column('resource_type', sa.String(100), nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('resource_data', postgresql.JSON, nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('workflow_execution_id', sa.String(200), nullable=True, index=True)
    )
    op.add_column('response_approvals',
        sa.Column('workflow_webhook_url', sa.String(500), nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True, index=True)
    )
    op.add_column('response_approvals',
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('approved', sa.Boolean, nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('rejection_reason', sa.Text, nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('escalation_level', sa.Integer, default=0)
    )
    op.add_column('response_approvals',
        sa.Column('escalated_to', sa.String(200), nullable=True)
    )
    op.add_column('response_approvals',
        sa.Column('metadata', postgresql.JSON, nullable=True)
    )

    # Rename reviewer_id to reviewer_email for consistency
    op.alter_column('response_approvals', 'reviewer_id',
        new_column_name='reviewer_email',
        type_=sa.String(200)
    )

    # Set default values for existing records
    op.execute("""
        UPDATE response_approvals
        SET approval_type = 'email_content_review',
            resource_type = 'email_template',
            approved = CASE
                WHEN status = 'approved' THEN true
                WHEN status = 'rejected' THEN false
                ELSE NULL
            END
        WHERE approval_type IS NULL
    """)

    # Create approval_history table
    op.create_table(
        'approval_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('approval_request_id', sa.Integer, sa.ForeignKey('response_approvals.id'), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('actor_email', sa.String(200), nullable=False),
        sa.Column('action_data', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True)
    )

    # Create approval_settings table
    op.create_table(
        'approval_settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('approval_type', sa.String(100), unique=True, nullable=False),
        sa.Column('enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('default_timeout_minutes', sa.Integer, default=60, nullable=False),
        sa.Column('auto_approve_threshold', sa.Integer, nullable=True),
        sa.Column('default_approvers', postgresql.JSON, nullable=True),
        sa.Column('escalation_chain', postgresql.JSON, nullable=True),
        sa.Column('notification_template', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Add indexes for performance
    op.create_index('idx_approval_type_status', 'response_approvals', ['approval_type', 'status'])
    op.create_index('idx_approval_timeout', 'response_approvals', ['status', 'timeout_at'])
    op.create_index('idx_approval_workflow', 'response_approvals', ['workflow_execution_id'])

    # Insert default approval settings
    op.execute("""
        INSERT INTO approval_settings (approval_type, enabled, default_timeout_minutes, default_approvers)
        VALUES
            ('demo_site_review', true, 120, '["admin@example.com"]'::json),
            ('video_review', true, 60, '["admin@example.com"]'::json),
            ('email_content_review', true, 30, '["admin@example.com"]'::json),
            ('improvement_plan_review', true, 240, '["admin@example.com"]'::json),
            ('lead_qualification', true, 15, '["admin@example.com"]'::json),
            ('campaign_launch', true, 480, '["admin@example.com"]'::json),
            ('budget_approval', true, 720, '["admin@example.com"]'::json)
    """)

    # Create function to automatically populate approval_history on status change
    op.execute("""
        CREATE OR REPLACE FUNCTION log_approval_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status IS DISTINCT FROM NEW.status THEN
                INSERT INTO approval_history (approval_request_id, action, actor_email, action_data)
                VALUES (
                    NEW.id,
                    'status_changed',
                    COALESCE(NEW.reviewer_email, 'system'),
                    json_build_object(
                        'old_status', OLD.status,
                        'new_status', NEW.status,
                        'timestamp', NOW()
                    )
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER approval_status_change_trigger
        AFTER UPDATE ON response_approvals
        FOR EACH ROW
        EXECUTE FUNCTION log_approval_status_change();
    """)


def downgrade():
    """Downgrade database schema."""

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS approval_status_change_trigger ON response_approvals")
    op.execute("DROP FUNCTION IF EXISTS log_approval_status_change()")

    # Drop indexes
    op.drop_index('idx_approval_workflow', 'response_approvals')
    op.drop_index('idx_approval_timeout', 'response_approvals')
    op.drop_index('idx_approval_type_status', 'response_approvals')

    # Drop tables
    op.drop_table('approval_settings')
    op.drop_table('approval_history')

    # Rename column back
    op.alter_column('response_approvals', 'reviewer_email',
        new_column_name='reviewer_id',
        type_=sa.String(100)
    )

    # Drop columns
    op.drop_column('response_approvals', 'metadata')
    op.drop_column('response_approvals', 'escalated_to')
    op.drop_column('response_approvals', 'escalation_level')
    op.drop_column('response_approvals', 'rejection_reason')
    op.drop_column('response_approvals', 'approved')
    op.drop_column('response_approvals', 'decided_at')
    op.drop_column('response_approvals', 'timeout_at')
    op.drop_column('response_approvals', 'workflow_webhook_url')
    op.drop_column('response_approvals', 'workflow_execution_id')
    op.drop_column('response_approvals', 'resource_data')
    op.drop_column('response_approvals', 'resource_type')
    op.drop_column('response_approvals', 'approval_type')
