import { ReactNode } from 'react'

interface SourceCardProps {
  icon: ReactNode
  title: string
  description: string
  color: string
  enabled?: boolean
  onClick: () => void
}

/**
 * SourceCard - Displays a data source option for scraping
 * Usage: <SourceCard icon={icon} title="Craigslist" description="..." onClick={...} />
 */
export default function SourceCard({
  icon,
  title,
  description,
  color,
  enabled = true,
  onClick
}: SourceCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={!enabled}
      className={`
        group relative overflow-hidden rounded-xl border-2 p-6 text-left transition-all
        ${enabled
          ? 'border-dark-border hover:border-terminal-500 hover:shadow-lg hover:scale-105 cursor-pointer bg-dark-surface'
          : 'border-dark-border bg-dark-border/20 cursor-not-allowed opacity-60'
        }
      `}
    >
      {/* Background gradient on hover */}
      {enabled && (
        <div
          className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity"
          style={{ background: `linear-gradient(135deg, ${color}22, transparent)` }}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="text-4xl">{icon}</div>
          {!enabled && (
            <span className="text-xs font-medium text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded">
              Coming Soon
            </span>
          )}
        </div>

        <h3 className="text-lg font-bold text-dark-text-primary mb-1 group-hover:text-terminal-500 transition-colors">
          {title}
        </h3>
        <p className="text-sm text-dark-text-secondary">
          {description}
        </p>

        {/* Active indicator */}
        {enabled && (
          <div className="mt-4 flex items-center text-xs text-terminal-500 opacity-0 group-hover:opacity-100 transition-opacity">
            <span className="mr-1">→</span>
            <span>Click to configure</span>
          </div>
        )}
      </div>
    </button>
  )
}
