import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PlusIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { mockABTests } from '@/mocks/models.mock'
import ABTestCard from '@/components/ABTestCard'

type StatusFilter = 'all' | 'draft' | 'running' | 'paused' | 'completed'

/**
 * AI-GYM A/B Tests - Test Management
 * Route: /ai-gym/ab-tests
 */
export default function AIGymABTests() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  const filteredTests = mockABTests.filter(test => {
    if (statusFilter === 'all') return true
    return test.status === statusFilter
  })

  const stats = {
    total: mockABTests.length,
    running: mockABTests.filter(t => t.status === 'running').length,
    completed: mockABTests.filter(t => t.status === 'completed').length,
    draft: mockABTests.filter(t => t.status === 'draft').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">A/B Tests</h1>
          <p className="text-dark-text-muted mt-1">
            Create and manage model comparison tests
          </p>
        </div>
        <Link
          to="/ai-gym/ab-tests/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-terminal-500 text-white rounded-lg hover:bg-terminal-600 transition-colors font-medium"
        >
          <PlusIcon className="w-5 h-5" />
          Create A/B Test
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-2xl font-bold text-dark-text-primary">{stats.total}</div>
          <div className="text-sm text-dark-text-muted">Total Tests</div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-400">{stats.running}</div>
          <div className="text-sm text-dark-text-muted">Running</div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-2xl font-bold text-emerald-400">{stats.completed}</div>
          <div className="text-sm text-dark-text-muted">Completed</div>
        </div>
        <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
          <div className="text-2xl font-bold text-gray-400">{stats.draft}</div>
          <div className="text-sm text-dark-text-muted">Drafts</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <FunnelIcon className="w-5 h-5 text-dark-text-muted" />
          <span className="text-sm font-medium text-dark-text-primary">Filter by Status</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {(['all', 'running', 'completed', 'draft', 'paused'] as StatusFilter[]).map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                statusFilter === status
                  ? 'bg-terminal-500 text-white'
                  : 'bg-dark-bg text-dark-text-secondary hover:bg-dark-border'
              }`}
            >
              {status === 'all' ? 'All Tests' : status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Test Cards */}
      {filteredTests.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredTests.map(test => (
            <ABTestCard key={test.id} test={test} />
          ))}
        </div>
      ) : (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-12 text-center">
          <div className="text-dark-text-muted mb-4">
            No {statusFilter !== 'all' && statusFilter} tests found
          </div>
          {statusFilter !== 'all' ? (
            <button
              onClick={() => setStatusFilter('all')}
              className="text-terminal-400 hover:text-terminal-300"
            >
              View all tests →
            </button>
          ) : (
            <Link
              to="/ai-gym/ab-tests/new"
              className="text-terminal-400 hover:text-terminal-300"
            >
              Create your first test →
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
