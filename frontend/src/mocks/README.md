# Mock Data Infrastructure

Complete mock data layer for all 7 user journeys. Use this data to build and test the frontend without requiring backend APIs.

## Files Created

1. **[leads.mock.ts](leads.mock.ts)** - 12 sample leads across all sources (Craigslist, Google Maps, LinkedIn, Job Boards)
2. **[scrapeJobs.mock.ts](scrapeJobs.mock.ts)** - 6 scrape jobs in various states (running, completed, failed, queued, paused)
3. **[analysis.mock.ts](analysis.mock.ts)** - 3 website analyses with detailed scores and improvements
4. **[demoSites.mock.ts](demoSites.mock.ts)** - 5 demo sites with generated code, deployment info, and metrics
5. **[videos.mock.ts](videos.mock.ts)** - 5 videos with scripts, voiceovers, recordings, and analytics
6. **[campaigns.mock.ts](campaigns.mock.ts)** - 5 email campaigns with engagement metrics and templates
7. **[conversations.mock.ts](conversations.mock.ts)** - 4 conversations with messages and AI suggestions
8. **[models.mock.ts](models.mock.ts)** - AI model configs, performance data, and A/B tests for AI-GYM
9. **[approvals.mock.ts](approvals.mock.ts)** - 7 approval requests with risk assessment and rules
10. **[workflows.mock.ts](workflows.mock.ts)** - 5 n8n workflows with nodes, connections, and execution history
11. **[webhooks.mock.ts](webhooks.mock.ts)** - 8 webhook deliveries with retry logic and logs

## Usage

Import mock data in your components:

```typescript
// Import specific mocks
import { mockLeads, getLeadsBySource } from '@/mocks/leads.mock'
import { mockScrapeJobs, getActiveJobs } from '@/mocks/scrapeJobs.mock'

// Or import everything
import { mockLeads, mockCampaigns, mockVideos } from '@/mocks'

// Use helper functions
const craigslistLeads = getLeadsBySource('craigslist')
const activeJobs = getActiveJobs()
const pendingApprovals = getPendingApprovals()
```

## Data Coverage

### Journey 1: Multi-Source Scraping
- **Leads**: 12 samples across 4 sources with variety of statuses
- **Scrape Jobs**: 6 jobs showing all states (queued, running, paused, completed, failed)
- **Helper Functions**: Filter by source, status, enrichment state

### Journey 2: Website Analysis → Demo Site
- **Analyses**: 3 analyses (high quality, poor quality, in-progress)
- **Demo Sites**: 5 sites with React, Next.js, and HTML frameworks
- **Improvements**: Detailed improvement plans with priorities
- **Metrics**: Design, SEO, performance, accessibility scores

### Journey 3: Demo Site → Video
- **Videos**: 5 videos in various states (draft, generating, completed, failed)
- **Scripts**: Complete narration with scene breakdowns
- **Voiceovers**: ElevenLabs, OpenAI, Google TTS samples
- **Recordings**: Screen recordings with action tracking
- **Analytics**: View counts, watch percentages, shares

### Journey 4: Email Outreach
- **Campaigns**: 5 campaigns (active, completed, draft, scheduled, paused)
- **Templates**: 2 email templates with variables
- **Metrics**: Open rates, click rates, reply rates, bounce rates
- **Progress Tracking**: Real-time sending progress

### Journey 5: Conversation AI
- **Conversations**: 4 conversations with different priorities
- **Messages**: Full email threads with sentiment analysis
- **AI Suggestions**: Multiple AI-generated response options
- **Risk Assessment**: Key points, questions, sentiment scores

### Journey 6: AI-GYM
- **Models**: 6 AI models (Claude, GPT-4, Gemini, DeepSeek)
- **Performance**: Request counts, quality scores, costs, response times
- **A/B Tests**: Running and completed tests with results
- **Quality Metrics**: User feedback and response quality tracking

### Journey 7: Approvals & Workflows
- **Approvals**: 7 requests across different types and risk levels
- **Workflows**: 5 n8n workflows with visual node graphs
- **Executions**: Workflow run history with timing and results
- **Webhooks**: 8 webhook deliveries with retry logic

## Mock Data Features

All mock data includes:

- **Realistic IDs**: Unique identifiers following backend patterns
- **Timestamps**: ISO 8601 formatted dates
- **Status Tracking**: Multiple states per entity type
- **Metrics & Analytics**: Performance data, costs, success rates
- **Relationships**: Cross-references between related entities
- **Edge Cases**: Errors, failures, retries, edge states
- **Helper Functions**: Common filtering and aggregation operations

## Testing Scenarios

The mock data covers:

1. **Happy Paths**: Successful completions and workflows
2. **Error States**: Failed jobs, rejected approvals, webhook retries
3. **In-Progress**: Active scraping, generating content, sending emails
4. **High Priority**: Urgent conversations, critical approvals
5. **Historical**: Completed campaigns, archived workflows
6. **Analytics**: View counts, engagement metrics, performance data

## Next Steps

Use this mock data to implement:

1. Source selection and scraping wizards
2. Analysis results and improvement recommendations
3. Demo site previews and code viewers
4. Video player with scripts and analytics
5. Campaign builder and monitoring dashboards
6. Conversation inbox with AI suggestions
7. AI-GYM model performance comparison
8. Approval queue with risk assessment
9. Workflow visual editor and execution logs
10. Webhook delivery monitoring

All UI components can be built and tested locally using this comprehensive mock data layer.
