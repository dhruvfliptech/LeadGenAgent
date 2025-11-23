import { useState, useEffect } from 'react'
import { scheduleApi } from '../services/phase3Api'
import { ClockIcon, CheckIcon } from '@heroicons/react/24/outline'

interface CronBuilderProps {
  value: string
  onChange: (expression: string) => void
  onValidation?: (isValid: boolean, nextRuns?: string[], error?: string) => void
}

interface CronValues {
  minute: string
  hour: string
  day: string
  month: string
  weekday: string
}

const MINUTE_OPTIONS = [
  { value: '*', label: 'Every minute' },
  { value: '0', label: 'Top of hour' },
  { value: '15', label: 'Quarter past' },
  { value: '30', label: 'Half past' },
  { value: '45', label: 'Quarter to' },
  { value: '*/5', label: 'Every 5 minutes' },
  { value: '*/10', label: 'Every 10 minutes' },
  { value: '*/15', label: 'Every 15 minutes' },
  { value: '*/30', label: 'Every 30 minutes' },
]

const HOUR_OPTIONS = [
  { value: '*', label: 'Every hour' },
  { value: '0', label: '12:00 AM' },
  { value: '6', label: '6:00 AM' },
  { value: '9', label: '9:00 AM' },
  { value: '12', label: '12:00 PM' },
  { value: '15', label: '3:00 PM' },
  { value: '18', label: '6:00 PM' },
  { value: '21', label: '9:00 PM' },
  { value: '*/2', label: 'Every 2 hours' },
  { value: '*/4', label: 'Every 4 hours' },
  { value: '*/6', label: 'Every 6 hours' },
  { value: '*/12', label: 'Every 12 hours' },
]

const DAY_OPTIONS = [
  { value: '*', label: 'Every day' },
  { value: '1', label: '1st' },
  { value: '15', label: '15th' },
  { value: '*/2', label: 'Every 2 days' },
  { value: '*/7', label: 'Every week' },
]

