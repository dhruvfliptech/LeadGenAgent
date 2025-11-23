# Database Migration Quick Reference

**Date:** 2025-11-05
**Migrations:** 023, 024
**Tables Added:** auto_responses, response_variables, campaign_metrics, campaign_metrics_snapshots

---

## Pre-Flight Checklist

- [ ] Full database backup completed
- [ ] Schema backup completed
- [ ] Test database created
- [ ] Migrations tested on test database
- [ ] Rollback procedure documented
- [ ] Monitoring queries prepared
- [ ] Team notified of maintenance window

---

## Backup Commands

### Full Backup
```bash
pg_dump -h localhost -U postgres -d craigslist_db -F c -f backup_pre_migration_023_024_$(date +%Y%m%d_%H%M%S).dump
```

### Schema Only Backup
```bash
pg_dump -h localhost -U postgres -d craigslist_db -s -f backup_schema_$(date +%Y%m%d_%H%M%S).sql
```

### Verify Backup
```bash
pg_restore --list backup_pre_migration_023_024_*.dump | head -20
```

---

## Test Database Setup

```bash
# Create test database
createdb -U postgres craigslist_test

# Restore from production backup
pg_restore -h localhost -U postgres -d craigslist_test backup_pre_migration_023_024_*.dump

# Test migrations
cd /Users/greenmachine2.0/Craigslist/backend
PYTHONPATH=/Users/greenmachine2.0/Craigslist/backend alembic upgrade head

# Verify tables created
psql -U postgres -d craigslist_test -c "\dt auto_responses"
psql -U postgres -d craigslist_test -c "\dt response_variables"
psql -U postgres -d craigslist_test -c "\dt campaign_metrics"
psql -U postgres -d craigslist_test -c "\dt campaign_metrics_snapshots"
```

---

## Production Migration

### Apply Migrations
```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Check current migration version
alembic current

# Show pending migrations
alembic heads

# Apply migrations
alembic upgrade head

# Verify success
alembic current
```

### Expected Output
```
INFO  [alembic.runtime.migration] Running upgrade 022 -> 023, Create auto-response tables
INFO  [alembic.runtime.migration] Running upgrade 023 -> 024, Create campaign metrics tables
```

---

## Verification Queries

### Check Table Creation
```sql
-- Verify all tables exist
SELECT tablename
FROM pg_tables
WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY tablename;

-- Expected: 4 rows
```

### Check Indexes
```sql
-- Verify indexes created
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY tablename, indexname;

-- Expected: 11 indexes total
-- auto_responses: 6 indexes
-- response_variables: 1 index
-- campaign_metrics: 2 indexes
-- campaign_metrics_snapshots: 1 index
```

### Check Foreign Keys
```sql
-- Verify foreign key constraints
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('auto_responses', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY tc.table_name;

-- Expected:
-- auto_responses.lead_id -> leads.id
-- auto_responses.template_id -> response_templates.id
-- campaign_metrics.campaign_id -> campaigns.id
-- campaign_metrics_snapshots.campaign_id -> campaigns.id
-- campaign_metrics_snapshots.metrics_id -> campaign_metrics.id
```

### Check Table Sizes
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
FROM pg_tables
WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY bytes DESC;

-- Expected: All tables should be empty (8192 bytes)
```

---

## Rollback Procedure

### If Migration Fails

```bash
# Rollback to version 022
alembic downgrade 022_create_n8n_workflow_system

# Verify rollback
alembic current
```

### If Catastrophic Failure

```bash
# Stop application
systemctl stop craigslist-backend  # or equivalent

# Restore from backup
pg_restore -h localhost -U postgres -d craigslist_db -c backup_pre_migration_023_024_*.dump

# Verify restoration
psql -U postgres -d craigslist_db -c "SELECT version();"

# Restart application
systemctl start craigslist-backend
```

---

## Post-Migration Monitoring

### Monitor Table Growth (First 24 Hours)

```sql
-- Run every hour
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY n_tup_ins DESC;
```

### Monitor Index Usage

```sql
-- Run daily for first week
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('auto_responses', 'response_variables', 'campaign_metrics', 'campaign_metrics_snapshots')
ORDER BY idx_scan DESC;
```

### Monitor Query Performance

```sql
-- Requires pg_stat_statements extension
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE query LIKE '%auto_responses%'
   OR query LIKE '%campaign_metrics%'
   OR query LIKE '%response_variables%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Performance Baselines

### Expected Index Scan Ratios

After 1 week of operation:

- `idx_auto_response_lead_template`: High usage (>1000 scans/day)
- `idx_auto_response_status_scheduled`: High usage (>500 scans/day)
- `idx_auto_response_engagement`: Medium usage (>100 scans/day)
- `idx_metrics_rates`: High usage (>1000 scans/day)
- `idx_snapshot_campaign_time`: Medium usage (>100 scans/day)

### Alert Thresholds

