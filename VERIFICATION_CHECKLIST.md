# Frontend Integration Verification Checklist

Use this checklist to verify all frontend integration fixes are working correctly.

---

## Pre-Flight Checks

- [ ] Backend is running on `http://localhost:8000`
- [ ] Frontend is running on `http://localhost:5173`
- [ ] Database is migrated and seeded
- [ ] `.env` file exists with correct values

---

## 1. Template Type Mismatches - VERIFICATION

### Check Type Definitions

- [ ] Open `/frontend/src/types/campaign.ts`
- [ ] Verify `EmailTemplate` interface has:
  - [ ] `subject_template: string` (not `subject`)
  - [ ] `body_template: string` (not `body_html`)
  - [ ] `variables: Record<string, any>` (not `string[]`)
  - [ ] New fields: `use_ai_enhancement`, `ai_tone`, `ai_length`
- [ ] Verify `EmailTemplateCreate` interface exists
- [ ] Verify `EmailTemplateUpdate` interface exists

### Check Mock Data

- [ ] Open `/frontend/src/mocks/campaigns.mock.ts`
- [ ] Verify `mockTemplates` uses new field names
- [ ] Verify variables are objects, not arrays

### TypeScript Validation

```bash
cd /Users/greenmachine2.0/Craigslist/frontend
npm run type-check
```

- [ ] No TypeScript errors
- [ ] No type mismatches in console

**Status:** ✅ PASS / ❌ FAIL

---

## 2. Email Tracking API Service - VERIFICATION

### Check File Exists

```bash
ls -la /Users/greenmachine2.0/Craigslist/frontend/src/services/emailTrackingApi.ts
```

- [ ] File exists
- [ ] File is ~183 lines

### Check API Functions

- [ ] Open file and verify functions exist:
  - [ ] `trackOpen()`
  - [ ] `trackClick()`
  - [ ] `createTrackingUrl()`
  - [ ] `getCampaignTracking()`
  - [ ] `getEmailTracking()`
  - [ ] `unsubscribe()`

### Test in Browser Console

```javascript
// Open http://localhost:5173
import('./src/services/emailTrackingApi').then(m => {
  const url = m.emailTrackingApi.createTrackingUrl('test', 'https://example.com')
  console.log('Tracking URL:', url)
})
```

- [ ] URL generated successfully
- [ ] URL contains token
- [ ] URL points to backend

**Status:** ✅ PASS / ❌ FAIL

---

## 3. Templates UI Connected to Live API - VERIFICATION

### Check File Changes

- [ ] Open `/frontend/src/pages/Templates.tsx`
- [ ] Verify imports include:
  - [ ] `useQuery` from @tanstack/react-query
  - [ ] `useMutation` from @tanstack/react-query
  - [ ] `api` from @/services/api
- [ ] Verify `USE_MOCK_DATA` constant exists

### Test Template Operations

1. **Fetch Templates**
   - [ ] Navigate to http://localhost:5173/templates
   - [ ] Templates load from API (not mock data)
   - [ ] Loading skeleton shows briefly
   - [ ] Templates display correctly

2. **Create Template**
   - [ ] Click "Create Template" button
   - [ ] Fill in form:
     - Name: "Test Template"
     - Subject: "Hello {{name}}"
     - Body: "<p>Test email</p>"
   - [ ] Click "Create Template"
   - [ ] Success toast appears
   - [ ] Template appears in list
   - [ ] Check Network tab: POST to `/api/v1/templates`

3. **Edit Template**
   - [ ] Click edit icon on a template
   - [ ] Modify subject line
   - [ ] Click "Save Changes"
   - [ ] Success toast appears
   - [ ] Changes reflected in list
   - [ ] Check Network tab: PUT to `/api/v1/templates/{id}`

4. **Delete Template**
   - [ ] Click delete icon on test template
   - [ ] Confirm deletion
   - [ ] Success toast appears
   - [ ] Template removed from list
   - [ ] Check Network tab: DELETE to `/api/v1/templates/{id}`

5. **Duplicate Template**
   - [ ] Click duplicate icon
   - [ ] Template duplicated with "(Copy)" suffix
   - [ ] Success toast appears

### Check Loading States

- [ ] Refresh page and verify loading skeleton shows
- [ ] Loading skeleton has proper animations
- [ ] No blank screens during loading

### Check Error Handling

- [ ] Stop backend server
- [ ] Try to create template
- [ ] Error toast appears
- [ ] No app crash
- [ ] Restart backend

**Status:** ✅ PASS / ❌ FAIL

---

## 4. Environment Flags - VERIFICATION

### Check Environment Files

```bash
cd /Users/greenmachine2.0/Craigslist/frontend
ls -la .env*
```

- [ ] `.env` exists
- [ ] `.env.development` exists
- [ ] `.env.example` exists

### Check Environment Variables

```bash
cat .env
```

- [ ] `VITE_API_URL=http://localhost:8000`
- [ ] `VITE_WS_URL=ws://localhost:8000`
- [ ] `VITE_USE_MOCK_DATA=false`

### Test Mock Data Mode

1. **Enable Mock Data**
   ```bash
   echo "VITE_USE_MOCK_DATA=true" >> .env
   ```

2. **Restart Dev Server**
   ```bash
   npm run dev
   ```

3. **Verify Mock Data Used**
   - [ ] Navigate to templates page
   - [ ] Check Network tab: No API calls to `/templates`
   - [ ] Mock templates displayed
   - [ ] No errors in console

4. **Disable Mock Data**
   ```bash
   echo "VITE_USE_MOCK_DATA=false" > .env
   npm run dev
   ```

5. **Verify Live API Used**
   - [ ] Navigate to templates page
   - [ ] Check Network tab: API call to `/templates`
   - [ ] Live data displayed

