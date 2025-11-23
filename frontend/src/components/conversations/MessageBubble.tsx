import { ConversationMessage } from '@/types/conversation'
import { formatRelativeTime } from '@/utils/dateFormat'

interface MessageBubbleProps {
  message: ConversationMessage
  isOutgoing: boolean
}

export default function MessageBubble({ message, isOutgoing }: MessageBubbleProps) {
  return (
    <div className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-2xl ${isOutgoing ? 'ml-12' : 'mr-12'}`}>
        {/* Message header */}
        <div className={`flex items-center gap-2 mb-1 ${isOutgoing ? 'justify-end' : 'justify-start'}`}>
          <span className="text-xs text-dark-text-muted">
            {isOutgoing ? 'You' : message.sender_email}
          </span>
          <span className="text-xs text-dark-text-muted">
            {formatRelativeTime(message.sent_at)}
          </span>
        </div>

        {/* Message bubble */}
        <div
          className={`rounded-lg px-4 py-3 ${
            isOutgoing
              ? 'bg-[#0A84FF] text-white'
              : 'bg-[#2C2C2E] text-dark-text-primary border border-dark-border'
          }`}
        >
          {message.html_content ? (
            <div
              dangerouslySetInnerHTML={{ __html: message.html_content }}
              className="text-sm whitespace-pre-wrap break-words"
            />
          ) : (
            <p className="text-sm whitespace-pre-wrap break-words">
              {message.content}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
