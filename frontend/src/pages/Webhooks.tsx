import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
  QueueListIcon,
  PaperAirplaneIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline'
import {
  mockWebhooks,
  mockWebhookLogs,
  getWebhookStats,
  getWebhookLogs,
  WebhookStatus,
  WebhookEventType
} from '@/mocks/webhooks.mock'
import { formatRelativeTime } from '@/utils/dateFormat'

export default function Webhooks() {
  const [filterStatus, setFilterStatus] = useState<WebhookStatus | 'all'>('all')
  const [filterEvent, setFilterEvent] = useState<WebhookEventType | 'all'>('all')
  const [expandedWebhook, setExpandedWebhook] = useState<string | null>(null)

  const stats = getWebhookStats()

  // Filter webhooks
  const filteredWebhooks = useMemo(() => {
    let filtered = mockWebhooks

    if (filterStatus !== 'all') {
      filtered = filtered.filter(w => w.status === filterStatus)
    }

    if (filterEvent !== 'all') {
      filtered = filtered.filter(w => w.event_type === filterEvent)
    }

    return filtered.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [filterStatus, filterEvent])

  const statusIcon = (status: WebhookStatus) => {
    switch (status) {
      case 'delivered':
        return <CheckCircleIcon className="w-4 h-4 text-green-600" />
      case 'failed':
        return <XCircleIcon className="w-4 h-4 text-red-600" />
      case 'sending':
        return <PaperAirplaneIcon className="w-4 h-4 text-blue-600 animate-pulse" />
      case 'retrying':
        return <ArrowPathIcon className="w-4 h-4 text-yellow-600 animate-spin" />
      case 'queued':
        return <ClockIcon className="w-4 h-4 text-gray-600" />
    }
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

        <div className="flex-1 min-w-0">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <QueueListIcon className="w-8 h-8 text-gray-500" />
            Webhook Queue
          </h1>
          <p className="mt-1 text-gray-600">
            Monitor webhook delivery status and retry failed deliveries
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Queued</div>
          <div className="text-2xl font-bold text-gray-900">
            {stats.queued}
          </div>
        </div>

        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Sending</div>
          <div className="text-2xl font-bold text-blue-600">
            {stats.sending}
          </div>
        </div>

        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Delivered</div>
          <div className="text-2xl font-bold text-green-600">
            {stats.delivered}
          </div>
        </div>

        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Failed</div>
          <div className="text-2xl font-bold text-red-600">
            {stats.failed}
          </div>
        </div>

        <div className="card p-5">
          <div className="text-sm text-gray-500 mb-1">Success Rate</div>
          <div className="text-2xl font-bold text-purple-600">
            {stats.success_rate.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <label className="font-medium text-gray-700">Status:</label>
            <select
              className="form-input py-1 text-sm"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
            >
              <option value="all">All Statuses</option>
              <option value="queued">Queued</option>
              <option value="sending">Sending</option>
              <option value="delivered">Delivered</option>
              <option value="failed">Failed</option>
              <option value="retrying">Retrying</option>
            </select>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <label className="font-medium text-gray-700">Event Type:</label>
            <select
              className="form-input py-1 text-sm"
              value={filterEvent}
              onChange={(e) => setFilterEvent(e.target.value as any)}
            >
              <option value="all">All Events</option>
              <option value="lead.created">Lead Created</option>
              <option value="lead.updated">Lead Updated</option>
              <option value="lead.enriched">Lead Enriched</option>
              <option value="email.received">Email Received</option>
              <option value="email.sent">Email Sent</option>
              <option value="demo_site.generated">Demo Site Generated</option>
              <option value="video.completed">Video Completed</option>
              <option value="campaign.completed">Campaign Completed</option>
            </select>
          </div>
          <div className="ml-auto text-sm text-gray-500">
            Showing {filteredWebhooks.length} of {stats.total}
          </div>
        </div>
      </div>

      {/* Webhooks Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Webhook ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Event Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attempts
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredWebhooks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No webhooks found
                  </td>
                </tr>
              ) : (
                filteredWebhooks.map((webhook) => (
                  <>
                    <tr key={webhook.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-mono text-gray-900">
                          {webhook.webhook_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{webhook.event_type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {statusIcon(webhook.status)}
                          <span
                            className={`text-sm font-medium capitalize ${
                              webhook.status === 'delivered' ? 'text-green-600' :
                              webhook.status === 'failed' ? 'text-red-600' :
                              webhook.status === 'sending' ? 'text-blue-600' :
                              webhook.status === 'retrying' ? 'text-yellow-600' :
                              'text-gray-600'
                            }`}
                          >
                            {webhook.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {webhook.attempts}/{webhook.max_attempts}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {webhook.response_time_ms ? `${webhook.response_time_ms}ms` : '—'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatRelativeTime(webhook.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => setExpandedWebhook(
                            expandedWebhook === webhook.webhook_id ? null : webhook.webhook_id
                          )}
                          className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
                        >
                          {expandedWebhook === webhook.webhook_id ? (
                            <>
                              <ChevronUpIcon className="w-4 h-4" />
                              Hide
                            </>
                          ) : (
                            <>
                              <ChevronDownIcon className="w-4 h-4" />
                              View
                            </>
                          )}
                        </button>
                      </td>
                    </tr>
                    {expandedWebhook === webhook.webhook_id && (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-4">
                            {/* Webhook Details */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Target URL</div>
                                <div className="text-sm text-gray-900 font-mono break-all">
                                  {webhook.target_url}
                                </div>
                              </div>
                              {webhook.workflow_id && (
                                <div>
                                  <div className="text-xs font-medium text-gray-500 mb-1">Workflow</div>
                                  <Link
                                    to={`/workflows/${webhook.workflow_id}`}
                                    className="text-sm text-blue-600 hover:text-blue-700"
                                  >
                                    {webhook.workflow_id}
                                  </Link>
                                </div>
                              )}
                              {webhook.next_retry_at && (
                                <div>
                                  <div className="text-xs font-medium text-gray-500 mb-1">Next Retry</div>
                                  <div className="text-sm text-gray-900">
                                    {formatRelativeTime(webhook.next_retry_at)}
                                  </div>
                                </div>
                              )}
                              {webhook.error_message && (
                                <div>
                                  <div className="text-xs font-medium text-red-600 mb-1">Error</div>
                                  <div className="text-sm text-red-900">
                                    {webhook.error_message}
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Payload Preview */}
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-2">Payload</div>
                              <pre className="bg-white p-3 rounded border border-gray-200 text-xs overflow-x-auto max-h-40">
                                {JSON.stringify(webhook.payload, null, 2)}
                              </pre>
                            </div>

                            {/* Delivery Logs */}
                            {(() => {
                              const logs = getWebhookLogs(webhook.webhook_id)
                              if (logs.length === 0) return null

                              return (
                                <div>
                                  <div className="text-xs font-medium text-gray-500 mb-2">
                                    Delivery Attempts ({logs.length})
                                  </div>
                                  <div className="space-y-2">
                                    {logs.map((log) => (
                                      <div
                                        key={log.id}
                                        className={`p-3 rounded border ${
                                          log.success
                                            ? 'bg-green-50 border-green-200'
                                            : 'bg-red-50 border-red-200'
                                        }`}
                                      >
                                        <div className="flex items-start justify-between mb-2">
                                          <div className="flex items-center gap-2">
                                            {log.success ? (
                                              <CheckCircleIcon className="w-4 h-4 text-green-600" />
                                            ) : (
                                              <XCircleIcon className="w-4 h-4 text-red-600" />
                                            )}
                                            <span className="text-sm font-medium">
                                              Attempt #{log.attempt_number}
                                            </span>
                                          </div>
                                          <div className="text-xs text-gray-500">
                                            {formatRelativeTime(log.timestamp)}
                                          </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 text-xs">
                                          <div>
                                            <span className="text-gray-600">Status Code:</span>{' '}
                                            <span className="font-medium">
                                              {log.response_status_code || 'N/A'}
                                            </span>
                                          </div>
                                          <div>
                                            <span className="text-gray-600">Response Time:</span>{' '}
                                            <span className="font-medium">
                                              {log.response_time_ms ? `${log.response_time_ms}ms` : 'N/A'}
                                            </span>
                                          </div>
                                        </div>
                                        {log.error_message && (
                                          <div className="mt-2 text-xs text-red-900">
                                            {log.error_message}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )
                            })()}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Event Type Stats */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Events by Type</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats.by_event_type).map(([event, count]) => (
              <div key={event} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{count}</div>
                <div className="text-xs text-gray-600 mt-1">{event}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Response Time</h3>
          <div className="text-4xl font-bold text-blue-600">
            {stats.avg_response_time.toFixed(0)}ms
          </div>
        </div>
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Retry Rate</h3>
          <div className="text-4xl font-bold text-yellow-600">
            {((stats.retrying / stats.total) * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    </div>
  )
}
