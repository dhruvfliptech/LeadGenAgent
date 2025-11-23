// Removed unused imports
import { RuleCondition as RuleConditionType } from '../services/phase3Api'
import { TrashIcon, PlusIcon } from '@heroicons/react/24/outline'

interface RuleConditionProps {
  condition: RuleConditionType
  onChange: (condition: RuleConditionType) => void
  onDelete: () => void
  isFirst?: boolean
  showLogicOperator?: boolean
}

const FIELD_OPTIONS = [
  { value: 'lead.title', label: 'Lead Title', type: 'string' },
  { value: 'lead.description', label: 'Lead Description', type: 'string' },
  { value: 'lead.price', label: 'Price', type: 'number' },
  { value: 'lead.location', label: 'Location', type: 'string' },
  { value: 'lead.contact_name', label: 'Contact Name', type: 'string' },
  { value: 'lead.email', label: 'Email', type: 'string' },
  { value: 'lead.phone', label: 'Phone', type: 'string' },
  { value: 'lead.category', label: 'Category', type: 'string' },
  { value: 'lead.subcategory', label: 'Subcategory', type: 'string' },
  { value: 'lead.posted_at', label: 'Posted Date', type: 'date' },
  { value: 'lead.scraped_at', label: 'Scraped Date', type: 'date' },
]

const OPERATOR_OPTIONS: Record<string, { value: string; label: string; supportedTypes: string[] }[]> = {
  string: [
    { value: 'equals', label: 'Equals', supportedTypes: ['string', 'number'] },
    { value: 'contains', label: 'Contains', supportedTypes: ['string'] },
    { value: 'starts_with', label: 'Starts with', supportedTypes: ['string'] },
    { value: 'ends_with', label: 'Ends with', supportedTypes: ['string'] },
    { value: 'in', label: 'In list', supportedTypes: ['string'] },
    { value: 'not_in', label: 'Not in list', supportedTypes: ['string'] },
  ],
  number: [
    { value: 'equals', label: 'Equals', supportedTypes: ['string', 'number'] },
    { value: 'greater_than', label: 'Greater than', supportedTypes: ['number'] },
    { value: 'less_than', label: 'Less than', supportedTypes: ['number'] },
    { value: 'in', label: 'In range', supportedTypes: ['number'] },
  ],
  date: [
    { value: 'equals', label: 'On date', supportedTypes: ['date'] },
    { value: 'greater_than', label: 'After date', supportedTypes: ['date'] },
    { value: 'less_than', label: 'Before date', supportedTypes: ['date'] },
  ],
}

