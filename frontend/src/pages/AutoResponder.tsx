import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Template, autoResponderApi } from '../services/phase3Api'
import TemplateEditor from '../components/TemplateEditor'
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  ChartBarIcon,
  
  BeakerIcon,
  ArrowTrendingUpIcon,
  
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ViewMode = 'list' | 'create' | 'edit' | 'analytics'

export default function AutoResponder() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  
  const queryClient = useQueryClient()

  // Fetch templates
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => autoResponderApi.getTemplates().then(res => res.data),
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: autoResponderApi.createTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setViewMode('list')
      toast.success('Template created successfully')
    },
    onError: () => {
      toast.error('Failed to create template')
    },
  })

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<Template>) =>
      autoResponderApi.updateTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setViewMode('list')
      setSelectedTemplate(null)
      toast.success('Template updated successfully')
    },
    onError: () => {
      toast.error('Failed to update template')
    },
  })

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: autoResponderApi.deleteTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete template')
    },
  })

  // A/B Test mutation
  const abTestMutation = useMutation({
    mutationFn: ({ templateId, variant }: { templateId: number; variant: Partial<Template> }) =>
      autoResponderApi.createABTest(templateId, variant),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('A/B test created successfully')
    },
    onError: () => {
      toast.error('Failed to create A/B test')
    },
  })

  const filteredTemplates = templates.filter(template => 
    selectedCategory === 'all' || template.category === selectedCategory
  )

  const categories = ['all', ...Array.from(new Set(templates.map(t => t.category)))]

  const handleSaveTemplate = (templateData: Omit<Template, 'id' | 'created_at' | 'updated_at'>) => {
    if (selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate.id, ...templateData })
    } else {
      createMutation.mutate(templateData)
    }
  }

  const handleEditTemplate = (template: Template) => {
    setSelectedTemplate(template)
    setViewMode('edit')
  }

  const handleDeleteTemplate = (id: number) => {
    if (confirm('Are you sure you want to delete this template?')) {
      deleteMutation.mutate(id)
    }
  }

  const handleCreateABTest = (template: Template) => {
    const variant = {
      ...template,
      name: `${template.name} - Variant B`,
      subject: template.subject + ' (Variant B)',
    }
    abTestMutation.mutate({ templateId: template.id, variant })
  }

  const renderTemplateCard = (template: Template) => (
    <div key={template.id} className="card-terminal p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-terminal-400 font-mono">
            {template.name}
          </h3>
          <p className="text-dark-text-secondary text-sm mt-1">
            Category: {template.category}
          </p>
          <p className="text-dark-text-muted text-sm">
            Subject: {template.subject}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`status-${template.is_active ? 'online' : 'offline'}`}>
            {template.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Performance Metrics */}
      {template.performance_metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-dark-bg p-2 rounded border border-dark-border">
            <div className="text-xs text-dark-text-secondary">Open Rate</div>
            <div className="text-terminal-400 font-mono font-bold">
              {(template.performance_metrics.open_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-dark-bg p-2 rounded border border-dark-border">
            <div className="text-xs text-dark-text-secondary">Response Rate</div>
            <div className="text-terminal-400 font-mono font-bold">
              {(template.performance_metrics.response_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-dark-bg p-2 rounded border border-dark-border">
            <div className="text-xs text-dark-text-secondary">Conversion Rate</div>
            <div className="text-terminal-400 font-mono font-bold">
              {(template.performance_metrics.conversion_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-dark-bg p-2 rounded border border-dark-border">
            <div className="text-xs text-dark-text-secondary">Total Sent</div>
            <div className="text-terminal-400 font-mono font-bold">
              {template.performance_metrics.total_sent.toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* A/B Test Results */}
      {template.ab_test_data && (
        <div className="bg-dark-bg border border-terminal-500/30 rounded p-3 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-terminal-400 font-mono text-sm">A/B Test Results</span>
            {template.ab_test_data.winner && (
              <span className="text-xs bg-terminal-500/20 text-terminal-400 px-2 py-1 rounded">
                Winner: Variant {template.ab_test_data.winner}
              </span>
            )}
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-xs text-dark-text-secondary mb-1">Variant A</div>
              <div className="text-xs space-y-1">
                <div>Open: {(template.ab_test_data.variant_a_stats.open_rate * 100).toFixed(1)}%</div>
                <div>Response: {(template.ab_test_data.variant_a_stats.response_rate * 100).toFixed(1)}%</div>
              </div>
            </div>
            <div>
              <div className="text-xs text-dark-text-secondary mb-1">Variant B</div>
              <div className="text-xs space-y-1">
                <div>Open: {(template.ab_test_data.variant_b_stats.open_rate * 100).toFixed(1)}%</div>
                <div>Response: {(template.ab_test_data.variant_b_stats.response_rate * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <button
            onClick={() => handleEditTemplate(template)}
            className="btn-secondary text-xs"
          >
            <PencilIcon className="w-3 h-3 mr-1" />
            Edit
          </button>
          
          {!template.ab_test_data && (
            <button
              onClick={() => handleCreateABTest(template)}
              className="btn-terminal text-xs"
            >
              <BeakerIcon className="w-3 h-3 mr-1" />
              A/B Test
            </button>
          )}
        </div>
        
        <button
          onClick={() => handleDeleteTemplate(template.id)}
          className="btn-danger text-xs"
        >
          <TrashIcon className="w-3 h-3" />
        </button>
      </div>
    </div>
  )

  const renderTemplateList = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Auto-Responder Templates
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Manage email templates and A/B test performance
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setViewMode('analytics')}
            className="btn-terminal"
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            Analytics
          </button>
          <button
            onClick={() => setViewMode('create')}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Template
          </button>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex space-x-2 overflow-x-auto">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`btn text-sm whitespace-nowrap ${
              selectedCategory === category ? 'btn-terminal-solid' : 'btn-secondary'
            }`}
          >
            {category === 'all' ? 'All Categories' : category.replace('_', ' ').toUpperCase()}
          </button>
        ))}
      </div>

      {/* Templates Grid */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-text-secondary mt-2">Loading templates...</div>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-dark-text-muted mb-4">
            {selectedCategory === 'all' ? 'No templates found' : `No templates in ${selectedCategory} category`}
          </div>
          <button
            onClick={() => setViewMode('create')}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Your First Template
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTemplates.map(renderTemplateCard)}
        </div>
      )}
    </div>
  )

  const renderAnalytics = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Template Analytics
        </h1>
        <button
          onClick={() => setViewMode('list')}
          className="btn-secondary"
        >
          Back to Templates
        </button>
      </div>

      {/* Overall Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Templates</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {templates.length}
              </p>
            </div>
            <ArrowTrendingUpIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Active Templates</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {templates.filter(t => t.is_active).length}
              </p>
            </div>
            <ArrowTrendingUpIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Avg Open Rate</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {templates.filter(t => t.performance_metrics).length > 0 ? 
                  (templates
                    .filter(t => t.performance_metrics)
                    .reduce((acc, t) => acc + (t.performance_metrics?.open_rate || 0), 0) /
                    templates.filter(t => t.performance_metrics).length * 100
                  ).toFixed(1) + '%'
                  : 'N/A'
                }
              </p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">A/B Tests</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {templates.filter(t => t.ab_test_data).length}
              </p>
            </div>
            <BeakerIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
      </div>

      {/* Performance Table */}
      <div className="card-terminal">
        <div className="p-4 border-b border-dark-border">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono">
            Template Performance
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="table-terminal">
            <thead>
              <tr>
                <th>Template</th>
                <th>Category</th>
                <th>Open Rate</th>
                <th>Response Rate</th>
                <th>Conversion Rate</th>
                <th>Total Sent</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {templates.map(template => (
                <tr key={template.id}>
                  <td className="font-medium">{template.name}</td>
                  <td>{template.category}</td>
                  <td>
                    {template.performance_metrics ? 
                      `${(template.performance_metrics.open_rate * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </td>
                  <td>
                    {template.performance_metrics ? 
                      `${(template.performance_metrics.response_rate * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </td>
                  <td>
                    {template.performance_metrics ? 
                      `${(template.performance_metrics.conversion_rate * 100).toFixed(1)}%` : 
                      'N/A'
                    }
                  </td>
                  <td>
                    {template.performance_metrics ? 
                      template.performance_metrics.total_sent.toLocaleString() : 
                      'N/A'
                    }
                  </td>
                  <td>
                    <span className={`status-${template.is_active ? 'online' : 'offline'}`}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  // Render based on view mode
  if (viewMode === 'create' || viewMode === 'edit') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            {viewMode === 'create' ? 'Create Template' : 'Edit Template'}
          </h1>
          <button
            onClick={() => {
              setViewMode('list')
              setSelectedTemplate(null)
            }}
            className="btn-secondary"
          >
            Back to Templates
          </button>
        </div>
        
        <TemplateEditor
          template={selectedTemplate || undefined}
          onSave={handleSaveTemplate}
          onCancel={() => {
            setViewMode('list')
            setSelectedTemplate(null)
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      </div>
    )
  }

  if (viewMode === 'analytics') {
    return renderAnalytics()
  }

  return renderTemplateList()
}