# Database Operations Guide - Conversation Management System

**Version**: 1.0
**Date**: November 4, 2025
**Database**: PostgreSQL 15+ with pgvector extension

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Running Migrations](#running-migrations)
3. [Backup & Restore](#backup--restore)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [High Availability](#high-availability)
6. [Disaster Recovery](#disaster-recovery)
7. [Performance Optimization](#performance-optimization)
8. [Security & Access Control](#security--access-control)
9. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

1. PostgreSQL 15 or higher
2. pgvector extension
3. Python 3.10+
4. Alembic migration tool

### Install PostgreSQL and pgvector

#### Ubuntu/Debian
```bash
# Install PostgreSQL 15
sudo apt update
sudo apt install postgresql-15 postgresql-contrib-15

# Install pgvector
sudo apt install postgresql-15-pgvector

# Verify installation
sudo -u postgres psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

#### macOS (Homebrew)
```bash
# Install PostgreSQL
brew install postgresql@15

# Install pgvector
brew install pgvector

# Start PostgreSQL
brew services start postgresql@15
```

#### Docker (Recommended for Development)
```bash
# Pull PostgreSQL with pgvector
docker pull ankane/pgvector:latest

# Run container
docker run -d \
  --name craigslist-db \
  -e POSTGRES_DB=craigslist_db \
  -e POSTGRES_USER=craigslist_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  -v pgvector_data:/var/lib/postgresql/data \
  ankane/pgvector:latest
```

### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE craigslist_db;
CREATE USER craigslist_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE craigslist_db TO craigslist_user;

# Connect to database
\c craigslist_db

# Grant schema permissions
GRANT ALL ON SCHEMA public TO craigslist_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO craigslist_user;

# Verify pgvector is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

\q
```

### Configure Connection Pool

Create `/Users/greenmachine2.0/Craigslist/backend/app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://craigslist_user:secure_password@localhost:5432/craigslist_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Number of persistent connections
    max_overflow=10,           # Additional connections if pool is full
    pool_timeout=30,           # Wait time for connection (seconds)
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection health before use
    echo=False,                # Set to True for SQL query logging
    echo_pool=False,           # Set to True for connection pool logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://craigslist_user:secure_password@localhost:5432/craigslist_db

# Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Postmark (for sending emails)
POSTMARK_API_TOKEN=...
POSTMARK_FROM_EMAIL=...

# Gmail API (for monitoring replies)
GMAIL_CREDENTIALS_PATH=...
```

---

## Running Migrations

### Apply Migrations

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Check current revision
alembic current

# Upgrade to latest
alembic upgrade head

# Verify migrations applied
alembic history
```

### Expected Output

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 011 -> 012, Enable pgvector extension
INFO  [alembic.runtime.migration] Running upgrade 012 -> 013, Create conversation management tables
```

### Verify Tables Created

```bash
psql -U craigslist_user -d craigslist_db -c "\dt"
```

Expected tables:
- conversations
- conversation_messages
- ai_suggestions

### Verify Indexes

```sql
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
ORDER BY tablename, indexname;
```

### Rollback Migration (if needed)

```bash
# Rollback one step
alembic downgrade -1

# Rollback to specific version
alembic downgrade 011

# Rollback all (DANGEROUS)
alembic downgrade base
```

---

## Backup & Restore

### Automated Backup Script

Create `/Users/greenmachine2.0/Craigslist/backend/scripts/backup_db.sh`:

```bash
#!/bin/bash

# Configuration
DB_NAME="craigslist_db"
DB_USER="craigslist_user"
BACKUP_DIR="/var/backups/postgresql/craigslist"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Full backup (includes all data)
pg_dump -U $DB_USER -d $DB_NAME -F c -b -v \
  -f "$BACKUP_DIR/full_backup_$DATE.dump"

# Schema-only backup (for disaster recovery planning)
pg_dump -U $DB_USER -d $DB_NAME -s -F p \
  -f "$BACKUP_DIR/schema_backup_$DATE.sql"

# Conversation tables only (incremental)
pg_dump -U $DB_USER -d $DB_NAME -F c -b \
  -t conversations \
  -t conversation_messages \
  -t ai_suggestions \
  -f "$BACKUP_DIR/conversations_backup_$DATE.dump"

# Compress backups
gzip "$BACKUP_DIR/full_backup_$DATE.dump"
gzip "$BACKUP_DIR/schema_backup_$DATE.sql"
gzip "$BACKUP_DIR/conversations_backup_$DATE.dump"

# Delete old backups
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete

# Log success
echo "[$(date)] Backup completed: $BACKUP_DIR" >> /var/log/craigslist_backup.log

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/ s3://craigslist-backups/$(date +%Y/%m/) --recursive
```

Make executable:
```bash
chmod +x /Users/greenmachine2.0/Craigslist/backend/scripts/backup_db.sh
```

### Scheduled Backups (cron)

```bash
# Edit crontab
crontab -e

# Add backup schedule
# Daily full backup at 2 AM
0 2 * * * /Users/greenmachine2.0/Craigslist/backend/scripts/backup_db.sh

# Incremental every 4 hours
0 */4 * * * /Users/greenmachine2.0/Craigslist/backend/scripts/backup_conversations.sh
```

### Restore from Backup

#### Full Restore
```bash
# Stop application first
systemctl stop craigslist-backend

# Drop existing database
dropdb -U postgres craigslist_db

# Create fresh database
createdb -U postgres craigslist_db

# Restore from backup
pg_restore -U craigslist_user -d craigslist_db \
  -v /var/backups/postgresql/craigslist/full_backup_20251104_020000.dump.gz

# Verify restoration
psql -U craigslist_user -d craigslist_db -c "SELECT COUNT(*) FROM conversations;"

# Restart application
systemctl start craigslist-backend
```

#### Point-in-Time Recovery (PITR)

Enable WAL archiving in `postgresql.conf`:
```conf
# Enable WAL archiving
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
archive_timeout = 3600  # Archive every hour
```

Restore to specific time:
```bash
# Stop PostgreSQL
systemctl stop postgresql

# Restore base backup
pg_restore -d craigslist_db base_backup.dump

# Create recovery.conf
cat > /var/lib/postgresql/15/main/recovery.conf <<EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '2025-11-04 14:30:00'
EOF

# Start PostgreSQL (will enter recovery mode)
systemctl start postgresql

# Monitor recovery
tail -f /var/log/postgresql/postgresql-15-main.log
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. Database connections
2. Query performance
3. Table bloat
4. Replication lag (if applicable)
5. Disk space
6. Index usage

### Monitoring Script

Create `/Users/greenmachine2.0/Craigslist/backend/scripts/monitor_db.py`:

```python
#!/usr/bin/env python3
import psycopg2
from datetime import datetime
import json

def check_database_health():
    conn = psycopg2.connect(
        dbname="craigslist_db",
        user="craigslist_user",
        password="secure_password",
        host="localhost"
    )
    cur = conn.cursor()

    metrics = {}

    # 1. Connection count
    cur.execute("""
        SELECT count(*) FROM pg_stat_activity
        WHERE datname = 'craigslist_db'
    """)
    metrics['active_connections'] = cur.fetchone()[0]

    # 2. Table sizes
    cur.execute("""
        SELECT
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
    """)
    metrics['table_sizes'] = dict(cur.fetchall())

    # 3. Slow queries (last hour)
    cur.execute("""
        SELECT
            COUNT(*) as slow_query_count
        FROM pg_stat_statements
        WHERE mean_time > 1000  -- queries taking > 1 second
    """)
    result = cur.fetchone()
    metrics['slow_queries'] = result[0] if result else 0

    # 4. Index usage
    cur.execute("""
        SELECT
            COUNT(*) as unused_indexes
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
        AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
        AND idx_scan = 0
    """)
    metrics['unused_indexes'] = cur.fetchone()[0]

    # 5. Conversation metrics
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'needs_reply') as needs_reply,
            COUNT(*) FILTER (WHERE status = 'active') as active,
            COUNT(*) FILTER (WHERE status = 'waiting') as waiting
        FROM conversations
    """)
    conv_stats = cur.fetchone()
    metrics['conversation_stats'] = {
        'needs_reply': conv_stats[0],
        'active': conv_stats[1],
        'waiting': conv_stats[2]
    }

    cur.close()
    conn.close()

    # Alert if thresholds exceeded
    alerts = []

    if metrics['active_connections'] > 25:
        alerts.append(f"HIGH: {metrics['active_connections']} active connections (threshold: 25)")

    if metrics['slow_queries'] > 10:
        alerts.append(f"WARNING: {metrics['slow_queries']} slow queries detected")

    if metrics['unused_indexes'] > 5:
        alerts.append(f"INFO: {metrics['unused_indexes']} unused indexes found")

    # Output
    print(json.dumps({
        'timestamp': datetime.utcnow().isoformat(),
        'metrics': metrics,
        'alerts': alerts
    }, indent=2))

    return len(alerts) > 0

if __name__ == '__main__':
    import sys
    has_alerts = check_database_health()
    sys.exit(1 if has_alerts else 0)
```

### Alert Configuration

Create `/Users/greenmachine2.0/Craigslist/backend/config/alerts.yaml`:

```yaml
database_alerts:
  connection_pool:
    warning: 20
    critical: 25

  query_performance:
    slow_query_threshold_ms: 1000
    max_slow_queries: 10

  storage:
    warning_gb: 50
    critical_gb: 80

  replication:
    lag_warning_seconds: 10
    lag_critical_seconds: 60

notification_channels:
  - type: email
    to: admin@craigslist.com
    severity: critical

  - type: slack
    webhook: https://hooks.slack.com/services/...
    severity: warning

  - type: pagerduty
    api_key: ...
    severity: critical
```

---

## High Availability

### Replication Setup (Primary-Replica)

#### Primary Server Configuration

Edit `postgresql.conf` on primary:
```conf
# Replication settings
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
hot_standby = on
```

Create replication user:
```sql
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';
```

Edit `pg_hba.conf`:
```conf
# Allow replication connections
host    replication     replicator      replica_ip/32          md5
```

#### Replica Server Setup

```bash
# Stop PostgreSQL on replica
systemctl stop postgresql

# Clear data directory
rm -rf /var/lib/postgresql/15/main/*

# Base backup from primary
pg_basebackup -h primary_ip -D /var/lib/postgresql/15/main -U replicator -P -v -R -X stream -C -S replica_1

# Start replica
systemctl start postgresql
```

Verify replication:
```sql
-- On primary
SELECT * FROM pg_stat_replication;

-- On replica
SELECT * FROM pg_stat_wal_receiver;
```

### Failover Procedure

#### Automatic Failover (using repmgr)

Install repmgr:
```bash
apt install postgresql-15-repmgr
```

Configure `/etc/repmgr.conf`:
```conf
node_id=1
node_name='primary'
conninfo='host=primary_ip user=repmgr dbname=repmgr'
data_directory='/var/lib/postgresql/15/main'
failover='automatic'
promote_command='repmgr standby promote -f /etc/repmgr.conf'
follow_command='repmgr standby follow -f /etc/repmgr.conf'
```

#### Manual Failover

```bash
# On replica server
# 1. Promote replica to primary
pg_ctl promote -D /var/lib/postgresql/15/main

# 2. Update application to point to new primary
# Edit DATABASE_URL in .env

# 3. Restart application
systemctl restart craigslist-backend
```

---

## Disaster Recovery

### RTO/RPO Targets

| Scenario | RTO (Recovery Time) | RPO (Recovery Point) |
|----------|-------------------|---------------------|
| Single conversation | 5 minutes | 0 (PITR) |
| Corrupted table | 30 minutes | 4 hours |
| Database server failure | 2 hours | 24 hours |
| Data center disaster | 4 hours | 24 hours |

### Disaster Recovery Runbook

#### 1. Database Corruption

```bash
# Identify corrupted tables
SELECT * FROM pg_class WHERE relname IN ('conversations', 'conversation_messages');

# Drop and recreate from backup
DROP TABLE conversation_messages CASCADE;
pg_restore -t conversation_messages backup.dump

# Verify integrity
SELECT COUNT(*) FROM conversation_messages;
```

#### 2. Complete Database Loss

```bash
# 1. Provision new PostgreSQL server
# 2. Install pgvector extension
CREATE EXTENSION vector;

# 3. Restore from latest backup
pg_restore -d craigslist_db latest_backup.dump

# 4. Apply WAL files for PITR
# (see PITR section above)

# 5. Update DNS/load balancer to point to new server
# 6. Restart application
```

#### 3. Data Center Disaster

```bash
# 1. Failover to backup region
# 2. Restore from S3/cloud storage
aws s3 cp s3://craigslist-backups/latest/ ./backups/ --recursive

# 3. Restore database
pg_restore -d craigslist_db backups/full_backup.dump

# 4. Update application configuration
# 5. Run smoke tests
# 6. Switch DNS to disaster recovery site
```

---

## Performance Optimization

### Regular Maintenance Tasks

```sql
-- Daily: VACUUM ANALYZE
VACUUM ANALYZE conversations;
VACUUM ANALYZE conversation_messages;
VACUUM ANALYZE ai_suggestions;

-- Weekly: REINDEX (during low traffic)
REINDEX TABLE conversation_messages;

-- Monthly: VACUUM FULL (requires exclusive lock)
VACUUM FULL conversation_messages;
```

### Autovacuum Configuration

Edit `postgresql.conf`:
```conf
# Autovacuum settings
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 10s

# Vacuum thresholds
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

### Query Optimization

```sql
-- Enable query planning statistics
SET enable_seqscan = off;  -- Force index usage (testing only)

-- Analyze query plan
EXPLAIN ANALYZE
SELECT * FROM conversations
WHERE status = 'needs_reply'
ORDER BY last_message_at DESC
LIMIT 50;

-- Update statistics
ANALYZE conversations;
```

---

## Security & Access Control

### Database User Roles

```sql
-- Read-only user for analytics
CREATE ROLE analytics_reader WITH LOGIN PASSWORD 'analytics_pass';
GRANT CONNECT ON DATABASE craigslist_db TO analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;

-- Application user (CRUD operations)
CREATE ROLE app_user WITH LOGIN PASSWORD 'app_pass';
GRANT CONNECT ON DATABASE craigslist_db TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Admin user (schema changes, backups)
CREATE ROLE db_admin WITH LOGIN SUPERUSER PASSWORD 'admin_pass';
```

### SSL/TLS Encryption

```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
ssl_ca_file = '/etc/ssl/certs/ca.crt'
```

### Audit Logging

```conf
# postgresql.conf
log_connections = on
log_disconnections = on
log_duration = on
log_statement = 'ddl'  # Log schema changes
log_min_duration_statement = 1000  # Log queries > 1 second
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Pool Exhausted

```
Error: FATAL: remaining connection slots are reserved
```

Solution:
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND state_change < now() - interval '1 hour';
```

#### 2. Slow Vector Similarity Queries

```sql
-- Check vector index
SELECT * FROM pg_indexes WHERE indexname = 'ix_messages_embedding_cosine';

-- Rebuild vector index
DROP INDEX ix_messages_embedding_cosine;
CREATE INDEX ix_messages_embedding_cosine
ON conversation_messages USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### 3. Migration Failure

```bash
# Check migration status
alembic current

# Manual migration rollback
alembic downgrade -1

# Fix issue, then reapply
alembic upgrade head
```

---

**Last Updated**: November 4, 2025
**On-Call**: Database Operations Team
**Emergency Contact**: db-ops@craigslist.com
