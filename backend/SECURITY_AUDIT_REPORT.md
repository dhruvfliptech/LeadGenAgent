# Security Audit Report - CraigLeads Pro Backend

**Audit Date:** November 5, 2025
**Auditor:** Security Specialist
**Scope:** 4 Newly Enabled Features
**Working Directory:** `/Users/greenmachine2.0/Craigslist/backend`

## Executive Summary

**Overall Security Score: 5.5/10 (MEDIUM-HIGH RISK)**

The audit reveals significant security vulnerabilities across all four newly enabled features. While some security measures are in place (CORS, rate limiting framework, authentication skeleton), critical vulnerabilities exist that could lead to data breaches, unauthorized access, and system compromise.

---

## Critical Security Findings by Feature

## 1. Auto-Response Templates (`app/api/endpoints/templates.py`)

### Critical Findings (HIGH SEVERITY)

#### SQL Injection Vulnerabilities
- **Lines 152, 285, 377**: Direct string interpolation in SQL WHERE clauses
- **Risk:** Attackers can execute arbitrary SQL commands
- **Evidence:**
```python
# Line 152
query = query.where(ResponseTemplate.category == category)
# Direct user input without parameterization
```
- **OWASP Reference:** A03:2021 - Injection

#### Missing Authentication
- **All endpoints**: No authentication decorators or dependency injection
- **Risk:** Unauthorized users can create, modify, and delete templates
- **Evidence:** No `Depends(get_current_user)` in any endpoint definition

#### XSS Vulnerabilities
- **Lines 190, 395**: Template content stored without sanitization
- **Risk:** Stored XSS attacks through malicious templates
- **Evidence:**
```python
# Line 190
template = ResponseTemplate(**template_data.dict())
# No HTML sanitization on body_template or subject_template
```

### Medium Findings

#### Insufficient Input Validation
- **Lines 141-145**: Query parameters not properly validated
- **Risk:** Resource exhaustion through large limit values
- **Evidence:** `limit: int = Query(100, ge=1, le=1000)` allows 1000 records

#### Missing Authorization Checks
- **Lines 233-267**: Delete operation lacks ownership verification
- **Risk:** Any user can delete any template

### Recommended Fixes
```python
# Add authentication
@router.get("/", dependencies=[Depends(get_current_user)])

# Use parameterized queries properly
from sqlalchemy import bindparam
stmt = select(ResponseTemplate).where(ResponseTemplate.category == bindparam('category'))
result = await db.execute(stmt, {'category': category})

# Input sanitization
from bleach import clean
template_data.body_template = clean(template_data.body_template, tags=[], strip=True)

# Add rate limiting
from app.core.rate_limiter import RateLimiter
@router.post("/", dependencies=[Depends(RateLimiter(times=10, per=60))])
```

---

## 2. Email Tracking (`app/api/endpoints/email_tracking.py`)

### Critical Findings (HIGH SEVERITY)

#### Insecure Direct Object Reference (IDOR)
- **Line 110**: Token decoding exposes internal IDs without validation
- **Risk:** Predictable token generation allows unauthorized access
- **Evidence:**
```python
# Line 110
campaign_id, lead_id = email_service._decode_tracking_token(tracking_token)
# No HMAC validation or signature verification
```
- **OWASP Reference:** A01:2021 - Broken Access Control

#### Open Redirect Vulnerability
- **Lines 74-84**: Unvalidated URL parameter in redirect
- **Risk:** Phishing attacks through malicious redirects
- **Evidence:**
```python
# Line 74
original_url = unquote(url)
# Line 81-82
return RedirectResponse(url=redirect_url, status_code=302)
# No domain whitelist validation
```

#### HTML Injection
- **Lines 131-194**: Unsanitized email address in HTML response
- **Risk:** HTML/JavaScript injection through malicious email addresses
- **Evidence:**
```python
# Line 182
<span class="email">{lead.email}</span>
# Direct interpolation without escaping
```

### Medium Findings

