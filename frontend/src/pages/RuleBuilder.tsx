import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Rule, RuleCondition as RuleConditionType, RuleAction, ruleEngineApi } from '../services/phase3Api'
import RuleCondition from '../components/RuleCondition'
import { 
  PlusIcon, 
  PlayIcon,
  CheckIcon,
  
  TrashIcon,
  PencilIcon,
  BeakerIcon,
  
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ViewMode = 'list' | 'create' | 'edit' | 'test'

interface TestResult {
  passed: boolean
  matchedConditions: string[]
  executedActions: string[]
  error?: string
}

export default function RuleBuilder() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null)
  const [testData, setTestData] = useState('')
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    conditions: [] as RuleConditionType[],
    actions: [] as RuleAction[],
    logic_operator: 'AND' as 'AND' | 'OR',
    is_active: true,
    priority: 1,
    exclude_lists: [] as string[],
  })

  const queryClient = useQueryClient()

  // Fetch rules
  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: () => ruleEngineApi.getRules().then(res => res.data),
  })

  // Fetch exclude lists
  const { data: excludeLists = [] } = useQuery({
    queryKey: ['exclude-lists'],
    queryFn: () => ruleEngineApi.getExcludeLists().then(res => res.data),
  })

  // Create rule mutation
  const createMutation = useMutation({
    mutationFn: ruleEngineApi.createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      setViewMode('list')
      resetForm()
      toast.success('Rule created successfully')
    },
    onError: () => {
      toast.error('Failed to create rule')
    },
  })

  // Update rule mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<Rule>) =>
      ruleEngineApi.updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      setViewMode('list')
      resetForm()
      toast.success('Rule updated successfully')
    },
    onError: () => {
      toast.error('Failed to update rule')
    },
  })

  // Delete rule mutation
  const deleteMutation = useMutation({
    mutationFn: ruleEngineApi.deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] })
      toast.success('Rule deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete rule')
    },
  })

  // Test rule mutation
  const testMutation = useMutation({
    mutationFn: ({ rule, testData }: { rule: any; testData: any }) =>
      ruleEngineApi.testRule(rule, testData),
    onSuccess: (data) => {
      setTestResult(data.data)
    },
    onError: () => {
      toast.error('Failed to test rule')
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      conditions: [],
      actions: [],
      logic_operator: 'AND',
      is_active: true,
      priority: 1,
      exclude_lists: [],
    })
    setSelectedRule(null)
  }

  useEffect(() => {
    if (selectedRule) {
      setFormData({
        name: selectedRule.name,
        description: selectedRule.description || '',
        conditions: selectedRule.conditions,
        actions: selectedRule.actions,
        logic_operator: selectedRule.logic_operator,
        is_active: selectedRule.is_active,
        priority: selectedRule.priority,
        exclude_lists: selectedRule.exclude_lists,
      })
    }
  }, [selectedRule])

  const generateConditionId = () => Math.random().toString(36).substr(2, 9)
  const generateActionId = () => Math.random().toString(36).substr(2, 9)

  const addCondition = () => {
    const newCondition: RuleConditionType = {
      id: generateConditionId(),
      field: '',
      operator: 'equals',
      value: '',
      logic_operator: formData.conditions.length > 0 ? 'AND' : undefined,
    }
    setFormData(prev => ({
      ...prev,
      conditions: [...prev.conditions, newCondition]
    }))
  }

  const updateCondition = (index: number, condition: RuleConditionType) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.map((c, i) => i === index ? condition : c)
    }))
  }

  const removeCondition = (index: number) => {
    setFormData(prev => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index)
    }))
  }

  const addAction = () => {
    const newAction: RuleAction = {
      id: generateActionId(),
      type: 'send_template',
      parameters: {},
    }
    setFormData(prev => ({
      ...prev,
      actions: [...prev.actions, newAction]
    }))
  }

  const updateAction = (index: number, action: RuleAction) => {
    setFormData(prev => ({
      ...prev,
      actions: prev.actions.map((a, i) => i === index ? action : a)
    }))
  }

  const removeAction = (index: number) => {
    setFormData(prev => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== index)
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (formData.conditions.length === 0) {
      toast.error('At least one condition is required')
      return
    }
    
    if (formData.actions.length === 0) {
      toast.error('At least one action is required')
      return
    }

    if (selectedRule) {
      updateMutation.mutate({ id: selectedRule.id, ...formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleTestRule = () => {
    if (!testData) {
      toast.error('Please provide test data')
      return
    }

    try {
      const parsedTestData = JSON.parse(testData)
      testMutation.mutate({ rule: formData, testData: parsedTestData })
    } catch (error) {
      toast.error('Invalid JSON test data')
    }
  }

  const renderActionEditor = (action: RuleAction, index: number) => (
    <div key={action.id} className="card-terminal p-4">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-terminal-400 font-mono">Action {index + 1}</h4>
          <button
            type="button"
            onClick={() => removeAction(index)}
            className="btn-danger p-2"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="form-label-terminal">Action Type</label>
            <select
              className="form-input-terminal"
              value={action.type}
              onChange={(e) => updateAction(index, {
                ...action,
                type: e.target.value as any,
                parameters: {}
              })}
            >
              <option value="send_template">Send Template</option>
              <option value="add_tag">Add Tag</option>
              <option value="set_status">Set Status</option>
              <option value="create_task">Create Task</option>
              <option value="webhook">Webhook</option>
            </select>
          </div>

          <div>
            <label className="form-label-terminal">Parameters</label>
            <textarea
              className="form-input-terminal h-20"
              value={JSON.stringify(action.parameters, null, 2)}
              onChange={(e) => {
                try {
                  const parameters = JSON.parse(e.target.value)
                  updateAction(index, { ...action, parameters })
                } catch {
                  // Invalid JSON, don't update
                }
              }}
              placeholder='{"template_id": 1, "delay_minutes": 5}'
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderRuleForm = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          {selectedRule ? 'Edit Rule' : 'Create Rule'}
        </h1>
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={() => setViewMode('test')}
            className="btn-terminal"
          >
            <BeakerIcon className="w-4 h-4 mr-2" />
            Test Rule
          </button>
          <button
            onClick={() => {
              setViewMode('list')
              resetForm()
            }}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Basic Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label-terminal">Rule Name</label>
              <input
                type="text"
                className="form-input-terminal"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="High-value leads auto-response"
                required
              />
            </div>
            
            <div>
              <label className="form-label-terminal">Priority</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) || 1 }))}
                min="1"
                max="100"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="form-label-terminal">Description</label>
            <textarea
              className="form-input-terminal h-20"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Automatically respond to leads with prices above $50,000"
            />
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="form-label-terminal">Logic Operator</label>
              <select
                className="form-input-terminal"
                value={formData.logic_operator}
                onChange={(e) => setFormData(prev => ({ ...prev, logic_operator: e.target.value as 'AND' | 'OR' }))}
              >
                <option value="AND">AND (all conditions must match)</option>
                <option value="OR">OR (any condition can match)</option>
              </select>
            </div>

            <div className="flex items-center mt-6">
              <input
                type="checkbox"
                id="is_active"
                className="mr-2 text-terminal-500 focus:ring-terminal-500"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <label htmlFor="is_active" className="form-label-terminal">
                Rule is active
              </label>
            </div>
          </div>
        </div>

        {/* Conditions */}
        <div className="card-terminal p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-terminal-400 font-mono">
              Conditions ({formData.logic_operator})
            </h2>
            <button
              type="button"
              onClick={addCondition}
              className="btn-terminal"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Condition
            </button>
          </div>

          {formData.conditions.length === 0 ? (
            <div className="text-center py-8 text-dark-text-muted">
              No conditions added. Click "Add Condition" to start building your rule.
            </div>
          ) : (
            <div className="space-y-4">
              {formData.conditions.map((condition, index) => (
                <RuleCondition
                  key={condition.id}
                  condition={condition}
                  onChange={(newCondition) => updateCondition(index, newCondition)}
                  onDelete={() => removeCondition(index)}
                  isFirst={index === 0}
                  showLogicOperator={formData.logic_operator === 'AND'}
                />
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="card-terminal p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-terminal-400 font-mono">
              Actions
            </h2>
            <button
              type="button"
              onClick={addAction}
              className="btn-terminal"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Action
            </button>
          </div>

          {formData.actions.length === 0 ? (
            <div className="text-center py-8 text-dark-text-muted">
              No actions added. Click "Add Action" to define what happens when the rule matches.
            </div>
          ) : (
            <div className="space-y-4">
              {formData.actions.map((action, index) => renderActionEditor(action, index))}
            </div>
          )}
        </div>

        {/* Exclude Lists */}
        {excludeLists.length > 0 && (
          <div className="card-terminal p-6">
            <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
              Exclude Lists
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {excludeLists.map(list => (
                <label key={list} className="flex items-center">
                  <input
                    type="checkbox"
                    className="mr-2 text-terminal-500 focus:ring-terminal-500"
                    checked={formData.exclude_lists.includes(list)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData(prev => ({ ...prev, exclude_lists: [...prev.exclude_lists, list] }))
                      } else {
                        setFormData(prev => ({ ...prev, exclude_lists: prev.exclude_lists.filter(l => l !== list) }))
                      }
                    }}
                  />
                  <span className="text-dark-text-secondary text-sm">{list}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => {
              setViewMode('list')
              resetForm()
            }}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-terminal-solid"
            disabled={createMutation.isPending || updateMutation.isPending}
          >
            {createMutation.isPending || updateMutation.isPending ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                Saving...
              </div>
            ) : (
              <div className="flex items-center">
                <CheckIcon className="w-4 h-4 mr-2" />
                {selectedRule ? 'Update Rule' : 'Create Rule'}
              </div>
            )}
          </button>
        </div>
      </form>
    </div>
  )

  const renderTestInterface = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Test Rule
        </h1>
        <button
          onClick={() => setViewMode(selectedRule ? 'edit' : 'create')}
          className="btn-secondary"
        >
          Back to Editor
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Data Input */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Test Data
          </h2>
          <textarea
            className="code-block w-full h-64"
            value={testData}
            onChange={(e) => setTestData(e.target.value)}
            placeholder={JSON.stringify({
              lead: {
                title: "2020 Tesla Model 3",
                price: 35000,
                location: "San Francisco, CA",
                contact_name: "John Smith",
                email: "john@example.com",
                category: "automotive",
                posted_at: new Date().toISOString()
              }
            }, null, 2)}
          />
          <button
            onClick={handleTestRule}
            className="btn-terminal-solid mt-4"
            disabled={testMutation.isPending}
          >
            {testMutation.isPending ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                Testing...
              </div>
            ) : (
              <div className="flex items-center">
                <PlayIcon className="w-4 h-4 mr-2" />
                Test Rule
              </div>
            )}
          </button>
        </div>

        {/* Test Results */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Test Results
          </h2>
          
          {testResult ? (
            <div className="space-y-4">
              <div className={`p-4 rounded border ${
                testResult.passed 
                  ? 'bg-terminal-900/20 border-terminal-500/30 text-terminal-400'
                  : 'bg-red-900/20 border-red-500/30 text-red-400'
              }`}>
                <div className="font-mono font-bold">
                  {testResult.passed ? '✓ Rule Passed' : '✗ Rule Failed'}
                </div>
                {testResult.error && (
                  <div className="text-sm mt-2">Error: {testResult.error}</div>
                )}
              </div>

              {testResult.matchedConditions.length > 0 && (
                <div>
                  <h3 className="text-terminal-400 font-mono font-semibold mb-2">
                    Matched Conditions:
                  </h3>
                  <ul className="space-y-1">
                    {testResult.matchedConditions.map((condition, index) => (
                      <li key={index} className="text-sm text-green-400 font-mono">
                        ✓ {condition}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {testResult.executedActions.length > 0 && (
                <div>
                  <h3 className="text-terminal-400 font-mono font-semibold mb-2">
                    Executed Actions:
                  </h3>
                  <ul className="space-y-1">
                    {testResult.executedActions.map((action, index) => (
                      <li key={index} className="text-sm text-blue-400 font-mono">
                        → {action}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-dark-text-muted">
              Enter test data and click "Test Rule" to see results
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderRulesList = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Rule Builder
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Create and manage automated rules for lead processing
          </p>
        </div>
        
        <button
          onClick={() => setViewMode('create')}
          className="btn-terminal-solid"
        >
          <PlusIcon className="w-4 h-4 mr-2" />
          Create Rule
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-text-secondary mt-2">Loading rules...</div>
        </div>
      ) : rules.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-dark-text-muted mb-4">No rules found</div>
          <button
            onClick={() => setViewMode('create')}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Your First Rule
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {rules.map(rule => (
            <div key={rule.id} className="card-terminal p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-terminal-400 font-mono">
                      {rule.name}
                    </h3>
                    <span className={`status-${rule.is_active ? 'online' : 'offline'}`}>
                      {rule.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span className="text-xs bg-dark-border text-dark-text-secondary px-2 py-1 rounded">
                      Priority: {rule.priority}
                    </span>
                  </div>
                  
                  {rule.description && (
                    <p className="text-dark-text-secondary text-sm mb-3">
                      {rule.description}
                    </p>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-dark-text-secondary">Conditions:</span>
                      <span className="ml-2 text-terminal-400 font-mono">
                        {rule.conditions.length} ({rule.logic_operator})
                      </span>
                    </div>
                    <div>
                      <span className="text-dark-text-secondary">Actions:</span>
                      <span className="ml-2 text-terminal-400 font-mono">
                        {rule.actions.length}
                      </span>
                    </div>
                    <div>
                      <span className="text-dark-text-secondary">Exclude Lists:</span>
                      <span className="ml-2 text-terminal-400 font-mono">
                        {rule.exclude_lists.length}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      setSelectedRule(rule)
                      setViewMode('edit')
                    }}
                    className="btn-secondary"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this rule?')) {
                        deleteMutation.mutate(rule.id)
                      }
                    }}
                    className="btn-danger"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // Render based on view mode
  if (viewMode === 'create' || viewMode === 'edit') {
    return renderRuleForm()
  }

  if (viewMode === 'test') {
    return renderTestInterface()
  }

  return renderRulesList()
}