# Frontend Integration Quick Start

Fast reference for connecting frontend pages to backend API.

---

## Quick Setup

### 1. Environment Variables

```bash
# .env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_USE_MOCK_DATA=false  # false = live API, true = mock data
```

### 2. Restart Dev Server

```bash
npm run dev
```

---

## Integration Pattern

### Step 1: Add React Query Hooks

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
```

### Step 2: Add Environment Flag

```typescript
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'
```

### Step 3: Fetch Data

```typescript
const { data: items = [], isLoading } = useQuery({
  queryKey: ['items'],
  queryFn: async () => {
    if (USE_MOCK_DATA) return mockItems
    const res = await api.get('/items')
    return res.data
  },
})
```

### Step 4: Add Mutations

```typescript
const queryClient = useQueryClient()

// Create
const createMutation = useMutation({
  mutationFn: (data) => api.post('/items', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['items'] })
    toast.success('Created!')
  },
})

// Update
const updateMutation = useMutation({
  mutationFn: ({ id, data }) => api.put(`/items/${id}`, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['items'] })
    toast.success('Updated!')
  },
})

// Delete
const deleteMutation = useMutation({
  mutationFn: (id) => api.delete(`/items/${id}`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['items'] })
    toast.success('Deleted!')
  },
})
```

### Step 5: Add Loading State

```typescript
if (isLoading) {
  return <div>Loading...</div>
}
```

---

## API Services

### Templates API

```typescript
import { api } from '@/services/api'

// GET all templates
const templates = await api.get('/templates')

// GET template by ID
const template = await api.get('/templates/1')

// POST create template
const newTemplate = await api.post('/templates', {
  name: 'My Template',
  subject_template: 'Hello {{name}}',
  body_template: '<p>Email body</p>',
  variables: { name: 'Recipient name' },
})

// PUT update template
const updated = await api.put('/templates/1', {
  subject_template: 'Updated subject',
})

// DELETE template
await api.delete('/templates/1')
```

### Email Tracking API

```typescript
import { emailTrackingApi } from '@/services/emailTrackingApi'

// Create tracking URL
const url = emailTrackingApi.createTrackingUrl('token', 'https://example.com')

// Get campaign tracking stats
const stats = await emailTrackingApi.getCampaignTracking('campaign-id')

// Get email tracking details
const tracking = await emailTrackingApi.getEmailTracking('email-id')
```

### Workflows API

```typescript
import { workflowsApi } from '@/services/workflowsApi'

// Get workflows
const workflows = await workflowsApi.getWorkflows()

// Get workflow stats
const stats = await workflowsApi.getStats()

// Get pending approvals
const approvals = await workflowsApi.getPendingApprovals()

// Approve request
await workflowsApi.approveRequest(id, 'Looks good!')

// Reject request
await workflowsApi.rejectRequest(id, 'Needs changes')
```

### Demo Sites API

```typescript
import { demoSitesApi } from '@/services/demoSitesApi'

// Get all demo sites
const sites = await demoSitesApi.getDemoSites()

// Get site by ID
const site = await demoSitesApi.getDemoSite('site-id')

// Create demo site
const newSite = await demoSitesApi.createDemoSite({
  lead_id: 123,
  site_name: 'Example Business',
  template_name: 'modern-business',
})
```

---

## Type Definitions

### EmailTemplate

```typescript
interface EmailTemplate {
  id: number
  name: string
  subject_template: string      // Use this (not 'subject')
  body_template: string          // Use this (not 'body_html')
  variables: Record<string, any> // Use this (not 'string[]')
  created_at: string
  updated_at: string
}
```

### Create/Update Types

```typescript
interface EmailTemplateCreate {
  name: string
  subject_template: string
  body_template: string
  variables?: Record<string, any>
}

