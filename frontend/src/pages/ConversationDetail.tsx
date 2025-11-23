import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Conversation } from '@/types/conversation'
import { mockConversations } from '@/mocks/conversations.mock'
import MessageThread from '@/components/conversations/MessageThread'
import AISuggestionsPanel from '@/components/conversations/AISuggestionsPanel'
import ResponseComposer from '@/components/conversations/ResponseComposer'
import SentimentBadge from '@/components/conversations/SentimentBadge'
import {
  ArrowLeftIcon,
  UserCircleIcon,
  EnvelopeIcon,
  BuildingOfficeIcon,
  TagIcon,
  ClockIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

const priorityColors = {
  urgent: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-gray-500',
}

const statusLabels: Record<Conversation['status'], { label: string; color: string }> = {
  active: { label: 'Active', color: 'text-green-400 bg-green-500/20 border-green-500/30' },
  replied: { label: 'Replied', color: 'text-blue-400 bg-blue-500/20 border-blue-500/30' },
  closed: { label: 'Closed', color: 'text-gray-400 bg-gray-500/20 border-gray-500/30' },
  snoozed: { label: 'Snoozed', color: 'text-purple-400 bg-purple-500/20 border-purple-500/30' },
  needs_reply: { label: 'Needs Reply', color: 'text-orange-400 bg-orange-500/20 border-orange-500/30' },
  waiting: { label: 'Waiting', color: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30' },
  archived: { label: 'Archived', color: 'text-slate-400 bg-slate-500/20 border-slate-500/30' },
}

export default function ConversationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    // In real app, fetch from API using id
    // For now, use mock data
    const found = mockConversations.find(c => c.id === Number(id))
    if (found) {
      setConversation(found)
    } else {
      toast.error('Conversation not found')
      navigate('/conversations')
    }
  }, [id, navigate])

  const handleUseSuggestion = (suggestionId: number) => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      toast.success('Response sent successfully!')
      setIsLoading(false)
      // In real app, refetch conversation data
    }, 1000)
  }

  const handleEditSuggestion = (suggestionId: number, content: string) => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      toast.success('Response sent with your edits!')
      setIsLoading(false)
    }, 1000)
  }

  const handleRegenerateSuggestion = (suggestionId: number) => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      toast.success('Generating new suggestions...')
      setIsLoading(false)
    }, 1500)
  }

  const handleSendResponse = (content: string) => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      toast.success('Response sent!')
      setIsLoading(false)
    }, 1000)
  }

  const handleGenerateAI = () => {
    toast.success('Generating AI suggestions...')
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terminal-500" />
      </div>
    )
  }

  const statusConfig = statusLabels[conversation.status]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/conversations"
            className="p-2 text-dark-text-muted hover:text-terminal-400 hover:bg-dark-surface rounded-lg transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary flex items-center gap-3">
              {conversation.lead_name}
              <span className={`w-3 h-3 rounded-full ${priorityColors[conversation.priority]}`} />
            </h1>
            <p className="text-sm text-dark-text-muted mt-1">
              Conversation #{conversation.conversation_id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <span className={`px-3 py-1.5 text-sm font-medium rounded-lg border ${statusConfig.color}`}>
            {statusConfig.label}
          </span>

          {/* Priority Badge */}
          {conversation.priority === 'urgent' && (
            <span className="px-3 py-1.5 text-sm font-bold text-red-400 bg-red-500/20 border border-red-500/30 rounded-lg uppercase">
              Urgent
            </span>
          )}
        </div>
      </div>

      {/* Three-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Contact Info & Context (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          {/* Contact Card */}
          <div className="card">
            <h3 className="text-sm font-semibold text-dark-text-muted uppercase tracking-wide mb-4">
              Contact Information
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <UserCircleIcon className="w-5 h-5 text-dark-text-muted flex-shrink-0" />
                <div>
                  <div className="text-xs text-dark-text-muted">Name</div>
                  <div className="text-sm text-dark-text-primary font-medium">
                    {conversation.lead_name}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <EnvelopeIcon className="w-5 h-5 text-dark-text-muted flex-shrink-0" />
                <div>
                  <div className="text-xs text-dark-text-muted">Email</div>
                  <div className="text-sm text-dark-text-primary">
                    {conversation.lead_email}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Conversation Meta */}
          <div className="card">
            <h3 className="text-sm font-semibold text-dark-text-muted uppercase tracking-wide mb-4">
              Conversation Details
            </h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-dark-text-muted mb-1">Overall Sentiment</div>
                <SentimentBadge sentiment={conversation.overall_sentiment} size="md" />
              </div>
              <div>
                <div className="text-xs text-dark-text-muted mb-1">Priority</div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${priorityColors[conversation.priority]}`} />
                  <span className="text-sm text-dark-text-primary capitalize">
                    {conversation.priority}
                  </span>
                </div>
              </div>
              <div>
                <div className="text-xs text-dark-text-muted mb-1">Messages</div>
                <div className="text-sm text-dark-text-primary">
                  {conversation.messages_count} messages
                </div>
              </div>
              <div>
                <div className="text-xs text-dark-text-muted mb-1">Last Activity</div>
                <div className="text-sm text-dark-text-primary">
                  {new Date(conversation.last_message_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>

          {/* Tags */}
          {conversation.tags && conversation.tags.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-dark-text-muted uppercase tracking-wide mb-3">
                Tags
              </h3>
              <div className="flex flex-wrap gap-2">
                {conversation.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2.5 py-1 text-xs bg-dark-bg-secondary text-dark-text-muted rounded-full border border-dark-border flex items-center gap-1.5"
                  >
                    <TagIcon className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Snoozed Info */}
          {conversation.status === 'snoozed' && conversation.snoozed_until && (
            <div className="card bg-purple-500/10 border-purple-500/30">
              <div className="flex items-center gap-2 text-purple-400 mb-2">
                <ClockIcon className="w-5 h-5" />
                <span className="font-semibold">Snoozed</span>
              </div>
              <p className="text-sm text-dark-text-muted">
                Until {new Date(conversation.snoozed_until).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Middle Column: Message Thread (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card">
            <MessageThread messages={conversation.messages} />
          </div>

          {/* Response Composer */}
          <div className="card p-0 overflow-hidden">
            <ResponseComposer
              onSend={handleSendResponse}
              onGenerateAI={handleGenerateAI}
              isLoading={isLoading}
              placeholder="Type your response to this conversation..."
            />
          </div>
        </div>

        {/* Right Column: AI Suggestions (4 cols) */}
        <div className="lg:col-span-4">
          <div className="card sticky top-6">
            {conversation.suggestions && conversation.suggestions.length > 0 ? (
              <AISuggestionsPanel
                suggestions={conversation.suggestions}
                onUseSuggestion={handleUseSuggestion}
                onEditSuggestion={handleEditSuggestion}
                onRegenerateSuggestion={handleRegenerateSuggestion}
                onGenerateNew={handleGenerateAI}
                isLoading={isLoading}
              />
            ) : (
              <div className="text-center py-8">
                <SparklesIcon className="w-16 h-16 mx-auto text-dark-text-muted mb-4" />
                <p className="text-dark-text-muted mb-4">
                  No AI suggestions yet
                </p>
                <button
                  onClick={handleGenerateAI}
                  className="px-4 py-2 bg-terminal-500 hover:bg-terminal-600 text-white rounded-lg font-medium transition-colors"
                >
                  Generate AI Suggestions
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
