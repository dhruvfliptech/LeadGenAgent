// This is a showcase page for testing all source-related components
// Access via /source-showcase route (for development only)

import { useState } from 'react'
import SourceSelector, { SOURCE_CONFIGS, getSourceConfig } from '@/components/SourceSelector'
import SourceBadge from '@/components/SourceBadge'
import { LeadSource } from '@/types/lead'

export default function SourceShowcase() {
  const [selectedSource, setSelectedSource] = useState<LeadSource>('craigslist')

  return (
    <div className="space-y-8 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-dark-text-primary mb-2">
          Multi-Source Component Showcase
        </h1>
        <p className="text-dark-text-secondary mb-8">
          Development preview of all source-related UI components
        </p>

        {/* Source Selector */}
        <section className="card p-6 mb-8">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Source Selector Component
          </h2>
          <div className="max-w-md">
            <SourceSelector
              value={selectedSource}
              onChange={setSelectedSource}
              enabledSources={['craigslist', 'google_maps', 'linkedin']}
            />
          </div>
          <div className="mt-4 p-4 bg-dark-bg rounded">
            <p className="text-sm text-dark-text-secondary">
              Selected: <span className="text-terminal-400 font-mono">{selectedSource}</span>
            </p>
          </div>
        </section>

        {/* Source Badges */}
        <section className="card p-6 mb-8">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Source Badges
          </h2>

          <div className="space-y-6">
            {/* Small */}
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-3">
                Small (sm)
              </h3>
              <div className="flex flex-wrap gap-2">
                {SOURCE_CONFIGS.map(source => (
                  <SourceBadge
                    key={source.id}
                    source={source.id}
                    size="sm"
                  />
                ))}
              </div>
            </div>

            {/* Medium */}
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-3">
                Medium (md)
              </h3>
              <div className="flex flex-wrap gap-3">
                {SOURCE_CONFIGS.map(source => (
                  <SourceBadge
                    key={source.id}
                    source={source.id}
                    size="md"
                  />
                ))}
              </div>
            </div>

            {/* Large */}
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-3">
                Large (lg)
              </h3>
              <div className="flex flex-wrap gap-4">
                {SOURCE_CONFIGS.map(source => (
                  <SourceBadge
                    key={source.id}
                    source={source.id}
                    size="lg"
                  />
                ))}
              </div>
            </div>

            {/* Icon Only */}
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-3">
                Icon Only
              </h3>
              <div className="flex flex-wrap gap-2">
                {SOURCE_CONFIGS.map(source => (
                  <SourceBadge
                    key={source.id}
                    source={source.id}
                    size="md"
                    showName={false}
                  />
                ))}
              </div>
            </div>

            {/* Name Only */}
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-3">
                Name Only
              </h3>
              <div className="flex flex-wrap gap-2">
                {SOURCE_CONFIGS.map(source => (
                  <SourceBadge
                    key={source.id}
                    source={source.id}
                    size="md"
                    showIcon={false}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Source Chart Bars */}
        <section className="card p-6 mb-8">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Source Statistics Bars
          </h2>
          <div className="space-y-3">
            {SOURCE_CONFIGS.map((source) => {
              const mockCount = Math.floor(Math.random() * 500) + 50
              const mockPercentage = (mockCount / 500) * 100
              return (
                <div key={source.id} className="space-y-1">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{source.icon}</span>
                      <span className="text-sm font-medium text-dark-text-primary">
                        {source.name}
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-dark-text-primary">
                      {mockCount}
                    </span>
                  </div>
                  <div className="w-full bg-dark-border rounded-full h-2">
                    <div
                      className={`source-stat-bar-${source.id} h-2 rounded-full transition-all duration-500`}
                      style={{ width: `${mockPercentage}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-dark-text-muted">
                    Response rate: {(Math.random() * 50 + 20).toFixed(1)}%
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* Color Palette */}
        <section className="card p-6 mb-8">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Color Palette
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {SOURCE_CONFIGS.map(source => (
              <div
                key={source.id}
                className="border border-dark-border rounded-lg p-4"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{source.icon}</span>
                  <div>
                    <div className="font-medium text-dark-text-primary">
                      {source.name}
                    </div>
                    <div className="text-xs font-mono text-dark-text-muted">
                      {source.color}
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div
                    className="h-8 rounded"
                    style={{ backgroundColor: source.color }}
                  ></div>
                  <div
                    className="h-8 rounded"
                    style={{ backgroundColor: `${source.color}40` }}
                  ></div>
                  <div
                    className="h-8 rounded border"
                    style={{
                      borderColor: `${source.color}80`,
                      backgroundColor: `${source.color}10`
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Best Performing Source Card Preview */}
        <section className="card p-6 mb-8 bg-gradient-to-br from-terminal-900/20 to-dark-surface border-terminal-500/30">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Best Performing Source Card Preview
          </h2>
          <div className="flex items-start gap-3">
            <div className="text-4xl">🏆</div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-dark-text-primary mb-2">
                Best Performing Source
              </h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{getSourceConfig(selectedSource).icon}</span>
                  <span className="text-xl font-bold text-terminal-400">
                    {getSourceConfig(selectedSource).name}
                  </span>
                </div>
                <div className="text-dark-text-secondary space-y-1">
                  <div>450 leads generated</div>
                  <div>45.2% response rate</div>
                  <div>18.7% conversion rate</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Usage Code Examples */}
        <section className="card p-6">
          <h2 className="text-xl font-semibold text-dark-text-primary mb-4">
            Usage Examples
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-2">
                Source Selector
              </h3>
              <pre className="code-block">
{`<SourceSelector
  value={source}
  onChange={setSource}
  enabledSources={['craigslist', 'google_maps']}
/>`}
              </pre>
            </div>
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-2">
                Source Badge
              </h3>
              <pre className="code-block">
{`<SourceBadge
  source="craigslist"
  size="sm"
  showIcon={true}
  showName={true}
/>`}
              </pre>
            </div>
            <div>
              <h3 className="text-sm font-medium text-dark-text-secondary mb-2">
                Get Source Config
              </h3>
              <pre className="code-block">
{`const config = getSourceConfig('google_maps')
// config.name => "Google Maps"
// config.icon => "🗺️"
// config.color => "#4285F4"`}
              </pre>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
