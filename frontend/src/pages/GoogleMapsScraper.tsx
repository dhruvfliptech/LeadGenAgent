import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapIcon, ArrowLeftIcon, MapPinIcon } from '@heroicons/react/24/outline'
import { googleMapsApi } from '@/services/api'
import toast from 'react-hot-toast'

export default function GoogleMapsScraper() {
  const navigate = useNavigate()
  const [location, setLocation] = useState('vancouver')
  const [businessCategory, setBusinessCategory] = useState('')
  const [maxResults, setMaxResults] = useState(20)
  const [extractEmails, setExtractEmails] = useState(true)
  const [usePlacesAPI, setUsePlacesAPI] = useState(true) // Use Google Places API by default
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async () => {
    if (!location.trim()) {
      toast.error('Please enter a location')
      return
    }

    if (!businessCategory.trim()) {
      toast.error('Please enter a business category')
      return
    }

    setIsLoading(true)

    try {
      const response = await googleMapsApi.startScrape({
        query: businessCategory.trim(),
        location: location.trim(),
        max_results: maxResults,
        extract_emails: extractEmails,
        use_places_api: usePlacesAPI, // Use Google Places API (reliable)
      })

      const jobId = response.data.job_id
      const estimatedTime = response.data.estimated_time_seconds

      toast.success(
        `Google Maps scraping job started! Estimated time: ${Math.ceil(estimatedTime / 60)} minutes`,
        { duration: 5000 }
      )

      console.log('Job started:', response.data)

      // Navigate to scraper jobs page
      setTimeout(() => navigate('/scraper'), 2000)
    } catch (error: any) {
      console.error('Failed to start scraping:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start scraping job'
      toast.error(errorMessage)
    } finally {
      setIsLoading(false)
    }
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

      {/* Location */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Target Locations</h3>
        <div className="relative">
          <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
          <input
            type="text"
            className="form-input pl-10"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g., San Francisco, CA or New York, NY or Vancouver"
          />
        </div>
        <p className="text-xs text-dark-text-muted mt-3">
          Selected: <span className="text-terminal-500 font-mono">{location || '0 locations'}</span> • Select one or more locations to search for businesses
        </p>
      </div>

      {/* Business Search Criteria */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Business Search</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
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
              value={10}
              disabled
            />
            <p className="text-xs text-dark-text-muted mt-1">
              How far from the location to search (1-50 miles)
            </p>
          </div>

          <div>
            <label className="form-label">Additional Keywords (optional)</label>
            <input
              className="form-input"
              placeholder="luxury, affordable, 24/7, emergency"
              disabled
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">Max Results</label>
            <input
              type="number"
              min={5}
              max={100}
              step={5}
              className="form-input"
              value={maxResults}
              onChange={e => setMaxResults(parseInt(e.target.value || '20', 10))}
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Maximum businesses to scrape (5-100, recommended: 20)
            </p>
          </div>

          <div>
            <label className="form-label">Scraping Method</label>
            <label className="flex items-center gap-3 p-3 bg-dark-border/30 rounded-md cursor-pointer hover:bg-dark-border/50 transition-colors">
              <input
                type="checkbox"
                checked={usePlacesAPI}
                onChange={e => setUsePlacesAPI(e.target.checked)}
                className="w-4 h-4"
              />
              <div>
                <div className="text-sm font-medium text-dark-text-primary">
                  Use Google Places API
                </div>
                <div className="text-xs text-dark-text-muted">
                  Official Google API - Most reliable (recommended)
                </div>
              </div>
            </label>
          </div>

          <div className="md:col-span-2">
            <label className="form-label">Email Extraction</label>
            <label className="flex items-center gap-3 p-3 bg-dark-border/30 rounded-md cursor-pointer hover:bg-dark-border/50 transition-colors">
              <input
                type="checkbox"
                checked={extractEmails}
                onChange={e => setExtractEmails(e.target.checked)}
                className="w-4 h-4"
              />
              <div>
                <div className="text-sm font-medium text-dark-text-primary">
                  Extract emails from websites
                </div>
                <div className="text-xs text-dark-text-muted">
                  Visits business websites to find contact emails (~5s per business)
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
            {location ? `${location}` : '0 locations selected'}
            {businessCategory && ` • ${businessCategory}`}
            {` • Up to ${maxResults} results`}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/scraper')}
              className="btn-secondary"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!location.trim() || !businessCategory.trim() || isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Starting...' : 'Start Scraping'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
