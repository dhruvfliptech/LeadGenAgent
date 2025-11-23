import { Conversation } from '@/types/conversation'
import SentimentBadge from './SentimentBadge'
import { formatDistanceToNow } from 'date-fns'
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  EyeIcon
} from '@heroicons/react/24/outline'

interface ConversationsTableProps {
  conversations: Conversation[]
  onSelectConversation: (conversation: Conversation) => void
  className?: string
}

const priorityColors = {
  urgent: 'text-red-400',
  high: 'text-orange-400',
  medium: 'text-yellow-400',
  low: 'text-gray-400',
}

const statusLabels: Record<Conversation['status'], { label: string; color: string }> = {
  active: { label: 'Active', color: 'text-green-400 bg-green-500/20' },
  replied: { label: 'Replied', color: 'text-blue-400 bg-blue-500/20' },
  closed: { label: 'Closed', color: 'text-gray-400 bg-gray-500/20' },
  snoozed: { label: 'Snoozed', color: 'text-purple-400 bg-purple-500/20' },
  needs_reply: { label: 'Needs Reply', color: 'text-orange-400 bg-orange-500/20' },
  waiting: { label: 'Waiting', color: 'text-yellow-400 bg-yellow-500/20' },
  archived: { label: 'Archived', color: 'text-slate-400 bg-slate-500/20' },
}

export default function ConversationsTable({
  conversations,
  onSelectConversation,
  className = ''
}: ConversationsTableProps) {
  if (conversations.length === 0) {
    return (
      <div className="text-center py-12">
        <ChatBubbleLeftRightIcon className="w-16 h-16 mx-auto text-dark-text-muted mb-4" />
        <p className="text-dark-text-muted">No conversations found</p>
      </div>
    )
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-dark-border">
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Priority
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Contact
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Subject
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Sentiment
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Messages
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Last Activity
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              AI
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-dark-text-muted uppercase tracking-wide">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {conversations.map((conversation) => {
            const hasPendingSuggestions = conversation.suggestions?.some(s => !s.was_used)
            const statusConfig = statusLabels[conversation.status]

            return (
              <tr
                key={conversation.id}
                className={`
                  border-b border-dark-border hover:bg-dark-bg-secondary transition-colors cursor-pointer
                  ${conversation.needs_response ? 'bg-orange-500/5' : ''}
                `}
                onClick={() => onSelectConversation(conversation)}
              >
                {/* Priority */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        conversation.priority === 'urgent'
                          ? 'bg-red-500 animate-pulse'
                          : conversation.priority === 'high'
                          ? 'bg-orange-500'
                          : conversation.priority === 'medium'
                          ? 'bg-yellow-500'
                          : 'bg-gray-500'
                      }`}
                    />
                    <span className={`text-xs font-medium ${priorityColors[conversation.priority]}`}>
                      {conversation.priority}
                    </span>
                  </div>
                </td>

                {/* Contact */}
                <td className="px-4 py-3">
                  <div>
                    <div className="font-medium text-dark-text-primary">
                      {conversation.lead_name}
                    </div>
                    <div className="text-xs text-dark-text-muted truncate max-w-[200px]">
                      {conversation.lead_email}
                    </div>
                  </div>
                </td>

                {/* Subject */}
                <td className="px-4 py-3">
                  <div className="max-w-[300px]">
                    <div className="font-medium text-dark-text-primary truncate">
                      {conversation.subject}
                    </div>
                    {conversation.tags && conversation.tags.length > 0 && (
                      <div className="flex gap-1 mt-1">
                        {conversation.tags.slice(0, 2).map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-1.5 py-0.5 text-xs bg-dark-bg-secondary text-dark-text-muted rounded"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </td>

                {/* Sentiment */}
                <td className="px-4 py-3">
                  <SentimentBadge sentiment={conversation.overall_sentiment} size="sm" />
                </td>

                {/* Status */}
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded ${statusConfig.color}`}
                  >
                    {statusConfig.label}
                  </span>
                </td>

                {/* Messages Count */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-sm text-dark-text-primary">
                    <ChatBubbleLeftRightIcon className="w-4 h-4 text-dark-text-muted" />
                    {conversation.messages_count}
                  </div>
                </td>

                {/* Last Activity */}
                <td className="px-4 py-3">
                  <div className="text-sm text-dark-text-muted">
                    {formatDistanceToNow(new Date(conversation.last_message_at), {
                      addSuffix: true,
                    })}
                  </div>
                </td>

                {/* AI Suggestions */}
                <td className="px-4 py-3">
                  {hasPendingSuggestions ? (
                    <div className="flex items-center gap-1 text-terminal-400">
                      <SparklesIcon className="w-4 h-4" />
                      <span className="text-xs font-medium">
                        {conversation.suggestions?.filter(s => !s.was_used).length}
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-dark-text-muted">-</span>
                  )}
                </td>

                {/* Actions */}
                <td className="px-4 py-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onSelectConversation(conversation)
                    }}
                    className="p-2 text-terminal-400 hover:text-terminal-300 hover:bg-terminal-500/10 rounded transition-colors"
                    title="View conversation"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
