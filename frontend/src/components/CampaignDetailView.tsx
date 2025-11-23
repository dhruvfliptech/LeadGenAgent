import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Campaign, CampaignEmail } from '@/types/campaign'
import CampaignStatusBadge from './CampaignStatusBadge'
import EmailStatusBadge from './EmailStatusBadge'
import {
  PlayIcon,
  PauseIcon,
  XMarkIcon as XIcon,
  EnvelopeIcon as MailIcon,
  UsersIcon,
  ChartBarIcon,
  CursorArrowRaysIcon as CursorClickIcon,
  ArrowUturnLeftIcon as ReplyIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'

interface CampaignDetailViewProps {
  campaign: Campaign
  onPause?: () => void
  onResume?: () => void
  onCancel?: () => void
}

// Mock email recipients data
const generateMockEmails = (campaign: Campaign): CampaignEmail[] => {
  const emails: CampaignEmail[] = []
  const statuses: Array<{ status: any; weight: number }> = [
    { status: 'delivered', weight: 50 },
    { status: 'opened', weight: 30 },
    { status: 'clicked', weight: 10 },
    { status: 'replied', weight: 5 },
    { status: 'bounced', weight: 3 },
    { status: 'queued', weight: 2 },
  ]

  for (let i = 0; i < Math.min(campaign.emails_sent, 20); i++) {
    // Get weighted random status
    const rand = Math.random() * 100
    let cumulative = 0
    let selectedStatus = 'sent'
    for (const { status, weight } of statuses) {
      cumulative += weight
      if (rand < cumulative) {
        selectedStatus = status
        break
      }
    }

    emails.push({
      id: i + 1,
      email_id: `email_${i + 1}`,
      campaign_id: campaign.campaign_id,
      lead_id: 100 + i,
      lead_email: `contact${i + 1}@example.com`,
      lead_name: `Contact ${i + 1}`,
      status: selectedStatus as any,
      sent_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      opens_count: selectedStatus === 'opened' ? Math.floor(Math.random() * 3) + 1 : 0,
      clicks_count: selectedStatus === 'clicked' ? Math.floor(Math.random() * 2) + 1 : 0,
      created_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
    })
  }

  return emails
}

export default function CampaignDetailView({
  campaign: initialCampaign,
  onPause,
  onResume,
  onCancel,
}: CampaignDetailViewProps) {
  const [campaign, setCampaign] = useState(initialCampaign)
  const [emails] = useState<CampaignEmail[]>(generateMockEmails(initialCampaign))

  // Simulate live progress for sending campaigns
  useEffect(() => {
    if (campaign.status !== 'sending') return

    const interval = setInterval(() => {
      setCampaign((prev) => {
        if (prev.emails_sent >= prev.total_recipients) {
          return { ...prev, status: 'completed' }
        }

        const newEmailsSent = Math.min(
          prev.emails_sent + Math.floor(Math.random() * 3) + 1,
          prev.total_recipients
        )
        const newDelivered = Math.floor(newEmailsSent * 0.94)
        const newOpened = Math.floor(newDelivered * 0.4)
        const newClicked = Math.floor(newOpened * 0.15)
        const newReplied = Math.floor(newOpened * 0.05)
        const newBounced = newEmailsSent - newDelivered

        return {
          ...prev,
          emails_sent: newEmailsSent,
          emails_delivered: newDelivered,
          emails_opened: newOpened,
          emails_clicked: newClicked,
          emails_replied: newReplied,
          emails_bounced: newBounced,
          open_rate: newDelivered > 0 ? (newOpened / newDelivered) * 100 : 0,
          click_rate: newOpened > 0 ? (newClicked / newOpened) * 100 : 0,
          reply_rate: newOpened > 0 ? (newReplied / newOpened) * 100 : 0,
          bounce_rate: newEmailsSent > 0 ? (newBounced / newEmailsSent) * 100 : 0,
        }
      })
    }, 3000) // Update every 3 seconds

    return () => clearInterval(interval)
  }, [campaign.status])

  const progress = campaign.total_recipients > 0
    ? Math.round((campaign.emails_sent / campaign.total_recipients) * 100)
    : 0

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
              <CampaignStatusBadge status={campaign.status} />
            </div>
            <p className="text-gray-600">{campaign.subject}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {campaign.status === 'sending' && (
              <button
                onClick={onPause}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <PauseIcon className="h-4 w-4 mr-1" />
                Pause
              </button>
            )}
            {campaign.status === 'paused' && (
              <button
                onClick={onResume}
                className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <PlayIcon className="h-4 w-4 mr-1" />
                Resume
              </button>
            )}
            {(campaign.status === 'sending' || campaign.status === 'paused') && (
              <button
                onClick={onCancel}
                className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
              >
                <XIcon className="h-4 w-4 mr-1" />
                Cancel
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {(campaign.status === 'sending' || campaign.status === 'paused') && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Sending Progress
              </span>
              <span className="text-sm font-medium text-gray-700">
                {campaign.emails_sent} / {campaign.total_recipients} ({progress}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  campaign.status === 'sending' ? 'bg-blue-600' : 'bg-yellow-600'
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <MailIcon className="h-10 w-10 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Delivered</p>
              <p className="text-2xl font-bold text-gray-900">{campaign.emails_delivered}</p>
              <p className="text-xs text-gray-500 mt-1">
                {campaign.emails_sent > 0
                  ? `${((campaign.emails_delivered / campaign.emails_sent) * 100).toFixed(1)}%`
                  : '0%'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UsersIcon className="h-10 w-10 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Open Rate</p>
              <p className="text-2xl font-bold text-gray-900">{campaign.open_rate.toFixed(1)}%</p>
              <p className="text-xs text-gray-500 mt-1">{campaign.emails_opened} opened</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CursorClickIcon className="h-10 w-10 text-indigo-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Click Rate</p>
              <p className="text-2xl font-bold text-gray-900">{campaign.click_rate.toFixed(1)}%</p>
              <p className="text-xs text-gray-500 mt-1">{campaign.emails_clicked} clicked</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ReplyIcon className="h-10 w-10 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Reply Rate</p>
              <p className="text-2xl font-bold text-gray-900">{campaign.reply_rate.toFixed(1)}%</p>
              <p className="text-xs text-gray-500 mt-1">{campaign.emails_replied} replies</p>
            </div>
          </div>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Bounced</p>
              <p className="text-xl font-bold text-orange-600">{campaign.emails_bounced}</p>
            </div>
            <ExclamationCircleIcon className="h-8 w-8 text-orange-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Send Rate</p>
              <p className="text-xl font-bold text-gray-900">{campaign.send_rate_per_hour}/hr</p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Cost</p>
              <p className="text-xl font-bold text-gray-900">${campaign.actual_cost.toFixed(2)}</p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Recipients Table */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recipients</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sent At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Opens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Clicks
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {emails.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No emails sent yet
                  </td>
                </tr>
              ) : (
                emails.map((email) => (
                  <tr key={email.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/leads/${email.lead_id}`}
                        className="block hover:bg-blue-50 rounded p-1 -m-1 transition-colors"
                      >
                        <div className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline">
                          {email.lead_name}
                        </div>
                        <div className="text-sm text-gray-500">{email.lead_email}</div>
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <EmailStatusBadge status={email.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(email.sent_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {email.opens_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {email.clicks_count}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Campaign Details */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Campaign Details</h2>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd className="text-sm text-gray-900 mt-1">{formatDate(campaign.created_at)}</dd>
          </div>
          {campaign.scheduled_at && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Scheduled</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(campaign.scheduled_at)}</dd>
            </div>
          )}
          {campaign.started_at && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Started</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(campaign.started_at)}</dd>
            </div>
          )}
          {campaign.completed_at && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Completed</dt>
              <dd className="text-sm text-gray-900 mt-1">{formatDate(campaign.completed_at)}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500">Tracking</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {campaign.track_opens && 'Opens, '}
              {campaign.track_clicks && 'Clicks'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Follow-up</dt>
            <dd className="text-sm text-gray-900 mt-1">
              {campaign.follow_up_enabled
                ? `Enabled (${campaign.follow_up_delay_days} days)`
                : 'Disabled'}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
