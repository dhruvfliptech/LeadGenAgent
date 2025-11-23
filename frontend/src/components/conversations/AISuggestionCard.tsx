import { useState } from 'react'
import { AISuggestion } from '@/types/conversation'
import {
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  SparklesIcon,
  ArrowPathIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { Menu } from '@headlessui/react'

interface AISuggestionCardProps {
  suggestion: AISuggestion
  onApprove: (editedContent?: string) => void
  onReject: () => void
  onEdit: (content: string) => void
  onRegenerate: (tone: 'formal' | 'casual' | 'shorter' | 'humor') => void
  isLoading?: boolean
}

export default function AISuggestionCard({
  suggestion,
  onApprove,
  onReject,
  onEdit,
  onRegenerate,
  isLoading = false
}: AISuggestionCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(
    suggestion.suggested_content ?? suggestion.content ?? ''
  )
  const [showDetails, setShowDetails] = useState(false)

  const getConfidenceBadge = (score: number) => {
    if (score >= 85) {
      return { color: 'bg-green-500/20 text-green-400 border-green-500/30', icon: '✨', label: 'High' }
    } else if (score >= 70) {
      return { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', icon: '⚡', label: 'Medium' }
    } else {
      return { color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', icon: '⚠️', label: 'Low' }
    }
  }

  const confidence = getConfidenceBadge(suggestion.confidence_score)

  const handleSave = () => {
    onEdit(editedContent ?? '')
    setIsEditing(false)
  }

  const handleApprove = () => {
    if (isEditing) {
      onApprove(editedContent)
    } else {
      onApprove()
    }
  }

  return (
    <div className="border-2 border-dashed border-[#8E44AD]/50 rounded-lg p-6 bg-[#8E44AD]/5 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <SparklesIcon className="w-5 h-5 text-[#8E44AD]" />
          <h3 className="text-lg font-semibold text-dark-text-primary">AI Suggested Reply</h3>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${confidence.color}`}>
          <span>{confidence.icon}</span>
          <span>{confidence.label} Confidence</span>
          <span className="font-bold">{suggestion.confidence_score}%</span>
        </div>
      </div>

      {/* Message content */}
      {isEditing ? (
        <div className="mb-4">
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="w-full h-48 px-4 py-3 bg-dark-surface border border-dark-border rounded-lg text-dark-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-[#8E44AD] focus:border-[#8E44AD]"
            placeholder="Edit the AI suggestion..."
          />
        </div>
      ) : (
        <div className="mb-4 bg-dark-surface border border-dark-border rounded-lg p-4">
          <p className="text-sm text-dark-text-primary whitespace-pre-wrap break-words">
            {editedContent}
          </p>
        </div>
      )}

      {/* AI Analysis Details */}
      {suggestion.sentiment_analysis && (
        <div className="mb-4">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-2 text-sm text-dark-text-muted hover:text-dark-text-secondary transition-colors"
          >
            <span>AI Analysis</span>
            <ChevronDownIcon className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
          </button>

          {showDetails && (
            <div className="mt-3 space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-dark-text-muted">Detected question:</span>
                <span className="text-terminal-400">
                  {suggestion.sentiment_analysis.detected_questions?.[0] || 'None'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-dark-text-muted">Sentiment:</span>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  suggestion.sentiment_analysis.sentiment === 'positive'
                    ? 'bg-green-500/20 text-green-400'
                    : suggestion.sentiment_analysis.sentiment === 'negative'
                    ? 'bg-red-500/20 text-red-400'
                    : 'bg-blue-500/20 text-blue-400'
                }`}>
                  {suggestion.sentiment_analysis.sentiment} {
                    suggestion.sentiment_analysis.sentiment === 'positive' ? '😊' :
                    suggestion.sentiment_analysis.sentiment === 'negative' ? '😟' : '😐'
                  }
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-dark-text-muted">Intent:</span>
                <span className="text-terminal-400">{suggestion.sentiment_analysis.intent}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-dark-text-muted">Suggested tone:</span>
                <span className="text-terminal-400">{suggestion.sentiment_analysis.suggested_tone}</span>
              </div>

              {suggestion.context_used && (
                <div className="pt-2 border-t border-dark-border">
                  <div className="text-dark-text-muted mb-2">Context Used:</div>
                  <ul className="space-y-1 text-dark-text-secondary">
                    <li>• {suggestion.context_used.previous_emails} previous email(s)</li>
                    {suggestion.context_used.lead_data && <li>• Lead website data</li>}
                    {suggestion.context_used.similar_conversations > 0 && (
                      <li>• {suggestion.context_used.similar_conversations} similar conversation(s)</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-3 pt-4 border-t border-dark-border">
        {isEditing ? (
          <>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-terminal-500 text-black rounded-md hover:bg-terminal-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckIcon className="w-4 h-4" />
              Save Changes
            </button>
            <button
              onClick={() => {
                setEditedContent(suggestion.suggested_content ?? suggestion.content ?? '')
                setIsEditing(false)
              }}
              disabled={isLoading}
              className="px-4 py-2 text-dark-text-secondary hover:text-dark-text-primary transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-dark-surface border border-dark-border text-dark-text-primary rounded-md hover:bg-dark-border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PencilIcon className="w-4 h-4" />
              Edit Reply
            </button>
            <button
              onClick={handleApprove}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-terminal-500 text-black rounded-md hover:bg-terminal-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckIcon className="w-4 h-4" />
              {isLoading ? 'Sending...' : 'Approve & Send'}
            </button>
            <button
              onClick={onReject}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-red-900/20 border border-red-500 text-red-400 rounded-md hover:bg-red-900/40 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <XMarkIcon className="w-4 h-4" />
              Reject
            </button>
          </>
        )}

        {/* Regenerate dropdown */}
        <Menu as="div" className="relative ml-auto">
          <Menu.Button
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 bg-dark-surface border border-dark-border text-dark-text-secondary rounded-md hover:bg-dark-border hover:text-dark-text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowPathIcon className="w-4 h-4" />
            Regenerate
            <ChevronDownIcon className="w-3 h-3" />
          </Menu.Button>
          <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right bg-dark-surface border border-dark-border rounded-md shadow-lg focus:outline-none z-10">
            <div className="p-1">
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={() => onRegenerate('formal')}
                    className={`${
                      active ? 'bg-dark-border' : ''
                    } w-full text-left px-3 py-2 text-sm text-dark-text-primary rounded-md`}
                  >
                    More formal
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={() => onRegenerate('casual')}
                    className={`${
                      active ? 'bg-dark-border' : ''
                    } w-full text-left px-3 py-2 text-sm text-dark-text-primary rounded-md`}
                  >
                    More casual
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={() => onRegenerate('shorter')}
                    className={`${
                      active ? 'bg-dark-border' : ''
                    } w-full text-left px-3 py-2 text-sm text-dark-text-primary rounded-md`}
                  >
                    Shorter version
                  </button>
                )}
              </Menu.Item>
              <Menu.Item>
                {({ active }) => (
                  <button
                    onClick={() => onRegenerate('humor')}
                    className={`${
                      active ? 'bg-dark-border' : ''
                    } w-full text-left px-3 py-2 text-sm text-dark-text-primary rounded-md`}
                  >
                    Add humor
                  </button>
                )}
              </Menu.Item>
            </div>
          </Menu.Items>
        </Menu>
      </div>
    </div>
  )
}
