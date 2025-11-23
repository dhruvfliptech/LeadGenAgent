import { useState } from 'react'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  DocumentTextIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface ResponseComposerProps {
  onSend: (content: string) => void
  onGenerateAI?: () => void
  onSaveDraft?: (content: string) => void
  onSchedule?: (content: string, scheduledAt: Date) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
}

export default function ResponseComposer({
  onSend,
  onGenerateAI,
  onSaveDraft,
  onSchedule,
  isLoading,
  placeholder = 'Type your response...',
  className = ''
}: ResponseComposerProps) {
  const [content, setContent] = useState('')
  const [showScheduleModal, setShowScheduleModal] = useState(false)

  const handleSend = () => {
    if (content.trim()) {
      onSend(content)
      setContent('')
    }
  }

  const handleSaveDraft = () => {
    if (content.trim() && onSaveDraft) {
      onSaveDraft(content)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter to send
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={`border border-dark-border rounded-lg bg-dark-surface ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-3 border-b border-dark-border">
        <button
          onClick={onGenerateAI}
          disabled={isLoading}
          className="px-3 py-1.5 text-sm bg-terminal-500/20 text-terminal-400 hover:bg-terminal-500/30 rounded flex items-center gap-2 transition-colors disabled:opacity-50"
          title="Generate AI response"
        >
          <SparklesIcon className="w-4 h-4" />
          Generate with AI
        </button>

        <div className="flex-1" />

        {/* Character Counter */}
        <span className="text-xs text-dark-text-muted">
          {content.length} characters
        </span>
      </div>

      {/* Text Editor */}
      <div className="p-3">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className="w-full min-h-[150px] bg-transparent border-none text-dark-text-primary placeholder:text-dark-text-muted focus:outline-none resize-y disabled:opacity-50"
        />
      </div>

      {/* Actions Footer */}
      <div className="flex items-center gap-2 p-3 border-t border-dark-border bg-dark-bg-secondary">
        {/* Helper Text */}
        <div className="flex-1 text-xs text-dark-text-muted">
          <kbd className="px-1.5 py-0.5 bg-dark-surface border border-dark-border rounded text-xs">
            {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}
          </kbd>
          {' + '}
          <kbd className="px-1.5 py-0.5 bg-dark-surface border border-dark-border rounded text-xs">
            Enter
          </kbd>
          {' to send'}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Save Draft */}
          {onSaveDraft && (
            <button
              onClick={handleSaveDraft}
              disabled={isLoading || !content.trim()}
              className="px-3 py-2 text-sm border border-dark-border text-dark-text-primary hover:border-terminal-500 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <DocumentTextIcon className="w-4 h-4" />
              Save Draft
            </button>
          )}

          {/* Schedule */}
          {onSchedule && (
            <button
              onClick={() => setShowScheduleModal(true)}
              disabled={isLoading || !content.trim()}
              className="px-3 py-2 text-sm border border-dark-border text-dark-text-primary hover:border-terminal-500 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <ClockIcon className="w-4 h-4" />
              Schedule
            </button>
          )}

          {/* Send */}
          <button
            onClick={handleSend}
            disabled={isLoading || !content.trim()}
            className="px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Sending...
              </>
            ) : (
              <>
                <PaperAirplaneIcon className="w-4 h-4" />
                Send
              </>
            )}
          </button>
        </div>
      </div>

      {/* Schedule Modal (simple placeholder) */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Schedule Message
            </h3>
            <p className="text-sm text-dark-text-muted mb-4">
              Schedule feature coming soon...
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowScheduleModal(false)}
                className="px-4 py-2 border border-dark-border text-dark-text-primary hover:border-terminal-500 rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowScheduleModal(false)
                  handleSend()
                }}
                className="px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded transition-colors"
              >
                Send Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
