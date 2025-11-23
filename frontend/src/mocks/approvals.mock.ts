/**
 * Mock approval workflow data
 */

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired'
export type ApprovalType = 'email_campaign' | 'email_response' | 'lead_action' | 'demo_site_deploy' | 'video_publish' | 'workflow_trigger'
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export interface ApprovalRule {
  id: number
  rule_id: string
  name: string
  description: string
  type: ApprovalType
  conditions: {
    field: string
    operator: 'equals' | 'contains' | 'greater_than' | 'less_than'
    value: any
  }[]
  requires_approval: boolean
  risk_level: RiskLevel
  auto_approve_after_hours?: number
  approvers: string[]
  enabled: boolean
  created_at: string
}

export interface MockApproval {
  id: number
  approval_id: string
  type: ApprovalType
  status: ApprovalStatus
  risk_level: RiskLevel

  // What needs approval
  title: string
  description: string
  context: Record<string, any>

  // Risk assessment
  risk_factors: string[]
  risk_score: number

  // Related entities
  lead_id?: number
  lead_name?: string
  campaign_id?: string
  demo_site_id?: number
  video_id?: string
  workflow_id?: string

  // Preview data
  preview_data?: {
    email_subject?: string
    email_body?: string
    recipient?: string
    action?: string
    url?: string
  }

  // Approval tracking
  requested_by: string
  requested_at: string
  assigned_to?: string
  reviewed_by?: string
  reviewed_at?: string
  expires_at?: string

  // Decision
  approved?: boolean
  rejection_reason?: string
  notes?: string

  created_at: string
  updated_at: string
}

