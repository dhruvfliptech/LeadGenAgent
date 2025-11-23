import axios from 'axios'

// Use Vite env vars (process.env is not available in the browser by default)
const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Feature flags - aligned with backend reality
// These features are currently disabled because backend endpoints/services are broken
// See: backend CRITICAL_BUGS_FOUND.md for details
const FEATURES_ENABLED = {
  templates: false,        // Disabled - backend router commented out
  rules: false,            // Disabled - backend router commented out
  notifications: false,    // Disabled - backend router commented out
  schedules: false,        // Disabled - backend router commented out
  analytics: false,        // Disabled - not fully implemented
  exports: false,          // Disabled - export service has DB access issues
  abTesting: false,        // Disabled - not implemented
  locationGroups: false,   // Disabled - not implemented
}

// Helper to return disabled feature response
const disabledFeature = <T>(featureName: string, defaultValue: T): Promise<{ data: T }> => {
  console.warn(`[Phase 3] Feature '${featureName}' is currently disabled. Returning empty data.`)
  return Promise.resolve({ data: defaultValue })
}

// Types for Phase 3 features
export interface Template {
  id: number
  name: string
  subject: string
  content: string
  variables: string[]
  category: string
  is_active: boolean
  performance_metrics?: {
    open_rate: number
    response_rate: number
    conversion_rate: number
    total_sent: number
  }
  ab_test_data?: {
    variant_a_stats: PerformanceMetrics
    variant_b_stats: PerformanceMetrics
    winner?: 'A' | 'B'
    confidence_level?: number
  }
  created_at: string
  updated_at: string
}

export interface PerformanceMetrics {
  open_rate: number
  response_rate: number
  conversion_rate: number
  total_sent: number
}

export interface Rule {
  id: number
  name: string
  description?: string
  conditions: RuleCondition[]
  actions: RuleAction[]
  logic_operator: 'AND' | 'OR'
  is_active: boolean
  priority: number
  exclude_lists: string[]
  created_at: string
  updated_at: string
}

export interface RuleCondition {
  id: string
  field: string
  operator: 'equals' | 'contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'in' | 'not_in'
  value: string | number | string[]
  logic_operator?: 'AND' | 'OR' | 'NOT'
}

export interface RuleAction {
  id: string
  type: 'send_template' | 'add_tag' | 'set_status' | 'create_task' | 'webhook'
  parameters: Record<string, any>
}

export interface Notification {
  id: number
  title: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  channel: 'email' | 'sms' | 'webhook' | 'in_app'
  status: 'pending' | 'sent' | 'delivered' | 'failed'
  recipient: string
  metadata?: Record<string, any>
  created_at: string
  read_at?: string
}

export interface NotificationTemplate {
  id: number
  name: string
  channel: 'email' | 'sms' | 'webhook' | 'in_app'
  subject?: string
  content: string
  variables: string[]
  is_active: boolean
  created_at: string
}

export interface Schedule {
  id: number
  name: string
  description?: string
  cron_expression: string
  task_type: 'scrape' | 'send_emails' | 'export_data' | 'cleanup' | 'custom'
  task_config: Record<string, any>
  is_active: boolean
  last_run?: string
  next_run: string
  status: 'idle' | 'running' | 'failed' | 'success'
  created_at: string
}

export interface ScheduleLog {
  id: number
  schedule_id: number
  status: 'running' | 'success' | 'failed'
  message?: string
  duration?: number
  started_at: string
  completed_at?: string
}

export interface AnalyticsData {
  lead_funnel: {
    total_scraped: number
    total_contacted: number
    total_responded: number
    total_converted: number
  }
  roi_metrics: {
    total_revenue: number
    total_cost: number
    roi_percentage: number
    cost_per_lead: number
    revenue_per_lead: number
  }
  performance_trends: {
    date: string
    leads_scraped: number
    emails_sent: number
    responses_received: number
    conversions: number
  }[]
  top_performing_templates: Template[]
  location_performance: {
    location: string
    lead_count: number
    conversion_rate: number
    revenue: number
  }[]
}

