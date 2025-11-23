/**
 * Mock n8n workflow data
 */

export type WorkflowStatus = 'active' | 'inactive' | 'error'
export type ExecutionStatus = 'running' | 'success' | 'error' | 'waiting'

export interface WorkflowNode {
  id: string
  name: string
  type: string
  parameters: Record<string, any>
  position: [number, number]
}

export interface WorkflowConnection {
  source: string
  target: string
  sourceOutput: string
  targetInput: string
}

export interface WorkflowExecution {
  id: number
  execution_id: string
  workflow_id: string
  status: ExecutionStatus
  started_at: string
  finished_at?: string
  duration_ms?: number
  data: {
    input?: Record<string, any>
    output?: Record<string, any>
    error?: string
  }
  created_at: string
}

export interface MockWorkflow {
  id: number
  workflow_id: string
  n8n_workflow_id?: string
  name: string
  description: string
  status: WorkflowStatus

  // Workflow definition
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]

  // Trigger configuration
  trigger_type: 'webhook' | 'schedule' | 'manual' | 'event'
  trigger_config?: {
    webhook_path?: string
    cron_expression?: string
    event_type?: string
  }

  // Statistics
  total_executions: number
  successful_executions: number
  failed_executions: number
  avg_execution_time_ms: number
  last_execution_at?: string
  last_execution_status?: ExecutionStatus

  // Settings
  enabled: boolean
  timeout_seconds: number
  retry_on_failure: boolean
  max_retries: number

  created_at: string
  updated_at: string
}

