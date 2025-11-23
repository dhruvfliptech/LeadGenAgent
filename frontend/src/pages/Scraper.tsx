// No local state; builder handles inputs
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  PlayIcon,
  StopIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { api } from '@/services/api'
import ScrapeBuilder from '@/components/ScrapeBuilder'
import { formatRelativeTime } from '@/utils/dateFormat'

interface ScrapeJob {
  job_id: string
  status: string
  progress?: number
  location_ids: number[]
  categories?: string[]
  keywords?: string[]
  max_pages: number
  priority: string
  created_at: string
  started_at?: string
  completed_at?: string
}

export default function Scraper() {
  // State moved to ScrapeBuilder
  
  const queryClient = useQueryClient()

  // Locations loaded inside builder

  const { data: jobs } = useQuery<ScrapeJob[]>({
    queryKey: ['scrape-jobs'],
    queryFn: () => api.get('/scraper/jobs').then(res => res.data),
    refetchInterval: 5000, // Poll every 5 seconds
  })

  const { data: queueStatus } = useQuery({
    queryKey: ['queue-status'],
    queryFn: () => api.get('/scraper/queue/status').then(res => res.data),
    refetchInterval: 5000,
  })

  const createJobMutation = useMutation({
    mutationFn: (data: any) => api.post('/scraper/jobs', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrape-jobs'] })
      queryClient.invalidateQueries({ queryKey: ['queue-status'] })
      toast.success('Scraping job created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create scraping job')
    },
  })

  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => api.delete(`/scraper/jobs/${jobId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrape-jobs'] })
      toast.success('Job cancelled successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel job')
    },
  })

  const handleBuilderSubmit = (payload: any) => {
    if (!payload.location_ids?.length) {
      toast.error('Please select at least one location')
      return
    }
    createJobMutation.mutate(payload)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />
      case 'running':
        return <PlayIcon className="w-5 h-5 text-blue-500" />
      case 'cancelled':
        return <StopIcon className="w-5 h-5 text-gray-500" />
      default:
        return <ClockIcon className="w-5 h-5 text-yellow-500" />
    }
  }

  // Categories handled via /scraper/categories in builder


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Scraper
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Create and manage Craigslist scraping jobs
          </p>
        </div>
      </div>

      {/* Queue Status */}
      {queueStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="text-sm font-medium text-dark-text-secondary">High Priority</div>
            <div className="text-2xl font-bold text-red-400">{queueStatus?.queues?.high ?? 0}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm font-medium text-dark-text-secondary">Normal Priority</div>
            <div className="text-2xl font-bold text-blue-400">{queueStatus?.queues?.normal ?? 0}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm font-medium text-dark-text-secondary">Low Priority</div>
            <div className="text-2xl font-bold text-dark-text-secondary">{queueStatus?.queues?.low ?? 0}</div>
          </div>
          <div className="card p-4">
            <div className="text-sm font-medium text-dark-text-secondary">Active Jobs</div>
            <div className="text-2xl font-bold text-green-400">{queueStatus?.active_jobs ?? 0}</div>
          </div>
        </div>
      )}

      {/* Scrape Builder */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Create New Scraping Job</h3>
        <ScrapeBuilder onSubmit={handleBuilderSubmit} />
      </div>

      {/* Job History */}
      <div className="card">
        <div className="px-6 py-4 border-b border-dark-border">
          <h3 className="text-lg font-medium text-dark-text-primary">Recent Jobs</h3>
        </div>
        <div className="overflow-x-auto">
          {jobs && jobs.length > 0 ? (
            <table className="min-w-full divide-y divide-dark-border">
              <thead className="bg-dark-border/30">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Locations
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-dark-surface divide-y divide-dark-border">
                {jobs.map((job) => (
                  <tr key={job.job_id} className="hover:bg-dark-border/30">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-xs bg-dark-border px-2 py-1 rounded text-dark-text-primary">
                        {job.job_id}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(job.status)}
                        <span className="ml-2 text-sm capitalize text-dark-text-primary">{job.status}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-dark-text-primary">
                        {Array.isArray((job as any)?.location_ids)
                          ? `${(job as any).location_ids.length} location${(job as any).location_ids.length !== 1 ? 's' : ''}`
                          : '—'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {job.progress !== undefined ? (
                        <div className="flex items-center">
                          <div className="w-16 bg-dark-border rounded-full h-2 mr-2">
                            <div
                              className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${job.progress}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-dark-text-secondary">{job.progress}%</span>
                        </div>
                      ) : (
                        <span className="text-sm text-dark-text-muted">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      {formatRelativeTime(job.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {(job.status === 'queued' || job.status === 'running') && (
                        <button
                          onClick={() => cancelJobMutation.mutate(job.job_id)}
                          disabled={cancelJobMutation.isPending}
                          className="text-red-400 hover:text-red-300"
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <ClockIcon className="mx-auto h-12 w-12 text-dark-text-muted mb-4" />
              <h3 className="text-lg font-medium text-dark-text-primary mb-2">No scraping jobs yet</h3>
              <p className="text-dark-text-secondary">Create your first scraping job using the form above to start collecting leads from Craigslist.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}