// Video analytics component showing engagement metrics

import { useQuery } from '@tanstack/react-query'
import { videosApi } from '@/services/videosApi'
import { HostedVideo, VideoAnalytics as VideoAnalyticsType } from '@/types/video'
import {
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  ShareIcon,
  ChartBarIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  DeviceTabletIcon,
  MapPinIcon
} from '@heroicons/react/24/outline'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface VideoAnalyticsProps {
  video: HostedVideo
}

export default function VideoAnalytics({ video }: VideoAnalyticsProps) {
  const { data: analytics, isLoading } = useQuery<VideoAnalyticsType>({
    queryKey: ['video-analytics', video.id],
    queryFn: () => videosApi.getAnalytics(video.id).then(res => res.data),
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="h-6 bg-dark-border rounded w-1/3 mb-4" />
            <div className="h-32 bg-dark-border rounded" />
          </div>
        ))}
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="card p-12 text-center">
        <ChartBarIcon className="w-12 h-12 mx-auto text-dark-text-muted mb-3" />
        <p className="text-dark-text-secondary">No analytics data available yet</p>
      </div>
    )
  }

  // Device icon helper
  const getDeviceIcon = (device: string) => {
    if (device.toLowerCase().includes('mobile')) return DevicePhoneMobileIcon
    if (device.toLowerCase().includes('tablet')) return DeviceTabletIcon
    return ComputerDesktopIcon
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <EyeIcon className="w-5 h-5 text-blue-400" />
            <span className="text-sm text-dark-text-secondary">Total Views</span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary">
            {analytics.total_views}
          </div>
          <div className="text-xs text-dark-text-muted mt-1">
            {analytics.unique_viewers} unique viewers
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <ClockIcon className="w-5 h-5 text-terminal-400" />
            <span className="text-sm text-dark-text-secondary">Avg Watch</span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary">
            {analytics.avg_watch_percentage.toFixed(0)}%
          </div>
          <div className="text-xs text-dark-text-muted mt-1">
            {Math.floor((analytics.avg_watch_percentage / 100) * video.duration_seconds)}s watched
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircleIcon className="w-5 h-5 text-green-400" />
            <span className="text-sm text-dark-text-secondary">Completion</span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary">
            {analytics.completion_rate.toFixed(0)}%
          </div>
          <div className="text-xs text-dark-text-muted mt-1">
            {Math.floor(analytics.total_views * (analytics.completion_rate / 100))} completed
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center gap-3 mb-2">
            <ShareIcon className="w-5 h-5 text-purple-400" />
            <span className="text-sm text-dark-text-secondary">Shares</span>
          </div>
          <div className="text-3xl font-bold text-dark-text-primary">
            {analytics.shares}
          </div>
          <div className="text-xs text-dark-text-muted mt-1">
            {analytics.total_views > 0 ? ((analytics.shares / analytics.total_views) * 100).toFixed(1) : 0}% share rate
          </div>
        </div>
      </div>

      {/* Views Over Time */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Views Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={analytics.views_over_time}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
            <XAxis
              dataKey="date"
              stroke="#718096"
              tick={{ fill: '#A0AEC0' }}
              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis stroke="#718096" tick={{ fill: '#A0AEC0' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1A202C',
                border: '1px solid #2D3748',
                borderRadius: '8px'
              }}
              labelStyle={{ color: '#E2E8F0' }}
            />
            <Line
              type="monotone"
              dataKey="views"
              stroke="#48BB78"
              strokeWidth={2}
              dot={{ fill: '#48BB78', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Watch Completion Distribution */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Watch Completion Rate
        </h3>
        <div className="mb-6">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-dark-text-secondary">Overall Completion</span>
            <span className="text-dark-text-primary font-semibold">
              {analytics.completion_rate.toFixed(0)}%
            </span>
          </div>
          <div className="w-full h-3 bg-dark-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-terminal-600 to-terminal-400 transition-all duration-500"
              style={{ width: `${analytics.completion_rate}%` }}
            />
          </div>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={analytics.watch_completion_distribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
            <XAxis dataKey="range" stroke="#718096" tick={{ fill: '#A0AEC0' }} />
            <YAxis stroke="#718096" tick={{ fill: '#A0AEC0' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1A202C',
                border: '1px solid #2D3748',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey="count" fill="#48BB78" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Geographic and Device Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Locations */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
            <MapPinIcon className="w-5 h-5" />
            Top Locations
          </h3>
          {analytics.top_locations.length > 0 ? (
            <div className="space-y-4">
              {analytics.top_locations.map((location, index) => (
                <div key={index}>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-dark-text-primary font-medium">
                      {index + 1}. {location.location || 'Unknown'}
                    </span>
                    <span className="text-dark-text-secondary">
                      {location.views} views ({location.percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-dark-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${location.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-dark-text-secondary">
              No location data available
            </div>
          )}
        </div>

        {/* Device Breakdown */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
            <ComputerDesktopIcon className="w-5 h-5" />
            Device Breakdown
          </h3>
          {analytics.device_breakdown.length > 0 ? (
            <div className="space-y-4">
              {analytics.device_breakdown.map((device, index) => {
                const Icon = getDeviceIcon(device.device)
                return (
                  <div key={index}>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-dark-text-primary font-medium flex items-center gap-2">
                        <Icon className="w-4 h-4" />
                        {device.device}
                      </span>
                      <span className="text-dark-text-secondary">
                        {device.views} views ({device.percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full h-2 bg-dark-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-purple-500 transition-all"
                        style={{ width: `${device.percentage}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-dark-text-secondary">
              No device data available
            </div>
          )}
        </div>
      </div>

      {/* Total Watch Time */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-2">
          Total Watch Time
        </h3>
        <p className="text-3xl font-bold text-terminal-400">
          {Math.floor(analytics.total_watch_time_seconds / 3600)}h{' '}
          {Math.floor((analytics.total_watch_time_seconds % 3600) / 60)}m
        </p>
        <p className="text-sm text-dark-text-secondary mt-2">
          Across {analytics.total_views} views
        </p>
      </div>
    </div>
  )
}
