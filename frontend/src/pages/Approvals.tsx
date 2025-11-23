import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, workflowApprovalsApi } from '@/services/api'
import { formatRelativeTime } from '@/utils/dateFormat'
import {
  InboxStackIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilSquareIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type PendingApproval = {
  id: number
  approval_type: string
  resource_id: number
  resource_type: string
  resource_data: any
  status: string
  created_at: string
  timeout_at?: string
  metadata?: any
  workflow_execution_id: string
}

// Legacy support for old approval format
type LegacyApproval = {
  queue_id: number
  approval_id: number
  lead: {
    id: number
    title: string
    compensation?: string
    posted_at?: string
  }
  response: {
    subject?: string
    body: string
  }
  priority: 'low' | 'normal' | 'high' | 'urgent'
  sla_deadline?: string
  created_at?: string
}

export default function Approvals() {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<Record<number, boolean>>({})
  const [drafts, setDrafts] = useState<Record<number, { subject?: string; body: string }>>({})
  const [filterType] = useState<string>('all')
  const [showLegacy] = useState(true)

  // Fetch workflow approvals
  const { data: _workflowData, isLoading: workflowLoading } = useQuery<{ count: number; approvals: PendingApproval[]}>({
    queryKey: ['workflow-approvals-pending', filterType],
    queryFn: () => workflowApprovalsApi.getPending(filterType !== 'all' ? filterType : undefined).then(r => r.data),
    refetchInterval: 10000,
  })

  // Fetch legacy approvals (response approvals)
  const { data: _legacyData, isLoading: legacyLoading, error } = useQuery<{ count: number; approvals: LegacyApproval[]}>({
    queryKey: ['approvals-pending'],
    queryFn: () => api.get('/approvals/pending', { params: { limit: 20 } }).then(r => r.data),
    refetchInterval: 10000,
    enabled: showLegacy
  })

  const isLoading = workflowLoading || (showLegacy && legacyLoading)

  const approveMutation = useMutation({
    mutationFn: (payload: { id: number; subject?: string; body?: string }) =>
      api.post(`/approvals/${payload.id}/review`, {
        reviewer_id: 'web-ui',
        reviewer_name: 'Web UI',
        action: 'approve',
        modified_subject: payload.subject,
        modified_body: payload.body,
      }),
    onSuccess: () => {
      toast.success('Response approved and sent')
      queryClient.invalidateQueries({ queryKey: ['approvals-pending'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to approve')
  })

  const rejectMutation = useMutation({
    mutationFn: (payload: { id: number; notes: string }) =>
      api.post(`/approvals/${payload.id}/review`, {
        reviewer_id: 'web-ui',
        reviewer_name: 'Web UI',
        action: 'reject',
        review_notes: payload.notes || 'Not a fit',
      }),
    onSuccess: () => {
      toast.success('Response rejected')
      queryClient.invalidateQueries({ queryKey: ['approvals-pending'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Failed to reject')
  })

  const approveAllMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.allSettled(
        approvals.map(item =>
          api.post(`/approvals/${item.approval_id}/review`, {
            reviewer_id: 'web-ui',
            reviewer_name: 'Web UI',
            action: 'approve',
            modified_subject: item.response.subject,
            modified_body: item.response.body,
          })
        )
      )
      const successful = results.filter(r => r.status === 'fulfilled').length
      const failed = results.filter(r => r.status === 'rejected').length
      return { successful, failed }
    },
    onSuccess: (data) => {
      if (data.failed > 0) {
        toast.success(`Approved ${data.successful} responses. ${data.failed} failed.`)
      } else {
        toast.success(`All ${data.successful} responses approved and sent!`)
      }
      queryClient.invalidateQueries({ queryKey: ['approvals-pending'] })
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Failed to approve all')
    }
  })

  const approvals = _legacyData?.approvals || []
  const total = _legacyData?.count || 0

  const byPriority = useMemo(() => {
    const buckets: Record<string, number> = { urgent: 0, high: 0, normal: 0, low: 0 }
    approvals.forEach(a => { buckets[a.priority] = (buckets[a.priority] || 0) + 1 })
    return buckets
  }, [approvals])

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading approvals</div>
        <button className="btn-primary" onClick={() => queryClient.invalidateQueries({ queryKey: ['approvals-pending'] })}>Retry</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate flex items-center gap-2">
            <InboxStackIcon className="w-6 h-6 text-gray-500" /> Response Queue
          </h2>
          <p className="mt-1 text-sm text-gray-500">{total} pending • urgent {byPriority.urgent} • high {byPriority.high} • normal {byPriority.normal} • low {byPriority.low}</p>
        </div>
        {approvals.length > 0 && (
          <div className="mt-4 flex md:mt-0 md:ml-4">
            <button
              className="btn-primary inline-flex items-center gap-2"
              onClick={() => {
                if (window.confirm(`Are you sure you want to approve all ${approvals.length} responses?`)) {
                  approveAllMutation.mutate()
                }
              }}
              disabled={approveAllMutation.isPending}
            >
              <CheckIcon className="w-4 h-4" />
              {approveAllMutation.isPending ? 'Approving All...' : 'Approve All'}
            </button>
          </div>
        )}
      </div>

      {/* Queue */}
      <div className="grid grid-cols-1 gap-4">
        {isLoading && (
          <div className="card p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          </div>
        )}
        {!isLoading && approvals.length === 0 && (
          <div className="card p-12 text-center">
            <InboxStackIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No pending approvals</h3>
            <p className="text-gray-500">All responses have been reviewed. Generate new responses from the Leads page.</p>
          </div>
        )}
        {approvals.map(item => {
          const isEditing = editing[item.approval_id]
          const draft = drafts[item.approval_id] || { subject: item.response.subject, body: item.response.body }
          const due = item.sla_deadline ? formatRelativeTime(item.sla_deadline) : '—'
          return (
            <div key={item.approval_id} className="card">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-500">Lead</div>
                  <div className="font-medium">{item.lead.title}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Priority</div>
                  <div className={`font-medium capitalize ${item.priority === 'urgent' ? 'text-red-600' : item.priority === 'high' ? 'text-orange-600' : item.priority === 'normal' ? 'text-blue-600' : 'text-gray-600'}`}>{item.priority}</div>
                </div>
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500 mb-1">Generated Response</div>
                  {isEditing ? (
                    <div className="space-y-2">
                      <input
                        className="form-input"
                        placeholder="Subject"
                        value={draft.subject || ''}
                        onChange={e => setDrafts(prev => ({ ...prev, [item.approval_id]: { ...draft, subject: e.target.value } }))}
                      />
                      <textarea
                        className="form-input h-40"
                        value={draft.body}
                        onChange={e => setDrafts(prev => ({ ...prev, [item.approval_id]: { ...draft, body: e.target.value } }))}
                      />
                    </div>
                  ) : (
                    <div>
                      {item.response.subject && (
                        <div className="font-medium mb-2">{item.response.subject}</div>
                      )}
                      <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border border-gray-200 max-h-56 overflow-auto">
                        {item.response.body}
                      </pre>
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-sm text-gray-500 mb-1">Context</div>
                  <div className="space-y-1 text-sm text-gray-700">
                    <div>{item.lead.compensation ? `💰 ${item.lead.compensation}` : '—'}</div>
                    <div>{item.lead.posted_at ? `📅 Posted ${formatRelativeTime(item.lead.posted_at)}` : ''}</div>
                    <div>⏱️ SLA {due}</div>
                  </div>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <button
                  className="text-gray-600 hover:text-gray-900 inline-flex items-center gap-1"
                  onClick={() => setEditing(prev => ({ ...prev, [item.approval_id]: !prev[item.approval_id] }))}
                >
                  <PencilSquareIcon className="w-4 h-4" /> {isEditing ? 'Done' : 'Edit'}
                </button>
                <div className="flex items-center gap-3">
                  <button
                    className="btn-secondary inline-flex items-center gap-1"
                    onClick={() => rejectMutation.mutate({ id: item.approval_id, notes: 'Not relevant' })}
                    disabled={rejectMutation.isPending}
                  >
                    <XCircleIcon className="w-4 h-4" /> Reject
                  </button>
                  <button
                    className="btn-primary inline-flex items-center gap-1"
                    onClick={() => approveMutation.mutate({ id: item.approval_id, subject: draft.subject, body: draft.body })}
                    disabled={approveMutation.isPending}
                  >
                    <CheckCircleIcon className="w-4 h-4" /> Approve
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}