export default function RuleCondition({ 
  condition, 
  onChange, 
  onDelete, 
  isFirst = false,
  showLogicOperator = true 
}: RuleConditionProps) {
  const selectedField = FIELD_OPTIONS.find(f => f.value === condition.field)
  const fieldType = selectedField?.type || 'string'
  const availableOperators = OPERATOR_OPTIONS[fieldType] || OPERATOR_OPTIONS.string

  const handleFieldChange = (field: string) => {
    const newFieldType = FIELD_OPTIONS.find(f => f.value === field)?.type || 'string'
    const newAvailableOperators = OPERATOR_OPTIONS[newFieldType] || OPERATOR_OPTIONS.string
    
    // Reset operator if current one is not supported by new field type
    const newOperator = newAvailableOperators.find(op => op.value === condition.operator)?.value || 
                       newAvailableOperators[0]?.value || 'equals'

    onChange({
      ...condition,
      field,
      operator: newOperator as any,
      value: fieldType === 'number' ? 0 : '',
    })
  }

  const handleOperatorChange = (operator: string) => {
    let newValue = condition.value
    
    // Reset value when switching to/from list operators
    if ((operator === 'in' || operator === 'not_in') && !Array.isArray(condition.value)) {
      newValue = []
    } else if ((operator !== 'in' && operator !== 'not_in') && Array.isArray(condition.value)) {
      newValue = fieldType === 'number' ? 0 : ''
    }

    onChange({
      ...condition,
      operator: operator as any,
      value: newValue,
    })
  }

  const handleValueChange = (value: any) => {
    onChange({
      ...condition,
      value,
    })
  }

  const handleListValueChange = (index: number, value: string) => {
    if (!Array.isArray(condition.value)) return
    
    const newList = [...condition.value]
    newList[index] = value
    handleValueChange(newList)
  }

  const addListItem = () => {
    if (!Array.isArray(condition.value)) return
    handleValueChange([...condition.value, ''])
  }

  const removeListItem = (index: number) => {
    if (!Array.isArray(condition.value)) return
    const newList = condition.value.filter((_, i) => i !== index)
    handleValueChange(newList)
  }

  const renderValueInput = () => {
    const isListOperator = condition.operator === 'in' || condition.operator === 'not_in'
    
    if (isListOperator) {
      const values = Array.isArray(condition.value) ? condition.value : []
      
      return (
        <div className="space-y-2">
          {values.map((value, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type={fieldType === 'number' ? 'number' : fieldType === 'date' ? 'datetime-local' : 'text'}
                className="form-input-terminal flex-1"
                value={value}
                onChange={(e) => handleListValueChange(index, e.target.value)}
                placeholder={`Value ${index + 1}`}
              />
              <button
                type="button"
                onClick={() => removeListItem(index)}
                className="btn-danger p-2"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addListItem}
            className="btn-terminal text-sm"
          >
            <PlusIcon className="w-4 h-4 mr-1" />
            Add Value
          </button>
        </div>
      )
    }

    return (
      <input
        type={fieldType === 'number' ? 'number' : fieldType === 'date' ? 'datetime-local' : 'text'}
        className="form-input-terminal"
        value={condition.value as string | number}
        onChange={(e) => handleValueChange(
          fieldType === 'number' ? parseFloat(e.target.value) || 0 : e.target.value
        )}
        placeholder="Enter value..."
      />
    )
  }

  return (
    <div className="card-terminal p-4">
      <div className="space-y-4">
        {/* Logic Operator (for non-first conditions) */}
        {!isFirst && showLogicOperator && (
          <div className="flex items-center space-x-2">
            <span className="text-terminal-400 font-mono text-sm">Logic:</span>
            <select
              className="form-input-terminal w-auto"
              value={condition.logic_operator || 'AND'}
              onChange={(e) => onChange({
                ...condition,
                logic_operator: e.target.value as 'AND' | 'OR' | 'NOT'
              })}
            >
              <option value="AND">AND</option>
              <option value="OR">OR</option>
              <option value="NOT">NOT</option>
            </select>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Field Selection */}
          <div>
            <label className="form-label-terminal">Field</label>
            <select
              className="form-input-terminal"
              value={condition.field}
              onChange={(e) => handleFieldChange(e.target.value)}
            >
              <option value="">Select field...</option>
              {FIELD_OPTIONS.map(field => (
                <option key={field.value} value={field.value}>
                  {field.label}
                </option>
              ))}
            </select>
          </div>

          {/* Operator Selection */}
          <div>
            <label className="form-label-terminal">Operator</label>
            <select
              className="form-input-terminal"
              value={condition.operator}
              onChange={(e) => handleOperatorChange(e.target.value)}
            >
              {availableOperators.map(operator => (
                <option key={operator.value} value={operator.value}>
                  {operator.label}
                </option>
              ))}
            </select>
          </div>

          {/* Value Input */}
          <div>
            <label className="form-label-terminal">Value</label>
            {renderValueInput()}
          </div>
        </div>

        {/* Delete Button */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onDelete}
            className="btn-danger"
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Remove Condition
          </button>
        </div>
      </div>

      {/* Preview */}
      <div className="mt-4 p-3 bg-dark-bg border border-dark-border rounded">
        <div className="text-xs text-dark-text-secondary mb-1">Preview:</div>
        <div className="font-mono text-sm text-terminal-400">
          {!isFirst && condition.logic_operator && (
            <span className="text-yellow-400">{condition.logic_operator} </span>
          )}
          <span className="text-blue-400">{selectedField?.label || 'Field'}</span>
          <span className="text-white"> {availableOperators.find(op => op.value === condition.operator)?.label || 'operator'} </span>
          <span className="text-green-400">
            {Array.isArray(condition.value) ? 
              `[${condition.value.join(', ')}]` : 
              condition.value?.toString() || 'value'
            }
          </span>
        </div>
      </div>
    </div>
  )
}