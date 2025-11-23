/**
 * Mock AI model performance data for AI-GYM
 */

export type ModelProvider = 'anthropic' | 'openai' | 'google' | 'deepseek' | 'meta'
export type TaskType = 'email_generation' | 'lead_scoring' | 'sentiment_analysis' | 'content_generation' | 'script_writing' | 'analysis'

export interface ModelConfig {
  model_id: string
  provider: ModelProvider
  name: string
  display_name: string
  context_window: number
  cost_per_1k_input_tokens: number
  cost_per_1k_output_tokens: number
  max_output_tokens: number
  supports_streaming: boolean
  supports_function_calling: boolean
}

export interface ModelPerformance {
  model_id: string
  task_type: TaskType
  total_requests: number
  successful_requests: number
  failed_requests: number
  avg_response_time_ms: number
  avg_quality_score: number
  avg_cost_per_request: number
  total_cost: number
  p95_response_time_ms: number
  error_rate: number
  last_24h_requests: number
  last_7d_requests: number
}

export interface ABTest {
  id: number
  test_id: string
  name: string
  description: string
  task_type: TaskType
  status: 'draft' | 'running' | 'paused' | 'completed'
  models: string[]
  traffic_split: Record<string, number>
  started_at?: string
  completed_at?: string
  winner?: string
  results?: {
    model_id: string
    requests: number
    avg_quality: number
    avg_cost: number
    avg_response_time: number
  }[]
  created_at: string
}

export interface QualityMetric {
  id: number
  metric_id: string
  model_id: string
  task_type: TaskType
  request_id: string
  quality_score: number
  user_feedback?: 'positive' | 'negative' | 'neutral'
  feedback_text?: string
  response_used: boolean
  response_time_ms: number
  cost: number
  created_at: string
}

export const mockModelConfigs: ModelConfig[] = [
  {
    model_id: 'claude-sonnet-4.5',
    provider: 'anthropic',
    name: 'claude-sonnet-4.5',
    display_name: 'Claude Sonnet 4.5',
    context_window: 200000,
    cost_per_1k_input_tokens: 0.003,
    cost_per_1k_output_tokens: 0.015,
    max_output_tokens: 8192,
    supports_streaming: true,
    supports_function_calling: true,
  },
  {
    model_id: 'claude-opus-4',
    provider: 'anthropic',
    name: 'claude-opus-4',
    display_name: 'Claude Opus 4',
    context_window: 200000,
    cost_per_1k_input_tokens: 0.015,
    cost_per_1k_output_tokens: 0.075,
    max_output_tokens: 8192,
    supports_streaming: true,
    supports_function_calling: true,
  },
  {
    model_id: 'gpt-4-turbo',
    provider: 'openai',
    name: 'gpt-4-turbo',
    display_name: 'GPT-4 Turbo',
    context_window: 128000,
    cost_per_1k_input_tokens: 0.01,
    cost_per_1k_output_tokens: 0.03,
    max_output_tokens: 4096,
    supports_streaming: true,
    supports_function_calling: true,
  },
  {
    model_id: 'gpt-4o',
    provider: 'openai',
    name: 'gpt-4o',
    display_name: 'GPT-4o',
    context_window: 128000,
    cost_per_1k_input_tokens: 0.005,
    cost_per_1k_output_tokens: 0.015,
    max_output_tokens: 16384,
    supports_streaming: true,
    supports_function_calling: true,
  },
  {
    model_id: 'gemini-2.0-flash',
    provider: 'google',
    name: 'gemini-2.0-flash',
    display_name: 'Gemini 2.0 Flash',
    context_window: 1000000,
    cost_per_1k_input_tokens: 0.0001,
    cost_per_1k_output_tokens: 0.0004,
    max_output_tokens: 8192,
    supports_streaming: true,
    supports_function_calling: true,
  },
  {
    model_id: 'deepseek-chat',
    provider: 'deepseek',
    name: 'deepseek-chat',
    display_name: 'DeepSeek Chat',
    context_window: 64000,
    cost_per_1k_input_tokens: 0.0001,
    cost_per_1k_output_tokens: 0.0002,
    max_output_tokens: 4096,
    supports_streaming: true,
    supports_function_calling: false,
  },
]

