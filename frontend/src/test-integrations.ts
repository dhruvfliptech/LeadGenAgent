// @ts-nocheck

/**
 * Frontend Integration Test Utility
 *
 * Run this in the browser console to verify all API integrations are working
 * Usage: import('./test-integrations.js').then(m => m.testIntegrations())
 */

import { api } from './services/api'
import { emailTrackingApi } from './services/emailTrackingApi'
import { workflowsApi } from './services/workflowsApi'
import { demoSitesApi } from './services/demoSitesApi'

interface TestResult {
  name: string
  success: boolean
  data?: any
  error?: string
  duration?: number
}

const results: TestResult[] = []

async function runTest(name: string, testFn: () => Promise<any>): Promise<void> {
  const startTime = performance.now()
  try {
    console.log(`🧪 Testing ${name}...`)
    const data = await testFn()
    const duration = performance.now() - startTime
    results.push({ name, success: true, data, duration })
    console.log(`✅ ${name} - ${duration.toFixed(0)}ms`)
  } catch (error: any) {
    const duration = performance.now() - startTime
    results.push({ name, success: false, error: error.message, duration })
    console.error(`❌ ${name} - ${error.message}`)
  }
}

export async function testIntegrations() {
  console.group('🧪 Frontend API Integration Tests')
  console.log('Testing connection to backend API...\n')

  results.length = 0 // Clear previous results

  // ==================== Templates API ====================
  console.group('📧 Templates API')

  await runTest('GET /templates', async () => {
    const response = await api.get('/templates')
    if (!Array.isArray(response.data)) {
      throw new Error('Expected array of templates')
    }
    return { count: response.data.length, templates: response.data }
  })

  await runTest('GET /templates/{id}', async () => {
    const response = await api.get('/templates/1')
    if (!response.data.id) {
      throw new Error('Expected template object with id')
    }
    return response.data
  })

  console.groupEnd()

  // ==================== Email Tracking API ====================
  console.group('📊 Email Tracking API')

  await runTest('Email Tracking - Create URL', async () => {
    const trackingUrl = emailTrackingApi.createTrackingUrl('test-token', 'https://example.com')
    if (!trackingUrl.includes('test-token')) {
      throw new Error('Tracking URL missing token')
    }
    return { url: trackingUrl }
  })

  console.groupEnd()

  // ==================== Workflows API ====================
  console.group('🔄 Workflows API')

  await runTest('GET /n8n-webhooks/workflows', async () => {
    const response = await workflowsApi.getWorkflows()
    if (!Array.isArray(response.data)) {
      throw new Error('Expected array of workflows')
    }
    return { count: response.data.length, workflows: response.data }
  })

  await runTest('GET /n8n-webhooks/stats', async () => {
    const response = await workflowsApi.getStats()
    return response.data
  })

  await runTest('GET /approvals/pending', async () => {
    const response = await workflowsApi.getPendingApprovals()
    if (!Array.isArray(response.data)) {
      throw new Error('Expected array of approvals')
    }
    return { count: response.data.length, approvals: response.data }
  })

  console.groupEnd()

  // ==================== Demo Sites API ====================
  console.group('🌐 Demo Sites API')

  await runTest('GET /demo-sites', async () => {
    const response = await demoSitesApi.getDemoSites()
    if (!Array.isArray(response.data)) {
      throw new Error('Expected array of demo sites')
    }
    return { count: response.data.length, sites: response.data }
  })

  console.groupEnd()

  // ==================== Summary ====================
  console.log('\n')
  console.group('📊 Test Summary')

  const totalTests = results.length
  const passedTests = results.filter(r => r.success).length
  const failedTests = results.filter(r => !r.success).length
  const avgDuration = results.reduce((sum, r) => sum + (r.duration || 0), 0) / totalTests

  console.log(`Total Tests: ${totalTests}`)
  console.log(`✅ Passed: ${passedTests}`)
  console.log(`❌ Failed: ${failedTests}`)
  console.log(`⏱️  Average Duration: ${avgDuration.toFixed(0)}ms`)
  console.log('\n')

  if (failedTests > 0) {
    console.group('Failed Tests:')
    results.filter(r => !r.success).forEach(r => {
      console.log(`- ${r.name}: ${r.error}`)
    })
    console.groupEnd()
  }

  console.groupEnd()
  console.groupEnd()

  // Return results for programmatic access
  return {
    total: totalTests,
    passed: passedTests,
    failed: failedTests,
    avgDuration,
    results
  }
}

// ==================== Individual Test Functions ====================

export async function testTemplatesAPI() {
  console.group('📧 Templates API Test')

  try {
    // Test GET all templates
    console.log('1. Fetching all templates...')
    const templates = await api.get('/templates')
    console.log(`✅ Found ${templates.data.length} templates`)

    // Test GET single template
    if (templates.data.length > 0) {
      const firstTemplate = templates.data[0]
      console.log(`2. Fetching template ${firstTemplate.id}...`)
      const template = await api.get(`/templates/${firstTemplate.id}`)
      console.log('✅ Template details:', template.data)
    }

    console.log('\n🎉 Templates API is working!')
  } catch (error: any) {
    console.error('❌ Templates API test failed:', error.message)
  }

  console.groupEnd()
}

export async function testWorkflowsAPI() {
  console.group('🔄 Workflows API Test')

  try {
    // Test GET workflows
    console.log('1. Fetching workflows...')
    const workflows = await workflowsApi.getWorkflows()
    console.log(`✅ Found ${workflows.data.length} workflows`)

    // Test GET stats
    console.log('2. Fetching workflow stats...')
    const stats = await workflowsApi.getStats()
    console.log('✅ Workflow stats:', stats.data)

    // Test GET pending approvals
    console.log('3. Fetching pending approvals...')
    const approvals = await workflowsApi.getPendingApprovals()
    console.log(`✅ Found ${approvals.data.length} pending approvals`)

    console.log('\n🎉 Workflows API is working!')
  } catch (error: any) {
    console.error('❌ Workflows API test failed:', error.message)
  }

  console.groupEnd()
}

export async function testEmailTrackingAPI() {
  console.group('📊 Email Tracking API Test')

  try {
    // Test tracking URL generation
    console.log('1. Creating tracking URL...')
    const trackingUrl = emailTrackingApi.createTrackingUrl('test-123', 'https://example.com')
    console.log('✅ Tracking URL:', trackingUrl)

    console.log('\n🎉 Email Tracking API is working!')
  } catch (error: any) {
    console.error('❌ Email Tracking API test failed:', error.message)
  }

  console.groupEnd()
}

export async function testDemoSitesAPI() {
  console.group('🌐 Demo Sites API Test')

  try {
    // Test GET demo sites
    console.log('1. Fetching demo sites...')
    const sites = await demoSitesApi.getDemoSites()
    console.log(`✅ Found ${sites.data.length} demo sites`)

    console.log('\n🎉 Demo Sites API is working!')
  } catch (error: any) {
    console.error('❌ Demo Sites API test failed:', error.message)
  }

  console.groupEnd()
}

// Make functions available globally for easy console access
if (typeof window !== 'undefined') {
  (window as any).testIntegrations = testIntegrations
  (window as any).testTemplatesAPI = testTemplatesAPI
  (window as any).testWorkflowsAPI = testWorkflowsAPI
  (window as any).testEmailTrackingAPI = testEmailTrackingAPI
  (window as any).testDemoSitesAPI = testDemoSitesAPI
}

export default testIntegrations
