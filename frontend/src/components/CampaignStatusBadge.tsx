import { CampaignStatus } from '@/types/campaign'

interface CampaignStatusBadgeProps {
  status: CampaignStatus
  className?: string
}

export default function CampaignStatusBadge({ status, className = '' }: CampaignStatusBadgeProps) {
  const getStatusConfig = (status: CampaignStatus) => {
    switch (status) {
      case 'draft':
        return {
          label: 'Draft',
          classes: 'bg-gray-100 text-gray-700 border-gray-300',
        }
      case 'scheduled':
        return {
          label: 'Scheduled',
          classes: 'bg-blue-100 text-blue-700 border-blue-300',
        }
      case 'sending':
        return {
          label: 'Sending',
          classes: 'bg-yellow-100 text-yellow-700 border-yellow-300 animate-pulse',
        }
      case 'paused':
        return {
          label: 'Paused',
          classes: 'bg-orange-100 text-orange-700 border-orange-300',
        }
      case 'completed':
        return {
          label: 'Completed',
          classes: 'bg-green-100 text-green-700 border-green-300',
        }
      case 'cancelled':
        return {
          label: 'Cancelled',
          classes: 'bg-red-100 text-red-700 border-red-300',
        }
      default:
        return {
          label: status,
          classes: 'bg-gray-100 text-gray-700 border-gray-300',
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.classes} ${className}`}
    >
      {config.label}
    </span>
  )
}
