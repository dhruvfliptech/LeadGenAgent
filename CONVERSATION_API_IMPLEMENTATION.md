# Conversation Management API - Implementation Complete

**Date**: November 4, 2025
**Status**: ✅ Complete and Ready for Testing
**Based on**: UX_FLOW_CONVERSATIONS.md Section 11

---

## Overview

Complete REST API implementation for the conversation management system with email reply handling, AI-powered response generation, and real-time WebSocket notifications.

---

## Files Created/Modified

### 1. Database Models
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/models/conversations.py`

✅ **Already Existed** - Models include:
- `Conversation` - Main conversation thread
- `ConversationMessage` - Individual email messages
- `AISuggestion` - AI-generated reply suggestions
- Enums: `ConversationStatus`, `MessageDirection`, `AISuggestionStatus`

**Updated**: `/Users/greenmachine2.0/Craigslist/backend/app/models/__init__.py`
- Exported conversation models for application-wide use

---

### 2. Request/Response Schemas
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/schemas/conversation.py` ✅ **NEW**

**Schemas Created**:

**Response Models**:
- `ConversationListResponse` - Paginated conversation list
- `ConversationThreadResponse` - Full conversation with messages
- `AISuggestionResponse` - AI suggestion details
- `MessageResponse` - Individual message
- `ConversationStatsResponse` - Analytics data

**Request Models**:
- `ApproveReplyRequest` - Approve AI suggestion
- `RejectReplyRequest` - Reject AI suggestion
- `SendReplyRequest` - Send custom reply
- `RegenerateReplyRequest` - Regenerate AI with custom params
- `ArchiveConversationRequest` - Archive conversation
- `ConversationFilters` - List filtering params

**Helper Models**:
- `LeadInfo`, `SenderRecipientInfo`, `AIMetadata`
- `SuccessResponse` - Generic success response

---

### 3. ConversationAI Service
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/services/conversation_ai.py`

✅ **Already Existed** - Comprehensive AI service with:

**Core Methods**:
- `analyze_reply()` - Sentiment/intent analysis
- `generate_reply()` - Context-aware AI responses
- `suggest_improvements()` - Draft review and feedback
- `regenerate_reply()` - Tone-adjusted regeneration

**Features**:
- Integration with AI Council (multi-model routing)
- Vector store for similar conversation retrieval
- Confidence scoring and quality evaluation
- Support for custom tone adjustments

---

### 4. Vector Store Service
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/services/vector_store.py`

✅ **Already Existed** - PostgreSQL pgvector integration:
- Semantic search for similar conversations
- OpenAI embeddings (text-embedding-3-small)
- Best practice retrieval by intent
- Outcome tracking and analytics

---

### 5. API Endpoints
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/conversations.py` ✅ **NEW**

**Endpoints Implemented**:

#### GET /api/v1/conversations
List conversations with filtering and pagination
- **Query Params**: status, lead_id, search, page, page_size, sort_by, sort_order
- **Response**: Paginated list with lead info and pending suggestion flags

#### GET /api/v1/conversations/:id
Get full conversation thread
- **Response**: Messages, pending AI suggestions, conversation metadata

#### GET /api/v1/conversations/:id/ai-suggestion
Get pending AI suggestion
- **Response**: Latest pending AI suggestion with confidence score and analysis

#### POST /api/v1/conversations/:id/approve
Approve and send AI reply
- **Body**: `suggestion_id`, optional `edited_body`, `edited_subject`
- **Actions**: Sends email via Postmark, creates message record, updates status
- **WebSocket**: Emits `conversation:sent` event

#### POST /api/v1/conversations/:id/reject
Reject AI suggestion
- **Body**: `suggestion_id`, optional `reason`
- **Actions**: Marks suggestion as rejected

#### POST /api/v1/conversations/:id/reply
Send custom reply (not AI-generated)
- **Body**: `subject`, `body`, optional `body_html`
- **Actions**: Sends email, creates message record
- **WebSocket**: Emits `conversation:sent` event

#### POST /api/v1/conversations/:id/regenerate
Regenerate AI suggestion with custom parameters
- **Body**: `message_id`, optional `tone`, `length`, `custom_prompt`
- **Response**: New AI suggestion
- **WebSocket**: Emits `conversation:ai_ready` event

#### PATCH /api/v1/conversations/:id/archive
Archive conversation
- **Body**: optional `reason`
- **Actions**: Sets status to archived, records timestamp

#### GET /api/v1/conversations/stats
Get conversation analytics
- **Response**: Comprehensive stats:
  - Total/active/archived conversation counts
  - Weekly email metrics (sent, received, response rate)
  - AI performance (suggestions, approval rate, confidence)
  - Delivery metrics (opens, clicks, rates)

---

### 6. WebSocket Integration
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/websocket.py` ✅ **UPDATED**

