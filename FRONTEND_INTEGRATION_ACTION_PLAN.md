# Frontend Integration Action Plan

**Priority:** High
**Estimated Time:** 5 hours
**Goal:** Connect all 4 features to live backend APIs

---

## Quick Wins (30 minutes)

### 1. Fix Template Type Alignment (15 min)

**File:** `/frontend/src/types/campaign.ts`

**Current:**
```typescript
interface EmailTemplate {
  id: number
  name: string
  subject: string
  body_html: string
  variables: string[]
}
```

**Fix to:**
```typescript
interface EmailTemplate {
  id: number
  name: string
  description?: string
  category?: string
  subject_template: string
  body_template: string
  body_text?: string
  variables: Record<string, any>
  use_ai_enhancement?: boolean
  ai_tone?: string
  ai_length?: string
  is_active: boolean
  sent_count: number
  response_count: number
  response_rate: number
  conversion_rate: number
  created_at: string
  updated_at: string
}
```

### 2. Add Environment Flag (15 min)

**File:** `/frontend/.env.development`

```bash
# Add this line
VITE_USE_MOCK_DATA=false
VITE_API_URL=http://localhost:8000
```

**Update all pages to check:**
```typescript
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

const { data: templates } = useQuery({
  queryKey: ['templates'],
  queryFn: async () => {
    if (USE_MOCK_DATA) {
      return mockTemplates
    }
    return api.get('/templates').then(res => res.data)
  }
})
```

---

## Critical Fixes (3 hours)

### 3. Create Email Tracking API Service (1 hour)

**Create file:** `/frontend/src/services/emailTrackingApi.ts`

```typescript
import { api } from './api'

export const emailTrackingApi = {
  /**
   * Track email open event
   * Note: This is typically called automatically by email client
   * when loading the tracking pixel
   */
  trackOpen: (trackingToken: string) =>
    api.get(`/email-tracking/open/${trackingToken}`),

  /**
   * Track email click event
   * This creates a redirect URL for tracking
   */
  createTrackingUrl: (trackingToken: string, originalUrl: string) => {
    const encodedUrl = encodeURIComponent(originalUrl)
    return `${api.defaults.baseURL}/email-tracking/click/${trackingToken}?url=${encodedUrl}`
  },

  /**
   * Get email tracking stats for a campaign
   */
  getCampaignTracking: (campaignId: string) =>
    api.get(`/campaigns/${campaignId}/tracking`),

  /**
   * Get email tracking stats for a specific email
   */
  getEmailTracking: (emailId: string) =>
    api.get(`/campaigns/emails/${emailId}/tracking`),

  /**
   * Mark email as unsubscribed
   */
  unsubscribe: (trackingToken: string) =>
    api.get(`/email-tracking/unsubscribe/${trackingToken}`)
}
```

**Update Campaigns page:**
```typescript
import { emailTrackingApi } from '@/services/emailTrackingApi'

// Use in campaign detail view
const { data: trackingStats } = useQuery({
  queryKey: ['campaign-tracking', campaignId],
  queryFn: () => emailTrackingApi.getCampaignTracking(campaignId)
})
```

### 4. Connect Templates to Backend API (1.5 hours)

**File:** `/frontend/src/pages/Templates.tsx`

**Replace mock data:**
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import toast from 'react-hot-toast'

