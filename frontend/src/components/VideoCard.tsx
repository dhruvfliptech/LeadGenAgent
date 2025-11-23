// Video card component for grid and list views - Journey 3

import { useState } from 'react'
import {
  PlayIcon,
  ShareIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  EyeIcon,
  ClockIcon,
  DocumentIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { MockVideo } from '@/mocks/videos.mock'
import { formatDistanceToNow } from 'date-fns'

interface VideoCardProps {
  video: MockVideo
  onClick: () => void
  onShare: () => void
  onDownload: () => void
  onDelete: () => void
  viewMode: 'grid' | 'list'
}

export default function VideoCard({
  video,
  onClick,
  onShare,
  onDownload,
  onDelete,
  viewMode
}: VideoCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  // Format duration
  const formatDuration = (seconds: number) => {
    if (seconds === 0) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Status badge
  const getStatusBadge = () => {
    switch (video.status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
            Completed
          </span>
        )
      case 'generating_script':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse">
            Script {video.progress_percentage}%
          </span>
        )
      case 'generating_voiceover':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-500/20 text-purple-400 border border-purple-500/30 animate-pulse">
            Voiceover {video.progress_percentage}%
          </span>
        )
      case 'recording_screen':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 animate-pulse">
            Recording {video.progress_percentage}%
          </span>
        )
      case 'composing':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30 animate-pulse">
            Composing {video.progress_percentage}%
          </span>
        )
      case 'draft':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400 border border-gray-500/30">
            Draft
          </span>
        )
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/30">
            Failed
          </span>
        )
    }
  }

  if (viewMode === 'list') {
    return (
      <div
        className="card p-4 hover:shadow-lg transition-shadow cursor-pointer"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
      >
        <div className="flex items-center gap-4">
          {/* Thumbnail */}
          <div className="relative flex-shrink-0 w-32 h-20 bg-dark-border rounded overflow-hidden group">
            {video.thumbnail_url ? (
              <img
                src={video.thumbnail_url}
                alt={video.lead_title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-terminal-600 to-terminal-800">
                <DocumentIcon className="w-8 h-8 text-terminal-300" />
              </div>
            )}
            {video.status === 'completed' && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity">
                <PlayIcon className="w-8 h-8 text-white" />
              </div>
            )}
            {video.status !== 'completed' && video.status !== 'failed' && video.status !== 'draft' && (
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-dark-border">
                <div
                  className="h-full bg-terminal-500 transition-all duration-300"
                  style={{ width: `${video.progress_percentage}%` }}
                />
              </div>
            )}
          </div>

          {/* Video info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-semibold text-dark-text-primary truncate">
                  {video.lead_title}
                </h3>
                <p className="text-sm text-dark-text-secondary truncate">
                  {video.demo_url}
                </p>
              </div>
              <div>{getStatusBadge()}</div>
            </div>

            <div className="mt-2 flex items-center gap-4 text-sm text-dark-text-muted">
              <span className="flex items-center gap-1">
                <ClockIcon className="w-4 h-4" />
                {formatDuration(video.duration_seconds)}
              </span>
              {video.file_size_mb > 0 && (
                <span>{video.file_size_mb.toFixed(1)} MB</span>
              )}
              <span className="flex items-center gap-1">
                <EyeIcon className="w-4 h-4" />
                {video.view_count} views
              </span>
              {video.average_watch_percentage > 0 && (
                <span>{video.average_watch_percentage}% watch</span>
              )}
              <span className="text-xs">
                {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>

          {/* Actions */}
          {video.status === 'completed' && (
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onShare()
                }}
                className="p-2 text-dark-text-secondary hover:text-terminal-400 hover:bg-terminal-500/10 rounded transition-colors"
                title="Share"
              >
                <ShareIcon className="w-5 h-5" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDownload()
                }}
                className="p-2 text-dark-text-secondary hover:text-green-400 hover:bg-green-500/10 rounded transition-colors"
                title="Download"
              >
                <ArrowDownTrayIcon className="w-5 h-5" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete()
                }}
                className="p-2 text-dark-text-secondary hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                title="Delete"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Grid view
  return (
    <div
      className="card overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      {/* Thumbnail */}
      <div className="relative w-full h-48 bg-dark-border group">
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.lead_title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-terminal-600 to-terminal-800">
            <DocumentIcon className="w-16 h-16 text-terminal-300" />
          </div>
        )}

        {/* Play overlay */}
        {video.status === 'completed' && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="w-16 h-16 rounded-full bg-terminal-500 flex items-center justify-center">
              <PlayIcon className="w-8 h-8 text-white ml-1" />
            </div>
          </div>
        )}

        {/* Processing indicator */}
        {video.status !== 'completed' && video.status !== 'failed' && video.status !== 'draft' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terminal-500" />
            <p className="mt-3 text-sm text-terminal-400 font-medium capitalize">
              {video.status.replace(/_/g, ' ')}
            </p>
            <div className="mt-2 w-3/4 h-2 bg-dark-border rounded-full overflow-hidden">
              <div
                className="h-full bg-terminal-500 transition-all duration-300"
                style={{ width: `${video.progress_percentage}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-dark-text-muted">{video.progress_percentage}%</p>
          </div>
        )}

        {/* Failed indicator */}
        {video.status === 'failed' && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70">
            <div className="text-center">
              <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400 mb-2" />
              <p className="text-sm text-red-400 font-medium">Generation Failed</p>
            </div>
          </div>
        )}

        {/* Status badge */}
        <div className="absolute top-2 right-2">
          {getStatusBadge()}
        </div>
      </div>

      {/* Video details */}
      <div className="p-4">
        <h3 className="text-base font-semibold text-dark-text-primary truncate mb-1">
          {video.lead_title}
        </h3>

        <p className="text-sm text-dark-text-secondary truncate mb-3">
          {video.demo_url}
        </p>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-dark-text-muted mb-3">
          <span className="flex items-center gap-1">
            <ClockIcon className="w-3 h-3" />
            {formatDuration(video.duration_seconds)}
          </span>
          {video.file_size_mb > 0 && (
            <span>{video.file_size_mb.toFixed(1)} MB</span>
          )}
          <span className="flex items-center gap-1">
            <EyeIcon className="w-3 h-3" />
            {video.view_count}
          </span>
        </div>

        <div className="text-xs text-dark-text-muted mb-4">
          Created {formatDistanceToNow(new Date(video.created_at), { addSuffix: true })}
        </div>

        {/* Actions */}
        {video.status === 'completed' && (
          <div className="flex items-center gap-2 pt-3 border-t border-dark-border">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onShare()
              }}
              className="flex-1 p-2 text-dark-text-secondary hover:text-terminal-400 hover:bg-terminal-500/10 rounded transition-colors"
              title="Share"
            >
              <ShareIcon className="w-5 h-5 mx-auto" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDownload()
              }}
              className="flex-1 p-2 text-dark-text-secondary hover:text-green-400 hover:bg-green-500/10 rounded transition-colors"
              title="Download"
            >
              <ArrowDownTrayIcon className="w-5 h-5 mx-auto" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
              }}
              className="flex-1 p-2 text-dark-text-secondary hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
              title="Delete"
            >
              <TrashIcon className="w-5 h-5 mx-auto" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
