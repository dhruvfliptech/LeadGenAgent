import { useState } from 'react'

interface SendRateControlProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
}

export default function SendRateControl({
  value,
  onChange,
  min = 5,
  max = 100,
  step = 5,
}: SendRateControlProps) {
  const [localValue, setLocalValue] = useState(value)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseInt(e.target.value)
    setLocalValue(newValue)
    onChange(newValue)
  }

  const getSafetyLevel = (rate: number) => {
    if (rate <= 20) return { label: 'Safe', color: 'text-green-600', bg: 'bg-green-50' }
    if (rate <= 50) return { label: 'Moderate', color: 'text-yellow-600', bg: 'bg-yellow-50' }
    return { label: 'Aggressive', color: 'text-red-600', bg: 'bg-red-50' }
  }

  const safety = getSafetyLevel(localValue)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Send Rate per Hour
        </label>
        <div className={`px-2.5 py-1 rounded-md text-xs font-medium ${safety.bg} ${safety.color}`}>
          {safety.label}
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localValue}
          onChange={handleChange}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
        />
        <div className="flex items-center space-x-2">
          <input
            type="number"
            min={min}
            max={max}
            step={step}
            value={localValue}
            onChange={handleChange}
            className="w-20 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-500">/hr</span>
        </div>
      </div>

      <div className="text-xs text-gray-500 space-y-1">
        <p>Estimated completion time: <strong>{Math.ceil(100 / localValue)} hours</strong> (for 100 recipients)</p>
        <p className="text-gray-400">
          Lower rates reduce the risk of being flagged as spam by email providers.
        </p>
      </div>
    </div>
  )
}
