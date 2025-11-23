/**
 * Mock webhook queue data
 */

export type WebhookStatus = 'queued' | 'sending' | 'delivered' | 'failed' | 'retrying'
export type WebhookEventType = 'lead.created' | 'lead.updated' | 'lead.enriched' | 'email.received' | 'email.sent' | 'demo_site.generated' | 'video.completed' | 'campaign.completed'

export interface MockWebhook {
  id: number
  webhook_id: string
  event_type: WebhookEventType
  status: WebhookStatus

  // Target
  target_url: string
  workflow_id?: string

  // Payload
  payload: Record<string, any>
  headers: Record<string, string>

  // Delivery attempts
  attempts: number
  max_attempts: number
  last_attempt_at?: string
  next_retry_at?: string

  // Response tracking
  response_status_code?: number
  response_body?: string
  response_time_ms?: number
  error_message?: string

  // Timing
  created_at: string
  delivered_at?: string
  failed_at?: string
}

export interface WebhookLog {
  id: number
  log_id: string
  webhook_id: string
  attempt_number: number
  timestamp: string
  request_headers: Record<string, string>
  request_body: Record<string, any>
  response_status_code?: number
  response_headers?: Record<string, string>
  response_body?: string
  response_time_ms?: number
  error_message?: string
  success: boolean
}

