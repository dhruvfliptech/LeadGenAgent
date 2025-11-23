import { TaskType } from '@/mocks/models.mock'
import { CheckIcon } from '@heroicons/react/24/solid'

interface TaskTypeSelectorProps {
  selected: TaskType | 'all'
  onChange: (taskType: TaskType | 'all') => void
}

const taskTypes: { value: TaskType | 'all'; label: string; description: string }[] = [
  { value: 'all', label: 'All Tasks', description: 'Show all task types' },
  { value: 'email_generation', label: 'Email Generation', description: 'Personalized email responses' },
  { value: 'lead_scoring', label: 'Lead Scoring', description: 'Lead qualification & scoring' },
  { value: 'sentiment_analysis', label: 'Sentiment Analysis', description: 'Message sentiment detection' },
  { value: 'content_generation', label: 'Content Generation', description: 'Marketing content creation' },
  { value: 'script_writing', label: 'Script Writing', description: 'Sales scripts & templates' },
  { value: 'analysis', label: 'Analysis', description: 'Data analysis & insights' },
]

/**
 * TaskTypeSelector component for filtering AI models by task type
 * Usage:
 * <TaskTypeSelector
 *   selected={selectedTaskType}
 *   onChange={(taskType) => setSelectedTaskType(taskType)}
 * />
 */
export default function TaskTypeSelector({ selected, onChange }: TaskTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {taskTypes.map((taskType) => {
        const isSelected = selected === taskType.value
        return (
          <button
            key={taskType.value}
            onClick={() => onChange(taskType.value)}
            className={`relative p-4 text-left rounded-lg border-2 transition-all ${
              isSelected
                ? 'border-terminal-500 bg-terminal-500/10 ring-2 ring-terminal-500/20'
                : 'border-dark-border bg-dark-surface hover:border-terminal-500/50'
            }`}
          >
            {isSelected && (
              <CheckIcon className="absolute top-3 right-3 w-5 h-5 text-terminal-400" />
            )}
            <div className="pr-6">
              <div className={`font-semibold mb-1 ${isSelected ? 'text-terminal-400' : 'text-dark-text-primary'}`}>
                {taskType.label}
              </div>
              <div className="text-xs text-dark-text-muted">
                {taskType.description}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
