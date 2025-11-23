import { Fragment } from 'react'
import { Listbox, Transition } from '@headlessui/react'
import { ChevronDownIcon, CheckIcon } from '@heroicons/react/24/outline'
import { LeadSource } from '@/types/lead'

export interface SourceConfig {
  id: LeadSource
  name: string
  icon: string
  color: string
  enabled: boolean
}

export const SOURCE_CONFIGS: SourceConfig[] = [
  { id: 'craigslist', name: 'Craigslist', icon: '📍', color: '#FF6600', enabled: true },
  { id: 'google_maps', name: 'Google Maps', icon: '🗺️', color: '#4285F4', enabled: false },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: '#0A66C2', enabled: false },
  { id: 'indeed', name: 'Indeed', icon: '🔍', color: '#2557A7', enabled: false },
  { id: 'monster', name: 'Monster', icon: '👹', color: '#6E48AA', enabled: false },
  { id: 'ziprecruiter', name: 'ZipRecruiter', icon: '⚡', color: '#1C8C3F', enabled: false },
]

interface SourceSelectorProps {
  value: LeadSource
  onChange: (source: LeadSource) => void
  enabledSources?: LeadSource[]
  className?: string
}

export default function SourceSelector({
  value,
  onChange,
  enabledSources,
  className = ''
}: SourceSelectorProps) {
  // Filter to only show enabled sources
  const availableSources = enabledSources
    ? SOURCE_CONFIGS.filter(s => enabledSources.includes(s.id))
    : SOURCE_CONFIGS.filter(s => s.enabled)

  const selectedSource = SOURCE_CONFIGS.find(s => s.id === value) || availableSources[0]

  return (
    <Listbox value={value} onChange={onChange}>
      <div className={`relative ${className}`}>
        <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-dark-surface border border-dark-border py-3 pl-4 pr-10 text-left focus:outline-none focus:ring-2 focus:ring-terminal-500 transition-all">
          <span className="flex items-center gap-3">
            <span className="text-2xl">{selectedSource.icon}</span>
            <span className="block truncate text-dark-text-primary font-medium">
              {selectedSource.name}
            </span>
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <ChevronDownIcon
              className="h-5 w-5 text-dark-text-muted"
              aria-hidden="true"
            />
          </span>
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-dark-surface border border-dark-border py-1 shadow-lg focus:outline-none">
            {availableSources.map((source) => (
              <Listbox.Option
                key={source.id}
                className={({ active }) =>
                  `relative cursor-pointer select-none py-3 pl-4 pr-10 ${
                    active ? 'bg-dark-border/50' : ''
                  }`
                }
                value={source.id}
              >
                {({ selected }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{source.icon}</span>
                      <div className="flex flex-col">
                        <span
                          className={`block truncate ${
                            selected ? 'font-semibold' : 'font-normal'
                          } text-dark-text-primary`}
                        >
                          {source.name}
                        </span>
                        {!source.enabled && (
                          <span className="text-xs text-yellow-400">Coming Soon</span>
                        )}
                      </div>
                    </div>
                    {selected ? (
                      <span className="absolute inset-y-0 right-0 flex items-center pr-3">
                        <CheckIcon
                          className="h-5 w-5 text-terminal-500"
                          aria-hidden="true"
                        />
                      </span>
                    ) : null}
                  </>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  )
}

// Helper function to get source config
export function getSourceConfig(source: LeadSource): SourceConfig {
  return SOURCE_CONFIGS.find(s => s.id === source) || SOURCE_CONFIGS[0]
}
