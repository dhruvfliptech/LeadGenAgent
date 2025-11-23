# Conversation Management Database Schema

**Version**: 1.0
**Date**: November 4, 2025
**Migrations**: 012_enable_pgvector.py, 013_create_conversations.py

## Overview

This schema supports a complete conversation management system for email-based lead communication with AI-powered reply suggestions. It includes vector embeddings for semantic search and comprehensive tracking of email threads.

---

## Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONVERSATIONS                            │
├──────────────────┬──────────────────────────────────────────────┤
│ PK  id           │ UUID (Primary Key)                           │
│ FK  lead_id      │ INTEGER → leads.id (CASCADE DELETE)          │
│     subject      │ TEXT (Email subject line)                    │
│     status       │ ENUM (active, needs_reply, waiting, archived)│
│     last_message_at │ TIMESTAMP WITH TIMEZONE                   │
│     created_at   │ TIMESTAMP WITH TIMEZONE (auto)               │
│     updated_at   │ TIMESTAMP WITH TIMEZONE (auto)               │
└──────────────────┴──────────────────────────────────────────────┘
                              │
                              │ 1:N (cascade delete)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERSATION_MESSAGES                         │
├──────────────────┬──────────────────────────────────────────────┤
│ PK  id           │ UUID (Primary Key)                           │
│ FK  conversation_id │ UUID → conversations.id (CASCADE DELETE)  │
│     direction    │ ENUM (inbound, outbound)                     │
│     content      │ TEXT (Plain text content)                    │
│     html_content │ TEXT (HTML version, nullable)                │
│     sent_at      │ TIMESTAMP WITH TIMEZONE                      │
│     sender_email │ TEXT                                         │
│     recipient_email │ TEXT                                      │
│     gmail_message_id │ TEXT (nullable, tracking)                │
│     postmark_message_id │ TEXT (nullable, tracking)             │
│     gmail_thread_id │ TEXT (nullable, threading)                │
│     headers      │ JSONB (Email headers, nullable)              │
│     attachments  │ JSONB (Attachment metadata, nullable)        │
│     embedding    │ VECTOR(1536) (Semantic search, nullable)     │
│     created_at   │ TIMESTAMP WITH TIMEZONE (auto)               │
└──────────────────┴──────────────────────────────────────────────┘
                              │
                              │ 1:N (cascade delete)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       AI_SUGGESTIONS                             │
