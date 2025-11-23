import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { MockAnalysis } from '@/mocks/analysis.mock'
import { AnalysisMetrics } from '@/types/demoSite'

interface AnalysisMetricsViewProps {
  analysis: MockAnalysis
  currentMetrics: AnalysisMetrics
}

interface ScoreCardProps {
  title: string
  originalScore: number
  currentScore: number
  issues: string[]
  strengths: string[]
  color: string
}

function ScoreCard({ title, originalScore, currentScore, issues, strengths, color }: ScoreCardProps) {
  const improvement = currentScore - originalScore
  const hasImproved = improvement > 0

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-text-primary">{title}</h3>
        <div className="flex items-center gap-2">
          <div className="text-3xl font-bold text-dark-text-primary">
            {currentScore}
          </div>
          {hasImproved && (
            <div className="flex items-center gap-1 text-green-500 text-sm">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              +{improvement}
            </div>
          )}
        </div>
      </div>

      {/* Before/After Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-xs text-dark-text-muted mb-1">
          <span>Original: {originalScore}</span>
          <span>Current: {currentScore}</span>
        </div>
        <div className="h-2 bg-dark-border rounded-full overflow-hidden">
          <div
            className={`h-full ${color} transition-all duration-500`}
            style={{ width: `${currentScore}%` }}
          />
        </div>
      </div>

      {/* Issues Fixed */}
      {hasImproved && issues.length > 0 && (
        <div className="mb-3">
          <div className="text-sm font-medium text-dark-text-primary mb-2 flex items-center gap-2">
            <CheckCircleIcon className="w-4 h-4 text-green-500" />
            Issues Fixed
          </div>
          <ul className="space-y-1">
            {issues.slice(0, 3).map((issue, idx) => (
              <li key={idx} className="text-sm text-dark-text-secondary flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span className="line-through opacity-60">{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strengths */}
      {strengths.length > 0 && (
        <div>
          <div className="text-sm font-medium text-dark-text-primary mb-2">Strengths Maintained</div>
          <ul className="space-y-1">
            {strengths.slice(0, 2).map((strength, idx) => (
              <li key={idx} className="text-sm text-dark-text-secondary flex items-start gap-2">
                <span className="text-terminal-500 mt-0.5">•</span>
                <span>{strength}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default function AnalysisMetricsView({ analysis, currentMetrics }: AnalysisMetricsViewProps) {
  const totalImprovement = currentMetrics.overall_score - analysis.overall_score

  return (
    <div className="space-y-6">
      {/* Overall Score Header */}
      <div className="card p-6 bg-gradient-to-r from-terminal-900/20 to-dark-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-dark-text-primary mb-2">
              Overall Website Health
            </h2>
            <p className="text-dark-text-secondary">
              Comprehensive analysis before and after improvements
            </p>
          </div>
          <div className="text-center">
            <div className="text-5xl font-bold text-terminal-400 mb-2">
              {currentMetrics.overall_score}
            </div>
            <div className="flex items-center gap-2 justify-center text-green-500">
              <ArrowTrendingUpIcon className="w-5 h-5" />
              <span className="text-xl font-semibold">+{totalImprovement}</span>
            </div>
            <div className="text-sm text-dark-text-muted mt-1">
              from {analysis.overall_score}
            </div>
          </div>
        </div>
      </div>

      {/* Category Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ScoreCard
          title="Design Quality"
          originalScore={analysis.design.score}
          currentScore={currentMetrics.design_score}
          issues={analysis.design.issues}
          strengths={analysis.design.strengths}
          color="bg-gradient-to-r from-purple-500 to-pink-500"
        />

        <ScoreCard
          title="SEO Optimization"
          originalScore={analysis.seo.score}
          currentScore={currentMetrics.seo_score}
          issues={analysis.seo.issues}
          strengths={analysis.seo.strengths}
          color="bg-gradient-to-r from-blue-500 to-cyan-500"
        />

        <ScoreCard
          title="Performance"
          originalScore={analysis.performance.score}
          currentScore={currentMetrics.performance_score}
          issues={analysis.performance.issues}
          strengths={analysis.performance.strengths}
          color="bg-gradient-to-r from-green-500 to-emerald-500"
        />

        <ScoreCard
          title="Accessibility"
          originalScore={analysis.accessibility.score}
          currentScore={currentMetrics.accessibility_score}
          issues={analysis.accessibility.issues}
          strengths={analysis.accessibility.strengths}
          color="bg-gradient-to-r from-orange-500 to-amber-500"
        />
      </div>

      {/* Detailed Metrics */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5" />
          Detailed Performance Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {analysis.performance.metrics && (
            <>
              <div className="text-center p-4 rounded-lg bg-dark-border/30">
                <div className="text-sm text-dark-text-muted mb-1">Page Load Time</div>
                <div className="text-2xl font-bold text-dark-text-primary">
                  {analysis.performance.metrics.page_load_time}s
                </div>
              </div>
              <div className="text-center p-4 rounded-lg bg-dark-border/30">
                <div className="text-sm text-dark-text-muted mb-1">Time to Interactive</div>
                <div className="text-2xl font-bold text-dark-text-primary">
                  {analysis.performance.metrics.time_to_interactive}s
                </div>
              </div>
              <div className="text-center p-4 rounded-lg bg-dark-border/30">
                <div className="text-sm text-dark-text-muted mb-1">First Contentful Paint</div>
                <div className="text-2xl font-bold text-dark-text-primary">
                  {analysis.performance.metrics.first_contentful_paint}s
                </div>
              </div>
              <div className="text-center p-4 rounded-lg bg-dark-border/30">
                <div className="text-sm text-dark-text-muted mb-1">Total Page Size</div>
                <div className="text-2xl font-bold text-dark-text-primary">
                  {analysis.performance.metrics.total_page_size_mb}MB
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* SEO Details */}
      {analysis.seo.details && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-dark-text-primary mb-4">
            SEO Analysis Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Meta Tags</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {analysis.seo.details.meta_tags_present}/{analysis.seo.details.meta_tags_present + analysis.seo.details.meta_tags_missing}
              </div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Alt Texts Missing</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {analysis.seo.details.alt_texts_missing}
              </div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">Structured Data</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {analysis.seo.details.structured_data ? '✓' : '✗'}
              </div>
            </div>
            <div>
              <div className="text-sm text-dark-text-muted mb-1">WCAG Level</div>
              <div className="text-xl font-bold text-dark-text-primary">
                {analysis.accessibility.details?.wcag_level || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