// Auto-Responder API
export const autoResponderApi = {
  // Templates
  getTemplates: () =>
    FEATURES_ENABLED.templates
      ? api.get<Template[]>('/api/v1/templates')
      : disabledFeature('templates', [] as Template[]),

  createTemplate: (template: Omit<Template, 'id' | 'created_at' | 'updated_at'>) =>
    FEATURES_ENABLED.templates
      ? api.post<Template>('/api/v1/templates', template)
      : Promise.reject(new Error('Templates feature is currently disabled')),

  updateTemplate: (id: number, template: Partial<Template>) =>
    FEATURES_ENABLED.templates
      ? api.put<Template>(`/api/v1/templates/${id}`, template)
      : Promise.reject(new Error('Templates feature is currently disabled')),

  deleteTemplate: (id: number) =>
    FEATURES_ENABLED.templates
      ? api.delete(`/api/v1/templates/${id}`)
      : Promise.reject(new Error('Templates feature is currently disabled')),

  // A/B Testing
  createABTest: (templateId: number, variantB: Partial<Template>) =>
    FEATURES_ENABLED.abTesting
      ? api.post(`/api/v1/templates/${templateId}/ab-test`, variantB)
      : Promise.reject(new Error('A/B Testing feature is currently disabled')),

  getABTestResults: (templateId: number) =>
    FEATURES_ENABLED.abTesting
      ? api.get(`/api/v1/templates/${templateId}/ab-test/results`)
      : disabledFeature('abTesting', {}),

  // Template performance
  getTemplatePerformance: (templateId: number, dateRange?: { start: string; end: string }) =>
    FEATURES_ENABLED.templates
      ? api.get(`/api/v1/templates/${templateId}/performance`, { params: dateRange })
      : disabledFeature('templates.performance', {}),
}

// Rule Engine API
export const ruleEngineApi = {
  getRules: () =>
    FEATURES_ENABLED.rules
      ? api.get<Rule[]>('/api/v1/rules')
      : disabledFeature('rules', [] as Rule[]),

  createRule: (rule: Omit<Rule, 'id' | 'created_at' | 'updated_at'>) =>
    FEATURES_ENABLED.rules
      ? api.post<Rule>('/api/v1/rules', rule)
      : Promise.reject(new Error('Rules feature is currently disabled')),

  updateRule: (id: number, rule: Partial<Rule>) =>
    FEATURES_ENABLED.rules
      ? api.put<Rule>(`/api/v1/rules/${id}`, rule)
      : Promise.reject(new Error('Rules feature is currently disabled')),

  deleteRule: (id: number) =>
    FEATURES_ENABLED.rules
      ? api.delete(`/api/v1/rules/${id}`)
      : Promise.reject(new Error('Rules feature is currently disabled')),

  testRule: (rule: Omit<Rule, 'id' | 'created_at' | 'updated_at'>, testData: any) =>
    FEATURES_ENABLED.rules
      ? api.post('/api/v1/rules/test', { rule, testData })
      : Promise.reject(new Error('Rules feature is currently disabled')),

  // Exclude lists
  getExcludeLists: () =>
    FEATURES_ENABLED.rules
      ? api.get<string[]>('/api/v1/rules/exclude-lists')
      : disabledFeature('rules.excludeLists', [] as string[]),

  createExcludeList: (name: string, emails: string[]) =>
    FEATURES_ENABLED.rules
      ? api.post('/api/v1/rules/exclude-lists', { name, emails })
      : Promise.reject(new Error('Rules feature is currently disabled')),

  deleteExcludeList: (name: string) =>
    FEATURES_ENABLED.rules
      ? api.delete(`/api/v1/rules/exclude-lists/${name}`)
      : Promise.reject(new Error('Rules feature is currently disabled')),
}

