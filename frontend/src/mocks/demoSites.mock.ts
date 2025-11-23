/**
 * Mock demo site data for generated sites
 */

import type {
  DemoSite,
  Framework,
  BuildStatus,
  DeploymentProvider,
  ValidationResult,
  ImprovementSummary,
  DeploymentConfig,
  AnalysisMetrics,
} from '../types/demoSite'

export const mockDemoSites: DemoSite[] = [
  // Completed React demo site
  {
    id: 1,
    build_id: 'build_react_abc123',
    lead_id: 1,
    lead_title: 'Acme Design Studio',
    lead_url: 'https://acmedesign.example.com',
    framework: 'react',
    status: 'completed',
    files: {
      'package.json': JSON.stringify({
        name: 'acme-design-demo',
        version: '1.0.0',
        dependencies: {
          react: '^18.2.0',
          'react-dom': '^18.2.0',
        },
      }, null, 2),
      'src/App.jsx': `import React from 'react'
import Hero from './components/Hero'
import Services from './components/Services'
import Portfolio from './components/Portfolio'
import Contact from './components/Contact'

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <Hero />
      <Services />
      <Portfolio />
      <Contact />
    </div>
  )
}`,
      'src/components/Hero.jsx': `export default function Hero() {
  return (
    <section className="py-20 px-4">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-5xl font-bold mb-4">Professional Web Design</h1>
        <p className="text-xl text-gray-600 mb-8">
          Transform your business with stunning, modern websites
        </p>
        <button className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700">
          Get Started
        </button>
      </div>
    </section>
  )
}`,
      'README.md': '# Acme Design Demo Site\n\nGenerated demo showcasing improved design.',
    },
    deployment_config: {
      framework: 'react',
      build_command: 'npm run build',
      install_command: 'npm install',
      output_directory: 'dist',
      dev_command: 'npm run dev',
      port: 3000,
    },
    improvements_applied: [
      {
        id: 'imp_001',
        title: 'Modern responsive design',
        category: 'design',
        priority: 'high',
        impact: 'Significantly improved mobile experience',
      },
      {
        id: 'imp_002',
        title: 'Performance optimization',
        category: 'performance',
        priority: 'high',
        impact: 'Reduced load time by 60%',
      },
      {
        id: 'imp_003',
        title: 'SEO enhancements',
        category: 'seo',
        priority: 'medium',
        impact: 'Better search visibility',
      },
    ],
    original_url: 'https://acmedesign.example.com',
    generation_time_seconds: 45,
    total_lines_of_code: 487,
    ai_model_used: 'claude-sonnet-4.5',
    ai_cost: 0.23,
    validation_results: {
      is_valid: true,
      errors: [],
      warnings: ['Consider adding error boundaries'],
      file_count: 5,
      total_size_bytes: 12847,
      has_required_files: true,
      placeholders_found: [],
    },
    analysis_metrics: {
      overall_score: 85,
      design_score: 88,
      seo_score: 82,
      performance_score: 90,
      accessibility_score: 86,
    },
    preview_url: 'https://acme-design-demo.vercel.app',
    deployment_provider: 'vercel',
    deployed_at: '2025-01-05T11:15:00Z',
    deployment_status: 'deployed',
    view_count: 47,
    click_count: 12,
    last_viewed_at: '2025-01-05T14:30:00Z',
    created_at: '2025-01-05T11:00:00Z',
    updated_at: '2025-01-05T11:15:00Z',
  },

  // HTML demo site - in progress
  {
    id: 2,
    build_id: 'build_html_def456',
    lead_id: 3,
    lead_title: 'Digital Growth Co',
    lead_url: 'https://digitalgrowth.example.com',
    framework: 'html',
    status: 'generating',
    files: {},
    deployment_config: {
      framework: 'html',
      build_command: 'echo "No build needed"',
      install_command: 'echo "No install needed"',
      output_directory: '.',
      dev_command: 'python -m http.server 8080',
      port: 8080,
    },
    improvements_applied: [],
    original_url: 'https://digitalgrowth.example.com',
    generation_time_seconds: 0,
    total_lines_of_code: 0,
    ai_model_used: 'gpt-4-turbo',
    ai_cost: 0,
    validation_results: {
      is_valid: false,
      errors: [],
      warnings: [],
      file_count: 0,
      total_size_bytes: 0,
      has_required_files: false,
      placeholders_found: [],
    },
    created_at: '2025-01-05T14:40:00Z',
    updated_at: '2025-01-05T14:40:00Z',
  },

  // Next.js demo site - completed and deployed
  {
    id: 3,
    build_id: 'build_next_ghi789',
    lead_id: 5,
    lead_title: 'Modern Web Solutions',
    lead_url: 'https://modernwebsolutions.example.com',
    framework: 'nextjs',
    status: 'completed',
    files: {
      'package.json': JSON.stringify({
        name: 'modern-web-demo',
        version: '1.0.0',
        dependencies: {
          next: '^14.0.0',
          react: '^18.2.0',
          'react-dom': '^18.2.0',
        },
      }, null, 2),
      'app/page.tsx': `export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-4">Modern Web Solutions</h1>
      <p className="text-lg">Beautiful, functional websites for businesses</p>
    </main>
  )
}`,
      'app/layout.tsx': `export const metadata = {
  title: 'Modern Web Solutions',
  description: 'Professional web development services',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}`,
      'README.md': '# Modern Web Solutions Demo\n\nNext.js demo with SSR.',
    },
    deployment_config: {
      framework: 'nextjs',
      build_command: 'npm run build',
      install_command: 'npm install',
      output_directory: '.next',
      dev_command: 'npm run dev',
      port: 3000,
    },
    improvements_applied: [
      {
        id: 'imp_010',
        title: 'Server-side rendering',
        category: 'performance',
        priority: 'high',
        impact: 'Faster initial page load',
      },
      {
        id: 'imp_011',
        title: 'SEO optimization',
        category: 'seo',
        priority: 'high',
        impact: 'Better search rankings',
      },
    ],
    original_url: 'https://modernwebsolutions.example.com',
    generation_time_seconds: 67,
    total_lines_of_code: 623,
    ai_model_used: 'claude-sonnet-4.5',
    ai_cost: 0.31,
    validation_results: {
      is_valid: true,
      errors: [],
      warnings: [],
      file_count: 4,
      total_size_bytes: 15234,
      has_required_files: true,
      placeholders_found: [],
    },
    analysis_metrics: {
      overall_score: 92,
      design_score: 90,
      seo_score: 95,
      performance_score: 94,
      accessibility_score: 89,
    },
    preview_url: 'https://modern-web-demo.vercel.app',
    deployment_provider: 'vercel',
    deployed_at: '2025-01-05T13:30:00Z',
    deployment_status: 'deployed',
    view_count: 23,
    click_count: 8,
    last_viewed_at: '2025-01-05T14:15:00Z',
    created_at: '2025-01-05T13:00:00Z',
    updated_at: '2025-01-05T13:30:00Z',
  },

  // Failed demo site
  {
    id: 4,
    build_id: 'build_react_jkl012',
    lead_id: 11,
    lead_title: 'Design Pro',
    lead_url: 'https://designpro.example.com',
    framework: 'react',
    status: 'failed',
    files: {},
    deployment_config: {
      framework: 'react',
      build_command: 'npm run build',
      install_command: 'npm install',
      output_directory: 'dist',
      dev_command: 'npm run dev',
      port: 3000,
    },
    improvements_applied: [],
    original_url: 'https://designpro.example.com',
    generation_time_seconds: 15,
    total_lines_of_code: 0,
    ai_model_used: 'gpt-4-turbo',
    ai_cost: 0.08,
    validation_results: {
      is_valid: false,
      errors: ['Failed to fetch original website', 'Connection timeout after 30s'],
      warnings: [],
      file_count: 0,
      total_size_bytes: 0,
      has_required_files: false,
      placeholders_found: [],
    },
    deployment_error: 'Source website unreachable',
    created_at: '2025-01-05T12:00:00Z',
    updated_at: '2025-01-05T12:15:00Z',
  },

  // Completed with Netlify deployment
  {
    id: 5,
    build_id: 'build_html_mno345',
    lead_id: 12,
    lead_title: 'Social Boost',
    lead_url: 'https://socialboost.example.com',
    framework: 'html',
    status: 'completed',
    files: {
      'index.html': `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Social Boost - Social Media Marketing</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 4rem 2rem;
    }
    h1 {
      color: white;
      font-size: 3rem;
      margin-bottom: 1rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Grow Your Social Media Presence</h1>
    <p style="color: white; font-size: 1.25rem;">Expert team helping you reach millions</p>
  </div>
</body>
</html>`,
      'styles.css': `/* Additional styles */
.button {
  background: white;
  color: #667eea;
  padding: 1rem 2rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
}`,
      'README.md': '# Social Boost Demo\n\nSimple, effective HTML demo.',
    },
    deployment_config: {
      framework: 'html',
      build_command: 'echo "Static HTML"',
      install_command: 'echo "No dependencies"',
      output_directory: '.',
      dev_command: 'python -m http.server 8080',
      port: 8080,
    },
    improvements_applied: [
      {
        id: 'imp_020',
        title: 'Modern gradient design',
        category: 'design',
        priority: 'medium',
        impact: 'More appealing visual style',
      },
      {
        id: 'imp_021',
        title: 'Mobile responsive',
        category: 'design',
        priority: 'high',
        impact: 'Works on all devices',
      },
    ],
    original_url: 'https://socialboost.example.com',
    generation_time_seconds: 28,
    total_lines_of_code: 142,
    ai_model_used: 'claude-sonnet-4.5',
    ai_cost: 0.12,
    validation_results: {
      is_valid: true,
      errors: [],
      warnings: [],
      file_count: 3,
      total_size_bytes: 4256,
      has_required_files: true,
      placeholders_found: [],
    },
    analysis_metrics: {
      overall_score: 78,
      design_score: 82,
      seo_score: 70,
      performance_score: 95,
      accessibility_score: 75,
    },
    preview_url: 'https://social-boost-demo.netlify.app',
    deployment_provider: 'netlify',
    deployed_at: '2025-01-04T16:45:00Z',
    deployment_status: 'deployed',
    view_count: 156,
    click_count: 42,
    last_viewed_at: '2025-01-05T14:20:00Z',
    created_at: '2025-01-04T16:30:00Z',
    updated_at: '2025-01-04T16:45:00Z',
  },
]

