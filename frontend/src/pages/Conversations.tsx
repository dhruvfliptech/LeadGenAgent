import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ChatBubbleLeftRightIcon, ChevronLeftIcon } from '@heroicons/react/24/outline'
import ConversationList from '@/components/conversations/ConversationList'
import ConversationThread from '@/components/conversations/ConversationThread'
import { Conversation } from '@/types/conversation'
import { mockConversations, getConversationStats } from '@/mocks/conversations.mock'
import toast from 'react-hot-toast'
import '@/styles/conversations.css'

export default function Conversations() {
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showMobileThread, setShowMobileThread] = useState(false)
  const [filters, setFilters] = useState({
    needs_reply: false,
    active: false,
    archived: false
  })

  // Use mock data
  const conversations = mockConversations as Conversation[]
  const isLoading = false
  const error = null

  // Use mock stats
  const mockStats = getConversationStats()
  const stats = {
    needs_reply: mockStats.needs_response,
    active: mockStats.active,
    archived: 0,
    total: mockStats.total,
    waiting: 0
  }

  // Get selected conversation thread (mock data already includes messages and suggestions)
  const conversationThread = selectedConversation
  const isLoadingThread = false

  // Mock handlers for mutations (using toast for demo)
  const [isProcessing, setIsProcessing] = useState(false)

  // Auto-select first conversation if none selected
  useEffect(() => {
    if (!selectedConversation && conversations.length > 0) {
      setSelectedConversation(conversations[0])
    }
  }, [conversations, selectedConversation])

  const handleApproveReply = (suggestionId: number, editedContent?: string) => {
    setIsProcessing(true)
    setTimeout(() => {
      toast.success('Reply sent successfully!')
      setIsProcessing(false)
    }, 1000)
  }

  const handleRejectReply = (suggestionId: number) => {
    toast.success('AI suggestion rejected')
  }

  const handleSendCustomReply = (content: string) => {
    if (!selectedConversation) return
    setIsProcessing(true)
    setTimeout(() => {
      toast.success('Reply sent successfully!')
      setIsProcessing(false)
    }, 1000)
  }

  const handleRegenerateReply = (messageId: number, tone: 'formal' | 'casual' | 'shorter' | 'humor') => {
    toast.success(`Generating new reply with ${tone} tone...`)
  }

  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation)
    setShowMobileThread(true)
  }

  const handleBackToList = () => {
    setShowMobileThread(false)
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading conversations</div>
        <button
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    )
  }

  // Empty state - no conversations yet
  if (!isLoading && conversations.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-md">
          <ChatBubbleLeftRightIcon className="w-16 h-16 mx-auto text-dark-text-muted mb-4" />
          <h3 className="text-xl font-semibold text-dark-text-primary mb-2">No conversations yet</h3>
          <p className="text-dark-text-muted mb-6">
            Start by sending emails to leads from the Leads page. When they reply, they'll appear here.
          </p>
          <Link to="/leads" className="btn-primary inline-flex items-center">
            Go to Leads Page →
          </Link>
        </div>
      </div>
    )
  }

  // All caught up state
  const hasActiveConversations = conversations.some(c => c.status === 'needs_reply' || c.status === 'active')
  if (!isLoading && conversations.length > 0 && !hasActiveConversations) {
    return (
      <div className="space-y-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Conversations
          </h2>
          <p className="mt-1 text-sm text-dark-text-muted">
            Manage email conversations with your leads
          </p>
        </div>

        <div className="flex items-center justify-center py-24">
          <div className="text-center max-w-md">
            <div className="text-6xl mb-4">✅</div>
            <h3 className="text-xl font-semibold text-dark-text-primary mb-2">All caught up!</h3>
            <p className="text-dark-text-muted">
              No pending replies right now. Great job staying on top of your conversations!
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Conversations
          </h2>
          <p className="mt-1 text-sm text-dark-text-muted">
            Manage email conversations with your leads
          </p>
        </div>

        {stats && stats.needs_reply > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-[#FF3B30]/20 text-[#FF3B30] rounded-lg border border-[#FF3B30]/30">
            <span className="w-2 h-2 bg-[#FF3B30] rounded-full animate-pulse" />
            <span className="text-sm font-medium">{stats.needs_reply} need{stats.needs_reply !== 1 ? 's' : ''} reply</span>
          </div>
        )}
      </div>

      {/* Two-panel layout */}
      <div className="card overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 h-[calc(100vh-16rem)]">
          {/* Sidebar - Conversation List (Hidden on mobile when thread is shown) */}
          <div className={`lg:col-span-1 h-full overflow-hidden ${showMobileThread ? 'hidden lg:block' : 'block'}`}>
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-terminal-500" />
              </div>
            ) : (
              <ConversationList
                conversations={conversations}
                selectedId={selectedConversation?.id}
                onSelect={handleSelectConversation}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                filters={filters}
                onFilterChange={setFilters}
                stats={{
                  needs_reply: stats?.needs_reply || 0,
                  active: stats?.active || 0,
                  archived: stats?.archived || 0
                }}
              />
            )}
          </div>

          {/* Main content - Conversation Thread (Full screen on mobile) */}
          <div className={`lg:col-span-2 h-full overflow-hidden lg:border-l border-dark-border ${!showMobileThread ? 'hidden lg:block' : 'block'}`}>
            {/* Mobile back button */}
            <div className="lg:hidden px-4 py-3 border-b border-dark-border bg-dark-surface flex items-center gap-3">
              <button
                onClick={handleBackToList}
                className="flex items-center gap-2 text-terminal-400 hover:text-terminal-300"
              >
                <ChevronLeftIcon className="w-5 h-5" />
                <span className="text-sm font-medium">Back</span>
              </button>
            </div>

            {isLoadingThread ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-terminal-500" />
              </div>
            ) : conversationThread ? (
              <ConversationThread
                conversation={conversationThread}
                onApproveReply={handleApproveReply}
                onRejectReply={handleRejectReply}
                onSendCustomReply={handleSendCustomReply}
                onRegenerateReply={handleRegenerateReply}
                isLoading={isProcessing}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-dark-text-muted">Select a conversation to view</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
