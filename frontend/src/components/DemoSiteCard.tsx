import { useState } from 'react'
import {
  GlobeAltIcon,
  CodeBracketIcon,
  ClockIcon,
  CurrencyDollarIcon,
  EyeIcon,
  ArrowTopRightOnSquareIcon,
  ArrowPathIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { DemoSite } from '@/types/demoSite'
import { demoSitesUtils } from '@/services/demoSitesApi'
import { formatRelativeTime } from '@/utils/dateFormat'

interface DemoSiteCardProps {
  demoSite: DemoSite
  onView: (demoSite: DemoSite) => void
  onRedeploy?: (buildId: string) => void
  onDelete?: (buildId: string) => void
}

export default function DemoSiteCard({ demoSite, onView, onRedeploy, onDelete }: DemoSiteCardProps) {
  const [imageError, setImageError] = useState(false)

  const statusColor = demoSitesUtils.getStatusColor(demoSite.status)
  const frameworkIcon = demoSitesUtils.getFrameworkIcon(demoSite.framework)
  const frameworkName = demoSitesUtils.getFrameworkName(demoSite.framework)

  // Generate preview image URL (screenshot service)
  const previewImageUrl = demoSite.preview_url && !imageError
    ? `https://api.screenshotmachine.com/?key=demo&url=${encodeURIComponent(demoSite.preview_url)}&dimension=1024x768`
    : null

  const isCompleted = demoSite.status === 'completed'
  const isFailed = demoSite.status === 'failed'
  const isInProgress = ['analyzing', 'planning', 'generating', 'deploying'].includes(demoSite.status)

  return (
    <div className="card overflow-hidden hover:shadow-lg transition-shadow duration-200">
      {/* Preview Image or Placeholder */}
      <div
        className="relative h-48 bg-gradient-to-br from-terminal-900/20 to-dark-border cursor-pointer"
        onClick={() => onView(demoSite)}
      >
        {previewImageUrl ? (
          <img
            src={previewImageUrl}
            alt={`Preview of ${demoSite.lead_title || demoSite.original_url}`}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center">
              <span className="text-6xl">{frameworkIcon}</span>
              <div className="mt-2 text-sm text-dark-text-muted">{frameworkName}</div>
            </div>
          </div>
        )}

        {/* Status Badge */}
        <div className="absolute top-2 right-2">
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${statusColor} backdrop-blur-sm`}>
            {isInProgress && (
              <ArrowPathIcon className="w-3 h-3 mr-1 animate-spin" />
            )}
            {isCompleted && (
              <CheckCircleIcon className="w-3 h-3 mr-1" />
            )}
            {isFailed && (
              <ExclamationTriangleIcon className="w-3 h-3 mr-1" />
            )}
            {demoSite.status}
          </span>
        </div>

        {/* Framework Badge */}
        <div className="absolute top-2 left-2">
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-dark-surface/90 text-dark-text-primary border border-dark-border backdrop-blur-sm">
            <span className="mr-1">{frameworkIcon}</span>
            {frameworkName}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3
          className="text-lg font-semibold text-dark-text-primary mb-1 truncate cursor-pointer hover:text-terminal-400 transition-colors"
          onClick={() => onView(demoSite)}
          title={demoSite.lead_title || demoSite.original_url}
        >
          {demoSite.lead_title || 'Untitled Demo'}
        </h3>

        {/* Original URL */}
        <a
          href={demoSite.original_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-dark-text-secondary hover:text-terminal-400 flex items-center gap-1 mb-3 truncate"
        >
          <GlobeAltIcon className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">{demoSite.original_url}</span>
          <ArrowTopRightOnSquareIcon className="w-3 h-3 flex-shrink-0" />
        </a>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
          {/* Lines of Code */}
          <div className="flex items-center gap-2">
            <CodeBracketIcon className="w-4 h-4 text-terminal-500" />
            <span className="text-dark-text-secondary">
              {demoSite.total_lines_of_code.toLocaleString()} lines
            </span>
          </div>

          {/* Generation Time */}
          <div className="flex items-center gap-2">
            <ClockIcon className="w-4 h-4 text-blue-500" />
            <span className="text-dark-text-secondary">
              {demoSitesUtils.formatDuration(demoSite.generation_time_seconds)}
            </span>
          </div>

          {/* AI Cost */}
          <div className="flex items-center gap-2">
            <CurrencyDollarIcon className="w-4 h-4 text-green-500" />
            <span className="text-dark-text-secondary font-mono">
              ${demoSite.ai_cost.toFixed(4)}
            </span>
          </div>

          {/* Views */}
          {demoSite.view_count !== undefined && (
            <div className="flex items-center gap-2">
              <EyeIcon className="w-4 h-4 text-purple-500" />
              <span className="text-dark-text-secondary">
                {demoSite.view_count} views
              </span>
            </div>
          )}
        </div>

        {/* Improvements Count */}
        {demoSite.improvements_applied && demoSite.improvements_applied.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-dark-text-muted mb-1">Improvements Applied:</div>
            <div className="flex flex-wrap gap-1">
              {demoSite.improvements_applied.slice(0, 3).map((improvement, idx) => (
                <span
                  key={idx}
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${demoSitesUtils.getPriorityColor(improvement.priority)}`}
                  title={improvement.title}
                >
                  {demoSitesUtils.getCategoryIcon(improvement.category)} {improvement.category}
                </span>
              ))}
              {demoSite.improvements_applied.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-dark-border text-dark-text-secondary">
                  +{demoSite.improvements_applied.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Validation Status */}
        {demoSite.validation_results && (
          <div className="mb-3 text-xs">
            {demoSite.validation_results.is_valid ? (
              <div className="flex items-center gap-1 text-green-600">
                <CheckCircleIcon className="w-4 h-4" />
                <span>Validation passed</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-red-600">
                <ExclamationTriangleIcon className="w-4 h-4" />
                <span>{demoSite.validation_results.errors.length} validation errors</span>
              </div>
            )}
          </div>
        )}

        {/* Created Date */}
        <div className="text-xs text-dark-text-muted mb-3">
          Created {formatRelativeTime(demoSite.created_at)}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-3 border-t border-dark-border">
          <button
            onClick={() => onView(demoSite)}
            className="btn-primary text-sm flex-1"
          >
            View Details
          </button>

          {isCompleted && demoSite.preview_url && (
            <a
              href={demoSite.preview_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm px-3 py-2"
              title="Open live preview"
            >
              <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            </a>
          )}

          {isCompleted && onRedeploy && (
            <button
              onClick={() => onRedeploy(demoSite.build_id)}
              className="btn-secondary text-sm px-3 py-2"
              title="Redeploy"
            >
              <ArrowPathIcon className="w-4 h-4" />
            </button>
          )}

          {onDelete && (
            <button
              onClick={() => onDelete(demoSite.build_id)}
              className="text-red-600 hover:text-red-800 hover:bg-red-50 rounded px-3 py-2 transition-colors"
              title="Delete demo"
            >
              <TrashIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
