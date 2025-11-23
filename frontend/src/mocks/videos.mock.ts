/**
 * Mock video data for demo site videos
 */

export type VideoStatus = 'draft' | 'generating_script' | 'generating_voiceover' | 'recording_screen' | 'composing' | 'completed' | 'failed'
export type VoiceProvider = 'elevenlabs' | 'openai' | 'google'
export type VoiceGender = 'male' | 'female' | 'neutral'

export interface VideoScript {
  id: number
  script_id: string
  demo_site_id: number
  content: string
  scenes: {
    id: string
    timestamp: number
    duration: number
    narration: string
    action: string
    screen_section?: string
  }[]
  total_duration: number
  word_count: number
  generated_by: string
  created_at: string
}

export interface Voiceover {
  id: number
  voiceover_id: string
  script_id: number
  provider: VoiceProvider
  voice_name: string
  voice_gender: VoiceGender
  audio_url?: string
  duration_seconds: number
  file_size_bytes: number
  cost: number
  status: 'pending' | 'generating' | 'completed' | 'failed'
  error_message?: string
  created_at: string
}

export interface ScreenRecording {
  id: number
  recording_id: string
  demo_site_id: number
  video_url?: string
  duration_seconds: number
  resolution: string
  file_size_bytes: number
  fps: number
  actions_recorded: string[]
  status: 'recording' | 'processing' | 'completed' | 'failed'
  error_message?: string
  created_at: string
}

export interface MockVideo {
  id: number
  video_id: string
  demo_site_id: number
  lead_id: number
  lead_title: string
  demo_url: string

  // Status and progress
  status: VideoStatus
  progress_percentage: number

  // Components
  script?: VideoScript
  voiceover?: Voiceover
  screen_recording?: ScreenRecording

  // Final video
  final_video_url?: string
  thumbnail_url?: string
  duration_seconds: number
  file_size_mb: number
  resolution: string

  // Metrics
  generation_time_seconds: number
  total_cost: number

  // Analytics
  view_count: number
  average_watch_percentage: number
  share_count: number

  // Timestamps
  created_at: string
  completed_at?: string
  updated_at: string
}

