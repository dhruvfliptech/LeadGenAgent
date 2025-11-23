# Journey 7: Component Structure

## File Tree

```
frontend/src/
├── components/
│   ├── approvals/
│   │   ├── RiskIndicator.tsx         # Risk level badge component
│   │   ├── ApprovalCard.tsx          # Queue item card
│   │   └── index.ts                  # Exports
│   │
│   └── workflows/
│       ├── WorkflowCard.tsx          # Workflow summary card
│       ├── WorkflowDiagram.tsx       # Visual node diagram
│       └── index.ts                  # Exports
│
├── pages/
│   ├── ApprovalsEnhanced.tsx         # /approvals-new
│   ├── ApprovalDetail.tsx            # /approvals/:id
│   ├── ApprovalRules.tsx             # /approvals/rules
│   ├── WorkflowsEnhanced.tsx         # /workflows-new
│   ├── WorkflowDetail.tsx            # /workflows/:id
│   └── Webhooks.tsx                  # /webhooks
│
├── mocks/
│   ├── approvals.mock.ts             # Approval data
│   ├── workflows.mock.ts             # Workflow data
│   └── webhooks.mock.ts              # Webhook data
│
└── App.tsx                           # Routes configuration
```

## Component Hierarchy

### Approvals Flow
```
ApprovalsEnhanced (Queue Page)
│
├── Stats Cards (4)
│   ├── Pending
│   ├── Approved Today
│   ├── Rejected
│   └── Expired
│
├── Filters
│   ├── Status Filter
│   ├── Risk Level Filter
│   └── Type Filter
│
└── Approval Grid
    └── ApprovalCard (multiple)
        ├── RiskIndicator
        ├── Type Badge
        ├── Title & Description
        ├── Risk Factors List
        └── Expiration Warning
            ↓ (click)
        ApprovalDetail (Detail Page)
        │
        ├── Header
        │   ├── Title
        │   └── RiskIndicator (large)
        │
        ├── Left Column
        │   ├── Risk Assessment Panel
        │   │   ├── Score Bar
        │   │   └── Risk Factors List
        │   │
        │   ├── Preview Panel
        │   │   ├── Email Subject
        │   │   ├── Recipient
        │   │   └── Email Body
        │   │
        │   └── Context Panel
        │
        └── Right Sidebar
            ├── Actions (Approve/Reject)
            ├── Status Info
            ├── Details
            └── Review History
```

### Approval Rules Flow
```
ApprovalRules (Rules Page)
│
├── Header
│   └── Create Rule Button
│
├── Rules Table
│   ├── Rule Row (multiple)
│   │   ├── Name & Description
│   │   ├── Type
│   │   ├── RiskIndicator
│   │   ├── Conditions Count
│   │   ├── Status Toggle
│   │   └── Actions (Test, Edit)
│   │
│   └── Rule Editor Modal (on click Edit/Create)
│       ├── Name Input
│       ├── Description Textarea
│       ├── Type Select
│       ├── Risk Level Select
│       ├── Requires Approval Checkbox
│       ├── Auto-approve Hours Input
│       ├── Approvers Input
│       └── Conditions Builder
```

### Workflows Flow
```
WorkflowsEnhanced (Dashboard Page)
│
├── Stats Cards (4)
│   ├── Total Workflows
│   ├── Active
│   ├── Success Rate
│   └── Total Executions
│
├── Status Filter Tabs
│   ├── All
│   ├── Active
│   ├── Inactive
│   └── Error
│
└── Workflows Grid
    └── WorkflowCard (multiple)
        ├── Status Badge
        ├── Trigger Type Icon
        ├── Name & Description
        ├── Stats (Executions, Success %, Avg Time)
        └── Last Execution Status
            ↓ (click)
        WorkflowDetail (Detail Page)
        │
        ├── Header
        │   ├── Name & Status Badge
        │   └── Actions (Test, Enable/Disable)
        │
        ├── Stats Row (4 cards)
        │   ├── Total Executions
        │   ├── Success Rate
        │   ├── Failed
        │   └── Avg Time
        │
        ├── Trigger Info Panel
        │   ├── Type
        │   ├── Configuration
        │   ├── Timeout
        │   └── Retry Settings
        │
        ├── WorkflowDiagram
        │   ├── Node Columns
        │   │   └── Node Cards (multiple)
        │   │       ├── Type Badge
        │   │       ├── Name
        │   │       └── Parameters Preview
        │   │
        │   └── Connections List
        │
        ├── Execution History Table
        │   └── Execution Row (multiple)
        │       ├── ID
        │       ├── Status Badge
        │       ├── Started Time
        │       ├── Duration
        │       └── View Details Button
        │           ↓ (click)
        │           Execution Details Panel
        │           ├── Input Data (JSON)
        │           ├── Output Data (JSON)
        │           └── Error (if any)
        │
        └── Logs Viewer (collapsible)
```

