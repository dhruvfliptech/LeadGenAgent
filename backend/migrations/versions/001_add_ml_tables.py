"""Add ML tables for lead scoring system

Revision ID: 001_add_ml_tables
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_ml_tables'
down_revision = None
depends_on = None


def upgrade():
    # Create lead_feedback table
    op.create_table('lead_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('user_rating', sa.Float(), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('interaction_duration', sa.Float(), nullable=True),
        sa.Column('feedback_source', sa.String(length=50), nullable=False),
        sa.Column('feedback_confidence', sa.Float(), nullable=False),
        sa.Column('contact_successful', sa.Boolean(), nullable=True),
        sa.Column('contact_response_time', sa.Float(), nullable=True),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('prediction_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_feedback_lead_id'), 'lead_feedback', ['lead_id'], unique=False)
    op.create_index(op.f('ix_lead_feedback_action_type'), 'lead_feedback', ['action_type'], unique=False)
    op.create_index(op.f('ix_lead_feedback_session_id'), 'lead_feedback', ['session_id'], unique=False)
    op.create_index(op.f('ix_lead_feedback_model_version'), 'lead_feedback', ['model_version'], unique=False)
    op.create_index(op.f('ix_lead_feedback_created_at'), 'lead_feedback', ['created_at'], unique=False)

    # Create model_metrics table
    op.create_table('model_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('precision', sa.Float(), nullable=True),
        sa.Column('recall', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('auc_roc', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('contact_success_rate', sa.Float(), nullable=True),
        sa.Column('avg_prediction_score', sa.Float(), nullable=True),
        sa.Column('training_samples', sa.Integer(), nullable=True),
        sa.Column('validation_samples', sa.Integer(), nullable=True),
        sa.Column('feature_count', sa.Integer(), nullable=True),
        sa.Column('training_duration', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_metrics_model_version'), 'model_metrics', ['model_version'], unique=False)
    op.create_index(op.f('ix_model_metrics_is_active'), 'model_metrics', ['is_active'], unique=False)

    # Create ab_test_variants table
    op.create_table('ab_test_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(length=100), nullable=False),
        sa.Column('variant_name', sa.String(length=50), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('traffic_percentage', sa.Float(), nullable=False),
        sa.Column('is_control', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('avg_score', sa.Float(), nullable=True),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_variants_test_name'), 'ab_test_variants', ['test_name'], unique=False)
    op.create_index(op.f('ix_ab_test_variants_variant_name'), 'ab_test_variants', ['variant_name'], unique=False)
    op.create_index(op.f('ix_ab_test_variants_model_version'), 'ab_test_variants', ['model_version'], unique=False)
    op.create_index(op.f('ix_ab_test_variants_is_active'), 'ab_test_variants', ['is_active'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('ab_test_variants')
    op.drop_table('model_metrics')
    op.drop_table('lead_feedback')