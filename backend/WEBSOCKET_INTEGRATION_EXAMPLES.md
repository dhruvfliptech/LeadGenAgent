# WebSocket Integration Examples

**Quick Reference Guide for Adding Real-Time Events to Celery Tasks**

This document shows practical examples of integrating WebSocket events into existing Celery tasks.

---

## Quick Start

### 1. Import the Publisher

```python
from app.core.websocket_publisher import ws_publisher
```

### 2. Publish Events

```python
# In your Celery task
ws_publisher.campaign_launched(
    campaign_id=123,
    campaign_name="My Campaign",
    total_recipients=500
)
```

That's it! The event will be automatically published to Redis and pushed to all connected WebSocket clients.

---

## Campaign Tasks Integration

### Example: Launch Campaign Task

**File:** `app/tasks/campaign_tasks.py`

```python
from app.core.websocket_publisher import ws_publisher

@shared_task
def launch_campaign_async(campaign_id: int):
    """Launch a campaign with WebSocket notifications."""
    from app.db.database import SessionLocal
    from app.models.campaigns import Campaign

    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        # Update campaign status
        campaign.status = CampaignStatusEnum.RUNNING
        campaign.started_at = datetime.utcnow()
        db.commit()

        # Count recipients
        total_recipients = db.query(CampaignRecipient).filter(
            CampaignRecipient.campaign_id == campaign_id
        ).count()

        # WEBSOCKET EVENT: Campaign launched
        ws_publisher.campaign_launched(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            total_recipients=total_recipients,
            scheduled_at=campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
        )

        # Queue email sending
        send_campaign_emails.apply_async(args=[campaign_id], countdown=5)

        return {"status": "success"}

    finally:
        db.close()
```

### Example: Campaign Stats Update

```python
@shared_task
def update_campaign_metrics():
    """Update campaign metrics with real-time stats broadcasting."""
    from app.db.database import SessionLocal
    from app.models.campaigns import Campaign

    db = SessionLocal()
    try:
        campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatusEnum.RUNNING
        ).all()

        for campaign in campaigns:
            # Calculate stats
            sent = campaign.emails_sent
            opened = campaign.emails_opened
            clicked = campaign.emails_clicked
            replied = campaign.emails_replied
            bounced = campaign.emails_bounced

            # Calculate rates
            open_rate = (opened / sent * 100) if sent > 0 else 0
            click_rate = (clicked / sent * 100) if sent > 0 else 0
            reply_rate = (replied / sent * 100) if sent > 0 else 0
            bounce_rate = (bounced / sent * 100) if sent > 0 else 0

            # Update in DB
            campaign.open_rate = open_rate
            campaign.click_rate = click_rate
            campaign.reply_rate = reply_rate
            campaign.bounce_rate = bounce_rate
            db.commit()

            # WEBSOCKET EVENT: Stats updated
            ws_publisher.campaign_stats_updated(
                campaign_id=campaign.id,
                emails_sent=sent,
                emails_opened=opened,
                emails_clicked=clicked,
                emails_replied=replied,
                emails_bounced=bounced,
                open_rate=round(open_rate, 2),
                click_rate=round(click_rate, 2),
                reply_rate=round(reply_rate, 2),
                bounce_rate=round(bounce_rate, 2)
            )

        return {"status": "success", "updated": len(campaigns)}

    finally:
        db.close()
```

---

## Email Tasks Integration

### Example: Send Campaign Email

**File:** `app/tasks/email_tasks.py`

