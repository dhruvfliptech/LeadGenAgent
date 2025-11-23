# Journey 7: Testing Checklist

## Quick Start Testing

### Prerequisites
```bash
cd /Users/greenmachine2.0/Craigslist/frontend
npm run dev
```

Visit: http://localhost:5173

## Test Routes

### 1. Approvals Queue (`/approvals-new`)
- [ ] Page loads without errors
- [ ] 4 stats cards display correctly
- [ ] Filters work (Status, Risk Level, Type)
- [ ] Approval cards render in grid layout
- [ ] Cards show risk indicators
- [ ] Critical/High priority items appear first
- [ ] Clicking card navigates to detail page
- [ ] "Approval Rules" button links correctly

**Expected Result:**
- 3 pending approvals visible by default
- High risk items at top
- Expiring approvals show warning

### 2. Approval Detail (`/approvals/appr_abc123`)
- [ ] Page loads with approval details
- [ ] Risk indicator displays with score
- [ ] Risk assessment panel shows score bar
- [ ] Risk factors list displays
- [ ] Preview panel shows email content
- [ ] Context information renders
- [ ] Approve button works (shows toast)
- [ ] Reject button shows form
- [ ] Rejection reason textarea appears
- [ ] Back to Approvals link works

**Test Cases:**
- Critical approval: `/approvals/appr_def456`
- Approved approval: `/approvals/appr_ghi789`
- Rejected approval: `/approvals/appr_jkl012`

### 3. Approval Rules (`/approvals/rules`)
- [ ] Page loads with rules table
- [ ] 4 rules display
- [ ] Enable/Disable toggle works (shows toast)
- [ ] Test button shows toast
- [ ] Edit button opens modal
- [ ] Create Rule button opens modal
- [ ] Modal has all form fields
- [ ] Cancel button closes modal
- [ ] Save button closes modal (shows toast)
- [ ] Back to Approvals link works

**Expected Result:**
- 4 rules in table
- Toggle changes status
- Modal opens and closes smoothly

### 4. Workflows Dashboard (`/workflows-new`)
- [ ] Page loads without errors
- [ ] 4 stats cards display
- [ ] Tab filters work (All, Active, Inactive, Error)
- [ ] Workflow cards render
- [ ] Cards show correct status badges
- [ ] Success rate calculates correctly
- [ ] Last execution status displays
- [ ] Clicking card navigates to detail
- [ ] "Webhook Queue" button links correctly
- [ ] "New Workflow" button present

**Expected Result:**
- 5 workflows total
- 4 active workflows
- 1 error workflow (Slack Notifications)
- Success rates displayed

### 5. Workflow Detail (`/workflows/wf_enrich_abc123`)
- [ ] Page loads with workflow details
- [ ] Status badge displays correctly
- [ ] 4 stats cards render
- [ ] Test button works (shows toast)
- [ ] Enable/Disable toggle works (shows toast)
- [ ] Trigger configuration panel displays
- [ ] Workflow diagram renders nodes
- [ ] Nodes show connections
- [ ] Execution history table displays
- [ ] Clicking "View Details" expands execution
- [ ] Execution data (input/output) displays
- [ ] "Show Logs" button toggles logs viewer
- [ ] Logs display in terminal style
- [ ] Back to Workflows link works

**Test Cases:**
- Lead enrichment: `/workflows/wf_enrich_abc123`
- Email response: `/workflows/wf_email_def456`
- Error workflow: `/workflows/wf_slack_mno345`

### 6. Webhooks Queue (`/webhooks`)
- [ ] Page loads without errors
- [ ] 5 stats cards display
- [ ] Status filter works
- [ ] Event type filter works
- [ ] Webhooks table renders
- [ ] Status icons display correctly
- [ ] Attempts show correctly
- [ ] Response times display
- [ ] Clicking "View" expands row
- [ ] Expanded row shows details
- [ ] Payload displays as JSON
- [ ] Delivery attempts show
- [ ] Attempt cards have status indicators
- [ ] Event type stats grid displays
- [ ] Performance stats show
- [ ] Back to Workflows link works

**Expected Result:**
- 8 webhooks in queue
- 5 delivered successfully
- 1 failed, 1 retrying
- Success rate: 62.5%

