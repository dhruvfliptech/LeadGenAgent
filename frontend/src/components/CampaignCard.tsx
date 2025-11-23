import { Link } from 'react-router-dom'
import { Campaign } from '@/types/campaign'
import CampaignStatusBadge from './CampaignStatusBadge'
import { EnvelopeIcon as MailIcon, UsersIcon, ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline'

interface CampaignCardProps {
  campaign: Campaign
}

export default function CampaignCard({ campaign }: CampaignCardProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Not scheduled'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getProgressPercentage = () => {
    if (campaign.total_recipients === 0) return 0
    return Math.round((campaign.emails_sent / campaign.total_recipients) * 100)
  }

  const progress = getProgressPercentage()

  return (
    <Link
      to={`/campaigns/${campaign.id}`}
      className="block bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {campaign.name}
          </h3>
          <p className="text-sm text-gray-500 mt-1 truncate">
            {campaign.subject}
          </p>
        </div>
        <CampaignStatusBadge status={campaign.status} className="ml-3" />
      </div>

      {/* Progress Bar (for active campaigns) */}
      {(campaign.status === 'sending' || campaign.status === 'paused') && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-gray-600">Progress</span>
            <span className="text-xs font-medium text-gray-600">
              {campaign.emails_sent} / {campaign.total_recipients}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex items-center space-x-2">
          <UsersIcon className="h-5 w-5 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Recipients</p>
            <p className="text-sm font-semibold text-gray-900">
              {campaign.total_recipients}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <MailIcon className="h-5 w-5 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Sent</p>
            <p className="text-sm font-semibold text-gray-900">
              {campaign.emails_sent}
            </p>
          </div>
        </div>

        {campaign.emails_sent > 0 && (
          <>
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Open Rate</p>
                <p className="text-sm font-semibold text-gray-900">
                  {campaign.open_rate.toFixed(1)}%
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <ChartBarIcon className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Reply Rate</p>
                <p className="text-sm font-semibold text-gray-900">
                  {campaign.reply_rate.toFixed(1)}%
                </p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex items-center text-xs text-gray-500">
          <ClockIcon className="h-4 w-4 mr-1" />
          {campaign.status === 'scheduled' && `Starts ${formatDate(campaign.scheduled_at)}`}
          {campaign.status === 'sending' && `Started ${formatDate(campaign.started_at)}`}
          {campaign.status === 'completed' && `Completed ${formatDate(campaign.completed_at)}`}
          {campaign.status === 'draft' && `Created ${formatDate(campaign.created_at)}`}
          {campaign.status === 'paused' && `Paused ${formatDate(campaign.paused_at)}`}
        </div>
        <span className="text-xs font-medium text-blue-600 hover:text-blue-700">
          View Details →
        </span>
      </div>
    </Link>
  )
}
