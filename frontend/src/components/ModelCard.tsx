import { ModelConfig, ModelPerformance } from '@/mocks/models.mock'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/solid'
import { ClockIcon, CurrencyDollarIcon, ChartBarIcon } from '@heroicons/react/24/outline'

interface ModelCardProps {
  config: ModelConfig
  performance?: ModelPerformance
  selected?: boolean
  onClick?: () => void
}

const providerColors: Record<string, string> = {
  anthropic: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  openai: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  google: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  deepseek: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  meta: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
}

/**
 * ModelCard component displays AI model configuration and performance metrics
 * Usage:
 * <ModelCard
 *   config={modelConfig}
 *   performance={modelPerformance}
 *   selected={isSelected}
 *   onClick={() => handleSelect(model)}
 * />
 */
export default function ModelCard({
  config,
  performance,
  selected = false,
  onClick,
}: ModelCardProps) {
  const qualityScore = performance?.avg_quality_score || 0
  const qualityColor = qualityScore >= 9 ? 'text-emerald-400' : qualityScore >= 8 ? 'text-blue-400' : 'text-yellow-400'

  const errorRate = performance?.error_rate || 0
  const errorColor = errorRate < 1 ? 'text-emerald-400' : errorRate < 3 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div
      className={`bg-dark-surface border-2 rounded-lg p-6 transition-all cursor-pointer hover:border-terminal-500/50 ${
        selected ? 'border-terminal-500 ring-2 ring-terminal-500/20' : 'border-dark-border'
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-dark-text-primary">
              {config.display_name}
            </h3>
            {selected && (
              <CheckCircleIcon className="w-5 h-5 text-terminal-400" />
            )}
          </div>
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${providerColors[config.provider]}`}>
            {config.provider}
          </span>
        </div>
        {performance && (
          <div className="text-right">
            <div className={`text-2xl font-bold ${qualityColor}`}>
              {qualityScore.toFixed(1)}
            </div>
            <div className="text-xs text-dark-text-muted">Quality Score</div>
          </div>
        )}
      </div>

      {/* Performance Metrics */}
      {performance && (
        <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-dark-border">
          <div>
            <div className="flex items-center gap-1 text-dark-text-muted text-xs mb-1">
              <ClockIcon className="w-3.5 h-3.5" />
              Avg Time
            </div>
            <div className="text-sm font-semibold text-dark-text-primary">
              {performance.avg_response_time_ms.toLocaleString()}ms
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1 text-dark-text-muted text-xs mb-1">
              <CurrencyDollarIcon className="w-3.5 h-3.5" />
              Avg Cost
            </div>
            <div className="text-sm font-semibold text-dark-text-primary">
              ${performance.avg_cost_per_request.toFixed(3)}
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1 text-dark-text-muted text-xs mb-1">
              <ChartBarIcon className="w-3.5 h-3.5" />
              Requests
            </div>
            <div className="text-sm font-semibold text-dark-text-primary">
              {performance.total_requests.toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Model Specs */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-dark-text-muted">Context Window:</span>
          <span className="text-dark-text-primary font-medium">
            {(config.context_window / 1000).toLocaleString()}K
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-dark-text-muted">Input Cost:</span>
          <span className="text-dark-text-primary font-medium">
            ${config.cost_per_1k_input_tokens.toFixed(4)}/1K
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-dark-text-muted">Output Cost:</span>
          <span className="text-dark-text-primary font-medium">
            ${config.cost_per_1k_output_tokens.toFixed(4)}/1K
          </span>
        </div>
        {performance && (
          <div className="flex justify-between pt-2 border-t border-dark-border">
            <span className="text-dark-text-muted">Error Rate:</span>
            <span className={`font-medium ${errorColor}`}>
              {errorRate.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Features */}
      <div className="flex gap-2 mt-4 pt-4 border-t border-dark-border">
        {config.supports_streaming ? (
          <span className="flex items-center gap-1 text-xs text-emerald-400">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            Streaming
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-dark-text-muted">
            <XCircleIcon className="w-3.5 h-3.5" />
            Streaming
          </span>
        )}
        {config.supports_function_calling ? (
          <span className="flex items-center gap-1 text-xs text-emerald-400">
            <CheckCircleIcon className="w-3.5 h-3.5" />
            Functions
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-dark-text-muted">
            <XCircleIcon className="w-3.5 h-3.5" />
            Functions
          </span>
        )}
      </div>

      {/* Cost Efficiency (if performance available) */}
      {performance && (
        <div className="mt-4 p-3 bg-terminal-500/10 border border-terminal-500/30 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-xs text-dark-text-muted">Cost Efficiency</span>
            <span className="text-sm font-bold text-terminal-400">
              {(performance.avg_quality_score / performance.avg_cost_per_request).toFixed(0)} Q/$
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
