import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  GlobeAltIcon,
  ArrowLeftIcon,
  KeyIcon,
  CodeBracketIcon,
  PlusIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function CustomUrlScraper() {
  const navigate = useNavigate()

  // URL Configuration
  const [urls, setUrls] = useState<string[]>([])
  const [urlInput, setUrlInput] = useState('')

  // Scraping Configuration
  const [selectors, setSelectors] = useState({
    title: '',
    description: '',
    price: '',
    email: '',
    phone: '',
    custom: [] as Array<{key: string, selector: string}>
  })

  // Authentication
  const [authType, setAuthType] = useState<'none' | 'basic' | 'bearer' | 'cookies'>('none')
  const [authUsername, setAuthUsername] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authToken, setAuthToken] = useState('')
  const [cookies, setCookies] = useState('')

  // Advanced Options
  const [waitForSelector, setWaitForSelector] = useState('')
  const [scrollToBottom, setScrollToBottom] = useState(false)
  const [followPagination, setFollowPagination] = useState(false)
  const [paginationSelector, setPaginationSelector] = useState('')
  const [maxPages, setMaxPages] = useState(10)
  const [delayBetweenRequests, setDelayBetweenRequests] = useState(1000)
  const [userAgent, setUserAgent] = useState('')

  // Campaign Assignment
  const [assignToCampaign, setAssignToCampaign] = useState(false)
  const [selectedCampaign, setSelectedCampaign] = useState('')

  const addUrl = () => {
    const trimmed = urlInput.trim()
    if (trimmed && !urls.includes(trimmed)) {
      try {
        new URL(trimmed) // Validate URL
        setUrls([...urls, trimmed])
        setUrlInput('')
      } catch {
        toast.error('Please enter a valid URL')
      }
    }
  }

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index))
  }

  const addCustomSelector = () => {
    setSelectors({
      ...selectors,
      custom: [...selectors.custom, { key: '', selector: '' }]
    })
  }

  const updateCustomSelector = (index: number, field: 'key' | 'selector', value: string) => {
    const updated = [...selectors.custom]
    updated[index][field] = value
    setSelectors({ ...selectors, custom: updated })
  }

  const removeCustomSelector = (index: number) => {
    setSelectors({
      ...selectors,
      custom: selectors.custom.filter((_, i) => i !== index)
    })
  }

  const handleSubmit = () => {
    if (urls.length === 0) {
      toast.error('Please add at least one URL to scrape')
      return
    }

    const config = {
      urls,
      selectors,
      authentication: authType !== 'none' ? {
        type: authType,
        username: authType === 'basic' ? authUsername : undefined,
        password: authType === 'basic' ? authPassword : undefined,
        token: authType === 'bearer' ? authToken : undefined,
        cookies: authType === 'cookies' ? cookies : undefined,
      } : undefined,
      advanced: {
        waitForSelector: waitForSelector || undefined,
        scrollToBottom,
        followPagination,
        paginationSelector: followPagination ? paginationSelector : undefined,
        maxPages: followPagination ? maxPages : undefined,
        delayBetweenRequests,
        userAgent: userAgent || undefined,
      },
      campaign: assignToCampaign ? selectedCampaign : undefined,
    }

    console.log('Custom URL scraping config:', config)
    toast.success('Custom URL scraping job created!')
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
          <div className="p-3 rounded-lg bg-[#10B981]/10 border border-[#10B981]/20">
            <GlobeAltIcon className="w-8 h-8 text-[#10B981]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-dark-text-primary">Custom URL Scraper</h1>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Scrape data from any website with custom CSS selectors
            </p>
          </div>
        </div>
      </div>

      {/* Target URLs */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Target URLs</h3>
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              type="url"
              className="form-input flex-1"
              value={urlInput}
              onChange={e => setUrlInput(e.target.value)}
              onKeyPress={e => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addUrl()
                }
              }}
              placeholder="https://example.com/page"
            />
            <button onClick={addUrl} className="btn-secondary">
              <PlusIcon className="w-5 h-5" />
            </button>
          </div>

          {urls.length > 0 && (
            <div className="space-y-2">
              {urls.map((url, idx) => (
                <div key={idx} className="flex items-center gap-2 p-3 bg-dark-border/30 rounded-md">
                  <GlobeAltIcon className="w-5 h-5 text-dark-text-muted flex-shrink-0" />
                  <span className="text-sm text-dark-text-primary flex-1 truncate">{url}</span>
                  <button
                    onClick={() => removeUrl(idx)}
                    className="text-red-400 hover:text-red-300 text-lg"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* CSS Selectors */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">
          Data Extraction (CSS Selectors)
        </h3>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label">Title Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={selectors.title}
                onChange={e => setSelectors({...selectors, title: e.target.value})}
                placeholder=".post-title, h1.title"
              />
            </div>

            <div>
              <label className="form-label">Description Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={selectors.description}
                onChange={e => setSelectors({...selectors, description: e.target.value})}
                placeholder=".post-content, .description"
              />
            </div>

            <div>
              <label className="form-label">Price Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={selectors.price}
                onChange={e => setSelectors({...selectors, price: e.target.value})}
                placeholder=".price, [itemprop='price']"
              />
            </div>

            <div>
              <label className="form-label">Email Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={selectors.email}
                onChange={e => setSelectors({...selectors, email: e.target.value})}
                placeholder="a[href^='mailto:']"
              />
            </div>

            <div>
              <label className="form-label">Phone Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={selectors.phone}
                onChange={e => setSelectors({...selectors, phone: e.target.value})}
                placeholder="a[href^='tel:'], .phone"
              />
            </div>
          </div>

          {/* Custom Selectors */}
          <div className="pt-4 border-t border-dark-border">
            <div className="flex items-center justify-between mb-3">
              <label className="form-label mb-0">Custom Fields</label>
              <button onClick={addCustomSelector} className="btn-secondary text-sm">
                <PlusIcon className="w-4 h-4 mr-1" />
                Add Field
              </button>
            </div>

            {selectors.custom.length > 0 && (
              <div className="space-y-2">
                {selectors.custom.map((field, idx) => (
                  <div key={idx} className="flex gap-2">
                    <input
                      type="text"
                      className="form-input flex-1"
                      value={field.key}
                      onChange={e => updateCustomSelector(idx, 'key', e.target.value)}
                      placeholder="Field name (e.g., rating)"
                    />
                    <input
                      type="text"
                      className="form-input flex-1 font-mono text-sm"
                      value={field.selector}
                      onChange={e => updateCustomSelector(idx, 'selector', e.target.value)}
                      placeholder="CSS selector"
                    />
                    <button
                      onClick={() => removeCustomSelector(idx)}
                      className="btn-secondary text-red-400 hover:text-red-300"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Authentication */}
      <div className="card-terminal p-6">
        <div className="flex items-center gap-2 mb-4">
          <KeyIcon className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-medium text-dark-text-primary">Authentication</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="form-label">Authentication Type</label>
            <select
              className="form-input"
              value={authType}
              onChange={e => setAuthType(e.target.value as any)}
            >
              <option value="none">None (Public)</option>
              <option value="basic">Basic Auth (Username/Password)</option>
              <option value="bearer">Bearer Token (API Key)</option>
              <option value="cookies">Cookies</option>
            </select>
          </div>

          {authType === 'basic' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Username</label>
                <input
                  type="text"
                  className="form-input"
                  value={authUsername}
                  onChange={e => setAuthUsername(e.target.value)}
                />
              </div>
              <div>
                <label className="form-label">Password</label>
                <input
                  type="password"
                  className="form-input"
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                />
              </div>
            </div>
          )}

          {authType === 'bearer' && (
            <div>
              <label className="form-label">Bearer Token / API Key</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={authToken}
                onChange={e => setAuthToken(e.target.value)}
                placeholder="your-api-key-here"
              />
            </div>
          )}

          {authType === 'cookies' && (
            <div>
              <label className="form-label">Cookies (JSON format)</label>
              <textarea
                className="form-input font-mono text-sm"
                rows={4}
                value={cookies}
                onChange={e => setCookies(e.target.value)}
                placeholder='{"session_id": "abc123", "token": "xyz789"}'
              />
            </div>
          )}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="card-terminal p-6">
        <div className="flex items-center gap-2 mb-4">
          <CodeBracketIcon className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-medium text-dark-text-primary">Advanced Options</h3>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label">Wait for Selector</label>
              <input
                type="text"
                className="form-input font-mono text-sm"
                value={waitForSelector}
                onChange={e => setWaitForSelector(e.target.value)}
                placeholder=".content-loaded"
              />
              <p className="text-xs text-dark-text-muted mt-1">
                Wait for this element before scraping
              </p>
            </div>

            <div>
              <label className="form-label">User Agent</label>
              <input
                type="text"
                className="form-input text-sm"
                value={userAgent}
                onChange={e => setUserAgent(e.target.value)}
                placeholder="Leave empty for default"
              />
            </div>

            <div>
              <label className="form-label">Delay Between Requests (ms)</label>
              <input
                type="number"
                min={0}
                max={10000}
                step={100}
                className="form-input"
                value={delayBetweenRequests}
                onChange={e => setDelayBetweenRequests(parseInt(e.target.value || '1000', 10))}
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={scrollToBottom}
                onChange={e => setScrollToBottom(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm text-dark-text-primary">Scroll to bottom (for lazy loading)</span>
            </label>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={followPagination}
                onChange={e => setFollowPagination(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm text-dark-text-primary">Follow Pagination</span>
            </label>

            {followPagination && (
              <div className="ml-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="form-label">Next Page Selector</label>
                  <input
                    type="text"
                    className="form-input font-mono text-sm"
                    value={paginationSelector}
                    onChange={e => setPaginationSelector(e.target.value)}
                    placeholder="a.next-page, .pagination .next"
                  />
                </div>
                <div>
                  <label className="form-label">Max Pages</label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    className="form-input"
                    value={maxPages}
                    onChange={e => setMaxPages(parseInt(e.target.value || '10', 10))}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Campaign Assignment */}
      <div className="card-terminal p-6">
        <h3 className="text-lg font-medium text-dark-text-primary mb-4">Campaign Assignment</h3>
        <div className="space-y-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={assignToCampaign}
              onChange={e => setAssignToCampaign(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-dark-text-primary">
              Automatically assign scraped leads to a campaign
            </span>
          </label>

          {assignToCampaign && (
            <div>
              <label className="form-label">Select Campaign</label>
              <select
                className="form-input"
                value={selectedCampaign}
                onChange={e => setSelectedCampaign(e.target.value)}
              >
                <option value="">Choose a campaign...</option>
                <option value="1">Q1 Outreach Campaign</option>
                <option value="2">Product Launch - Tech Leads</option>
                <option value="3">Real Estate Investors</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-blue-400 mb-2">CSS Selector Tips</h4>
        <ul className="text-sm text-dark-text-secondary space-y-1">
          <li>• Use browser DevTools to find selectors (right-click → Inspect)</li>
          <li>• Be as specific as possible to avoid extracting wrong data</li>
          <li>• Test selectors on a single page first before scraping multiple URLs</li>
          <li>• Use <code className="text-terminal-400">.class</code> for classes, <code className="text-terminal-400">#id</code> for IDs</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="sticky bottom-0 bg-dark-surface/95 backdrop-blur-sm p-6 border-t border-dark-border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="text-sm text-dark-text-secondary">
            {urls.length} URL{urls.length !== 1 ? 's' : ''} configured
            {assignToCampaign && selectedCampaign && ' • Campaign assigned'}
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/scraper')} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={urls.length === 0}
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
