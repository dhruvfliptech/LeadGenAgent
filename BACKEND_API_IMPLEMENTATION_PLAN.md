# Backend API Implementation Plan

**Comprehensive Backend Endpoints Required for FlipTech Pro**

This document identifies all backend API endpoints needed to make every page, section, feature, button, and link in the FlipTech Pro application fully functional.

---

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [User Management & Settings](#2-user-management--settings)
3. [Lead Management](#3-lead-management)
4. [Multi-Source Scraping](#4-multi-source-scraping)
5. [Enrichment & AI Processing](#5-enrichment--ai-processing)
6. [Campaign Management](#6-campaign-management)
7. [Email Templates](#7-email-templates)
8. [Conversations & Auto-Response](#8-conversations--auto-response)
9. [Approval Workflows](#9-approval-workflows)
10. [n8n Workflow Integration](#10-n8n-workflow-integration)
11. [Demo Sites & Videos](#11-demo-sites--videos)
12. [Analytics & Reporting](#12-analytics--reporting)
13. [Webhooks & External Integrations](#13-webhooks--external-integrations)
14. [AI-GYM & Model Management](#14-ai-gym--model-management)
15. [Notifications & Real-time Updates](#15-notifications--real-time-updates)
16. [File Operations](#16-file-operations)
17. [Location & Map Management](#17-location--map-management)
18. [Scheduling](#18-scheduling)

---

## 1. Authentication & Authorization

### Core Authentication
```http
POST   /api/v1/auth/register          # User registration
POST   /api/v1/auth/login             # User login
POST   /api/v1/auth/logout            # User logout
POST   /api/v1/auth/refresh           # Refresh access token
POST   /api/v1/auth/forgot-password   # Request password reset
POST   /api/v1/auth/reset-password    # Reset password with token
GET    /api/v1/auth/me                # Get current user
PUT    /api/v1/auth/me                # Update current user
```

### API Key Management
```http
GET    /api/v1/auth/api-keys          # List all API keys
POST   /api/v1/auth/api-keys          # Create new API key
PUT    /api/v1/auth/api-keys/:id      # Update API key
DELETE /api/v1/auth/api-keys/:id      # Delete API key
POST   /api/v1/auth/api-keys/:id/test # Test API key connection
```

**Used by:** Settings page API Keys tab, authentication flows

---

## 2. User Management & Settings

### Profile
```http
GET    /api/v1/users/profile          # Get user profile
PUT    /api/v1/users/profile          # Update user profile
PATCH  /api/v1/users/profile/avatar   # Upload avatar
DELETE /api/v1/users/profile/avatar   # Remove avatar
```

### Settings
```http
GET    /api/v1/settings/email         # Get email settings (SMTP)
PUT    /api/v1/settings/email         # Update email settings
POST   /api/v1/settings/email/test    # Test email configuration
GET    /api/v1/settings/notifications # Get notification preferences
PUT    /api/v1/settings/notifications # Update notification preferences
GET    /api/v1/settings/preferences   # Get user preferences
PUT    /api/v1/settings/preferences   # Update user preferences
```

**Used by:** Settings page (all tabs), profile management

---

## 3. Lead Management

### Lead CRUD Operations
```http
GET    /api/v1/leads                  # List leads with filters
GET    /api/v1/leads/:id              # Get single lead detail
POST   /api/v1/leads                  # Create new lead manually
PUT    /api/v1/leads/:id              # Update lead
PATCH  /api/v1/leads/:id              # Partial update lead
DELETE /api/v1/leads/:id              # Delete lead
POST   /api/v1/leads/batch            # Batch create leads
PUT    /api/v1/leads/batch-update     # Batch update leads
DELETE /api/v1/leads/batch-delete     # Batch delete leads
```

### Lead Filtering & Search
```http
GET    /api/v1/leads/search           # Advanced search with filters
POST   /api/v1/leads/advanced-filter  # Complex filter with conditions
GET    /api/v1/leads/export           # Export leads (CSV, Excel)
GET    /api/v1/leads/stats            # Get lead statistics
```

### Lead Status & Actions
```http
PATCH  /api/v1/leads/:id/status       # Update lead status
POST   /api/v1/leads/:id/tag          # Add tag to lead
DELETE /api/v1/leads/:id/tag/:tagId   # Remove tag from lead
POST   /api/v1/leads/:id/note         # Add note to lead
PUT    /api/v1/leads/:id/note/:noteId # Update note
DELETE /api/v1/leads/:id/note/:noteId # Delete note
POST   /api/v1/leads/:id/contact      # Mark as contacted
GET    /api/v1/leads/:id/timeline     # Get lead activity timeline
```

### Lead Enrichment
```http
POST   /api/v1/leads/:id/enrich       # Enrich single lead
POST   /api/v1/leads/batch-enrich     # Batch enrich leads
GET    /api/v1/leads/:id/enrichment-history # Get enrichment history
```

### Lead AI Analysis
```http
POST   /api/v1/leads/:id/analyze      # AI analysis of lead
GET    /api/v1/leads/:id/analysis     # Get existing analysis
POST   /api/v1/leads/:id/score        # Calculate qualification score
```

**Used by:** Leads page, Lead Detail page, bulk actions, filtering, enrichment workflows

---

## 4. Multi-Source Scraping

### Craigslist Scraping
```http
GET    /api/v1/scraper/categories     # Get available categories
GET    /api/v1/scraper/locations      # Get available locations
POST   /api/v1/scraper/jobs           # Create scrape job
GET    /api/v1/scraper/jobs           # List scrape jobs
GET    /api/v1/scraper/jobs/:id       # Get scrape job detail
DELETE /api/v1/scraper/jobs/:id       # Cancel/delete scrape job
POST   /api/v1/scraper/jobs/:id/retry # Retry failed scrape
```

### Google Maps Scraping
```http
GET    /api/v1/google-maps/categories # Get business categories
GET    /api/v1/google-maps/sources    # Get configured sources
POST   /api/v1/google-maps/scrape     # Start Google Maps scrape
GET    /api/v1/google-maps/jobs       # List Google Maps jobs
GET    /api/v1/google-maps/jobs/:id   # Get job detail
```

### LinkedIn Scraping
```http
GET    /api/v1/linkedin/sources       # Get LinkedIn sources
POST   /api/v1/linkedin/scrape        # Start LinkedIn scrape
GET    /api/v1/linkedin/jobs          # List LinkedIn jobs
GET    /api/v1/linkedin/jobs/:id      # Get job detail
POST   /api/v1/linkedin/auth          # Authenticate LinkedIn
```

### Job Boards (Indeed, Monster, ZipRecruiter)
```http
GET    /api/v1/job-boards/sources     # Get available job boards
POST   /api/v1/job-boards/scrape      # Start job board scrape
GET    /api/v1/job-boards/jobs        # List job board scrape jobs
GET    /api/v1/job-boards/jobs/:id    # Get job detail
```

### Social Media Scraping
```http
POST   /api/v1/social-media/scrape    # Start social media scrape
GET    /api/v1/social-media/jobs      # List social media jobs
GET    /api/v1/social-media/platforms # Get supported platforms
```

### Custom URL Scraping
```http
POST   /api/v1/custom-url/scrape      # Scrape custom URL
POST   /api/v1/custom-url/analyze     # Analyze URL structure
GET    /api/v1/custom-url/jobs        # List custom URL jobs
```

### Audience Builder
```http
POST   /api/v1/audience-builder/build # Build audience from criteria
GET    /api/v1/audience-builder/audiences # List saved audiences
GET    /api/v1/audience-builder/audiences/:id # Get audience detail
PUT    /api/v1/audience-builder/audiences/:id # Update audience
DELETE /api/v1/audience-builder/audiences/:id # Delete audience
```

**Used by:** Scraper pages (Craigslist, Google Maps, LinkedIn, Social Media, Custom URL), Audience Builder, Scrape Jobs page

---

## 5. Enrichment & AI Processing

### Contact Enrichment
```http
POST   /api/v1/enrichment/hunter-io   # Find email with Hunter.io
POST   /api/v1/enrichment/apollo-io   # Enrich with Apollo.io
POST   /api/v1/enrichment/clearbit    # Enrich with Clearbit
POST   /api/v1/enrichment/phone       # Find phone numbers
POST   /api/v1/enrichment/company     # Get company information
```

### AI Analysis
```http
POST   /api/v1/ai/analyze-sentiment   # Analyze message sentiment
POST   /api/v1/ai/generate-response   # Generate AI response
POST   /api/v1/ai/analyze-lead        # Analyze lead quality
POST   /api/v1/ai/extract-info        # Extract structured info
POST   /api/v1/ai/classify            # Classify content
POST   /api/v1/ai/summarize           # Summarize text
```

### ML Scoring
```http
POST   /api/v1/ml/score-lead          # Score single lead
POST   /api/v1/ml/score-leads         # Batch score leads
GET    /api/v1/ml/models              # List available models
GET    /api/v1/ml/models/:id          # Get model details
PUT    /api/v1/ml/models/:id/activate # Activate model
```

**Used by:** Lead enrichment workflows, AI response generation, scoring system, n8n workflows

---

## 6. Campaign Management

### Campaign CRUD
```http
GET    /api/v1/campaigns              # List campaigns
GET    /api/v1/campaigns/:id          # Get campaign detail
POST   /api/v1/campaigns              # Create campaign
PUT    /api/v1/campaigns/:id          # Update campaign
DELETE /api/v1/campaigns/:id          # Delete campaign
POST   /api/v1/campaigns/:id/duplicate # Duplicate campaign
```

### Campaign Execution
```http
POST   /api/v1/campaigns/:id/launch   # Launch campaign
POST   /api/v1/campaigns/:id/pause    # Pause campaign
POST   /api/v1/campaigns/:id/resume   # Resume campaign
POST   /api/v1/campaigns/:id/stop     # Stop campaign
POST   /api/v1/campaigns/:id/schedule # Schedule campaign
```

### Campaign Recipients
```http
GET    /api/v1/campaigns/:id/recipients # Get campaign recipients
POST   /api/v1/campaigns/:id/recipients # Add recipients
DELETE /api/v1/campaigns/:id/recipients/:leadId # Remove recipient
POST   /api/v1/campaigns/:id/test-send # Send test email
```

### Campaign Analytics
```http
GET    /api/v1/campaigns/:id/stats    # Get campaign statistics
GET    /api/v1/campaigns/:id/opens    # Get open tracking data
GET    /api/v1/campaigns/:id/clicks   # Get click tracking data
GET    /api/v1/campaigns/:id/replies  # Get reply tracking data
GET    /api/v1/campaigns/:id/bounces  # Get bounce data
GET    /api/v1/campaigns/:id/unsubscribes # Get unsubscribe data
GET    /api/v1/campaigns/:id/timeline # Get campaign timeline
```

**Used by:** Campaigns page, Campaign Detail page, Campaign Creation, Lead Detail page

---

## 7. Email Templates

### Template CRUD
```http
GET    /api/v1/templates              # List templates
GET    /api/v1/templates/:id          # Get template detail
POST   /api/v1/templates              # Create template
PUT    /api/v1/templates/:id          # Update template
DELETE /api/v1/templates/:id          # Delete template
POST   /api/v1/templates/:id/duplicate # Duplicate template
```

### Template Operations
```http
POST   /api/v1/templates/batch-duplicate # Bulk duplicate
DELETE /api/v1/templates/batch-delete # Bulk delete
PATCH  /api/v1/templates/:id/category # Update category
POST   /api/v1/templates/:id/favorite # Mark as favorite
DELETE /api/v1/templates/:id/favorite # Remove favorite
```

### Template Testing
```http
POST   /api/v1/templates/:id/preview  # Generate preview
POST   /api/v1/templates/:id/test     # Send test email
POST   /api/v1/templates/:id/validate # Validate template
POST   /api/v1/templates/render       # Render with variables
```

### Template Analytics
```http
GET    /api/v1/templates/:id/usage    # Get usage statistics
GET    /api/v1/templates/:id/performance # Get performance metrics
```

**Used by:** Templates page, Campaign creation, bulk template actions

---

## 8. Conversations & Auto-Response

### Conversations
```http
GET    /api/v1/conversations          # List conversations
GET    /api/v1/conversations/:id      # Get conversation detail
POST   /api/v1/conversations          # Create conversation
DELETE /api/v1/conversations/:id      # Delete conversation
PATCH  /api/v1/conversations/:id/status # Update status
```

### Messages
```http
GET    /api/v1/conversations/:id/messages # Get messages
POST   /api/v1/conversations/:id/messages # Send message
PUT    /api/v1/conversations/:id/messages/:msgId # Edit message
DELETE /api/v1/conversations/:id/messages/:msgId # Delete message
POST   /api/v1/conversations/:id/messages/:msgId/react # Add reaction
```

### Auto-Response
```http
GET    /api/v1/auto-responder/rules   # List auto-response rules
GET    /api/v1/auto-responder/rules/:id # Get rule detail
POST   /api/v1/auto-responder/rules   # Create rule
PUT    /api/v1/auto-responder/rules/:id # Update rule
DELETE /api/v1/auto-responder/rules/:id # Delete rule
PATCH  /api/v1/auto-responder/rules/:id/toggle # Enable/disable rule
POST   /api/v1/auto-responder/test    # Test rule matching
```

### AI Response Generation
```http
POST   /api/v1/conversations/:id/generate-response # Generate AI response
POST   /api/v1/conversations/:id/analyze # Analyze conversation
GET    /api/v1/conversations/:id/suggestions # Get response suggestions
```

**Used by:** Conversations page, Conversation Detail page, Auto-Responder page, Rule Builder

---

## 9. Approval Workflows

### Approvals
```http
GET    /api/v1/approvals              # List approvals
GET    /api/v1/approvals/:id          # Get approval detail
POST   /api/v1/approvals              # Create approval request
PUT    /api/v1/approvals/:id          # Update approval
DELETE /api/v1/approvals/:id          # Delete approval
```

### Approval Actions
```http
POST   /api/v1/approvals/:id/approve  # Approve request
POST   /api/v1/approvals/:id/reject   # Reject request
POST   /api/v1/approvals/:id/request-changes # Request changes
POST   /api/v1/approvals/:id/delegate # Delegate to another user
GET    /api/v1/approvals/:id/preview  # Preview approval content
```

### Approval Rules
```http
GET    /api/v1/approvals/rules        # List approval rules
GET    /api/v1/approvals/rules/:id    # Get rule detail
POST   /api/v1/approvals/rules        # Create rule
PUT    /api/v1/approvals/rules/:id    # Update rule
DELETE /api/v1/approvals/rules/:id    # Delete rule
PATCH  /api/v1/approvals/rules/:id/toggle # Enable/disable rule
POST   /api/v1/approvals/rules/test   # Test rule conditions
```

### Approval Stats
```http
GET    /api/v1/approvals/stats        # Get approval statistics
GET    /api/v1/approvals/pending      # Get pending approvals
GET    /api/v1/approvals/urgent       # Get urgent approvals
GET    /api/v1/approvals/history      # Get approval history
```

**Used by:** Approvals page, Approval Detail page, Approval Rules page, n8n workflows

---

## 10. n8n Workflow Integration

### Workflows
```http
GET    /api/v1/workflows              # List workflows
GET    /api/v1/workflows/:id          # Get workflow detail
POST   /api/v1/workflows              # Create workflow
PUT    /api/v1/workflows/:id          # Update workflow
DELETE /api/v1/workflows/:id          # Delete workflow
```

### Workflow Execution
```http
POST   /api/v1/workflows/:id/execute  # Trigger workflow execution
POST   /api/v1/workflows/:id/activate # Activate workflow
POST   /api/v1/workflows/:id/deactivate # Deactivate workflow
GET    /api/v1/workflows/:id/executions # Get execution history
GET    /api/v1/workflows/:id/executions/:execId # Get execution detail
POST   /api/v1/workflows/:id/executions/:execId/retry # Retry execution
```

### Workflow Testing
```http
POST   /api/v1/workflows/:id/test     # Test workflow
POST   /api/v1/workflows/:id/validate # Validate workflow definition
GET    /api/v1/workflows/:id/logs     # Get workflow logs
```

### Workflow Stats
```http
GET    /api/v1/workflows/stats        # Get workflow statistics
GET    /api/v1/workflows/:id/stats    # Get specific workflow stats
GET    /api/v1/workflows/failing      # Get failing workflows
GET    /api/v1/workflows/active       # Get active workflows
```

**Used by:** Workflows Dashboard, Workflow Detail page, n8n integration, automation triggers

---

## 11. Demo Sites & Videos

### Demo Sites
```http
GET    /api/v1/demo-sites             # List demo sites
GET    /api/v1/demo-sites/:id         # Get demo site detail
POST   /api/v1/demo-sites             # Create demo site
PUT    /api/v1/demo-sites/:id         # Update demo site
DELETE /api/v1/demo-sites/:id         # Delete demo site
```

### Demo Site Operations
```http
POST   /api/v1/demo-sites/analyze     # Analyze target website
POST   /api/v1/demo-sites/generate    # Generate demo site
POST   /api/v1/demo-sites/:id/deploy  # Deploy to Vercel
POST   /api/v1/demo-sites/:id/undeploy # Remove deployment
GET    /api/v1/demo-sites/:id/preview # Get preview URL
POST   /api/v1/demo-sites/:id/regenerate # Regenerate demo
```

### Videos
```http
GET    /api/v1/videos                 # List videos
GET    /api/v1/videos/:id             # Get video detail
POST   /api/v1/videos                 # Create video
DELETE /api/v1/videos/:id             # Delete video
```

### Video Operations
```http
POST   /api/v1/videos/generate        # Generate video from demo site
POST   /api/v1/videos/:id/process     # Process video
POST   /api/v1/videos/:id/voiceover   # Add voiceover
POST   /api/v1/videos/:id/publish     # Publish video
GET    /api/v1/videos/:id/status      # Get processing status
POST   /api/v1/videos/:id/download    # Download video file
```

**Used by:** Demo Sites page, Demo Site Detail page, Videos page, Video Detail page

---

## 12. Analytics & Reporting

### Dashboard Analytics
```http
GET    /api/v1/analytics/dashboard    # Get dashboard statistics
GET    /api/v1/analytics/overview     # Get system overview
GET    /api/v1/analytics/recent-activity # Get recent activity
GET    /api/v1/analytics/kpis         # Get key performance indicators
```

### Lead Analytics
```http
GET    /api/v1/analytics/leads        # Lead analytics
GET    /api/v1/analytics/leads/sources # Leads by source
GET    /api/v1/analytics/leads/status # Leads by status
GET    /api/v1/analytics/leads/timeline # Lead timeline data
GET    /api/v1/analytics/leads/conversion # Conversion funnel
```

### Campaign Analytics
```http
GET    /api/v1/analytics/campaigns    # Campaign analytics
GET    /api/v1/analytics/campaigns/performance # Performance metrics
GET    /api/v1/analytics/campaigns/comparison # Compare campaigns
GET    /api/v1/analytics/email-performance # Email performance
```

### Revenue Analytics
```http
GET    /api/v1/analytics/revenue      # Revenue statistics
GET    /api/v1/analytics/roi          # ROI calculations
GET    /api/v1/analytics/conversions  # Conversion tracking
GET    /api/v1/analytics/ltv          # Lifetime value metrics
```

### Reports
```http
GET    /api/v1/reports                # List saved reports
POST   /api/v1/reports/generate       # Generate custom report
GET    /api/v1/reports/:id            # Get report
DELETE /api/v1/reports/:id            # Delete report
GET    /api/v1/reports/:id/export     # Export report (PDF, Excel)
```

**Used by:** Dashboard, Analytics page, reporting features

---

## 13. Webhooks & External Integrations

### Webhooks
```http
GET    /api/v1/webhooks               # List webhooks
GET    /api/v1/webhooks/:id           # Get webhook detail
POST   /api/v1/webhooks               # Create webhook
PUT    /api/v1/webhooks/:id           # Update webhook
DELETE /api/v1/webhooks/:id           # Delete webhook
```

### Webhook Operations
```http
POST   /api/v1/webhooks/:id/test      # Test webhook
PATCH  /api/v1/webhooks/:id/toggle    # Enable/disable webhook
GET    /api/v1/webhooks/:id/logs      # Get webhook logs
POST   /api/v1/webhooks/:id/retry     # Retry failed webhook
```

### Incoming Webhooks
```http
POST   /webhooks/lead-created         # Lead creation webhook
POST   /webhooks/email-received       # Email received webhook
POST   /webhooks/high-priority-lead   # High priority lead webhook
POST   /webhooks/workflow-complete    # Workflow completion webhook
```

### External Services
```http
POST   /api/v1/integrations/n8n/sync  # Sync with n8n
POST   /api/v1/integrations/vercel/deploy # Deploy to Vercel
POST   /api/v1/integrations/slack/notify # Send Slack notification
GET    /api/v1/integrations/status    # Get integration status
```

**Used by:** Webhooks page, n8n workflows, external integrations

---

## 14. AI-GYM & Model Management

### Models
```http
GET    /api/v1/ai-gym/models          # List AI models
GET    /api/v1/ai-gym/models/:id      # Get model detail
POST   /api/v1/ai-gym/models          # Create/register model
PUT    /api/v1/ai-gym/models/:id      # Update model
DELETE /api/v1/ai-gym/models/:id      # Delete model
```

### Model Operations
```http
POST   /api/v1/ai-gym/models/:id/train # Train model
POST   /api/v1/ai-gym/models/:id/evaluate # Evaluate model
POST   /api/v1/ai-gym/models/:id/activate # Activate model
POST   /api/v1/ai-gym/models/:id/deactivate # Deactivate model
GET    /api/v1/ai-gym/models/:id/metrics # Get model metrics
```

### A/B Tests
```http
GET    /api/v1/ai-gym/ab-tests        # List A/B tests
GET    /api/v1/ai-gym/ab-tests/:id    # Get A/B test detail
POST   /api/v1/ai-gym/ab-tests        # Create A/B test
PUT    /api/v1/ai-gym/ab-tests/:id    # Update A/B test
DELETE /api/v1/ai-gym/ab-tests/:id    # Delete A/B test
```

### A/B Test Operations
```http
POST   /api/v1/ai-gym/ab-tests/:id/start # Start A/B test
POST   /api/v1/ai-gym/ab-tests/:id/stop # Stop A/B test
GET    /api/v1/ai-gym/ab-tests/:id/results # Get test results
POST   /api/v1/ai-gym/ab-tests/:id/select-winner # Select winning variant
```

### Model Metrics
```http
GET    /api/v1/ai-gym/metrics         # Get overall metrics
GET    /api/v1/ai-gym/leaderboard     # Get model leaderboard
GET    /api/v1/ai-gym/performance-history # Get performance over time
```

**Used by:** AI-GYM Dashboard, AI-GYM Models page, A/B Tests pages

---

## 15. Notifications & Real-time Updates

### Notifications
```http
GET    /api/v1/notifications          # List notifications
GET    /api/v1/notifications/unread   # Get unread count
PATCH  /api/v1/notifications/:id/read # Mark as read
PATCH  /api/v1/notifications/read-all # Mark all as read
DELETE /api/v1/notifications/:id      # Delete notification
DELETE /api/v1/notifications/clear-all # Clear all notifications
```

### Real-time WebSocket
```websocket
WS     /ws                            # WebSocket connection
```

**WebSocket Events:**
- `lead.created` - New lead created
- `lead.updated` - Lead updated
- `scrape.progress` - Scrape job progress
- `scrape.completed` - Scrape job completed
- `campaign.status` - Campaign status change
- `approval.pending` - New approval pending
- `approval.resolved` - Approval resolved
- `workflow.started` - Workflow started
- `workflow.completed` - Workflow completed
- `notification.new` - New notification

**Used by:** Notifications page, real-time updates across all pages, notification bell

---

## 16. File Operations

### File Upload
```http
POST   /api/v1/files/upload           # Upload file
POST   /api/v1/files/upload-multiple  # Upload multiple files
POST   /api/v1/files/upload-avatar    # Upload avatar
POST   /api/v1/files/upload-logo      # Upload company logo
```

### File Management
```http
GET    /api/v1/files                  # List files
GET    /api/v1/files/:id              # Get file detail
DELETE /api/v1/files/:id              # Delete file
GET    /api/v1/files/:id/download     # Download file
```

### Import/Export
```http
POST   /api/v1/import/leads           # Import leads from CSV
POST   /api/v1/import/templates       # Import templates
GET    /api/v1/export/leads           # Export leads to CSV
GET    /api/v1/export/campaigns       # Export campaigns
GET    /api/v1/export/analytics       # Export analytics report
```

**Used by:** Settings page, import/export features, file uploads

---

## 17. Location & Map Management

### Locations
```http
GET    /api/v1/locations              # List saved locations
GET    /api/v1/locations/:id          # Get location detail
POST   /api/v1/locations              # Add location
PUT    /api/v1/locations/:id          # Update location
DELETE /api/v1/locations/:id          # Delete location
```

### Location Operations
```http
GET    /api/v1/locations/search       # Search locations
GET    /api/v1/locations/nearby       # Get nearby locations
GET    /api/v1/locations/:id/leads    # Get leads from location
GET    /api/v1/locations/stats        # Get location statistics
```

### Map Data
```http
GET    /api/v1/map/leads              # Get leads for map display
GET    /api/v1/map/heatmap            # Get heatmap data
GET    /api/v1/map/clusters           # Get clustered location data
```

**Used by:** Location Map page, location-based filtering, scraper location selection

---

## 18. Scheduling

### Schedules
```http
GET    /api/v1/schedules              # List scheduled tasks
GET    /api/v1/schedules/:id          # Get schedule detail
POST   /api/v1/schedules              # Create schedule
PUT    /api/v1/schedules/:id          # Update schedule
DELETE /api/v1/schedules/:id          # Delete schedule
```

### Schedule Operations
```http
POST   /api/v1/schedules/:id/pause    # Pause schedule
POST   /api/v1/schedules/:id/resume   # Resume schedule
GET    /api/v1/schedules/:id/next-run # Get next run time
GET    /api/v1/schedules/:id/history  # Get execution history
POST   /api/v1/schedules/:id/run-now  # Execute immediately
```

**Used by:** Schedule page, campaign scheduling, automated scraping

---

## Implementation Priority

### Phase 1: Core Infrastructure (Weeks 1-2)
1. Authentication & Authorization
2. User Management & Settings
3. Database migrations & models
4. WebSocket infrastructure
5. File upload system

### Phase 2: Lead Management (Weeks 3-4)
1. Lead CRUD operations
2. Lead filtering & search
3. Lead enrichment endpoints
4. Lead AI analysis
5. Timeline & activity tracking

### Phase 3: Scraping Infrastructure (Weeks 5-7)
1. Craigslist scraping (existing)
2. Google Maps scraping
3. LinkedIn scraping
4. Job boards scraping
5. Social media scraping
6. Custom URL scraping
7. Scrape job management

### Phase 4: Communication & Campaigns (Weeks 8-10)
1. Email templates
2. Campaign management
3. Campaign execution & tracking
4. Conversations & messaging
5. Auto-response system
6. Email sending infrastructure

### Phase 5: Workflows & Approvals (Weeks 11-12)
1. n8n workflow integration
2. Approval workflow system
3. Approval rules engine
4. Webhook system
5. External integrations

### Phase 6: Demo Sites & Content (Weeks 13-14)
1. Demo site generation
2. Vercel deployment
3. Video generation
4. Video processing pipeline

### Phase 7: Analytics & AI (Weeks 15-16)
1. Analytics endpoints
2. Reporting system
3. AI-GYM model management
4. A/B testing framework
5. ML scoring system

### Phase 8: Polish & Optimization (Weeks 17-18)
1. Real-time notifications
2. Performance optimization
3. Caching layer
4. Error handling & logging
5. API documentation
6. Testing & QA

---

## Technical Stack Recommendations

### Backend Framework
- **FastAPI** (Python) - Current choice, excellent for APIs
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **Celery** - Async task queue for long-running operations
- **Redis** - Caching & Celery broker

### Database
- **PostgreSQL** - Primary database (already in use)
- **Redis** - Caching, session storage, real-time data

### Authentication
- **JWT** - Token-based authentication
- **Bcrypt** - Password hashing
- **OAuth2** - Third-party authentication

### External Services
- **n8n** - Workflow automation
- **Vercel API** - Demo site deployment
- **Hunter.io** - Email finding
- **Apollo.io** - Lead enrichment
- **OpenRouter/OpenAI** - AI/LLM operations
- **ElevenLabs** - Voice generation
- **FFmpeg** - Video processing

### Real-time
- **WebSocket** (FastAPI native)
- **Redis Pub/Sub** - Message broadcasting

### Email
- **SMTP** - Email sending
- **SendGrid/AWS SES** - Production email service
- **Mailgun** - Email tracking & webhooks

### Storage
- **AWS S3** or **Cloudinary** - File storage
- **Local storage** - Development

### Monitoring & Logging
- **Sentry** - Error tracking
- **LogDNA/DataDog** - Log management
- **Prometheus** - Metrics
- **Grafana** - Monitoring dashboards

---

## API Design Principles

### RESTful Conventions
- Use standard HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Use plural nouns for resources (`/leads`, `/campaigns`)
- Use nested routes for related resources (`/campaigns/:id/recipients`)
- Use query parameters for filtering, sorting, pagination

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Pagination
```http
GET /api/v1/leads?page=1&per_page=20&sort=-created_at
```

### Filtering
```http
GET /api/v1/leads?status=new&source=craigslist&min_score=7
```

### Versioning
- Use URL versioning: `/api/v1/`
- Maintain backward compatibility
- Deprecate old versions with warnings

### Rate Limiting
- Implement rate limiting per API key
- Return `429 Too Many Requests` when limit exceeded
- Include rate limit headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

### Security
- HTTPS only in production
- JWT authentication
- API key authentication for external services
- CORS configuration
- Input validation & sanitization
- SQL injection prevention (use ORM)
- XSS prevention
- CSRF protection

---

## Next Steps

1. **Review & Prioritize**: Review this plan and adjust priorities based on business needs
2. **Database Schema**: Design comprehensive database schema for all entities
3. **API Documentation**: Set up OpenAPI/Swagger documentation
4. **Development Environment**: Set up development environment with all services
5. **CI/CD Pipeline**: Set up automated testing and deployment
6. **Start Phase 1**: Begin implementation with core infrastructure

---

**Document Version:** 1.0
**Last Updated:** 2025-01-05
**Status:** Ready for Implementation
