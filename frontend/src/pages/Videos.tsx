// Main Videos page for Journey 3: Demo Site → Video Creation

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  VideoCameraIcon,
  EyeIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  Squares2X2Icon,
  ListBulletIcon
} from '@heroicons/react/24/outline'
import { mockVideos, getTotalVideoStats, MockVideo } from '@/mocks/videos.mock'
import VideoCard from '@/components/VideoCard'
import CreateVideoWizard from '@/components/CreateVideoWizard'
import toast from 'react-hot-toast'

type VideoStatusFilter = 'all' | 'completed' | 'generating_script' | 'generating_voiceover' | 'recording_screen' | 'composing' | 'draft' | 'failed'

export default function Videos() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<VideoStatusFilter>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [isCreateWizardOpen, setIsCreateWizardOpen] = useState(false)

  // Get stats from mock data
  const stats = getTotalVideoStats()

  // Filter videos
  const filteredVideos = mockVideos.filter(video => {
    const matchesStatus = statusFilter === 'all' || video.status === statusFilter
    const matchesSearch = !searchQuery ||
      video.lead_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      video.demo_url.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesStatus && matchesSearch
  })

  const handleVideoClick = (video: MockVideo) => {
    if (video.status === 'completed') {
      navigate(`/videos/${video.video_id}`)
    } else {
      toast('Video is still being generated', { icon: '⏳' })
    }
  }

  const handleDownload = (video: MockVideo) => {
    if (video.status !== 'completed' || !video.final_video_url) {
      toast.error('Video is not ready for download')
      return
    }
    toast.success('Downloading video...')
    // Simulate download
    window.open(video.final_video_url, '_blank')
  }

  const handleShare = (video: MockVideo) => {
    if (video.status !== 'completed') {
      toast.error('Video is not ready to share')
      return
    }
    navigator.clipboard.writeText(video.final_video_url || video.demo_url)
    toast.success('Video URL copied to clipboard!')
  }

  const handleDelete = (video: MockVideo) => {
    if (confirm(`Delete video for "${video.lead_title}"?`)) {
      toast.success('Video deleted (mock)')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Demo Videos
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Create personalized demo videos from generated sites
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsCreateWizardOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <PlusIcon className="w-5 h-5" />
            Create Video
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <VideoCameraIcon className="h-6 w-6 text-terminal-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-dark-text-primary">{stats.total_videos}</div>
              <div className="text-sm font-medium text-dark-text-secondary">Total Videos</div>
              <div className="text-xs text-dark-text-muted mt-1">
                {stats.completed} completed
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CloudArrowUpIcon className="h-6 w-6 text-yellow-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-dark-text-primary">
                {stats.in_progress}
              </div>
              <div className="text-sm font-medium text-dark-text-secondary">In Progress</div>
              <div className="text-xs text-dark-text-muted mt-1">
                {stats.failed} failed
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <EyeIcon className="h-6 w-6 text-blue-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-dark-text-primary">
                {stats.total_views}
              </div>
              <div className="text-sm font-medium text-dark-text-secondary">Total Views</div>
              <div className="text-xs text-dark-text-muted mt-1">
                {stats.avg_watch_percentage.toFixed(0)}% avg watch
              </div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-6 w-6 text-green-500" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-terminal-400 font-mono">
                ${stats.total_cost.toFixed(2)}
              </div>
              <div className="text-sm font-medium text-dark-text-secondary">Total Cost</div>
              <div className="text-xs text-dark-text-muted mt-1">
                {(stats.avg_generation_time / 60).toFixed(1)}m avg time
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <FunnelIcon className="h-5 w-5 text-dark-text-secondary flex-shrink-0" />

          {/* Search */}
          <div className="flex-1 w-full sm:w-auto">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-dark-text-muted" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title or URL..."
                className="form-input pl-10 w-full"
              />
            </div>
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as VideoStatusFilter)}
            className="form-input w-full sm:w-auto"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="generating_script">Generating Script</option>
            <option value="generating_voiceover">Generating Voiceover</option>
            <option value="recording_screen">Recording Screen</option>
            <option value="composing">Composing</option>
            <option value="draft">Draft</option>
            <option value="failed">Failed</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 border border-dark-border rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-secondary hover:text-dark-text-primary'
              }`}
              title="Grid View"
            >
              <Squares2X2Icon className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-secondary hover:text-dark-text-primary'
              }`}
              title="List View"
            >
              <ListBulletIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Videos Grid/List */}
      {filteredVideos.length > 0 ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {filteredVideos.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onClick={() => handleVideoClick(video)}
              onDownload={() => handleDownload(video)}
              onShare={() => handleShare(video)}
              onDelete={() => handleDelete(video)}
              viewMode={viewMode}
            />
          ))}
        </div>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <VideoCameraIcon className="mx-auto h-12 w-12 text-dark-text-muted" />
            <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No videos found</h3>
            <p className="mt-1 text-sm text-dark-text-secondary">
              {searchQuery || statusFilter !== 'all'
                ? 'Try adjusting your filters.'
                : 'Get started by creating your first demo video.'}
            </p>
            <div className="mt-6">
              <button
                onClick={() => setIsCreateWizardOpen(true)}
                className="btn-primary inline-flex items-center gap-2"
              >
                <PlusIcon className="w-5 h-5" />
                Create Video
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Video Wizard */}
      <CreateVideoWizard
        isOpen={isCreateWizardOpen}
        onClose={() => setIsCreateWizardOpen(false)}
        onSuccess={() => {
          setIsCreateWizardOpen(false)
          toast.success('Video generation started!')
        }}
      />
    </div>
  )
}
