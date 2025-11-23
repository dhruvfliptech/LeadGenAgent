"""Phase 3 Tables Migration

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001_add_ml_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create Phase 3 tables."""
    
    # Response templates table
    op.create_table(
        'response_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('subject_template', sa.Text(), nullable=False),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('use_ai_enhancement', sa.Boolean(), nullable=False, default=False),
        sa.Column('ai_tone', sa.String(50), nullable=False, default='professional'),
        sa.Column('ai_length', sa.String(50), nullable=False, default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_test_variant', sa.Boolean(), nullable=False, default=False),
        sa.Column('control_template_id', sa.Integer(), nullable=True),
        sa.Column('test_weight', sa.Float(), nullable=False, default=50.0),
        sa.Column('sent_count', sa.Integer(), nullable=False, default=0),
        sa.Column('response_count', sa.Integer(), nullable=False, default=0),
        sa.Column('conversion_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['control_template_id'], ['response_templates.id'])
    )
    
    # Auto responses table
    op.create_table(
        'auto_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), nullable=False, index=True),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('personalization_data', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delay_minutes', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('email_opened', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_clicked', sa.Boolean(), nullable=False, default=False),
        sa.Column('lead_responded', sa.Boolean(), nullable=False, default=False),
        sa.Column('response_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.ForeignKeyConstraint(['template_id'], ['response_templates.id'])
    )
    
    # Response variables table
    op.create_table(
        'response_variables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variable_type', sa.String(50), nullable=False),
        sa.Column('source_field', sa.String(100), nullable=True),
        sa.Column('default_value', sa.String(255), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('validation_regex', sa.String(500), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Filter rules table
    op.create_table(
        'filter_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=100, index=True),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('operator', sa.String(50), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('value_list', sa.JSON(), nullable=True),
        sa.Column('regex_pattern', sa.String(500), nullable=True),
        sa.Column('min_value', sa.Float(), nullable=True),
        sa.Column('max_value', sa.Float(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('action_config', sa.JSON(), nullable=True),
        sa.Column('evaluation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('match_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Rule sets table
    op.create_table(
        'rule_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=100, index=True),
        sa.Column('logic_operator', sa.String(10), nullable=False, default='and'),
        sa.Column('evaluation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('match_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Rule set rules association table
    op.create_table(
        'rule_set_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_set_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_set_id'], ['rule_sets.id']),
        sa.ForeignKeyConstraint(['rule_id'], ['filter_rules.id'])
    )
    
    # Exclude lists table
    op.create_table(
        'exclude_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('list_type', sa.String(50), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_case_sensitive', sa.Boolean(), nullable=False, default=False),
        sa.Column('match_type', sa.String(50), nullable=False, default='exact'),
        sa.Column('match_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Exclude list items table
    op.create_table(
        'exclude_list_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exclude_list_id', sa.Integer(), nullable=False, index=True),
        sa.Column('value', sa.String(500), nullable=False, index=True),
        sa.Column('pattern', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('match_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_matched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['exclude_list_id'], ['exclude_lists.id'])
    )
    
    # Rule executions table
    op.create_table(
        'rule_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False, index=True),
        sa.Column('rule_id', sa.Integer(), nullable=True, index=True),
        sa.Column('rule_set_id', sa.Integer(), nullable=True, index=True),
        sa.Column('matched', sa.Boolean(), nullable=False, index=True),
        sa.Column('action_taken', sa.String(50), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('evaluation_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
        sa.ForeignKeyConstraint(['rule_id'], ['filter_rules.id']),
        sa.ForeignKeyConstraint(['rule_set_id'], ['rule_sets.id'])
    )
    
    # Schedules table
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False, index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=100),
        sa.Column('recurrence_type', sa.String(50), nullable=False),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('task_config', sa.JSON(), nullable=True),
        sa.Column('timeout_minutes', sa.Integer(), nullable=False, default=60),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('retry_delay_minutes', sa.Integer(), nullable=False, default=5),
        sa.Column('total_runs', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_runs', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_runs', sa.Integer(), nullable=False, default=0),
        sa.Column('average_duration_seconds', sa.Float(), nullable=True),
        sa.Column('peak_hours_only', sa.Boolean(), nullable=False, default=False),
        sa.Column('peak_start_hour', sa.Integer(), nullable=False, default=9),
        sa.Column('peak_end_hour', sa.Integer(), nullable=False, default=17),
        sa.Column('peak_timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('notify_on_success', sa.Boolean(), nullable=False, default=False),
        sa.Column('notify_on_failure', sa.Boolean(), nullable=False, default=True),
        sa.Column('notification_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Schedule executions table
    op.create_table(
        'schedule_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('records_created', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('log_file_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'])
    )
    
    # Schedule templates table
    op.create_table(
        'schedule_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_recommended', sa.Boolean(), nullable=False, default=False),
        sa.Column('difficulty_level', sa.String(20), nullable=False, default='beginner'),
        sa.Column('default_config', sa.JSON(), nullable=False),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.Column('optional_fields', sa.JSON(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('setup_instructions', sa.Text(), nullable=True),
        sa.Column('configuration_help', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Scraping schedules table
    op.create_table(
        'scraping_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('location_ids', sa.JSON(), nullable=False),
        sa.Column('categories', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('delay_between_requests', sa.Float(), nullable=False, default=2.0),
        sa.Column('concurrent_requests', sa.Integer(), nullable=False, default=3),
        sa.Column('pages_per_location', sa.Integer(), nullable=False, default=5),
        sa.Column('enable_email_extraction', sa.Boolean(), nullable=False, default=False),
        sa.Column('enable_captcha_solving', sa.Boolean(), nullable=False, default=False),
        sa.Column('min_lead_quality_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('skip_duplicates', sa.Boolean(), nullable=False, default=True),
        sa.Column('duplicate_check_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('adaptive_scheduling', sa.Boolean(), nullable=False, default=False),
        sa.Column('peak_detection', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'])
    )
    
    # Schedule notifications table
    op.create_table(
        'schedule_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False, index=True),
        sa.Column('execution_id', sa.Integer(), nullable=True, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id']),
        sa.ForeignKeyConstraint(['execution_id'], ['schedule_executions.id'])
    )
    
    # Notification preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('priority_threshold', sa.String(20), nullable=False, default='normal'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('quiet_start_hour', sa.Integer(), nullable=False, default=22),
        sa.Column('quiet_end_hour', sa.Integer(), nullable=False, default=8),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('max_per_hour', sa.Integer(), nullable=True),
        sa.Column('max_per_day', sa.Integer(), nullable=True),
        sa.Column('digest_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('digest_frequency_hours', sa.Integer(), nullable=False, default=24),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Notification channels table
    op.create_table(
        'notification_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('channel_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('credentials', sa.JSON(), nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, default=60),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, default=1000),
        sa.Column('total_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_sent', sa.Integer(), nullable=False, default=0),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('is_healthy', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('priority', sa.String(20), nullable=False, default='normal', index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(50), nullable=True, index=True),
        sa.Column('broadcast', sa.Boolean(), nullable=False, default=False),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Notification deliveries table
    op.create_table(
        'notification_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False, index=True),
        sa.Column('channel_id', sa.Integer(), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('delivery_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id']),
        sa.ForeignKeyConstraint(['channel_id'], ['notification_channels.id'])
    )
    
    # Notification templates table
    op.create_table(
        'notification_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('channel_type', sa.String(50), nullable=False, index=True),
        sa.Column('title_template', sa.String(255), nullable=False),
        sa.Column('message_template', sa.Text(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('format_config', sa.JSON(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Notification digests table
    op.create_table(
        'notification_digests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('digest_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('notification_count', sa.Integer(), nullable=False),
        sa.Column('notification_ids', sa.JSON(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # WebSocket connections table
    op.create_table(
        'websocket_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_ping_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    print("Phase 3 tables created successfully!")


def downgrade():
    """Drop Phase 3 tables."""
    
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('websocket_connections')
    op.drop_table('notification_digests')
    op.drop_table('notification_templates')
    op.drop_table('notification_deliveries')
    op.drop_table('notifications')
    op.drop_table('notification_channels')
    op.drop_table('notification_preferences')
    op.drop_table('schedule_notifications')
    op.drop_table('scraping_schedules')
    op.drop_table('schedule_templates')
    op.drop_table('schedule_executions')
    op.drop_table('schedules')
    op.drop_table('rule_executions')
    op.drop_table('exclude_list_items')
    op.drop_table('exclude_lists')
    op.drop_table('rule_set_rules')
    op.drop_table('rule_sets')
    op.drop_table('filter_rules')
    op.drop_table('response_variables')
    op.drop_table('auto_responses')
    op.drop_table('response_templates')
    
    print("Phase 3 tables dropped successfully!")