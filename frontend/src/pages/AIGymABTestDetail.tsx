import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  TrophyIcon,
  ClockIcon,
  BeakerIcon,
  ChartBarIcon,
  CpuChipIcon,
  CurrencyDollarIcon,
} from '@heroicons/react/24/outline'
import { CheckCircleIcon } from '@heroicons/react/24/solid'
import { mockABTests, mockModelConfigs } from '@/mocks/models.mock'
import { formatDistanceToNow, format } from 'date-fns'
import PerformanceChart from '@/components/PerformanceChart'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

/**
 * AI-GYM A/B Test Detail - Individual test results and analysis
 * Route: /ai-gym/ab-tests/:id
 */
export default function AIGymABTestDetail() {
  const { id } = useParams<{ id: string }>()
  const test = mockABTests.find(t => t.id === parseInt(id || '0'))

  if (!test) {
    return (
      <div className="text-center py-12">
        <p className="text-dark-text-muted">Test not found</p>
        <Link to="/ai-gym/ab-tests" className="text-terminal-400 hover:text-terminal-300 mt-4 inline-block">
          ← Back to A/B Tests
        </Link>
      </div>
    )
  }

  const statusConfig = {
    draft: { color: 'bg-gray-500/20 text-gray-400 border-gray-500/30', label: 'Draft' },
    running: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'Running' },
    paused: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', label: 'Paused' },
    completed: { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', label: 'Completed' },
  }

  const status = statusConfig[test.status]
  const totalRequests = test.results?.reduce((sum, r) => sum + r.requests, 0) || 0
  const winnerResult = test.winner && test.results?.find(r => r.model_id === test.winner)
  const winnerConfig = test.winner && mockModelConfigs.find(c => c.model_id === test.winner)

  // Prepare chart data
  const comparisonData = test.results?.map(result => {
    const config = mockModelConfigs.find(c => c.model_id === result.model_id)
    return {
      model: config?.display_name || result.model_id,
      quality: result.avg_quality,
      cost: result.avg_cost * 1000, // Scale for visibility
      responseTime: result.avg_response_time / 1000, // Convert to seconds
      requests: result.requests,
    }
  }) || []

  // Mock quality over time data
  const qualityOverTime = [
    { date: 'Day 1', ...Object.fromEntries(test.models.map(m => [m, 8.0 + Math.random()])) },
    { date: 'Day 2', ...Object.fromEntries(test.models.map(m => [m, 8.2 + Math.random()])) },
    { date: 'Day 3', ...Object.fromEntries(test.models.map(m => [m, 8.4 + Math.random()])) },
    { date: 'Day 4', ...Object.fromEntries(test.models.map(m => [m, 8.6 + Math.random()])) },
    { date: 'Day 5', ...Object.fromEntries(test.models.map(m => [m, 8.8 + Math.random()])) },
  ]

  const chartLines = test.models.map((modelId, idx) => {
    const config = mockModelConfigs.find(c => c.model_id === modelId)
    return {
      dataKey: modelId,
      name: config?.display_name || modelId,
      color: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'][idx],
    }
  })

  // Calculate statistical significance (mock)
  const statisticalSignificance = test.winner ? 95.3 : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/ai-gym/ab-tests"
          className="inline-flex items-center gap-2 text-dark-text-muted hover:text-terminal-400 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to A/B Tests
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-dark-text-primary mb-2">{test.name}</h1>
            <p className="text-dark-text-muted">{test.description}</p>
          </div>
          <span className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium border ${status.color}`}>
            {status.label}
          </span>
        </div>
      </div>

      {/* Test Configuration */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
        <h2 className="text-xl font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
          <BeakerIcon className="w-6 h-6 text-terminal-400" />
          Test Configuration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <div className="text-sm text-dark-text-muted mb-1">Task Type</div>
            <div className="text-lg font-semibold text-dark-text-primary capitalize">
              {test.task_type.replace('_', ' ')}
            </div>
          </div>
          <div>
            <div className="text-sm text-dark-text-muted mb-1">Models Being Tested</div>
            <div className="text-lg font-semibold text-dark-text-primary">
              {test.models.length} models
            </div>
          </div>
          {test.started_at && (
            <div>
              <div className="text-sm text-dark-text-muted mb-1 flex items-center gap-1">
                <ClockIcon className="w-4 h-4" />
                Started
              </div>
              <div className="text-lg font-semibold text-dark-text-primary">
                {format(new Date(test.started_at), 'MMM d, yyyy')}
              </div>
              <div className="text-xs text-dark-text-muted">
                {formatDistanceToNow(new Date(test.started_at))} ago
              </div>
            </div>
          )}
          {totalRequests > 0 && (
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Total Requests</div>
              <div className="text-lg font-semibold text-dark-text-primary">
                {totalRequests.toLocaleString()}
              </div>
            </div>
          )}
        </div>

        {/* Traffic Split Visualization */}
        <div className="mt-6 pt-6 border-t border-dark-border">
          <div className="text-sm font-medium text-dark-text-primary mb-3">Traffic Split</div>
          <div className="space-y-3">
            {test.models.map((modelId, idx) => {
              const config = mockModelConfigs.find(c => c.model_id === modelId)
              const split = test.traffic_split[modelId] || 0
              const colors = [
                { bg: 'bg-blue-500', text: 'text-blue-400' },
                { bg: 'bg-emerald-500', text: 'text-emerald-400' },
                { bg: 'bg-yellow-500', text: 'text-yellow-400' },
                { bg: 'bg-purple-500', text: 'text-purple-400' },
              ]
              const color = colors[idx % colors.length]

              return (
                <div key={modelId}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-dark-text-primary">
                      {config?.display_name || modelId}
                    </span>
                    <span className={`font-medium ${color.text}`}>{split}%</span>
                  </div>
                  <div className="w-full bg-dark-border rounded-full h-2">
                    <div
                      className={`${color.bg} h-2 rounded-full transition-all`}
                      style={{ width: `${split}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Winner Announcement */}
      {test.winner && winnerConfig && winnerResult && (
        <div className="bg-gradient-to-r from-emerald-500/20 to-blue-500/20 border-2 border-emerald-500/50 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <TrophyIcon className="w-8 h-8 text-emerald-400" />
            <div>
              <h2 className="text-2xl font-bold text-emerald-400">Winner Identified</h2>
              <p className="text-dark-text-muted">
                Statistical significance: {statisticalSignificance.toFixed(1)}%
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-dark-surface/50 rounded-lg">
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Winning Model</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {winnerConfig.display_name}
              </div>
              <div className="text-xs text-dark-text-muted capitalize">{winnerConfig.provider}</div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Quality Score</div>
              <div className="text-xl font-bold text-emerald-400">
                {winnerResult.avg_quality.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Avg Cost</div>
              <div className="text-xl font-bold text-dark-text-primary">
                ${winnerResult.avg_cost.toFixed(3)}
              </div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Avg Response Time</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {winnerResult.avg_response_time.toLocaleString()}ms
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results Comparison */}
      {test.results && test.results.length > 0 && (
        <>
          {/* Side-by-Side Results */}
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-dark-text-primary mb-6">
              Results Comparison
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {test.results.map(result => {
                const config = mockModelConfigs.find(c => c.model_id === result.model_id)
                const isWinner = test.winner === result.model_id

                return (
                  <div
                    key={result.model_id}
                    className={`p-6 rounded-lg border-2 ${
                      isWinner
                        ? 'border-emerald-500 bg-emerald-500/5'
                        : 'border-dark-border bg-dark-bg/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-dark-text-primary">
                          {config?.display_name || result.model_id}
                        </h3>
                        <p className="text-sm text-dark-text-muted capitalize">
                          {config?.provider}
                        </p>
                      </div>
                      {isWinner && (
                        <div className="flex items-center gap-1 px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-medium">
                          <CheckCircleIcon className="w-4 h-4" />
                          Winner
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-dark-surface rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <ChartBarIcon className="w-4 h-4 text-blue-400" />
                          <span className="text-xs text-dark-text-muted">Quality Score</span>
                        </div>
                        <div className={`text-2xl font-bold ${
                          isWinner ? 'text-emerald-400' : 'text-blue-400'
                        }`}>
                          {result.avg_quality.toFixed(1)}
                        </div>
                      </div>

                      <div className="p-4 bg-dark-surface rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <CurrencyDollarIcon className="w-4 h-4 text-yellow-400" />
                          <span className="text-xs text-dark-text-muted">Avg Cost</span>
                        </div>
                        <div className="text-2xl font-bold text-dark-text-primary">
                          ${result.avg_cost.toFixed(3)}
                        </div>
                      </div>

                      <div className="p-4 bg-dark-surface rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <ClockIcon className="w-4 h-4 text-purple-400" />
                          <span className="text-xs text-dark-text-muted">Response Time</span>
                        </div>
                        <div className="text-2xl font-bold text-dark-text-primary">
                          {result.avg_response_time.toLocaleString()}
                          <span className="text-sm text-dark-text-muted ml-1">ms</span>
                        </div>
                      </div>

                      <div className="p-4 bg-dark-surface rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <CpuChipIcon className="w-4 h-4 text-emerald-400" />
                          <span className="text-xs text-dark-text-muted">Requests</span>
                        </div>
                        <div className="text-2xl font-bold text-dark-text-primary">
                          {result.requests.toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Cost Efficiency */}
                    <div className="mt-4 pt-4 border-t border-dark-border">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-dark-text-muted">Cost Efficiency</span>
                        <span className="text-lg font-bold text-terminal-400">
                          {(result.avg_quality / result.avg_cost).toFixed(0)} Q/$
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Performance Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PerformanceChart
              data={qualityOverTime}
              lines={chartLines}
              title="Quality Score Over Time"
              yAxisLabel="Quality Score"
            />

            {/* Comparison Bar Chart */}
            <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                Metrics Comparison
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                  <XAxis
                    dataKey="model"
                    stroke="#718096"
                    style={{ fontSize: '12px' }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#718096" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a202c',
                      border: '1px solid #2d3748',
                      borderRadius: '6px',
                      color: '#e2e8f0',
                    }}
                  />
                  <Legend />
                  <Bar dataKey="quality" name="Quality Score" fill="#3b82f6" />
                  <Bar dataKey="responseTime" name="Response Time (s)" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detailed Metrics Table */}
          <div className="bg-dark-surface border border-dark-border rounded-lg">
            <div className="p-6 border-b border-dark-border">
              <h2 className="text-xl font-semibold text-dark-text-primary">
                Detailed Metrics
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-dark-bg/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Model
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Requests
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Quality Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Avg Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Response Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase">
                      Cost Efficiency
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {test.results.map(result => {
                    const config = mockModelConfigs.find(c => c.model_id === result.model_id)
                    const isWinner = test.winner === result.model_id

                    return (
                      <tr
                        key={result.model_id}
                        className={isWinner ? 'bg-emerald-500/5' : 'hover:bg-dark-bg/30'}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            {isWinner && <TrophyIcon className="w-4 h-4 text-emerald-400" />}
                            <div>
                              <div className="font-medium text-dark-text-primary">
                                {config?.display_name || result.model_id}
                              </div>
                              <div className="text-xs text-dark-text-muted capitalize">
                                {config?.provider}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                          {result.requests.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`font-bold ${isWinner ? 'text-emerald-400' : 'text-blue-400'}`}>
                            {result.avg_quality.toFixed(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                          ${result.avg_cost.toFixed(3)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                          {result.avg_response_time.toLocaleString()}ms
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="font-semibold text-terminal-400">
                            {(result.avg_quality / result.avg_cost).toFixed(0)} Q/$
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* No Results Yet */}
      {(!test.results || test.results.length === 0) && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-12 text-center">
          <BeakerIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-4" />
          <p className="text-dark-text-muted mb-2">No results yet</p>
          <p className="text-sm text-dark-text-muted">
            {test.status === 'draft' ? 'Start the test to begin collecting results' : 'Results will appear as requests are processed'}
          </p>
        </div>
      )}
    </div>
  )
}
