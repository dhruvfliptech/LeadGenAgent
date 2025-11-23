// Real-time monitoring component for active workflow executions

import { ClockIcon, BoltIcon } from '@heroicons/react/24/outline'
import { WorkflowExecution } from '@/types/workflow'
import { formatRelativeTime } from '@/utils/dateFormat'
import { useWorkflowUpdates } from '@/hooks/useWorkflowUpdates'

interface LiveExecutionMonitorProps {
  executions: WorkflowExecution[]
  onViewDetails?: (execution: WorkflowExecution) => void
}

export default function LiveExecutionMonitor({
  executions,
  onViewDetails
}: LiveExecutionMonitorProps) {
  const { activeExecutions, isConnected } = useWorkflowUpdates({
    autoConnect: true
  })

  const runningExecutions = executions.filter(e => e.status === 'running')

  // Merge static executions with live updates
  const mergedExecutions = runningExecutions.map(exec => {
    const liveUpdate = activeExecutions.find(a => a.execution_id === exec.id)
    return liveUpdate ? { ...exec, liveUpdate } : exec
  })

  if (mergedExecutions.length === 0) {
    return (
      <div className="card p-6 text-center">
        <BoltIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-3" />
        <p className="text-dark-text-secondary">No active executions</p>
        <p className="text-xs text-dark-text-muted mt-1">
          Executions will appear here when workflows are running
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Connection Status */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
          <span className="text-dark-text-muted">
            {isConnected ? 'Live updates enabled' : 'Connecting...'}
          </span>
        </div>
        <span className="text-dark-text-muted">
          {mergedExecutions.length} active execution{mergedExecutions.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Execution Cards */}
      {mergedExecutions.map((execution: any) => {
        const liveUpdate = execution.liveUpdate
        const progress = liveUpdate?.progress_percentage ?? 0
        const currentNode = liveUpdate?.current_node
        const eta = liveUpdate?.eta_seconds

        return (
          <div
            key={execution.id}
            className="card p-4 hover:shadow-lg transition-shadow cursor-pointer border border-blue-500/30 bg-blue-500/5"
            onClick={() => onViewDetails?.(execution)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <ClockIcon className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0" />
                  <h4 className="font-medium text-dark-text-primary truncate">
                    {execution.workflowName}
                  </h4>
                </div>
                <div className="text-xs text-dark-text-muted">
                  Started {formatRelativeTime(execution.startedAt)}
                </div>
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30">
                Running
              </span>
            </div>

            {/* Current Node */}
            {currentNode && (
              <div className="mb-3 p-2 bg-dark-bg rounded border border-dark-border">
                <div className="text-xs text-dark-text-muted mb-1">Current Step</div>
                <div className="text-sm text-dark-text-primary font-medium">{currentNode}</div>
              </div>
            )}

            {/* Progress Bar */}
            {progress > 0 && (
              <div className="mb-2">
                <div className="flex justify-between text-xs text-dark-text-secondary mb-1">
                  <span>{progress}% complete</span>
                  {eta && (
                    <span>
                      ETA: {eta < 60 ? `${eta}s` : `${Math.floor(eta / 60)}m ${eta % 60}s`}
                    </span>
                  )}
                </div>
                <div className="w-full bg-dark-border rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Message */}
            {liveUpdate?.message && (
              <div className="text-xs text-dark-text-muted italic">
                {liveUpdate.message}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
