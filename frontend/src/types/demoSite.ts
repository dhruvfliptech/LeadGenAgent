export type Framework = 'html' | 'react' | 'nextjs'
export type BuildStatus = 'pending' | 'analyzing' | 'planning' | 'generating' | 'deploying' | 'completed' | 'failed'
export type DeploymentProvider = 'vercel' | 'netlify' | 'github_pages'

export interface DemoSiteFile {
  path: string
  content: string
  language?: string
  size?: number
}

export interface DeploymentConfig {
  framework: Framework
  build_command: string
  install_command: string
  output_directory: string
  dev_command: string
  port: number
  environment_variables?: Record<string, string>
}

export interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  file_count: number
  total_size_bytes: number
  has_required_files: boolean
  placeholders_found: string[]
}

export interface ImprovementSummary {
  id: string
  title: string
  category: string
  priority: string
  impact: string
}

export interface AnalysisMetrics {
  overall_score: number
  design_score: number
  seo_score: number
  performance_score: number
  accessibility_score: number
}

export interface DemoSite {
  id: number
  build_id: string
  lead_id: number
  lead_title?: string
  lead_url?: string

  // Build details
  framework: Framework
  status: BuildStatus
  files: Record<string, string>
  deployment_config: DeploymentConfig

  // Improvements
  improvements_applied: ImprovementSummary[]
  original_url: string

  // Metrics
  generation_time_seconds: number
  total_lines_of_code: number
  ai_model_used: string
  ai_cost: number
  validation_results: ValidationResult
  analysis_metrics?: AnalysisMetrics

  // Deployment
  preview_url?: string
  deployment_provider?: DeploymentProvider
  deployed_at?: string
  deployment_status?: 'deploying' | 'deployed' | 'failed'
  deployment_error?: string

  // Analytics
  view_count?: number
  click_count?: number
  last_viewed_at?: string

  // Timestamps
  created_at: string
  updated_at: string
}

export interface CreateDemoSiteRequest {
  lead_id: number
  original_url: string
  original_html: string
  improvement_plan: Record<string, any>
  framework: Framework
  include_comments?: boolean
  auto_deploy?: boolean
  deployment_provider?: DeploymentProvider
}

export interface DemoSiteStats {
  total_demos: number
  completed_demos: number
  failed_demos: number
  total_cost: number
  avg_generation_time: number
  by_framework: Record<Framework, number>
  by_status: Record<BuildStatus, number>
  recent_demos: DemoSite[]
}

export interface ComprehensiveAnalysis {
  url: string
  overall_score: number
  design: {
    score: number
    issues: string[]
    strengths: string[]
    metrics: Record<string, any>
  }
  seo: {
    score: number
    issues: string[]
    strengths: string[]
    details: Record<string, any>
  }
  performance: {
    score: number
    issues: string[]
    strengths: string[]
    metrics: Record<string, any>
  }
  accessibility: {
    score: number
    issues: string[]
    strengths: string[]
    details: Record<string, any>
  }
  title: string
  meta_description: string
}

export interface ImprovementPlan {
  url: string
  analyzed_at: string
  improvements: {
    id: string
    category: string
    priority: string
    title: string
    description: string
    current_state: string
    proposed_change: string
    impact: string
    difficulty: string
    time_estimate: string
    code_example?: string
    resources: string[]
    dependencies: string[]
  }[]
  summary: {
    total_improvements: number
    critical_priority: number
    high_priority: number
    medium_priority: number
    low_priority: number
    estimated_total_impact: string
    estimated_total_time: string
    quick_wins: number
    categories: Record<string, number>
  }
  analysis_metadata: Record<string, any>
}
