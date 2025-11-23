import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { mockScrapeJobs, MockScrapeJob, generateProgressUpdate } from '@/mocks/scrapeJobs.mock'
import SourceBadge from '@/components/SourceBadge'
import { formatRelativeTime } from '@/utils/dateFormat'

/**
 * ScrapeJobs - Active jobs monitoring page
 * Shows real-time progress of all scraping jobs
 * URL: /scraper/jobs
 */
export default function ScrapeJobs() {
  const [jobs, setJobs] = useState<MockScrapeJob[]>(mockScrapeJobs)
  const [filter, setFilter] = useState<'all' | 'active' | 'completed' | 'failed'>('all')

  // Simulate WebSocket updates for running jobs
  useEffect(() => {
    const interval = setInterval(() => {
      setJobs(prevJobs =>
        prevJobs.map(job => {
          if (job.status === 'running' && job.progress.percentage < 100) {
            const update = generateProgressUpdate(job)
            return {
              ...job,
              progress: {
                ...update.progress,
                percentage: Math.min((update.progress.current / job.progress.total) * 100, 100)
              },
              leads_found: update.leads_found,
              updated_at: update.updated_at
            }
          }
          return job
        })
      )
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      case 'running':
        return <PlayIcon className="w-5 h-5 text-blue-500 animate-pulse" />
      case 'paused':
        return <PauseIcon className="w-5 h-5 text-yellow-500" />
      case 'cancelled':
        return <StopIcon className="w-5 h-5 text-gray-500" />
      default:
        return <ClockIcon className="w-5 h-5 text-yellow-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/10 text-green-500 border-green-500/20'
      case 'failed':
        return 'bg-red-500/10 text-red-500 border-red-500/20'
      case 'running':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'paused':
        return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
      case 'queued':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
    }
  }

  const filteredJobs = jobs.filter(job => {
    if (filter === 'all') return true
    if (filter === 'active') return ['running', 'queued', 'paused'].includes(job.status)
    if (filter === 'completed') return job.status === 'completed'
    if (filter === 'failed') return job.status === 'failed'
    return true
  })

  const stats = {
    total: jobs.length,
    active: jobs.filter(j => ['running', 'queued'].includes(j.status)).length,
    completed: jobs.filter(j => j.status === 'completed').length,
    failed: jobs.filter(j => j.status === 'failed').length
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-dark-text-primary">Scraping Jobs</h2>
          <p className="text-sm text-dark-text-secondary mt-1">
            Monitor active and recent scraping jobs
          </p>
        </div>
        <Link to="/scraper" className="btn-primary">
          + New Scrape Job
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Total Jobs</div>
          <div className="text-2xl font-bold text-dark-text-primary mt-1">{stats.total}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Active</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{stats.active}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Completed</div>
          <div className="text-2xl font-bold text-green-400 mt-1">{stats.completed}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Failed</div>
          <div className="text-2xl font-bold text-red-400 mt-1">{stats.failed}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {(['all', 'active', 'completed', 'failed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-terminal-500 text-dark-bg'
                : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Jobs Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-dark-border">
            <thead className="bg-dark-border/30">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Job
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Leads Found
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-dark-surface divide-y divide-dark-border">
              {filteredJobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <ClockIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-3" />
                    <p className="text-dark-text-secondary">No jobs found</p>
                  </td>
                </tr>
              ) : (
                filteredJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-dark-border/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1">
                        <code className="text-xs bg-dark-border px-2 py-1 rounded text-dark-text-primary inline-block w-fit">
                          {job.job_id}
                        </code>
                        <SourceBadge source={job.source} size="sm" />
                        {job.config.locations && job.config.locations.length > 0 && (
                          <span className="text-xs text-dark-text-muted">
                            {job.config.locations.length} location{job.config.locations.length !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(job.status)}
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="w-full">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-dark-text-secondary">
                            {job.progress.current} / {job.progress.total}
                          </span>
                          <span className="text-xs font-medium text-dark-text-primary">
                            {job.progress.percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-dark-border rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              job.status === 'running' ? 'bg-blue-500' :
                              job.status === 'completed' ? 'bg-green-500' :
                              job.status === 'failed' ? 'bg-red-500' :
                              'bg-gray-500'
                            }`}
                            style={{ width: `${job.progress.percentage}%` }}
                          />
                        </div>
                        {job.status === 'running' && job.progress.rate_per_minute && (
                          <p className="text-xs text-dark-text-muted mt-1">
                            {job.progress.rate_per_minute}/min • {Math.ceil((job.progress.estimated_time_remaining || 0) / 60)}m remaining
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm">
                        <div className="font-medium text-dark-text-primary">{job.leads_found}</div>
                        {job.leads_enriched > 0 && (
                          <div className="text-xs text-dark-text-muted">
                            {job.leads_enriched} enriched
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      {job.started_at ? formatRelativeTime(job.started_at) : 'Not started'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        to={`/scraper/jobs/${job.job_id}`}
                        className="text-terminal-500 hover:text-terminal-400 transition-colors"
                      >
                        View Details →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Refresh indicator */}
      {stats.active > 0 && (
        <div className="flex items-center justify-center gap-2 text-sm text-dark-text-muted">
          <ArrowPathIcon className="w-4 h-4 animate-spin" />
          <span>Auto-refreshing active jobs...</span>
        </div>
      )}
    </div>
  )
}
