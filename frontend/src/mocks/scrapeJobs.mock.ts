/**
 * Mock scrape job data for all sources
 */

export type ScrapeSource = 'craigslist' | 'google_maps' | 'linkedin' | 'job_boards'
export type JobStatus = 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'

export interface ScrapeProgress {
  current: number
  total: number
  percentage: number
  rate_per_minute?: number
  estimated_time_remaining?: number
}

export interface ScrapeJobConfig {
  source: ScrapeSource
  locations?: string[]
  categories?: string[]
  keywords?: string[]
  max_results?: number
  include_contact_info?: boolean
  enable_enrichment?: boolean

  // Google Maps specific
  search_query?: string
  place_types?: string[]

  // LinkedIn specific
  company_size?: string[]
  industries?: string[]

  // Job Boards specific
  job_boards?: string[]
  job_types?: string[]
}

export interface MockScrapeJob {
  id: number
  job_id: string
  source: ScrapeSource
  status: JobStatus
  config: ScrapeJobConfig

  // Progress tracking
  progress: ScrapeProgress
  leads_found: number
  leads_enriched: number

  // Timing
  started_at?: string
  completed_at?: string
  paused_at?: string
  estimated_completion?: string

  // Error tracking
  error_message?: string
  errors_count: number
  captcha_challenges: number

  // Costs
  api_calls_made: number
  estimated_cost: number

  created_at: string
  updated_at: string
}

