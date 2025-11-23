import { LeadSource } from '@/types/lead'
import { getSourceConfig } from './SourceSelector'

interface SourceBadgeProps {
  source: LeadSource
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  showName?: boolean
  className?: string
}

export default function SourceBadge({
  source,
  size = 'sm',
  showIcon = true,
  showName = true,
  className = ''
}: SourceBadgeProps) {
  const config = getSourceConfig(source)

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-sm px-3 py-1 gap-1.5',
    lg: 'text-base px-4 py-1.5 gap-2'
  }

  const iconSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  }

  return (
    <span
      className={`source-badge source-badge-${source} inline-flex items-center rounded-full font-medium ${sizeClasses[size]} ${className}`}
      style={{
        backgroundColor: `${config.color}15`,
        color: config.color,
        borderColor: `${config.color}50`,
        borderWidth: '1px'
      }}
    >
      {showIcon && <span className={iconSizes[size]}>{config.icon}</span>}
      {showName && <span>{config.name}</span>}
    </span>
  )
}

// Export for use in other components
export function SourceIcon({ source, className = '' }: { source: LeadSource; className?: string }) {
  const config = getSourceConfig(source)
  return <span className={className}>{config.icon}</span>
}

export function SourceName({ source }: { source: LeadSource }) {
  const config = getSourceConfig(source)
  return <>{config.name}</>
}

export function SourceColor({ source }: { source: LeadSource }): string {
  const config = getSourceConfig(source)
  return config.color
}
