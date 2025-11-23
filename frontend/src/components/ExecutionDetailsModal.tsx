// Modal to display detailed execution information with node-by-node breakdown

import { Dialog } from '@headlessui/react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  StopCircleIcon,

  ChevronRightIcon,
  ChevronDownIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { WorkflowExecution, ExecutionTimeline, NodeExecutionDetail } from '@/types/workflow'
import { workflowsApi } from '@/services/workflowsApi'
import { formatDateTime, formatRelativeTime } from '@/utils/dateFormat'
import { useExecutionMonitor } from '@/hooks/useWorkflowUpdates'
import toast from 'react-hot-toast'
import { useState } from 'react'

interface ExecutionDetailsModalProps {
  execution: WorkflowExecution | null
  isOpen: boolean
  onClose: () => void
}

export default function ExecutionDetailsModal({
  execution,
  isOpen,
  onClose
}: ExecutionDetailsModalProps) {
  const queryClient = useQueryClient()
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  // Fetch detailed timeline for execution
  const { data: timeline } = useQuery<ExecutionTimeline>({
    queryKey: ['execution-timeline', execution?.id],
    queryFn: () => workflowsApi.getExecutionTimeline(execution!.id).then(res => res.data),
    enabled: !!execution?.id && isOpen
  })

  // Monitor live updates for running executions
  const { executionUpdate, isComplete: _isComplete } = useExecutionMonitor(
    execution?.status === 'running' ? execution.id : null
  )

  const retryMutation = useMutation({
    mutationFn: () => workflowsApi.retryExecution(execution!.id),
    onSuccess: () => {
      toast.success('Execution retry initiated')
      queryClient.invalidateQueries({ queryKey: ['executions'] })
      onClose()
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to retry execution')
    }
  })

  const cancelMutation = useMutation({
    mutationFn: () => workflowsApi.cancelExecution(execution!.id),
    onSuccess: () => {
      toast.success('Execution canceled')
      queryClient.invalidateQueries({ queryKey: ['executions'] })
      onClose()
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to cancel execution')
    }
  })

  if (!execution) return null

  const toggleNodeExpanded = (nodeName: string) => {
    setExpandedNodes(prev => {
      const next = new Set(prev)
      if (next.has(nodeName)) {
        next.delete(nodeName)
      } else {
        next.add(nodeName)
      }
      return next
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'error':
        return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
      case 'running':
        return <ClockIcon className="w-5 h-5 text-blue-500 animate-spin" />
      case 'waiting':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      success: 'bg-green-500/20 text-green-400 border-green-500/30',
      error: 'bg-red-500/20 text-red-400 border-red-500/30',
      running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      waiting: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      canceled: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles] || styles.canceled}`}>
        {status}
      </span>
    )
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return '—'
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}m`
  }

  const renderNodeDetails = (node: NodeExecutionDetail) => {
    const isExpanded = expandedNodes.has(node.node_name)

    return (
      <div key={node.node_name} className="border border-dark-border rounded-lg overflow-hidden">
        <button
          onClick={() => toggleNodeExpanded(node.node_name)}
          className="w-full p-4 flex items-center justify-between hover:bg-dark-border/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            {getStatusIcon(node.status)}
            <div className="text-left">
              <div className="font-medium text-dark-text-primary">{node.node_name}</div>
              <div className="text-xs text-dark-text-muted">{node.node_type}</div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {node.duration_ms && (
              <div className="text-sm text-dark-text-secondary">
                {formatDuration(node.duration_ms)}
              </div>
            )}
            {node.retry_count && node.retry_count > 0 && (
              <div className="text-xs text-yellow-500">
                {node.retry_count} retries
              </div>
            )}
            {isExpanded ? (
              <ChevronDownIcon className="w-5 h-5 text-dark-text-muted" />
            ) : (
              <ChevronRightIcon className="w-5 h-5 text-dark-text-muted" />
            )}
          </div>
        </button>

        {isExpanded && (
          <div className="p-4 bg-dark-bg border-t border-dark-border space-y-3">
            {/* Timestamps */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-dark-text-muted">Started</div>
                <div className="text-dark-text-primary">{formatDateTime(node.start_time)}</div>
              </div>
              {node.end_time && (
                <div>
                  <div className="text-dark-text-muted">Completed</div>
                  <div className="text-dark-text-primary">{formatDateTime(node.end_time)}</div>
                </div>
              )}
            </div>

            {/* Error Details */}
            {node.error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <ExclamationCircleIcon className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-red-400 mb-1">Error</div>
                    <div className="text-sm text-red-300">{node.error.message}</div>
                    {node.error.stack && (
                      <details className="mt-2">
                        <summary className="text-xs text-red-400 cursor-pointer">Stack Trace</summary>
                        <pre className="mt-2 text-xs text-red-300 overflow-x-auto p-2 bg-black/30 rounded">
                          {node.error.stack}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Input/Output Data */}
            {(node.input_data || node.output_data) && (
              <div className="space-y-2">
                {node.input_data && (
                  <details className="group">
                    <summary className="text-sm font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary">
                      Input Data
                    </summary>
                    <pre className="mt-2 text-xs text-dark-text-muted overflow-x-auto p-3 bg-black/30 rounded border border-dark-border">
                      {JSON.stringify(node.input_data, null, 2)}
                    </pre>
                  </details>
                )}

                {node.output_data && (
                  <details className="group">
                    <summary className="text-sm font-medium text-dark-text-secondary cursor-pointer hover:text-dark-text-primary">
                      Output Data
                    </summary>
                    <pre className="mt-2 text-xs text-dark-text-muted overflow-x-auto p-3 bg-black/30 rounded border border-dark-border">
                      {JSON.stringify(node.output_data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/70" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4 overflow-y-auto">
        <Dialog.Panel className="mx-auto max-w-4xl w-full bg-dark-surface rounded-xl shadow-xl my-8">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dark-border sticky top-0 bg-dark-surface z-10">
            <div className="flex-1 min-w-0">
              <Dialog.Title className="text-xl font-bold text-dark-text-primary truncate">
                Execution #{execution.id.slice(0, 8)}
              </Dialog.Title>
              <div className="mt-1 flex items-center gap-3 text-sm text-dark-text-secondary">
                <span className="font-mono">{execution.workflowName}</span>
                <span className="text-dark-text-muted">•</span>
                {getStatusBadge(execution.status)}
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-dark-text-secondary hover:text-dark-text-primary"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card p-4">
                <div className="text-xs text-dark-text-muted">Started</div>
                <div className="text-sm text-dark-text-primary font-medium mt-1">
                  {formatRelativeTime(execution.startedAt)}
                </div>
              </div>

              {execution.finishedAt && (
                <div className="card p-4">
                  <div className="text-xs text-dark-text-muted">Finished</div>
                  <div className="text-sm text-dark-text-primary font-medium mt-1">
                    {formatRelativeTime(execution.finishedAt)}
                  </div>
                </div>
              )}

              <div className="card p-4">
                <div className="text-xs text-dark-text-muted">Duration</div>
                <div className="text-sm text-dark-text-primary font-medium mt-1">
                  {execution.duration ? formatDuration(execution.duration * 1000) : '—'}
                </div>
              </div>

              <div className="card p-4">
                <div className="text-xs text-dark-text-muted">Mode</div>
                <div className="text-sm text-dark-text-primary font-medium mt-1 capitalize">
                  {execution.mode}
                </div>
              </div>
            </div>

            {/* Live Progress */}
            {execution.status === 'running' && executionUpdate && (
              <div className="card p-4 bg-blue-500/10 border border-blue-500/30">
                <div className="flex items-center gap-3">
                  <ClockIcon className="w-5 h-5 text-blue-500 animate-spin" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-blue-400">
                      {executionUpdate.current_node || 'Processing...'}
                    </div>
                    {executionUpdate.progress_percentage !== undefined && (
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-blue-300 mb-1">
                          <span>{executionUpdate.progress_percentage}% complete</span>
                          {executionUpdate.eta_seconds && (
                            <span>ETA: {formatDuration(executionUpdate.eta_seconds * 1000)}</span>
                          )}
                        </div>
                        <div className="w-full bg-dark-border rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${executionUpdate.progress_percentage}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Execution Error */}
            {execution.error && (
              <div className="card p-4 bg-red-500/10 border border-red-500/30">
                <div className="flex items-start gap-3">
                  <ExclamationCircleIcon className="w-6 h-6 text-red-500 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="font-medium text-red-400">Execution Failed</div>
                    <div className="text-sm text-red-300 mt-1">{execution.error.message}</div>
                    {execution.error.description && (
                      <div className="text-sm text-red-300/80 mt-1">{execution.error.description}</div>
                    )}
                    {execution.error.node && (
                      <div className="text-xs text-red-400 mt-2">
                        Failed at node: <span className="font-mono">{execution.error.node}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Node Execution Timeline */}
            {timeline && timeline.nodes && timeline.nodes.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-dark-text-primary mb-3 flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5" />
                  Execution Timeline
                </h3>
                <div className="space-y-2">
                  {timeline.nodes.map(node => renderNodeDetails(node))}
                </div>
              </div>
            )}

            {/* Approval Gates */}
            {timeline?.approval_gates && timeline.approval_gates.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-dark-text-primary mb-3">
                  Approval Gates
                </h3>
                <div className="space-y-2">
                  {timeline.approval_gates.map((gate, idx) => (
                    <div key={idx} className="card p-4 bg-yellow-500/10 border border-yellow-500/30">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-yellow-400">{gate.node_name}</div>
                          <div className="text-sm text-yellow-300/80 mt-1">
                            Waiting since {formatRelativeTime(gate.waiting_since)}
                          </div>
                        </div>
                        {getStatusBadge(gate.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 p-6 border-t border-dark-border bg-dark-bg">
            {execution.status === 'running' && (
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="btn-secondary flex items-center gap-2 text-red-500 hover:text-red-400 disabled:opacity-50"
              >
                <StopCircleIcon className="w-5 h-5" />
                Cancel Execution
              </button>
            )}

            {execution.status === 'error' && (
              <button
                onClick={() => retryMutation.mutate()}
                disabled={retryMutation.isPending}
                className="btn-primary flex items-center gap-2 disabled:opacity-50"
              >
                <ArrowPathIcon className="w-5 h-5" />
                Retry Execution
              </button>
            )}

            <button onClick={onClose} className="btn-secondary">
              Close
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
