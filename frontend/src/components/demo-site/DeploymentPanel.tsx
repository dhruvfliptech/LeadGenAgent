import { useState } from 'react'
import {
  RocketLaunchIcon,
  ArrowTopRightOnSquareIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { DemoSite } from '@/types/demoSite'
import { formatRelativeTime } from '@/utils/dateFormat'

interface DeploymentPanelProps {
  demoSite: DemoSite
}

export default function DeploymentPanel({ demoSite }: DeploymentPanelProps) {
  const [isDeploying, setIsDeploying] = useState(false)

  const handleDeploy = () => {
    setIsDeploying(true)
    setTimeout(() => setIsDeploying(false), 3000)
  }

  const getDeploymentStatusColor = (status?: string) => {
    switch (status) {
      case 'deployed':
        return 'text-green-500 bg-green-500/10'
      case 'deploying':
        return 'text-yellow-500 bg-yellow-500/10'
      case 'failed':
        return 'text-red-500 bg-red-500/10'
      default:
        return 'text-gray-500 bg-gray-500/10'
    }
  }

  const getProviderLogo = (provider?: string) => {
    switch (provider) {
      case 'vercel':
        return '▲'
      case 'netlify':
        return '◆'
      case 'github_pages':
        return '🐙'
      default:
        return '🚀'
    }
  }

  return (
    <div className="space-y-6">
      {/* Deployment Status */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
          <RocketLaunchIcon className="w-5 h-5" />
          Deployment Status
        </h3>

        {demoSite.deployment_status === 'deployed' && demoSite.preview_url ? (
          <div className="space-y-4">
            {/* Deployed Successfully */}
            <div className="flex items-start gap-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircleIcon className="w-6 h-6 text-green-500 flex-shrink-0" />
              <div className="flex-1">
                <div className="font-medium text-dark-text-primary mb-1">
                  Successfully Deployed
                </div>
                <p className="text-sm text-dark-text-secondary mb-3">
                  Your demo site is live and accessible
                </p>

                {/* Provider Badge */}
                {demoSite.deployment_provider && (
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-dark-border text-sm">
                    <span className="text-xl">{getProviderLogo(demoSite.deployment_provider)}</span>
                    <span className="font-medium text-dark-text-primary capitalize">
                      {demoSite.deployment_provider}
                    </span>
                  </div>
                )}

                {/* Deployment Time */}
                {demoSite.deployed_at && (
                  <div className="text-sm text-dark-text-muted mt-2">
                    Deployed {formatRelativeTime(demoSite.deployed_at)}
                  </div>
                )}
              </div>
            </div>

            {/* Live URL */}
            <div>
              <label className="text-sm font-medium text-dark-text-primary mb-2 block">
                Live Preview URL
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={demoSite.preview_url}
                  readOnly
                  className="form-input flex-1 font-mono text-sm"
                />
                <a
                  href={demoSite.preview_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary flex items-center gap-2"
                >
                  <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  Open
                </a>
              </div>
            </div>

            {/* Analytics */}
            {(demoSite.view_count !== undefined || demoSite.click_count !== undefined) && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-dark-border/30 rounded-lg">
                  <div className="text-sm text-dark-text-muted mb-1">Page Views</div>
                  <div className="text-2xl font-bold text-dark-text-primary">
                    {demoSite.view_count || 0}
                  </div>
                </div>
                <div className="p-4 bg-dark-border/30 rounded-lg">
                  <div className="text-sm text-dark-text-muted mb-1">Clicks</div>
                  <div className="text-2xl font-bold text-dark-text-primary">
                    {demoSite.click_count || 0}
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 pt-4 border-t border-dark-border">
              <button
                onClick={handleDeploy}
                disabled={isDeploying}
                className="btn-secondary flex items-center gap-2"
              >
                <ArrowPathIcon className={`w-4 h-4 ${isDeploying ? 'animate-spin' : ''}`} />
                Redeploy
              </button>
              <button className="btn-secondary">
                View Logs
              </button>
            </div>
          </div>
        ) : demoSite.deployment_status === 'deploying' ? (
          <div className="flex items-start gap-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
            <ClockIcon className="w-6 h-6 text-yellow-500 flex-shrink-0 animate-pulse" />
            <div>
              <div className="font-medium text-dark-text-primary mb-1">
                Deployment In Progress
              </div>
              <p className="text-sm text-dark-text-secondary">
                Your demo site is being deployed. This usually takes 1-2 minutes.
              </p>
            </div>
          </div>
        ) : demoSite.deployment_status === 'failed' ? (
          <div className="flex items-start gap-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <ExclamationCircleIcon className="w-6 h-6 text-red-500 flex-shrink-0" />
            <div className="flex-1">
              <div className="font-medium text-dark-text-primary mb-1">
                Deployment Failed
              </div>
              <p className="text-sm text-dark-text-secondary mb-3">
                {demoSite.deployment_error || 'An error occurred during deployment'}
              </p>
              <button
                onClick={handleDeploy}
                disabled={isDeploying}
                className="btn-primary flex items-center gap-2"
              >
                <ArrowPathIcon className={`w-4 h-4 ${isDeploying ? 'animate-spin' : ''}`} />
                Retry Deployment
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <RocketLaunchIcon className="w-12 h-12 text-dark-text-muted mx-auto mb-4" />
            <p className="text-dark-text-secondary mb-4">
              This demo site hasn't been deployed yet
            </p>
            <button
              onClick={handleDeploy}
              disabled={isDeploying}
              className="btn-primary flex items-center gap-2 mx-auto"
            >
              <RocketLaunchIcon className="w-4 h-4" />
              Deploy Now
            </button>
          </div>
        )}
      </div>

      {/* Deployment Providers */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Available Deployment Providers
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 border-2 border-dark-border rounded-lg hover:border-terminal-500 transition-colors cursor-pointer">
            <div className="text-4xl mb-2">▲</div>
            <div className="font-medium text-dark-text-primary mb-1">Vercel</div>
            <p className="text-sm text-dark-text-secondary">
              Optimized for Next.js and React
            </p>
          </div>

          <div className="p-4 border-2 border-dark-border rounded-lg hover:border-terminal-500 transition-colors cursor-pointer">
            <div className="text-4xl mb-2">◆</div>
            <div className="font-medium text-dark-text-primary mb-1">Netlify</div>
            <p className="text-sm text-dark-text-secondary">
              Great for static sites and JAMstack
            </p>
          </div>

          <div className="p-4 border-2 border-dark-border rounded-lg hover:border-terminal-500 transition-colors cursor-pointer">
            <div className="text-4xl mb-2">🐙</div>
            <div className="font-medium text-dark-text-primary mb-1">GitHub Pages</div>
            <p className="text-sm text-dark-text-secondary">
              Simple static site hosting
            </p>
          </div>
        </div>
      </div>

      {/* Environment Variables */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
          Environment Variables
        </h3>
        {demoSite.deployment_config.environment_variables &&
        Object.keys(demoSite.deployment_config.environment_variables).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(demoSite.deployment_config.environment_variables).map(([key, value]) => (
              <div key={key} className="flex items-center gap-4 p-3 bg-dark-border/30 rounded-lg">
                <code className="text-sm font-mono text-dark-text-primary flex-1">{key}</code>
                <code className="text-sm font-mono text-dark-text-secondary">{value}</code>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-dark-text-secondary text-center py-4">
            No environment variables configured
          </p>
        )}
      </div>
    </div>
  )
}
