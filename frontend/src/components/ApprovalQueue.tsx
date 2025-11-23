// Component to display and manage pending approval requests

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  RocketLaunchIcon,
  VideoCameraIcon,
  EnvelopeIcon,
  DocumentTextIcon,
  EyeIcon
} from '@heroicons/react/24/outline'
import { ApprovalRequest } from '@/types/workflow'
import { workflowsApi } from '@/services/workflowsApi'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

interface ApprovalQueueProps {
  approvals: ApprovalRequest[]
  filterType?: string
}

export default function ApprovalQueue({ approvals, filterType }: ApprovalQueueProps) {
  const queryClient = useQueryClient()
  const [expandedApproval, setExpandedApproval] = useState<number | null>(null)
  const [rejectReason, setRejectReason] = useState('')

  const approveMutation = useMutation({
    mutationFn: ({ id, comments }: { id: number; comments?: string }) =>
      workflowsApi.approveRequest(id, comments),
    onSuccess: () => {
      toast.success('Approval granted')
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['executions'] })
      setExpandedApproval(null)
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to approve')
    }
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      workflowsApi.rejectRequest(id, reason),
    onSuccess: () => {
      toast.success('Request rejected')
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['executions'] })
      setExpandedApproval(null)
      setRejectReason('')
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to reject')
    }
  })

  const getApprovalIcon = (type: string) => {
    switch (type) {
      case 'demo_site':
        return <RocketLaunchIcon className="w-6 h-6 text-blue-500" />
      case 'demo_video':
        return <VideoCameraIcon className="w-6 h-6 text-purple-500" />
      case 'email_send':
        return <EnvelopeIcon className="w-6 h-6 text-green-500" />
      default:
        return <DocumentTextIcon className="w-6 h-6 text-gray-500" />
    }
  }

  const getApprovalTypeLabel = (type: string) => {
    switch (type) {
      case 'demo_site':
        return 'Demo Site'
      case 'demo_video':
        return 'Demo Video'
      case 'email_send':
        return 'Email Send'
      default:
        return 'Resource'
    }
  }

  const calculateTimeRemaining = (timeoutAt: string) => {
    const timeout = new Date(timeoutAt).getTime()
    const now = Date.now()
    const remaining = timeout - now

    if (remaining <= 0) return 'Expired'

    const minutes = Math.floor(remaining / 60000)
    const hours = Math.floor(minutes / 60)

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m remaining`
    }
    return `${minutes}m remaining`
  }

  const getTimeRemainingColor = (timeoutAt: string) => {
    const timeout = new Date(timeoutAt).getTime()
    const now = Date.now()
    const remaining = timeout - now
    const minutes = remaining / 60000

    if (minutes <= 0) return 'text-red-500'
    if (minutes <= 15) return 'text-yellow-500'
    return 'text-green-500'
  }

  const filteredApprovals = filterType
    ? approvals.filter(a => a.approval_type === filterType)
    : approvals

  if (filteredApprovals.length === 0) {
    return (
      <div className="card p-6 text-center">
        <CheckCircleIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-3" />
        <p className="text-dark-text-secondary">No pending approvals</p>
        <p className="text-xs text-dark-text-muted mt-1">
          All requests have been processed
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {filteredApprovals.map(approval => {
        const isExpanded = expandedApproval === approval.id
        const metadata = approval.metadata || {}

        return (
          <div
            key={approval.id}
            className="card p-6 border-l-4 border-yellow-500"
          >
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className="flex-shrink-0">
                {getApprovalIcon(approval.approval_type)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-lg font-semibold text-dark-text-primary">
                      {getApprovalTypeLabel(approval.approval_type)} Approval Required
                    </h3>
                    {metadata.business_name && (
                      <p className="text-sm text-dark-text-secondary mt-1">
                        Business: {metadata.business_name}
                      </p>
                    )}
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                    Pending
                  </span>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3 text-sm">
                  {metadata.category && (
                    <div>
                      <span className="text-dark-text-muted">Category:</span>
                      <span className="text-dark-text-primary ml-2">{metadata.category}</span>
                    </div>
                  )}
                  {metadata.quality_score !== undefined && (
                    <div>
                      <span className="text-dark-text-muted">Quality Score:</span>
                      <span className="text-dark-text-primary ml-2 font-semibold">
                        {metadata.quality_score}
                      </span>
                    </div>
                  )}
                  {metadata.lead_id && (
                    <div>
                      <span className="text-dark-text-muted">Lead ID:</span>
                      <span className="text-dark-text-primary ml-2 font-mono">
                        #{metadata.lead_id}
                      </span>
                    </div>
                  )}
                </div>

                {/* Time Remaining */}
                <div className="flex items-center gap-2 mb-3">
                  <ClockIcon className={`w-4 h-4 ${getTimeRemainingColor(approval.timeout_at)}`} />
                  <span className={`text-sm font-medium ${getTimeRemainingColor(approval.timeout_at)}`}>
                    {calculateTimeRemaining(approval.timeout_at)}
                  </span>
                  <span className="text-xs text-dark-text-muted">
                    • Created {formatRelativeTime(approval.created_at)}
                  </span>
                </div>

                {/* Preview Links */}
                <div className="flex items-center gap-3 mb-4">
                  {metadata.preview_url && (
                    <a
                      href={metadata.preview_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-2"
                    >
                      <EyeIcon className="w-4 h-4" />
                      View Demo
                    </a>
                  )}
                  {metadata.video_url && (
                    <a
                      href={metadata.video_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary text-sm py-1.5 px-3 flex items-center gap-2"
                    >
                      <VideoCameraIcon className="w-4 h-4" />
                      View Video
                    </a>
                  )}
                  {approval.resource_data && (
                    <button
                      onClick={() => setExpandedApproval(isExpanded ? null : approval.id)}
                      className="btn-secondary text-sm py-1.5 px-3"
                    >
                      {isExpanded ? 'Hide' : 'Show'} Details
                    </button>
                  )}
                </div>

                {/* Expanded Details */}
                {isExpanded && approval.resource_data && (
                  <div className="mb-4 p-4 bg-dark-bg rounded border border-dark-border">
                    <h4 className="text-sm font-medium text-dark-text-primary mb-2">
                      Resource Data
                    </h4>
                    <pre className="text-xs text-dark-text-muted overflow-x-auto">
                      {JSON.stringify(approval.resource_data, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Email Subject (if email approval) */}
                {approval.approval_type === 'email_send' && metadata.email_subject && (
                  <div className="mb-4 p-3 bg-dark-bg rounded border border-dark-border">
                    <div className="text-xs text-dark-text-muted mb-1">Subject:</div>
                    <div className="text-sm text-dark-text-primary font-medium">
                      {metadata.email_subject}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => approveMutation.mutate({ id: approval.id })}
                    disabled={approveMutation.isPending || rejectMutation.isPending}
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                  >
                    <CheckCircleIcon className="w-5 h-5" />
                    Approve
                  </button>

                  <div className="flex-1 flex items-center gap-2">
                    <input
                      type="text"
                      value={expandedApproval === approval.id ? rejectReason : ''}
                      onChange={(e) => {
                        setExpandedApproval(approval.id)
                        setRejectReason(e.target.value)
                      }}
                      placeholder="Rejection reason (optional)"
                      className="form-input flex-1 text-sm"
                    />
                    <button
                      onClick={() => {
                        if (!rejectReason.trim()) {
                          toast.error('Please provide a rejection reason')
                          return
                        }
                        rejectMutation.mutate({
                          id: approval.id,
                          reason: rejectReason
                        })
                      }}
                      disabled={approveMutation.isPending || rejectMutation.isPending}
                      className="btn-secondary flex items-center gap-2 text-red-500 hover:text-red-400 disabled:opacity-50"
                    >
                      <XCircleIcon className="w-5 h-5" />
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
