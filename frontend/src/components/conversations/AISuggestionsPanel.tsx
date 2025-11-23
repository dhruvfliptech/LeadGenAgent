import { AISuggestion } from '@/types/conversation'
import SuggestionCard from './SuggestionCard'
import { SparklesIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

interface AISuggestionsPanelProps {
  suggestions: AISuggestion[]
  onUseSuggestion: (suggestionId: number) => void
  onEditSuggestion: (suggestionId: number, content: string) => void
  onRegenerateSuggestion: (suggestionId: number) => void
  onGenerateNew?: () => void
  isLoading?: boolean
  className?: string
}

export default function AISuggestionsPanel({
  suggestions,
  onUseSuggestion,
  onEditSuggestion,
  onRegenerateSuggestion,
  onGenerateNew,
  isLoading,
  className = ''
}: AISuggestionsPanelProps) {
  // Sort suggestions by confidence score (highest first)
  const sortedSuggestions = [...suggestions].sort(
    (a, b) => b.confidence_score - a.confidence_score
  )

  const hasSuggestions = suggestions.length > 0
  const unusedSuggestions = suggestions.filter(s => !s.was_used)

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-dark-text-primary flex items-center gap-2">
            <SparklesIcon className="w-5 h-5 text-terminal-400" />
            AI Response Suggestions
          </h3>
          <p className="text-xs text-dark-text-muted mt-1">
            {unusedSuggestions.length > 0
              ? `${unusedSuggestions.length} suggestion${unusedSuggestions.length > 1 ? 's' : ''} available`
              : 'All suggestions have been used'
            }
          </p>
        </div>

        {/* Generate New Button */}
        {onGenerateNew && (
          <button
            onClick={onGenerateNew}
            disabled={isLoading}
            className="px-3 py-2 text-sm border border-terminal-500 text-terminal-400 hover:bg-terminal-500/10 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowPathIcon className="w-4 h-4" />
            Generate More
          </button>
        )}
      </div>

      {/* Suggestions List */}
      {hasSuggestions ? (
        <div className="space-y-4">
          {sortedSuggestions.map((suggestion, index) => (
            <div key={suggestion.id}>
              {/* Recommended Badge for first (highest confidence) suggestion */}
              {index === 0 && !suggestion.was_used && suggestion.confidence_score >= 0.85 && (
                <div className="flex items-center gap-2 mb-2 text-xs text-terminal-400">
                  <SparklesIcon className="w-4 h-4" />
                  <span className="font-semibold uppercase tracking-wide">
                    Recommended
                  </span>
                </div>
              )}

              <SuggestionCard
                suggestion={suggestion}
                onUse={onUseSuggestion}
                onEdit={onEditSuggestion}
                onRegenerate={onRegenerateSuggestion}
                isLoading={isLoading}
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-dark-border rounded-lg">
          <SparklesIcon className="w-12 h-12 mx-auto text-dark-text-muted mb-3" />
          <p className="text-dark-text-muted mb-4">
            No AI suggestions available yet
          </p>
          {onGenerateNew && (
            <button
              onClick={onGenerateNew}
              disabled={isLoading}
              className="px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              Generate AI Suggestions
            </button>
          )}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="p-4 border border-terminal-500/50 bg-terminal-500/10 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-terminal-500" />
            <span className="text-sm text-terminal-400">
              AI is generating suggestions...
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
