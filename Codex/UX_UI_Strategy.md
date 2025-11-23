## UX & UI Strategy – Unified Dashboard Experience

### 1. Goals
- Transition to a glassmorphism-inspired, data-dense experience that balances operations (scraping, campaigns) with insights (AI-GYM, analytics).
- Maintain continuity for existing users while expanding information architecture to support new modules (demo builder, video automation, conversation agent).
- Define component specifications to accelerate design-to-dev handoff using shadcn/ui + Tailwind.

### 2. Information Architecture
| Section | Purpose | Key Views |
|---------|---------|-----------|
| Overview | Platform health snapshot and AI-GYM summary | KPI tiles, model leaderboard, activity feed |
| Acquisition | Manage scraping sources, job status, lead intake | Source catalog, job run history, lead quality heatmap |
| Intelligence | Website analyses, demo QA status, video assets | Side-by-side viewer, improvement planner, QA reports |
| Outreach | Campaign scheduler, email templates, deliverability | Campaign cards, send calendar, template editor |
| Conversations | Reply queue, sentiment trends, HITL approvals | Thread viewer, suggestion panel, triage queue |
| Analytics | Funnel metrics, A/B tests, ROI dashboards | Cohort charts, AB test matrix, revenue table |
| Settings | Integrations, API keys, compliance configs | Integration checklist, consent settings |

Navigation adopts persistent left rail with icons + labels, sub-nav tabs per section.

### 3. Visual Language
- **Theme**: Frosted glass panels with gradient accents (primary: #6C5CE7, secondary: #00B894, neutral background #0B132B).
- **Typography**: `Inter` for body, `Sora` for headings. H1 32px-bold, H2 24px-semibold, body 14-16px.
- **Color Tokens**:
  - `surface-glass`: rgba(14, 25, 44, 0.6) with backdrop blur
  - `accent-positive`: #00B894
  - `accent-warning`: #FDCB6E
  - `accent-danger`: #E17055
  - `text-primary`: #FFFFFF, `text-secondary`: rgba(255,255,255,0.7)
- **Density**: Use 16px spacing grid; components adhere to 8px increments internally.

### 4. Component Specs
1. **KPI Tile**
   - Dimensions: 260x160, glass card, icon badge, metric, delta indicator.
   - Variants: Primary metric, secondary metric, status metric (with traffic light).

2. **Model Leaderboard**
   - Table with columns: Rank, Model, Uses, Quality, Cost, Conversion.
   - Support sorting, inline sparkline per model (reply rate over time).

3. **Workflow Timeline**
   - Horizontal stepper showing scrape → analysis → demo → video → email status.
   - Each step displays status badge (success, in-progress, blocked) with tooltip details.

4. **Lead Detail Drawer**
   - Slide-over panel triggered from list.
   - Tabs: Summary, Analysis, Assets, Conversation.
   - Feature: side-by-side website viewer with overlay annotations.

5. **Approval Queue Card**
   - Compact list with CTA buttons (Approve, Request Changes, Reject) and preview modals.
   - Include AI confidence score and recommended action.

6. **Campaign Scheduler**
   - Calendar heatmap displaying send volume per hour.
   - Draggable handles to adjust distribution; summary stats update live.

7. **Conversation Console**
   - Two-panel layout: thread list (left) + message view (right).
   - Suggestion composer with AI-generated response, rationale, cost estimate.

### 5. Interaction Patterns
- **Status Chips**: use consistent color coding; clickable to filter.
- **Global Search**: fuzzy search across leads, campaigns, companies, knowledge base.
- **Command Palette** (`⌘K`): quick actions (create campaign, rerun analysis, view latest demo).
- **Notifications**: toast for short-lived events, in-app inbox for approvals and alerts.
- **Dark Mode**: default; ensure contrast ratios > 4.5:1. Light mode optional in later release.

### 6. Responsive Strategy
- Desktop-first (1280px+), degrade gracefully to tablet (1024px) with collapsible navigation.
- Mobile: limited to read-only insights (KPI, campaign status); editing locked to desktop for now.

### 7. Accessibility
- Adhere to WCAG 2.1 AA: focus states, keyboard navigation, ARIA labels for dynamic charts.
- Provide alternative text for videos/demos; ensure color-coded statuses have text labels.

### 8. UX Research & Validation Plan
- Conduct contextual inquiry with outreach operators (2 sessions per module).
- Usability tests after each epic (5 participants) focusing on new modules.
- Integrate Hotjar/FullStory for qualitative insights (with consent).
- NPS and task success metrics tracked in analytics deck.

### 9. Delivery Checklist per Feature
1. Low-fidelity wireframes reviewed by product & engineering.
2. High-fidelity Figma with component spec + tokens.
3. Accessibility audit (color contrast, keyboard flow) before code handoff.
4. Frontend build in Next.js with Storybook story + automated screenshot diff.
5. Post-release survey to capture adoption issues.

### 10. Asset & Component Management
- Use shadcn/ui generator for base components; extend in `/components/ui` with tokens.
- Maintain design tokens in `tailwind.config.ts` and sync with Figma via Style Dictionary.
- Document component usage in `frontend/docs/ui-catalog.md` (to be created).

### 11. Risks & Mitigations
- **Complexity Creep**: enforce scope lock per epic; backlog extra visual polish.
- **Performance**: monitor Lighthouse scores; lazy-load heavy charts; virtualization for large lists.
- **Inconsistency**: centralize tokens and adopt linting (eslint-plugin-tailwindcss) to align spacing/color usage.

### 12. Next Actions
1. Produce Figma sitemap & UI kit aligning with this spec.
2. Schedule UX workshops for acquisition and outreach domains.
3. Implement design QA checklist in CI (chromatic snapshots).

