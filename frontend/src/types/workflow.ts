// Workflow types for n8n integration and monitoring

export type WorkflowStatus = 'running' | 'success' | 'error' | 'waiting' | 'canceled'
export type ExecutionMode = 'manual' | 'trigger' | 'webhook' | 'retry' | 'cli'

export interface WorkflowNode {
  id: string
  name: string
  type: string
  typeVersion: number
  position: [number, number]
  parameters: Record<string, any>
  credentials?: Record<string, any>
}

export interface Workflow {
  id: string
  name: string
  active: boolean
  createdAt: string
  updatedAt: string
  nodes: WorkflowNode[]
  connections: Record<string, any>
  staticData: Record<string, any>
  settings?: {
    saveDataErrorExecution?: string
    saveDataSuccessExecution?: string
    saveManualExecutions?: boolean
    executionTimeout?: number
    timezone?: string
  }
  versionId?: string
  tags?: string[]
}

export interface ExecutionNodeData {
  startTime: number
  executionTime: number
  source?: string[]
  executionStatus?: 'success' | 'error' | 'running'
  data?: {
    main?: any[][]
    [key: string]: any
  }
  error?: {
    message: string
    description?: string
    stack?: string
  }
}

export interface ExecutionError {
  message: string
  node: string
  timestamp: string
  stack?: string
  description?: string
  context?: Record<string, any>
}

export interface WorkflowExecution {
  id: string
  workflowId: string
  workflowName: string
  status: WorkflowStatus
  mode: ExecutionMode
  startedAt: string
  stoppedAt?: string
  finishedAt?: string
  duration?: number
  retryOf?: string
  retrySuccessId?: string
  data?: {
    resultData: {
      runData: Record<string, ExecutionNodeData[]>
      lastNodeExecuted?: string
    }
    executionData?: {
      contextData: Record<string, any>
      nodeExecutionStack: any[]
      waitingExecution: Record<string, any>
    }
  }
  waitTill?: string
  error?: ExecutionError
  metadata?: Record<string, any>
}

export interface WorkflowStats {
  total_executions: number
  successful_executions: number
  failed_executions: number
  running_executions: number
  waiting_executions: number
  avg_duration_seconds: number
  success_rate: number
  executions_by_day: Array<{
    date: string
    total: number
    success: number
    failed: number
  }>
  executions_by_hour: Array<{
    hour: number
    count: number
  }>
  slowest_nodes: Array<{
    node_name: string
    avg_duration_ms: number
    execution_count: number
  }>
  error_distribution: Array<{
    error_type: string
    count: number
    percentage: number
  }>
}

export interface WorkflowMetrics {
  workflow_id: string
  workflow_name: string
  total_executions: number
  success_count: number
  failure_count: number
  avg_duration_seconds: number
  last_execution_at?: string
  last_success_at?: string
  last_failure_at?: string
  success_rate: number
}

export interface ApprovalRequest {
  id: number
  approval_type: 'demo_site' | 'demo_video' | 'email_send' | 'resource_create'
  resource_id: number
  resource_type: string
  resource_data: Record<string, any>
  status: 'pending' | 'approved' | 'rejected' | 'timeout'
  created_at: string
  timeout_at: string
  decided_at?: string
  reviewer_email?: string
  comments?: string
  timeout_action?: 'approve' | 'reject'
  metadata?: {
    lead_id?: number
    business_name?: string
    category?: string
    quality_score?: number
    preview_url?: string
    video_url?: string
    email_subject?: string
  }
}

export interface NodeExecutionDetail {
  node_name: string
  node_type: string
  status: 'success' | 'error' | 'running' | 'waiting'
  start_time: string
  end_time?: string
  duration_ms?: number
  input_data?: any
  output_data?: any
  error?: {
    message: string
    stack?: string
  }
  retry_count?: number
}

export interface ExecutionTimeline {
  execution_id: string
  workflow_name: string
  status: WorkflowStatus
  total_duration_ms: number
  nodes: NodeExecutionDetail[]
  approval_gates?: Array<{
    node_name: string
    status: 'pending' | 'approved' | 'rejected' | 'timeout'
    waiting_since: string
    timeout_at: string
  }>
}

export interface LiveExecutionUpdate {
  execution_id: string
  workflow_id: string
  workflow_name: string
  status: WorkflowStatus
  current_node?: string
  progress_percentage?: number
  eta_seconds?: number
  message?: string
  timestamp: string
}

export interface WorkflowFilters {
  active?: boolean
  status?: WorkflowStatus
  workflow_id?: string
  search?: string
  limit?: number
  offset?: number
}

export interface ExecutionFilters {
  workflow_id?: string
  status?: WorkflowStatus
  mode?: ExecutionMode
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}

export interface PaginatedExecutions {
  executions: WorkflowExecution[]
  total: number
  offset: number
  limit: number
}

export interface WorkflowHealthStatus {
  workflow_id: string
  workflow_name: string
  is_healthy: boolean
  health_score: number
  issues: Array<{
    severity: 'critical' | 'warning' | 'info'
    message: string
    recommendation?: string
  }>
  recent_failure_rate: number
  avg_duration_trend: 'increasing' | 'stable' | 'decreasing'
  last_check: string
}
