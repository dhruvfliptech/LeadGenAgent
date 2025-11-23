import { useQuery } from '@tanstack/react-query'
import { SparklesIcon, CurrencyDollarIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import { aiMvpApi } from '@/services/phase3Api'

export default function AICostTracker() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['ai-gym-stats'],
    queryFn: () => aiMvpApi.getStats().then(res => res.data),
    refetchInterval: 30000, // Refresh every 30s
  })

  if (isLoading) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <SparklesIcon className="w-5 h-5 text-purple-500" />
          <h3 className="text-lg font-semibold">AI Usage & Cost</h3>
        </div>
        <div className="animate-pulse space-y-3">
          <div className="h-12 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  const requestCount = stats?.request_count || 0
  const totalCost = stats?.total_cost || 0
  const avgCost = stats?.avg_cost || 0
  const totalTokens = stats?.total_tokens || 0

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-purple-500" />
          <h3 className="text-lg font-semibold">AI Usage & Cost</h3>
        </div>
        <div className="text-xs text-gray-500">
          Real-time tracking
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <div className="flex items-center gap-2 text-purple-600 mb-1">
            <ChartBarIcon className="w-4 h-4" />
            <div className="text-xs font-medium">Total Requests</div>
          </div>
          <div className="text-2xl font-bold text-purple-900">{requestCount}</div>
          <div className="text-xs text-purple-600 mt-1">
            AI analyses + emails
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-600 mb-1">
            <CurrencyDollarIcon className="w-4 h-4" />
            <div className="text-xs font-medium">Total Cost</div>
          </div>
          <div className="text-2xl font-bold text-green-900">
            ${totalCost.toFixed(2)}
          </div>
          <div className="text-xs text-green-600 mt-1">
            All-time spend
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-600 mb-1">
            <CurrencyDollarIcon className="w-4 h-4" />
            <div className="text-xs font-medium">Avg Cost/Request</div>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            ${avgCost.toFixed(4)}
          </div>
          <div className="text-xs text-blue-600 mt-1">
            Per AI call
          </div>
        </div>

        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
          <div className="flex items-center gap-2 text-orange-600 mb-1">
            <ChartBarIcon className="w-4 h-4" />
            <div className="text-xs font-medium">Total Tokens</div>
          </div>
          <div className="text-2xl font-bold text-orange-900">
            {totalTokens.toLocaleString()}
          </div>
          <div className="text-xs text-orange-600 mt-1">
            Input + output
          </div>
        </div>
      </div>

      {requestCount > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            💡 <span className="font-medium">Cost Projection:</span> At current rate,{' '}
            <span className="font-semibold">100 leads/day</span> = ~${(avgCost * 200 * 30).toFixed(2)}/month
            {' • '}
            <span className="font-semibold">1000 leads/day</span> = ~${(avgCost * 2000 * 30).toFixed(2)}/month
          </div>
        </div>
      )}
    </div>
  )
}