export const mockScrapeJobs: MockScrapeJob[] = [
  // Active Craigslist job
  {
    id: 1,
    job_id: 'job_cl_abc123',
    source: 'craigslist',
    status: 'running',
    config: {
      source: 'craigslist',
      locations: ['San Francisco, CA', 'Oakland, CA', 'San Jose, CA'],
      categories: ['computer services', 'web design'],
      keywords: ['web design', 'SEO', 'marketing'],
      max_results: 500,
      include_contact_info: true,
      enable_enrichment: true,
    },
    progress: {
      current: 127,
      total: 500,
      percentage: 25.4,
      rate_per_minute: 15,
      estimated_time_remaining: 1489,
    },
    leads_found: 127,
    leads_enriched: 45,
    started_at: '2025-01-05T14:30:00Z',
    estimated_completion: '2025-01-05T15:00:00Z',
    errors_count: 3,
    captcha_challenges: 1,
    api_calls_made: 45,
    estimated_cost: 2.25,
    created_at: '2025-01-05T14:25:00Z',
    updated_at: '2025-01-05T14:35:00Z',
  },

  // Completed Google Maps job
  {
    id: 2,
    job_id: 'job_gm_def456',
    source: 'google_maps',
    status: 'completed',
    config: {
      source: 'google_maps',
      search_query: 'web design agency',
      locations: ['San Francisco Bay Area'],
      place_types: ['web_design', 'marketing_agency'],
      max_results: 100,
      enable_enrichment: true,
    },
    progress: {
      current: 100,
      total: 100,
      percentage: 100,
    },
    leads_found: 100,
    leads_enriched: 95,
    started_at: '2025-01-05T10:00:00Z',
    completed_at: '2025-01-05T10:45:00Z',
    errors_count: 0,
    captcha_challenges: 0,
    api_calls_made: 95,
    estimated_cost: 4.75,
    created_at: '2025-01-05T09:55:00Z',
    updated_at: '2025-01-05T10:45:00Z',
  },

  // Queued LinkedIn job
  {
    id: 3,
    job_id: 'job_li_ghi789',
    source: 'linkedin',
    status: 'queued',
    config: {
      source: 'linkedin',
      keywords: ['marketing director', 'CMO'],
      locations: ['San Francisco', 'Palo Alto'],
      company_size: ['51-200', '201-500'],
      industries: ['SaaS', 'Technology'],
      max_results: 200,
      enable_enrichment: true,
    },
    progress: {
      current: 0,
      total: 200,
      percentage: 0,
    },
    leads_found: 0,
    leads_enriched: 0,
    errors_count: 0,
    captcha_challenges: 0,
    api_calls_made: 0,
    estimated_cost: 0,
    created_at: '2025-01-05T14:40:00Z',
    updated_at: '2025-01-05T14:40:00Z',
  },

  // Failed Craigslist job
  {
    id: 4,
    job_id: 'job_cl_jkl012',
    source: 'craigslist',
    status: 'failed',
    config: {
      source: 'craigslist',
      locations: ['New York, NY'],
      categories: ['computer services'],
      max_results: 300,
    },
    progress: {
      current: 45,
      total: 300,
      percentage: 15,
    },
    leads_found: 45,
    leads_enriched: 12,
    started_at: '2025-01-05T08:00:00Z',
    error_message: 'Too many CAPTCHA challenges - API key may be invalid',
    errors_count: 15,
    captcha_challenges: 10,
    api_calls_made: 12,
    estimated_cost: 0.60,
    created_at: '2025-01-05T07:55:00Z',
    updated_at: '2025-01-05T08:15:00Z',
  },

  // Paused Job Boards job
  {
    id: 5,
    job_id: 'job_jb_mno345',
    source: 'job_boards',
    status: 'paused',
    config: {
      source: 'job_boards',
      job_boards: ['Indeed', 'Monster', 'LinkedIn Jobs'],
      keywords: ['web developer', 'frontend engineer'],
      locations: ['Remote', 'San Francisco'],
      job_types: ['full-time', 'contract'],
      max_results: 150,
    },
    progress: {
      current: 67,
      total: 150,
      percentage: 44.7,
    },
    leads_found: 67,
    leads_enriched: 30,
    started_at: '2025-01-05T12:00:00Z',
    paused_at: '2025-01-05T12:30:00Z',
    errors_count: 2,
    captcha_challenges: 0,
    api_calls_made: 30,
    estimated_cost: 1.50,
    created_at: '2025-01-05T11:55:00Z',
    updated_at: '2025-01-05T12:30:00Z',
  },

  // Completed LinkedIn job
  {
    id: 6,
    job_id: 'job_li_pqr678',
    source: 'linkedin',
    status: 'completed',
    config: {
      source: 'linkedin',
      keywords: ['CEO', 'founder'],
      locations: ['San Francisco Bay Area'],
      company_size: ['11-50', '51-200'],
      industries: ['Startup', 'Technology'],
      max_results: 50,
      enable_enrichment: true,
    },
    progress: {
      current: 50,
      total: 50,
      percentage: 100,
    },
    leads_found: 50,
    leads_enriched: 48,
    started_at: '2025-01-04T16:00:00Z',
    completed_at: '2025-01-04T16:30:00Z',
    errors_count: 0,
    captcha_challenges: 0,
    api_calls_made: 48,
    estimated_cost: 2.40,
    created_at: '2025-01-04T15:55:00Z',
    updated_at: '2025-01-04T16:30:00Z',
  },
]

// Helper functions
export const getActiveJobs = () =>
  mockScrapeJobs.filter(job => job.status === 'running' || job.status === 'queued')

export const getJobsBySource = (source: ScrapeSource) =>
  mockScrapeJobs.filter(job => job.source === source)

export const getJobsByStatus = (status: JobStatus) =>
  mockScrapeJobs.filter(job => job.status === status)

export const getCompletedJobs = () =>
  mockScrapeJobs.filter(job => job.status === 'completed')

export const getFailedJobs = () =>
  mockScrapeJobs.filter(job => job.status === 'failed')

// Simulate WebSocket progress update
export const generateProgressUpdate = (job: MockScrapeJob) => ({
  job_id: job.job_id,
  status: job.status,
  progress: {
    ...job.progress,
    current: Math.min(job.progress.current + Math.floor(Math.random() * 5) + 1, job.progress.total),
  },
  leads_found: job.leads_found + Math.floor(Math.random() * 3),
  updated_at: new Date().toISOString(),
})

// Helper to get leads by source (for preview)
export const getLeadsBySource = (source: ScrapeSource) => {
  // This would normally come from the leads API
  return []
}