**Added Helper Functions**:
- `notify_conversation_new_reply()` - New inbound email
- `notify_conversation_ai_ready()` - AI suggestion ready
- `notify_conversation_sent()` - Reply sent successfully
- `notify_conversation_error()` - Error notification

**Event Types**:
```typescript
'conversation:new_reply'  // { conversation_id, message_id, sender, timestamp }
'conversation:ai_ready'   // { conversation_id, suggestion_id, confidence, timestamp }
'conversation:sent'       // { conversation_id, message_id, timestamp }
'conversation:error'      // { conversation_id, error, timestamp }
```

---

### 7. Main Application
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/main.py` ✅ **UPDATED**

**Changes**:
- Imported `conversations` endpoint module
- Registered router: `app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])`

---

### 8. Configuration
**File**: `/Users/greenmachine2.0/Craigslist/backend/app/core/config.py` ✅ **UPDATED**

**Added Setting**:
- `POSTMARK_SERVER_TOKEN` - For sending transactional emails

---

## API Architecture

### Service Dependencies

```
conversations.py (Endpoints)
    ├── get_conversation_ai() → ConversationAI service
    │   ├── AICouncil (multi-model routing)
    │   └── VectorStore (similar conversation retrieval)
    │
    ├── get_email_sender() → EmailSender service
    │   └── Postmark API client
    │
    ├── Database (AsyncSession)
    │   ├── Conversation model
    │   ├── ConversationMessage model
    │   └── AISuggestion model
    │
    └── WebSocket Manager
        └── Real-time event broadcasting
```

### Request Flow Examples

#### 1. Approve AI Reply Flow
```
POST /conversations/123/approve
  ↓
1. Validate suggestion exists and is pending
2. Get conversation and lead data
3. Send email via Postmark
   ├── Success: Get message_id
   └── Failure: Return HTTP 500
4. Create ConversationMessage record
5. Update AISuggestion status (approved/edited)
6. Update Conversation metadata
7. Commit transaction
8. Emit WebSocket event: conversation:sent
9. Return success response
```

#### 2. Regenerate AI Suggestion Flow
```
POST /conversations/123/regenerate
  ↓
1. Get conversation, messages, and lead
2. Build conversation history
3. Analyze inbound message (ConversationAI.analyze_reply)
4. Build lead context from lead data
5. Regenerate with tone adjustment (ConversationAI.regenerate_reply)
6. Create new AISuggestion record
7. Commit transaction
8. Emit WebSocket event: conversation:ai_ready
9. Return new suggestion
```

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful operation
- `404 Not Found` - Conversation/suggestion/message not found
- `400 Bad Request` - Invalid request (already approved, invalid status, etc.)
- `500 Internal Server Error` - Email send failure, database error, AI service error

### Error Response Format
```json
{
  "detail": "Descriptive error message",
  "conversation_id": 123,
  "timestamp": "2025-11-04T12:00:00Z"
}
```

### Retry Logic
- Email send failures: No automatic retry (user must retry manually)
- Database transaction failures: Rolled back automatically
- AI generation failures: Fallback to default analysis/content

---

## Integration Points

### 1. Email Sending (Postmark)
**Service**: `EmailSender` (`/services/ai_mvp/email_sender.py`)
**Config Required**:
- `POSTMARK_SERVER_TOKEN` - Postmark API token
- `SMTP_FROM_EMAIL` - Sender email address
- `USER_NAME` - Sender name

**Features**:
- HTML and plain text support
- Open/click tracking
- Bounce/spam handling
- Metadata tagging

### 2. AI Generation (AI Council)
**Service**: `ConversationAI` (`/services/conversation_ai.py`)
**Config Required**:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- AI_GYM tracking enabled

**Routing**:
- Analysis tasks → Cheap models (GPT-3.5)
- Reply generation → Premium models (GPT-4, Claude-3)
- Based on lead value and task complexity

### 3. Vector Store (pgvector)
**Service**: `VectorStore` (`/services/vector_store.py`)
**Database Required**:
- PostgreSQL with pgvector extension
- `conversation_vectors` table (see migration in file)

**Features**:
- Semantic search with cosine similarity
- HNSW index for performance
- Intent-based filtering

### 4. WebSocket (Real-time Updates)
**Manager**: `ConnectionManager` in `/api/endpoints/websocket.py`
**Connection**: `ws://localhost:8000/ws`

**Client Usage**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'conversation:ai_ready') {
    // Show notification, update UI
  }
};
```

---

## Database Schema

### Required Tables
1. `conversations` - ✅ Already exists
2. `conversation_messages` - ✅ Already exists
3. `ai_suggestions` - ✅ Already exists
4. `conversation_vectors` - ⚠️ Needs migration (see vector_store.py)

### Migration Needed
```sql
-- Run vector store schema migration
CREATE EXTENSION IF NOT EXISTS vector;

