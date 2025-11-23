import { useState } from 'react'
import { Conversation } from '@/types/conversation'
import MessageBubble from './MessageBubble'
import AISuggestionCard from './AISuggestionCard'
import { PaperAirplaneIcon, PencilSquareIcon } from '@heroicons/react/24/outline'

interface ConversationThreadProps {
  conversation: Conversation
  onApproveReply: (suggestionId: number, editedContent?: string) => void
  onRejectReply: (suggestionId: number) => void
  onSendCustomReply: (content: string) => void
  onRegenerateReply: (messageId: number, tone: 'formal' | 'casual' | 'shorter' | 'humor') => void
  isLoading?: boolean
}

export default function ConversationThread({
  conversation,
  onApproveReply,
  onRejectReply,
  onSendCustomReply,
  onRegenerateReply,
  isLoading = false
}: ConversationThreadProps) {
  const [showCustomReply, setShowCustomReply] = useState(false)
  const [customReplyContent, setCustomReplyContent] = useState('')
  const [_editedAIContent, setEditedAIContent] = useState('')

  const handleSendCustomReply = () => {
    if (!customReplyContent.trim()) return
    onSendCustomReply(customReplyContent)
    setCustomReplyContent('')
    setShowCustomReply(false)
  }

  const handleApprove = (editedContent?: string) => {
    if (conversation.ai_suggestion) {
      onApproveReply(conversation.ai_suggestion.id, editedContent)
    }
  }

  const handleReject = () => {
    if (conversation.ai_suggestion) {
      onRejectReply(conversation.ai_suggestion.id)
    }
  }

  const handleRegenerate = (tone: 'formal' | 'casual' | 'shorter' | 'humor') => {
    if (conversation.ai_suggestion) {
      onRegenerateReply(conversation.ai_suggestion.message_id, tone)
    }
  }

  return (
    <div className="flex flex-col h-full bg-dark-bg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-dark-border bg-dark-surface">
        <h2 className="text-lg font-semibold text-dark-text-primary">
          Conversation with {conversation.lead?.contact_name || 'Unknown'}
        </h2>
        <p className="text-sm text-dark-text-muted">
          {conversation.lead?.email || conversation.lead?.reply_email}
        </p>
        <p className="text-xs text-dark-text-muted mt-1">
          Lead: {conversation.lead?.title}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {conversation.messages && conversation.messages.length > 0 ? (
          <>
            {conversation.messages
              .sort((a, b) => {
                const aTimestamp = a.sent_at ?? a.received_at ?? a.created_at
                const bTimestamp = b.sent_at ?? b.received_at ?? b.created_at
                return new Date(aTimestamp).getTime() - new Date(bTimestamp).getTime()
              })
              .map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isOutgoing={message.direction === 'outbound'}
                />
              ))}

            {/* AI Suggestion */}
            {conversation.ai_suggestion && conversation.ai_suggestion.status === 'pending' && (
              <div className="my-6">
                <AISuggestionCard
                  suggestion={conversation.ai_suggestion}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onEdit={setEditedAIContent}
                  onRegenerate={handleRegenerate}
                  isLoading={isLoading}
                />
              </div>
            )}

            {/* Custom reply option */}
            {!showCustomReply && !conversation.ai_suggestion && (
              <div className="mt-6">
                <button
                  onClick={() => setShowCustomReply(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-dark-surface border border-dark-border text-dark-text-primary rounded-md hover:bg-dark-border transition-colors"
                >
                  <PencilSquareIcon className="w-4 h-4" />
                  Write Custom Reply
                </button>
              </div>
            )}

            {/* Custom reply form */}
            {showCustomReply && (
              <div className="mt-6 border border-dark-border rounded-lg p-4 bg-dark-surface">
                <h4 className="text-sm font-medium text-dark-text-primary mb-3">Write Custom Reply</h4>
                <textarea
                  value={customReplyContent}
                  onChange={(e) => setCustomReplyContent(e.target.value)}
                  placeholder="Type your reply..."
                  className="w-full h-32 px-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-terminal-500 focus:border-terminal-500"
                />
                <div className="flex items-center gap-3 mt-3">
                  <button
                    onClick={handleSendCustomReply}
                    disabled={!customReplyContent.trim() || isLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-terminal-500 text-black rounded-md hover:bg-terminal-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PaperAirplaneIcon className="w-4 h-4" />
                    {isLoading ? 'Sending...' : 'Send Reply'}
                  </button>
                  <button
                    onClick={() => {
                      setShowCustomReply(false)
                      setCustomReplyContent('')
                    }}
                    disabled={isLoading}
                    className="px-4 py-2 text-dark-text-secondary hover:text-dark-text-primary transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-dark-text-muted">No messages yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
