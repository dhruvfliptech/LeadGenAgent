import { useState } from 'react'

export default function TestScraper() {
  const [status, setStatus] = useState<string>('Testing...')
  const [errors, setErrors] = useState<string[]>([])

  const testEndpoints = async () => {
    const tests = [
      { name: 'Queue Status', url: 'http://localhost:8000/api/v1/scraper/queue/status' },
      { name: 'Jobs List', url: 'http://localhost:8000/api/v1/scraper/jobs' },
      { name: 'Locations Hierarchy', url: 'http://localhost:8000/api/v1/locations/hierarchy' },
      { name: 'Categories', url: 'http://localhost:8000/api/v1/scraper/categories/structured' },
    ]

    const results: string[] = []
    
    for (const test of tests) {
      try {
        const response = await fetch(test.url)
        if (response.ok) {
          results.push(`✅ ${test.name}: OK`)
        } else {
          results.push(`❌ ${test.name}: Status ${response.status}`)
        }
      } catch (error) {
        results.push(`❌ ${test.name}: ${error}`)
      }
    }
    
    setErrors(results)
    setStatus('Tests Complete')
  }

  useState(() => {
    testEndpoints()
  })

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Scraper Page Debug</h1>
      <div className="bg-gray-800 text-white p-4 rounded">
        <p className="mb-2">Status: {status}</p>
        <div className="space-y-1">
          {errors.map((err, i) => (
            <div key={i} className="font-mono text-sm">{err}</div>
          ))}
        </div>
      </div>
      
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Environment Variables:</h2>
        <div className="bg-gray-100 p-3 rounded">
          <p>VITE_API_URL: {import.meta.env.VITE_API_URL || 'Not set (using default)'}</p>
          <p>Default API URL: http://localhost:8000</p>
        </div>
      </div>
      
      <div className="mt-6">
        <button 
          onClick={() => window.location.href = '/scraper'}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Go to Real Scraper Page
        </button>
      </div>
    </div>
  )
}