export const mockVideos: MockVideo[] = [
  // Completed video
  {
    id: 1,
    video_id: 'vid_abc123',
    demo_site_id: 1,
    lead_id: 1,
    lead_title: 'Acme Design Studio',
    demo_url: 'https://acme-design-demo.vercel.app',
    status: 'completed',
    progress_percentage: 100,
    script: {
      id: 1,
      script_id: 'scr_abc123',
      demo_site_id: 1,
      content: `Welcome to Acme Design Studio's new website. Let me show you the improvements we've made.

First, you'll notice the modern, responsive hero section with a clear call-to-action. The gradient background creates an inviting atmosphere.

Scroll down to see our services section, featuring clean card layouts that work beautifully on any device.

Our portfolio showcases recent projects with smooth hover effects and optimized images for fast loading.

Finally, the contact form is now mobile-friendly with proper validation and accessibility features.

These improvements result in a 60% faster load time and significantly better user experience. Visit acmedesign.com to transform your business today.`,
      scenes: [
        {
          id: 'scene_1',
          timestamp: 0,
          duration: 5,
          narration: "Welcome to Acme Design Studio's new website. Let me show you the improvements we've made.",
          action: 'Show homepage hero section',
          screen_section: 'hero',
        },
        {
          id: 'scene_2',
          timestamp: 5,
          duration: 4,
          narration: "First, you'll notice the modern, responsive hero section with a clear call-to-action.",
          action: 'Highlight CTA button',
          screen_section: 'hero',
        },
        {
          id: 'scene_3',
          timestamp: 9,
          duration: 5,
          narration: 'Scroll down to see our services section, featuring clean card layouts that work beautifully on any device.',
          action: 'Scroll to services, show cards',
          screen_section: 'services',
        },
        {
          id: 'scene_4',
          timestamp: 14,
          duration: 5,
          narration: 'Our portfolio showcases recent projects with smooth hover effects and optimized images for fast loading.',
          action: 'Scroll to portfolio, hover over items',
          screen_section: 'portfolio',
        },
        {
          id: 'scene_5',
          timestamp: 19,
          duration: 5,
          narration: 'Finally, the contact form is now mobile-friendly with proper validation and accessibility features.',
          action: 'Scroll to contact form, show form fields',
          screen_section: 'contact',
        },
        {
          id: 'scene_6',
          timestamp: 24,
          duration: 6,
          narration: "These improvements result in a 60% faster load time and significantly better user experience. Visit acmedesign.com to transform your business today.",
          action: 'Scroll back to top, fade out',
          screen_section: 'hero',
        },
      ],
      total_duration: 30,
      word_count: 142,
      generated_by: 'claude-sonnet-4.5',
      created_at: '2025-01-05T11:20:00Z',
    },
    voiceover: {
      id: 1,
      voiceover_id: 'vo_abc123',
      script_id: 1,
      provider: 'elevenlabs',
      voice_name: 'Josh - Professional Male',
      voice_gender: 'male',
      audio_url: 'https://cdn.example.com/voiceovers/vo_abc123.mp3',
      duration_seconds: 30,
      file_size_bytes: 480000,
      cost: 0.15,
      status: 'completed',
      created_at: '2025-01-05T11:25:00Z',
    },
    screen_recording: {
      id: 1,
      recording_id: 'rec_abc123',
      demo_site_id: 1,
      video_url: 'https://cdn.example.com/recordings/rec_abc123.mp4',
      duration_seconds: 30,
      resolution: '1920x1080',
      file_size_bytes: 8500000,
      fps: 30,
      actions_recorded: [
        'Load homepage',
        'Highlight hero CTA',
        'Scroll to services',
        'Show service cards',
        'Scroll to portfolio',
        'Hover portfolio items',
        'Scroll to contact',
        'Show contact form',
        'Scroll to top',
      ],
      status: 'completed',
      created_at: '2025-01-05T11:30:00Z',
    },
    final_video_url: 'https://cdn.example.com/videos/vid_abc123.mp4',
    thumbnail_url: 'https://cdn.example.com/thumbnails/vid_abc123.jpg',
    duration_seconds: 30,
    file_size_mb: 12.4,
    resolution: '1920x1080',
    generation_time_seconds: 420,
    total_cost: 0.42,
    view_count: 87,
    average_watch_percentage: 78,
    share_count: 5,
    created_at: '2025-01-05T11:20:00Z',
    completed_at: '2025-01-05T11:40:00Z',
    updated_at: '2025-01-05T11:40:00Z',
  },

  // Video in progress - generating voiceover
  {
    id: 2,
    video_id: 'vid_def456',
    demo_site_id: 3,
    lead_id: 5,
    lead_title: 'Modern Web Solutions',
    demo_url: 'https://modern-web-demo.vercel.app',
    status: 'generating_voiceover',
    progress_percentage: 45,
    script: {
      id: 2,
      script_id: 'scr_def456',
      demo_site_id: 3,
      content: `Discover Modern Web Solutions' redesigned website, built with Next.js for blazing-fast performance.

The server-side rendering ensures your content loads instantly, while the modern design captures attention immediately.

Browse through our responsive portfolio that adapts perfectly to any screen size.

Contact us through our streamlined form, and let's build something amazing together.`,
      scenes: [
        {
          id: 'scene_1',
          timestamp: 0,
          duration: 5,
          narration: "Discover Modern Web Solutions' redesigned website, built with Next.js for blazing-fast performance.",
          action: 'Show homepage',
        },
        {
          id: 'scene_2',
          timestamp: 5,
          duration: 4,
          narration: 'The server-side rendering ensures your content loads instantly, while the modern design captures attention immediately.',
          action: 'Show performance metrics',
        },
        {
          id: 'scene_3',
          timestamp: 9,
          duration: 4,
          narration: 'Browse through our responsive portfolio that adapts perfectly to any screen size.',
          action: 'Show portfolio on mobile view',
        },
        {
          id: 'scene_4',
          timestamp: 13,
          duration: 3,
          narration: "Contact us through our streamlined form, and let's build something amazing together.",
          action: 'Show contact form',
        },
      ],
      total_duration: 16,
      word_count: 68,
      generated_by: 'claude-sonnet-4.5',
      created_at: '2025-01-05T14:30:00Z',
    },
    voiceover: {
      id: 2,
      voiceover_id: 'vo_def456',
      script_id: 2,
      provider: 'elevenlabs',
      voice_name: 'Rachel - Professional Female',
      voice_gender: 'female',
      duration_seconds: 16,
      file_size_bytes: 0,
      cost: 0.08,
      status: 'generating',
      created_at: '2025-01-05T14:35:00Z',
    },
    duration_seconds: 16,
    file_size_mb: 0,
    resolution: '1920x1080',
    generation_time_seconds: 0,
    total_cost: 0.08,
    view_count: 0,
    average_watch_percentage: 0,
    share_count: 0,
    created_at: '2025-01-05T14:30:00Z',
    updated_at: '2025-01-05T14:35:00Z',
  },

  // Video in draft stage
  {
    id: 3,
    video_id: 'vid_ghi789',
    demo_site_id: 5,
    lead_id: 12,
    lead_title: 'Social Boost',
    demo_url: 'https://social-boost-demo.netlify.app',
    status: 'draft',
    progress_percentage: 0,
    duration_seconds: 0,
    file_size_mb: 0,
    resolution: '1920x1080',
    generation_time_seconds: 0,
    total_cost: 0,
    view_count: 0,
    average_watch_percentage: 0,
    share_count: 0,
    created_at: '2025-01-05T15:00:00Z',
    updated_at: '2025-01-05T15:00:00Z',
  },

  // Completed video with high engagement
  {
    id: 4,
    video_id: 'vid_jkl012',
    demo_site_id: 1,
    lead_id: 1,
    lead_title: 'Acme Design Studio - Version 2',
    demo_url: 'https://acme-design-demo-v2.vercel.app',
    status: 'completed',
    progress_percentage: 100,
    script: {
      id: 4,
      script_id: 'scr_jkl012',
      demo_site_id: 1,
      content: 'See how Acme Design Studio can transform your online presence with cutting-edge web design.',
      scenes: [
        {
          id: 'scene_1',
          timestamp: 0,
          duration: 10,
          narration: 'See how Acme Design Studio can transform your online presence with cutting-edge web design.',
          action: 'Full site tour',
        },
      ],
      total_duration: 10,
      word_count: 16,
      generated_by: 'gpt-4-turbo',
      created_at: '2025-01-04T10:00:00Z',
    },
    voiceover: {
      id: 4,
      voiceover_id: 'vo_jkl012',
      script_id: 4,
      provider: 'openai',
      voice_name: 'Alloy',
      voice_gender: 'neutral',
      audio_url: 'https://cdn.example.com/voiceovers/vo_jkl012.mp3',
      duration_seconds: 10,
      file_size_bytes: 160000,
      cost: 0.05,
      status: 'completed',
      created_at: '2025-01-04T10:05:00Z',
    },
    screen_recording: {
      id: 4,
      recording_id: 'rec_jkl012',
      demo_site_id: 1,
      video_url: 'https://cdn.example.com/recordings/rec_jkl012.mp4',
      duration_seconds: 10,
      resolution: '1920x1080',
      file_size_bytes: 2800000,
      fps: 30,
      actions_recorded: ['Full site scroll'],
      status: 'completed',
      created_at: '2025-01-04T10:10:00Z',
    },
    final_video_url: 'https://cdn.example.com/videos/vid_jkl012.mp4',
    thumbnail_url: 'https://cdn.example.com/thumbnails/vid_jkl012.jpg',
    duration_seconds: 10,
    file_size_mb: 4.2,
    resolution: '1920x1080',
    generation_time_seconds: 180,
    total_cost: 0.12,
    view_count: 234,
    average_watch_percentage: 92,
    share_count: 18,
    created_at: '2025-01-04T10:00:00Z',
    completed_at: '2025-01-04T10:20:00Z',
    updated_at: '2025-01-04T10:20:00Z',
  },

  // Failed video
  {
    id: 5,
    video_id: 'vid_mno345',
    demo_site_id: 4,
    lead_id: 11,
    lead_title: 'Design Pro',
    demo_url: 'https://designpro-demo.vercel.app',
    status: 'failed',
    progress_percentage: 25,
    script: {
      id: 5,
      script_id: 'scr_mno345',
      demo_site_id: 4,
      content: 'Demo script for Design Pro website.',
      scenes: [],
      total_duration: 0,
      word_count: 6,
      generated_by: 'claude-sonnet-4.5',
      created_at: '2025-01-05T09:00:00Z',
    },
    duration_seconds: 0,
    file_size_mb: 0,
    resolution: '1920x1080',
    generation_time_seconds: 45,
    total_cost: 0.03,
    view_count: 0,
    average_watch_percentage: 0,
    share_count: 0,
    created_at: '2025-01-05T09:00:00Z',
    updated_at: '2025-01-05T09:15:00Z',
  },
]

