import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  RocketLaunchIcon,
  CodeBracketIcon,
  ChartBarIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'
import { mockDemoSites, getTotalStats } from '@/mocks/demoSites.mock'
import { DemoSite, Framework, BuildStatus } from '@/types/demoSite'
import DemoSiteCard from '@/components/DemoSiteCard'
import CreateDemoWizard from '@/components/CreateDemoWizard'
import toast from 'react-hot-toast'

export default function DemoSites() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({
    status: '' as BuildStatus | '',
    framework: '' as Framework | '',
    search: ''
  })
  const [isCreateWizardOpen, setIsCreateWizardOpen] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  // Use mock data
  const allDemoSites = mockDemoSites
  const stats = getTotalStats()

  // Filter demo sites based on filters
  const demoSites = useMemo(() => {
    return allDemoSites.filter(site => {
      if (filters.status && site.status !== filters.status) return false
      if (filters.framework && site.framework !== filters.framework) return false
      if (filters.search) {
        const searchLower = filters.search.toLowerCase()
        return (
          site.lead_title?.toLowerCase().includes(searchLower) ||
          site.original_url.toLowerCase().includes(searchLower)
        )
      }
      return true
    })
  }, [allDemoSites, filters])

  const isLoading = false
  const error = null

  const handleViewDemo = (demo: DemoSite) => {
    navigate(`/demo-sites/${demo.id}`)
  }

  const handleRedeploy = (buildId: string) => {
    if (confirm('Are you sure you want to redeploy this demo site?')) {
      toast.success('Redeployment started! (Mock)')
    }
  }

  const handleDelete = (buildId: string) => {
    if (confirm('Are you sure you want to delete this demo site? This action cannot be undone.')) {
      toast.success('Demo site deleted! (Mock)')
    }
  }

  const handleCreateSuccess = (buildId: string) => {
    toast.success('Demo site created! Redirecting...')
    const newSite = mockDemoSites.find(s => s.build_id === buildId)
    if (newSite) {
      setTimeout(() => navigate(`/demo-sites/${newSite.id}`), 1500)
    }
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">Error loading demo sites</div>
        <button onClick={() => window.location.reload()} className="btn-primary">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-dark-text-primary sm:text-3xl sm:truncate">
            Demo Sites
          </h2>
          <p className="mt-1 text-sm text-dark-text-secondary">
            AI-generated website demos with improvements applied
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsCreateWizardOpen(true)}
            className="btn-primary flex items-center gap-2"
          >
            <PlusIcon className="w-5 h-5" />
            Create Demo Site
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <RocketLaunchIcon className="h-6 w-6 text-terminal-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">{stats.total_demos}</div>
                <div className="text-sm font-medium text-dark-text-secondary">Total Demos</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  {stats.completed_demos} completed
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CodeBracketIcon className="h-6 w-6 text-blue-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">
                  {Object.values(stats.by_framework).reduce((a, b) => a + b, 0)}
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Frameworks Used</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  {stats.by_framework.react || 0} React, {stats.by_framework.nextjs || 0} Next.js
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CurrencyDollarIcon className="h-6 w-6 text-green-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-terminal-400 font-mono">
                  ${stats.total_cost.toFixed(2)}
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Total AI Cost</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  Avg ${(stats.total_cost / (stats.total_demos || 1)).toFixed(4)}
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChartBarIcon className="h-6 w-6 text-purple-500" />
              </div>
              <div className="ml-4">
                <div className="text-2xl font-bold text-dark-text-primary">
                  {stats.avg_generation_time.toFixed(1)}s
                </div>
                <div className="text-sm font-medium text-dark-text-secondary">Avg Build Time</div>
                <div className="text-xs text-dark-text-muted mt-1">
                  Fastest generation times
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <FunnelIcon className="h-5 w-5 text-dark-text-secondary flex-shrink-0" />

          {/* Search */}
          <div className="flex-1 w-full sm:w-auto">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-dark-text-muted" />
              </div>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search by lead name or URL..."
                className="form-input pl-10 w-full"
              />
            </div>
          </div>

          {/* Status Filter */}
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as BuildStatus | '' }))}
            className="form-input w-full sm:w-auto"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="analyzing">Analyzing</option>
            <option value="planning">Planning</option>
            <option value="generating">Generating</option>
            <option value="deploying">Deploying</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          {/* Framework Filter */}
          <select
            value={filters.framework}
            onChange={(e) => setFilters(prev => ({ ...prev, framework: e.target.value as Framework | '' }))}
            className="form-input w-full sm:w-auto"
          >
            <option value="">All Frameworks</option>
            <option value="html">HTML/CSS/JS</option>
            <option value="react">React</option>
            <option value="nextjs">Next.js</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 border border-dark-border rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                viewMode === 'grid'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-secondary hover:text-dark-text-primary'
              }`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                viewMode === 'list'
                  ? 'bg-terminal-500 text-white'
                  : 'text-dark-text-secondary hover:text-dark-text-primary'
              }`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Demo Sites Grid/List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-48 bg-dark-border rounded mb-4"></div>
              <div className="h-4 bg-dark-border rounded mb-2"></div>
              <div className="h-3 bg-dark-border rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : demoSites.length > 0 ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {demoSites.map((demo) => (
            <DemoSiteCard
              key={demo.id}
              demoSite={demo}
              onView={handleViewDemo}
              onRedeploy={handleRedeploy}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <RocketLaunchIcon className="mx-auto h-12 w-12 text-dark-text-muted" />
            <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No demo sites</h3>
            <p className="mt-1 text-sm text-dark-text-secondary">
              {filters.search || filters.status || filters.framework
                ? 'No demo sites match your filters.'
                : 'Get started by creating your first demo site.'}
            </p>
            <div className="mt-6">
              <button
                onClick={() => setIsCreateWizardOpen(true)}
                className="btn-primary inline-flex items-center gap-2"
              >
                <PlusIcon className="w-5 h-5" />
                Create Demo Site
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Demo Wizard */}
      <CreateDemoWizard
        isOpen={isCreateWizardOpen}
        onClose={() => setIsCreateWizardOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </div>
  )
}