export const mockWebhooks: MockWebhook[] = [
  // Successfully delivered webhook
  {
    id: 1,
    webhook_id: 'wh_abc123',
    event_type: 'lead.created',
    status: 'delivered',
    target_url: 'https://n8n.example.com/webhook/lead-created',
    workflow_id: 'wf_enrich_abc123',
    payload: {
      event: 'lead.created',
      lead_id: 145,
      lead: {
        id: 145,
        title: 'New Web Design Lead',
        company_name: 'Test Company',
        website: 'https://testcompany.com',
        location: 'San Francisco, CA',
        source: 'craigslist',
        scraped_at: '2025-01-05T14:30:00Z',
      },
      timestamp: '2025-01-05T14:30:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'lead.created',
      'X-Webhook-ID': 'wh_abc123',
    },
    attempts: 1,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T14:30:00Z',
    response_status_code: 200,
    response_body: '{"status":"received","workflow_triggered":true}',
    response_time_ms: 234,
    created_at: '2025-01-05T14:30:00Z',
    delivered_at: '2025-01-05T14:30:00Z',
  },

  // Webhook currently sending
  {
    id: 2,
    webhook_id: 'wh_def456',
    event_type: 'email.received',
    status: 'sending',
    target_url: 'https://n8n.example.com/webhook/email-received',
    workflow_id: 'wf_email_def456',
    payload: {
      event: 'email.received',
      conversation_id: 'conv_abc123',
      message: {
        id: 4,
        from: 'john@acmedesign.com',
        to: 'sales@ourcompany.com',
        subject: 'Re: Transform Your Website with Modern Design',
        body: 'Friday afternoon works great for me...',
        received_at: '2025-01-05T14:30:00Z',
      },
      timestamp: '2025-01-05T14:30:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'email.received',
      'X-Webhook-ID': 'wh_def456',
    },
    attempts: 1,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T14:30:05Z',
    created_at: '2025-01-05T14:30:00Z',
  },

  // Failed webhook with retry
  {
    id: 3,
    webhook_id: 'wh_ghi789',
    event_type: 'demo_site.generated',
    status: 'retrying',
    target_url: 'https://n8n.example.com/webhook/demo-site-generated',
    workflow_id: 'wf_demo_jkl012',
    payload: {
      event: 'demo_site.generated',
      demo_site_id: 1,
      lead_id: 1,
      demo_site: {
        id: 1,
        build_id: 'build_react_abc123',
        framework: 'react',
        status: 'completed',
        preview_url: 'https://acme-design-demo.vercel.app',
      },
      timestamp: '2025-01-05T11:15:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'demo_site.generated',
      'X-Webhook-ID': 'wh_ghi789',
    },
    attempts: 2,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T11:20:00Z',
    next_retry_at: '2025-01-05T11:25:00Z',
    response_status_code: 500,
    response_body: '{"error":"Internal server error"}',
    response_time_ms: 5234,
    error_message: 'HTTP 500: Internal server error',
    created_at: '2025-01-05T11:15:00Z',
  },

  // Permanently failed webhook
  {
    id: 4,
    webhook_id: 'wh_jkl012',
    event_type: 'video.completed',
    status: 'failed',
    target_url: 'https://broken.example.com/webhook/video-completed',
    payload: {
      event: 'video.completed',
      video_id: 'vid_abc123',
      demo_site_id: 1,
      video: {
        id: 1,
        video_id: 'vid_abc123',
        status: 'completed',
        final_video_url: 'https://cdn.example.com/videos/vid_abc123.mp4',
        duration_seconds: 30,
      },
      timestamp: '2025-01-05T11:40:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'video.completed',
      'X-Webhook-ID': 'wh_jkl012',
    },
    attempts: 3,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T12:00:00Z',
    response_status_code: 404,
    error_message: 'HTTP 404: Endpoint not found after 3 attempts',
    created_at: '2025-01-05T11:40:00Z',
    failed_at: '2025-01-05T12:00:00Z',
  },

  // Queued webhook
  {
    id: 5,
    webhook_id: 'wh_mno345',
    event_type: 'campaign.completed',
    status: 'queued',
    target_url: 'https://n8n.example.com/webhook/campaign-completed',
    payload: {
      event: 'campaign.completed',
      campaign_id: 'camp_def456',
      campaign: {
        id: 2,
        campaign_id: 'camp_def456',
        name: 'SEO Services - December 2024',
        status: 'completed',
        total_recipients: 200,
        emails_sent: 200,
        open_rate: 52.1,
        reply_rate: 8.0,
      },
      timestamp: '2024-12-15T20:00:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'campaign.completed',
      'X-Webhook-ID': 'wh_mno345',
    },
    attempts: 0,
    max_attempts: 3,
    created_at: '2024-12-15T20:00:00Z',
  },

  // Lead enriched webhook - delivered
  {
    id: 6,
    webhook_id: 'wh_pqr678',
    event_type: 'lead.enriched',
    status: 'delivered',
    target_url: 'https://n8n.example.com/webhook/lead-enriched',
    workflow_id: 'wf_enrich_abc123',
    payload: {
      event: 'lead.enriched',
      lead_id: 145,
      enrichment_data: {
        email: 'contact@testcompany.com',
        phone: '(555) 123-4567',
        linkedin_url: 'https://linkedin.com/company/testcompany',
        employee_count: 25,
        annual_revenue: '$2M-$5M',
        enrichment_source: 'apollo.io',
      },
      timestamp: '2025-01-05T14:30:02Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'lead.enriched',
      'X-Webhook-ID': 'wh_pqr678',
    },
    attempts: 1,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T14:30:02Z',
    response_status_code: 200,
    response_body: '{"status":"received"}',
    response_time_ms: 156,
    created_at: '2025-01-05T14:30:02Z',
    delivered_at: '2025-01-05T14:30:02Z',
  },

  // Email sent webhook - delivered
  {
    id: 7,
    webhook_id: 'wh_stu901',
    event_type: 'email.sent',
    status: 'delivered',
    target_url: 'https://analytics.example.com/webhook/email-sent',
    payload: {
      event: 'email.sent',
      email_id: 'email_001',
      campaign_id: 'camp_abc123',
      recipient: 'john@acmedesign.com',
      subject: 'Transform Your Website with Modern Design',
      sent_at: '2025-01-05T10:00:00Z',
      timestamp: '2025-01-05T10:00:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'email.sent',
      'X-Webhook-ID': 'wh_stu901',
    },
    attempts: 1,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T10:00:00Z',
    response_status_code: 200,
    response_time_ms: 89,
    created_at: '2025-01-05T10:00:00Z',
    delivered_at: '2025-01-05T10:00:00Z',
  },

  // Lead updated webhook - delivered
  {
    id: 8,
    webhook_id: 'wh_vwx234',
    event_type: 'lead.updated',
    status: 'delivered',
    target_url: 'https://crm.example.com/webhook/lead-updated',
    payload: {
      event: 'lead.updated',
      lead_id: 1,
      changes: {
        status: {
          old: 'new',
          new: 'contacted',
        },
        last_contact_at: '2025-01-05T10:00:00Z',
      },
      timestamp: '2025-01-05T10:00:00Z',
    },
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'lead.updated',
      'X-Webhook-ID': 'wh_vwx234',
    },
    attempts: 1,
    max_attempts: 3,
    last_attempt_at: '2025-01-05T10:00:01Z',
    response_status_code: 201,
    response_body: '{"synced":true}',
    response_time_ms: 312,
    created_at: '2025-01-05T10:00:01Z',
    delivered_at: '2025-01-05T10:00:01Z',
  },
]

