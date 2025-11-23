-- Migration 005: Webhook Integration Tables
-- Phase 5, Task 3: Webhook Integrations
-- Created: 2025-11-04
-- Description: Creates tables for webhook queue, logs, and retry tracking

-- ============================================================================
-- webhook_queue: Queue for outgoing webhooks with retry logic
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_queue (
    id SERIAL PRIMARY KEY,

    -- Webhook destination
    webhook_url VARCHAR(500) NOT NULL,

    -- Webhook payload and headers
    payload JSONB NOT NULL,
    headers JSONB,

    -- Webhook type/event
    event_type VARCHAR(100) NOT NULL,

    -- Entity tracking (for reference)
    entity_type VARCHAR(50),
    entity_id INTEGER,

    -- Delivery status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status values: pending, sending, sent, failed, cancelled

    -- Retry logic
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMPTZ,

    -- Priority (higher = more important)
    priority INTEGER NOT NULL DEFAULT 0,

    -- Error tracking
    last_error VARCHAR(1000),
    error_details JSONB,

    -- Response tracking
    response_status INTEGER,
    response_body TEXT,
    response_time_ms INTEGER,

    -- Security
    signature VARCHAR(255),

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ
);

-- Indexes for webhook_queue
CREATE INDEX IF NOT EXISTS idx_webhook_queue_status ON webhook_queue(status);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_event_type ON webhook_queue(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_entity ON webhook_queue(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_priority ON webhook_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_retry_at ON webhook_queue(next_retry_at);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_created_at ON webhook_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_webhook_queue_sent_at ON webhook_queue(sent_at);

-- Composite index for queue processing
CREATE INDEX IF NOT EXISTS idx_webhook_queue_processing
    ON webhook_queue(status, priority DESC, next_retry_at);

-- Composite index for entity lookup
CREATE INDEX IF NOT EXISTS idx_webhook_queue_entity_lookup
    ON webhook_queue(entity_type, entity_id, created_at DESC);

-- Updated_at trigger for webhook_queue
CREATE OR REPLACE FUNCTION update_webhook_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_webhook_queue_updated_at
    BEFORE UPDATE ON webhook_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_webhook_queue_updated_at();


-- ============================================================================
-- webhook_logs: Comprehensive audit log of all webhook activity
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_logs (
    id SERIAL PRIMARY KEY,

    -- Direction and type
    direction VARCHAR(20) NOT NULL,  -- incoming, outgoing
    event_type VARCHAR(100),

    -- Request details
    webhook_url VARCHAR(500),
    method VARCHAR(10) NOT NULL,  -- GET, POST, PUT, DELETE
    headers JSONB,
    payload JSONB,

    -- Response details
    response_status INTEGER,
    response_headers JSONB,
    response_body JSONB,

    -- Performance metrics
    duration_ms INTEGER,

    -- Error tracking
    error_message VARCHAR(1000),
    error_details JSONB,

    -- Security
    signature_valid BOOLEAN,
    signature VARCHAR(255),

    -- Entity tracking (for reference)
    entity_type VARCHAR(50),
    entity_id INTEGER,

    -- Queue reference (for outgoing webhooks)
    webhook_queue_id INTEGER,

    -- Source tracking (for incoming webhooks)
    source_ip VARCHAR(45),  -- IPv4/IPv6
    user_agent VARCHAR(255),

    -- Metadata
    metadata JSONB,

    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for webhook_logs
CREATE INDEX IF NOT EXISTS idx_webhook_logs_direction ON webhook_logs(direction);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_event_type ON webhook_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_entity ON webhook_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_queue_id ON webhook_logs(webhook_queue_id);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_created_at ON webhook_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_response_status ON webhook_logs(response_status);

-- Composite index for lookup by direction and event type
CREATE INDEX IF NOT EXISTS idx_webhook_logs_lookup
    ON webhook_logs(direction, event_type, created_at DESC);

-- Composite index for entity lookup
CREATE INDEX IF NOT EXISTS idx_webhook_logs_entity_lookup
    ON webhook_logs(entity_type, entity_id, created_at DESC);

-- Composite index for status monitoring
CREATE INDEX IF NOT EXISTS idx_webhook_logs_status
    ON webhook_logs(response_status, created_at DESC);


-- ============================================================================
-- webhook_retry_history: Detailed retry attempt tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_retry_history (
    id SERIAL PRIMARY KEY,

    -- Reference to webhook queue item
    webhook_queue_id INTEGER NOT NULL,

    -- Retry attempt number
    attempt_number INTEGER NOT NULL,

    -- Attempt details
    status VARCHAR(50) NOT NULL,  -- sent, failed
    error_message VARCHAR(1000),
    response_status INTEGER,
    response_time_ms INTEGER,

    -- Timestamp
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for webhook_retry_history
CREATE INDEX IF NOT EXISTS idx_webhook_retry_queue ON webhook_retry_history(webhook_queue_id);
CREATE INDEX IF NOT EXISTS idx_webhook_retry_attempted ON webhook_retry_history(attempted_at DESC);

-- Composite index for queue retry lookup
CREATE INDEX IF NOT EXISTS idx_webhook_retry_queue_lookup
    ON webhook_retry_history(webhook_queue_id, attempted_at DESC);


-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE webhook_queue IS 'Queue for outgoing webhooks with retry logic and prioritization';
COMMENT ON TABLE webhook_logs IS 'Comprehensive audit log of all webhook activity (incoming and outgoing)';
COMMENT ON TABLE webhook_retry_history IS 'Detailed history of webhook retry attempts';

COMMENT ON COLUMN webhook_queue.status IS 'Webhook delivery status: pending, sending, sent, failed, cancelled';
COMMENT ON COLUMN webhook_queue.priority IS 'Priority level (0=normal, higher=more important)';
COMMENT ON COLUMN webhook_queue.retry_count IS 'Number of retry attempts made';
COMMENT ON COLUMN webhook_queue.next_retry_at IS 'Next scheduled retry time (NULL if no retry scheduled)';

COMMENT ON COLUMN webhook_logs.direction IS 'Webhook direction: incoming (from n8n) or outgoing (to n8n)';
COMMENT ON COLUMN webhook_logs.duration_ms IS 'Request duration in milliseconds';
COMMENT ON COLUMN webhook_logs.signature_valid IS 'Whether webhook signature was valid (for incoming webhooks)';


-- ============================================================================
-- Sample queries for webhook monitoring
-- ============================================================================

-- Get pending webhooks ready for processing
-- SELECT * FROM webhook_queue
-- WHERE status IN ('pending', 'failed')
--   AND retry_count < max_retries
--   AND (next_retry_at IS NULL OR next_retry_at <= NOW())
-- ORDER BY priority DESC, created_at ASC
-- LIMIT 10;

-- Get webhook statistics
-- SELECT
--     status,
--     COUNT(*) as count,
--     AVG(retry_count) as avg_retries,
--     MAX(retry_count) as max_retries
-- FROM webhook_queue
-- GROUP BY status;

-- Get recent webhook activity
-- SELECT
--     direction,
--     event_type,
--     response_status,
--     COUNT(*) as count,
--     AVG(duration_ms) as avg_duration_ms
-- FROM webhook_logs
-- WHERE created_at > NOW() - INTERVAL '24 hours'
-- GROUP BY direction, event_type, response_status
-- ORDER BY count DESC;

-- Get failed webhooks with retry history
-- SELECT
--     wq.*,
--     COUNT(wrh.id) as retry_attempts
-- FROM webhook_queue wq
-- LEFT JOIN webhook_retry_history wrh ON wq.id = wrh.webhook_queue_id
-- WHERE wq.status = 'failed'
-- GROUP BY wq.id
-- ORDER BY wq.created_at DESC;