interface EmailTemplateUpdate {
  name?: string
  subject_template?: string
  body_template?: string
  variables?: Record<string, any>
}
```

---

## Testing

### Run All Tests

```javascript
// In browser console
testIntegrations()
```

### Run Individual Tests

```javascript
testTemplatesAPI()
testWorkflowsAPI()
testEmailTrackingAPI()
testDemoSitesAPI()
```

### Expected Output

```
🧪 Frontend API Integration Tests
Testing connection to backend API...

📧 Templates API
  ✅ GET /templates - 45ms
  ✅ GET /templates/{id} - 23ms

📊 Email Tracking API
  ✅ Email Tracking - Create URL - 1ms

🔄 Workflows API
  ✅ GET /n8n-webhooks/workflows - 67ms
  ✅ GET /n8n-webhooks/stats - 34ms
  ✅ GET /approvals/pending - 28ms

🌐 Demo Sites API
  ✅ GET /demo-sites - 52ms

📊 Test Summary
Total Tests: 7
✅ Passed: 7
❌ Failed: 0
⏱️ Average Duration: 35ms
```

---

## Common Issues

### Backend Not Running

```bash
# Check if backend is running
curl http://localhost:8000/docs

# Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### CORS Errors

Add to `backend/app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Type Errors

```bash
# Check types
npm run type-check

# Update types
npm install --save-dev @types/node @types/react
```

### Mock Data Not Loading

```bash
# 1. Update .env
VITE_USE_MOCK_DATA=true

# 2. Restart dev server
npm run dev

# 3. Clear browser cache
# Hard reload: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
```

---

## Best Practices

### 1. Always Use React Query

✅ Good:
```typescript
const { data } = useQuery({
  queryKey: ['items'],
  queryFn: () => api.get('/items'),
})
```

❌ Bad:
```typescript
const [data, setData] = useState([])
useEffect(() => {
  api.get('/items').then(res => setData(res.data))
}, [])
```

### 2. Handle Loading States

✅ Good:
```typescript
if (isLoading) return <LoadingSkeleton />
if (error) return <ErrorMessage />
return <DataDisplay data={data} />
```

❌ Bad:
```typescript
return <DataDisplay data={data || []} />
```

### 3. Use Mutations for Write Operations

✅ Good:
```typescript
const mutation = useMutation({
  mutationFn: (data) => api.post('/items', data),
  onSuccess: () => queryClient.invalidateQueries(['items']),
})
```

❌ Bad:
```typescript
const handleSubmit = async () => {
  await api.post('/items', data)
  fetchItems() // Manual refetch
}
```

### 4. Provide User Feedback

✅ Good:
```typescript
onSuccess: () => {
  toast.success('Saved!')
  setIsEditing(false)
},
onError: (error) => {
  toast.error(error.message)
}
```

❌ Bad:
```typescript
onSuccess: () => {
  // Silent success
}
```

---

## Files Reference

### API Services
- `/frontend/src/services/api.ts` - Base API client
- `/frontend/src/services/emailTrackingApi.ts` - Email tracking
- `/frontend/src/services/workflowsApi.ts` - Workflows & approvals
- `/frontend/src/services/demoSitesApi.ts` - Demo sites

### Type Definitions
- `/frontend/src/types/campaign.ts` - Templates & campaigns
- `/frontend/src/types/workflow.ts` - Workflows & approvals
- `/frontend/src/types/demoSite.ts` - Demo sites

### Examples
- `/frontend/src/pages/Templates.tsx` - Full integration example
- `/frontend/src/test-integrations.ts` - Test utility

### Configuration
- `/frontend/.env` - Environment variables
- `/frontend/.env.development` - Development config
- `/frontend/.env.example` - Config template

---

## Quick Commands

```bash
# Start frontend
npm run dev

# Start backend
cd backend && uvicorn app.main:app --reload

# Run tests (in browser console)
testIntegrations()

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## Getting Help

1. Check browser console for errors
2. Check Network tab for failed requests
3. Run integration tests: `testIntegrations()`
4. Check backend logs
5. Review API docs: `http://localhost:8000/docs`

---

**Last Updated:** November 5, 2025
**Status:** Production Ready
