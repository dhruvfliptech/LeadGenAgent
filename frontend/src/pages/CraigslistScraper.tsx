import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPinIcon, ArrowLeftIcon, MagnifyingGlassIcon, TagIcon } from '@heroicons/react/24/outline'
import { api } from '@/services/api'
import toast from 'react-hot-toast'

interface Location {
  id: number
  name: string
  code: string
  url: string
  state?: string
  country?: string
  region?: string
}

interface Category {
  name: string
  slug: string
}

interface CategoryGroup {
  [group: string]: Category[]
}

// Helper to normalize category data from API
function normalizeCategories(data: Record<string, string[] | Category[]>): CategoryGroup {
  const normalized: CategoryGroup = {}
  for (const [group, items] of Object.entries(data)) {
    if (items.length === 0) continue
    // Check if items are strings or objects
    if (typeof items[0] === 'string') {
      // Convert strings to Category objects
      normalized[group] = (items as string[]).map(item => ({
        name: item.charAt(0).toUpperCase() + item.slice(1), // Capitalize first letter
        slug: item.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
      }))
    } else {
      normalized[group] = items as Category[]
    }
  }
  return normalized
}

export default function CraigslistScraper() {
  const navigate = useNavigate()

  // Location state
  const [locations, setLocations] = useState<Location[]>([])
  const [selectedLocationIds, setSelectedLocationIds] = useState<number[]>([])
  const [locationSearch, setLocationSearch] = useState('')

  // Category state
  const [categories, setCategories] = useState<CategoryGroup>({})
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})

  // Search options
  const [keywords, setKeywords] = useState('')
  const [maxPages, setMaxPages] = useState(5)
  const [enableEmailExtraction, setEnableEmailExtraction] = useState(false)
  const [captchaApiKey, setCaptchaApiKey] = useState('')
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal')

  const [isLoading, setIsLoading] = useState(false)

  // Load locations on mount
  useEffect(() => {
    const loadLocations = async () => {
      try {
        const response = await api.get('/locations/')
        // Filter to only show Craigslist locations (not Google Maps places)
        const craigslistLocations = (response.data || []).filter(
          (loc: Location) => loc.url?.includes('craigslist.org')
        )
        setLocations(craigslistLocations)
      } catch (error) {
        console.error('Failed to load locations:', error)
        // Use some default locations (IDs match typical database entries)
        setLocations([
          { id: 4, name: 'San Francisco Bay Area', code: 'sfbay', url: 'https://sfbay.craigslist.org', state: 'CA', country: 'US', region: 'US' },
          { id: 5, name: 'Los Angeles', code: 'losangeles', url: 'https://losangeles.craigslist.org', state: 'CA', country: 'US', region: 'US' },
          { id: 6, name: 'New York City', code: 'newyork', url: 'https://newyork.craigslist.org', state: 'NY', country: 'US', region: 'US' },
        ])
      }
    }
    loadLocations()
  }, [])

  // Load categories on mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        // Try structured endpoint first (returns {name, slug} objects)
        const response = await api.get('/scraper/categories/structured')
        const data = response.data || {}
        setCategories(data)
        // Default expand the first category group
        const firstGroup = Object.keys(data)[0]
        if (firstGroup) {
          setExpandedGroups({ [firstGroup]: true })
        }
      } catch (error) {
        console.error('Failed to load structured categories, trying fallback:', error)
        try {
          // Fallback to regular categories endpoint (returns string arrays)
          const response = await api.get('/scraper/categories')
          const normalized = normalizeCategories(response.data || {})
          setCategories(normalized)
          const firstGroup = Object.keys(normalized)[0]
          if (firstGroup) {
            setExpandedGroups({ [firstGroup]: true })
          }
        } catch (fallbackError) {
          console.error('Failed to load categories:', fallbackError)
          // Use default categories
          const defaults: CategoryGroup = {
            'gigs': [
              { name: 'Computer Gigs', slug: 'computer' },
              { name: 'Creative Gigs', slug: 'creative' },
              { name: 'Event Gigs', slug: 'event' },
              { name: 'Labor Gigs', slug: 'labor' },
              { name: 'Talent Gigs', slug: 'talent' },
              { name: 'Writing Gigs', slug: 'writing' },
              { name: 'Domestic Gigs', slug: 'domestic' },
            ],
            'jobs': [
              { name: 'Accounting/Finance', slug: 'accounting-finance' },
              { name: 'Admin/Office', slug: 'admin-office' },
              { name: 'Software/QA/DBA', slug: 'software-qa-dba' },
              { name: 'Web/Info Design', slug: 'web-info-design' },
              { name: 'Sales/Business Dev', slug: 'sales-biz-dev' },
              { name: 'Marketing/PR/Ad', slug: 'marketing-pr-ad' },
            ],
            'services': [
              { name: 'Automotive', slug: 'automotive' },
              { name: 'Computer', slug: 'computer' },
              { name: 'Creative', slug: 'creative' },
              { name: 'Financial', slug: 'financial' },
              { name: 'Legal', slug: 'legal' },
            ],
          }
          setCategories(defaults)
          setExpandedGroups({ 'gigs': true })
        }
      }
    }
    loadCategories()
  }, [])

  // Filter locations based on search
  const filteredLocations = locations.filter(loc =>
    loc.name.toLowerCase().includes(locationSearch.toLowerCase()) ||
    loc.code.toLowerCase().includes(locationSearch.toLowerCase()) ||
    (loc.state && loc.state.toLowerCase().includes(locationSearch.toLowerCase()))
  )

  // Toggle location selection
  const toggleLocation = (id: number) => {
    setSelectedLocationIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  // Toggle category selection
  const toggleCategory = (slug: string) => {
    setSelectedCategories(prev =>
      prev.includes(slug) ? prev.filter(x => x !== slug) : [...prev, slug]
    )
  }

  // Toggle category group expansion
  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }))
  }

  // Select all in group
  const selectAllInGroup = (group: string) => {
    const slugs = (categories[group] || []).map(c => c.slug)
    setSelectedCategories(prev => Array.from(new Set([...prev, ...slugs])))
  }

  // Clear group
  const clearGroup = (group: string) => {
    const slugs = new Set((categories[group] || []).map(c => c.slug))
    setSelectedCategories(prev => prev.filter(s => !slugs.has(s)))
  }

  const handleSubmit = async () => {
    if (selectedLocationIds.length === 0) {
      toast.error('Please select at least one location')
      return
    }

    setIsLoading(true)

    try {
      const payload = {
        location_ids: selectedLocationIds,
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        keywords: keywords.trim() ? keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        max_pages: maxPages,
        priority,
        enable_email_extraction: enableEmailExtraction,
        captcha_api_key: enableEmailExtraction && captchaApiKey.trim() ? captchaApiKey.trim() : undefined,
      }

      console.log('Submitting scrape job with payload:', payload)
      const response = await api.post('/scraper/jobs', payload)
      console.log('Scrape job response:', response.data)
      const jobId = response.data.job_id

      toast.success(
        `Craigslist scraping job started! Job ID: ${jobId}`,
        { duration: 5000 }
      )

      // Navigate to scraper jobs page
      setTimeout(() => navigate('/scraper/jobs'), 2000)
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
          <div className="p-3 rounded-lg bg-[#FF6600]/10 border border-[#FF6600]/20">
            <MapPinIcon className="w-8 h-8 text-[#FF6600]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-dark-text-primary">Craigslist Scraper</h1>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Scrape local classifieds, gigs, and services from Craigslist
            </p>
          </div>
        </div>
      </div>

      {/* Locations */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Target Locations</h3>
        <div className="relative mb-4">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-text-muted" />
          <input
            type="text"
            className="form-input pl-10"
            value={locationSearch}
            onChange={(e) => setLocationSearch(e.target.value)}
            placeholder="Search cities... (e.g., San Francisco, Los Angeles)"
          />
        </div>

        <div className="max-h-64 overflow-y-auto border border-dark-border rounded-lg">
          {filteredLocations.length > 0 ? (
            <div className="divide-y divide-dark-border">
              {filteredLocations.slice(0, 50).map((loc) => (
                <label
                  key={loc.id}
                  className="flex items-center gap-3 p-3 hover:bg-dark-border/30 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedLocationIds.includes(loc.id)}
                    onChange={() => toggleLocation(loc.id)}
                    className="w-4 h-4 rounded border-dark-border"
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-dark-text-primary">{loc.name}</div>
                    <div className="text-xs text-dark-text-muted">
                      {loc.state && `${loc.state}, `}{loc.country || loc.region}
                    </div>
                  </div>
                  <code className="text-xs bg-dark-border px-2 py-1 rounded text-dark-text-secondary">
                    {loc.code}
                  </code>
                </label>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-dark-text-muted">
              No locations found matching "{locationSearch}"
            </div>
          )}
        </div>

        <p className="text-xs text-dark-text-muted mt-3">
          Selected: <span className="text-terminal-500 font-mono">{selectedLocationIds.length} locations</span>
        </p>
      </div>

      {/* Categories */}
      <div className="card-terminal p-6">
        <div className="flex items-center gap-2 mb-4">
          <TagIcon className="w-5 h-5 text-dark-text-secondary" />
          <h3 className="text-lg font-medium text-dark-text-primary">Categories</h3>
        </div>

        <div className="space-y-3">
          {Object.entries(categories).map(([group, items]) => (
            <div key={group} className="border border-dark-border rounded-lg overflow-hidden">
              <div className="flex items-center justify-between p-3 bg-dark-surface">
                <button
                  className="flex items-center gap-2 text-left font-medium text-terminal-400"
                  onClick={() => toggleGroup(group)}
                >
                  <span className="inline-block w-4 text-center">
                    {expandedGroups[group] ? '▾' : '▸'}
                  </span>
                  {group}
                  <span className="text-xs text-dark-text-muted">
                    ({items.filter(i => selectedCategories.includes(i.slug)).length}/{items.length})
                  </span>
                </button>
                <div className="flex gap-2">
                  <button
                    className="text-xs text-terminal-500 hover:text-terminal-400"
                    onClick={() => selectAllInGroup(group)}
                  >
                    Select All
                  </button>
                  <button
                    className="text-xs text-dark-text-muted hover:text-dark-text-secondary"
                    onClick={() => clearGroup(group)}
                  >
                    Clear
                  </button>
                </div>
              </div>

              {expandedGroups[group] && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 p-3 bg-dark-bg">
                  {items.map((cat) => (
                    <label
                      key={cat.slug}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:text-dark-text-primary transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedCategories.includes(cat.slug)}
                        onChange={() => toggleCategory(cat.slug)}
                        className="w-4 h-4 rounded"
                      />
                      <span className={selectedCategories.includes(cat.slug) ? 'text-dark-text-primary' : 'text-dark-text-secondary'}>
                        {cat.name}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="text-xs text-dark-text-muted mt-3">
          Selected: <span className="text-terminal-500 font-mono">{selectedCategories.length} categories</span>
        </p>
      </div>

      {/* Search Criteria */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Search Criteria</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="form-label">Keywords (optional)</label>
            <input
              className="form-input"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="e.g., marketing, web design, plumbing (comma-separated)"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Comma-separated keywords to filter listings
            </p>
          </div>

          <div>
            <label className="form-label">Max Pages per Category</label>
            <input
              type="number"
              min={1}
              max={20}
              className="form-input"
              value={maxPages}
              onChange={e => setMaxPages(parseInt(e.target.value || '5', 10))}
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Each page contains ~120 listings (1-20 pages)
            </p>
          </div>

          <div>
            <label className="form-label">Priority</label>
            <select
              className="form-input"
              value={priority}
              onChange={e => setPriority(e.target.value as any)}
            >
              <option value="low">Low - Background processing</option>
              <option value="normal">Normal - Standard queue</option>
              <option value="high">High - Priority processing</option>
            </select>
          </div>
        </div>
      </div>

      {/* Email Extraction */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Email Extraction</h3>
        <div className="space-y-4">
          <label className="flex items-center gap-3 p-3 bg-dark-border/30 rounded-md cursor-pointer hover:bg-dark-border/50 transition-colors">
            <input
              type="checkbox"
              checked={enableEmailExtraction}
              onChange={e => setEnableEmailExtraction(e.target.checked)}
              className="w-4 h-4"
            />
            <div>
              <div className="text-sm font-medium text-dark-text-primary">
                Enable Email Extraction
              </div>
              <div className="text-xs text-dark-text-muted">
                Extract contact emails from listings (requires CAPTCHA solving)
              </div>
            </div>
          </label>

          {enableEmailExtraction && (
            <div>
              <label className="form-label">2Captcha API Key</label>
              <input
                type="password"
                className="form-input"
                value={captchaApiKey}
                onChange={e => setCaptchaApiKey(e.target.value)}
                placeholder="Your 2captcha.com API key"
              />
              <p className="text-xs text-dark-text-muted mt-1">
                Required for solving CAPTCHAs during email extraction (~$2.99 per 1000 CAPTCHAs)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-orange-400 mb-2">How Craigslist Scraping Works</h4>
        <ul className="text-sm text-dark-text-secondary space-y-2">
          <li>1. Scrapes listings from selected locations and categories</li>
          <li>2. Extracts title, price, description, and contact information</li>
          <li>3. Optionally extracts emails (requires CAPTCHA solving)</li>
          <li>4. Results are saved as leads and can be used in campaigns</li>
          <li>5. Includes rate limiting to avoid being blocked</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="sticky bottom-0 bg-dark-surface/95 backdrop-blur-sm p-6 border-t border-dark-border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="text-sm text-dark-text-secondary">
            {selectedLocationIds.length} location{selectedLocationIds.length !== 1 ? 's' : ''} |{' '}
            {selectedCategories.length} categor{selectedCategories.length !== 1 ? 'ies' : 'y'} |{' '}
            {maxPages} page{maxPages !== 1 ? 's' : ''} |{' '}
            ~{selectedLocationIds.length * selectedCategories.length * maxPages * 120} potential leads
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
              disabled={selectedLocationIds.length === 0 || isLoading}
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
