# Conversation API - Quick Reference

Complete endpoint reference with request/response examples for the conversation management system.

---

## Base URL
```
http://localhost:8000/api/v1/conversations
```

---

## Endpoints

### 1. List Conversations
```http
GET /api/v1/conversations
```

**Query Parameters:**
```
status:              active | needs_reply | waiting | archived
lead_id:             integer
has_pending_suggestion: boolean
search:              string (search in subject or lead name)
page:                integer (default: 1)
page_size:           integer (default: 20, max: 100)
sort_by:             last_message_at | created_at | message_count
sort_order:          asc | desc (default: desc)
```

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/conversations?status=needs_reply&page=1&page_size=20&sort_by=last_message_at&sort_order=desc"
```

**Example Response:**
```json
{
  "conversations": [
    {
      "id": 1,
      "lead": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "title": "Website Development Project"
      },
      "subject": "Re: Website Development Inquiry",
      "status": "needs_reply",
      "message_count": 3,
      "last_message_at": "2025-11-04T10:30:00Z",
      "last_inbound_at": "2025-11-04T10:30:00Z",
      "last_outbound_at": "2025-11-03T14:20:00Z",
      "has_pending_suggestion": true,
      "created_at": "2025-11-02T09:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

---

### 2. Get Conversation Thread
```http
GET /api/v1/conversations/{conversation_id}
```

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/conversations/1"
```

**Example Response:**
```json
{
  "id": 1,
  "lead": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "title": "Website Development Project"
  },
  "subject": "Re: Website Development Inquiry",
  "status": "needs_reply",
  "message_count": 3,
  "last_message_at": "2025-11-04T10:30:00Z",
  "last_inbound_at": "2025-11-04T10:30:00Z",
  "last_outbound_at": "2025-11-03T14:20:00Z",
  "created_at": "2025-11-02T09:00:00Z",
  "updated_at": "2025-11-04T10:30:00Z",
  "archived_at": null,
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "direction": "outbound",
      "sender": {
        "email": "you@company.com",
        "name": "Your Name"
      },
      "recipient": {
        "email": "john@example.com",
        "name": "John Doe"
      },
      "subject": "Website Development Proposal",
      "body_text": "Hi John, I reviewed your website...",
      "body_html": "<p>Hi John, I reviewed your website...</p>",
      "sent_at": "2025-11-02T09:00:00Z",
      "read_at": null,
      "is_read": true,
      "created_at": "2025-11-02T09:00:00Z",
      "attachments": []
    },
    {
      "id": 2,
      "conversation_id": 1,
      "direction": "inbound",
      "sender": {
        "email": "john@example.com",
        "name": "John Doe"
      },
      "recipient": {
        "email": "you@company.com",
        "name": "Your Name"
      },
      "subject": "Re: Website Development Proposal",
      "body_text": "Thanks! Can you show me examples?",
      "body_html": null,
      "sent_at": "2025-11-04T10:30:00Z",
      "read_at": "2025-11-04T10:31:00Z",
      "is_read": true,
      "created_at": "2025-11-04T10:30:00Z",
      "attachments": []
    }
  ],
  "pending_suggestions": [
    {
      "id": 5,
      "conversation_id": 1,
      "reply_to_message_id": 2,
      "suggested_subject": "Re: Website Development Proposal",
      "suggested_body": "Hi John! Absolutely. I've analyzed your site and created a demo...",
      "edited_body": null,
      "confidence_score": 0.92,
      "sentiment_analysis": {
        "sentiment": "positive",
        "intent": "question",
        "engagement_score": 0.85
      },
      "context_used": ["conversation_history", "lead_profile", "similar_conversations"],
      "ai_reasoning": "Lead is interested and asking for examples. High engagement.",
      "ai_metadata": {
        "provider": "ai_council",
        "model": "gpt-4",
        "tokens_used": 450,
        "cost": 0.012
      },
      "status": "pending",
      "created_at": "2025-11-04T10:31:00Z",
      "approved_at": null,
      "rejected_at": null,
      "sent_at": null,
      "user_rating": null,
      "feedback_notes": null
    }
  ]
}
```

---

### 3. Get AI Suggestion
```http
GET /api/v1/conversations/{conversation_id}/ai-suggestion
```

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/conversations/1/ai-suggestion"
```