const MONTH_OPTIONS = [
  { value: '*', label: 'Every month' },
  { value: '1', label: 'January' },
  { value: '2', label: 'February' },
  { value: '3', label: 'March' },
  { value: '4', label: 'April' },
  { value: '5', label: 'May' },
  { value: '6', label: 'June' },
  { value: '7', label: 'July' },
  { value: '8', label: 'August' },
  { value: '9', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
  { value: '*/3', label: 'Every 3 months' },
  { value: '*/6', label: 'Every 6 months' },
]

const WEEKDAY_OPTIONS = [
  { value: '*', label: 'Any day' },
  { value: '0', label: 'Sunday' },
  { value: '1', label: 'Monday' },
  { value: '2', label: 'Tuesday' },
  { value: '3', label: 'Wednesday' },
  { value: '4', label: 'Thursday' },
  { value: '5', label: 'Friday' },
  { value: '6', label: 'Saturday' },
  { value: '1-5', label: 'Weekdays' },
  { value: '0,6', label: 'Weekends' },
]

const PRESET_SCHEDULES = [
  { name: 'Every minute', expression: '* * * * *' },
  { name: 'Every 5 minutes', expression: '*/5 * * * *' },
  { name: 'Every hour', expression: '0 * * * *' },
  { name: 'Every day at midnight', expression: '0 0 * * *' },
  { name: 'Every day at 9 AM', expression: '0 9 * * *' },
  { name: 'Every weekday at 9 AM', expression: '0 9 * * 1-5' },
  { name: 'Every Monday at 9 AM', expression: '0 9 * * 1' },
  { name: 'Every month on 1st at midnight', expression: '0 0 1 * *' },
  { name: 'Every Sunday at 6 PM', expression: '0 18 * * 0' },
  { name: 'Twice daily (9 AM & 6 PM)', expression: '0 9,18 * * *' },
]

export default function CronBuilder({ value, onChange, onValidation }: CronBuilderProps) {
  const [mode, setMode] = useState<'simple' | 'advanced'>('simple')
  const [cronValues, setCronValues] = useState<CronValues>({
    minute: '0',
    hour: '9',
    day: '*',
    month: '*',
    weekday: '*',
  })
  const [manualExpression, setManualExpression] = useState(value)
  const [validation, setValidation] = useState<{
    isValid: boolean
    nextRuns?: string[]
    error?: string
  }>({ isValid: true })

  // Parse cron expression into components
  useEffect(() => {
    if (value && value !== manualExpression) {
      setManualExpression(value)
      const parts = value.split(' ')
      if (parts.length === 5) {
        setCronValues({
          minute: parts[0],
          hour: parts[1],
          day: parts[2],
          month: parts[3],
          weekday: parts[4],
        })
      }
    }
  }, [value])

  // Build cron expression from components
  useEffect(() => {
    if (mode === 'simple') {
      const expression = `${cronValues.minute} ${cronValues.hour} ${cronValues.day} ${cronValues.month} ${cronValues.weekday}`
      if (expression !== value) {
        onChange(expression)
      }
    }
  }, [cronValues, mode, onChange, value])

  // Validate cron expression
  useEffect(() => {
    const validateExpression = async () => {
      const expression = mode === 'simple' 
        ? `${cronValues.minute} ${cronValues.hour} ${cronValues.day} ${cronValues.month} ${cronValues.weekday}`
        : manualExpression

      if (!expression.trim()) {
        setValidation({ isValid: false, error: 'Expression is required' })
        onValidation?.(false, [], 'Expression is required')
        return
      }

      try {
        const result = await scheduleApi.validateCron(expression)
        setValidation({
          isValid: result.data.valid,
          nextRuns: result.data.next_runs,
          error: result.data.error,
        })
        onValidation?.(result.data.valid, result.data.next_runs, result.data.error)
      } catch (error) {
        setValidation({ 
          isValid: false, 
          error: 'Failed to validate expression' 
        })
        onValidation?.(false, [], 'Failed to validate expression')
      }
    }

    const timeoutId = setTimeout(validateExpression, 300)
    return () => clearTimeout(timeoutId)
  }, [cronValues, manualExpression, mode, onValidation])

  const handlePresetSelect = (expression: string) => {
    onChange(expression)
    setManualExpression(expression)
    
    const parts = expression.split(' ')
    if (parts.length === 5) {
      setCronValues({
        minute: parts[0],
        hour: parts[1],
        day: parts[2],
        month: parts[3],
        weekday: parts[4],
      })
    }
  }

  const handleManualChange = (expression: string) => {
    setManualExpression(expression)
    onChange(expression)
  }

  const updateCronValue = (field: keyof CronValues, value: string) => {
    setCronValues(prev => ({ ...prev, [field]: value }))
  }

  const getHumanReadable = () => {
    const expression = mode === 'simple' 
      ? `${cronValues.minute} ${cronValues.hour} ${cronValues.day} ${cronValues.month} ${cronValues.weekday}`
      : manualExpression

    // Simple human-readable interpretation
    if (expression === '* * * * *') return 'Every minute'
    if (expression === '0 * * * *') return 'Every hour'
    if (expression === '0 0 * * *') return 'Every day at midnight'
    if (expression === '0 9 * * 1-5') return 'Every weekday at 9:00 AM'
    if (expression === '0 9 * * *') return 'Every day at 9:00 AM'
    
    return 'Custom schedule'
  }

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <div className="flex items-center space-x-4">
        <button
          type="button"
          onClick={() => setMode('simple')}
          className={`btn ${mode === 'simple' ? 'btn-terminal-solid' : 'btn-secondary'}`}
        >
          Simple Builder
        </button>
        <button
          type="button"
          onClick={() => setMode('advanced')}
          className={`btn ${mode === 'advanced' ? 'btn-terminal-solid' : 'btn-secondary'}`}
        >
          Advanced Editor
        </button>
      </div>

      {mode === 'simple' ? (
        <div className="space-y-6">
          {/* Preset Schedules */}
          <div>
            <label className="form-label-terminal">Quick Presets</label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {PRESET_SCHEDULES.map(preset => (
                <button
                  key={preset.expression}
                  type="button"
                  onClick={() => handlePresetSelect(preset.expression)}
                  className="btn-secondary text-xs py-2 text-left"
                  title={preset.expression}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Simple Builder */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="form-label-terminal">Minute</label>
              <select
                className="form-input-terminal"
                value={cronValues.minute}
                onChange={(e) => updateCronValue('minute', e.target.value)}
              >
                {MINUTE_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="text-xs text-dark-text-muted mt-1">0-59</div>
            </div>

            <div>
              <label className="form-label-terminal">Hour</label>
              <select
                className="form-input-terminal"
                value={cronValues.hour}
                onChange={(e) => updateCronValue('hour', e.target.value)}
              >
                {HOUR_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="text-xs text-dark-text-muted mt-1">0-23</div>
            </div>

            <div>
              <label className="form-label-terminal">Day of Month</label>
              <select
                className="form-input-terminal"
                value={cronValues.day}
                onChange={(e) => updateCronValue('day', e.target.value)}
              >
                {DAY_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="text-xs text-dark-text-muted mt-1">1-31</div>
            </div>

            <div>
              <label className="form-label-terminal">Month</label>
              <select
                className="form-input-terminal"
                value={cronValues.month}
                onChange={(e) => updateCronValue('month', e.target.value)}
              >
                {MONTH_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="text-xs text-dark-text-muted mt-1">1-12</div>
            </div>

            <div>
              <label className="form-label-terminal">Day of Week</label>
              <select
                className="form-input-terminal"
                value={cronValues.weekday}
                onChange={(e) => updateCronValue('weekday', e.target.value)}
              >
                {WEEKDAY_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <div className="text-xs text-dark-text-muted mt-1">0-6 (Sun-Sat)</div>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <label className="form-label-terminal">Cron Expression</label>
          <input
            type="text"
            className="form-input-terminal font-mono"
            value={manualExpression}
            onChange={(e) => handleManualChange(e.target.value)}
            placeholder="0 9 * * 1-5"
          />
          <div className="text-xs text-dark-text-muted mt-1">
            Format: minute hour day month weekday
          </div>
        </div>
      )}

      {/* Current Expression Display */}
      <div className="card-terminal p-4">
        <div className="flex items-center space-x-3 mb-3">
          <ClockIcon className="w-5 h-5 text-terminal-400" />
          <span className="text-terminal-400 font-mono font-semibold">Current Expression</span>
        </div>
        
        <div className="space-y-2">
          <div className="bg-dark-bg border border-dark-border rounded p-3">
            <div className="font-mono text-terminal-400 text-lg">
              {mode === 'simple' 
                ? `${cronValues.minute} ${cronValues.hour} ${cronValues.day} ${cronValues.month} ${cronValues.weekday}`
                : manualExpression
              }
            </div>
          </div>
          
          <div className="text-sm text-dark-text-secondary">
            <strong>Runs:</strong> {getHumanReadable()}
          </div>
        </div>
      </div>

      {/* Validation Status */}
      <div className={`card p-4 ${
        validation.isValid 
          ? 'bg-terminal-900/20 border-terminal-500/30' 
          : 'bg-red-900/20 border-red-500/30'
      }`}>
        <div className="flex items-center space-x-3 mb-3">
          {validation.isValid ? (
            <CheckIcon className="w-5 h-5 text-terminal-400" />
          ) : (
            <div className="w-5 h-5 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
          )}
          <span className={`font-mono font-semibold ${
            validation.isValid ? 'text-terminal-400' : 'text-red-400'
          }`}>
            {validation.isValid ? 'Valid Expression' : 'Invalid Expression'}
          </span>
        </div>

        {validation.error && (
          <div className="text-red-400 text-sm mb-3">
            {validation.error}
          </div>
        )}

        {validation.isValid && validation.nextRuns && validation.nextRuns.length > 0 && (
          <div>
            <div className="text-sm text-dark-text-secondary mb-2">
              Next 5 scheduled runs:
            </div>
            <div className="space-y-1">
              {validation.nextRuns.map((run, index) => (
                <div key={index} className="text-xs font-mono text-terminal-400">
                  {new Date(run).toLocaleString()}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="bg-dark-surface border border-dark-border rounded p-4">
        <h4 className="text-terminal-400 font-mono font-semibold mb-2">
          Cron Expression Format
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
          <div>
            <div className="text-terminal-400 font-mono">Minute</div>
            <div className="text-dark-text-secondary">0-59</div>
            <div className="text-dark-text-muted">* = every</div>
          </div>
          <div>
            <div className="text-terminal-400 font-mono">Hour</div>
            <div className="text-dark-text-secondary">0-23</div>
            <div className="text-dark-text-muted">*/6 = every 6</div>
          </div>
          <div>
            <div className="text-terminal-400 font-mono">Day</div>
            <div className="text-dark-text-secondary">1-31</div>
            <div className="text-dark-text-muted">1,15 = 1st & 15th</div>
          </div>
          <div>
            <div className="text-terminal-400 font-mono">Month</div>
            <div className="text-dark-text-secondary">1-12</div>
            <div className="text-dark-text-muted">1-6 = Jan-June</div>
          </div>
          <div>
            <div className="text-terminal-400 font-mono">Weekday</div>
            <div className="text-dark-text-secondary">0-6 (Sun-Sat)</div>
            <div className="text-dark-text-muted">1-5 = Mon-Fri</div>
          </div>
        </div>
      </div>
    </div>
  )
}