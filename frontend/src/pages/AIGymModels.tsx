import { useState, useMemo } from 'react'
import { CheckIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/solid'
import {
  mockModelConfigs,
  mockModelPerformance,
  TaskType,
  ModelConfig,
  ModelPerformance,
} from '@/mocks/models.mock'
import ModelCard from '@/components/ModelCard'
import TaskTypeSelector from '@/components/TaskTypeSelector'
import CostEfficiencyChart from '@/components/CostEfficiencyChart'
import PerformanceChart from '@/components/PerformanceChart'

/**
 * AI-GYM Models - Model Comparison View
 * Route: /ai-gym/models
 */
export default function AIGymModels() {
  const [selectedTaskType, setSelectedTaskType] = useState<TaskType | 'all'>('email_generation')
  const [selectedModels, setSelectedModels] = useState<string[]>([
    'claude-sonnet-4.5',
    'gpt-4o',
  ])
  const [showModelSelector, setShowModelSelector] = useState(false)

  // Get performance data for selected task type
  const taskPerformance = useMemo(() => {
    if (selectedTaskType === 'all') return mockModelPerformance
    return mockModelPerformance.filter(p => p.task_type === selectedTaskType)
  }, [selectedTaskType])

  // Get selected models with their performance
  const selectedModelsData = useMemo(() => {
    return selectedModels.map(modelId => {
      const config = mockModelConfigs.find(c => c.model_id === modelId)
      const performance = taskPerformance.find(p => p.model_id === modelId)
      return { config, performance }
    }).filter(m => m.config) as { config: ModelConfig; performance?: ModelPerformance }[]
  }, [selectedModels, taskPerformance])

  // Performance comparison data
  const comparisonMetrics = useMemo(() => {
    if (selectedModelsData.length === 0) return null

    const metrics = ['Quality Score', 'Response Time (ms)', 'Cost per Request', 'Error Rate']
    return metrics.map(metric => {
      const row: any = { metric }
      selectedModelsData.forEach(({ config, performance }) => {
        if (!performance) {
          row[config.model_id] = 'N/A'
          return
        }

        switch (metric) {
          case 'Quality Score':
            row[config.model_id] = performance.avg_quality_score.toFixed(1)
            break
          case 'Response Time (ms)':
            row[config.model_id] = performance.avg_response_time_ms.toLocaleString()
            break
          case 'Cost per Request':
            row[config.model_id] = `$${performance.avg_cost_per_request.toFixed(3)}`
            break
          case 'Error Rate':
            row[config.model_id] = `${performance.error_rate.toFixed(2)}%`
            break
        }
      })
      return row
    })
  }, [selectedModelsData])

  // Cost efficiency data for chart
  const costEfficiencyData = useMemo(() => {
    return selectedModelsData
      .filter(m => m.performance)
      .map(({ config, performance }) => ({
        model: config.display_name,
        qualityPerDollar: performance!.avg_quality_score / performance!.avg_cost_per_request,
        quality: performance!.avg_quality_score,
        cost: performance!.avg_cost_per_request,
      }))
  }, [selectedModelsData])

  // Mock quality over time data for selected models
  const qualityOverTime = [
    { date: 'Jan 1', ...Object.fromEntries(selectedModelsData.map(m => [m.config.model_id, 8.0 + Math.random()])) },
    { date: 'Jan 2', ...Object.fromEntries(selectedModelsData.map(m => [m.config.model_id, 8.2 + Math.random()])) },
    { date: 'Jan 3', ...Object.fromEntries(selectedModelsData.map(m => [m.config.model_id, 8.4 + Math.random()])) },
    { date: 'Jan 4', ...Object.fromEntries(selectedModelsData.map(m => [m.config.model_id, 8.6 + Math.random()])) },
    { date: 'Jan 5', ...Object.fromEntries(selectedModelsData.map(m => [m.config.model_id, 8.8 + Math.random()])) },
  ]

  const chartLines = selectedModelsData.map((m, idx) => ({
    dataKey: m.config.model_id,
    name: m.config.display_name,
    color: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'][idx],
  }))

  const handleToggleModel = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      setSelectedModels(selectedModels.filter(id => id !== modelId))
    } else {
      setSelectedModels([...selectedModels, modelId])
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">Model Comparison</h1>
          <p className="text-dark-text-muted mt-1">
            Compare AI models side-by-side across performance metrics
          </p>
        </div>
        <button
          onClick={() => setShowModelSelector(!showModelSelector)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-terminal-500 text-white rounded-lg hover:bg-terminal-600 transition-colors font-medium"
        >
          <PlusIcon className="w-5 h-5" />
          {showModelSelector ? 'Done' : 'Add Models'}
        </button>
      </div>

      {/* Model Selector */}
      {showModelSelector && (
        <div className="bg-dark-surface border-2 border-terminal-500 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            Select Models to Compare
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockModelConfigs.map(config => {
              const isSelected = selectedModels.includes(config.model_id)
              return (
                <button
                  key={config.model_id}
                  onClick={() => handleToggleModel(config.model_id)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    isSelected
                      ? 'border-terminal-500 bg-terminal-500/10'
                      : 'border-dark-border bg-dark-bg hover:border-terminal-500/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-dark-text-primary">
                      {config.display_name}
                    </div>
                    {isSelected && (
                      <CheckIcon className="w-5 h-5 text-terminal-400" />
                    )}
                  </div>
                  <div className="text-sm text-dark-text-muted">
                    {config.provider} • {(config.context_window / 1000).toLocaleString()}K context
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Task Type Filter */}
      <div>
        <h2 className="text-xl font-semibold text-dark-text-primary mb-4">Filter by Task Type</h2>
        <TaskTypeSelector selected={selectedTaskType} onChange={setSelectedTaskType} />
      </div>

      {/* Selected Models Cards */}
      {selectedModelsData.length > 0 ? (
        <>
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-dark-text-primary">
                Selected Models ({selectedModelsData.length})
              </h2>
              {selectedModelsData.length > 1 && (
                <span className="text-sm text-dark-text-muted">
                  {selectedTaskType === 'all' ? 'All tasks' : `Task: ${selectedTaskType.replace('_', ' ')}`}
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {selectedModelsData.map(({ config, performance }) => (
                <div key={config.model_id} className="relative">
                  <button
                    onClick={() => handleToggleModel(config.model_id)}
                    className="absolute -top-2 -right-2 z-10 p-1 bg-red-500 rounded-full text-white hover:bg-red-600 transition-colors"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                  <ModelCard config={config} performance={performance} selected />
                </div>
              ))}
            </div>
          </div>

          {/* Performance Charts */}
          {selectedModelsData.some(m => m.performance) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PerformanceChart
                data={qualityOverTime}
                lines={chartLines}
                title="Quality Score Over Time"
                yAxisLabel="Quality Score"
              />
              {costEfficiencyData.length > 0 && (
                <CostEfficiencyChart data={costEfficiencyData} />
              )}
            </div>
          )}

          {/* Comparison Table */}
          {comparisonMetrics && selectedModelsData.some(m => m.performance) && (
            <div className="bg-dark-surface border border-dark-border rounded-lg">
              <div className="p-6 border-b border-dark-border">
                <h2 className="text-xl font-semibold text-dark-text-primary">
                  Performance Comparison
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-dark-bg/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                        Metric
                      </th>
                      {selectedModelsData.map(({ config }) => (
                        <th
                          key={config.model_id}
                          className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider"
                        >
                          {config.display_name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-border">
                    {comparisonMetrics.map((row, idx) => (
                      <tr key={idx} className="hover:bg-dark-bg/30">
                        <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                          {row.metric}
                        </td>
                        {selectedModelsData.map(({ config }) => {
                          const value = row[config.model_id]
                          let colorClass = 'text-dark-text-secondary'

                          // Highlight best values
                          if (row.metric === 'Quality Score') {
                            const numValue = parseFloat(value)
                            if (numValue >= 9) colorClass = 'text-emerald-400 font-semibold'
                            else if (numValue >= 8.5) colorClass = 'text-blue-400 font-semibold'
                          } else if (row.metric === 'Cost per Request') {
                            const numValue = parseFloat(value.replace('$', ''))
                            if (numValue <= 0.01) colorClass = 'text-emerald-400 font-semibold'
                          }

                          return (
                            <td
                              key={config.model_id}
                              className={`px-6 py-4 whitespace-nowrap ${colorClass}`}
                            >
                              {value}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Model Specifications */}
          <div className="bg-dark-surface border border-dark-border rounded-lg">
            <div className="p-6 border-b border-dark-border">
              <h2 className="text-xl font-semibold text-dark-text-primary">
                Model Specifications
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-dark-bg/50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider">
                      Specification
                    </th>
                    {selectedModelsData.map(({ config }) => (
                      <th
                        key={config.model_id}
                        className="px-6 py-3 text-left text-xs font-medium text-dark-text-muted uppercase tracking-wider"
                      >
                        {config.display_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Provider
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap text-dark-text-secondary capitalize">
                        {config.provider}
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Context Window
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                        {(config.context_window / 1000).toLocaleString()}K tokens
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Input Cost (per 1K)
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                        ${config.cost_per_1k_input_tokens.toFixed(4)}
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Output Cost (per 1K)
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                        ${config.cost_per_1k_output_tokens.toFixed(4)}
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Max Output Tokens
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap text-dark-text-secondary">
                        {config.max_output_tokens.toLocaleString()}
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Streaming Support
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap">
                        {config.supports_streaming ? (
                          <span className="text-emerald-400">✓ Yes</span>
                        ) : (
                          <span className="text-red-400">✗ No</span>
                        )}
                      </td>
                    ))}
                  </tr>
                  <tr className="hover:bg-dark-bg/30">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-dark-text-primary">
                      Function Calling
                    </td>
                    {selectedModelsData.map(({ config }) => (
                      <td key={config.model_id} className="px-6 py-4 whitespace-nowrap">
                        {config.supports_function_calling ? (
                          <span className="text-emerald-400">✓ Yes</span>
                        ) : (
                          <span className="text-red-400">✗ No</span>
                        )}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-12 text-center">
          <PlusIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-4" />
          <p className="text-dark-text-muted mb-4">No models selected for comparison</p>
          <button
            onClick={() => setShowModelSelector(true)}
            className="text-terminal-400 hover:text-terminal-300"
          >
            Select models to compare →
          </button>
        </div>
      )}
    </div>
  )
}
