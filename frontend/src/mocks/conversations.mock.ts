import type {
  Conversation,
  ConversationMessage,
  AISuggestion,
} from '@/types/conversation'

/**
 * Mock conversation and AI suggestion data
 */

export type MockConversation = Conversation

export const mockConversations: MockConversation[] = [
  // High priority conversation with multiple messages
  {
    id: 1,
    conversation_id: 'conv_abc123',
    lead_id: 1,
    lead_name: 'John Smith',
    lead_email: 'john@acmedesign.com',
    subject: 'Re: Transform Your Website with Modern Design',
    status: 'active',
    messages_count: 3,
    last_message_at: '2025-01-05T14:30:00Z',
    last_message_direction: 'inbound',
    overall_sentiment: 'positive',
    priority: 'high',
    tags: ['interested', 'budget-mentioned'],
    needs_response: true,
    unread_count: 1,
    created_at: '2025-01-05T10:00:00Z',
    updated_at: '2025-01-05T14:30:00Z',
    messages: [
      {
        id: 1,
        message_id: 'msg_001',
        conversation_id: 'conv_abc123',
        direction: 'outbound',
        from_email: 'sales@ourcompany.com',
        to_email: 'john@acmedesign.com',
        subject: 'Transform Your Website with Modern Design',
        body_text: `Hi John,

I came across your web design business and noticed your website could benefit from a modern refresh.

We specialize in creating:
- Mobile-responsive designs
- Fast-loading pages
- SEO-optimized content

I've created a free demo of what your new site could look like: https://acme-design-demo.vercel.app

Would you be interested in a quick 15-minute call to discuss?

Best regards,
Sarah`,
        sentiment: 'neutral',
        sentiment_score: 0.5,
        key_points: ['Website refresh opportunity', 'Free demo created', 'Call invitation'],
        questions_asked: ['Would you be interested in a call?'],
        received_at: '2025-01-05T10:00:00Z',
        created_at: '2025-01-05T10:00:00Z',
      },
      {
        id: 2,
        message_id: 'msg_002',
        conversation_id: 'conv_abc123',
        direction: 'inbound',
        from_email: 'john@acmedesign.com',
        to_email: 'sales@ourcompany.com',
        subject: 'Re: Transform Your Website with Modern Design',
        body_text: `Hi Sarah,

Thanks for reaching out! The demo looks impressive. We've been thinking about updating our site for a while now.

What's your typical timeline and pricing structure for a project like this?

Best,
John`,
        sentiment: 'positive',
        sentiment_score: 0.8,
        key_points: ['Interested in demo', 'Actively considering update', 'Asking about timeline and pricing'],
        questions_asked: ['What is your typical timeline?', 'What is your pricing structure?'],
        received_at: '2025-01-05T11:30:00Z',
        created_at: '2025-01-05T11:30:00Z',
      },
      {
        id: 3,
        message_id: 'msg_003',
        conversation_id: 'conv_abc123',
        direction: 'outbound',
        from_email: 'sales@ourcompany.com',
        to_email: 'john@acmedesign.com',
        subject: 'Re: Transform Your Website with Modern Design',
        body_text: `Hi John,

Great to hear you liked the demo!

For a site of your scope, we typically complete projects in 3-4 weeks. Our pricing ranges from $3,000-$5,000 depending on features and complexity.

Since you already have existing content, we could likely hit the lower end of that range.

I have availability this Thursday or Friday for a 15-minute call to discuss specifics. Which works better for you?

Best,
Sarah`,
        sentiment: 'positive',
        sentiment_score: 0.7,
        key_points: ['Timeline: 3-4 weeks', 'Pricing: $3k-$5k', 'Meeting invitation'],
        questions_asked: ['Thursday or Friday?'],
        received_at: '2025-01-05T13:00:00Z',
        created_at: '2025-01-05T13:00:00Z',
      },
      {
        id: 4,
        message_id: 'msg_004',
        conversation_id: 'conv_abc123',
        direction: 'inbound',
        from_email: 'john@acmedesign.com',
        to_email: 'sales@ourcompany.com',
        subject: 'Re: Transform Your Website with Modern Design',
        body_text: `Hi Sarah,

Friday afternoon works great for me. Let's say 2pm PST?

Also, do you offer any kind of payment plan or milestone-based billing?

Thanks,
John`,
        sentiment: 'positive',
        sentiment_score: 0.85,
        key_points: ['Agreed to Friday 2pm PST meeting', 'Interested in payment flexibility'],
        questions_asked: ['Do you offer payment plans?', 'Do you offer milestone-based billing?'],
        received_at: '2025-01-05T14:30:00Z',
        created_at: '2025-01-05T14:30:00Z',
      },
    ],
    suggestions: [
      {
        id: 1,
        suggestion_id: 'sug_001',
        message_id: 4,
        type: 'meeting',
        title: 'Confirm meeting and address payment question',
        content: `Hi John,

Perfect! I've sent you a calendar invite for Friday at 2pm PST.

Yes, we absolutely offer milestone-based billing. Typically we structure it as:
- 30% upon project kickoff
- 40% at design approval
- 30% upon launch

This helps spread out the investment and ensures you're happy at each stage.

I'll prepare some additional examples similar to your business to share on our call.

Looking forward to speaking with you!

Best,
Sarah`,
        rationale: 'Lead is highly engaged and asking about payment flexibility, which is a strong buying signal. Confirming the meeting and immediately addressing the payment question removes friction and moves the deal forward.',
        confidence_score: 0.92,
        model_used: 'claude-sonnet-4.5',
        was_used: false,
        created_at: '2025-01-05T14:31:00Z',
      },
      {
        id: 2,
        suggestion_id: 'sug_002',
        message_id: 4,
        type: 'reply',
        title: 'Confirm meeting with brief payment info',
        content: `Hi John,

Friday at 2pm PST works perfectly - calendar invite coming your way!

We do offer milestone-based payment plans. I'll prepare a detailed breakdown to walk through on our call.

See you Friday!

Sarah`,
        rationale: 'A more concise response that confirms the meeting and acknowledges the payment question without overwhelming detail. Good for keeping momentum.',
        confidence_score: 0.85,
        model_used: 'gpt-4-turbo',
        was_used: false,
        created_at: '2025-01-05T14:31:00Z',
      },
    ],
  },

  // Urgent conversation needing response
  {
    id: 2,
    conversation_id: 'conv_def456',
    lead_id: 8,
    lead_name: 'CEO Startup Inc',
    lead_email: 'ceo@startupinc.com',
    subject: 'Website Redesign - Urgent Timeline',
    status: 'active',
    messages_count: 2,
    last_message_at: '2025-01-05T14:00:00Z',
    last_message_direction: 'inbound',
    overall_sentiment: 'urgent',
    priority: 'urgent',
    tags: ['urgent', 'tight-deadline', 'high-value'],
    needs_response: true,
    unread_count: 2,
    created_at: '2025-01-05T13:00:00Z',
    updated_at: '2025-01-05T14:00:00Z',
    messages: [
      {
        id: 5,
        message_id: 'msg_005',
        conversation_id: 'conv_def456',
        direction: 'inbound',
        from_email: 'ceo@startupinc.com',
        to_email: 'sales@ourcompany.com',
        subject: 'Website Redesign - Urgent Timeline',
        body_text: `Hi,

We need a complete website redesign ASAP. We're launching a major product in 3 weeks and our current site isn't ready.

Budget isn't a concern - quality and speed are priority. Can you help?

Need response today if possible.`,
        sentiment: 'urgent',
        sentiment_score: 0.95,
        key_points: ['Urgent 3-week deadline', 'Major product launch', 'Budget flexible', 'Needs same-day response'],
        questions_asked: ['Can you help with urgent timeline?'],
        received_at: '2025-01-05T13:00:00Z',
        created_at: '2025-01-05T13:00:00Z',
      },
      {
        id: 6,
        message_id: 'msg_006',
        conversation_id: 'conv_def456',
        direction: 'inbound',
        from_email: 'ceo@startupinc.com',
        to_email: 'sales@ourcompany.com',
        subject: 'Re: Website Redesign - Urgent Timeline',
        body_text: `Following up on my earlier email. We're evaluating vendors today and need to make a decision by EOD.

Current site: startupinc.com

Can you take a look and let me know if this is feasible?`,
        sentiment: 'urgent',
        sentiment_score: 0.98,
        key_points: ['Evaluating vendors today', 'Decision by end of day', 'Provided website for review'],
        questions_asked: ['Is this feasible?'],
        received_at: '2025-01-05T14:00:00Z',
        created_at: '2025-01-05T14:00:00Z',
      },
    ],
    suggestions: [
      {
        id: 3,
        suggestion_id: 'sug_003',
        message_id: 6,
        type: 'reply',
        title: 'URGENT: Immediate response with capability',
        content: `Hi there,

Yes, we can absolutely help with your 3-week timeline. We specialize in rapid, high-quality launches for product releases.

I'm reviewing your current site now and can have a proposal ready within 2 hours.

Can we jump on a quick 20-minute call at 3pm today to discuss scope? I'll have preliminary mockups ready to share.

My direct line: (555) 123-4567

Best regards,
Sarah Chen
Senior Solutions Architect`,
        rationale: 'This is a high-value, time-sensitive opportunity. The response demonstrates urgency, capability, and professionalism. Offering a same-day call with mockups shows commitment and moves quickly toward closing.',
        confidence_score: 0.96,
        model_used: 'claude-sonnet-4.5',
        was_used: false,
        created_at: '2025-01-05T14:02:00Z',
      },
    ],
  },

  // Replied conversation (closed)
  {
    id: 3,
    conversation_id: 'conv_ghi789',
    lead_id: 2,
    lead_name: 'SEO Masters',
    lead_email: 'contact@seomasters.com',
    subject: 'Thanks but not right now',
    status: 'closed',
    messages_count: 2,
    last_message_at: '2025-01-04T16:00:00Z',
    last_message_direction: 'inbound',
    overall_sentiment: 'neutral',
    priority: 'low',
    tags: ['not-interested', 'timing'],
    needs_response: false,
    created_at: '2025-01-04T10:00:00Z',
    updated_at: '2025-01-04T16:00:00Z',
    messages: [
      {
        id: 7,
        message_id: 'msg_007',
        conversation_id: 'conv_ghi789',
        direction: 'outbound',
        from_email: 'sales@ourcompany.com',
        to_email: 'contact@seomasters.com',
        subject: 'Free Website Audit',
        body_text: 'Hi, we noticed your SEO business could benefit from a website update...',
        sentiment: 'neutral',
        sentiment_score: 0.5,
        key_points: ['Outreach email'],
        questions_asked: [],
        received_at: '2025-01-04T10:00:00Z',
        created_at: '2025-01-04T10:00:00Z',
      },
      {
        id: 8,
        message_id: 'msg_008',
        conversation_id: 'conv_ghi789',
        direction: 'inbound',
        from_email: 'contact@seomasters.com',
        to_email: 'sales@ourcompany.com',
        subject: 'Re: Free Website Audit',
        body_text: `Thanks for reaching out, but we just completed a redesign last month. We're good for now.

Maybe check back next year?`,
        sentiment: 'neutral',
        sentiment_score: 0.4,
        key_points: ['Recently completed redesign', 'Not interested now', 'Suggests future contact'],
        questions_asked: [],
        received_at: '2025-01-04T16:00:00Z',
        created_at: '2025-01-04T16:00:00Z',
      },
    ],
    suggestions: [],
  },

  // Snoozed conversation
  {
    id: 4,
    conversation_id: 'conv_jkl012',
    lead_id: 6,
    lead_name: 'Creative Studio SF',
    lead_email: 'hello@creativestudiosf.com',
    subject: 'Following up on proposal',
    status: 'snoozed',
    messages_count: 4,
    last_message_at: '2025-01-03T14:00:00Z',
    last_message_direction: 'outbound',
    overall_sentiment: 'positive',
    priority: 'medium',
    tags: ['proposal-sent', 'follow-up'],
    needs_response: false,
    snoozed_until: '2025-01-08T09:00:00Z',
    created_at: '2025-01-02T10:00:00Z',
    updated_at: '2025-01-03T14:00:00Z',
    messages: [
      {
        id: 9,
        message_id: 'msg_009',
        conversation_id: 'conv_jkl012',
        direction: 'outbound',
        from_email: 'sales@ourcompany.com',
        to_email: 'hello@creativestudiosf.com',
        subject: 'Following up on proposal',
        body_text: 'Hi, I wanted to follow up on the proposal I sent last week. Have you had a chance to review it?',
        sentiment: 'neutral',
        sentiment_score: 0.5,
        key_points: ['Follow-up on proposal'],
        questions_asked: ['Have you reviewed the proposal?'],
        received_at: '2025-01-03T14:00:00Z',
        created_at: '2025-01-03T14:00:00Z',
      },
    ],
    suggestions: [],
  },
]

