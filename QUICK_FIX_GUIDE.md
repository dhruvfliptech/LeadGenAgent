# Quick Fix Guide - Production Issues

**Time to Fix:** 30-60 minutes
**Priority:** CRITICAL - Do This Now

---

## Step 1: Fix Backend CSP Configuration (5 minutes)

### File: `backend/app/core/security_middleware.py`

**Find lines 68-79 and replace with:**

```python
# Content-Security-Policy - Prevent XSS and other injection attacks
csp_directives = [
    "default-src 'self'",
    f"script-src 'self' 'nonce-{nonce}'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # ✅ FIXED: Added Google Fonts
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",  # ✅ FIXED: Added Google Fonts
    "connect-src 'self' ws: wss: https:",  # ✅ FIXED: Allow WebSocket and API calls
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests"
]

# Note: Removed path-specific WebSocket logic - now global
headers["Content-Security-Policy"] = "; ".join(csp_directives)
```

**Remove the WebSocket-specific code (lines 81-83):**
```python
# DELETE THIS CODE:
# # Add WebSocket support if needed
# if request.url.path.startswith("/ws"):
#     csp_directives.append(f"connect-src 'self' ws: wss:")
```

---

## Step 2: Remove Duplicate Permissions-Policy (2 minutes)

### File: `backend/app/middleware/template_security_middleware.py`

**Find line 78-82 and DELETE (or comment out):**

```python
# DELETE OR COMMENT OUT THIS LINE:
# response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

The comprehensive version in `security_middleware.py` already handles this.

---

## Step 3: Create Frontend Production Environment File (3 minutes)

### File: `frontend/.env.production` (CREATE NEW FILE)

**Replace YOUR_DOMAIN with your actual domain:**

```env
# Production Environment Variables
# IMPORTANT: Replace placeholders with your actual production URLs

# Backend API URL - REPLACE THIS
VITE_API_URL=https://api.YOUR_DOMAIN.com

# WebSocket URL - REPLACE THIS
VITE_WS_URL=wss://api.YOUR_DOMAIN.com

# Use live API in production
VITE_USE_MOCK_DATA=false

# Feature Flags - Enable all features
VITE_ENABLE_WORKFLOWS=true
VITE_ENABLE_TEMPLATES=true
VITE_ENABLE_EMAIL_TRACKING=true
VITE_ENABLE_APPROVALS=true
VITE_ENABLE_DEMO_SITES=true
```

---

## Quick Command Summary

```bash
# 1. Update CSP in security_middleware.py
# 2. Comment out duplicate Permissions-Policy
# 3. Create frontend/.env.production with your actual domain
# 4. Update ALLOWED_HOSTS in backend production config
# 5. Rebuild and deploy

cd frontend
npm run build
```

---

See PRODUCTION_ISSUES_ANALYSIS.md for detailed explanations.
