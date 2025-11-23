import { useState, useMemo } from 'react'
import {
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
  ArrowDownTrayIcon,
  CodeBracketIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClipboardDocumentIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'
import { DemoSite } from '@/types/demoSite'
import { demoSitesApi, demoSitesUtils } from '@/services/demoSitesApi'
import toast from 'react-hot-toast'

interface DemoSiteModalProps {
  demoSite: DemoSite | null
  isOpen: boolean
  onClose: () => void
}

type Tab = 'overview' | 'improvements' | 'code' | 'analytics'

export default function DemoSiteModal({ demoSite, isOpen, onClose }: DemoSiteModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({})

  if (!isOpen || !demoSite) return null

  const filesByDirectory = useMemo(() => {
    const grouped: Record<string, string[]> = {}
    Object.keys(demoSite.files).forEach(filePath => {
      const parts = filePath.split('/')
      const directory = parts.length > 1 ? parts[0] : 'root'
      if (!grouped[directory]) grouped[directory] = []
      grouped[directory].push(filePath)
    })
    return grouped
  }, [demoSite.files])

  const handleDownload = async () => {
    try {
      const response = await demoSitesApi.downloadDemoSite(demoSite.build_id)
      const blob = response.data
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `demo-${demoSite.build_id}.zip`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Demo site downloaded!')
    } catch (error) {
      toast.error('Failed to download demo site')
    }
  }

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    toast.success('Code copied to clipboard!')
  }

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  const getFileLanguage = (filePath: string): string => {
    const ext = filePath.split('.').pop()?.toLowerCase()
    const languageMap: Record<string, string> = {
      'ts': 'typescript',
      'tsx': 'typescript',
      'js': 'javascript',
      'jsx': 'javascript',
      'json': 'json',
      'css': 'css',
      'html': 'html',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml'
    }
    return languageMap[ext || ''] || 'plaintext'
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: DocumentTextIcon },
    { id: 'improvements', name: 'Improvements', icon: CheckCircleIcon },
    { id: 'code', name: 'Code Files', icon: CodeBracketIcon },
    { id: 'analytics', name: 'Analytics', icon: ChartBarIcon }
  ]

  // Group improvements by category
  const improvementsByCategory = useMemo(() => {
    const grouped: Record<string, typeof demoSite.improvements_applied> = {}
    demoSite.improvements_applied.forEach(improvement => {
      if (!grouped[improvement.category]) grouped[improvement.category] = []
      grouped[improvement.category].push(improvement)
    })
    return grouped
  }, [demoSite.improvements_applied])

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 transition-opacity bg-dark-bg/80 backdrop-blur-sm" onClick={onClose} />

        {/* Modal */}
        <div className="inline-block align-bottom bg-dark-surface rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full border border-dark-border">
          {/* Header */}
          <div className="px-6 py-4 border-b border-dark-border bg-gradient-to-r from-terminal-900/20 to-dark-surface">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-dark-text-primary mb-1">
                  {demoSite.lead_title || 'Demo Site'}
                </h3>
                <a
                  href={demoSite.original_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-dark-text-secondary hover:text-terminal-400 flex items-center gap-1"
                >
                  {demoSite.original_url}
                  <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                </a>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${demoSitesUtils.getStatusColor(demoSite.status)}`}>
                  {demoSite.status}
                </span>
                <button onClick={onClose} className="text-dark-text-secondary hover:text-dark-text-primary">
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 mt-4">
              {demoSite.preview_url && (
                <a
                  href={demoSite.preview_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary text-sm flex items-center gap-2"
                >
                  <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  Open Live Preview
                </a>
              )}
              <button
                onClick={handleDownload}
                className="btn-secondary text-sm flex items-center gap-2"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                Download ZIP
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-dark-border bg-dark-border/30">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => {
                const TabIcon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as Tab)}
                    className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      isActive
                        ? 'border-terminal-500 text-terminal-400'
                        : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:border-dark-border'
                    }`}
                  >
                    <TabIcon className="w-4 h-4" />
                    {tab.name}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Quick Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Framework</div>
                    <div className="text-lg font-semibold text-dark-text-primary flex items-center gap-2">
                      <span>{demoSitesUtils.getFrameworkIcon(demoSite.framework)}</span>
                      {demoSitesUtils.getFrameworkName(demoSite.framework)}
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Lines of Code</div>
                    <div className="text-lg font-semibold text-dark-text-primary">
                      {demoSite.total_lines_of_code.toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">Generation Time</div>
                    <div className="text-lg font-semibold text-dark-text-primary">
                      {demoSitesUtils.formatDuration(demoSite.generation_time_seconds)}
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="text-xs text-dark-text-muted mb-1">AI Cost</div>
                    <div className="text-lg font-semibold text-terminal-400 font-mono">
                      ${demoSite.ai_cost.toFixed(4)}
                    </div>
                  </div>
                </div>

                {/* AI Model Used */}
                <div>
                  <h4 className="text-sm font-medium text-dark-text-primary mb-2">AI Model</h4>
                  <div className="bg-purple-100 text-purple-800 px-3 py-2 rounded text-sm inline-flex items-center gap-2">
                    <CodeBracketIcon className="w-4 h-4" />
                    {demoSite.ai_model_used}
                  </div>
                </div>

                {/* Validation Results */}
                {demoSite.validation_results && (
                  <div>
                    <h4 className="text-sm font-medium text-dark-text-primary mb-3">Validation Results</h4>
                    <div className="bg-dark-border/30 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-dark-text-secondary">Status</span>
                        {demoSite.validation_results.is_valid ? (
                          <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
                            <CheckCircleIcon className="w-4 h-4" />
                            Valid
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-red-600 text-sm font-medium">
                            <ExclamationTriangleIcon className="w-4 h-4" />
                            Issues Found
                          </span>
                        )}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-dark-text-secondary">Files Generated</span>
                        <span className="text-sm font-medium text-dark-text-primary">
                          {demoSite.validation_results.file_count}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-dark-text-secondary">Total Size</span>
                        <span className="text-sm font-medium text-dark-text-primary">
                          {demoSitesUtils.formatFileSize(demoSite.validation_results.total_size_bytes)}
                        </span>
                      </div>
                      {demoSite.validation_results.errors.length > 0 && (
                        <div>
                          <div className="text-xs text-red-600 font-medium mb-1">Errors:</div>
                          <ul className="space-y-1">
                            {demoSite.validation_results.errors.map((error, idx) => (
                              <li key={idx} className="text-xs text-red-600 flex items-start gap-1">
                                <span>•</span>
                                <span>{error}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {demoSite.validation_results.warnings.length > 0 && (
                        <div>
                          <div className="text-xs text-yellow-600 font-medium mb-1">Warnings:</div>
                          <ul className="space-y-1">
                            {demoSite.validation_results.warnings.map((warning, idx) => (
                              <li key={idx} className="text-xs text-yellow-600 flex items-start gap-1">
                                <span>•</span>
                                <span>{warning}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Deployment Config */}
                <div>
                  <h4 className="text-sm font-medium text-dark-text-primary mb-3">Deployment Configuration</h4>
                  <div className="bg-dark-border/30 rounded-lg p-4 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-dark-text-secondary">Build Command:</span>
                      <code className="text-terminal-400 font-mono">{demoSite.deployment_config.build_command}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-text-secondary">Install Command:</span>
                      <code className="text-terminal-400 font-mono">{demoSite.deployment_config.install_command}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-text-secondary">Output Directory:</span>
                      <code className="text-terminal-400 font-mono">{demoSite.deployment_config.output_directory}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-text-secondary">Dev Command:</span>
                      <code className="text-terminal-400 font-mono">{demoSite.deployment_config.dev_command}</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-text-secondary">Port:</span>
                      <code className="text-terminal-400 font-mono">{demoSite.deployment_config.port}</code>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Improvements Tab */}
            {activeTab === 'improvements' && (
              <div className="space-y-4">
                <div className="bg-terminal-900/20 rounded-lg p-4 mb-4">
                  <div className="text-sm text-dark-text-secondary mb-1">Total Improvements Applied</div>
                  <div className="text-3xl font-bold text-terminal-400">
                    {demoSite.improvements_applied.length}
                  </div>
                </div>

                {Object.entries(improvementsByCategory).map(([category, improvements]) => (
                  <div key={category} className="border border-dark-border rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full flex items-center justify-between p-4 bg-dark-border/30 hover:bg-dark-border/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{demoSitesUtils.getCategoryIcon(category)}</span>
                        <span className="font-medium text-dark-text-primary capitalize">{category}</span>
                        <span className="text-sm text-dark-text-muted">({improvements.length})</span>
                      </div>
                      {expandedCategories[category] ? (
                        <ChevronDownIcon className="w-5 h-5 text-dark-text-secondary" />
                      ) : (
                        <ChevronRightIcon className="w-5 h-5 text-dark-text-secondary" />
                      )}
                    </button>

                    {expandedCategories[category] && (
                      <div className="p-4 space-y-3">
                        {improvements.map((improvement, idx) => (
                          <div key={idx} className="bg-dark-surface rounded-lg p-3 border border-dark-border">
                            <div className="flex items-start justify-between mb-2">
                              <h5 className="font-medium text-dark-text-primary">{improvement.title}</h5>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium ${demoSitesUtils.getPriorityColor(improvement.priority)}`}>
                                {improvement.priority}
                              </span>
                            </div>
                            <p className="text-sm text-dark-text-secondary">
                              Impact: {improvement.impact}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Code Tab */}
            {activeTab === 'code' && (
              <div className="grid grid-cols-4 gap-4">
                {/* File Tree */}
                <div className="col-span-1 border-r border-dark-border pr-4">
                  <h4 className="text-sm font-medium text-dark-text-primary mb-3">Files</h4>
                  <div className="space-y-2">
                    {Object.entries(filesByDirectory).map(([directory, files]) => (
                      <div key={directory}>
                        <div className="text-xs font-medium text-dark-text-muted mb-1 uppercase">
                          {directory}
                        </div>
                        {files.map(filePath => (
                          <button
                            key={filePath}
                            onClick={() => setSelectedFile(filePath)}
                            className={`w-full text-left text-sm px-2 py-1 rounded transition-colors ${
                              selectedFile === filePath
                                ? 'bg-terminal-500/20 text-terminal-400'
                                : 'text-dark-text-secondary hover:bg-dark-border/30'
                            }`}
                          >
                            {filePath.split('/').pop()}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Code Viewer */}
                <div className="col-span-3">
                  {selectedFile ? (
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-medium text-dark-text-primary">{selectedFile}</h4>
                        <button
                          onClick={() => handleCopyCode(demoSite.files[selectedFile])}
                          className="btn-secondary text-xs flex items-center gap-1"
                        >
                          <ClipboardDocumentIcon className="w-3 h-3" />
                          Copy
                        </button>
                      </div>
                      <div className="bg-dark-bg border border-dark-border rounded-lg p-4 overflow-x-auto">
                        <pre className="text-xs text-dark-text-primary font-mono">
                          <code className={`language-${getFileLanguage(selectedFile)}`}>
                            {demoSite.files[selectedFile]}
                          </code>
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 text-dark-text-muted">
                      Select a file to view its contents
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-dark-border/30 rounded-lg p-6">
                    <div className="text-sm text-dark-text-muted mb-2">Total Views</div>
                    <div className="text-3xl font-bold text-dark-text-primary">
                      {demoSite.view_count || 0}
                    </div>
                  </div>
                  <div className="bg-dark-border/30 rounded-lg p-6">
                    <div className="text-sm text-dark-text-muted mb-2">Total Clicks</div>
                    <div className="text-3xl font-bold text-dark-text-primary">
                      {demoSite.click_count || 0}
                    </div>
                  </div>
                </div>

                {demoSite.last_viewed_at && (
                  <div>
                    <div className="text-sm text-dark-text-muted">Last Viewed</div>
                    <div className="text-dark-text-primary">
                      {new Date(demoSite.last_viewed_at).toLocaleString()}
                    </div>
                  </div>
                )}

                <div className="text-center py-8 text-dark-text-muted">
                  <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>More detailed analytics coming soon</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
