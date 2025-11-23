import { ConversationPriority, SentimentType, ConversationStatus } from '@/types/conversation'

interface ConversationFiltersProps {
  filters: {
    status?: ConversationStatus | 'all'
    priority?: ConversationPriority | 'all'
    sentiment?: SentimentType | 'all'
    needs_response?: boolean
  }
  onFilterChange: (filters: ConversationFiltersProps['filters']) => void
  counts?: {
    active?: number
    needs_response?: number
    urgent?: number
    closed?: number
  }
}

export default function ConversationFilters({ filters, onFilterChange, counts }: ConversationFiltersProps) {
  const updateFilter = (key: string, value: any) => {
    onFilterChange({ ...filters, [key]: value })
  }

  return (
    <div className="space-y-4 p-4 bg-dark-surface rounded-lg border border-dark-border">
      <h3 className="font-semibold text-dark-text-primary text-sm uppercase tracking-wide">
        Filters
      </h3>

      {/* Status Filter */}
      <div>
        <label className="block text-sm font-medium text-dark-text-muted mb-2">
          Status
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="status"
              checked={filters.status === 'all' || !filters.status}
              onChange={() => updateFilter('status', 'all')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">All</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="status"
              checked={filters.status === 'active'}
              onChange={() => updateFilter('status', 'active')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">Active</span>
            {counts?.active !== undefined && (
              <span className="ml-auto text-xs text-dark-text-muted bg-dark-bg-secondary px-2 py-0.5 rounded">
                {counts.active}
              </span>
            )}
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="status"
              checked={filters.status === 'replied'}
              onChange={() => updateFilter('status', 'replied')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">Replied</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="status"
              checked={filters.status === 'snoozed'}
              onChange={() => updateFilter('status', 'snoozed')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">Snoozed</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="status"
              checked={filters.status === 'closed'}
              onChange={() => updateFilter('status', 'closed')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">Closed</span>
            {counts?.closed !== undefined && (
              <span className="ml-auto text-xs text-dark-text-muted bg-dark-bg-secondary px-2 py-0.5 rounded">
                {counts.closed}
              </span>
            )}
          </label>
        </div>
      </div>

      {/* Priority Filter */}
      <div className="pt-3 border-t border-dark-border">
        <label className="block text-sm font-medium text-dark-text-muted mb-2">
          Priority
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="priority"
              checked={filters.priority === 'all' || !filters.priority}
              onChange={() => updateFilter('priority', 'all')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">All</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="priority"
              checked={filters.priority === 'urgent'}
              onChange={() => updateFilter('priority', 'urgent')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              Urgent
            </span>
            {counts?.urgent !== undefined && (
              <span className="ml-auto text-xs text-dark-text-muted bg-dark-bg-secondary px-2 py-0.5 rounded">
                {counts.urgent}
              </span>
            )}
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="priority"
              checked={filters.priority === 'high'}
              onChange={() => updateFilter('priority', 'high')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-orange-500" />
              High
            </span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="priority"
              checked={filters.priority === 'medium'}
              onChange={() => updateFilter('priority', 'medium')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              Medium
            </span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="priority"
              checked={filters.priority === 'low'}
              onChange={() => updateFilter('priority', 'low')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              Low
            </span>
          </label>
        </div>
      </div>

      {/* Sentiment Filter */}
      <div className="pt-3 border-t border-dark-border">
        <label className="block text-sm font-medium text-dark-text-muted mb-2">
          Sentiment
        </label>
        <div className="space-y-1.5">
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="sentiment"
              checked={filters.sentiment === 'all' || !filters.sentiment}
              onChange={() => updateFilter('sentiment', 'all')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">All</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="sentiment"
              checked={filters.sentiment === 'positive'}
              onChange={() => updateFilter('sentiment', 'positive')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">😊 Positive</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="sentiment"
              checked={filters.sentiment === 'neutral'}
              onChange={() => updateFilter('sentiment', 'neutral')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">😐 Neutral</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="sentiment"
              checked={filters.sentiment === 'negative'}
              onChange={() => updateFilter('sentiment', 'negative')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">☹️ Negative</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
            <input
              type="radio"
              name="sentiment"
              checked={filters.sentiment === 'urgent'}
              onChange={() => updateFilter('sentiment', 'urgent')}
              className="text-terminal-500 focus:ring-terminal-500"
            />
            <span className="text-sm text-dark-text-primary">🚨 Urgent</span>
          </label>
        </div>
      </div>

      {/* Needs Response Checkbox */}
      <div className="pt-3 border-t border-dark-border">
        <label className="flex items-center gap-2 cursor-pointer hover:bg-dark-bg-secondary p-2 rounded transition-colors">
          <input
            type="checkbox"
            checked={filters.needs_response || false}
            onChange={(e) => updateFilter('needs_response', e.target.checked)}
            className="text-terminal-500 focus:ring-terminal-500 rounded"
          />
          <span className="text-sm font-medium text-dark-text-primary">
            Needs Response
          </span>
          {counts?.needs_response !== undefined && (
            <span className="ml-auto text-xs text-dark-text-muted bg-dark-bg-secondary px-2 py-0.5 rounded">
              {counts.needs_response}
            </span>
          )}
        </label>
      </div>

      {/* Reset Filters */}
      <button
        onClick={() => onFilterChange({ status: 'all', priority: 'all', sentiment: 'all', needs_response: false })}
        className="w-full mt-2 px-3 py-2 text-sm text-terminal-400 hover:text-terminal-300 border border-dark-border rounded hover:border-terminal-500 transition-colors"
      >
        Reset Filters
      </button>
    </div>
  )
}
