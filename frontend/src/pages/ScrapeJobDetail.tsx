import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  PauseIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'
import { mockScrapeJobs, MockScrapeJob, generateProgressUpdate, getLeadsBySource } from '@/mocks/scrapeJobs.mock'
import { mockLeads } from '@/mocks/leads.mock'
import SourceBadge from '@/components/SourceBadge'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

/**
 * ScrapeJobDetail - Detailed view of a single scraping job
 * Shows live progress, activity log, and leads preview
 * URL: /scraper/jobs/:job_id
 */
export default function ScrapeJobDetail() {
  const { job_id } = useParams<{ job_id: string }>()
  const navigate = useNavigate()
  const [job, setJob] = useState<MockScrapeJob | null>(
    mockScrapeJobs.find(j => j.job_id === job_id) || null
  )
  const [activityLog, setActivityLog] = useState<Array<{
    timestamp: string
    type: 'success' | 'warning' | 'info' | 'error'
    message: string
  }>>([
    { timestamp: new Date().toISOString(), type: 'success', message: `Started job ${job_id}` },
    { timestamp: new Date().toISOString(), type: 'info', message: 'Connecting to data source...' },
    { timestamp: new Date().toISOString(), type: 'success', message: 'Connection established' }
  ])

  // Simulate WebSocket updates
  useEffect(() => {
    if (!job) return

    const interval = setInterval(() => {
      if (job.status === 'running' && job.progress.percentage < 100) {
        const update = generateProgressUpdate(job)

        setJob(prev => {
          if (!prev) return null
          return {
            ...prev,
            progress: {
              ...update.progress,
              percentage: Math.min((update.progress.current / prev.progress.total) * 100, 100)
            },
            leads_found: update.leads_found,
            updated_at: update.updated_at
          }
        })

        // Add random activity log entries
        if (Math.random() > 0.7) {
          const messages = [
            { type: 'success' as const, message: `Found ${Math.floor(Math.random() * 5) + 1} new listings` },
            { type: 'success' as const, message: 'Lead created successfully' },
            { type: 'info' as const, message: 'Enrichment queued' },
            { type: 'success' as const, message: 'Email found via Hunter.io' },
            { type: 'warning' as const, message: 'Duplicate listing skipped' }
          ]
          const msg = messages[Math.floor(Math.random() * messages.length)]
          setActivityLog(prev => [
            { timestamp: new Date().toISOString(), ...msg },
            ...prev
          ].slice(0, 50))
        }
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [job])

  if (!job) {
    return (
      <div className="space-y-6">
        <Link to="/scraper/jobs" className="inline-flex items-center gap-2 text-terminal-500 hover:text-terminal-400">
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Jobs
        </Link>
        <div className="card p-12 text-center">
          <XCircleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-dark-text-primary mb-2">Job Not Found</h3>
          <p className="text-dark-text-secondary">Job ID: {job_id}</p>
        </div>
      </div>
    )
  }

  const handlePause = () => {
    setJob({ ...job, status: 'paused', paused_at: new Date().toISOString() })
    toast.success('Job paused')
    setActivityLog(prev => [{
      timestamp: new Date().toISOString(),
      type: 'warning',
      message: 'Job paused by user'
    }, ...prev])
  }

  const handleResume = () => {
    setJob({ ...job, status: 'running', paused_at: undefined })
    toast.success('Job resumed')
    setActivityLog(prev => [{
      timestamp: new Date().toISOString(),
      type: 'info',
      message: 'Job resumed'
    }, ...prev])
  }

  const handleCancel = () => {
    setJob({ ...job, status: 'cancelled' })
    toast.success('Job cancelled')
    setActivityLog(prev => [{
      timestamp: new Date().toISOString(),
      type: 'error',
      message: 'Job cancelled by user'
    }, ...prev])
  }

  const getStatusBadge = () => {
    const statusConfig = {
      running: { color: 'bg-blue-500/10 text-blue-500 border-blue-500/20', icon: PlayIcon, pulse: true },
      paused: { color: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20', icon: PauseIcon, pulse: false },
      completed: { color: 'bg-green-500/10 text-green-500 border-green-500/20', icon: CheckCircleIcon, pulse: false },
      failed: { color: 'bg-red-500/10 text-red-500 border-red-500/20', icon: XCircleIcon, pulse: false },
      cancelled: { color: 'bg-gray-500/10 text-gray-500 border-gray-500/20', icon: StopIcon, pulse: false },
      queued: { color: 'bg-purple-500/10 text-purple-500 border-purple-500/20', icon: InformationCircleIcon, pulse: false }
    }

    const config = statusConfig[job.status] || statusConfig.queued
    const Icon = config.icon

    return (
      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border ${config.color} ${config.pulse ? 'animate-pulse' : ''}`}>
        <Icon className="w-4 h-4" />
        {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
      </span>
    )
  }

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />
      case 'warning':
        return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
      case 'error':
        return <XCircleIcon className="w-4 h-4 text-red-500" />
      default:
        return <InformationCircleIcon className="w-4 h-4 text-blue-500" />
    }
  }

  // Get sample leads for this source
  const sampleLeads = mockLeads.filter(lead => lead.source === job.source).slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link to="/scraper/jobs" className="inline-flex items-center gap-2 text-terminal-500 hover:text-terminal-400 mb-4">
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Jobs
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold text-dark-text-primary">Job Details</h2>
              {getStatusBadge()}
            </div>
            <code className="text-sm bg-dark-border px-3 py-1 rounded text-dark-text-secondary">
              {job.job_id}
            </code>
          </div>

          <div className="flex gap-2">
            {job.status === 'running' && (
              <button onClick={handlePause} className="btn-secondary">
                <PauseIcon className="w-4 h-4" />
                Pause
              </button>
            )}
            {job.status === 'paused' && (
              <button onClick={handleResume} className="btn-primary">
                <PlayIcon className="w-4 h-4" />
                Resume
              </button>
            )}
            {['running', 'paused', 'queued'].includes(job.status) && (
              <button onClick={handleCancel} className="btn-secondary text-red-500 hover:text-red-400">
                <StopIcon className="w-4 h-4" />
                Cancel
              </button>
            )}
            {job.status === 'completed' && (
              <button className="btn-primary">
                <ArrowDownTrayIcon className="w-4 h-4" />
                Export
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Progress Overview</h3>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-dark-text-secondary">Overall Progress</span>
            <span className="text-lg font-bold text-dark-text-primary">{job.progress.percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-dark-border rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all duration-500 ${
                job.status === 'running' ? 'bg-gradient-to-r from-blue-500 to-terminal-500' :
                job.status === 'completed' ? 'bg-green-500' :
                job.status === 'failed' ? 'bg-red-500' :
                'bg-gray-500'
              }`}
              style={{ width: `${job.progress.percentage}%` }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-dark-border/30 rounded-lg p-4">
            <div className="text-xs text-dark-text-muted mb-1">Items Scraped</div>
            <div className="text-2xl font-bold text-dark-text-primary">
              {job.progress.current} <span className="text-sm text-dark-text-muted">/ {job.progress.total}</span>
            </div>
          </div>

          <div className="bg-dark-border/30 rounded-lg p-4">
            <div className="text-xs text-dark-text-muted mb-1">Leads Found</div>
            <div className="text-2xl font-bold text-green-400">{job.leads_found}</div>
          </div>

          <div className="bg-dark-border/30 rounded-lg p-4">
            <div className="text-xs text-dark-text-muted mb-1">Enriched</div>
            <div className="text-2xl font-bold text-blue-400">{job.leads_enriched}</div>
          </div>

          <div className="bg-dark-border/30 rounded-lg p-4">
            <div className="text-xs text-dark-text-muted mb-1">Errors</div>
            <div className="text-2xl font-bold text-red-400">{job.errors_count}</div>
          </div>
        </div>

        {job.status === 'running' && job.progress.rate_per_minute && (
          <div className="mt-4 pt-4 border-t border-dark-border">
            <div className="flex items-center justify-between text-sm">
              <span className="text-dark-text-secondary">Processing Rate:</span>
              <span className="text-dark-text-primary font-medium">{job.progress.rate_per_minute} items/min</span>
            </div>
            {job.progress.estimated_time_remaining && (
              <div className="flex items-center justify-between text-sm mt-1">
                <span className="text-dark-text-secondary">Estimated Time Remaining:</span>
                <span className="text-dark-text-primary font-medium">
                  {Math.ceil(job.progress.estimated_time_remaining / 60)} minutes
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Configuration & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-dark-text-primary mb-4">Configuration</h3>

          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Source:</dt>
              <dd><SourceBadge source={job.source} size="sm" /></dd>
            </div>

            {job.config.locations && job.config.locations.length > 0 && (
              <div className="flex justify-between">
                <dt className="text-dark-text-secondary">Locations:</dt>
                <dd className="text-dark-text-primary text-right">
                  {job.config.locations.slice(0, 2).join(', ')}
                  {job.config.locations.length > 2 && ` +${job.config.locations.length - 2} more`}
                </dd>
              </div>
            )}

            {job.config.categories && job.config.categories.length > 0 && (
              <div className="flex justify-between">
                <dt className="text-dark-text-secondary">Categories:</dt>
                <dd className="text-dark-text-primary text-right">{job.config.categories.join(', ')}</dd>
              </div>
            )}

            {job.config.keywords && job.config.keywords.length > 0 && (
              <div className="flex justify-between">
                <dt className="text-dark-text-secondary">Keywords:</dt>
                <dd className="text-dark-text-primary text-right">{job.config.keywords.join(', ')}</dd>
              </div>
            )}

            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Max Results:</dt>
              <dd className="text-dark-text-primary">{job.config.max_results}</dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Enrichment:</dt>
              <dd className="text-dark-text-primary">{job.config.enable_enrichment ? 'Enabled' : 'Disabled'}</dd>
            </div>

            <div className="flex justify-between pt-3 border-t border-dark-border">
              <dt className="text-dark-text-secondary">Created:</dt>
              <dd className="text-dark-text-primary">{formatRelativeTime(job.created_at)}</dd>
            </div>

            {job.started_at && (
              <div className="flex justify-between">
                <dt className="text-dark-text-secondary">Started:</dt>
                <dd className="text-dark-text-primary">{formatRelativeTime(job.started_at)}</dd>
              </div>
            )}

            {job.completed_at && (
              <div className="flex justify-between">
                <dt className="text-dark-text-secondary">Completed:</dt>
                <dd className="text-dark-text-primary">{formatRelativeTime(job.completed_at)}</dd>
              </div>
            )}

            <div className="flex justify-between pt-3 border-t border-dark-border">
              <dt className="text-dark-text-secondary">API Calls:</dt>
              <dd className="text-dark-text-primary">{job.api_calls_made}</dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Estimated Cost:</dt>
              <dd className="text-dark-text-primary font-medium">${job.estimated_cost.toFixed(2)}</dd>
            </div>
          </dl>
        </div>

        {/* Activity Log */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-dark-text-primary mb-4">Activity Log</h3>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {activityLog.map((entry, index) => (
              <div key={index} className="flex items-start gap-2 text-sm">
                {getActivityIcon(entry.type)}
                <div className="flex-1">
                  <span className="text-dark-text-primary">{entry.message}</span>
                  <div className="text-xs text-dark-text-muted">{formatRelativeTime(entry.timestamp)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Leads Preview */}
      <div className="card">
        <div className="px-6 py-4 border-b border-dark-border flex items-center justify-between">
          <h3 className="text-lg font-medium text-dark-text-primary">Leads Preview</h3>
          <Link to="/leads" className="text-terminal-500 hover:text-terminal-400 text-sm">
            View All Leads →
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-dark-border">
            <thead className="bg-dark-border/30">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase">Contact</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {sampleLeads.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-dark-text-muted">
                    No leads found yet...
                  </td>
                </tr>
              ) : (
                sampleLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-dark-border/30">
                    <td className="px-6 py-4 text-sm text-dark-text-primary">{lead.title}</td>
                    <td className="px-6 py-4 text-sm text-dark-text-primary">{lead.company_name}</td>
                    <td className="px-6 py-4 text-sm text-dark-text-secondary">{lead.location}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {lead.email && <span className="text-xs text-green-500">📧</span>}
                        {lead.phone && <span className="text-xs text-blue-500">📞</span>}
                        {!lead.email && !lead.phone && <span className="text-xs text-dark-text-muted">-</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        lead.enrichment_status === 'enriched' ? 'bg-green-500/10 text-green-500' :
                        lead.enrichment_status === 'enriching' ? 'bg-blue-500/10 text-blue-500' :
                        lead.enrichment_status === 'failed' ? 'bg-red-500/10 text-red-500' :
                        'bg-yellow-500/10 text-yellow-500'
                      }`}>
                        {lead.enrichment_status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
