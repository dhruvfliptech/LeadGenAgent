// Multi-step wizard for creating demo videos - Journey 3

import { useState, useEffect } from 'react'
import { Dialog } from '@headlessui/react'
import { XMarkIcon, CheckIcon, ArrowRightIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import { mockDemoSites, getDemoSitesByStatus } from '@/mocks/demoSites.mock'
import { VoiceProvider, VoiceGender } from '@/mocks/videos.mock'
import toast from 'react-hot-toast'

interface CreateVideoWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

interface WizardStep {
  id: number
  name: string
  description: string
}

const WIZARD_STEPS: WizardStep[] = [
  {
    id: 1,
    name: 'Select Demo',
    description: 'Choose a demo site'
  },
  {
    id: 2,
    name: 'Configure',
    description: 'Voice and settings'
  },
  {
    id: 3,
    name: 'Review',
    description: 'Review and start'
  }
]

interface VideoConfig {
  duration: number // in seconds
  voiceProvider: VoiceProvider
  voiceGender: VoiceGender
  style: 'professional' | 'casual' | 'technical' | 'sales'
}

const DEFAULT_CONFIG: VideoConfig = {
  duration: 30,
  voiceProvider: 'elevenlabs',
  voiceGender: 'male',
  style: 'professional'
}

export default function CreateVideoWizard({
  isOpen,
  onClose,
  onSuccess
}: CreateVideoWizardProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedDemoSiteId, setSelectedDemoSiteId] = useState<number | null>(null)
  const [config, setConfig] = useState<VideoConfig>(DEFAULT_CONFIG)
  const [isRendering, setIsRendering] = useState(false)
  const [renderStage, setRenderStage] = useState('')
  const [renderProgress, setRenderProgress] = useState(0)

  // Get completed demo sites
  const completedDemoSites = getDemoSitesByStatus('completed')
  const selectedDemoSite = completedDemoSites.find(d => d.id === selectedDemoSiteId)

  useEffect(() => {
    if (!isOpen) {
      // Reset state when closed
      setCurrentStep(1)
      setSelectedDemoSiteId(null)
      setConfig(DEFAULT_CONFIG)
      setIsRendering(false)
      setRenderStage('')
      setRenderProgress(0)
    }
  }, [isOpen])

  const handleClose = () => {
    if (!isRendering) {
      onClose()
    }
  }

  const handleNext = () => {
    if (currentStep === 1 && !selectedDemoSiteId) {
      toast.error('Please select a demo site')
      return
    }

    if (currentStep === 3) {
      // Start rendering
      handleStartRendering()
      return
    }

    setCurrentStep(prev => Math.min(prev + 1, WIZARD_STEPS.length))
  }

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1))
  }

  const handleStartRendering = () => {
    setIsRendering(true)

    // Simulate video rendering stages
    const stages = [
      { name: 'Script Generation', duration: 2000, progress: 20 },
      { name: 'Voiceover', duration: 3000, progress: 40 },
      { name: 'Screen Recording', duration: 4000, progress: 70 },
      { name: 'Composing', duration: 3000, progress: 90 },
      { name: 'Publishing', duration: 2000, progress: 100 }
    ]

    let currentStageIndex = 0

    const runNextStage = () => {
      if (currentStageIndex >= stages.length) {
        // Rendering complete
        setTimeout(() => {
          onSuccess()
          toast.success('Video generated successfully!')
        }, 500)
        return
      }

      const stage = stages[currentStageIndex]
      setRenderStage(stage.name)
      setRenderProgress(stage.progress)

      currentStageIndex++
      setTimeout(runNextStage, stage.duration)
    }

    runNextStage()
  }

  const renderStepContent = () => {
    if (isRendering) {
      return (
        <div className="py-8">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-6 text-center">
            Rendering Video
          </h3>
          <div className="flex flex-col items-center justify-center">
            {/* Circular progress */}
            <div className="relative w-32 h-32 mb-6">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="60"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  className="text-dark-border"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="60"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 60}`}
                  strokeDashoffset={`${2 * Math.PI * 60 * (1 - renderProgress / 100)}`}
                  className="text-terminal-500 transition-all duration-500"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-terminal-400">
                  {renderProgress}%
                </span>
              </div>
            </div>

            {/* Stage indicator */}
            <div className="space-y-4 w-full max-w-md">
              {['Script Generation', 'Voiceover', 'Screen Recording', 'Composing', 'Publishing'].map((stage, index) => {
                const stageProgress = [20, 40, 70, 90, 100][index]
                const isActive = renderStage === stage
                const isComplete = renderProgress > stageProgress

                return (
                  <div key={stage} className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isComplete ? 'bg-green-500' : isActive ? 'bg-terminal-500 animate-pulse' : 'bg-dark-border'
                    }`}>
                      {isComplete ? (
                        <CheckIcon className="w-5 h-5 text-white" />
                      ) : (
                        <span className="text-sm font-medium text-white">{index + 1}</span>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className={`text-sm font-medium ${
                        isActive ? 'text-terminal-400' : isComplete ? 'text-green-400' : 'text-dark-text-muted'
                      }`}>
                        {stage}
                      </p>
                    </div>
                    {isActive && (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-terminal-500" />
                    )}
                  </div>
                )
              })}
            </div>

            <p className="mt-6 text-sm text-dark-text-secondary">
              Estimated time remaining: {Math.ceil((100 - renderProgress) / 10)} seconds
            </p>
          </div>
        </div>
      )
    }

    switch (currentStep) {
      case 1:
        return (
          <div>
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Select Demo Site
            </h3>
            {completedDemoSites.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {completedDemoSites.map((demo) => (
                  <button
                    key={demo.id}
                    onClick={() => setSelectedDemoSiteId(demo.id)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                      selectedDemoSiteId === demo.id
                        ? 'border-terminal-500 bg-terminal-500/10'
                        : 'border-dark-border hover:border-terminal-600 bg-dark-surface'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-dark-text-primary">
                          {demo.lead_title}
                        </h4>
                        <p className="text-sm text-dark-text-secondary mt-1">
                          {demo.preview_url || demo.original_url}
                        </p>
                        <div className="flex items-center gap-3 mt-2 text-xs text-dark-text-muted">
                          <span className="capitalize">{demo.framework}</span>
                          <span>•</span>
                          <span>{demo.view_count || 0} views</span>
                          <span>•</span>
                          <span>{new Date(demo.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      {selectedDemoSiteId === demo.id && (
                        <CheckIcon className="w-6 h-6 text-terminal-400 flex-shrink-0" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-dark-text-secondary">
                  No completed demo sites available. Generate a demo site first.
                </p>
              </div>
            )}
          </div>
        )

      case 2:
        return (
          <div>
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Configure Video
            </h3>
            <div className="space-y-6">
              {/* Duration */}
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Duration
                </label>
                <select
                  value={config.duration}
                  onChange={(e) => setConfig({ ...config, duration: parseInt(e.target.value) })}
                  className="form-input w-full"
                >
                  <option value={15}>15 seconds - Quick demo</option>
                  <option value={30}>30 seconds - Standard</option>
                  <option value={60}>60 seconds - Detailed</option>
                  <option value={90}>90 seconds - Comprehensive</option>
                </select>
              </div>

              {/* Voice Provider */}
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Voice Provider
                </label>
                <select
                  value={config.voiceProvider}
                  onChange={(e) => setConfig({ ...config, voiceProvider: e.target.value as VoiceProvider })}
                  className="form-input w-full"
                >
                  <option value="elevenlabs">ElevenLabs - Premium Quality</option>
                  <option value="openai">OpenAI - Natural Sound</option>
                  <option value="google">Google - Fast Generation</option>
                </select>
              </div>

              {/* Voice Gender */}
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Voice Gender
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['male', 'female', 'neutral'] as VoiceGender[]).map(gender => (
                    <button
                      key={gender}
                      onClick={() => setConfig({ ...config, voiceGender: gender })}
                      className={`p-3 rounded-lg border-2 transition-all capitalize ${
                        config.voiceGender === gender
                          ? 'border-terminal-500 bg-terminal-500/10 text-terminal-400'
                          : 'border-dark-border hover:border-terminal-600 text-dark-text-primary'
                      }`}
                    >
                      {gender}
                    </button>
                  ))}
                </div>
              </div>

              {/* Style */}
              <div>
                <label className="block text-sm font-medium text-dark-text-primary mb-2">
                  Style
                </label>
                <select
                  value={config.style}
                  onChange={(e) => setConfig({ ...config, style: e.target.value as VideoConfig['style'] })}
                  className="form-input w-full"
                >
                  <option value="professional">Professional - Business tone</option>
                  <option value="casual">Casual - Friendly approach</option>
                  <option value="technical">Technical - Detailed explanations</option>
                  <option value="sales">Sales - Conversion focused</option>
                </select>
              </div>
            </div>
          </div>
        )

      case 3:
        return (
          <div>
            <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
              Review & Generate
            </h3>
            <div className="space-y-4">
              {/* Demo Site */}
              <div className="card p-4 bg-dark-surface">
                <h4 className="text-sm font-medium text-dark-text-secondary mb-2">Demo Site</h4>
                <p className="text-dark-text-primary font-semibold">{selectedDemoSite?.lead_title}</p>
                <p className="text-sm text-dark-text-muted mt-1">{selectedDemoSite?.preview_url}</p>
              </div>

              {/* Configuration */}
              <div className="card p-4 bg-dark-surface">
                <h4 className="text-sm font-medium text-dark-text-secondary mb-3">Configuration</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">Duration:</span>
                    <span className="text-dark-text-primary font-medium">{config.duration} seconds</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">Voice Provider:</span>
                    <span className="text-dark-text-primary font-medium capitalize">{config.voiceProvider}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">Voice Gender:</span>
                    <span className="text-dark-text-primary font-medium capitalize">{config.voiceGender}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-text-muted">Style:</span>
                    <span className="text-dark-text-primary font-medium capitalize">{config.style}</span>
                  </div>
                </div>
              </div>

              {/* Cost Estimate */}
              <div className="card p-4 bg-dark-surface border border-terminal-500/30">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-dark-text-secondary">Estimated Cost</h4>
                    <p className="text-xs text-dark-text-muted mt-1">
                      Voice generation + rendering
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-terminal-400 font-mono">$0.35</p>
                    <p className="text-xs text-dark-text-muted">~{Math.ceil(config.duration / 5)} minutes</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
    }
  }

  return (
    <Dialog open={isOpen} onClose={handleClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-3xl w-full bg-dark-surface rounded-xl shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dark-border">
            <div>
              <Dialog.Title className="text-xl font-bold text-dark-text-primary">
                Create Demo Video
              </Dialog.Title>
              <p className="text-sm text-dark-text-secondary mt-1">
                {isRendering ? 'Generating your video...' : `Step ${currentStep} of ${WIZARD_STEPS.length}: ${WIZARD_STEPS[currentStep - 1].name}`}
              </p>
            </div>
            {!isRendering && (
              <button
                onClick={handleClose}
                className="text-dark-text-secondary hover:text-dark-text-primary"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            )}
          </div>

          {/* Progress Steps */}
          {!isRendering && (
            <div className="px-6 pt-6">
              <div className="flex items-center justify-between">
                {WIZARD_STEPS.map((step, index) => (
                  <div key={step.id} className="flex items-center flex-1">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                          currentStep > step.id
                            ? 'bg-terminal-500 text-white'
                            : currentStep === step.id
                            ? 'bg-terminal-500 text-white ring-4 ring-terminal-500/20'
                            : 'bg-dark-border text-dark-text-muted'
                        }`}
                      >
                        {currentStep > step.id ? (
                          <CheckIcon className="w-5 h-5" />
                        ) : (
                          step.id
                        )}
                      </div>
                      <span className="text-xs text-dark-text-secondary mt-2 text-center">
                        {step.name}
                      </span>
                    </div>
                    {index < WIZARD_STEPS.length - 1 && (
                      <div
                        className={`flex-1 h-1 mx-2 rounded ${
                          currentStep > step.id ? 'bg-terminal-500' : 'bg-dark-border'
                        }`}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Content */}
          <div className="p-6">
            {renderStepContent()}
          </div>

          {/* Footer */}
          {!isRendering && (
            <div className="flex items-center justify-between p-6 border-t border-dark-border">
              <button
                onClick={handleBack}
                disabled={currentStep === 1}
                className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeftIcon className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleNext}
                disabled={currentStep === 1 && !selectedDemoSiteId}
                className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {currentStep === 3 ? 'Generate Video' : 'Next'}
                <ArrowRightIcon className="w-4 h-4" />
              </button>
            </div>
          )}
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
