# Multi-Source UI Implementation Guide

## Overview

This document describes the comprehensive multi-source UI enhancements added to the lead generation platform. The implementation supports 6 lead sources: Craigslist, Google Maps, LinkedIn, Indeed, Monster, and ZipRecruiter.

## Files Created/Modified

### New Components

1. **`/frontend/src/components/SourceSelector.tsx`**
   - Dropdown component for selecting lead sources
   - Shows source icons, names, and enabled/disabled status
   - Supports filtering to only enabled sources
   - Uses Headless UI for accessible dropdown

2. **`/frontend/src/components/SourceBadge.tsx`**
   - Badge component for displaying source information
   - Supports small, medium, and large sizes
   - Color-coded by source with custom styling
   - Exports helper functions: `SourceIcon`, `SourceName`, `SourceColor`

### Updated Files

3. **`/frontend/src/types/lead.ts`**
   - Added `LeadSource` type union
   - Added `SourceMetadata` interface with source-specific fields:
     - Google Maps: rating, review_count, google_maps_url, business_category
     - LinkedIn: job_title, company_name, linkedin_url, company_size
     - Job Boards: salary, posted_date, job_url, salary_range
   - Added `source` and `source_metadata` fields to `Lead` interface

4. **`/frontend/src/index.css`**
   - Source badge styles for all 6 sources
   - Source filter dropdown styles
   - Source statistics bar chart styles with gradients
   - Color scheme:
     - Craigslist: #FF6600 (Orange)
     - Google Maps: #4285F4 (Blue)
     - LinkedIn: #0A66C2 (LinkedIn Blue)
     - Indeed: #2557A7 (Dark Blue)
     - Monster: #6E48AA (Purple)
     - ZipRecruiter: #1C8C3F (Green)

5. **`/frontend/src/components/ScrapeBuilder.tsx`**
   - Added source selector at the top
   - Dynamic form fields based on selected source:
     - **Craigslist**: Location + Category (existing)
     - **Google Maps**: Business Category + Location + Radius
     - **LinkedIn**: Job Keywords + Location + Company Size
     - **Job Boards**: Job Title + Location + Salary Range
   - Visual indicator for enabled/disabled sources
   - Validation prevents submission for disabled sources

6. **`/frontend/src/pages/Leads.tsx`**
   - Added source filter dropdown in filters section
   - Added source badge to each lead card
   - Source-specific metadata in expanded view:
     - Google Maps: Rating stars, review count, category, Maps link
     - LinkedIn: Job title, company name, company size, LinkedIn link
     - Job Boards: Salary, posted date, job listing link
   - Mobile-responsive layout

7. **`/frontend/src/pages/Dashboard.tsx`**
   - Added "Leads by Source" chart with progress bars
   - Color-coded bars using source-specific gradients
   - Shows count and response rate per source
   - Added "Best Performing Source" card:
     - Displays top source by response/conversion rate
     - Shows lead count and performance metrics
   - Handles empty states gracefully

8. **`/frontend/src/services/api.ts`**
   - Added `sourceApi` helper object with methods:
     - `getLeadsBySource(source)`: Filter leads by source
     - `getSourceStats()`: Get statistics by source
     - `getBestPerformingSource()`: Get top performing source
     - `createScrapeJob(data)`: Create job with source-specific params
     - `getEnabledSources()`: Get list of enabled sources

## Source Configuration

### Source Configs (in `SourceSelector.tsx`)

```typescript
const SOURCE_CONFIGS: SourceConfig[] = [
  { id: 'craigslist', name: 'Craigslist', icon: '📍', color: '#FF6600', enabled: true },
  { id: 'google_maps', name: 'Google Maps', icon: '🗺️', color: '#4285F4', enabled: false },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: '#0A66C2', enabled: false },
  { id: 'indeed', name: 'Indeed', icon: '🔍', color: '#2557A7', enabled: false },
  { id: 'monster', name: 'Monster', icon: '👹', color: '#6E48AA', enabled: false },
  { id: 'ziprecruiter', name: 'ZipRecruiter', icon: '⚡', color: '#1C8C3F', enabled: false },
]
```

Only Craigslist is enabled by default. Other sources will be enabled in Phase 2.

## Usage Examples

### Using SourceSelector

```tsx
import SourceSelector from '@/components/SourceSelector'

<SourceSelector
  value={source}
  onChange={setSource}
  enabledSources={['craigslist', 'google_maps']}
/>
```

### Using SourceBadge

```tsx
import SourceBadge from '@/components/SourceBadge'

<SourceBadge
  source="craigslist"
  size="sm"
  showIcon={true}
  showName={true}
/>
```

