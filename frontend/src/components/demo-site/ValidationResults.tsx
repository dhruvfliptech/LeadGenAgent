import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { ValidationResult } from '@/types/demoSite'

interface ValidationResultsProps {
  validation: ValidationResult
}

export default function ValidationResults({ validation }: ValidationResultsProps) {
  const hasErrors = validation.errors.length > 0
  const hasWarnings = validation.warnings.length > 0

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-dark-text-primary mb-4 flex items-center gap-2">
        <DocumentTextIcon className="w-5 h-5" />
        Validation Results
      </h3>

      {/* Overall Status */}
      {validation.is_valid ? (
        <div className="flex items-start gap-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg mb-4">
          <CheckCircleIcon className="w-6 h-6 text-green-500 flex-shrink-0" />
          <div>
            <div className="font-medium text-dark-text-primary mb-1">
              Validation Passed
            </div>
            <p className="text-sm text-dark-text-secondary">
              All required files are present and code structure is valid
            </p>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg mb-4">
          <ExclamationCircleIcon className="w-6 h-6 text-red-500 flex-shrink-0" />
          <div>
            <div className="font-medium text-dark-text-primary mb-1">
              Validation Failed
            </div>
            <p className="text-sm text-dark-text-secondary">
              Found {validation.errors.length} error{validation.errors.length !== 1 ? 's' : ''} that need to be fixed
            </p>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-4 bg-dark-border/30 rounded-lg">
          <div className="text-2xl font-bold text-dark-text-primary mb-1">
            {validation.file_count}
          </div>
          <div className="text-sm text-dark-text-secondary">Files</div>
        </div>

        <div className="text-center p-4 bg-dark-border/30 rounded-lg">
          <div className="text-2xl font-bold text-dark-text-primary mb-1">
            {(validation.total_size_bytes / 1024).toFixed(1)}KB
          </div>
          <div className="text-sm text-dark-text-secondary">Total Size</div>
        </div>

        <div className="text-center p-4 bg-dark-border/30 rounded-lg">
          <div className="text-2xl font-bold text-red-500 mb-1">
            {validation.errors.length}
          </div>
          <div className="text-sm text-dark-text-secondary">Errors</div>
        </div>

        <div className="text-center p-4 bg-dark-border/30 rounded-lg">
          <div className="text-2xl font-bold text-yellow-500 mb-1">
            {validation.warnings.length}
          </div>
          <div className="text-sm text-dark-text-secondary">Warnings</div>
        </div>
      </div>

      {/* Errors */}
      {hasErrors && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
            <h4 className="font-medium text-dark-text-primary">
              Errors ({validation.errors.length})
            </h4>
          </div>
          <div className="space-y-2">
            {validation.errors.map((error, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
              >
                <span className="text-red-500 mt-0.5">✗</span>
                <span className="text-sm text-dark-text-secondary flex-1">{error}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {hasWarnings && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />
            <h4 className="font-medium text-dark-text-primary">
              Warnings ({validation.warnings.length})
            </h4>
          </div>
          <div className="space-y-2">
            {validation.warnings.map((warning, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
              >
                <span className="text-yellow-500 mt-0.5">⚠</span>
                <span className="text-sm text-dark-text-secondary flex-1">{warning}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Placeholders Found */}
      {validation.placeholders_found && validation.placeholders_found.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-orange-500" />
            <h4 className="font-medium text-dark-text-primary">
              Placeholders Found ({validation.placeholders_found.length})
            </h4>
          </div>
          <div className="space-y-2">
            {validation.placeholders_found.map((placeholder, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg"
              >
                <span className="text-orange-500 mt-0.5">◉</span>
                <code className="text-sm text-dark-text-secondary font-mono flex-1">
                  {placeholder}
                </code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Clear */}
      {!hasErrors && !hasWarnings && validation.placeholders_found.length === 0 && validation.is_valid && (
        <div className="text-center py-8">
          <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <p className="text-dark-text-secondary">
            No issues found. Your demo site is ready to deploy!
          </p>
        </div>
      )}
    </div>
  )
}
