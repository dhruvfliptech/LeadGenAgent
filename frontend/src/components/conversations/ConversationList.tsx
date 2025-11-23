import { Conversation } from '@/types/conversation'
import { formatRelativeTime } from '@/utils/dateFormat'
import {
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
  CheckCircleIcon,
  InboxIcon
} from '@heroicons/react/24/outline'

interface ConversationListProps {
  conversations: Conversation[]
  selectedId?: number
  onSelect: (conversation: Conversation) => void
  searchQuery: string
  onSearchChange: (query: string) => void
  filters: {
    needs_reply: boolean
    active: boolean
    archived: boolean
  }
  onFilterChange: (filters: { needs_reply: boolean; active: boolean; archived: boolean }) => void
  stats: {
    needs_reply: number
    active: number
    archived: number
  }
}

// Helper function for status icons
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
      return <ChatBubbleLeftRightIcon className="w-5 h-5 text-terminal-500" />
    case 'pending':
      return <ClockIcon className="w-5 h-5 text-yellow-500" />
    case 'closed':
      return <CheckCircleIcon className="w-5 h-5 text-green-500" />
    default:
      return <InboxIcon className="w-5 h-5 text-gray-500" />
  }
}

export default function ConversationList({
  conversations,
  selectedId,
  onSelect,
  searchQuery,
  onSearchChange,
  filters,
  onFilterChange,
  stats
}: ConversationListProps) {

  const filteredConversations = conversations.filter(conv => {
    // Apply status filters
    if (filters.needs_reply && conv.status !== 'needs_reply') return false
    if (filters.active && conv.status !== 'active') return false
    if (filters.archived && conv.status !== 'archived') return false

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        conv.subject.toLowerCase().includes(query) ||
        conv.lead?.title.toLowerCase().includes(query) ||
        conv.lead?.email.toLowerCase().includes(query) ||
        conv.lead?.contact_name?.toLowerCase().includes(query)
      )
    }

    return true
  })

  return (
    <div className="flex flex-col h-full bg-dark-surface border-r border-dark-border">
      {/* Search bar */}
      <div className="p-4 border-b border-dark-border">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-md text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:ring-2 focus:ring-terminal-500 focus:border-terminal-500"
          />
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-text-muted" />
        </div>
      </div>

      {/* Filters */}
      <div className="px-4 py-3 border-b border-dark-border space-y-2">
        <label className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            checked={filters.needs_reply}
            onChange={(e) => onFilterChange({ ...filters, needs_reply: e.target.checked })}
            className="w-4 h-4 rounded border-dark-border bg-dark-bg text-terminal-500 focus:ring-terminal-500 focus:ring-offset-dark-surface"
          />
          <span className="text-sm text-dark-text-primary group-hover:text-terminal-400 transition-colors">
            Needs Reply
          </span>
          {stats.needs_reply > 0 && (
            <span className="ml-auto text-xs px-2 py-0.5 bg-[#FF3B30]/20 text-[#FF3B30] rounded-full">
              {stats.needs_reply}
            </span>
          )}
        </label>
        <label className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            checked={filters.active}
            onChange={(e) => onFilterChange({ ...filters, active: e.target.checked })}
            className="w-4 h-4 rounded border-dark-border bg-dark-bg text-terminal-500 focus:ring-terminal-500 focus:ring-offset-dark-surface"
          />
          <span className="text-sm text-dark-text-primary group-hover:text-terminal-400 transition-colors">
            Active
          </span>
          {stats.active > 0 && (
            <span className="ml-auto text-xs px-2 py-0.5 bg-[#0A84FF]/20 text-[#0A84FF] rounded-full">
              {stats.active}
            </span>
          )}
        </label>
        <label className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            checked={filters.archived}
            onChange={(e) => onFilterChange({ ...filters, archived: e.target.checked })}
            className="w-4 h-4 rounded border-dark-border bg-dark-bg text-terminal-500 focus:ring-terminal-500 focus:ring-offset-dark-surface"
          />
          <span className="text-sm text-dark-text-primary group-hover:text-terminal-400 transition-colors">
            Archived
          </span>
          {stats.archived > 0 && (
            <span className="ml-auto text-xs px-2 py-0.5 bg-[#34C759]/20 text-[#34C759] rounded-full">
              {stats.archived}
            </span>
          )}
        </label>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {/* Needs Reply Section */}
        {filteredConversations.some(c => c.status === 'needs_reply') && (
          <div>
            <div className="px-4 py-2 text-xs font-semibold text-[#FF3B30] uppercase tracking-wider bg-[#FF3B30]/10">
              ⚡ Needs Reply ({filteredConversations.filter(c => c.status === 'needs_reply').length})
            </div>
            {filteredConversations
              .filter(c => c.status === 'needs_reply')
              .map(conversation => (
                <ConversationListItem
                  key={conversation.id}
                  conversation={conversation}
                  isSelected={conversation.id === selectedId}
                  onClick={() => onSelect(conversation)}
                />
              ))}
          </div>
        )}

        {/* Active Section */}
        {filteredConversations.some(c => c.status === 'active' || c.status === 'waiting') && (
          <div>
            <div className="px-4 py-2 text-xs font-semibold text-[#0A84FF] uppercase tracking-wider bg-[#0A84FF]/10">
              💬 Active ({filteredConversations.filter(c => c.status === 'active' || c.status === 'waiting').length})
            </div>
            {filteredConversations
              .filter(c => c.status === 'active' || c.status === 'waiting')
              .map(conversation => (
                <ConversationListItem
                  key={conversation.id}
                  conversation={conversation}
                  isSelected={conversation.id === selectedId}
                  onClick={() => onSelect(conversation)}
                />
              ))}
          </div>
        )}

        {/* Archived Section */}
        {filteredConversations.some(c => c.status === 'archived') && (
          <div>
            <div className="px-4 py-2 text-xs font-semibold text-[#34C759] uppercase tracking-wider bg-[#34C759]/10">
              ✅ Archived ({filteredConversations.filter(c => c.status === 'archived').length})
            </div>
            {filteredConversations
              .filter(c => c.status === 'archived')
              .map(conversation => (
                <ConversationListItem
                  key={conversation.id}
                  conversation={conversation}
                  isSelected={conversation.id === selectedId}
                  onClick={() => onSelect(conversation)}
                />
              ))}
          </div>
        )}

        {/* Empty state */}
        {filteredConversations.length === 0 && (
          <div className="p-6 text-center text-dark-text-muted">
            <p className="text-sm">No conversations found</p>
          </div>
        )}
      </div>
    </div>
  )
}

