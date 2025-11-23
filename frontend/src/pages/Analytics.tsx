import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../services/phase3Api'
import { useAnalyticsUpdates } from '../hooks/useWebSocket'
import { 
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CurrencyDollarIcon,
  UserGroupIcon,
  EnvelopeIcon,
  DocumentArrowDownIcon,
  CalendarIcon,
  FunnelIcon,
  
} from '@heroicons/react/24/outline'
import {
  LineChart,
  Line,
  
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

type ViewMode = 'dashboard' | 'funnel' | 'roi' | 'performance' | 'export'

const TERMINAL_COLORS = {
  primary: '#00FF00',
  secondary: '#00CC00',
  accent: '#00B300',
  background: '#0a0a0a',
  surface: '#111111',
  border: '#1a1a1a',
  text: {
    primary: '#ffffff',
    secondary: '#a0a0a0',
    muted: '#666666'
  }
}

const CHART_COLORS = [
  TERMINAL_COLORS.primary,
  TERMINAL_COLORS.secondary,
  TERMINAL_COLORS.accent,
  '#FFD700',
  '#FF6B6B',
  '#4ECDC4',
  '#45B7D1',
  '#96CEB4'
]

export default function Analytics() {
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard')
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  })

  // WebSocket for real-time analytics updates
  const { lastMessage, isConnected } = useAnalyticsUpdates()

  // Fetch analytics data
  const { data: analyticsData, isLoading } = useQuery({
    queryKey: ['analytics', dateRange],
    queryFn: () => analyticsApi.getDashboardData(dateRange).then(res => res.data),
  })

  // Handle real-time updates
  useEffect(() => {
    if (lastMessage && lastMessage.data.type === 'analytics_update') {
      // Invalidate and refetch analytics data
      // queryClient.invalidateQueries({ queryKey: ['analytics'] })
    }
  }, [lastMessage])

  const handleExport = async (type: string) => {
    try {
      const response = await analyticsApi.exportData(type as any, dateRange)
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}_export_${new Date().toISOString().split('T')[0]}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
        <div className="text-dark-text-secondary mt-2">Loading analytics...</div>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <ChartBarIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
        <div className="text-dark-text-muted">No analytics data available</div>
      </div>
    )
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-terminal p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Leads</p>
              <p className="text-3xl font-bold text-terminal-400 font-mono">
                {analyticsData.lead_funnel.total_scraped.toLocaleString()}
              </p>
              <div className="flex items-center text-sm text-terminal-400 mt-1">
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                <span>+12.5% vs last period</span>
              </div>
            </div>
            <UserGroupIcon className="w-12 h-12 text-terminal-500" />
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Conversion Rate</p>
              <p className="text-3xl font-bold text-terminal-400 font-mono">
                {((analyticsData.lead_funnel.total_converted / analyticsData.lead_funnel.total_scraped) * 100).toFixed(1)}%
              </p>
              <div className="flex items-center text-sm text-red-400 mt-1">
                <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
                <span>-2.1% vs last period</span>
              </div>
            </div>
            <FunnelIcon className="w-12 h-12 text-terminal-500" />
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Revenue</p>
              <p className="text-3xl font-bold text-terminal-400 font-mono">
                ${analyticsData.roi_metrics.total_revenue.toLocaleString()}
              </p>
              <div className="flex items-center text-sm text-terminal-400 mt-1">
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                <span>+8.7% vs last period</span>
              </div>
            </div>
            <CurrencyDollarIcon className="w-12 h-12 text-terminal-500" />
          </div>
        </div>

        <div className="card-terminal p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">ROI</p>
              <p className="text-3xl font-bold text-terminal-400 font-mono">
                {analyticsData.roi_metrics.roi_percentage.toFixed(1)}%
              </p>
              <div className="flex items-center text-sm text-terminal-400 mt-1">
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
                <span>+15.3% vs last period</span>
              </div>
            </div>
            <ChartBarIcon className="w-12 h-12 text-terminal-500" />
          </div>
        </div>
      </div>

      {/* Performance Trends Chart */}
      <div className="card-terminal p-6">
        <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
          Performance Trends
        </h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={analyticsData.performance_trends}>
              <CartesianGrid strokeDasharray="3 3" stroke={TERMINAL_COLORS.border} />
              <XAxis 
                dataKey="date" 
                stroke={TERMINAL_COLORS.text.secondary}
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis stroke={TERMINAL_COLORS.text.secondary} fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: TERMINAL_COLORS.surface,
                  border: `1px solid ${TERMINAL_COLORS.border}`,
                  borderRadius: '8px',
                  color: TERMINAL_COLORS.text.primary
                }}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="leads_scraped" 
                stroke={TERMINAL_COLORS.primary} 
                strokeWidth={2}
                name="Leads Scraped"
              />
              <Line 
                type="monotone" 
                dataKey="emails_sent" 
                stroke={TERMINAL_COLORS.secondary} 
                strokeWidth={2}
                name="Emails Sent"
              />
              <Line 
                type="monotone" 
                dataKey="responses_received" 
                stroke={CHART_COLORS[3]} 
                strokeWidth={2}
                name="Responses"
              />
              <Line 
                type="monotone" 
                dataKey="conversions" 
                stroke={CHART_COLORS[4]} 
                strokeWidth={2}
                name="Conversions"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Performing Templates and Location Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Top Performing Templates
          </h2>
          <div className="space-y-3">
            {analyticsData.top_performing_templates.slice(0, 5).map((template) => (
              <div key={template.id} className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
                <div className="flex-1">
                  <div className="font-medium text-dark-text-primary">{template.name}</div>
                  <div className="text-xs text-dark-text-secondary">{template.category}</div>
                </div>
                <div className="text-right">
                  <div className="text-terminal-400 font-mono font-bold">
                    {template.performance_metrics ? 
                      `${(template.performance_metrics.response_rate * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </div>
                  <div className="text-xs text-dark-text-muted">Response Rate</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Location Performance
          </h2>
          <div className="space-y-3">
            {analyticsData.location_performance.slice(0, 5).map((location) => (
              <div key={location.location} className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
                <div className="flex-1">
                  <div className="font-medium text-dark-text-primary">{location.location}</div>
                  <div className="text-xs text-dark-text-secondary">
                    {location.lead_count} leads
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-terminal-400 font-mono font-bold">
                    ${location.revenue.toLocaleString()}
                  </div>
                  <div className="text-xs text-dark-text-muted">Revenue</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  const renderFunnelView = () => (
    <div className="space-y-6">
      <div className="card-terminal p-6">
        <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-6">
          Lead Conversion Funnel
        </h2>
        
        {/* Funnel Visualization */}
        <div className="space-y-4">
          <div className="relative">
            <div className="bg-terminal-500/20 border border-terminal-500/50 rounded p-4">
              <div className="flex items-center justify-between">
                <span className="text-terminal-400 font-mono">Leads Scraped</span>
                <span className="text-2xl font-bold text-terminal-400 font-mono">
                  {analyticsData.lead_funnel.total_scraped.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-terminal-500/30 h-2 rounded mt-2" />
            </div>
          </div>
          
          <div className="relative ml-8">
            <div className="bg-blue-500/20 border border-blue-500/50 rounded p-4">
              <div className="flex items-center justify-between">
                <span className="text-blue-400 font-mono">Leads Contacted</span>
                <span className="text-2xl font-bold text-blue-400 font-mono">
                  {analyticsData.lead_funnel.total_contacted.toLocaleString()}
                </span>
              </div>
              <div className="bg-blue-500/30 h-2 rounded mt-2" style={{
                width: `${(analyticsData.lead_funnel.total_contacted / analyticsData.lead_funnel.total_scraped) * 100}%`
              }} />
              <div className="text-xs text-blue-300 mt-1">
                {((analyticsData.lead_funnel.total_contacted / analyticsData.lead_funnel.total_scraped) * 100).toFixed(1)}% of scraped
              </div>
            </div>
          </div>
          
          <div className="relative ml-16">
            <div className="bg-yellow-500/20 border border-yellow-500/50 rounded p-4">
              <div className="flex items-center justify-between">
                <span className="text-yellow-400 font-mono">Responses Received</span>
                <span className="text-2xl font-bold text-yellow-400 font-mono">
                  {analyticsData.lead_funnel.total_responded.toLocaleString()}
                </span>
              </div>
              <div className="bg-yellow-500/30 h-2 rounded mt-2" style={{
                width: `${(analyticsData.lead_funnel.total_responded / analyticsData.lead_funnel.total_contacted) * 100}%`
              }} />
              <div className="text-xs text-yellow-300 mt-1">
                {((analyticsData.lead_funnel.total_responded / analyticsData.lead_funnel.total_contacted) * 100).toFixed(1)}% of contacted
              </div>
            </div>
          </div>
          
          <div className="relative ml-24">
            <div className="bg-green-500/20 border border-green-500/50 rounded p-4">
              <div className="flex items-center justify-between">
                <span className="text-green-400 font-mono">Conversions</span>
                <span className="text-2xl font-bold text-green-400 font-mono">
                  {analyticsData.lead_funnel.total_converted.toLocaleString()}
                </span>
              </div>
              <div className="bg-green-500/30 h-2 rounded mt-2" style={{
                width: `${(analyticsData.lead_funnel.total_converted / analyticsData.lead_funnel.total_responded) * 100}%`
              }} />
              <div className="text-xs text-green-300 mt-1">
                {((analyticsData.lead_funnel.total_converted / analyticsData.lead_funnel.total_responded) * 100).toFixed(1)}% of responses
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Funnel Chart */}
      <div className="card-terminal p-6">
        <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
          Conversion Rates by Stage
        </h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={[
              { stage: 'Scraped', count: analyticsData.lead_funnel.total_scraped, rate: 100 },
              { stage: 'Contacted', count: analyticsData.lead_funnel.total_contacted, rate: (analyticsData.lead_funnel.total_contacted / analyticsData.lead_funnel.total_scraped) * 100 },
              { stage: 'Responded', count: analyticsData.lead_funnel.total_responded, rate: (analyticsData.lead_funnel.total_responded / analyticsData.lead_funnel.total_scraped) * 100 },
              { stage: 'Converted', count: analyticsData.lead_funnel.total_converted, rate: (analyticsData.lead_funnel.total_converted / analyticsData.lead_funnel.total_scraped) * 100 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke={TERMINAL_COLORS.border} />
              <XAxis dataKey="stage" stroke={TERMINAL_COLORS.text.secondary} />
              <YAxis stroke={TERMINAL_COLORS.text.secondary} />
              <Tooltip
                contentStyle={{
                  backgroundColor: TERMINAL_COLORS.surface,
                  border: `1px solid ${TERMINAL_COLORS.border}`,
                  borderRadius: '8px',
                  color: TERMINAL_COLORS.text.primary
                }}
              />
              <Bar dataKey="count" fill={TERMINAL_COLORS.primary} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )

  const renderROIView = () => (
    <div className="space-y-6">
      {/* ROI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-terminal p-6">
          <div className="text-center">
            <CurrencyDollarIcon className="w-12 h-12 text-terminal-500 mx-auto mb-2" />
            <p className="text-dark-text-secondary text-sm">Total Revenue</p>
            <p className="text-3xl font-bold text-terminal-400 font-mono">
              ${analyticsData.roi_metrics.total_revenue.toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="card-terminal p-6">
          <div className="text-center">
            <ChartBarIcon className="w-12 h-12 text-red-500 mx-auto mb-2" />
            <p className="text-dark-text-secondary text-sm">Total Cost</p>
            <p className="text-3xl font-bold text-red-400 font-mono">
              ${analyticsData.roi_metrics.total_cost.toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="card-terminal p-6">
          <div className="text-center">
            <ArrowTrendingUpIcon className="w-12 h-12 text-blue-500 mx-auto mb-2" />
            <p className="text-dark-text-secondary text-sm">ROI</p>
            <p className="text-3xl font-bold text-blue-400 font-mono">
              {analyticsData.roi_metrics.roi_percentage.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Cost per Lead and Revenue per Lead */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card-terminal p-6">
          <h3 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Cost Analysis
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Cost per Lead</span>
              <span className="text-terminal-400 font-mono font-bold">
                ${analyticsData.roi_metrics.cost_per_lead.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-dark-text-secondary">Revenue per Lead</span>
              <span className="text-terminal-400 font-mono font-bold">
                ${analyticsData.roi_metrics.revenue_per_lead.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-dark-border">
              <span className="text-dark-text-secondary">Net per Lead</span>
              <span className="text-terminal-400 font-mono font-bold">
                ${(analyticsData.roi_metrics.revenue_per_lead - analyticsData.roi_metrics.cost_per_lead).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="card-terminal p-6">
          <h3 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            ROI Breakdown
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    { name: 'Profit', value: analyticsData.roi_metrics.total_revenue - analyticsData.roi_metrics.total_cost },
                    { name: 'Cost', value: analyticsData.roi_metrics.total_cost }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  <Cell fill={TERMINAL_COLORS.primary} />
                  <Cell fill="#FF6B6B" />
                </Pie>
                <Tooltip
                  formatter={(value) => [`$${Number(value).toLocaleString()}`, '']}
                  contentStyle={{
                    backgroundColor: TERMINAL_COLORS.surface,
                    border: `1px solid ${TERMINAL_COLORS.border}`,
                    borderRadius: '8px',
                    color: TERMINAL_COLORS.text.primary
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )

  const renderExportCenter = () => (
    <div className="space-y-6">
      <div className="card-terminal p-6">
        <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-6">
          Export Center
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => handleExport('leads')}
            className="btn-terminal-solid p-6 h-auto flex-col"
          >
            <UserGroupIcon className="w-8 h-8 mb-2" />
            <span>Export Leads</span>
            <span className="text-xs text-black/70 mt-1">CSV format</span>
          </button>
          
          <button
            onClick={() => handleExport('templates')}
            className="btn-terminal-solid p-6 h-auto flex-col"
          >
            <EnvelopeIcon className="w-8 h-8 mb-2" />
            <span>Export Templates</span>
            <span className="text-xs text-black/70 mt-1">CSV format</span>
          </button>
          
          <button
            onClick={() => handleExport('notifications')}
            className="btn-terminal-solid p-6 h-auto flex-col"
          >
            <DocumentArrowDownIcon className="w-8 h-8 mb-2" />
            <span>Export Reports</span>
            <span className="text-xs text-black/70 mt-1">PDF format</span>
          </button>
          
          <button
            onClick={() => handleExport('schedules')}
            className="btn-terminal-solid p-6 h-auto flex-col"
          >
            <CalendarIcon className="w-8 h-8 mb-2" />
            <span>Export Schedules</span>
            <span className="text-xs text-black/70 mt-1">CSV format</span>
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Analytics Dashboard
          </h1>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-terminal-500' : 'bg-red-500'}`} />
            <span className="text-sm text-dark-text-secondary">
              {isConnected ? 'Live Data' : 'Offline'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          <input
            type="date"
            className="form-input-terminal w-auto"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
          />
          <span className="text-dark-text-muted">to</span>
          <input
            type="date"
            className="form-input-terminal w-auto"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex space-x-2 overflow-x-auto">
        {[
          { key: 'dashboard', label: 'Dashboard', icon: ChartBarIcon },
          { key: 'funnel', label: 'Lead Funnel', icon: FunnelIcon },
          { key: 'roi', label: 'ROI Analysis', icon: CurrencyDollarIcon },
          { key: 'export', label: 'Export Center', icon: DocumentArrowDownIcon },
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setViewMode(key as ViewMode)}
            className={`btn whitespace-nowrap ${
              viewMode === key ? 'btn-terminal-solid' : 'btn-secondary'
            }`}
          >
            <Icon className="w-4 h-4 mr-2" />
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {viewMode === 'dashboard' && renderDashboard()}
      {viewMode === 'funnel' && renderFunnelView()}
      {viewMode === 'roi' && renderROIView()}
      {viewMode === 'export' && renderExportCenter()}
    </div>
  )
}