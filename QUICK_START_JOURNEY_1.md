# Journey 1: Quick Start Guide

## What's Been Built

Complete UI for multi-source lead scraping with 4 data sources, real-time monitoring, and advanced lead management.

## Quick Access URLs

```
/scraper              → Main scraper with source selection
/scraper/jobs         → Active jobs monitoring
/scraper/jobs/:id     → Individual job details
/leads                → Enhanced leads table
```

## Key Components

### 1. SourceCard
Clickable cards for each data source (Craigslist, Google Maps, LinkedIn, Job Boards)

### 2. Wizards (3 total)
- **GoogleMapsWizard** - 3-step configuration for Google Maps scraping
- **LinkedInWizard** - 3-step with auth/CSV options
- **JobBoardsWizard** - 3-step multi-board selection

### 3. Pages
- **ScraperNew** - Source selection hub
- **ScrapeJobs** - Real-time job monitoring
- **ScrapeJobDetail** - Live job progress with activity log
- **LeadsEnhanced** - Filterable table with bulk actions
- **LeadDetailModal** - Full lead details in modal

## Features at a Glance

### Scraper Page
- 4 source cards with hover effects
- Wizard modals for configuration
- Active jobs preview (top 3)
- Getting started guide

### Jobs Monitoring
- Live progress updates (3s interval)
- Filter tabs (All/Active/Completed/Failed)
- Stats cards with counts
- Per-job progress bars
- Click-through to details

### Job Details
- Real-time progress tracking
- Activity log with live updates
- Pause/Resume/Cancel controls
- Configuration display
- Leads preview table

### Leads Page
- Source filtering tabs
- Search by title/company
- Bulk selection with actions
- Enrichment status badges
- Click-to-view modal

### Lead Detail Modal
- 3-tab interface (Overview/Activity/Assets)
- Complete contact information
- Clickable links (email, phone, website)
- Timeline of events
- Asset tracking

## Mock Data

### Leads
12 sample leads across all 4 sources with various statuses and enrichment states.

**Location:** `/frontend/src/mocks/leads.mock.ts`

### Jobs
6 sample scraping jobs in different states (running, completed, paused, failed, queued, cancelled).

**Location:** `/frontend/src/mocks/scrapeJobs.mock.ts`

## Real-Time Updates

All live components use `setInterval` to simulate WebSocket:
- **ScrapeJobs**: Updates every 3 seconds
- **ScrapeJobDetail**: Updates every 2 seconds
- Auto-increments progress, leads found, and activity logs

## Testing Checklist

- [ ] Navigate to `/scraper` and see 4 source cards
- [ ] Click each card and verify wizard opens
- [ ] Complete a wizard configuration
- [ ] Navigate to `/scraper/jobs` and see jobs list
- [ ] Watch progress bars animate in real-time
- [ ] Click a running job to view details
- [ ] Watch activity log update automatically
- [ ] Navigate to `/leads` and see all leads
- [ ] Click source filter tabs
- [ ] Search for a lead
- [ ] Select multiple leads via checkboxes
- [ ] Click a lead row to open modal
- [ ] Navigate through modal tabs

## Component Architecture

```
ScraperNew
  ├─ SourceCard (x4)
  ├─ GoogleMapsWizard
  ├─ LinkedInWizard
  ├─ JobBoardsWizard
  └─ ScrapeBuilder (existing)

ScrapeJobs
  └─ SourceBadge (existing)

ScrapeJobDetail
  └─ SourceBadge (existing)

LeadsEnhanced
  ├─ LeadDetailModal
  └─ SourceBadge (existing)
```

## Next Steps for API Integration

1. Replace mock imports with API calls:
```typescript
// Before
import { mockLeads } from '@/mocks/leads.mock'

// After
const { data: leads } = useQuery({
  queryKey: ['leads'],
  queryFn: () => api.get('/leads')
})
```

2. Replace setInterval with WebSocket:
```typescript
// Before
useEffect(() => {
  const interval = setInterval(updateProgress, 3000)
  return () => clearInterval(interval)
}, [])

// After
useEffect(() => {
  const ws = new WebSocket('ws://api.../jobs')
  ws.onmessage = (e) => updateProgress(JSON.parse(e.data))
  return () => ws.close()
}, [])
```

3. Wire up form submissions to backend:
```typescript
const handleSubmit = async (config) => {
  await api.post('/scraper/jobs', config)
}
```

## Styling

Uses existing dark theme:
- `card` - Container with border and padding
- `btn-primary` - Green accent button
- `btn-secondary` - Gray outlined button
- `form-input` - Text input styling
- `terminal-500` - Primary accent color

## File Locations

**New Components:**
- `/frontend/src/components/SourceCard.tsx`
- `/frontend/src/components/GoogleMapsWizard.tsx`
- `/frontend/src/components/LinkedInWizard.tsx`
- `/frontend/src/components/JobBoardsWizard.tsx`
- `/frontend/src/components/LeadDetailModal.tsx`

**New Pages:**
- `/frontend/src/pages/ScraperNew.tsx`
- `/frontend/src/pages/ScrapeJobs.tsx`
- `/frontend/src/pages/ScrapeJobDetail.tsx`
- `/frontend/src/pages/LeadsEnhanced.tsx`

**Updated:**
- `/frontend/src/App.tsx` (routes added)
- `/frontend/src/mocks/scrapeJobs.mock.ts` (helper function added)

## Design Patterns

### Wizard Pattern
All wizards follow same structure:
1. Step state management
2. Config object accumulation
3. Progress indicator (1-3 dots)
4. Back/Next/Submit buttons
5. Validation per step

### Real-Time Updates
All monitoring pages:
1. useState for data
2. useEffect with setInterval
3. Update function that transforms data
4. Cleanup function to clear interval

### Bulk Actions
Leads page pattern:
1. Set state for selected IDs
2. Conditional render of actions bar
3. Action handlers that operate on set
4. Clear selection after action

## Common Props

### SourceCard
```typescript
{
  icon: ReactNode
  title: string
  description: string
  color: string
  enabled?: boolean
  onClick: () => void
}
```

### Wizards
```typescript
{
  open: boolean
  onClose: () => void
  onSubmit: (config) => void
}
```

### LeadDetailModal
```typescript
{
  lead: MockLead | null
  open: boolean
  onClose: () => void
}
```

## Keyboard Shortcuts

- `Tab` - Navigate between elements
- `Enter` - Submit forms / Select items
- `Esc` - Close modals
- `Space` - Toggle checkboxes

## Responsive Design

All components are mobile-friendly:
- Grid layouts collapse on mobile
- Tables scroll horizontally
- Modals full-screen on small devices
- Touch-friendly tap targets (44px min)

## Performance Tips

- Leads table renders ~50 items by default
- Add virtual scrolling for 1000+ leads
- Debounce search input (300ms recommended)
- Memoize filter/sort functions
- Use React.memo for heavy components

## Support

For detailed documentation, see:
- `/JOURNEY_1_IMPLEMENTATION.md` - Full technical docs
- `/docs/USER_JOURNEYS.md` - Original specifications

---

**Status:** ✅ Journey 1 Complete - Ready for API Integration