export const mockApprovals: MockApproval[] = [
  // High risk email requiring approval
  {
    id: 1,
    approval_id: 'appr_abc123',
    type: 'email_response',
    status: 'pending',
    risk_level: 'high',
    title: 'Email response mentioning pricing and contract terms',
    description: 'AI-generated response includes specific pricing ($3k-$5k) and payment terms',
    context: {
      conversation_id: 'conv_abc123',
      lead_name: 'John Smith',
      lead_email: 'john@acmedesign.com',
    },
    risk_factors: [
      'Contains specific pricing information',
      'Mentions payment terms and milestone billing',
      'Commits to meeting time without calendar verification',
    ],
    risk_score: 75,
    lead_id: 1,
    lead_name: 'John Smith',
    preview_data: {
      email_subject: 'Re: Transform Your Website with Modern Design',
      email_body: `Hi John,

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
      recipient: 'john@acmedesign.com',
    },
    requested_by: 'AI Agent',
    requested_at: '2025-01-05T14:31:00Z',
    assigned_to: 'sarah@ourcompany.com',
    expires_at: '2025-01-05T16:31:00Z',
    created_at: '2025-01-05T14:31:00Z',
    updated_at: '2025-01-05T14:31:00Z',
  },

  // Critical urgent response
  {
    id: 2,
    approval_id: 'appr_def456',
    type: 'email_response',
    status: 'pending',
    risk_level: 'critical',
    title: 'URGENT: Response to high-value lead with tight deadline',
    description: 'CEO of startup requesting immediate response, budget flexible, 3-week timeline',
    context: {
      conversation_id: 'conv_def456',
      lead_name: 'CEO Startup Inc',
      lead_email: 'ceo@startupinc.com',
      urgency: 'Decision needed by EOD',
    },
    risk_factors: [
      'High-value opportunity ($10k+ potential)',
      'Extremely tight timeline (3 weeks)',
      'Commits to same-day proposal and mockups',
      'Provides direct phone number',
      'CEO-level contact',
    ],
    risk_score: 92,
    lead_id: 8,
    lead_name: 'CEO Startup Inc',
    preview_data: {
      email_subject: 'Re: Website Redesign - Urgent Timeline',
      email_body: `Hi there,

Yes, we can absolutely help with your 3-week timeline. We specialize in rapid, high-quality launches for product releases.

I'm reviewing your current site now and can have a proposal ready within 2 hours.

Can we jump on a quick 20-minute call at 3pm today to discuss scope? I'll have preliminary mockups ready to share.

My direct line: (555) 123-4567

Best regards,
Sarah Chen
Senior Solutions Architect`,
      recipient: 'ceo@startupinc.com',
    },
    requested_by: 'AI Agent',
    requested_at: '2025-01-05T14:02:00Z',
    assigned_to: 'sarah@ourcompany.com',
    expires_at: '2025-01-05T14:32:00Z',
    created_at: '2025-01-05T14:02:00Z',
    updated_at: '2025-01-05T14:02:00Z',
  },

  // Approved demo site deployment
  {
    id: 3,
    approval_id: 'appr_ghi789',
    type: 'demo_site_deploy',
    status: 'approved',
    risk_level: 'medium',
    title: 'Deploy demo site for Acme Design Studio',
    description: 'Generated React demo site ready for Vercel deployment',
    context: {
      framework: 'react',
      improvements_count: 3,
      validation_passed: true,
    },
    risk_factors: [
      'Public deployment will be visible to lead',
      'Uses company branding',
    ],
    risk_score: 45,
    lead_id: 1,
    lead_name: 'Acme Design Studio',
    demo_site_id: 1,
    preview_data: {
      url: 'https://acme-design-demo.vercel.app',
      action: 'Deploy to Vercel',
    },
    requested_by: 'Demo Site Generator',
    requested_at: '2025-01-05T11:10:00Z',
    assigned_to: 'sarah@ourcompany.com',
    reviewed_by: 'sarah@ourcompany.com',
    reviewed_at: '2025-01-05T11:12:00Z',
    approved: true,
    notes: 'Looks great, approved for deployment',
    created_at: '2025-01-05T11:10:00Z',
    updated_at: '2025-01-05T11:12:00Z',
  },

  // Rejected campaign
  {
    id: 4,
    approval_id: 'appr_jkl012',
    type: 'email_campaign',
    status: 'rejected',
    risk_level: 'high',
    title: 'Mass email campaign to 500+ leads',
    description: 'Cold outreach campaign targeting all web design leads',
    context: {
      recipients_count: 523,
      subject: 'Special Offer: 50% Off Website Redesign',
      has_discount: true,
    },
    risk_factors: [
      'Large recipient list (500+)',
      'Contains discount/promotional language',
      'Cold outreach with no prior contact',
      'May trigger spam filters',
    ],
    risk_score: 82,
    campaign_id: 'camp_rejected',
    preview_data: {
      email_subject: 'Special Offer: 50% Off Website Redesign',
      email_body: 'Limited time offer...',
      recipient: '523 leads',
    },
    requested_by: 'Campaign Manager',
    requested_at: '2025-01-04T10:00:00Z',
    assigned_to: 'manager@ourcompany.com',
    reviewed_by: 'manager@ourcompany.com',
    reviewed_at: '2025-01-04T10:15:00Z',
    approved: false,
    rejection_reason: 'Promotional language too aggressive, may harm sender reputation. Please revise to focus on value proposition.',
    created_at: '2025-01-04T10:00:00Z',
    updated_at: '2025-01-04T10:15:00Z',
  },

  // Low risk auto-approved
  {
    id: 5,
    approval_id: 'appr_mno345',
    type: 'lead_action',
    status: 'approved',
    risk_level: 'low',
    title: 'Update lead status to "Qualified"',
    description: 'AI scored lead at 8.5/10, recommending qualification',
    context: {
      current_status: 'contacted',
      new_status: 'qualified',
      ai_score: 8.5,
    },
    risk_factors: [],
    risk_score: 15,
    lead_id: 5,
    lead_name: 'Modern Web Solutions',
    requested_by: 'Lead Scoring AI',
    requested_at: '2025-01-05T13:00:00Z',
    reviewed_by: 'Auto-approved (low risk)',
    reviewed_at: '2025-01-05T13:00:00Z',
    approved: true,
    notes: 'Auto-approved based on AI confidence and low risk score',
    created_at: '2025-01-05T13:00:00Z',
    updated_at: '2025-01-05T13:00:00Z',
  },

  // Pending video publication
  {
    id: 6,
    approval_id: 'appr_pqr678',
    type: 'video_publish',
    status: 'pending',
    risk_level: 'medium',
    title: 'Publish demo video for Acme Design Studio',
    description: '30-second video showcasing website improvements',
    context: {
      duration_seconds: 30,
      includes_voiceover: true,
      voice_provider: 'elevenlabs',
    },
    risk_factors: [
      'Public video will represent company brand',
      'Uses AI-generated voiceover',
      'Shows client website',
    ],
    risk_score: 55,
    lead_id: 1,
    lead_name: 'Acme Design Studio',
    video_id: 'vid_abc123',
    preview_data: {
      url: 'https://cdn.example.com/videos/vid_abc123.mp4',
      action: 'Publish to video library',
    },
    requested_by: 'Video Composer',
    requested_at: '2025-01-05T11:40:00Z',
    assigned_to: 'sarah@ourcompany.com',
    expires_at: '2025-01-05T15:40:00Z',
    created_at: '2025-01-05T11:40:00Z',
    updated_at: '2025-01-05T11:40:00Z',
  },

  // Expired approval
  {
    id: 7,
    approval_id: 'appr_stu901',
    type: 'email_response',
    status: 'expired',
    risk_level: 'medium',
    title: 'Follow-up email to inactive lead',
    description: 'Re-engagement email after 30 days of no response',
    context: {
      days_since_last_contact: 30,
      previous_attempts: 2,
    },
    risk_factors: [
      'Lead has not responded to previous emails',
      'May be perceived as spam',
    ],
    risk_score: 50,
    lead_id: 3,
    lead_name: 'Digital Growth Co',
    requested_by: 'Follow-up Automation',
    requested_at: '2025-01-03T10:00:00Z',
    assigned_to: 'sarah@ourcompany.com',
    expires_at: '2025-01-03T12:00:00Z',
    created_at: '2025-01-03T10:00:00Z',
    updated_at: '2025-01-03T12:00:00Z',
  },
]

export const mockApprovalRules: ApprovalRule[] = [
  {
    id: 1,
    rule_id: 'rule_001',
    name: 'High-value email responses',
    description: 'Require approval for emails mentioning pricing above $1000',
    type: 'email_response',
    conditions: [
      { field: 'contains_pricing', operator: 'equals', value: true },
      { field: 'pricing_amount', operator: 'greater_than', value: 1000 },
    ],
    requires_approval: true,
    risk_level: 'high',
    approvers: ['sarah@ourcompany.com', 'manager@ourcompany.com'],
    enabled: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    rule_id: 'rule_002',
    name: 'Urgent responses',
    description: 'Require immediate approval for urgent/critical leads',
    type: 'email_response',
    conditions: [
      { field: 'priority', operator: 'equals', value: 'urgent' },
    ],
    requires_approval: true,
    risk_level: 'critical',
    auto_approve_after_hours: 1,
    approvers: ['sarah@ourcompany.com'],
    enabled: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 3,
    rule_id: 'rule_003',
    name: 'Demo site deployments',
    description: 'Always require approval before deploying demo sites',
    type: 'demo_site_deploy',
    conditions: [],
    requires_approval: true,
    risk_level: 'medium',
    approvers: ['sarah@ourcompany.com'],
    enabled: true,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 4,
    rule_id: 'rule_004',
    name: 'Large email campaigns',
    description: 'Require approval for campaigns with 100+ recipients',
    type: 'email_campaign',
    conditions: [
      { field: 'recipients_count', operator: 'greater_than', value: 100 },
    ],
    requires_approval: true,
    risk_level: 'high',
    approvers: ['manager@ourcompany.com'],
    enabled: true,
    created_at: '2025-01-01T00:00:00Z',
  },
]

// Helper functions
export const getPendingApprovals = () =>
  mockApprovals.filter(approval => approval.status === 'pending')

export const getApprovalsByRiskLevel = (riskLevel: RiskLevel) =>
  mockApprovals.filter(approval => approval.risk_level === riskLevel)

export const getApprovalsByType = (type: ApprovalType) =>
  mockApprovals.filter(approval => approval.type === type)

export const getUrgentApprovals = () =>
  mockApprovals.filter(approval =>
    approval.status === 'pending' &&
    (approval.risk_level === 'critical' || approval.risk_level === 'high')
  )

export const getApprovalStats = () => ({
  total: mockApprovals.length,
  pending: mockApprovals.filter(a => a.status === 'pending').length,
  approved: mockApprovals.filter(a => a.status === 'approved').length,
  rejected: mockApprovals.filter(a => a.status === 'rejected').length,
  expired: mockApprovals.filter(a => a.status === 'expired').length,
  by_risk: {
    low: mockApprovals.filter(a => a.risk_level === 'low').length,
    medium: mockApprovals.filter(a => a.risk_level === 'medium').length,
    high: mockApprovals.filter(a => a.risk_level === 'high').length,
    critical: mockApprovals.filter(a => a.risk_level === 'critical').length,
  },
  avg_risk_score: mockApprovals.reduce((sum, a) => sum + a.risk_score, 0) / mockApprovals.length,
})
