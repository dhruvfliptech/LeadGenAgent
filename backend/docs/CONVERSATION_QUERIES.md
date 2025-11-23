# Conversation Management - Sample Queries & Operations

**Version**: 1.0
**Date**: November 4, 2025
**Related Files**:
- Models: `/Users/greenmachine2.0/Craigslist/backend/app/models/conversation.py`
- Schema: `/Users/greenmachine2.0/Craigslist/backend/docs/CONVERSATION_SCHEMA.md`

---

## Table of Contents

1. [Basic CRUD Operations](#basic-crud-operations)
2. [Common Queries](#common-queries)
3. [Advanced Queries](#advanced-queries)
4. [Vector Similarity Search](#vector-similarity-search)
5. [Analytics & Reporting](#analytics--reporting)
6. [Maintenance Queries](#maintenance-queries)
7. [Performance Monitoring](#performance-monitoring)

---

## Basic CRUD Operations

### Create a New Conversation

```python
from app.models.conversation import Conversation, ConversationMessage, MessageDirection
from datetime import datetime

# Create conversation when user sends first email
conversation = Conversation(
    lead_id=123,
    subject="Website Improvements for Your Business",
    status=ConversationStatus.WAITING,
    last_message_at=datetime.utcnow()
)
db.add(conversation)
db.commit()

# Add initial outbound message
initial_message = conversation.add_message(
    direction=MessageDirection.OUTBOUND,
    content="Hi John, I noticed your website could benefit from...",
    sender_email="user@craigleads.com",
    recipient_email="john@example.com",
    postmark_message_id="pm_12345678"
)
db.add(initial_message)
db.commit()
```

### Add Inbound Message (Lead Reply)

```python
from app.models.conversation import MessageDirection, ConversationStatus

# When Gmail monitoring detects a reply
conversation = db.query(Conversation).filter_by(id=conversation_id).first()

inbound_message = conversation.add_message(
    direction=MessageDirection.INBOUND,
    content="Thanks! I'm interested. Can you show me examples?",
    sender_email="john@example.com",
    recipient_email="user@craigleads.com",
    gmail_message_id="1234567890abcdef",
    gmail_thread_id="thread_abc123",
    headers={
        "message-id": "<abc@gmail.com>",
        "in-reply-to": "<xyz@postmarkapp.com>",
        "subject": "Re: Website Improvements for Your Business"
    }
)
db.add(inbound_message)
db.commit()

# Status is automatically updated to NEEDS_REPLY by add_message()
```

### Create AI Suggestion

```python
from app.models.conversation import AISuggestion, SuggestionStatus

# Generate AI suggestion for the inbound message
suggestion = AISuggestion(
    conversation_id=conversation.id,
    in_reply_to_message_id=inbound_message.id,
    suggested_content="Hi John! Absolutely. I've analyzed your website and created...",
    confidence_score=0.92,
    sentiment_analysis={
        "sentiment": "positive",
        "intent": "requesting_information",
        "tone": "interested",
        "urgency": "medium"
    },
    context_used={
        "previous_messages": 1,
        "lead_website_data": True,
        "similar_conversations": 3
    },
    model_used="gpt-4",
    tokens_used=450,
    generation_cost=0.0135,
    status=SuggestionStatus.PENDING
)
db.add(suggestion)
db.commit()
```

### Approve AI Suggestion

```python
# User approves the suggestion
suggestion = db.query(AISuggestion).filter_by(id=suggestion_id).first()
suggestion.approve(user_id=current_user.id, feedback="Looks good!")

# Send the email and create outbound message
outbound_message = conversation.add_message(
    direction=MessageDirection.OUTBOUND,
    content=suggestion.suggested_content,
    sender_email="user@craigleads.com",
    recipient_email="john@example.com",
    postmark_message_id="pm_23456789"
)

db.commit()
```

### Edit and Send Suggestion

```python
# User edits the suggestion before sending
edited_content = "Hi John! I've analyzed your site and found 3 key improvements..."

suggestion.edit(
    edited_content=edited_content,
    user_id=current_user.id,
    feedback="Added more specifics about improvements"
)

# Send the edited version
outbound_message = conversation.add_message(
    direction=MessageDirection.OUTBOUND,
    content=edited_content,  # Use edited version
    sender_email="user@craigleads.com",
    recipient_email="john@example.com",
    postmark_message_id="pm_34567890"
)

db.commit()
```

### Archive Conversation

```python
conversation = db.query(Conversation).filter_by(id=conversation_id).first()
conversation.archive()
db.commit()
```

---

## Common Queries

### Get All Conversations Needing Reply

```python
from app.models.conversation import get_conversations_needing_reply

# Using utility function
conversations = get_conversations_needing_reply(db, limit=50)

# Or directly with SQLAlchemy
from app.models.conversation import Conversation, ConversationStatus

conversations = db.query(Conversation)\
    .filter(Conversation.status == ConversationStatus.NEEDS_REPLY)\
    .order_by(Conversation.last_message_at.desc())\
    .limit(50)\
    .all()

# With lead information
from app.models.leads import Lead

conversations = db.query(Conversation)\
    .join(Lead)\
    .filter(Conversation.status == ConversationStatus.NEEDS_REPLY)\
    .options(joinedload(Conversation.lead))\
    .order_by(Conversation.last_message_at.desc())\
    .all()
```

### Get Conversation with Full Thread

```python
from sqlalchemy.orm import joinedload

# Fetch conversation with all messages and suggestions
conversation = db.query(Conversation)\
    .filter_by(id=conversation_id)\
    .options(
        joinedload(Conversation.messages),
        joinedload(Conversation.ai_suggestions),
        joinedload(Conversation.lead)
    )\
    .first()

# Messages are automatically sorted by sent_at (defined in model relationship)
for message in conversation.messages:
    print(f"{message.direction.value}: {message.content[:50]}...")
```

### Get Pending AI Suggestions

```python
from app.models.conversation import get_pending_ai_suggestions

# Using utility function
suggestions = get_pending_ai_suggestions(db, limit=50)

# Or with conversation context
from app.models.conversation import AISuggestion, SuggestionStatus

suggestions = db.query(AISuggestion)\
    .join(Conversation)\
    .join(Lead)\
    .filter(AISuggestion.status == SuggestionStatus.PENDING)\
    .options(
        joinedload(AISuggestion.conversation),
        joinedload(AISuggestion.in_reply_to_message)
    )\
    .order_by(AISuggestion.created_at.desc())\
    .all()
```

### Get Conversations by Lead

```python
# All conversations for a specific lead
conversations = db.query(Conversation)\
    .filter(Conversation.lead_id == lead_id)\
    .order_by(Conversation.last_message_at.desc())\
    .all()

# Active conversations only
active_conversations = db.query(Conversation)\
    .filter(
        Conversation.lead_id == lead_id,
        Conversation.status.in_([
            ConversationStatus.ACTIVE,
            ConversationStatus.NEEDS_REPLY,
            ConversationStatus.WAITING
        ])
    )\
    .all()
```

### Search Conversations by Subject or Content

```python
from sqlalchemy import or_

search_term = "website improvements"

# Search in subject and message content
conversations = db.query(Conversation)\
    .join(ConversationMessage)\
    .filter(
        or_(
            Conversation.subject.ilike(f"%{search_term}%"),
            ConversationMessage.content.ilike(f"%{search_term}%")
        )
    )\
    .distinct()\
    .all()
```

---

## Advanced Queries

### Get Conversation Summary Statistics

```python
from sqlalchemy import func, case

# Summary stats for all conversations
stats = db.query(
    func.count(Conversation.id).label('total_conversations'),
    func.count(case([(Conversation.status == ConversationStatus.NEEDS_REPLY, 1)])).label('needs_reply'),
    func.count(case([(Conversation.status == ConversationStatus.ACTIVE, 1)])).label('active'),
    func.count(case([(Conversation.status == ConversationStatus.WAITING, 1)])).label('waiting'),
    func.count(case([(Conversation.status == ConversationStatus.ARCHIVED, 1)])).label('archived'),
).first()

print(f"Total: {stats.total_conversations}")
print(f"Needs Reply: {stats.needs_reply}")
print(f"Active: {stats.active}")
```

### Get Average Response Time

```python
from sqlalchemy import func, extract

# Calculate average time between inbound and outbound messages
response_times = db.query(
    Conversation.id,
    Lead.title.label('lead_title'),
    func.avg(
        extract('epoch',
            func.lead(ConversationMessage.sent_at).over(
                partition_by=ConversationMessage.conversation_id,
                order_by=ConversationMessage.sent_at
            ) - ConversationMessage.sent_at
        )
    ).label('avg_response_seconds')
)\
.join(ConversationMessage)\
.join(Lead)\
.filter(ConversationMessage.direction == MessageDirection.INBOUND)\
.group_by(Conversation.id, Lead.title)\
.all()

for conv in response_times:
    hours = conv.avg_response_seconds / 3600 if conv.avg_response_seconds else 0
    print(f"{conv.lead_title}: {hours:.1f} hours average response time")
```

### Get High-Confidence Approved Suggestions

```python
# Find AI suggestions that were approved with high confidence
# This helps identify successful AI patterns

high_confidence_approved = db.query(AISuggestion)\
    .filter(
        AISuggestion.status == SuggestionStatus.APPROVED,
        AISuggestion.confidence_score >= 0.85
    )\
    .order_by(AISuggestion.confidence_score.desc())\
    .all()

# Calculate approval rate by confidence bucket
from sqlalchemy import case

approval_by_confidence = db.query(
    case(
        [(AISuggestion.confidence_score >= 0.85, 'high')],
        [(AISuggestion.confidence_score >= 0.70, 'medium')],
        else_='low'
    ).label('confidence_level'),
    func.count(AISuggestion.id).label('total'),
    func.count(case([(AISuggestion.status == SuggestionStatus.APPROVED, 1)])).label('approved'),
    (func.count(case([(AISuggestion.status == SuggestionStatus.APPROVED, 1)])).cast(Float) /
     func.count(AISuggestion.id) * 100).label('approval_rate')
)\
.group_by('confidence_level')\
.all()
```

### Get Most Active Conversations

```python
# Conversations with the most message exchanges
most_active = db.query(
    Conversation.id,
    Conversation.subject,
    Lead.title.label('lead_title'),
    func.count(ConversationMessage.id).label('message_count')
)\
.join(ConversationMessage)\
.join(Lead)\
.group_by(Conversation.id, Conversation.subject, Lead.title)\
.order_by(func.count(ConversationMessage.id).desc())\
.limit(20)\
.all()
```

### Get Conversations with Unread Messages

```python
from datetime import datetime, timedelta

# Conversations with messages in last 24 hours that need reply
recent_cutoff = datetime.utcnow() - timedelta(hours=24)

unread_conversations = db.query(Conversation)\
    .filter(
        Conversation.status == ConversationStatus.NEEDS_REPLY,
        Conversation.last_message_at >= recent_cutoff
    )\
    .order_by(Conversation.last_message_at.desc())\
    .all()
```

### Get Messages with Attachments

```python
# Find all messages that have attachments
messages_with_attachments = db.query(ConversationMessage)\
    .filter(ConversationMessage.attachments.isnot(None))\
    .filter(ConversationMessage.attachments != [])\
    .all()

# Count attachments per conversation
attachment_counts = db.query(
    Conversation.id,
    Conversation.subject,
    func.count(ConversationMessage.id).label('message_count'),
    func.sum(
        func.jsonb_array_length(ConversationMessage.attachments)
    ).label('total_attachments')
)\
.join(ConversationMessage)\
.filter(ConversationMessage.attachments.isnot(None))\
.group_by(Conversation.id, Conversation.subject)\
.all()
```

---

## Vector Similarity Search

### Find Similar Messages (Semantic Search)

```python
from app.models.conversation import find_similar_messages
import openai

# 1. Generate embedding for query
query = "How much does website redesign cost?"
response = openai.Embedding.create(
    input=query,
    model="text-embedding-ada-002"
)
query_embedding = response['data'][0]['embedding']

# 2. Find similar messages using utility function
similar_messages = find_similar_messages(
    db=db,
    embedding=query_embedding,
    limit=10,
    min_similarity=0.7  # 70% similarity threshold
)

# 3. Display results
for message in similar_messages:
    print(f"Similarity: {1 - message.embedding.cosine_distance(query_embedding):.2%}")
    print(f"Content: {message.content[:100]}...")
    print(f"Conversation: {message.conversation.subject}")
    print("---")
```

### Store Embedding for New Message

```python
import openai

# When creating a new message, generate and store embedding
message = ConversationMessage(
    conversation_id=conversation_id,
    direction=MessageDirection.INBOUND,
    content="Thanks for the info! What's your pricing?",
    sender_email="john@example.com",
    recipient_email="user@craigleads.com",
    sent_at=datetime.utcnow()
)

# Generate embedding
response = openai.Embedding.create(
    input=message.content,
    model="text-embedding-ada-002"
)
embedding = response['data'][0]['embedding']

# Store embedding
message.set_embedding(embedding)

db.add(message)
db.commit()
```

### Bulk Generate Embeddings for Existing Messages

```python
import openai
from tqdm import tqdm

# Find messages without embeddings
messages_without_embeddings = db.query(ConversationMessage)\
    .filter(ConversationMessage.embedding.is_(None))\
    .all()

print(f"Found {len(messages_without_embeddings)} messages without embeddings")

# Generate embeddings in batches (OpenAI allows up to 2048 texts per request)
batch_size = 100

for i in tqdm(range(0, len(messages_without_embeddings), batch_size)):
    batch = messages_without_embeddings[i:i+batch_size]
    texts = [msg.content for msg in batch]

    # Generate embeddings for batch
    response = openai.Embedding.create(
        input=texts,
        model="text-embedding-ada-002"
    )

    # Store embeddings
    for msg, embedding_data in zip(batch, response['data']):
        msg.set_embedding(embedding_data['embedding'])

    db.commit()

print("Embeddings generated successfully!")
```

### Find Conversations on Similar Topics

```python
# Find conversations discussing similar topics
def find_similar_conversations(db, query_text, limit=10):
    # Generate embedding for query
    response = openai.Embedding.create(
        input=query_text,
        model="text-embedding-ada-002"
    )
    query_embedding = response['data'][0]['embedding']

    # Find similar messages grouped by conversation
    similar_conversations = db.query(
        Conversation.id,
        Conversation.subject,
        func.min(ConversationMessage.embedding.cosine_distance(query_embedding)).label('min_distance'),
        func.count(ConversationMessage.id).label('relevant_messages')
    )\
    .join(ConversationMessage)\
    .filter(ConversationMessage.embedding.isnot(None))\
    .group_by(Conversation.id, Conversation.subject)\
    .order_by('min_distance')\
    .limit(limit)\
    .all()

    return similar_conversations

# Usage
results = find_similar_conversations(db, "website pricing and costs", limit=5)
for conv in results:
    similarity = 1 - conv.min_distance
    print(f"Similarity: {similarity:.2%} - {conv.subject}")
    print(f"  Relevant messages: {conv.relevant_messages}")
```

---

## Analytics & Reporting

### Daily Conversation Report

```python
from datetime import datetime, timedelta
from sqlalchemy import func, case

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

# Get daily statistics
daily_stats = db.query(
    func.count(Conversation.id).label('new_conversations'),
    func.count(case([(Conversation.status == ConversationStatus.NEEDS_REPLY, 1)])).label('needs_reply'),
    func.count(ConversationMessage.id).label('total_messages'),
    func.count(case([(ConversationMessage.direction == MessageDirection.INBOUND, 1)])).label('inbound_messages'),
    func.count(case([(ConversationMessage.direction == MessageDirection.OUTBOUND, 1)])).label('outbound_messages'),
    func.count(AISuggestion.id).label('ai_suggestions_generated'),
    func.count(case([(AISuggestion.status == SuggestionStatus.APPROVED, 1)])).label('suggestions_approved'),
    func.avg(AISuggestion.confidence_score).label('avg_confidence')
)\
.select_from(Conversation)\
.outerjoin(ConversationMessage)\
.outerjoin(AISuggestion)\
.filter(func.date(Conversation.created_at) == today)\
.first()

print(f"Daily Report for {today}")
print(f"New Conversations: {daily_stats.new_conversations}")
print(f"Needs Reply: {daily_stats.needs_reply}")
print(f"Total Messages: {daily_stats.total_messages}")
print(f"AI Approval Rate: {daily_stats.suggestions_approved / daily_stats.ai_suggestions_generated * 100:.1f}%")
```

### AI Suggestion Performance

```python
# Analyze AI suggestion performance over time
ai_performance = db.query(
    func.date(AISuggestion.created_at).label('date'),
    func.count(AISuggestion.id).label('total_generated'),
    func.count(case([(AISuggestion.status == SuggestionStatus.APPROVED, 1)])).label('approved'),
    func.count(case([(AISuggestion.status == SuggestionStatus.EDITED, 1)])).label('edited'),
    func.count(case([(AISuggestion.status == SuggestionStatus.REJECTED, 1)])).label('rejected'),
    func.avg(AISuggestion.confidence_score).label('avg_confidence'),
    func.sum(AISuggestion.generation_cost).label('total_cost')
)\
.group_by(func.date(AISuggestion.created_at))\
.order_by(func.date(AISuggestion.created_at).desc())\
.limit(30)\
.all()

for day in ai_performance:
    approval_rate = (day.approved / day.total_generated * 100) if day.total_generated > 0 else 0
    print(f"{day.date}: {day.total_generated} suggestions, {approval_rate:.1f}% approved, ${day.total_cost:.2f}")
```

### Response Rate by Lead Category

```python
# Calculate response rates by lead category
response_rates = db.query(
    Lead.category,
    func.count(distinct(Conversation.id)).label('conversations_started'),
    func.count(distinct(
        case([(ConversationMessage.direction == MessageDirection.INBOUND, Conversation.id)])
    )).label('conversations_with_reply'),
    (func.count(distinct(
        case([(ConversationMessage.direction == MessageDirection.INBOUND, Conversation.id)])
    )).cast(Float) / func.count(distinct(Conversation.id)) * 100).label('response_rate')
)\
.join(Conversation)\
.outerjoin(ConversationMessage)\
.group_by(Lead.category)\
.order_by('response_rate desc')\
.all()

print("\nResponse Rate by Category:")
for row in response_rates:
    print(f"{row.category}: {row.response_rate:.1f}% ({row.conversations_with_reply}/{row.conversations_started})")
```

### Cost Analysis

```python
# Calculate AI costs per conversation
cost_per_conversation = db.query(
    Conversation.id,
    Conversation.subject,
    Lead.title.label('lead_title'),
    func.count(AISuggestion.id).label('suggestions_count'),
    func.sum(AISuggestion.generation_cost).label('total_cost'),
    func.sum(AISuggestion.tokens_used).label('total_tokens')
)\
.join(Lead)\
.outerjoin(AISuggestion)\
.group_by(Conversation.id, Conversation.subject, Lead.title)\
.order_by(func.sum(AISuggestion.generation_cost).desc())\
.limit(20)\
.all()

print("\nTop 20 Most Expensive Conversations:")
for conv in cost_per_conversation:
    print(f"{conv.lead_title}: ${conv.total_cost:.2f} ({conv.suggestions_count} suggestions, {conv.total_tokens} tokens)")
```

---

## Maintenance Queries

### Archive Old Conversations

```python
from datetime import datetime, timedelta

# Archive conversations inactive for 90+ days
cutoff_date = datetime.utcnow() - timedelta(days=90)

archived_count = db.query(Conversation)\
    .filter(
        Conversation.status != ConversationStatus.ARCHIVED,
        Conversation.last_message_at < cutoff_date
    )\
    .update({'status': ConversationStatus.ARCHIVED, 'updated_at': datetime.utcnow()})

db.commit()
print(f"Archived {archived_count} old conversations")
```

### Delete Conversations (GDPR Right to Deletion)

```python
# Delete all conversations for a specific lead
lead_id = 123

db.query(Conversation)\
    .filter(Conversation.lead_id == lead_id)\
    .delete()

db.commit()
print(f"Deleted all conversations for lead {lead_id}")

# Note: CASCADE delete will automatically remove:
# - conversation_messages
# - ai_suggestions
```

### Cleanup Orphaned Data

```python
# Find and clean up any orphaned records (shouldn't happen with CASCADE, but good to check)

# Check for messages without conversations
orphaned_messages = db.query(ConversationMessage)\
    .outerjoin(Conversation)\
    .filter(Conversation.id.is_(None))\
    .count()

if orphaned_messages > 0:
    print(f"WARNING: Found {orphaned_messages} orphaned messages!")
    # Cleanup if needed
    db.query(ConversationMessage)\
        .outerjoin(Conversation)\
        .filter(Conversation.id.is_(None))\
        .delete(synchronize_session=False)
    db.commit()
```

### Vacuum and Analyze

```sql
-- Run from psql or via raw SQL
VACUUM ANALYZE conversations;
VACUUM ANALYZE conversation_messages;
VACUUM ANALYZE ai_suggestions;

-- Full vacuum (requires exclusive lock, run during maintenance window)
VACUUM FULL conversations;
VACUUM FULL conversation_messages;
VACUUM FULL ai_suggestions;

-- Reindex for optimal performance
REINDEX TABLE conversations;
REINDEX TABLE conversation_messages;
REINDEX TABLE ai_suggestions;
```

---

## Performance Monitoring

### Check Index Usage

```sql
-- Find unused indexes
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
ORDER BY idx_scan ASC, tablename;

-- Indexes with idx_scan = 0 are never used
```

### Check Table Sizes

```sql
-- Check table and index sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('conversations', 'conversation_messages', 'ai_suggestions')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Slow Query Analysis

```sql
-- Enable pg_stat_statements if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries related to conversations
SELECT
    substring(query, 1, 100) AS short_query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE query LIKE '%conversation%'
ORDER BY mean_time DESC
LIMIT 20;

-- Reset stats after optimization
SELECT pg_stat_statements_reset();
```

### Monitor Connection Pool

```python
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    print(f"New connection: {id(dbapi_conn)}")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    print(f"Connection checked out: {id(dbapi_conn)}")

@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    print(f"Connection checked in: {id(dbapi_conn)}")

# Check pool status
from app.database import engine

pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked in: {pool.checkedin()}")
print(f"Overflow: {pool.overflow()}")
print(f"Checked out: {pool.checkedout()}")
```

---

## Best Practices

### 1. Always Use Transactions

```python
from sqlalchemy import exc

try:
    # Start transaction
    conversation = Conversation(...)
    db.add(conversation)

    message = conversation.add_message(...)
    db.add(message)

    # Commit together
    db.commit()
except exc.SQLAlchemyError as e:
    db.rollback()
    print(f"Error: {e}")
    raise
```

### 2. Use Eager Loading for Relationships

```python
from sqlalchemy.orm import joinedload

# BAD: N+1 query problem
conversations = db.query(Conversation).all()
for conv in conversations:
    print(conv.lead.title)  # Each iteration makes a new query!

# GOOD: Eager load relationships
conversations = db.query(Conversation)\
    .options(joinedload(Conversation.lead))\
    .all()
for conv in conversations:
    print(conv.lead.title)  # No additional queries!
```

### 3. Paginate Large Results

```python
def get_conversations_paginated(db, page=1, per_page=20, status=None):
    query = db.query(Conversation)

    if status:
        query = query.filter(Conversation.status == status)

    # Calculate offset
    offset = (page - 1) * per_page

    # Get total count
    total = query.count()

    # Get page results
    conversations = query\
        .order_by(Conversation.last_message_at.desc())\
        .offset(offset)\
        .limit(per_page)\
        .all()

    return {
        'conversations': conversations,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }
```

### 4. Use Bulk Operations for Better Performance

```python
from sqlalchemy import insert

# BAD: Individual inserts
for data in message_data_list:
    message = ConversationMessage(**data)
    db.add(message)
db.commit()

# GOOD: Bulk insert
db.execute(
    insert(ConversationMessage),
    message_data_list
)
db.commit()
```

---

**Last Updated**: November 4, 2025
**Maintained By**: Database Operations Team
