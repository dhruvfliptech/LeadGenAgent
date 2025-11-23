# UX Flow: Conversation Management System

**Date**: November 4, 2025
**Purpose**: Define complete user experience for email reply handling and AI conversations

---

## User Journey Overview

```
START: User sends email via Leads page
   ↓
WAIT: System monitors Gmail for replies (background)
   ↓
NOTIFICATION: "New reply from [Lead Name]!" (toast + badge)
   ↓
VIEW: User clicks to see Conversations page
   ↓
READ: Full conversation thread displayed
   ↓
AI SUGGESTS: Proposed response shown with confidence score
   ↓
DECISION: User can Edit, Approve, or Reject
   ↓
SEND: Response sent (if approved)
   ↓
TRACK: Conversation continues, repeat cycle
```

---

## Page-by-Page UX Design

### 1. Dashboard (Enhanced)

**New Elements**:
```
┌─────────────────────────────────────────────────┐
│ Dashboard                                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  [Stats Cards]  [Stats Cards]  [Stats Cards]    │
│                                                  │
│  🔔 NEW: Conversation Activity Card              │
│  ┌──────────────────────────────────────────┐   │
│  │ 💬 Active Conversations          [View] │   │
│  │                                          │   │
│  │ • 3 pending replies (needs approval)     │   │
│  │ • 5 ongoing conversations                │   │
│  │ • 12 total conversations today           │   │
│  │                                          │   │
│  │ Recent:                                  │   │
│  │ [Avatar] John Doe replied 5 min ago  👁️ │   │
│  │ [Avatar] Jane Smith needs reply   ⚡    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Interactions**:
- Click "View" → Navigate to Conversations page
- Click conversation item → Open that specific conversation
- Real-time updates via WebSocket (new reply badge appears)

---

### 2. Navigation (Updated)

**Current**:
```
Core: Dashboard | Leads | Scraper
Phase 3: Approvals | Location Map
```

**NEW**:
```
Core: Dashboard | Leads | Scraper | 💬 Conversations (NEW!)
Phase 3: Approvals | Location Map
```

**Badge System**:
- Red dot badge on "Conversations" when pending replies exist
- Number badge showing count: `💬 Conversations (3)`

---

### 3. Conversations Page (NEW - Primary Interface)

#### Layout Structure:
```
┌───────────────────────────────────────────────────────────────────┐
│ 💬 Conversations                                    [Filters ▾]   │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Sidebar (30%)              │  Main Content (70%)                 │
│  ┌──────────────────────┐   │  ┌────────────────────────────────┐│
│  │ Search: [________🔍] │   │  │ Conversation with John Doe     ││
│  │                      │   │  │ john@example.com               ││
│  │ Filters:             │   │  │ Lead: ABC Corp Website         ││
│  │ ☐ Needs Reply        │   │  │                                ││
│  │ ☑ Active             │   │  │ ─────────────────────────────  ││
│  │ ☐ Archived           │   │  │                                ││
│  │                      │   │  │ [Your Email - Sent 2 days ago] ││
│  │ ─────────────────── │   │  │ Subject: Website Improvements  ││
│  │                      │   │  │ Hi John, I noticed your site...││
│  │ ⚡ NEEDS REPLY (3)   │   │  │                                ││
│  │ ┌────────────────┐   │   │  │ [Their Reply - 5 min ago]     ││
│  │ │🔴 John Doe     │ ←─┼───┼─→│ Thanks! I'm interested. Can   ││
│  │ │ 5 min ago      │   │   │  │ you show me examples?         ││
│  │ └────────────────┘   │   │  │                                ││
│  │ ┌────────────────┐   │   │  │ ─────────────────────────────  ││
│  │ │⚡ Jane Smith   │   │   │  │                                ││
│  │ │ 2 hours ago    │   │   │  │ 🤖 AI SUGGESTED REPLY          ││
│  │ └────────────────┘   │   │  │ ┌────────────────────────────┐││
│  │                      │   │  │ │ ✨ High Confidence (92%)   │││
│  │ 💬 ACTIVE (5)        │   │  │ │                            │││
│  │ ┌────────────────┐   │   │  │ │ Hi John! Absolutely. I've  │││
│  │ │ Mike Johnson   │   │   │  │ │ analyzed your site and     │││
│  │ │ Yesterday      │   │   │  │ │ created a demo showing 3   │││
│  │ └────────────────┘   │   │  │ │ improvements. Check it out:│││
│  │                      │   │  │ │ [View Demo]                │││
│  │ ✅ ARCHIVED (45)     │   │  │ │                            │││
│  └──────────────────────┘   │  │ │ [Edit] [Approve] [Reject]  │││
│                              │  │ └────────────────────────────┘││
│                              │  │                                ││
│                              │  │ Or write custom reply:         ││
│                              │  │ [Write Custom Reply ✏️]         ││
│                              │  └────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────┘
```

#### Sidebar List Item States:
```
🔴 Red Dot = New reply, needs attention (pulsing animation)
⚡ Lightning = AI reply pending approval
💬 Speech bubble = Active conversation (no action needed yet)
✅ Checkmark = Archived/completed
```

#### Main Content - Message Bubbles:
```
OUTGOING (Your messages):
┌─────────────────────────────────────────┐
│ [Your Email - Sent 2 days ago]          │ ← Right-aligned
│ Subject: Website Improvements           │   Blue background
│ Hi John, I noticed your site could...   │   #0A84FF
└─────────────────────────────────────────┘

