import { useState } from 'react'
import CategorySelector from '@/components/CategorySelector'
import LocationSelector from '@/components/LocationSelector'
import SourceSelector from '@/components/SourceSelector'
import { LeadSource } from '@/types/lead'

export default function ScrapeBuilder({
  onSubmit,
}: {
  onSubmit: (payload: {
    source: LeadSource
    location_ids: number[]
    categories?: string[]
    keywords?: string[]
    max_pages: number
    priority: 'low' | 'normal' | 'high'
    enable_email_extraction: boolean
    captcha_api_key?: string
    // Google Maps specific
    business_category?: string
    radius?: number
    // LinkedIn specific
    company_size?: string
    // Job boards specific
    salary_range?: string
  }) => void
}) {
  const [source, setSource] = useState<LeadSource>('craigslist')
  const [selectedLocationIds, setSelectedLocationIds] = useState<number[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [keywords, setKeywords] = useState('')
  const [maxPages, setMaxPages] = useState(5)
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal')
  const [enableEmail, setEnableEmail] = useState(false)
  const [captchaKey, setCaptchaKey] = useState('')

  // Google Maps specific
  const [businessCategory, setBusinessCategory] = useState('')
  const [radius, setRadius] = useState(10)

  // LinkedIn specific
  const [companySize, setCompanySize] = useState('')

  // Job boards specific
  const [salaryRange, setSalaryRange] = useState('')

  const submit = () => {
    const basePayload = {
      source,
      location_ids: selectedLocationIds,
      keywords: keywords.trim() ? keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
      max_pages: maxPages,
      priority,
      enable_email_extraction: enableEmail,
      captcha_api_key: enableEmail && captchaKey.trim() ? captchaKey.trim() : undefined,
    }

    // Add source-specific fields
    let payload: any = { ...basePayload }

    if (source === 'craigslist') {
      payload.categories = categories.length ? categories : undefined
    } else if (source === 'google_maps') {
      payload.business_category = businessCategory || undefined
      payload.radius = radius
    } else if (source === 'linkedin') {
      payload.company_size = companySize || undefined
    } else if (['indeed', 'monster', 'ziprecruiter'].includes(source)) {
      payload.salary_range = salaryRange || undefined
    }

    onSubmit(payload)
  }

  const renderSourceSpecificFields = () => {
    switch (source) {
      case 'craigslist':
        return (
          <div className="card p-4">
            <h3 className="text-lg font-medium text-dark-text-primary mb-3">Categories (optional)</h3>
            <CategorySelector value={categories} onChange={setCategories} />
          </div>
        )

      case 'google_maps':
        return (
          <div className="card p-4">
            <h3 className="text-lg font-medium text-dark-text-primary mb-3">Business Search</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Business Category</label>
                <input
                  className="form-input"
                  value={businessCategory}
                  onChange={e => setBusinessCategory(e.target.value)}
                  placeholder="e.g., restaurants, plumbers, dentists"
                />
              </div>
              <div>
                <label className="form-label">Search Radius (miles)</label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  className="form-input"
                  value={radius}
                  onChange={e => setRadius(parseInt(e.target.value || '10', 10))}
                />
              </div>
            </div>
            <p className="text-xs text-dark-text-muted mt-2">
              Search for businesses on Google Maps by category and location
            </p>
          </div>
        )

      case 'linkedin':
        return (
          <div className="card p-4">
            <h3 className="text-lg font-medium text-dark-text-primary mb-3">LinkedIn Job Search</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company Size</label>
                <select
                  className="form-input"
                  value={companySize}
                  onChange={e => setCompanySize(e.target.value)}
                >
                  <option value="">Any Size</option>
                  <option value="1-10">1-10 employees</option>
                  <option value="11-50">11-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-500">201-500 employees</option>
                  <option value="501-1000">501-1000 employees</option>
                  <option value="1001-5000">1001-5000 employees</option>
                  <option value="5001+">5001+ employees</option>
                </select>
              </div>
            </div>
            <p className="text-xs text-yellow-400 mt-2">
              LinkedIn scraping requires Piloterr service integration (coming soon)
            </p>
          </div>
        )

      case 'indeed':
      case 'monster':
      case 'ziprecruiter':
        const sourceName = source.charAt(0).toUpperCase() + source.slice(1)
        return (
          <div className="card p-4">
            <h3 className="text-lg font-medium text-dark-text-primary mb-3">{sourceName} Job Search</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Salary Range</label>
                <select
                  className="form-input"
                  value={salaryRange}
                  onChange={e => setSalaryRange(e.target.value)}
                >
                  <option value="">Any Salary</option>
                  <option value="0-40000">$0 - $40,000</option>
                  <option value="40000-60000">$40,000 - $60,000</option>
                  <option value="60000-80000">$60,000 - $80,000</option>
                  <option value="80000-100000">$80,000 - $100,000</option>
                  <option value="100000-150000">$100,000 - $150,000</option>
                  <option value="150000+">$150,000+</option>
                </select>
              </div>
            </div>
            <p className="text-xs text-yellow-400 mt-2">
              {sourceName} integration coming soon in Phase 2
            </p>
          </div>
        )

      default:
        return null
    }
  }

  const isSourceEnabled = source === 'craigslist'

  return (
    <div className="space-y-6">
      {/* Source Selector */}
      <div className="card p-4">
        <h3 className="text-lg font-medium text-dark-text-primary mb-3">Lead Source</h3>
        <SourceSelector
          value={source}
          onChange={setSource}
          enabledSources={['craigslist']} // Only Craigslist enabled for now
        />
        {!isSourceEnabled && (
          <div className="mt-3 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-md">
            <p className="text-sm text-yellow-400">
              This source is not yet available. Currently only Craigslist is supported. Additional sources will be added in Phase 2.
            </p>
          </div>
        )}
      </div>

      {/* Locations */}
      <div className="card p-4">
        <h3 className="text-lg font-medium text-dark-text-primary mb-3">Locations</h3>
        <LocationSelector selectedIds={selectedLocationIds} onChange={setSelectedLocationIds} />
      </div>

      {/* Source-specific fields */}
      {renderSourceSpecificFields()}

      {/* Common Search Criteria */}
      <div className="card p-4">
        <h3 className="text-lg font-medium text-dark-text-primary mb-3">Search Criteria</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="form-label">Keywords (comma-separated)</label>
            <input
              className="form-input"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="marketing, plumbing, web design"
            />
          </div>
          <div>
            <label className="form-label">Max pages per search</label>
            <input
              type="number"
              min={1}
              max={20}
              className="form-input"
              value={maxPages}
              onChange={e => setMaxPages(parseInt(e.target.value || '1', 10))}
            />
          </div>
          <div>
            <label className="form-label">Priority</label>
            <select
              className="form-input"
              value={priority}
              onChange={e => setPriority(e.target.value as any)}
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="form-label">Email extraction</label>
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={enableEmail}
                onChange={e => setEnableEmail(e.target.checked)}
              />
              <input
                className="form-input"
                placeholder="2Captcha API key (optional)"
                value={captchaKey}
                onChange={e => setCaptchaKey(e.target.value)}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <div className="sticky bottom-0 bg-gray-900 p-4 border-t border-gray-800 rounded-md">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-200">
            {selectedLocationIds.length} location{selectedLocationIds.length !== 1 ? 's' : ''} •{' '}
            {source === 'craigslist' ? `${categories.length} categor${categories.length !== 1 ? 'ies' : 'y'}` : source.replace('_', ' ')} •{' '}
            {maxPages} page{maxPages !== 1 ? 's' : ''}
          </span>
          <button
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={submit}
            disabled={selectedLocationIds.length === 0 || !isSourceEnabled}
            title={
              selectedLocationIds.length === 0
                ? 'Select at least one location to start scraping'
                : !isSourceEnabled
                ? 'This source is not yet enabled'
                : 'Start scraping job'
            }
          >
            Start Scraping
          </button>
        </div>
        {selectedLocationIds.length === 0 && (
          <p className="text-xs text-yellow-400 mt-2">Please select at least one location to continue</p>
        )}
        {!isSourceEnabled && selectedLocationIds.length > 0 && (
          <p className="text-xs text-yellow-400 mt-2">This source is not yet enabled. Only Craigslist is currently available.</p>
        )}
      </div>
    </div>
  )
}