export default function Templates() {
  const queryClient = useQueryClient()

  // Fetch templates from backend
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.get('/templates').then(res => res.data)
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: (data: EmailTemplateCreate) =>
      api.post('/templates', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template created successfully!')
    }
  })

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: EmailTemplateUpdate }) =>
      api.put(`/templates/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template updated successfully!')
    }
  })

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template deleted successfully!')
    }
  })

  // Handle save (create or update)
  const handleSave = () => {
    const data = {
      name: formData.name,
      subject_template: formData.subject,
      body_template: formData.body_html,
      body_text: formData.body_text,
      category: formData.category,
      variables: formData.tags.reduce((acc, tag) => {
        acc[tag] = tag
        return acc
      }, {} as Record<string, string>)
    }

    if (isEditing && selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate, data })
    } else {
      createMutation.mutate(data)
    }
  }

  // Handle delete
  const handleDelete = (templateId: number) => {
    if (confirm('Are you sure you want to delete this template?')) {
      deleteMutation.mutate(templateId)
    }
  }

  // Rest of component...
}
```

### 5. Test All API Integrations (30 min)

**Create test file:** `/frontend/src/test-integrations.ts`

```typescript
import { api } from './services/api'
import { demoSitesApi } from './services/demoSitesApi'
import { workflowsApi } from './services/workflowsApi'
import { emailTrackingApi } from './services/emailTrackingApi'

async function testIntegrations() {
  console.group('🧪 Testing API Integrations')

  try {
    // Test Templates
    console.log('Testing Templates API...')
    const templates = await api.get('/templates')
    console.log('✅ Templates:', templates.data.length, 'templates found')

    // Test Email Tracking
    console.log('Testing Email Tracking API...')
    const trackingUrl = emailTrackingApi.createTrackingUrl('test-token', 'https://example.com')
    console.log('✅ Email Tracking:', trackingUrl)

    // Test Demo Sites
    console.log('Testing Demo Sites API...')
    const demoSites = await demoSitesApi.getDemoSites()
    console.log('✅ Demo Sites:', demoSites.data.length, 'sites found')

    // Test Workflows
    console.log('Testing Workflows API...')
    const workflows = await workflowsApi.getWorkflows()
    console.log('✅ Workflows:', workflows.data.length, 'workflows found')

    // Test Approvals
    console.log('Testing Approvals API...')
    const approvals = await workflowsApi.getPendingApprovals()
    console.log('✅ Approvals:', approvals.data.length, 'pending approvals')

    console.log('\n🎉 All API integrations working!')
  } catch (error) {
    console.error('❌ Integration test failed:', error)
  }

  console.groupEnd()
}

// Run in browser console: testIntegrations()
export { testIntegrations }
```

---

## Enhancement Phase (1 hour)

### 6. Add Better Loading States

**Create component:** `/frontend/src/components/LoadingStates.tsx`

```typescript
export function TemplatesSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="card p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
      ))}
    </div>
  )
}

export function CampaignsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="card p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-8 bg-gray-200 rounded mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      ))}
    </div>
  )
}
```

### 7. Add Error Boundaries

**Create component:** `/frontend/src/components/ErrorBoundary.tsx`

```typescript
import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error boundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="card p-12 text-center">
          <h2 className="text-xl font-bold text-red-600 mb-2">
            Something went wrong
          </h2>
          <p className="text-gray-600 mb-4">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Reload Page
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
```

**Wrap pages:**
```typescript
// In App.tsx
import { ErrorBoundary } from '@/components/ErrorBoundary'

<Route
  path="/templates"
  element={
    <ErrorBoundary>
      <Templates />
    </ErrorBoundary>
  }
/>
```

### 8. Add Notification Badges

**Update Layout.tsx:**
```typescript
import { useQuery } from '@tanstack/react-query'
import { workflowsApi } from '@/services/workflowsApi'

export default function Layout({ children }: LayoutProps) {
  // Fetch pending approvals count
  const { data: approvals } = useQuery({
    queryKey: ['pending-approvals-count'],
    queryFn: () => workflowsApi.getPendingApprovals(),
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  const pendingCount = approvals?.data?.length || 0

  // Update navigation
  const navigation: NavSection[] = [
    {
      title: 'Automation',
      items: [
        { name: 'Campaigns', href: '/campaigns', icon: MailIcon },
        { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
        { name: 'Workflows', href: '/workflows', icon: Cog6ToothIcon },
        {
          name: 'Approvals',
          href: '/approvals',
          icon: BellIcon,
          badge: pendingCount // Add badge count
        },
      ]
    }
  ]

  // Rest of component...
}
```

---

## Checklist

### Before Starting
- [ ] Backend is running on `http://localhost:8000`
- [ ] Frontend is running on `http://localhost:5173`
- [ ] Database is migrated and populated
- [ ] Redis is running (optional but recommended)

### Quick Wins
- [ ] Fix EmailTemplate type definition
- [ ] Add environment flag for mock data
- [ ] Update .env.development file

### Critical Fixes
- [ ] Create emailTrackingApi.ts service
- [ ] Update Templates.tsx to use backend API
- [ ] Update Campaigns.tsx to use tracking API
- [ ] Test all API integrations

### Enhancements
- [ ] Add loading skeletons
- [ ] Add error boundaries
- [ ] Add notification badges
- [ ] Add breadcrumb navigation

### Testing
- [ ] Templates: Create new template
- [ ] Templates: Edit existing template
- [ ] Templates: Delete template
- [ ] Templates: Preview template
- [ ] Email Tracking: View campaign stats
- [ ] Email Tracking: View email status
- [ ] Demo Sites: Create new demo site
- [ ] Demo Sites: View site details
- [ ] Workflows: View workflow list
- [ ] Workflows: View execution details
- [ ] Approvals: Approve/reject requests

---

## File Changes Summary

### New Files
1. `/frontend/src/services/emailTrackingApi.ts` (NEW)
2. `/frontend/src/components/LoadingStates.tsx` (NEW)
3. `/frontend/src/components/ErrorBoundary.tsx` (NEW)
4. `/frontend/src/test-integrations.ts` (NEW)

### Modified Files
1. `/frontend/src/types/campaign.ts` (Update EmailTemplate)
2. `/frontend/src/pages/Templates.tsx` (Connect to API)
3. `/frontend/src/pages/Campaigns.tsx` (Add tracking integration)
4. `/frontend/src/components/Layout.tsx` (Add notification badges)
5. `/frontend/.env.development` (Add VITE_USE_MOCK_DATA)
6. `/frontend/src/App.tsx` (Add error boundaries)

---

## Risk Assessment

### Low Risk
- ✅ Demo Sites - Already has complete API service
- ✅ Workflows - Already has complete API service
- ✅ Environment flags - Non-breaking change

### Medium Risk
- ⚠️ Templates - Type changes may break existing code
- ⚠️ Email Tracking - New service, needs testing

### Mitigation Strategy
1. Keep mock data as fallback
2. Add error boundaries around new integrations
3. Test each feature individually before deploying
4. Add feature flags for easy rollback

---

## Success Criteria

- [ ] All 4 features connect to live backend APIs
- [ ] No console errors in browser
- [ ] Loading states work correctly
- [ ] Error states display properly
- [ ] Type safety maintained (no TypeScript errors)
- [ ] Performance acceptable (< 2s load time)
- [ ] Mock data still works as fallback

---

## Timeline

**Day 1 (2 hours):**
- Morning: Quick Wins (30 min)
- Morning: Email Tracking Service (1 hour)
- Afternoon: Template API Integration (30 min)

**Day 2 (3 hours):**
- Morning: Testing & Bug Fixes (1 hour)
- Afternoon: Enhancements (1 hour)
- Evening: Final Testing & Documentation (1 hour)

**Total: 5 hours** over 2 days (half-days)

---

## Support & Resources

### Documentation
- Backend API docs: `http://localhost:8000/docs`
- Frontend types: `/frontend/src/types/`
- Backend endpoints: `/backend/app/api/endpoints/`

### Testing Tools
- React Query Devtools (already installed)
- Browser Network tab
- Postman/Insomnia for API testing

### Rollback Plan
If issues occur:
1. Set `VITE_USE_MOCK_DATA=true`
2. Restart frontend dev server
3. Mock data will be used instead of API
4. Debug and fix issues

---

**Created:** November 5, 2025
**Status:** Ready to Execute
**Confidence:** High
