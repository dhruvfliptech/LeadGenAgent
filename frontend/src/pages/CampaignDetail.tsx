import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { mockCampaigns } from '@/mocks/campaigns.mock'
import CampaignDetailView from '@/components/CampaignDetailView'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(() => {
    const found = mockCampaigns.find((c) => c.id === parseInt(id || '0'))
    return found || mockCampaigns[0]
  })

  const handlePause = () => {
    setCampaign((prev) => ({ ...prev, status: 'paused' }))
    // In real app, would call API
    console.log('Pausing campaign:', campaign.id)
  }

  const handleResume = () => {
    setCampaign((prev) => ({ ...prev, status: 'sending' }))
    // In real app, would call API
    console.log('Resuming campaign:', campaign.id)
  }

  const handleCancel = () => {
    if (window.confirm('Are you sure you want to cancel this campaign? This action cannot be undone.')) {
      setCampaign((prev) => ({ ...prev, status: 'cancelled' }))
      // In real app, would call API
      console.log('Cancelling campaign:', campaign.id)
    }
  }

  if (!campaign) {
    return (
      <div className="py-12 text-center">
        <p className="text-gray-500">Campaign not found</p>
        <Link to="/campaigns" className="text-blue-600 hover:text-blue-700 mt-2 inline-block">
          Back to Campaigns
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to="/campaigns"
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeftIcon className="h-4 w-4 mr-1" />
        Back to Campaigns
      </Link>

      {/* Campaign Detail View */}
      <CampaignDetailView
        campaign={campaign}
        onPause={handlePause}
        onResume={handleResume}
        onCancel={handleCancel}
      />
    </div>
  )
}
