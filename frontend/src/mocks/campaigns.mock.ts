/**
 * Mock email campaign data
 */

export type CampaignStatus = 'draft' | 'scheduled' | 'sending' | 'paused' | 'completed' | 'cancelled'
export type EmailStatus = 'queued' | 'sent' | 'delivered' | 'opened' | 'clicked' | 'replied' | 'bounced' | 'failed'

export interface EmailTemplate {
  id: number
  name: string
  description?: string
  category?: string
  subject: string
  body_html: string
  body_text: string
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

export interface MockCampaign {
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

export const mockCampaigns: MockCampaign[] = [
  // Active campaign in progress
  {
    id: 1,
    campaign_id: 'camp_abc123',
    name: 'Web Design Outreach - January 2025',
    subject: 'Transform Your Website with Modern Design',
    template_id: 1,
    status: 'sending',
    lead_filters: {
      sources: ['craigslist', 'google_maps'],
      tags: ['web-design'],
      has_email: true,
    },
    total_recipients: 150,
    scheduled_at: '2025-01-05T09:00:00Z',
    started_at: '2025-01-05T09:00:00Z',
    emails_sent: 87,
    emails_delivered: 82,
    emails_opened: 34,
    emails_clicked: 12,
    emails_replied: 3,
    emails_bounced: 5,
    emails_failed: 0,
    open_rate: 41.5,
    click_rate: 14.6,
    reply_rate: 3.7,
    bounce_rate: 6.1,
    send_rate_per_hour: 20,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: true,
    follow_up_delay_days: 3,
    estimated_cost: 15.0,
    actual_cost: 8.7,
    created_at: '2025-01-04T15:00:00Z',
    updated_at: '2025-01-05T14:30:00Z',
  },

  // Completed successful campaign
  {
    id: 2,
    campaign_id: 'camp_def456',
    name: 'SEO Services - December 2024',
    subject: 'Boost Your Google Rankings in 30 Days',
    template_id: 2,
    status: 'completed',
    lead_filters: {
      sources: ['craigslist'],
      tags: ['seo', 'marketing'],
      has_email: true,
    },
    total_recipients: 200,
    scheduled_at: '2024-12-15T10:00:00Z',
    started_at: '2024-12-15T10:00:00Z',
    completed_at: '2024-12-15T20:00:00Z',
    emails_sent: 200,
    emails_delivered: 188,
    emails_opened: 98,
    emails_clicked: 42,
    emails_replied: 15,
    emails_bounced: 12,
    emails_failed: 0,
    open_rate: 52.1,
    click_rate: 22.3,
    reply_rate: 8.0,
    bounce_rate: 6.4,
    send_rate_per_hour: 20,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: true,
    follow_up_delay_days: 5,
    estimated_cost: 20.0,
    actual_cost: 18.8,
    created_at: '2024-12-14T12:00:00Z',
    updated_at: '2024-12-15T20:00:00Z',
  },

  // Draft campaign
  {
    id: 3,
    campaign_id: 'camp_ghi789',
    name: 'LinkedIn Executives Outreach',
    subject: 'Exclusive Web Solutions for Tech Leaders',
    status: 'draft',
    lead_filters: {
      sources: ['linkedin'],
      tags: ['decision-maker', 'ceo'],
      has_email: true,
    },
    total_recipients: 45,
    emails_sent: 0,
    emails_delivered: 0,
    emails_opened: 0,
    emails_clicked: 0,
    emails_replied: 0,
    emails_bounced: 0,
    emails_failed: 0,
    open_rate: 0,
    click_rate: 0,
    reply_rate: 0,
    bounce_rate: 0,
    send_rate_per_hour: 10,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: false,
    estimated_cost: 4.5,
    actual_cost: 0,
    created_at: '2025-01-05T14:00:00Z',
    updated_at: '2025-01-05T14:00:00Z',
  },

  // Scheduled campaign
  {
    id: 4,
    campaign_id: 'camp_jkl012',
    name: 'Job Boards Follow-up',
    subject: 'We Can Build Your Team Landing Page',
    template_id: 3,
    status: 'scheduled',
    lead_filters: {
      sources: ['job_boards'],
      tags: ['hiring'],
      has_email: true,
    },
    total_recipients: 78,
    scheduled_at: '2025-01-06T10:00:00Z',
    emails_sent: 0,
    emails_delivered: 0,
    emails_opened: 0,
    emails_clicked: 0,
    emails_replied: 0,
    emails_bounced: 0,
    emails_failed: 0,
    open_rate: 0,
    click_rate: 0,
    reply_rate: 0,
    bounce_rate: 0,
    send_rate_per_hour: 15,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: true,
    follow_up_delay_days: 7,
    estimated_cost: 7.8,
    actual_cost: 0,
    created_at: '2025-01-05T13:00:00Z',
    updated_at: '2025-01-05T13:00:00Z',
  },

  // Paused campaign
  {
    id: 5,
    campaign_id: 'camp_mno345',
    name: 'Google Maps Local Businesses',
    subject: 'Free Website Audit for Local Businesses',
    template_id: 4,
    status: 'paused',
    lead_filters: {
      sources: ['google_maps'],
      has_email: true,
    },
    total_recipients: 120,
    scheduled_at: '2025-01-04T14:00:00Z',
    started_at: '2025-01-04T14:00:00Z',
    paused_at: '2025-01-04T16:30:00Z',
    emails_sent: 45,
    emails_delivered: 42,
    emails_opened: 18,
    emails_clicked: 6,
    emails_replied: 1,
    emails_bounced: 3,
    emails_failed: 0,
    open_rate: 42.9,
    click_rate: 14.3,
    reply_rate: 2.4,
    bounce_rate: 7.1,
    send_rate_per_hour: 20,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: true,
    follow_up_delay_days: 4,
    estimated_cost: 12.0,
    actual_cost: 4.5,
    created_at: '2025-01-04T12:00:00Z',
    updated_at: '2025-01-04T16:30:00Z',
  },
]

export const mockTemplates: EmailTemplate[] = [
  {
    id: 1,
    name: 'Web Design Introduction',
    description: 'Introduction email for web design services',
    category: 'Cold Outreach',
    subject: 'Transform Your Website with Modern Design',
    subject_template: 'Transform Your Website with Modern Design',
    body_template: `<p>Hi {{name}},</p>

<p>I came across your {{service_type}} business and noticed your website could benefit from a modern refresh.</p>

<p>We specialize in creating:</p>
<ul>
  <li>Mobile-responsive designs</li>
  <li>Fast-loading pages</li>
  <li>SEO-optimized content</li>
</ul>

<p>I've created a <strong>free demo</strong> of what your new site could look like: <a href="{{demo_url}}">View Demo</a></p>

<p>Would you be interested in a quick 15-minute call to discuss?</p>

<p>Best regards,<br>{{sender_name}}</p>`,
    body_html: `<p>Hi {{name}},</p>

<p>I came across your {{service_type}} business and noticed your website could benefit from a modern refresh.</p>

<p>We specialize in creating:</p>
<ul>
  <li>Mobile-responsive designs</li>
  <li>Fast-loading pages</li>
  <li>SEO-optimized content</li>
</ul>

<p>I've created a <strong>free demo</strong> of what your new site could look like: <a href="{{demo_url}}">View Demo</a></p>

<p>Would you be interested in a quick 15-minute call to discuss?</p>

<p>Best regards,<br>{{sender_name}}</p>`,
    body_text: `Hi {{name}},

I came across your {{service_type}} business and noticed your website could benefit from a modern refresh.

We specialize in creating:
- Mobile-responsive designs
- Fast-loading pages
- SEO-optimized content

I've created a free demo of what your new site could look like: {{demo_url}}

Would you be interested in a quick 15-minute call to discuss?

Best regards,
{{sender_name}}`,
    variables: {
      name: 'Recipient name',
      service_type: 'Business service type',
      demo_url: 'Demo URL',
      sender_name: 'Sender name'
    },
    use_ai_enhancement: false,
    ai_tone: 'professional',
    ai_length: 'medium',
    is_active: true,
    is_test_variant: false,
    test_weight: 50.0,
    sent_count: 245,
    response_count: 47,
    conversion_count: 12,
    response_rate: 19.2,
    conversion_rate: 4.9,
    tags: ['outreach', 'web-design'],
    created_at: '2025-01-03T10:00:00Z',
    updated_at: '2025-01-03T10:00:00Z',
  },
  {
    id: 2,
    name: 'SEO Services Pitch',
    description: 'SEO services pitch for businesses',
    category: 'Sales',
    subject: 'Boost Your Google Rankings in 30 Days',
    subject_template: 'Boost Your Google Rankings in 30 Days',
    body_template: `<p>Hi {{name}},</p>

<p>I noticed {{company_name}} isn't ranking for key terms like "{{keywords}}".</p>

<p>We've helped similar businesses increase their organic traffic by 200% in 30 days.</p>

<p><strong>Quick wins we can implement:</strong></p>
<ul>
  <li>Technical SEO fixes</li>
  <li>Content optimization</li>
  <li>Link building strategy</li>
</ul>

<p>Free audit available here: {{audit_url}}</p>

<p>Interested in learning more?</p>

<p>{{sender_name}}</p>`,
    body_html: `<p>Hi {{name}},</p>

<p>I noticed {{company_name}} isn't ranking for key terms like "{{keywords}}".</p>

<p>We've helped similar businesses increase their organic traffic by 200% in 30 days.</p>

<p><strong>Quick wins we can implement:</strong></p>
<ul>
  <li>Technical SEO fixes</li>
  <li>Content optimization</li>
  <li>Link building strategy</li>
</ul>

<p>Free audit available here: {{audit_url}}</p>

<p>Interested in learning more?</p>

<p>{{sender_name}}</p>`,
    body_text: `Hi {{name}},

I noticed {{company_name}} isn't ranking for key terms like "{{keywords}}".

We've helped similar businesses increase their organic traffic by 200% in 30 days.

Quick wins we can implement:
- Technical SEO fixes
- Content optimization
- Link building strategy

Free audit available here: {{audit_url}}

Interested in learning more?

{{sender_name}}`,
    variables: {
      name: 'Recipient name',
      company_name: 'Company name',
      keywords: 'Target keywords',
      audit_url: 'SEO audit URL',
      sender_name: 'Sender name'
    },
    use_ai_enhancement: true,
    ai_tone: 'friendly',
    ai_length: 'short',
    is_active: true,
    is_test_variant: false,
    test_weight: 50.0,
    sent_count: 187,
    response_count: 54,
    conversion_count: 18,
    response_rate: 28.9,
    conversion_rate: 9.6,
    tags: ['seo', 'growth'],
    created_at: '2025-01-02T14:00:00Z',
    updated_at: '2025-01-02T14:00:00Z',
  },
]

// Helper functions
export const getCampaignsByStatus = (status: CampaignStatus) =>
  mockCampaigns.filter(campaign => campaign.status === status)

export const getActiveCampaigns = () =>
  mockCampaigns.filter(campaign => ['sending', 'scheduled'].includes(campaign.status))

export const getCompletedCampaigns = () =>
  mockCampaigns.filter(campaign => campaign.status === 'completed')

export const getCampaignStats = () => ({
  total_campaigns: mockCampaigns.length,
  active: mockCampaigns.filter(c => c.status === 'sending').length,
  scheduled: mockCampaigns.filter(c => c.status === 'scheduled').length,
  completed: mockCampaigns.filter(c => c.status === 'completed').length,
  total_sent: mockCampaigns.reduce((sum, c) => sum + c.emails_sent, 0),
  total_opened: mockCampaigns.reduce((sum, c) => sum + c.emails_opened, 0),
  total_clicked: mockCampaigns.reduce((sum, c) => sum + c.emails_clicked, 0),
  total_replied: mockCampaigns.reduce((sum, c) => sum + c.emails_replied, 0),
  avg_open_rate: mockCampaigns.filter(c => c.emails_sent > 0).reduce((sum, c) => sum + c.open_rate, 0) / mockCampaigns.filter(c => c.emails_sent > 0).length || 0,
  avg_click_rate: mockCampaigns.filter(c => c.emails_sent > 0).reduce((sum, c) => sum + c.click_rate, 0) / mockCampaigns.filter(c => c.emails_sent > 0).length || 0,
  avg_reply_rate: mockCampaigns.filter(c => c.emails_sent > 0).reduce((sum, c) => sum + c.reply_rate, 0) / mockCampaigns.filter(c => c.emails_sent > 0).length || 0,
  total_cost: mockCampaigns.reduce((sum, c) => sum + c.actual_cost, 0),
})

export const getTopPerformingCampaigns = (limit: number = 5) =>
  [...mockCampaigns]
    .filter(c => c.emails_sent > 0)
    .sort((a, b) => b.reply_rate - a.reply_rate)
    .slice(0, limit)