### Webhooks Flow
```
Webhooks (Queue Page)
│
├── Stats Cards (5)
│   ├── Queued
│   ├── Sending
│   ├── Delivered
│   ├── Failed
│   └── Success Rate
│
├── Filters
│   ├── Status Filter
│   └── Event Type Filter
│
├── Webhooks Table
│   └── Webhook Row (multiple, expandable)
│       ├── Webhook ID
│       ├── Event Type
│       ├── Status Icon & Badge
│       ├── Attempts
│       ├── Response Time
│       ├── Created Time
│       └── View/Hide Button
│           ↓ (expand)
│           Webhook Details
│           ├── Target URL
│           ├── Workflow Link
│           ├── Next Retry (if retrying)
│           ├── Error Message (if failed)
│           ├── Payload (JSON)
│           └── Delivery Attempts
│               └── Attempt Card (multiple)
│                   ├── Attempt Number & Icon
│                   ├── Timestamp
│                   ├── Status Code
│                   ├── Response Time
│                   └── Error (if any)
│
└── Event Type Stats Grid
    └── Event Stat Card (8 types)
        ├── Count
        └── Event Name
```

## Data Flow

```
Mock Data (mocks/*.mock.ts)
  ↓
Pages (useState, useMemo)
  ↓
Components (props)
  ↓
User Interface
```

## State Management

### ApprovalsEnhanced
```typescript
const [filterRisk, setFilterRisk] = useState<RiskLevel | 'all'>('all')
const [filterType, setFilterType] = useState<ApprovalType | 'all'>('all')
const [filterStatus, setFilterStatus] = useState<'pending' | 'all'>('pending')
```

### ApprovalDetail
```typescript
const [rejectionReason, setRejectionReason] = useState('')
const [showRejectForm, setShowRejectForm] = useState(false)
```

### ApprovalRules
```typescript
const [rules, setRules] = useState(mockApprovalRules)
const [showRuleEditor, setShowRuleEditor] = useState(false)
const [editingRule, setEditingRule] = useState<ApprovalRule | null>(null)
```

### WorkflowsEnhanced
```typescript
const [filterStatus, setFilterStatus] = useState<WorkflowStatus | 'all'>('all')
```

### WorkflowDetail
```typescript
const [showLogs, setShowLogs] = useState(false)
const [selectedExecution, setSelectedExecution] = useState<string | null>(null)
```

### Webhooks
```typescript
const [filterStatus, setFilterStatus] = useState<WebhookStatus | 'all'>('all')
const [filterEvent, setFilterEvent] = useState<WebhookEventType | 'all'>('all')
const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null)
```

## Styling Patterns

### Color Coding
- **Risk Levels:**
  - Low: Green (bg-green-100, text-green-800)
  - Medium: Yellow (bg-yellow-100, text-yellow-800)
  - High: Orange (bg-orange-100, text-orange-800)
  - Critical: Red (bg-red-100, text-red-800)

- **Status:**
  - Success/Active/Delivered: Green
  - Error/Failed: Red
  - Pending/Queued: Gray
  - Sending/Retrying: Blue/Yellow

### Responsive Breakpoints
- Mobile: 1 column grid
- Desktop (lg): 2 column grid
- Stats cards: 1 → 2 → 4 columns

### Card Pattern
```tsx
<div className="card">
  <div className="px-6 py-4 border-b border-gray-200">
    {/* Header */}
  </div>
  <div className="p-6">
    {/* Content */}
  </div>
  <div className="px-6 py-4 border-t border-gray-200">
    {/* Footer */}
  </div>
</div>
```