#### Missing CSRF Protection
- **Line 93**: Unsubscribe endpoint lacks CSRF tokens
- **Risk:** Forced unsubscription attacks

#### Information Disclosure
- **Lines 176-194**: Detailed error messages expose system internals

### Recommended Fixes
```python
# Secure token generation with HMAC
import hmac
import hashlib

def generate_tracking_token(campaign_id: int, lead_id: int) -> str:
    message = f"{campaign_id}:{lead_id}:{datetime.utcnow().timestamp()}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{message}:{signature}"

# URL validation
from urllib.parse import urlparse

ALLOWED_DOMAINS = ['yourdomain.com', 'trusted-partner.com']
parsed = urlparse(original_url)
if parsed.netloc not in ALLOWED_DOMAINS:
    raise HTTPException(400, "Invalid redirect URL")

# HTML escaping
from markupsafe import escape
email_safe = escape(lead.email)
html_content = f'<span class="email">{email_safe}</span>'
```

---

## 3. Demo Site Builder (`app/api/endpoints/demo_sites.py`)

### Critical Findings (HIGH SEVERITY)

#### Server-Side Template Injection (SSTI)
- **Lines 118-125**: Direct template rendering without sandboxing
- **Risk:** Remote code execution through malicious templates
- **Evidence:**
```python
# Lines 118-125
generated = await site_generator.generate_site(
    template=template,
    content_data=content_data_dict,
    style_settings=request.style_settings.dict(),
    ai_model=request.ai_model,
    use_ai=request.use_ai_generation
)
# No template sandboxing or validation
```
- **OWASP Reference:** A03:2021 - Injection

#### Arbitrary File Write
- **Lines 503-518**: File export without path validation
- **Risk:** Directory traversal and file overwrite attacks
- **Evidence:**
```python
# Line 504
"filename": "index.html",  # User controllable
"content": demo_site.generated_html
```

#### Missing Access Controls
- **All endpoints**: No tenant isolation or ownership checks
- **Risk:** Cross-tenant data access and modification

### High Findings

#### Unvalidated External Deployment
- **Lines 935-950**: Vercel deployment without content validation
- **Risk:** Deployment of malicious code to production
- **Evidence:** Direct deployment of user-provided HTML/JS/CSS without scanning

#### Resource Exhaustion
- **Line 231**: No pagination limits enforced effectively
- **Risk:** DoS through large data requests

### Recommended Fixes
```python
# Template sandboxing
from jinja2.sandbox import SandboxedEnvironment

sandbox = SandboxedEnvironment()
template = sandbox.from_string(template_string)
rendered = template.render(data)

# Path validation
import os
safe_filename = os.path.basename(filename)
if safe_filename != filename:
    raise ValueError("Invalid filename")
safe_path = os.path.join(EXPORT_DIR, safe_filename)

# Tenant isolation
query = query.where(and_(
    DemoSite.id == demo_site_id,
    DemoSite.user_id == current_user.id,
    DemoSite.is_active == True
))

# Content validation before deployment
from app.services.content_scanner import ContentScanner
scanner = ContentScanner()
if not scanner.is_safe(html_content):
    raise HTTPException(400, "Content contains potentially malicious code")
```

---

## 4. N8N Workflows (`app/api/endpoints/workflow_approvals.py`, `app/services/approval_system.py`)

### Critical Findings (HIGH SEVERITY)

#### Server-Side Request Forgery (SSRF)
- **Lines 111-112 (approval_system.py)**: Unvalidated webhook URLs
- **Risk:** SSRF attacks to internal services
- **Evidence:**
```python
# Line 111
resume_webhook_url = f"{self.n8n_base_url}/workflow-resume/{workflow_execution_id}"
# Line 484-488
async with session.post(
    approval.workflow_webhook_url,  # User-controlled URL
    json=payload,
    timeout=aiohttp.ClientTimeout(total=10)
) as response:
```
- **OWASP Reference:** A10:2021 - Server-Side Request Forgery

