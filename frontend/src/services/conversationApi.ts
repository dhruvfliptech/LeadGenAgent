import { api } from './api'
import {
  Conversation,
  ConversationMessage,
  ConversationStats,
  SendReplyRequest,
  ApproveReplyRequest,
  RegenerateReplyRequest,
  AISuggestion
} from '@/types/conversation'

// Get all conversations with optional filters
export const getConversations = async (params?: {
  status?: string
  search?: string
  limit?: number
  offset?: number
}): Promise<Conversation[]> => {
  const response = await api.get('/conversations', { params })
  return response.data
}

// Get a specific conversation with full thread
export const getConversationThread = async (id: number): Promise<Conversation> => {
  const response = await api.get(`/conversations/${id}`)
  return response.data
}

// Get conversation statistics
export const getConversationStats = async (): Promise<ConversationStats> => {
  const response = await api.get('/conversations/stats')
  return response.data
}

// Send a custom reply
export const sendReply = async (data: SendReplyRequest): Promise<ConversationMessage> => {
  const response = await api.post(`/conversations/${data.conversation_id}/reply`, {
    content: data.content,
    html_content: data.html_content
  })
  return response.data
}

// Approve AI suggestion
export const approveReply = async (data: ApproveReplyRequest): Promise<ConversationMessage> => {
  const response = await api.post(`/conversations/suggestions/${data.suggestion_id}/approve`, {
    edited_content: data.edited_content
  })
  return response.data
}

// Reject AI suggestion
export const rejectReply = async (suggestionId: number): Promise<void> => {
  await api.post(`/conversations/suggestions/${suggestionId}/reject`)
}

// Regenerate AI reply with different tone
export const regenerateReply = async (data: RegenerateReplyRequest): Promise<AISuggestion> => {
  const response = await api.post(`/conversations/suggestions/regenerate`, data)
  return response.data
}

// Archive conversation
export const archiveConversation = async (id: number): Promise<void> => {
  await api.patch(`/conversations/${id}/archive`)
}

// Mark conversation as read
export const markAsRead = async (id: number): Promise<void> => {
  await api.patch(`/conversations/${id}/read`)
}

export default {
  getConversations,
  getConversationThread,
  getConversationStats,
  sendReply,
  approveReply,
  rejectReply,
  regenerateReply,
  archiveConversation,
  markAsRead
}
