import { useState } from 'react'
import {
  XMarkIcon,
  FunnelIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline'

export interface FilterConfig {
  status?: string[]
  source?: string[]
  dateRange?: { start?: string; end?: string }
  qualificationScore?: { min?: number; max?: number }
  location?: string[]
  tags?: string[]
  category?: string[]
  contacted?: boolean | null
  hasEmail?: boolean | null
  hasPhone?: boolean | null
  isProcessed?: boolean | null
}

interface AdvancedFiltersProps {
  isOpen: boolean
  onClose: () => void
  onApply: (filters: FilterConfig) => void
  availableFilters?: {
    statuses?: string[]
    sources?: string[]
    locations?: string[]
    tags?: string[]
    categories?: string[]
  }
}

export default function AdvancedFilters({
  isOpen,
  onClose,
  onApply,
  availableFilters = {}
}: AdvancedFiltersProps) {
  const [filters, setFilters] = useState<FilterConfig>({})
  const [showSection, setShowSection] = useState({
    status: true,
    source: false,
    dateRange: false,
    score: false,
    location: false,
    contact: false,
  })

  const {
    statuses = ['new', 'contacted', 'qualified', 'converted', 'rejected'],
    sources = ['craigslist', 'google_maps', 'linkedin', 'indeed', 'monster', 'ziprecruiter'],
  } = availableFilters

  const handleApply = () => {
    onApply(filters)
    onClose()
  }

  const handleReset = () => {
    setFilters({})
    onApply({})
    onClose()
  }

  const toggleSection = (section: keyof typeof showSection) => {
    setShowSection(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const toggleArrayFilter = (key: keyof FilterConfig, value: string) => {
    setFilters(prev => {
      const current = (prev[key] as string[]) || []
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value]
      return { ...prev, [key]: updated.length > 0 ? updated : undefined }
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-dark-surface border border-dark-border rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="sticky top-0 bg-dark-surface border-b border-dark-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-terminal-400" />
            <h2 className="text-lg font-semibold text-dark-text-primary">Advanced Filters</h2>
          </div>
          <button
            onClick={onClose}
            className="text-dark-text-muted hover:text-dark-text-primary transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Filters Content */}
        <div className="p-6 space-y-6">
          {/* Status Filter */}
          <div className="space-y-3">
            <button
              onClick={() => toggleSection('status')}
              className="w-full flex items-center justify-between text-left"
            >
              <h3 className="text-sm font-medium text-dark-text-primary">Status</h3>
              <ChevronDownIcon
                className={`h-4 w-4 text-dark-text-muted transition-transform ${
                  showSection.status ? 'rotate-180' : ''
                }`}
              />
            </button>
            {showSection.status && (
              <div className="grid grid-cols-2 gap-2">
                {statuses.map((status) => (
                  <label
                    key={status}
                    className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30"
                  >
                    <input
                      type="checkbox"
                      checked={filters.status?.includes(status) || false}
                      onChange={() => toggleArrayFilter('status', status)}
                      className="form-checkbox"
                    />
                    <span className="text-sm text-dark-text-secondary capitalize">
                      {status}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Source Filter */}
          <div className="space-y-3">
            <button
              onClick={() => toggleSection('source')}
              className="w-full flex items-center justify-between text-left"
            >
              <h3 className="text-sm font-medium text-dark-text-primary">Source</h3>
              <ChevronDownIcon
                className={`h-4 w-4 text-dark-text-muted transition-transform ${
                  showSection.source ? 'rotate-180' : ''
                }`}
              />
            </button>
            {showSection.source && (
              <div className="grid grid-cols-2 gap-2">
                {sources.map((source) => (
                  <label
                    key={source}
                    className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30"
                  >
                    <input
                      type="checkbox"
                      checked={filters.source?.includes(source) || false}
                      onChange={() => toggleArrayFilter('source', source)}
                      className="form-checkbox"
                    />
                    <span className="text-sm text-dark-text-secondary capitalize">
                      {source.replace('_', ' ')}
                    </span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Date Range Filter */}
          <div className="space-y-3">
            <button
              onClick={() => toggleSection('dateRange')}
              className="w-full flex items-center justify-between text-left"
            >
              <h3 className="text-sm font-medium text-dark-text-primary">Date Range</h3>
              <ChevronDownIcon
                className={`h-4 w-4 text-dark-text-muted transition-transform ${
                  showSection.dateRange ? 'rotate-180' : ''
                }`}
              />
            </button>
            {showSection.dateRange && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">From</label>
                  <input
                    type="date"
                    value={filters.dateRange?.start || ''}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, start: e.target.value },
                      }))
                    }
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="form-label">To</label>
                  <input
                    type="date"
                    value={filters.dateRange?.end || ''}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, end: e.target.value },
                      }))
                    }
                    className="form-input"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Qualification Score Filter */}
          <div className="space-y-3">
            <button
              onClick={() => toggleSection('score')}
              className="w-full flex items-center justify-between text-left"
            >
              <h3 className="text-sm font-medium text-dark-text-primary">
                Qualification Score
              </h3>
              <ChevronDownIcon
                className={`h-4 w-4 text-dark-text-muted transition-transform ${
                  showSection.score ? 'rotate-180' : ''
                }`}
              />
            </button>
            {showSection.score && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Min Score</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={filters.qualificationScore?.min || ''}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        qualificationScore: {
                          ...prev.qualificationScore,
                          min: e.target.value ? parseInt(e.target.value) : undefined,
                        },
                      }))
                    }
                    placeholder="0"
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="form-label">Max Score</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={filters.qualificationScore?.max || ''}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        qualificationScore: {
                          ...prev.qualificationScore,
                          max: e.target.value ? parseInt(e.target.value) : undefined,
                        },
                      }))
                    }
                    placeholder="10"
                    className="form-input"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Contact Info Filter */}
          <div className="space-y-3">
            <button
              onClick={() => toggleSection('contact')}
              className="w-full flex items-center justify-between text-left"
            >
              <h3 className="text-sm font-medium text-dark-text-primary">Contact Info</h3>
              <ChevronDownIcon
                className={`h-4 w-4 text-dark-text-muted transition-transform ${
                  showSection.contact ? 'rotate-180' : ''
                }`}
              />
            </button>
            {showSection.contact && (
              <div className="space-y-2">
                <label className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30">
                  <input
                    type="checkbox"
                    checked={filters.hasEmail === true}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        hasEmail: e.target.checked ? true : null,
                      }))
                    }
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-secondary">Has Email</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30">
                  <input
                    type="checkbox"
                    checked={filters.hasPhone === true}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        hasPhone: e.target.checked ? true : null,
                      }))
                    }
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-secondary">Has Phone</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30">
                  <input
                    type="checkbox"
                    checked={filters.contacted === true}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        contacted: e.target.checked ? true : null,
                      }))
                    }
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-secondary">Already Contacted</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer p-2 rounded hover:bg-dark-border/30">
                  <input
                    type="checkbox"
                    checked={filters.isProcessed === true}
                    onChange={(e) =>
                      setFilters((prev) => ({
                        ...prev,
                        isProcessed: e.target.checked ? true : null,
                      }))
                    }
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-secondary">Processed</span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-dark-surface border-t border-dark-border px-6 py-4 flex items-center justify-between">
          <button onClick={handleReset} className="btn-secondary">
            Reset All
          </button>
          <div className="flex items-center space-x-3">
            <button onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button onClick={handleApply} className="btn-primary">
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
