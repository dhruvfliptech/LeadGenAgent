# CraigLeads Pro - Production Issues Analysis

**Date:** November 9, 2025
**Status:** CRITICAL - Application Not Functional in Production
**Priority:** P0 - Immediate Fix Required

---

## Executive Summary

The application is experiencing **complete failure in production** due to multiple critical security and configuration issues. The errors indicate:

1. **Content Security Policy (CSP) violations** - Blocking external resources
2. **Network connectivity errors** - API communication failures
3. **Security header conflicts** - Duplicate/conflicting policies
4. **CORS misconfiguration** - Backend not allowing frontend connections

---

## Critical Issues Identified

### 🔴 ISSUE #1: Content Security Policy (CSP) Violations

**Error Messages:**
```
Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline'"

Refused to connect to '<URL>' because it violates the following Content Security Policy directive:
"connect-src 'self' ..."
```

**Root Cause:**

The CSP configuration in `backend/app/core/security_middleware.py` (lines 68-79) is **too restrictive**:

```python
csp_directives = [
    "default-src 'self'",
    f"script-src 'self' 'nonce-{nonce}'",
    "style-src 'self' 'unsafe-inline'",  # ❌ Missing fonts.googleapis.com
    "img-src 'self' data: https:",
    "font-src 'self'",  # ❌ Missing fonts.gstatic.com
    "connect-src 'self'",  # ❌ Missing API domain, WS domain
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests"
]
```

**Impact:**
- ❌ Google Fonts blocked → UI renders without proper fonts
- ❌ External API calls blocked → "Network error" messages
- ❌ WebSocket connections blocked → Real-time features fail
- ❌ External resources blocked → Broken functionality

**Fix Required:**

Update CSP directives to allow necessary external resources:

```python
csp_directives = [
    "default-src 'self'",
    f"script-src 'self' 'nonce-{nonce}'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",  # ✅ Allow Google Fonts
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",  # ✅ Allow Google Fonts
    "connect-src 'self' ws: wss: https:",  # ✅ Allow WebSocket and HTTPS connections
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests"
]
```

---

### 🔴 ISSUE #2: Feature-Policy / Permissions-Policy Header Conflict

**Error Message:**
```
Error with Feature-Policy header: Some features are specified in both Feature-Policy and
Permissions-Policy header: camera, microphone, geolocation. Values defined in Permissions-Policy
header will be used.
```

**Root Cause:**

**DUPLICATE HEADER DEFINITIONS** across two middleware files:

1. **File:** `backend/app/middleware/template_security_middleware.py` (line 78-82)
```python
response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

2. **File:** `backend/app/core/security_middleware.py` (lines 61-65)
```python
headers["Permissions-Policy"] = (
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
    "magnetometer=(), microphone=(), payment=(), usb=()"
)
```

**Impact:**
- ⚠️ Browser warning messages (not critical, but indicates poor code quality)
- ⚠️ Inconsistent policy enforcement
- ⚠️ Potential browser compatibility issues

**Fix Required:**

Remove the duplicate from `template_security_middleware.py` and keep only the comprehensive version in `security_middleware.py`.

---

### 🔴 ISSUE #3: Network Connection Failures

**Error Message:**
```
Network error. Please check your connection.
```

**Root Causes:**

#### 3.1 Frontend Environment Configuration

**Current:** Frontend is configured for **localhost** in `.env.development`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Issue:** When deployed to production:
- Frontend tries to connect to `localhost:8000` (which doesn't exist in browser)
- No production `.env.production` file for frontend
- Environment variables not set during build

#### 3.2 CORS Configuration Issue

**Current:** Backend CORS in `backend/app/main.py` (lines 261-267):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts_list,  # ❌ Only localhost domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**From `.env.production`:**
```env
ALLOWED_HOSTS=["https://your-frontend-domain.com", "https://api.your-domain.com"]
```

**Issue:**
- Placeholder domains not replaced with actual production domains
- Frontend origin not in ALLOWED_HOSTS → CORS blocks all requests
- Backend rejects all production frontend requests

#### 3.3 CSP `connect-src` Blocking API Calls

As mentioned in Issue #1, the CSP directive:
```python
"connect-src 'self'"
```

Blocks all external API calls including:
- Backend API calls from frontend
- WebSocket connections
- Third-party API integrations

**Impact:**
- 🔴 **COMPLETE APPLICATION FAILURE**
- No API communication possible
- All data fetching fails
- Real-time features non-functional

**Fixes Required:**

1. **Create frontend production environment file:**

Create `/frontend/.env.production`:
```env
VITE_API_URL=https://your-actual-api-domain.com
VITE_WS_URL=wss://your-actual-api-domain.com
VITE_USE_MOCK_DATA=false
VITE_ENABLE_WORKFLOWS=true
VITE_ENABLE_TEMPLATES=true
VITE_ENABLE_EMAIL_TRACKING=true
VITE_ENABLE_APPROVALS=true
VITE_ENABLE_DEMO_SITES=true
```

2. **Update backend `.env.production` with actual domains:**
```env
ALLOWED_HOSTS=https://your-actual-frontend-domain.com,https://your-actual-api-domain.com
```

3. **Fix CSP `connect-src` directive** (covered in Issue #1)

---

### 🟡 ISSUE #4: CORS Wildcard Security Risk

**Current Configuration:** `backend/app/main.py` (lines 265-266)
```python
allow_methods=["*"],
allow_headers=["*"],
```

**Issue:**
- Allows ALL HTTP methods (including dangerous ones like TRACE)
- Allows ALL headers (potential security risk)
- Not following security best practices

**Fix Required:**

Replace wildcards with explicit whitelist:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # ✅ Explicit list
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin"
    ],  # ✅ Whitelist specific headers
)
```