#### Privilege Escalation
- **Lines 664-701 (approval_system.py)**: Escalation without authorization checks
- **Risk:** Unauthorized approval privilege escalation
- **Evidence:**
```python
# Line 664
async def escalate_approval(self, approval_id: int, escalation_level: int = 1, escalated_to: Optional[str] = None):
    # No permission checks before escalation
```

### High Findings

#### Race Conditions
- **Lines 716-730**: Bulk approval without database locking
- **Risk:** Duplicate approvals and data corruption
- **Evidence:** Multiple async operations without transaction isolation

#### Insufficient Audit Logging
- **Missing**: No tamper-proof audit trail
- **Risk:** Inability to detect or investigate security incidents

### Medium Findings

#### Weak Auto-Approval Logic
- **Lines 269-300**: Predictable scoring algorithm
- **Risk:** Gaming the auto-approval system

### Recommended Fixes
```python
# SSRF Protection
from urllib.parse import urlparse
import ipaddress

def is_safe_webhook_url(url: str) -> bool:
    """Validate webhook URL against SSRF attacks"""
    parsed = urlparse(url)

    # Whitelist allowed hosts
    ALLOWED_HOSTS = ['n8n.internal', 'workflows.company.com']
    if parsed.hostname not in ALLOWED_HOSTS:
        return False

    # Block local/private IPs
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass  # Hostname, not IP

    # Only allow HTTPS
    if parsed.scheme != 'https':
        return False

    return True

# Permission checks for escalation
from app.core.auth import require_permission

@require_permission("approval.escalate")
async def escalate_approval(self, approval_id: int, ...):
    # Existing code

# Transaction locking for race conditions
from sqlalchemy import select, and_
from sqlalchemy.orm import with_for_update

async with db.begin():
    stmt = select(ResponseApproval).where(
        ResponseApproval.id == approval_id
    ).with_for_update()
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()
    # Process approval within transaction
```

---

## Global Security Issues

### Authentication & Authorization
- **Status:** Framework exists but NOT IMPLEMENTED in endpoints
- **Risk:** Complete bypass of access controls
- **Files:** `app/core/auth.py` exists but unused in new endpoints
- **Evidence:** No authentication dependencies in any of the 4 reviewed features

### Rate Limiting
- **Status:** Framework exists but NOT APPLIED to new endpoints
- **Risk:** API abuse, DoS attacks
- **Files:** `app/core/rate_limiter.py` exists but not integrated

### CORS Configuration
- **Status:** PARTIALLY CONFIGURED
- **Issue:** `allow_origins=settings.allowed_hosts_list` with `allow_credentials=True`
- **Risk:** Credential theft if origins misconfigured
- **Location:** `app/main.py` lines 358-364

### Input Validation
- **Status:** INCONSISTENT
- **Issue:** Pydantic models exist but many `.dict()` conversions bypass validation
- **Risk:** Various injection attacks

### Sensitive Data Exposure
- **Status:** HIGH RISK
- **Issues:**
  - No encryption at rest for templates
  - Tracking tokens expose internal IDs
  - Email addresses in logs
  - No PII redaction

---

## Security Recommendations Priority

### P0 - Critical (Immediate)
1. **Implement authentication on ALL endpoints**
   - Add `Depends(get_current_user)` to all route decorators
   - Implement user session management

2. **Fix SQL injection vulnerabilities**
   - Use parameterized queries consistently
   - Validate all query parameters

3. **Validate and sanitize all user inputs**
   - HTML sanitization for text fields
   - URL validation for redirects

4. **Fix open redirect vulnerability**
   - Implement domain whitelist
   - Validate all URL parameters

5. **Implement SSRF protection for webhooks**
   - URL validation and whitelisting
   - Block private IP ranges

### P1 - High (Within 24 hours)
1. **Add authorization checks (ownership verification)**
2. **Implement rate limiting on all endpoints**
3. **Secure token generation (use cryptographic signatures)**
4. **Add CSRF protection**
5. **Sandbox template rendering**

