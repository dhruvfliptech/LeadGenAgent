# Email Infrastructure - Quick Reference

Fast reference for FlipTech Pro email sending infrastructure.

## Files

```
backend/
├── app/
│   ├── core/
│   │   └── email_config.py          # Email configuration settings
│   ├── services/
│   │   ├── email_service.py         # Core email sending service
│   │   ├── email_template_service.py # Template rendering & tracking
│   │   └── campaign_service.py      # Campaign management (updated)
│   └── api/
│       └── endpoints/
│           └── email_tracking.py    # Tracking endpoints
├── .env.example                      # Environment configuration example
├── EMAIL_SETUP_GUIDE.md             # Complete setup guide
└── requirements.txt                  # Updated with jinja2
```

## Quick Setup (Gmail)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here  # Get from Google App Passwords
TEST_MODE=true  # Set false for production

# 3. Install dependencies
pip install jinja2

# 4. Test
python -c "from app.services.email_service import EmailService; print('OK')"
```

## Send Email (Simple)

```python
from app.services.email_service import EmailService

service = EmailService()
result = service.send_email(
    to_email="user@example.com",
    subject="Hello",
    html_body="<h1>Hello World!</h1>"
)
```

## Send Campaign Email (with Tracking)

```python
from app.services.email_service import EmailService
from app.db.database import SessionLocal

db = SessionLocal()
service = EmailService(db=db)

result = service.send_campaign_email(
    campaign_id=1,
    lead_id=123,
    subject="Special Offer",
    html_body="<h1>Check this out!</h1><p><a href='https://example.com'>Click here</a></p>"
)

db.close()
```

## API Endpoints

### Tracking Open
```http
GET /api/v1/tracking/open/{token}
Returns: 1x1 transparent pixel
```

### Tracking Click
```http
GET /api/v1/tracking/click/{token}?url=https://example.com
Returns: 302 redirect to original URL
```

### Unsubscribe
```http
GET /api/v1/tracking/unsubscribe/{token}
Returns: HTML confirmation page
```

## Environment Variables (Essential)

```bash
# Provider
EMAIL_PROVIDER=smtp              # smtp, sendgrid, mailgun, resend

# SMTP (Gmail/Outlook)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=email@gmail.com
SMTP_PASSWORD=app-password-here

# Sender
EMAIL_FROM=noreply@domain.com
EMAIL_FROM_NAME=FlipTech Pro
EMAIL_REPLY_TO=support@domain.com

# Tracking
TRACKING_DOMAIN=http://localhost:8000  # Change in production
TRACKING_PIXEL_ENABLED=true
LINK_TRACKING_ENABLED=true

# Testing
TEST_MODE=false                  # true = log only, false = send
DEBUG_EMAIL_OVERRIDE=            # Override all recipients for testing

# Limits
MAX_EMAILS_PER_HOUR=100
BATCH_SIZE=50
```

## Template Rendering

```python
from app.services.email_template_service import EmailTemplateService

service = EmailTemplateService()

# Render template
template = "<h1>Hello {{ name }}!</h1>"
html = service.render_template(template, {"name": "John"})

# Add tracking
html = service.add_tracking_pixel(html, "token-123")
html = service.wrap_links_for_tracking(html, "token-123")
html = service.add_unsubscribe_link(html, "token-123")

# Generate text version
text = service.generate_text_version(html)
```

## Campaign Workflow

```python
from app.services.campaign_service import CampaignService
from app.db.database import get_async_session

async def send_campaign():
    async with get_async_session() as db:
        service = CampaignService(db)

        # 1. Launch campaign (queues emails)
        campaign = await service.launch_campaign(
            campaign_id=1,
            send_immediately=True
        )

        # 2. Send emails (call separately or in background worker)
        # TODO: Move to Celery task in production
        results = await service.send_campaign_emails_sync(
            campaign_id=1,
            batch_size=50
        )

        print(f"Sent: {results['sent']}/{results['total']}")
        print(f"Failed: {results['failed']}")
```

## Testing Mode

```bash
# Enable test mode
TEST_MODE=true
```

Output when sending:
```
================================================================================
TEST MODE - Email would be sent:
To: user@example.com
From: FlipTech Pro <noreply@fliptechpro.com>
Subject: Welcome
Tracking Token: 1:123:abc123
HTML Body Length: 1234 chars
================================================================================
```

## Provider Comparison

| Provider  | Free Tier      | Setup Time | Best For              |
|-----------|----------------|------------|-----------------------|
| SMTP      | 100-500/day    | 5 min      | Development, testing  |
| SendGrid  | 100/day        | 15 min     | Production, analytics |
| Mailgun   | 5k/mo (3 mo)   | 20 min     | Developers, EU data   |
| Resend    | 100/day        | 10 min     | Modern projects       |

## Common Issues

### Email not sending
```python
# Check configuration
from app.core.email_config import email_config
is_valid, errors = email_config.validate_configuration()
print(errors)
```

### SMTP auth failed
- Gmail: Use app password, not regular password
- Enable 2FA first, then generate app password

### Emails in spam
- Use dedicated domain (not @gmail.com)
- Set up SPF, DKIM, DMARC records
- Include plain text version
- Add unsubscribe link

### Tracking not working
```bash
# Check tracking domain matches backend URL
TRACKING_DOMAIN=http://localhost:8000  # Dev
TRACKING_DOMAIN=https://api.yourdomain.com  # Prod
```

## TODO: Celery Integration

For production, move email sending to background tasks:

```python
# app/tasks/email.py
from celery import shared_task

@shared_task
def send_campaign_emails_task(campaign_id: int):
    """Send campaign emails in background"""
    from app.db.database import SessionLocal
    from app.services.campaign_service import CampaignService

    db = SessionLocal()
    try:
        service = CampaignService(db)
        return service.send_campaign_emails_sync(campaign_id)
    finally:
        db.close()

# Usage
send_campaign_emails_task.delay(campaign_id=1)
```

## Monitoring

Key metrics to track:
- Delivery rate: > 95%
- Open rate: 15-25%
- Click rate: 2-5%
- Bounce rate: < 5%
- Spam rate: < 0.1%

## Support

- Full guide: `EMAIL_SETUP_GUIDE.md`
- Logs: `tail -f logs/app.log | grep email`
- Config: `app/core/email_config.py`
- Service: `app/services/email_service.py`

---

**Version**: 1.0.0
**Last Updated**: November 2024
