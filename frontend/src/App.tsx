import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Leads from '@/pages/Leads'
import LeadsEnhanced from '@/pages/LeadsEnhanced'
import LeadDetail from '@/pages/LeadDetail'
import Scraper from '@/pages/Scraper'
import ScraperNew from '@/pages/ScraperNew'
import GoogleMapsScraper from '@/pages/GoogleMapsScraper'
import CraigslistScraper from '@/pages/CraigslistScraper'
import LinkedInScraper from '@/pages/LinkedInScraper'
import AudienceBuilder from '@/pages/AudienceBuilder'
import SocialMediaScraper from '@/pages/SocialMediaScraper'
import CustomUrlScraper from '@/pages/CustomUrlScraper'
import ScrapeJobs from '@/pages/ScrapeJobs'
import ScrapeJobDetail from '@/pages/ScrapeJobDetail'
import AutoResponder from '@/pages/AutoResponder'
import RuleBuilder from '@/pages/RuleBuilder'
import Notifications from '@/pages/Notifications'
import LocationMap from '@/pages/LocationMap'
import Schedule from '@/pages/Schedule'
import Analytics from '@/pages/Analytics'
import Approvals from '@/pages/Approvals'
import ApprovalsEnhanced from '@/pages/ApprovalsEnhanced'
import ApprovalDetail from '@/pages/ApprovalDetail'
import ApprovalRules from '@/pages/ApprovalRules'
import Conversations from '@/pages/Conversations'
import ConversationsEnhanced from '@/pages/ConversationsEnhanced'
import ConversationDetail from '@/pages/ConversationDetail'
import DemoSites from '@/pages/DemoSites'
import DemoSiteDetail from '@/pages/DemoSiteDetail'
import Videos from '@/pages/Videos'
import VideoDetail from '@/pages/VideoDetail'
import WorkflowDashboard from '@/pages/WorkflowDashboard'
import WorkflowsEnhanced from '@/pages/WorkflowsEnhanced'
import WorkflowDetail from '@/pages/WorkflowDetail'
import Webhooks from '@/pages/Webhooks'
import Campaigns from '@/pages/Campaigns'
import CampaignNew from '@/pages/CampaignNew'
import CampaignDetail from '@/pages/CampaignDetail'
import Templates from '@/pages/Templates'
import AIGym from '@/pages/AIGym'
import AIGymModels from '@/pages/AIGymModels'
import AIGymABTests from '@/pages/AIGymABTests'
import AIGymABTestDetail from '@/pages/AIGymABTestDetail'
import AIGymABTestNew from '@/pages/AIGymABTestNew'
import Settings from '@/pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        {/* Journey 1: Multi-Source Lead Scraping - Enhanced UI */}
        <Route path="/leads" element={<Leads />} />
        <Route path="/leads/:id" element={<LeadDetail />} />
        <Route path="/leads-mock" element={<LeadsEnhanced />} />
        <Route path="/scraper" element={<ScraperNew />} />
        <Route path="/scraper-old" element={<Scraper />} />
        <Route path="/scraper/google-maps" element={<GoogleMapsScraper />} />
        <Route path="/scraper/craigslist" element={<CraigslistScraper />} />
        <Route path="/scraper/linkedin" element={<LinkedInScraper />} />
        <Route path="/scraper/audience-builder" element={<AudienceBuilder />} />
        <Route path="/scraper/social-media" element={<SocialMediaScraper />} />
        <Route path="/scraper/custom-url" element={<CustomUrlScraper />} />
        <Route path="/scraper/jobs" element={<ScrapeJobs />} />
        <Route path="/scraper/jobs/:job_id" element={<ScrapeJobDetail />} />
        {/* New enhanced conversations with mock data */}
        <Route path="/conversations-new" element={<ConversationsEnhanced />} />
        <Route path="/conversations/:id" element={<ConversationDetail />} />
        {/* Original conversations page (API-based) */}
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/auto-responder" element={<AutoResponder />} />
        <Route path="/rules" element={<RuleBuilder />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/location-map" element={<LocationMap />} />
        <Route path="/schedule" element={<Schedule />} />
        <Route path="/analytics" element={<Analytics />} />
        {/* Journey 7: Approval Workflows & n8n Integration */}
        <Route path="/approvals-new" element={<ApprovalsEnhanced />} />
        <Route path="/approvals/:id" element={<ApprovalDetail />} />
        <Route path="/approvals/rules" element={<ApprovalRules />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/workflows-new" element={<WorkflowsEnhanced />} />
        <Route path="/workflows/:id" element={<WorkflowDetail />} />
        <Route path="/workflows" element={<WorkflowDashboard />} />
        <Route path="/webhooks" element={<Webhooks />} />
        {/* Journey 2: Website Analysis & Demo Site Generation */}
        <Route path="/demo-sites" element={<DemoSites />} />
        <Route path="/demo-sites/:id" element={<DemoSiteDetail />} />
        <Route path="/videos" element={<Videos />} />
        <Route path="/videos/:video_id" element={<VideoDetail />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/campaigns/new" element={<CampaignNew />} />
        <Route path="/campaigns/:id" element={<CampaignDetail />} />
        <Route path="/templates" element={<Templates />} />
        {/* Journey 6: AI-GYM Dashboard & Model Optimization */}
        <Route path="/ai-gym" element={<AIGym />} />
        <Route path="/ai-gym/models" element={<AIGymModels />} />
        <Route path="/ai-gym/ab-tests" element={<AIGymABTests />} />
        <Route path="/ai-gym/ab-tests/new" element={<AIGymABTestNew />} />
        <Route path="/ai-gym/ab-tests/:id" element={<AIGymABTestDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App