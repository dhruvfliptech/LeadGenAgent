import axios from 'axios'
import {
  DemoSite,
  CreateDemoSiteRequest,
  DemoSiteStats,
  ComprehensiveAnalysis,
  ImprovementPlan
} from '@/types/demoSite'

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Demo Sites API
export const demoSitesApi = {
  // Get all demo sites with optional filters
  getDemoSites: (params?: {
    status?: string
    framework?: string
    lead_id?: number
    search?: string
    limit?: number
    offset?: number
  }) =>
    api.get<DemoSite[]>('/api/v1/demo-sites', { params }),

  // Get single demo site
  getDemoSite: (buildId: string) =>
    api.get<DemoSite>(`/api/v1/demo-sites/${buildId}`),

  // Create new demo site
  createDemoSite: (request: CreateDemoSiteRequest) =>
    api.post<DemoSite>('/api/v1/demo-sites', request),

  // Get demo site status (for polling during generation)
  getDemoSiteStatus: (buildId: string) =>
    api.get<{
      build_id: string
      status: string
      progress_percentage: number
      current_step: string
      error_message?: string
    }>(`/api/v1/demo-sites/${buildId}/status`),

  // Deploy demo site
  deployDemoSite: (buildId: string, provider?: 'vercel' | 'netlify' | 'github_pages') =>
    api.post(`/api/v1/demo-sites/${buildId}/deploy`, { provider }),

  // Redeploy existing demo site
  redeployDemoSite: (buildId: string) =>
    api.post(`/api/v1/demo-sites/${buildId}/redeploy`),

  // Download demo site as ZIP
  downloadDemoSite: (buildId: string) =>
    api.get(`/api/v1/demo-sites/${buildId}/download`, { responseType: 'blob' }),

  // Delete demo site
  deleteDemoSite: (buildId: string) =>
    api.delete(`/api/v1/demo-sites/${buildId}`),

  // Get demo site stats
  getStats: () =>
    api.get<DemoSiteStats>('/api/v1/demo-sites/stats'),

  // Track view/click analytics
  trackView: (buildId: string) =>
    api.post(`/api/v1/demo-sites/${buildId}/track/view`),

  trackClick: (buildId: string, elementId?: string) =>
    api.post(`/api/v1/demo-sites/${buildId}/track/click`, { element_id: elementId }),
}

// Website Analysis API (from ai_mvp.py)
export const analysisApi = {
  // Comprehensive website analysis
  analyzeComprehensive: (url: string, includeAiDesign = false) =>
    api.post<ComprehensiveAnalysis>('/api/v1/ai-mvp/analyze-comprehensive', {
      url,
      include_ai_design: includeAiDesign
    }),

  // Generate improvement plan
  generateImprovementPlan: (data: {
    url: string
    analysis_result: any
    industry?: string
    competitor_urls?: string[]
    focus_areas?: string[]
    lead_value?: number
  }) =>
    api.post<ImprovementPlan>('/api/v1/ai-mvp/generate-improvement-plan', data),

  // Quick website analysis (lighter version)
  analyzeWebsite: (url: string, leadValue?: number, leadId?: number) =>
    api.post('/api/v1/ai-mvp/analyze-website', {
      url,
      lead_value: leadValue,
      lead_id: leadId
    }),
}

// Utility functions
export const demoSitesUtils = {
  // Get framework display name
  getFrameworkName: (framework: string): string => {
    const names: Record<string, string> = {
      html: 'HTML/CSS/JS',
      react: 'React + TypeScript',
      nextjs: 'Next.js'
    }
    return names[framework] || framework
  },

  // Get framework icon/emoji
  getFrameworkIcon: (framework: string): string => {
    const icons: Record<string, string> = {
      html: '🌐',
      react: '⚛️',
      nextjs: '▲'
    }
    return icons[framework] || '📄'
  },

  // Get status badge color
  getStatusColor: (status: string): string => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      analyzing: 'bg-blue-100 text-blue-800',
      planning: 'bg-purple-100 text-purple-800',
      generating: 'bg-yellow-100 text-yellow-800',
      deploying: 'bg-indigo-100 text-indigo-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  },

  // Format file size
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
  },

  // Format duration
  formatDuration: (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  },

  // Get priority badge color
  getPriorityColor: (priority: string): string => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-blue-100 text-blue-800 border-blue-300'
    }
    return colors[priority.toLowerCase()] || 'bg-gray-100 text-gray-800 border-gray-300'
  },

  // Get category icon
  getCategoryIcon: (category: string): string => {
    const icons: Record<string, string> = {
      design: '🎨',
      technical: '⚙️',
      content: '📝',
      seo: '🔍',
      performance: '⚡',
      accessibility: '♿',
      conversion: '💰',
      security: '🔒'
    }
    return icons[category.toLowerCase()] || '📋'
  },

  // Calculate overall health score from analysis
  calculateHealthScore: (analysis: ComprehensiveAnalysis): {
    score: number
    grade: string
    color: string
  } => {
    const score = analysis.overall_score
    let grade = 'F'
    let color = 'red'

    if (score >= 90) {
      grade = 'A'
      color = 'green'
    } else if (score >= 80) {
      grade = 'B'
      color = 'blue'
    } else if (score >= 70) {
      grade = 'C'
      color = 'yellow'
    } else if (score >= 60) {
      grade = 'D'
      color = 'orange'
    } else {
      grade = 'F'
      color = 'red'
    }

    return { score, grade, color }
  }
}

export default demoSitesApi
