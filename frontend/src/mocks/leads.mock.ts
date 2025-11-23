/**
 * Mock lead data for all sources
 */

export interface MockLead {
  id: number
  title: string
  company_name: string
  website?: string
  email?: string
  phone?: string
  location: string
  description: string
  source: 'craigslist' | 'google_maps' | 'linkedin' | 'job_boards'
  status: 'new' | 'contacted' | 'replied' | 'qualified' | 'won' | 'lost'
  enrichment_status: 'pending' | 'enriching' | 'enriched' | 'failed'
  tags: string[]
  scraped_at: string
  original_url: string
  price?: number
  rating?: number
  review_count?: number
  has_demo_site: boolean
  has_video: boolean
}

export const mockLeads: MockLead[] = [
  // Craigslist Leads
  {
    id: 1,
    title: 'Web Design Services',
    company_name: 'Acme Design Studio',
    website: 'https://acmedesign.example.com',
    email: 'john@acmedesign.com',
    phone: '(415) 555-0123',
    location: 'San Francisco, CA',
    description: 'Professional web design services for small businesses. 10+ years experience.',
    source: 'craigslist',
    status: 'new',
    enrichment_status: 'enriched',
    tags: ['web-design', 'high-intent'],
    scraped_at: '2025-01-05T10:30:00Z',
    original_url: 'https://sfbay.craigslist.org/sfc/csr/d/web-design-services/1234567890.html',
    price: 500,
    has_demo_site: true,
    has_video: true,
  },
  {
    id: 2,
    title: 'SEO Expert Available',
    company_name: 'SEO Masters Inc',
    website: 'https://seomasters.example.com',
    email: 'contact@seomasters.com',
    phone: '(415) 555-0124',
    location: 'San Francisco, CA',
    description: 'Boost your Google rankings with our proven SEO strategies.',
    source: 'craigslist',
    status: 'contacted',
    enrichment_status: 'enriched',
    tags: ['seo', 'marketing'],
    scraped_at: '2025-01-05T10:35:00Z',
    original_url: 'https://sfbay.craigslist.org/sfc/csr/d/seo-expert/1234567891.html',
    has_demo_site: true,
    has_video: false,
  },
  {
    id: 3,
    title: 'Marketing Agency',
    company_name: 'Digital Growth Co',
    location: 'Los Angeles, CA',
    description: 'Full-service digital marketing agency. Get more leads today!',
    source: 'craigslist',
    status: 'new',
    enrichment_status: 'enriching',
    tags: ['marketing'],
    scraped_at: '2025-01-05T10:40:00Z',
    original_url: 'https://losangeles.craigslist.org/lac/csr/d/marketing-agency/1234567892.html',
    has_demo_site: false,
    has_video: false,
  },

  // Google Maps Leads
  {
    id: 4,
    title: 'Bay Area Web Design',
    company_name: 'Bay Area Web Design',
    website: 'https://bayareawebdesign.example.com',
    email: 'info@bayareawebdesign.com',
    phone: '(510) 555-0150',
    location: 'Oakland, CA',
    description: 'Award-winning web design agency serving the San Francisco Bay Area.',
    source: 'google_maps',
    status: 'new',
    enrichment_status: 'enriched',
    rating: 4.8,
    review_count: 127,
    tags: ['web-design', 'verified'],
    scraped_at: '2025-01-05T11:00:00Z',
    original_url: 'https://maps.google.com/?cid=1234567890',
    has_demo_site: false,
    has_video: false,
  },
  {
    id: 5,
    title: 'Modern Web Solutions',
    company_name: 'Modern Web Solutions',
    website: 'https://modernwebsolutions.example.com',
    email: 'hello@modernwebsolutions.com',
    phone: '(415) 555-0175',
    location: 'San Francisco, CA',
    description: 'Creating beautiful, functional websites for businesses of all sizes.',
    source: 'google_maps',
    status: 'replied',
    enrichment_status: 'enriched',
    rating: 4.9,
    review_count: 89,
    tags: ['web-design', 'qualified'],
    scraped_at: '2025-01-05T11:05:00Z',
    original_url: 'https://maps.google.com/?cid=1234567891',
    has_demo_site: true,
    has_video: true,
  },
  {
    id: 6,
    title: 'Creative Studio SF',
    company_name: 'Creative Studio SF',
    website: 'https://creativestudiosf.example.com',
    phone: '(415) 555-0180',
    location: 'San Francisco, CA',
    description: 'Branding and web design studio.',
    source: 'google_maps',
    status: 'new',
    enrichment_status: 'pending',
    rating: 4.6,
    review_count: 45,
    tags: ['web-design', 'branding'],
    scraped_at: '2025-01-05T11:10:00Z',
    original_url: 'https://maps.google.com/?cid=1234567892',
    has_demo_site: false,
    has_video: false,
  },

  // LinkedIn Leads
  {
    id: 7,
    title: 'Marketing Director at Tech Corp',
    company_name: 'Tech Corp',
    website: 'https://techcorp.example.com',
    email: 'jane.smith@techcorp.com',
    location: 'San Francisco, CA',
    description: 'Marketing Director with 10+ years experience in B2B SaaS.',
    source: 'linkedin',
    status: 'new',
    enrichment_status: 'enriched',
    tags: ['marketing', 'saas', 'decision-maker'],
    scraped_at: '2025-01-05T11:30:00Z',
    original_url: 'https://www.linkedin.com/in/janesmith',
    has_demo_site: false,
    has_video: false,
  },
  {
    id: 8,
    title: 'CEO at Startup Inc',
    company_name: 'Startup Inc',
    website: 'https://startupinc.example.com',
    email: 'ceo@startupinc.com',
    phone: '(650) 555-0200',
    location: 'Palo Alto, CA',
    description: 'Serial entrepreneur building the next big thing.',
    source: 'linkedin',
    status: 'qualified',
    enrichment_status: 'enriched',
    tags: ['startup', 'ceo', 'high-value'],
    scraped_at: '2025-01-05T11:35:00Z',
    original_url: 'https://www.linkedin.com/in/ceostartup',
    has_demo_site: true,
    has_video: false,
  },

  // Job Board Leads
  {
    id: 9,
    title: 'Web Developer Position',
    company_name: 'Enterprise Solutions Ltd',
    website: 'https://enterprisesolutions.example.com',
    email: 'hr@enterprisesolutions.com',
    phone: '(415) 555-0250',
    location: 'San Francisco, CA',
    description: 'Hiring experienced web developers for our growing team.',
    source: 'job_boards',
    status: 'new',
    enrichment_status: 'enriched',
    tags: ['hiring', 'web-development'],
    scraped_at: '2025-01-05T12:00:00Z',
    original_url: 'https://www.indeed.com/viewjob?jk=1234567890',
    has_demo_site: false,
    has_video: false,
  },
  {
    id: 10,
    title: 'Marketing Manager Needed',
    company_name: 'Growth Agency',
    website: 'https://growthagency.example.com',
    email: 'jobs@growthagency.com',
    location: 'Los Angeles, CA',
    description: 'Join our team as a Marketing Manager and drive growth.',
    source: 'job_boards',
    status: 'contacted',
    enrichment_status: 'enriched',
    tags: ['hiring', 'marketing'],
    scraped_at: '2025-01-05T12:05:00Z',
    original_url: 'https://www.monster.com/job/marketing-manager/12345',
    has_demo_site: false,
    has_video: false,
  },

  // More variety for testing
  {
    id: 11,
    title: 'Graphic Design Services',
    company_name: 'Design Pro',
    email: 'contact@designpro.com',
    location: 'New York, NY',
    description: 'Professional graphic design for all your needs.',
    source: 'craigslist',
    status: 'new',
    enrichment_status: 'failed',
    tags: ['design'],
    scraped_at: '2025-01-05T12:10:00Z',
    original_url: 'https://newyork.craigslist.org/mnh/csr/d/graphic-design/1234567893.html',
    has_demo_site: false,
    has_video: false,
  },
  {
    id: 12,
    title: 'Social Media Marketing',
    company_name: 'Social Boost',
    website: 'https://socialboost.example.com',
    email: 'team@socialboost.com',
    phone: '(212) 555-0300',
    location: 'New York, NY',
    description: 'Grow your social media presence with our expert team.',
    source: 'google_maps',
    status: 'won',
    enrichment_status: 'enriched',
    rating: 5.0,
    review_count: 234,
    tags: ['social-media', 'marketing', 'success'],
    scraped_at: '2025-01-04T10:00:00Z',
    original_url: 'https://maps.google.com/?cid=1234567893',
    has_demo_site: true,
    has_video: true,
  },
]

// Helper functions for filtering
export const getLeadsBySource = (source: MockLead['source']) =>
  mockLeads.filter(lead => lead.source === source)

export const getLeadsByStatus = (status: MockLead['status']) =>
  mockLeads.filter(lead => lead.status === status)

export const getLeadsWithEmail = () =>
  mockLeads.filter(lead => lead.email)

export const getLeadsWithDemoSite = () =>
  mockLeads.filter(lead => lead.has_demo_site)

export const getLeadsWithVideo = () =>
  mockLeads.filter(lead => lead.has_video)