**Example Response:**
```json
{
  "id": 5,
  "conversation_id": 1,
  "reply_to_message_id": 2,
  "suggested_subject": "Re: Website Development Proposal",
  "suggested_body": "Hi John! Absolutely. I've analyzed your site and created a demo showing 3 key improvements...",
  "edited_body": null,
  "confidence_score": 0.92,
  "sentiment_analysis": {
    "sentiment": "positive",
    "sentiment_confidence": 0.88,
    "intent": "question",
    "intent_confidence": 0.95,
    "engagement_score": 0.85,
    "key_topics": ["examples", "demo", "website improvements"],
    "questions_asked": ["Can you show me examples?"],
    "urgency_level": "medium"
  },
  "context_used": [
    "Previous conversation: Initial proposal sent",
    "Lead website analysis",
    "3 similar successful conversations"
  ],
  "ai_reasoning": "Lead is interested and asking for concrete examples. High engagement score. Professional tone recommended.",
  "ai_metadata": {
    "provider": "ai_council",
    "model": "gpt-4",
    "tokens_used": 450,
    "cost": 0.012
  },
  "status": "pending",
  "created_at": "2025-11-04T10:31:00Z",
  "approved_at": null,
  "rejected_at": null,
  "sent_at": null,
  "user_rating": null,
  "feedback_notes": null
}
```

---

### 4. Approve AI Reply
```http
POST /api/v1/conversations/{conversation_id}/approve
```

**Request Body:**
```json
{
  "suggestion_id": 5,
  "edited_body": "Hi John! Absolutely. I've analyzed your site and created a demo showing 3 improvements. [User edited this part]",
  "edited_subject": null
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/1/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": 5,
    "edited_body": null,
    "edited_subject": null
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "Reply sent successfully",
  "data": {
    "conversation_id": 1,
    "message_id": 3,
    "postmark_message_id": "abc123-xyz789"
  }
}
```

**Side Effects:**
- ✉️ Email sent via Postmark
- 💾 Message record created
- ✅ Suggestion marked as approved
- 🔄 Conversation status updated to "waiting"
- 📡 WebSocket event emitted: `conversation:sent`

---

### 5. Reject AI Suggestion
```http
POST /api/v1/conversations/{conversation_id}/reject
```

**Request Body:**
```json
{
  "suggestion_id": 5,
  "reason": "Tone is too casual for this client"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/1/reject" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": 5,
    "reason": "Tone is too casual"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "AI suggestion rejected",
  "data": {
    "suggestion_id": 5
  }
}
```

---

### 6. Send Custom Reply
```http
POST /api/v1/conversations/{conversation_id}/reply
```

**Request Body:**
```json
{
  "subject": "Re: Website Development Proposal",
  "body": "Hi John,\n\nThank you for your interest. Here are some examples...",
  "body_html": "<p>Hi John,</p><p>Thank you for your interest. Here are some examples...</p>"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/1/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Re: Website Development Proposal",
    "body": "Hi John, Thank you for your interest...",
    "body_html": "<p>Hi John,</p><p>Thank you for your interest...</p>"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "Custom reply sent successfully",
  "data": {
    "conversation_id": 1,
    "message_id": 3,
    "postmark_message_id": "custom-abc123"
  }
}
```

**Side Effects:**
- ✉️ Email sent via Postmark
- 💾 Message record created
- 🔄 Conversation status updated to "waiting"
- 📡 WebSocket event emitted: `conversation:sent`

---

### 7. Regenerate AI Suggestion
```http
POST /api/v1/conversations/{conversation_id}/regenerate
```

**Request Body:**
```json
{
  "message_id": 2,
  "tone": "more_formal",
  "length": "shorter",
  "custom_prompt": "Include a specific call-to-action to schedule a demo call"
}
```

**Tone Options:**
- `more_formal` - Use formal business language
- `more_casual` - Use conversational language
- `shorter` - Keep under 100 words
- `add_humor` - Include light professional humor

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/1/regenerate" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": 2,
    "tone": "more_formal",
    "length": null,
    "custom_prompt": "Include pricing information"
  }'
