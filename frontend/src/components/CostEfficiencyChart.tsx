import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface CostEfficiencyData {
  model: string
  qualityPerDollar: number
  quality: number
  cost: number
}

interface CostEfficiencyChartProps {
  data: CostEfficiencyData[]
  title?: string
  height?: number
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

/**
 * Cost efficiency chart showing quality per dollar for each model
 * Usage:
 * <CostEfficiencyChart
 *   data={[
 *     { model: 'Claude Sonnet', qualityPerDollar: 207, quality: 8.7, cost: 0.042 },
 *     { model: 'GPT-4o', qualityPerDollar: 354, quality: 8.5, cost: 0.024 }
 *   ]}
 * />
 */
export default function CostEfficiencyChart({
  data,
  title = 'Cost Efficiency (Quality per Dollar)',
  height = 300,
}: CostEfficiencyChartProps) {
  return (
    <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
      <h3 className="text-lg font-semibold text-dark-text-primary mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
          <XAxis
            dataKey="model"
            stroke="#718096"
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#718096"
            style={{ fontSize: '12px' }}
            label={{ value: 'Quality / Cost', angle: -90, position: 'insideLeft', style: { fill: '#718096' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a202c',
              border: '1px solid #2d3748',
              borderRadius: '6px',
              color: '#e2e8f0',
            }}
            labelStyle={{ color: '#a0aec0' }}
            formatter={(value: number, name: string, props: any) => {
              if (name === 'qualityPerDollar') {
                return [
                  value.toFixed(2),
                  `Quality/Dollar (Q: ${props.payload.quality}, C: $${props.payload.cost.toFixed(3)})`
                ]
              }
              return [value, name]
            }}
          />
          <Bar dataKey="qualityPerDollar" radius={[8, 8, 0, 0]}>
            {data.map((_entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