```python
from app.core.websocket_publisher import ws_publisher

@shared_task
def send_campaign_email(
    campaign_id: int,
    recipient_id: int,
    lead_id: int,
    subject: str,
    html_body: str,
):
    """Send campaign email with WebSocket notifications."""
    from app.services.email_service import EmailService
    from app.db.database import SessionLocal
    from app.models.leads import Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # Send email
        email_service = EmailService(db=db)
        result = email_service.send_email(
            to_email=lead.email,
            subject=subject,
            html_body=html_body
        )

        # WEBSOCKET EVENT: Email sent
        ws_publisher.email_sent(
            to_email=lead.email,
            subject=subject,
            message_id=result.get("message_id"),
            provider=result.get("provider", "smtp"),
            campaign_id=campaign_id
        )

        # Update recipient status
        recipient = db.query(CampaignRecipient).filter(
            CampaignRecipient.id == recipient_id
        ).first()
        if recipient:
            recipient.status = RecipientStatusEnum.SENT
            recipient.sent_at = datetime.utcnow()
            db.commit()

        return {"status": "success", "message_id": result.get("message_id")}

    except Exception as e:
        logger.error(f"Failed to send email: {e}")

        # WEBSOCKET EVENT: Email failed
        ws_publisher.campaign_email_failed(
            campaign_id=campaign_id,
            recipient_id=recipient_id,
            lead_id=lead_id,
            to_email=lead.email if lead else "unknown",
            error=str(e),
            retry_count=0
        )

        raise

    finally:
        db.close()
```

---

## Scraper Tasks Integration

### Example: Scrape Craigslist with Progress Updates

**File:** `app/tasks/scraper_tasks.py`

```python
import time
from app.core.websocket_publisher import ws_publisher

@shared_task
def scrape_craigslist(location: str, category: str, max_results: int = 100):
    """Scrape Craigslist with real-time progress updates."""
    from app.scrapers.craigslist_scraper import CraigslistScraper
    from app.db.database import SessionLocal
    from app.models.leads import Lead

    # Generate scraper ID for tracking
    scraper_id = f"craigslist_{location}_{category}_{int(time.time())}"

    # WEBSOCKET EVENT: Scraper started
    ws_publisher.scraper_started(
        scraper_id=scraper_id,
        source="craigslist",
        max_results=max_results,
        location=location,
        category=category
    )

    db = SessionLocal()
    start_time = time.time()
    leads_found = 0

    try:
        scraper = CraigslistScraper()

        # Scrape with progress updates
        results = scraper.scrape(
            location=location,
            category=category,
            max_results=max_results
        )

        total = len(results)
        leads_created = 0
        leads_updated = 0

        for i, result in enumerate(results):
            # Save lead
            existing = db.query(Lead).filter(Lead.email == result.get("email")).first()

            if existing:
                # Update
                for key, value in result.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                leads_updated += 1
            else:
                # Create
                lead = Lead(
                    name=result.get("name"),
                    email=result.get("email"),
                    phone=result.get("phone"),
                    source="craigslist",
                    source_url=result.get("url"),
                    location=location,
                    category=category,
                    raw_data=result
                )
                db.add(lead)
                leads_created += 1
                leads_found += 1

                # WEBSOCKET EVENT: Lead found
                ws_publisher.scraper_lead_found(
                    scraper_id=scraper_id,
                    source="craigslist",
                    lead_id=lead.id if hasattr(lead, 'id') else 0,
                    lead_name=result.get("name"),
                    lead_email=result.get("email")
                )

            db.commit()

            # WEBSOCKET EVENT: Progress update (every 10 leads)
            if (i + 1) % 10 == 0:
                ws_publisher.scraper_progress(
                    scraper_id=scraper_id,
                    source="craigslist",
                    current=i + 1,
                    total=total,
                    leads_found=leads_found,
                    message=f"Processed {i + 1} of {total} results"
                )

        duration = time.time() - start_time

        # WEBSOCKET EVENT: Scraper completed
        ws_publisher.scraper_completed(
            scraper_id=scraper_id,
            source="craigslist",
            total_leads=total,
            leads_created=leads_created,
            leads_updated=leads_updated,
            duration_seconds=round(duration, 2),
            success=True
        )

        return {
            "status": "success",
            "scraper_id": scraper_id,
            "total_leads": total,
            "leads_created": leads_created,
            "leads_updated": leads_updated
        }

    except Exception as e:
        logger.error(f"Scraper failed: {e}")

        # WEBSOCKET EVENT: Scraper failed
        ws_publisher.scraper_failed(
            scraper_id=scraper_id,
            source="craigslist",
            error=str(e),
            partial_results=leads_found
        )

        raise

    finally:
        db.close()
```

---

## AI Tasks Integration

### Example: Generate AI Response

**File:** `app/tasks/ai_tasks.py`