---

### 🟡 ISSUE #5: Missing Frontend Security Meta Tags

**Current:** `frontend/index.html` (lines 1-17)
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="..." />
    <title>FlipTech Pro - Lead Generation Dashboard</title>
    <!-- ❌ No CSP meta tag -->
    <!-- ❌ No security headers -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
```

**Issue:**
- No CSP meta tag for client-side enforcement
- Missing X-UA-Compatible for IE compatibility
- External resources loaded without integrity checks (SRI)

**Fix Required:**

Add security meta tags:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <!-- Content Security Policy -->
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'self';
                   script-src 'self';
                   style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
                   font-src 'self' https://fonts.gstatic.com;
                   img-src 'self' data: https:;
                   connect-src 'self' ws: wss: https:;">

    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="description" content="FlipTech Pro - Multi-source Lead Generation & Outreach Automation Platform" />
    <title>FlipTech Pro - Lead Generation Dashboard</title>

    <!-- Preconnect for performance -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  </head>
```

---

### 🟡 ISSUE #6: Inconsistent X-Frame-Options

**Found in two files with DIFFERENT values:**

1. **`backend/app/middleware/template_security_middleware.py`** (line 79):
```python
response.headers["X-Frame-Options"] = "SAMEORIGIN"
```

2. **`backend/app/core/security_middleware.py`** (line 50):
```python
headers["X-Frame-Options"] = "DENY"
```

**Issue:**
- Conflicting values → Last one wins
- Inconsistent clickjacking protection
- Code maintainability issue

**Fix Required:**

Standardize to **`DENY`** for maximum security (unless you need to embed pages):
- Remove from `template_security_middleware.py`
- Keep only in `security_middleware.py` with value `DENY`

---

### 🟡 ISSUE #7: Development Server Exposed on All Interfaces

**File:** `frontend/vite.config.ts` (line 11)
```typescript
server: {
    port: 5176,
    host: true,  // ❌ Exposes to 0.0.0.0
    strictPort: true,
    watch: {
      usePolling: true
    }
}
```

**Issue:**
- `host: true` binds to `0.0.0.0` (all network interfaces)
- Exposes dev server to entire network
- Security risk if on shared network

**Fix Required:**

For production builds, this doesn't matter (only affects `vite dev`), but for security:
```typescript
server: {
    port: 5176,
    host: process.env.NODE_ENV === 'production' ? false : true,  // ✅ Only in dev
    strictPort: true,
    watch: {
      usePolling: true
    }
}
```

---

## Additional Shortcomings Identified

### 1. **No CSRF Protection**

**Issue:** No CSRF token validation visible in the codebase.

**Impact:** Vulnerable to Cross-Site Request Forgery attacks.

**Recommendation:** Implement CSRF protection for state-changing operations.

---

### 2. **No Rate Limiting at Application Level**

**Issue:** While security middleware exists, no global rate limiting is applied at the CORS/middleware level.

**Impact:** Vulnerable to brute force and DDoS attacks.

**Current:** Only feature-specific rate limits mentioned in docs.

**Recommendation:** Add rate limiting middleware before CORS.

---

### 3. **Unsafe Inline Styles in CSP**

**Current:** `"style-src 'self' 'unsafe-inline'"`

**Issue:** Allows inline styles, which can be exploited for XSS attacks.

**Impact:** Weakens XSS protection.

**Recommendation:**
- Use nonce-based or hash-based CSP for styles
- Move inline styles to external files

---

### 4. **No Subresource Integrity (SRI) for External Resources**

**Issue:** External resources (Google Fonts) loaded without integrity checks.

**Impact:** Vulnerable to CDN compromises.

**Recommendation:** Add SRI hashes to external links.

---

### 5. **Placeholder Production Configuration**

**File:** `.env.production` contains placeholder values:
```env
DATABASE_URL=postgresql://username:password@your-db-host:5432/craigslist_leads
REDIS_URL=redis://your-redis-host:6379
ALLOWED_HOSTS=["https://your-frontend-domain.com", "https://api.your-domain.com"]
SECRET_KEY=generate-a-secure-secret-key-using-openssl-rand-hex-32
```

**Issue:**
- Not ready for production deployment
- May have been deployed with placeholder values
- Critical security risk if SECRET_KEY is default

**Fix Required:** Replace all placeholder values with actual production values.

---

### 6. **No Health Check for CSP/CORS Issues**

**Issue:** `/health` endpoint doesn't check if CSP/CORS is properly configured.

