# User Journey Maps - Complete Frontend Flows

**Purpose:** Exhaustive documentation of every user flow in the application. This serves as the blueprint for frontend development - every screen, interaction, state, and transition documented in detail.

**Target Audience:** Developers, designers, stakeholders, and users who want to understand exactly how the application works.

---

## Table of Contents

1. [Journey 1: Multi-Source Lead Scraping](#journey-1-multi-source-lead-scraping)
2. [Journey 2: Website Analysis → Demo Site Generation](#journey-2-website-analysis--demo-site-generation)
3. [Journey 3: Demo Site → Video Creation](#journey-3-demo-site--video-creation)
4. [Journey 4: Email Outreach & Campaign Management](#journey-4-email-outreach--campaign-management)
5. [Journey 5: Conversation AI & Response Management](#journey-5-conversation-ai--response-management)
6. [Journey 6: AI-GYM Dashboard & Model Optimization](#journey-6-ai-gym-dashboard--model-optimization)
7. [Journey 7: Approval Workflows & n8n Integration](#journey-7-approval-workflows--n8n-integration)

---

## Journey 1: Multi-Source Lead Scraping

**Goal:** User scrapes leads from multiple sources (Craigslist, Google Maps, LinkedIn, Job Boards) and enriches them with contact information via n8n workflow.

### Entry Points
- Click "Scraper" in main navigation
- Click "New Scrape Job" from Leads page
- Quick action from dashboard

---

### Flow 1A: Craigslist Scraping

#### Screen 1: Scraper Page - Source Selection
**URL:** `/scraper`

**Page Elements:**
- **Header:** "Lead Scraper"
- **Subheader:** "Scrape leads from multiple sources"
- **Source Cards (4 cards in grid):**
  1. **Craigslist** - "Local classifieds & services" [Active]
  2. **Google Maps** - "Local businesses by location" [Active]
  3. **LinkedIn** - "Professional contacts & companies" [Active]
  4. **Job Boards** - "Indeed, Monster, ZipRecruiter" [Active]
- **Active Scraping Jobs Section:**
  - Table showing: Job ID, Source, Status, Progress, Started At, Actions
  - "View Details" button per job
  - Real-time status updates via WebSocket

**User Action:** Click "Craigslist" card

**State Changes:**
- Craigslist card highlights
- Modal/wizard opens

---

#### Screen 2: Craigslist Scraper Configuration Wizard

**Modal Title:** "Configure Craigslist Scraping Job"

**Step 1: Location Selection**

**UI Components:**
- **Step Indicator:** 1 of 4 active
- **Hierarchical Location Selector:**
  - **Search Bar:** "Search locations..."
  - **Tree View with Checkboxes:**
    - 📍 United States [+]
      - 📍 California [+]
        - ☐ San Francisco Bay Area
        - ☐ Los Angeles
        - ☐ San Diego
      - 📍 New York [+]
        - ☐ New York City
        - ☐ Buffalo
    - 📍 Canada [+]
    - 📍 International [+]
  - **Expand/Collapse All** button
  - **Select All/Deselect All** button
- **Selected Locations Chips:**
  - "San Francisco Bay Area ✕"
  - "New York City ✕"
  - Badge: "2 locations selected"
- **Buttons:**
  - "Cancel" (left)
  - "Next: Categories →" (right, primary, disabled if no selection)

**User Interactions:**
- Check/uncheck locations
- Search filters tree
- Remove location chips
- Expand/collapse regions

**Validation:**
- Must select at least 1 location
- Cannot exceed 50 locations (warning if over 10)

**User Action:** Select "San Francisco Bay Area" and "Los Angeles", click "Next"

**State Changes:**
- Step 2 becomes active
- Selected locations stored

---

**Step 2: Category Selection**

**UI Components:**
- **Step Indicator:** 2 of 4 active
- **Category Grid (clickable cards):**
  - **Services** [icon]
    - "Creative services, computer services, etc."
  - **For Sale** [icon]
    - "Goods, vehicles, etc."
  - **Gigs** [icon]
    - "Computer gigs, creative gigs, labor gigs"
  - **Community** [icon]
    - "Activities, events, general"
  - **Housing** [icon]
    - "Apartments, rooms, real estate"
  - **Jobs** [icon]
    - "All job categories"
  - [+ 10 more category cards]
- **Selected Categories Chips:**
  - Badge: "0 categories selected (optional)"
- **Info Box:** "💡 Leave empty to scrape all categories"
- **Buttons:**
  - "← Back" (secondary)
  - "Next: Filters →" (primary)

**User Interactions:**
- Click category cards to select/deselect
- Multiple selection allowed
- Hover shows category description

**Validation:**
- Optional - can proceed with no selection

**User Action:** Select "Services" and "Gigs", click "Next"

---

**Step 3: Search Filters**

**UI Components:**
- **Step Indicator:** 3 of 4 active
- **Form Fields:**
  1. **Keywords** (text input)
     - Placeholder: "e.g., web design, SEO, marketing"
     - Help text: "Comma-separated keywords (optional)"
  2. **Search Distance** (dropdown)
     - Options: Search titles only | Nearby areas | + search distance
  3. **Has Image?** (checkbox)
     - Label: "Only show listings with images"
  4. **Posted Today?** (checkbox)
     - Label: "Only show listings posted today"
  5. **Price Range** (dual slider)
     - Min: $0, Max: $10,000
     - Current: $0 - $10,000 (any)
  6. **Max Results** (number input)
     - Default: 100
     - Help text: "Maximum number of listings to scrape"
- **Advanced Filters (Collapsible):**
  - Dealer/Owner filter
  - Specific attributes per category
- **Buttons:**
  - "← Back"
  - "Next: Review →"

**User Action:** Enter "web design, SEO" in keywords, check "Has Image", set max results to 50, click "Next"

---

**Step 4: Review & Start**

**UI Components:**
- **Step Indicator:** 4 of 4 active
- **Review Summary Card:**
  - **Locations:** (2)
    - San Francisco Bay Area
    - Los Angeles
  - **Categories:** (2)
    - Services
    - Gigs
  - **Filters:**
    - Keywords: web design, SEO
    - Has image: Yes
    - Posted today: No
    - Max results: 50
  - **Estimated Results:** ~45-50 listings
  - **Estimated Time:** ~5-10 minutes
- **Lead Enrichment Toggle:**
  - ☑ "Enrich leads with contact information (email/phone)"
  - Help text: "Uses n8n workflow to find emails via Hunter.io/Apollo.io"
  - Cost indicator: "+$0.10 per lead enriched"
- **Notification Preferences:**
  - ☐ Email notification when complete
  - ☐ Slack notification when complete
- **Buttons:**
  - "← Back"
  - "Start Scraping" (primary, large)

**User Action:** Click "Start Scraping"

**State Changes:**
- Modal closes
- New job appears in Active Jobs table with "pending" status
- Toast notification: "✓ Scraping job started"
- Redirect to job detail view (optional)

---

#### Screen 3: Active Scraping Job View

**URL:** `/scraper/jobs/[job_id]`

**Real-time Updates:** WebSocket connection for live progress

**Page Elements:**
- **Header:**
  - Job ID: #12345
  - Status Badge: "In Progress" (pulsing animation)
  - Actions: "Pause" | "Cancel" | "Export"
- **Progress Overview Card:**
  - **Overall Progress Bar:** 34% complete
  - **Stats Row:**
    - Listings Scraped: 17 / 50
    - Leads Created: 12
    - Duplicates Skipped: 5
    - Errors: 0
  - **Time:**
    - Started: 2 minutes ago
    - Estimated completion: 3 minutes
- **Location Progress (per location):**
  - **San Francisco Bay Area:**
    - Progress bar: 45%
    - Status: "Scraping listings..." (with spinner)
    - Found: 8 leads
  - **Los Angeles:**
    - Progress bar: 20%
    - Status: "Starting..."
    - Found: 4 leads
- **Activity Log (live scroll):**
  - ✓ [12:34:56] Started job #12345
  - ✓ [12:35:02] Connected to Craigslist (San Francisco)
  - ✓ [12:35:15] Found 3 listings matching "web design"
  - ✓ [12:35:18] Lead created: "Web Design Services - $500"
  - ⚠ [12:35:20] Duplicate listing skipped
  - ✓ [12:35:23] Lead enrichment queued (Hunter.io)
  - ℹ [12:35:25] Enrichment complete: email found
- **Leads Preview Table:**
  - Shows leads as they're created (live updates)
  - Columns: Title, Location, Price, Posted Date, Contact Status
  - "View All Leads" button → redirects to Leads page with filter

**State Changes (Live via WebSocket):**
- Progress bars update in real-time
- Activity log scrolls automatically
- Leads appear in preview table as created
- Stats counters increment

**User Actions:**
- Watch progress
- Click "Pause" to pause scraping
- Click "Cancel" to stop job
- Click "View All Leads" to see results

---

**Screen 4: Job Complete**

**State Changes:**
- Status badge → "Completed" (green)
- Progress bar → 100%
- Stop button → "View Leads"
- Toast notification: "✓ Scraping job #12345 completed! 48 leads created"

**Final Stats:**
- Listings Scraped: 48 / 50
- Leads Created: 42
- Duplicates Skipped: 6
- Errors: 0
- Enriched Leads: 35 (83%)
- Duration: 8 minutes 42 seconds

**User Action:** Click "View Leads"

**Redirect:** `/leads?job_id=12345`

---

### Flow 1B: Google Maps Scraping

#### Screen 1: Google Maps Configuration Wizard

**Entry:** Click "Google Maps" card from Scraper page

**Step 1: Search Configuration**

**UI Components:**
- **Search Query Input:**
  - Label: "What are you looking for?"
  - Placeholder: "e.g., web design agency, Italian restaurant, dentist"
  - Help: "Business type or service"
- **Location Input:**
  - Label: "Where?"
  - Input: Autocomplete address/city
  - Placeholder: "e.g., San Francisco, CA"
  - Geolocation button: "Use my location"
- **Radius Slider:**
  - Label: "Search radius"
  - Range: 1 - 100 miles
  - Current: 25 miles
  - Visual: Map preview showing circle
- **Map Preview:**
  - Interactive map showing search area
  - Pin at center location
  - Circle showing radius
  - Draggable to adjust center

**Example Populated:**
- Query: "web design agency"
- Location: "San Francisco, CA"
- Radius: 25 miles

**User Action:** Fill form, click "Next"

---

**Step 2: Filters & Options**

**UI Components:**
- **Business Filters:**
  - **Rating Filter:** (star slider)
    - "Minimum rating: 4.0+ stars"
  - **Review Count:** (slider)
    - "Minimum reviews: 10+"
  - **Business Status:** (checkboxes)
    - ☑ Open now
    - ☐ Permanently closed
  - **Price Range:** (select)
    - $ | $$ | $$$ | $$$$
- **Scraping Options:**
  - **Max Results:** (number input)
    - Default: 100
    - Max: 500
  - **Include Reviews?** (toggle)
    - ☐ Scrape customer reviews
    - Help: "Adds ~10 seconds per business"
  - **Include Photos?** (toggle)
    - ☐ Download business photos
- **Lead Enrichment:**
  - ☑ Find email addresses (n8n → Hunter.io)
  - ☑ Find phone numbers
  - ☐ Find LinkedIn profiles

**User Action:** Set minimum rating 4.0+, max results 50, enable enrichment, click "Next"

---

**Step 3: Review & Start**

Similar to Craigslist flow - shows summary and starts scraping.

**Unique Elements:**
- Shows map visualization
- Estimated cost for enrichment
- Expected data: Name, Address, Phone, Website, Rating, Review Count, Hours

---

### Flow 1C: LinkedIn Scraping

#### Screen 1: LinkedIn Configuration Wizard

**⚠️ Warning Banner:**
"LinkedIn actively blocks scrapers. We recommend using LinkedIn Sales Navigator API or manual exports. Proceed with caution."

**Step 1: Search Type**

**UI Components:**
- **Search Type Cards:**
  1. **People Search**
     - "Find professionals by title, company, location"
     - Icon: person
  2. **Company Search**
     - "Find companies by industry, size, location"
     - Icon: building
  3. **Job Search**
     - "Find job postings by title, company, location"
     - Icon: briefcase

**User Action:** Select "People Search"

---

**Step 2: People Search Criteria**

**UI Components:**
- **Job Title:** (multi-input)
  - Placeholder: "e.g., Marketing Manager, CEO, Developer"
  - Can add multiple
- **Company:** (autocomplete)
  - "Current or past company"
- **Location:** (multi-select)
  - Cities or countries
- **Industry:** (dropdown)
  - Technology, Finance, Healthcare, etc.
- **Company Size:** (checkbox group)
  - 1-10 | 11-50 | 51-200 | 201-500 | 501-1000 | 1000+
- **Seniority Level:** (checkboxes)
  - Entry | Mid | Senior | Manager | Director | VP | C-level
- **Keywords:** (text input)
  - "Search in profiles, headlines, summaries"

**Example:**
- Job Title: "Marketing Director", "CMO"
- Industry: Technology
- Location: "San Francisco Bay Area", "New York"
- Company Size: 51-200, 201-500
- Seniority: Director, VP, C-level

**User Action:** Fill criteria, click "Next"

---

**Step 3: Authentication & Limits**

**UI Components:**
- **LinkedIn Account:** (required)
  - Username: (input)
  - Password: (password input)
  - Help: "We use your account to access LinkedIn. Credentials are encrypted."
  - ⚠️ "Your account may be flagged if scraping is detected"
- **Safety Limits:**
  - **Requests per day:** (slider)
    - Max: 100 (recommended)
    - Help: "Lower is safer"
  - **Delay between requests:** (slider)
    - Default: 10 seconds
    - Range: 5-60 seconds
- **Alternative: Import CSV**
  - "Already have a list? Upload LinkedIn CSV export"
  - File upload button

**User Action:** Enter credentials OR upload CSV, click "Next"

---

**Step 4: Review & Start**

Standard review screen + compliance warning about LinkedIn ToS.

---

### Flow 1D: Job Boards Scraping

#### Screen 1: Job Boards Configuration

**Step 1: Select Job Boards**

**UI Components:**
- **Job Board Cards (multi-select):**
  1. ☑ **Indeed**
     - "World's largest job site"
     - Coverage: Global
  2. ☑ **Monster**
     - "20M+ jobs globally"
     - Coverage: Global
  3. ☑ **ZipRecruiter**
     - "US-focused job board"
     - Coverage: USA
  4. ☐ **Glassdoor**
     - "Jobs + company reviews"
  5. ☐ **LinkedIn Jobs**
     - "Professional network jobs"
  6. ☐ **AngelList**
     - "Startup jobs"

**User Action:** Select Indeed, Monster, ZipRecruiter

---

**Step 2: Job Search Criteria**

**UI Components:**
- **Job Title/Keywords:** (text input)
  - Placeholder: "e.g., Software Engineer, Marketing Manager"
- **Location:** (multi-input)
  - Can add multiple cities/regions
- **Remote?** (toggle + options)
  - ☐ Remote only
  - ☐ Hybrid
  - ☑ Include on-site
- **Experience Level:** (checkboxes)
  - Entry Level | Mid Level | Senior | Executive
- **Salary Range:** (dual slider)
  - $0 - $200k+
- **Company Size:** (checkboxes)
  - Startup (1-50) | Small (51-200) | Medium (201-1000) | Large (1000+)
- **Date Posted:** (radio)
  - Last 24 hours | Last 3 days | Last week | Last month | Any time
- **Max Results per Board:** (number)
  - Default: 50
  - Max: 200

**User Action:** Fill criteria, click "Next"

---

**Step 3: Lead Extraction**

**UI Components:**
- **What to extract from job postings:**
  - ☑ Company name
  - ☑ Job title
  - ☑ Job description
  - ☑ Apply URL
  - ☑ Company website (if available)
  - ☑ Posted date
  - ☑ Salary (if listed)
- **Lead Enrichment:**
  - ☑ Find hiring manager emails
  - ☑ Find company contact info
  - Method: n8n workflow using Hunter.io/Apollo.io
- **Deduplication:**
  - ☑ Remove duplicate jobs across boards
  - Match by: Company name + Job title

**User Action:** Keep defaults, click "Next"

---

**Step 4: Review & Start**

Standard review showing:
- 3 job boards selected
- Search criteria summary
- Expected results: ~120-150 job postings
- Enrichment enabled
- Estimated time: 15-20 minutes

---

### Flow 1E: Lead Enrichment (n8n Background Process)

**This happens automatically in the background for all scraped leads**

#### n8n Workflow Visualization (for admin/debugging)

**Trigger:** New lead created in database (webhook)

**Steps:**
1. **Receive Lead Data**
   - Company name, website URL
2. **Hunter.io: Find Email**
   - Input: domain
   - Output: email addresses
   - Cost: $0.10
3. **If no email → Apollo.io Enrichment**
   - Input: company name + domain
   - Output: emails, phones, LinkedIn URLs
   - Cost: $0.20
4. **If still no contact → Clearbit**
   - Get company metadata
   - Cost: $0.15
5. **Update Lead in Database**
   - Add: email, phone, linkedin_url, enrichment_status
6. **Trigger Webhook to our app**
   - Notify lead enrichment complete

**Status Indicators (shown in Leads table):**
- 🟡 Pending enrichment
- 🔄 Enriching... (animated)
- ✅ Enriched (shows email/phone icons)
- ❌ Enrichment failed (shows retry button)

---

### Flow 1F: Viewing Scraped Leads

**URL:** `/leads`

**Entry Points:**
- Navigation → "Leads"
- After scraping job completes
- Dashboard widget

#### Screen: Leads Page

**Header:**
- Title: "Leads"
- Button: "+ New Lead" | "Import CSV" | "Export All"
- Stats Cards:
  - Total Leads: 1,247
  - New Today: 34
  - Enriched: 1,089 (87%)
  - Contacted: 423 (34%)

**Filters Panel (left sidebar):**
- **Source:** (checkboxes)
  - ☐ Craigslist (234)
  - ☐ Google Maps (567)
  - ☐ LinkedIn (123)
  - ☐ Job Boards (323)
- **Status:** (checkboxes)
  - ☐ New (234)
  - ☐ Contacted (423)
  - ☐ Replied (89)
  - ☐ Qualified (56)
- **Contact Info:** (checkboxes)
  - ☑ Has email
  - ☑ Has phone
  - ☐ Has LinkedIn
- **Location:** (multi-select dropdown)
- **Date Added:** (date range picker)
- **Tags:** (multi-select)
- **Clear Filters** button

**Search Bar:**
- Placeholder: "Search leads by name, company, title..."
- Fuzzy search enabled

**Leads Table:**
- **Columns:**
  1. ☐ (checkbox for bulk selection)
  2. Company/Name
     - Shows company name + lead title
     - Source icon (Craigslist/Google Maps/etc.)
  3. Contact Info
     - Email icon (clickable to copy)
     - Phone icon (clickable to copy)
     - LinkedIn icon (opens profile)
  4. Location
  5. Scraped Date
  6. Status (badge)
  7. Tags (chips)
  8. Actions (dropdown)
     - View Details
     - Edit
     - Send Email
     - Create Demo Site
     - Delete
- **Sorting:** Click column headers to sort
- **Pagination:** 25 per page
- **Bulk Actions Bar** (appears when rows selected):
  - "5 leads selected"
  - Actions: Send Email | Add Tag | Export | Delete

**Empty State (if no leads):**
- Illustration
- "No leads yet"
- "Start by scraping leads from Craigslist, Google Maps, or other sources"
- "Start Scraping" button

---

#### Screen: Lead Detail View

**URL:** `/leads/[lead_id]`

**Trigger:** Click lead row in table

**Modal/Slide-over Panel:**

**Header:**
- Lead title: "Web Design Services"
- Source badge: "Craigslist - San Francisco"
- Status dropdown: New → Contacted → Replied → Qualified → Won/Lost
- Actions: Edit | Delete | Create Demo | Send Email

**Tabs:**

**Tab 1: Overview**
- **Company Information:**
  - Name
  - Website (clickable link)
  - Phone
  - Email
  - Location
  - Description/Bio
- **Scraping Metadata:**
  - Source
  - Scraped Date
  - Job ID (link to job detail)
  - Original URL (link to listing)
- **Enrichment Data:**
  - Email found via: Hunter.io
  - Phone found via: Apollo.io
  - LinkedIn: [profile link]
  - Enrichment cost: $0.30
- **Tags:** (editable chips)
  - +Add tag
- **Notes:** (rich text editor)
  - Internal notes about this lead

**Tab 2: Activity Timeline**
- Chronological list of all interactions:
  - ✓ [Date] Lead created from Craigslist scrape
  - ✓ [Date] Email found via Hunter.io
  - ✓ [Date] Email sent: "Introduction to our services"
  - ✓ [Date] Email opened (2 times)
  - ✓ [Date] Reply received
  - ✓ [Date] Demo site created
  - ✓ [Date] Video sent
  - ✓ [Date] Status changed to "Qualified"

**Tab 3: Communications**
- Email thread view
- Shows all sent/received emails
- Reply inline

**Tab 4: Assets**
- Demo sites created for this lead
- Videos created
- Documents attached

---

## Journey 2: Website Analysis → Demo Site Generation

**Goal:** Analyze a lead's website, identify improvements, and generate an improved demo site using AI.

### Entry Points
- From Lead detail page → "Analyze Website" button
- Navigation → "Demo Sites" → "+ New Demo Site"
- Dashboard quick action

---

### Flow 2A: Website Analysis

#### Screen 1: Start Analysis

**URL:** `/demo-sites/new` or modal from lead detail

**UI Components:**
- **Header:** "Analyze Website & Create Demo"
- **Form:**
  - **Lead Selection:** (autocomplete dropdown)
    - Search existing leads OR
    - "Enter URL manually"
  - **Website URL:** (input)
    - Placeholder: "https://example.com"
    - Validation: Must be valid URL
  - **Analysis Depth:** (radio buttons)
    - ◉ Quick (homepage only) - ~30 seconds
    - ○ Standard (5 pages) - ~2 minutes
    - ○ Comprehensive (full site crawl) - ~5 minutes
  - **Analysis Focus:** (checkboxes)
    - ☑ Design & Visual
    - ☑ SEO & Content
    - ☑ Performance
    - ☑ Accessibility
    - ☑ Mobile Responsiveness
  - **Screenshot:** (toggle)
    - ☑ Capture website screenshot
- **Cost Estimate:**
  - "Estimated cost: $0.75 (AI analysis)"
- **Button:** "Start Analysis" (primary, large)

**User Action:** Select lead "Acme Corp", URL auto-fills, select "Standard" analysis, click "Start Analysis"

**State Change:**
- Redirect to analysis progress page
- Show loading state

---

#### Screen 2: Analysis in Progress

**URL:** `/demo-sites/analysis/[analysis_id]`

**Real-time Updates:** WebSocket connection

**UI Components:**
- **Progress Header:**
  - "Analyzing Acme Corp Website"
  - Status: "In Progress" (animated)
  - Progress: 45%
- **Step Progress:**
  - ✓ Fetching website content (completed)
  - ✓ Capturing screenshot (completed)
  - 🔄 Running Lighthouse audit (in progress)
  - ⏳ AI analysis (pending)
  - ⏳ Generating improvement plan (pending)
- **Screenshot Preview:**
  - Shows captured screenshot in card
  - Zoomable
- **Initial Findings (populate as available):**
  - **Quick Stats:**
    - Page load time: 3.2s
    - Page size: 2.4 MB
    - Requests: 87
  - **Issues Detected:** (counter increments live)
    - 12 design issues
    - 8 SEO issues
    - 15 performance issues
    - 6 accessibility issues
- **Activity Log:**
  - [12:34:56] Started analysis
  - [12:34:58] Fetched 5 pages
  - [12:35:05] Screenshot captured
  - [12:35:10] Lighthouse score: 68/100
  - [12:35:15] AI analysis 25% complete...

**Duration:** ~2 minutes

**State Change:** Analysis completes → redirect to results

---

#### Screen 3: Analysis Results

**URL:** `/demo-sites/analysis/[analysis_id]/results`

**Page Structure:** Dashboard-style with cards

**Header:**
- Website: "acmecorp.com"
- Overall Score: 68/100 (large, color-coded)
- Actions: "Generate Demo Site" | "Export Report" | "Re-analyze"

**Overview Cards (4 cards in row):**
1. **Design Score:** 72/100
   - Color: Yellow
   - Icon: Paint brush
2. **SEO Score:** 81/100
   - Color: Green
   - Icon: Search
3. **Performance Score:** 54/100
   - Color: Red
   - Icon: Lightning
4. **Accessibility Score:** 65/100
   - Color: Yellow
   - Icon: Universal access

**Detailed Analysis Tabs:**

#### Tab 1: Design Analysis

**Strengths Card:**
- ✓ Modern typography (Inter font)
- ✓ Clear visual hierarchy
- ✓ Professional color scheme
- ✓ Responsive grid layout

**Issues Card (12 issues):**
1. **Poor Color Contrast** [High Priority]
   - Text: #666 on #fff background (ratio: 3.5:1)
   - Requirement: 4.5:1 for WCAG AA
   - Affected: 15 elements
   - Fix: Change text to #555 or darker

2. **Inconsistent Spacing** [Medium Priority]
   - Margins vary (8px, 12px, 15px, 20px)
   - Recommendation: Use 8px grid system

3. **Logo Too Small** [Low Priority]
   - Current: 80px width
   - Recommendation: 120px for better visibility

[... 9 more design issues]

**Visual Comparison:**
- Side-by-side: Current vs. Proposed
- Screenshot with issues highlighted

---

#### Tab 2: SEO Analysis

**Strengths:**
- ✓ Fast page load (< 3s)
- ✓ Mobile-friendly
- ✓ Clean URL structure
- ✓ Sitemap present

**Issues (8 issues):**
1. **Missing H1 Tag** [Critical]
   - No H1 found on homepage
   - Fix: Add H1 with primary keyword

2. **Thin Meta Description** [High]
   - Current: 45 characters
   - Recommendation: 150-160 characters
   - Suggested: "Acme Corp provides professional web design services..."

3. **Missing Alt Text** [High]
   - 8 images missing alt attributes
   - Affects accessibility and SEO

[... 5 more SEO issues]

**Keyword Analysis:**
- Primary keyword: "web design services"
- Density: 0.8% (good)
- Related keywords found: design, website, portfolio

---

#### Tab 3: Performance Analysis

**Metrics:**
- **Load Time:** 3.2s (target: < 2s)
- **First Contentful Paint:** 1.8s
- **Time to Interactive:** 4.1s (target: < 3.5s)
- **Total Page Size:** 2.4 MB (target: < 1.5 MB)
- **Requests:** 87 (target: < 50)

**Issues (15 issues):**
1. **Unoptimized Images** [Critical]
   - 12 images not optimized
   - Potential savings: 1.2 MB (50%)
   - Fix: Convert to WebP, compress

2. **No Lazy Loading** [High]
   - All images load immediately
   - Fix: Implement lazy loading

3. **Large JavaScript Bundles** [High]
   - main.js: 487 KB
   - vendor.js: 823 KB
   - Fix: Code splitting, tree shaking

[... 12 more performance issues]

**Charts:**
- Load time waterfall
- Bundle size breakdown (pie chart)
- Before/after comparison

---

#### Tab 4: Accessibility Analysis

**WCAG Compliance:** Level A partially compliant

**Issues (6 issues):**
1. **Missing ARIA Labels** [High]
   - 4 buttons without labels
   - Screen readers can't identify purpose

2. **Low Color Contrast** [High]
   - 15 elements below WCAG AA threshold

3. **Keyboard Navigation Issues** [Medium]
   - Cannot tab through navigation menu
   - Fix: Add tabindex and focus styles

[... 3 more accessibility issues]

---

#### Tab 5: Improvement Plan

**AI-Generated Roadmap:**

**Summary Stats:**
- Total improvements: 41
- Critical: 3
- High: 12
- Medium: 18
- Low: 8
- Quick wins: 8 (< 1 hour each)
- Estimated total time: 2-3 weeks
- Estimated cost: $3,500-$5,000

**Improvement Cards (sorted by priority):**

**Improvement #1:**
- **Title:** Optimize Image Assets
- **Category:** Performance
- **Priority:** Critical
- **Impact:** "Reduce page load by 40%, improve SEO ranking"
- **Difficulty:** Easy
- **Time:** 2-4 hours
- **Current State:**
  - 12 unoptimized PNG/JPG images
  - Total size: 2.1 MB
- **Proposed Change:**
  - Convert to WebP format
  - Implement responsive images (srcset)
  - Add lazy loading
- **Code Example:**
  ```html
  <!-- Before -->
  <img src="hero.jpg" alt="Hero">

  <!-- After -->
  <img
    src="hero.webp"
    srcset="hero-400.webp 400w, hero-800.webp 800w"
    loading="lazy"
    alt="Hero image showing our team"
  >
  ```
- **Resources:**
  - [ImageOptim tool](...)
  - [WebP conversion guide](...)
- **Dependencies:** None
- **Checkbox:** ☑ Include in demo site

**Improvement #2:**
- **Title:** Fix Color Contrast for Accessibility
- **Category:** Accessibility
- **Priority:** Critical
- **Impact:** "WCAG AA compliance, better readability"
- **Difficulty:** Easy
- **Time:** 1 hour
- **Current State:**
  - 15 elements with contrast ratio < 4.5:1
  - Fails WCAG AA
- **Proposed Change:**
  - Update text color from #666 to #444
  - Update background colors
- **Code Example:**
  ```css
  /* Before */
  .text { color: #666; }

  /* After */
  .text { color: #444; } /* Contrast ratio: 8.6:1 ✓ */
  ```
- **Checkbox:** ☑ Include in demo site

[... 39 more improvements listed]

**Filter/Sort Options:**
- Filter by: Priority | Category | Difficulty
- Sort by: Priority | Impact | Time | Cost

**Bulk Actions:**
- "Select All Quick Wins"
- "Select All Critical"
- "33 improvements selected"

**Bottom Action Bar:**
- **Selected Improvements:** 33 / 41
- **Estimated Demo Generation Time:** 15-20 minutes
- **AI Cost:** $2.50
- **Button:** "Generate Demo Site →" (primary, large)

**User Action:** Review improvements, select 33 improvements, click "Generate Demo Site"

---

### Flow 2B: Demo Site Generation

#### Screen 1: Demo Site Configuration

**Modal:** "Configure Demo Site Generation"

**Form Fields:**

1. **Framework:** (radio cards)
   - ◉ **React** - "Modern, component-based"
   - ○ **Next.js** - "React with SSR/SSG"
   - ○ **HTML/CSS/JS** - "Simple, no framework"

2. **Design System:** (dropdown)
   - TailwindCSS (default)
   - Bootstrap
   - Material UI
   - Custom CSS

3. **Features to Include:** (checkboxes)
   - ☑ Responsive design (mobile/tablet/desktop)
   - ☑ SEO optimization (meta tags, structured data)
   - ☑ Performance optimizations (lazy loading, code splitting)
   - ☑ Accessibility features (ARIA, keyboard nav)
   - ☑ Analytics integration (Google Analytics)
   - ☑ Contact form

4. **Code Style:** (radio)
   - ◉ Include comments explaining improvements
   - ○ Production-ready (no comments)

5. **Deployment:** (toggle)
   - ☑ Auto-deploy to preview (Vercel)
   - ○ Generate files only

6. **AI Model Selection:** (dropdown with info)
   - ◉ Claude 4.5 Sonnet (Best quality) - $0.003/1K tokens
   - ○ GPT-4 Turbo (Fast) - $0.01/1K tokens
   - ○ DeepSeek (Budget) - $0.00014/1K tokens
   - Info: "AI-GYM will track which model produces best results"

**Cost Breakdown:**
- AI code generation: $2.50
- Vercel deployment: Free
- **Total: $2.50**

**Buttons:**
- "Cancel"
- "Generate Demo Site" (primary)

**User Action:** Keep defaults (React, TailwindCSS, Claude 4.5), click "Generate"

**State Change:**
- Modal closes
- Redirect to generation progress page

---

#### Screen 2: Demo Site Generation Progress

**URL:** `/demo-sites/[demo_id]/generating`

**Real-time Updates via WebSocket**

**Header:**
- "Generating Demo Site for Acme Corp"
- Status: "Generating" (animated)
- Overall Progress: 55%

**Step Progress:**
1. ✓ Analyzing improvement plan (completed)
2. ✓ Selecting AI model (Claude 4.5 Sonnet) (completed)
3. 🔄 Generating code (in progress) - 55%
   - Sub-steps:
     - ✓ Component structure planned
     - ✓ Homepage generated
     - 🔄 About page generating...
     - ⏳ Services page queued
     - ⏳ Contact page queued
4. ⏳ Validating generated code (pending)
5. ⏳ Deploying to preview (pending)

**Live Code Preview:**
- Shows generated files as they're created
- File tree (left):
  - src/
    - ✓ App.tsx
    - ✓ components/
      - ✓ Header.tsx
      - 🔄 Hero.tsx (generating...)
      - ⏳ Services.tsx
    - ⏳ styles/
- Code viewer (right):
  - Shows currently generating file
  - Syntax highlighted
  - Comments explaining improvements inline

**Activity Log:**
- [12:40:01] Started code generation
- [12:40:05] AI model selected: Claude 4.5 Sonnet
- [12:40:08] Prompt sent (2,450 tokens)
- [12:40:15] Homepage component generated (487 lines)
- [12:40:22] Applied improvement: Optimized images
- [12:40:25] Applied improvement: Fixed color contrast
- [12:40:30] About page component generating...

**Tokens Used:**
- Input: 3,250 tokens ($0.009)
- Output: 8,750 tokens ($0.026)
- Total cost: $0.035 (updating live)

**Estimated Time Remaining:** 8 minutes

---

#### Screen 3: Code Validation

**Progress:**
- Step 4: ✓ Validating generated code (in progress)

**Validation Checks:**
1. ✓ **Syntax Valid** - TypeScript/React syntax check passed
2. ✓ **Required Files Present** - package.json, App.tsx, index.html found
3. 🔄 **No Placeholders** - Checking for TODOs, FIXMEs...
   - ⚠️ Found 2 placeholders
   - Automatically fixing...
   - ✓ Fixed
4. 🔄 **Code Quality** - Running ESLint...
   - 3 warnings (non-blocking)
5. ✓ **Build Test** - Attempting build...
   - ✓ Build successful (dist/ created)
6. ✓ **Accessibility Audit** - Checking ARIA, contrast...
   - ✓ WCAG AA compliant
7. ✓ **Performance Check** - Analyzing bundle size...
   - Bundle size: 245 KB (good)

**Validation Result:**
- ✓ All checks passed
- ⚠️ 3 non-blocking warnings
- Build successful
- Ready to deploy

---

#### Screen 4: Deployment

**Progress:**
- Step 5: 🔄 Deploying to preview (in progress)

**Deployment Steps:**
1. ✓ Creating temporary Git repository
2. ✓ Committing generated code
3. 🔄 Deploying to Vercel...
   - ✓ Build started
   - ✓ Installing dependencies (npm install)
   - ✓ Building production bundle
   - 🔄 Deploying to CDN...
4. ⏳ Generating preview URL

**Log:**
```
[Vercel] Building project...
[Vercel] ✓ Installed dependencies (23 packages)
[Vercel] ✓ Built in 12.3s
[Vercel] ✓ Deployed to CDN
[Vercel] ✓ Preview URL: https://acme-demo-x7k3.vercel.app
```

**Deployment Complete!**

---

#### Screen 5: Demo Site Complete

**URL:** `/demo-sites/[demo_id]`

**Success Banner:**
"✓ Demo site successfully generated and deployed!"

**Header:**
- Demo Site: "Acme Corp - Improved"
- Preview URL: https://acme-demo-x7k3.vercel.app (clickable)
- Actions: "View Live" | "Edit Code" | "Create Video" | "Share" | "Download Files"

**Stats Cards:**
1. **Generation Time**
   - 14 minutes 32 seconds
2. **AI Cost**
   - $2.47 (Claude 4.5 Sonnet)
3. **Lines of Code**
   - 3,847 lines
4. **Files Generated**
   - 42 files

**Tabs:**

#### Tab 1: Preview

**Split View:**
- **Left: Original Site** (iframe)
  - Shows original acmecorp.com
- **Right: Demo Site** (iframe)
  - Shows new demo site
- **Sync Scroll:** Both iframes scroll together
- **Responsive Toggle:** Desktop | Tablet | Mobile
- **Zoom:** 50% | 75% | 100% | 125%

**Improvement Highlights (overlay):**
- Clickable hotspots on demo showing improvements
- Click hotspot → tooltip explaining the change
- Example: Click hero image → "Optimized to WebP, reduced size by 65%"

---

#### Tab 2: Code

**File Explorer (left sidebar):**
- src/
  - App.tsx (487 lines)
  - components/
    - Header.tsx (124 lines)
    - Hero.tsx (156 lines)
    - Services.tsx (234 lines)
    - Footer.tsx (89 lines)
  - styles/
    - globals.css (342 lines)
  - utils/
    - seo.ts (67 lines)
- package.json
- vite.config.ts
- README.md

**Code Viewer (right):**
- Syntax highlighting
- Line numbers
- Collapsible sections
- Search in file
- Download file button
- Copy to clipboard

**Comments in Code:** (example)
```tsx
// ✨ IMPROVEMENT: Fixed color contrast for accessibility
// Before: text-gray-500 (#6B7280, contrast 3.5:1)
// After: text-gray-700 (#374151, contrast 8.6:1) ✓ WCAG AA
<p className="text-gray-700">
  Welcome to Acme Corp
</p>

// ✨ IMPROVEMENT: Lazy loading images for performance
// Reduces initial page load by 40%
<img
  src={heroImage}
  alt="Professional web design services"
  loading="lazy"
  className="w-full h-auto"
/>
```

**Bulk Actions:**
- "Download All Files (.zip)"
- "Copy All to Clipboard"
- "Push to GitHub"

---

#### Tab 3: Improvements Applied

**List of all improvements from analysis that were implemented:**

Shows 33 improvement cards (same format as analysis) with:
- ✓ Checkmark (implemented)
- Before/After code snippets
- Impact metrics where available

**Example Card:**
**✓ Image Optimization**
- **Before:** 12 PNG images, 2.1 MB total
- **After:** 12 WebP images, 487 KB total (77% reduction)
- **Impact:** Page load reduced from 3.2s → 1.4s

---

#### Tab 4: Performance Comparison

**Metrics Table:**
| Metric | Original | Demo | Improvement |
|--------|----------|------|-------------|
| Overall Score | 68 | 94 | +26 ▲ |
| Design Score | 72 | 98 | +26 ▲ |
| SEO Score | 81 | 96 | +15 ▲ |
| Performance | 54 | 89 | +35 ▲ |
| Accessibility | 65 | 95 | +30 ▲ |
| Load Time | 3.2s | 1.4s | -56% ▼ |
| Page Size | 2.4 MB | 687 KB | -71% ▼ |
| Requests | 87 | 34 | -61% ▼ |

**Charts:**
- Radar chart comparing all scores
- Bar chart showing load time improvement
- Line chart showing Lighthouse score trends

---

#### Tab 5: Deployment

**Deployment Status:**
- ✓ Deployed to Vercel
- Preview URL: https://acme-demo-x7k3.vercel.app
- Deployed: 5 minutes ago
- Status: Active

**Deployment Options:**
- **Change Deployment Provider:**
  - Current: Vercel
  - Options: Netlify | GitHub Pages | Custom
- **Custom Domain:**
  - Input: "acme-demo.yourcompany.com"
  - Button: "Configure Domain"
- **Environment Variables:**
  - Add API keys, etc.
- **Redeploy:** Button to redeploy with changes

**Analytics (if available):**
- Views: 0
- Unique visitors: 0
- Avg. session: 0s
- Bounce rate: 0%

---

#### Tab 6: Share & Export

**Sharing Options:**

1. **Preview Link:**
   - URL: https://acme-demo-x7k3.vercel.app
   - Copy button
   - QR code (for mobile)

2. **Embed Code:**
   ```html
   <iframe src="https://acme-demo-x7k3.vercel.app" width="100%" height="600"></iframe>
   ```

3. **Share via Email:**
   - To: (email input)
   - Message: (textarea)
   - Include: ☑ Preview link ☑ Performance comparison ☑ Code download link
   - Button: "Send Email"

4. **Social Sharing:**
   - LinkedIn | Twitter | Facebook buttons
   - Auto-generated message: "Check out this improved website demo..."

**Export Options:**

1. **Download Files:**
   - "Download as .zip" button
   - File size: 2.4 MB

2. **Push to GitHub:**
   - Repo name: (input) "acme-demo"
   - Visibility: Public | Private
   - Button: "Create Repository"

3. **Export Report (PDF):**
   - Includes: Analysis, improvements, code samples, performance comparison
   - Button: "Generate PDF Report"

---

**Bottom Action Bar:**
- "← Back to Demo Sites"
- "Create Video from This Demo →" (primary, large)

**User Action:** Click "Create Video from This Demo"

**Transition:** Redirect to video creation flow

---

## Journey 3: Demo Site → Video Creation

**Goal:** Generate a Loom-style video walkthrough of the demo site with AI voiceover explaining the improvements.

### Entry Point
- From demo site detail page → "Create Video" button
- Navigation → "Videos" → "+ New Video"

---

### Flow 3A: Video Script Generation

#### Screen 1: Select Demo Site

**URL:** `/videos/new`

**If coming from demo site:** Pre-selected

**UI Components:**
- **Header:** "Create Demo Video"
- **Demo Site Selection:** (if not pre-selected)
  - Dropdown showing all completed demo sites
  - Shows: Thumbnail, Lead name, Created date
- **Video Style:** (radio cards)
  - ◉ **Professional** - "Corporate tone, feature-focused"
  - ○ **Casual** - "Friendly tone, storytelling"
  - ○ **Technical** - "Developer-focused, code details"
- **Duration:** (slider)
  - Range: 30s - 5 minutes
  - Default: 90 seconds
  - Help: "Longer videos cost more"
- **Key Points to Cover:** (checkboxes)
  - ☑ Design improvements
  - ☑ Performance optimizations
  - ☑ SEO enhancements
  - ☑ Accessibility features
  - ☑ Code quality
  - ☑ Mobile responsiveness
- **Call to Action:** (text input)
  - Placeholder: "e.g., Schedule a consultation at..."
  - Help: "What should viewers do next?"
- **Button:** "Generate Script →"

**User Action:** Keep defaults, add CTA "Contact us at hello@yourcompany.com", click "Generate Script"

---

#### Screen 2: Script Generation Progress

**URL:** `/videos/[video_id]/script-generation`

**Progress Indicator:**
- "Generating Video Script..."
- Progress: 40%

**Steps:**
1. ✓ Loading demo site data
2. ✓ Analyzing improvements
3. 🔄 AI script generation (Claude 4.5)
4. ⏳ Generating timecodes
5. ⏳ Validating script

**Live Preview:** (shows script as it's generated)
```
[INTRO - 0:00]
"Hi! Today I'll show you the transformed Acme Corp website.
We've made some incredible improvements that make this site
faster, more accessible, and better for SEO."

[DESIGN - 0:10]
"Let's start with the design. Notice the improved color contrast..."
```

**Duration:** ~30 seconds

---

#### Screen 3: Review & Edit Script

**URL:** `/videos/[video_id]/script`

**Header:**
- "Video Script for Acme Corp Demo"
- Estimated Duration: 1 minute 42 seconds
- Actions: "Regenerate" | "Edit" | "Approve"

**Script Editor:**
- **Timeline View** (left):
  - Visual timeline showing segments
  - Draggable segments to reorder
  - Duration per segment

**Segment List:**

**Segment 1: Intro (0:00 - 0:15)**
- **Narration:**
  ```
  Hi! I'm excited to show you the transformed Acme Corp website.
  We've made incredible improvements that make this site faster,
  more accessible, and much better for SEO. Let's dive in!
  ```
- **Action:** Show homepage, zoom in slightly
- **Duration:** 15 seconds
- **Edit** | **Delete** buttons

**Segment 2: Design Improvements (0:15 - 0:45)**
- **Narration:**
  ```
  First, let's talk design. Notice the improved color contrast -
  all text is now easily readable and meets accessibility standards.
  We've also fixed the inconsistent spacing using an 8-pixel grid system,
  giving the site a much cleaner, more professional look.
  ```
- **Action:** Scroll down homepage, highlight contrast changes
- **Duration:** 30 seconds

**Segment 3: Performance (0:45 - 1:15)**
- **Narration:**
  ```
  Now, performance. The original site took over 3 seconds to load.
  We've optimized all images to WebP format and implemented lazy loading,
  bringing load time down to just 1.4 seconds. That's a 56% improvement!
  ```
- **Action:** Show performance metrics overlay, scroll through images
- **Duration:** 30 seconds

**Segment 4: Mobile Responsiveness (1:15 - 1:35)**
- **Narration:**
  ```
  The site is now fully responsive. Watch how beautifully it adapts
  from desktop to tablet to mobile. Every element adjusts perfectly
  to ensure a great experience on any device.
  ```
- **Action:** Resize viewport to show responsive behavior
- **Duration:** 20 seconds

**Segment 5: Call to Action (1:35 - 1:42)**
- **Narration:**
  ```
  Want improvements like these for your website?
  Contact us at hello@yourcompany.com. Thanks for watching!
  ```
- **Action:** Show contact form, fade out
- **Duration:** 7 seconds

**Script Editor Features:**
- Rich text editing for narration
- Add/remove segments
- Reorder segments (drag and drop)
- Adjust segment duration
- Add visual cues (zoom, scroll, highlight)
- Preview button (text-to-speech preview)

**Bottom Stats:**
- Total duration: 1:42
- Word count: 187
- Estimated voiceover cost: $0.45
- Estimated video generation time: 5 minutes

**Buttons:**
- "← Back"
- "Save Draft"
- "Continue to Voiceover →" (primary)

**User Action:** Review script, make minor edits, click "Continue to Voiceover"

---

### Flow 3B: Voiceover Generation

#### Screen 1: Voice Selection

**URL:** `/videos/[video_id]/voiceover`

**Header:** "Select Voice for Narration"

**Voice Options (cards with play button):**

**Featured Voices:**

1. **Marcus** [▶️ Preview]
   - Gender: Male
   - Accent: American (neutral)
   - Tone: Professional, confident
   - Best for: Corporate, B2B
   - Sample: [waveform animation]

2. **Sarah** [▶️ Preview]
   - Gender: Female
   - Accent: American (neutral)
   - Tone: Friendly, approachable
   - Best for: General audiences

3. **James** [▶️ Preview]
   - Gender: Male
   - Accent: British
   - Tone: Authoritative, sophisticated
   - Best for: Premium services

4. **Emma** [▶️ Preview]
   - Gender: Female
   - Accent: Australian
   - Tone: Casual, energetic
   - Best for: Startups, creative

[+ 20 more voices...]

**Voice Settings:**
- **Speed:** (slider)
  - 0.75x | 1.0x | 1.25x | 1.5x
  - Default: 1.0x
- **Pitch:** (slider)
  - Lower | Normal | Higher
- **Emphasis:** (slider)
  - Monotone | Neutral | Expressive

**Preview:**
- "Test Voice" button
- Plays first segment with selected voice

**Cost Estimate:**
- Voice: Marcus (ElevenLabs)
- Characters: 832
- Cost: $0.42

**Buttons:**
- "← Back to Script"
- "Generate Voiceover →" (primary)

**User Action:** Select "Marcus", keep default settings, click "Generate Voiceover"

---

#### Screen 2: Voiceover Generation Progress

**URL:** `/videos/[video_id]/voiceover-generation`

**Progress:**
- "Generating Voiceover..."
- Progress: 60%

**Steps:**
1. ✓ Script prepared (5 segments)
2. ✓ Voice selected (Marcus - ElevenLabs)
3. 🔄 Generating audio (60%)
   - ✓ Segment 1: Intro (done)
   - ✓ Segment 2: Design (done)
   - 🔄 Segment 3: Performance (generating...)
   - ⏳ Segment 4: Mobile
   - ⏳ Segment 5: CTA
4. ⏳ Stitching audio segments
5. ⏳ Quality check

**Activity Log:**
- [12:50:01] Started voiceover generation
- [12:50:03] Segment 1 complete (3.2s audio)
- [12:50:08] Segment 2 complete (6.8s audio)
- [12:50:12] Segment 3 generating...

**Duration:** ~1-2 minutes

---

#### Screen 3: Voiceover Review

**URL:** `/videos/[video_id]/voiceover-review`

**Header:**
- "Review Voiceover"
- Total Duration: 1:42
- Cost: $0.42

**Audio Player:**
- Large waveform visualization
- Playback controls: Play/Pause, Skip 5s, Speed
- Current time / Total time
- Volume control

**Segment Timeline:**
- Visual timeline showing all segments
- Click segment to jump to that part
- Segment markers with labels

**Segment List (expandable):**
1. **Intro (0:00 - 0:15)** [▶️ Play]
   - Transcript displayed
   - "Regenerate This Segment" button
2. **Design (0:15 - 0:45)** [▶️ Play]
3. **Performance (0:45 - 1:15)** [▶️ Play]
4. **Mobile (1:15 - 1:35)** [▶️ Play]
5. **CTA (1:35 - 1:42)** [▶️ Play]

**Quality Check:**
- ✓ No audio clipping
- ✓ Consistent volume
- ✓ Pronunciation correct
- ✓ Natural pacing

**Actions:**
- "Regenerate Segment" (if unhappy with specific segment)
- "Try Different Voice" (back to voice selection)
- "Download Audio" (.mp3)

**Buttons:**
- "← Back"
- "Approve & Continue to Recording →" (primary)

**User Action:** Listen to voiceover, approve, click "Continue to Recording"

---

### Flow 3C: Screen Recording

#### Screen 1: Recording Configuration

**URL:** `/videos/[video_id]/recording-config`

**Header:** "Configure Screen Recording"

**Settings:**

1. **Recording Quality:** (radio)
   - ◉ 1080p (Full HD) - Recommended
   - ○ 720p (HD) - Faster processing
   - ○ 4K - Best quality, slower

2. **Frame Rate:** (radio)
   - ○ 24 fps - Cinematic
   - ◉ 30 fps - Standard (recommended)
   - ○ 60 fps - Smooth (larger file)

3. **Recording Actions:** (auto-generated from script)
   - **Segment 1:** Load homepage, zoom 110%
   - **Segment 2:** Scroll down 500px, highlight contrast
   - **Segment 3:** Show devtools performance tab
   - **Segment 4:** Resize viewport (1920→768→375)
   - **Segment 5:** Navigate to contact form
   - [Edit Actions] button

4. **Annotations:** (checkboxes)
   - ☑ Show cursor
   - ☑ Highlight clicks
   - ☑ Show improvement callouts
   - ☐ Show code snippets overlay

5. **Branding:** (optional)
   - **Watermark:** Upload logo
   - **Intro Slide:** (toggle)
     - Company logo + tagline
   - **Outro Slide:** (toggle)
     - CTA + contact info

**Preview Script Actions:**
- Shows timeline of actions synchronized with voiceover
- Can drag actions to adjust timing

**Buttons:**
- "← Back"
- "Start Recording →" (primary)

**User Action:** Keep defaults, click "Start Recording"

---

#### Screen 2: Recording in Progress

**URL:** `/videos/[video_id]/recording`

**⚠️ "Do not close this window while recording"**

**Progress:**
- "Recording Screen..."
- Overall: 45%

**Live Preview:**
- Shows the browser being automated in real-time
- Puppeteer controlling a headless Chrome instance
- User can see exactly what's being recorded

**Current Action:**
- Segment 2 of 5
- Action: "Scrolling down homepage"
- Voiceover playing: "Notice the improved color contrast..."

**Steps:**
1. ✓ Browser launched
2. ✓ Demo site loaded
3. 🔄 Recording segment 2 (45%)
   - ✓ Segment 1: Intro complete (15s)
   - 🔄 Segment 2: Design (in progress)
   - ⏳ Segment 3: Performance
   - ⏳ Segment 4: Mobile
   - ⏳ Segment 5: CTA
4. ⏳ Processing video
5. ⏳ Compositing final video

**Activity Log:**
- [13:00:01] Started screen recording
- [13:00:03] Browser launched (Chromium)
- [13:00:05] Loaded demo site
- [13:00:08] Segment 1 recorded (15s)
- [13:00:25] Segment 2 recording...
- [13:00:35] Scroll action executed
- [13:00:40] Highlight annotation added

**Duration:** ~2-3 minutes

---

### Flow 3D: Video Composition

#### Screen 1: Composing Final Video

**URL:** `/videos/[video_id]/composition`

**Progress:**
- "Composing Final Video..."
- Progress: 70%

**Steps:**
1. ✓ Screen recording complete (1:42)
2. ✓ Voiceover audio ready (1:42)
3. 🔄 Combining video + audio (FFmpeg)
4. ⏳ Adding annotations/overlays
5. ⏳ Rendering final video
6. ⏳ Uploading to CDN

**FFmpeg Output (for devs):**
```
[ffmpeg] Input #1: screen-recording.webm (1920x1080, 30fps)
[ffmpeg] Input #2: voiceover.mp3 (44.1kHz stereo)
[ffmpeg] Encoding to H.264...
[ffmpeg] Progress: 70% (72s / 102s)
[ffmpeg] Estimated time remaining: 45 seconds
```

**Technical Details:**
- Video codec: H.264
- Audio codec: AAC
- Resolution: 1920x1080
- Frame rate: 30fps
- Bitrate: 5 Mbps
- Estimated file size: 12 MB

**Duration:** ~2-3 minutes

---

#### Screen 2: Video Complete!

**URL:** `/videos/[video_id]`

**Success Banner:**
"✓ Video successfully created and uploaded!"

**Header:**
- Video: "Acme Corp Demo Walkthrough"
- Duration: 1:42
- Actions: "Download" | "Share" | "Re-generate" | "Create Another"

**Stats Cards:**
1. **Generation Time**
   - 8 minutes 15 seconds
2. **Total Cost**
   - Script: $0.15 (AI)
   - Voiceover: $0.42 (ElevenLabs)
   - Recording: $0.20 (compute)
   - Total: $0.77
3. **File Size**
   - 11.8 MB (H.264)
4. **Quality**
   - 1080p, 30fps

**Video Player:**
- Large, professional video player
- Play/Pause, Seek, Volume
- Fullscreen, Picture-in-Picture
- Playback speed (0.5x - 2x)
- Captions/subtitles (auto-generated)
- Download quality options (1080p, 720p, 480p)

**Tabs:**

#### Tab 1: Video

Shows the video player (already described above)

---

#### Tab 2: Analytics

**Views & Engagement:**
- Views: 0
- Unique viewers: 0
- Avg. watch time: 0%
- Completion rate: 0%
- Replays: 0

**Viewer Behavior:**
- Drop-off points (heatmap)
- Most rewatched segments
- Average watch time per segment

**Chart:** Watch time graph (time on X-axis, % viewers on Y-axis)

---

#### Tab 3: Share & Embed

**Sharing Options:**

1. **Direct Link:**
   - URL: https://cdn.yourcompany.com/videos/acme-corp-demo.mp4
   - Copy button

2. **Embed Code:**
   ```html
   <video width="640" height="360" controls>
     <source src="https://cdn.yourcompany.com/videos/acme-corp-demo.mp4" type="video/mp4">
   </video>
   ```

3. **Email Integration:**
   - "Add to Email Campaign" button
   - Embeds video in email outreach

4. **Social Sharing:**
   - LinkedIn | Twitter | Facebook buttons
   - Auto-generates preview card with thumbnail

**Download Options:**
- Download video (MP4)
- Download audio only (MP3)
- Download thumbnail (PNG)
- Download transcript (TXT)

---

#### Tab 4: Transcript

**Auto-generated from voiceover:**

```
[0:00] Hi! I'm excited to show you the transformed Acme Corp website.
We've made incredible improvements that make this site faster,
more accessible, and much better for SEO. Let's dive in!

[0:15] First, let's talk design. Notice the improved color contrast -
all text is now easily readable and meets accessibility standards.
We've also fixed the inconsistent spacing using an 8-pixel grid system,
giving the site a much cleaner, more professional look.

[0:45] Now, performance. The original site took over 3 seconds to load.
We've optimized all images to WebP format and implemented lazy loading,
bringing load time down to just 1.4 seconds. That's a 56% improvement!

[1:15] The site is now fully responsive. Watch how beautifully it adapts
from desktop to tablet to mobile. Every element adjusts perfectly
to ensure a great experience on any device.

[1:35] Want improvements like these for your website?
Contact us at hello@yourcompany.com. Thanks for watching!
```

**Features:**
- Search transcript
- Click timestamp → jump to that point in video
- Edit transcript
- Download as TXT/SRT/VTT

---

**Bottom Action Bar:**
- "← Back to Videos"
- "Send This Video via Email →" (primary)

**User Action:** Click "Send This Video via Email"

**Transition:** Redirect to email outreach flow

---

## Journey 4: Email Outreach & Campaign Management

**Goal:** Send personalized emails to leads with demo sites/videos attached, track engagement, and manage responses.

### Entry Points
- From video detail page → "Send via Email"
- From demo site detail page → "Send via Email"
- From lead detail page → "Send Email"
- Navigation → "Emails" → "+ New Campaign"

---

### Flow 4A: Create Email Campaign

#### Screen 1: Campaign Setup

**URL:** `/emails/campaigns/new`

**Header:** "Create Email Campaign"

**Step 1: Campaign Details**

**UI Components:**
- **Campaign Name:** (text input)
  - Placeholder: "e.g., Q1 Web Design Outreach"
  - Help: "Internal name for tracking"
- **Campaign Goal:** (dropdown)
  - Options: Lead Generation | Demo Showcase | Follow-up | Re-engagement
- **Sender Information:**
  - **From Name:** (input)
    - Default: Your Name
  - **From Email:** (dropdown)
    - Options: your verified email addresses
    - "+ Add New Email" → Email verification flow
  - **Reply-To Email:** (input, optional)
    - Different from sender if needed
- **Schedule:** (radio)
  - ◉ Send immediately
  - ○ Schedule for later (date/time picker)
  - ○ Send as drip campaign (multiple emails over time)

**Buttons:**
- "Cancel"
- "Next: Recipients →" (primary)

**User Action:** Name campaign "Acme Corp Demo Showcase", keep defaults, click "Next"

---

#### Screen 2: Select Recipients

**UI Components:**
- **Selection Method:** (tabs)
  - Tab 1: **From Leads**
  - Tab 2: **Upload CSV**
  - Tab 3: **Manual Entry**

**Tab 1: From Leads** (active)

**Lead Filters:**
- **Source:** Craigslist | Google Maps | LinkedIn | Job Boards
- **Status:** New | Contacted | Replied | Qualified
- **Has Email?** ☑ (required)
- **Has Demo Site?** ☐
- **Has Video?** ☐
- **Tags:** (multi-select)
- **Date Added:** (date range)
- **Location:** (multi-select)
- **Search:** Free text search

**Apply Filters → Shows matching leads**

**Leads Table:**
- ☐ Select All (23 leads match)
- Columns: Name, Email, Source, Status
- Checkbox per row

**Selected Recipients:**
- **Count:** 23 leads selected
- **List Preview:** (expandable)
  - Shows first 5, "+ 18 more"
- **Deduplication:** ✓ Remove duplicates
- **Email Validation:** ✓ Verify emails before sending

**Smart Recommendations:**
💡 "15 of these leads have demo sites. Consider including demo links in your email."
💡 "8 leads have videos. Videos increase reply rate by 40%."

**Buttons:**
- "← Back"
- "Next: Email Content →" (primary)

**User Action:** Select 23 leads (those with demo sites), click "Next"

---

#### Screen 3: Email Content

**Split View:**
- **Left:** Email editor
- **Right:** Live preview

**Email Editor:**

1. **Template Selection:** (dropdown)
   - Choose from templates:
     - Blank
     - Cold Outreach
     - Demo Showcase ← Selected
     - Follow-up
     - Re-engagement
   - Or: "Load from previous campaign"

2. **Subject Line:** (text input)
   - Placeholder: Pre-filled from template
   - Default: "{{leadName}}, see how we improved {{companyName}}'s website"
   - Character counter: 52 / 70 (optimal)
   - **Personalization tokens** dropdown:
     - {{leadName}}
     - {{companyName}}
     - {{leadTitle}}
     - {{leadLocation}}
     - {{yourName}}
     - {{customField}}

3. **Preview Text:** (text input)
   - Help: "Shown in inbox preview"
   - Default: "We created a demo showing specific improvements..."
   - Character counter: 45 / 90 (optimal)

4. **Email Body:** (rich text editor)

**Template Pre-filled Content:**
```
Hi {{leadName}},

I noticed {{companyName}}'s website and saw some opportunities
for improvement. I took the liberty of creating a demo site
showing what these enhancements could look like.

Here's what we improved:
• Design & visual contrast (WCAG compliant)
• Page load speed (56% faster)
• SEO optimization
• Mobile responsiveness

[CTA Button: View Your Demo Site]

I also created a short video walkthrough explaining each improvement:

[CTA Button: Watch Video]

Would love to hear your thoughts. Reply if you're interested
in discussing these improvements.

Best,
{{yourName}}
{{yourCompany}}
{{yourPhone}}
```

**Editor Features:**
- Bold, Italic, Underline
- Headings (H1, H2, H3)
- Bullet/numbered lists
- Links
- Images (upload or URL)
- Personalization tokens
- CTA buttons (styled)
- Variables (dynamic content)

5. **Attachments:** (optional)
   - Demo site link (auto-included)
   - Video link (auto-included)
   - PDF report
   - Custom file upload

6. **CTA Buttons:**
   - **Button 1:** "View Your Demo Site"
     - URL: {{demoSiteUrl}} (automatically personalized)
     - Style: Primary (blue)
   - **Button 2:** "Watch Video"
     - URL: {{videoUrl}}
     - Style: Secondary (gray)
   - "+ Add Another CTA"

7. **Tracking:** (checkboxes)
   - ☑ Track opens (pixel tracking)
   - ☑ Track clicks (link wrapping)
   - ☑ Track replies (IMAP monitoring)

**Live Preview (right side):**
- Shows desktop/mobile toggle
- Renders email exactly as recipient sees it
- Personalization tokens replaced with sample data
- "Send Test Email" button

**Email Quality Score:**
- Overall: 85/100 (Good)
- ✓ Personalized subject line
- ✓ Short paragraphs (easy to read)
- ✓ Clear CTA
- ⚠️ Could improve: Add recipient's pain point
- ✓ Mobile-friendly

**Buttons:**
- "← Back"
- "Save as Template"
- "Send Test Email"
- "Next: Review & Send →" (primary)

**User Action:** Edit subject line to include lead's location, click "Send Test Email" to self, review, click "Next"

---

#### Screen 4: Review & Send

**URL:** `/emails/campaigns/review`

**Header:** "Review Campaign Before Sending"

**Campaign Summary:**

**Recipients:**
- Total: 23 recipients
- With valid emails: 23 (100%)
- Previously contacted: 0
- Unsubscribed: 0 (excluded)
- Bounced before: 0 (excluded)

**Email Details:**
- Subject: "{{leadName}}, see how we improved {{companyName}}'s website"
- Preview: "We created a demo showing specific improvements..."
- Attachments: Demo site link, Video link
- Tracking: Opens, Clicks, Replies enabled

**Personalization Preview:**
- Shows how email looks for 3 random recipients
- Ensures tokens are replaced correctly

**Compliance Check:**
- ✓ Unsubscribe link included (required)
- ✓ Physical address included (CAN-SPAM)
- ✓ No spam trigger words detected
- ✓ Sender email verified

**Sending Options:**
- **Send Rate:** (slider)
  - Send 10 emails per hour (recommended for deliverability)
  - Help: "Slower sending avoids spam filters"
- **Smart Sending:** (toggle)
  - ☑ Send during business hours only (9am-5pm recipient timezone)
  - ☑ Avoid weekends

**Cost Estimate:**
- Email sending: Free (first 1000/month)
- Tracking service: $0.02 per email
- Total: $0.46

**Buttons:**
- "← Back"
- "Save as Draft"
- "Schedule Campaign"
- "Send Now" (primary, large)

**Confirmation Modal:**
"Are you sure you want to send this campaign to 23 recipients?"
- "Cancel"
- "Yes, Send Campaign" (destructive style)

**User Action:** Click "Send Now", confirm in modal

**State Change:**
- Campaign status → "Sending"
- Redirect to campaign detail/monitoring page

---

### Flow 4B: Campaign Monitoring

#### Screen 1: Campaign Detail Page

**URL:** `/emails/campaigns/[campaign_id]`

**Header:**
- Campaign: "Acme Corp Demo Showcase"
- Status Badge: "Sending" (animated) → "Sent" when complete
- Actions: "Pause" | "View Recipients" | "Duplicate" | "Export Results"

**Real-time Stats (updating via WebSocket):**

**Overview Cards (4 cards):**
1. **Sent**
   - 23 / 23 (100%)
   - Last sent: 2 minutes ago

2. **Opened**
   - 7 (30.4%)
   - Avg. time to open: 1.5 hours

3. **Clicked**
   - 4 (17.4%)
   - Click-through rate: 17.4%

4. **Replied**
   - 2 (8.7%)
   - Response rate: 8.7%

**Performance Chart:**
- Line graph showing opens/clicks/replies over time
- X-axis: Time
- Y-axis: Count
- Multiple lines for each metric

**Engagement Timeline:**
- Live feed of recipient actions:
  - ✉️ [13:15] Email sent to John Smith
  - 👁️ [13:17] John Smith opened email
  - 🖱️ [13:18] John Smith clicked "View Demo Site"
  - 💬 [13:25] John Smith replied
  - ✉️ [13:16] Email sent to Jane Doe
  - 👁️ [13:20] Jane Doe opened email
  - [Auto-scroll, newest first]

**Recipients Table:**

**Filters:**
- All | Sent | Opened | Clicked | Replied | Bounced | Unsubscribed

**Table Columns:**
1. Recipient Name
2. Email
3. Status (badge)
   - Sent (gray)
   - Opened (blue)
   - Clicked (green)
   - Replied (purple)
   - Bounced (red)
4. Opened (count + last time)
   - "Opened 2x, last 5 min ago"
5. Clicks (count)
   - "3 clicks"
6. Last Activity
   - "Replied 2 min ago"
7. Actions (dropdown)
   - View Activity
   - Send Follow-up
   - View Reply
   - Mark as...

**Click on recipient row → Opens activity detail**

---

#### Screen 2: Recipient Activity Detail

**Modal:** "Activity for John Smith"

**Contact Info:**
- Name: John Smith
- Email: john@acmecorp.com
- Company: Acme Corp
- Lead Source: Google Maps

**Email Journey:**
- ✉️ **Sent:** Today at 1:15 PM
- 👁️ **Opened:** Today at 1:17 PM (2 minutes later)
  - Device: iPhone 14, iOS 16
  - Location: San Francisco, CA
  - Email Client: Gmail
- 👁️ **Opened Again:** Today at 1:22 PM
  - Device: MacBook Pro, macOS 13
  - Email Client: Gmail Web
- 🖱️ **Clicked:** "View Your Demo Site" at 1:18 PM
  - Visited: https://acme-demo-x7k3.vercel.app
  - Time on site: 3 minutes 24 seconds
- 🖱️ **Clicked:** "Watch Video" at 1:21 PM
  - Watched: 1:15 / 1:42 (73%)
- 💬 **Replied:** Today at 1:25 PM
  - Subject: "Re: John, see how we improved Acme Corp's website"
  - Message preview: "This looks great! Can we schedule a call..."

**Engagement Score:** 95/100 (Very High)
- Opened multiple times ✓
- Clicked both CTAs ✓
- Watched most of video ✓
- Replied positively ✓

**Suggested Next Steps:**
💡 "High engagement! Recommended action: Schedule a call"
- "Send Follow-up Email"
- "Mark as Qualified Lead"
- "Add to Sales Pipeline"

**Reply Preview:**
```
From: John Smith <john@acmecorp.com>
Subject: Re: John, see how we improved Acme Corp's website
Date: Today at 1:25 PM

This looks great! Can we schedule a call to discuss
implementing these improvements? I'm available this week.

Best,
John
```

**Quick Actions:**
- "Reply" (opens email composer)
- "Mark as Qualified"
- "Schedule Call" (calendar integration)

**User Action:** Click "Reply" to respond

---

### Flow 4C: Managing Replies (Conversation AI Integration)

#### Screen 1: Reply to Email

**Modal:** "Reply to John Smith"

**Context Panel (left):**
- Original email thread
- Lead information
- Demo site link
- Video link
- Previous interactions

**Reply Composer (right):**

**AI-Generated Response Suggestions:**

💡 "AI suggested 3 responses based on conversation context:"

**Suggestion 1: Professional & Scheduled** ⭐ Recommended
```
Hi John,

Great to hear you're interested! I'd be happy to discuss
these improvements in detail.

I have availability this Thursday 2-4pm or Friday 10am-12pm.
Would either of those work for you?

Looking forward to our conversation.

Best,
[Your Name]
```
- Tone: Professional
- Includes: Calendar availability
- Approval rating: 92% (AI-GYM score)
- "Use This Response" button

**Suggestion 2: Casual & Open-Ended**
```
Hey John!

So glad you liked the demo!

When works best for you for a quick call? I'm pretty
flexible this week.

Cheers,
[Your Name]
```
- Tone: Casual
- "Use This Response" button

**Suggestion 3: Detailed & Technical**
```
Hi John,

Absolutely! I'd love to walk through the technical
implementation of these improvements...
[longer response]
```
- Tone: Technical
- "Use This Response" button

**Or:**
- "Write Custom Response" (blank composer)
- "Edit Suggestion" (start from suggestion)

**Reply Composer Features:**
- Rich text editor
- Personalization tokens
- Attach files
- Include calendar invite
- Schedule send
- Track opens/clicks

**User Action:** Click "Use This Response" on Suggestion 1, edit slightly, click "Send"

**State Change:**
- Email sent
- Conversation status → "Replied"
- Activity logged in timeline
- AI learns from selection (AI-GYM feedback)

---

### Flow 4D: Email Campaign Analytics

#### Screen: All Campaigns

**URL:** `/emails/campaigns`

**Header:**
- "Email Campaigns"
- "+ New Campaign" button
- Filters: All | Active | Scheduled | Completed | Drafts

**Stats Overview (cards):**
1. **Total Campaigns:** 12
2. **Emails Sent:** 1,247
3. **Avg. Open Rate:** 32.5%
4. **Avg. Reply Rate:** 9.2%

**Campaigns Table:**

**Columns:**
1. Campaign Name
2. Status (badge)
3. Recipients
4. Sent
5. Opened (% + bar graph)
6. Clicked (% + bar graph)
7. Replied (% + bar graph)
8. Created
9. Actions

**Example Row:**
- Name: "Acme Corp Demo Showcase"
- Status: Completed ✓
- Recipients: 23
- Sent: 23 (100%)
- Opened: 7 (30.4%) [████░░░░░░]
- Clicked: 4 (17.4%) [███░░░░░░░]
- Replied: 2 (8.7%) [██░░░░░░░░]
- Created: Today
- Actions: View | Duplicate | Export

**Charts:**
- Campaign performance over time
- Best performing subject lines
- Optimal send times
- Reply rate by lead source

---

## Journey 5: Conversation AI & Response Management

**Goal:** Use AI to manage email conversations, suggest responses, and automate follow-ups while keeping human in the loop.

### Entry Points
- Email reply received → Notification
- Navigation → "Conversations"
- Lead detail page → "Conversations" tab

---

### Flow 5A: Viewing Conversations

#### Screen: Conversations Page

**URL:** `/conversations`

**Header:**
- "Conversations"
- Search bar: "Search conversations..."
- Filters: (dropdown) All | Active | Pending Response | AI Suggested | Archived

**Stats Cards:**
1. **Active Conversations:** 34
2. **Pending Your Response:** 12
3. **AI Suggestions:** 8
4. **Avg. Response Time:** 2.4 hours

**Conversation List (inbox-style):**

**Filters Sidebar (left):**
- **Status:**
  - ☐ New (5)
  - ☑ Active (34)
  - ☐ Waiting for reply (12)
  - ☐ Qualified (8)
  - ☐ Closed (45)
- **Has AI Suggestion:** ☑ (8)
- **Lead Source:**
  - ☐ Craigslist
  - ☐ Google Maps
  - etc.
- **Sentiment:**
  - ☐ Positive 😊
  - ☐ Neutral 😐
  - ☐ Negative ☹️
- **Date Range:** (picker)

**Conversation List (center/right):**

**Columns/Cards:**

**Conversation 1:** [Has AI suggestion badge]
- **From:** John Smith (Acme Corp)
- **Subject:** "Re: Demo site improvements"
- **Last Message:** "This looks great! Can we schedule..."
- **Sentiment:** 😊 Positive
- **Status:** Active (green badge)
- **AI Suggestion:** Available (blue badge)
- **Last Activity:** 5 minutes ago
- **Unread:** 1 new message (bold)
- Click to open →

**Conversation 2:**
- **From:** Jane Doe (XYZ Company)
- **Subject:** "Questions about pricing"
- **Last Message:** "What are your rates for..."
- **Sentiment:** 😐 Neutral
- **Status:** Waiting for response (yellow badge)
- **AI Suggestion:** Available
- **Last Activity:** 2 hours ago

[... more conversations]

**Sort:** Recent Activity | Unread First | AI Suggestions First

**User Action:** Click on John Smith conversation

---

#### Screen: Conversation Detail

**URL:** `/conversations/[conversation_id]`

**Layout:** 3-column

**Left Column: Conversation Thread**

**Header:**
- Contact: John Smith (Acme Corp)
- Status dropdown: Active → [Qualified | Closed | Spam]
- Actions: Archive | Mark as Spam | Forward

**Thread (email-style):**

**Message 1 (outbound):**
- **From:** You
- **Date:** Today at 1:15 PM
- **Subject:** "John, see how we improved Acme Corp's website"
- **Body:** [Full email content]
- **Attachments:** Demo site link, Video link
- **Tracking:** Opened 2x, Clicked 2x

**Message 2 (inbound):**
- **From:** John Smith
- **Date:** Today at 1:25 PM
- **Subject:** "Re: John, see how we improved Acme Corp's website"
- **Body:** "This looks great! Can we schedule a call to discuss implementing these improvements? I'm available this week."
- **Sentiment:** 😊 Positive (85% confidence)
- **Key Points Detected:** (AI analysis)
  - ✓ Interested in services
  - ✓ Ready to schedule call
  - ✓ Available this week
- **Suggested Response:** Available (see middle column)

**Reply Composer:** (bottom of thread)
- Text editor
- Or: "Use AI Suggestion →"

---

**Middle Column: AI Response Suggestions**

**Header:**
- "AI-Generated Response Suggestions"
- Model used: Claude 4.5 Sonnet
- Confidence: 92%

**Suggestion 1: Schedule Call** ⭐ Recommended
- **Tone:** Professional
- **Strategy:** Direct scheduling
- **Response:**
  ```
  Hi John,

  Great to hear you're interested! I'd be happy to discuss
  these improvements in detail.

  I have availability this Thursday 2-4pm or Friday 10am-12pm PST.
  Would either of those work for you?

  Looking forward to our conversation.

  Best,
  [Your Name]
  ```
- **Why recommended:**
  - Matches recipient's intent (wants to schedule)
  - Provides specific times (reduces back-and-forth)
  - Professional tone matches conversation
- **Approval Rate:** 94% (from AI-GYM historical data)
- **Actions:**
  - "Use This Response" (primary)
  - "Edit Before Sending"
  - "👍 Good" | "👎 Bad" (feedback for AI-GYM)

**Suggestion 2: Request More Info**
- **Tone:** Inquisitive
- **Strategy:** Qualify before scheduling
- **Response:**
  ```
  Hi John,

  Thanks for your interest! Before we schedule a call,
  could you share a bit more about your goals for the website?

  Specifically:
  - What's your timeline for implementing changes?
  - What's your budget range?
  - Are you the decision-maker, or should others join the call?

  This will help me prepare for our conversation.

  Best,
  [Your Name]
  ```
- **Why this option:**
  - Qualifies lead before investing time
  - Gathers information for better call prep
- **Approval Rate:** 78%
- **Actions:**
  - "Use This Response"
  - "👍 Good" | "👎 Bad"

**Suggestion 3: Send Calendar Link**
- **Tone:** Efficient
- **Strategy:** Self-scheduling
- **Response:**
  ```
  Hi John,

  Excellent! I'd love to chat.

  Feel free to grab a time that works for you on my calendar:
  [Calendly Link]

  Talk soon!
  [Your Name]
  ```
- **Why this option:**
  - Fastest scheduling (no back-and-forth)
  - Low-friction for recipient
- **Approval Rate:** 82%
- **Actions:**
  - "Use This Response"
  - "👍 Good" | "👎 Bad"

**Generate New Suggestions:**
- "Try Different Tone" dropdown: Professional | Casual | Technical
- "Regenerate with Instructions" (custom prompt)

---

**Right Column: Context & Intelligence**

**Contact Card:**
- **Name:** John Smith
- **Email:** john@acmecorp.com
- **Company:** Acme Corp
- **Title:** Marketing Director
- **Location:** San Francisco, CA
- **LinkedIn:** [profile link]
- **Phone:** (415) 555-0123
- **Tags:** web-design, high-intent, qualified
- "View Full Lead Profile" link

**Engagement History:**
- ✉️ Email sent (Demo Showcase) - Today 1:15 PM
- 👁️ Opened email 2x
- 🖱️ Clicked demo site link - 1:18 PM
- 🎥 Watched video (73% completion) - 1:21 PM
- 💬 Replied positively - 1:25 PM
- **Engagement Score:** 95/100

**Demo Site:**
- Thumbnail preview
- URL: https://acme-demo-x7k3.vercel.app
- Created: Today
- "View Demo Site" link

**Video:**
- Thumbnail preview
- Duration: 1:42
- Watch time: 73%
- "Watch Video" link

**AI Insights:**
- **Sentiment Analysis:** 😊 Very Positive (85%)
- **Intent:** High interest, ready to buy
- **Urgency:** Medium (mentioned "this week")
- **Decision-making:** Likely decision-maker (Marketing Director)
- **Recommended Action:** Schedule call soon (within 24 hours)
- **Win Probability:** 67% (based on similar leads)

**Similar Conversations:**
- Shows 3 similar conversations (same sentiment, industry, stage)
- Click to view → Learn from past responses
- Example: "Jane Doe (XYZ Co) - 85% similar - Resulted in closed deal"

**Notes:**
- Internal notes field
- Auto-saved
- Visible only to team

---

**User Action:** Click "Use This Response" on Suggestion 1

**Modal Confirmation:**
"Send this reply to John Smith?"

**Preview:**
- Shows full email as it will appear
- Personalization tokens replaced
- Signature added

**Options:**
- ☐ Track opens
- ☐ Track clicks
- ☐ Send copy to me
- **Send in:** (radio)
  - ◉ Immediately
  - ○ Schedule for: [time picker]

**Buttons:**
- "Cancel"
- "Edit First"
- "Send Now" (primary)

**User Action:** Click "Send Now"

**State Changes:**
- Reply sent
- Conversation status → "Waiting for reply"
- Activity logged
- AI learns from approval (AI-GYM feedback: +1 for Claude 4.5)
- Notification sent to John Smith

---

### Flow 5B: Sentiment Analysis & Auto-Routing

**Scenario:** Negative reply received

**Message from Lead:**
```
Subject: Re: Demo site

I'm not interested. Please remove me from your list.
```

**AI Processing (automatic):**
1. **Sentiment detected:** ☹️ Negative (95% confidence)
2. **Intent detected:** Unsubscribe request
3. **Urgency:** High (compliance required)
4. **Auto-action taken:**
   - Lead marked as "Not Interested"
   - Email address unsubscribed (CAN-SPAM compliance)
   - Removed from all active campaigns
   - No AI suggestion generated (compliance prevents response)

**Notification to User:**
"John Doe (XYZ Corp) has unsubscribed. Lead status updated."

**No human intervention needed**

---

### Flow 5C: Conversation Analytics

**URL:** `/conversations/analytics`

**Header:** "Conversation Intelligence"

**Overview Cards:**
1. **Total Conversations:** 234
2. **Avg. Response Time:** 2.4 hours
3. **Response Rate:** 87%
4. **AI Acceptance Rate:** 76%

**Sentiment Distribution:**
- 😊 Positive: 145 (62%)
- 😐 Neutral: 67 (29%)
- ☹️ Negative: 22 (9%)
- Pie chart visualization

**Conversation Outcomes:**
- Qualified: 89 (38%)
- Closed Won: 34 (15%)
- Closed Lost: 56 (24%)
- Still Active: 55 (23%)
- Funnel visualization

**AI Performance (AI-GYM Integration):**
- **Claude 4.5 Sonnet:**
  - Suggestions generated: 156
  - Accepted by human: 124 (79%)
  - Avg. response time: 1.2s
  - Cost per suggestion: $0.08
- **GPT-4 Turbo:**
  - Suggestions generated: 78
  - Accepted: 54 (69%)
  - Avg. response time: 0.8s
  - Cost per suggestion: $0.12

**Charts:**
- Response time over time
- Sentiment trends
- Conversation volume by source
- Win rate by lead source

---

## Journey 6: AI-GYM Dashboard & Model Optimization

**Goal:** Monitor AI model performance, run A/B tests, optimize costs, and select the best models for each task.

### Entry Points
- Navigation → "AI-GYM"
- Dashboard widget → "View AI Performance"
- Settings → "AI Model Configuration"

---

### Flow 6A: AI-GYM Dashboard Overview

#### Screen 1: AI-GYM Dashboard

**URL:** `/ai-gym`

**Header:**
- Title: "AI-GYM - Model Performance & Optimization"
- Subtitle: "Compare AI models, optimize costs, and improve quality"
- Actions: "+ Create A/B Test" | "Settings" | "Export Report"

**Quick Stats (4 cards):**

1. **Total AI Calls**
   - 12,847 requests
   - +23% vs. last month

2. **Total Cost**
   - $347.82
   - Avg: $0.027 per request

3. **Overall Quality Score**
   - 87/100 (Good)
   - +5 points vs. last month

4. **Cost Savings**
   - $89.50 saved
   - vs. using only GPT-4

**Tabs:**

#### Tab 1: Model Performance Overview

**Model Comparison Table:**

**Columns:**
1. Model Name
2. Provider
3. Tasks Used
4. Quality Score (0-100)
5. Approval Rate (%)
6. Avg. Cost per Call
7. Avg. Latency (ms)
8. Total Calls
9. Total Cost
10. Actions

**Rows (example data):**

**Row 1: Claude 4.5 Sonnet**
- Provider: Anthropic
- Tasks: Website Analysis, Code Gen, Email Writing
- Quality: 92/100 [████████████████████░] (green)
- Approval: 87% [████████████████████░]
- Cost: $0.032
- Latency: 1,240ms
- Calls: 4,523
- Total: $144.74
- Actions: View Details | Configure | A/B Test

**Row 2: GPT-4 Turbo**
- Provider: OpenAI
- Tasks: Script Gen, Conversation AI
- Quality: 85/100 [████████████████░░░░] (yellow)
- Approval: 79%
- Cost: $0.045
- Latency: 890ms
- Calls: 3,201
- Total: $144.05
- Actions: View Details | Configure | A/B Test

**Row 3: DeepSeek Chat**
- Provider: DeepSeek
- Tasks: Email Writing, Conversation AI
- Quality: 78/100 [██████████████░░░░░░] (yellow)
- Approval: 71%
- Cost: $0.00042
- Latency: 1,980ms
- Calls: 2,834
- Total: $1.19
- Actions: View Details | Configure | A/B Test

**Row 4: GPT-4o Mini**
- Provider: OpenAI
- Tasks: Conversation AI, Email Writing
- Quality: 74/100 [█████████████░░░░░░░] (orange)
- Approval: 68%
- Cost: $0.0015
- Latency: 650ms
- Calls: 1,845
- Total: $2.77
- Actions: View Details | Configure | A/B Test

**Row 5: Gemini 1.5 Pro**
- Provider: Google
- Tasks: Website Analysis
- Quality: 81/100 [███████████████░░░░░] (yellow)
- Approval: 76%
- Cost: $0.0125
- Latency: 1,120ms
- Calls: 444
- Total: $5.55
- Actions: View Details | Configure | A/B Test

**Sort Options:**
- Sort by: Quality (default) | Cost | Approval Rate | Calls | Latency

**Filter Options:**
- Provider: All | Anthropic | OpenAI | DeepSeek | Google
- Task Type: All | Website Analysis | Code Gen | Email Writing | etc.
- Quality Threshold: Slider (0-100)

**Charts (below table):**

1. **Quality vs. Cost Scatter Plot**
   - X-axis: Cost per call
   - Y-axis: Quality score
   - Each model is a bubble (size = # of calls)
   - Quadrants: High Quality Low Cost (best) | High Quality High Cost | Low Quality Low Cost | Low Quality High Cost
   - Shows sweet spot models

2. **Model Usage Over Time**
   - Line chart
   - X-axis: Date
   - Y-axis: Number of calls
   - Multiple lines (one per model)
   - Shows adoption trends

---

#### Tab 2: Task-Specific Performance

**Task Type Selector:**
- Dropdown: Website Analysis | Code Generation | Email Writing | Conversation AI | Video Script | Lead Scoring

**Selected: Website Analysis**

**Performance by Model (cards):**

**Card 1: Claude 4.5 Sonnet** ⭐ Best for this task
- **Quality Score:** 94/100
- **Metrics:**
  - Completeness: 97% (has all required sections)
  - Accuracy: 92% (findings are correct)
  - Actionability: 96% (includes code examples)
  - User Approval: 91%
- **Cost:** $0.042 per analysis
- **Speed:** 1,450ms avg
- **Sample Size:** 1,234 analyses
- **Recommendation:** "Best overall choice for website analysis"
- **Actions:** Set as Default | View Samples | A/B Test

**Card 2: Gemini 1.5 Pro**
- **Quality Score:** 81/100
- **Metrics:**
  - Completeness: 85%
  - Accuracy: 79%
  - Actionability: 80%
  - User Approval: 76%
- **Cost:** $0.0125 per analysis (70% cheaper)
- **Speed:** 1,120ms (22% faster)
- **Sample Size:** 444 analyses
- **Recommendation:** "Good budget alternative"
- **Actions:** Set as Default | View Samples | A/B Test

**Card 3: GPT-4 Turbo**
- **Quality Score:** 87/100
- **Metrics:**
  - Completeness: 91%
  - Accuracy: 85%
  - Actionability: 86%
  - User Approval: 81%
- **Cost:** $0.055 per analysis
- **Speed:** 980ms (fastest)
- **Sample Size:** 567 analyses
- **Recommendation:** "Good if speed is priority"
- **Actions:** Set as Default | View Samples | A/B Test

**Comparison Chart:**
- Radar chart comparing the 3 models across 5 dimensions:
  - Quality
  - Cost Efficiency
  - Speed
  - Completeness
  - User Approval

**ROI Calculator:**
- "If you switch from Claude 4.5 to Gemini 1.5 for website analysis:"
- Cost savings: $36.41 per 1,000 analyses
- Quality reduction: -13 points
- Speed improvement: +330ms faster
- **Recommendation:** "Keep Claude 4.5 for quality, or switch to Gemini for cost savings if quality threshold is > 80"

---

#### Tab 3: Active A/B Tests

**Header:**
- "Active A/B Tests (3)"
- "+ Create New A/B Test" button

**A/B Test Cards:**

**Test 1: Email Writing - Claude vs. DeepSeek** [Active]
- **Status:** In Progress (64% complete)
- **Started:** 3 days ago
- **End Date:** In 4 days
- **Variants:**
  - **Variant A (Control):** Claude 4.5 Sonnet
    - Sample: 156 emails
    - Quality: 89/100
    - Approval: 84%
    - Cost: $4.99
  - **Variant B:** DeepSeek Chat
    - Sample: 148 emails
    - Quality: 76/100
    - Approval: 69%
    - Cost: $0.06
- **Progress Bar:** 64% (304 / 500 target samples)
- **Current Leader:** Variant A (Claude 4.5)
  - Quality advantage: +13 points
  - Cost: 83x more expensive
- **Statistical Significance:** 95% (p-value: 0.03)
- **Actions:** View Details | Pause Test | End Early | Adjust Traffic

**Test 2: Conversation AI - GPT-4 vs. GPT-4o Mini** [Active]
- **Status:** In Progress (23% complete)
- **Started:** Yesterday
- **End Date:** In 6 days
- **Variants:**
  - **Variant A (Control):** GPT-4 Turbo
    - Sample: 45 conversations
    - Quality: 85/100
    - Approval: 79%
    - Cost: $2.03
  - **Variant B:** GPT-4o Mini
    - Sample: 48 conversations
    - Quality: 74/100
    - Approval: 68%
    - Cost: $0.07
- **Progress:** 23% (93 / 400 target)
- **Current Leader:** Too early to determine
- **Statistical Significance:** Not yet significant (need more data)
- **Actions:** View Details | Pause Test

**Test 3: Website Analysis - Claude vs. Gemini** [Completed]
- **Status:** Completed ✓
- **Duration:** 7 days
- **Winner:** Claude 4.5 Sonnet
- **Results:**
  - **Claude 4.5:** Quality 94/100, Approval 91%, Cost $0.042
  - **Gemini 1.5:** Quality 81/100, Approval 76%, Cost $0.0125
- **Decision:** Keep Claude 4.5 as default (quality worth the cost)
- **Statistical Significance:** 99% (p-value: 0.001)
- **Recommendation Applied:** ✓ Claude 4.5 set as default
- **Actions:** View Full Report | Re-run Test | Archive

**Empty State (if no tests):**
- "No active A/B tests"
- "Create a test to compare models and optimize your AI performance"
- "+ Create Your First A/B Test" button

---

### Flow 6B: Create A/B Test

#### Screen 1: A/B Test Configuration

**Modal:** "Create New A/B Test"

**Step 1: Select Task Type**

**Task Type Cards (clickable):**
- ◉ **Email Writing**
  - "Compare which model writes better emails"
- ○ **Conversation AI**
- ○ **Website Analysis**
- ○ **Code Generation**
- ○ **Video Script**
- ○ **Lead Scoring**

**User Action:** Select "Email Writing"

---

**Step 2: Select Models to Compare**

**UI Components:**

**Variant A (Control):**
- Label: "Current default model"
- Model: Claude 4.5 Sonnet (locked)
- Current stats shown:
  - Quality: 89/100
  - Approval: 84%
  - Cost: $0.032 per email

**vs.**

**Variant B (Test):**
- Dropdown: "Select model to test against"
- Options:
  - GPT-4 Turbo
  - DeepSeek Chat ← Selected
  - GPT-4o Mini
  - Gemini 1.5 Pro
- Selected model stats:
  - Quality: 76/100 (historical, if available)
  - Approval: 69%
  - Cost: $0.00042 per email

**Comparison Preview:**
- Side-by-side cards showing both models
- Highlights: DeepSeek is 76x cheaper but -13 quality points

---

**Step 3: Configure Test Parameters**

**Form Fields:**

1. **Test Name:** (text input)
   - Default: "Email Writing - Claude vs DeepSeek"
   - Editable

2. **Sample Size:** (number input)
   - Default: 500 (recommended)
   - Help: "Number of emails to generate (250 per variant)"
   - Min: 100, Max: 10,000

3. **Traffic Split:** (slider)
   - Variant A: 50%
   - Variant B: 50%
   - Can adjust: 90/10, 80/20, etc.
   - Help: "Unequal splits useful if testing risky model"

4. **Duration:** (radio)
   - ◉ Until sample size reached
   - ○ Run for: [7] days (number input)
   - ○ Run until: [date picker]

5. **Success Metric:** (dropdown)
   - Quality Score (AI-evaluated)
   - ◉ User Approval Rate (primary)
   - Click-through Rate
   - Reply Rate
   - Combined Score

6. **Significance Level:** (slider)
   - Default: 95% confidence
   - Help: "Higher = more certainty but longer test"

**Cost Estimate:**
- Variant A (Claude): 250 emails × $0.032 = $8.00
- Variant B (DeepSeek): 250 emails × $0.00042 = $0.11
- **Total test cost:** $8.11

**Statistical Power:**
- "With 500 samples, this test can detect a 10% difference in approval rate with 95% confidence"

**Buttons:**
- "Cancel"
- "← Back"
- "Start A/B Test" (primary)

**User Action:** Review settings, click "Start A/B Test"

**Confirmation:**
"Start A/B test comparing Claude 4.5 vs. DeepSeek for email writing?"
- "This will randomly assign emails to each model"
- "You can pause or stop the test anytime"
- "Cancel" | "Yes, Start Test"

**State Change:**
- Test created with status "Active"
- System starts routing 50% of email requests to each model
- Redirect to test monitoring page

---

### Flow 6C: Monitor A/B Test

#### Screen: A/B Test Detail View

**URL:** `/ai-gym/tests/[test_id]`

**Header:**
- Test: "Email Writing - Claude vs DeepSeek"
- Status: Active (animated badge)
- Started: 3 days ago
- Progress: 64% complete
- Actions: "Pause Test" | "End Early" | "Adjust Traffic" | "Export Data"

**Progress Overview:**

**Progress Bar:** 64% (320 / 500 samples)
- Variant A: 162 samples
- Variant B: 158 samples
- Remaining: 180 samples
- ETA: 4 days (based on current rate)

**Real-time Stats Cards:**

**Variant A: Claude 4.5 Sonnet**
- **Quality Score:** 89/100 [████████████████████░]
- **User Approval:** 84% (136 / 162 approved)
- **Avg Response Time:** 1.2s
- **Total Cost:** $5.18
- **Cost per Email:** $0.032
- **Edit Distance:** 12.3 chars avg (how much human edited)

**Variant B: DeepSeek Chat**
- **Quality Score:** 76/100 [████████████████░░░░]
- **User Approval:** 69% (109 / 158 approved)
- **Avg Response Time:** 2.1s
- **Total Cost:** $0.07
- **Cost per Email:** $0.00042
- **Edit Distance:** 28.7 chars avg (more editing needed)

**Current Leader:** Variant A (Claude 4.5)
- Quality advantage: +13 points
- Approval advantage: +15%
- Cost disadvantage: 76x more expensive

**Statistical Analysis:**

**Significance Test:**
- **P-value:** 0.03
- **Confidence:** 95% ✓ Significant
- **Interpretation:** "There is a statistically significant difference between the models. Claude 4.5 performs better with 95% confidence."

**Effect Size:**
- Approval rate difference: +15% (large effect)
- Quality score difference: +13 points (medium-large effect)

**Charts:**

1. **Approval Rate Over Time**
   - Line chart
   - X-axis: Sample number
   - Y-axis: Cumulative approval rate
   - Two lines (Variant A and B)
   - Shows convergence/divergence

2. **Quality Score Distribution**
   - Box plot or histogram
   - Shows distribution of quality scores for each variant
   - Highlights median, quartiles, outliers

3. **Cost vs. Quality Scatter**
   - Each email as a point
   - X-axis: Quality score
   - Y-axis: Cost
   - Color-coded by variant

**Sample Comparisons (expandable section):**

**Show Side-by-Side Samples:**
- Button: "View Sample Emails"

**Sample 1:**
- **Prompt:** "Write cold email to web design agency lead"
- **Variant A (Claude):**
  ```
  Subject: Quick idea for improving [Company]'s website

  Hi [Name],

  I noticed [Company]'s website has great content, but I spotted
  a few quick wins that could boost your conversion rate by 20-30%.

  I created a free demo showing exactly what I mean: [demo link]

  No pressure - just thought you might find it useful.

  Best,
  [Your Name]
  ```
  - Quality: 92/100
  - User approved: Yes ✓
  - Edits: 0 characters

- **Variant B (DeepSeek):**
  ```
  Subject: Website improvement opportunity

  Hello [Name],

  I am reaching out regarding [Company]'s website. I have identified
  several areas for improvement that could enhance your online presence.

  Please see the demonstration here: [demo link]

  Let me know if you are interested to discuss further.

  Regards,
  [Your Name]
  ```
  - Quality: 74/100
  - User approved: No ✗
  - Feedback: "Too formal, lacks personality"
  - Edits: 47 characters (user rewrote parts)

**Pagination:** Showing 1-5 of 320 samples

---

**Decision Helper:**

**If you end the test now:**
- **Recommendation:** Deploy Variant A (Claude 4.5)
- **Confidence:** 95%
- **Reasoning:**
  - Claude has significantly higher approval rate (+15%)
  - Higher quality scores (+13 points)
  - Lower edit distance (less work for humans)
  - Cost difference ($8 vs $0.11 per 500 emails) is acceptable for quality gain
- **Projected ROI:** For 1,000 emails/month:
  - Additional cost: $32
  - Time saved editing: ~8 hours
  - Higher conversion expected from better emails

**Alternative:**
- "If budget is primary concern, consider DeepSeek with human review/editing"

**Actions:**
- "Deploy Winner (Claude 4.5)" (primary)
- "Continue Test" (secondary)
- "Deploy Both (Gradual Rollout)"

**User Action:** Click "Deploy Winner"

**Confirmation:**
"Set Claude 4.5 Sonnet as default for Email Writing?"
- This will apply to all future email generation
- Current default will be archived
- You can change this anytime in Settings
- "Cancel" | "Yes, Deploy Claude 4.5"

**State Change:**
- Model routing updated
- Test marked as "Completed"
- Email writing tasks now use Claude 4.5 by default
- Success notification: "✓ Claude 4.5 Sonnet is now the default for Email Writing"

---

#### Tab 4: Cost Optimization

**Header:** "AI Cost Analysis & Optimization"

**Total Spend Widget:**
- **This Month:** $347.82
- **Last Month:** $284.12 (+22%)
- **YTD:** $1,892.47
- **Projected Annual:** $4,170

**Cost Breakdown (pie chart):**
- Website Analysis: $156.34 (45%)
- Code Generation: $87.23 (25%)
- Email Writing: $52.11 (15%)
- Conversation AI: $34.87 (10%)
- Other: $17.27 (5%)

**Optimization Opportunities:**

**Card 1: Switch Code Generation to DeepSeek** 💡
- **Potential Savings:** $64.50/month (74% reduction)
- **Quality Trade-off:** -11 points (acceptable)
- **Recommendation:** Consider switching
- **Details:**
  - Current: Claude 4.5 ($0.042/call, 2,078 calls/month)
  - Alternative: DeepSeek ($0.00042/call)
  - Quality: 87 → 76 (still above 70 threshold)
- **Actions:** "Run A/B Test" | "Switch Now" | "Dismiss"

**Card 2: Reduce Email AI Calls with Templates** 💡
- **Potential Savings:** $38.20/month
- **Strategy:** Use AI for custom emails only, templates for standard outreach
- **Details:**
  - 48% of emails are standard cold outreach
  - These could use templates with token replacement
  - Save AI calls for personalized/complex emails only
- **Actions:** "Create Templates" | "Learn More" | "Dismiss"

**Card 3: Batch Processing for Analysis** 💡
- **Potential Savings:** $12.40/month (API efficiency)
- **Strategy:** Batch multiple website analyses into single request
- **Details:**
  - Currently: 1 request per website
  - Possible: Analyze 5 websites per request (shared context)
  - Same quality, 40% less cost due to context reuse
- **Actions:** "Enable Batching" | "Learn More" | "Dismiss"

**Historical Cost Trends:**
- Line chart showing daily/weekly/monthly costs
- Annotations showing when optimizations were applied
- Forecasting future costs

**Cost by Model Table:**
- Similar to performance table but sorted by total cost
- Shows: Model, Total Calls, Avg Cost, Total Spent, % of Budget

---

#### Tab 5: Quality Analytics

**Header:** "AI Output Quality Metrics"

**Overall Quality Score:** 87/100 (Good)
- Target: 85+ (on track ✓)
- Trend: +5 points vs. last month ↑

**Quality by Task Type (bar chart):**
- Website Analysis: 92/100 (Excellent)
- Code Generation: 87/100 (Good)
- Email Writing: 85/100 (Good)
- Conversation AI: 83/100 (Good)
- Video Script: 89/100 (Good)
- Lead Scoring: 78/100 (Fair)

**Quality Metrics Deep Dive:**

**1. Completeness** (does output have all required elements?)
- Overall: 91%
- Breakdown by model:
  - Claude 4.5: 97%
  - GPT-4: 88%
  - Gemini: 85%
  - DeepSeek: 79%

**2. Accuracy** (is output factually correct?)
- Overall: 86%
- Measured by: Human verification + automated checks
- Common errors:
  - Hallucinated URLs (12% of code gen)
  - Incorrect metric calculations (8% of analysis)
  - Outdated information (5% of email content)

**3. Actionability** (can user immediately use output?)
- Overall: 88%
- High for: Code gen (95%), Website analysis (94%)
- Low for: Lead scoring (72%) - needs more context

**4. Human Approval Rate** (% of outputs accepted without edits)
- Overall: 76%
- Claude 4.5: 87%
- GPT-4: 79%
- DeepSeek: 69%
- GPT-4o Mini: 68%

**5. Edit Distance** (how much human changes output)
- Overall: 18.7 characters avg
- Low = better (less editing needed)
- Claude 4.5: 12.3 chars (best)
- GPT-4: 16.8 chars
- DeepSeek: 28.4 chars
- GPT-4o Mini: 31.2 chars

**Quality Issues Log:**

**Recent Quality Issues (table):**
1. **Code Gen - Missing Package.json**
   - Model: DeepSeek
   - Task: React component generation
   - Issue: Didn't generate package.json dependencies
   - Impact: User had to manually create it
   - Status: Reported to model evaluation
   - Frequency: 23% of code gen tasks

2. **Email Writing - Spam Trigger Words**
   - Model: GPT-4o Mini
   - Issue: Used words like "FREE", "LIMITED TIME" (spam triggers)
   - Impact: Lower deliverability
   - Status: Fixed in prompt
   - Frequency: 12% of emails

3. **Website Analysis - Incomplete SEO Check**
   - Model: Gemini 1.5
   - Issue: Missed structured data analysis
   - Impact: Incomplete analysis
   - Status: Under investigation
   - Frequency: 8% of analyses

**User Feedback:**
- Shows aggregated feedback from approval/rejection decisions
- Word cloud of common issues
- Trending complaints

---

### Flow 6D: Model Configuration

#### Screen: Model Settings

**URL:** `/ai-gym/settings`

**Header:** "AI Model Configuration"

**Task-Based Model Selection:**

**For each task type, configure default model:**

**Website Analysis:**
- **Current Default:** Claude 4.5 Sonnet
- **Alternative Models:** (dropdown)
  - Claude 4.5 Sonnet ← Selected
  - GPT-4 Turbo
  - Gemini 1.5 Pro
  - DeepSeek Chat
- **Fallback Model:** (if primary fails)
  - Dropdown: GPT-4 Turbo
- **Quality Threshold:** (slider)
  - Minimum: 80/100
  - "If output scores below 80, regenerate with fallback model"
- **Max Retries:** 2
- **Save** button

**Code Generation:**
- Current Default: Claude 4.5 Sonnet
- [Similar configuration]

**Email Writing:**
- Current Default: Claude 4.5 Sonnet
- [Similar configuration]

[... all task types]

**Global Settings:**

**AI Council Mode:** (toggle)
- ☑ Enabled
- "Query multiple models simultaneously for critical tasks"
- **Council Models:** (multi-select)
  - ☑ Claude 4.5 Sonnet
  - ☑ GPT-4 Turbo
  - ☐ DeepSeek Chat
- **When to use:** (dropdown)
  - Critical tasks only (demo gen, analysis)
  - All tasks
  - Never
- **Selection Strategy:** (radio)
  - ◉ Best quality (highest scoring output)
  - ○ Majority vote (if outputs similar)
  - ○ Fastest response
  - ○ Best cost/quality ratio

**Cost Limits:**
- **Daily Limit:** $50
- **Monthly Limit:** $500
- **Alert at:** 80% of limit
- **When limit reached:** (dropdown)
  - Switch to cheapest models
  - Pause AI tasks
  - Send notification only

**Quality Assurance:**
- ☑ Validate all AI outputs before returning
- ☑ Check for placeholders (TODO, FIXME, etc.)
- ☑ Run syntax validation (for code)
- ☑ Check for sensitive data in outputs

**Logging & Monitoring:**
- ☑ Log all AI requests/responses
- ☑ Track user feedback
- ☑ Enable performance monitoring
- **Data Retention:** 90 days

**Buttons:**
- "Reset to Defaults"
- "Export Configuration"
- "Save Changes" (primary)

---

## Journey 7: Approval Workflows & n8n Integration

**Goal:** Human-in-the-loop approval for AI-generated content and orchestration with n8n workflows.

### Entry Points
- Navigation → "Approvals"
- Notification → "3 items need approval"
- n8n workflow → Sends item to approval queue

---

### Flow 7A: Approval Queue

#### Screen 1: Approvals Page

**URL:** `/approvals`

**Header:**
- Title: "Approval Queue"
- Badge: "12 pending" (red badge)
- Actions: "Settings" | "Approve All" | "Export"

**Stats Cards:**
1. **Pending Approval:** 12
2. **Approved Today:** 34
3. **Rejected Today:** 3
4. **Avg Approval Time:** 2.3 minutes

**Filters (left sidebar):**
- **Status:** (checkboxes)
  - ☑ Pending (12)
  - ☐ Approved (1,234)
  - ☐ Rejected (89)
- **Item Type:** (checkboxes)
  - ☑ Email (5)
  - ☑ Demo Site (3)
  - ☑ Video (2)
  - ☑ AI Response (2)
  - ☐ Code Change (0)
- **Priority:** (checkboxes)
  - ☑ High (3)
  - ☑ Medium (7)
  - ☑ Low (2)
- **Age:** (radio)
  - ◉ All
  - ○ Last 24 hours
  - ○ Last week
  - ○ Older than 1 week
- **Assigned To:** (dropdown)
  - Me (8)
  - Unassigned (4)
  - Team member 1 (0)

**Approval Queue (table/cards):**

**Item 1: Email - Cold Outreach** [High Priority]
- **Type:** Email
- **For Lead:** Acme Corp - John Smith
- **AI Generated By:** Claude 4.5 Sonnet
- **Created:** 5 minutes ago
- **Priority:** High (red badge)
- **Status:** Pending (yellow badge)
- **Preview:** "Hi John, I noticed Acme Corp's website..."
- **Risk Score:** Low (green)
- **Estimated Send Time:** In queue (will send immediately after approval)
- **Actions:** "Review & Approve" (primary) | "Reject" | "Edit" | "Assign"

**Item 2: Demo Site - XYZ Company** [High Priority]
- **Type:** Demo Site
- **For Lead:** XYZ Company - Jane Doe
- **Generated By:** Claude 4.5 Sonnet
- **Created:** 15 minutes ago
- **Priority:** High
- **Status:** Pending
- **Preview:** "React demo site with 42 files"
- **Risk Score:** Medium (requires code review)
- **Validation:** ✓ Build successful, ⚠️ 3 warnings
- **Actions:** "Review & Approve" | "Reject" | "Edit Code"

**Item 3: AI Response - Conversation Reply** [Medium Priority]
- **Type:** AI Conversation Response
- **For:** Conversation with Mark Johnson
- **Generated By:** GPT-4 Turbo
- **Created:** 1 hour ago
- **Priority:** Medium
- **Status:** Pending
- **Preview:** "Thanks for your interest! I'd be happy to schedule..."
- **Risk Score:** Low
- **Actions:** "Review & Approve" | "Reject" | "Edit"

[... 9 more items]

**Sort Options:**
- Sort by: Priority (default) | Created Date | Type | Risk Score

**Bulk Actions:**
- Checkbox to select multiple items
- "5 items selected"
- Actions: "Approve All" | "Reject All" | "Assign To..."

---

### Flow 7B: Review & Approve Item

#### Screen: Approval Detail View

**Triggered by:** Click "Review & Approve" on Item 1

**Modal/Slide-over:** "Review Email for Approval"

**Layout:** Three columns

**Left Column: Original Context**

**Lead Information:**
- **Name:** John Smith
- **Company:** Acme Corp
- **Source:** Google Maps
- **Status:** New lead
- **Email:** john@acmecorp.com
- **Website:** acmecorp.com
- **Last Contact:** Never

**Demo Site:** (if applicable)
- Thumbnail preview
- URL: https://acme-demo-x7k3.vercel.app
- "View Demo Site" link

**Video:** (if applicable)
- Thumbnail preview
- Duration: 1:42
- "Watch Video" link

**Original AI Prompt:**
```
Task: Write cold outreach email
Lead: Acme Corp (web design agency)
Context: We created demo site showing improvements
Tone: Professional but friendly
Include: Demo site link, video link
CTA: Schedule call
```

---

**Middle Column: AI-Generated Content**

**Email Preview:**

**From:** Your Name <you@yourcompany.com>
**To:** John Smith <john@acmecorp.com>
**Subject:** Quick idea for improving Acme Corp's website

**Body:**
```
Hi John,

I noticed Acme Corp's website has great content, but I spotted
a few quick wins that could boost your conversion rate by 20-30%.

I took the liberty of creating a free demo showing exactly
what I mean:

[View Demo Site] (button)

I also put together a quick video walkthrough (1:42):

[Watch Video] (button)

No pressure - just thought you might find it useful. If you'd
like to discuss implementing these improvements, I have some
time this week.

Best,
[Your Name]
[Your Company]
[Your Phone]
```

**Quality Score:** 92/100
- Completeness: 98%
- Tone: Professional ✓
- Grammar: Perfect ✓
- Personalization: Good ✓
- CTA: Clear ✓

**Risk Assessment:**
- ✓ No spam trigger words
- ✓ Unsubscribe link included
- ✓ Physical address included (CAN-SPAM)
- ✓ No sensitive information
- ✓ Links valid and working
- **Overall Risk:** Low (green)

**AI Model Used:**
- Claude 4.5 Sonnet
- Cost: $0.032
- Generated: 5 minutes ago
- Confidence: 94%

---

**Right Column: Approval Interface**

**Decision:**

**Option 1: Approve** ✓ (green button, large)
- "Send email immediately"
- Hotkey: Cmd+Enter

**Option 2: Approve with Edits** (blue button)
- "Edit email before sending"
- Opens inline editor

**Option 3: Reject** ✗ (red button)
- "Don't send, provide feedback"
- Requires rejection reason

**Option 4: Defer** (gray button)
- "Decide later"
- Keeps in pending queue

**Quick Edits:** (if minor changes needed)
- Inline edit subject line
- Inline edit body
- "Quick edit and approve" button

**Schedule Send:** (toggle)
- ☐ Schedule for later
- Time picker appears if checked

**Feedback to AI-GYM:** (optional)
- "How would you rate this email?"
- Stars: ★★★★★ (5/5)
- "This helps improve future AI outputs"

**Comments:** (textarea)
- "Internal notes about this approval"
- Visible to team only

**Similar Past Approvals:**
- Shows 3 similar emails that were approved
- "You approved 87% of similar emails"
- Click to view past examples

---

**User Action:** Review email, looks good, click "Approve"

**Confirmation:**
"Send this email to John Smith?"
- Email will be sent immediately
- Tracking will be enabled (opens, clicks)
- "Cancel" | "Yes, Send Email" (primary)

**State Changes:**
- Approval status → "Approved"
- Email sent via SMTP
- Item removed from pending queue
- Notification to lead's timeline
- AI-GYM feedback recorded (+1 for Claude 4.5)
- Success toast: "✓ Email sent to John Smith"

---

### Flow 7C: Reject with Feedback

**User Action:** Click "Reject" instead of Approve

**Modal:** "Reject Email - Provide Feedback"

**Form:**

1. **Rejection Reason:** (required, radio)
   - ○ Poor quality/Grammar issues
   - ○ Wrong tone
   - ○ Factually incorrect
   - ○ Inappropriate content
   - ○ Missing required information
   - ◉ Other (specify)

2. **Detailed Feedback:** (textarea, required)
   - Placeholder: "Why are you rejecting this? (helps AI learn)"
   - Example: "Too pushy, mentions '20-30%' improvement without proof"

3. **Specific Issues:** (checkboxes, optional)
   - ☑ Subject line needs work
   - ☑ Body content too long
   - ☐ Wrong personalization
   - ☐ Broken links
   - ☑ Inappropriate tone

4. **Suggested Action:** (radio)
   - ◉ Regenerate with different prompt
   - ○ Assign to human to write manually
   - ○ Skip this lead entirely
   - ○ Try different AI model

**AI-GYM Feedback:**
- "This rejection will be used to improve future outputs"
- Model: Claude 4.5 Sonnet will receive negative feedback
- Similar prompts will be adjusted

**Buttons:**
- "Cancel"
- "Reject & Regenerate" (primary)
- "Reject & Skip Lead"

**User Action:** Provide feedback, click "Reject & Regenerate"

**State Changes:**
- Item marked as "Rejected"
- AI receives feedback (AI-GYM learning)
- New generation queued with improved prompt
- New item appears in approval queue ~30s later
- Toast: "Email rejected. Regenerating with feedback..."

---

### Flow 7D: n8n Workflow Integration

#### Screen: n8n Workflows Page

**URL:** `/workflows`

**Header:**
- Title: "n8n Workflow Integrations"
- Subtitle: "Orchestrate complex automations"
- Actions: "+ Create Workflow" | "View n8n Dashboard" | "Settings"

**Stats Cards:**
1. **Active Workflows:** 8
2. **Executions Today:** 234
3. **Success Rate:** 97.4%
4. **Avg Execution Time:** 3.2s

**Active Workflows (cards):**

**Workflow 1: Lead Enrichment Pipeline** [Active]
- **Trigger:** New lead created
- **Steps:** (visual flow diagram)
  1. Receive lead webhook
  2. Hunter.io → Find email
  3. If no email → Apollo.io
  4. If still no email → Clearbit
  5. Update lead in database
  6. Trigger webhook back to our app
- **Executions Today:** 87
- **Success Rate:** 94%
- **Avg Duration:** 4.2s
- **Cost:** $8.70 today
- **Actions:** "View in n8n" | "Edit" | "Pause" | "View Logs"

**Workflow 2: Demo Site Auto-Deploy** [Active]
- **Trigger:** Demo site approved
- **Steps:**
  1. Receive approval webhook
  2. Push code to GitHub
  3. Trigger Vercel deployment
  4. Wait for deployment
  5. Send preview URL back
  6. Notify lead via email
- **Executions Today:** 12
- **Success Rate:** 100%
- **Actions:** "View in n8n" | "Edit" | "Pause"

**Workflow 3: Email Campaign Scheduler** [Active]
- **Trigger:** Cron (daily 9am)
- **Steps:**
  1. Query leads ready for follow-up
  2. For each lead:
     - Generate personalized email (AI)
     - Send to approval queue
     - Wait for approval
     - Send email if approved
  3. Update lead statuses
- **Executions Today:** 1 (runs once daily)
- **Leads Processed:** 45
- **Actions:** "View in n8n" | "Edit" | "Run Now"

**Workflow 4: Video Generation Queue** [Active]
- **Trigger:** Demo site completed
- **Steps:**
  1. Wait 5 minutes (cooldown)
  2. Generate video script (AI)
  3. Generate voiceover (ElevenLabs)
  4. Record screen (Puppeteer)
  5. Compose video (FFmpeg)
  6. Upload to CDN
  7. Send completion webhook
- **Executions Today:** 8
- **Success Rate:** 87.5% (1 failed)
- **Actions:** "View in n8n" | "Edit" | "View Failed Runs"

**Workflow 5: Conversation Auto-Responder** [Active]
- **Trigger:** Email reply received
- **Steps:**
  1. Parse email reply
  2. Analyze sentiment (AI)
  3. Generate response suggestions (AI)
  4. Send to approval queue
  5. Wait for approval
  6. Send approved response
- **Executions Today:** 23
- **Auto-approved:** 12 (52%)
- **Needs review:** 11
- **Actions:** "View in n8n" | "Edit"

[... 3 more workflows]

**Create New Workflow:**
- Button: "+ Create Workflow"
- Opens: Workflow template selector

**Templates:**
1. Lead Enrichment
2. Demo Site Pipeline
3. Email Campaign
4. Video Generation
5. Webhook Handler
6. Data Sync
7. Notification System
8. Custom (blank)

---

### Flow 7E: Webhook Queue

#### Screen: Webhook Queue

**URL:** `/workflows/webhooks`

**Header:** "Webhook Queue & Logs"

**Queue Stats:**
1. **Queued:** 23 webhooks
2. **Processing:** 5
3. **Failed:** 2 (need retry)
4. **Completed Today:** 567

**Webhook Queue Table:**

**Columns:**
1. ID
2. Direction (Inbound/Outbound)
3. Target (URL/workflow)
4. Payload (preview)
5. Status
6. Attempts
7. Created
8. Actions

**Row 1: Outbound to n8n**
- ID: #12847
- Direction: Outbound → n8n
- Target: https://n8n.example.com/webhook/lead-enrichment
- Payload: `{"lead_id": 1234, "name": "Acme Corp", ...}`
- Status: Completed ✓
- Attempts: 1/3
- Created: 2 min ago
- Actions: "View Response" | "Retry" | "Delete"

**Row 2: Inbound from n8n**
- ID: #12848
- Direction: Inbound ← n8n
- Source: Lead enrichment workflow
- Payload: `{"lead_id": 1234, "email": "john@acme.com", ...}`
- Status: Processed ✓
- Created: 1 min ago
- Actions: "View Details"

**Row 3: Outbound to n8n**
- ID: #12849
- Direction: Outbound → n8n
- Target: https://n8n.example.com/webhook/demo-deploy
- Payload: `{"demo_id": 789, "files": {...}}`
- Status: Failed ✗
- Attempts: 3/3 (max retries reached)
- Error: "Connection timeout after 30s"
- Created: 10 min ago
- Actions: "Retry Now" | "View Error" | "Delete"

**Filters:**
- Status: All | Queued | Processing | Completed | Failed
- Direction: All | Inbound | Outbound
- Date Range: (picker)

**Retry Failed Webhooks:**
- "2 failed webhooks"
- "Retry All Failed" button

---

### Flow 7F: Approval Settings

#### Screen: Approval Settings

**URL:** `/approvals/settings`

**Header:** "Approval Workflow Configuration"

**Auto-Approval Rules:**

**Enable Auto-Approval:** (toggle)
- ☑ Enabled
- "Automatically approve items meeting criteria below"

**Rules:**

**Rule 1: High-Quality AI Outputs**
- **Name:** Auto-approve high-quality content
- **Conditions:**
  - Quality score ≥ 90
  - Risk score = Low
  - AI model = Claude 4.5 Sonnet
  - Content type = Email OR AI Response
- **Action:** Auto-approve and send
- **Enabled:** ☑ Yes
- **Applied:** 156 times this week
- **Actions:** "Edit" | "Disable" | "View History"

**Rule 2: Trusted Lead Segments**
- **Name:** Auto-approve emails to qualified leads
- **Conditions:**
  - Lead status = Qualified
  - Previous approval rate ≥ 90%
  - Quality score ≥ 85
- **Action:** Auto-approve
- **Enabled:** ☑ Yes
- **Applied:** 89 times this week
- **Actions:** "Edit" | "Disable"

**Rule 3: Low-Risk Changes**
- **Name:** Auto-approve minor edits
- **Conditions:**
  - Change type = Template variable only
  - No code changes
  - Approved by 2+ team members previously
- **Action:** Auto-approve
- **Enabled:** ☐ No (disabled)
- **Actions:** "Edit" | "Enable"

**Add New Rule:**
- "+ Create Auto-Approval Rule" button

---

**Notification Settings:**

**When approval needed:**
- ☑ Email notification
- ☑ Slack notification
- ☐ SMS notification (for high priority only)
- **Send to:** (multi-select)
  - ☑ Me
  - ☑ Team lead
  - ☐ All team members

**Reminder frequency:**
- Every 30 minutes for pending items
- Daily summary at 9am

**Approval Permissions:**

**Who can approve:**
- ☑ Admin users (all items)
- ☑ Team leads (all items)
- ☑ Team members (low priority only)
- ☐ External reviewers

**Approval requirements:**
- **Standard items:** 1 approval required
- **High-risk items:** 2 approvals required
- **Code changes:** 1 technical review + 1 business review

**High-risk criteria:**
- Quality score < 80
- Contains sensitive data
- Cost > $10
- New AI model (not tested)

---

**Buttons:**
- "Reset to Defaults"
- "Export Settings"
- "Save Changes" (primary)

---

## Complete!

This completes all 7 user journeys! The document now provides exhaustive detail on every feature, screen, interaction, and flow in the application.

### Summary of All Journeys:

1. ✅ **Multi-Source Scraping** - Craigslist, Google Maps, LinkedIn, Job Boards with n8n enrichment
2. ✅ **Website Analysis → Demo Site** - AI-powered analysis and code generation
3. ✅ **Demo Site → Video** - Script, voiceover, recording, composition
4. ✅ **Email Outreach** - Campaign creation, monitoring, tracking
5. ✅ **Conversation AI** - Response suggestions, sentiment analysis, management
6. ✅ **AI-GYM** - Model performance tracking, A/B testing, cost optimization
7. ✅ **Approvals & n8n** - Human-in-the-loop workflow with orchestration

**Next Steps:**
With this complete blueprint, you can now:
1. Walk through the entire application conceptually
2. Validate all features and flows
3. Use this as spec for frontend development
4. Share with stakeholders/investors/users for feedback
5. Begin building UI components based on these detailed specs

The document is production-ready for guiding frontend development!
