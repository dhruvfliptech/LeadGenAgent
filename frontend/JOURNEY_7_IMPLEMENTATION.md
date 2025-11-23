# Journey 7: Approval Workflows & n8n Integration - Implementation Guide

## Overview
Complete UI implementation for the Approval Workflows and n8n Integration journey. This includes approval queue management, workflow monitoring, and webhook delivery tracking.

## Routes

### Approvals
- `/approvals-new` - Enhanced approval queue with filters and stats
- `/approvals/:id` - Detailed approval view with risk assessment and preview
- `/approvals/rules` - Approval rules configuration page
- `/approvals` - Original approval page (legacy)

### Workflows
- `/workflows-new` - Enhanced workflow dashboard with status filters
- `/workflows/:id` - Workflow detail page with visual diagram and execution history
- `/workflows` - Original workflow dashboard (legacy)

### Webhooks
- `/webhooks` - Webhook queue monitoring with delivery tracking

## Components

### Approval Components (`/src/components/approvals/`)
1. **RiskIndicator.tsx**
   - Visual risk level badge (low, medium, high, critical)
   - Color-coded with risk score display
   - Configurable size (sm, md, lg)

2. **ApprovalCard.tsx**
   - Compact approval display for queue view
   - Risk factors preview
   - Expiration warnings
   - Click to view detail

### Workflow Components (`/src/components/workflows/`)
1. **WorkflowCard.tsx**
   - Workflow summary card with status
   - Execution stats (total, success rate, avg time)
   - Last execution status indicator
   - Trigger type badge

2. **WorkflowDiagram.tsx**
   - Visual workflow node representation
   - Color-coded nodes by type
   - Connection flow display
   - Node parameter preview

## Pages

### Approvals
1. **ApprovalsEnhanced.tsx** (`/approvals-new`)
   - Stats cards: Pending, Approved Today, Rejected, Expired
   - Filters: Status, Risk Level, Type
   - Approval cards grid (sorted by priority)
   - Link to approval rules

2. **ApprovalDetail.tsx** (`/approvals/:id`)
   - Full approval details
   - Risk assessment panel with score bar
   - Preview panel (email content, action details)
   - Approve/Reject actions with reason
   - Context and related entities
   - Review history timeline

3. **ApprovalRules.tsx** (`/approvals/rules`)
   - Rules table with enable/disable toggle
   - Rule editor modal
   - Test rule functionality
   - Condition builder UI

### Workflows
1. **WorkflowsEnhanced.tsx** (`/workflows-new`)
   - Stats cards: Total, Active, Success Rate, Total Executions
   - Status filter tabs (All, Active, Inactive, Error)
   - Workflow cards grid
   - Link to webhook queue

2. **WorkflowDetail.tsx** (`/workflows/:id`)
   - Workflow info and status
   - Execution stats
   - Trigger configuration panel
   - Visual workflow diagram
   - Execution history table
   - Execution detail viewer
   - Logs viewer
   - Enable/Disable toggle
   - Test workflow button

### Webhooks
1. **Webhooks.tsx** (`/webhooks`)
   - Stats cards: Queued, Sending, Delivered, Failed, Success Rate
   - Filters: Status, Event Type
   - Webhooks table with expandable rows
   - Delivery attempt logs
   - Payload preview
   - Event type stats
   - Performance metrics

## Mock Data
All pages use mock data from:
- `/src/mocks/approvals.mock.ts` - Approval requests and rules
- `/src/mocks/workflows.mock.ts` - n8n workflows and executions
- `/src/mocks/webhooks.mock.ts` - Webhook queue and delivery logs

## Features

### Approvals
- Priority-based sorting (critical → high → medium → low)
- Risk factor visualization
- Expiration warnings
- Status filtering
- Type filtering
- Approval/rejection with notes
- Auto-approval rule configuration

### Workflows
- Real-time status indicators
- Success rate calculation
- Visual node diagrams
- Execution history
- Error tracking
- Manual test execution
- Enable/disable workflows
- Detailed execution logs

### Webhooks
- Delivery status tracking
- Retry mechanism monitoring
- Response time metrics
- Payload inspection
- Multi-attempt delivery logs
- Event type analytics
- Failed webhook alerts

## Accessibility
- ARIA labels on interactive elements
- Keyboard navigation support
- Semantic HTML structure
- Color-contrast compliant
- Screen reader friendly status indicators

## Performance
- Memoized filters and sorting
- Lazy-loaded execution details
- Optimized re-renders with useMemo
- Efficient table rendering
- Collapsible sections for large data

## Usage Examples

### Navigate to Enhanced Approvals
```tsx
<Link to="/approvals-new">View Approval Queue</Link>
```

### View Approval Detail
```tsx
<Link to="/approvals/appr_abc123">View Approval</Link>
```

### Configure Rules
```tsx
<Link to="/approvals/rules">Manage Rules</Link>
```

### View Workflow
```tsx
<Link to="/workflows/wf_enrich_abc123">View Workflow</Link>
```

### Monitor Webhooks
```tsx
<Link to="/webhooks">Webhook Queue</Link>
```

## Mobile Responsiveness
- Responsive grid layouts (1 column mobile, 2 columns desktop)
- Touch-friendly buttons and interactions
- Collapsible sections for small screens
- Horizontal scroll for tables on mobile
- Adaptive stats cards

## Future Enhancements
- Real-time webhook delivery updates via WebSocket
- Approval notification system
- Workflow builder/editor UI
- Webhook retry manual trigger
- Export approval history
- Workflow performance analytics
- Rule template library
