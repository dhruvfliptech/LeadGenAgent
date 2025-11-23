import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: string
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
}

const variantStyles = {
  default: 'bg-gray-100 text-gray-800 border-gray-200',
  success: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  error: 'bg-red-100 text-red-800 border-red-200',
  info: 'bg-blue-100 text-blue-800 border-blue-200',
}

const statusVariantMap: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
  // Scrape jobs
  queued: 'default',
  running: 'info',
  paused: 'warning',
  completed: 'success',
  failed: 'error',
  cancelled: 'default',

  // Leads
  new: 'info',
  contacted: 'default',
  replied: 'success',
  qualified: 'success',
  won: 'success',
  lost: 'error',

  // Enrichment
  pending: 'default',
  enriching: 'info',
  enriched: 'success',

  // Campaigns
  draft: 'default',
  scheduled: 'warning',
  sending: 'info',
  active: 'info',
  inactive: 'default',

  // Demo sites & Videos
  analyzing: 'info',
  planning: 'info',
  generating: 'info',
  deploying: 'info',
  deployed: 'success',

  // Approvals
  approved: 'success',
  rejected: 'error',
  expired: 'default',

  // Workflows
  error: 'error',
  success: 'success',
  waiting: 'warning',

  // Webhooks
  delivered: 'success',
  retrying: 'warning',

  // Emails
  sent: 'success',
  opened: 'success',
  clicked: 'success',
  bounced: 'error',

  // Conversations
  needs_reply: 'error',
  closed: 'default',
  snoozed: 'warning',
}

export function StatusBadge({ status, variant, className }: StatusBadgeProps) {
  const autoVariant = statusVariantMap[status.toLowerCase()] || 'default'
  const finalVariant = variant || autoVariant

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        variantStyles[finalVariant],
        className
      )}
    >
      {status}
    </span>
  )
}
