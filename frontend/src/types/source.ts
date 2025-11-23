// Multi-source type definitions
// Re-export from lead.ts for convenience

export type {
  LeadSource,
  SourceMetadata,
  Lead
} from './lead'

export { SOURCE_CONFIGS, getSourceConfig } from '@/components/SourceSelector'
export type { SourceConfig } from '@/components/SourceSelector'

// Source-specific scrape job payloads
export interface CraigslistScrapePayload {
  source: 'craigslist'
  location_ids: number[]
  categories?: string[]
  keywords?: string[]
  max_pages: number
  priority: 'low' | 'normal' | 'high'
  enable_email_extraction: boolean
  captcha_api_key?: string
}

export interface GoogleMapsScrapePayload {
  source: 'google_maps'
  location_ids: number[]
  business_category: string
  radius: number
  keywords?: string[]
  max_pages: number
  priority: 'low' | 'normal' | 'high'
  enable_email_extraction: boolean
  captcha_api_key?: string
}

export interface LinkedInScrapePayload {
  source: 'linkedin'
  location_ids: number[]
  keywords?: string[]
  company_size?: string
  max_pages: number
  priority: 'low' | 'normal' | 'high'
  enable_email_extraction: boolean
}

export interface JobBoardScrapePayload {
  source: 'indeed' | 'monster' | 'ziprecruiter'
  location_ids: number[]
  keywords?: string[]
  salary_range?: string
  max_pages: number
  priority: 'low' | 'normal' | 'high'
  enable_email_extraction: boolean
}

export type ScrapeJobPayload =
  | CraigslistScrapePayload
  | GoogleMapsScrapePayload
  | LinkedInScrapePayload
  | JobBoardScrapePayload

// Source statistics
export interface SourceStats {
  source: string
  count: number
  response_rate?: number
  conversion_rate?: number
  avg_qualification_score?: number
  last_scraped?: string
}

export interface SourceStatsResponse {
  by_source: Record<string, SourceStats>
  total_leads: number
  best_source?: SourceStats
}