```

**Example Response:**
```json
{
  "id": 6,
  "conversation_id": 1,
  "reply_to_message_id": 2,
  "suggested_subject": "Re: Website Development Proposal",
  "suggested_body": "Dear Mr. Doe,\n\nThank you for your inquiry. I would be pleased to provide examples...",
  "edited_body": null,
  "confidence_score": 0.88,
  "sentiment_analysis": {
    "sentiment": "positive",
    "intent": "question"
  },
  "context_used": ["conversation_history", "lead_profile", "tone_adjustment"],
  "ai_reasoning": "Regenerated with more_formal adjustment: Use formal business language. Avoid contractions. Be respectful and professional.",
  "ai_metadata": {
    "provider": "ai_council",
    "model": "gpt-4",
    "tokens_used": 380,
    "cost": 0.010
  },
  "status": "pending",
  "created_at": "2025-11-04T10:45:00Z",
  "approved_at": null,
  "rejected_at": null,
  "sent_at": null,
  "user_rating": null,
  "feedback_notes": null
}
```

**Side Effects:**
- 🤖 New AI suggestion created
- 📡 WebSocket event emitted: `conversation:ai_ready`

---

### 8. Archive Conversation
```http
PATCH /api/v1/conversations/{conversation_id}/archive
```

**Request Body:**
```json
{
  "reason": "Lead not interested"
}
```

**Example Request:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/conversations/1/archive" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Lead not interested"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "Conversation archived successfully",
  "data": {
    "conversation_id": 1,
    "archived_at": "2025-11-04T11:00:00Z"
  }
}
```

**Side Effects:**
- 📁 Conversation status changed to "archived"
- 🕐 Archived timestamp recorded

---

### 9. Get Conversation Stats
```http
GET /api/v1/conversations/stats
```

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/conversations/stats"
```

**Example Response:**
```json
{
  "total_conversations": 150,
  "active_conversations": 45,
  "needs_reply": 12,
  "waiting_for_response": 25,
  "archived_conversations": 68,
  "emails_sent_week": 38,
  "emails_received_week": 22,
  "response_rate_week": 57.89,
  "avg_response_time_hours": 4.5,
  "ai_suggestions_generated_week": 35,
  "ai_suggestions_approved_week": 28,
  "ai_approval_rate_week": 80.0,
  "avg_confidence_score": 0.87,
  "emails_opened_week": 26,
  "emails_clicked_week": 15,
  "open_rate_week": 68.42,
  "click_rate_week": 39.47
}
```

---

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleConversationEvent(data);
};
```

### Event Types

#### 1. New Reply Received
```json
{
  "type": "conversation:new_reply",
  "conversation_id": 1,
  "message_id": 2,
  "sender": "john@example.com",
  "timestamp": "2025-11-04T10:30:00Z"
}
```

#### 2. AI Suggestion Ready
```json
{
  "type": "conversation:ai_ready",
  "conversation_id": 1,
  "suggestion_id": 5,
  "confidence": 0.92,
  "timestamp": "2025-11-04T10:31:00Z"
}
```

#### 3. Reply Sent
```json
{
  "type": "conversation:sent",
  "conversation_id": 1,
  "message_id": 3,
  "timestamp": "2025-11-04T10:35:00Z"
}
```

#### 4. Error
```json
{
  "type": "conversation:error",
  "conversation_id": 1,
  "error": "Failed to send email: Invalid recipient",
  "timestamp": "2025-11-04T10:35:00Z"
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Conversation 999 not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Suggestion already approved. Cannot approve."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Failed to send email: Postmark API error",
  "timestamp": "2025-11-04T10:35:00Z",
  "request_id": "abc123"
}
```

---

## Testing with cURL

### Complete Test Flow
```bash
# 1. List conversations
curl "http://localhost:8000/api/v1/conversations?status=needs_reply"

# 2. Get conversation thread
curl "http://localhost:8000/api/v1/conversations/1"

# 3. Get AI suggestion
curl "http://localhost:8000/api/v1/conversations/1/ai-suggestion"

# 4. Regenerate with different tone
curl -X POST "http://localhost:8000/api/v1/conversations/1/regenerate" \
  -H "Content-Type: application/json" \
  -d '{"message_id": 2, "tone": "more_casual"}'

# 5. Approve and send
curl -X POST "http://localhost:8000/api/v1/conversations/1/approve" \
  -H "Content-Type: application/json" \
  -d '{"suggestion_id": 5}'

# 6. Check stats
curl "http://localhost:8000/api/v1/conversations/stats"
```

---

## Rate Limits

**Current**: None implemented

**Recommended**:
- List endpoint: 100 requests/minute
- AI regeneration: 20 requests/minute
- Approve/send: 50 requests/minute

---

## Next Steps

1. **Frontend Integration**: Connect React components to these endpoints
2. **WebSocket**: Implement real-time UI updates
3. **Testing**: Run integration tests with mock data
4. **Monitoring**: Add logging and metrics
5. **Production**: Configure Postmark and deploy

---

**Documentation Version**: 1.0
**Last Updated**: November 4, 2025
