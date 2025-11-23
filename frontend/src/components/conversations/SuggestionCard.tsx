import { useState } from 'react'
import { AISuggestion } from '@/types/conversation'
import {
  SparklesIcon,
  CheckCircleIcon,
  PencilSquareIcon,
  ArrowPathIcon,
  LightBulbIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface SuggestionCardProps {
  suggestion: AISuggestion
  onUse: (suggestionId: number) => void
  onEdit: (suggestionId: number, content: string) => void
  onRegenerate: (suggestionId: number) => void
  isLoading?: boolean
}

// Confidence score colors
const getConfidenceColor = (score: number) => {
  if (score >= 0.85) return 'text-green-400 bg-green-500/20 border-green-500/30'
  if (score >= 0.70) return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'
  return 'text-red-400 bg-red-500/20 border-red-500/30'
}

const getConfidenceLabel = (score: number) => {
  if (score >= 0.85) return 'High Confidence'
  if (score >= 0.70) return 'Medium Confidence'
  return 'Low Confidence'
}

export default function SuggestionCard({
  suggestion,
  onUse,
  onEdit,
  onRegenerate,
  isLoading
}: SuggestionCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(suggestion.content)

  const confidenceScore = suggestion.confidence_score
  const confidenceColorClass = getConfidenceColor(confidenceScore)

  const handleSaveEdit = () => {
    onEdit(suggestion.id, editedContent)
    setIsEditing(false)
  }

  const handleCancelEdit = () => {
    setEditedContent(suggestion.content)
    setIsEditing(false)
  }

  return (
    <div className="p-4 rounded-lg border border-dark-border bg-dark-surface hover:border-terminal-500/50 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-terminal-400" />
          <div>
            <h4 className="font-semibold text-dark-text-primary">
              {suggestion.title}
            </h4>
            <p className="text-xs text-dark-text-muted">
              {suggestion.model_used}
            </p>
          </div>
        </div>

        {/* Confidence Badge */}
        <span
          className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${confidenceColorClass}`}
        >
          {Math.round(confidenceScore * 100)}%
        </span>
      </div>

      {/* Confidence Label */}
      <div className="flex items-center gap-2 mb-3">
        <ChartBarIcon className="w-4 h-4 text-dark-text-muted" />
        <span className="text-xs text-dark-text-muted">
          {getConfidenceLabel(confidenceScore)}
        </span>
      </div>

      {/* Response Content */}
      {isEditing ? (
        <div className="mb-3">
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="w-full min-h-[200px] p-3 bg-dark-bg-secondary border border-dark-border rounded-lg text-dark-text-primary focus:outline-none focus:ring-2 focus:ring-terminal-500 resize-y"
            placeholder="Edit the AI-generated response..."
          />
        </div>
      ) : (
        <div className="mb-3 p-3 bg-dark-bg-secondary rounded-lg">
          <pre className="text-sm text-dark-text-primary whitespace-pre-wrap font-sans">
            {suggestion.content}
          </pre>
        </div>
      )}

      {/* Rationale */}
      <div className="mb-4 p-3 bg-terminal-500/10 border border-terminal-500/30 rounded-lg">
        <div className="flex items-start gap-2">
          <LightBulbIcon className="w-4 h-4 text-terminal-400 flex-shrink-0 mt-0.5" />
          <div>
            <h5 className="text-xs font-semibold text-terminal-400 uppercase tracking-wide mb-1">
              Why this suggestion?
            </h5>
            <p className="text-xs text-dark-text-muted">
              {suggestion.rationale}
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {isEditing ? (
          <>
            <button
              onClick={handleSaveEdit}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              <CheckCircleIcon className="w-4 h-4 inline mr-1" />
              Save & Use
            </button>
            <button
              onClick={handleCancelEdit}
              disabled={isLoading}
              className="px-4 py-2 border border-dark-border hover:border-terminal-500 text-dark-text-primary rounded-lg transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onUse(suggestion.id)}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <CheckCircleIcon className="w-4 h-4" />
              Use This Response
            </button>
            <button
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
              className="px-4 py-2 border border-dark-border hover:border-terminal-500 text-dark-text-primary rounded-lg transition-colors disabled:opacity-50"
              title="Edit before sending"
            >
              <PencilSquareIcon className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRegenerate(suggestion.id)}
              disabled={isLoading}
              className="px-4 py-2 border border-dark-border hover:border-terminal-500 text-dark-text-primary rounded-lg transition-colors disabled:opacity-50"
              title="Regenerate with different approach"
            >
              <ArrowPathIcon className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {/* Used Indicator */}
      {suggestion.was_used && (
        <div className="mt-3 pt-3 border-t border-dark-border">
          <div className="flex items-center gap-2 text-xs text-green-400">
            <CheckCircleIcon className="w-4 h-4" />
            <span>This response was used</span>
          </div>
        </div>
      )}
    </div>
  )
}
