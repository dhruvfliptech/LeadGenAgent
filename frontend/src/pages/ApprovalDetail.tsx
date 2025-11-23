import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline'
import RiskIndicator from '@/components/approvals/RiskIndicator'
import { mockApprovals } from '@/mocks/approvals.mock'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

export default function ApprovalDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectForm, setShowRejectForm] = useState(false)

  const approval = mockApprovals.find(a => a.approval_id === id)

  if (!approval) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Approval not found</h2>
        <Link to="/approvals" className="text-blue-600 hover:text-blue-700">
          Back to Approvals
        </Link>
      </div>
    )
  }

  const handleApprove = () => {
    toast.success('Approval request approved')
    navigate('/approvals')
  }

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      toast.error('Please provide a rejection reason')
      return
    }
    toast.success('Approval request rejected')
    navigate('/approvals')
  }

  const isExpired = approval.status === 'expired'
  const isPending = approval.status === 'pending'
  const isReviewed = approval.status === 'approved' || approval.status === 'rejected'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/approvals"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Approvals
        </Link>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {approval.title}
            </h1>
            <p className="text-gray-600">
              {approval.description}
            </p>
          </div>
          <div className="ml-6">
            <RiskIndicator level={approval.risk_level} score={approval.risk_score} size="lg" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Risk Assessment */}
          <div className="card">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <ExclamationTriangleIcon className="w-5 h-5 text-orange-500" />
                Risk Assessment
              </h2>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-2">Risk Score</div>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${
                        approval.risk_score >= 80 ? 'bg-red-600' :
                        approval.risk_score >= 60 ? 'bg-orange-500' :
                        approval.risk_score >= 40 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${approval.risk_score}%` }}
                    />
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {approval.risk_score}/100
                  </div>
                </div>
              </div>

              {approval.risk_factors.length > 0 && (
                <div>
                  <div className="text-sm text-gray-500 mb-2">Risk Factors</div>
                  <ul className="space-y-2">
                    {approval.risk_factors.map((factor, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <span className="text-orange-500 mt-0.5">•</span>
                        <span className="flex-1 text-gray-700">{factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Preview Panel */}
          {approval.preview_data && (
            <div className="card">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-gray-500" />
                  Preview
                </h2>
              </div>
              <div className="p-6 space-y-4">
                {approval.preview_data.email_subject && (
                  <div>
                    <div className="text-sm font-medium text-gray-500 mb-1">Subject</div>
                    <div className="text-gray-900">{approval.preview_data.email_subject}</div>
                  </div>
                )}

                {approval.preview_data.recipient && (
                  <div>
                    <div className="text-sm font-medium text-gray-500 mb-1">Recipient</div>
                    <div className="text-gray-900">{approval.preview_data.recipient}</div>
                  </div>
                )}

                {approval.preview_data.email_body && (
                  <div>
                    <div className="text-sm font-medium text-gray-500 mb-1">Message</div>
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <pre className="whitespace-pre-wrap text-sm text-gray-900 font-sans">
                        {approval.preview_data.email_body}
                      </pre>
                    </div>
                  </div>
                )}

                {approval.preview_data.url && (
                  <div>
                    <div className="text-sm font-medium text-gray-500 mb-1">URL</div>
                    <a
                      href={approval.preview_data.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
                    >
                      <GlobeAltIcon className="w-4 h-4" />
                      {approval.preview_data.url}
                    </a>
                  </div>
                )}

                {approval.preview_data.action && (
                  <div>
                    <div className="text-sm font-medium text-gray-500 mb-1">Action</div>
                    <div className="text-gray-900">{approval.preview_data.action}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Context */}
          {approval.context && Object.keys(approval.context).length > 0 && (
            <div className="card">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Context</h2>
              </div>
              <div className="p-6">
                <dl className="grid grid-cols-2 gap-4">
                  {Object.entries(approval.context).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-sm font-medium text-gray-500 mb-1">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </dt>
                      <dd className="text-sm text-gray-900">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Right Column */}
        <div className="space-y-6">
          {/* Actions */}
          {isPending && (
            <div className="card p-6 space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">Actions</h2>

              {!showRejectForm ? (
                <>
                  <button
                    onClick={handleApprove}
                    className="w-full btn-primary inline-flex items-center justify-center gap-2"
                  >
                    <CheckCircleIcon className="w-5 h-5" />
                    Approve
                  </button>
                  <button
                    onClick={() => setShowRejectForm(true)}
                    className="w-full btn-secondary inline-flex items-center justify-center gap-2"
                  >
                    <XCircleIcon className="w-5 h-5" />
                    Reject
                  </button>
                </>
              ) : (
                <div className="space-y-3">
                  <textarea
                    className="form-input w-full"
                    rows={4}
                    placeholder="Reason for rejection..."
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleReject}
                      className="flex-1 btn-secondary"
                    >
                      Confirm Reject
                    </button>
                    <button
                      onClick={() => setShowRejectForm(false)}
                      className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Status */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Status</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Status</span>
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                    approval.status === 'approved' ? 'bg-green-100 text-green-800' :
                    approval.status === 'rejected' ? 'bg-red-100 text-red-800' :
                    approval.status === 'expired' ? 'bg-gray-100 text-gray-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  {approval.status === 'approved' && <CheckCircleIcon className="w-3 h-3" />}
                  {approval.status === 'rejected' && <XCircleIcon className="w-3 h-3" />}
                  {approval.status === 'pending' && <ClockIcon className="w-3 h-3" />}
                  {approval.status.charAt(0).toUpperCase() + approval.status.slice(1)}
                </span>
              </div>

              {approval.expires_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Expires</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formatRelativeTime(approval.expires_at)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Related Information */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Details</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-600">Type</dt>
                <dd className="text-sm font-medium text-gray-900 mt-1">
                  {approval.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-gray-600">Requested By</dt>
                <dd className="text-sm font-medium text-gray-900 mt-1 flex items-center gap-1">
                  <UserIcon className="w-4 h-4" />
                  {approval.requested_by}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-gray-600">Requested</dt>
                <dd className="text-sm font-medium text-gray-900 mt-1">
                  {formatRelativeTime(approval.requested_at)}
                </dd>
              </div>

              {approval.assigned_to && (
                <div>
                  <dt className="text-sm text-gray-600">Assigned To</dt>
                  <dd className="text-sm font-medium text-gray-900 mt-1">
                    {approval.assigned_to}
                  </dd>
                </div>
              )}

              {approval.lead_name && (
                <div>
                  <dt className="text-sm text-gray-600">Related Lead</dt>
                  <dd className="text-sm font-medium text-gray-900 mt-1">
                    <Link to={`/leads`} className="text-blue-600 hover:text-blue-700">
                      {approval.lead_name}
                    </Link>
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Review History */}
          {isReviewed && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Review History</h2>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`flex-shrink-0 w-2 h-2 mt-1.5 rounded-full ${
                      approval.approved ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {approval.approved ? 'Approved' : 'Rejected'}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {approval.reviewed_by} • {formatRelativeTime(approval.reviewed_at!)}
                    </div>
                    {approval.rejection_reason && (
                      <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-2 rounded">
                        {approval.rejection_reason}
                      </div>
                    )}
                    {approval.notes && (
                      <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-2 rounded">
                        {approval.notes}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
