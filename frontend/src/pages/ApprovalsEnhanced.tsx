import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  InboxStackIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  AdjustmentsHorizontalIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import ApprovalCard from '@/components/approvals/ApprovalCard'
import { mockApprovals, getApprovalStats, RiskLevel, ApprovalType } from '@/mocks/approvals.mock'

export default function ApprovalsEnhanced() {
  const [filterRisk, setFilterRisk] = useState<RiskLevel | 'all'>('all')
  const [filterType, setFilterType] = useState<ApprovalType | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<'pending' | 'all'>('pending')

  const stats = getApprovalStats()

  // Get today's date for filtering
  const today = new Date().toISOString().split('T')[0]
  const approvedToday = mockApprovals.filter(a =>
    a.status === 'approved' &&
    a.reviewed_at &&
    a.reviewed_at.startsWith(today)
  ).length

  // Filter approvals
  const filteredApprovals = useMemo(() => {
    let filtered = mockApprovals

    if (filterStatus === 'pending') {
      filtered = filtered.filter(a => a.status === 'pending')
    }

    if (filterRisk !== 'all') {
      filtered = filtered.filter(a => a.risk_level === filterRisk)
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(a => a.type === filterType)
    }

    // Sort by risk level (critical first) and then by creation time
    const riskOrder = { critical: 0, high: 1, medium: 2, low: 3 }
    return filtered.sort((a, b) => {
      if (a.risk_level !== b.risk_level) {
        return riskOrder[a.risk_level] - riskOrder[b.risk_level]
      }
      return new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime()
    })
  }, [filterRisk, filterType, filterStatus])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate flex items-center gap-2">
            <InboxStackIcon className="w-8 h-8 text-gray-500" />
            Approval Workflows
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Review and approve automated actions before they execute
          </p>
        </div>
        <div className="mt-4 flex gap-3 md:mt-0 md:ml-4">
          <Link to="/approvals/rules" className="btn-secondary inline-flex items-center gap-2">
            <Cog6ToothIcon className="w-4 h-4" />
            Approval Rules
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-orange-500 p-3">
                <ClockIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Pending
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.pending}
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
                  Approved Today
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {approvedToday}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-red-500 p-3">
                <XCircleIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Rejected
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.rejected}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="rounded-md bg-gray-500 p-3">
                <ClockIcon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Expired
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {stats.expired}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <AdjustmentsHorizontalIcon className="w-5 h-5 text-gray-400" />
          <div className="flex items-center gap-2 text-sm">
            <label className="font-medium text-gray-700">Status:</label>
            <select
              className="form-input py-1 text-sm"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
            >
              <option value="pending">Pending Only</option>
              <option value="all">All Statuses</option>
            </select>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <label className="font-medium text-gray-700">Risk Level:</label>
            <select
              className="form-input py-1 text-sm"
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value as any)}
            >
              <option value="all">All Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <label className="font-medium text-gray-700">Type:</label>
            <select
              className="form-input py-1 text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
            >
              <option value="all">All Types</option>
              <option value="email_response">Email Response</option>
              <option value="email_campaign">Email Campaign</option>
              <option value="lead_action">Lead Action</option>
              <option value="demo_site_deploy">Demo Site</option>
              <option value="video_publish">Video</option>
              <option value="workflow_trigger">Workflow</option>
            </select>
          </div>
          <div className="ml-auto text-sm text-gray-500">
            Showing {filteredApprovals.length} of {stats.total}
          </div>
        </div>
      </div>

      {/* Approvals Grid */}
      {filteredApprovals.length === 0 ? (
        <div className="card p-12 text-center">
          <InboxStackIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No approvals found</h3>
          <p className="text-gray-500">
            {filterStatus === 'pending'
              ? 'All pending approvals have been reviewed.'
              : 'No approvals match your current filters.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredApprovals.map(approval => (
            <ApprovalCard key={approval.id} approval={approval} />
          ))}
        </div>
      )}
    </div>
  )
}
