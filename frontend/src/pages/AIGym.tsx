import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  CpuChipIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  BanknotesIcon,
  PlusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BeakerIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import {
  getTotalModelStats,
  getActiveABTests,
  mockModelPerformance,
  mockModelConfigs,
  TaskType,
} from '@/mocks/models.mock'
import PerformanceChart from '@/components/PerformanceChart'
import CostEfficiencyChart from '@/components/CostEfficiencyChart'
import TaskTypeSelector from '@/components/TaskTypeSelector'

/**
 * AI-GYM Dashboard - Overview of AI model performance and optimization
 * Route: /ai-gym
 */
export default function AIGym() {
  const [selectedTaskType, setSelectedTaskType] = useState<TaskType | 'all'>('all')

  const stats = getTotalModelStats()
  const activeTests = getActiveABTests()

  // Filter performance data by task type
  const filteredPerformance = useMemo(() => {
    if (selectedTaskType === 'all') return mockModelPerformance
    return mockModelPerformance.filter(p => p.task_type === selectedTaskType)
  }, [selectedTaskType])

  // Top models by quality
  const topModels = useMemo(() => {
    return [...filteredPerformance]
      .sort((a, b) => b.avg_quality_score - a.avg_quality_score)
      .slice(0, 5)
      .map(perf => {
        const config = mockModelConfigs.find(c => c.model_id === perf.model_id)
        return { ...perf, config }
      })
  }, [filteredPerformance])

  // Cost efficiency data
  const costEfficiencyData = useMemo(() => {
    return [...filteredPerformance]
      .map(perf => {
        const config = mockModelConfigs.find(c => c.model_id === perf.model_id)
        return {
          model: config?.display_name || perf.model_id,
          qualityPerDollar: perf.avg_quality_score / perf.avg_cost_per_request,
          quality: perf.avg_quality_score,
          cost: perf.avg_cost_per_request,
        }
      })
      .sort((a, b) => b.qualityPerDollar - a.qualityPerDollar)
      .slice(0, 6)
  }, [filteredPerformance])

  // Mock quality over time data
  const qualityOverTime = [
    { date: 'Jan 1', 'claude-sonnet-4.5': 8.5, 'gpt-4o': 8.3, 'gpt-4-turbo': 8.1 },
    { date: 'Jan 2', 'claude-sonnet-4.5': 8.6, 'gpt-4o': 8.4, 'gpt-4-turbo': 8.2 },
    { date: 'Jan 3', 'claude-sonnet-4.5': 8.7, 'gpt-4o': 8.5, 'gpt-4-turbo': 8.3 },
    { date: 'Jan 4', 'claude-sonnet-4.5': 8.8, 'gpt-4o': 8.6, 'gpt-4-turbo': 8.4 },
    { date: 'Jan 5', 'claude-sonnet-4.5': 8.9, 'gpt-4o': 8.7, 'gpt-4-turbo': 8.5 },
  ]

  // Task type breakdown
  const taskBreakdown = useMemo(() => {
    const breakdown: Record<string, number> = {}
    mockModelPerformance.forEach(perf => {
      breakdown[perf.task_type] = (breakdown[perf.task_type] || 0) + perf.total_requests
    })
    return Object.entries(breakdown).map(([task, requests]) => ({ task, requests }))
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">AI-GYM</h1>
          <p className="text-dark-text-muted mt-1">
            Model Performance & Optimization Dashboard
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/ai-gym/ab-tests/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-terminal-500 text-white rounded-lg hover:bg-terminal-600 transition-colors font-medium"
          >
            <PlusIcon className="w-5 h-5" />
            Create A/B Test
          </Link>
          <button className="px-4 py-2 bg-dark-border text-dark-text-primary rounded-lg hover:bg-dark-border/70 transition-colors font-medium">
            Export Report
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Requests */}
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <CpuChipIcon className="w-6 h-6 text-blue-400" />
            </div>
            <span className="flex items-center gap-1 text-sm text-emerald-400">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              +23%
            </span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary mb-1">
            {stats.total_requests.toLocaleString()}
          </div>
          <div className="text-sm text-dark-text-muted">Total AI Calls</div>
          <div className="text-xs text-dark-text-muted mt-2">
            {stats.models_in_use} models in use
          </div>
        </div>

        {/* Total Cost */}
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-yellow-500/20 rounded-lg">
              <CurrencyDollarIcon className="w-6 h-6 text-yellow-400" />
            </div>
            <span className="flex items-center gap-1 text-sm text-emerald-400">
              <ArrowTrendingDownIcon className="w-4 h-4" />
              -12%
            </span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary mb-1">
            ${stats.total_cost.toFixed(2)}
          </div>
          <div className="text-sm text-dark-text-muted">Total Cost</div>
          <div className="text-xs text-dark-text-muted mt-2">
            Avg: ${(stats.total_cost / stats.total_requests).toFixed(3)} per request
          </div>
        </div>

        {/* Quality Score */}
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="flex items-center gap-1 text-sm text-emerald-400">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              +5pts
            </span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary mb-1">
            {stats.avg_quality.toFixed(1)}/10
          </div>
          <div className="text-sm text-dark-text-muted">Overall Quality Score</div>
          <div className="text-xs text-emerald-400 mt-2">Good</div>
        </div>

        {/* Cost Savings */}
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <BanknotesIcon className="w-6 h-6 text-purple-400" />
            </div>
            <span className="flex items-center gap-1 text-sm text-emerald-400">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              +34%
            </span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary mb-1">
            $89.50
          </div>
          <div className="text-sm text-dark-text-muted">Cost Savings</div>
          <div className="text-xs text-dark-text-muted mt-2">vs. using only GPT-4</div>
        </div>
      </div>

      {/* Task Type Filter */}
      <div>
        <h2 className="text-xl font-semibold text-dark-text-primary mb-4">Filter by Task Type</h2>
        <TaskTypeSelector selected={selectedTaskType} onChange={setSelectedTaskType} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceChart
          data={qualityOverTime}
          lines={[
            { dataKey: 'claude-sonnet-4.5', name: 'Claude Sonnet 4.5', color: '#10b981' },
            { dataKey: 'gpt-4o', name: 'GPT-4o', color: '#3b82f6' },
            { dataKey: 'gpt-4-turbo', name: 'GPT-4 Turbo', color: '#f59e0b' },
          ]}
          title="Quality Over Time"
          yAxisLabel="Quality Score"
        />
        <CostEfficiencyChart data={costEfficiencyData} />
      </div>

      {/* Top Models Table */}
      <div className="bg-dark-surface border border-dark-border rounded-lg">
        <div className="p-6 border-b border-dark-border">
          <h2 className="text-xl font-semibold text-dark-text-primary">
            Top Models by Quality
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-bg/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Task Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Quality Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Avg Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Avg Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Requests
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                  Error Rate
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border">
              {topModels.map((model, idx) => {
                const qualityColor = model.avg_quality_score >= 9 ? 'text-emerald-400' :
                                   model.avg_quality_score >= 8 ? 'text-blue-400' : 'text-yellow-400'
                const errorColor = model.error_rate < 1 ? 'text-emerald-400' :
                                 model.error_rate < 3 ? 'text-yellow-400' : 'text-red-400'

                return (
                  <tr key={`${model.model_id}-${idx}`} className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-dark-text-primary">
                        {model.config?.display_name || model.model_id}
                      </div>
                      <div className="text-xs text-dark-text-muted">
                        {model.config?.provider}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      {model.task_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-lg font-bold ${qualityColor}`}>
                        {model.avg_quality_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      <div className="flex items-center gap-1">
                        <ClockIcon className="w-4 h-4 text-dark-text-muted" />
                        {model.avg_response_time_ms.toLocaleString()}ms
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      ${model.avg_cost_per_request.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text-secondary">
                      {model.total_requests.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${errorColor}`}>
                        {model.error_rate.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Active A/B Tests */}
      <div className="bg-dark-surface border border-dark-border rounded-lg">
        <div className="p-6 border-b border-dark-border flex items-center justify-between">
          <h2 className="text-xl font-semibold text-dark-text-primary flex items-center gap-2">
            <BeakerIcon className="w-6 h-6 text-terminal-400" />
            Active A/B Tests
          </h2>
          <Link
            to="/ai-gym/ab-tests"
            className="text-sm text-terminal-400 hover:text-terminal-300"
          >
            View All Tests →
          </Link>
        </div>
        {activeTests.length > 0 ? (
          <div className="p-6 space-y-4">
            {activeTests.map((test) => (
              <Link
                key={test.id}
                to={`/ai-gym/ab-tests/${test.id}`}
                className="block p-4 bg-dark-bg/50 border border-dark-border rounded-lg hover:border-terminal-500/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-dark-text-primary">{test.name}</h3>
                    <p className="text-sm text-dark-text-muted mt-1">{test.description}</p>
                  </div>
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 text-xs font-medium rounded-full border border-blue-500/30">
                    Running
                  </span>
                </div>
                <div className="flex gap-4 text-sm">
                  <span className="text-dark-text-muted">
                    Models: <span className="text-dark-text-primary">{test.models.length}</span>
                  </span>
                  <span className="text-dark-text-muted">
                    Task: <span className="text-dark-text-primary">{test.task_type.replace('_', ' ')}</span>
                  </span>
                  {test.results && (
                    <span className="text-dark-text-muted">
                      Requests: <span className="text-dark-text-primary">
                        {test.results.reduce((sum, r) => sum + r.requests, 0)}
                      </span>
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <BeakerIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-4" />
            <p className="text-dark-text-muted">No active A/B tests</p>
            <Link
              to="/ai-gym/ab-tests/new"
              className="inline-block mt-4 text-terminal-400 hover:text-terminal-300"
            >
              Create your first test →
            </Link>
          </div>
        )}
      </div>

      {/* Task Type Breakdown */}
      <div className="bg-dark-surface border border-dark-border rounded-lg">
        <div className="p-6 border-b border-dark-border">
          <h2 className="text-xl font-semibold text-dark-text-primary">Task Type Breakdown</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            {taskBreakdown.map(({ task, requests }) => {
              const percentage = (requests / stats.total_requests) * 100
              return (
                <div key={task}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-dark-text-primary capitalize">
                      {task.replace('_', ' ')}
                    </span>
                    <span className="text-dark-text-muted">
                      {requests.toLocaleString()} ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full bg-dark-border rounded-full h-2">
                    <div
                      className="bg-terminal-500 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
