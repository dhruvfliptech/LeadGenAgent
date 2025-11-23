import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CampaignFormData } from '@/types/campaign'
import { mockTemplates } from '@/mocks/campaigns.mock'
import EmailTemplateEditor from './EmailTemplateEditor'
import TemplatePreview from './TemplatePreview'
import SendRateControl from './SendRateControl'
import { CheckIcon } from '@heroicons/react/24/solid'

const STEPS = [
  { id: 1, name: 'Basic Info' },
  { id: 2, name: 'Lead Filtering' },
  { id: 3, name: 'Email Content' },
  { id: 4, name: 'Scheduling' },
  { id: 5, name: 'Review' },
]

export default function CampaignCreationWizard() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    subject: '',
    template_id: undefined,
    body_html: '',
    body_text: '',
    lead_filters: {
      sources: [],
      statuses: [],
      tags: [],
      has_email: true,
    },
    scheduled_at: '',
    send_rate_per_hour: 20,
    track_opens: true,
    track_clicks: true,
    follow_up_enabled: false,
    follow_up_delay_days: 3,
  })

  const updateFormData = (updates: Partial<CampaignFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }))
  }

  const nextStep = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = () => {
    // In real implementation, this would call an API
    console.log('Creating campaign:', formData)
    // Show success message and redirect
    alert('Campaign created successfully!')
    navigate('/campaigns')
  }

  const loadTemplate = (templateId: number) => {
    const template = mockTemplates.find((t) => t.id === templateId)
    if (template) {
      updateFormData({
        template_id: templateId,
        subject: template.subject,
        body_html: template.body_html,
        body_text: template.body_text,
      })
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Step Indicator */}
      <nav aria-label="Progress" className="mb-8">
        <ol className="flex items-center justify-between">
          {STEPS.map((step) => (
            <li key={step.id} className="relative flex-1">
              <div className="flex items-center">
                <div className="flex items-center">
                  {currentStep > step.id ? (
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600">
                      <CheckIcon className="h-6 w-6 text-white" />
                    </div>
                  ) : (
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                        currentStep === step.id
                          ? 'border-blue-600 bg-blue-600 text-white'
                          : 'border-gray-300 bg-white text-gray-500'
                      }`}
                    >
                      <span className="text-sm font-medium">{step.id}</span>
                    </div>
                  )}
                  <span
                    className={`ml-3 text-sm font-medium ${
                      currentStep === step.id
                        ? 'text-blue-600'
                        : currentStep > step.id
                        ? 'text-gray-900'
                        : 'text-gray-500'
                    }`}
                  >
                    {step.name}
                  </span>
                </div>
                {step.id < STEPS.length && (
                  <div
                    className={`ml-4 flex-1 h-0.5 ${
                      currentStep > step.id ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            </li>
          ))}
        </ol>
      </nav>

      {/* Step Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-8">
        {/* Step 1: Basic Info */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Campaign Details</h2>
              <p className="text-gray-600">Set up the basic information for your email campaign.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Campaign Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => updateFormData({ name: e.target.value })}
                placeholder="e.g., Q1 Web Design Outreach"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">Internal name for tracking purposes</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Use Existing Template (Optional)
              </label>
              <div className="grid grid-cols-1 gap-3">
                {mockTemplates.map((template) => (
                  <div
                    key={template.id}
                    onClick={() => loadTemplate(template.id)}
                    className={`cursor-pointer border-2 rounded-lg p-4 transition-colors ${
                      formData.template_id === template.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{template.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">{template.subject}</p>
                      </div>
                      <input
                        type="radio"
                        checked={formData.template_id === template.id}
                        onChange={() => loadTemplate(template.id)}
                        className="h-4 w-4 text-blue-600"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Lead Filtering */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Target Audience</h2>
              <p className="text-gray-600">Select which leads should receive this campaign.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Lead Sources
              </label>
              <div className="space-y-2">
                {['craigslist', 'google_maps', 'linkedin', 'job_boards'].map((source) => (
                  <label key={source} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.lead_filters.sources?.includes(source)}
                      onChange={(e) => {
                        const sources = formData.lead_filters.sources || []
                        updateFormData({
                          lead_filters: {
                            ...formData.lead_filters,
                            sources: e.target.checked
                              ? [...sources, source]
                              : sources.filter((s) => s !== source),
                          },
                        })
                      }}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">
                      {source.replace('_', ' ')}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Lead Status
              </label>
              <div className="space-y-2">
                {['new', 'contacted', 'qualified', 'converted'].map((status) => (
                  <label key={status} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.lead_filters.statuses?.includes(status)}
                      onChange={(e) => {
                        const statuses = formData.lead_filters.statuses || []
                        updateFormData({
                          lead_filters: {
                            ...formData.lead_filters,
                            statuses: e.target.checked
                              ? [...statuses, status]
                              : statuses.filter((s) => s !== status),
                          },
                        })
                      }}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{status}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.lead_filters.has_email}
                  onChange={(e) =>
                    updateFormData({
                      lead_filters: {
                        ...formData.lead_filters,
                        has_email: e.target.checked,
                      },
                    })
                  }
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Only leads with email addresses
                </span>
              </label>
              <p className="ml-6 text-xs text-gray-500">Recommended for email campaigns</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <p className="text-sm text-blue-800">
                <strong>Estimated recipients:</strong> ~150 leads match your filters
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Email Content */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Content</h2>
              <p className="text-gray-600">Compose your email or customize the selected template.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <EmailTemplateEditor
                  subject={formData.subject}
                  bodyHtml={formData.body_html}
                  bodyText={formData.body_text}
                  onSubjectChange={(subject) => updateFormData({ subject })}
                  onBodyHtmlChange={(body_html) => updateFormData({ body_html })}
                  onBodyTextChange={(body_text) => updateFormData({ body_text })}
                />
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Preview</h3>
                <TemplatePreview subject={formData.subject} bodyHtml={formData.body_html} />
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Scheduling */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Schedule & Settings</h2>
              <p className="text-gray-600">Configure when and how emails will be sent.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                When to Send
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    checked={!formData.scheduled_at}
                    onChange={() => updateFormData({ scheduled_at: '' })}
                    className="h-4 w-4 text-blue-600"
                  />
                  <span className="ml-2 text-sm text-gray-700">Send immediately</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    checked={!!formData.scheduled_at}
                    onChange={() => {
                      const tomorrow = new Date()
                      tomorrow.setDate(tomorrow.getDate() + 1)
                      updateFormData({ scheduled_at: tomorrow.toISOString() })
                    }}
                    className="h-4 w-4 text-blue-600"
                  />
                  <span className="ml-2 text-sm text-gray-700">Schedule for later</span>
                </label>
              </div>

              {formData.scheduled_at && (
                <div className="mt-3">
                  <input
                    type="datetime-local"
                    value={formData.scheduled_at.slice(0, 16)}
                    onChange={(e) =>
                      updateFormData({ scheduled_at: new Date(e.target.value).toISOString() })
                    }
                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>

            <SendRateControl
              value={formData.send_rate_per_hour}
              onChange={(send_rate_per_hour) => updateFormData({ send_rate_per_hour })}
            />

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.track_opens}
                  onChange={(e) => updateFormData({ track_opens: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Track email opens</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.track_clicks}
                  onChange={(e) => updateFormData({ track_clicks: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Track link clicks</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.follow_up_enabled}
                  onChange={(e) => updateFormData({ follow_up_enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Enable automatic follow-up</span>
              </label>

              {formData.follow_up_enabled && (
                <div className="ml-6">
                  <label className="block text-xs text-gray-600 mb-1">
                    Follow-up delay (days)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="30"
                    value={formData.follow_up_delay_days}
                    onChange={(e) =>
                      updateFormData({ follow_up_delay_days: parseInt(e.target.value) })
                    }
                    className="w-24 px-2 py-1 text-sm border border-gray-300 rounded-md"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 5: Review */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Review & Launch</h2>
              <p className="text-gray-600">Review your campaign settings before launching.</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6 space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Campaign Name</h3>
                <p className="text-base text-gray-900">{formData.name}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Subject Line</h3>
                <p className="text-base text-gray-900">{formData.subject}</p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Target Audience</h3>
                <p className="text-base text-gray-900">
                  ~150 leads matching your filters
                </p>
                <ul className="mt-2 text-sm text-gray-600 space-y-1">
                  {formData.lead_filters.sources && formData.lead_filters.sources.length > 0 && (
                    <li>
                      Sources: {formData.lead_filters.sources.map(s => s.replace('_', ' ')).join(', ')}
                    </li>
                  )}
                  {formData.lead_filters.has_email && <li>Only leads with email</li>}
                </ul>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Send Schedule</h3>
                <p className="text-base text-gray-900">
                  {formData.scheduled_at
                    ? `Scheduled for ${new Date(formData.scheduled_at).toLocaleString()}`
                    : 'Send immediately'}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Send Rate</h3>
                <p className="text-base text-gray-900">
                  {formData.send_rate_per_hour} emails per hour
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Tracking</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>{formData.track_opens ? '✓' : '✗'} Track opens</li>
                  <li>{formData.track_clicks ? '✓' : '✗'} Track clicks</li>
                  <li>{formData.follow_up_enabled ? '✓' : '✗'} Automatic follow-up</li>
                </ul>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 mb-1">Estimated Cost</h3>
                <p className="text-2xl font-bold text-gray-900">$15.00</p>
                <p className="text-xs text-gray-500 mt-1">Based on 150 recipients @ $0.10 each</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> Once launched, you can pause but not edit the campaign.
                Make sure all details are correct before proceeding.
              </p>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={currentStep === 1 ? () => navigate('/campaigns') : prevStep}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {currentStep === 1 ? 'Cancel' : 'Back'}
          </button>

          {currentStep < STEPS.length ? (
            <button
              type="button"
              onClick={nextStep}
              disabled={currentStep === 1 && !formData.name}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700"
            >
              Launch Campaign
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