INCOMING (Their replies):
┌─────────────────────────────────────────┐
│ [Their Reply - 5 min ago]               │ ← Left-aligned
│ Thanks! I'm interested. Can you show... │   Gray background
└─────────────────────────────────────────┘   #2C2C2E

AI SUGGESTED (Pending approval):
┌─────────────────────────────────────────┐
│ 🤖 AI SUGGESTED REPLY                   │ ← Center, dashed border
│ ✨ High Confidence (92%)                │   Purple accent
│                                         │   #8E44AD
│ [Draft message text here...]            │
│                                         │
│ [Edit ✏️] [Approve ✅] [Reject ❌]       │
└─────────────────────────────────────────┘
```

---

### 4. AI Suggestion Card - Detailed Design

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI SUGGESTED REPLY                  ✨ Confidence: 92%  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Hi John! Absolutely. I've analyzed your website and         │
│ identified 3 key improvements that could increase your      │
│ conversions by 25-40%. I've created a demo site showing:    │
│                                                              │
│ 1. Faster load times (from 4.2s to 1.1s)                   │
│ 2. Mobile-responsive redesign                               │
│ 3. Clear call-to-action buttons                             │
│                                                              │
│ Check it out here: [View Live Demo →]                       │
│                                                              │
│ Would you like to schedule a quick 15-minute call to        │
│ discuss implementation?                                      │
│                                                              │
│ Best regards,                                                │
│ [Your Name]                                                  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ 🧠 AI Analysis:                                             │
│ • Detected question about examples ✓                        │
│ • Sentiment: Positive, interested 😊                        │
│ • Intent: Requesting proof/demonstration                    │
│ • Suggested tone: Professional but friendly                 │
│                                                              │
│ 📊 Context Used:                                            │
│ • Previous email (website analysis)                         │
│ • Lead's website data                                       │
│ • 3 similar successful conversations                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [✏️ Edit Reply]    [✅ Approve & Send]    [❌ Reject]      │
│                                                              │
│  Or: [🔄 Regenerate with different tone ▾]                  │
│      ├─ More formal                                         │
│      ├─ More casual                                         │
│      ├─ Shorter version                                     │
│      └─ Add humor                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Edit Reply Modal

**Triggered by**: Click "Edit Reply" on AI suggestion

```
┌─────────────────────────────────────────────────────────┐
│ ✏️ Edit AI Reply                                [Close] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ To: john@example.com                                    │
│ Subject: Re: Website Improvements                       │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Hi John! Absolutely. I've analyzed your website and │ │
│ │ identified 3 key improvements...                    │ │
│ │                                                     │ │
│ │ [Full editable text here]                          │ │
│ │                                                     │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ 💡 AI Suggestions:                                      │
│ • Add urgency: "Limited-time offer"                    │
│ • Personalize: Mention their industry (e-commerce)     │
│ • CTA: Make "schedule call" more prominent             │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Apply Suggestion 1] [Apply 2] [Apply 3]           │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│                [Cancel]    [Save & Send ✉️]             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 6. Approval Flow - Step by Step

**User Action → System Response**:

1. **User clicks "Approve & Send"**:
   ```
   ┌────────────────────────────────────┐
   │ ✅ Sending reply...                │  ← Loading state
   │ [Progress spinner]                 │
   └────────────────────────────────────┘
   ```

2. **Success**:
   ```
   ┌────────────────────────────────────┐
   │ ✅ Reply sent successfully!        │  ← Toast notification
   │ Conversation updated.              │    (disappears in 3s)
   └────────────────────────────────────┘

   [Conversation thread updates to show sent message]
   [Sidebar badge count decreases by 1]
   ```

3. **Error**:
   ```
   ┌────────────────────────────────────┐
   │ ❌ Failed to send reply            │  ← Error toast
   │ Postmark error: Invalid recipient  │
   │ [Retry] [Edit]                     │
   └────────────────────────────────────┘
   ```

---

### 7. Notification System

