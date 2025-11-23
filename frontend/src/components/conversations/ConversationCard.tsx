import { Conversation } from '@/types/conversation'
import SentimentBadge from './SentimentBadge'
import { formatDistanceToNow } from 'date-fns'
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ClockIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline'

interface ConversationCardProps {
  conversation: Conversation
  onClick: () => void
  isSelected?: boolean
}

const priorityColors = {
  urgent: 'border-red-500/50 bg-red-500/5',
  high: 'border-orange-500/50 bg-orange-500/5',
  medium: 'border-yellow-500/50 bg-yellow-500/5',
  low: 'border-gray-500/50 bg-gray-500/5',
}

const statusColors: Record<Conversation['status'], string> = {
  active: 'bg-green-500',
  replied: 'bg-blue-500',
  closed: 'bg-gray-500',
  snoozed: 'bg-purple-500',
  needs_reply: 'bg-orange-500',
  waiting: 'bg-yellow-500',
  archived: 'bg-slate-500',
}

export default function ConversationCard({ conversation, onClick, isSelected }: ConversationCardProps) {
  const lastMessage = conversation.messages[conversation.messages.length - 1]
  const hasAISuggestions = conversation.suggestions && conversation.suggestions.length > 0
  const hasPendingSuggestions = conversation.suggestions?.some(s => !s.was_used)

  return (
    <div
      onClick={onClick}
      className={`
        relative p-4 border rounded-lg cursor-pointer transition-all hover:shadow-lg
        ${isSelected
          ? 'border-terminal-500 bg-terminal-500/10 shadow-md'
          : 'border-dark-border bg-dark-surface hover:border-terminal-500/50'
        }
        ${conversation.needs_response ? priorityColors[conversation.priority] : ''}
      `}
    >
      {/* Status and Priority Indicators */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className={`w-2 h-2 rounded-full ${statusColors[conversation.status]} flex-shrink-0`} />
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-dark-text-primary truncate">
              {conversation.lead_name}
            </h3>
            <p className="text-xs text-dark-text-muted truncate">
              {conversation.lead_email}
            </p>
          </div>
        </div>

        {/* Priority Badge */}
        {conversation.priority === 'urgent' && (
          <span className="flex-shrink-0 px-2 py-0.5 text-xs font-bold text-red-400 bg-red-500/20 border border-red-500/30 rounded uppercase">
            Urgent
          </span>
        )}
      </div>

      {/* Subject */}
      <p className="text-sm text-dark-text-primary font-medium mb-2 truncate">
        {conversation.subject}
      </p>

      {/* Last Message Preview */}
      <p className="text-sm text-dark-text-muted mb-3 line-clamp-2">
        {lastMessage?.body_text || 'No messages yet'}
      </p>

      {/* Metadata Row */}
      <div className="flex items-center gap-3 text-xs text-dark-text-muted flex-wrap">
        {/* Message Count */}
        <div className="flex items-center gap-1">
          <ChatBubbleLeftRightIcon className="w-3.5 h-3.5" />
          <span>{conversation.messages_count}</span>
        </div>

        {/* Sentiment */}
        <SentimentBadge sentiment={conversation.overall_sentiment} size="sm" />

        {/* Time */}
        <div className="flex items-center gap-1">
          <ClockIcon className="w-3.5 h-3.5" />
          <span>{formatDistanceToNow(new Date(conversation.last_message_at), { addSuffix: true })}</span>
        </div>

        {/* Needs Response Indicator */}
        {conversation.needs_response && (
          <span className="flex items-center gap-1 text-orange-400 font-medium">
            <ArrowRightIcon className="w-3.5 h-3.5" />
            Reply needed
          </span>
        )}

        {/* AI Suggestions Badge */}
        {hasPendingSuggestions && (
          <span className="flex items-center gap-1 text-terminal-400 bg-terminal-500/20 px-2 py-0.5 rounded">
            <SparklesIcon className="w-3.5 h-3.5" />
            AI Ready
          </span>
        )}
      </div>

      {/* Tags */}
      {conversation.tags && conversation.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {conversation.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="px-2 py-0.5 text-xs bg-dark-bg-secondary text-dark-text-muted rounded border border-dark-border"
            >
              {tag}
            </span>
          ))}
          {conversation.tags.length > 3 && (
            <span className="px-2 py-0.5 text-xs text-dark-text-muted">
              +{conversation.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {/* Snoozed Until */}
      {conversation.status === 'snoozed' && conversation.snoozed_until && (
        <div className="mt-2 text-xs text-purple-400 flex items-center gap-1">
          <ClockIcon className="w-3.5 h-3.5" />
          Snoozed until {new Date(conversation.snoozed_until).toLocaleDateString()}
        </div>
      )}
    </div>
  )
}
