// Component to display and manage n8n workflows

import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  PlayIcon,
  PauseIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,

  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { Workflow, WorkflowMetrics } from '@/types/workflow'
import { workflowsApi } from '@/services/workflowsApi'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

interface WorkflowListProps {
  workflows: Workflow[]
  metrics?: Map<string, WorkflowMetrics>
  onViewDetails?: (workflow: Workflow) => void
  onViewStats?: (workflow: Workflow) => void
}

export default function WorkflowList({
  workflows,
  metrics,
  // @ts-ignore - onViewDetails from props
  onViewDetails,
  onViewStats
}: WorkflowListProps) {
  const queryClient = useQueryClient()

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? workflowsApi.deactivateWorkflow(id) : workflowsApi.activateWorkflow(id),
    onSuccess: (_, variables) => {
      const action = variables.active ? 'deactivated' : 'activated'
      toast.success(`Workflow ${action}`)
      queryClient.invalidateQueries({ queryKey: ['workflows'] })
      queryClient.invalidateQueries({ queryKey: ['workflow-metrics'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to toggle workflow')
    }
  })

  const triggerWorkflowMutation = useMutation({
    mutationFn: (workflowId: string) => workflowsApi.triggerWorkflow(workflowId),
    onSuccess: () => {
      toast.success('Workflow triggered successfully')
      queryClient.invalidateQueries({ queryKey: ['executions'] })
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to trigger workflow')
    }
  })

  const handleToggleActive = (workflow: Workflow) => {
    toggleActiveMutation.mutate({
      id: workflow.id,
      active: workflow.active
    })
  }

  const handleTrigger = (workflow: Workflow) => {
    if (!workflow.active) {
      toast.error('Workflow must be active to trigger manually')
      return
    }
    triggerWorkflowMutation.mutate(workflow.id)
  }

  if (workflows.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <Cog6ToothIcon className="mx-auto h-12 w-12 text-dark-text-muted" />
          <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No workflows found</h3>
          <p className="mt-1 text-sm text-dark-text-secondary">
            No n8n workflows are available at this time.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {workflows.map((workflow) => {
        const metric = metrics?.get(workflow.id)
        const successRate = metric?.success_rate ?? 0
        const successRateColor = successRate >= 90 ? 'text-green-500' : successRate >= 70 ? 'text-yellow-500' : 'text-red-500'

        return (
          <div
            key={workflow.id}
            className="card p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between">
              {/* Workflow Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-dark-text-primary truncate">
                    {workflow.name}
                  </h3>
                  {workflow.active ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5 animate-pulse"></span>
                      Active
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30">
                      Inactive
                    </span>
                  )}
                </div>

                {/* Metrics Row */}
                <div className="flex items-center gap-6 text-sm text-dark-text-secondary">
                  <div className="flex items-center gap-1.5">
                    <ChartBarIcon className="w-4 h-4" />
                    <span>{metric?.total_executions ?? 0} executions</span>
                  </div>

                  {metric && (
                    <>
                      <div className="flex items-center gap-1.5">
                        <CheckCircleIcon className={`w-4 h-4 ${successRateColor}`} />
                        <span className={successRateColor}>
                          {successRate.toFixed(1)}% success
                        </span>
                      </div>

                      {metric.avg_duration_seconds > 0 && (
                        <div className="flex items-center gap-1.5">
                          <ClockIcon className="w-4 h-4" />
                          <span>
                            {metric.avg_duration_seconds < 60
                              ? `${metric.avg_duration_seconds.toFixed(1)}s avg`
                              : `${(metric.avg_duration_seconds / 60).toFixed(1)}m avg`}
                          </span>
                        </div>
                      )}

                      {metric.last_execution_at && (
                        <div className="flex items-center gap-1.5 text-dark-text-muted">
                          <span>Last run: {formatRelativeTime(metric.last_execution_at)}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Execution Stats */}
                {metric && metric.total_executions > 0 && (
                  <div className="mt-3 flex items-center gap-4">
                    <div className="flex-1 max-w-md">
                      <div className="flex items-center justify-between text-xs text-dark-text-muted mb-1">
                        <span>Success / Failures</span>
                        <span>
                          {metric.success_count} / {metric.failure_count}
                        </span>
                      </div>
                      <div className="w-full bg-dark-border rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full bg-green-500 transition-all duration-300"
                          style={{ width: `${successRate}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 ml-4">
                {workflow.active && (
                  <button
                    onClick={() => handleTrigger(workflow)}
                    disabled={triggerWorkflowMutation.isPending}
                    className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-1.5 disabled:opacity-50"
                    title="Trigger manually"
                  >
                    <PlayIcon className="w-4 h-4" />
                    Trigger
                  </button>
                )}

                <button
                  onClick={() => onViewStats?.(workflow)}
                  className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-1.5"
                  title="View statistics"
                >
                  <ChartBarIcon className="w-4 h-4" />
                  Stats
                </button>

                <button
                  onClick={() => handleToggleActive(workflow)}
                  disabled={toggleActiveMutation.isPending}
                  className={`btn-secondary text-sm py-1.5 px-3 flex items-center gap-1.5 disabled:opacity-50 ${
                    workflow.active ? 'text-yellow-500 hover:text-yellow-400' : 'text-green-500 hover:text-green-400'
                  }`}
                  title={workflow.active ? 'Pause workflow' : 'Activate workflow'}
                >
                  {workflow.active ? (
                    <>
                      <PauseIcon className="w-4 h-4" />
                      Pause
                    </>
                  ) : (
                    <>
                      <PlayIcon className="w-4 h-4" />
                      Activate
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Node Count */}
            <div className="mt-4 pt-4 border-t border-dark-border">
              <div className="flex items-center gap-2 text-xs text-dark-text-muted">
                <Cog6ToothIcon className="w-4 h-4" />
                <span>{workflow.nodes?.length ?? 0} nodes configured</span>
                {workflow.tags && workflow.tags.length > 0 && (
                  <>
                    <span className="text-dark-border">|</span>
                    <div className="flex items-center gap-1 flex-wrap">
                      {workflow.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-terminal-500/20 text-terminal-400 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
