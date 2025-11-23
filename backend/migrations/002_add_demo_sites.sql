-- Migration: Add demo_sites and deployment_history tables
-- Description: Creates tables for tracking Vercel deployments and deployment history
-- Author: Phase 3, Task 4 - Vercel Deployment Integration
-- Date: 2025-11-04

-- Create demo_sites table
CREATE TABLE IF NOT EXISTS demo_sites (
    id SERIAL PRIMARY KEY,

    -- Foreign keys
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Vercel identifiers
    vercel_project_id VARCHAR(255),
    vercel_deployment_id VARCHAR(255),
    vercel_team_id VARCHAR(255),

    -- Project details
    project_name VARCHAR(255) NOT NULL,
    framework VARCHAR(50) NOT NULL,

    -- URLs
    url TEXT,
    preview_url TEXT,
    custom_domain VARCHAR(255),

    -- Deployment status
    status VARCHAR(50) NOT NULL DEFAULT 'queued',

    -- Build information
    build_time FLOAT,
    build_output TEXT,
    error_message TEXT,

    -- Framework detection
    framework_detected VARCHAR(50),

    -- Deployment regions (JSON array)
    regions JSON,

    -- Environment variables (JSON object)
    env_vars JSON,

    -- Files metadata
    files_count INTEGER,
    total_size_bytes INTEGER,

    -- SSL/Security
    ssl_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ssl_issued_at TIMESTAMP WITH TIME ZONE,

    -- Performance metrics
    deployment_duration FLOAT,
    lambda_invocations INTEGER NOT NULL DEFAULT 0,
    bandwidth_bytes INTEGER NOT NULL DEFAULT 0,

    -- Cost tracking
    estimated_cost FLOAT,
    actual_cost FLOAT,

    -- Analytics
    page_views INTEGER NOT NULL DEFAULT 0,
    unique_visitors INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    -- Deployment metadata (JSON)
    deployment_metadata JSON,
    build_metadata JSON,

    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_deployment_id INTEGER REFERENCES demo_sites(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deployed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Flags
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    auto_deploy BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes for demo_sites
CREATE INDEX IF NOT EXISTS idx_demo_sites_lead_id ON demo_sites(lead_id);
CREATE INDEX IF NOT EXISTS idx_demo_sites_vercel_project_id ON demo_sites(vercel_project_id);
CREATE INDEX IF NOT EXISTS idx_demo_sites_vercel_deployment_id ON demo_sites(vercel_deployment_id);
CREATE INDEX IF NOT EXISTS idx_demo_sites_project_name ON demo_sites(project_name);
CREATE INDEX IF NOT EXISTS idx_demo_sites_framework ON demo_sites(framework);
CREATE INDEX IF NOT EXISTS idx_demo_sites_custom_domain ON demo_sites(custom_domain);
CREATE INDEX IF NOT EXISTS idx_demo_sites_status ON demo_sites(status);
CREATE INDEX IF NOT EXISTS idx_demo_sites_created_at ON demo_sites(created_at);
CREATE INDEX IF NOT EXISTS idx_demo_sites_deployed_at ON demo_sites(deployed_at);
CREATE INDEX IF NOT EXISTS idx_demo_sites_deleted_at ON demo_sites(deleted_at);
CREATE INDEX IF NOT EXISTS idx_demo_sites_is_active ON demo_sites(is_active);
CREATE INDEX IF NOT EXISTS idx_demo_sites_is_deleted ON demo_sites(is_deleted);

-- Create deployment_history table
CREATE TABLE IF NOT EXISTS deployment_history (
    id SERIAL PRIMARY KEY,

    -- Foreign keys
    demo_site_id INTEGER NOT NULL REFERENCES demo_sites(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(50) NOT NULL,
    previous_status VARCHAR(50),
    new_status VARCHAR(50),

    -- Event metadata (JSON)
    event_data JSON,
    error_details TEXT,

    -- User tracking (if applicable)
    user_id INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for deployment_history
CREATE INDEX IF NOT EXISTS idx_deployment_history_demo_site_id ON deployment_history(demo_site_id);
CREATE INDEX IF NOT EXISTS idx_deployment_history_event_type ON deployment_history(event_type);
CREATE INDEX IF NOT EXISTS idx_deployment_history_created_at ON deployment_history(created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_demo_sites_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_demo_sites_updated_at
    BEFORE UPDATE ON demo_sites
    FOR EACH ROW
    EXECUTE FUNCTION update_demo_sites_updated_at();

-- Add comments to tables
COMMENT ON TABLE demo_sites IS 'Stores information about demo sites deployed to Vercel';
COMMENT ON TABLE deployment_history IS 'Tracks deployment events and status changes for audit purposes';

-- Add comments to key columns
COMMENT ON COLUMN demo_sites.lead_id IS 'Reference to the lead this demo site is for';
COMMENT ON COLUMN demo_sites.vercel_project_id IS 'Vercel project ID from Vercel API';
COMMENT ON COLUMN demo_sites.vercel_deployment_id IS 'Vercel deployment ID from Vercel API';
COMMENT ON COLUMN demo_sites.status IS 'Deployment status: queued, building, ready, error, cancelled';
COMMENT ON COLUMN demo_sites.framework IS 'Framework type: html, react, nextjs, vue, svelte';
COMMENT ON COLUMN demo_sites.regions IS 'JSON array of deployment regions (e.g., ["sfo1", "iad1"])';
COMMENT ON COLUMN demo_sites.is_deleted IS 'Soft delete flag - deployment marked as deleted but not removed';
COMMENT ON COLUMN deployment_history.event_type IS 'Event type: created, status_change, redeployed, updated, deleted, error';

-- Insert sample data (optional - for testing)
-- INSERT INTO demo_sites (lead_id, project_name, framework, status, vercel_project_id, url)
-- VALUES (1, 'demo-html-lead-1-20251104', 'html', 'ready', 'prj_test123', 'https://demo-html-lead-1.vercel.app');
