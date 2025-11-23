import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MapIcon, UserGroupIcon, MapPinIcon, MagnifyingGlassIcon, ChatBubbleLeftRightIcon, GlobeAltIcon } from '@heroicons/react/24/outline'
import SourceCard from '@/components/SourceCard'
import ScrapeBuilder from '@/components/ScrapeBuilder'
import { getActiveJobs } from '@/mocks/scrapeJobs.mock'
import toast from 'react-hot-toast'

/**
 * ScraperNew - Enhanced scraper page with multi-source selection
 * Shows source cards for Craigslist, Google Maps, and LinkedIn
 */
export default function ScraperNew() {
  const navigate = useNavigate()
  const [showCraigslistForm, setShowCraigslistForm] = useState(false)

  const handleCraigslistSubmit = (payload: any) => {
    console.log('Craigslist config:', payload)
    toast.success('Craigslist scraping job started!')
    setShowCraigslistForm(false)
  }

  const activeJobs = getActiveJobs()

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-dark-text-primary">Lead Scraper</h2>
          <p className="text-sm text-dark-text-secondary mt-1">
            Scrape leads from multiple sources
          </p>
        </div>
        <Link
          to="/scraper/jobs"
          className="btn-secondary"
        >
          View All Jobs ({activeJobs.length} active)
        </Link>
      </div>

      {/* Source Selection Cards */}
      <div>
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Select Data Source</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <SourceCard
            icon={<MapPinIcon className="w-10 h-10" />}
            title="Craigslist"
            description="Local classifieds & services"
            color="#FF6600"
            enabled
            onClick={() => setShowCraigslistForm(true)}
          />

          <SourceCard
            icon={<MapIcon className="w-10 h-10" />}
            title="Google Maps"
            description="Local businesses by location"
            color="#4285F4"
            enabled
            onClick={() => navigate('/scraper/google-maps')}
          />

          <SourceCard
            icon={<UserGroupIcon className="w-10 h-10" />}
            title="LinkedIn"
            description="Professional contacts & companies"
            color="#0A66C2"
            enabled
            onClick={() => navigate('/scraper/linkedin')}
          />

          <SourceCard
            icon={<MagnifyingGlassIcon className="w-10 h-10" />}
            title="Audience Builder"
            description="Hunter.io & Apollo.io B2B data"
            color="#6C5CE7"
            enabled
            onClick={() => navigate('/scraper/audience-builder')}
          />

          <SourceCard
            icon={<ChatBubbleLeftRightIcon className="w-10 h-10" />}
            title="Social Media"
            description="Twitter, Reddit, YouTube, etc"
            color="#1DA1F2"
            enabled
            onClick={() => navigate('/scraper/social-media')}
          />

          <SourceCard
            icon={<GlobeAltIcon className="w-10 h-10" />}
            title="Custom URL"
            description="Any website with CSS selectors"
            color="#10B981"
            enabled
            onClick={() => navigate('/scraper/custom-url')}
          />
        </div>
      </div>

      {/* Craigslist Configuration Form */}
      {showCraigslistForm && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-medium text-dark-text-primary">
                📍 Configure Craigslist Scraping
              </h3>
              <p className="text-sm text-dark-text-secondary mt-1">
                Select locations, categories, and filters
              </p>
            </div>
            <button
              onClick={() => setShowCraigslistForm(false)}
              className="btn-secondary text-sm"
            >
              Cancel
            </button>
          </div>
          <ScrapeBuilder onSubmit={handleCraigslistSubmit} />
        </div>
      )}

      {/* Active Jobs Section */}
      {activeJobs.length > 0 && (
        <div className="card">
          <div className="px-6 py-4 border-b border-dark-border flex items-center justify-between">
            <h3 className="text-lg font-medium text-dark-text-primary">Active Scraping Jobs</h3>
            <Link to="/scraper/jobs" className="text-terminal-500 hover:text-terminal-400 text-sm">
              View All →
            </Link>
          </div>

          <div className="divide-y divide-dark-border">
            {activeJobs.slice(0, 3).map((job) => (
              <Link
                key={job.id}
                to={`/scraper/jobs/${job.job_id}`}
                className="block px-6 py-4 hover:bg-dark-border/30 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <code className="text-xs bg-dark-border px-2 py-1 rounded text-dark-text-primary">
                        {job.job_id}
                      </code>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        job.status === 'running' ? 'bg-blue-500/10 text-blue-500' :
                        job.status === 'queued' ? 'bg-purple-500/10 text-purple-500' :
                        'bg-gray-500/10 text-gray-500'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-dark-text-secondary">
                        {job.config.locations?.join(', ') || 'N/A'}
                      </span>
                      <span className="text-dark-text-muted">•</span>
                      <span className="text-dark-text-primary font-medium">
                        {job.leads_found} leads found
                      </span>
                    </div>
                  </div>

                  <div className="w-48 ml-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-dark-text-secondary">Progress</span>
                      <span className="text-xs font-medium text-dark-text-primary">
                        {job.progress.percentage.toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-dark-border rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${job.progress.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Info Card */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-blue-400 mb-2">Getting Started</h4>
        <ul className="text-sm text-dark-text-secondary space-y-1">
          <li>• Select a data source above to begin scraping</li>
          <li>• Configure your search parameters and filters</li>
          <li>• Enable enrichment to find contact information automatically</li>
          <li>• Monitor progress in real-time from the jobs page</li>
        </ul>
      </div>
    </div>
  )
}