### Filtering Leads by Source

```tsx
const [filters, setFilters] = useState({
  source: '' as LeadSource | '',
  // ... other filters
})

<select
  value={filters.source}
  onChange={(e) => setFilters(prev => ({
    ...prev,
    source: e.target.value as LeadSource | ''
  }))}
>
  <option value="">All Sources</option>
  <option value="craigslist">Craigslist</option>
  <option value="google_maps">Google Maps</option>
  {/* ... */}
</select>
```

### Creating Source-Specific Scrape Job

```tsx
const payload = {
  source: 'google_maps',
  location_ids: [1, 2, 3],
  business_category: 'restaurants',
  radius: 10,
  max_pages: 5,
  priority: 'normal',
  enable_email_extraction: true
}

sourceApi.createScrapeJob(payload)
```

## Mobile Responsiveness

All components are mobile-responsive:

- Source selector: Full-width dropdown on mobile
- Source badges: Wrap properly on small screens
- Filter grid: Stacks vertically on mobile (1 column)
- Charts: Responsive width with horizontal scrolling if needed
- Dashboard cards: Stack vertically on mobile

## Backend Requirements

The backend needs to support the following endpoints:

### Required Endpoints

1. **GET `/api/v1/leads?source={source}`**
   - Filter leads by source
   - Returns array of leads

2. **GET `/api/v1/leads/stats/by-source`**
   - Returns statistics grouped by source
   - Example response:
   ```json
   {
     "craigslist": {
       "count": 450,
       "response_rate": 0.35,
       "conversion_rate": 0.12
     },
     "google_maps": {
       "count": 320,
       "response_rate": 0.45,
       "conversion_rate": 0.18
     }
   }
   ```

3. **GET `/api/v1/leads/stats/best-source`**
   - Returns the best performing source
   - Example response:
   ```json
   {
     "source": "google_maps",
     "count": 320,
     "response_rate": 0.45,
     "conversion_rate": 0.18
   }
   ```

4. **POST `/api/v1/scraper/jobs`**
   - Accept `source` field in request body
   - Accept source-specific fields (business_category, radius, company_size, salary_range)

5. **GET `/api/v1/config/enabled-sources`**
   - Returns array of enabled source IDs
   - Example response:
   ```json
   {
     "enabled_sources": ["craigslist", "google_maps"]
   }
   ```

### Database Schema Updates

The `leads` table needs:

```sql
ALTER TABLE leads ADD COLUMN source VARCHAR(50) DEFAULT 'craigslist';
ALTER TABLE leads ADD COLUMN source_metadata JSONB;
```

## Testing Checklist

- [ ] Source selector shows all 6 sources
- [ ] Only enabled sources are selectable
- [ ] Source badges display correctly with proper colors
- [ ] Lead filtering by source works
- [ ] Source-specific metadata displays in expanded view
- [ ] Dashboard charts show source statistics
- [ ] Best performing source card displays correctly
- [ ] Mobile layout works on all screen sizes
- [ ] Form validation prevents submitting disabled sources
- [ ] Source-specific form fields appear/disappear correctly

## Future Enhancements (Phase 2)

1. Enable additional sources (Google Maps, LinkedIn, etc.)
2. Add source-specific scrapers
3. Implement email discovery for non-Craigslist sources
4. Add source comparison analytics
5. Source-specific AI analysis prompts
6. Bulk operations by source
7. Source performance optimization recommendations

## Accessibility

- All dropdowns use Headless UI for keyboard navigation
- Color is not the only indicator (icons + text labels)
- Proper ARIA labels on all interactive elements
- Sufficient color contrast for all source colors
- Focus states visible on all interactive elements

## Performance Considerations

- Source configs are static and memoized
- Dashboard charts use CSS animations for smooth transitions
- Source badges are lightweight components
- API calls are cached with React Query
- Filtering happens on backend, not frontend

## Color Palette Reference

| Source | Hex Color | RGB | Usage |
|--------|-----------|-----|-------|
| Craigslist | #FF6600 | rgb(255, 102, 0) | Badges, charts, text |
| Google Maps | #4285F4 | rgb(66, 133, 244) | Badges, charts, text |
| LinkedIn | #0A66C2 | rgb(10, 102, 194) | Badges, charts, text |
| Indeed | #2557A7 | rgb(37, 87, 167) | Badges, charts, text |
| Monster | #6E48AA | rgb(110, 72, 170) | Badges, charts, text |
| ZipRecruiter | #1C8C3F | rgb(28, 140, 63) | Badges, charts, text |

All colors have 0.1 opacity for backgrounds and 0.3 for borders.