export const mockWorkflows: MockWorkflow[] = [
  // Lead enrichment workflow
  {
    id: 1,
    workflow_id: 'wf_enrich_abc123',
    n8n_workflow_id: 'n8n_123',
    name: 'Lead Enrichment Pipeline',
    description: 'Enriches new leads with contact info from Hunter.io, Apollo.io, and Clearbit',
    status: 'active',
    nodes: [
      {
        id: 'trigger',
        name: 'Webhook Trigger',
        type: 'n8n-nodes-base.webhook',
        parameters: {
          path: 'lead-created',
          method: 'POST',
        },
        position: [250, 300],
      },
      {
        id: 'hunter',
        name: 'Hunter.io - Find Email',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: 'https://api.hunter.io/v2/email-finder',
          method: 'GET',
        },
        position: [450, 200],
      },
      {
        id: 'apollo',
        name: 'Apollo.io - Enrich Lead',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: 'https://api.apollo.io/v1/people/match',
          method: 'POST',
        },
        position: [450, 400],
      },
      {
        id: 'merge',
        name: 'Merge Data',
        type: 'n8n-nodes-base.merge',
        parameters: {
          mode: 'combine',
        },
        position: [650, 300],
      },
      {
        id: 'update_lead',
        name: 'Update Lead in Database',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/leads/{{$json.lead_id}}',
          method: 'PUT',
        },
        position: [850, 300],
      },
    ],
    connections: [
      { source: 'trigger', target: 'hunter', sourceOutput: 'main', targetInput: 'main' },
      { source: 'trigger', target: 'apollo', sourceOutput: 'main', targetInput: 'main' },
      { source: 'hunter', target: 'merge', sourceOutput: 'main', targetInput: 'main' },
      { source: 'apollo', target: 'merge', sourceOutput: 'main', targetInput: 'main' },
      { source: 'merge', target: 'update_lead', sourceOutput: 'main', targetInput: 'main' },
    ],
    trigger_type: 'webhook',
    trigger_config: {
      webhook_path: 'lead-created',
    },
    total_executions: 1523,
    successful_executions: 1487,
    failed_executions: 36,
    avg_execution_time_ms: 2341,
    last_execution_at: '2025-01-05T14:30:00Z',
    last_execution_status: 'success',
    enabled: true,
    timeout_seconds: 60,
    retry_on_failure: true,
    max_retries: 3,
    created_at: '2024-12-01T10:00:00Z',
    updated_at: '2025-01-05T14:30:00Z',
  },

  // Email response workflow
  {
    id: 2,
    workflow_id: 'wf_email_def456',
    n8n_workflow_id: 'n8n_456',
    name: 'AI Email Response Generator',
    description: 'Generates AI responses for incoming emails and routes through approval workflow',
    status: 'active',
    nodes: [
      {
        id: 'trigger',
        name: 'Email Received',
        type: 'n8n-nodes-base.webhook',
        parameters: {
          path: 'email-received',
          method: 'POST',
        },
        position: [250, 300],
      },
      {
        id: 'analyze',
        name: 'Analyze Sentiment',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/ai/analyze-sentiment',
          method: 'POST',
        },
        position: [450, 300],
      },
      {
        id: 'generate',
        name: 'Generate AI Response',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/ai/generate-response',
          method: 'POST',
        },
        position: [650, 300],
      },
      {
        id: 'check_risk',
        name: 'Check Risk Level',
        type: 'n8n-nodes-base.if',
        parameters: {
          conditions: {
            boolean: [
              {
                value1: '={{$json.risk_score}}',
                value2: 70,
                operation: 'larger',
              },
            ],
          },
        },
        position: [850, 300],
      },
      {
        id: 'approval',
        name: 'Request Approval',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/approvals',
          method: 'POST',
        },
        position: [1050, 200],
      },
      {
        id: 'send_auto',
        name: 'Auto-Send Response',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/emails/send',
          method: 'POST',
        },
        position: [1050, 400],
      },
    ],
    connections: [
      { source: 'trigger', target: 'analyze', sourceOutput: 'main', targetInput: 'main' },
      { source: 'analyze', target: 'generate', sourceOutput: 'main', targetInput: 'main' },
      { source: 'generate', target: 'check_risk', sourceOutput: 'main', targetInput: 'main' },
      { source: 'check_risk', target: 'approval', sourceOutput: 'true', targetInput: 'main' },
      { source: 'check_risk', target: 'send_auto', sourceOutput: 'false', targetInput: 'main' },
    ],
    trigger_type: 'webhook',
    trigger_config: {
      webhook_path: 'email-received',
    },
    total_executions: 342,
    successful_executions: 339,
    failed_executions: 3,
    avg_execution_time_ms: 3124,
    last_execution_at: '2025-01-05T14:31:00Z',
    last_execution_status: 'success',
    enabled: true,
    timeout_seconds: 120,
    retry_on_failure: true,
    max_retries: 2,
    created_at: '2024-12-10T10:00:00Z',
    updated_at: '2025-01-05T14:31:00Z',
  },

  // Daily lead scoring workflow
  {
    id: 3,
    workflow_id: 'wf_score_ghi789',
    n8n_workflow_id: 'n8n_789',
    name: 'Daily Lead Scoring',
    description: 'Runs ML lead scoring on all active leads daily',
    status: 'active',
    nodes: [
      {
        id: 'trigger',
        name: 'Schedule: Daily 9 AM',
        type: 'n8n-nodes-base.cron',
        parameters: {
          cronExpression: '0 9 * * *',
        },
        position: [250, 300],
      },
      {
        id: 'fetch_leads',
        name: 'Fetch Active Leads',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/leads?status=active',
          method: 'GET',
        },
        position: [450, 300],
      },
      {
        id: 'score_batch',
        name: 'Batch Score Leads',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/ml/score-leads',
          method: 'POST',
        },
        position: [650, 300],
      },
      {
        id: 'update_scores',
        name: 'Update Lead Scores',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/leads/batch-update',
          method: 'PUT',
        },
        position: [850, 300],
      },
    ],
    connections: [
      { source: 'trigger', target: 'fetch_leads', sourceOutput: 'main', targetInput: 'main' },
      { source: 'fetch_leads', target: 'score_batch', sourceOutput: 'main', targetInput: 'main' },
      { source: 'score_batch', target: 'update_scores', sourceOutput: 'main', targetInput: 'main' },
    ],
    trigger_type: 'schedule',
    trigger_config: {
      cron_expression: '0 9 * * *',
    },
    total_executions: 35,
    successful_executions: 35,
    failed_executions: 0,
    avg_execution_time_ms: 12456,
    last_execution_at: '2025-01-05T09:00:00Z',
    last_execution_status: 'success',
    enabled: true,
    timeout_seconds: 300,
    retry_on_failure: true,
    max_retries: 3,
    created_at: '2024-12-01T10:00:00Z',
    updated_at: '2025-01-05T09:00:00Z',
  },

  // Demo site generation workflow
  {
    id: 4,
    workflow_id: 'wf_demo_jkl012',
    n8n_workflow_id: 'n8n_012',
    name: 'Automated Demo Site Generation',
    description: 'Analyzes lead website, generates improved demo, and deploys to Vercel',
    status: 'active',
    nodes: [
      {
        id: 'trigger',
        name: 'Manual Trigger',
        type: 'n8n-nodes-base.manualTrigger',
        parameters: {},
        position: [250, 300],
      },
      {
        id: 'analyze',
        name: 'Analyze Website',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/demo-sites/analyze',
          method: 'POST',
        },
        position: [450, 300],
      },
      {
        id: 'generate',
        name: 'Generate Demo Site',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/demo-sites/generate',
          method: 'POST',
        },
        position: [650, 300],
      },
      {
        id: 'approval',
        name: 'Request Deployment Approval',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/approvals',
          method: 'POST',
        },
        position: [850, 300],
      },
      {
        id: 'deploy',
        name: 'Deploy to Vercel',
        type: 'n8n-nodes-base.httpRequest',
        parameters: {
          url: '{{$env.API_URL}}/api/v1/demo-sites/deploy',
          method: 'POST',
        },
        position: [1050, 300],
      },
    ],
    connections: [
      { source: 'trigger', target: 'analyze', sourceOutput: 'main', targetInput: 'main' },
      { source: 'analyze', target: 'generate', sourceOutput: 'main', targetInput: 'main' },
      { source: 'generate', target: 'approval', sourceOutput: 'main', targetInput: 'main' },
      { source: 'approval', target: 'deploy', sourceOutput: 'main', targetInput: 'main' },
    ],
    trigger_type: 'manual',
    total_executions: 23,
    successful_executions: 21,
    failed_executions: 2,
    avg_execution_time_ms: 45234,
    last_execution_at: '2025-01-05T11:00:00Z',
    last_execution_status: 'success',
    enabled: true,
    timeout_seconds: 600,
    retry_on_failure: false,
    max_retries: 0,
    created_at: '2024-12-15T10:00:00Z',
    updated_at: '2025-01-05T11:00:00Z',
  },

  // Inactive workflow with error
  {
    id: 5,
    workflow_id: 'wf_slack_mno345',
    n8n_workflow_id: 'n8n_345',
    name: 'Slack Notifications',
    description: 'Send Slack notifications for high-priority leads',
    status: 'error',
    nodes: [
      {
        id: 'trigger',
        name: 'High Priority Lead',
        type: 'n8n-nodes-base.webhook',
        parameters: {
          path: 'high-priority-lead',
          method: 'POST',
        },
        position: [250, 300],
      },
      {
        id: 'slack',
        name: 'Send Slack Message',
        type: 'n8n-nodes-base.slack',
        parameters: {
          channel: '#leads',
        },
        position: [450, 300],
      },
    ],
    connections: [
      { source: 'trigger', target: 'slack', sourceOutput: 'main', targetInput: 'main' },
    ],
    trigger_type: 'webhook',
    trigger_config: {
      webhook_path: 'high-priority-lead',
    },
    total_executions: 15,
    successful_executions: 12,
    failed_executions: 3,
    avg_execution_time_ms: 892,
    last_execution_at: '2025-01-04T15:00:00Z',
    last_execution_status: 'error',
    enabled: false,
    timeout_seconds: 30,
    retry_on_failure: true,
    max_retries: 3,
    created_at: '2024-12-20T10:00:00Z',
    updated_at: '2025-01-04T15:00:00Z',
  },
]