├──────────────────┬──────────────────────────────────────────────┤
│ PK  id           │ UUID (Primary Key)                           │
│ FK  conversation_id │ UUID → conversations.id (CASCADE DELETE)  │
│ FK  in_reply_to_message_id │ UUID → conversation_messages.id    │
│     suggested_content │ TEXT (AI-generated plain text)          │
│     suggested_html_content │ TEXT (HTML version, nullable)      │
│     confidence_score │ FLOAT (0.0 to 1.0)                       │
│     sentiment_analysis │ JSONB (Sentiment, intent, tone)        │
│     context_used │ JSONB (Context AI used for generation)       │
│     model_used   │ VARCHAR(100) (AI model identifier)           │
│     tokens_used  │ INTEGER (Token usage tracking)               │
│     generation_cost │ FLOAT (Cost in USD)                       │
│     status       │ ENUM (pending, approved, rejected, edited)   │
│     user_feedback │ TEXT (Approval/rejection reason, nullable)  │
│     edited_content │ TEXT (User's edited version, nullable)     │
│     approved_at  │ TIMESTAMP WITH TIMEZONE (nullable)           │
│ FK  approved_by  │ INTEGER → users.id (SET NULL)                │
│     created_at   │ TIMESTAMP WITH TIMEZONE (auto)               │
│     updated_at   │ TIMESTAMP WITH TIMEZONE (auto)               │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## Entity Relationships

```
┌──────────┐       ┌────────────────┐       ┌──────────────────┐
│  leads   │ 1:N   │ conversations  │ 1:N   │ conversation_    │
│          ├───────┤                ├───────┤   messages       │
│  id      │       │ lead_id (FK)   │       │conversation_id(FK)│
└──────────┘       └────────────────┘       └──────────────────┘
                                                      │
                                                      │ 1:N
                                                      ↓
                                             ┌──────────────────┐
                                             │ ai_suggestions   │
                                             │                  │
                                             │in_reply_to_msg_id│
                                             │  (FK)            │
                                             └──────────────────┘
                                                      │
                                                      │ N:1
                   ┌──────────┐                      │
                   │  users   │ ◄────────────────────┘
                   │          │       approved_by (FK)
                   │  id      │
                   └──────────┘
```

---

## Indexes for Performance

### conversations

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `ix_conversations_lead_id` | lead_id | B-tree | Find conversations by lead |
| `ix_conversations_status` | status | B-tree | Filter by status |
| `ix_conversations_last_message_at` | last_message_at | B-tree | Sort by recency |
| `ix_conversations_created_at` | created_at | B-tree | Sort by creation |
| `ix_conversations_lead_status_last_message` | lead_id, status, last_message_at | Composite | Common filter+sort pattern |

### conversation_messages

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `ix_messages_conversation_id` | conversation_id | B-tree | Find messages by conversation |
| `ix_messages_sent_at` | sent_at | B-tree | Sort messages chronologically |
| `ix_messages_direction` | direction | B-tree | Filter inbound/outbound |
| `ix_messages_sender_email` | sender_email | B-tree | Find messages by sender |
| `ix_messages_recipient_email` | recipient_email | B-tree | Find messages by recipient |
| `ix_messages_gmail_message_id` | gmail_message_id | B-tree | Gmail API integration |
| `ix_messages_postmark_message_id` | postmark_message_id | B-tree | Postmark API integration |
| `ix_messages_gmail_thread_id` | gmail_thread_id | B-tree | Gmail threading |
| `ix_messages_conversation_sent` | conversation_id, sent_at | Composite | Get conversation thread |
| `ix_messages_embedding_cosine` | embedding | IVFFlat (vector) | Semantic similarity search |

### ai_suggestions

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `ix_suggestions_conversation_id` | conversation_id | B-tree | Find suggestions by conversation |
| `ix_suggestions_in_reply_to` | in_reply_to_message_id | B-tree | Find suggestion for message |
| `ix_suggestions_status` | status | B-tree | Filter by status |
| `ix_suggestions_confidence_score` | confidence_score | B-tree | Sort by confidence |
| `ix_suggestions_created_at` | created_at | B-tree | Sort by creation time |
| `ix_suggestions_approved_by` | approved_by | B-tree | Find approvals by user |
| `ix_suggestions_conversation_status` | conversation_id, status | Composite | Get pending suggestions |
| `ix_suggestions_unique_pending` | conversation_id, in_reply_to_message_id, status | Unique (partial) | Prevent duplicate pending |

---

## Enum Types

### conversation_status
- `active`: Ongoing conversation, no immediate action needed
- `needs_reply`: New inbound message received, user needs to respond
- `waiting`: Waiting for lead's response to user's message
- `archived`: Conversation completed or archived

### message_direction
- `inbound`: Message from lead to user
- `outbound`: Message from user to lead

### suggestion_status
- `pending`: AI suggestion generated, awaiting user action
- `approved`: User approved and sent the suggestion as-is
- `rejected`: User rejected the suggestion
- `edited`: User edited the suggestion before sending

---

## Vector Embeddings (pgvector)

### Configuration

- **Dimensions**: 1536 (OpenAI text-embedding-ada-002)
- **Index Type**: IVFFlat with 100 lists
- **Distance Metric**: Cosine distance (`vector_cosine_ops`)
- **Usage**: Semantic search for similar messages

### Vector Index Details

```sql
CREATE INDEX ix_messages_embedding_cosine
ON conversation_messages
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Why IVFFlat?**
- Faster searches on large datasets (>10K messages)
- Trade-off: ~95% recall for 10x speed improvement
- Good for production semantic search

**Alternative**: For smaller datasets (<10K), consider HNSW:
```sql
-- Optional: Better recall, slower writes
CREATE INDEX ix_messages_embedding_hnsw
ON conversation_messages
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## Data Flow Examples

### 1. User Sends Initial Email

```
User Action → Create Lead
           → Create Conversation (status: waiting)
           → Create ConversationMessage (direction: outbound)
           → Update conversation.last_message_at
```

### 2. Lead Replies (Gmail Monitoring)

```
Gmail API → Detect new email
         → Create ConversationMessage (direction: inbound)
         → Update conversation.status = needs_reply
         → Update conversation.last_message_at
         → Trigger AI analysis
         → Generate embedding for message
         → Create AISuggestion (status: pending)
         → Send WebSocket notification to frontend
```

### 3. User Approves AI Suggestion

```
User Click → Update ai_suggestion.status = approved
          → Set ai_suggestion.approved_by and approved_at
          → Create ConversationMessage (direction: outbound)
          → Send email via Postmark
          → Store postmark_message_id
          → Update conversation.status = waiting
          → Update conversation.last_message_at
```

### 4. User Edits & Sends Suggestion

```
User Edit → Update ai_suggestion.status = edited
         → Store edited_content
         → Set approved_by and approved_at
         → Create ConversationMessage with edited content
         → Send email via Postmark
         → Update conversation status
```

---

## Storage Estimates

### Per Conversation (Average)

| Component | Size | Count | Total |
|-----------|------|-------|-------|
| Conversation row | ~200 bytes | 1 | 200 B |
| Messages | ~2 KB each | 5 avg | 10 KB |
| Message embeddings | 6 KB each | 5 avg | 30 KB |
| AI suggestions | ~3 KB each | 3 avg | 9 KB |
| **Total per conversation** | | | **~49 KB** |

### Projected Growth

| Metric | 1K Conversations | 10K Conversations | 100K Conversations |
|--------|------------------|-------------------|--------------------|
| Total Storage | ~49 MB | ~490 MB | ~4.9 GB |
| Vector Index | ~30 MB | ~300 MB | ~3 GB |
| JSONB Fields | ~12 MB | ~120 MB | ~1.2 GB |
| **Total** | **~91 MB** | **~910 MB** | **~9.1 GB** |

**Recommendation**: Plan for 10-15 GB storage for 100K conversations including overhead.

---

## Backup Strategy

### Critical Tables (High Priority)

1. `conversations` - Core business data
2. `conversation_messages` - Email thread history
3. `ai_suggestions` - AI performance tracking

### Backup Frequency

- **Full Backup**: Daily at 2 AM
- **Incremental**: Every 4 hours
- **WAL Archiving**: Continuous (PITR enabled)
- **Retention**: 30 days full, 7 days incremental

### Recovery Scenarios

| Scenario | RTO | RPO | Method |
|----------|-----|-----|--------|
| Single conversation | 5 min | 0 | Point-in-time recovery |
| Corrupted table | 30 min | 4 hours | Latest incremental |
| Database failure | 2 hours | 24 hours | Latest full backup |
| Disaster recovery | 4 hours | 24 hours | Off-site backup restore |

---

## Performance Tuning

### Query Optimization

1. **Always use indexes**: Status, timestamps, foreign keys
2. **Limit results**: Use pagination for conversations/messages
3. **Partial indexes**: Status-specific indexes for hot paths
4. **Covering indexes**: Include frequently selected columns

### Connection Pooling

```python
# SQLAlchemy configuration
SQLALCHEMY_POOL_SIZE = 20          # Concurrent connections
SQLALCHEMY_MAX_OVERFLOW = 10       # Additional connections
SQLALCHEMY_POOL_TIMEOUT = 30       # Connection timeout (seconds)
SQLALCHEMY_POOL_RECYCLE = 3600     # Recycle connections hourly
```

### Monitoring Queries

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
ORDER BY idx_scan DESC;

-- Check table bloat
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions');

-- Check slow queries
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE query LIKE '%conversation%'
ORDER BY mean_time DESC
LIMIT 20;
```

---

## Maintenance Schedule

### Daily

- VACUUM ANALYZE on all conversation tables
- Monitor index bloat
- Check replication lag (if applicable)

### Weekly

- REINDEX conversation_messages (large table)
- Cleanup archived conversations older than 90 days
- Generate performance reports

### Monthly

- Full VACUUM (during maintenance window)
- Archive old conversations to cold storage
- Review and optimize slow queries
- Update vector index statistics

---

## Security Considerations

### Data Privacy

- Email content contains PII (personally identifiable information)
- GDPR compliance: Provide data export and deletion
- Encryption at rest: Enable PostgreSQL transparent data encryption
- Encryption in transit: Enforce SSL/TLS connections

### Access Control

```sql
-- Read-only user for analytics
CREATE ROLE conversation_reader;
GRANT SELECT ON conversations, conversation_messages, ai_suggestions
TO conversation_reader;

-- Application user (full CRUD)
CREATE ROLE conversation_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations, conversation_messages, ai_suggestions
TO conversation_app;

-- Admin user (schema changes)
CREATE ROLE conversation_admin WITH LOGIN SUPERUSER;
```

### Row-Level Security (Future)

```sql
-- Optional: Multi-tenant isolation
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversation_isolation ON conversations
  USING (lead_id IN (
    SELECT id FROM leads WHERE user_id = current_user_id()
  ));
```

---

## Migration Checklist

- [ ] Install pgvector extension (`apt install postgresql-15-pgvector`)
- [ ] Run migration 012: Enable pgvector
- [ ] Run migration 013: Create conversation tables
- [ ] Verify indexes created successfully
- [ ] Configure connection pooling
- [ ] Set up backup schedule
- [ ] Configure monitoring alerts
- [ ] Test vector similarity search
- [ ] Load test with sample data (1K+ conversations)
- [ ] Document rollback procedure

---

## Rollback Procedure

### If migrations fail:

```bash
# Check current revision
cd /Users/greenmachine2.0/Craigslist/backend
alembic current

# Rollback to previous version
alembic downgrade -1  # One step back
# or
alembic downgrade 011  # Specific version

# Verify tables dropped
psql -c "\dt" craigslist_db

# Re-apply if needed
alembic upgrade head
```

### Emergency rollback:

```sql
-- Manual cleanup if alembic fails
DROP TABLE IF EXISTS ai_suggestions CASCADE;
DROP TABLE IF EXISTS conversation_messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TYPE IF EXISTS suggestion_status;
DROP TYPE IF EXISTS message_direction;
DROP TYPE IF EXISTS conversation_status;
DROP EXTENSION IF EXISTS vector CASCADE;
```

---

**Last Updated**: November 4, 2025
**Maintained By**: Database Operations Team
**Next Review**: December 4, 2025