#### In-App Notifications:
```
TOP RIGHT BELL ICON: 🔔 (3)  ← Badge count

Dropdown menu:
┌────────────────────────────────────────┐
│ 🔔 Notifications                       │
├────────────────────────────────────────┤
│ 🔴 New reply from John Doe             │ ← Unread (bold)
│    "Thanks! I'm interested..."         │
│    5 minutes ago                [View] │
├────────────────────────────────────────┤
│ ⚡ AI reply ready for Jane Smith       │
│    Confidence: 88%                     │
│    2 hours ago                  [View] │
├────────────────────────────────────────┤
│ ✅ Reply sent to Mike Johnson          │ ← Read (faded)
│    Yesterday                           │
├────────────────────────────────────────┤
│                        [Mark all read] │
└────────────────────────────────────────┘
```

#### Desktop/Browser Notifications:
```
╔═══════════════════════════════════════╗
║ 💬 CraigLeads Pro                     ║
║ New reply from John Doe               ║
║ "Thanks! I'm interested. Can you..." ║
║                                       ║
║ [View Conversation] [Dismiss]        ║
╚═══════════════════════════════════════╝
```

---

### 8. Mobile Responsive Design

**Conversations on Mobile** (< 768px):
```
┌─────────────────────┐
│ ← Conversations     │  ← Back button when conversation open
├─────────────────────┤
│                     │
│ [Conversation List] │  ← Full width on mobile
│                     │
│ OR                  │  ← Slides in when conversation selected
│                     │
│ [Active Thread]     │  ← Full screen conversation view
│                     │
│ [AI Suggestion]     │  ← Scrollable
│                     │
└─────────────────────┘

Interaction:
1. Default: Show list of conversations
2. Tap conversation → Slide to full-screen thread view
3. Tap back arrow → Slide back to list
```

---

### 9. Filter & Search UX

**Search Bar**:
```
┌─────────────────────────────────────┐
│ Search: [__________________ 🔍]     │
└─────────────────────────────────────┘

As user types:
- Real-time filtering of conversation list
- Searches: lead name, email, message content
- Highlights matching text in results
```

**Filter Dropdown**:
```
[Filters ▾]

Opens:
┌───────────────────────────────┐
│ ☑ Needs Reply (3)             │ ← Checked by default
│ ☐ Active (5)                  │
│ ☐ Waiting for Response (2)    │
│ ☐ Archived (45)               │
├───────────────────────────────┤
│ Sort by:                      │
│ ◉ Most Recent                 │
│ ○ Oldest First                │
│ ○ Most Messages               │
│ ○ Highest Priority            │
├───────────────────────────────┤
│ [Clear Filters] [Apply]       │
└───────────────────────────────┘
```

---

### 10. Empty States

**No Conversations Yet**:
```
┌─────────────────────────────────────┐
│         💬                          │
│                                     │
│   No conversations yet              │
│                                     │
│   Start by sending emails to leads  │
│   from the Leads page. When they    │
│   reply, they'll appear here.       │
│                                     │
│   [Go to Leads Page →]              │
│                                     │
└─────────────────────────────────────┘
```

**All Caught Up**:
```
┌─────────────────────────────────────┐
│         ✅                          │
│                                     │
│   All caught up!                    │
│                                     │
│   No pending replies right now.     │
│   Great job staying on top of       │
│   your conversations!               │
│                                     │
└─────────────────────────────────────┘
```

---

### 11. Keyboard Shortcuts (Power User Feature)

```
Global:
- `C` → Go to Conversations page
- `N` → Next conversation
- `P` → Previous conversation
- `/` → Focus search bar

In Conversation View:
- `R` → Reply (opens custom reply box)
- `A` → Approve AI suggestion
- `E` → Edit AI suggestion
- `Esc` → Close modals/go back
- `Cmd+Enter` → Send reply
```

---

### 12. Color System & Visual Hierarchy

**Status Colors**:
```
🔴 Needs Reply:     #FF3B30 (Red)
⚡ AI Pending:       #8E44AD (Purple)
💬 Active:           #0A84FF (Blue)
✅ Archived:         #34C759 (Green)
⚠️ Error:            #FF9500 (Orange)
```

**Confidence Indicators**:
```
High (85-100%):     ✨ Green badge   #34C759
Medium (70-84%):    ⚡ Yellow badge  #FFCC00
Low (<70%):         ⚠️ Orange badge  #FF9500
```

**Message Bubbles**:
```
Outgoing:   Blue    #0A84FF
Incoming:   Gray    #2C2C2E
AI Draft:   Purple  #8E44AD (dashed border)
```

---

### 13. Animation & Micro-interactions

**New Reply Appears**:
- Fade in from top
- Pulse red dot on sidebar item 3 times
- Play subtle notification sound (optional)
- Desktop notification if page not focused

