import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { XMarkIcon, UserIcon, BuildingOfficeIcon, BriefcaseIcon, ExclamationTriangleIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type SearchType = 'people' | 'company' | 'jobs'

interface LinkedInConfig {
  search_type: SearchType
  job_titles?: string[]
  company?: string
  locations: string[]
  industries: string[]
  company_sizes: string[]
  seniority_levels: string[]
  keywords?: string
  max_results: number
  enable_enrichment: boolean
  auth_method: 'credentials' | 'csv'
  username?: string
  password?: string
  csv_file?: File
  rate_limit: number
  request_delay: number
}

interface LinkedInWizardProps {
  open: boolean
  onClose: () => void
  onSubmit: (config: LinkedInConfig) => void
}

const COMPANY_SIZES = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1000+']
const SENIORITY_LEVELS = ['Entry', 'Mid', 'Senior', 'Manager', 'Director', 'VP', 'C-level']
const INDUSTRIES = ['Technology', 'Finance', 'Healthcare', 'Marketing', 'Education', 'Retail', 'Manufacturing', 'Real Estate']

/**
 * LinkedInWizard - 3-step wizard for LinkedIn scraping
 * Step 1: Search type (People/Company/Jobs)
 * Step 2: Search criteria
 * Step 3: Authentication OR CSV upload
 */
export default function LinkedInWizard({ open, onClose, onSubmit }: LinkedInWizardProps) {
  const [step, setStep] = useState(1)
  const [config, setConfig] = useState<LinkedInConfig>({
    search_type: 'people',
    locations: [],
    industries: [],
    company_sizes: [],
    seniority_levels: [],
    max_results: 100,
    enable_enrichment: true,
    auth_method: 'csv',
    rate_limit: 100,
    request_delay: 10
  })

  const handleNext = () => {
    if (step === 2 && config.locations.length === 0) {
      toast.error('Please select at least one location')
      return
    }
    setStep(step + 1)
  }

  const handleBack = () => setStep(step - 1)

  const handleSubmit = () => {
    if (config.auth_method === 'credentials' && (!config.username || !config.password)) {
      toast.error('Please provide LinkedIn credentials')
      return
    }
    if (config.auth_method === 'csv' && !config.csv_file) {
      toast.error('Please upload a CSV file')
      return
    }
    onSubmit(config)
    onClose()
    setStep(1)
  }

  const renderStep1 = () => (
    <div className="space-y-4">
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 flex gap-3">
        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-yellow-400 font-medium">LinkedIn Warning</p>
          <p className="text-xs text-dark-text-secondary mt-1">
            LinkedIn actively blocks scrapers. We recommend using LinkedIn Sales Navigator API or manual CSV exports. Proceed with caution.
          </p>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-3">
          What do you want to search?
        </label>

        <div className="grid grid-cols-3 gap-4">
          <button
            onClick={() => setConfig({ ...config, search_type: 'people' })}
            className={`p-6 rounded-lg border-2 transition-all ${
              config.search_type === 'people'
                ? 'border-terminal-500 bg-terminal-500/10'
                : 'border-dark-border hover:border-dark-border/50'
            }`}
          >
            <UserIcon className="w-8 h-8 text-terminal-500 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-dark-text-primary mb-1">People Search</h4>
            <p className="text-xs text-dark-text-muted">Find professionals by title, company, location</p>
          </button>

          <button
            onClick={() => setConfig({ ...config, search_type: 'company' })}
            className={`p-6 rounded-lg border-2 transition-all ${
              config.search_type === 'company'
                ? 'border-terminal-500 bg-terminal-500/10'
                : 'border-dark-border hover:border-dark-border/50'
            }`}
          >
            <BuildingOfficeIcon className="w-8 h-8 text-terminal-500 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-dark-text-primary mb-1">Company Search</h4>
            <p className="text-xs text-dark-text-muted">Find companies by industry, size, location</p>
          </button>

          <button
            onClick={() => setConfig({ ...config, search_type: 'jobs' })}
            className={`p-6 rounded-lg border-2 transition-all ${
              config.search_type === 'jobs'
                ? 'border-terminal-500 bg-terminal-500/10'
                : 'border-dark-border hover:border-dark-border/50'
            }`}
          >
            <BriefcaseIcon className="w-8 h-8 text-terminal-500 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-dark-text-primary mb-1">Job Search</h4>
            <p className="text-xs text-dark-text-muted">Find job postings by title, company, location</p>
          </button>
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      {config.search_type === 'people' && (
        <>
          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Job Titles (comma-separated)
            </label>
            <input
              type="text"
              placeholder="e.g., Marketing Manager, CEO, Developer"
              className="form-input w-full"
              onChange={(e) => setConfig({ ...config, job_titles: e.target.value.split(',').map(t => t.trim()) })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Company (optional)
            </label>
            <input
              type="text"
              placeholder="Current or past company"
              className="form-input w-full"
              onChange={(e) => setConfig({ ...config, company: e.target.value })}
            />
          </div>
        </>
      )}

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Locations (comma-separated)
        </label>
        <input
          type="text"
          placeholder="e.g., San Francisco, New York, London"
          className="form-input w-full"
          onChange={(e) => setConfig({ ...config, locations: e.target.value.split(',').map(l => l.trim()) })}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Industries
        </label>
        <div className="grid grid-cols-2 gap-2">
          {INDUSTRIES.map((industry) => (
            <label key={industry} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.industries.includes(industry)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig({ ...config, industries: [...config.industries, industry] })
                  } else {
                    setConfig({ ...config, industries: config.industries.filter(i => i !== industry) })
                  }
                }}
                className="form-checkbox"
              />
              <span className="text-sm text-dark-text-primary">{industry}</span>
            </label>
          ))}
        </div>
      </div>

      {config.search_type === 'people' && (
        <>
          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Company Size
            </label>
            <div className="grid grid-cols-3 gap-2">
              {COMPANY_SIZES.map((size) => (
                <label key={size} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.company_sizes.includes(size)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setConfig({ ...config, company_sizes: [...config.company_sizes, size] })
                      } else {
                        setConfig({ ...config, company_sizes: config.company_sizes.filter(s => s !== size) })
                      }
                    }}
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-primary">{size}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Seniority Level
            </label>
            <div className="grid grid-cols-3 gap-2">
              {SENIORITY_LEVELS.map((level) => (
                <label key={level} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.seniority_levels.includes(level)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setConfig({ ...config, seniority_levels: [...config.seniority_levels, level] })
                      } else {
                        setConfig({ ...config, seniority_levels: config.seniority_levels.filter(l => l !== level) })
                      }
                    }}
                    className="form-checkbox"
                  />
                  <span className="text-sm text-dark-text-primary">{level}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Keywords (optional)
        </label>
        <input
          type="text"
          placeholder="Search in profiles, headlines, summaries"
          className="form-input w-full"
          onChange={(e) => setConfig({ ...config, keywords: e.target.value })}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Max Results
        </label>
        <input
          type="number"
          value={config.max_results}
          onChange={(e) => setConfig({ ...config, max_results: parseInt(e.target.value) })}
          min="1"
          max="500"
          className="form-input w-full"
        />
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-3">
          Authentication Method
        </label>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setConfig({ ...config, auth_method: 'csv' })}
            className={`p-4 rounded-lg border-2 transition-all ${
              config.auth_method === 'csv'
                ? 'border-terminal-500 bg-terminal-500/10'
                : 'border-dark-border hover:border-dark-border/50'
            }`}
          >
            <ArrowUpTrayIcon className="w-6 h-6 text-terminal-500 mx-auto mb-2" />
            <h4 className="text-sm font-medium text-dark-text-primary">Upload CSV</h4>
            <p className="text-xs text-dark-text-muted mt-1">Recommended - safer method</p>
          </button>

          <button
            onClick={() => setConfig({ ...config, auth_method: 'credentials' })}
            className={`p-4 rounded-lg border-2 transition-all ${
              config.auth_method === 'credentials'
                ? 'border-terminal-500 bg-terminal-500/10'
                : 'border-dark-border hover:border-dark-border/50'
            }`}
          >
            <UserIcon className="w-6 h-6 text-terminal-500 mx-auto mb-2" />
            <h4 className="text-sm font-medium text-dark-text-primary">LinkedIn Login</h4>
            <p className="text-xs text-dark-text-muted mt-1">May trigger account flags</p>
          </button>
        </div>
      </div>

      {config.auth_method === 'credentials' && (
        <>
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <p className="text-sm text-red-400 font-medium">High Risk</p>
            <p className="text-xs text-dark-text-secondary mt-1">
              Your account may be flagged or banned if scraping is detected. Use at your own risk.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              LinkedIn Username/Email
            </label>
            <input
              type="text"
              value={config.username || ''}
              onChange={(e) => setConfig({ ...config, username: e.target.value })}
              className="form-input w-full"
              placeholder="your.email@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              LinkedIn Password
            </label>
            <input
              type="password"
              value={config.password || ''}
              onChange={(e) => setConfig({ ...config, password: e.target.value })}
              className="form-input w-full"
              placeholder="••••••••"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Credentials are encrypted and never stored
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Daily Request Limit: {config.rate_limit}
            </label>
            <input
              type="range"
              min="10"
              max="200"
              value={config.rate_limit}
              onChange={(e) => setConfig({ ...config, rate_limit: parseInt(e.target.value) })}
              className="w-full"
            />
            <p className="text-xs text-dark-text-muted mt-1">Lower is safer (recommended: 100)</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-2">
              Delay Between Requests: {config.request_delay}s
            </label>
            <input
              type="range"
              min="5"
              max="60"
              value={config.request_delay}
              onChange={(e) => setConfig({ ...config, request_delay: parseInt(e.target.value) })}
              className="w-full"
            />
          </div>
        </>
      )}

      {config.auth_method === 'csv' && (
        <div>
          <label className="block text-sm font-medium text-dark-text-primary mb-2">
            Upload LinkedIn CSV Export
          </label>
          <div className="border-2 border-dashed border-dark-border rounded-lg p-8 text-center">
            <ArrowUpTrayIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-3" />
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setConfig({ ...config, csv_file: e.target.files?.[0] })}
              className="hidden"
              id="csv-upload"
            />
            <label
              htmlFor="csv-upload"
              className="btn-primary cursor-pointer inline-block"
            >
              Choose CSV File
            </label>
            {config.csv_file && (
              <p className="text-sm text-terminal-500 mt-2">
                Selected: {config.csv_file.name}
              </p>
            )}
            <p className="text-xs text-dark-text-muted mt-2">
              Export your LinkedIn search results to CSV and upload here
            </p>
          </div>
        </div>
      )}

      <div className="bg-dark-border/30 rounded-lg p-4">
        <div className="flex items-start">
          <input
            type="checkbox"
            id="enrichment"
            checked={config.enable_enrichment}
            onChange={(e) => setConfig({ ...config, enable_enrichment: e.target.checked })}
            className="form-checkbox mt-1"
          />
          <div className="ml-3">
            <label htmlFor="enrichment" className="text-sm font-medium text-dark-text-primary">
              Enrich leads with additional contact data
            </label>
            <p className="text-xs text-dark-text-muted mt-1">
              Find additional emails and phone numbers (+$0.10 per lead)
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />

      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl w-full bg-dark-surface rounded-xl shadow-xl">
          <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border">
            <div>
              <Dialog.Title className="text-lg font-bold text-dark-text-primary">
                💼 Configure LinkedIn Scraping
              </Dialog.Title>
              <p className="text-sm text-dark-text-secondary mt-1">
                Step {step} of 3
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-dark-text-muted hover:text-dark-text-primary transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          <div className="px-6 pt-4">
            <div className="flex items-center gap-2">
              {[1, 2, 3].map((s) => (
                <div
                  key={s}
                  className={`flex-1 h-2 rounded-full transition-colors ${
                    s <= step ? 'bg-terminal-500' : 'bg-dark-border'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
          </div>

          <div className="flex items-center justify-between px-6 py-4 border-t border-dark-border">
            <button
              onClick={step === 1 ? onClose : handleBack}
              className="btn-secondary"
            >
              {step === 1 ? 'Cancel' : '← Back'}
            </button>
            <button
              onClick={step === 3 ? handleSubmit : handleNext}
              className="btn-primary"
            >
              {step === 3 ? 'Start Scraping' : 'Next →'}
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
