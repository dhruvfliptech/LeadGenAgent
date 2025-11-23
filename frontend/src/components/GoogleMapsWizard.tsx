import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import { XMarkIcon, MapPinIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface GoogleMapsConfig {
  search_query: string
  location: string
  radius: number
  min_rating: number
  min_reviews: number
  open_now: boolean
  max_results: number
  enable_enrichment: boolean
}

interface GoogleMapsWizardProps {
  open: boolean
  onClose: () => void
  onSubmit: (config: GoogleMapsConfig) => void
}

/**
 * GoogleMapsWizard - 3-step wizard for configuring Google Maps scraping
 * Step 1: Search query + location + radius with map preview
 * Step 2: Business type filters (rating, reviews, status)
 * Step 3: Review & start
 */
export default function GoogleMapsWizard({ open, onClose, onSubmit }: GoogleMapsWizardProps) {
  const [step, setStep] = useState(1)
  const [config, setConfig] = useState<GoogleMapsConfig>({
    search_query: '',
    location: '',
    radius: 25,
    min_rating: 0,
    min_reviews: 0,
    open_now: false,
    max_results: 100,
    enable_enrichment: true
  })

  const handleNext = () => {
    if (step === 1) {
      if (!config.search_query || !config.location) {
        toast.error('Please enter search query and location')
        return
      }
    }
    setStep(step + 1)
  }

  const handleBack = () => setStep(step - 1)

  const handleSubmit = () => {
    onSubmit(config)
    onClose()
    setStep(1)
  }

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          What are you looking for?
        </label>
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
          <input
            type="text"
            value={config.search_query}
            onChange={(e) => setConfig({ ...config, search_query: e.target.value })}
            placeholder="e.g., web design agency, Italian restaurant, dentist"
            className="form-input pl-10 w-full"
          />
        </div>
        <p className="mt-1 text-xs text-dark-text-muted">Business type or service</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Where?
        </label>
        <div className="relative">
          <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
          <input
            type="text"
            value={config.location}
            onChange={(e) => setConfig({ ...config, location: e.target.value })}
            placeholder="e.g., San Francisco, CA"
            className="form-input pl-10 w-full"
          />
        </div>
        <p className="mt-1 text-xs text-dark-text-muted">City or address</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-2">
          Search Radius: {config.radius} miles
        </label>
        <input
          type="range"
          min="1"
          max="100"
          value={config.radius}
          onChange={(e) => setConfig({ ...config, radius: parseInt(e.target.value) })}
          className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-dark-text-muted mt-1">
          <span>1 mi</span>
          <span>100 mi</span>
        </div>
      </div>

      {/* Map Preview Placeholder */}
      <div className="bg-dark-border rounded-lg p-8 text-center">
        <MapPinIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-2" />
        <p className="text-sm text-dark-text-muted">Map preview would show here</p>
        {config.location && (
          <p className="text-xs text-dark-text-secondary mt-1">
            {config.radius} mile radius around {config.location}
          </p>
        )}
      </div>
    </div>
  )

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-dark-text-primary mb-3">
          Business Filters
        </label>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-dark-text-secondary mb-2">
              Minimum Rating: {config.min_rating > 0 ? `${config.min_rating}+ stars` : 'Any'}
            </label>
            <input
              type="range"
              min="0"
              max="5"
              step="0.5"
              value={config.min_rating}
              onChange={(e) => setConfig({ ...config, min_rating: parseFloat(e.target.value) })}
              className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-dark-text-muted mt-1">
              <span>Any</span>
              <span>⭐⭐⭐⭐⭐</span>
            </div>
          </div>

          <div>
            <label className="block text-sm text-dark-text-secondary mb-2">
              Minimum Reviews: {config.min_reviews > 0 ? `${config.min_reviews}+` : 'Any'}
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              value={config.min_reviews}
              onChange={(e) => setConfig({ ...config, min_reviews: parseInt(e.target.value) })}
              className="w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-dark-text-muted mt-1">
              <span>Any</span>
              <span>100+</span>
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="open_now"
              checked={config.open_now}
              onChange={(e) => setConfig({ ...config, open_now: e.target.checked })}
              className="form-checkbox"
            />
            <label htmlFor="open_now" className="ml-2 text-sm text-dark-text-primary">
              Only show businesses that are open now
            </label>
          </div>
        </div>
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
        <p className="mt-1 text-xs text-dark-text-muted">Maximum: 500</p>
      </div>

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
              Enrich leads with contact information
            </label>
            <p className="text-xs text-dark-text-muted mt-1">
              Find emails via Hunter.io/Apollo.io (+$0.10 per lead)
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="bg-dark-border/30 rounded-lg p-6">
        <h4 className="text-sm font-medium text-dark-text-primary mb-4">Review Configuration</h4>

        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Search Query:</dt>
            <dd className="text-dark-text-primary font-medium">{config.search_query}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Location:</dt>
            <dd className="text-dark-text-primary font-medium">{config.location}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Radius:</dt>
            <dd className="text-dark-text-primary font-medium">{config.radius} miles</dd>
          </div>
          {config.min_rating > 0 && (
            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Min Rating:</dt>
              <dd className="text-dark-text-primary font-medium">{config.min_rating}+ stars</dd>
            </div>
          )}
          {config.min_reviews > 0 && (
            <div className="flex justify-between">
              <dt className="text-dark-text-secondary">Min Reviews:</dt>
              <dd className="text-dark-text-primary font-medium">{config.min_reviews}+</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Max Results:</dt>
            <dd className="text-dark-text-primary font-medium">{config.max_results}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-dark-text-secondary">Enrichment:</dt>
            <dd className="text-dark-text-primary font-medium">
              {config.enable_enrichment ? 'Enabled' : 'Disabled'}
            </dd>
          </div>
        </dl>
      </div>

      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-400 mb-2">Estimated Results</h4>
        <p className="text-sm text-dark-text-secondary">
          ~{Math.min(config.max_results, 80)}-{config.max_results} businesses
        </p>
        <p className="text-xs text-dark-text-muted mt-1">
          Estimated time: ~{Math.ceil(config.max_results / 20)} minutes
        </p>
        {config.enable_enrichment && (
          <p className="text-xs text-dark-text-muted mt-1">
            Enrichment cost: ~${(config.max_results * 0.1).toFixed(2)}
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
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-dark-border">
            <div>
              <Dialog.Title className="text-lg font-bold text-dark-text-primary">
                🗺️ Configure Google Maps Scraping
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

          {/* Progress */}
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

          {/* Content */}
          <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
            {step === 1 && renderStep1()}
            {step === 2 && renderStep2()}
            {step === 3 && renderStep3()}
          </div>

          {/* Footer */}
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