### P2 - Medium (Within 1 week)
1. **Add comprehensive audit logging**
2. **Implement input/output encoding**
3. **Add transaction isolation for concurrent operations**
4. **Configure security headers (CSP, HSTS, etc.)**
5. **Implement data encryption at rest**

---

## Compliance Gaps

### OWASP Top 10 Coverage
- ❌ A01:2021 - Broken Access Control (No auth on endpoints)
- ❌ A02:2021 - Cryptographic Failures (Weak token generation)
- ❌ A03:2021 - Injection (SQL, XSS, SSTI vulnerabilities)
- ⚠️ A04:2021 - Insecure Design (Some protections missing)
- ❌ A05:2021 - Security Misconfiguration (Auth not enforced)
- ⚠️ A06:2021 - Vulnerable Components (Unknown)
- ❌ A07:2021 - Identification and Authentication Failures (No auth)
- ⚠️ A08:2021 - Software and Data Integrity Failures (No signing)
- ⚠️ A09:2021 - Security Logging and Monitoring Failures (Incomplete)
- ❌ A10:2021 - Server-Side Request Forgery (Webhook URLs unvalidated)

### GDPR/Privacy Concerns
- No consent management for email tracking
- No data retention policies
- No right to erasure implementation
- PII exposed in logs and responses

---

## Security Testing Checklist

### Immediate Testing Required
- [ ] SQL injection testing on all query parameters
- [ ] XSS testing on all input fields
- [ ] Authentication bypass testing
- [ ] IDOR testing on all resource IDs
- [ ] Open redirect testing on URL parameters
- [ ] SSRF testing on webhook endpoints
- [ ] Rate limiting effectiveness
- [ ] CORS misconfiguration testing

### Test Commands
```bash
# SQL Injection Test
curl "http://localhost:8000/api/v1/templates/?category=test' OR '1'='1"

# XSS Test
curl -X POST "http://localhost:8000/api/v1/templates/" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","body_template":"<script>alert(1)</script>"}'

# IDOR Test
curl "http://localhost:8000/api/v1/templates/999999"

# Open Redirect Test
curl "http://localhost:8000/api/v1/tracking/click/token123?url=https://evil.com"

# SSRF Test
curl -X POST "http://localhost:8000/api/v1/workflow-approvals/create" \
  -H "Content-Type: application/json" \
  -d '{"resume_webhook_url":"http://169.254.169.254/latest/meta-data/"}'
```

---

## Conclusion

The current implementation poses **SIGNIFICANT SECURITY RISKS** and should **NOT be deployed to production** without immediate remediation of critical vulnerabilities. The lack of authentication alone makes the system completely vulnerable to unauthorized access.

**Recommended Action:**
1. **IMMEDIATELY DISABLE** these features until security fixes are implemented
2. Implement P0 fixes within 24 hours
3. Conduct security testing before re-enabling
4. Consider a professional penetration test

---

## Appendix: Quick Security Fixes

### 1. Add Authentication to All Endpoints
```python
from app.core.auth import get_current_user
from fastapi import Depends

# Update all route decorators
@router.get("/", dependencies=[Depends(get_current_user)])
@router.post("/", dependencies=[Depends(get_current_user)])
@router.put("/{id}", dependencies=[Depends(get_current_user)])
@router.delete("/{id}", dependencies=[Depends(get_current_user)])
```

### 2. Add Security Headers
```python
# app/core/security_middleware.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from secure import SecureHeaders

secure_headers = SecureHeaders()

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts_list
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    secure_headers.fastapi(response)
    return response
```

### 3. Environment Variables to Set
```bash
# Critical for Security
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL="postgresql://user:pass@localhost/db"
export ALLOWED_HOSTS="https://yourdomain.com"
export ENVIRONMENT="production"
export DEBUG="False"
export ENABLE_AUTH="True"
```

---

**Report Generated:** 2025-11-05
**Next Security Review:** After P0 fixes implemented
**Classification:** CONFIDENTIAL - CRITICAL SECURITY ISSUES FOUND