// Component to display and manage failed executions

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ExclamationCircleIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'
import { WorkflowExecution } from '@/types/workflow'
import { workflowsApi } from '@/services/workflowsApi'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

interface ErrorLogViewerProps {
  executions: WorkflowExecution[]
}

export default function ErrorLogViewer({ executions }: ErrorLogViewerProps) {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [expandedError, setExpandedError] = useState<string | null>(null)

  const retryMutation = useMutation({
    mutationFn: (executionId: string) => workflowsApi.retryExecution(executionId),
    onSuccess: () => {
      toast.success('Retry initiated')
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to retry')
    }
  })

  const markResolvedMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      workflowsApi.markErrorResolved(id, notes),
    onSuccess: () => {
      toast.success('Marked as resolved')
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to mark as resolved')
    }
  })

  const filteredExecutions = searchTerm
    ? executions.filter(
        e =>
          e.workflowName.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.error?.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
          e.error?.node.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : executions

  if (filteredExecutions.length === 0) {
    return (
      <div className="card p-6 text-center">
        <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-3" />
        <p className="text-dark-text-secondary">
          {searchTerm ? 'No errors match your search' : 'No failed executions'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
        <input
          type="text"
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search errors..."
          className="form-input pl-10 w-full"
        />
      </div>

      {/* Error List */}
      {filteredExecutions.map(execution => {
        const isExpanded = expandedError === execution.id

        return (
          <div key={execution.id} className="card p-4 border-l-4 border-red-500">
            <div className="flex items-start gap-4">
              <ExclamationCircleIcon className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-semibold text-dark-text-primary">
                      {execution.workflowName}
                    </h4>
                    <div className="text-sm text-dark-text-secondary mt-1">
                      {execution.error?.message}
                    </div>
                    {execution.error?.node && (
                      <div className="text-xs text-dark-text-muted mt-1">
                        Failed at: <span className="font-mono text-red-400">{execution.error.node}</span>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-dark-text-muted whitespace-nowrap ml-4">
                    {formatRelativeTime(execution.stoppedAt || execution.startedAt)}
                  </span>
                </div>

                {/* Stack Trace Toggle */}
                {execution.error?.stack && (
                  <button
                    onClick={() => setExpandedError(isExpanded ? null : execution.id)}
                    className="flex items-center gap-1 text-sm text-dark-text-secondary hover:text-dark-text-primary mb-3"
                  >
                    {isExpanded ? (
                      <ChevronDownIcon className="w-4 h-4" />
                    ) : (
                      <ChevronRightIcon className="w-4 h-4" />
                    )}
                    {isExpanded ? 'Hide' : 'Show'} Stack Trace
                  </button>
                )}

                {isExpanded && execution.error?.stack && (
                  <pre className="text-xs text-red-300 bg-black/30 p-3 rounded border border-red-500/30 overflow-x-auto mb-3">
                    {execution.error.stack}
                  </pre>
                )}

                {/* Actions */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => retryMutation.mutate(execution.id)}
                    disabled={retryMutation.isPending}
                    className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <ArrowPathIcon className="w-4 h-4" />
                    Retry
                  </button>
                  <button
                    onClick={() => markResolvedMutation.mutate({ id: execution.id })}
                    disabled={markResolvedMutation.isPending}
                    className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-1.5 text-green-500 hover:text-green-400 disabled:opacity-50"
                  >
                    <CheckCircleIcon className="w-4 h-4" />
                    Mark Resolved
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
