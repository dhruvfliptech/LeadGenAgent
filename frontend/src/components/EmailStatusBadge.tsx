import { EmailStatus } from '@/types/campaign'

interface EmailStatusBadgeProps {
  status: EmailStatus
  className?: string
}

export default function EmailStatusBadge({ status, className = '' }: EmailStatusBadgeProps) {
  const getStatusConfig = (status: EmailStatus) => {
    switch (status) {
      case 'queued':
        return {
          label: 'Queued',
          classes: 'bg-gray-100 text-gray-600 border-gray-300',
        }
      case 'sent':
        return {
          label: 'Sent',
          classes: 'bg-blue-100 text-blue-600 border-blue-300',
        }
      case 'delivered':
        return {
          label: 'Delivered',
          classes: 'bg-indigo-100 text-indigo-600 border-indigo-300',
        }
      case 'opened':
        return {
          label: 'Opened',
          classes: 'bg-purple-100 text-purple-600 border-purple-300',
        }
      case 'clicked':
        return {
          label: 'Clicked',
          classes: 'bg-violet-100 text-violet-600 border-violet-300',
        }
      case 'replied':
        return {
          label: 'Replied',
          classes: 'bg-green-100 text-green-600 border-green-300',
        }
      case 'bounced':
        return {
          label: 'Bounced',
          classes: 'bg-orange-100 text-orange-600 border-orange-300',
        }
      case 'failed':
        return {
          label: 'Failed',
          classes: 'bg-red-100 text-red-600 border-red-300',
        }
      default:
        return {
          label: status,
          classes: 'bg-gray-100 text-gray-600 border-gray-300',
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${config.classes} ${className}`}
    >
      {config.label}
    </span>
  )
}
