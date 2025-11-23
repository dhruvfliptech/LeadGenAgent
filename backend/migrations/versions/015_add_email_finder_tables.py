"""
Add email finder tables and quota tracking.

Revision ID: 015
Revises: 014
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, ARRAY


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    """Create email finder tables."""

    # Create email_finder_usage table
    op.create_table(
        'email_finder_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.Enum('HUNTER_IO', 'ROCKETREACH', name='servicename'), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('requests_used', sa.Integer(), default=0, nullable=False),
        sa.Column('quota_remaining', sa.Integer(), nullable=True),
        sa.Column('quota_limit', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), default=0.0, nullable=False),
        sa.Column('endpoint', sa.String(50), nullable=True),
        sa.Column('domain', sa.String(255), nullable=True),
        sa.Column('success', sa.Boolean(), default=True, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('results_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_email_finder_usage_service', 'email_finder_usage', ['service'])
    op.create_index('ix_email_finder_usage_date', 'email_finder_usage', ['date'])
    op.create_index('ix_email_finder_usage_domain', 'email_finder_usage', ['domain'])

    # Create found_emails table
    op.create_table(
        'found_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('source', sa.Enum('HUNTER_IO', 'ROCKETREACH', 'SCRAPED', 'MANUAL', 'CRAIGSLIST', name='emailsource'), nullable=False),
        sa.Column('source_service_id', sa.Integer(), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('position', sa.String(255), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('seniority', sa.String(50), nullable=True),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('verification_status', sa.String(50), nullable=True),
        sa.Column('verification_score', sa.Integer(), nullable=True),
        sa.Column('is_generic', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_personal', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_disposable', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_webmail', sa.Boolean(), default=False, nullable=False),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('twitter_handle', sa.String(100), nullable=True),
        sa.Column('sources', JSON, nullable=True),
        sa.Column('metadata', JSON, nullable=True),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('times_used', sa.Integer(), default=0, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_service_id'], ['email_finder_usage.id']),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'])
    )

    op.create_index('ix_found_emails_email', 'found_emails', ['email'])
    op.create_index('ix_found_emails_domain', 'found_emails', ['domain'])
    op.create_index('ix_found_emails_source', 'found_emails', ['source'])
    op.create_index('ix_found_emails_lead_id', 'found_emails', ['lead_id'])

    # Create email_finder_quotas table
    op.create_table(
        'email_finder_quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.Enum('HUNTER_IO', 'ROCKETREACH', name='servicename'), nullable=False, unique=True),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quota_limit', sa.Integer(), nullable=False),
        sa.Column('requests_used', sa.Integer(), default=0, nullable=False),
        sa.Column('requests_remaining', sa.Integer(), nullable=False),
        sa.Column('total_cost', sa.Float(), default=0.0, nullable=False),
        sa.Column('cost_per_request', sa.Float(), default=0.0, nullable=False),
        sa.Column('alert_threshold', sa.Integer(), nullable=True),
        sa.Column('alert_sent', sa.Boolean(), default=False, nullable=False),
        sa.Column('plan_name', sa.String(100), nullable=True),
        sa.Column('plan_level', sa.Integer(), nullable=True),
        sa.Column('reset_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_email_finder_quotas_service', 'email_finder_quotas', ['service'], unique=True)
    op.create_index('ix_email_finder_quotas_month', 'email_finder_quotas', ['month'])
    op.create_index('ix_email_finder_quotas_year', 'email_finder_quotas', ['year'])

    # Add email_source column to leads table (if not exists)
    # Check if column exists to avoid errors if migration is run multiple times
    try:
        op.add_column('leads', sa.Column('email_source', sa.String(50), nullable=True))
        op.create_index('ix_leads_email_source', 'leads', ['email_source'])
    except Exception as e:
        print(f"Column email_source may already exist: {e}")


def downgrade():
    """Drop email finder tables."""

    # Drop indexes and column from leads
    try:
        op.drop_index('ix_leads_email_source', table_name='leads')
        op.drop_column('leads', 'email_source')
    except Exception as e:
        print(f"Could not drop email_source column: {e}")

    # Drop email_finder_quotas table
    op.drop_index('ix_email_finder_quotas_year', table_name='email_finder_quotas')
    op.drop_index('ix_email_finder_quotas_month', table_name='email_finder_quotas')
    op.drop_index('ix_email_finder_quotas_service', table_name='email_finder_quotas')
    op.drop_table('email_finder_quotas')

    # Drop found_emails table
    op.drop_index('ix_found_emails_lead_id', table_name='found_emails')
    op.drop_index('ix_found_emails_source', table_name='found_emails')
    op.drop_index('ix_found_emails_domain', table_name='found_emails')
    op.drop_index('ix_found_emails_email', table_name='found_emails')
    op.drop_table('found_emails')

    # Drop email_finder_usage table
    op.drop_index('ix_email_finder_usage_domain', table_name='email_finder_usage')
    op.drop_index('ix_email_finder_usage_date', table_name='email_finder_usage')
    op.drop_index('ix_email_finder_usage_service', table_name='email_finder_usage')
    op.drop_table('email_finder_usage')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS emailsource')
    op.execute('DROP TYPE IF EXISTS servicename')
