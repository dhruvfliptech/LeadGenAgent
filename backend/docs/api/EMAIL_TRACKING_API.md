# Email Tracking API Documentation

## Overview

The Email Tracking API provides real-time tracking of email engagement including open tracking, link click tracking, and unsubscribe management. This system uses transparent pixel tracking and secure token-based redirects.

**Base URL:** `/api/v1/tracking`

## Key Features

- Transparent 1x1 pixel tracking for email opens
- Secure click tracking with URL validation
- Unsubscribe management with GDPR compliance
- No-cache enforcement for real-time tracking
- SSRF and open redirect prevention
- Visitor identification and analytics

## Architecture

The Email Tracking system works by:

1. **Open Tracking:** Embeds a tracking pixel in emails. When the email is opened, the pixel loads.
2. **Click Tracking:** Replaces links with tracking URLs that record clicks before redirecting.
3. **Unsubscribe Tracking:** Marks leads as unsubscribed and prevents future emails.

---

## Endpoints

### 1. Track Email Open

Record email open event using 1x1 transparent GIF pixel.

**Endpoint:** `GET /open/{tracking_token}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tracking_token | string | Yes | Unique tracking token from email |

**Response:**

- Content-Type: `image/gif`
- Body: 1x1 transparent GIF pixel (43 bytes)
- Headers: Cache-Control: no-cache, must-revalidate

**Response Headers:**

```
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
Content-Type: image/gif
Content-Length: 43
```

**Usage in Email Template:**

```html
<img src="https://api.example.com/api/v1/tracking/open/abc123token"
     width="1" height="1" alt="" style="display:none;" />
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/tracking/open/abc123token" \
  -v
```

**Example Response:**

```
< HTTP/1.1 200 OK
< Cache-Control: no-cache, no-store, must-revalidate
< Pragma: no-cache
< Expires: 0
< Content-Type: image/gif
< Content-Length: 43

[Binary GIF data - 1x1 transparent pixel]
```

**Notes:**

- Returns GIF pixel even if tracking fails (graceful degradation)
- Non-blocking - does not interrupt email experience
- No user-agent detection required
- Works across all email clients

---

### 2. Track Email Click

Record email link click and redirect to original URL.

**Endpoint:** `GET /click/{tracking_token}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tracking_token | string | Yes | Unique tracking token from email |
| url | string | Yes | Original URL to redirect to (URL-encoded) |

**Query String Example:**

```
GET /api/v1/tracking/click/abc123token?url=https%3A%2F%2Fexample.com%2Fpage
```

**Response:**

- Status: `302 Found` (HTTP redirect)
- Location: Original URL (validated)
- Headers: Cache-Control: no-cache

**Security Validation:**

All redirect URLs are validated to prevent:
- Open redirect attacks
- SSRF attacks
- Malicious URL schemes
- Private IP ranges (configurable)

**Usage in Email Template:**

```html
<a href="https://api.example.com/api/v1/tracking/click/abc123token?url=https%3A%2F%2Fexample.com%2Fpage">
  Click here
</a>
```

**Example Request:**

```bash
# Click tracking with URL parameter
curl -X GET "https://api.example.com/api/v1/tracking/click/abc123token?url=https%3A%2F%2Fexample.com%2Fpage" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -L
```

**Error Responses:**

| Code | Message | Description |
|------|---------|-------------|
| 302 | Redirect | Success - redirects to URL |
| 400 | Invalid redirect URL | URL failed security validation |
| 400 | Invalid tracking token | Token malformed or invalid |
| 404 | Token not found | Tracking token doesn't exist |
| 500 | Server error | Internal processing error |

**Example Error Response:**

```json
{
  "detail": "Invalid redirect URL. For security reasons, we cannot redirect to this URL."
}
```

---

### 3. Unsubscribe from Emails

Mark lead as unsubscribed from email campaigns.

**Endpoint:** `GET /unsubscribe/{tracking_token}`

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| tracking_token | string | Yes | Unique tracking token from email |

**Response:**

- Content-Type: `text/html`
- Status: 200 OK
- Body: Styled HTML confirmation page

**Response Schema (HTML):**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Unsubscribed - FlipTech Pro</title>
</head>
<body>
  <div class="container">
    <h1>You've Been Unsubscribed</h1>
    <p>The email address test@example.com has been successfully removed from our mailing list.</p>
    <p>You will no longer receive marketing emails from FlipTech Pro.</p>
  </div>
</body>
</html>
```

**Usage in Email Template:**

```html
<p>
  <a href="https://api.example.com/api/v1/tracking/unsubscribe/abc123token">
    Unsubscribe from these emails
  </a>
</p>
```

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/tracking/unsubscribe/abc123token"
```

