import axios, { AxiosError } from 'axios'
import toast from 'react-hot-toast'

// Get API base URL from environment or default to localhost
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Track which Phase 3 endpoints are disabled to avoid repeated errors
const disabledEndpoints = new Set<string>()

// Create axios instance
export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError) => {
    const url = error.config?.url || ''

    // Handle common errors
    if (error.response?.status === 401) {
      // Handle unauthorized
      toast.error('Unauthorized. Please log in.')
      // localStorage.removeItem('token')
      // window.location.href = '/login'
    } else if (error.response?.status === 404) {
      // Check if this is a Phase 3 endpoint (templates, rules, notifications, schedules, exports)
      const isPhase3Endpoint = ['/templates', '/rules', '/notifications', '/schedules', '/exports'].some(endpoint => url.includes(endpoint))

      if (isPhase3Endpoint && !disabledEndpoints.has(url)) {
        // Only show warning once per endpoint
        disabledEndpoints.add(url)
        console.warn('Phase 3 feature not yet enabled:', url)
        // Don't show toast for Phase 3 endpoints - they're expected to be disabled
      } else if (!isPhase3Endpoint) {
        console.warn('Resource not found:', url)
        toast.error('Resource not found')
      }
    } else if (error.response?.status === 422) {
      // Validation error
      const detail = (error.response?.data as any)?.detail
      const message = Array.isArray(detail)
        ? detail.map((d: any) => d.msg).join(', ')
        : detail || 'Validation error'
      toast.error(message)
    } else if (error.response?.status && error.response.status >= 500) {
      const message = (error.response?.data as any)?.detail || error.message || 'Server error'
      console.error('Server error:', message)
      toast.error(`Server error: ${message}`)
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.')
    } else if (error.message === 'Network Error') {
      // Don't show toast for background WebSocket errors or non-user-initiated requests
      // WebSocket errors will be handled by the useWebSocket hook
      if (error.config?.url && !error.config.url.includes('/ws')) {
        toast.error('Network error. Please check your connection.')
      }
    }

    return Promise.reject(error)
  }
)

// Google Maps Scraper API
export const googleMapsApi = {
  // Start a Google Maps scraping job
  startScrape: (data: {
    query: string
    location: string
    max_results?: number
    extract_emails?: boolean
    use_places_api?: boolean
    location_id?: number
  }) => api.post('/google-maps/scrape', data),

  // Get job status
  getJobStatus: (jobId: string, includeResults: boolean = false) =>
    api.get(`/google-maps/status/${jobId}`, {
      params: { include_results: includeResults }
    }),

  // List all jobs
  listJobs: (status?: string, limit: number = 50) =>
    api.get('/google-maps/jobs', {
      params: { status, limit }
    }),

  // Delete a job
  deleteJob: (jobId: string) =>
    api.delete(`/google-maps/jobs/${jobId}`),
}

// Workflow Approvals API for n8n integration
export const workflowApprovalsApi = {
  // Get pending approvals
  getPending: (approvalType?: string, approverEmail?: string, limit: number = 50) =>
    api.get('/workflow-approvals/pending', {
      params: { approval_type: approvalType, approver_email: approverEmail, limit }
    }),

  // Get approval details
  getDetails: (approvalId: number) =>
    api.get(`/workflow-approvals/${approvalId}`),

  // Submit approval decision
  approve: (approvalId: number, reviewerEmail: string, comments?: string, modifiedData?: any) =>
    api.post(`/workflow-approvals/${approvalId}/decide`, {
      approved: true,
      reviewer_email: reviewerEmail,
      comments,
      modified_data: modifiedData
    }),

  // Reject approval
  reject: (approvalId: number, reviewerEmail: string, comments: string) =>
    api.post(`/workflow-approvals/${approvalId}/decide`, {
      approved: false,
      reviewer_email: reviewerEmail,
      comments
    }),

  // Escalate approval
  escalate: (approvalId: number, escalationLevel: number = 1, escalatedTo?: string, reason?: string) =>
    api.post(`/workflow-approvals/${approvalId}/escalate`, {
      escalation_level: escalationLevel,
      escalated_to: escalatedTo,
      reason
    }),

  // Bulk approve
  bulkApprove: (approvalIds: number[], reviewerEmail: string, comments?: string) =>
    api.post('/workflow-approvals/bulk-approve', {
      approval_ids: approvalIds,
      reviewer_email: reviewerEmail,
      comments
    }),

  // Get statistics
  getStats: () =>
    api.get('/workflow-approvals/stats'),

  // Auto-approval rules
  getRules: (activeOnly: boolean = true) =>
    api.get('/workflow-approvals/auto-approval/rules', {
      params: { active_only: activeOnly }
    }),

  // Create auto-approval rule
  createRule: (ruleData: any) =>
    api.post('/workflow-approvals/auto-approval/rules', ruleData),

  // Get rule performance
  getRulePerformance: (ruleId: number) =>
    api.get(`/workflow-approvals/auto-approval/rules/${ruleId}/performance`),

  // Optimize rule threshold
  optimizeRule: (ruleId: number, targetApprovalRate: number = 0.8) =>
    api.post(`/workflow-approvals/auto-approval/rules/${ruleId}/optimize`, null, {
      params: { target_approval_rate: targetApprovalRate }
    }),

  // Get rule templates
  getRuleTemplates: () =>
    api.get('/workflow-approvals/auto-approval/templates'),

  // Apply rule template
  applyRuleTemplate: (templateIndex: number) =>
    api.post(`/workflow-approvals/auto-approval/templates/${templateIndex}/apply`)
}

// API helper functions for multi-source operations
export const sourceApi = {
  // Get leads by source
  getLeadsBySource: (source: string) =>
    api.get(`/leads?source=${source}`),

  // Get source statistics
  getSourceStats: () =>
    api.get('/leads/stats/by-source'),

  // Get best performing source
  getBestPerformingSource: () =>
    api.get('/leads/stats/best-source'),

  // Create scraping job with source
  createScrapeJob: (data: {
    source: string
    location_ids: number[]
    categories?: string[]
    keywords?: string[]
    max_pages: number
    priority: string
    enable_email_extraction: boolean
    captcha_api_key?: string
    business_category?: string
    radius?: number
    company_size?: string
    salary_range?: string
  }) => api.post('/scraper/jobs', data),

  // Get enabled sources from config
  getEnabledSources: () =>
    api.get('/config/enabled-sources'),
}

// Lead operations
export const getLeadById = async (id: number) => {
  const response = await api.get(`/leads/${id}`)
  return response.data
}

export default api