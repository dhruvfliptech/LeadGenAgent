import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeftIcon,
  ArrowTopRightOnSquareIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CodeBracketIcon,
  ChartBarIcon,
  CogIcon,
  RocketLaunchIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { mockDemoSites } from '@/mocks/demoSites.mock'
import { mockAnalyses } from '@/mocks/analysis.mock'
import FileExplorer from '@/components/demo-site/FileExplorer'
import CodeViewer from '@/components/demo-site/CodeViewer'
import AnalysisMetricsView from '@/components/demo-site/AnalysisMetricsView'
import ImprovementsView from '@/components/demo-site/ImprovementsView'
import DeploymentPanel from '@/components/demo-site/DeploymentPanel'
import ValidationResults from '@/components/demo-site/ValidationResults'
import { demoSitesUtils } from '@/services/demoSitesApi'

type Tab = 'overview' | 'code' | 'improvements' | 'metrics' | 'deployment'

export default function DemoSiteDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)

  const demoSite = mockDemoSites.find(site => site.id === Number(id))
  const analysis = demoSite ? mockAnalyses.find(a => a.lead_id === demoSite.lead_id) : null

  useEffect(() => {
    if (demoSite?.files && !selectedFile) {
      const files = Object.keys(demoSite.files)
      if (files.length > 0) {
        setSelectedFile(files[0])
      }
    }
  }, [demoSite, selectedFile])

  if (!demoSite) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-dark-text-primary mb-2">Demo Site Not Found</h3>
        <p className="text-dark-text-secondary mb-4">The demo site you're looking for doesn't exist.</p>
        <button onClick={() => navigate('/demo-sites')} className="btn-primary">
          Back to Demo Sites
        </button>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: DocumentTextIcon },
    { id: 'code', name: 'Code', icon: CodeBracketIcon },
    { id: 'improvements', name: 'Improvements', icon: CheckCircleIcon },
    { id: 'metrics', name: 'Metrics', icon: ChartBarIcon },
    { id: 'deployment', name: 'Deployment', icon: RocketLaunchIcon }
  ]

  const statusColor = demoSitesUtils.getStatusColor(demoSite.status)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/demo-sites')}
          className="flex items-center gap-2 text-dark-text-secondary hover:text-dark-text-primary mb-4"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Demo Sites
        </button>

        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-dark-text-primary">
                {demoSite.lead_title || 'Untitled Demo'}
              </h1>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
                {demoSite.status}
              </span>
            </div>
            <a
              href={demoSite.original_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-dark-text-secondary hover:text-terminal-400 flex items-center gap-2 mb-2"
            >
              <span>Original: {demoSite.original_url}</span>
              <ArrowTopRightOnSquareIcon className="w-4 h-4" />
            </a>
            <div className="text-sm text-dark-text-muted">
              Build ID: <code className="font-mono text-terminal-400">{demoSite.build_id}</code>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {demoSite.preview_url && (
              <a
                href={demoSite.preview_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary flex items-center gap-2"
              >
                <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                View Live
              </a>
            )}
            {demoSite.status === 'completed' && (
              <>
                <button className="btn-secondary flex items-center gap-2">
                  <ArrowPathIcon className="w-4 h-4" />
                  Redeploy
                </button>
                <button className="btn-secondary flex items-center gap-2">
                  <ArrowDownTrayIcon className="w-4 h-4" />
                  Download
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-sm text-dark-text-secondary mb-1">Framework</div>
          <div className="text-2xl font-bold text-dark-text-primary flex items-center gap-2">
            <span>{demoSitesUtils.getFrameworkIcon(demoSite.framework)}</span>
            <span>{demoSitesUtils.getFrameworkName(demoSite.framework)}</span>
          </div>
        </div>

        <div className="card p-4">
          <div className="text-sm text-dark-text-secondary mb-1">Generation Time</div>
          <div className="text-2xl font-bold text-dark-text-primary">
            {demoSitesUtils.formatDuration(demoSite.generation_time_seconds)}
          </div>
        </div>

        <div className="card p-4">
          <div className="text-sm text-dark-text-secondary mb-1">Lines of Code</div>
          <div className="text-2xl font-bold text-dark-text-primary">
            {demoSite.total_lines_of_code.toLocaleString()}
          </div>
        </div>

        <div className="card p-4">
          <div className="text-sm text-dark-text-secondary mb-1">AI Cost</div>
          <div className="text-2xl font-bold text-terminal-400 font-mono">
            ${demoSite.ai_cost.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-dark-border">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-terminal-500 text-terminal-400'
                  : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Validation Results */}
            <ValidationResults validation={demoSite.validation_results} />

            {/* Improvements Summary */}
            {demoSite.improvements_applied.length > 0 && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                  Applied Improvements ({demoSite.improvements_applied.length})
                </h3>
                <div className="space-y-3">
                  {demoSite.improvements_applied.map((improvement, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-3 p-3 rounded-lg bg-dark-border/30"
                    >
                      <span className="text-2xl">{demoSitesUtils.getCategoryIcon(improvement.category)}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-dark-text-primary">{improvement.title}</h4>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${demoSitesUtils.getPriorityColor(improvement.priority)}`}>
                            {improvement.priority}
                          </span>
                        </div>
                        <p className="text-sm text-dark-text-secondary">{improvement.impact}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analysis Metrics Preview */}
            {demoSite.analysis_metrics && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
                  Analysis Scores
                </h3>
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-terminal-400 mb-1">
                      {demoSite.analysis_metrics.overall_score}
                    </div>
                    <div className="text-sm text-dark-text-secondary">Overall</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-dark-text-primary mb-1">
                      {demoSite.analysis_metrics.design_score}
                    </div>
                    <div className="text-sm text-dark-text-secondary">Design</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-dark-text-primary mb-1">
                      {demoSite.analysis_metrics.seo_score}
                    </div>
                    <div className="text-sm text-dark-text-secondary">SEO</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-dark-text-primary mb-1">
                      {demoSite.analysis_metrics.performance_score}
                    </div>
                    <div className="text-sm text-dark-text-secondary">Performance</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-dark-text-primary mb-1">
                      {demoSite.analysis_metrics.accessibility_score}
                    </div>
                    <div className="text-sm text-dark-text-secondary">Accessibility</div>
                  </div>
                </div>
              </div>
            )}

            {/* Configuration */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
                <CogIcon className="w-5 h-5" />
                Deployment Configuration
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-dark-text-muted mb-1">Framework</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.framework}
                  </code>
                </div>
                <div>
                  <div className="text-dark-text-muted mb-1">Build Command</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.build_command}
                  </code>
                </div>
                <div>
                  <div className="text-dark-text-muted mb-1">Install Command</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.install_command}
                  </code>
                </div>
                <div>
                  <div className="text-dark-text-muted mb-1">Output Directory</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.output_directory}
                  </code>
                </div>
                <div>
                  <div className="text-dark-text-muted mb-1">Dev Command</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.dev_command}
                  </code>
                </div>
                <div>
                  <div className="text-dark-text-muted mb-1">Port</div>
                  <code className="text-dark-text-primary bg-dark-border/30 px-2 py-1 rounded">
                    {demoSite.deployment_config.port}
                  </code>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Code Tab */}
        {activeTab === 'code' && (
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-3">
              <FileExplorer
                files={demoSite.files}
                selectedFile={selectedFile}
                onFileSelect={setSelectedFile}
              />
            </div>
            <div className="col-span-9">
              {selectedFile && demoSite.files[selectedFile] ? (
                <CodeViewer
                  filename={selectedFile}
                  content={demoSite.files[selectedFile]}
                />
              ) : (
                <div className="card p-12 text-center">
                  <CodeBracketIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
                  <p className="text-dark-text-secondary">Select a file to view its contents</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Improvements Tab */}
        {activeTab === 'improvements' && analysis && (
          <ImprovementsView
            improvements={analysis.improvements}
            appliedImprovements={demoSite.improvements_applied}
            summary={analysis.improvements_summary}
          />
        )}

        {/* Metrics Tab */}
        {activeTab === 'metrics' && analysis && demoSite.analysis_metrics && (
          <AnalysisMetricsView
            analysis={analysis}
            currentMetrics={demoSite.analysis_metrics}
          />
        )}

        {/* Deployment Tab */}
        {activeTab === 'deployment' && (
          <DeploymentPanel demoSite={demoSite} />
        )}
      </div>
    </div>
  )
}
