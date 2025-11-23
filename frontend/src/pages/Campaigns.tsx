import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CampaignStatus } from '@/types/campaign'
import { mockCampaigns, getCampaignStats } from '@/mocks/campaigns.mock'
import CampaignsTable from '@/components/CampaignsTable'
import CampaignCard from '@/components/CampaignCard'
import { PlusIcon, Squares2X2Icon as ViewGridIcon, ListBulletIcon as ViewListIcon } from '@heroicons/react/24/outline'
import { EnvelopeIcon as MailIcon, UsersIcon, ChartBarIcon, CursorArrowRaysIcon as CursorClickIcon } from '@heroicons/react/24/solid'

export default function Campaigns() {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid')
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | 'all'>('all')

  const stats = getCampaignStats()

  const filteredCampaigns =
    statusFilter === 'all'
      ? mockCampaigns
      : mockCampaigns.filter((c) => c.status === statusFilter)

  const statusCounts = {
    all: mockCampaigns.length,
    sending: mockCampaigns.filter((c) => c.status === 'sending').length,
    scheduled: mockCampaigns.filter((c) => c.status === 'scheduled').length,
    completed: mockCampaigns.filter((c) => c.status === 'completed').length,
    draft: mockCampaigns.filter((c) => c.status === 'draft').length,
    paused: mockCampaigns.filter((c) => c.status === 'paused').length,
    cancelled: mockCampaigns.filter((c) => c.status === 'cancelled').length,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">Email Campaigns</h1>
          <p className="mt-1 text-sm text-dark-text-muted">
            Manage and track your email outreach campaigns
          </p>
        </div>
        <Link
          to="/campaigns/new"
          className="btn-primary inline-flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Campaign
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card-terminal p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <MailIcon className="h-10 w-10 text-terminal-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dark-text-muted">Total Sent</p>
              <p className="text-2xl font-bold text-dark-text-primary">{stats.total_sent}</p>
            </div>
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UsersIcon className="h-10 w-10 text-terminal-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dark-text-muted">Avg Open Rate</p>
              <p className="text-2xl font-bold text-dark-text-primary">
                {stats.avg_open_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CursorClickIcon className="h-10 w-10 text-terminal-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dark-text-muted">Avg Click Rate</p>
              <p className="text-2xl font-bold text-dark-text-primary">
                {stats.avg_click_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-10 w-10 text-terminal-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dark-text-muted">Avg Reply Rate</p>
              <p className="text-2xl font-bold text-dark-text-primary">
                {stats.avg_reply_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & View Controls */}
      <div className="card-terminal p-4">
        <div className="flex items-center justify-between">
          {/* Status Filters */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === 'all'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
            >
              All ({statusCounts.all})
            </button>
            <button
              onClick={() => setStatusFilter('sending')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === 'sending'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
            >
              Sending ({statusCounts.sending})
            </button>
            <button
              onClick={() => setStatusFilter('scheduled')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === 'scheduled'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
            >
              Scheduled ({statusCounts.scheduled})
            </button>
            <button
              onClick={() => setStatusFilter('completed')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === 'completed'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
            >
              Completed ({statusCounts.completed})
            </button>
            <button
              onClick={() => setStatusFilter('draft')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                statusFilter === 'draft'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
            >
              Drafts ({statusCounts.draft})
            </button>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'grid'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
              title="Grid view"
            >
              <ViewGridIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'table'
                  ? 'bg-terminal-500/20 text-terminal-300 border border-terminal-500/50'
                  : 'bg-dark-surface text-dark-text-muted hover:bg-dark-hover border border-dark-border'
              }`}
              title="Table view"
            >
              <ViewListIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Campaigns Display */}
      {filteredCampaigns.length === 0 ? (
        <div className="card-terminal p-12 text-center">
          <MailIcon className="mx-auto h-12 w-12 text-dark-text-muted" />
          <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No campaigns</h3>
          <p className="mt-1 text-sm text-dark-text-muted">
            Get started by creating a new email campaign.
          </p>
          <div className="mt-6">
            <Link
              to="/campaigns/new"
              className="btn-primary inline-flex items-center"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Campaign
            </Link>
          </div>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCampaigns.map((campaign) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </div>
      ) : (
        <CampaignsTable campaigns={filteredCampaigns} />
      )}
    </div>
  )
}
