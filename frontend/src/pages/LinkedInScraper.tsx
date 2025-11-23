import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserGroupIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import LocationSelector from '@/components/LocationSelector'
import toast from 'react-hot-toast'

export default function LinkedInScraper() {
  const navigate = useNavigate()
  const [selectedLocationIds, setSelectedLocationIds] = useState<number[]>([])
  const [jobTitle, setJobTitle] = useState('')
  const [companySize, setCompanySize] = useState('')
  const [industry, setIndustry] = useState('')
  const [keywords, setKeywords] = useState('')
  const [maxResults, setMaxResults] = useState(100)
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal')
  const [includeProfiles, setIncludeProfiles] = useState(true)

  const handleSubmit = () => {
    if (selectedLocationIds.length === 0) {
      toast.error('Please select at least one location')
      return
    }

    if (!jobTitle.trim() && !industry.trim()) {
      toast.error('Please enter a job title or industry')
      return
    }

    const payload = {
      source: 'linkedin',
      location_ids: selectedLocationIds,
      job_title: jobTitle.trim() || undefined,
      company_size: companySize || undefined,
      industry: industry.trim() || undefined,
      keywords: keywords.trim() ? keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
      max_results: maxResults,
      priority,
      include_profiles: includeProfiles,
    }

    console.log('LinkedIn scraping job:', payload)
    toast.success('LinkedIn scraping job created successfully!')

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
          <div className="p-3 rounded-lg bg-[#0A66C2]/10 border border-[#0A66C2]/20">
            <UserGroupIcon className="w-8 h-8 text-[#0A66C2]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-dark-text-primary">LinkedIn Scraper</h1>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Find professional contacts and companies on LinkedIn
            </p>
          </div>
        </div>
      </div>

      {/* Service Integration Notice */}
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-yellow-400 mb-2">
          LinkedIn Integration via Piloterr
        </h4>
        <p className="text-sm text-dark-text-secondary">
          LinkedIn scraping requires integration with the Piloterr service for reliable data extraction.
          This feature is currently in development and will be available soon.
        </p>
      </div>

      {/* Locations */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Target Locations</h3>
        <LocationSelector selectedIds={selectedLocationIds} onChange={setSelectedLocationIds} />
        <p className="text-xs text-dark-text-muted mt-3">
          Select one or more locations to search for LinkedIn profiles and jobs
        </p>
      </div>

      {/* Search Criteria */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Search Criteria</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">Job Title</label>
            <input
              className="form-input"
              value={jobTitle}
              onChange={e => setJobTitle(e.target.value)}
              placeholder="e.g., Marketing Manager, Software Engineer"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              The job title to search for
            </p>
          </div>

          <div>
            <label className="form-label">Industry</label>
            <input
              className="form-input"
              value={industry}
              onChange={e => setIndustry(e.target.value)}
              placeholder="e.g., Technology, Healthcare, Finance"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Industry or business sector
            </p>
          </div>

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
            <p className="text-xs text-dark-text-muted mt-1">
              Filter by company size
            </p>
          </div>

          <div>
            <label className="form-label">Additional Keywords (optional)</label>
            <input
              className="form-input"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="remote, hiring, startup"
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Comma-separated keywords to refine search
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
              onChange={e => setMaxResults(parseInt(e.target.value || '100', 10))}
            />
            <p className="text-xs text-dark-text-muted mt-1">
              Maximum profiles to scrape per location
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
            <label className="form-label">Profile Scraping</label>
            <label className="flex items-center gap-3 p-3 bg-dark-border/30 rounded-md cursor-pointer hover:bg-dark-border/50 transition-colors">
              <input
                type="checkbox"
                checked={includeProfiles}
                onChange={e => setIncludeProfiles(e.target.checked)}
                className="w-4 h-4"
              />
              <div>
                <div className="text-sm font-medium text-dark-text-primary">
                  Include profiles
                </div>
                <div className="text-xs text-dark-text-muted">
                  Scrape individual profiles
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-blue-400 mb-2">How LinkedIn Scraping Works</h4>
        <ul className="text-sm text-dark-text-secondary space-y-2">
          <li>• Searches LinkedIn for profiles and jobs matching your criteria</li>
          <li>• Extracts professional information: name, title, company, location</li>
          <li>• Can include company details like size, industry, and website</li>
          <li>• Results are saved as leads for outreach campaigns</li>
          <li>• Respects LinkedIn's terms of service and rate limits</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="sticky bottom-0 bg-dark-surface/95 backdrop-blur-sm p-6 border-t border-dark-border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="text-sm text-dark-text-secondary">
            {selectedLocationIds.length} location{selectedLocationIds.length !== 1 ? 's' : ''} selected
            {jobTitle && ` • ${jobTitle}`}
            {industry && ` • ${industry}`}
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
              disabled={selectedLocationIds.length === 0 || (!jobTitle.trim() && !industry.trim())}
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
