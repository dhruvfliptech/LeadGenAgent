import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  DocumentTextIcon,
  MapPinIcon,
  CheckCircleIcon,
  PhoneIcon,
  SparklesIcon,
  TrophyIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'
import { api } from '@/services/api'
import { aiMvpApi } from '@/services/phase3Api'
import AICostTracker from '@/components/AICostTracker'
// @ts-ignore - SourceBadge exported for external use
import SourceBadge from '@/components/SourceBadge'
import { getSourceConfig } from '@/components/SourceSelector'
import { LeadSource } from '@/types/lead'

interface LeadStats {
  total_leads: number
  processed_leads: number
  contacted_leads: number
  status_breakdown: Record<string, number>
  processing_rate: number
  contact_rate: number
  by_source?: Record<LeadSource, {
    count: number
    response_rate?: number
    conversion_rate?: number
  }>
}

function StatCard({ title, value, icon: Icon, subtitle }: {
  title: string
  value: string | number
  icon: any
  subtitle?: string
}) {
  return (
    <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-6 w-6 text-terminal-500" />
        </div>
        <div className="ml-4">
          <div className="text-2xl font-bold text-dark-text-primary">{value}</div>
          <div className="text-sm font-medium text-dark-text-secondary">{title}</div>
          {subtitle && (
            <div className="text-xs text-dark-text-muted mt-1">{subtitle}</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery<LeadStats>({
    queryKey: ['lead-stats'],
    queryFn: () => api.get('/leads/stats/summary').then(res => res.data),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => api.get('/locations?active_only=true').then(res => res.data),
  })

  const { data: aiPerformance } = useQuery({
    queryKey: ['ai-performance'],
    queryFn: () => aiMvpApi.getPerformance(1).then(res => res.data),
    refetchInterval: 60000, // Refresh every minute
  })

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading dashboard data</div>
        <button 
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Dashboard
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Overview of your Craigslist lead generation activity
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-dark-surface border border-dark-border rounded-lg p-6 animate-pulse">
              <div className="flex items-center">
                <div className="h-6 w-6 bg-dark-border rounded"></div>
                <div className="ml-4 flex-1">
                  <div className="h-8 bg-dark-border rounded mb-2"></div>
                  <div className="h-4 bg-dark-border rounded w-2/3"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Leads"
            value={stats.total_leads}
            icon={DocumentTextIcon}
          />
          <StatCard
            title="Processed Leads"
            value={stats.processed_leads}
            icon={CheckCircleIcon}
            subtitle={`${stats.processing_rate}% processed`}
          />
          <StatCard
            title="Contacted Leads"
            value={stats.contacted_leads}
            icon={PhoneIcon}
            subtitle={`${stats.contact_rate}% contacted`}
          />
          <StatCard
            title="Active Locations"
            value={locations?.length || 0}
            icon={MapPinIcon}
          />
        </div>
      ) : null}

      {/* Revenue & ROI Section */}
      <div className="card">
        <div className="px-6 py-4 border-b border-dark-border">
          <div className="flex items-center gap-2">
            <CurrencyDollarIcon className="h-5 w-5 text-green-500" />
            <h3 className="text-lg font-medium text-dark-text-primary">
              Revenue & ROI Analysis
            </h3>
          </div>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Track revenue generated from your lead generation campaigns
          </p>
        </div>

        {/* Revenue Stats Grid */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            {/* Total Revenue */}
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <CurrencyDollarIcon className="h-5 w-5 text-green-500" />
                <span className="text-sm font-medium text-green-400">Total Revenue</span>
              </div>
              <div className="text-2xl font-bold text-green-400">$12,450</div>
              <div className="text-xs text-dark-text-muted mt-1">From 23 closed deals</div>
            </div>

            {/* Average Deal Value */}
            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <ChartBarIcon className="h-5 w-5 text-blue-500" />
                <span className="text-sm font-medium text-blue-400">Avg Deal Value</span>
              </div>
              <div className="text-2xl font-bold text-blue-400">$541</div>
              <div className="text-xs text-dark-text-muted mt-1">Per closed deal</div>
            </div>

            {/* Conversion Rate */}
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowTrendingUpIcon className="h-5 w-5 text-purple-500" />
                <span className="text-sm font-medium text-purple-400">Conversion Rate</span>
              </div>
              <div className="text-2xl font-bold text-purple-400">8.5%</div>
              <div className="text-xs text-dark-text-muted mt-1">Leads to customers</div>
            </div>

            {/* ROI */}
            <div className="bg-terminal-500/10 border border-terminal-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrophyIcon className="h-5 w-5 text-terminal-500" />
                <span className="text-sm font-medium text-terminal-400">ROI</span>
              </div>
              <div className="text-2xl font-bold text-terminal-400">385%</div>
              <div className="text-xs text-dark-text-muted mt-1">Return on investment</div>
            </div>
          </div>

          {/* Revenue by Source */}
          <div className="border-t border-dark-border pt-6">
            <h4 className="text-sm font-medium text-dark-text-primary mb-4">Revenue by Lead Source</h4>
            <div className="space-y-4">
              {[
                { source: 'Craigslist', revenue: 6250, deals: 12, color: 'bg-orange-500' },
                { source: 'Google Maps', revenue: 3850, deals: 7, color: 'bg-blue-500' },
                { source: 'LinkedIn', revenue: 2350, deals: 4, color: 'bg-indigo-500' },
              ].map((item) => (
                <div key={item.source} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                      <span className="text-sm font-medium text-dark-text-primary">
                        {item.source}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-green-400">
                        ${item.revenue.toLocaleString()}
                      </div>
                      <div className="text-xs text-dark-text-muted">
                        {item.deals} deals
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-dark-border rounded-full h-2">
                    <div
                      className={`${item.color} h-2 rounded-full transition-all duration-500`}
                      style={{ width: `${(item.revenue / 12450 * 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cost Breakdown */}
          <div className="border-t border-dark-border pt-6 mt-6">
            <h4 className="text-sm font-medium text-dark-text-primary mb-4">Cost Breakdown</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-dark-border/30 rounded-lg p-4">
                <div className="text-xs text-dark-text-secondary mb-1">AI Processing Costs</div>
                <div className="text-lg font-bold text-dark-text-primary">$284.50</div>
                <div className="text-xs text-red-400 mt-1">↑ 12% from last month</div>
              </div>
              <div className="bg-dark-border/30 rounded-lg p-4">
                <div className="text-xs text-dark-text-secondary mb-1">Scraping & Enrichment</div>
                <div className="text-lg font-bold text-dark-text-primary">$156.00</div>
                <div className="text-xs text-green-400 mt-1">↓ 8% from last month</div>
              </div>
              <div className="bg-dark-border/30 rounded-lg p-4">
                <div className="text-xs text-dark-text-secondary mb-1">Total Operating Cost</div>
                <div className="text-lg font-bold text-dark-text-primary">$440.50</div>
                <div className="text-xs text-dark-text-muted mt-1">3.5% of revenue</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Cost Tracking */}
      <AICostTracker />

      {/* Source Statistics & Status Breakdown */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Leads by Source Chart */}
          {stats.by_source && Object.keys(stats.by_source).length > 0 && (
            <div className="card p-6">
              <h3 className="text-lg font-medium text-dark-text-primary mb-4">
                Leads by Source
              </h3>
              <div className="space-y-3">
                {Object.entries(stats.by_source)
                  .sort(([, a], [, b]) => b.count - a.count)
                  .map(([source, data]) => {
                    const config = getSourceConfig(source as LeadSource)
                    const percentage = stats.total_leads > 0 ? (data.count / stats.total_leads * 100) : 0
                    return (
                      <div key={source} className="space-y-1">
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{config.icon}</span>
                            <span className="text-sm font-medium text-dark-text-primary">
                              {config.name}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-dark-text-primary">
                            {data.count}
                          </span>
                        </div>
                        <div className="w-full bg-dark-border rounded-full h-2">
                          <div
                            className={`source-stat-bar-${source} h-2 rounded-full transition-all duration-500`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                        {data.response_rate !== undefined && (
                          <div className="text-xs text-dark-text-muted">
                            Response rate: {(data.response_rate * 100).toFixed(1)}%
                          </div>
                        )}
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {/* Lead Status Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-dark-text-primary mb-4">
              Lead Status Breakdown
            </h3>
            <div className="space-y-3">
              {Object.entries(stats.status_breakdown).map(([status, count]) => (
                <div key={status} className="flex justify-between items-center">
                  <span className="text-sm font-medium text-dark-text-secondary capitalize">
                    {status.replace('_', ' ')}
                  </span>
                  <div className="flex items-center">
                    <span className="text-sm text-dark-text-primary mr-3">{count}</span>
                    <div className="w-16 bg-dark-border rounded-full h-2">
                      <div
                        className="bg-terminal-500 h-2 rounded-full transition-all duration-500"
                        style={{
                          width: `${stats.total_leads > 0 ? (count / stats.total_leads * 100) : 0}%`
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Best Performing Source & Quick Actions */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Best Performing Source */}
          {stats.by_source && Object.keys(stats.by_source).length > 0 && (
            <div className="card p-6 bg-gradient-to-br from-terminal-900/20 to-dark-surface border-terminal-500/30">
              <div className="flex items-start gap-3">
                <TrophyIcon className="h-8 w-8 text-terminal-500" />
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-dark-text-primary mb-2">
                    Best Performing Source
                  </h3>
                  {(() => {
                    const bestSource = Object.entries(stats.by_source)
                      .sort(([, a], [, b]) => {
                        const scoreA = (a.response_rate || 0) * 0.5 + (a.conversion_rate || 0) * 0.5
                        const scoreB = (b.response_rate || 0) * 0.5 + (b.conversion_rate || 0) * 0.5
                        return scoreB - scoreA
                      })[0]

                    if (!bestSource) return null

                    const [source, data] = bestSource
                    const config = getSourceConfig(source as LeadSource)

                    return (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{config.icon}</span>
                          <span className="text-xl font-bold text-terminal-400">
                            {config.name}
                          </span>
                        </div>
                        <div className="text-dark-text-secondary space-y-1">
                          <div>{data.count} leads generated</div>
                          {data.response_rate !== undefined && (
                            <div>{(data.response_rate * 100).toFixed(1)}% response rate</div>
                          )}
                          {data.conversion_rate !== undefined && (
                            <div>{(data.conversion_rate * 100).toFixed(1)}% conversion rate</div>
                          )}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-dark-text-primary mb-4">
              Quick Actions
            </h3>
            <div className="space-y-3">
              <Link to="/scraper" className="btn-primary w-full block text-center">
                Start New Scrape Job
              </Link>
              <Link to="/leads" className="btn-secondary w-full block text-center">
                View Recent Leads
              </Link>
              <Link to="/location-map" className="btn-secondary w-full block text-center">
                Manage Locations
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* AI Performance Comparison */}
      {aiPerformance && aiPerformance.models && aiPerformance.models.length > 0 && (
        <div className="card">
          <div className="px-6 py-4 border-b border-dark-border">
            <div className="flex items-center gap-2">
              <SparklesIcon className="h-5 w-5 text-purple-500" />
              <h3 className="text-lg font-medium text-dark-text-primary">
                AI Model Performance Comparison
              </h3>
            </div>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Compare costs and performance across different AI models
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-dark-border">
              <thead className="bg-dark-border/30">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Task Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Requests
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Avg Cost
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Total Cost
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Avg Duration
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                    Quality Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-dark-surface divide-y divide-dark-border">
                {aiPerformance.models.map((model: any, idx: number) => (
                  <tr key={idx} className="hover:bg-dark-border/20">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-dark-text-primary">
                      {model.model_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      {model.task_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-primary text-right">
                      {model.request_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-terminal-400 text-right font-mono">
                      ${model.avg_cost.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-terminal-400 text-right font-mono">
                      ${model.total_cost.toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary text-right">
                      {model.avg_duration_seconds ? `${model.avg_duration_seconds.toFixed(2)}s` : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      {model.avg_quality_score ? (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          model.avg_quality_score >= 0.8 ? 'bg-green-100 text-green-800' :
                          model.avg_quality_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {(model.avg_quality_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        <span className="text-dark-text-muted">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="card">
        <div className="px-6 py-4 border-b border-dark-border">
          <h3 className="text-lg font-medium text-dark-text-primary">
            Recent Activity
          </h3>
        </div>
        <div className="p-6">
          <div className="text-center text-dark-text-secondary">
            <DocumentTextIcon className="mx-auto h-12 w-12 text-terminal-500" />
            <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No recent activity</h3>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Get started by running your first scraping job.
            </p>
            <div className="mt-6">
              <Link to="/scraper" className="btn-primary inline-block">
                Start Scraping
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}