```sql
-- Create monitoring view
CREATE OR REPLACE VIEW campaign_metrics_alerts AS
SELECT
    cm.campaign_id,
    c.name AS campaign_name,
    cm.delivery_rate,
    cm.bounce_rate,
    cm.spam_rate,
    cm.unsubscribe_rate,
    CASE
        WHEN cm.bounce_rate > 5 THEN 'HIGH_BOUNCE_RATE'
        WHEN cm.spam_rate > 0.1 THEN 'HIGH_SPAM_RATE'
        WHEN cm.unsubscribe_rate > 0.5 THEN 'HIGH_UNSUBSCRIBE_RATE'
        WHEN cm.delivery_rate < 95 THEN 'LOW_DELIVERY_RATE'
        ELSE 'OK'
    END AS alert_status
FROM campaign_metrics cm
JOIN campaigns c ON cm.campaign_id = c.id
WHERE cm.total_sent > 100;

-- Check alerts
SELECT * FROM campaign_metrics_alerts WHERE alert_status != 'OK';
```

---

## Maintenance Schedule

### Daily Tasks
- [ ] Check table sizes
- [ ] Review query performance
- [ ] Check for failed auto-responses (status = 'failed')

### Weekly Tasks
- [ ] Review index usage statistics
- [ ] Analyze table statistics (ANALYZE)
- [ ] Review campaign metrics trends

### Monthly Tasks
- [ ] Vacuum full on large tables (if needed)
- [ ] Review and optimize slow queries
- [ ] Archive old campaign metrics snapshots (>90 days)

---

## Common Queries for Operations

### Check Auto-Response Queue
```sql
SELECT
    status,
    COUNT(*) AS count,
    MIN(scheduled_at) AS oldest_scheduled,
    MAX(scheduled_at) AS newest_scheduled
FROM auto_responses
WHERE status IN ('pending', 'scheduled')
GROUP BY status;
```

### Failed Auto-Responses
```sql
SELECT
    ar.id,
    ar.lead_id,
    l.title AS lead_title,
    ar.status,
    ar.error_message,
    ar.retry_count,
    ar.created_at
FROM auto_responses ar
JOIN leads l ON ar.lead_id = l.id
WHERE ar.status = 'failed'
    AND ar.created_at > NOW() - INTERVAL '24 hours'
ORDER BY ar.created_at DESC
LIMIT 20;
```

### Campaign Performance Summary
```sql
SELECT
    c.id,
    c.name,
    cm.total_sent,
    cm.delivery_rate,
    cm.open_rate,
    cm.click_rate,
    cm.conversion_rate,
    cm.roi,
    CASE
        WHEN cm.delivery_rate >= 95 AND cm.open_rate >= 20 AND cm.click_rate >= 2.5 THEN 'High Performing'
        WHEN cm.bounce_rate > 5 OR cm.spam_rate > 0.1 THEN 'Needs Attention'
        ELSE 'Normal'
    END AS performance_status
FROM campaigns c
JOIN campaign_metrics cm ON c.id = cm.campaign_id
WHERE c.status IN ('running', 'completed')
ORDER BY cm.roi DESC
LIMIT 20;
```

### Metrics Snapshot Timeline
```sql
SELECT
    cms.campaign_id,
    c.name,
    cms.snapshot_at,
    cms.snapshot_type,
    cms.total_sent,
    cms.open_rate,
    cms.click_rate,
    cms.conversion_rate
FROM campaign_metrics_snapshots cms
JOIN campaigns c ON cms.campaign_id = c.id
WHERE cms.campaign_id = :campaign_id
ORDER BY cms.snapshot_at;
```

---

## Troubleshooting

### Migration Failed: Foreign Key Violation

**Error:** `foreign key constraint fails`

**Resolution:**
```sql
-- Check if referenced tables exist
SELECT tablename FROM pg_tables WHERE tablename IN ('leads', 'response_templates', 'campaigns');

-- If missing, create them first or check migration order
```

### Migration Failed: Table Already Exists

**Error:** `relation "auto_responses" already exists`

**Resolution:**
```bash
# Check current version
alembic current

# If stuck, stamp to correct version
alembic stamp 022_create_n8n_workflow_system

# Try upgrade again
alembic upgrade head
```

### High Table Bloat

**Symptom:** Table size growing rapidly

**Resolution:**
```sql
-- Check bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_table_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
    n_dead_tup
FROM pg_stat_user_tables
WHERE tablename IN ('auto_responses', 'campaign_metrics_snapshots')
ORDER BY n_dead_tup DESC;

-- If high dead tuples, vacuum
VACUUM ANALYZE auto_responses;
VACUUM ANALYZE campaign_metrics_snapshots;
```

### Slow Queries

**Symptom:** Query execution time > 1 second

**Resolution:**
```sql
-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM auto_responses
WHERE lead_id = 123 AND status = 'pending';

-- If missing index, create it
CREATE INDEX idx_custom ON auto_responses(lead_id, status);
```

---

## Emergency Contacts

- **Database Administrator:** [Your Name]
- **Backend Team Lead:** [Team Lead Name]
- **On-Call Engineer:** [On-Call Contact]
- **Escalation:** [Manager Contact]

---

## Migration Completion Checklist

- [ ] Migrations 023 and 024 applied successfully
- [ ] All 4 tables created (verified with SQL)
- [ ] All indexes created (11 total)
- [ ] Foreign keys validated (5 total)
- [ ] Sample data inserted and retrieved successfully
- [ ] Application restarted and tested
- [ ] Monitoring queries executed
- [ ] Performance baselines recorded
- [ ] Team notified of completion
- [ ] Documentation updated
- [ ] Post-migration review scheduled (1 week)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Next Review:** After migration deployment
