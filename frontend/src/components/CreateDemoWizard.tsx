import { useState, useEffect } from 'react'
import {
  XMarkIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  SparklesIcon,
  CodeBracketIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline'
import { demoSitesUtils } from '@/services/demoSitesApi'
import { Framework } from '@/types/demoSite'
import { mockLeads } from '@/mocks/leads.mock'
import { mockAnalyses } from '@/mocks/analysis.mock'
import GenerationProgress from '@/components/demo-site/GenerationProgress'
import toast from 'react-hot-toast'

interface Lead {
  id: number
  title: string
  original_url: string
  price?: number
}

interface CreateDemoWizardProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (buildId: string) => void
  preselectedLeadId?: number
}

type Step = 'select-lead' | 'review-analysis' | 'configure' | 'generating'
type GenerationStep = 'analyzing' | 'planning' | 'generating' | 'validating' | 'deploying' | 'completed'

export default function CreateDemoWizard({ isOpen, onClose, onSuccess, preselectedLeadId }: CreateDemoWizardProps) {
  const [currentStep, setCurrentStep] = useState<Step>('select-lead')
  const [generationStep, setGenerationStep] = useState<GenerationStep>('analyzing')
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [selectedFramework, setSelectedFramework] = useState<Framework>('react')
  const [includeComments, setIncludeComments] = useState(true)
  const [autoDeploy, setAutoDeploy] = useState(true)

  // Use mock leads data
  const leads = mockLeads.filter(l => l.status === 'qualified').slice(0, 10)
  const leadsLoading = false

  // Get analysis for selected lead
  const analysis = selectedLead ? mockAnalyses.find(a => a.lead_id === selectedLead.id) : null

  // Preselect lead if provided
  useEffect(() => {
    if (preselectedLeadId && leads) {
      const lead = leads.find(l => l.id === preselectedLeadId)
      if (lead) {
        setSelectedLead(lead)
        setCurrentStep('review-analysis')
      }
    }
  }, [preselectedLeadId, leads])

  const handleClose = () => {
    setCurrentStep('select-lead')
    setGenerationStep('analyzing')
    setSelectedLead(null)
    setSelectedFramework('react')
    setIncludeComments(true)
    setAutoDeploy(true)
    onClose()
  }

  const handleReviewAnalysis = () => {
    if (!selectedLead) return
    setCurrentStep('review-analysis')
  }

  const handleCreateDemo = () => {
    setCurrentStep('generating')
    simulateGeneration()
  }

  const simulateGeneration = () => {
    const steps: GenerationStep[] = ['analyzing', 'planning', 'generating', 'validating', 'deploying', 'completed']
    let currentIndex = 0

    const interval = setInterval(() => {
      currentIndex++
      if (currentIndex < steps.length) {
        setGenerationStep(steps[currentIndex])
      } else {
        clearInterval(interval)
        // Simulate successful generation
        setTimeout(() => {
          toast.success('Demo site generated successfully!')
          onSuccess('build_react_abc123') // Mock build ID
          handleClose()
        }, 500)
      }
    }, 3000) // Change step every 3 seconds
  }

  if (!isOpen) return null

  const steps = [
    { id: 'select-lead', name: 'Select Lead', icon: CheckCircleIcon },
    { id: 'review-analysis', name: 'Review Analysis', icon: SparklesIcon },
    { id: 'configure', name: 'Configure', icon: CodeBracketIcon }
  ]

  const currentStepIndex = steps.findIndex(s => s.id === currentStep)

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 transition-opacity bg-dark-bg/80 backdrop-blur-sm" onClick={handleClose} />

        {/* Modal */}
        <div className="inline-block align-bottom bg-dark-surface rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full border border-dark-border">
          {/* Header */}
          <div className="px-6 py-4 border-b border-dark-border">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-dark-text-primary">
                Create Demo Site
              </h3>
              <button
                onClick={handleClose}
                className="text-dark-text-secondary hover:text-dark-text-primary"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Progress Steps */}
            <div className="mt-4">
              <div className="flex items-center justify-between">
                {steps.map((step, index) => (
                  <div key={step.id} className="flex items-center">
                    <div
                      className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                        index <= currentStepIndex
                          ? 'border-terminal-500 bg-terminal-500/20 text-terminal-400'
                          : 'border-dark-border bg-dark-bg text-dark-text-muted'
                      }`}
                    >
                      <step.icon className="w-5 h-5" />
                    </div>
                    {index < steps.length - 1 && (
                      <div
                        className={`w-16 h-0.5 mx-2 ${
                          index < currentStepIndex ? 'bg-terminal-500' : 'bg-dark-border'
                        }`}
                      />
                    )}
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between mt-2">
                {steps.map((step) => (
                  <div key={step.id} className="text-xs text-dark-text-secondary w-20 text-center">
                    {step.name}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
            {/* Step 1: Select Lead */}
            {currentStep === 'select-lead' && (
              <div>
                <h4 className="text-lg font-medium text-dark-text-primary mb-4">
                  Select a Lead
                </h4>
                {leadsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-terminal-500 mx-auto"></div>
                    <p className="mt-2 text-dark-text-secondary">Loading leads...</p>
                  </div>
                ) : leads && leads.length > 0 ? (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {leads.map((lead) => (
                      <div
                        key={lead.id}
                        onClick={() => setSelectedLead(lead)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                          selectedLead?.id === lead.id
                            ? 'border-terminal-500 bg-terminal-500/10'
                            : 'border-dark-border hover:border-terminal-600'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h5 className="font-medium text-dark-text-primary">{lead.title}</h5>
                            <p className="text-sm text-dark-text-secondary mt-1 truncate">{lead.original_url}</p>
                            {lead.price && (
                              <p className="text-sm text-green-600 font-semibold mt-1">
                                ${lead.price.toLocaleString()}
                              </p>
                            )}
                          </div>
                          {selectedLead?.id === lead.id && (
                            <CheckCircleIcon className="w-6 h-6 text-terminal-500" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-dark-text-secondary">
                    No qualified leads found. Please qualify some leads first.
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Review Analysis */}
            {currentStep === 'review-analysis' && analysis && (
              <div>
                <h4 className="text-lg font-medium text-dark-text-primary mb-4">
                  Website Analysis Results
                </h4>

                {/* Overall Score */}
                <div className="bg-gradient-to-r from-terminal-900/20 to-dark-border rounded-lg p-6 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h5 className="text-sm text-dark-text-secondary mb-1">Overall Health Score</h5>
                      <div className="text-4xl font-bold text-terminal-400">
                        {analysis.overall_score.toFixed(0)}/100
                      </div>
                    </div>
                    <div className={`text-6xl ${
                      analysis.overall_score >= 80 ? 'text-green-500' :
                      analysis.overall_score >= 60 ? 'text-yellow-500' :
                      'text-red-500'
                    }`}>
                      {analysis.overall_score >= 80 ? '😊' :
                       analysis.overall_score >= 60 ? '😐' : '😞'}
                    </div>
                  </div>
                </div>

                {/* Category Scores */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Design</div>
                    <div className="text-2xl font-bold text-dark-text-primary">
                      {analysis.design.score}/100
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">SEO</div>
                    <div className="text-2xl font-bold text-dark-text-primary">
                      {analysis.seo.score}/100
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Performance</div>
                    <div className="text-2xl font-bold text-dark-text-primary">
                      {analysis.performance.score}/100
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Accessibility</div>
                    <div className="text-2xl font-bold text-dark-text-primary">
                      {analysis.accessibility.score}/100
                    </div>
                  </div>
                </div>

                {/* Top Issues */}
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-dark-text-primary mb-2">Top Issues Found:</h5>
                  <ul className="space-y-1">
                    {[
                      ...analysis.design.issues.slice(0, 2),
                      ...analysis.seo.issues.slice(0, 2),
                      ...analysis.performance.issues.slice(0, 1)
                    ].map((issue, idx) => (
                      <li key={idx} className="text-sm text-dark-text-secondary flex items-start gap-2">
                        <span className="text-red-500 mt-0.5">•</span>
                        <span>{issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Step 3: Configure */}
            {currentStep === 'configure' && analysis && (
              <div>
                <h4 className="text-lg font-medium text-dark-text-primary mb-4">
                  Configure Demo Site
                </h4>

                {/* Plan Summary */}
                <div className="bg-terminal-900/20 rounded-lg p-4 mb-6">
                  <h5 className="font-medium text-dark-text-primary mb-2">Improvement Plan Summary</h5>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-dark-text-muted">Total Improvements</div>
                      <div className="text-xl font-bold text-terminal-400">
                        {analysis.improvements_summary.total_improvements}
                      </div>
                    </div>
                    <div>
                      <div className="text-dark-text-muted">High Priority</div>
                      <div className="text-xl font-bold text-orange-500">
                        {analysis.improvements_summary.high_priority}
                      </div>
                    </div>
                    <div>
                      <div className="text-dark-text-muted">Quick Wins</div>
                      <div className="text-xl font-bold text-green-500">
                        {analysis.improvements_summary.quick_wins}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Framework Selection */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-dark-text-primary mb-2">
                    Select Framework
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['html', 'react', 'nextjs'] as Framework[]).map((framework) => (
                      <button
                        key={framework}
                        onClick={() => setSelectedFramework(framework)}
                        className={`p-4 rounded-lg border-2 transition-colors ${
                          selectedFramework === framework
                            ? 'border-terminal-500 bg-terminal-500/10'
                            : 'border-dark-border hover:border-terminal-600'
                        }`}
                      >
                        <div className="text-3xl mb-2">{demoSitesUtils.getFrameworkIcon(framework)}</div>
                        <div className="font-medium text-dark-text-primary text-sm">
                          {demoSitesUtils.getFrameworkName(framework)}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Options */}
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeComments}
                      onChange={(e) => setIncludeComments(e.target.checked)}
                      className="form-checkbox h-5 w-5 text-terminal-500 rounded border-dark-border bg-dark-bg"
                    />
                    <div>
                      <div className="text-sm font-medium text-dark-text-primary">
                        Include Explanation Comments
                      </div>
                      <div className="text-xs text-dark-text-secondary">
                        Add inline comments explaining improvements
                      </div>
                    </div>
                  </label>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoDeploy}
                      onChange={(e) => setAutoDeploy(e.target.checked)}
                      className="form-checkbox h-5 w-5 text-terminal-500 rounded border-dark-border bg-dark-bg"
                    />
                    <div>
                      <div className="text-sm font-medium text-dark-text-primary">
                        Auto-deploy to Preview
                      </div>
                      <div className="text-xs text-dark-text-secondary">
                        Automatically deploy to Vercel for live preview
                      </div>
                    </div>
                  </label>
                </div>
              </div>
            )}

            {/* Step 4: Generating */}
            {currentStep === 'generating' && (
              <GenerationProgress
                currentStep={generationStep}
                onComplete={() => {
                  // Completion handled in simulateGeneration
                }}
              />
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-dark-border bg-dark-border/30">
            <div className="flex items-center justify-between">
              <button
                onClick={handleClose}
                className="btn-secondary"
                disabled={currentStep === 'generating'}
              >
                Cancel
              </button>

              <div className="flex items-center gap-2">
                {currentStep === 'select-lead' && (
                  <button
                    onClick={handleReviewAnalysis}
                    disabled={!selectedLead}
                    className="btn-primary flex items-center gap-2"
                  >
                    <span>Review Analysis</span>
                    <ArrowRightIcon className="w-4 h-4" />
                  </button>
                )}

                {currentStep === 'review-analysis' && (
                  <button
                    onClick={() => setCurrentStep('configure')}
                    className="btn-primary flex items-center gap-2"
                  >
                    <span>Configure Demo</span>
                    <ArrowRightIcon className="w-4 h-4" />
                  </button>
                )}

                {currentStep === 'configure' && (
                  <button
                    onClick={handleCreateDemo}
                    className="btn-primary flex items-center gap-2"
                  >
                    <RocketLaunchIcon className="w-4 h-4" />
                    <span>Create Demo Site</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
