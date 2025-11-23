import { Location } from './location'

export type LeadSource =
  | 'craigslist'
  | 'google_maps'
  | 'linkedin'
  | 'indeed'
  | 'monster'
  | 'ziprecruiter'
  | 'job_boards'

export interface SourceMetadata {
  // Craigslist specific
  craigslist_posting_id?: string
  craigslist_region?: string
  craigslist_category?: string
  craigslist_subcategory?: string
  craigslist_images?: string[]
  craigslist_post_flags?: string[]
  reply_to_address?: string

  // Google Maps specific
  rating?: number
  review_count?: number
  google_maps_url?: string
  google_place_id?: string
  business_category?: string
  business_type?: string
  address_full?: string
  neighborhood?: string
  website?: string
  hours_of_operation?: string
  price_level?: number
  accepts_credit_cards?: boolean
  accepts_cash?: boolean
  wheelchair_accessible?: boolean
  outdoor_seating?: boolean
  delivery_available?: boolean
  takeout_available?: boolean
  reservations_accepted?: boolean
  popular_times?: Record<string, string[]>

  // LinkedIn specific
  job_title?: string
  company_name?: string
  linkedin_url?: string
  company_size?: string
  industry?: string
  profile_headline?: string
  years_of_experience?: number
  education?: string
  skills?: string[]

  // Job boards specific (Indeed, Monster, ZipRecruiter)
  salary?: string
  posted_date?: string
  job_url?: string
  salary_range?: string

  // Social media specific
  social_platform?: string
  username?: string
  follower_count?: number
  post_url?: string
  engagement_metrics?: {
    likes?: number
    shares?: number
    comments?: number
  }

  // Audience Builder specific (Hunter.io, Apollo.io)
  verified_email?: boolean
  email_confidence_score?: number
  department?: string
  seniority_level?: string
  company_domain?: string
  company_revenue?: string

  // Custom URL scraper
  custom_fields?: Record<string, any>
}

export interface Lead {
  id: number
  craigslist_id: string
  title: string
  description?: string
  price?: number
  url: string
  email?: string
  phone?: string
  contact_name?: string
  compensation?: string
  employment_type?: string[]
  is_remote?: boolean
  reply_email?: string
  reply_phone?: string
  location: Location
  category?: string
  subcategory?: string
  is_processed: boolean
  is_contacted: boolean
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'rejected'
  qualification_score?: number
  qualification_reasoning?: string
  posted_at?: string
  scraped_at: string
  created_at: string
  updated_at: string

  // Multi-source fields
  source: LeadSource
  source_metadata?: SourceMetadata

  // AI MVP fields
  ai_analysis?: string
  ai_model?: string
  ai_cost?: number
  ai_request_id?: number
  generated_email_subject?: string
  generated_email_body?: string

  // User feedback for AI learning
  user_feedback?: 'positive' | 'negative' | null
}