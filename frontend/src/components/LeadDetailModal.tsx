import { Fragment } from 'react'
import { Dialog, Transition, Tab } from '@headlessui/react'
import {
  XMarkIcon,
  EnvelopeIcon,
  PhoneIcon,
  GlobeAltIcon,
  MapPinIcon,
  TagIcon,
  ClockIcon,
  StarIcon
} from '@heroicons/react/24/outline'
import { MockLead } from '@/mocks/leads.mock'
import SourceBadge from '@/components/SourceBadge'
import { formatRelativeTime } from '@/utils/dateFormat'

interface LeadDetailModalProps {
  lead: MockLead | null
  open: boolean
  onClose: () => void
}

/**
 * LeadDetailModal - Modal displaying full lead details
 * Shows overview, enrichment data, activity timeline, and metadata
 */
export default function LeadDetailModal({ lead, open, onClose }: LeadDetailModalProps) {
  if (!lead) return null

  const getEnrichmentBadge = () => {
    const config = {
      enriched: { color: 'bg-green-500/10 text-green-500 border-green-500/20', label: 'Enriched' },
      enriching: { color: 'bg-blue-500/10 text-blue-500 border-blue-500/20', label: 'Enriching...' },
      pending: { color: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20', label: 'Pending' },
      failed: { color: 'bg-red-500/10 text-red-500 border-red-500/20', label: 'Failed' }
    }

    const badge = config[lead.enrichment_status]

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded border text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    )
  }

  const getStatusBadge = () => {
    const config = {
      new: { color: 'bg-blue-500/10 text-blue-500', label: 'New' },
      contacted: { color: 'bg-yellow-500/10 text-yellow-500', label: 'Contacted' },
      replied: { color: 'bg-purple-500/10 text-purple-500', label: 'Replied' },
      qualified: { color: 'bg-green-500/10 text-green-500', label: 'Qualified' },
      won: { color: 'bg-emerald-500/10 text-emerald-500', label: 'Won' },
      lost: { color: 'bg-red-500/10 text-red-500', label: 'Lost' }
    }

    const badge = config[lead.status]

    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded text-sm font-medium ${badge.color}`}>
        {badge.label}
      </span>
    )
  }

  return (
    <Transition appear show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-xl bg-dark-surface shadow-xl transition-all">
                {/* Header */}
                <div className="flex items-start justify-between px-6 py-4 border-b border-dark-border">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Dialog.Title className="text-xl font-bold text-dark-text-primary">
                        {lead.title}
                      </Dialog.Title>
                      {getStatusBadge()}
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <SourceBadge source={lead.source} size="sm" />
                      {getEnrichmentBadge()}
                      {lead.price && (
                        <span className="text-sm font-semibold text-green-500">
                          ${lead.price.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="text-dark-text-muted hover:text-dark-text-primary transition-colors"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>

                {/* Tabs */}
                <Tab.Group>
                  <Tab.List className="flex gap-4 px-6 border-b border-dark-border">
                    {['Overview', 'Activity', 'Assets'].map((tab) => (
                      <Tab
                        key={tab}
                        className={({ selected }) =>
                          `py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
                            selected
                              ? 'border-terminal-500 text-terminal-500'
                              : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary'
                          }`
                        }
                      >
                        {tab}
                      </Tab>
                    ))}
                  </Tab.List>

                  <Tab.Panels className="px-6 py-6">
                    {/* Overview Tab */}
                    <Tab.Panel className="space-y-6">
                      {/* Company Information */}
                      <div>
                        <h3 className="text-sm font-semibold text-dark-text-primary mb-4 uppercase tracking-wider">
                          Company Information
                        </h3>
                        <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="flex items-start gap-3">
                            <div className="mt-1">
                              <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                <span className="text-lg">🏢</span>
                              </div>
                            </div>
                            <div className="flex-1">
                              <dt className="text-xs text-dark-text-muted mb-1">Company Name</dt>
                              <dd className="text-sm font-medium text-dark-text-primary">{lead.company_name}</dd>
                            </div>
                          </div>

                          {lead.website && (
                            <div className="flex items-start gap-3">
                              <div className="mt-1">
                                <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                  <GlobeAltIcon className="w-4 h-4 text-terminal-500" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <dt className="text-xs text-dark-text-muted mb-1">Website</dt>
                                <dd>
                                  <a
                                    href={lead.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm font-medium text-terminal-500 hover:text-terminal-400"
                                  >
                                    {lead.website}
                                  </a>
                                </dd>
                              </div>
                            </div>
                          )}

                          {lead.email && (
                            <div className="flex items-start gap-3">
                              <div className="mt-1">
                                <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                  <EnvelopeIcon className="w-4 h-4 text-blue-500" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <dt className="text-xs text-dark-text-muted mb-1">Email</dt>
                                <dd>
                                  <a
                                    href={`mailto:${lead.email}`}
                                    className="text-sm font-medium text-dark-text-primary hover:text-terminal-500"
                                  >
                                    {lead.email}
                                  </a>
                                </dd>
                              </div>
                            </div>
                          )}

                          {lead.phone && (
                            <div className="flex items-start gap-3">
                              <div className="mt-1">
                                <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                  <PhoneIcon className="w-4 h-4 text-green-500" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <dt className="text-xs text-dark-text-muted mb-1">Phone</dt>
                                <dd>
                                  <a
                                    href={`tel:${lead.phone}`}
                                    className="text-sm font-medium text-dark-text-primary hover:text-terminal-500"
                                  >
                                    {lead.phone}
                                  </a>
                                </dd>
                              </div>
                            </div>
                          )}

                          <div className="flex items-start gap-3">
                            <div className="mt-1">
                              <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                <MapPinIcon className="w-4 h-4 text-red-500" />
                              </div>
                            </div>
                            <div className="flex-1">
                              <dt className="text-xs text-dark-text-muted mb-1">Location</dt>
                              <dd className="text-sm font-medium text-dark-text-primary">{lead.location}</dd>
                            </div>
                          </div>

                          {(lead.rating || lead.review_count) && (
                            <div className="flex items-start gap-3">
                              <div className="mt-1">
                                <div className="w-8 h-8 rounded-lg bg-dark-border flex items-center justify-center">
                                  <StarIcon className="w-4 h-4 text-yellow-500" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <dt className="text-xs text-dark-text-muted mb-1">Rating</dt>
                                <dd className="text-sm font-medium text-dark-text-primary">
                                  {lead.rating ? `${lead.rating} stars` : 'N/A'}
                                  {lead.review_count && (
                                    <span className="text-dark-text-muted ml-2">
                                      ({lead.review_count} reviews)
                                    </span>
                                  )}
                                </dd>
                              </div>
                            </div>
                          )}
                        </dl>
                      </div>

                      {/* Description */}
                      {lead.description && (
                        <div>
                          <h3 className="text-sm font-semibold text-dark-text-primary mb-3 uppercase tracking-wider">
                            Description
                          </h3>
                          <p className="text-sm text-dark-text-secondary leading-relaxed">
                            {lead.description}
                          </p>
                        </div>
                      )}

                      {/* Tags */}
                      {lead.tags.length > 0 && (
                        <div>
                          <h3 className="text-sm font-semibold text-dark-text-primary mb-3 uppercase tracking-wider">
                            Tags
                          </h3>
                          <div className="flex flex-wrap gap-2">
                            {lead.tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-dark-border text-dark-text-primary"
                              >
                                <TagIcon className="w-3 h-3" />
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Metadata */}
                      <div>
                        <h3 className="text-sm font-semibold text-dark-text-primary mb-3 uppercase tracking-wider">
                          Metadata
                        </h3>
                        <dl className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <dt className="text-dark-text-muted mb-1">Scraped At</dt>
                            <dd className="text-dark-text-primary flex items-center gap-2">
                              <ClockIcon className="w-4 h-4" />
                              {formatRelativeTime(lead.scraped_at)}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-dark-text-muted mb-1">Original URL</dt>
                            <dd>
                              <a
                                href={lead.original_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-terminal-500 hover:text-terminal-400 text-sm"
                              >
                                View Original →
                              </a>
                            </dd>
                          </div>
                          <div>
                            <dt className="text-dark-text-muted mb-1">Has Demo Site</dt>
                            <dd className="text-dark-text-primary">
                              {lead.has_demo_site ? '✅ Yes' : '❌ No'}
                            </dd>
                          </div>
                          <div>
                            <dt className="text-dark-text-muted mb-1">Has Video</dt>
                            <dd className="text-dark-text-primary">
                              {lead.has_video ? '✅ Yes' : '❌ No'}
                            </dd>
                          </div>
                        </dl>
                      </div>
                    </Tab.Panel>

                    {/* Activity Tab */}
                    <Tab.Panel>
                      <div className="space-y-4">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                            <CheckCircleIcon className="w-4 h-4 text-blue-500" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm text-dark-text-primary">Lead created from {lead.source} scrape</p>
                            <p className="text-xs text-dark-text-muted mt-1">{formatRelativeTime(lead.scraped_at)}</p>
                          </div>
                        </div>

                        {lead.enrichment_status === 'enriched' && (
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                              <CheckCircleIcon className="w-4 h-4 text-green-500" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm text-dark-text-primary">Lead enrichment completed</p>
                              <p className="text-xs text-dark-text-muted mt-1">Contact information found</p>
                            </div>
                          </div>
                        )}

                        <div className="text-center py-8 text-dark-text-muted text-sm">
                          More activity coming soon...
                        </div>
                      </div>
                    </Tab.Panel>

                    {/* Assets Tab */}
                    <Tab.Panel>
                      <div className="space-y-4">
                        {lead.has_demo_site && (
                          <div className="bg-dark-border/30 rounded-lg p-4">
                            <h4 className="text-sm font-medium text-dark-text-primary mb-2">Demo Site</h4>
                            <p className="text-xs text-dark-text-muted">Demo site created for this lead</p>
                          </div>
                        )}

                        {lead.has_video && (
                          <div className="bg-dark-border/30 rounded-lg p-4">
                            <h4 className="text-sm font-medium text-dark-text-primary mb-2">Video</h4>
                            <p className="text-xs text-dark-text-muted">Personalized video created</p>
                          </div>
                        )}

                        {!lead.has_demo_site && !lead.has_video && (
                          <div className="text-center py-8 text-dark-text-muted text-sm">
                            No assets created yet
                          </div>
                        )}
                      </div>
                    </Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>

                {/* Footer Actions */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-dark-border">
                  <button onClick={onClose} className="btn-secondary">
                    Close
                  </button>
                  <button className="btn-primary">
                    <EnvelopeIcon className="w-4 h-4" />
                    Send Email
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

function CheckCircleIcon({ className }: { className: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}
