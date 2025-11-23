import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlayIcon,
  StopIcon,
  BoltIcon,
  CalendarIcon,
  CursorArrowRaysIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import WorkflowDiagram from '@/components/workflows/WorkflowDiagram'
import { mockWorkflows, mockExecutions, getRecentExecutions } from '@/mocks/workflows.mock'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

const triggerIcons = {
  webhook: BoltIcon,
  schedule: CalendarIcon,
  manual: CursorArrowRaysIcon,
  event: BoltIcon
}

export default function WorkflowDetail() {
  const { id } = useParams<{ id: string }>()
  const [showLogs, setShowLogs] = useState(false)
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null)

  const workflow = mockWorkflows.find(w => w.workflow_id === id)
  const executions = workflow ? getRecentExecutions(workflow.workflow_id, 10) : []

  if (!workflow) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflow not found</h2>
        <Link to="/workflows" className="text-blue-600 hover:text-blue-700">
          Back to Workflows
        </Link>
      </div>
    )
  }

  const TriggerIcon = triggerIcons[workflow.trigger_type]
  const successRate = workflow.total_executions > 0
    ? (workflow.successful_executions / workflow.total_executions * 100).toFixed(1)
    : 0

  const handleToggleWorkflow = () => {
    toast.success(workflow.enabled ? 'Workflow disabled' : 'Workflow enabled')
  }

  const handleTestWorkflow = () => {
    toast.success('Workflow test execution started')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/workflows"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Workflows
        </Link>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {workflow.name}
              </h1>
              <span
                className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
                  workflow.status === 'active'
                    ? 'bg-green-100 text-green-800'
                    : workflow.status === 'error'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {workflow.status === 'active' && <CheckCircleIcon className="w-4 h-4" />}
                {workflow.status === 'error' && <XCircleIcon className="w-4 h-4" />}
                {workflow.status === 'inactive' && <ClockIcon className="w-4 h-4" />}
                {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
              </span>
            </div>
            <p className="text-gray-600">{workflow.description}</p>
          </div>
          <div className="ml-6 flex gap-2">
            <button
              onClick={handleTestWorkflow}
              className="btn-secondary inline-flex items-center gap-2"
            >
              <PlayIcon className="w-4 h-4" />
              Test
            </button>
            <button
              onClick={handleToggleWorkflow}
              className={`btn-primary inline-flex items-center gap-2 ${
                workflow.enabled ? 'bg-red-600 hover:bg-red-700' : ''
              }`}
            >
              {workflow.enabled ? (
                <>
                  <StopIcon className="w-4 h-4" />
                  Disable
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  Enable
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Total Executions</div>
          <div className="text-2xl font-bold text-gray-900">
            {workflow.total_executions.toLocaleString()}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-green-600">
            {successRate}%
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Failed</div>
          <div className="text-2xl font-bold text-red-600">
            {workflow.failed_executions}
          </div>
        </div>
        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Avg Time</div>
          <div className="text-2xl font-bold text-blue-600">
            {(workflow.avg_execution_time_ms / 1000).toFixed(1)}s
          </div>
        </div>
      </div>

      {/* Trigger Info */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TriggerIcon className="w-5 h-5 text-gray-500" />
            Trigger Configuration
          </h2>
        </div>
        <div className="p-6">
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Type</dt>
              <dd className="text-sm text-gray-900 capitalize">
                {workflow.trigger_type}
              </dd>
            </div>
            {workflow.trigger_config?.webhook_path && (
              <div>
                <dt className="text-sm font-medium text-gray-500 mb-1">Webhook Path</dt>
                <dd className="text-sm text-gray-900 font-mono">
                  /webhook/{workflow.trigger_config.webhook_path}
                </dd>
              </div>
            )}
            {workflow.trigger_config?.cron_expression && (
              <div>
                <dt className="text-sm font-medium text-gray-500 mb-1">Schedule</dt>
                <dd className="text-sm text-gray-900 font-mono">
                  {workflow.trigger_config.cron_expression}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Timeout</dt>
              <dd className="text-sm text-gray-900">
                {workflow.timeout_seconds}s
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 mb-1">Retry on Failure</dt>
              <dd className="text-sm text-gray-900">
                {workflow.retry_on_failure ? `Yes (max ${workflow.max_retries})` : 'No'}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Workflow Diagram */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Workflow Diagram</h2>
        </div>
        <WorkflowDiagram workflow={workflow} />
      </div>

      {/* Execution History */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Execution History</h2>
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="text-sm text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
          >
            <DocumentTextIcon className="w-4 h-4" />
            {showLogs ? 'Hide' : 'Show'} Logs
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Execution ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {executions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    No executions yet
                  </td>
                </tr>
              ) : (
                executions.map((execution) => (
                  <tr key={execution.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-mono text-gray-900">
                        {execution.execution_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                          execution.status === 'success'
                            ? 'bg-green-100 text-green-800'
                            : execution.status === 'error'
                            ? 'bg-red-100 text-red-800'
                            : execution.status === 'running'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {execution.status === 'success' && <CheckCircleIcon className="w-3 h-3" />}
                        {execution.status === 'error' && <XCircleIcon className="w-3 h-3" />}
                        {execution.status === 'running' && <ClockIcon className="w-3 h-3" />}
                        {execution.status.charAt(0).toUpperCase() + execution.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatRelativeTime(execution.started_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {execution.duration_ms ? `${(execution.duration_ms / 1000).toFixed(2)}s` : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => setSelectedExecution(
                          selectedExecution === execution.execution_id ? null : execution.execution_id
                        )}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        {selectedExecution === execution.execution_id ? 'Hide' : 'View'} Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Details */}
      {selectedExecution && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Execution Details: {selectedExecution}
            </h3>
          </div>
          <div className="p-6">
            {(() => {
              const execution = executions.find(e => e.execution_id === selectedExecution)
              if (!execution) return null

              return (
                <div className="space-y-4">
                  {execution.data.input && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-2">Input Data</div>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-x-auto">
                        {JSON.stringify(execution.data.input, null, 2)}
                      </pre>
                    </div>
                  )}
                  {execution.data.output && (
                    <div>
                      <div className="text-sm font-medium text-gray-500 mb-2">Output Data</div>
                      <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-x-auto">
                        {JSON.stringify(execution.data.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {execution.data.error && (
                    <div>
                      <div className="text-sm font-medium text-red-600 mb-2">Error</div>
                      <div className="bg-red-50 p-4 rounded-lg text-sm text-red-900">
                        {execution.data.error}
                      </div>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>
      )}

      {/* Logs Viewer */}
      {showLogs && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <DocumentTextIcon className="w-5 h-5 text-gray-500" />
              Workflow Logs
            </h2>
          </div>
          <div className="p-6 bg-gray-900">
            <pre className="text-green-400 text-xs font-mono">
              {`[${new Date().toISOString()}] Workflow initialized
[${new Date().toISOString()}] Trigger: ${workflow.trigger_type}
[${new Date().toISOString()}] Nodes: ${workflow.nodes.length}
[${new Date().toISOString()}] Status: ${workflow.status}
[${new Date().toISOString()}] Last execution: ${workflow.last_execution_at ? formatRelativeTime(workflow.last_execution_at) : 'Never'}
[${new Date().toISOString()}] Success rate: ${successRate}%`}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