**Status:** ✅ PASS / ❌ FAIL

---

## 5. Integration Tests - VERIFICATION

### Run Test Utility

1. **Open Browser Console**
   - Navigate to http://localhost:5173
   - Open DevTools (F12)
   - Go to Console tab

2. **Run All Tests**
   ```javascript
   testIntegrations()
   ```

3. **Expected Output:**
   ```
   🧪 Frontend API Integration Tests

   📧 Templates API
     ✅ GET /templates - XXms
     ✅ GET /templates/{id} - XXms

   📊 Email Tracking API
     ✅ Email Tracking - Create URL - XXms

   🔄 Workflows API
     ✅ GET /n8n-webhooks/workflows - XXms
     ✅ GET /n8n-webhooks/stats - XXms
     ✅ GET /approvals/pending - XXms

   🌐 Demo Sites API
     ✅ GET /demo-sites - XXms

   📊 Test Summary
   Total Tests: 7
   ✅ Passed: 7
   ❌ Failed: 0
   ```

4. **Verification**
   - [ ] All 7 tests pass
   - [ ] No failed tests
   - [ ] All response times < 500ms
   - [ ] No console errors

### Run Individual Tests

```javascript
testTemplatesAPI()
testWorkflowsAPI()
testEmailTrackingAPI()
testDemoSitesAPI()
```

- [ ] Templates API test passes
- [ ] Workflows API test passes
- [ ] Email Tracking API test passes
- [ ] Demo Sites API test passes

**Status:** ✅ PASS / ❌ FAIL

---

## 6. Backward Compatibility - VERIFICATION

### Check Old Field Names Work

1. **Test with Old Mock Data**
   - [ ] Create test file with old field names (`subject`, `body_html`)
   - [ ] Import in Templates page
   - [ ] Verify page still renders correctly
   - [ ] No errors in console

2. **Test Mixed Format**
   - [ ] Mix old and new field names in mock data
   - [ ] Verify all templates display
   - [ ] Fallback logic works

**Status:** ✅ PASS / ❌ FAIL

---

## 7. Documentation - VERIFICATION

### Check Documentation Files

```bash
cd /Users/greenmachine2.0/Craigslist/frontend
ls -la *.md
```

- [ ] `FRONTEND_INTEGRATION_COMPLETE.md` exists
- [ ] `INTEGRATION_QUICK_START.md` exists

### Read Documentation

- [ ] Complete docs are comprehensive
- [ ] Quick start has copy-paste examples
- [ ] All endpoints documented
- [ ] Troubleshooting section present

**Status:** ✅ PASS / ❌ FAIL

---

## 8. Performance - VERIFICATION

### Check Load Times

1. **Templates Page**
   - [ ] Open DevTools Network tab
   - [ ] Clear cache (Cmd+Shift+R)
   - [ ] Navigate to templates page
   - [ ] Check DOMContentLoaded time
   - [ ] Should be < 2 seconds

2. **API Response Times**
   - [ ] Check Network tab
   - [ ] GET /templates response time < 500ms
   - [ ] POST /templates response time < 500ms
   - [ ] PUT /templates response time < 500ms

3. **React Query Caching**
   - [ ] Navigate to templates page
   - [ ] Navigate away
   - [ ] Navigate back to templates
   - [ ] Check Network tab: No new API call (cached)

**Status:** ✅ PASS / ❌ FAIL

---

## 9. Error Handling - VERIFICATION

### Test Error Scenarios

1. **Network Error**
   - [ ] Stop backend server
   - [ ] Try to load templates
   - [ ] User-friendly error message shown
   - [ ] No app crash

2. **Validation Error**
   - [ ] Try to create template with empty name
   - [ ] Validation error shown
   - [ ] Form highlights error field

3. **404 Error**
   - [ ] Try to load non-existent template
   - [ ] 404 error handled gracefully
   - [ ] User redirected or shown error

4. **500 Error**
   - [ ] Trigger server error (if possible)
   - [ ] Error toast shown
   - [ ] No app crash

**Status:** ✅ PASS / ❌ FAIL

---

## 10. Console Verification - VERIFICATION

### Check Browser Console

- [ ] No errors in console
- [ ] No warnings in console
- [ ] No 404s in Network tab
- [ ] No CORS errors
- [ ] React Query DevTools working (if installed)

**Status:** ✅ PASS / ❌ FAIL

---

## Final Checklist

### Code Quality
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Code formatted consistently
- [ ] No console.log statements

### Functionality
- [ ] All CRUD operations work
- [ ] Loading states display
- [ ] Error handling works
- [ ] Mock data fallback works

### Performance
- [ ] Page loads < 2s
- [ ] API calls < 500ms
- [ ] Caching works
- [ ] No memory leaks

### Documentation
- [ ] README updated
- [ ] API docs complete
- [ ] Examples provided
- [ ] Troubleshooting guide included

### Testing
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Edge cases tested
- [ ] Error scenarios tested

---

## Sign-Off

**Tested By:** _________________
**Date:** _________________
**Overall Status:** ✅ PASS / ❌ FAIL

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

---

## If Tests Fail

### Troubleshooting Steps

1. **Check Backend**
   ```bash
   curl http://localhost:8000/docs
   ```

2. **Check Frontend**
   ```bash
   npm run dev
   ```

3. **Check Environment**
   ```bash
   cat .env
   ```

4. **Clear Cache**
   - Hard reload: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

5. **Check Logs**
   - Browser console
   - Backend terminal
   - Network tab

6. **Re-run Tests**
   ```javascript
   testIntegrations()
   ```

---

**Document Version:** 1.0
**Last Updated:** November 5, 2025
**Status:** Ready for QA
