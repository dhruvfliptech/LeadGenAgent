import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  BoltIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import WorkflowCard from '@/components/workflows/WorkflowCard'
import { mockWorkflows, getWorkflowStats, WorkflowStatus } from '@/mocks/workflows.mock'

export default function WorkflowsEnhanced() {
  const [filterStatus, setFilterStatus] = useState<WorkflowStatus | 'all'>('all')

  const stats = getWorkflowStats()

  // Filter workflows
  const filteredWorkflows = useMemo(() => {
    if (filterStatus === 'all') {
      return mockWorkflows
    }
    return mockWorkflows.filter(w => w.status === filterStatus)
  }, [filterStatus])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate flex items-center gap-2">
            <BoltIcon className="w-8 h-8 text-gray-500" />
            n8n Workflows
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor and manage automated workflow executions
          </p>
        </div>
        <div className="mt-4 flex gap-3 md:mt-0 md:ml-4">
          <Link to="/webhooks" className="btn-secondary inline-flex items-center gap-2">
            <ClockIcon className="w-4 h-4" />
            Webhook Queue
          </Link>
          <button className="btn-primary inline-flex items-center gap-2">
            <PlusIcon className="w-4 h-4" />
            New Workflow
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-blue-500 p-3">
                <BoltIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Workflows
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.total}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-green-500 p-3">
                <CheckCircleIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Active
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.active}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-purple-500 p-3">
                <CheckCircleIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Success Rate
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.avg_success_rate.toFixed(1)}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-orange-500 p-3">
                <BoltIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Executions
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.total_executions.toLocaleString()}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setFilterStatus('all')}
            className={`${
              filterStatus === 'all'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            All Workflows
            <span className="bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs font-medium">
              {stats.total}
            </span>
          </button>

          <button
            onClick={() => setFilterStatus('active')}
            className={`${
              filterStatus === 'active'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <CheckCircleIcon className="w-4 h-4" />
            Active
            <span className="bg-green-100 text-green-900 py-0.5 px-2.5 rounded-full text-xs font-medium">
              {stats.active}
            </span>
          </button>

          <button
            onClick={() => setFilterStatus('inactive')}
            className={`${
              filterStatus === 'inactive'
                ? 'border-gray-500 text-gray-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <ClockIcon className="w-4 h-4" />
            Inactive
            <span className="bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs font-medium">
              {stats.inactive}
            </span>
          </button>

          <button
            onClick={() => setFilterStatus('error')}
            className={`${
              filterStatus === 'error'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <XCircleIcon className="w-4 h-4" />
            Error
            <span className="bg-red-100 text-red-900 py-0.5 px-2.5 rounded-full text-xs font-medium">
              {stats.error}
            </span>
          </button>
        </nav>
      </div>

      {/* Workflows Grid */}
      {filteredWorkflows.length === 0 ? (
        <div className="card p-12 text-center">
          <BoltIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No workflows found</h3>
          <p className="text-gray-500">
            {filterStatus === 'all'
              ? 'Create your first workflow to get started.'
              : `No workflows with status "${filterStatus}".`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredWorkflows.map(workflow => (
            <WorkflowCard key={workflow.id} workflow={workflow} />
          ))}
        </div>
      )}

      {/* Quick Stats Footer */}
      <div className="card p-6">
        <div className="grid grid-cols-3 gap-6 text-center">
          <div>
            <div className="text-3xl font-bold text-green-600">
              {stats.successful_executions.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">Successful Executions</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-red-600">
              {stats.failed_executions.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500 mt-1">Failed Executions</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-blue-600">
              {stats.avg_success_rate.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">Average Success Rate</div>
          </div>
        </div>
      </div>
    </div>
  )
}