```python
from app.core.websocket_publisher import ws_publisher

@shared_task
def generate_ai_response(conversation_id: int, message: str):
    """Generate AI response with real-time status updates."""
    from app.db.database import SessionLocal
    import openai

    task_id = f"ai_response_{conversation_id}_{int(time.time())}"

    # WEBSOCKET EVENT: AI processing started
    ws_publisher.ai_processing(
        task_id=task_id,
        task_type="response",
        resource_id=conversation_id
    )

    db = SessionLocal()
    try:
        # Call AI service (example with OpenAI)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )

        ai_response = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        # Save response to database
        # ... save logic ...

        # WEBSOCKET EVENT: AI response ready
        ws_publisher.ai_response_ready(
            task_id=task_id,
            conversation_id=conversation_id,
            response=ai_response,
            confidence=0.95,  # Example confidence score
            tokens_used=tokens_used
        )

        return {
            "status": "success",
            "task_id": task_id,
            "response": ai_response
        }

    finally:
        db.close()
```

### Example: Analyze Lead

```python
@shared_task
def analyze_lead(lead_id: int):
    """Analyze lead quality with AI."""
    from app.db.database import SessionLocal
    from app.models.leads import Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        # AI analysis logic
        quality_score = 85.5  # Example
        tags = ["high-priority", "qualified"]
        priority = "high"

        # Update lead
        # lead.quality_score = quality_score
        # lead.tags = tags
        # db.commit()

        # WEBSOCKET EVENT: Lead analyzed
        ws_publisher.ai_lead_analyzed(
            lead_id=lead_id,
            quality_score=quality_score,
            tags=tags,
            priority=priority
        )

        return {
            "status": "success",
            "lead_id": lead_id,
            "quality_score": quality_score
        }

    finally:
        db.close()
```

---

## Demo Tasks Integration

### Example: Generate Demo Site

**File:** `app/tasks/demo_tasks.py`

```python
from app.core.websocket_publisher import ws_publisher

@shared_task
def generate_demo_site(lead_id: int, template: str = "default"):
    """Generate demo site with progress updates."""
    from app.db.database import SessionLocal

    demo_id = f"demo_{lead_id}_{int(time.time())}"
    start_time = time.time()

    # WEBSOCKET EVENT: Demo generation started
    ws_publisher.demo_generating(
        demo_id=demo_id,
        lead_id=lead_id,
        template=template
    )

    db = SessionLocal()
    try:
        # Step 1: Generate HTML
        ws_publisher.demo_composing(
            demo_id=demo_id,
            progress_percent=25.0,
            current_step="Generating HTML"
        )
        time.sleep(2)  # Simulate work

        # Step 2: Create video
        ws_publisher.demo_composing(
            demo_id=demo_id,
            progress_percent=50.0,
            current_step="Creating video"
        )
        time.sleep(3)  # Simulate work

        # Step 3: Upload to hosting
        ws_publisher.demo_composing(
            demo_id=demo_id,
            progress_percent=75.0,
            current_step="Uploading to hosting"
        )
        time.sleep(2)  # Simulate work

        # Complete
        demo_url = f"https://demo.fliptechpro.com/{demo_id}"
        video_url = f"https://cdn.fliptechpro.com/{demo_id}.mp4"
        duration = time.time() - start_time

        # WEBSOCKET EVENT: Demo completed
        ws_publisher.demo_completed(
            demo_id=demo_id,
            lead_id=lead_id,
            demo_url=demo_url,
            video_url=video_url,
            duration_seconds=round(duration, 2)
        )

        return {
            "status": "success",
            "demo_id": demo_id,
            "demo_url": demo_url
        }

    except Exception as e:
        logger.error(f"Demo generation failed: {e}")

        # WEBSOCKET EVENT: Demo failed
        ws_publisher.demo_failed(
            demo_id=demo_id,
            lead_id=lead_id,
            error=str(e),
            step_failed="Unknown"
        )

        raise

    finally:
        db.close()
```

---

## System Notifications

### Example: Send System Alert