## Visual Regression Tests

### Component Rendering
- [ ] RiskIndicator - all levels (low, medium, high, critical)
- [ ] ApprovalCard - with and without expiration
- [ ] WorkflowCard - all statuses (active, inactive, error)
- [ ] WorkflowDiagram - multiple node layouts

### Responsive Design
- [ ] Mobile (375px): Cards stack vertically
- [ ] Tablet (768px): 2-column grid
- [ ] Desktop (1024px+): Full layout

### Color Coding
- [ ] Green for success/low risk/active
- [ ] Yellow for medium risk/retrying
- [ ] Orange for high risk
- [ ] Red for critical/failed/error
- [ ] Blue for pending/sending

## Interaction Tests

### Filtering
- [ ] Status filters update results
- [ ] Risk level filters work
- [ ] Type filters work
- [ ] Event type filters work
- [ ] Filter combinations work
- [ ] Count updates correctly

### Navigation
- [ ] All internal links work
- [ ] Back buttons navigate correctly
- [ ] Workflow links open detail pages
- [ ] Lead links go to leads page

### Actions
- [ ] Approve button shows success toast
- [ ] Reject button shows form
- [ ] Enable/Disable toggles work
- [ ] Test workflow shows toast
- [ ] Rule toggle updates state
- [ ] Modal open/close works

## Mock Data Verification

### Approvals
```typescript
// Check these approval IDs exist:
- appr_abc123 (High risk email)
- appr_def456 (Critical urgent)
- appr_ghi789 (Approved demo site)
- appr_jkl012 (Rejected campaign)
```

### Workflows
```typescript
// Check these workflow IDs exist:
- wf_enrich_abc123 (Lead Enrichment)
- wf_email_def456 (AI Email Response)
- wf_score_ghi789 (Daily Lead Scoring)
- wf_demo_jkl012 (Demo Site Generation)
- wf_slack_mno345 (Slack Notifications - Error)
```

### Webhooks
```typescript
// Check these webhook IDs exist:
- wh_abc123 (Delivered)
- wh_def456 (Sending)
- wh_ghi789 (Retrying)
- wh_jkl012 (Failed)
```

## Performance Tests

### Load Time
- [ ] Page loads in < 2 seconds
- [ ] Images load progressively
- [ ] No layout shift on load

### Interactions
- [ ] Filter updates are instant
- [ ] Modal opens smoothly
- [ ] Tables scroll smoothly
- [ ] Expandable rows animate

## Accessibility Tests

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Enter/Space activate buttons
- [ ] Escape closes modals
- [ ] Arrow keys navigate tables

### Screen Reader
- [ ] Status indicators have aria-labels
- [ ] Tables have proper headers
- [ ] Forms have labels
- [ ] Links have descriptive text

### Color Contrast
- [ ] All text meets WCAG AA
- [ ] Status badges readable
- [ ] Links distinguishable
- [ ] Focus indicators visible

## Browser Testing

### Recommended Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Error Handling

### Missing Data
- [ ] Invalid approval ID shows "not found"
- [ ] Invalid workflow ID shows "not found"
- [ ] Empty states show helpful messages
- [ ] Filters with no results show empty state

### Edge Cases
- [ ] Very long approval titles truncate
- [ ] Large JSON payloads scroll
- [ ] Many risk factors show "+N more"
- [ ] Long webhook URLs break properly

## Final Checklist

- [ ] No console errors
- [ ] No TypeScript errors
- [ ] All routes accessible
- [ ] All buttons functional
- [ ] All links working
- [ ] All filters working
- [ ] All modals working
- [ ] All toasts showing
- [ ] Mobile responsive
- [ ] Keyboard accessible
- [ ] Screen reader friendly

## Known Limitations

1. Mock data only (no API integration yet)
2. Actions show toasts but don't persist
3. Real-time updates not implemented
4. No authentication/authorization

## Next Steps for Production

1. Replace mock data with API calls
2. Add real-time WebSocket updates
3. Implement approval action persistence
4. Add authentication/authorization
5. Implement workflow editor
6. Add webhook retry button
7. Export functionality
8. Advanced filtering options
