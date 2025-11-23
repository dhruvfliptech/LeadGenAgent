# WebSocket Quick Start Guide

**Get up and running with real-time updates in 5 minutes**

---

## For Backend Developers

### Add Events to Celery Tasks

```python
# 1. Import the publisher
from app.core.websocket_publisher import ws_publisher

# 2. Publish events in your task
@shared_task
def my_campaign_task(campaign_id: int):
    # Start event
    ws_publisher.campaign_launched(
        campaign_id=campaign_id,
        campaign_name="My Campaign",
        total_recipients=500
    )

    # ... do work ...

    # Progress event
    ws_publisher.campaign_stats_updated(
        campaign_id=campaign_id,
        emails_sent=100,
        emails_opened=50,
        emails_clicked=10,
        emails_replied=5,
        emails_bounced=2,
        open_rate=50.0,
        click_rate=10.0,
        reply_rate=5.0,
        bounce_rate=2.0
    )

    # Complete event
    ws_publisher.campaign_completed(
        campaign_id=campaign_id,
        campaign_name="My Campaign",
        total_sent=500,
        total_opened=250,
        total_clicked=50,
        total_replied=25,
        open_rate=50.0,
        click_rate=10.0,
        reply_rate=5.0
    )
```

### Add Events to FastAPI Endpoints

```python
# 1. Import the service
from app.services.websocket_service import websocket_service

# 2. Publish events (async)
@router.post("/campaigns/{id}/launch")
async def launch_campaign(id: int):
    # ... launch logic ...

    await websocket_service.campaign_launched(
        campaign_id=id,
        campaign_name=campaign.name,
        total_recipients=len(recipients)
    )

    return {"success": True}
```

---

## For Frontend Developers

### Connect to WebSocket

```javascript
// Simple connection
const ws = new WebSocket('ws://localhost:8000/ws?channels=campaigns,emails');

ws.onopen = () => {
  console.log('Connected!');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);

  // Handle events
  if (data.type === 'campaign:launched') {
    showNotification('Campaign launched!');
  }
};
```

### React Hook

```typescript
import { useEffect, useState } from 'react';

function useCampaignEvents(campaignId: number) {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(
      `ws://localhost:8000/ws/campaigns?campaign_id=${campaignId}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEvents(prev => [...prev, data]);
    };

    return () => ws.close();
  }, [campaignId]);

  return events;
}

// Usage
function CampaignDashboard({ campaignId }) {
  const events = useCampaignEvents(campaignId);

  return (
    <div>
      {events.map(event => (
        <div key={event.timestamp}>
          {event.type}: {JSON.stringify(event)}
        </div>
      ))}
    </div>
  );
}
```

---

## Available Event Types

### Campaigns
- `campaign:launched`
- `campaign:paused`
- `campaign:resumed`
- `campaign:completed`
- `campaign:stats_updated`

### Emails
- `email:sent`
- `email:opened`
- `email:clicked`
- `email:bounced`

### Scrapers
- `scraper:started`
- `scraper:progress`
- `scraper:lead_found`
- `scraper:completed`
- `scraper:failed`

### AI
- `ai:processing`
- `ai:response_ready`
- `ai:lead_analyzed`

### Demos
- `demo:generating`
- `demo:composing`
- `demo:completed`
- `demo:failed`

---

## WebSocket Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/ws` | General purpose |
| `/ws/campaigns` | Campaign events only |
| `/ws/emails` | Email tracking events |
| `/ws/scraper` | Scraper progress |
| `/ws/ai` | AI processing |
| `/ws/demos` | Demo generation |
| `GET /ws/stats` | Connection statistics |

---

## Testing

### 1. Test with wscat

```bash
# Install
npm install -g wscat

# Connect
wscat -c "ws://localhost:8000/ws/campaigns"

# Send test message
> {"type": "ping"}
< {"type": "pong", "timestamp": "..."}
```

### 2. Test Publishing

```python
# Python test
from app.core.websocket_publisher import ws_publisher

ws_publisher.campaign_launched(
    campaign_id=999,
    campaign_name="Test Campaign",
    total_recipients=10
)
```

### 3. Check Connection Stats

```bash
curl http://localhost:8000/api/v1/ws/stats
```

---

## Common Patterns

### Subscribe to Specific Campaign

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Join campaign room
  ws.send(JSON.stringify({
    type: 'join_room',
    room: 'campaign:123'
  }));
};
```

### Progress Bar Updates

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'scraper:progress') {
    updateProgressBar(data.percent);
  }
};
```

### Real-Time Stats

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'campaign:stats_updated') {
    updateDashboard({
      sent: data.emails_sent,
      opened: data.emails_opened,
      openRate: data.open_rate
    });
  }
};
```

---

## Full Documentation

- **Architecture & Events**: `WEBSOCKET_GUIDE.md`
- **Integration Examples**: `WEBSOCKET_INTEGRATION_EXAMPLES.md`
- **Implementation Summary**: `WEBSOCKET_SUMMARY.md`

---

## Need Help?

1. Check the full guides in the backend folder
2. Look at existing integrations in `app/tasks/`
3. Test with wscat before integrating
4. Monitor Redis: `redis-cli PSUBSCRIBE 'fliptechpro:*'`

---

**That's it! You're ready to add real-time updates to FlipTech Pro.**
