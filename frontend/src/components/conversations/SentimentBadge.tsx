import { SentimentType } from '@/types/conversation'

interface SentimentBadgeProps {
  sentiment: SentimentType
  score?: number
  size?: 'sm' | 'md' | 'lg'
}

// Maps sentiment to colors, icons, and labels
const sentimentConfig = {
  positive: {
    label: 'Positive',
    icon: '😊',
    bgColor: 'bg-green-500/20',
    textColor: 'text-green-400',
    borderColor: 'border-green-500/30',
  },
  neutral: {
    label: 'Neutral',
    icon: '😐',
    bgColor: 'bg-gray-500/20',
    textColor: 'text-gray-400',
    borderColor: 'border-gray-500/30',
  },
  negative: {
    label: 'Negative',
    icon: '☹️',
    bgColor: 'bg-red-500/20',
    textColor: 'text-red-400',
    borderColor: 'border-red-500/30',
  },
  urgent: {
    label: 'Urgent',
    icon: '🚨',
    bgColor: 'bg-orange-500/20',
    textColor: 'text-orange-400',
    borderColor: 'border-orange-500/30',
  },
}

export default function SentimentBadge({ sentiment, score, size = 'md' }: SentimentBadgeProps) {
  const config = sentimentConfig[sentiment]

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${config.bgColor} ${config.textColor} ${config.borderColor} ${sizeClasses[size]} font-medium`}
      title={score ? `Confidence: ${Math.round(score * 100)}%` : undefined}
    >
      <span className="leading-none">{config.icon}</span>
      <span>{config.label}</span>
      {score !== undefined && (
        <span className="text-xs opacity-70">
          {Math.round(score * 100)}%
        </span>
      )}
    </span>
  )
}