// List item component
interface ConversationListItemProps {
  conversation: Conversation
  isSelected: boolean
  onClick: () => void
}

function ConversationListItem({ conversation, isSelected, onClick }: ConversationListItemProps) {

  return (
    <button
      onClick={onClick}
      className={`w-full px-4 py-3 text-left border-b border-dark-border hover:bg-dark-border/50 transition-colors ${
        isSelected ? 'bg-terminal-500/10 border-l-4 border-l-terminal-500' : ''
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-1 flex-shrink-0">
          {getStatusIcon(conversation.status)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-medium text-dark-text-primary truncate">
              {conversation.lead?.contact_name || conversation.lead?.email || 'Unknown'}
            </h4>
            {conversation.unread_count && conversation.unread_count > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-xs bg-terminal-500 text-black rounded-full">
                {conversation.unread_count}
              </span>
            )}
          </div>
          <p className="text-xs text-dark-text-muted mb-1 truncate">
            {conversation.lead?.title}
          </p>
          <div className="flex items-center justify-between">
            <p className="text-xs text-dark-text-muted truncate flex-1">
              {conversation.subject}
            </p>
            <span className="text-xs text-dark-text-muted ml-2 flex-shrink-0">
              {formatRelativeTime(conversation.last_message_at)}
            </span>
          </div>
        </div>
      </div>
    </button>
  )
}
