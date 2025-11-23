/**
 * Email Tracking API Service
 * Handles email tracking for opens, clicks, and engagement metrics
 */

import { api } from './api'

export interface EmailTrackingStats {
  total_sent: number
  total_delivered: number
  total_opened: number
  total_clicked: number
  total_bounced: number
  total_unsubscribed: number
  open_rate: number
  click_rate: number
  bounce_rate: number
  unique_opens: number
  unique_clicks: number
}

export interface CampaignTrackingStats extends EmailTrackingStats {
  campaign_id: string
  emails: EmailTracking[]
}

export interface EmailTracking {
  email_id: string
  lead_id: number
  lead_email: string
  status: 'sent' | 'delivered' | 'opened' | 'clicked' | 'bounced' | 'unsubscribed'
  sent_at?: string
  delivered_at?: string
  first_opened_at?: string
  last_opened_at?: string
  first_clicked_at?: string
  last_clicked_at?: string
  opens_count: number
  clicks_count: number
  bounce_reason?: string
  unsubscribed_at?: string
}

export interface TrackingEvent {
  event_type: 'open' | 'click' | 'bounce' | 'unsubscribe'
  timestamp: string
  user_agent?: string
  ip_address?: string
  location?: string
  device_type?: string
}

export const emailTrackingApi = {
  /**
   * Track email open event
   * Note: This is typically called automatically by email client
   * when loading the tracking pixel
   */
  trackOpen: (trackingToken: string) =>
    api.get(`/email-tracking/open/${trackingToken}`),

  /**
   * Track email click event
   * Creates a redirect URL for tracking
   */
  trackClick: (trackingToken: string, url: string) =>
    api.get(`/email-tracking/click/${trackingToken}`, {
      params: { url }
    }),

  /**
   * Create a tracking URL for a link
   * Returns the full tracking URL that redirects to the original
   */
  createTrackingUrl: (trackingToken: string, originalUrl: string): string => {
    const encodedUrl = encodeURIComponent(originalUrl)
    const baseUrl = api.defaults.baseURL?.replace('/api/v1', '') || 'http://localhost:8000'
    return `${baseUrl}/api/v1/email-tracking/click/${trackingToken}?url=${encodedUrl}`
  },

  /**
   * Get email tracking stats for a campaign
   */
  getCampaignTracking: (campaignId: string) =>
    api.get<CampaignTrackingStats>(`/campaigns/${campaignId}/tracking`),

  /**
   * Get email tracking stats for a specific email
   */
  getEmailTracking: (emailId: string) =>
    api.get<EmailTracking>(`/campaigns/emails/${emailId}/tracking`),

  /**
   * Get tracking events for a specific email
   */
  getEmailEvents: (emailId: string) =>
    api.get<TrackingEvent[]>(`/campaigns/emails/${emailId}/events`),

  /**
   * Mark email as unsubscribed
   */
  unsubscribe: (trackingToken: string, reason?: string) =>
    api.post(`/email-tracking/unsubscribe/${trackingToken}`, { reason }),

  /**
   * Get overall email tracking statistics
   */
  getOverallStats: (startDate?: string, endDate?: string) =>
    api.get<EmailTrackingStats>('/email-tracking/stats', {
      params: { start_date: startDate, end_date: endDate }
    }),

  /**
   * Get tracking stats for a specific lead
   */
  getLeadTrackingHistory: (leadId: number) =>
    api.get<EmailTracking[]>(`/leads/${leadId}/email-tracking`),

  /**
   * Get engagement timeline for a campaign
   */
  getCampaignTimeline: (campaignId: string, days: number = 30) =>
    api.get(`/campaigns/${campaignId}/tracking/timeline`, {
      params: { days }
    }),

  /**
   * Get best performing emails
   */
  getBestPerformingEmails: (limit: number = 10, metric: 'opens' | 'clicks' | 'replies' = 'opens') =>
    api.get('/email-tracking/best-performing', {
      params: { limit, metric }
    }),

  /**
   * Get email deliverability report
   */
  getDeliverabilityReport: (campaignId?: string) =>
    api.get('/email-tracking/deliverability', {
      params: { campaign_id: campaignId }
    }),

  /**
   * Get geographic distribution of opens/clicks
   */
  getGeoDistribution: (campaignId: string) =>
    api.get(`/campaigns/${campaignId}/tracking/geo-distribution`),

  /**
   * Get device/browser breakdown
   */
  getDeviceBreakdown: (campaignId: string) =>
    api.get(`/campaigns/${campaignId}/tracking/devices`),

  /**
   * Get engagement heatmap (by hour/day)
   */
  getEngagementHeatmap: (campaignId: string) =>
    api.get(`/campaigns/${campaignId}/tracking/heatmap`),

  /**
   * Verify tracking pixel is working
   */
  verifyTracking: (emailId: string) =>
    api.post(`/campaigns/emails/${emailId}/verify-tracking`),

  /**
   * Bulk mark emails as bounced
   */
  bulkMarkBounced: (emailIds: string[], reason: string) =>
    api.post('/email-tracking/bulk-bounce', {
      email_ids: emailIds,
      reason
    }),

  /**
   * Export tracking data as CSV
   */
  exportTrackingData: (campaignId: string) =>
    api.get(`/campaigns/${campaignId}/tracking/export`, {
      responseType: 'blob'
    }),
}

export default emailTrackingApi
