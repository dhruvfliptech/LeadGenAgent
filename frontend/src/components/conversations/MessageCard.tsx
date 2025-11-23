import { ConversationMessage } from '@/types/conversation'
import SentimentBadge from './SentimentBadge'
import KeyPointsList from './KeyPointsList'
import { formatDistanceToNow } from 'date-fns'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'

interface MessageCardProps {
  message: ConversationMessage
  showDetails?: boolean
}

export default function MessageCard({ message, showDetails = true }: MessageCardProps) {
  const isInbound = message.direction === 'inbound'

  return (
    <div
      className={`
        p-4 rounded-lg border
        ${isInbound
          ? 'bg-dark-surface border-dark-border'
          : 'bg-terminal-500/10 border-terminal-500/30'
        }
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Direction Icon */}
          <div
            className={`
              p-2 rounded-full
              ${isInbound
                ? 'bg-blue-500/20 text-blue-400'
                : 'bg-terminal-500/20 text-terminal-400'
              }
            `}
          >
            {isInbound ? (
              <ArrowDownIcon className="w-4 h-4" />
            ) : (
              <ArrowUpIcon className="w-4 h-4" />
            )}
          </div>

          {/* From/To Info */}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-dark-text-primary">
                {isInbound ? message.from_email : 'You'}
              </span>
              <span className="text-xs text-dark-text-muted">
                {isInbound ? 'to' : 'to'} {isInbound ? message.to_email : message.to_email}
              </span>
            </div>
            <div className="text-xs text-dark-text-muted mt-0.5">
              {formatDistanceToNow(new Date(message.received_at), { addSuffix: true })}
            </div>
          </div>
        </div>

        {/* Sentiment Badge (only for inbound messages) */}
        {isInbound && showDetails && (
          <SentimentBadge
            sentiment={message.sentiment}
            score={message.sentiment_score}
            size="sm"
          />
        )}
      </div>

      {/* Subject */}
      {message.subject && (
        <div className="mb-2">
          <span className="text-xs text-dark-text-muted font-medium">Subject: </span>
          <span className="text-sm text-dark-text-primary">{message.subject}</span>
        </div>
      )}

      {/* Message Body */}
      <div className="prose prose-invert prose-sm max-w-none mb-3">
        <div className="text-dark-text-primary whitespace-pre-wrap">
          {message.body_html ? (
            <div dangerouslySetInnerHTML={{ __html: message.body_html }} />
          ) : (
            message.body_text
          )}
        </div>
      </div>

      {/* AI Analysis (only for inbound messages with details) */}
      {isInbound && showDetails && (message.key_points.length > 0 || message.questions_asked.length > 0) && (
        <div className="pt-3 border-t border-dark-border">
          <KeyPointsList
            keyPoints={message.key_points}
            questions={message.questions_asked}
          />
        </div>
      )}
    </div>
  )
}
