import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MapPinIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  PaperAirplaneIcon,
  CheckCircleIcon,
  XMarkIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline'

interface OnboardingStep {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  link: string
  linkText: string
  completed: boolean
}

interface OnboardingFlowProps {
  onDismiss?: () => void
}

export default function OnboardingFlow({ onDismiss }: OnboardingFlowProps) {
  const [steps, setSteps] = useState<OnboardingStep[]>([
    {
      id: 'setup-locations',
      title: 'Set Up Your Locations',
      description: 'Add the locations where you want to scrape leads from. Start with your local area.',
      icon: <MapPinIcon className="h-8 w-8" />,
      link: '/location-map',
      linkText: 'Add Locations',
      completed: false,
    },
    {
      id: 'first-scrape',
      title: 'Run Your First Scrape',
      description: 'Configure and launch your first scraping job to start collecting leads.',
      icon: <MagnifyingGlassIcon className="h-8 w-8" />,
      link: '/scraper',
      linkText: 'Start Scraping',
      completed: false,
    },
    {
      id: 'create-template',
      title: 'Create an Email Template',
      description: 'Build reusable email templates to engage with your leads efficiently.',
      icon: <DocumentTextIcon className="h-8 w-8" />,
      link: '/templates',
      linkText: 'Create Template',
      completed: false,
    },
    {
      id: 'send-campaign',
      title: 'Send Your First Campaign',
      description: 'Select leads and send your first email campaign to start generating responses.',
      icon: <PaperAirplaneIcon className="h-8 w-8" />,
      link: '/campaigns/new',
      linkText: 'Create Campaign',
      completed: false,
    },
  ])

  const [currentStep, setCurrentStep] = useState(0)
  const [dismissed, setDismissed] = useState(false)

  const handleStepComplete = (stepId: string) => {
    setSteps(prev =>
      prev.map(step =>
        step.id === stepId ? { ...step, completed: true } : step
      )
    )
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    if (onDismiss) {
      onDismiss()
    }
  }

  const completedSteps = steps.filter(s => s.completed).length
  const progress = (completedSteps / steps.length) * 100

  if (dismissed) {
    return null
  }

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-dark-text-primary">Welcome to FlipTech Pro!</h2>
          <p className="text-sm text-dark-text-secondary mt-1">
            Let's get you started with your lead generation journey
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className="text-dark-text-muted hover:text-dark-text-primary transition-colors"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-dark-text-primary">
            Progress
          </span>
          <span className="text-sm font-medium text-terminal-400">
            {completedSteps} / {steps.length} completed
          </span>
        </div>
        <div className="w-full bg-dark-border rounded-full h-3">
          <div
            className="bg-terminal-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`border rounded-lg p-4 transition-all ${
              index === currentStep
                ? 'border-terminal-500 bg-terminal-500/5'
                : step.completed
                ? 'border-green-500/20 bg-green-500/5'
                : 'border-dark-border bg-dark-surface/50'
            }`}
          >
            <div className="flex items-start space-x-4">
              <div
                className={`flex-shrink-0 p-3 rounded-lg ${
                  step.completed
                    ? 'bg-green-500/10 text-green-400'
                    : index === currentStep
                    ? 'bg-terminal-500/10 text-terminal-400'
                    : 'bg-dark-border text-dark-text-muted'
                }`}
              >
                {step.completed ? (
                  <CheckCircleIcon className="h-8 w-8" />
                ) : (
                  step.icon
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h3 className="text-base font-semibold text-dark-text-primary">
                        {index + 1}. {step.title}
                      </h3>
                      {step.completed && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                          Done
                        </span>
                      )}
                      {index === currentStep && !step.completed && (
                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-terminal-500/10 text-terminal-400 border border-terminal-500/20">
                          Current
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-dark-text-secondary mb-3">
                      {step.description}
                    </p>

                    {!step.completed && (
                      <div className="flex items-center space-x-3">
                        <Link
                          to={step.link}
                          className="inline-flex items-center px-4 py-2 bg-terminal-500 text-white text-sm font-medium rounded-md hover:bg-terminal-600 transition-colors"
                        >
                          {step.linkText}
                          <ChevronRightIcon className="h-4 w-4 ml-1" />
                        </Link>
                        <button
                          onClick={() => handleStepComplete(step.id)}
                          className="text-sm text-dark-text-secondary hover:text-dark-text-primary transition-colors"
                        >
                          Mark as complete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Completion Message */}
      {completedSteps === steps.length && (
        <div className="mt-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-start space-x-3">
            <CheckCircleIcon className="h-6 w-6 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-semibold text-green-400 mb-1">
                Congratulations! You're all set up!
              </h4>
              <p className="text-sm text-dark-text-secondary mb-3">
                You've completed the onboarding process. Start managing your leads and campaigns from the dashboard.
              </p>
              <button
                onClick={handleDismiss}
                className="text-sm font-medium text-green-400 hover:text-green-300 transition-colors"
              >
                Got it, let's go! →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help Links */}
      <div className="mt-6 pt-6 border-t border-dark-border">
        <h4 className="text-sm font-medium text-dark-text-primary mb-3">Need Help?</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <a
            href="#"
            className="text-sm text-terminal-400 hover:text-terminal-300 transition-colors"
          >
            📚 View Documentation
          </a>
          <a
            href="#"
            className="text-sm text-terminal-400 hover:text-terminal-300 transition-colors"
          >
            🎥 Watch Tutorial Videos
          </a>
          <a
            href="#"
            className="text-sm text-terminal-400 hover:text-terminal-300 transition-colors"
          >
            💬 Join Community Forum
          </a>
          <a
            href="#"
            className="text-sm text-terminal-400 hover:text-terminal-300 transition-colors"
          >
            📧 Contact Support
          </a>
        </div>
      </div>
    </div>
  )
}
