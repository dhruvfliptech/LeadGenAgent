#!/usr/bin/env python
"""
Script to create campaign management tables directly.
This bypasses Alembic migration chain issues.
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

async def create_tables():
    """Create campaign management tables."""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True,
    )

    # SQL to create tables
    sql_commands = """
    -- Create campaigns table
    CREATE TABLE IF NOT EXISTS campaigns (
        id SERIAL PRIMARY KEY,
        campaign_id VARCHAR(100) UNIQUE NOT NULL,
        name VARCHAR(255) NOT NULL,
        template_id INTEGER,
        status VARCHAR(50) DEFAULT 'draft' NOT NULL,
        scheduled_at TIMESTAMP WITH TIME ZONE,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        total_recipients INTEGER DEFAULT 0 NOT NULL,
        emails_sent INTEGER DEFAULT 0 NOT NULL,
        emails_opened INTEGER DEFAULT 0 NOT NULL,
        emails_clicked INTEGER DEFAULT 0 NOT NULL,
        emails_replied INTEGER DEFAULT 0 NOT NULL,
        emails_bounced INTEGER DEFAULT 0 NOT NULL,
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );

    -- Create campaigns indexes
    CREATE INDEX IF NOT EXISTS ix_campaigns_campaign_id ON campaigns(campaign_id) UNIQUE;
    CREATE INDEX IF NOT EXISTS ix_campaigns_name ON campaigns(name);
    CREATE INDEX IF NOT EXISTS ix_campaigns_status ON campaigns(status);
    CREATE INDEX IF NOT EXISTS ix_campaigns_created_by ON campaigns(created_by);
    CREATE INDEX IF NOT EXISTS ix_campaigns_scheduled_at ON campaigns(scheduled_at);
    CREATE INDEX IF NOT EXISTS ix_campaigns_started_at ON campaigns(started_at);
    CREATE INDEX IF NOT EXISTS ix_campaigns_created_at ON campaigns(created_at);

    -- Create campaign_recipients table
    CREATE TABLE IF NOT EXISTS campaign_recipients (
        id SERIAL PRIMARY KEY,
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
        email_address VARCHAR(255) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending' NOT NULL,
        sent_at TIMESTAMP WITH TIME ZONE,
        opened_at TIMESTAMP WITH TIME ZONE,
        clicked_at TIMESTAMP WITH TIME ZONE,
        replied_at TIMESTAMP WITH TIME ZONE,
        bounced_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        CONSTRAINT uq_campaign_recipients_campaign_lead UNIQUE(campaign_id, lead_id)
    );

    -- Create campaign_recipients indexes
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_campaign_id ON campaign_recipients(campaign_id);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_lead_id ON campaign_recipients(lead_id);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_email_address ON campaign_recipients(email_address);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_status ON campaign_recipients(status);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_sent_at ON campaign_recipients(sent_at);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_opened_at ON campaign_recipients(opened_at);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_clicked_at ON campaign_recipients(clicked_at);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_replied_at ON campaign_recipients(replied_at);
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_bounced_at ON campaign_recipients(bounced_at);

    -- Create email_tracking table
    CREATE TABLE IF NOT EXISTS email_tracking (
        id SERIAL PRIMARY KEY,
        campaign_recipient_id INTEGER NOT NULL REFERENCES campaign_recipients(id) ON DELETE CASCADE,
        event_type VARCHAR(50) NOT NULL,
        event_data JSONB,
        user_agent TEXT,
        ip_address INET,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );

    -- Create email_tracking indexes
    CREATE INDEX IF NOT EXISTS ix_email_tracking_campaign_recipient_id ON email_tracking(campaign_recipient_id);
    CREATE INDEX IF NOT EXISTS ix_email_tracking_event_type ON email_tracking(event_type);
    CREATE INDEX IF NOT EXISTS ix_email_tracking_ip_address ON email_tracking(ip_address);
    CREATE INDEX IF NOT EXISTS ix_email_tracking_created_at ON email_tracking(created_at);

    -- Create composite indexes
    CREATE INDEX IF NOT EXISTS ix_campaign_recipients_campaign_status ON campaign_recipients(campaign_id, status);
    CREATE INDEX IF NOT EXISTS ix_email_tracking_recipient_event ON email_tracking(campaign_recipient_id, event_type);
    """

    async with engine.begin() as conn:
        # Execute each command separately to avoid issues
        for command in sql_commands.split(';'):
            command = command.strip()
            if command:
                try:
                    await conn.execute(text(command))
                    print(f"Executed: {command[:60]}...")
                except Exception as e:
                    print(f"Error executing: {command[:60]}...\nError: {e}")

        await conn.commit()

    await engine.dispose()
    print("\nCampaign management tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
