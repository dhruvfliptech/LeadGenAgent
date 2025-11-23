import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DataPoint {
  date: string
  [key: string]: number | string
}

interface PerformanceChartProps {
  data: DataPoint[]
  lines: {
    dataKey: string
    name: string
    color: string
  }[]
  title?: string
  yAxisLabel?: string
  height?: number
}

/**
 * Performance chart for displaying quality over time by model
 * Usage:
 * <PerformanceChart
 *   data={qualityOverTime}
 *   lines={[
 *     { dataKey: 'claude-sonnet-4.5', name: 'Claude Sonnet 4.5', color: '#10b981' },
 *     { dataKey: 'gpt-4o', name: 'GPT-4o', color: '#3b82f6' }
 *   ]}
 *   yAxisLabel="Quality Score"
 * />
 */
export default function PerformanceChart({
  data,
  lines,
  title,
  yAxisLabel,
  height = 300,
}: PerformanceChartProps) {
  return (
    <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
      {title && (
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis
            dataKey="date"
            stroke="#718096"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#718096"
            style={{ fontSize: '12px' }}
            label={yAxisLabel ? { value: yAxisLabel, angle: -90, position: 'insideLeft', style: { fill: '#718096' } } : undefined}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a202c',
              border: '1px solid #2d3748',
              borderRadius: '6px',
              color: '#e2e8f0',
            }}
            labelStyle={{ color: '#a0aec0' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#a0aec0' }}
          />
          {lines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={2}
              dot={{ fill: line.color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
