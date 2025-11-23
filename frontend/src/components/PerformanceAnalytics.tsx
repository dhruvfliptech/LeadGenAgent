// Performance analytics component for workflow optimization insights

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { ClockIcon, BoltIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { WorkflowStats } from '@/types/workflow'

interface PerformanceAnalyticsProps {
  stats: WorkflowStats
  workflowId?: string
}

export default function PerformanceAnalytics({ stats }: PerformanceAnalyticsProps) {
  // Prepare slowest nodes data
  const slowestNodesData = stats.slowest_nodes?.slice(0, 8).map(node => ({
    name: node.node_name.length > 20 ? node.node_name.substring(0, 20) + '...' : node.node_name,
    'Avg Duration (ms)': node.avg_duration_ms,
    Executions: node.execution_count
  })) || []

  // Calculate performance score
  const performanceScore = Math.min(
    100,
    Math.round((stats.success_rate + (stats.avg_duration_seconds < 30 ? 50 : 25)) / 1.5)
  )

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-500/20 border-green-500/30'
    if (score >= 60) return 'bg-yellow-500/20 border-yellow-500/30'
    return 'bg-red-500/20 border-red-500/30'
  }

  // Generate recommendations
  const recommendations: Array<{ type: 'warning' | 'info'; message: string }> = []

  if (stats.avg_duration_seconds > 60) {
    recommendations.push({
      type: 'warning',
      message: `Average execution time is ${(stats.avg_duration_seconds / 60).toFixed(1)}m. Consider optimizing slow nodes.`
    })
  }

  if (stats.success_rate < 90) {
    recommendations.push({
      type: 'warning',
      message: `Success rate is ${stats.success_rate.toFixed(1)}%. Review error patterns to improve reliability.`
    })
  }

  if (stats.slowest_nodes && stats.slowest_nodes[0]?.avg_duration_ms > 5000) {
    recommendations.push({
      type: 'warning',
      message: `Node "${stats.slowest_nodes[0].node_name}" is taking ${(stats.slowest_nodes[0].avg_duration_ms / 1000).toFixed(1)}s on average. This may be a bottleneck.`
    })
  }

  if (stats.success_rate >= 95 && stats.avg_duration_seconds < 30) {
    recommendations.push({
      type: 'info',
      message: 'Workflows are performing well! Continue monitoring for sustained performance.'
    })
  }

  return (
    <div className="space-y-6">
      {/* Performance Score */}
      <div className={`card p-6 border-2 ${getScoreBgColor(performanceScore)}`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-dark-text-primary mb-1">
              Overall Performance Score
            </h3>
            <p className="text-sm text-dark-text-secondary">
              Based on success rate and execution speed
            </p>
          </div>
          <div className={`text-5xl font-bold ${getScoreColor(performanceScore)}`}>
            {performanceScore}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <ClockIcon className="w-6 h-6 text-blue-500" />
            <div>
              <div className="text-xs text-dark-text-muted">Avg Duration</div>
              <div className="text-lg font-semibold text-dark-text-primary">
                {stats.avg_duration_seconds < 60
                  ? `${stats.avg_duration_seconds.toFixed(1)}s`
                  : `${(stats.avg_duration_seconds / 60).toFixed(1)}m`}
              </div>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-3">
            <BoltIcon className="w-6 h-6 text-green-500" />
            <div>
              <div className="text-xs text-dark-text-muted">Success Rate</div>
              <div className="text-lg font-semibold text-dark-text-primary">
                {stats.success_rate.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500" />
            <div>
              <div className="text-xs text-dark-text-muted">Failed Executions</div>
              <div className="text-lg font-semibold text-dark-text-primary">
                {stats.failed_executions}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Slowest Nodes Chart */}
      {slowestNodesData.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Node Performance Analysis
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={slowestNodesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={100} />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                  color: '#F3F4F6'
                }}
              />
              <Legend />
              <Bar dataKey="Avg Duration (ms)" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-dark-text-muted mt-2">
            Identify and optimize nodes with high average execution times
          </p>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Optimization Recommendations
          </h3>
          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border ${
                  rec.type === 'warning'
                    ? 'bg-yellow-500/10 border-yellow-500/30'
                    : 'bg-blue-500/10 border-blue-500/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  {rec.type === 'warning' ? (
                    <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <BoltIcon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  )}
                  <p className={`text-sm ${rec.type === 'warning' ? 'text-yellow-300' : 'text-blue-300'}`}>
                    {rec.message}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bottleneck Summary */}
      {stats.slowest_nodes && stats.slowest_nodes.length > 0 && (
        <div className="card p-6 bg-orange-500/10 border border-orange-500/30">
          <h3 className="text-lg font-semibold text-orange-400 mb-3">
            Potential Bottlenecks
          </h3>
          <div className="space-y-2">
            {stats.slowest_nodes.slice(0, 3).map((node, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-dark-bg rounded">
                <div>
                  <div className="font-medium text-dark-text-primary">{node.node_name}</div>
                  <div className="text-xs text-dark-text-muted">
                    {node.execution_count} executions
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-orange-400 font-semibold">
                    {node.avg_duration_ms < 1000
                      ? `${node.avg_duration_ms.toFixed(0)}ms`
                      : `${(node.avg_duration_ms / 1000).toFixed(2)}s`}
                  </div>
                  <div className="text-xs text-dark-text-muted">avg time</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
