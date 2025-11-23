import { useState } from 'react'
import {
  CheckCircleIcon,
  ClockIcon,
  SparklesIcon,
  CodeBracketIcon,
  FunnelIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { Improvement } from '@/mocks/analysis.mock'
import { ImprovementSummary } from '@/types/demoSite'
import { demoSitesUtils } from '@/services/demoSitesApi'

interface ImprovementsViewProps {
  improvements: Improvement[]
  appliedImprovements: ImprovementSummary[]
  summary: {
    total_improvements: number
    critical_priority: number
    high_priority: number
    medium_priority: number
    low_priority: number
    estimated_total_impact: string
    estimated_total_time: string
    quick_wins: number
    categories: Record<string, number>
  }
}

type PriorityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low'
type CategoryFilter = 'all' | 'design' | 'seo' | 'performance' | 'accessibility' | 'content' | 'ux'

export default function ImprovementsView({ improvements, appliedImprovements, summary }: ImprovementsViewProps) {
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all')
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all')

  const appliedIds = new Set(appliedImprovements.map(imp => imp.id))

  const filteredImprovements = improvements.filter(imp => {
    if (priorityFilter !== 'all' && imp.priority !== priorityFilter) return false
    if (categoryFilter !== 'all' && imp.category !== categoryFilter) return false
    return true
  })

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-terminal-500/20 rounded-lg">
              <SparklesIcon className="w-6 h-6 text-terminal-500" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text-primary">
                {summary.total_improvements}
              </div>
              <div className="text-sm text-dark-text-secondary">Total Improvements</div>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-500/20 rounded-lg">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text-primary">
                {summary.critical_priority + summary.high_priority}
              </div>
              <div className="text-sm text-dark-text-secondary">Critical + High</div>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-500/20 rounded-lg">
              <CheckCircleIcon className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <div className="text-2xl font-bold text-dark-text-primary">
                {appliedImprovements.length}
              </div>
              <div className="text-sm text-dark-text-secondary">Applied</div>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 rounded-lg">
              <ClockIcon className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <div className="text-lg font-bold text-dark-text-primary">
                {summary.estimated_total_time}
              </div>
              <div className="text-sm text-dark-text-secondary">Est. Time</div>
            </div>
          </div>
        </div>
      </div>

      {/* Impact Summary */}
      <div className="card p-6 bg-gradient-to-r from-terminal-900/20 to-dark-border">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-2">Expected Impact</h3>
        <p className="text-dark-text-secondary">{summary.estimated_total_impact}</p>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <FunnelIcon className="w-5 h-5 text-dark-text-secondary" />

          <div className="flex-1">
            <label className="text-sm text-dark-text-secondary mb-2 block">Priority</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value as PriorityFilter)}
              className="form-input w-full sm:w-48"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="text-sm text-dark-text-secondary mb-2 block">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
              className="form-input w-full sm:w-48"
            >
              <option value="all">All Categories</option>
              <option value="design">Design</option>
              <option value="seo">SEO</option>
              <option value="performance">Performance</option>
              <option value="accessibility">Accessibility</option>
              <option value="content">Content</option>
              <option value="ux">UX</option>
            </select>
          </div>
        </div>
      </div>

      {/* Improvements List */}
      <div className="space-y-4">
        {filteredImprovements.length === 0 ? (
          <div className="card p-12 text-center">
            <SparklesIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-4" />
            <p className="text-dark-text-secondary">No improvements match your filters</p>
          </div>
        ) : (
          filteredImprovements.map((improvement) => {
            const isApplied = appliedIds.has(improvement.id)

            return (
              <div
                key={improvement.id}
                className={`card p-6 ${isApplied ? 'border-2 border-green-500/30 bg-green-500/5' : ''}`}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="flex-shrink-0">
                    <span className="text-4xl">{demoSitesUtils.getCategoryIcon(improvement.category)}</span>
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <h4 className="text-lg font-semibold text-dark-text-primary">
                          {improvement.title}
                        </h4>
                        {isApplied && (
                          <CheckCircleIcon className="w-5 h-5 text-green-500" title="Applied" />
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${demoSitesUtils.getPriorityColor(improvement.priority)}`}>
                          {improvement.priority}
                        </span>
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-dark-border text-dark-text-secondary">
                          {improvement.category}
                        </span>
                      </div>
                    </div>

                    <p className="text-dark-text-secondary mb-4">{improvement.description}</p>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm font-medium text-dark-text-primary mb-1">Current State</div>
                        <p className="text-sm text-dark-text-secondary">{improvement.current_state}</p>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-dark-text-primary mb-1">Proposed Change</div>
                        <p className="text-sm text-dark-text-secondary">{improvement.proposed_change}</p>
                      </div>
                    </div>

                    {/* Impact */}
                    <div className="bg-terminal-900/20 rounded-lg p-3 mb-4">
                      <div className="text-sm font-medium text-dark-text-primary mb-1">Expected Impact</div>
                      <p className="text-sm text-terminal-400">{improvement.impact}</p>
                    </div>

                    {/* Code Example */}
                    {improvement.code_example && (
                      <div className="mb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <CodeBracketIcon className="w-4 h-4 text-dark-text-secondary" />
                          <span className="text-sm font-medium text-dark-text-primary">Code Example</span>
                        </div>
                        <pre className="bg-[#1a1b26] text-gray-200 p-4 rounded-lg text-sm overflow-x-auto">
                          <code>{improvement.code_example}</code>
                        </pre>
                      </div>
                    )}

                    {/* Metadata */}
                    <div className="flex items-center gap-6 text-sm text-dark-text-muted">
                      <div className="flex items-center gap-2">
                        <ClockIcon className="w-4 h-4" />
                        <span>{improvement.time_estimate}</span>
                      </div>
                      <div>
                        <span className="font-medium">Difficulty:</span> {improvement.difficulty}
                      </div>
                      {improvement.dependencies.length > 0 && (
                        <div>
                          <span className="font-medium">Dependencies:</span> {improvement.dependencies.length}
                        </div>
                      )}
                    </div>

                    {/* Resources */}
                    {improvement.resources.length > 0 && (
                      <div className="mt-3">
                        <div className="text-sm font-medium text-dark-text-primary mb-2">Resources</div>
                        <div className="flex flex-wrap gap-2">
                          {improvement.resources.map((resource, idx) => (
                            <a
                              key={idx}
                              href={resource}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-terminal-400 hover:text-terminal-300 underline"
                            >
                              {new URL(resource).hostname}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
