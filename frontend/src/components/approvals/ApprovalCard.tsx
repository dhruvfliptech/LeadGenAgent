import { MockApproval } from '@/mocks/approvals.mock'
import RiskIndicator from './RiskIndicator'
import { ClockIcon, UserIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { formatRelativeTime } from '@/utils/dateFormat'
import { Link } from 'react-router-dom'

interface ApprovalCardProps {
  approval: MockApproval
}

const typeLabels: Record<string, string> = {
  email_campaign: 'Email Campaign',
  email_response: 'Email Response',
  lead_action: 'Lead Action',
  demo_site_deploy: 'Demo Site',
  video_publish: 'Video',
  workflow_trigger: 'Workflow'
}

export default function ApprovalCard({ approval }: ApprovalCardProps) {
  const isExpiringSoon = approval.expires_at &&
    new Date(approval.expires_at).getTime() - Date.now() < 30 * 60 * 1000 // 30 minutes

  return (
    <Link
      to={`/approvals/${approval.approval_id}`}
      className="block card hover:shadow-md transition-shadow"
    >
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-gray-500 uppercase">
                {typeLabels[approval.type] || approval.type}
              </span>
              {isExpiringSoon && (
                <span className="inline-flex items-center gap-1 text-xs text-red-600">
                  <ExclamationTriangleIcon className="w-3 h-3" />
                  Expiring Soon
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {approval.title}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {approval.description}
            </p>
          </div>
          <div className="ml-4">
            <RiskIndicator level={approval.risk_level} score={approval.risk_score} />
          </div>
        </div>
      </div>

      <div className="px-6 py-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="flex items-center gap-1 text-gray-500 mb-1">
              <UserIcon className="w-4 h-4" />
              <span>Requested by</span>
            </div>
            <div className="font-medium text-gray-900">{approval.requested_by}</div>
          </div>
          <div>
            <div className="flex items-center gap-1 text-gray-500 mb-1">
              <ClockIcon className="w-4 h-4" />
              <span>Requested</span>
            </div>
            <div className="font-medium text-gray-900">
              {formatRelativeTime(approval.requested_at)}
            </div>
          </div>
        </div>

        {approval.lead_name && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">Related to:</span>{' '}
            <span className="text-sm font-medium text-gray-900">{approval.lead_name}</span>
          </div>
        )}

        {approval.risk_factors.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-500 mb-1">Risk Factors:</div>
            <ul className="text-sm text-gray-700 space-y-1">
              {approval.risk_factors.slice(0, 2).map((factor, idx) => (
                <li key={idx} className="flex items-start gap-1">
                  <span className="text-orange-500 mt-0.5">•</span>
                  <span className="flex-1">{factor}</span>
                </li>
              ))}
              {approval.risk_factors.length > 2 && (
                <li className="text-gray-500">
                  +{approval.risk_factors.length - 2} more
                </li>
              )}
            </ul>
          </div>
        )}
      </div>

      {approval.expires_at && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-sm">
          <span className="text-gray-500">Expires:</span>{' '}
          <span className={`font-medium ${isExpiringSoon ? 'text-red-600' : 'text-gray-900'}`}>
            {formatRelativeTime(approval.expires_at)}
          </span>
        </div>
      )}
    </Link>
  )
}
