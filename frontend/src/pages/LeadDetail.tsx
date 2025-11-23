import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  EnvelopeIcon,
  PhoneIcon,
  MapPinIcon,
  LinkIcon,
  ClockIcon,
  TagIcon,
  CurrencyDollarIcon,
  BriefcaseIcon,
  StarIcon,
  ChatBubbleLeftRightIcon,
  PencilIcon,
  TrashIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline'
import { Lead } from '@/types/lead'
import { getLeadById } from '@/services/api'
import toast from 'react-hot-toast'

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lead, setLead] = useState<Lead | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'details' | 'history' | 'campaigns'>('details')

  useEffect(() => {
    if (id) {
      loadLead(parseInt(id))
    }
  }, [id])

  const loadLead = async (leadId: number) => {
    try {
      setLoading(true)
      const data = await getLeadById(leadId)
      setLead(data)
    } catch (error) {
      console.error('Failed to load lead:', error)
      toast.error('Failed to load lead details')
      navigate('/leads')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getSourceBadgeColor = (source: string) => {
    const colors: Record<string, string> = {
      craigslist: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
      google_maps: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      linkedin: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
      indeed: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      monster: 'bg-green-500/10 text-green-400 border-green-500/20',
      ziprecruiter: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    }
    return colors[source] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'
  }

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
      contacted: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      qualified: 'bg-green-500/10 text-green-400 border-green-500/20',
      converted: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      rejected: 'bg-red-500/10 text-red-400 border-red-500/20',
    }
    return colors[status] || 'bg-gray-500/10 text-gray-400 border-gray-500/20'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terminal-500"></div>
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="text-center py-12">
        <p className="text-dark-text-secondary">Lead not found</p>
        <button onClick={() => navigate('/leads')} className="btn-primary mt-4">
          Back to Leads
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/leads')}
            className="btn-secondary"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back
          </button>
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary">{lead.title}</h1>
            <p className="text-sm text-dark-text-secondary mt-1">
              Lead ID: {lead.id} • Scraped {formatDate(lead.scraped_at)}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button className="btn-secondary">
            <PencilIcon className="h-4 w-4 mr-2" />
            Edit
          </button>
          <button className="btn-secondary text-red-400 border-red-500/20 hover:bg-red-500/10">
            <TrashIcon className="h-4 w-4 mr-2" />
            Delete
          </button>
          <button className="btn-primary">
            <PaperAirplaneIcon className="h-4 w-4 mr-2" />
            Send Email
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <span className="text-xs text-dark-text-muted block mb-1">Status</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadgeColor(lead.status)}`}>
                {lead.status.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-xs text-dark-text-muted block mb-1">Source</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getSourceBadgeColor(lead.source)}`}>
                {lead.source.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            {lead.qualification_score !== undefined && (
              <div>
                <span className="text-xs text-dark-text-muted block mb-1">Qualification Score</span>
                <div className="flex items-center space-x-2">
                  <StarIcon className="h-5 w-5 text-yellow-400" />
                  <span className="text-lg font-bold text-dark-text-primary">
                    {lead.qualification_score}/10
                  </span>
                </div>
              </div>
            )}
            {lead.is_contacted && (
              <div>
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                  CONTACTED
                </span>
              </div>
            )}
          </div>

          {lead.price && (
            <div className="text-right">
              <span className="text-xs text-dark-text-muted block mb-1">Price</span>
              <span className="text-2xl font-bold text-terminal-400">
                ${lead.price.toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-border">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('details')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'details'
                ? 'border-terminal-500 text-terminal-400'
                : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'history'
                ? 'border-terminal-500 text-terminal-400'
                : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
            }`}
          >
            Conversation History
          </button>
          <button
            onClick={() => setActiveTab('campaigns')}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'campaigns'
                ? 'border-terminal-500 text-terminal-400'
                : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
            }`}
          >
            Campaign Interactions
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'details' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Contact Information */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Contact Information</h2>
              <div className="space-y-4">
                {lead.contact_name && (
                  <div className="flex items-start space-x-3">
                    <TagIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                    <div>
                      <p className="text-sm text-dark-text-muted">Name</p>
                      <p className="text-dark-text-primary font-medium">{lead.contact_name}</p>
                    </div>
                  </div>
                )}
                {(lead.email || lead.reply_email) && (
                  <div className="flex items-start space-x-3">
                    <EnvelopeIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                    <div>
                      <p className="text-sm text-dark-text-muted">Email</p>
                      <a
                        href={`mailto:${lead.email || lead.reply_email}`}
                        className="text-terminal-400 hover:text-terminal-300 font-medium"
                      >
                        {lead.email || lead.reply_email}
                      </a>
                    </div>
                  </div>
                )}
                {(lead.phone || lead.reply_phone) && (
                  <div className="flex items-start space-x-3">
                    <PhoneIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                    <div>
                      <p className="text-sm text-dark-text-muted">Phone</p>
                      <a
                        href={`tel:${lead.phone || lead.reply_phone}`}
                        className="text-terminal-400 hover:text-terminal-300 font-medium"
                      >
                        {lead.phone || lead.reply_phone}
                      </a>
                    </div>
                  </div>
                )}
                {lead.location && (
                  <div className="flex items-start space-x-3">
                    <MapPinIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                    <div>
                      <p className="text-sm text-dark-text-muted">Location</p>
                      <p className="text-dark-text-primary font-medium">
                        {lead.location.city}, {lead.location.state}
                      </p>
                    </div>
                  </div>
                )}
                {lead.url && (
                  <div className="flex items-start space-x-3">
                    <LinkIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                    <div>
                      <p className="text-sm text-dark-text-muted">Original URL</p>
                      <a
                        href={lead.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-terminal-400 hover:text-terminal-300 font-medium break-all"
                      >
                        {lead.url}
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            {lead.description && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Description</h2>
                <p className="text-dark-text-secondary whitespace-pre-wrap">{lead.description}</p>
              </div>
            )}

            {/* Job Details */}
            {(lead.compensation || lead.employment_type || lead.is_remote !== undefined) && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Job Details</h2>
                <div className="space-y-4">
                  {lead.compensation && (
                    <div className="flex items-start space-x-3">
                      <CurrencyDollarIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                      <div>
                        <p className="text-sm text-dark-text-muted">Compensation</p>
                        <p className="text-dark-text-primary font-medium">{lead.compensation}</p>
                      </div>
                    </div>
                  )}
                  {lead.employment_type && lead.employment_type.length > 0 && (
                    <div className="flex items-start space-x-3">
                      <BriefcaseIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                      <div>
                        <p className="text-sm text-dark-text-muted">Employment Type</p>
                        <p className="text-dark-text-primary font-medium">
                          {lead.employment_type.join(', ')}
                        </p>
                      </div>
                    </div>
                  )}
                  {lead.is_remote !== undefined && (
                    <div className="flex items-start space-x-3">
                      <MapPinIcon className="h-5 w-5 text-dark-text-muted mt-0.5" />
                      <div>
                        <p className="text-sm text-dark-text-muted">Remote Work</p>
                        <p className="text-dark-text-primary font-medium">
                          {lead.is_remote ? 'Yes' : 'No'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AI Analysis */}
            {lead.ai_analysis && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">AI Analysis</h2>
                <div className="space-y-4">
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <p className="text-dark-text-secondary whitespace-pre-wrap">{lead.ai_analysis}</p>
                  </div>
                  {lead.qualification_reasoning && (
                    <div>
                      <h3 className="text-sm font-medium text-dark-text-primary mb-2">Qualification Reasoning</h3>
                      <p className="text-dark-text-secondary">{lead.qualification_reasoning}</p>
                    </div>
                  )}
                  {lead.ai_model && (
                    <div className="flex items-center justify-between text-xs text-dark-text-muted">
                      <span>Model: {lead.ai_model}</span>
                      {lead.ai_cost && <span>Cost: ${lead.ai_cost.toFixed(4)}</span>}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Generated Email */}
            {(lead.generated_email_subject || lead.generated_email_body) && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Generated Email</h2>
                <div className="space-y-4">
                  {lead.generated_email_subject && (
                    <div>
                      <h3 className="text-sm font-medium text-dark-text-primary mb-2">Subject</h3>
                      <p className="text-dark-text-secondary">{lead.generated_email_subject}</p>
                    </div>
                  )}
                  {lead.generated_email_body && (
                    <div>
                      <h3 className="text-sm font-medium text-dark-text-primary mb-2">Body</h3>
                      <div className="bg-dark-border/30 rounded-lg p-4">
                        <p className="text-dark-text-secondary whitespace-pre-wrap">
                          {lead.generated_email_body}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Source-Specific Metadata */}
            {lead.source_metadata && Object.keys(lead.source_metadata).length > 0 && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">
                  {lead.source.replace('_', ' ').toUpperCase()} Details
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(lead.source_metadata).map(([key, value]) => {
                    if (value === null || value === undefined || value === '') return null
                    return (
                      <div key={key}>
                        <p className="text-xs text-dark-text-muted mb-1">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                        </p>
                        <p className="text-sm text-dark-text-primary">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Timeline */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Timeline</h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-terminal-500 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm text-dark-text-primary font-medium">Created</p>
                    <p className="text-xs text-dark-text-muted">{formatDate(lead.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm text-dark-text-primary font-medium">Scraped</p>
                    <p className="text-xs text-dark-text-muted">{formatDate(lead.scraped_at)}</p>
                  </div>
                </div>
                {lead.posted_at && (
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <p className="text-sm text-dark-text-primary font-medium">Posted</p>
                      <p className="text-xs text-dark-text-muted">{formatDate(lead.posted_at)}</p>
                    </div>
                  </div>
                )}
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-gray-500 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <p className="text-sm text-dark-text-primary font-medium">Last Updated</p>
                    <p className="text-xs text-dark-text-muted">{formatDate(lead.updated_at)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Categories */}
            {(lead.category || lead.subcategory) && (
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Categories</h2>
                <div className="space-y-2">
                  {lead.category && (
                    <span className="inline-block px-3 py-1 bg-dark-border rounded-full text-xs text-dark-text-primary">
                      {lead.category}
                    </span>
                  )}
                  {lead.subcategory && (
                    <span className="inline-block px-3 py-1 bg-dark-border rounded-full text-xs text-dark-text-primary ml-2">
                      {lead.subcategory}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <button className="w-full btn-secondary text-left justify-start">
                  <EnvelopeIcon className="h-4 w-4 mr-2" />
                  Send Email
                </button>
                <button className="w-full btn-secondary text-left justify-start">
                  <ChatBubbleLeftRightIcon className="h-4 w-4 mr-2" />
                  Add Note
                </button>
                <button className="w-full btn-secondary text-left justify-start">
                  <TagIcon className="h-4 w-4 mr-2" />
                  Change Status
                </button>
                <Link to={`/campaigns/new?lead_id=${lead.id}`} className="w-full btn-secondary text-left justify-start flex">
                  <PaperAirplaneIcon className="h-4 w-4 mr-2" />
                  Add to Campaign
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="card p-6">
          <div className="text-center py-12">
            <ChatBubbleLeftRightIcon className="h-16 w-16 text-dark-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-dark-text-primary mb-2">No Conversation History</h3>
            <p className="text-dark-text-secondary mb-6">
              Start a conversation with this lead by sending an email
            </p>
            <button className="btn-primary">
              <EnvelopeIcon className="h-4 w-4 mr-2" />
              Send First Email
            </button>
          </div>
        </div>
      )}

      {activeTab === 'campaigns' && (
        <div className="card p-6">
          <div className="text-center py-12">
            <PaperAirplaneIcon className="h-16 w-16 text-dark-text-muted mx-auto mb-4" />
            <h3 className="text-lg font-medium text-dark-text-primary mb-2">No Campaign Interactions</h3>
            <p className="text-dark-text-secondary mb-6">
              This lead hasn't been included in any campaigns yet
            </p>
            <Link to={`/campaigns/new?lead_id=${lead.id}`} className="btn-primary inline-flex items-center">
              <PaperAirplaneIcon className="h-4 w-4 mr-2" />
              Add to Campaign
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