**Recommendation:** Add configuration validation to health check.

---

### 7. **WebSocket CSP Configuration**

**Current:** `backend/app/core/security_middleware.py` (lines 81-83)
```python
# Add WebSocket support if needed
if request.url.path.startswith("/ws"):
    csp_directives.append(f"connect-src 'self' ws: wss:")
```

**Issue:**
- Only adds WebSocket support for `/ws` paths
- Doesn't help with general API calls
- Should be global, not path-specific

**Fix Required:** Move WebSocket support to main CSP directive list.

---

## Action Plan - Priority Order

### 🔴 **P0 - Critical (Fix Immediately)**

1. **Fix CSP `connect-src` directive** - Allow API and WebSocket connections
   - File: `backend/app/core/security_middleware.py` (line 74)
   - Change: `"connect-src 'self' ws: wss: https:"`

2. **Fix CSP `style-src` and `font-src`** - Allow Google Fonts
   - File: `backend/app/core/security_middleware.py` (lines 71, 73)
   - Add: `https://fonts.googleapis.com` to `style-src`
   - Add: `https://fonts.gstatic.com` to `font-src`

3. **Create frontend `.env.production`** with actual production URLs
   - File: `frontend/.env.production` (create new)
   - Add actual API and WebSocket URLs

4. **Update backend `.env.production`** with actual ALLOWED_HOSTS
   - File: `backend/.env.production` (or wherever production env is stored)
   - Replace placeholder domains with actual production domains

5. **Verify SECRET_KEY is properly set** in production
   - Ensure it's not the default placeholder value

---

### 🟡 **P1 - High (Fix Soon)**

6. **Remove Permissions-Policy duplicate**
   - File: `backend/app/middleware/template_security_middleware.py` (line 78-82)
   - Remove the duplicate header

7. **Standardize X-Frame-Options**
   - Choose `DENY` or `SAMEORIGIN` and use consistently
   - Remove from one of the two files

8. **Replace CORS wildcards with explicit lists**
   - File: `backend/app/main.py` (lines 265-266)
   - Use explicit method and header lists

---

### 🟢 **P2 - Medium (Fix Next Sprint)**

9. **Add CSP meta tag to index.html**
   - File: `frontend/index.html`
   - Add client-side CSP enforcement

10. **Implement CSRF protection**
    - Add CSRF token validation for state-changing operations

11. **Add rate limiting middleware**
    - Protect against brute force and DDoS

12. **Fix inline styles CSP issue**
    - Move to nonce-based or hash-based CSP

---

### 🔵 **P3 - Low (Nice to Have)**

13. **Add SRI to external resources**
14. **Fix Vite dev server exposure**
15. **Add CSP/CORS validation to health check**
16. **Fix WebSocket CSP path-specific logic**

---

## Testing Checklist (After Fixes)

- [ ] **Frontend loads without CSP errors in browser console**
- [ ] **Google Fonts load correctly**
- [ ] **API calls succeed (check Network tab)**
- [ ] **WebSocket connections establish successfully**
- [ ] **No "Network error" messages appear**
- [ ] **No Permissions-Policy warnings in console**
- [ ] **CORS allows frontend domain**
- [ ] **All features functional (test each major feature)**
- [ ] **Health check endpoint returns 200 OK**
- [ ] **No security warnings in browser DevTools**

---

## Deployment Recommendations

### Before Next Deployment:

1. **Use environment-specific builds:**
   ```bash
   # Frontend
   npm run build -- --mode production

   # Backend
   export ENVIRONMENT=production
   ```

2. **Verify environment variables:**
   ```bash
   # Check all required vars are set
   echo $DATABASE_URL
   echo $REDIS_URL
   echo $SECRET_KEY
   echo $ALLOWED_HOSTS
   ```

3. **Test locally with production config:**
   ```bash
   # Use production .env locally first
   cp .env.production .env
   # Run and test
   # Then deploy
   ```

4. **Set up monitoring:**
   - Enable error tracking (Sentry, etc.)
   - Monitor CSP violations
   - Track API error rates
   - Set up alerts for failures

---

## Root Cause Summary

The production failures stem from **three main categories of issues**:

1. **Security Over-Configuration:** CSP is too restrictive, blocking legitimate resources
2. **Environment Misconfiguration:** Placeholder values not replaced, wrong URLs for production
3. **Code Quality Issues:** Duplicate/conflicting security headers, no consistency

**Severity:** **CRITICAL** - Application is completely non-functional in production

**Estimated Fix Time:** 2-4 hours for P0 issues

**Prevention:**
- Add pre-deployment checklist
- Implement integration tests that check CSP/CORS
- Use environment-specific config validation
- Add health checks for configuration issues

---

## Contact

For questions or implementation assistance, refer to:
- `TECHNICAL_PROJECT_OVERVIEW.md` - Architecture details
- `backend/app/core/security_middleware.py` - Security implementation
- `backend/app/main.py` - Application configuration

---

**Document Version:** 1.0
**Last Updated:** November 9, 2025
**Next Review:** After P0 fixes are deployed
