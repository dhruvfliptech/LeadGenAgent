import { ConversationMessage } from '@/types/conversation'
import MessageCard from './MessageCard'
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'

interface MessageThreadProps {
  messages: ConversationMessage[]
  className?: string
}

export default function MessageThread({ messages, className = '' }: MessageThreadProps) {
  if (messages.length === 0) {
    return (
      <div className={`flex items-center justify-center p-12 ${className}`}>
        <div className="text-center">
          <ChatBubbleLeftRightIcon className="w-16 h-16 mx-auto text-dark-text-muted mb-4" />
          <p className="text-dark-text-muted">No messages in this conversation yet</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="text-xs font-semibold text-dark-text-muted uppercase tracking-wide mb-4">
        Message Thread ({messages.length})
      </div>

      {messages.map((message) => (
        <MessageCard key={message.id} message={message} showDetails={true} />
      ))}
    </div>
  )
}