// Notifications API
export const notificationsApi = {
  getNotifications: (params?: { page?: number; limit?: number; unread_only?: boolean }) =>
    FEATURES_ENABLED.notifications
      ? api.get<{ notifications: Notification[]; total: number }>('/api/v1/notifications', { params })
      : disabledFeature('notifications', { notifications: [] as Notification[], total: 0 }),

  markAsRead: (id: number) =>
    FEATURES_ENABLED.notifications
      ? api.patch(`/api/v1/notifications/${id}/read`)
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  markAllAsRead: () =>
    FEATURES_ENABLED.notifications
      ? api.patch('/api/v1/notifications/read-all')
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  deleteNotification: (id: number) =>
    FEATURES_ENABLED.notifications
      ? api.delete(`/api/v1/notifications/${id}`)
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  // Notification templates
  getNotificationTemplates: () =>
    FEATURES_ENABLED.notifications
      ? api.get<NotificationTemplate[]>('/api/v1/notifications/templates')
      : disabledFeature('notifications.templates', [] as NotificationTemplate[]),

  createNotificationTemplate: (template: Omit<NotificationTemplate, 'id' | 'created_at'>) =>
    FEATURES_ENABLED.notifications
      ? api.post<NotificationTemplate>('/api/v1/notifications/templates', template)
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  updateNotificationTemplate: (id: number, template: Partial<NotificationTemplate>) =>
    FEATURES_ENABLED.notifications
      ? api.put<NotificationTemplate>(`/api/v1/notifications/templates/${id}`, template)
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  deleteNotificationTemplate: (id: number) =>
    FEATURES_ENABLED.notifications
      ? api.delete(`/api/v1/notifications/templates/${id}`)
      : Promise.reject(new Error('Notifications feature is currently disabled')),

  // Channel preferences
  getChannelPreferences: () =>
    FEATURES_ENABLED.notifications
      ? api.get('/api/v1/notifications/preferences')
      : disabledFeature('notifications.preferences', {}),

  updateChannelPreferences: (preferences: Record<string, any>) =>
    FEATURES_ENABLED.notifications
      ? api.put('/api/v1/notifications/preferences', preferences)
      : Promise.reject(new Error('Notifications feature is currently disabled')),
}

// Schedule API
export const scheduleApi = {
  getSchedules: () =>
    FEATURES_ENABLED.schedules
      ? api.get<Schedule[]>('/api/v1/schedules')
      : disabledFeature('schedules', [] as Schedule[]),

  createSchedule: (schedule: Omit<Schedule, 'id' | 'created_at' | 'next_run' | 'status'>) =>
    FEATURES_ENABLED.schedules
      ? api.post<Schedule>('/api/v1/schedules', schedule)
      : Promise.reject(new Error('Schedules feature is currently disabled')),

  updateSchedule: (id: number, schedule: Partial<Schedule>) =>
    FEATURES_ENABLED.schedules
      ? api.put<Schedule>(`/api/v1/schedules/${id}`, schedule)
      : Promise.reject(new Error('Schedules feature is currently disabled')),

  deleteSchedule: (id: number) =>
    FEATURES_ENABLED.schedules
      ? api.delete(`/api/v1/schedules/${id}`)
      : Promise.reject(new Error('Schedules feature is currently disabled')),

  runSchedule: (id: number) =>
    FEATURES_ENABLED.schedules
      ? api.post(`/api/v1/schedules/${id}/run`)
      : Promise.reject(new Error('Schedules feature is currently disabled')),

  // Schedule logs
  getScheduleLogs: (scheduleId: number, params?: { page?: number; limit?: number }) =>
    FEATURES_ENABLED.schedules
      ? api.get<{ logs: ScheduleLog[]; total: number }>(`/api/v1/schedules/${scheduleId}/logs`, { params })
      : disabledFeature('schedules.logs', { logs: [] as ScheduleLog[], total: 0 }),

  // Cron validation
  validateCron: (expression: string) =>
    FEATURES_ENABLED.schedules
      ? api.post<{ valid: boolean; next_runs: string[]; error?: string }>('/api/v1/schedules/validate-cron', {
          expression,
        })
      : disabledFeature('schedules.validateCron', { valid: false, next_runs: [], error: 'Feature disabled' }),
}

