import { MockWorkflow } from '@/mocks/workflows.mock'
import { Link } from 'react-router-dom'
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  BoltIcon,
  CalendarIcon,
  CursorArrowRaysIcon
} from '@heroicons/react/24/outline'
import { formatRelativeTime } from '@/utils/dateFormat'

interface WorkflowCardProps {
  workflow: MockWorkflow
}

const statusConfig = {
  active: {
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: CheckCircleIcon
  },
  inactive: {
    color: 'bg-gray-100 text-gray-600 border-gray-200',
    icon: ClockIcon
  },
  error: {
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: XCircleIcon
  }
}

const triggerIcons = {
  webhook: BoltIcon,
  schedule: CalendarIcon,
  manual: CursorArrowRaysIcon,
  event: BoltIcon
}

export default function WorkflowCard({ workflow }: WorkflowCardProps) {
  const config = statusConfig[workflow.status]
  const StatusIcon = config.icon
  const TriggerIcon = triggerIcons[workflow.trigger_type]
  const successRate = workflow.total_executions > 0
    ? (workflow.successful_executions / workflow.total_executions * 100).toFixed(1)
    : 0

  return (
    <Link
      to={`/workflows/${workflow.workflow_id}`}
      className="block card hover:shadow-md transition-shadow"
    >
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full border ${config.color}`}
              >
                <StatusIcon className="w-3 h-3" />
                {workflow.status.charAt(0).toUpperCase() + workflow.status.slice(1)}
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                <TriggerIcon className="w-3 h-3" />
                {workflow.trigger_type}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">
              {workflow.name}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {workflow.description}
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-xs text-gray-500 mb-1">Total Executions</div>
            <div className="text-lg font-semibold text-gray-900">
              {workflow.total_executions.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Success Rate</div>
            <div className="text-lg font-semibold text-green-600">
              {successRate}%
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Avg Time</div>
            <div className="text-lg font-semibold text-gray-900">
              {(workflow.avg_execution_time_ms / 1000).toFixed(1)}s
            </div>
          </div>
        </div>
      </div>

      {workflow.last_execution_at && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Last execution:</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-900">
                {formatRelativeTime(workflow.last_execution_at)}
              </span>
              {workflow.last_execution_status === 'success' ? (
                <CheckCircleIcon className="w-4 h-4 text-green-600" />
              ) : workflow.last_execution_status === 'error' ? (
                <XCircleIcon className="w-4 h-4 text-red-600" />
              ) : (
                <ClockIcon className="w-4 h-4 text-yellow-600" />
              )}
            </div>
          </div>
        </div>
      )}
    </Link>
  )
}
