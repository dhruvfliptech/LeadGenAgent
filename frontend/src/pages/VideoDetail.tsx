// Video detail page with player, tabs, script viewer, and stats - Journey 3

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ArrowDownTrayIcon,
  ShareIcon,
  PlayIcon,
  TrashIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ChartBarIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { mockVideos } from '@/mocks/videos.mock'
import ScriptViewer from '@/components/ScriptViewer'
import VideoStatsPanel from '@/components/VideoStatsPanel'
import toast from 'react-hot-toast'

type TabType = 'details' | 'script' | 'stats' | 'settings'

export default function VideoDetail() {
  const { video_id } = useParams<{ video_id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabType>('details')
  const [isPlaying, setIsPlaying] = useState(false)

  // Find video by video_id
  const video = mockVideos.find(v => v.video_id === video_id)

  if (!video) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <h2 className="text-2xl font-bold text-dark-text-primary mb-4">Video Not Found</h2>
        <p className="text-dark-text-secondary mb-6">The requested video could not be found.</p>
        <button onClick={() => navigate('/videos')} className="btn-primary">
          Back to Videos
        </button>
      </div>
    )
  }

  const handleDownload = () => {
    if (!video.final_video_url) {
      toast.error('Video URL not available')
      return
    }
    toast.success('Downloading video...')
    window.open(video.final_video_url, '_blank')
  }

  const handleShare = () => {
    const url = video.final_video_url || video.demo_url
    navigator.clipboard.writeText(url)
    toast.success('Video URL copied to clipboard!')
  }

  const handleDelete = () => {
    if (confirm(`Delete video for "${video.lead_title}"? This cannot be undone.`)) {
      toast.success('Video deleted (mock)')
      navigate('/videos')
    }
  }

  const handleRegenerate = () => {
    if (confirm('Regenerate this video with the same settings?')) {
      toast.success('Video regeneration started (mock)')
    }
  }

  const tabs: { id: TabType; label: string; icon: any }[] = [
    { id: 'details', label: 'Details', icon: DocumentTextIcon },
    { id: 'script', label: 'Script', icon: DocumentTextIcon },
    { id: 'stats', label: 'Stats', icon: ChartBarIcon },
    { id: 'settings', label: 'Settings', icon: Cog6ToothIcon }
  ]

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/videos')}
            className="p-2 text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border rounded-lg transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary">{video.lead_title}</h1>
            <p className="text-sm text-dark-text-secondary mt-1">{video.demo_url}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleShare}
            className="btn-secondary flex items-center gap-2"
            title="Share"
          >
            <ShareIcon className="w-5 h-5" />
            Share
          </button>
          <button
            onClick={handleDownload}
            className="btn-secondary flex items-center gap-2"
            title="Download"
          >
            <ArrowDownTrayIcon className="w-5 h-5" />
            Download
          </button>
          <button
            onClick={handleRegenerate}
            className="btn-secondary flex items-center gap-2"
            title="Regenerate"
          >
            <ArrowPathIcon className="w-5 h-5" />
            Regenerate
          </button>
          <button
            onClick={handleDelete}
            className="btn-secondary flex items-center gap-2 text-red-400 hover:bg-red-500/10"
            title="Delete"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Video Player */}
      <div className="card overflow-hidden">
        <div className="relative w-full bg-dark-bg aspect-video">
          {video.thumbnail_url ? (
            <div className="relative w-full h-full">
              <img
                src={video.thumbnail_url}
                alt={video.lead_title}
                className="w-full h-full object-cover"
              />
              {!isPlaying && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <button
                    onClick={() => setIsPlaying(true)}
                    className="w-20 h-20 rounded-full bg-terminal-500 hover:bg-terminal-600 flex items-center justify-center transition-colors"
                  >
                    <PlayIcon className="w-10 h-10 text-white ml-2" />
                  </button>
                </div>
              )}
              {isPlaying && (
                <div className="absolute inset-0 flex items-center justify-center bg-black">
                  <p className="text-white">Video player (mock)</p>
                </div>
              )}
            </div>
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center">
                <PlayIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
                <p className="text-dark-text-secondary">No video preview available</p>
              </div>
            </div>
          )}
        </div>

        {/* Player controls */}
        <div className="p-4 border-t border-dark-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 text-dark-text-secondary hover:text-terminal-400 hover:bg-terminal-500/10 rounded transition-colors"
              >
                <PlayIcon className="w-5 h-5" />
              </button>
              <span className="text-sm text-dark-text-muted font-mono">
                0:00 / {formatDuration(video.duration_seconds)}
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-dark-text-muted">
              <span>{video.resolution}</span>
              <span>•</span>
              <span>{video.file_size_mb.toFixed(1)} MB</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-border">
        <nav className="flex gap-1" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 font-medium text-sm transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'border-terminal-500 text-terminal-400'
                    : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
                }`}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'details' && (
          <div className="space-y-6">
            {/* Video Info */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                Video Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Demo Site</p>
                  <p className="text-base font-semibold text-dark-text-primary">
                    {video.lead_title}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">URL</p>
                  <a
                    href={video.demo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-base font-semibold text-terminal-400 hover:underline"
                  >
                    {video.demo_url}
                  </a>
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Status</p>
                  <p className="text-base font-semibold text-green-400 capitalize">
                    {video.status}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Created</p>
                  <p className="text-base font-semibold text-dark-text-primary">
                    {new Date(video.created_at).toLocaleString()}
                  </p>
                </div>
                {video.completed_at && (
                  <div>
                    <p className="text-sm text-dark-text-muted mb-1">Completed</p>
                    <p className="text-base font-semibold text-dark-text-primary">
                      {new Date(video.completed_at).toLocaleString()}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Video ID</p>
                  <p className="text-base font-mono text-dark-text-primary">
                    {video.video_id}
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card p-6">
                <p className="text-sm text-dark-text-muted mb-2">Views</p>
                <p className="text-3xl font-bold text-dark-text-primary">{video.view_count}</p>
              </div>
              <div className="card p-6">
                <p className="text-sm text-dark-text-muted mb-2">Avg Watch %</p>
                <p className="text-3xl font-bold text-terminal-400">
                  {video.average_watch_percentage}%
                </p>
              </div>
              <div className="card p-6">
                <p className="text-sm text-dark-text-muted mb-2">Shares</p>
                <p className="text-3xl font-bold text-dark-text-primary">{video.share_count}</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'script' && video.script && (
          <ScriptViewer script={video.script} />
        )}

        {activeTab === 'stats' && (
          <VideoStatsPanel video={video} />
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                Video Settings
              </h3>
              <div className="space-y-4">
                {video.voiceover && (
                  <div>
                    <p className="text-sm text-dark-text-muted mb-1">Voice Provider</p>
                    <p className="text-base font-semibold text-dark-text-primary capitalize">
                      {video.voiceover.provider} - {video.voiceover.voice_name}
                    </p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Resolution</p>
                  <p className="text-base font-semibold text-dark-text-primary">
                    {video.resolution}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Duration</p>
                  <p className="text-base font-semibold text-dark-text-primary">
                    {formatDuration(video.duration_seconds)}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                Generation Details
              </h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Generation Time</p>
                  <p className="text-base font-semibold text-dark-text-primary">
                    {Math.floor(video.generation_time_seconds / 60)}m {video.generation_time_seconds % 60}s
                  </p>
                </div>
                <div>
                  <p className="text-sm text-dark-text-muted mb-1">Total Cost</p>
                  <p className="text-base font-semibold text-terminal-400 font-mono">
                    ${video.total_cost.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-6 bg-red-500/5 border border-red-500/20">
              <h3 className="text-lg font-semibold text-red-400 mb-2">
                Danger Zone
              </h3>
              <p className="text-sm text-dark-text-secondary mb-4">
                Irreversible actions for this video.
              </p>
              <button
                onClick={handleDelete}
                className="btn-secondary text-red-400 hover:bg-red-500/10 border-red-500/30"
              >
                Delete Video
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
