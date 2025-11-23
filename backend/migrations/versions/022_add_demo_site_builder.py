"""
Migration: Add Demo Site Builder Tables

Creates tables for AI-powered demo site builder:
- demo_site_templates: Pre-built and custom templates
- demo_site_analytics: Daily analytics aggregation
- demo_site_components: Reusable UI components
- Updates demo_sites table with new fields

Revision ID: 022_add_demo_site_builder
Revises: 021
Create Date: 2024-11-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '022_add_demo_site_builder'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""

    # Create demo_site_templates table
    op.create_table(
        'demo_site_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(255), nullable=False),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_template', sa.Text(), nullable=False),
        sa.Column('css_template', sa.Text(), nullable=False),
        sa.Column('js_template', sa.Text(), nullable=True),
        sa.Column('preview_image_url', sa.String(512), nullable=True),
        sa.Column('thumbnail_url', sa.String(512), nullable=True),
        sa.Column('customization_options', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('default_meta_title', sa.String(255), nullable=True),
        sa.Column('default_meta_description', sa.Text(), nullable=True),
        sa.Column('default_meta_keywords', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_demo_site_templates_template_name', 'demo_site_templates', ['template_name'], unique=True)
    op.create_index('ix_demo_site_templates_template_type', 'demo_site_templates', ['template_type'])
    op.create_index('ix_demo_site_templates_is_active', 'demo_site_templates', ['is_active'])

    # Create demo_site_analytics table
    op.create_table(
        'demo_site_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('demo_site_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('page_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_time_on_page', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('bounce_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cta_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('analytics_data', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['demo_site_id'], ['demo_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_demo_analytics_demo_site_id', 'demo_site_analytics', ['demo_site_id'])
    op.create_index('ix_demo_analytics_date', 'demo_site_analytics', ['date'])
    op.create_index('idx_demo_analytics_site_date', 'demo_site_analytics', ['demo_site_id', 'date'])

    # Create demo_site_components table
    op.create_table(
        'demo_site_components',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('component_name', sa.String(255), nullable=False),
        sa.Column('component_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('html_code', sa.Text(), nullable=False),
        sa.Column('css_code', sa.Text(), nullable=True),
        sa.Column('js_code', sa.Text(), nullable=True),
        sa.Column('preview_image', sa.String(512), nullable=True),
        sa.Column('preview_html', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('required_data_fields', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('optional_data_fields', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_demo_site_components_component_name', 'demo_site_components', ['component_name'], unique=True)
    op.create_index('ix_demo_site_components_component_type', 'demo_site_components', ['component_type'])
    op.create_index('ix_demo_site_components_is_active', 'demo_site_components', ['is_active'])
    op.create_index('ix_demo_site_components_category', 'demo_site_components', ['category'])

    # Add new fields to demo_sites table
    op.add_column('demo_sites', sa.Column('template_id', sa.Integer(), nullable=True))
    op.add_column('demo_sites', sa.Column('content_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('demo_sites', sa.Column('style_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('demo_sites', sa.Column('generated_html', sa.Text(), nullable=True))
    op.add_column('demo_sites', sa.Column('generated_css', sa.Text(), nullable=True))
    op.add_column('demo_sites', sa.Column('generated_js', sa.Text(), nullable=True))
    op.add_column('demo_sites', sa.Column('total_conversions', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('demo_sites', sa.Column('site_name', sa.String(255), nullable=True))

    # Add foreign key for template_id
    op.create_foreign_key(
        'fk_demo_sites_template_id',
        'demo_sites',
        'demo_site_templates',
        ['template_id'],
        ['id']
    )

    op.create_index('ix_demo_sites_template_id', 'demo_sites', ['template_id'])

    print("✓ Created demo_site_templates table")
    print("✓ Created demo_site_analytics table")
    print("✓ Created demo_site_components table")
    print("✓ Added new fields to demo_sites table")


def downgrade():
    """Downgrade database schema."""

    # Remove indexes
    op.drop_index('ix_demo_sites_template_id', 'demo_sites')
    op.drop_index('ix_demo_site_components_category', 'demo_site_components')
    op.drop_index('ix_demo_site_components_is_active', 'demo_site_components')
    op.drop_index('ix_demo_site_components_component_type', 'demo_site_components')
    op.drop_index('ix_demo_site_components_component_name', 'demo_site_components')
    op.drop_index('idx_demo_analytics_site_date', 'demo_site_analytics')
    op.drop_index('ix_demo_analytics_date', 'demo_site_analytics')
    op.drop_index('ix_demo_analytics_demo_site_id', 'demo_site_analytics')
    op.drop_index('ix_demo_site_templates_is_active', 'demo_site_templates')
    op.drop_index('ix_demo_site_templates_template_type', 'demo_site_templates')
    op.drop_index('ix_demo_site_templates_template_name', 'demo_site_templates')

    # Remove foreign key
    op.drop_constraint('fk_demo_sites_template_id', 'demo_sites', type_='foreignkey')

    # Remove columns from demo_sites
    op.drop_column('demo_sites', 'site_name')
    op.drop_column('demo_sites', 'total_conversions')
    op.drop_column('demo_sites', 'generated_js')
    op.drop_column('demo_sites', 'generated_css')
    op.drop_column('demo_sites', 'generated_html')
    op.drop_column('demo_sites', 'style_settings')
    op.drop_column('demo_sites', 'content_data')
    op.drop_column('demo_sites', 'template_id')

    # Drop tables
    op.drop_table('demo_site_components')
    op.drop_table('demo_site_analytics')
    op.drop_table('demo_site_templates')

    print("✓ Rolled back demo site builder changes")