export const mockModelPerformance: ModelPerformance[] = [
  {
    model_id: 'claude-sonnet-4.5',
    task_type: 'email_generation',
    total_requests: 342,
    successful_requests: 339,
    failed_requests: 3,
    avg_response_time_ms: 2341,
    avg_quality_score: 8.7,
    avg_cost_per_request: 0.042,
    total_cost: 14.36,
    p95_response_time_ms: 3892,
    error_rate: 0.88,
    last_24h_requests: 45,
    last_7d_requests: 234,
  },
  {
    model_id: 'gpt-4-turbo',
    task_type: 'email_generation',
    total_requests: 298,
    successful_requests: 292,
    failed_requests: 6,
    avg_response_time_ms: 1876,
    avg_quality_score: 8.3,
    avg_cost_per_request: 0.038,
    total_cost: 11.32,
    p95_response_time_ms: 3124,
    error_rate: 2.01,
    last_24h_requests: 38,
    last_7d_requests: 198,
  },
  {
    model_id: 'gpt-4o',
    task_type: 'email_generation',
    total_requests: 412,
    successful_requests: 408,
    failed_requests: 4,
    avg_response_time_ms: 1542,
    avg_quality_score: 8.5,
    avg_cost_per_request: 0.024,
    total_cost: 9.89,
    p95_response_time_ms: 2487,
    error_rate: 0.97,
    last_24h_requests: 52,
    last_7d_requests: 287,
  },
  {
    model_id: 'claude-sonnet-4.5',
    task_type: 'lead_scoring',
    total_requests: 1523,
    successful_requests: 1520,
    failed_requests: 3,
    avg_response_time_ms: 892,
    avg_quality_score: 9.1,
    avg_cost_per_request: 0.008,
    total_cost: 12.18,
    p95_response_time_ms: 1423,
    error_rate: 0.20,
    last_24h_requests: 187,
    last_7d_requests: 1089,
  },
  {
    model_id: 'gpt-4o',
    task_type: 'lead_scoring',
    total_requests: 1345,
    successful_requests: 1338,
    failed_requests: 7,
    avg_response_time_ms: 743,
    avg_quality_score: 8.8,
    avg_cost_per_request: 0.006,
    total_cost: 8.07,
    p95_response_time_ms: 1124,
    error_rate: 0.52,
    last_24h_requests: 165,
    last_7d_requests: 934,
  },
  {
    model_id: 'gemini-2.0-flash',
    task_type: 'lead_scoring',
    total_requests: 2134,
    successful_requests: 2098,
    failed_requests: 36,
    avg_response_time_ms: 456,
    avg_quality_score: 8.2,
    avg_cost_per_request: 0.001,
    total_cost: 2.13,
    p95_response_time_ms: 782,
    error_rate: 1.69,
    last_24h_requests: 267,
    last_7d_requests: 1523,
  },
  {
    model_id: 'claude-sonnet-4.5',
    task_type: 'script_writing',
    total_requests: 87,
    successful_requests: 86,
    failed_requests: 1,
    avg_response_time_ms: 4567,
    avg_quality_score: 9.3,
    avg_cost_per_request: 0.156,
    total_cost: 13.57,
    p95_response_time_ms: 6234,
    error_rate: 1.15,
    last_24h_requests: 12,
    last_7d_requests: 56,
  },
  {
    model_id: 'gpt-4-turbo',
    task_type: 'script_writing',
    total_requests: 72,
    successful_requests: 69,
    failed_requests: 3,
    avg_response_time_ms: 3892,
    avg_quality_score: 8.6,
    avg_cost_per_request: 0.142,
    total_cost: 10.22,
    p95_response_time_ms: 5123,
    error_rate: 4.17,
    last_24h_requests: 9,
    last_7d_requests: 47,
  },
  {
    model_id: 'claude-sonnet-4.5',
    task_type: 'analysis',
    total_requests: 234,
    successful_requests: 233,
    failed_requests: 1,
    avg_response_time_ms: 3124,
    avg_quality_score: 9.0,
    avg_cost_per_request: 0.087,
    total_cost: 20.36,
    p95_response_time_ms: 4892,
    error_rate: 0.43,
    last_24h_requests: 28,
    last_7d_requests: 167,
  },
  {
    model_id: 'deepseek-chat',
    task_type: 'content_generation',
    total_requests: 567,
    successful_requests: 542,
    failed_requests: 25,
    avg_response_time_ms: 1234,
    avg_quality_score: 7.8,
    avg_cost_per_request: 0.003,
    total_cost: 1.70,
    p95_response_time_ms: 2341,
    error_rate: 4.41,
    last_24h_requests: 67,
    last_7d_requests: 389,
  },
]

