import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { mockTemplates } from '@/mocks/campaigns.mock'
import { api } from '@/services/api'
import { EmailTemplate, EmailTemplateCreate, EmailTemplateUpdate } from '@/types/campaign'
import EmailTemplateEditor from '@/components/EmailTemplateEditor'
import TemplatePreview from '@/components/TemplatePreview'
import { PlusIcon, EyeIcon, PencilIcon, TrashIcon, DocumentDuplicateIcon as DuplicateIcon, TagIcon, XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

// Environment flag for mock data
const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA === 'true'

const AVAILABLE_TAGS = [
  { name: 'Cold Outreach', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  { name: 'Follow-up', color: 'bg-green-100 text-green-800 border-green-200' },
  { name: 'Introduction', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  { name: 'Sales', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  { name: 'Real Estate', color: 'bg-red-100 text-red-800 border-red-200' },
  { name: 'Web Design', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  { name: 'Marketing', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  { name: 'B2B', color: 'bg-teal-100 text-teal-800 border-teal-200' },
  { name: 'B2C', color: 'bg-pink-100 text-pink-800 border-pink-200' },
]

const AVAILABLE_CATEGORIES = [
  'All Templates',
  'Cold Outreach',
  'Follow-ups',
  'Introductions',
  'Sales Pitches',
  'Event Invitations',
  'Proposals',
]

export default function Templates() {
  const queryClient = useQueryClient()
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null)
  const [selectedTemplates, setSelectedTemplates] = useState<Set<number>>(new Set())
  const [isCreating, setIsCreating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('All Templates')
  const [searchQuery, setSearchQuery] = useState('')

  // Form state for creating/editing
  const [formData, setFormData] = useState({
    name: '',
    subject_template: '',
    body_template: '',
    body_text: '',
    tags: [] as string[],
    category: '',
    description: '',
    use_ai_enhancement: false,
    ai_tone: 'professional',
    ai_length: 'medium',
  })

  // Fetch templates from API or use mock data
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      if (USE_MOCK_DATA) {
        return mockTemplates
      }
      const response = await api.get<EmailTemplate[]>('/templates')
      return response.data
    },
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: async (data: EmailTemplateCreate) => {
      const response = await api.post('/templates', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template created successfully!')
      setIsCreating(false)
      setFormData({
        name: '',
        subject_template: '',
        body_template: '',
        body_text: '',
        tags: [],
        category: '',
        description: '',
        use_ai_enhancement: false,
        ai_tone: 'professional',
        ai_length: 'medium',
      })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create template')
    },
  })

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: EmailTemplateUpdate }) => {
      const response = await api.put(`/templates/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template updated successfully!')
      setIsEditing(false)
      setSelectedTemplate(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update template')
    },
  })

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/templates/${id}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template deleted successfully!')
      if (selectedTemplate) {
        setSelectedTemplate(null)
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete template')
    },
  })

  // Get tag color
  const getTagColor = (tagName: string) => {
    const tag = AVAILABLE_TAGS.find(t => t.name === tagName)
    return tag?.color || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  // Filter templates
  const filteredTemplates = templates.filter((template: any) => {
    const matchesCategory = selectedCategory === 'All Templates' ||
      template.category === selectedCategory
    const matchesSearch = searchQuery === '' ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (template.subject_template || template.subject || '').toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  // Add/remove tag
  const toggleTag = (tagName: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.includes(tagName)
        ? prev.tags.filter(t => t !== tagName)
        : [...prev.tags, tagName]
    }))
  }

  // Bulk selection
  const toggleTemplateSelection = (id: number) => {
    const newSelected = new Set(selectedTemplates)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedTemplates(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedTemplates.size === filteredTemplates.length) {
      setSelectedTemplates(new Set())
    } else {
      setSelectedTemplates(new Set(filteredTemplates.map(t => t.id)))
    }
  }

  const handleBulkAction = (action: string) => {
    toast.success(`${action} applied to ${selectedTemplates.size} templates`)
    setSelectedTemplates(new Set())
  }

  const handleCreateNew = () => {
    setIsCreating(true)
    setIsEditing(false)
    setSelectedTemplate(null)
    setFormData({
      name: '',
      subject_template: '',
      body_template: '',
      body_text: '',
      tags: [],
      category: '',
      description: '',
      use_ai_enhancement: false,
      ai_tone: 'professional',
      ai_length: 'medium',
    })
  }

  const handleEdit = (templateId: number) => {
    const template: any = templates.find((t: any) => t.id === templateId)
    if (template) {
      setIsCreating(false)
      setIsEditing(true)
      setSelectedTemplate(templateId)

      // Extract tags from variables object if it exists
      let tags: string[] = []
      if (template.variables && typeof template.variables === 'object') {
        tags = Object.keys(template.variables)
      } else if (Array.isArray(template.variables)) {
        tags = template.variables
      } else if (template.tags) {
        tags = template.tags
      }

      setFormData({
        name: template.name,
        subject_template: template.subject_template || template.subject || '',
        body_template: template.body_template || template.body_html || '',
        body_text: template.body_text || '',
        tags,
        category: template.category || '',
        description: template.description || '',
        use_ai_enhancement: template.use_ai_enhancement || false,
        ai_tone: template.ai_tone || 'professional',
        ai_length: template.ai_length || 'medium',
      })
    }
  }

  const handleView = (templateId: number) => {
    setIsCreating(false)
    setIsEditing(false)
    setSelectedTemplate(templateId)
  }

  const handleSave = () => {
    // Prepare data with variables from tags
    const variables: Record<string, string> = {}
    formData.tags.forEach(tag => {
      variables[tag] = tag
    })

    const data: EmailTemplateCreate = {
      name: formData.name,
      subject_template: formData.subject_template,
      body_template: formData.body_template,
      category: formData.category || undefined,
      description: formData.description || undefined,
      variables,
      use_ai_enhancement: formData.use_ai_enhancement,
      ai_tone: formData.ai_tone,
      ai_length: formData.ai_length,
    }

    if (isEditing && selectedTemplate) {
      updateMutation.mutate({ id: selectedTemplate, data })
    } else {
      createMutation.mutate(data)
    }
  }

  const handleCancel = () => {
    setIsCreating(false)
    setIsEditing(false)
    setSelectedTemplate(null)
  }

  const handleDuplicate = (templateId: number) => {
    const template: any = templates.find((t: any) => t.id === templateId)
    if (template) {
      const data: EmailTemplateCreate = {
        name: `${template.name} (Copy)`,
        subject_template: template.subject_template || template.subject,
        body_template: template.body_template || template.body_html,
        category: template.category,
        description: template.description,
        variables: template.variables,
        use_ai_enhancement: template.use_ai_enhancement,
        ai_tone: template.ai_tone,
        ai_length: template.ai_length,
      }
      createMutation.mutate(data)
    }
  }

  const handleDelete = (templateId: number) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      deleteMutation.mutate(templateId)
    }
  }

  const currentTemplate: any = selectedTemplate
    ? templates.find((t: any) => t.id === selectedTemplate)
    : null

  // Show loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-dark-text-primary">Email Templates</h1>
            <p className="mt-1 text-sm text-dark-text-secondary">
              Loading templates...
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="card p-6 animate-pulse">
              <div className="h-8 bg-dark-border rounded mb-4"></div>
              <div className="h-8 bg-dark-border rounded mb-4"></div>
              <div className="h-8 bg-dark-border rounded"></div>
            </div>
          </div>
          <div className="lg:col-span-2">
            <div className="card p-6 animate-pulse">
              <div className="h-12 bg-dark-border rounded mb-4"></div>
              <div className="h-64 bg-dark-border rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">Email Templates</h1>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Create and manage reusable email templates
          </p>
        </div>
        <button
          onClick={handleCreateNew}
          className="btn-primary"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Template
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Templates List */}
        <div className="lg:col-span-1 space-y-4">
          {/* Category Filter */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold text-dark-text-primary mb-3 flex items-center gap-2">
              <TagIcon className="h-4 w-4" />
              Categories
            </h3>
            <div className="space-y-1">
              {AVAILABLE_CATEGORIES.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                    selectedCategory === category
                      ? 'bg-terminal-500/20 text-terminal-400 font-medium'
                      : 'text-dark-text-secondary hover:bg-dark-border/50'
                  }`}
                >
                  {category}
                  {category === 'All Templates' && ` (${templates.length})`}
                </button>
              ))}
            </div>
          </div>

          {/* Search Bar */}
          <div className="card p-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search templates..."
              className="form-input"
            />
          </div>

          {/* Bulk Actions Bar */}
          {selectedTemplates.size > 0 && (
            <div className="bg-terminal-500/10 border border-terminal-500/20 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-dark-text-primary">
                  {selectedTemplates.size} template{selectedTemplates.size !== 1 ? 's' : ''} selected
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleBulkAction('Duplicate')}
                    className="btn-secondary text-sm"
                  >
                    <DuplicateIcon className="w-4 h-4" />
                    Duplicate
                  </button>
                  <button
                    onClick={() => handleBulkAction('Change Category')}
                    className="btn-secondary text-sm"
                  >
                    <TagIcon className="w-4 h-4" />
                    Category
                  </button>
                  <button
                    onClick={() => handleBulkAction('Export')}
                    className="btn-secondary text-sm"
                  >
                    <ArrowDownTrayIcon className="w-4 h-4" />
                    Export
                  </button>
                  <button
                    onClick={() => handleBulkAction('Delete')}
                    className="btn-secondary text-sm text-red-500 hover:text-red-400"
                  >
                    <TrashIcon className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Templates List */}
          <div className="card">
            <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
              <h2 className="text-sm font-semibold text-dark-text-primary">
                Templates ({filteredTemplates.length})
              </h2>
              <input
                type="checkbox"
                checked={selectedTemplates.size === filteredTemplates.length && filteredTemplates.length > 0}
                onChange={toggleSelectAll}
                className="form-checkbox"
                title="Select all"
              />
            </div>
            <div className="divide-y divide-dark-border max-h-96 overflow-y-auto">
              {filteredTemplates.map((template) => (
                <div
                  key={template.id}
                  className={`p-4 hover:bg-dark-border/30 transition-colors ${
                    selectedTemplate === template.id ? 'bg-terminal-500/10' : ''
                  } ${selectedTemplates.has(template.id) ? 'bg-terminal-500/5' : ''}`}
                >
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedTemplates.has(template.id)}
                      onChange={(e) => {
                        e.stopPropagation()
                        toggleTemplateSelection(template.id)
                      }}
                      className="form-checkbox mt-1"
                    />
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => handleView(template.id)}
                    >
                      <h3 className="text-sm font-medium text-dark-text-primary">
                        {template.name}
                      </h3>
                      <p className="text-xs text-dark-text-secondary mt-1 line-clamp-2">
                        {template.subject_template || template.subject}
                      </p>
                      <div className="flex flex-wrap items-center mt-2 gap-1">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-dark-border text-dark-text-secondary">
                          {template.variables ? Object.keys(template.variables).length : 0} variables
                        </span>
                        {template.tags && template.tags.slice(0, 2).map((tag: string) => (
                          <span
                            key={tag}
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getTagColor(tag)}`}
                          >
                            {tag}
                          </span>
                        ))}
                        {template.tags && template.tags.length > 2 && (
                          <span className="text-xs text-dark-text-muted">
                            +{template.tags.length - 2} more
                          </span>
                        )}
                      </div>
                      <div className="mt-3 flex items-center space-x-2">
                    <button
                      onClick={() => handleView(template.id)}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-terminal-400 hover:text-terminal-300"
                      title="View"
                    >
                      <EyeIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleEdit(template.id)}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-dark-text-secondary hover:text-dark-text-primary"
                      title="Edit"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDuplicate(template.id)}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-dark-text-secondary hover:text-dark-text-primary"
                      title="Duplicate"
                    >
                      <DuplicateIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="inline-flex items-center px-2 py-1 text-xs font-medium text-red-400 hover:text-red-300"
                      title="Delete"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Editor/Preview Panel */}
        <div className="lg:col-span-2">
          {(isCreating || isEditing) ? (
            <div className="card p-6">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-dark-text-primary">
                  {isCreating ? 'Create New Template' : 'Edit Template'}
                </h2>
              </div>

              {/* Template Name */}
              <div className="mb-6">
                <label className="form-label">
                  Template Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Web Design Introduction"
                  className="form-input"
                />
              </div>

              {/* Category */}
              <div className="mb-6">
                <label className="form-label">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="form-input"
                >
                  <option value="">Select a category...</option>
                  {AVAILABLE_CATEGORIES.filter(c => c !== 'All Templates').map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>

              {/* Tags */}
              <div className="mb-6">
                <label className="form-label mb-2">
                  Tags
                </label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {formData.tags.map((tag) => (
                    <span
                      key={tag}
                      className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium border ${getTagColor(tag)}`}
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => toggleTag(tag)}
                        className="ml-1 hover:text-red-400"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </span>
                  ))}
                  {formData.tags.length === 0 && (
                    <span className="text-sm text-dark-text-muted italic">No tags selected</span>
                  )}
                </div>
                <div className="bg-dark-border/30 border border-dark-border rounded-lg p-3">
                  <p className="text-xs text-dark-text-secondary mb-2">Available Tags:</p>
                  <div className="flex flex-wrap gap-2">
                    {AVAILABLE_TAGS.map((tag) => (
                      <button
                        key={tag.name}
                        type="button"
                        onClick={() => toggleTag(tag.name)}
                        disabled={formData.tags.includes(tag.name)}
                        className={`px-3 py-1 rounded-md text-sm font-medium border transition-all ${
                          formData.tags.includes(tag.name)
                            ? 'opacity-50 cursor-not-allowed'
                            : 'hover:scale-105 cursor-pointer'
                        } ${tag.color}`}
                      >
                        + {tag.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Template Editor */}
              <EmailTemplateEditor
                subject={formData.subject_template}
                bodyHtml={formData.body_template}
                bodyText={formData.body_text}
                onSubjectChange={(subject) => setFormData({ ...formData, subject_template: subject })}
                onBodyHtmlChange={(body_html) => setFormData({ ...formData, body_template: body_html })}
                onBodyTextChange={(body_text) => setFormData({ ...formData, body_text })}
              />

              {/* Preview */}
              <div className="mt-6">
                <h3 className="text-sm font-medium text-dark-text-primary mb-2">Preview</h3>
                <TemplatePreview subject={formData.subject_template} bodyHtml={formData.body_template} />
              </div>

              {/* Actions */}
              <div className="mt-6 flex items-center justify-end space-x-3">
                <button
                  onClick={handleCancel}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!formData.name || !formData.subject_template || createMutation.isPending || updateMutation.isPending}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Saving...'
                    : isCreating
                    ? 'Create Template'
                    : 'Save Changes'}
                </button>
              </div>
            </div>
          ) : currentTemplate ? (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary">
                    {currentTemplate.name}
                  </h2>
                  <p className="text-sm text-dark-text-secondary mt-1">
                    Created {new Date(currentTemplate.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleEdit(currentTemplate.id)}
                  className="btn-secondary"
                >
                  <PencilIcon className="h-4 w-4 mr-1" />
                  Edit
                </button>
              </div>

              {/* Variables */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-dark-text-primary mb-2">Variables Used</h3>
                <div className="flex flex-wrap gap-2">
                  {(() => {
                    const vars = currentTemplate.variables
                    const varArray = typeof vars === 'object' && !Array.isArray(vars)
                      ? Object.keys(vars)
                      : Array.isArray(vars)
                      ? vars
                      : []
                    return varArray.map((variable: string) => (
                      <span
                        key={variable}
                        className="inline-flex items-center px-2.5 py-1 rounded text-xs font-mono bg-dark-border text-dark-text-secondary"
                      >
                        {`{{${variable}}}`}
                      </span>
                    ))
                  })()}
                </div>
              </div>

              {/* Preview */}
              <div>
                <h3 className="text-sm font-medium text-dark-text-primary mb-2">Preview</h3>
                <TemplatePreview
                  subject={currentTemplate.subject_template || currentTemplate.subject}
                  bodyHtml={currentTemplate.body_template || currentTemplate.body_html}
                />
              </div>

              {/* Raw HTML (Collapsible) */}
              <details className="mt-6">
                <summary className="text-sm font-medium text-dark-text-primary cursor-pointer hover:text-terminal-400">
                  View Raw HTML
                </summary>
                <pre className="mt-2 p-4 bg-dark-border/30 rounded-md text-xs overflow-x-auto text-dark-text-secondary">
                  <code>{currentTemplate.body_template || currentTemplate.body_html}</code>
                </pre>
              </details>

              {/* Plain Text Version */}
              <details className="mt-4">
                <summary className="text-sm font-medium text-dark-text-primary cursor-pointer hover:text-terminal-400">
                  View Plain Text Version
                </summary>
                <pre className="mt-2 p-4 bg-dark-border/30 rounded-md text-xs whitespace-pre-wrap text-dark-text-secondary">
                  {currentTemplate.body_text}
                </pre>
              </details>
            </div>
          ) : (
            <div className="card p-12 text-center">
              <PlusIcon className="mx-auto h-12 w-12 text-dark-text-muted" />
              <h3 className="mt-2 text-sm font-medium text-dark-text-primary">No template selected</h3>
              <p className="mt-1 text-sm text-dark-text-secondary">
                Select a template from the list or create a new one
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreateNew}
                  className="btn-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create Template
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
