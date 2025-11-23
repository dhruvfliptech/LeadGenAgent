// Main workflow monitoring dashboard for n8n integration

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Cog6ToothIcon,
  ChartBarIcon,
  BellIcon,
  ExclamationCircleIcon,
  ClockIcon,
  CheckCircleIcon,
  BoltIcon
} from '@heroicons/react/24/outline'
import { workflowsApi } from '@/services/workflowsApi'
import { Workflow, WorkflowExecution, WorkflowStats, WorkflowMetrics, ApprovalRequest } from '@/types/workflow'
import WorkflowList from '@/components/WorkflowList'
import ExecutionDetailsModal from '@/components/ExecutionDetailsModal'
import LiveExecutionMonitor from '@/components/LiveExecutionMonitor'
import WorkflowStatistics from '@/components/WorkflowStatistics'
import ApprovalQueue from '@/components/ApprovalQueue'
import ErrorLogViewer from '@/components/ErrorLogViewer'
import PerformanceAnalytics from '@/components/PerformanceAnalytics'
import { formatRelativeTime } from '@/utils/dateFormat'

type DashboardTab = 'overview' | 'workflows' | 'executions' | 'approvals' | 'errors' | 'analytics'

export default function WorkflowDashboard() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview')
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null)
  const [isExecutionModalOpen, setIsExecutionModalOpen] = useState(false)

  // Fetch workflows
  const { data: workflows, isLoading: workflowsLoading } = useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: () => workflowsApi.getWorkflows().then(res => res.data),
    refetchInterval: 30000
  })

  // Fetch workflow metrics for all workflows
  const { data: workflowMetricsArray } = useQuery<WorkflowMetrics[]>({
    queryKey: ['workflow-metrics'],
    queryFn: async () => {
      if (!workflows || workflows.length === 0) return []
      const metricsPromises = workflows.map(w =>
        workflowsApi.getWorkflowMetrics(w.id).then(res => res.data).catch(() => null)
      )
      const results = await Promise.all(metricsPromises)
      return results.filter(m => m !== null) as WorkflowMetrics[]
    },
    enabled: !!workflows && workflows.length > 0,
    refetchInterval: 60000
  })

  // Fetch overall stats
  const { data: stats } = useQuery<WorkflowStats>({
    queryKey: ['workflow-stats'],
    queryFn: () => workflowsApi.getStats().then(res => res.data),
    refetchInterval: 30000
  })

  // Fetch recent executions
  const { data: executions } = useQuery<WorkflowExecution[]>({
    queryKey: ['executions'],
    queryFn: () => workflowsApi.getRecentExecutions(100).then(res => res.data),
    refetchInterval: 10000
  })

  // Fetch pending approvals
  const { data: approvals } = useQuery<ApprovalRequest[]>({
    queryKey: ['approvals'],
    queryFn: () => workflowsApi.getPendingApprovals().then(res => res.data),
    refetchInterval: 15000
  })

  // Filter executions
  const runningExecutions = executions?.filter(e => e.status === 'running') || []
  const failedExecutions = executions?.filter(e => e.status === 'error') || []
  const recentExecutions = executions?.slice(0, 10) || []

  // Convert metrics array to map
  const metricsMap = new Map<string, WorkflowMetrics>()
  workflowMetricsArray?.forEach(m => metricsMap.set(m.workflow_id, m))

  const handleViewExecutionDetails = (execution: WorkflowExecution) => {
    setSelectedExecution(execution)
    setIsExecutionModalOpen(true)
  }

  const tabs = [
    { id: 'overview' as DashboardTab, name: 'Overview', icon: ChartBarIcon },
    { id: 'workflows' as DashboardTab, name: 'Workflows', icon: Cog6ToothIcon, badge: workflows?.filter(w => w.active).length },
    { id: 'executions' as DashboardTab, name: 'Live Executions', icon: ClockIcon, badge: runningExecutions.length },
    { id: 'approvals' as DashboardTab, name: 'Approvals', icon: BellIcon, badge: approvals?.length },
    { id: 'errors' as DashboardTab, name: 'Errors', icon: ExclamationCircleIcon, badge: failedExecutions.length },
    { id: 'analytics' as DashboardTab, name: 'Analytics', icon: BoltIcon }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl">
          Workflow Automation Dashboard
        </h2>
        <p className="mt-1 text-sm text-dark-text-secondary">
          Monitor and manage n8n workflow executions in real-time
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Cog6ToothIcon className="h-6 w-6 text-terminal-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">
                  {workflows?.filter(w => w.active).length || 0}
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Active Workflows</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  {workflows?.length || 0} total
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-6 w-6 text-green-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-terminal-400 font-mono">
                  {stats.success_rate.toFixed(1)}%
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Success Rate</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  {stats.successful_executions} successful
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationCircleIcon className="h-6 w-6 text-red-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">
                  {stats.failed_executions}
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Failed</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  {stats.running_executions} running
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BellIcon className="h-6 w-6 text-yellow-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">
                  {approvals?.length || 0}
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Pending Approvals</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  Awaiting decision
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-dark-border">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                  isActive
                    ? 'border-terminal-500 text-terminal-400'
                    : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
                }`}
              >
                <Icon className={`-ml-0.5 mr-2 h-5 w-5 ${isActive ? 'text-terminal-500' : 'text-dark-text-muted'}`} />
                {tab.name}
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span className={`ml-2 py-0.5 px-2 rounded-full text-xs font-medium ${
                    isActive
                      ? 'bg-terminal-500 text-white'
                      : 'bg-dark-border text-dark-text-secondary'
                  }`}>
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Live Executions */}
            {runningExecutions.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
                  <ClockIcon className="w-5 h-5 text-blue-500" />
                  Active Executions ({runningExecutions.length})
                </h3>
                <LiveExecutionMonitor
                  executions={runningExecutions}
                  onViewDetails={handleViewExecutionDetails}
                />
              </div>
            )}

            {/* Pending Approvals Preview */}
            {approvals && approvals.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
                  <BellIcon className="w-5 h-5 text-yellow-500" />
                  Pending Approvals ({approvals.length})
                </h3>
                <ApprovalQueue approvals={approvals.slice(0, 3)} />
                {approvals.length > 3 && (
                  <button
                    onClick={() => setActiveTab('approvals')}
                    className="mt-4 btn-secondary w-full"
                  >
                    View All {approvals.length} Approvals
                  </button>
                )}
              </div>
            )}

            {/* Recent Executions */}
            <div>
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                Recent Executions
              </h3>
              <div className="card overflow-hidden">
                <div className="divide-y divide-dark-border">
                  {recentExecutions.map(execution => {
                    const statusColors = {
                      success: 'text-green-500',
                      error: 'text-red-500',
                      running: 'text-blue-500',
                      waiting: 'text-yellow-500',
                      canceled: 'text-gray-500'
                    }
                    const statusIcons = {
                      success: CheckCircleIcon,
                      error: ExclamationCircleIcon,
                      running: ClockIcon,
                      waiting: ClockIcon,
                      canceled: ExclamationCircleIcon
                    }
                    const StatusIcon = statusIcons[execution.status as keyof typeof statusIcons] || ClockIcon

                    return (
                      <button
                        key={execution.id}
                        onClick={() => handleViewExecutionDetails(execution)}
                        className="w-full p-4 flex items-center justify-between hover:bg-dark-border/50 transition-colors text-left"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <StatusIcon className={`w-5 h-5 flex-shrink-0 ${statusColors[execution.status as keyof typeof statusColors]}`} />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-dark-text-primary truncate">
                              {execution.workflowName}
                            </div>
                            <div className="text-xs text-dark-text-muted">
                              {formatRelativeTime(execution.startedAt)}
                              {execution.duration && ` • ${execution.duration.toFixed(1)}s`}
                            </div>
                          </div>
                        </div>
                        <span className={`text-xs font-medium capitalize ${statusColors[execution.status as keyof typeof statusColors]}`}>
                          {execution.status}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Statistics Overview */}
            {stats && (
              <div>
                <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                  Execution Statistics
                </h3>
                <WorkflowStatistics stats={stats} />
              </div>
            )}
          </div>
        )}

        {activeTab === 'workflows' && (
          <div>
            {workflowsLoading ? (
              <div className="card p-12 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terminal-500 mx-auto"></div>
                <p className="text-dark-text-secondary mt-4">Loading workflows...</p>
              </div>
            ) : (
              <WorkflowList
                workflows={workflows || []}
                metrics={metricsMap}
              />
            )}
          </div>
        )}

        {activeTab === 'executions' && (
          <div>
            <LiveExecutionMonitor
              executions={runningExecutions}
              onViewDetails={handleViewExecutionDetails}
            />
          </div>
        )}

        {activeTab === 'approvals' && (
          <div>
            {approvals && approvals.length > 0 ? (
              <ApprovalQueue approvals={approvals} />
            ) : (
              <div className="card p-12 text-center">
                <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <p className="text-dark-text-secondary">No pending approvals</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'errors' && (
          <div>
            <ErrorLogViewer executions={failedExecutions} />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            {stats ? (
              <PerformanceAnalytics stats={stats} />
            ) : (
              <div className="card p-12 text-center">
                <p className="text-dark-text-secondary">Loading analytics...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Execution Details Modal */}
      <ExecutionDetailsModal
        execution={selectedExecution}
        isOpen={isExecutionModalOpen}
        onClose={() => {
          setIsExecutionModalOpen(false)
          setSelectedExecution(null)
        }}
      />
    </div>
  )
}
