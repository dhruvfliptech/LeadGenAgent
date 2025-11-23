export type CampaignStatus = 'draft' | 'scheduled' | 'sending' | 'paused' | 'completed' | 'cancelled'
export type EmailStatus = 'queued' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'replied' | 'bounced' | 'failed'

export interface EmailTemplate {
  id: number
  name: string
  description?: string
  category?: string
  subject?: string
  body_html?: string
  body_text?: string
  subject_template: string
  body_template: string
  variables: Record<string, any>
  use_ai_enhancement: boolean
  ai_tone: string
  ai_length: string
  is_active: boolean
  is_test_variant: boolean
  control_template_id?: number
  test_weight: number
  sent_count: number
  response_count: number
  conversion_count: number
  response_rate: number
  conversion_rate: number
  tags?: string[]
  created_at: string
  updated_at: string
}

export interface EmailTemplateCreate {
  name: string
  description?: string
  category?: string
  subject_template: string
  body_template: string
  variables?: Record<string, any>
  use_ai_enhancement?: boolean
  ai_tone?: string
  ai_length?: string
  test_weight?: number
}

export interface EmailTemplateUpdate {
  name?: string
  description?: string
  category?: string
  subject_template?: string
  body_template?: string
  variables?: Record<string, any>
  use_ai_enhancement?: boolean
  ai_tone?: string
  ai_length?: string
  is_active?: boolean
  test_weight?: number
}

export interface CampaignEmail {
  id: number
  email_id: string
  campaign_id: string
  lead_id: number
  lead_email: string
  lead_name: string
  status: EmailStatus
  sent_at?: string
  delivered_at?: string
  opened_at?: string
  clicked_at?: string
  replied_at?: string
  bounce_reason?: string
  opens_count: number
  clicks_count: number
  created_at: string
}

export interface Campaign {
  id: number
  campaign_id: string
  name: string
  subject: string
  template_id?: number
  status: CampaignStatus

  // Targeting
  lead_filters: {
    sources?: string[]
    statuses?: string[]
    tags?: string[]
    has_email?: boolean
    has_phone?: boolean
  }
  total_recipients: number

  // Scheduling
  scheduled_at?: string
  started_at?: string
  completed_at?: string
  paused_at?: string

  // Progress
  emails_sent: number
  emails_delivered: number
  emails_opened: number
  emails_clicked: number
  emails_replied: number
  emails_bounced: number
  emails_failed: number

  // Metrics
  open_rate: number
  click_rate: number
  reply_rate: number
  bounce_rate: number

  // Settings
  send_rate_per_hour: number
  track_opens: boolean
  track_clicks: boolean
  follow_up_enabled: boolean
  follow_up_delay_days?: number

  // Costs
  estimated_cost: number
  actual_cost: number

  created_at: string
  updated_at: string
}

export interface CampaignStats {
  total_campaigns: number
  active: number
  scheduled: number
  completed: number
  total_sent: number
  total_opened: number
  total_clicked: number
  total_replied: number
  avg_open_rate: number
  avg_click_rate: number
  avg_reply_rate: number
  total_cost: number
}

export interface CampaignFormData {
  name: string
  subject: string
  template_id?: number
  body_html: string
  body_text: string
  lead_filters: {
    sources?: string[]
    statuses?: string[]
    tags?: string[]
    has_email?: boolean
  }
  scheduled_at?: string
  send_rate_per_hour: number
  track_opens: boolean
  track_clicks: boolean
  follow_up_enabled: boolean
  follow_up_delay_days?: number
}