// Helper functions
export const getConversationsByStatus = (status: MockConversation['status']) =>
  mockConversations.filter(conv => conv.status === status)

export const getNeedsResponse = () =>
  mockConversations.filter(conv => conv.needs_response)

export const getByPriority = (priority: MockConversation['priority']) =>
  mockConversations.filter(conv => conv.priority === priority)

export const getUrgentConversations = () =>
  mockConversations.filter(conv => conv.priority === 'urgent' || conv.overall_sentiment === 'urgent')

export const getActiveConversations = () =>
  mockConversations.filter(conv => conv.status === 'active')

export const getConversationStats = () => ({
  total: mockConversations.length,
  active: mockConversations.filter(c => c.status === 'active').length,
  needs_response: mockConversations.filter(c => c.needs_response).length,
  urgent: mockConversations.filter(c => c.priority === 'urgent').length,
  snoozed: mockConversations.filter(c => c.status === 'snoozed').length,
  closed: mockConversations.filter(c => c.status === 'closed').length,
  avg_messages: mockConversations.reduce((sum, c) => sum + c.messages_count, 0) / mockConversations.length,
  positive_sentiment: mockConversations.filter(c => c.overall_sentiment === 'positive').length,
  negative_sentiment: mockConversations.filter(c => c.overall_sentiment === 'negative').length,
})
