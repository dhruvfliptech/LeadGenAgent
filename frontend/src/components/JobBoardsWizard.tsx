import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface JobBoard {
  id: string
  name: string
  description: string
  coverage: string
  icon: string
}

const JOB_BOARDS: JobBoard[] = [
  { id: 'indeed', name: 'Indeed', description: "World's largest job site", coverage: 'Global', icon: '🔍' },
  { id: 'monster', name: 'Monster', description: '20M+ jobs globally', coverage: 'Global', icon: '👹' },
  { id: 'ziprecruiter', name: 'ZipRecruiter', description: 'US-focused job board', coverage: 'USA', icon: '⚡' },
  { id: 'glassdoor', name: 'Glassdoor', description: 'Jobs + company reviews', coverage: 'Global', icon: '🚪' },
  { id: 'linkedin_jobs', name: 'LinkedIn Jobs', description: 'Professional network jobs', coverage: 'Global', icon: '💼' },
  { id: 'angellist', name: 'AngelList', description: 'Startup jobs', coverage: 'Global', icon: '👼' }
]

const EXPERIENCE_LEVELS = ['Entry Level', 'Mid Level', 'Senior', 'Executive']
const JOB_TYPES = ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Internship']
const COMPANY_SIZES = ['Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)']

interface JobBoardsConfig {
  selected_boards: string[]
  job_title: string
  locations: string[]
  remote_options: {
    remote_only: boolean
    hybrid: boolean
    on_site: boolean
  }
  experience_levels: string[]
  salary_min: number
  salary_max: number
  company_sizes: string[]
  date_posted: string
  max_results_per_board: number
  extract_fields: {
    company_name: boolean
    job_title: boolean
    job_description: boolean
    apply_url: boolean
    company_website: boolean
    posted_date: boolean
    salary: boolean
  }
  enable_enrichment: boolean
  deduplicate: boolean
}

interface JobBoardsWizardProps {
  open: boolean
  onClose: () => void
  onSubmit: (config: JobBoardsConfig) => void
}

/**
 * JobBoardsWizard - 3-step wizard for job board scraping
 * Step 1: Select job boards
 * Step 2: Job search criteria
 * Step 3: Lead extraction configuration
 */
