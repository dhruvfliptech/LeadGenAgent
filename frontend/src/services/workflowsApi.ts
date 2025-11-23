// API service for n8n workflow operations and monitoring

import { api } from './api'
import {
  Workflow,
  WorkflowExecution,
  WorkflowStats,
  WorkflowMetrics,
  ApprovalRequest,
  ExecutionFilters,
  WorkflowFilters,
  PaginatedExecutions,
  WorkflowHealthStatus,
  ExecutionTimeline
} from '@/types/workflow'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export const workflowsApi = {
  // ==================== Workflows ====================

  /**
   * Get all workflows with optional filters
   */
  getWorkflows: (filters?: WorkflowFilters) =>
    api.get<Workflow[]>('/n8n-webhooks/workflows', { params: filters }),

  /**
   * Get a specific workflow by ID
   */
  getWorkflow: (id: string) =>
    api.get<Workflow>(`/n8n-webhooks/workflows/${id}`),

  /**
   * Activate a workflow
   */
  activateWorkflow: (id: string) =>
    api.post(`/n8n-webhooks/workflows/${id}/activate`),

  /**
   * Deactivate a workflow
   */
  deactivateWorkflow: (id: string) =>
    api.post(`/n8n-webhooks/workflows/${id}/deactivate`),

  /**
   * Get workflow metrics (executions, success rate, etc.)
   */
  getWorkflowMetrics: (workflowId: string) =>
    api.get<WorkflowMetrics>(`/n8n-webhooks/workflows/${workflowId}/metrics`),

  /**
   * Get workflow health status
   */
  getWorkflowHealth: (workflowId: string) =>
    api.get<WorkflowHealthStatus>(`/n8n-webhooks/workflows/${workflowId}/health`),

  // ==================== Executions ====================

  /**
   * Get executions with pagination and filters
   */
  getExecutions: (filters?: ExecutionFilters) =>
    api.get<PaginatedExecutions>('/n8n-webhooks/executions', { params: filters }),

  /**
   * Get a specific execution by ID
   */
  getExecution: (id: string) =>
    api.get<WorkflowExecution>(`/n8n-webhooks/executions/${id}`),

  /**
   * Get detailed execution timeline with node-by-node breakdown
   */
  getExecutionTimeline: (id: string) =>
    api.get<ExecutionTimeline>(`/n8n-webhooks/executions/${id}/timeline`),

  /**
   * Retry a failed execution
   */
  retryExecution: (id: string) =>
    api.post<WorkflowExecution>(`/n8n-webhooks/executions/${id}/retry`),

  /**
   * Cancel a running execution
   */
  cancelExecution: (id: string) =>
    api.post(`/n8n-webhooks/executions/${id}/cancel`),

  /**
   * Delete an execution
   */
  deleteExecution: (id: string) =>
    api.delete(`/n8n-webhooks/executions/${id}`),

  /**
   * Get recent executions (last 50)
   */
  getRecentExecutions: (limit: number = 50) =>
    api.get<WorkflowExecution[]>('/n8n-webhooks/executions/recent', {
      params: { limit }
    }),

  // ==================== Statistics ====================

  /**
   * Get overall workflow statistics
   */
  getStats: () =>
    api.get<WorkflowStats>('/n8n-webhooks/stats'),

  /**
   * Get workflow-specific statistics
   */
  getWorkflowStats: (workflowId: string) =>
    api.get<WorkflowStats>(`/n8n-webhooks/workflows/${workflowId}/stats`),

  /**
   * Get execution statistics for a date range
   */
  getExecutionStats: (startDate: string, endDate: string) =>
    api.get<WorkflowStats>('/n8n-webhooks/stats/executions', {
      params: { start_date: startDate, end_date: endDate }
    }),

  // ==================== Approvals ====================

  /**
   * Get all pending approvals
   */
  getPendingApprovals: () =>
    api.get<ApprovalRequest[]>('/approvals/pending'),

  /**
   * Get approvals by type
   */
  getApprovalsByType: (type: string) =>
    api.get<ApprovalRequest[]>('/approvals/by-type', { params: { type } }),

  /**
   * Get a specific approval request
   */
  getApproval: (id: number) =>
    api.get<ApprovalRequest>(`/approvals/${id}`),

  /**
   * Approve a request
   */
  approveRequest: (id: number, comments?: string) =>
    api.post<ApprovalRequest>(`/approvals/${id}/decide`, {
      approved: true,
      comments
    }),

  /**
   * Reject a request
   */
  rejectRequest: (id: number, reason: string) =>
    api.post<ApprovalRequest>(`/approvals/${id}/decide`, {
      approved: false,
      comments: reason
    }),

  /**
   * Get approval statistics
   */
  getApprovalStats: () =>
    api.get('/approvals/stats'),

  // ==================== Error Logs ====================

  /**
   * Get failed executions with error details
   */
  getFailedExecutions: (filters?: ExecutionFilters) =>
    api.get<WorkflowExecution[]>('/n8n-webhooks/executions/failed', {
      params: filters
    }),

  /**
   * Mark an execution error as resolved
   */
  markErrorResolved: (executionId: string, notes?: string) =>
    api.post(`/n8n-webhooks/executions/${executionId}/resolve`, { notes }),

  /**
   * Get error summary grouped by error type
   */
  getErrorSummary: () =>
    api.get('/n8n-webhooks/errors/summary'),

  // ==================== Performance ====================

  /**
   * Get slowest workflow nodes
   */
  getSlowestNodes: (workflowId?: string, limit: number = 10) =>
    api.get('/n8n-webhooks/performance/slowest-nodes', {
      params: { workflow_id: workflowId, limit }
    }),

  /**
   * Get bottleneck analysis
   */
  getBottleneckAnalysis: (workflowId: string) =>
    api.get(`/n8n-webhooks/workflows/${workflowId}/bottlenecks`),

  /**
   * Get execution duration trends
   */
  getDurationTrends: (workflowId: string, days: number = 30) =>
    api.get(`/n8n-webhooks/workflows/${workflowId}/duration-trends`, {
      params: { days }
    }),

  // ==================== WebSocket ====================

  /**
   * Connect to live workflow updates via WebSocket
   * Returns a WebSocket connection for real-time execution monitoring
   */
  connectLiveUpdates: (): WebSocket => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/workflows`)

    ws.onopen = () => {
      console.log('[WorkflowsAPI] WebSocket connected')
    }

    ws.onerror = (error) => {
      console.error('[WorkflowsAPI] WebSocket error:', error)
    }

    ws.onclose = (event) => {
      console.log('[WorkflowsAPI] WebSocket closed:', event.code, event.reason)
    }

    return ws
  },

  /**
   * Subscribe to specific workflow execution updates
   */
  subscribeToExecution: (ws: WebSocket, executionId: string) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        execution_id: executionId
      }))
    }
  },

  /**
   * Unsubscribe from execution updates
   */
  unsubscribeFromExecution: (ws: WebSocket, executionId: string) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'unsubscribe',
        execution_id: executionId
      }))
    }
  },

  // ==================== Manual Triggers ====================

  /**
   * Manually trigger a workflow execution
   */
  triggerWorkflow: (workflowId: string, data?: Record<string, any>) =>
    api.post(`/n8n-webhooks/workflows/${workflowId}/trigger`, data),

  /**
   * Test a workflow with sample data
   */
  testWorkflow: (workflowId: string, data?: Record<string, any>) =>
    api.post(`/n8n-webhooks/workflows/${workflowId}/test`, data),
}

export default workflowsApi
