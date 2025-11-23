# Email Sending Infrastructure - Setup Guide

Complete guide for setting up FlipTech Pro's email sending infrastructure with tracking.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Provider Setup](#provider-setup)
  - [SMTP (Gmail)](#smtp-gmail)
  - [SMTP (Outlook)](#smtp-outlook)
  - [SendGrid](#sendgrid)
  - [Mailgun](#mailgun)
  - [Resend](#resend)
- [Configuration](#configuration)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

FlipTech Pro includes a production-ready email infrastructure with:

- **Multi-provider support**: SMTP, SendGrid, Mailgun, Resend
- **Email tracking**: Open tracking, click tracking, unsubscribe handling
- **Template system**: Jinja2 templates with variable substitution
- **Rate limiting**: Configurable sending limits
- **Bounce detection**: Track and handle bounced emails
- **Test mode**: Development mode that logs emails instead of sending

### Architecture

```
Campaign Service
    |
    v
Email Service (multi-provider)
    |
    +-- SMTP (Gmail, Outlook, Custom)
    +-- SendGrid API
    +-- Mailgun API
    +-- Resend API
    |
    v
Email Template Service
    |
    +-- Template rendering (Jinja2)
    +-- Tracking pixel injection
    +-- Link wrapping
    +-- Unsubscribe link
    |
    v
Tracking Endpoints
    |
    +-- /api/v1/tracking/open/{token}
    +-- /api/v1/tracking/click/{token}
    +-- /api/v1/tracking/unsubscribe/{token}
```

---

## Quick Start

### 1. Copy Environment File

```bash
cd backend
cp .env.example .env
```

### 2. Configure Email Provider

**For Testing (Gmail - easiest):**

```bash
# In .env file:
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
TEST_MODE=true  # Logs emails instead of sending
```

### 3. Test Configuration

```python
# Test in Python shell
from app.services.email_service import EmailService

service = EmailService()
result = service.send_email(
    to_email="test@example.com",
    subject="Test Email",
    html_body="<h1>Hello World!</h1>"
)
print(result)
```

---

## Provider Setup

### SMTP (Gmail)

**Best for**: Development, testing, small campaigns (up to 100-500 emails/day)

#### Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification

#### Step 2: Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and your device
3. Click "Generate"
4. Copy the 16-character password (remove spaces)

#### Step 3: Configure

```bash
# .env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # App password from step 2
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=your-email@gmail.com
```

#### Gmail Limits

- **Free tier**: ~100-500 emails/day
- **Google Workspace**: 2,000 emails/day
- Rate limit: ~30 emails/minute

**Warning**: Gmail may mark your emails as spam if sending to many recipients. Not recommended for production.

---

### SMTP (Outlook)

**Best for**: Development, Office 365 users

#### Configuration

```bash
# .env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
EMAIL_FROM=your-email@outlook.com
```

#### Outlook Limits

- **Personal**: 300 emails/day
- **Office 365**: 10,000 emails/day

---

### SendGrid

**Best for**: Production, high-volume sending, detailed analytics

#### Step 1: Sign Up

1. Create account at [SendGrid](https://sendgrid.com)
2. Verify email address

#### Step 2: Verify Sender Identity

**Option A: Single Sender Verification (Quick)**
1. Go to Settings → Sender Authentication → Single Sender Verification
2. Add your email and verify it

**Option B: Domain Authentication (Recommended for Production)**
1. Go to Settings → Sender Authentication → Authenticate Your Domain
2. Add DNS records to your domain
3. Wait for verification (usually 24-48 hours)

#### Step 3: Create API Key

1. Go to Settings → API Keys
2. Click "Create API Key"
3. Name: "FlipTech Pro Production"
4. Permissions: "Full Access" or "Mail Send"
5. Copy the key (starts with `SG.`)

#### Step 4: Configure

```bash
# .env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your-api-key-here
EMAIL_FROM=noreply@yourdomain.com  # Must be verified
EMAIL_FROM_NAME=FlipTech Pro
```

#### Step 5: Install SDK (if using API)

```bash
pip install sendgrid
```

Then uncomment the SendGrid code in `app/services/email_service.py`

#### SendGrid Limits

- **Free tier**: 100 emails/day forever
- **Essentials ($19.95/mo)**: 50,000 emails/month
- **Pro ($89.95/mo)**: 100,000 emails/month

---

### Mailgun

**Best for**: Developers who want control, EU data residency

#### Step 1: Sign Up

1. Create account at [Mailgun](https://mailgun.com)
2. Add payment method (required even for free tier)

#### Step 2: Add Domain

1. Go to Sending → Domains → Add New Domain
2. Add your domain (e.g., `mg.yourdomain.com`)
3. Add DNS records (MX, TXT, CNAME)
4. Wait for verification

#### Step 3: Get API Key

1. Go to Settings → API Keys
2. Copy your "Private API key"

#### Step 4: Configure

```bash
# .env
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-private-api-key
MAILGUN_DOMAIN=mg.yourdomain.com
EMAIL_FROM=noreply@mg.yourdomain.com
```

#### Step 5: Install SDK

```bash
pip install requests
```

Then uncomment the Mailgun code in `app/services/email_service.py`

#### Mailgun Limits

- **Free tier**: 5,000 emails/month (first 3 months)
- **Foundation ($35/mo)**: 50,000 emails/month
- **Growth ($80/mo)**: 100,000 emails/month

---

### Resend

**Best for**: Modern projects, developers who value simplicity

#### Step 1: Sign Up

1. Create account at [Resend](https://resend.com)
2. Verify email

#### Step 2: Verify Domain (Optional for Testing)

For testing, you can use `onboarding@resend.dev`

For production:
1. Go to Domains → Add Domain
2. Add DNS records
3. Wait for verification

#### Step 3: Create API Key

1. Go to [API Keys](https://resend.com/api-keys)
2. Click "Create API Key"
3. Copy the key (starts with `re_`)

#### Step 4: Configure

```bash
# .env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your-api-key-here
EMAIL_FROM=noreply@yourdomain.com  # Or onboarding@resend.dev for testing
```

#### Step 5: Install SDK

```bash
pip install resend
```

Then uncomment the Resend code in `app/services/email_service.py`

#### Resend Limits

- **Free tier**: 100 emails/day, 3,000 emails/month
- **Pro ($20/mo)**: 50,000 emails/month

---

## Configuration

### Environment Variables

All email configuration is in `.env`:

```bash
# Provider
EMAIL_PROVIDER=smtp  # smtp, sendgrid, mailgun, resend

# Sender settings
EMAIL_FROM=noreply@fliptechpro.com
EMAIL_FROM_NAME=FlipTech Pro
EMAIL_REPLY_TO=support@fliptechpro.com

# Tracking
TRACKING_DOMAIN=http://localhost:8000  # Change to https://yourdomain.com in prod
TRACKING_PIXEL_ENABLED=true
LINK_TRACKING_ENABLED=true

# Rate limiting
MAX_EMAILS_PER_HOUR=100
MAX_EMAILS_PER_DAY=1000
BATCH_SIZE=50
BATCH_DELAY_SECONDS=1

# Testing
TEST_MODE=false  # Set to true to log emails instead of sending
DEBUG_EMAIL_OVERRIDE=  # Override all recipients for testing
```

### Testing Mode

For development, enable test mode to log emails instead of sending:

```bash
TEST_MODE=true
```

Output:
```
================================================================================
TEST MODE - Email would be sent:
To: user@example.com
From: FlipTech Pro <noreply@fliptechpro.com>
Subject: Welcome to FlipTech Pro
Tracking Token: 123:456:abc123def456
HTML Body Length: 1234 chars
================================================================================
```

### Debug Email Override

Override all recipients for testing:

```bash
DEBUG_EMAIL_OVERRIDE=your-test-email@gmail.com
```

All emails will be sent to this address instead of real recipients.

---

## Testing

### Test Email Sending

```python
from app.services.email_service import EmailService

service = EmailService()

# Simple test
result = service.send_email(
    to_email="test@example.com",
    subject="Test Email",
    html_body="<h1>Hello!</h1><p>This is a test.</p>"
)
print(f"Success: {result['success']}")
print(f"Message ID: {result['message_id']}")
```

### Test Template Rendering

```python
from app.services.email_template_service import EmailTemplateService

template_service = EmailTemplateService()

template = """
<h1>Hello {{ name }}!</h1>
<p>Welcome to {{ company }}.</p>
"""

html = template_service.render_template(template, {
    "name": "John",
    "company": "FlipTech Pro"
})

print(html)
# Output: <h1>Hello John!</h1><p>Welcome to FlipTech Pro.</p>
```

### Test Campaign Email

```python
from app.services.email_service import EmailService
from app.db.database import SessionLocal

db = SessionLocal()
service = EmailService(db=db)

result = service.send_campaign_email(
    campaign_id=1,
    lead_id=123,
    subject="Special Offer",
    html_body="<h1>Limited Time Offer!</h1>"
)

db.close()
```

### Test Tracking

1. Send test email with tracking
2. Open email to trigger pixel
3. Click link to trigger click tracking
4. Check logs:

```bash
tail -f logs/app.log | grep "tracking"
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Verify sender domain with email provider
- [ ] Configure SPF records
- [ ] Configure DKIM records
- [ ] Set up DMARC policy
- [ ] Test deliverability to major providers (Gmail, Outlook, etc.)
- [ ] Set `TEST_MODE=false`
- [ ] Remove `DEBUG_EMAIL_OVERRIDE`
- [ ] Set `TRACKING_DOMAIN` to production domain
- [ ] Configure appropriate rate limits
- [ ] Set up monitoring and alerts
- [ ] Test unsubscribe flow
- [ ] Verify bounce handling

### DNS Records

**SPF Record** (Add to DNS):
```
Type: TXT
Name: @
Value: v=spf1 include:_spf.youremailprovider.com ~all
```

**DKIM Record** (Provided by email provider):
```
Type: TXT
Name: default._domainkey
Value: v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY
```

**DMARC Record**:
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
```

### Monitoring

Monitor these metrics:

- **Delivery rate**: Should be > 95%
- **Open rate**: Typical is 15-25%
- **Click rate**: Typical is 2-5%
- **Bounce rate**: Should be < 5%
- **Spam complaint rate**: Should be < 0.1%

### Celery Integration (TODO)

For production, move email sending to background tasks:

```python
# app/tasks/email.py
from celery import shared_task
from app.services.email_service import EmailService
from app.db.database import SessionLocal

@shared_task
def send_email_task(email_data: dict):
    """Send email asynchronously"""
    db = SessionLocal()
    try:
        service = EmailService(db=db)
        return service.send_email(**email_data)
    finally:
        db.close()

@shared_task
def send_campaign_emails_task(campaign_id: int):
    """Send all emails in a campaign"""
    db = SessionLocal()
    try:
        from app.services.campaign_service import CampaignService
        service = CampaignService(db=db)
        return service.send_campaign_emails_sync(campaign_id)
    finally:
        db.close()
```

Usage:
```python
# Instead of:
service.send_email(...)

# Use:
send_email_task.delay(email_data)
```

---

## Troubleshooting

### Email Not Sending

**Check 1**: Verify configuration
```python
from app.core.email_config import email_config

is_valid, errors = email_config.validate_configuration()
print(f"Valid: {is_valid}")
print(f"Errors: {errors}")
```

**Check 2**: Enable test mode
```bash
TEST_MODE=true
```

**Check 3**: Check logs
```bash
tail -f logs/app.log | grep "email"
```

### SMTP Authentication Failed

**Gmail**:
- Make sure 2FA is enabled
- Use app password, not regular password
- App password should be 16 characters with no spaces

**Outlook**:
- Some accounts require "Allow less secure apps"
- Check account security settings

### Emails Going to Spam

**Solutions**:
1. Verify sender domain
2. Set up SPF, DKIM, DMARC records
3. Use a dedicated sending domain (not @gmail.com)
4. Warm up your domain (start with small volumes)
5. Avoid spam trigger words
6. Include plain text version
7. Make unsubscribe link prominent

### Tracking Not Working

**Check 1**: Verify tracking domain
```bash
# Should match your backend URL
TRACKING_DOMAIN=http://localhost:8000  # Dev
TRACKING_DOMAIN=https://api.yourdomain.com  # Prod
```

**Check 2**: Test tracking endpoints
```bash
# Should return 1x1 pixel
curl http://localhost:8000/api/v1/tracking/open/test-token

# Should redirect
curl -L http://localhost:8000/api/v1/tracking/click/test-token?url=https://example.com
```

### Rate Limit Exceeded

Adjust limits based on your provider's tier:

```bash
# Gmail
MAX_EMAILS_PER_HOUR=100
MAX_EMAILS_PER_DAY=500

# SendGrid Free
MAX_EMAILS_PER_HOUR=100
MAX_EMAILS_PER_DAY=100

# SendGrid Essentials
MAX_EMAILS_PER_HOUR=2000
MAX_EMAILS_PER_DAY=50000
```

### Dependencies Missing

If you get import errors, install missing packages:

```bash
# For SendGrid
pip install sendgrid

# For Mailgun
pip install requests

# For Resend
pip install resend

# For template rendering
pip install jinja2 beautifulsoup4
```

---

## API Reference

### Email Service

```python
from app.services.email_service import EmailService

service = EmailService(db=session)

# Send single email
service.send_email(
    to_email="user@example.com",
    subject="Subject",
    html_body="<html>...</html>",
    text_body="Plain text...",  # Optional
    from_email="custom@domain.com",  # Optional
    from_name="Custom Name",  # Optional
    reply_to="reply@domain.com"  # Optional
)

# Send batch
service.send_batch([
    {"to_email": "user1@example.com", "subject": "Hi", "html_body": "..."},
    {"to_email": "user2@example.com", "subject": "Hi", "html_body": "..."}
])

# Send campaign email
service.send_campaign_email(
    campaign_id=1,
    lead_id=123,
    subject="Campaign Subject",
    html_body="<html>...</html>"
)

# Validate email
service.validate_email("user@example.com")  # Returns True or raises

# Check bounce
is_bounced = service.check_bounce("user@example.com")
```

### Template Service

```python
from app.services.email_template_service import EmailTemplateService

service = EmailTemplateService()

# Render template
html = service.render_template(
    "<h1>Hello {{ name }}!</h1>",
    {"name": "John"}
)

# Add tracking pixel
html = service.add_tracking_pixel(html, "tracking-token")

# Wrap links
html = service.wrap_links_for_tracking(html, "tracking-token")

# Generate text version
text = service.generate_text_version(html)

# Validate variables
is_valid, missing = service.validate_variables(
    template_html="<p>{{ name }} {{ email }}</p>",
    variables={"name": "John"},
    required_variables=["name", "email"]
)
```

---

## Support

For issues or questions:

1. Check logs: `tail -f logs/app.log`
2. Review this guide
3. Check provider documentation
4. Contact support

---

**Last Updated**: November 2024
**Version**: 1.0.0
