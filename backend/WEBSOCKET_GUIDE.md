# WebSocket Infrastructure Guide

**FlipTech Pro Real-Time Communication System**

This guide provides comprehensive documentation for the WebSocket infrastructure, including architecture, event types, client connection examples, and testing procedures.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Available Endpoints](#available-endpoints)
3. [Event Types Reference](#event-types-reference)
4. [Client Connection Examples](#client-connection-examples)
5. [Channel Subscriptions](#channel-subscriptions)
6. [Room-Based Messaging](#room-based-messaging)
7. [Redis Pub/Sub Integration](#redis-pubsub-integration)
8. [Publishing Events from Backend](#publishing-events-from-backend)
9. [Testing Procedures](#testing-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### System Components

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  Web Clients    │◄────────│  FastAPI         │◄────────│  Redis Pub/Sub  │
│  (Browser/App)  │  WS     │  WebSocket       │  Sub    │                 │
│                 │         │  Server          │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    ▲                             ▲
                                    │                             │
                                    │                             │ Publish
                                    │                             │
                            ┌───────┴──────────────────────────┬──┴────┐
                            │                                  │       │
                     ┌──────▼──────┐                  ┌────────▼───┐   │
                     │             │                  │            │   │
                     │  HTTP API   │                  │   Celery   │   │
                     │  Endpoints  │                  │   Tasks    │   │
                     │             │                  │            │   │
                     └─────────────┘                  └────────────┘   │
```

### Data Flow

1. **Events Generated**: Backend services (API endpoints, Celery tasks) generate events
2. **Published to Redis**: Events are published to Redis Pub/Sub channels
3. **Redis Listener**: WebSocket server subscribes to Redis channels
4. **Message Routing**: Messages are routed to appropriate WebSocket connections
5. **Client Delivery**: Events are pushed to connected clients in real-time

### Key Features

- **Channel-Based Subscriptions**: Clients subscribe to specific channels (campaigns, emails, scrapers, etc.)
- **Room-Based Broadcasting**: Targeted messages to specific resources (e.g., campaign:123)
- **Heartbeat Monitoring**: Automatic connection health checks every 30 seconds
- **Automatic Reconnection**: Redis listener recovers from connection failures
- **Type-Safe Events**: Pydantic models for all event types
- **Backward Compatible**: Maintains compatibility with existing WebSocket code

---

## Available Endpoints

### 1. `/ws` - Main WebSocket Endpoint

**General-purpose WebSocket connection with flexible channel subscriptions.**

**Query Parameters:**
- `client_id` (optional): Client identifier (default: "default")
- `channels` (optional): Comma-separated list of channels to subscribe to

**Example:**
```
ws://localhost:8000/ws?client_id=user123&channels=leads,notifications
```

**Supported Client Messages:**
```json
// Ping/Pong for connection testing
{ "type": "ping" }

// Subscribe to channels
{ "type": "subscribe", "channels": ["campaigns", "emails"] }

// Unsubscribe from channels
{ "type": "unsubscribe", "channels": ["emails"] }

// Join a specific room
{ "type": "join_room", "room": "campaign:456" }

// Leave a room
{ "type": "leave_room", "room": "campaign:456" }
```

---

### 2. `/ws/campaigns` - Campaign Updates

**Dedicated endpoint for campaign-related events.**

**Query Parameters:**
- `client_id` (optional): Client identifier
- `campaign_id` (optional): Specific campaign to monitor

**Example:**
```
ws://localhost:8000/ws/campaigns?campaign_id=123
```

**Receives:**
- Campaign launch notifications
- Email send progress
- Statistics updates
- Campaign completion events

---

### 3. `/ws/emails` - Email Tracking

**Real-time email event tracking.**

**Example:**
```
ws://localhost:8000/ws/emails?client_id=dashboard
```

**Receives:**
- Email sent confirmations
- Delivery events
- Open tracking
- Click tracking
- Bounce notifications
- Unsubscribe events

---

### 4. `/ws/scraper` - Scraper Progress (Legacy)

**Original scraper endpoint (maintained for backward compatibility).**

**Receives:**
- Scraper progress updates
- Lead discovery notifications

---

### 5. `/ws/ai` - AI Processing Updates

**AI and ML processing status updates.**

**Example:**
```
ws://localhost:8000/ws/ai
```

**Receives:**
- AI processing status
- Response generation complete
- Lead analysis results
- Email content generation
- ML model training updates

---

### 6. `/ws/demos` - Demo Generation Progress

**Demo site and video generation tracking.**

**Query Parameters:**
- `client_id` (optional): Client identifier
- `demo_id` (optional): Specific demo to monitor

**Example:**
```
ws://localhost:8000/ws/demos?demo_id=demo_789
```

**Receives:**
- Demo generation start
- Recording progress
- Video composition progress
- Upload progress
- Demo completion with URL
- Error notifications

---

### 7. `GET /ws/stats` - Connection Statistics

**HTTP endpoint to check WebSocket health and statistics.**

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_connections": 15,
    "clients": 8,
    "total_channel_subscriptions": 45,
    "total_room_subscriptions": 12,
    "redis_connected": true,
    "redis": {
      "healthy": true,
      "connected": true,
      "running": true,
      "subscriptions": 8,
      "channels": [
        "fliptechpro:campaigns",
        "fliptechpro:emails",
        "fliptechpro:scrapers",
        "fliptechpro:ai",
        "fliptechpro:demos",
        "fliptechpro:notifications",
        "fliptechpro:leads",
        "fliptechpro:conversations"
      ]
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Event Types Reference

### Campaign Events (8 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `campaign:launched` | Campaign has been launched | campaigns |
| `campaign:paused` | Campaign paused by user | campaigns |
| `campaign:resumed` | Campaign resumed after pause | campaigns |
| `campaign:completed` | Campaign finished successfully | campaigns |
| `campaign:email_sent` | Individual email sent | campaigns |
| `campaign:email_failed` | Email send failed | campaigns |
| `campaign:stats_updated` | Campaign statistics updated | campaigns |

**Example Event:**
```json
{
  "type": "campaign:launched",
  "campaign_id": 123,
  "campaign_name": "Q1 Outreach",
  "total_recipients": 500,
  "scheduled_at": null,
  "room": "campaign:123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Email Events (6 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `email:sent` | Email sent successfully | emails |
| `email:delivered` | Email delivered to inbox | emails |
| `email:opened` | Email opened by recipient | emails |
| `email:clicked` | Link clicked in email | emails |
| `email:bounced` | Email bounced | emails |
| `email:unsubscribed` | Recipient unsubscribed | emails |

**Example Event:**
```json
{
  "type": "email:opened",
  "email_id": 456,
  "campaign_id": 123,
  "lead_id": 789,
  "to_email": "prospect@example.com",
  "opened_at": "2024-01-15T10:35:00Z",
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1",
  "room": "campaign:123",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

---

### Scraper Events (9 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `scraper:started` | Scraping job started | scrapers |
| `scraper:progress` | Progress update | scrapers |
| `scraper:lead_found` | New lead discovered | scrapers |
| `scraper:completed` | Scraping completed | scrapers |
| `scraper:failed` | Scraping failed | scrapers |
| `scraper:google_maps_progress` | Google Maps specific progress | scrapers |
| `scraper:linkedin_progress` | LinkedIn specific progress | scrapers |
| `scraper:job_board_progress` | Job board specific progress | scrapers |

**Example Event:**
```json
{
  "type": "scraper:progress",
  "scraper_id": "scrape_abc123",
  "source": "craigslist",
  "current": 50,
  "total": 100,
  "percent": 50.0,
  "leads_found": 12,
  "message": "Processing page 5 of 10",
  "room": "scraper:scrape_abc123",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

---

### AI Events (7 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `ai:processing` | AI task started | ai |
| `ai:response_ready` | AI response generated | ai |
| `ai:analysis_complete` | Analysis finished | ai |
| `ai:model_trained` | ML model training complete | ai |
| `ai:email_generated` | Email content generated | ai |
| `ai:lead_analyzed` | Lead analysis complete | ai |
| `ai:conversation_processed` | Conversation analyzed | ai |

**Example Event:**
```json
{
  "type": "ai:lead_analyzed",
  "lead_id": 789,
  "quality_score": 85.5,
  "tags": ["high-priority", "qualified"],
  "priority": "high",
  "room": "lead:789",
  "timestamp": "2024-01-15T10:45:00Z"
}
```

---

### Demo Events (6 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `demo:generating` | Demo generation started | demos |
| `demo:recording` | Recording in progress | demos |
| `demo:composing` | Video composition in progress | demos |
| `demo:uploading` | Uploading to hosting | demos |
| `demo:completed` | Demo ready | demos |
| `demo:failed` | Demo generation failed | demos |

**Example Event:**
```json
{
  "type": "demo:completed",
  "demo_id": "demo_xyz",
  "lead_id": 789,
  "demo_url": "https://demo.fliptechpro.com/demo_xyz",
  "video_url": "https://cdn.fliptechpro.com/video_xyz.mp4",
  "duration_seconds": 120.5,
  "room": "demo:demo_xyz",
  "timestamp": "2024-01-15T11:00:00Z"
}
```

---

### System Events (4 types)

| Event Type | Description | Channel |
|------------|-------------|---------|
| `notification:system` | System notification | notifications |
| `connection` | Connection status | - |
| `heartbeat` | Connection health check | - |
| `lead:created` | New lead created | leads |
| `conversation:new_reply` | New conversation message | conversations |

---

## Client Connection Examples

### JavaScript/TypeScript (Browser)

```typescript
// Connect to main WebSocket with channel subscriptions
const ws = new WebSocket(
  'ws://localhost:8000/ws?client_id=user123&channels=campaigns,emails'
);

// Connection opened
ws.onopen = () => {
  console.log('WebSocket connected');

  // Subscribe to additional channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['scrapers', 'ai']
  }));

  // Join a specific campaign room
  ws.send(JSON.stringify({
    type: 'join_room',
    room: 'campaign:123'
  }));
};

// Receive messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'connection':
      console.log('Connected:', message);
      break;

    case 'campaign:launched':
      console.log('Campaign launched:', message);
      // Update UI
      break;

    case 'email:opened':
      console.log('Email opened:', message);
      // Update stats
      break;

    case 'scraper:progress':
      console.log('Scraper progress:', message.percent + '%');
      // Update progress bar
      break;

    case 'heartbeat':
      // Connection is healthy
      break;

    default:
      console.log('Unknown message:', message);
  }
};

// Error handling
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Connection closed
ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Implement reconnection logic
};

// Send ping to test connection
function ping() {
  ws.send(JSON.stringify({ type: 'ping' }));
}
```

---

### React Hook Example

```typescript
import { useEffect, useState, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export function useWebSocket(url: string, channels?: string[]) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Build URL with channels
    const channelParam = channels?.join(',');
    const wsUrl = channelParam
      ? `${url}?channels=${channelParam}`
      : url;

    // Connect
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnected(false);
    };

    // Cleanup
    return () => {
      ws.close();
    };
  }, [url, channels]);

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return { connected, messages, sendMessage };
}

// Usage
function CampaignMonitor({ campaignId }: { campaignId: number }) {
  const { connected, messages, sendMessage } = useWebSocket(
    'ws://localhost:8000/ws/campaigns',
    ['campaigns']
  );

  useEffect(() => {
    if (connected) {
      // Join campaign room
      sendMessage({
        type: 'join_room',
        room: `campaign:${campaignId}`
      });
    }
  }, [connected, campaignId]);

  // Filter campaign events
  const campaignEvents = messages.filter(
    (msg) => msg.type.startsWith('campaign:')
  );

  return (
    <div>
      <h2>Campaign Monitor</h2>
      <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>
      <ul>
        {campaignEvents.map((event, i) => (
          <li key={i}>{event.type}: {JSON.stringify(event)}</li>
        ))}
      </ul>
    </div>
  );
}
```

---

### Python Client Example

```python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8000/ws?channels=campaigns,emails"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # Subscribe to additional channels
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channels": ["scrapers"]
        }))

        # Listen for messages
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "campaign:launched":
                print(f"Campaign launched: {data['campaign_name']}")

            elif data["type"] == "scraper:progress":
                print(f"Scraper progress: {data['percent']}%")

            elif data["type"] == "heartbeat":
                # Connection is healthy
                pass

            else:
                print(f"Received: {data}")

# Run
asyncio.run(connect_websocket())
```

---

## Channel Subscriptions

### Available Channels

- `fliptechpro:campaigns` - Campaign events
- `fliptechpro:emails` - Email tracking events
- `fliptechpro:scrapers` - Scraper progress
- `fliptechpro:ai` - AI processing
- `fliptechpro:demos` - Demo generation
- `fliptechpro:notifications` - System notifications
- `fliptechpro:leads` - Lead updates
- `fliptechpro:conversations` - Conversation updates

### Dynamic Subscription

Clients can dynamically subscribe and unsubscribe from channels:

```javascript
// Subscribe
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['campaigns', 'emails']
}));

// Unsubscribe
ws.send(JSON.stringify({
  type: 'unsubscribe',
  channels: ['emails']
}));
```

---

## Room-Based Messaging

Rooms allow targeted messages to specific resources (e.g., a specific campaign, lead, or demo).

### Room Format

- Campaign: `campaign:{campaign_id}`
- Lead: `lead:{lead_id}`
- Demo: `demo:{demo_id}`
- Conversation: `conversation:{conversation_id}`
- Scraper: `scraper:{scraper_id}`

### Joining Rooms

```javascript
// Join a campaign room
ws.send(JSON.stringify({
  type: 'join_room',
  room: 'campaign:123'
}));

// Leave a room
ws.send(JSON.stringify({
  type: 'leave_room',
  room: 'campaign:123'
}));
```

### Publishing to Rooms

Backend services automatically send events to appropriate rooms:

```python
# In Celery task
from app.core.websocket_publisher import ws_publisher

ws_publisher.campaign_launched(
    campaign_id=123,
    campaign_name="Q1 Outreach",
    total_recipients=500
)
# This automatically publishes to room "campaign:123"
```

---

## Redis Pub/Sub Integration

### Architecture

The WebSocket server subscribes to Redis Pub/Sub channels and forwards messages to WebSocket clients.

### Redis Channels

All channels are prefixed with `fliptechpro:` to avoid conflicts:

```
fliptechpro:campaigns
fliptechpro:emails
fliptechpro:scrapers
fliptechpro:ai
fliptechpro:demos
fliptechpro:notifications
fliptechpro:leads
fliptechpro:conversations
```

### Message Format

All messages published to Redis must be JSON with these fields:

```json
{
  "type": "event:name",
  "timestamp": "2024-01-15T10:30:00Z",
  "room": "optional_room",
  "data": {
    // Event-specific data
  }
}
```

### Direct Redis Publishing (Advanced)

```python
import redis
import json
from datetime import datetime

r = redis.from_url("redis://localhost:6379")

# Publish event
r.publish("fliptechpro:campaigns", json.dumps({
    "type": "campaign:launched",
    "campaign_id": 123,
    "campaign_name": "Test",
    "total_recipients": 100,
    "timestamp": datetime.utcnow().isoformat()
}))
```

---

## Publishing Events from Backend

### From Celery Tasks (Synchronous)

```python
from app.core.websocket_publisher import ws_publisher

@shared_task
def send_campaign_email(campaign_id: int, recipient_id: int):
    # ... send email logic ...

    # Publish event
    ws_publisher.campaign_email_sent(
        campaign_id=campaign_id,
        recipient_id=recipient_id,
        lead_id=lead.id,
        to_email=lead.email,
        subject="Your subject"
    )
```

### From API Endpoints (Async)

```python
from app.services.websocket_service import websocket_service

@router.post("/campaigns/{campaign_id}/launch")
async def launch_campaign(campaign_id: int):
    # ... launch logic ...

    # Publish event
    await websocket_service.campaign_launched(
        campaign_id=campaign_id,
        campaign_name=campaign.name,
        total_recipients=len(recipients)
    )

    return {"success": True}
```

### All Available Publisher Methods

**Sync (for Celery):** `ws_publisher.method_name()`
**Async (for FastAPI):** `await websocket_service.method_name()`

Methods:
- `campaign_launched()`
- `campaign_paused()`
- `campaign_resumed()`
- `campaign_completed()`
- `campaign_stats_updated()`
- `email_sent()`
- `email_opened()`
- `scraper_started()`
- `scraper_progress()`
- `scraper_lead_found()`
- `scraper_completed()`
- `scraper_failed()`
- `ai_processing()`
- `ai_response_ready()`
- `demo_generating()`
- `demo_completed()`
- `demo_failed()`
- `lead_created()`
- `system_notification()`

---

## Testing Procedures

### 1. Manual Testing with wscat

Install wscat:
```bash
npm install -g wscat
```

Connect and test:
```bash
# Connect to main endpoint
wscat -c "ws://localhost:8000/ws?channels=campaigns"

# Send messages
> {"type": "ping"}
< {"type": "pong", "timestamp": "2024-01-15T10:30:00Z"}

> {"type": "subscribe", "channels": ["emails"]}
< {"type": "subscribed", "channels": ["emails"], "timestamp": "..."}
```

### 2. Testing Event Publishing

```python
# Test script: test_websocket_events.py
from app.core.websocket_publisher import ws_publisher

# Test campaign event
ws_publisher.campaign_launched(
    campaign_id=999,
    campaign_name="Test Campaign",
    total_recipients=10
)

# Test scraper event
ws_publisher.scraper_progress(
    scraper_id="test_123",
    source="craigslist",
    current=5,
    total=10,
    leads_found=3,
    message="Testing"
)
```

### 3. Connection Stats Check

```bash
curl http://localhost:8000/api/v1/ws/stats
```

### 4. Redis Message Monitoring

```bash
# Monitor all Redis pub/sub activity
redis-cli PSUBSCRIBE 'fliptechpro:*'
```

### 5. Load Testing

```python
# load_test_websocket.py
import asyncio
import websockets
import json

async def client(client_id):
    uri = f"ws://localhost:8000/ws?client_id=client_{client_id}"
    async with websockets.connect(uri) as ws:
        # Receive welcome
        msg = await ws.recv()
        print(f"Client {client_id}: {msg}")

        # Stay connected for 60 seconds
        await asyncio.sleep(60)

async def main():
    # Create 100 concurrent connections
    tasks = [client(i) for i in range(100)]
    await asyncio.gather(*tasks)

asyncio.run(main())
```

---

## Troubleshooting

### Issue: WebSocket won't connect

**Check:**
1. Redis is running: `redis-cli ping`
2. REDIS_URL environment variable is set
3. FastAPI server is running
4. No firewall blocking WebSocket connections

**Solution:**
```bash
# Check Redis
redis-cli ping

# Check environment
echo $REDIS_URL

# Check WebSocket stats
curl http://localhost:8000/api/v1/ws/stats
```

---

### Issue: Events not being received

**Check:**
1. Client is subscribed to correct channel
2. Redis Pub/Sub is working
3. Event is being published correctly

**Debug:**
```bash
# Monitor Redis pub/sub
redis-cli PSUBSCRIBE 'fliptechpro:*'

# Check stats
curl http://localhost:8000/api/v1/ws/stats
```

**Solution:**
```javascript
// Ensure proper subscription
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['campaigns']
}));
```

---

### Issue: Connection keeps dropping

**Check:**
1. Heartbeat is working
2. Client is handling heartbeat messages
3. Network stability

**Solution:**
```javascript
// Implement auto-reconnect
function connectWebSocket() {
  const ws = new WebSocket(url);

  ws.onclose = () => {
    console.log('Reconnecting in 5 seconds...');
    setTimeout(connectWebSocket, 5000);
  };

  return ws;
}
```

---

### Issue: High memory usage

**Check:**
1. Number of active connections
2. Message queue size
3. Redis memory usage

**Solution:**
```bash
# Check stats
curl http://localhost:8000/api/v1/ws/stats

# Check Redis memory
redis-cli INFO memory
```

---

## Performance Considerations

### Connection Limits

- Recommended max connections per server: **10,000**
- Heartbeat interval: **30 seconds** (configurable via `WEBSOCKET_PING_INTERVAL`)
- Redis connection pool size: **10**

### Scaling

For high-traffic scenarios:

1. **Horizontal Scaling**: Run multiple FastAPI instances behind a load balancer
2. **Redis Scaling**: Use Redis Cluster for high availability
3. **Message Rate Limiting**: Implement rate limiting in publisher

### Best Practices

1. **Subscribe only to needed channels**: Avoid subscribing to all channels
2. **Handle heartbeats**: Respond to or ignore heartbeat messages
3. **Implement reconnection**: Auto-reconnect on disconnect
4. **Use rooms for targeted messages**: Subscribe to specific resources
5. **Clean up subscriptions**: Unsubscribe when no longer needed

---

## Security Considerations

### Authentication

WebSocket connections should be authenticated:

```python
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    # Verify token
    user = verify_token(token)
    if not user:
        await websocket.close(code=1008)  # Policy violation
        return

    # Continue with connection...
```

### Rate Limiting

Implement rate limiting for message publishing:

```python
from app.core.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=100, window=60)

if not limiter.check(client_id):
    await websocket.send_json({
        "type": "error",
        "message": "Rate limit exceeded"
    })
```

---

## Conclusion

This WebSocket infrastructure provides a robust, scalable real-time communication system for FlipTech Pro. With Redis Pub/Sub integration, type-safe events, and flexible subscriptions, it supports all real-time features across campaigns, emails, scrapers, AI, and demos.

For additional support or questions, refer to the codebase or create an issue in the project repository.
