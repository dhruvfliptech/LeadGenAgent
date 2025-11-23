import { useState, useEffect } from 'react'
import { Template } from '../services/phase3Api'
import { EyeIcon, CodeBracketIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface TemplateEditorProps {
  template?: Template
  onSave: (template: Omit<Template, 'id' | 'created_at' | 'updated_at'>) => void
  onCancel: () => void
  isLoading?: boolean
}

interface TemplateVariable {
  name: string
  description: string
  example: string
}

const AVAILABLE_VARIABLES: TemplateVariable[] = [
  { name: 'lead.title', description: 'Lead post title', example: '2015 Honda Civic for Sale' },
  { name: 'lead.price', description: 'Listed price', example: '$12,000' },
  { name: 'lead.location', description: 'Location name', example: 'San Francisco, CA' },
  { name: 'lead.contact_name', description: 'Contact person name', example: 'John Smith' },
  { name: 'lead.description', description: 'Post description', example: 'Well maintained vehicle...' },
  { name: 'user.name', description: 'Your name', example: 'Mike Johnson' },
  { name: 'user.company', description: 'Your company', example: 'ABC Motors' },
  { name: 'user.phone', description: 'Your phone number', example: '(555) 123-4567' },
  { name: 'user.email', description: 'Your email', example: 'mike@abcmotors.com' },
]

export default function TemplateEditor({ template, onSave, onCancel, isLoading }: TemplateEditorProps) {
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    content: '',
    category: 'initial_contact',
    is_active: true,
    variables: [] as string[],
  })
  
  const [viewMode, setViewMode] = useState<'edit' | 'preview'>('edit')
  // Removed unused temp state

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name,
        subject: template.subject,
        content: template.content,
        category: template.category,
        is_active: template.is_active,
        variables: template.variables,
      })
    }
  }, [template])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
  }

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const insertVariable = (variable: string) => {
    const textarea = document.getElementById('content-textarea') as HTMLTextAreaElement
    if (!textarea) return

    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const currentContent = formData.content
    
    const newContent = currentContent.substring(0, start) + 
                      `{{${variable}}}` + 
                      currentContent.substring(end)
    
    handleInputChange('content', newContent)
    
    // Update variables list if not already included
    if (!formData.variables.includes(variable)) {
      handleInputChange('variables', [...formData.variables, variable])
    }

    // Reset selection and focus
    setTimeout(() => {
      const newPosition = start + variable.length + 4 // {{}}
      textarea.setSelectionRange(newPosition, newPosition)
      textarea.focus()
    }, 0)
  }

  const renderPreview = () => {
    let previewContent = formData.content
    
    // Replace variables with example values
    AVAILABLE_VARIABLES.forEach(variable => {
      const regex = new RegExp(`{{${variable.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}}}`, 'g')
      previewContent = previewContent.replace(regex, 
        `<span class="bg-terminal-500/20 text-terminal-400 px-1 rounded">${variable.example}</span>`)
    })

    return (
      <div className="space-y-4">
        <div>
          <label className="form-label-terminal">Subject Preview</label>
          <div className="p-3 bg-dark-bg border border-dark-border rounded-md">
            <div 
              className="text-dark-text-primary"
              dangerouslySetInnerHTML={{ 
                __html: formData.subject.replace(/{{(.*?)}}/g, 
                  (match, variable) => {
                    const varInfo = AVAILABLE_VARIABLES.find(v => v.name === variable)
                    return varInfo ? 
                      `<span class="bg-terminal-500/20 text-terminal-400 px-1 rounded">${varInfo.example}</span>` : 
                      match
                  })
              }}
            />
          </div>
        </div>
        
        <div>
          <label className="form-label-terminal">Content Preview</label>
          <div className="p-4 bg-dark-bg border border-dark-border rounded-md min-h-[200px]">
            <div 
              className="text-dark-text-primary whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ __html: previewContent }}
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card-terminal p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-terminal-400 font-mono">
          {template ? 'Edit Template' : 'Create Template'}
        </h2>
        
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setViewMode('edit')}
            className={`btn ${viewMode === 'edit' ? 'btn-terminal-solid' : 'btn-secondary'}`}
          >
            <CodeBracketIcon className="w-4 h-4 mr-2" />
            Edit
          </button>
          <button
            type="button"
            onClick={() => setViewMode('preview')}
            className={`btn ${viewMode === 'preview' ? 'btn-terminal-solid' : 'btn-secondary'}`}
          >
            <EyeIcon className="w-4 h-4 mr-2" />
            Preview
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="form-label-terminal">Template Name</label>
            <input
              type="text"
              className="form-input-terminal"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Initial Contact Template"
              required
            />
          </div>
          
          <div>
            <label className="form-label-terminal">Category</label>
            <select
              className="form-input-terminal"
              value={formData.category}
              onChange={(e) => handleInputChange('category', e.target.value)}
            >
              <option value="initial_contact">Initial Contact</option>
              <option value="follow_up">Follow Up</option>
              <option value="appointment">Appointment</option>
              <option value="closing">Closing</option>
              <option value="thank_you">Thank You</option>
            </select>
          </div>
        </div>

        {/* Subject Line */}
        <div>
          <label className="form-label-terminal">Subject Line</label>
          <input
            type="text"
            className="form-input-terminal"
            value={formData.subject}
            onChange={(e) => handleInputChange('subject', e.target.value)}
            placeholder="Interested in your {{lead.title}}"
            required
          />
        </div>

        {viewMode === 'edit' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Content Editor */}
            <div className="lg:col-span-2">
              <label className="form-label-terminal">Template Content</label>
              <textarea
                id="content-textarea"
                className="form-input-terminal h-64 resize-none"
                value={formData.content}
                onChange={(e) => handleInputChange('content', e.target.value)}
                placeholder="Hi {{lead.contact_name}},&#10;&#10;I'm interested in your {{lead.title}} listed for {{lead.price}}...&#10;&#10;Best regards,&#10;{{user.name}}"
                required
              />
            </div>

            {/* Variables Panel */}
            <div>
              <label className="form-label-terminal">Available Variables</label>
              <div className="bg-dark-bg border border-dark-border rounded-md p-3 h-64 overflow-y-auto">
                {AVAILABLE_VARIABLES.map((variable) => (
                  <div
                    key={variable.name}
                    className="mb-3 p-2 border border-dark-border rounded hover:border-terminal-500/50 cursor-pointer transition-colors"
                    onClick={() => insertVariable(variable.name)}
                  >
                    <div className="text-terminal-400 font-mono text-sm">
                      {`{{${variable.name}}}`}
                    </div>
                    <div className="text-dark-text-secondary text-xs mt-1">
                      {variable.description}
                    </div>
                    <div className="text-dark-text-muted text-xs">
                      Ex: {variable.example}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          renderPreview()
        )}

        {/* Active Status */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="is_active"
            className="mr-2 text-terminal-500 focus:ring-terminal-500"
            checked={formData.is_active}
            onChange={(e) => handleInputChange('is_active', e.target.checked)}
          />
          <label htmlFor="is_active" className="form-label-terminal">
            Template is active
          </label>
        </div>

        {/* Used Variables Display */}
        {formData.variables.length > 0 && (
          <div>
            <label className="form-label-terminal">Variables Used</label>
            <div className="flex flex-wrap gap-2">
              {formData.variables.map((variable) => (
                <span
                  key={variable}
                  className="inline-flex items-center px-2 py-1 bg-terminal-500/20 text-terminal-400 text-xs font-mono rounded border border-terminal-500/30"
                >
                  {`{{${variable}}}`}
                  <button
                    type="button"
                    onClick={() => {
                      const newVariables = formData.variables.filter(v => v !== variable)
                      handleInputChange('variables', newVariables)
                      // Remove from content as well
                      const newContent = formData.content.replace(new RegExp(`{{${variable}}}`, 'g'), '')
                      handleInputChange('content', newContent)
                    }}
                    className="ml-1 text-red-400 hover:text-red-300"
                  >
                    <XMarkIcon className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-dark-border">
          <button
            type="button"
            onClick={onCancel}
            className="btn-secondary"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-terminal-solid"
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                Saving...
              </div>
            ) : (
              <div className="flex items-center">
                <CheckIcon className="w-4 h-4 mr-2" />
                {template ? 'Update Template' : 'Create Template'}
              </div>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}