export const mockWebhookLogs: WebhookLog[] = [
  // First attempt - success
  {
    id: 1,
    log_id: 'log_001',
    webhook_id: 'wh_abc123',
    attempt_number: 1,
    timestamp: '2025-01-05T14:30:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'lead.created',
      'X-Webhook-ID': 'wh_abc123',
    },
    request_body: {
      event: 'lead.created',
      lead_id: 145,
    },
    response_status_code: 200,
    response_headers: {
      'content-type': 'application/json',
    },
    response_body: '{"status":"received","workflow_triggered":true}',
    response_time_ms: 234,
    success: true,
  },

  // First attempt - failed
  {
    id: 2,
    log_id: 'log_002',
    webhook_id: 'wh_ghi789',
    attempt_number: 1,
    timestamp: '2025-01-05T11:15:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'demo_site.generated',
      'X-Webhook-ID': 'wh_ghi789',
    },
    request_body: {
      event: 'demo_site.generated',
      demo_site_id: 1,
    },
    response_status_code: 500,
    response_body: '{"error":"Internal server error"}',
    response_time_ms: 5234,
    error_message: 'HTTP 500: Internal server error',
    success: false,
  },

  // Second attempt - still failed
  {
    id: 3,
    log_id: 'log_003',
    webhook_id: 'wh_ghi789',
    attempt_number: 2,
    timestamp: '2025-01-05T11:20:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'demo_site.generated',
      'X-Webhook-ID': 'wh_ghi789',
      'X-Retry-Attempt': '2',
    },
    request_body: {
      event: 'demo_site.generated',
      demo_site_id: 1,
    },
    response_status_code: 500,
    response_body: '{"error":"Internal server error"}',
    response_time_ms: 4892,
    error_message: 'HTTP 500: Internal server error',
    success: false,
  },

  // Failed webhook - all attempts exhausted
  {
    id: 4,
    log_id: 'log_004',
    webhook_id: 'wh_jkl012',
    attempt_number: 1,
    timestamp: '2025-01-05T11:40:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'video.completed',
    },
    request_body: {
      event: 'video.completed',
      video_id: 'vid_abc123',
    },
    response_status_code: 404,
    error_message: 'HTTP 404: Not Found',
    success: false,
  },
  {
    id: 5,
    log_id: 'log_005',
    webhook_id: 'wh_jkl012',
    attempt_number: 2,
    timestamp: '2025-01-05T11:45:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'video.completed',
      'X-Retry-Attempt': '2',
    },
    request_body: {
      event: 'video.completed',
      video_id: 'vid_abc123',
    },
    response_status_code: 404,
    error_message: 'HTTP 404: Not Found',
    success: false,
  },
  {
    id: 6,
    log_id: 'log_006',
    webhook_id: 'wh_jkl012',
    attempt_number: 3,
    timestamp: '2025-01-05T12:00:00Z',
    request_headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Event': 'video.completed',
      'X-Retry-Attempt': '3',
    },
    request_body: {
      event: 'video.completed',
      video_id: 'vid_abc123',
    },
    response_status_code: 404,
    error_message: 'HTTP 404: Not Found - Max retries exceeded',
    success: false,
  },
]

// Helper functions
export const getWebhooksByStatus = (status: WebhookStatus) =>
  mockWebhooks.filter(wh => wh.status === status)

export const getWebhooksByEvent = (eventType: WebhookEventType) =>
  mockWebhooks.filter(wh => wh.event_type === eventType)

export const getFailedWebhooks = () =>
  mockWebhooks.filter(wh => wh.status === 'failed' || wh.status === 'retrying')

export const getQueuedWebhooks = () =>
  mockWebhooks.filter(wh => wh.status === 'queued')

export const getWebhookLogs = (webhookId: string) =>
  mockWebhookLogs.filter(log => log.webhook_id === webhookId)

export const getWebhookStats = () => ({
  total: mockWebhooks.length,
  queued: mockWebhooks.filter(wh => wh.status === 'queued').length,
  sending: mockWebhooks.filter(wh => wh.status === 'sending').length,
  delivered: mockWebhooks.filter(wh => wh.status === 'delivered').length,
  failed: mockWebhooks.filter(wh => wh.status === 'failed').length,
  retrying: mockWebhooks.filter(wh => wh.status === 'retrying').length,
  success_rate: (mockWebhooks.filter(wh => wh.status === 'delivered').length / mockWebhooks.length) * 100,
  avg_response_time: mockWebhooks
    .filter(wh => wh.response_time_ms)
    .reduce((sum, wh) => sum + (wh.response_time_ms || 0), 0) /
    mockWebhooks.filter(wh => wh.response_time_ms).length || 0,
  by_event_type: {
    'lead.created': mockWebhooks.filter(wh => wh.event_type === 'lead.created').length,
    'lead.updated': mockWebhooks.filter(wh => wh.event_type === 'lead.updated').length,
    'lead.enriched': mockWebhooks.filter(wh => wh.event_type === 'lead.enriched').length,
    'email.received': mockWebhooks.filter(wh => wh.event_type === 'email.received').length,
    'email.sent': mockWebhooks.filter(wh => wh.event_type === 'email.sent').length,
    'demo_site.generated': mockWebhooks.filter(wh => wh.event_type === 'demo_site.generated').length,
    'video.completed': mockWebhooks.filter(wh => wh.event_type === 'video.completed').length,
    'campaign.completed': mockWebhooks.filter(wh => wh.event_type === 'campaign.completed').length,
  },
})
