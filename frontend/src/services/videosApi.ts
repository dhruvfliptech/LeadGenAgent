// API client for Phase 4 Video Management

import { api } from './api'
import {
  HostedVideo,
  VideoFilters,
  VideoStats,
  VideoAnalytics,
  VideoView,
  CreateVideoRequest,
  VideoGenerationProgress
} from '@/types/video'

export const videosApi = {
  // Get all videos with optional filters
  getVideos: (filters?: VideoFilters) =>
    api.get<HostedVideo[]>('/hosted-videos', { params: filters }),

  // Get a single video by ID
  getVideo: (id: number) =>
    api.get<HostedVideo>(`/hosted-videos/${id}`),

  // Create/upload a new video
  createVideo: (data: CreateVideoRequest) =>
    api.post<HostedVideo>('/hosted-videos/upload', data),

  // Update video metadata
  updateVideo: (id: number, updates: Partial<HostedVideo>) =>
    api.put<HostedVideo>(`/hosted-videos/${id}`, updates),

  // Delete a video
  deleteVideo: (id: number) =>
    api.delete(`/hosted-videos/${id}`),

  // Get shareable link
  getShareLink: (id: number) =>
    api.get<{ share_url: string }>(`/hosted-videos/${id}/share`),

  // Get embed code
  getEmbedCode: (id: number) =>
    api.get<{ embed_code: string }>(`/hosted-videos/${id}/embed`),

  // Get video analytics
  getAnalytics: (id: number) =>
    api.get<VideoAnalytics>(`/hosted-videos/${id}/analytics`),

  // Track a video view
  trackView: (id: number, data: Partial<VideoView>) =>
    api.post<VideoView>(`/hosted-videos/${id}/track-view`, data),

  // Get overall video statistics
  getStats: () =>
    api.get<VideoStats>('/hosted-videos/stats/overview'),

  // Get video generation progress
  getGenerationProgress: (id: number) =>
    api.get<VideoGenerationProgress>(`/hosted-videos/${id}/progress`),

  // Download video
  downloadVideo: async (id: number, title: string) => {
    const response = await api.get(`/hosted-videos/${id}/download`, {
      responseType: 'blob'
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${title}.mp4`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    return response
  },

  // Generate QR code for sharing
  getQRCode: (id: number) =>
    api.get<{ qr_code_data_url: string }>(`/hosted-videos/${id}/qr-code`),

  // Email video to lead
  emailToLead: (id: number, data: { lead_id: number; message?: string }) =>
    api.post(`/hosted-videos/${id}/email`, data),

  // Regenerate video with new settings
  regenerateVideo: (id: number, data: CreateVideoRequest) =>
    api.post<HostedVideo>(`/hosted-videos/${id}/regenerate`, data),
}

export default videosApi
