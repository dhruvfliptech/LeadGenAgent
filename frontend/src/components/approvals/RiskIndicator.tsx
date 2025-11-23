import { RiskLevel } from '@/mocks/approvals.mock'

interface RiskIndicatorProps {
  level: RiskLevel
  score?: number
  showScore?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const riskConfig = {
  low: {
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: '✓',
    label: 'Low Risk'
  },
  medium: {
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: '⚠',
    label: 'Medium Risk'
  },
  high: {
    color: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: '⚠',
    label: 'High Risk'
  },
  critical: {
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: '⚠',
    label: 'Critical Risk'
  }
}

const sizeConfig = {
  sm: 'text-xs px-2 py-1',
  md: 'text-sm px-3 py-1.5',
  lg: 'text-base px-4 py-2'
}

export default function RiskIndicator({ level, score, showScore = true, size = 'md' }: RiskIndicatorProps) {
  const config = riskConfig[level]

  return (
    <div className="inline-flex items-center gap-2">
      <span
        className={`inline-flex items-center gap-1 rounded-full border font-medium ${config.color} ${sizeConfig[size]}`}
      >
        <span>{config.icon}</span>
        <span>{config.label}</span>
      </span>
      {showScore && score !== undefined && (
        <span className="text-sm text-gray-500">
          Score: {score}/100
        </span>
      )}
    </div>
  )
}
