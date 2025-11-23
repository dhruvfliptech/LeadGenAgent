// Video statistics and engagement metrics panel - Journey 3

import {
  EyeIcon,
  ClockIcon,
  ShareIcon,
  ChartBarIcon,
  PlayIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline'
import { MockVideo } from '@/mocks/videos.mock'
import { formatDistanceToNow } from 'date-fns'

interface VideoStatsPanelProps {
  video: MockVideo
}

export default function VideoStatsPanel({ video }: VideoStatsPanelProps) {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(2)}`
  }

  const formatBytes = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  // Calculate engagement metrics
  const avgWatchTime = (video.duration_seconds * video.average_watch_percentage) / 100
  const completionRate = video.view_count > 0
    ? ((video.view_count * video.average_watch_percentage) / 100).toFixed(1)
    : '0'

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <EyeIcon className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-text-primary">{video.view_count}</p>
              <p className="text-sm text-dark-text-secondary">Total Views</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
              <ChartBarIcon className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-text-primary">
                {video.average_watch_percentage}%
              </p>
              <p className="text-sm text-dark-text-secondary">Avg Watch %</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <ShareIcon className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-text-primary">{video.share_count}</p>
              <p className="text-sm text-dark-text-secondary">Shares</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-terminal-500/20 flex items-center justify-center">
              <ArrowTrendingUpIcon className="w-6 h-6 text-terminal-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-dark-text-primary">
                {completionRate}
              </p>
              <p className="text-sm text-dark-text-secondary">Completions</p>
            </div>
          </div>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Engagement Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Watch Time */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-dark-text-secondary">Average Watch Time</span>
              <span className="text-sm font-semibold text-terminal-400">
                {formatDuration(Math.floor(avgWatchTime))}
              </span>
            </div>
            <div className="w-full h-2 bg-dark-border rounded-full overflow-hidden">
              <div
                className="h-full bg-terminal-500 transition-all"
                style={{ width: `${video.average_watch_percentage}%` }}
              />
            </div>
            <p className="text-xs text-dark-text-muted mt-1">
              out of {formatDuration(video.duration_seconds)}
            </p>
          </div>

          {/* Share Rate */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-dark-text-secondary">Share Rate</span>
              <span className="text-sm font-semibold text-purple-400">
                {video.view_count > 0 ? ((video.share_count / video.view_count) * 100).toFixed(1) : '0'}%
              </span>
            </div>
            <div className="w-full h-2 bg-dark-border rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all"
                style={{
                  width: `${video.view_count > 0 ? Math.min((video.share_count / video.view_count) * 100, 100) : 0}%`
                }}
              />
            </div>
            <p className="text-xs text-dark-text-muted mt-1">
              {video.share_count} of {video.view_count} viewers
            </p>
          </div>

          {/* Engagement Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-dark-text-secondary">Engagement Score</span>
              <span className="text-sm font-semibold text-green-400">
                {((video.average_watch_percentage + (video.share_count > 0 ? 20 : 0)) / 1.2).toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-2 bg-dark-border rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{
                  width: `${Math.min(((video.average_watch_percentage + (video.share_count > 0 ? 20 : 0)) / 1.2), 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-dark-text-muted mt-1">
              Combined metric
            </p>
          </div>
        </div>
      </div>

      {/* Video Details */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Video Details
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div>
            <p className="text-xs text-dark-text-muted mb-1">Duration</p>
            <p className="text-base font-semibold text-dark-text-primary flex items-center gap-2">
              <ClockIcon className="w-4 h-4" />
              {formatDuration(video.duration_seconds)}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-1">Resolution</p>
            <p className="text-base font-semibold text-dark-text-primary">
              {video.resolution}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-1">File Size</p>
            <p className="text-base font-semibold text-dark-text-primary">
              {video.file_size_mb > 0 ? `${video.file_size_mb.toFixed(1)} MB` : '--'}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-1">Generation Time</p>
            <p className="text-base font-semibold text-dark-text-primary">
              {video.generation_time_seconds > 0
                ? `${Math.floor(video.generation_time_seconds / 60)}m ${video.generation_time_seconds % 60}s`
                : '--'}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-1">Generation Cost</p>
            <p className="text-base font-semibold text-terminal-400 font-mono">
              {formatCost(video.total_cost)}
            </p>
          </div>
          <div>
            <p className="text-xs text-dark-text-muted mb-1">Created</p>
            <p className="text-base font-semibold text-dark-text-primary">
              {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
            </p>
          </div>
        </div>
      </div>

      {/* Components Breakdown */}
      {video.script && video.voiceover && video.screen_recording && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Components
          </h3>
          <div className="space-y-4">
            {/* Script */}
            <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-dark-text-primary mb-1">
                    Script
                  </h4>
                  <p className="text-xs text-dark-text-muted">
                    {video.script.word_count} words • {video.script.scenes.length} scenes
                  </p>
                </div>
                <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">
                  Generated
                </span>
              </div>
            </div>

            {/* Voiceover */}
            <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-dark-text-primary mb-1">
                    Voiceover
                  </h4>
                  <p className="text-xs text-dark-text-muted">
                    {video.voiceover.voice_name} • {video.voiceover.provider} • {formatBytes(video.voiceover.file_size_bytes)}
                  </p>
                </div>
                <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">
                  {video.voiceover.status}
                </span>
              </div>
            </div>

            {/* Screen Recording */}
            <div className="p-4 bg-dark-surface rounded-lg border border-dark-border">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-dark-text-primary mb-1">
                    Screen Recording
                  </h4>
                  <p className="text-xs text-dark-text-muted">
                    {video.screen_recording.resolution} • {video.screen_recording.fps} fps • {formatBytes(video.screen_recording.file_size_bytes)}
                  </p>
                </div>
                <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full">
                  {video.screen_recording.status}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Insights */}
      <div className="card p-6 bg-gradient-to-r from-terminal-500/10 to-blue-500/10 border border-terminal-500/30">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Performance Insights
        </h3>
        <div className="space-y-3">
          {video.average_watch_percentage >= 80 && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-dark-text-primary">High Retention</p>
                <p className="text-xs text-dark-text-secondary">
                  Viewers are watching {video.average_watch_percentage}% of your video on average
                </p>
              </div>
            </div>
          )}
          {video.share_count > 5 && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                <ShareIcon className="w-4 h-4 text-purple-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-dark-text-primary">Great Shareability</p>
                <p className="text-xs text-dark-text-secondary">
                  This video has been shared {video.share_count} times
                </p>
              </div>
            </div>
          )}
          {video.view_count > 50 && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                <EyeIcon className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-dark-text-primary">Popular Video</p>
                <p className="text-xs text-dark-text-secondary">
                  Reached {video.view_count} views
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
