export type MessageDirection = 'inbound' | 'outbound'
export type SentimentType = 'positive' | 'neutral' | 'negative' | 'urgent'
export type ConversationStatus =
  | 'active'
  | 'replied'
  | 'closed'
  | 'snoozed'
  | 'needs_reply'
  | 'waiting'
  | 'archived'
export type ConversationPriority = 'low' | 'medium' | 'high' | 'urgent'
export type SuggestionType = 'reply' | 'follow_up' | 'meeting' | 'demo' | 'pricing'

export interface Conversation {
  id: number
  conversation_id: string
  lead_id: number
  lead_name: string
  lead_email: string
  subject: string
  status: ConversationStatus
  messages_count: number
  last_message_at: string
  last_message_direction: MessageDirection
  overall_sentiment: SentimentType
  priority: ConversationPriority
  tags: string[]
  assigned_to?: string
  needs_response: boolean
  snoozed_until?: string
  created_at: string
  updated_at: string
  messages: ConversationMessage[]
  suggestions: AISuggestion[]

  // Legacy fields for backward compatibility
  lead?: {
    id: number
    title: string
    email: string
    reply_email?: string
    contact_name?: string
  }
  unread_count?: number
  ai_suggestion?: AISuggestion
}

export interface ConversationMessage {
  id: number
  message_id: string
  conversation_id: string | number
  direction: MessageDirection
  from_email: string
  to_email: string
  subject: string
  body_text: string
  body_html?: string
  sentiment: SentimentType
  sentiment_score: number
  key_points: string[]
  questions_asked: string[]
  received_at: string
  created_at: string

  // Legacy fields for backward compatibility
  content?: string
  html_content?: string
  sent_at?: string
  sender_email?: string
  recipient_email?: string
  postmark_message_id?: string
  is_read?: boolean
}

export interface AISuggestion {
  id: number
  suggestion_id: string
  message_id: number
  type: SuggestionType
  title: string
  content: string
  rationale: string
  confidence_score: number
  model_used: string
  was_used: boolean
  created_at: string

  // Legacy fields for backward compatibility
  conversation_id?: number
  suggested_content?: string
  html_content?: string
  sentiment_analysis?: {
    sentiment: 'positive' | 'neutral' | 'negative'
    intent: string
    detected_questions: string[]
    suggested_tone: string
  }
  context_used?: {
    previous_emails: number
    lead_data: boolean
    similar_conversations: number
  }
  status?: 'pending' | 'approved' | 'rejected' | 'edited'
  updated_at?: string
}

export interface ConversationFilters {
  search?: string
  status?: 'needs_reply' | 'active' | 'waiting' | 'archived' | ''
  needs_reply?: boolean
  active?: boolean
  archived?: boolean
}

export interface ConversationStats {
  total: number
  needs_reply: number
  active: number
  waiting: number
  archived: number
}

export interface SendReplyRequest {
  conversation_id: number
  content: string
  html_content?: string
}

export interface ApproveReplyRequest {
  suggestion_id: number
  edited_content?: string
}

export interface RegenerateReplyRequest {
  message_id: number
  tone?: 'formal' | 'casual' | 'shorter' | 'humor'
}