// Analytics API
export const analyticsApi = {
  getDashboardData: (dateRange?: { start: string; end: string }) =>
    FEATURES_ENABLED.analytics
      ? api.get<AnalyticsData>('/api/v1/analytics/dashboard', { params: dateRange })
      : disabledFeature('analytics.dashboard', {} as AnalyticsData),

  getLeadFunnel: (dateRange?: { start: string; end: string }) =>
    FEATURES_ENABLED.analytics
      ? api.get('/api/v1/analytics/lead-funnel', { params: dateRange })
      : disabledFeature('analytics.leadFunnel', {}),

  getROIMetrics: (dateRange?: { start: string; end: string }) =>
    FEATURES_ENABLED.analytics
      ? api.get('/api/v1/analytics/roi', { params: dateRange })
      : disabledFeature('analytics.roi', {}),

  getPerformanceTrends: (dateRange?: { start: string; end: string }) =>
    FEATURES_ENABLED.analytics
      ? api.get('/api/v1/analytics/trends', { params: dateRange })
      : disabledFeature('analytics.trends', {}),

  exportData: (type: 'leads' | 'templates' | 'notifications' | 'schedules', filters?: Record<string, any>) =>
    FEATURES_ENABLED.exports
      ? api.post(`/api/v1/exports/${type}`, filters, { responseType: 'blob' })
      : Promise.reject(new Error('Export feature is currently disabled')),
}

// Location API extensions
export const locationApi = {
  // These core location endpoints work
  getLocationStats: () => api.get('/api/v1/locations/stats'),
  getHeatMapData: () => api.get('/api/v1/locations/heatmap'),
  getLocations: (params?: any) => api.get('/api/v1/locations', { params }),
  getLocationsTree: (params?: any) => api.get('/api/v1/locations/tree', { params }),
  getUSStates: () => api.get('/api/v1/locations/us/states'),
  getLocationsByState: (state: string, activeOnly = true) =>
    api.get('/api/v1/locations/by_state', { params: { state, active_only: activeOnly } }),

  // Location groups/presets - disabled (not implemented yet)
  getLocationGroups: () =>
    FEATURES_ENABLED.locationGroups
      ? api.get('/api/v1/locations/groups')
      : disabledFeature('locationGroups', []),

  createLocationGroup: (name: string, locations: string[]) =>
    FEATURES_ENABLED.locationGroups
      ? api.post('/api/v1/locations/groups', { name, locations })
      : Promise.reject(new Error('Location groups feature is currently disabled')),

  updateLocationGroup: (id: number, data: { name?: string; locations?: string[] }) =>
    FEATURES_ENABLED.locationGroups
      ? api.put(`/api/v1/locations/groups/${id}`, data)
      : Promise.reject(new Error('Location groups feature is currently disabled')),

  deleteLocationGroup: (id: number) =>
    FEATURES_ENABLED.locationGroups
      ? api.delete(`/api/v1/locations/groups/${id}`)
      : Promise.reject(new Error('Location groups feature is currently disabled')),
}

export const scraperApi = {
  getCategories: (locationId?: number, refresh = false) =>
    api.get('/api/v1/scraper/categories', { params: { location_id: locationId, refresh } }),
  getCategoriesStructured: () =>
    api.get('/api/v1/scraper/categories/structured'),
}

// AI MVP API
export const aiMvpApi = {
  analyzeWebsite: (data: {
    url: string
    lead_value?: number
    lead_id?: number
    fetch_timeout?: number
  }) =>
    api.post('/api/v1/ai-mvp/analyze-website', data),

  generateEmail: (data: {
    prospect_name: string
    company_name: string
    website_analysis: string
    our_service_description: string
    lead_value?: number
    lead_id?: number
  }) =>
    api.post('/api/v1/ai-mvp/generate-email', data),

  sendEmail: (data: {
    to_email: string
    subject: string
    html_body: string
    text_body?: string
    track_opens?: boolean
    track_links?: boolean
    tag?: string
    lead_id?: number
  }) =>
    api.post('/api/v1/ai-mvp/send-email', data),

  getStats: (taskType?: string) =>
    api.get('/api/v1/ai-mvp/stats', { params: { task_type: taskType } }),

  getPerformance: (minSamples?: number) =>
    api.get('/api/v1/ai-mvp/performance', { params: { min_samples: minSamples } }),
}

export default api