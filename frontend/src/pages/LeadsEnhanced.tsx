import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FunnelIcon,
  MagnifyingGlassIcon,
  EnvelopeIcon,
  PhoneIcon,
  TagIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import { mockLeads, MockLead } from '@/mocks/leads.mock'
import SourceBadge from '@/components/SourceBadge'
import LeadDetailModal from '@/components/LeadDetailModal'
import { formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'

type SourceFilter = 'all' | 'craigslist' | 'google_maps' | 'linkedin' | 'job_boards'

/**
 * LeadsEnhanced - Enhanced leads page with source filtering and bulk actions
 * Features: Source tabs, bulk selection, lead detail modal, enrichment badges
 */
export default function LeadsEnhanced() {
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLeads, setSelectedLeads] = useState<Set<number>>(new Set())
  const [selectedLead, setSelectedLead] = useState<MockLead | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)

  // Filter leads
  const filteredLeads = mockLeads.filter(lead => {
    const matchesSource = sourceFilter === 'all' || lead.source === sourceFilter
    const matchesSearch = searchQuery === '' ||
      lead.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      lead.company_name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesSource && matchesSearch
  })

  // Calculate stats
  const stats = {
    total: mockLeads.length,
    craigslist: mockLeads.filter(l => l.source === 'craigslist').length,
    google_maps: mockLeads.filter(l => l.source === 'google_maps').length,
    linkedin: mockLeads.filter(l => l.source === 'linkedin').length,
    job_boards: mockLeads.filter(l => l.source === 'job_boards').length,
    enriched: mockLeads.filter(l => l.enrichment_status === 'enriched').length,
    withEmail: mockLeads.filter(l => l.email).length
  }

  // Bulk actions
  const toggleLeadSelection = (id: number) => {
    const newSelected = new Set(selectedLeads)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedLeads(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedLeads.size === filteredLeads.length) {
      setSelectedLeads(new Set())
    } else {
      setSelectedLeads(new Set(filteredLeads.map(l => l.id)))
    }
  }

  const handleBulkAction = (action: string) => {
    toast.success(`${action} applied to ${selectedLeads.size} leads`)
    setSelectedLeads(new Set())
  }

  const handleLeadClick = (lead: MockLead) => {
    setSelectedLead(lead)
    setShowDetailModal(true)
  }

  const getEnrichmentBadge = (status: string) => {
    const config = {
      enriched: { color: 'bg-green-500/10 text-green-500', label: '✓ Enriched', icon: '✓' },
      enriching: { color: 'bg-blue-500/10 text-blue-500', label: '↻ Enriching', icon: '↻' },
      pending: { color: 'bg-yellow-500/10 text-yellow-500', label: '⏳ Pending', icon: '⏳' },
      failed: { color: 'bg-red-500/10 text-red-500', label: '✗ Failed', icon: '✗' }
    }

    const badge = config[status as keyof typeof config] || config.pending

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    )
  }

  const getStatusBadge = (status: string) => {
    const config = {
      new: 'bg-blue-500/10 text-blue-500',
      contacted: 'bg-yellow-500/10 text-yellow-500',
      replied: 'bg-purple-500/10 text-purple-500',
      qualified: 'bg-green-500/10 text-green-500',
      won: 'bg-emerald-500/10 text-emerald-500',
      lost: 'bg-red-500/10 text-red-500'
    }

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${config[status as keyof typeof config] || 'bg-gray-500/10 text-gray-500'}`}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-dark-text-primary">Leads</h2>
          <p className="text-sm text-dark-text-secondary mt-1">
            {filteredLeads.length} of {stats.total} leads
          </p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary">
            <ArrowDownTrayIcon className="w-4 h-4" />
            Export
          </button>
          <Link to="/scraper" className="btn-primary">
            + New Scrape
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Total Leads</div>
          <div className="text-2xl font-bold text-dark-text-primary mt-1">{stats.total}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Enriched</div>
          <div className="text-2xl font-bold text-green-400 mt-1">
            {stats.enriched}
            <span className="text-sm text-dark-text-muted ml-2">
              ({Math.round((stats.enriched / stats.total) * 100)}%)
            </span>
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">With Email</div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{stats.withEmail}</div>
        </div>
        <div className="card p-4">
          <div className="text-sm font-medium text-dark-text-secondary">Selected</div>
          <div className="text-2xl font-bold text-terminal-500 mt-1">{selectedLeads.size}</div>
        </div>
      </div>

      {/* Source Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setSourceFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            sourceFilter === 'all'
              ? 'bg-terminal-500 text-dark-bg'
              : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
          }`}
        >
          All Sources ({stats.total})
        </button>
        <button
          onClick={() => setSourceFilter('craigslist')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            sourceFilter === 'craigslist'
              ? 'bg-terminal-500 text-dark-bg'
              : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
          }`}
        >
          📍 Craigslist ({stats.craigslist})
        </button>
        <button
          onClick={() => setSourceFilter('google_maps')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            sourceFilter === 'google_maps'
              ? 'bg-terminal-500 text-dark-bg'
              : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
          }`}
        >
          🗺️ Google Maps ({stats.google_maps})
        </button>
        <button
          onClick={() => setSourceFilter('linkedin')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            sourceFilter === 'linkedin'
              ? 'bg-terminal-500 text-dark-bg'
              : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
          }`}
        >
          💼 LinkedIn ({stats.linkedin})
        </button>
        <button
          onClick={() => setSourceFilter('job_boards')}
          className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
            sourceFilter === 'job_boards'
              ? 'bg-terminal-500 text-dark-bg'
              : 'bg-dark-border text-dark-text-secondary hover:bg-dark-border/50'
          }`}
        >
          🔍 Job Boards ({stats.job_boards})
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search leads by title, company..."
            className="form-input pl-10 w-full"
          />
        </div>
        <button className="btn-secondary">
          <FunnelIcon className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Bulk Actions Bar */}
      {selectedLeads.size > 0 && (
        <div className="bg-terminal-500/10 border border-terminal-500/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-dark-text-primary">
              {selectedLeads.size} lead{selectedLeads.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => handleBulkAction('Send Email')}
                className="btn-secondary text-sm"
              >
                <EnvelopeIcon className="w-4 h-4" />
                Send Email
              </button>
              <button
                onClick={() => handleBulkAction('Add Tags')}
                className="btn-secondary text-sm"
              >
                <TagIcon className="w-4 h-4" />
                Add Tags
              </button>
              <button
                onClick={() => handleBulkAction('Export')}
                className="btn-secondary text-sm"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                Export
              </button>
              <button
                onClick={() => handleBulkAction('Delete')}
                className="btn-secondary text-sm text-red-500 hover:text-red-400"
              >
                <TrashIcon className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Leads Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-dark-border">
            <thead className="bg-dark-border/30">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedLeads.size === filteredLeads.length && filteredLeads.length > 0}
                    onChange={toggleSelectAll}
                    className="form-checkbox"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Lead
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Enrichment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-secondary uppercase tracking-wider">
                  Scraped
                </th>
              </tr>
            </thead>
            <tbody className="bg-dark-surface divide-y divide-dark-border">
              {filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <p className="text-dark-text-secondary mb-4">No leads found</p>
                    <Link to="/scraper" className="btn-primary">
                      Start Scraping
                    </Link>
                  </td>
                </tr>
              ) : (
                filteredLeads.map((lead) => (
                  <tr
                    key={lead.id}
                    className="hover:bg-dark-border/30 transition-colors cursor-pointer"
                    onClick={() => handleLeadClick(lead)}
                  >
                    <td
                      className="px-6 py-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="checkbox"
                        checked={selectedLeads.has(lead.id)}
                        onChange={() => toggleLeadSelection(lead.id)}
                        className="form-checkbox"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-2">
                        <div>
                          <div className="text-sm font-medium text-dark-text-primary mb-1">
                            {lead.title}
                          </div>
                          <div className="text-xs text-dark-text-muted">{lead.company_name}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <SourceBadge source={lead.source} size="sm" />
                          {lead.price && (
                            <span className="text-xs font-semibold text-green-500">
                              ${lead.price.toLocaleString()}
                            </span>
                          )}
                        </div>
                        {lead.tags.length > 0 && (
                          <div className="flex gap-1 flex-wrap">
                            {lead.tags.slice(0, 2).map(tag => (
                              <span
                                key={tag}
                                className="text-xs px-2 py-0.5 rounded bg-dark-border text-dark-text-muted"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {lead.email && (
                          <div className="flex items-center gap-1 text-xs text-dark-text-secondary">
                            <EnvelopeIcon className="w-4 h-4 text-blue-500" />
                            <span className="hidden lg:inline">{lead.email}</span>
                          </div>
                        )}
                        {lead.phone && (
                          <div className="flex items-center gap-1 text-xs text-dark-text-secondary">
                            <PhoneIcon className="w-4 h-4 text-green-500" />
                            <span className="hidden lg:inline">{lead.phone}</span>
                          </div>
                        )}
                        {!lead.email && !lead.phone && (
                          <span className="text-xs text-dark-text-muted">No contact info</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-dark-text-secondary">
                      {lead.location}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(lead.status)}
                    </td>
                    <td className="px-6 py-4">
                      {getEnrichmentBadge(lead.enrichment_status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-dark-text-secondary whitespace-nowrap">
                      {formatRelativeTime(lead.scraped_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Lead Detail Modal */}
      <LeadDetailModal
        lead={selectedLead}
        open={showDetailModal}
        onClose={() => {
          setShowDetailModal(false)
          setSelectedLead(null)
        }}
      />
    </div>
  )
}
