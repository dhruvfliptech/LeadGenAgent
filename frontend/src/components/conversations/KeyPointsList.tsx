import { CheckCircleIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'

interface KeyPointsListProps {
  keyPoints: string[]
  questions?: string[]
  className?: string
}

export default function KeyPointsList({ keyPoints, questions, className = '' }: KeyPointsListProps) {
  const hasContent = keyPoints.length > 0 || (questions && questions.length > 0)

  if (!hasContent) {
    return null
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Key Points */}
      {keyPoints.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dark-text-muted uppercase tracking-wide mb-2">
            Key Points
          </h4>
          <ul className="space-y-1.5">
            {keyPoints.map((point, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-dark-text-primary">
                <CheckCircleIcon className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Questions Asked */}
      {questions && questions.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-dark-text-muted uppercase tracking-wide mb-2">
            Questions Asked
          </h4>
          <ul className="space-y-1.5">
            {questions.map((question, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-dark-text-primary">
                <QuestionMarkCircleIcon className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                <span className="italic">{question}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