export const mockABTests: ABTest[] = [
  {
    id: 1,
    test_id: 'test_abc123',
    name: 'Email Generation: Claude vs GPT-4o',
    description: 'Testing which model produces better personalized email responses',
    task_type: 'email_generation',
    status: 'running',
    models: ['claude-sonnet-4.5', 'gpt-4o'],
    traffic_split: {
      'claude-sonnet-4.5': 50,
      'gpt-4o': 50,
    },
    started_at: '2025-01-03T10:00:00Z',
    results: [
      {
        model_id: 'claude-sonnet-4.5',
        requests: 145,
        avg_quality: 8.7,
        avg_cost: 0.042,
        avg_response_time: 2341,
      },
      {
        model_id: 'gpt-4o',
        requests: 152,
        avg_quality: 8.5,
        avg_cost: 0.024,
        avg_response_time: 1542,
      },
    ],
    created_at: '2025-01-03T09:00:00Z',
  },
  {
    id: 2,
    test_id: 'test_def456',
    name: 'Lead Scoring: Multi-Model Comparison',
    description: 'Comparing Claude, GPT-4o, and Gemini for lead qualification accuracy',
    task_type: 'lead_scoring',
    status: 'completed',
    models: ['claude-sonnet-4.5', 'gpt-4o', 'gemini-2.0-flash'],
    traffic_split: {
      'claude-sonnet-4.5': 33,
      'gpt-4o': 33,
      'gemini-2.0-flash': 34,
    },
    started_at: '2024-12-20T10:00:00Z',
    completed_at: '2025-01-02T18:00:00Z',
    winner: 'claude-sonnet-4.5',
    results: [
      {
        model_id: 'claude-sonnet-4.5',
        requests: 456,
        avg_quality: 9.1,
        avg_cost: 0.008,
        avg_response_time: 892,
      },
      {
        model_id: 'gpt-4o',
        requests: 448,
        avg_quality: 8.8,
        avg_cost: 0.006,
        avg_response_time: 743,
      },
      {
        model_id: 'gemini-2.0-flash',
        requests: 467,
        avg_quality: 8.2,
        avg_cost: 0.001,
        avg_response_time: 456,
      },
    ],
    created_at: '2024-12-20T09:00:00Z',
  },
  {
    id: 3,
    test_id: 'test_ghi789',
    name: 'Budget AI: DeepSeek vs Gemini',
    description: 'Testing cost-effective models for high-volume content generation',
    task_type: 'content_generation',
    status: 'draft',
    models: ['deepseek-chat', 'gemini-2.0-flash'],
    traffic_split: {
      'deepseek-chat': 50,
      'gemini-2.0-flash': 50,
    },
    created_at: '2025-01-05T14:00:00Z',
  },
]

export const mockQualityMetrics: QualityMetric[] = [
  {
    id: 1,
    metric_id: 'qm_001',
    model_id: 'claude-sonnet-4.5',
    task_type: 'email_generation',
    request_id: 'req_001',
    quality_score: 9.2,
    user_feedback: 'positive',
    feedback_text: 'Perfect tone and personalization',
    response_used: true,
    response_time_ms: 2341,
    cost: 0.042,
    created_at: '2025-01-05T14:30:00Z',
  },
  {
    id: 2,
    metric_id: 'qm_002',
    model_id: 'gpt-4o',
    task_type: 'email_generation',
    request_id: 'req_002',
    quality_score: 8.5,
    user_feedback: 'positive',
    response_used: true,
    response_time_ms: 1542,
    cost: 0.024,
    created_at: '2025-01-05T14:25:00Z',
  },
  {
    id: 3,
    metric_id: 'qm_003',
    model_id: 'gemini-2.0-flash',
    task_type: 'lead_scoring',
    request_id: 'req_003',
    quality_score: 8.1,
    response_used: true,
    response_time_ms: 456,
    cost: 0.001,
    created_at: '2025-01-05T14:20:00Z',
  },
]

// Helper functions
export const getModelPerformanceByTask = (taskType: TaskType) =>
  mockModelPerformance.filter(perf => perf.task_type === taskType)

export const getTopModelsByQuality = (taskType: TaskType, limit: number = 3) =>
  [...mockModelPerformance]
    .filter(perf => perf.task_type === taskType)
    .sort((a, b) => b.avg_quality_score - a.avg_quality_score)
    .slice(0, limit)

export const getMostCostEffective = (taskType: TaskType, limit: number = 3) =>
  [...mockModelPerformance]
    .filter(perf => perf.task_type === taskType)
    .map(perf => ({
      ...perf,
      quality_per_dollar: perf.avg_quality_score / perf.avg_cost_per_request,
    }))
    .sort((a, b) => b.quality_per_dollar - a.quality_per_dollar)
    .slice(0, limit)

export const getActiveABTests = () =>
  mockABTests.filter(test => test.status === 'running')

export const getTotalModelStats = () => ({
  total_requests: mockModelPerformance.reduce((sum, p) => sum + p.total_requests, 0),
  total_cost: mockModelPerformance.reduce((sum, p) => sum + p.total_cost, 0),
  avg_quality: mockModelPerformance.reduce((sum, p) => sum + p.avg_quality_score, 0) / mockModelPerformance.length,
  avg_response_time: mockModelPerformance.reduce((sum, p) => sum + p.avg_response_time_ms, 0) / mockModelPerformance.length,
  total_errors: mockModelPerformance.reduce((sum, p) => sum + p.failed_requests, 0),
  models_in_use: [...new Set(mockModelPerformance.map(p => p.model_id))].length,
})
