import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline'
import { TaskType, mockModelConfigs } from '@/mocks/models.mock'
import TaskTypeSelector from '@/components/TaskTypeSelector'

type Step = 1 | 2 | 3

interface TestConfig {
  name: string
  description: string
  taskType: TaskType | null
  selectedModels: string[]
  trafficSplit: Record<string, number>
  duration: number // in days
  successMetric: 'quality' | 'cost' | 'quality_per_dollar'
}

/**
 * AI-GYM A/B Test Creator - 3-step wizard
 * Route: /ai-gym/ab-tests/new
 */
export default function AIGymABTestNew() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<Step>(1)
  const [config, setConfig] = useState<TestConfig>({
    name: '',
    description: '',
    taskType: null,
    selectedModels: [],
    trafficSplit: {},
    duration: 7,
    successMetric: 'quality',
  })

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep((currentStep + 1) as Step)
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as Step)
    }
  }

  const handleToggleModel = (modelId: string) => {
    if (config.selectedModels.includes(modelId)) {
      const newModels = config.selectedModels.filter(id => id !== modelId)
      setConfig({
        ...config,
        selectedModels: newModels,
        trafficSplit: distributeTraffic(newModels),
      })
    } else if (config.selectedModels.length < 4) {
      const newModels = [...config.selectedModels, modelId]
      setConfig({
        ...config,
        selectedModels: newModels,
        trafficSplit: distributeTraffic(newModels),
      })
    }
  }

  const distributeTraffic = (models: string[]): Record<string, number> => {
    if (models.length === 0) return {}
    const split = Math.floor(100 / models.length)
    const remainder = 100 - split * models.length
    const trafficSplit: Record<string, number> = {}

    models.forEach((modelId, idx) => {
      trafficSplit[modelId] = split + (idx === 0 ? remainder : 0)
    })

    return trafficSplit
  }

  const updateTrafficSplit = (modelId: string, value: number) => {
    const newSplit = { ...config.trafficSplit, [modelId]: value }
    const total = Object.values(newSplit).reduce((sum, v) => sum + v, 0)

    if (total <= 100) {
      setConfig({ ...config, trafficSplit: newSplit })
    }
  }

  const handleCreate = () => {
    // In real app, this would call API to create the test
    console.log('Creating A/B test:', config)
    navigate('/ai-gym/ab-tests')
  }

  const canProceedStep1 = config.taskType !== null
  const canProceedStep2 = config.selectedModels.length >= 2
  const canCreate =
    config.name.trim() !== '' &&
    Object.values(config.trafficSplit).reduce((sum, v) => sum + v, 0) === 100

  const steps = [
    { number: 1, title: 'Select Task Type', completed: currentStep > 1 },
    { number: 2, title: 'Choose Models', completed: currentStep > 2 },
    { number: 3, title: 'Configure Test', completed: false },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/ai-gym/ab-tests"
          className="inline-flex items-center gap-2 text-dark-text-muted hover:text-terminal-400 mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to A/B Tests
        </Link>
        <h1 className="text-3xl font-bold text-dark-text-primary">Create A/B Test</h1>
        <p className="text-dark-text-muted mt-1">
          Compare AI models to find the best performer for your task
        </p>
      </div>

      {/* Step Indicator */}
      <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
        <div className="flex items-center justify-between">
          {steps.map((step, idx) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step.completed
                      ? 'bg-emerald-500 text-white'
                      : currentStep === step.number
                      ? 'bg-terminal-500 text-white'
                      : 'bg-dark-border text-dark-text-muted'
                  }`}
                >
                  {step.completed ? <CheckCircleIcon className="w-6 h-6" /> : step.number}
                </div>
                <div>
                  <div
                    className={`font-medium ${
                      currentStep === step.number ? 'text-terminal-400' : 'text-dark-text-primary'
                    }`}
                  >
                    {step.title}
                  </div>
                  <div className="text-xs text-dark-text-muted">Step {step.number} of 3</div>
                </div>
              </div>
              {idx < steps.length - 1 && (
                <div className="flex-1 h-0.5 bg-dark-border mx-4" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step 1: Task Type Selection */}
      {currentStep === 1 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-2">
            Step 1: Select Task Type
          </h2>
          <p className="text-sm text-dark-text-muted mb-6">
            Choose the type of task you want to optimize for
          </p>
          <TaskTypeSelector
            selected={config.taskType || 'all'}
            onChange={(taskType) =>
              setConfig({ ...config, taskType: taskType === 'all' ? null : taskType })
            }
          />
        </div>
      )}

      {/* Step 2: Model Selection */}
      {currentStep === 2 && (
        <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-2">
            Step 2: Choose Models to Test
          </h2>
          <p className="text-sm text-dark-text-muted mb-2">
            Select 2-4 models to compare (currently {config.selectedModels.length} selected)
          </p>
          {config.selectedModels.length >= 4 && (
            <p className="text-sm text-yellow-400 mb-6">Maximum 4 models reached</p>
          )}
          {config.selectedModels.length < 2 && (
            <p className="text-sm text-red-400 mb-6">Select at least 2 models to continue</p>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
            {mockModelConfigs.map((model) => {
              const isSelected = config.selectedModels.includes(model.model_id)
              const isDisabled = !isSelected && config.selectedModels.length >= 4

              return (
                <button
                  key={model.model_id}
                  onClick={() => !isDisabled && handleToggleModel(model.model_id)}
                  disabled={isDisabled}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    isSelected
                      ? 'border-terminal-500 bg-terminal-500/10'
                      : isDisabled
                      ? 'border-dark-border bg-dark-bg/50 opacity-50 cursor-not-allowed'
                      : 'border-dark-border bg-dark-bg hover:border-terminal-500/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-dark-text-primary">
                      {model.display_name}
                    </div>
                    {isSelected && <CheckCircleIcon className="w-5 h-5 text-terminal-400" />}
                  </div>
                  <div className="text-sm text-dark-text-muted mb-2 capitalize">
                    {model.provider}
                  </div>
                  <div className="space-y-1 text-xs text-dark-text-muted">
                    <div>Context: {(model.context_window / 1000).toLocaleString()}K</div>
                    <div>
                      Input: ${model.cost_per_1k_input_tokens.toFixed(4)}/1K • Output: $
                      {model.cost_per_1k_output_tokens.toFixed(4)}/1K
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Step 3: Configuration */}
      {currentStep === 3 && (
        <div className="space-y-6">
          {/* Test Details */}
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
              Test Details
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Test Name *
                </label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                  placeholder="e.g., Email Generation: Claude vs GPT-4o"
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:border-terminal-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Description
                </label>
                <textarea
                  value={config.description}
                  onChange={(e) => setConfig({ ...config, description: e.target.value })}
                  placeholder="Describe what you're testing and why..."
                  rows={3}
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary placeholder-dark-text-muted focus:outline-none focus:border-terminal-500 resize-none"
                />
              </div>
            </div>
          </div>

          {/* Traffic Split */}
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-dark-text-primary mb-2">
              Traffic Split
            </h2>
            <p className="text-sm text-dark-text-muted mb-4">
              Configure how requests are distributed across models (must total 100%)
            </p>
            <div className="space-y-4">
              {config.selectedModels.map((modelId, idx) => {
                const model = mockModelConfigs.find((m) => m.model_id === modelId)
                const split = config.trafficSplit[modelId] || 0
                const colors = ['bg-blue-500', 'bg-emerald-500', 'bg-yellow-500', 'bg-purple-500']

                return (
                  <div key={modelId}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-dark-text-primary">
                        {model?.display_name || modelId}
                      </span>
                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={split}
                          onChange={(e) =>
                            updateTrafficSplit(modelId, parseInt(e.target.value) || 0)
                          }
                          className="w-20 px-3 py-1 bg-dark-bg border border-dark-border rounded text-dark-text-primary text-sm focus:outline-none focus:border-terminal-500"
                        />
                        <span className="text-sm text-dark-text-muted">%</span>
                      </div>
                    </div>
                    <div className="w-full bg-dark-border rounded-full h-2">
                      <div
                        className={`${colors[idx % colors.length]} h-2 rounded-full transition-all`}
                        style={{ width: `${split}%` }}
                      />
                    </div>
                  </div>
                )
              })}
              <div className="pt-4 border-t border-dark-border">
                <div className="flex justify-between text-sm">
                  <span className="text-dark-text-muted">Total</span>
                  <span
                    className={`font-medium ${
                      Object.values(config.trafficSplit).reduce((sum, v) => sum + v, 0) === 100
                        ? 'text-emerald-400'
                        : 'text-red-400'
                    }`}
                  >
                    {Object.values(config.trafficSplit).reduce((sum, v) => sum + v, 0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Test Configuration */}
          <div className="bg-dark-surface border border-dark-border rounded-lg p-6">
            <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
              Test Configuration
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Duration (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={config.duration}
                  onChange={(e) =>
                    setConfig({ ...config, duration: parseInt(e.target.value) || 7 })
                  }
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary focus:outline-none focus:border-terminal-500"
                />
                <p className="text-xs text-dark-text-muted mt-1">
                  How long the test should run
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Success Metric
                </label>
                <select
                  value={config.successMetric}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      successMetric: e.target.value as 'quality' | 'cost' | 'quality_per_dollar',
                    })
                  }
                  className="w-full px-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary focus:outline-none focus:border-terminal-500"
                >
                  <option value="quality">Highest Quality Score</option>
                  <option value="cost">Lowest Cost</option>
                  <option value="quality_per_dollar">Best Cost Efficiency (Quality/$)</option>
                </select>
                <p className="text-xs text-dark-text-muted mt-1">
                  How to determine the winner
                </p>
              </div>
            </div>
          </div>

          {/* Test Summary */}
          <div className="bg-terminal-500/10 border border-terminal-500/30 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-terminal-400 mb-4">Test Summary</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-dark-text-muted">Task Type:</span>
                <span className="text-dark-text-primary ml-2 capitalize">
                  {config.taskType?.replace('_', ' ') || 'Not selected'}
                </span>
              </div>
              <div>
                <span className="text-dark-text-muted">Models:</span>
                <span className="text-dark-text-primary ml-2">
                  {config.selectedModels.length}
                </span>
              </div>
              <div>
                <span className="text-dark-text-muted">Duration:</span>
                <span className="text-dark-text-primary ml-2">{config.duration} days</span>
              </div>
              <div>
                <span className="text-dark-text-muted">Success Metric:</span>
                <span className="text-dark-text-primary ml-2 capitalize">
                  {config.successMetric.replace('_', ' ')}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-dark-border">
        <button
          onClick={handleBack}
          disabled={currentStep === 1}
          className="inline-flex items-center gap-2 px-6 py-3 bg-dark-border text-dark-text-primary rounded-lg hover:bg-dark-border/70 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          Back
        </button>

        <div className="flex gap-3">
          <Link
            to="/ai-gym/ab-tests"
            className="px-6 py-3 text-dark-text-muted hover:text-dark-text-primary transition-colors"
          >
            Cancel
          </Link>
          {currentStep < 3 ? (
            <button
              onClick={handleNext}
              disabled={
                (currentStep === 1 && !canProceedStep1) ||
                (currentStep === 2 && !canProceedStep2)
              }
              className="inline-flex items-center gap-2 px-6 py-3 bg-terminal-500 text-white rounded-lg hover:bg-terminal-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={!canCreate}
              className="inline-flex items-center gap-2 px-6 py-3 bg-terminal-500 text-white rounded-lg hover:bg-terminal-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <BeakerIcon className="w-5 h-5" />
              Create Test
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