```python
from app.core.websocket_publisher import ws_publisher

def notify_system_error(title: str, message: str, action_url: str = None):
    """Send system-wide notification to all connected clients."""
    ws_publisher.system_notification(
        level="error",
        title=title,
        message=message,
        action_url=action_url
    )

def notify_success(title: str, message: str):
    """Send success notification."""
    ws_publisher.system_notification(
        level="success",
        title=title,
        message=message
    )

# Usage in task
@shared_task
def critical_task():
    try:
        # ... task logic ...
        notify_success(
            title="Task Completed",
            message="Critical task finished successfully"
        )
    except Exception as e:
        notify_system_error(
            title="Task Failed",
            message=f"Critical task failed: {str(e)}",
            action_url="/admin/tasks"
        )
```

---

## Testing Your Integration

### 1. Connect a WebSocket Client

```javascript
// In browser console or test file
const ws = new WebSocket('ws://localhost:8000/ws/campaigns');

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

### 2. Trigger a Celery Task

```python
# In Python shell or test script
from app.tasks.campaign_tasks import launch_campaign_async

result = launch_campaign_async.apply_async(args=[123])
```

### 3. Watch for Events

You should see real-time events in your WebSocket client console:

```json
{
  "type": "campaign:launched",
  "campaign_id": 123,
  "campaign_name": "Test Campaign",
  "total_recipients": 500,
  "room": "campaign:123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Common Patterns

### Pattern 1: Task with Start/Progress/Complete

```python
@shared_task
def long_running_task(resource_id: int):
    task_id = f"task_{resource_id}_{time.time()}"

    # Start
    ws_publisher.ai_processing(
        task_id=task_id,
        task_type="processing",
        resource_id=resource_id
    )

    try:
        # Progress updates
        for i in range(1, 11):
            # ... do work ...
            ws_publisher.scraper_progress(
                scraper_id=task_id,
                source="task",
                current=i,
                total=10,
                leads_found=0,
                message=f"Step {i}/10"
            )

        # Complete
        ws_publisher.scraper_completed(
            scraper_id=task_id,
            source="task",
            total_leads=0,
            leads_created=0,
            leads_updated=0,
            duration_seconds=10.0,
            success=True
        )

    except Exception as e:
        # Failed
        ws_publisher.scraper_failed(
            scraper_id=task_id,
            source="task",
            error=str(e),
            partial_results=0
        )
        raise
```

### Pattern 2: Room-Based Updates

```python
@shared_task
def update_campaign_stat(campaign_id: int, stat_type: str, value: int):
    """Update a specific campaign stat and notify room subscribers."""

    # Update database
    # ... update logic ...

    # Notify room
    ws_publisher.campaign_stats_updated(
        campaign_id=campaign_id,
        emails_sent=100,
        emails_opened=50,
        # ... other stats ...
    )
    # This automatically goes to room "campaign:{campaign_id}"
```

### Pattern 3: Conditional Notifications

```python
@shared_task
def process_email_open(email_id: int, campaign_id: int):
    """Process email open event."""

    # ... process logic ...

    # Only notify if campaign is active
    campaign = get_campaign(campaign_id)
    if campaign.status == "RUNNING":
        ws_publisher.email_opened(
            to_email=email.to_email,
            opened_at=datetime.utcnow().isoformat(),
            campaign_id=campaign_id,
            lead_id=email.lead_id
        )
```

---

## Best Practices

1. **Always use try/except**: Wrap publisher calls to prevent task failures
2. **Include task IDs**: Generate unique IDs for tracking
3. **Provide progress updates**: Every 10-20% for long tasks
4. **Use appropriate rooms**: Send targeted messages to rooms
5. **Keep messages small**: Don't send large data payloads
6. **Log all events**: Use logger alongside WebSocket events

---

## Complete Integration Checklist

- [ ] Import `ws_publisher` at top of file
- [ ] Add event at task start (if applicable)
- [ ] Add progress events for long-running tasks
- [ ] Add completion event with results
- [ ] Add failure event in exception handler
- [ ] Test with WebSocket client connection
- [ ] Verify events appear in Redis (optional)
- [ ] Check WebSocket stats endpoint

---

## Need Help?

- See full event reference: `WEBSOCKET_GUIDE.md`
- Check publisher methods: `app/core/websocket_publisher.py`
- View event schemas: `app/schemas/websocket_events.py`
- WebSocket endpoints: `app/api/endpoints/websocket.py`

Happy integrating!