**Approval Action**:
- Button changes: "Approve & Send" → "Sending..." (with spinner)
- Success: Green checkmark animation, message slides into thread
- Confetti animation (optional, can be disabled in settings)

**AI Suggestion Loading**:
```
┌─────────────────────────────────────┐
│ 🤖 AI is analyzing the reply...     │
│ [Animated dots: • • •]              │
│                                     │
│ Analyzing sentiment...        [✓]   │
│ Generating response...        [✓]   │
│ Optimizing tone...            [⏳]  │
└─────────────────────────────────────┘

Duration: ~2-5 seconds
Shows progress to build anticipation
```

---

### 14. Settings & Preferences

**New Settings Section**: `Conversations → Settings`

```
┌─────────────────────────────────────────────┐
│ 💬 Conversation Settings                     │
├─────────────────────────────────────────────┤
│                                              │
│ 🔔 Notifications:                            │
│ ☑ Desktop notifications for new replies     │
│ ☑ Play sound on new reply                   │
│ ☑ Email digest (daily summary)              │
│                                              │
│ 🤖 AI Behavior:                              │
│ Auto-approve replies with confidence > [92%] │
│ [Slider: 70% ─●────── 95%]                  │
│                                              │
│ ☐ Require manual approval for all replies   │
│ ☑ Show AI analysis details                  │
│ ☑ Suggest improvements to drafts            │
│                                              │
│ ⏱️ Response Timing:                          │
│ Wait [5] minutes before suggesting reply    │
│ Auto-archive after [30] days of inactivity  │
│                                              │
│ 🎨 Display:                                  │
│ ☑ Show conversation previews                │
│ ☑ Enable animations                         │
│ Theme: ◉ Dark  ○ Light  ○ Auto             │
│                                              │
│           [Save Preferences]                 │
│                                              │
└─────────────────────────────────────────────┘
```

---

### 15. Analytics View (Conversation Stats)

**New Dashboard Widget**:
```
┌─────────────────────────────────────────────────┐
│ 📊 Conversation Analytics                       │
├─────────────────────────────────────────────────┤
│                                                  │
│ This Week:                                      │
│ • 45 emails sent                                │
│ • 18 replies received (40% response rate) ↑     │
│ • 15 AI replies approved (83% approval rate)    │
│ • Avg response time: 2.5 hours ⚡               │
│                                                  │
│ [View Detailed Analytics →]                     │
│                                                  │
└─────────────────────────────────────────────────┘

Detailed Analytics Page:
- Response rate over time (line chart)
- AI approval rate by confidence level (bar chart)
- Most effective message types (pie chart)
- Time-to-response distribution (histogram)
```

---

## Technical Implementation Notes

### WebSocket Events:
```typescript
// Frontend subscribes to these events:
'conversation:new_reply'      → Trigger notification, update sidebar
'conversation:ai_ready'       → Show AI suggestion card
'conversation:sent'           → Update thread, remove from pending
'conversation:error'          → Show error toast
```

### API Endpoints Needed:
```
GET    /api/v1/conversations                    → List all conversations
GET    /api/v1/conversations/:id                → Get conversation thread
POST   /api/v1/conversations/:id/reply          → Send custom reply
POST   /api/v1/conversations/:id/approve        → Approve AI suggestion
POST   /api/v1/conversations/:id/reject         → Reject AI suggestion
POST   /api/v1/conversations/:id/regenerate     → Regenerate AI reply
PATCH  /api/v1/conversations/:id/archive        → Archive conversation
GET    /api/v1/conversations/stats              → Get analytics
```

### Database Tables:
```sql
-- conversations
id, lead_id, subject, status, last_message_at, created_at

-- conversation_messages
id, conversation_id, direction (inbound/outbound), content,
sent_at, sender_email, recipient_email, postmark_message_id

-- ai_suggestions
id, conversation_id, message_id (reply to), suggested_content,
confidence_score, sentiment_analysis, status (pending/approved/rejected),
created_at
```

---

## Success Metrics

**User can successfully**:
1. ✅ See new replies within 10 seconds of arrival
2. ✅ Read full conversation history in chronological order
3. ✅ Understand AI confidence level before approving
4. ✅ Edit AI suggestions inline without leaving page
5. ✅ Send reply with 2 clicks (View → Approve)
6. ✅ Track all conversations from single dashboard
7. ✅ Search/filter to find specific conversations quickly
8. ✅ Use keyboard shortcuts for common actions

**System Metrics**:
- Page load time < 1s
- AI suggestion generated in < 3s
- Email sent in < 2s after approval
- Real-time updates with < 500ms latency
- 99%+ uptime for Gmail monitoring

---

**Next Steps**: This UX flow will guide the implementation of all conversation features in parallel.