**Example Response:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unsubscribed - FlipTech Pro</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 40px; }
        .container { background: white; padding: 40px; border-radius: 8px; max-width: 500px; }
        h1 { color: #333; }
        p { color: #666; }
        .success-icon { font-size: 48px; color: #28a745; }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>You've Been Unsubscribed</h1>
        <p>The email address test@example.com has been successfully removed...</p>
    </div>
</body>
</html>
```

**Database Impact:**

The endpoint updates the lead record:
- Sets `email_unsubscribed = true` or `status = 'opted_out'`
- Records unsubscribe timestamp
- Triggers unsubscribe notification

**Compliance:**

- GDPR compliant - one-click unsubscribe
- CAN-SPAM compliant
- CASL compliant (Canada)
- GDPR Article 21 right to object

---

### 4. Unsubscribe Confirmation Page

Generic unsubscribe confirmation page.

**Endpoint:** `GET /unsubscribe-confirm`

**Response:**

- Content-Type: `text/html`
- Status: 200 OK
- Body: HTML form for manual unsubscribe

**Usage:**

Fallback page if token-based unsubscribe fails.

**Example Request:**

```bash
curl -X GET "https://api.example.com/api/v1/tracking/unsubscribe-confirm"
```

---

## Tracking Token Generation

### Token Structure

Tracking tokens are generated by the email service and encoded with:
- Campaign ID
- Lead ID
- Creation timestamp
- HMAC signature for validation

**Example Generation (Python):**

```python
import hmac
import hashlib
import base64
from datetime import datetime

def generate_tracking_token(campaign_id: int, lead_id: int, secret_key: str) -> str:
    """Generate a tracking token."""
    timestamp = int(datetime.utcnow().timestamp())
    data = f"{campaign_id}:{lead_id}:{timestamp}"

    # Create HMAC signature
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).digest()

    # Combine and encode
    token = base64.urlsafe_b64encode(data.encode() + signature).decode().rstrip('=')
    return token
```

---

## Integration Examples

### Email Template Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>Your Campaign</title>
</head>
<body>
    <h1>Hello {{first_name}}</h1>
    <p>Check out this great opportunity:</p>

    <!-- Include tracking pixel for open tracking -->
    <img src="https://api.example.com/api/v1/tracking/open/{{tracking_token}}"
         width="1" height="1" alt="" style="display:none;" />

    <!-- Use tracked links for click tracking -->
    <a href="https://api.example.com/api/v1/tracking/click/{{tracking_token}}?url=https%3A%2F%2Fexample.com%2Foffer">
        View Offer
    </a>

    <!-- Unsubscribe link (REQUIRED by law) -->
    <p style="font-size: 12px; color: #999;">
        <a href="https://api.example.com/api/v1/tracking/unsubscribe/{{tracking_token}}">
            Unsubscribe from these emails
        </a>
    </p>
</body>
</html>
```

### Python SDK Integration

```python
from email_service import EmailService

# Send email with tracking
email_service = EmailService()

token = email_service.generate_tracking_token(
    campaign_id=1,
    lead_id=42
)

# Replace placeholders in template
html_content = f"""
<img src="https://api.example.com/api/v1/tracking/open/{token}" width="1" height="1" />
<a href="https://api.example.com/api/v1/tracking/click/{token}?url=...">Link</a>
"""

email_service.send_email(
    to=lead.email,
    subject="Campaign",
    html=html_content,
    tracking_token=token
)
```

### JavaScript Integration

```javascript
// Generate email with tracking
const generateTrackedEmail = (lead, campaignId) => {
  const token = generateTrackingToken(campaignId, lead.id);

  return `
    <img src="https://api.example.com/api/v1/tracking/open/${token}"
         width="1" height="1" style="display:none;" />
    <a href="https://api.example.com/api/v1/tracking/click/${token}?url=${encodeURIComponent('https://example.com')}">
      Click Here
    </a>
    <a href="https://api.example.com/api/v1/tracking/unsubscribe/${token}">
      Unsubscribe
    </a>
  `;
};
```

---

## Analytics and Reporting

### Track Email Events

Events are automatically tracked in the database:

| Event | Trigger | Database Field |
|-------|---------|-----------------|
| `email_opened` | Pixel loads | email_opened = true |
| `email_clicked` | Link clicked | email_clicked = true |
| `email_unsubscribed` | Unsubscribe link | email_unsubscribed = true |

### Query Email Metrics

```python
from app.models import Lead, Campaign

# Get leads who opened emails
opened = db.query(Lead).filter(Lead.email_opened == True).all()

# Get leads who clicked
clicked = db.query(Lead).filter(Lead.email_clicked == True).all()

# Get unsubscribed leads
unsubscribed = db.query(Lead).filter(Lead.email_unsubscribed == True).all()

# Calculate rates
open_rate = len(opened) / total_sent
click_rate = len(clicked) / total_sent
unsubscribe_rate = len(unsubscribed) / total_sent
```

---

## Security Considerations

### 1. Token Validation

All tokens are validated using HMAC signatures:
- Prevents token forgery
- Detects tampering
- Validates expiration

### 2. URL Validation

All redirect URLs are validated:
- Domain whitelist check
- Private IP prevention
- URL scheme validation (https only)
- SSRF attack prevention

**Allowed Domains Configuration:**

```python
# settings.py
EMAIL_REDIRECT_ALLOWED_DOMAINS = [
    "example.com",
    "*.example.com",
    "trusted-domain.com"
]
```

### 3. Cache Prevention

All tracking endpoints include cache-busting headers:

```
Cache-Control: no-cache, no-store, must-revalidate
Pragma: no-cache
Expires: 0
```

This ensures every open/click is tracked, even if client-side caching is enabled.

### 4. Rate Limiting

Tracking endpoints have rate limits to prevent abuse:
- 10,000 opens per minute
- 5,000 clicks per minute
- Per-IP and per-token limits

---

## Error Handling

### Graceful Degradation

If tracking fails:
- **Open tracking:** Still returns pixel (doesn't break email)
- **Click tracking:** Redirects to validated URL (doesn't prevent navigation)
- **Unsubscribe:** Gracefully handles errors

### Retry Logic

```python
# Client-side retry example
async def track_email_open(token, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await fetch(
                f"/api/v1/tracking/open/{token}",
                method="GET"
            )
            if response.ok:
                return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## GDPR Compliance

### Data Handling

- **Minimal data collection:** Only track email engagement
- **Purpose limitation:** Data used only for engagement analytics
- **Retention:** Tracking data retained for 90 days by default
- **Deletion:** Automatic cleanup of expired tokens

### User Rights

- **Right to be forgotten:** Leads can request data deletion
- **Unsubscribe:** One-click unsubscribe via email link
- **Transparency:** Clear unsubscribe confirmation page

### Implementation

```python
# Automatic data cleanup
from datetime import datetime, timedelta

def cleanup_old_tracking_data(days=90):
    cutoff = datetime.utcnow() - timedelta(days=days)
    old_tokens = db.query(TrackingToken).filter(
        TrackingToken.created_at < cutoff
    ).delete()
    db.commit()
```

---

## Best Practices

1. **Always Include Unsubscribe Link** - Legal requirement in most jurisdictions
2. **Validate Tokens Before Use** - Prevent processing of invalid tokens
3. **Monitor Unsubscribe Rates** - High rates indicate content issues
4. **Use HTTPS URLs** - Only track over secure connections
5. **Respect Opt-out Preferences** - Never re-subscribe opted-out leads
6. **Test Email Rendering** - Ensure pixels/links work in all clients
7. **Handle Bounces** - Remove bounced emails from future campaigns
8. **Segment by Engagement** - Send only to engaged recipients

---

## Troubleshooting

### Issue: Email opens not being tracked

**Solutions:**
1. Verify tracking pixel is in email HTML
2. Check that email client loads images
3. Verify token is valid and not expired
4. Check network logs for tracking requests

### Issue: Click tracking not working

**Solutions:**
1. Verify links use correct tracking URL format
2. Check URL encoding (use `encodeURIComponent`)
3. Verify target URL is in allowed domains list
4. Test with unencoded URL first

### Issue: Unsubscribe not working

**Solutions:**
1. Verify token is valid
2. Check database for lead record
3. Verify lead email field is populated
4. Check for database transaction issues

---

## Webhook Events

Tracking events can trigger webhooks:

```
POST /webhooks/tracking-event

{
  "event_type": "email_opened|email_clicked|email_unsubscribed",
  "lead_id": 42,
  "campaign_id": 1,
  "timestamp": "2024-01-15T10:30:00Z",
  "tracking_token": "abc123token"
}
```

Configure webhooks in Account Settings.

---

## Performance Metrics

### Typical Response Times

| Endpoint | Response Time | Notes |
|----------|---------------|-------|
| /open | 5-10ms | Minimal processing |
| /click | 10-20ms | URL validation added |
| /unsubscribe | 50-100ms | Database update |

### Concurrent Load

- **Capacity:** 10,000+ concurrent tracking requests
- **Throughput:** 100,000+ events per minute
- **Availability:** 99.99% uptime SLA

---

## Examples

### Complete Email Campaign Flow

```bash
# 1. Generate tracking token
TOKEN=$(curl -X POST "https://api.example.com/api/v1/campaigns/tracking-token" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"campaign_id": 1, "lead_id": 42}' \
  | jq -r '.token')

# 2. Create email with tracking
EMAIL_HTML="
<img src='https://api.example.com/api/v1/tracking/open/$TOKEN' width='1' height='1' />
<a href='https://api.example.com/api/v1/tracking/click/$TOKEN?url=$(urlencode "https://example.com")'>
  Click here
</a>
<a href='https://api.example.com/api/v1/tracking/unsubscribe/$TOKEN'>
  Unsubscribe
</a>
"

# 3. Send email
curl -X POST "https://api.example.com/api/v1/campaigns/send" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "{\"lead_id\": 42, \"html\": \"$EMAIL_HTML\"}"

# 4. Monitor tracking events
curl "https://api.example.com/api/v1/campaigns/analytics?campaign_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Support

For issues or questions:
- Email: support@example.com
- Docs: https://docs.example.com
- Status: https://status.example.com