export const mockExecutions: WorkflowExecution[] = [
  {
    id: 1,
    execution_id: 'exec_001',
    workflow_id: 'wf_enrich_abc123',
    status: 'success',
    started_at: '2025-01-05T14:30:00Z',
    finished_at: '2025-01-05T14:30:02Z',
    duration_ms: 2341,
    data: {
      input: {
        lead_id: 145,
        company_name: 'Test Company',
        website: 'testcompany.com',
      },
      output: {
        email: 'contact@testcompany.com',
        phone: '(555) 123-4567',
        enrichment_source: 'hunter.io',
      },
    },
    created_at: '2025-01-05T14:30:00Z',
  },
  {
    id: 2,
    execution_id: 'exec_002',
    workflow_id: 'wf_email_def456',
    status: 'success',
    started_at: '2025-01-05T14:31:00Z',
    finished_at: '2025-01-05T14:31:03Z',
    duration_ms: 3124,
    data: {
      input: {
        conversation_id: 'conv_abc123',
        message: 'Thanks for the demo...',
      },
      output: {
        response_generated: true,
        risk_score: 75,
        approval_required: true,
      },
    },
    created_at: '2025-01-05T14:31:00Z',
  },
  {
    id: 3,
    execution_id: 'exec_003',
    workflow_id: 'wf_slack_mno345',
    status: 'error',
    started_at: '2025-01-04T15:00:00Z',
    finished_at: '2025-01-04T15:00:01Z',
    duration_ms: 892,
    data: {
      input: {
        lead_id: 123,
        priority: 'urgent',
      },
      error: 'Slack API authentication failed: invalid token',
    },
    created_at: '2025-01-04T15:00:00Z',
  },
]

// Helper functions
export const getActiveWorkflows = () =>
  mockWorkflows.filter(wf => wf.status === 'active')

export const getWorkflowsByTrigger = (triggerType: MockWorkflow['trigger_type']) =>
  mockWorkflows.filter(wf => wf.trigger_type === triggerType)

export const getFailingWorkflows = () =>
  mockWorkflows.filter(wf => wf.status === 'error' || (wf.failed_executions / wf.total_executions) > 0.1)

export const getRecentExecutions = (workflowId: string, limit: number = 10) =>
  mockExecutions
    .filter(exec => exec.workflow_id === workflowId)
    .slice(0, limit)

export const getWorkflowStats = () => ({
  total: mockWorkflows.length,
  active: mockWorkflows.filter(wf => wf.status === 'active').length,
  inactive: mockWorkflows.filter(wf => wf.status === 'inactive').length,
  error: mockWorkflows.filter(wf => wf.status === 'error').length,
  total_executions: mockWorkflows.reduce((sum, wf) => sum + wf.total_executions, 0),
  successful_executions: mockWorkflows.reduce((sum, wf) => sum + wf.successful_executions, 0),
  failed_executions: mockWorkflows.reduce((sum, wf) => sum + wf.failed_executions, 0),
  avg_success_rate: (mockWorkflows.reduce((sum, wf) => sum + (wf.successful_executions / wf.total_executions), 0) / mockWorkflows.length) * 100,
})
