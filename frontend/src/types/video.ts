// Type definitions for Phase 4 Video Management

export type HostingProvider = 'loom' | 's3'
export type VideoPrivacy = 'public' | 'unlisted' | 'private'
export type VideoStatus = 'uploading' | 'processing' | 'ready' | 'failed'
export type ScriptStyle = 'professional' | 'casual' | 'technical' | 'sales'
export type VoicePreset = 'professional_male' | 'professional_female' | 'casual_male' | 'casual_female'
export type VideoQuality = 'high' | 'medium' | 'low'

export interface HostedVideo {
  id: number
  composed_video_id: number
  demo_site_id: number
  lead_id: number
  hosting_provider: HostingProvider
  provider_video_id: string
  share_url: string
  embed_url: string
  thumbnail_url?: string
  title: string
  description?: string
  privacy: VideoPrivacy
  duration_seconds: number
  file_size_bytes: number
  status: VideoStatus
  upload_started_at: string
  upload_completed_at?: string
  view_count: number
  last_viewed_at?: string
  avg_watch_percentage?: number
  created_at: string
  updated_at: string

  // Relationships
  demo_site?: {
    id: number
    lead_name: string
    demo_url: string
    framework: string
  }
  lead?: {
    id: number
    business_name: string
    email?: string
    phone?: string
  }
}

export interface VideoView {
  id: number
  hosted_video_id: number
  viewer_ip: string
  viewer_location?: string
  viewer_device?: string
  watch_duration_seconds: number
  watch_percentage: number
  completed: boolean
  viewed_at: string
}

export interface VideoFilters {
  status?: VideoStatus
  demo_site_id?: number
  lead_id?: number
  hosting_provider?: HostingProvider
  search?: string
  date_from?: string
  date_to?: string
}

export interface VideoStats {
  total_videos: number
  ready_videos: number
  processing_videos: number
  failed_videos: number
  total_views: number
  total_storage_gb: number
  avg_watch_percentage: number
  top_videos: HostedVideo[]
}

export interface VideoConfig {
  scriptStyle: ScriptStyle
  voicePreset: VoicePreset
  videoQuality: VideoQuality
  includeBranding: boolean
  includeIntro: boolean
  includeOutro: boolean
  hostingProvider: HostingProvider | 'auto'
  privacy: VideoPrivacy
}

export interface VideoAnalytics {
  video_id: number
  total_views: number
  unique_viewers: number
  avg_watch_percentage: number
  completion_rate: number
  total_watch_time_seconds: number
  shares: number

  // Time series data
  views_over_time: {
    date: string
    views: number
  }[]

  // Geographic data
  top_locations: {
    location: string
    views: number
    percentage: number
  }[]

  // Device data
  device_breakdown: {
    device: string
    views: number
    percentage: number
  }[]

  // Engagement data
  watch_completion_distribution: {
    range: string
    count: number
    percentage: number
  }[]
}

export interface CreateVideoRequest {
  demo_site_id: number
  script_style?: ScriptStyle
  voice_preset?: VoicePreset
  video_quality?: VideoQuality
  include_branding?: boolean
  include_intro?: boolean
  include_outro?: boolean
  hosting_provider?: HostingProvider
  privacy?: VideoPrivacy
  custom_script?: string
}

export interface VideoGenerationProgress {
  stage: 'script' | 'voiceover' | 'recording' | 'composing' | 'uploading' | 'complete' | 'failed'
  progress_percentage: number
  status_message: string
  estimated_time_remaining?: number
}
