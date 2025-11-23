import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import LocationSelector from '@/components/LocationSelector'
import toast from 'react-hot-toast'

export default function GoogleMapsScraper() {
  const navigate = useNavigate()
  const [selectedLocationIds, setSelectedLocationIds] = useState<number[]>([])
  const [businessCategory, setBusinessCategory] = useState('')
  const [radius, setRadius] = useState(10)
  const [keywords, setKeywords] = useState('')
  const [maxResults, setMaxResults] = useState(50)
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal')
  const [enableEnrichment, setEnableEnrichment] = useState(false)

  const handleSubmit = () => {
    if (selectedLocationIds.length === 0) {
      toast.error('Please select at least one location')
      return
    }

    if (!businessCategory.trim()) {
      toast.error('Please enter a business category')
      return
    }

    const payload = {
      source: 'google_maps',
      location_ids: selectedLocationIds,
      business_category: businessCategory.trim(),
      radius,
      keywords: keywords.trim() ? keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
      max_results: maxResults,
      priority,
      enable_enrichment: enableEnrichment,
    }

    console.log('Google Maps scraping job:', payload)
    toast.success('Google Maps scraping job created successfully!')

    // Navigate back to scraper page or jobs list
    setTimeout(() => navigate('/scraper/jobs'), 1500)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/scraper')}
          className="p-2 rounded-md text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-[#4285F4]/10 border border-[#4285F4]/20">
            <MapIcon className="w-8 h-8 text-[#4285F4]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-dark-text-primary">Google Maps Scraper</h1>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Find local businesses by location and category
            </p>
          </div>
        </div>
      </div>

      {/* Locations */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Target Locations</h3>
        <LocationSelector selectedIds={selectedLocationIds} onChange={setSelectedLocationIds} />
        <p className="text-xs text-dark-text-muted mt-3">
          Select one or more locations to search for businesses
        </p>
      </div>

      {/* Business Search Criteria */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Business Search</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">
              Business Category <span className="text-red-400">*</span>
            </label>
            <input
              className="form-input"
              value={businessCategory}
              onChange={e => setBusinessCategory(e.target.value)}
              placeholder="e.g., restaurants, plumbers, dentists, real estate agents"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              The type of business you want to find
            </p>
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
            <p className="text-xs text-dark-text-muted mt-1">
              How far from the location to search (1-50 miles)
            </p>
          </div>

          <div className="md:col-span-2">
            <label className="form-label">Additional Keywords (optional)</label>
            <input
              className="form-input"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="luxury, affordable, 24/7, emergency"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Comma-separated keywords to refine your search
            </p>
          </div>
        </div>
      </div>

      {/* Scraping Settings */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Scraping Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="form-label">Max Results per Location</label>
            <input
              type="number"
              min={10}
              max={500}
              step={10}
              className="form-input"
              value={maxResults}
              onChange={e => setMaxResults(parseInt(e.target.value || '50', 10))}
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Maximum businesses to scrape per location
            </p>
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
            <p className="text-xs text-dark-text-muted mt-1">
              Job queue priority
            </p>
          </div>

          <div>
            <label className="form-label">Contact Enrichment</label>
            <label className="flex items-center gap-3 p-3 bg-dark-border/30 rounded-md cursor-pointer hover:bg-dark-border/50 transition-colors">
              <input
                type="checkbox"
                checked={enableEnrichment}
                onChange={e => setEnableEnrichment(e.target.checked)}
                className="w-4 h-4"
              />
              <div>
                <div className="text-sm font-medium text-dark-text-primary">
                  Enable enrichment
                </div>
                <div className="text-xs text-dark-text-muted">
                  Find emails & phone numbers
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-blue-400 mb-2">How Google Maps Scraping Works</h4>
        <ul className="text-sm text-dark-text-secondary space-y-2">
          <li>• Searches Google Maps for businesses matching your category in selected locations</li>
          <li>• Extracts business name, address, phone, website, rating, and review count</li>
          <li>• Optional enrichment finds additional contact information</li>
          <li>• Results are saved as leads and can be used in campaigns</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="sticky bottom-0 bg-dark-surface/95 backdrop-blur-sm p-6 border-t border-dark-border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="text-sm text-dark-text-secondary">
            {selectedLocationIds.length} location{selectedLocationIds.length !== 1 ? 's' : ''} selected
            {businessCategory && ` • ${businessCategory}`}
            {` • Up to ${maxResults * selectedLocationIds.length} results`}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/scraper')}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={selectedLocationIds.length === 0 || !businessCategory.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Scraping
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