// Helper functions
export const getVideoByDemoSiteId = (demoSiteId: number) =>
  mockVideos.find(video => video.demo_site_id === demoSiteId)

export const getVideosByStatus = (status: VideoStatus) =>
  mockVideos.filter(video => video.status === status)

export const getCompletedVideos = () =>
  mockVideos.filter(video => video.status === 'completed')

export const getHighEngagementVideos = (threshold: number = 80) =>
  mockVideos.filter(video => video.average_watch_percentage >= threshold)

export const getTotalVideoStats = () => ({
  total_videos: mockVideos.length,
  completed: mockVideos.filter(v => v.status === 'completed').length,
  in_progress: mockVideos.filter(v => !['completed', 'failed', 'draft'].includes(v.status)).length,
  failed: mockVideos.filter(v => v.status === 'failed').length,
  total_views: mockVideos.reduce((sum, v) => sum + v.view_count, 0),
  total_shares: mockVideos.reduce((sum, v) => sum + v.share_count, 0),
  avg_watch_percentage: mockVideos.filter(v => v.view_count > 0).reduce((sum, v) => sum + v.average_watch_percentage, 0) / mockVideos.filter(v => v.view_count > 0).length || 0,
  total_cost: mockVideos.reduce((sum, v) => sum + v.total_cost, 0),
  avg_generation_time: mockVideos.filter(v => v.generation_time_seconds > 0).reduce((sum, v) => sum + v.generation_time_seconds, 0) / mockVideos.filter(v => v.generation_time_seconds > 0).length || 0,
})