export default function JobBoardsWizard({ open, onClose, onSubmit }: JobBoardsWizardProps) {
  const [step, setStep] = useState(1)
  const [config, setConfig] = useState<JobBoardsConfig>({
    selected_boards: ['indeed', 'monster', 'ziprecruiter'],
    job_title: '',
    locations: [],
    remote_options: {
      remote_only: false,
      hybrid: false,
      on_site: true
    },
    experience_levels: [],
    salary_min: 0,
    salary_max: 200000,
    company_sizes: [],
    date_posted: 'any',
    max_results_per_board: 50,
    extract_fields: {
      company_name: true,
      job_title: true,
      job_description: true,
      apply_url: true,
      company_website: true,
      posted_date: true,
      salary: true
    },
    enable_enrichment: true,
    deduplicate: true
  })

  const handleNext = () => {
    if (step === 1 && config.selected_boards.length === 0) {
      toast.error('Please select at least one job board')
      return
    }
    if (step === 2 && !config.job_title) {
      toast.error('Please enter a job title or keywords')
      return
    }
    setStep(step + 1)
  }

  const handleBack = () => setStep(step - 1)

  const handleSubmit = () => {
    onSubmit(config)
    onClose()
    setStep(1)
  }

  const toggleBoard = (boardId: string) => {
    if (config.selected_boards.includes(boardId)) {
      setConfig({ ...config, selected_boards: config.selected_boards.filter(b => b !== boardId) })
    } else {
      setConfig({ ...config, selected_boards: [...config.selected_boards, boardId] })
    }
  }

  const renderStep1 = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-3">
          Select Job Boards ({config.selected_boards.length} selected)
        </label>

        <div className="grid grid-cols-2 gap-4">
          {JOB_BOARDS.map((board) => {
            const isSelected = config.selected_boards.includes(board.id)
            return (
              <button
                key={board.id}
                onClick={() => toggleBoard(board.id)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  isSelected
                    ? 'border-terminal-500 bg-terminal-500/10'
                    : 'border-dark-border hover:border-dark-border/50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-2xl">{board.icon}</span>
                  {isSelected && (
                    <CheckCircleIcon className="w-5 h-5 text-terminal-500" />
                  )}
                </div>
                <h4 className="text-sm font-medium text-dark-text-primary mb-1">{board.name}</h4>
                <p className="text-xs text-dark-text-muted mb-1">{board.description}</p>
                <span className="text-xs text-dark-text-secondary">Coverage: {board.coverage}</span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Job Title / Keywords
        </label>
        <input
          type="text"
          value={config.job_title}
          onChange={(e) => setConfig({ ...config, job_title: e.target.value })}
          placeholder="e.g., Software Engineer, Marketing Manager"
          className="form-input w-full"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Locations (comma-separated)
        </label>
        <input
          type="text"
          placeholder="e.g., San Francisco, New York, Remote"
          className="form-input w-full"
          onChange={(e) => setConfig({ ...config, locations: e.target.value.split(',').map(l => l.trim()) })}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Remote Options
        </label>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.remote_options.remote_only}
              onChange={(e) => setConfig({
                ...config,
                remote_options: { ...config.remote_options, remote_only: e.target.checked }
              })}
              className="form-checkbox"
            />
            <span className="text-sm text-dark-text-primary">Remote Only</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.remote_options.hybrid}
              onChange={(e) => setConfig({
                ...config,
                remote_options: { ...config.remote_options, hybrid: e.target.checked }
              })}
              className="form-checkbox"
            />
            <span className="text-sm text-dark-text-primary">Hybrid</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={config.remote_options.on_site}
              onChange={(e) => setConfig({
                ...config,
                remote_options: { ...config.remote_options, on_site: e.target.checked }
              })}
              className="form-checkbox"
            />
            <span className="text-sm text-dark-text-primary">On-site</span>
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Experience Level
        </label>
        <div className="grid grid-cols-2 gap-2">
          {EXPERIENCE_LEVELS.map((level) => (
            <label key={level} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.experience_levels.includes(level)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig({ ...config, experience_levels: [...config.experience_levels, level] })
                  } else {
                    setConfig({ ...config, experience_levels: config.experience_levels.filter(l => l !== level) })
                  }
                }}
                className="form-checkbox"
              />
              <span className="text-sm text-dark-text-primary">{level}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Salary Range: ${config.salary_min.toLocaleString()} - ${config.salary_max >= 200000 ? '200k+' : config.salary_max.toLocaleString()}
        </label>
        <div className="space-y-2">
          <input
            type="range"
            min="0"
            max="200000"
            step="5000"
            value={config.salary_min}
            onChange={(e) => setConfig({ ...config, salary_min: parseInt(e.target.value) })}
            className="w-full"
          />
          <input
            type="range"
            min="0"
            max="200000"
            step="5000"
            value={config.salary_max}
            onChange={(e) => setConfig({ ...config, salary_max: parseInt(e.target.value) })}
            className="w-full"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Company Size
        </label>
        <div className="grid grid-cols-2 gap-2">
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
          Date Posted
        </label>
        <select
          value={config.date_posted}
          onChange={(e) => setConfig({ ...config, date_posted: e.target.value })}
          className="form-input w-full"
        >
          <option value="24h">Last 24 hours</option>
          <option value="3d">Last 3 days</option>
          <option value="7d">Last week</option>
          <option value="30d">Last month</option>
          <option value="any">Any time</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Max Results per Board
        </label>
        <input
          type="number"
          value={config.max_results_per_board}
          onChange={(e) => setConfig({ ...config, max_results_per_board: parseInt(e.target.value) })}
          min="1"
          max="200"
          className="form-input w-full"
        />
        <p className="text-xs text-dark-text-muted mt-1">Maximum: 200 per board</p>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-3">
          What to extract from job postings
        </label>
        <div className="space-y-2">
          {Object.entries(config.extract_fields).map(([field, checked]) => (
            <label key={field} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checked}
                onChange={(e) => setConfig({
                  ...config,
                  extract_fields: { ...config.extract_fields, [field]: e.target.checked }
                })}
                className="form-checkbox"
              />
              <span className="text-sm text-dark-text-primary">
                {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-dark-border/30 rounded-lg p-4 space-y-3">
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
              Find hiring manager emails and company contact info
            </label>
            <p className="text-xs text-dark-text-muted mt-1">
              Uses n8n workflow with Hunter.io/Apollo.io (+$0.10 per lead)
            </p>
          </div>
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="deduplicate"
            checked={config.deduplicate}
            onChange={(e) => setConfig({ ...config, deduplicate: e.target.checked })}
            className="form-checkbox mt-1"
          />
          <div className="ml-3">
            <label htmlFor="deduplicate" className="text-sm font-medium text-dark-text-primary">
              Remove duplicate jobs across boards
            </label>
            <p className="text-xs text-dark-text-muted mt-1">
              Matches by company name + job title
            </p>
          </div>
        </div>
      </div>

      <div className="bg-dark-border/30 rounded-lg p-6">
        <h4 className="text-sm font-medium text-dark-text-primary mb-4">Review Configuration</h4>

        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Boards Selected:</dt>
            <dd className="text-dark-text-primary font-medium">{config.selected_boards.length}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Job Title:</dt>
            <dd className="text-dark-text-primary font-medium">{config.job_title || 'Any'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Locations:</dt>
            <dd className="text-dark-text-primary font-medium">
              {config.locations.length > 0 ? config.locations.join(', ') : 'Any'}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Max Results:</dt>
            <dd className="text-dark-text-primary font-medium">
              {config.max_results_per_board} per board (~{config.max_results_per_board * config.selected_boards.length} total)
            </dd>
          </div>
        </dl>
      </div>

      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-400 mb-2">Estimated Results</h4>
        <p className="text-sm text-dark-text-secondary">
          ~{config.max_results_per_board * config.selected_boards.length} job postings
        </p>
        <p className="text-xs text-dark-text-muted mt-1">
          Estimated time: ~{Math.ceil((config.max_results_per_board * config.selected_boards.length) / 30)} minutes
        </p>
        {config.enable_enrichment && (
          <p className="text-xs text-dark-text-muted mt-1">
            Enrichment cost: ~${(config.max_results_per_board * config.selected_boards.length * 0.1).toFixed(2)}
          </p>
        )}
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
                🔍 Configure Job Boards Scraping
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
