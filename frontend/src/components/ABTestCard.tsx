import { Link } from 'react-router-dom'
import { ABTest, mockModelConfigs } from '@/mocks/models.mock'
import {
  BeakerIcon,
  ClockIcon,
  CheckCircleIcon,
  PauseCircleIcon,
  DocumentTextIcon,
  TrophyIcon,
} from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'

interface ABTestCardProps {
  test: ABTest
}

const statusConfig = {
  draft: {
    color: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    icon: DocumentTextIcon,
    label: 'Draft',
  },
  running: {
    color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    icon: BeakerIcon,
    label: 'Running',
  },
  paused: {
    color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    icon: PauseCircleIcon,
    label: 'Paused',
  },
  completed: {
    color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    icon: CheckCircleIcon,
    label: 'Completed',
  },
}

/**
 * ABTestCard component displays A/B test information
 * Usage:
 * <ABTestCard test={abTest} />
 */
export default function ABTestCard({ test }: ABTestCardProps) {
  const status = statusConfig[test.status]
  const StatusIcon = status.icon

  const totalRequests = test.results?.reduce((sum, r) => sum + r.requests, 0) || 0
  const winnerResult = test.winner && test.results?.find(r => r.model_id === test.winner)
  const winnerConfig = test.winner && mockModelConfigs.find(c => c.model_id === test.winner)

  return (
    <Link
      to={`/ai-gym/ab-tests/${test.id}`}
      className="block bg-dark-surface border border-dark-border rounded-lg p-6 hover:border-terminal-500/50 transition-all hover:shadow-lg"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-2">
            {test.name}
          </h3>
          <p className="text-sm text-dark-text-muted line-clamp-2">
            {test.description}
          </p>
        </div>
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${status.color} whitespace-nowrap ml-4`}>
          <StatusIcon className="w-3.5 h-3.5" />
          {status.label}
        </span>
      </div>

      {/* Test Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 pb-4 border-b border-dark-border">
        <div>
          <div className="text-xs text-dark-text-muted mb-1">Task Type</div>
          <div className="text-sm font-medium text-dark-text-primary capitalize">
            {test.task_type.replace('_', ' ')}
          </div>
        </div>
        <div>
          <div className="text-xs text-dark-text-muted mb-1">Models</div>
          <div className="text-sm font-medium text-dark-text-primary">
            {test.models.length} models
          </div>
        </div>
        {totalRequests > 0 && (
          <div>
            <div className="text-xs text-dark-text-muted mb-1">Total Requests</div>
            <div className="text-sm font-medium text-dark-text-primary">
              {totalRequests.toLocaleString()}
            </div>
          </div>
        )}
        {test.started_at && (
          <div>
            <div className="text-xs text-dark-text-muted mb-1 flex items-center gap-1">
              <ClockIcon className="w-3 h-3" />
              {test.status === 'completed' ? 'Duration' : 'Running for'}
            </div>
            <div className="text-sm font-medium text-dark-text-primary">
              {formatDistanceToNow(new Date(test.started_at))}
            </div>
          </div>
        )}
      </div>

      {/* Winner Badge */}
      {test.winner && winnerConfig && winnerResult && (
        <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrophyIcon className="w-5 h-5 text-emerald-400" />
            <span className="font-semibold text-emerald-400">Winner</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-sm">
            <div>
              <div className="text-xs text-dark-text-muted">Model</div>
              <div className="font-medium text-dark-text-primary">{winnerConfig.display_name}</div>
            </div>
            <div>
              <div className="text-xs text-dark-text-muted">Quality</div>
              <div className="font-medium text-emerald-400">{winnerResult.avg_quality.toFixed(1)}</div>
            </div>
            <div>
              <div className="text-xs text-dark-text-muted">Cost</div>
              <div className="font-medium text-dark-text-primary">${winnerResult.avg_cost.toFixed(3)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Model Results Preview */}
      {test.results && test.results.length > 0 && !test.winner && (
        <div className="space-y-2">
          <div className="text-xs text-dark-text-muted mb-2">Current Results</div>
          {test.results.slice(0, 2).map(result => {
            const config = mockModelConfigs.find(c => c.model_id === result.model_id)
            return (
              <div
                key={result.model_id}
                className="flex items-center justify-between p-2 bg-dark-bg/50 rounded"
              >
                <div className="flex items-center gap-2">
                  <div className="text-sm font-medium text-dark-text-primary">
                    {config?.display_name || result.model_id}
                  </div>
                  <div className="text-xs text-dark-text-muted">
                    {result.requests} reqs
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div>
                    <span className="text-dark-text-muted">Q:</span>
                    <span className="text-blue-400 font-medium ml-1">
                      {result.avg_quality.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-dark-text-muted">$:</span>
                    <span className="text-dark-text-primary font-medium ml-1">
                      {result.avg_cost.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
          {test.results.length > 2 && (
            <div className="text-xs text-dark-text-muted text-center">
              +{test.results.length - 2} more models
            </div>
          )}
        </div>
      )}

      {/* Traffic Split (for running/draft tests) */}
      {(test.status === 'running' || test.status === 'draft') && (
        <div className="mt-4 pt-4 border-t border-dark-border">
          <div className="text-xs text-dark-text-muted mb-2">Traffic Split</div>
          <div className="flex gap-1 h-2 rounded-full overflow-hidden">
            {test.models.map((modelId, idx) => {
              const split = test.traffic_split[modelId] || 0
              const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-yellow-500', 'bg-purple-500']
              return (
                <div
                  key={modelId}
                  className={colors[idx % colors.length]}
                  style={{ width: `${split}%` }}
                  title={`${modelId}: ${split}%`}
                />
              )
            })}
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            {test.models.map((modelId, idx) => {
              const config = mockModelConfigs.find(c => c.model_id === modelId)
              const colors = ['text-blue-400', 'text-emerald-400', 'text-yellow-400', 'text-purple-400']
              return (
                <span key={modelId} className={`text-xs ${colors[idx % colors.length]}`}>
                  {config?.display_name}: {test.traffic_split[modelId]}%
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* View Details Link */}
      <div className="mt-4 pt-4 border-t border-dark-border">
        <div className="text-sm text-terminal-400 hover:text-terminal-300 font-medium">
          View Details →
        </div>
      </div>
    </Link>
  )
}
