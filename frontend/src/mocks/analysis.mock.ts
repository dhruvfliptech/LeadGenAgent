/**
 * Mock website analysis data for demo site generation
 */

export interface AnalysisScore {
  score: number
  issues: string[]
  strengths: string[]
  metrics?: Record<string, any>
  details?: Record<string, any>
}

export interface Improvement {
  id: string
  category: 'design' | 'seo' | 'performance' | 'accessibility' | 'content' | 'ux'
  priority: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  current_state: string
  proposed_change: string
  impact: string
  difficulty: 'easy' | 'medium' | 'hard'
  time_estimate: string
  code_example?: string
  resources: string[]
  dependencies: string[]
}

export interface MockAnalysis {
  id: number
  analysis_id: string
  lead_id: number
  url: string
  analyzed_at: string

  // Scores
  overall_score: number
  design: AnalysisScore
  seo: AnalysisScore
  performance: AnalysisScore
  accessibility: AnalysisScore

  // Content
  title: string
  meta_description: string
  html_content?: string

  // Improvements
  improvements: Improvement[]
  improvements_summary: {
    total_improvements: number
    critical_priority: number
    high_priority: number
    medium_priority: number
    low_priority: number
    estimated_total_impact: string
    estimated_total_time: string
    quick_wins: number
    categories: Record<string, number>
  }

  // Status
  status: 'analyzing' | 'completed' | 'failed'
  error_message?: string

  created_at: string
}

