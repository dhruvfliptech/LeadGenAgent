import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  EyeIcon,
  PhoneIcon,
  EnvelopeIcon,
  FunnelIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  BoltIcon,
  SparklesIcon,
  PaperAirplaneIcon,
  StarIcon,
  HandThumbUpIcon,
  HandThumbDownIcon
} from '@heroicons/react/24/outline'
import { HandThumbUpIcon as HandThumbUpSolidIcon, HandThumbDownIcon as HandThumbDownSolidIcon } from '@heroicons/react/24/solid'
import { api } from '@/services/api'
import { aiMvpApi } from '@/services/phase3Api'
import { Lead, LeadSource } from '@/types/lead'
// @ts-ignore - formatDate utility function
import { formatDate, formatRelativeTime } from '@/utils/dateFormat'
import toast from 'react-hot-toast'
import SourceBadge from '@/components/SourceBadge'

export default function Leads() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({
    status: '',
    location_id: '',
    is_processed: '',
    is_contacted: '',
    source: '' as LeadSource | ''
  })
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [actionLoading, setActionLoading] = useState<Record<number, string | null>>({})

  const { data: leads, isLoading, error } = useQuery<Lead[]>({
    queryKey: ['leads', filters],
    queryFn: () => {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value)
      })
      return api.get(`/leads?${params.toString()}`).then(res => res.data)
    },
  })

  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: () => api.get('/locations').then(res => res.data),
  })

  const generateResponseMutation = useMutation<any, any, Lead>({
    mutationFn: (lead: Lead) =>
      api.post('/approvals/generate-and-queue', { lead_id: lead.id, auto_submit: true, use_ai: true }),
    // @ts-ignore - lead parameter in onSuccess
    onSuccess: (_, lead) => {
      toast.success('Response generated and queued for approval')
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Failed to generate response')
    }
  })

  const analyzeWebsiteMutation = useMutation({
    mutationFn: (lead: Lead) =>
      aiMvpApi.analyzeWebsite({
        url: lead.url,
        lead_value: lead.price || 10000,
        lead_id: lead.id
      }),
    onSuccess: (response, lead) => {
      const data = response.data
      toast.success(`Website analyzed! Cost: $${data.ai_cost.toFixed(4)}`)

      // Update lead with AI analysis
      updateLeadMutation.mutate({
        leadId: lead.id,
        data: {
          ai_analysis: data.ai_analysis,
          ai_model: data.ai_model,
          ai_cost: data.ai_cost,
          ai_request_id: data.ai_request_id
        }
      })
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Failed to analyze website')
    }
  })

  const generateEmailMutation = useMutation({
    mutationFn: ({ lead, analysis }: { lead: Lead, analysis: string }) => {
      const companyName = lead.title.split('-')[0]?.trim() || lead.title.slice(0, 50)
      return aiMvpApi.generateEmail({
        prospect_name: lead.contact_name || 'there',
        company_name: companyName,
        website_analysis: analysis,
        our_service_description: 'AI-powered lead generation and outreach automation that helps businesses find and connect with qualified leads from Craigslist',
        lead_value: lead.price || 10000,
        lead_id: lead.id
      })
    },
    onSuccess: (response, { lead }) => {
      const data = response.data
      toast.success(`Email generated! Cost: $${data.ai_cost.toFixed(4)}`)

      // Update lead with generated email
      updateLeadMutation.mutate({
        leadId: lead.id,
        data: {
          generated_email_subject: data.subject,
          generated_email_body: data.body
        }
      })
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Failed to generate email')
    }
  })

  const sendEmailMutation = useMutation({
    mutationFn: ({ lead, subject, body }: { lead: Lead; subject: string; body: string }) => {
      const toEmail = lead.reply_email || lead.email
      if (!toEmail) {
        throw new Error('No email address available')
      }
      return aiMvpApi.sendEmail({
        to_email: toEmail,
        subject,
        html_body: `<p>${body.replace(/\n/g, '<br>')}</p>`,
        tag: 'ai-generated',
        lead_id: lead.id,
        track_opens: true,
        track_links: true
      })
    },
    onSuccess: (_, { lead }) => {
      toast.success('Email sent successfully!')
      // Mark as contacted
      updateLeadMutation.mutate({
        leadId: lead.id,
        data: { is_contacted: true }
      })
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || e.message || 'Failed to send email')
    }
  })

  const updateLeadMutation = useMutation({
    mutationFn: ({ leadId, data }: { leadId: number; data: Partial<Lead> }) =>
      api.put(`/leads/${leadId}`, data),
    onMutate: async ({ leadId, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['leads'] })

      // Snapshot the previous value
      const previousLeads = queryClient.getQueryData<Lead[]>(['leads', filters])

      // Optimistically update
      queryClient.setQueryData<Lead[]>(['leads', filters], (old) =>
        old?.map(lead => lead.id === leadId ? { ...lead, ...data } : lead)
      )

      return { previousLeads }
    },
    onError: (e: any, _, context) => {
      // Rollback on error
      queryClient.setQueryData(['leads', filters], context?.previousLeads)
      toast.error(e?.response?.data?.detail || 'Failed to update lead')
    },
    onSuccess: (_, { data }) => {
      const action = data.is_processed ? 'marked as processed' :
                     data.status === 'rejected' ? 'archived' : 'updated'
      toast.success(`Lead ${action}`)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
    }
  })

  const getStatusBadge = (status: string) => {
    const styles = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      qualified: 'bg-green-100 text-green-800',
      converted: 'bg-purple-100 text-purple-800',
      rejected: 'bg-red-100 text-red-800'
    }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    )
  }

  const toggleExpanded = (id: number) =>
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }))

  const handleGenerateResponse = (lead: Lead) => {
    setActionLoading(prev => ({ ...prev, [lead.id]: 'generate' }))
    generateResponseMutation.mutate(lead, {
      onSettled: () => setActionLoading(prev => ({ ...prev, [lead.id]: null }))
    })
  }

  const handleAnalyzeWebsite = (lead: Lead) => {
    setActionLoading(prev => ({ ...prev, [lead.id]: 'analyze' }))
    analyzeWebsiteMutation.mutate(lead, {
      onSettled: () => setActionLoading(prev => ({ ...prev, [lead.id]: null }))
    })
  }

  const handleGenerateEmail = (lead: Lead) => {
    if (!lead.ai_analysis) {
      toast.error('Please analyze the website first')
      return
    }
    setActionLoading(prev => ({ ...prev, [lead.id]: 'email' }))
    generateEmailMutation.mutate({ lead, analysis: lead.ai_analysis }, {
      onSettled: () => setActionLoading(prev => ({ ...prev, [lead.id]: null }))
    })
  }

  const handleSendEmail = (lead: Lead) => {
    if (!lead.generated_email_subject || !lead.generated_email_body) {
      toast.error('Please generate an email first')
      return
    }
    if (!lead.email && !lead.reply_email) {
      toast.error('No email address available')
      return
    }
    setActionLoading(prev => ({ ...prev, [lead.id]: 'send' }))
    sendEmailMutation.mutate({
      lead,
      subject: lead.generated_email_subject,
      body: lead.generated_email_body
    }, {
      onSettled: () => setActionLoading(prev => ({ ...prev, [lead.id]: null }))
    })
  }

  const handleUpdateLead = (leadId: number, data: Partial<Lead>, action: string) => {
    setActionLoading(prev => ({ ...prev, [leadId]: action }))
    updateLeadMutation.mutate({ leadId, data }, {
      onSettled: () => setActionLoading(prev => ({ ...prev, [leadId]: null }))
    })
  }

  const handleFeedback = (lead: Lead, feedback: 'positive' | 'negative') => {
    const newFeedback = lead.user_feedback === feedback ? null : feedback
    updateLeadMutation.mutate({
      leadId: lead.id,
      data: { user_feedback: newFeedback }
    })
    toast.success(newFeedback ? `Marked as ${feedback === 'positive' ? 'good' : 'bad'} lead` : 'Feedback removed')
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading leads</div>
        <button 
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex-1 min-w-0">
        <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          Leads
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Manage and track your scraped leads
        </p>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex items-center space-x-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
            <select
              value={filters.source}
              onChange={(e) => setFilters(prev => ({ ...prev, source: e.target.value as LeadSource | '' }))}
              className="form-input"
            >
              <option value="">All Sources</option>
              <option value="craigslist">Craigslist</option>
              <option value="google_maps">Google Maps</option>
              <option value="linkedin">LinkedIn</option>
              <option value="indeed">Indeed</option>
              <option value="monster">Monster</option>
              <option value="ziprecruiter">ZipRecruiter</option>
            </select>

            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="form-input"
            >
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="contacted">Contacted</option>
              <option value="qualified">Qualified</option>
              <option value="converted">Converted</option>
              <option value="rejected">Rejected</option>
            </select>

            <select
              value={filters.location_id}
              onChange={(e) => setFilters(prev => ({ ...prev, location_id: e.target.value }))}
              className="form-input"
            >
              <option value="">All Locations</option>
              {locations?.map((location: any) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>

            <select
              value={filters.is_processed}
              onChange={(e) => setFilters(prev => ({ ...prev, is_processed: e.target.value }))}
              className="form-input"
            >
              <option value="">Processing Status</option>
              <option value="true">Processed</option>
              <option value="false">Unprocessed</option>
            </select>

            <select
              value={filters.is_contacted}
              onChange={(e) => setFilters(prev => ({ ...prev, is_contacted: e.target.value }))}
              className="form-input"
            >
              <option value="">Contact Status</option>
              <option value="true">Contacted</option>
              <option value="false">Not Contacted</option>
            </select>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      {isLoading ? (
        <div className="card">
          <div className="p-6 space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : leads && leads.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lead
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Scraped
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => {
                  const scorePct = Math.round(((lead.qualification_score ?? 0) * 100))
                  const scoreClass = scorePct >= 70
                    ? 'bg-green-100 text-green-800'
                    : scorePct >= 40
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                  return (
                    <>
                      <tr key={lead.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-start gap-2">
                            <button onClick={() => toggleExpanded(lead.id)} className="mt-0.5 text-gray-500 hover:text-gray-700">
                              {expanded[lead.id] ? <ChevronDownIcon className="w-4 h-4" /> : <ChevronRightIcon className="w-4 h-4" />}
                            </button>
                            <div className="flex flex-col gap-1">
                              <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                                {lead.title}
                              </div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <SourceBadge source={lead.source || 'craigslist'} size="sm" />
                                {lead.price && (
                                  <span className="text-sm text-green-600 font-semibold">
                                    ${lead.price.toLocaleString()}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`px-2 py-1 rounded text-sm font-medium inline-flex items-center gap-1 ${scoreClass}`}>
                            <BoltIcon className="w-3.5 h-3.5" /> {isNaN(scorePct) ? '—' : `${scorePct}%`}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{lead.location.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            {getStatusBadge(lead.status)}
                            <div className="flex space-x-1">
                              {lead.is_processed && (
                                <div className="w-2 h-2 bg-green-400 rounded-full" title="Processed" />
                              )}
                              {lead.is_contacted && (
                                <div className="w-2 h-2 bg-blue-400 rounded-full" title="Contacted" />
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            {lead.phone && (
                              <PhoneIcon className="w-4 h-4 text-green-500" />
                            )}
                            {lead.email && (
                              <EnvelopeIcon className="w-4 h-4 text-blue-500" />
                            )}
                            {!lead.phone && !lead.email && (
                              <span className="text-xs text-gray-400">No contact info</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatRelativeTime(lead.scraped_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex items-center justify-end space-x-3">
                            {/* Lead Quality Feedback */}
                            <div className="flex items-center space-x-1 border-r border-gray-300 pr-3">
                              <button
                                onClick={() => handleFeedback(lead, 'positive')}
                                className={`transition-colors ${
                                  lead.user_feedback === 'positive'
                                    ? 'text-green-600'
                                    : 'text-gray-400 hover:text-green-500'
                                }`}
                                title="Good lead"
                              >
                                {lead.user_feedback === 'positive' ? (
                                  <HandThumbUpSolidIcon className="w-4 h-4" />
                                ) : (
                                  <HandThumbUpIcon className="w-4 h-4" />
                                )}
                              </button>
                              <button
                                onClick={() => handleFeedback(lead, 'negative')}
                                className={`transition-colors ${
                                  lead.user_feedback === 'negative'
                                    ? 'text-red-600'
                                    : 'text-gray-400 hover:text-red-500'
                                }`}
                                title="Bad lead"
                              >
                                {lead.user_feedback === 'negative' ? (
                                  <HandThumbDownSolidIcon className="w-4 h-4" />
                                ) : (
                                  <HandThumbDownIcon className="w-4 h-4" />
                                )}
                              </button>
                            </div>
                            <a
                              href={lead.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-600 hover:text-primary-900"
                              title="View post"
                            >
                              <EyeIcon className="w-4 h-4" />
                            </a>
                            <button
                              className="text-purple-600 hover:text-purple-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                              onClick={() => handleAnalyzeWebsite(lead)}
                              disabled={!!actionLoading[lead.id]}
                              title="Analyze website with AI"
                            >
                              <SparklesIcon className="w-4 h-4" />
                              {actionLoading[lead.id] === 'analyze' ? 'Analyzing...' : lead.ai_analysis ? 'Re-analyze' : 'AI Analyze'}
                            </button>
                            {lead.ai_analysis && (
                              <button
                                className="text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                                onClick={() => handleGenerateEmail(lead)}
                                disabled={!!actionLoading[lead.id]}
                                title="Generate personalized email"
                              >
                                <PaperAirplaneIcon className="w-4 h-4" />
                                {actionLoading[lead.id] === 'email' ? 'Generating...' : lead.generated_email_subject ? 'Regenerate' : 'Email'}
                              </button>
                            )}
                            <button
                              className="text-green-600 hover:text-green-800 disabled:opacity-50 disabled:cursor-not-allowed"
                              onClick={() => handleGenerateResponse(lead)}
                              disabled={actionLoading[lead.id] === 'generate'}
                            >
                              {actionLoading[lead.id] === 'generate' ? 'Generating...' : 'Generate'}
                            </button>
                            <button
                              className="text-yellow-600 hover:text-yellow-800 disabled:opacity-50 disabled:cursor-not-allowed"
                              onClick={() => handleUpdateLead(lead.id, { is_processed: true }, 'skip')}
                              disabled={!!actionLoading[lead.id]}
                            >
                              {actionLoading[lead.id] === 'skip' ? 'Skipping...' : 'Skip'}
                            </button>
                            <button
                              className="text-red-600 hover:text-red-800 disabled:opacity-50 disabled:cursor-not-allowed"
                              onClick={() => handleUpdateLead(lead.id, { status: 'rejected' }, 'archive')}
                              disabled={!!actionLoading[lead.id]}
                            >
                              {actionLoading[lead.id] === 'archive' ? 'Archiving...' : 'Archive'}
                            </button>
                          </div>
                        </td>
                      </tr>
                      {expanded[lead.id] && (
                        <tr>
                          <td colSpan={7} className="bg-gray-50 px-6 py-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                              <div className="space-y-1">
                                <div className="font-medium text-gray-700">Metadata</div>
                                <div className="text-gray-600">{lead.compensation ? `💰 ${lead.compensation}` : '—'}</div>
                                <div className="text-gray-600">{lead.employment_type?.length ? `🧾 ${lead.employment_type.join(', ')}` : '—'}</div>
                                <div className="text-gray-600">{lead.is_remote ? '📍 Remote OK' : ''}</div>
                                <div className="text-gray-600">{lead.posted_at ? `📅 Posted ${formatRelativeTime(lead.posted_at)}` : ''}</div>
                              </div>
                              <div className="space-y-1">
                                <div className="font-medium text-gray-700">Contact</div>
                                <div className="text-gray-600">{lead.reply_email ? `📧 ${lead.reply_email}` : lead.email ? `📧 ${lead.email}` : '—'}</div>
                                <div className="text-gray-600">{lead.reply_phone ? `📞 ${lead.reply_phone}` : lead.phone ? `📞 ${lead.phone}` : ''}</div>
                                <div className="text-gray-600">{lead.contact_name ? `👤 ${lead.contact_name}` : ''}</div>
                              </div>
                              <div className="space-y-1">
                                <div className="font-medium text-gray-700">ML Insights</div>
                                <div className="text-gray-600 whitespace-pre-line break-words max-h-28 overflow-auto">
                                  {lead.qualification_reasoning || 'No reasoning available'}
                                </div>
                              </div>
                            </div>

                            {/* Source-Specific Metadata */}
                            {lead.source_metadata && (
                              <div className="mt-4 pt-4 border-t border-gray-200">
                                <div className="font-medium text-gray-700 mb-2">Source Details</div>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                                  {/* Google Maps specific */}
                                  {lead.source === 'google_maps' && (
                                    <>
                                      {lead.source_metadata.rating && (
                                        <div className="flex items-center gap-2 text-gray-600">
                                          <StarIcon className="w-4 h-4 text-yellow-500" />
                                          <span>{lead.source_metadata.rating} stars</span>
                                          {lead.source_metadata.review_count && (
                                            <span className="text-gray-500">({lead.source_metadata.review_count} reviews)</span>
                                          )}
                                        </div>
                                      )}
                                      {lead.source_metadata.business_category && (
                                        <div className="text-gray-600">Category: {lead.source_metadata.business_category}</div>
                                      )}
                                      {lead.source_metadata.google_maps_url && (
                                        <a href={lead.source_metadata.google_maps_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                          View on Google Maps
                                        </a>
                                      )}
                                    </>
                                  )}

                                  {/* LinkedIn specific */}
                                  {lead.source === 'linkedin' && (
                                    <>
                                      {lead.source_metadata.job_title && (
                                        <div className="text-gray-600">Job: {lead.source_metadata.job_title}</div>
                                      )}
                                      {lead.source_metadata.company_name && (
                                        <div className="text-gray-600">Company: {lead.source_metadata.company_name}</div>
                                      )}
                                      {lead.source_metadata.company_size && (
                                        <div className="text-gray-600">Size: {lead.source_metadata.company_size} employees</div>
                                      )}
                                      {lead.source_metadata.linkedin_url && (
                                        <a href={lead.source_metadata.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                          View on LinkedIn
                                        </a>
                                      )}
                                    </>
                                  )}

                                  {/* Job boards specific */}
                                  {['indeed', 'monster', 'ziprecruiter'].includes(lead.source) && (
                                    <>
                                      {lead.source_metadata.salary && (
                                        <div className="text-gray-600">Salary: {lead.source_metadata.salary}</div>
                                      )}
                                      {lead.source_metadata.posted_date && (
                                        <div className="text-gray-600">Posted: {formatRelativeTime(lead.source_metadata.posted_date)}</div>
                                      )}
                                      {lead.source_metadata.job_url && (
                                        <a href={lead.source_metadata.job_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                          View Job Listing
                                        </a>
                                      )}
                                    </>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* AI MVP Analysis */}
                            {lead.ai_analysis && (
                              <div className="mt-4 pt-4 border-t border-gray-200">
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <SparklesIcon className="w-5 h-5 text-purple-500" />
                                    <div className="font-medium text-gray-700">AI Website Analysis</div>
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {lead.ai_model} • ${lead.ai_cost?.toFixed(4)}
                                  </div>
                                </div>
                                <div className="text-sm text-gray-600 whitespace-pre-line bg-white p-3 rounded border border-gray-200 max-h-48 overflow-auto">
                                  {lead.ai_analysis}
                                </div>
                              </div>
                            )}

                            {/* Generated Email */}
                            {lead.generated_email_subject && lead.generated_email_body && (
                              <div className="mt-4 pt-4 border-t border-gray-200">
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-2">
                                    <PaperAirplaneIcon className="w-5 h-5 text-blue-500" />
                                    <div className="font-medium text-gray-700">Generated Email</div>
                                  </div>
                                  {(lead.email || lead.reply_email) && (
                                    <button
                                      onClick={() => handleSendEmail(lead)}
                                      disabled={actionLoading[lead.id] === 'send'}
                                      className="btn-primary text-sm py-1.5 px-3 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                      <EnvelopeIcon className="w-4 h-4" />
                                      {actionLoading[lead.id] === 'send' ? 'Sending...' : 'Send Email'}
                                    </button>
                                  )}
                                </div>
                                <div className="bg-white p-3 rounded border border-gray-200 space-y-2">
                                  <div>
                                    <div className="text-xs font-medium text-gray-500 mb-1">Subject:</div>
                                    <div className="text-sm text-gray-900 font-medium">{lead.generated_email_subject}</div>
                                  </div>
                                  <div>
                                    <div className="text-xs font-medium text-gray-500 mb-1">Body:</div>
                                    <div className="text-sm text-gray-600 whitespace-pre-line max-h-48 overflow-auto">
                                      {lead.generated_email_body}
                                    </div>
                                  </div>
                                  {!lead.email && !lead.reply_email && (
                                    <div className="text-xs text-red-500 mt-2">
                                      ⚠️ No email address available - cannot send email
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <div className="text-gray-500">No leads found matching your filters.</div>
            <Link to="/scraper" className="btn-primary mt-4 inline-block">
              Start Scraping
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}