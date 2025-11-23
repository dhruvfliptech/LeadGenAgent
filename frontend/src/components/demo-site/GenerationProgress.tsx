import { useEffect, useState } from 'react'
import {
  MagnifyingGlassIcon,
  LightBulbIcon,
  CodeBracketIcon,
  CheckBadgeIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline'

type GenerationStep = 'analyzing' | 'planning' | 'generating' | 'validating' | 'deploying' | 'completed'

interface GenerationProgressProps {
  currentStep: GenerationStep
  onComplete?: () => void
}

const steps = [
  {
    id: 'analyzing' as GenerationStep,
    name: 'Analyzing',
    description: 'Analyzing website structure and content',
    icon: MagnifyingGlassIcon,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/20',
    duration: 5000
  },
  {
    id: 'planning' as GenerationStep,
    name: 'Planning',
    description: 'Creating improvement strategy',
    icon: LightBulbIcon,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/20',
    duration: 3000
  },
  {
    id: 'generating' as GenerationStep,
    name: 'Generating',
    description: 'Writing optimized code',
    icon: CodeBracketIcon,
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/20',
    duration: 8000
  },
  {
    id: 'validating' as GenerationStep,
    name: 'Validating',
    description: 'Checking code quality',
    icon: CheckBadgeIcon,
    color: 'text-green-500',
    bgColor: 'bg-green-500/20',
    duration: 2000
  },
  {
    id: 'deploying' as GenerationStep,
    name: 'Deploying',
    description: 'Deploying to preview environment',
    icon: RocketLaunchIcon,
    color: 'text-terminal-500',
    bgColor: 'bg-terminal-500/20',
    duration: 4000
  }
]

export default function GenerationProgress({ currentStep, onComplete }: GenerationProgressProps) {
  const [progress, setProgress] = useState(0)
  const [timeRemaining, setTimeRemaining] = useState(0)

  const currentStepIndex = steps.findIndex(s => s.id === currentStep)
  const currentStepData = steps[currentStepIndex]

  useEffect(() => {
    // Calculate total time remaining
    const remainingSteps = steps.slice(currentStepIndex)
    const totalTime = remainingSteps.reduce((sum, step) => sum + step.duration, 0)
    setTimeRemaining(Math.ceil(totalTime / 1000))

    // Simulate progress for current step
    const stepDuration = currentStepData?.duration || 5000
    const interval = 100
    const increment = (interval / stepDuration) * 100

    const timer = setInterval(() => {
      setProgress(prev => {
        const next = Math.min(prev + increment, 100)
        if (next >= 100 && onComplete) {
          setTimeout(onComplete, 500)
        }
        return next
      })
      setTimeRemaining(prev => Math.max(prev - 0.1, 0))
    }, interval)

    return () => clearInterval(timer)
  }, [currentStep, currentStepIndex, currentStepData, onComplete])

  const isStepComplete = (stepId: GenerationStep) => {
    const stepIndex = steps.findIndex(s => s.id === stepId)
    return stepIndex < currentStepIndex
  }

  const isStepActive = (stepId: GenerationStep) => {
    return stepId === currentStep
  }

  return (
    <div className="space-y-6">
      {/* Overall Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-dark-text-primary">
            Overall Progress
          </span>
          <span className="text-sm text-dark-text-secondary">
            {((currentStepIndex / steps.length) * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-dark-border rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-terminal-500 to-terminal-400 transition-all duration-500"
            style={{ width: `${(currentStepIndex / steps.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Current Step Info */}
      {currentStepData && (
        <div className="card p-6 bg-gradient-to-r from-terminal-900/20 to-dark-border">
          <div className="flex items-center gap-4">
            <div className={`p-4 rounded-full ${currentStepData.bgColor}`}>
              <currentStepData.icon className={`w-8 h-8 ${currentStepData.color} animate-pulse`} />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-dark-text-primary mb-1">
                {currentStepData.name}
              </h3>
              <p className="text-dark-text-secondary">{currentStepData.description}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-terminal-400 mb-1">
                {Math.ceil(timeRemaining)}s
              </div>
              <div className="text-xs text-dark-text-muted">remaining</div>
            </div>
          </div>

          {/* Step Progress */}
          <div className="mt-4">
            <div className="h-1.5 bg-dark-border rounded-full overflow-hidden">
              <div
                className={`h-full ${currentStepData.color.replace('text-', 'bg-')} transition-all duration-300`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Steps Timeline */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          const Icon = step.icon
          const isComplete = isStepComplete(step.id)
          const isActive = isStepActive(step.id)

          return (
            <div
              key={step.id}
              className={`flex items-center gap-4 p-4 rounded-lg transition-all ${
                isActive
                  ? 'bg-terminal-500/10 border-2 border-terminal-500'
                  : isComplete
                  ? 'bg-green-500/10 border-2 border-green-500/30'
                  : 'bg-dark-border/30 border-2 border-transparent'
              }`}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isActive
                    ? step.bgColor + ' ' + step.color
                    : 'bg-dark-border text-dark-text-muted'
                }`}
              >
                {isComplete ? (
                  <CheckBadgeIcon className="w-6 h-6" />
                ) : (
                  <Icon className={`w-6 h-6 ${isActive ? 'animate-pulse' : ''}`} />
                )}
              </div>

              <div className="flex-1">
                <div className="font-medium text-dark-text-primary">{step.name}</div>
                <div className="text-sm text-dark-text-secondary">{step.description}</div>
              </div>

              <div className="flex-shrink-0">
                {isComplete ? (
                  <span className="text-green-500 font-medium">✓ Complete</span>
                ) : isActive ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-terminal-500" />
                    <span className="text-terminal-400 font-medium">In Progress</span>
                  </div>
                ) : (
                  <span className="text-dark-text-muted">Pending</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Tips */}
      <div className="card p-4 bg-blue-500/10 border border-blue-500/30">
        <div className="flex items-start gap-3">
          <LightBulbIcon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-dark-text-secondary">
            <strong className="text-dark-text-primary">Tip:</strong> Generation typically takes 15-30 seconds.
            You can close this window and check back later - your demo will continue building in the background.
          </div>
        </div>
      </div>
    </div>
  )
}
