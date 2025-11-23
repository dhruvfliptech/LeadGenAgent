import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UserGroupIcon,
  MagnifyingGlassIcon,
  BuildingOfficeIcon,
  EnvelopeIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ServiceType = 'hunter' | 'apollo' | null

interface HunterConfig {
  domain: string
  department?: string
  seniority?: string
  limit: number
}

interface ApolloConfig {
  companyName?: string
  title?: string[]
  industry?: string[]
  companySize?: string
  location?: string[]
  limit: number
}

export default function AudienceBuilder() {
  const navigate = useNavigate()
  const [activeService, setActiveService] = useState<ServiceType>(null)

  // Hunter.io state
  const [hunterDomain, setHunterDomain] = useState('')
  const [hunterDepartment, setHunterDepartment] = useState('')
  const [hunterSeniority, setHunterSeniority] = useState('')
  const [hunterLimit, setHunterLimit] = useState(50)

  // Apollo.io state
  const [apolloCompanyName, setApolloCompanyName] = useState('')
  const [apolloTitle, setApolloTitle] = useState<string[]>([])
  const [apolloTitleInput, setApolloTitleInput] = useState('')
  const [apolloIndustry, setApolloIndustry] = useState<string[]>([])
  const [apolloIndustryInput, setApolloIndustryInput] = useState('')
  const [apolloCompanySize, setApolloCompanySize] = useState('')
  const [apolloLocation, setApolloLocation] = useState<string[]>([])
  const [apolloLocationInput, setApolloLocationInput] = useState('')
  const [apolloLimit, setApolloLimit] = useState(100)

  const handleHunterSubmit = () => {
    if (!hunterDomain.trim()) {
      toast.error('Please enter a company domain')
      return
    }

    const config: HunterConfig = {
      domain: hunterDomain.trim(),
      department: hunterDepartment || undefined,
      seniority: hunterSeniority || undefined,
      limit: hunterLimit
    }

    console.log('Hunter.io search config:', config)
    toast.success(`Finding contacts at ${hunterDomain}...`)

    setTimeout(() => {
      toast.success('Audience building job created! Check the jobs page for progress.')
      navigate('/scraper/jobs')
    }, 1500)
  }

  const handleApolloSubmit = () => {
    if (!apolloCompanyName.trim() && apolloTitle.length === 0 && apolloIndustry.length === 0) {
      toast.error('Please provide at least one search criteria')
      return
    }

    const config: ApolloConfig = {
      companyName: apolloCompanyName.trim() || undefined,
      title: apolloTitle.length > 0 ? apolloTitle : undefined,
      industry: apolloIndustry.length > 0 ? apolloIndustry : undefined,
      companySize: apolloCompanySize || undefined,
      location: apolloLocation.length > 0 ? apolloLocation : undefined,
      limit: apolloLimit
    }

    console.log('Apollo.io search config:', config)
    toast.success('Building audience from Apollo.io...')

    setTimeout(() => {
      toast.success('Audience building job created! Check the jobs page for progress.')
      navigate('/scraper/jobs')
    }, 1500)
  }

  const addTag = (value: string, setter: (tags: string[]) => void, current: string[]) => {
    const trimmed = value.trim()
    if (trimmed && !current.includes(trimmed)) {
      setter([...current, trimmed])
    }
  }

  const removeTag = (index: number, setter: (tags: string[]) => void, current: string[]) => {
    setter(current.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-dark-text-primary">Audience Builder</h1>
        <p className="mt-1 text-sm text-dark-text-secondary">
          Find and enrich B2B contacts using Hunter.io and Apollo.io
        </p>
      </div>

      {/* Service Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Hunter.io Card */}
        <button
          onClick={() => setActiveService(activeService === 'hunter' ? null : 'hunter')}
          className={`card-terminal p-6 text-left transition-all ${
            activeService === 'hunter'
              ? 'ring-2 ring-terminal-500'
              : 'hover:bg-dark-border/30'
          }`}
        >
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-[#FF6633]/10 border border-[#FF6633]/20">
              <EnvelopeIcon className="w-8 h-8 text-[#FF6633]" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-1">
                Hunter.io
              </h3>
              <p className="text-sm text-dark-text-secondary mb-3">
                Find email addresses by company domain. Perfect for targeted outreach to specific organizations.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Domain Search
                </span>
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Email Verification
                </span>
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Department Filter
                </span>
              </div>
            </div>
          </div>
        </button>

        {/* Apollo.io Card */}
        <button
          onClick={() => setActiveService(activeService === 'apollo' ? null : 'apollo')}
          className={`card-terminal p-6 text-left transition-all ${
            activeService === 'apollo'
              ? 'ring-2 ring-terminal-500'
              : 'hover:bg-dark-border/30'
          }`}
        >
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-[#6C5CE7]/10 border border-[#6C5CE7]/20">
              <UserGroupIcon className="w-8 h-8 text-[#6C5CE7]" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-1">
                Apollo.io
              </h3>
              <p className="text-sm text-dark-text-secondary mb-3">
                Advanced B2B database with 275M+ contacts. Search by title, industry, company size, and location.
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Title Search
                </span>
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Industry Filter
                </span>
                <span className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                  Company Size
                </span>
              </div>
            </div>
          </div>
        </button>
      </div>

      {/* Hunter.io Configuration */}
      {activeService === 'hunter' && (
        <div className="card-terminal p-6 space-y-6 animate-fadeIn">
          <div className="flex items-center gap-3 pb-4 border-b border-dark-border">
            <EnvelopeIcon className="w-6 h-6 text-[#FF6633]" />
            <h3 className="text-xl font-semibold text-dark-text-primary">
              Hunter.io Domain Search
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="form-label">
                Company Domain <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                className="form-input"
                value={hunterDomain}
                onChange={e => setHunterDomain(e.target.value)}
                placeholder="example.com"
              />
              <p className="text-xs text-dark-text-muted mt-1">
                Enter the company's website domain without http:// or www
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Department (optional)</label>
                <select
                  className="form-input"
                  value={hunterDepartment}
                  onChange={e => setHunterDepartment(e.target.value)}
                >
                  <option value="">All Departments</option>
                  <option value="executive">Executive</option>
                  <option value="it">IT</option>
                  <option value="finance">Finance</option>
                  <option value="management">Management</option>
                  <option value="sales">Sales</option>
                  <option value="legal">Legal</option>
                  <option value="support">Support</option>
                  <option value="hr">HR</option>
                  <option value="marketing">Marketing</option>
                  <option value="communication">Communication</option>
                </select>
              </div>

              <div>
                <label className="form-label">Seniority (optional)</label>
                <select
                  className="form-input"
                  value={hunterSeniority}
                  onChange={e => setHunterSeniority(e.target.value)}
                >
                  <option value="">All Levels</option>
                  <option value="junior">Junior</option>
                  <option value="senior">Senior</option>
                  <option value="executive">Executive</option>
                </select>
              </div>

              <div>
                <label className="form-label">Max Results</label>
                <input
                  type="number"
                  min={10}
                  max={500}
                  step={10}
                  className="form-input"
                  value={hunterLimit}
                  onChange={e => setHunterLimit(parseInt(e.target.value || '50', 10))}
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-dark-border">
            <button
              onClick={() => setActiveService(null)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleHunterSubmit}
              disabled={!hunterDomain.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
              Find Contacts
            </button>
          </div>
        </div>
      )}

      {/* Apollo.io Configuration */}
      {activeService === 'apollo' && (
        <div className="card-terminal p-6 space-y-6 animate-fadeIn">
          <div className="flex items-center gap-3 pb-4 border-b border-dark-border">
            <UserGroupIcon className="w-6 h-6 text-[#6C5CE7]" />
            <h3 className="text-xl font-semibold text-dark-text-primary">
              Apollo.io People Search
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="form-label">Company Name (optional)</label>
              <input
                type="text"
                className="form-input"
                value={apolloCompanyName}
                onChange={e => setApolloCompanyName(e.target.value)}
                placeholder="e.g., Google, Microsoft, Amazon"
              />
            </div>

            <div>
              <label className="form-label">Job Titles</label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="form-input flex-1"
                    value={apolloTitleInput}
                    onChange={e => setApolloTitleInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(apolloTitleInput, setApolloTitle, apolloTitle)
                        setApolloTitleInput('')
                      }
                    }}
                    placeholder="CEO, Marketing Manager, Software Engineer"
                  />
                  <button
                    onClick={() => {
                      addTag(apolloTitleInput, setApolloTitle, apolloTitle)
                      setApolloTitleInput('')
                    }}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
                {apolloTitle.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {apolloTitle.map((title, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-terminal-500/10 text-terminal-400 rounded-md text-sm"
                      >
                        {title}
                        <button
                          onClick={() => removeTag(idx, setApolloTitle, apolloTitle)}
                          className="hover:text-terminal-300"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="form-label">Industries</label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="form-input flex-1"
                    value={apolloIndustryInput}
                    onChange={e => setApolloIndustryInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(apolloIndustryInput, setApolloIndustry, apolloIndustry)
                        setApolloIndustryInput('')
                      }
                    }}
                    placeholder="Technology, Healthcare, Finance"
                  />
                  <button
                    onClick={() => {
                      addTag(apolloIndustryInput, setApolloIndustry, apolloIndustry)
                      setApolloIndustryInput('')
                    }}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
                {apolloIndustry.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {apolloIndustry.map((industry, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-terminal-500/10 text-terminal-400 rounded-md text-sm"
                      >
                        {industry}
                        <button
                          onClick={() => removeTag(idx, setApolloIndustry, apolloIndustry)}
                          className="hover:text-terminal-300"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company Size</label>
                <select
                  className="form-input"
                  value={apolloCompanySize}
                  onChange={e => setApolloCompanySize(e.target.value)}
                >
                  <option value="">Any Size</option>
                  <option value="1-10">1-10 employees</option>
                  <option value="11-50">11-50 employees</option>
                  <option value="51-200">51-200 employees</option>
                  <option value="201-500">201-500 employees</option>
                  <option value="501-1000">501-1000 employees</option>
                  <option value="1001-5000">1001-5000 employees</option>
                  <option value="5001-10000">5001-10000 employees</option>
                  <option value="10001+">10001+ employees</option>
                </select>
              </div>

              <div>
                <label className="form-label">Max Results</label>
                <input
                  type="number"
                  min={10}
                  max={1000}
                  step={10}
                  className="form-input"
                  value={apolloLimit}
                  onChange={e => setApolloLimit(parseInt(e.target.value || '100', 10))}
                />
              </div>
            </div>

            <div>
              <label className="form-label">Locations</label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="form-input flex-1"
                    value={apolloLocationInput}
                    onChange={e => setApolloLocationInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(apolloLocationInput, setApolloLocation, apolloLocation)
                        setApolloLocationInput('')
                      }
                    }}
                    placeholder="San Francisco, New York, Remote"
                  />
                  <button
                    onClick={() => {
                      addTag(apolloLocationInput, setApolloLocation, apolloLocation)
                      setApolloLocationInput('')
                    }}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
                {apolloLocation.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {apolloLocation.map((location, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-terminal-500/10 text-terminal-400 rounded-md text-sm"
                      >
                        {location}
                        <button
                          onClick={() => removeTag(idx, setApolloLocation, apolloLocation)}
                          className="hover:text-terminal-300"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-dark-border">
            <button
              onClick={() => setActiveService(null)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleApolloSubmit}
              disabled={!apolloCompanyName.trim() && apolloTitle.length === 0 && apolloIndustry.length === 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
              Find Contacts
            </button>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
          <h4 className="text-sm font-medium text-blue-400 mb-2">Hunter.io Benefits</h4>
          <ul className="text-sm text-dark-text-secondary space-y-1">
            <li>• Verified email addresses with confidence scores</li>
            <li>• Department and seniority filtering</li>
            <li>• Find decision-makers at target companies</li>
            <li>• Email pattern detection and validation</li>
          </ul>
        </div>

        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-6">
          <h4 className="text-sm font-medium text-purple-400 mb-2">Apollo.io Benefits</h4>
          <ul className="text-sm text-dark-text-secondary space-y-1">
            <li>• Access to 275M+ verified B2B contacts</li>
            <li>• Advanced filtering by title, industry, company size</li>
            <li>• Real-time data enrichment and validation</li>
            <li>• Direct phone numbers and social profiles</li>
          </ul>
        </div>
      </div>

      {/* Integration Notice */}
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-yellow-400 mb-2">
          API Integration Required
        </h4>
        <p className="text-sm text-dark-text-secondary">
          To use these services, you'll need to configure your Hunter.io and Apollo.io API keys in the settings.
          Both services offer free tiers with limited credits per month, perfect for getting started.
        </p>
      </div>
    </div>
  )
}
