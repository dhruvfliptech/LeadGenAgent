// Charts and statistics component for workflow executions

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { WorkflowStats } from '@/types/workflow'
import { ChartBarIcon } from '@heroicons/react/24/outline'

interface WorkflowStatisticsProps {
  stats: WorkflowStats
}

const COLORS = {
  success: '#10B981',
  failed: '#EF4444',
  running: '#3B82F6',
  waiting: '#F59E0B'
}

export default function WorkflowStatistics({ stats }: WorkflowStatisticsProps) {
  // Prepare data for execution trend chart
  const executionTrendData = stats.executions_by_day.map(day => ({
    date: new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    Total: day.total,
    Success: day.success,
    Failed: day.failed
  }))

  // Prepare data for hourly distribution
  const hourlyData = stats.executions_by_hour.map(hour => ({
    hour: `${hour.hour}:00`,
    Executions: hour.count
  }))

  // Prepare data for status pie chart
  const statusData = [
    { name: 'Success', value: stats.successful_executions, color: COLORS.success },
    { name: 'Failed', value: stats.failed_executions, color: COLORS.failed },
    { name: 'Running', value: stats.running_executions, color: COLORS.running },
    { name: 'Waiting', value: stats.waiting_executions, color: COLORS.waiting }
  ].filter(item => item.value > 0)

  // Prepare error distribution data
  const errorData = stats.error_distribution.slice(0, 5).map(error => ({
    type: error.error_type.length > 30 ? error.error_type.substring(0, 30) + '...' : error.error_type,
    Count: error.count,
    Percentage: error.percentage
  }))

  return (
    <div className="space-y-6">
      {/* Execution Volume Over Time */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5" />
          Execution Volume (Last 30 Days)
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={executionTrendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9CA3AF" />
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
            <Line
              type="monotone"
              dataKey="Success"
              stroke={COLORS.success}
              strokeWidth={2}
              dot={{ fill: COLORS.success, r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="Failed"
              stroke={COLORS.failed}
              strokeWidth={2}
              dot={{ fill: COLORS.failed, r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="Total"
              stroke="#6B7280"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#6B7280', r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Distribution */}
        {hourlyData.length > 0 && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Executions by Hour
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="hour" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#F3F4F6'
                  }}
                />
                <Bar dataKey="Executions" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Status Distribution */}
        {statusData.length > 0 && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Execution Status Distribution
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#F3F4F6'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Error Distribution */}
      {errorData.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Top Error Types
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={errorData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" stroke="#9CA3AF" />
              <YAxis dataKey="type" type="category" stroke="#9CA3AF" width={150} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                  color: '#F3F4F6'
                }}
              />
              <Bar dataKey="Count" fill={COLORS.failed} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Slowest Nodes */}
      {stats.slowest_nodes && stats.slowest_nodes.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Slowest Workflow Nodes
          </h3>
          <div className="space-y-3">
            {stats.slowest_nodes.slice(0, 5).map((node, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
                <div>
                  <div className="font-medium text-dark-text-primary">{node.node_name}</div>
                  <div className="text-xs text-dark-text-muted">{node.execution_count} executions</div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-yellow-500">
                    {node.avg_duration_ms < 1000
                      ? `${node.avg_duration_ms.toFixed(0)}ms`
                      : `${(node.avg_duration_ms / 1000).toFixed(2)}s`}
                  </div>
                  <div className="text-xs text-dark-text-muted">avg duration</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