-- See full schema in:
-- /services/vector_store.py → VECTOR_STORE_SCHEMA constant
```

---

## Testing Checklist

### Unit Tests Needed
- [ ] Conversation list filtering and pagination
- [ ] AI suggestion approval with email sending
- [ ] Custom reply sending
- [ ] AI regeneration with tone adjustments
- [ ] Conversation archiving
- [ ] Stats calculation

### Integration Tests Needed
- [ ] Full conversation flow (receive → AI generate → approve → send)
- [ ] WebSocket event broadcasting
- [ ] Email send with Postmark mock
- [ ] Vector store similarity search
- [ ] Error handling and rollback

### Manual Testing
1. **Setup**:
   ```bash
   # Set environment variables
   export POSTMARK_SERVER_TOKEN="your-token"
   export SMTP_FROM_EMAIL="your-email@example.com"
   export USER_NAME="Your Name"
   export OPENAI_API_KEY="your-key"

   # Run migrations
   # (Add conversation_vectors table)

   # Start backend
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Test Endpoints**:
   ```bash
   # List conversations
   curl http://localhost:8000/api/v1/conversations

   # Get conversation thread
   curl http://localhost:8000/api/v1/conversations/1

   # Get AI suggestion
   curl http://localhost:8000/api/v1/conversations/1/ai-suggestion

   # Approve reply
   curl -X POST http://localhost:8000/api/v1/conversations/1/approve \
     -H "Content-Type: application/json" \
     -d '{"suggestion_id": 1}'

   # Get stats
   curl http://localhost:8000/api/v1/conversations/stats
   ```

3. **Test WebSocket**:
   ```bash
   # Use websocat or browser console
   websocat ws://localhost:8000/ws
   ```

---

## API Documentation

### Interactive Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoint Summary
```
GET    /api/v1/conversations           # List with filters
GET    /api/v1/conversations/:id       # Get thread
GET    /api/v1/conversations/:id/ai-suggestion
POST   /api/v1/conversations/:id/approve
POST   /api/v1/conversations/:id/reject
POST   /api/v1/conversations/:id/reply
POST   /api/v1/conversations/:id/regenerate
PATCH  /api/v1/conversations/:id/archive
GET    /api/v1/conversations/stats
```

---

## Performance Considerations

### Optimizations Implemented
1. **Database**:
   - Eager loading with `selectinload()` for relationships
   - Indexed fields: status, lead_id, timestamps
   - Efficient count queries for stats

2. **Caching Opportunities** (Future):
   - Conversation list cache (Redis)
   - Stats cache with TTL
   - AI suggestions cache

3. **Pagination**:
   - Default: 20 items per page
   - Max: 100 items per page
   - Efficient offset/limit queries

### Scalability
- Async/await throughout for concurrency
- Background tasks for AI generation (future)
- Vector store HNSW index for fast similarity search
- WebSocket connection pooling

---

## Security Considerations

### Implemented
- ✅ Input validation with Pydantic schemas
- ✅ SQL injection prevention (SQLAlchemy parameterized queries)
- ✅ Email validation for recipients
- ✅ Status checking (can't approve non-pending suggestions)

### TODO
- [ ] User authentication (JWT tokens)
- [ ] Rate limiting (conversation creation, AI regeneration)
- [ ] CSRF protection for WebSocket
- [ ] Audit logging for all actions

---

## Next Steps

### Required for Production
1. **Database Migration**: Create `conversation_vectors` table
2. **Environment Variables**: Set all required config values
3. **Email Setup**: Configure Postmark account and domain
4. **Testing**: Run full integration test suite
5. **Monitoring**: Add logging, metrics, and alerts

### Future Enhancements
1. **Gmail Integration**: Monitor inbox for replies
2. **Scheduled Suggestions**: Auto-generate AI suggestions on new replies
3. **A/B Testing**: Test different AI reply strategies
4. **Analytics Dashboard**: Visualize conversation performance
5. **Template System**: Reusable reply templates
6. **Bulk Operations**: Archive/reply to multiple conversations

---

## Support & Documentation

### Related Files
- **UX Flow**: `/UX_FLOW_CONVERSATIONS.md`
- **Database Models**: `/backend/app/models/conversations.py`
- **API Endpoints**: `/backend/app/api/endpoints/conversations.py`
- **AI Service**: `/backend/app/services/conversation_ai.py`
- **Vector Store**: `/backend/app/services/vector_store.py`
- **Schemas**: `/backend/app/schemas/conversation.py`

### Key Dependencies
- FastAPI - Web framework
- SQLAlchemy - ORM
- Pydantic - Validation
- Postmarker - Postmark API client
- OpenAI - Embeddings and AI
- pgvector - Vector similarity search
- structlog - Structured logging

---

## Summary

✅ **All endpoints implemented and ready for testing**

The conversation management API is complete with:
- 9 REST endpoints covering all required operations
- Comprehensive request/response validation
- AI-powered reply generation and analysis
- Real-time WebSocket notifications
- Email sending via Postmark
- Vector store for context retrieval
- Full error handling and transaction management

**Status**: Ready for integration testing and frontend development.