// Helper functions
export const getDemoSiteByLeadId = (leadId: number) =>
  mockDemoSites.find(site => site.lead_id === leadId)

export const getDemoSitesByStatus = (status: BuildStatus) =>
  mockDemoSites.filter(site => site.status === status)

export const getDemoSitesByFramework = (framework: Framework) =>
  mockDemoSites.filter(site => site.framework === framework)

export const getDeployedDemoSites = () =>
  mockDemoSites.filter(site => site.deployment_status === 'deployed')

export const getDemoSitesWithMetrics = () =>
  mockDemoSites.filter(site => site.analysis_metrics)

export const getTotalStats = () => ({
  total_demos: mockDemoSites.length,
  completed_demos: mockDemoSites.filter(s => s.status === 'completed').length,
  failed_demos: mockDemoSites.filter(s => s.status === 'failed').length,
  total_cost: mockDemoSites.reduce((sum, s) => sum + s.ai_cost, 0),
  avg_generation_time: mockDemoSites
    .filter(s => s.generation_time_seconds > 0)
    .reduce((sum, s) => sum + s.generation_time_seconds, 0) /
    mockDemoSites.filter(s => s.generation_time_seconds > 0).length,
  by_framework: {
    html: mockDemoSites.filter(s => s.framework === 'html').length,
    react: mockDemoSites.filter(s => s.framework === 'react').length,
    nextjs: mockDemoSites.filter(s => s.framework === 'nextjs').length,
  },
  by_status: {
    pending: mockDemoSites.filter(s => s.status === 'pending').length,
    analyzing: mockDemoSites.filter(s => s.status === 'analyzing').length,
    planning: mockDemoSites.filter(s => s.status === 'planning').length,
    generating: mockDemoSites.filter(s => s.status === 'generating').length,
    deploying: mockDemoSites.filter(s => s.status === 'deploying').length,
    completed: mockDemoSites.filter(s => s.status === 'completed').length,
    failed: mockDemoSites.filter(s => s.status === 'failed').length,
  },
  recent_demos: mockDemoSites.slice(0, 5),
})