export const mockAnalyses: MockAnalysis[] = [
  // High quality site with minor issues
  {
    id: 1,
    analysis_id: 'ana_abc123',
    lead_id: 1,
    url: 'https://acmedesign.example.com',
    analyzed_at: '2025-01-05T10:30:00Z',
    overall_score: 78,
    design: {
      score: 82,
      issues: [
        'Inconsistent button styles across pages',
        'Mobile navigation could be more intuitive',
        'Color contrast issues on some call-to-action buttons',
      ],
      strengths: [
        'Modern, clean layout',
        'Good use of whitespace',
        'Professional color scheme',
        'Responsive grid system',
      ],
      metrics: {
        color_contrast_ratio: 4.2,
        whitespace_score: 85,
        consistency_score: 78,
      },
    },
    seo: {
      score: 75,
      issues: [
        'Missing alt text on 3 images',
        'Meta descriptions too short on 2 pages',
        'H1 tags missing on contact page',
        'No structured data markup',
      ],
      strengths: [
        'Good page titles',
        'Clean URL structure',
        'Proper heading hierarchy on most pages',
      ],
      details: {
        meta_tags_present: 8,
        meta_tags_missing: 4,
        alt_texts_missing: 3,
        structured_data: false,
      },
    },
    performance: {
      score: 72,
      issues: [
        'Large uncompressed images (1.2MB total)',
        'No lazy loading for images',
        'Render-blocking CSS',
        'No CDN usage',
      ],
      strengths: [
        'Minimal JavaScript',
        'Fast server response time',
      ],
      metrics: {
        page_load_time: 2.8,
        time_to_interactive: 3.2,
        first_contentful_paint: 1.1,
        total_page_size_mb: 1.8,
      },
    },
    accessibility: {
      score: 80,
      issues: [
        'Missing ARIA labels on 2 forms',
        'Insufficient color contrast on footer links',
        'Skip navigation link missing',
      ],
      strengths: [
        'Semantic HTML structure',
        'Keyboard navigation works',
        'Focus states visible',
      ],
      details: {
        wcag_level: 'AA',
        aria_labels_present: 12,
        aria_labels_missing: 2,
      },
    },
    title: 'Acme Design Studio - Professional Web Design Services',
    meta_description: 'Professional web design services for small businesses with 10+ years of experience.',
    improvements: [
      {
        id: 'imp_001',
        category: 'performance',
        priority: 'high',
        title: 'Optimize and compress images',
        description: 'Large images are slowing down page load times significantly.',
        current_state: '1.2MB total image size, no compression',
        proposed_change: 'Compress images to WebP format, implement lazy loading',
        impact: 'Reduce page load time by 40-50%, improve SEO ranking',
        difficulty: 'easy',
        time_estimate: '1-2 hours',
        code_example: '<img src="image.webp" loading="lazy" alt="Description">',
        resources: [
          'https://web.dev/optimize-images/',
          'https://squoosh.app/',
        ],
        dependencies: [],
      },
      {
        id: 'imp_002',
        category: 'seo',
        priority: 'high',
        title: 'Add structured data markup',
        description: 'Missing Schema.org markup for better search engine understanding.',
        current_state: 'No structured data present',
        proposed_change: 'Add Organization, Service, and Review schemas',
        impact: 'Improve search visibility, enable rich snippets',
        difficulty: 'medium',
        time_estimate: '2-3 hours',
        resources: [
          'https://schema.org/Organization',
          'https://developers.google.com/search/docs/advanced/structured-data',
        ],
        dependencies: [],
      },
      {
        id: 'imp_003',
        category: 'design',
        priority: 'medium',
        title: 'Standardize button styles',
        description: 'Inconsistent button styling across different pages.',
        current_state: 'Multiple button styles with varying colors and sizes',
        proposed_change: 'Create unified button component with consistent styling',
        impact: 'Improve brand consistency and user experience',
        difficulty: 'easy',
        time_estimate: '1 hour',
        resources: [],
        dependencies: [],
      },
      {
        id: 'imp_004',
        category: 'accessibility',
        priority: 'high',
        title: 'Add ARIA labels to forms',
        description: 'Contact and newsletter forms missing accessibility labels.',
        current_state: '2 forms without proper ARIA labels',
        proposed_change: 'Add aria-label and aria-describedby attributes',
        impact: 'Improve screen reader compatibility, meet WCAG AA standards',
        difficulty: 'easy',
        time_estimate: '30 minutes',
        code_example: '<input type="email" aria-label="Email address" aria-describedby="email-help">',
        resources: [
          'https://www.w3.org/WAI/WCAG21/quickref/',
        ],
        dependencies: [],
      },
      {
        id: 'imp_005',
        category: 'seo',
        priority: 'medium',
        title: 'Complete missing alt text',
        description: '3 images without descriptive alt attributes.',
        current_state: 'Portfolio images missing alt text',
        proposed_change: 'Add descriptive alt text to all images',
        impact: 'Improve accessibility and image SEO',
        difficulty: 'easy',
        time_estimate: '15 minutes',
        resources: [],
        dependencies: [],
      },
    ],
    improvements_summary: {
      total_improvements: 5,
      critical_priority: 0,
      high_priority: 3,
      medium_priority: 2,
      low_priority: 0,
      estimated_total_impact: 'High - significantly improve performance, SEO, and accessibility',
      estimated_total_time: '5-6.5 hours',
      quick_wins: 3,
      categories: {
        performance: 1,
        seo: 2,
        design: 1,
        accessibility: 1,
      },
    },
    status: 'completed',
    created_at: '2025-01-05T10:30:00Z',
  },

  // Poor quality site with many issues
  {
    id: 2,
    analysis_id: 'ana_def456',
    lead_id: 3,
    url: 'https://digitalgrowth.example.com',
    analyzed_at: '2025-01-05T11:00:00Z',
    overall_score: 42,
    design: {
      score: 38,
      issues: [
        'Outdated visual design (circa 2010)',
        'No responsive design - breaks on mobile',
        'Poor typography choices',
        'Cluttered layout with too many elements',
        'Inconsistent spacing',
        'Low quality images',
      ],
      strengths: [
        'Clear branding',
      ],
      metrics: {
        color_contrast_ratio: 2.8,
        whitespace_score: 42,
        consistency_score: 35,
      },
    },
    seo: {
      score: 35,
      issues: [
        'Duplicate title tags',
        'Missing meta descriptions on all pages',
        'No heading tags used properly',
        'Broken internal links (5 found)',
        'No sitemap.xml',
        'No robots.txt',
      ],
      strengths: [],
      details: {
        meta_tags_present: 2,
        meta_tags_missing: 12,
        alt_texts_missing: 15,
        structured_data: false,
      },
    },
    performance: {
      score: 48,
      issues: [
        'Extremely slow page load (8.5s)',
        'Massive image files (4.2MB)',
        'Multiple render-blocking scripts',
        'No caching headers',
        'Inline CSS causing bloat',
      ],
      strengths: [],
      metrics: {
        page_load_time: 8.5,
        time_to_interactive: 10.2,
        first_contentful_paint: 4.1,
        total_page_size_mb: 5.3,
      },
    },
    accessibility: {
      score: 45,
      issues: [
        'No ARIA labels anywhere',
        'Very poor color contrast',
        'Non-semantic HTML (all divs)',
        'No keyboard navigation support',
        'Missing alt text on all images',
      ],
      strengths: [],
      details: {
        wcag_level: 'Fail',
        aria_labels_present: 0,
        aria_labels_missing: 20,
      },
    },
    title: 'Digital Growth Co',
    meta_description: '',
    improvements: [
      {
        id: 'imp_006',
        category: 'design',
        priority: 'critical',
        title: 'Complete responsive redesign',
        description: 'Site completely breaks on mobile devices and tablets.',
        current_state: 'Fixed-width layout, no media queries, unusable on mobile',
        proposed_change: 'Implement mobile-first responsive design with breakpoints',
        impact: 'Make site usable on 70% of traffic currently bouncing',
        difficulty: 'hard',
        time_estimate: '16-20 hours',
        resources: [
          'https://web.dev/responsive-web-design-basics/',
        ],
        dependencies: [],
      },
      {
        id: 'imp_007',
        category: 'performance',
        priority: 'critical',
        title: 'Optimize massive image files',
        description: 'Images are 4.2MB total, causing 8+ second load times.',
        current_state: 'Uncompressed high-res images, no optimization',
        proposed_change: 'Compress to WebP, implement responsive images, lazy loading',
        impact: 'Reduce load time from 8.5s to ~2s, dramatically improve SEO',
        difficulty: 'medium',
        time_estimate: '3-4 hours',
        resources: [],
        dependencies: [],
      },
      {
        id: 'imp_008',
        category: 'seo',
        priority: 'critical',
        title: 'Implement complete SEO foundation',
        description: 'Missing all basic SEO elements - meta descriptions, proper headings, sitemap.',
        current_state: 'No meta descriptions, duplicate titles, broken links, no sitemap',
        proposed_change: 'Add all meta tags, fix heading structure, create sitemap, fix broken links',
        impact: 'Go from invisible to searchable, enable Google indexing',
        difficulty: 'medium',
        time_estimate: '4-5 hours',
        resources: [
          'https://developers.google.com/search/docs/beginner/seo-starter-guide',
        ],
        dependencies: [],
      },
    ],
    improvements_summary: {
      total_improvements: 3,
      critical_priority: 3,
      high_priority: 0,
      medium_priority: 0,
      low_priority: 0,
      estimated_total_impact: 'Critical - site is currently non-functional for most users',
      estimated_total_time: '23-29 hours',
      quick_wins: 0,
      categories: {
        design: 1,
        performance: 1,
        seo: 1,
      },
    },
    status: 'completed',
    created_at: '2025-01-05T11:00:00Z',
  },

  // Analysis in progress
  {
    id: 3,
    analysis_id: 'ana_ghi789',
    lead_id: 5,
    url: 'https://modernwebsolutions.example.com',
    analyzed_at: '2025-01-05T14:45:00Z',
    overall_score: 0,
    design: {
      score: 0,
      issues: [],
      strengths: [],
    },
    seo: {
      score: 0,
      issues: [],
      strengths: [],
    },
    performance: {
      score: 0,
      issues: [],
      strengths: [],
    },
    accessibility: {
      score: 0,
      issues: [],
      strengths: [],
    },
    title: '',
    meta_description: '',
    improvements: [],
    improvements_summary: {
      total_improvements: 0,
      critical_priority: 0,
      high_priority: 0,
      medium_priority: 0,
      low_priority: 0,
      estimated_total_impact: '',
      estimated_total_time: '',
      quick_wins: 0,
      categories: {},
    },
    status: 'analyzing',
    created_at: '2025-01-05T14:45:00Z',
  },
]

// Helper functions
export const getAnalysisByLeadId = (leadId: number) =>
  mockAnalyses.find(analysis => analysis.lead_id === leadId)

export const getCompletedAnalyses = () =>
  mockAnalyses.filter(analysis => analysis.status === 'completed')

export const getHighScoreAnalyses = (threshold: number = 70) =>
  mockAnalyses.filter(analysis => analysis.overall_score >= threshold)

export const getLowScoreAnalyses = (threshold: number = 50) =>
  mockAnalyses.filter(analysis => analysis.overall_score < threshold && analysis.overall_score > 0)

export const getCriticalImprovements = () =>
  mockAnalyses.flatMap(analysis =>
    analysis.improvements
      .filter(imp => imp.priority === 'critical')
      .map(imp => ({ ...imp, analysis_id: analysis.analysis_id, url: analysis.url }))
  )
