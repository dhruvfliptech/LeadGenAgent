import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Conversation, ConversationPriority, SentimentType, ConversationStatus } from '@/types/conversation'
import { mockConversations } from '@/mocks/conversations.mock'
import ConversationsTable from '@/components/conversations/ConversationsTable'
import ConversationCard from '@/components/conversations/ConversationCard'
import ConversationFilters from '@/components/conversations/ConversationFilters'
import {
  MagnifyingGlassIcon,
  Squares2X2Icon,
  TableCellsIcon,
  FunnelIcon
} from '@heroicons/react/24/outline'

type ViewMode = 'cards' | 'table'

export default function ConversationsEnhanced() {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<ViewMode>('cards')
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(true)
  const [filters, setFilters] = useState<{
    status?: ConversationStatus | 'all'
    priority?: ConversationPriority | 'all'
    sentiment?: SentimentType | 'all'
    needs_response?: boolean
  }>({
    status: 'all',
    priority: 'all',
    sentiment: 'all',
    needs_response: false,
  })

  // Use mock data - in real app, would fetch from API
  const conversations = mockConversations

  // Filter conversations
  const filteredConversations = useMemo(() => {
    return conversations.filter((conversation) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        const matchesSearch =
          conversation.lead_name.toLowerCase().includes(query) ||
          conversation.lead_email.toLowerCase().includes(query) ||
          conversation.subject.toLowerCase().includes(query)
        if (!matchesSearch) return false
      }

      // Status filter
      if (filters.status && filters.status !== 'all') {
        if (conversation.status !== filters.status) return false
      }

      // Priority filter
      if (filters.priority && filters.priority !== 'all') {
        if (conversation.priority !== filters.priority) return false
      }

      // Sentiment filter
      if (filters.sentiment && filters.sentiment !== 'all') {
        if (conversation.overall_sentiment !== filters.sentiment) return false
      }

      // Needs response filter
      if (filters.needs_response) {
        if (!conversation.needs_response) return false
      }

      return true
    })
  }, [conversations, searchQuery, filters])

  // Calculate stats
  const stats = useMemo(() => {
    return {
      total: conversations.length,
      active: conversations.filter(c => c.status === 'active').length,
      needs_response: conversations.filter(c => c.needs_response).length,
      urgent: conversations.filter(c => c.priority === 'urgent').length,
      closed: conversations.filter(c => c.status === 'closed').length,
      ai_suggestions: conversations.filter(c => c.suggestions && c.suggestions.some(s => !s.was_used)).length,
    }
  }, [conversations])

  const handleSelectConversation = (conversation: Conversation) => {
    navigate(`/conversations/${conversation.id}`)
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
            AI-powered conversation management
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-dark-text-muted">Active</p>
              <p className="text-2xl font-bold text-dark-text-primary mt-1">
                {stats.active}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-dark-text-muted">Needs Response</p>
              <p className="text-2xl font-bold text-orange-400 mt-1">
                {stats.needs_response}
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-dark-text-muted">AI Suggestions</p>
              <p className="text-2xl font-bold text-terminal-400 mt-1">
                {stats.ai_suggestions}
              </p>
            </div>
            <div className="w-12 h-12 bg-terminal-500/20 rounded-full flex items-center justify-center">
              <span className="text-lg">✨</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-dark-text-muted">Urgent</p>
              <p className="text-2xl font-bold text-red-400 mt-1">
                {stats.urgent}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and View Controls */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-dark-bg-secondary border border-dark-border rounded-lg text-dark-text-primary placeholder:text-dark-text-muted focus:outline-none focus:ring-2 focus:ring-terminal-500"
              />
            </div>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 bg-dark-bg-secondary rounded-lg p-1">
            <button
              onClick={() => setViewMode('cards')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'cards'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-muted hover:text-dark-text-primary'
              }`}
              title="Card view"
            >
              <Squares2X2Icon className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'table'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-muted hover:text-dark-text-primary'
              }`}
              title="Table view"
            >
              <TableCellsIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Toggle Filters */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg border transition-colors flex items-center gap-2 ${
              showFilters
                ? 'bg-terminal-500/20 border-terminal-500 text-terminal-400'
                : 'border-dark-border text-dark-text-primary hover:border-terminal-500'
            }`}
          >
            <FunnelIcon className="w-5 h-5" />
            Filters
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Filters Sidebar */}
        {showFilters && (
          <div className="lg:col-span-3">
            <ConversationFilters
              filters={filters}
              onFilterChange={setFilters}
              counts={{
                active: stats.active,
                needs_response: stats.needs_response,
                urgent: stats.urgent,
                closed: stats.closed,
              }}
            />
          </div>
        )}

        {/* Conversations List */}
        <div className={showFilters ? 'lg:col-span-9' : 'lg:col-span-12'}>
          <div className="card">
            {/* Results Count */}
            <div className="mb-4 pb-4 border-b border-dark-border">
              <p className="text-sm text-dark-text-muted">
                Showing {filteredConversations.length} of {conversations.length} conversations
              </p>
            </div>

            {/* Conversations */}
            {filteredConversations.length > 0 ? (
              viewMode === 'cards' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredConversations.map((conversation) => (
                    <ConversationCard
                      key={conversation.id}
                      conversation={conversation}
                      onClick={() => handleSelectConversation(conversation)}
                    />
                  ))}
                </div>
              ) : (
                <ConversationsTable
                  conversations={filteredConversations}
                  onSelectConversation={handleSelectConversation}
                />
              )
            ) : (
              <div className="text-center py-12">
                <p className="text-dark-text-muted">No conversations match your filters</p>
                <button
                  onClick={() => {
                    setFilters({ status: 'all', priority: 'all', sentiment: 'all', needs_response: false })
                    setSearchQuery('')
                  }}
                  className="mt-4 px-4 py-2 text-terminal-400 hover:text-terminal-300 border border-terminal-500 rounded-lg transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
