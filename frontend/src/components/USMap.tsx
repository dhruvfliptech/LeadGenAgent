import { useState, useCallback } from 'react'

// removed unused StateData interface

interface USMapProps {
  selectedStates: string[]
  onStateToggle: (stateCode: string) => void
  onStatesChange: (states: string[]) => void
  showHeatMap?: boolean
  heatMapData?: Record<string, number>
  showLeadCounts?: boolean
  leadCountData?: Record<string, number>
  interactive?: boolean
}

// US State coordinates and paths (simplified SVG paths)
const STATE_PATHS = {
  AL: "M 633 342 L 633 435 L 692 435 L 692 342 Z",
  AK: "M 158 435 L 158 500 L 250 500 L 250 435 Z",
  AZ: "M 200 300 L 200 400 L 300 400 L 300 300 Z",
  AR: "M 500 300 L 500 400 L 600 400 L 600 300 Z",
  CA: "M 50 200 L 50 450 L 150 450 L 150 200 Z",
  CO: "M 350 250 L 350 350 L 450 350 L 450 250 Z",
  CT: "M 800 200 L 850 200 L 850 230 L 800 230 Z",
  DE: "M 780 250 L 800 250 L 800 280 L 780 280 Z",
  FL: "M 650 400 L 650 500 L 750 500 L 750 400 Z",
  GA: "M 630 320 L 630 420 L 730 420 L 730 320 Z",
  HI: "M 250 450 L 300 450 L 300 500 L 250 500 Z",
  ID: "M 250 100 L 250 250 L 350 250 L 350 100 Z",
  IL: "M 550 200 L 550 350 L 600 350 L 600 200 Z",
  IN: "M 600 200 L 600 350 L 650 350 L 650 200 Z",
  IA: "M 500 200 L 500 300 L 600 300 L 600 200 Z",
  KS: "M 400 250 L 400 350 L 500 350 L 500 250 Z",
  KY: "M 600 280 L 600 330 L 700 330 L 700 280 Z",
  LA: "M 500 380 L 500 430 L 580 430 L 580 380 Z",
  ME: "M 820 100 L 870 100 L 870 200 L 820 200 Z",
  MD: "M 740 250 L 790 250 L 790 280 L 740 280 Z",
  MA: "M 800 180 L 870 180 L 870 210 L 800 210 Z",
  MI: "M 620 150 L 620 250 L 680 250 L 680 150 Z",
  MN: "M 480 100 L 480 200 L 550 200 L 550 100 Z",
  MS: "M 580 320 L 580 420 L 630 420 L 630 320 Z",
  MO: "M 500 230 L 500 330 L 600 330 L 600 230 Z",
  MT: "M 300 80 L 300 200 L 450 200 L 450 80 Z",
  NE: "M 400 200 L 400 280 L 500 280 L 500 200 Z",
  NV: "M 150 200 L 150 350 L 250 350 L 250 200 Z",
  NH: "M 800 150 L 830 150 L 830 200 L 800 200 Z",
  NJ: "M 760 220 L 790 220 L 790 280 L 760 280 Z",
  NM: "M 300 300 L 300 400 L 400 400 L 400 300 Z",
  NY: "M 750 150 L 750 230 L 820 230 L 820 150 Z",
  NC: "M 700 280 L 700 330 L 800 330 L 800 280 Z",
  ND: "M 400 80 L 400 180 L 500 180 L 500 80 Z",
  OH: "M 650 200 L 650 300 L 720 300 L 720 200 Z",
  OK: "M 400 300 L 400 380 L 500 380 L 500 300 Z",
  OR: "M 50 100 L 50 250 L 200 250 L 200 100 Z",
  PA: "M 720 200 L 720 280 L 800 280 L 800 200 Z",
  RI: "M 850 200 L 870 200 L 870 220 L 850 220 Z",
  SC: "M 700 320 L 700 370 L 750 370 L 750 320 Z",
  SD: "M 400 150 L 400 230 L 500 230 L 500 150 Z",
  TN: "M 580 280 L 580 330 L 700 330 L 700 280 Z",
  TX: "M 300 350 L 300 480 L 500 480 L 500 350 Z",
  UT: "M 300 200 L 300 320 L 380 320 L 380 200 Z",
  VT: "M 800 120 L 820 120 L 820 180 L 800 180 Z",
  VA: "M 720 250 L 720 310 L 800 310 L 800 250 Z",
  WA: "M 50 50 L 50 150 L 200 150 L 200 50 Z",
  WV: "M 680 230 L 680 300 L 740 300 L 740 230 Z",
  WI: "M 550 120 L 550 220 L 620 220 L 620 120 Z",
  WY: "M 350 150 L 350 250 L 450 250 L 450 150 Z"
}

const STATE_NAMES: Record<string, string> = {
  AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California',
  CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia',
  HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa',
  KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland',
  MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri',
  MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey',
  NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio',
  OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina',
  SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont',
  VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming'
}

export default function USMap({
  selectedStates,
  onStateToggle,
  onStatesChange,
  showHeatMap = false,
  heatMapData = {},
  showLeadCounts = false,
  leadCountData = {},
  interactive = true
}: USMapProps) {
  const [hoveredState, setHoveredState] = useState<string | null>(null)

  const getStateColor = useCallback((stateCode: string) => {
    const isSelected = selectedStates.includes(stateCode)
    const isHovered = hoveredState === stateCode
    
    if (showHeatMap && heatMapData[stateCode]) {
      const density = heatMapData[stateCode]
      const intensity = Math.min(density / 100, 1) // Normalize to 0-1
      
      if (isSelected) {
        return `rgba(0, 255, 0, ${0.3 + intensity * 0.7})` // Terminal green with varying opacity
      } else if (isHovered) {
        return `rgba(0, 255, 0, ${0.1 + intensity * 0.3})`
      } else {
        return `rgba(0, 255, 0, ${intensity * 0.5})`
      }
    }
    
    if (isSelected) {
      return '#00FF00' // Terminal green
    } else if (isHovered && interactive) {
      return '#00CC00' // Slightly darker green on hover
    } else {
      return '#1a1a1a' // Dark surface color
    }
  }, [selectedStates, hoveredState, showHeatMap, heatMapData, interactive])

  const getStrokeColor = useCallback((stateCode: string) => {
    const isSelected = selectedStates.includes(stateCode)
    const isHovered = hoveredState === stateCode
    
    if (isSelected) {
      return '#00FF00'
    } else if (isHovered && interactive) {
      return '#00CC00'
    } else {
      return '#333333'
    }
  }, [selectedStates, hoveredState, interactive])

  const handleStateClick = (stateCode: string) => {
    if (!interactive) return
    onStateToggle(stateCode)
  }

  const handleSelectAll = () => {
    onStatesChange(Object.keys(STATE_NAMES))
  }

  const handleSelectNone = () => {
    onStatesChange([])
  }

  const handleSelectRegion = (region: string) => {
    const regions: Record<string, string[]> = {
      northeast: ['CT', 'ME', 'MA', 'NH', 'NJ', 'NY', 'PA', 'RI', 'VT'],
      southeast: ['AL', 'AR', 'DE', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'NC', 'SC', 'TN', 'VA', 'WV'],
      midwest: ['IL', 'IN', 'IA', 'KS', 'MI', 'MN', 'MO', 'NE', 'ND', 'OH', 'SD', 'WI'],
      southwest: ['AZ', 'NM', 'TX', 'OK'],
      west: ['AK', 'CA', 'CO', 'HI', 'ID', 'MT', 'NV', 'OR', 'UT', 'WA', 'WY']
    }
    
    if (regions[region]) {
      onStatesChange(regions[region])
    }
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      {interactive && (
        <div className="flex flex-wrap gap-2 mb-4">
          <button onClick={handleSelectAll} className="btn-terminal text-xs">
            Select All
          </button>
          <button onClick={handleSelectNone} className="btn-secondary text-xs">
            Select None
          </button>
          <button onClick={() => handleSelectRegion('northeast')} className="btn-secondary text-xs">
            Northeast
          </button>
          <button onClick={() => handleSelectRegion('southeast')} className="btn-secondary text-xs">
            Southeast
          </button>
          <button onClick={() => handleSelectRegion('midwest')} className="btn-secondary text-xs">
            Midwest
          </button>
          <button onClick={() => handleSelectRegion('southwest')} className="btn-secondary text-xs">
            Southwest
          </button>
          <button onClick={() => handleSelectRegion('west')} className="btn-secondary text-xs">
            West
          </button>
        </div>
      )}

      {/* Map */}
      <div className="relative bg-dark-bg border border-dark-border rounded-lg p-4">
        <svg
          viewBox="0 0 900 500"
          className="w-full h-auto"
          style={{ maxHeight: '500px' }}
        >
          {Object.entries(STATE_PATHS).map(([stateCode, path]) => (
            <g key={stateCode}>
              {/* State path */}
              <path
                d={path}
                fill={getStateColor(stateCode)}
                stroke={getStrokeColor(stateCode)}
                strokeWidth="1"
                className={interactive ? "cursor-pointer transition-all duration-200" : ""}
                onClick={() => handleStateClick(stateCode)}
                onMouseEnter={() => interactive && setHoveredState(stateCode)}
                onMouseLeave={() => interactive && setHoveredState(null)}
              />
              
              {/* State label */}
              <text
                x={getStateCenterX(path)}
                y={getStateCenterY(path)}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs font-mono fill-current text-dark-text-primary pointer-events-none"
                style={{ fontSize: '10px' }}
              >
                {stateCode}
              </text>
              
              {/* Lead count display */}
              {showLeadCounts && leadCountData[stateCode] && (
                <text
                  x={getStateCenterX(path)}
                  y={getStateCenterY(path) + 12}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="text-xs font-mono fill-current text-terminal-400 pointer-events-none"
                  style={{ fontSize: '8px' }}
                >
                  {leadCountData[stateCode]}
                </text>
              )}
            </g>
          ))}
        </svg>

        {/* Hover tooltip */}
        {hoveredState && interactive && (
          <div className="absolute top-4 right-4 bg-dark-surface border border-terminal-500/30 rounded p-2 pointer-events-none">
            <div className="text-terminal-400 font-mono text-sm font-bold">
              {STATE_NAMES[hoveredState]}
            </div>
            <div className="text-dark-text-secondary text-xs">
              {selectedStates.includes(hoveredState) ? 'Selected' : 'Click to select'}
            </div>
            {showLeadCounts && leadCountData[hoveredState] && (
              <div className="text-terminal-400 text-xs">
                {leadCountData[hoveredState]} leads
              </div>
            )}
            {showHeatMap && heatMapData[hoveredState] && (
              <div className="text-terminal-400 text-xs">
                Density: {heatMapData[hoveredState]}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      {(showHeatMap || showLeadCounts) && (
        <div className="flex items-center justify-between text-xs">
          {showHeatMap && (
            <div className="flex items-center space-x-2">
              <span className="text-dark-text-secondary">Heat Map:</span>
              <div className="flex items-center space-x-1">
                <div className="w-4 h-3 bg-terminal-500/20" />
                <span className="text-dark-text-muted">Low</span>
                <div className="w-4 h-3 bg-terminal-500/60" />
                <span className="text-dark-text-muted">Medium</span>
                <div className="w-4 h-3 bg-terminal-500" />
                <span className="text-dark-text-muted">High</span>
              </div>
            </div>
          )}
          
          {selectedStates.length > 0 && (
            <div className="text-terminal-400 font-mono">
              {selectedStates.length} state{selectedStates.length !== 1 ? 's' : ''} selected
            </div>
          )}
        </div>
      )}

      {/* Selected states list */}
      {selectedStates.length > 0 && interactive && (
        <div className="bg-dark-surface border border-dark-border rounded p-3">
          <div className="text-sm text-dark-text-secondary mb-2">Selected States:</div>
          <div className="flex flex-wrap gap-1">
            {selectedStates.map(stateCode => (
              <span
                key={stateCode}
                className="inline-flex items-center px-2 py-1 bg-terminal-500/20 text-terminal-400 text-xs font-mono rounded border border-terminal-500/30"
              >
                {STATE_NAMES[stateCode]}
                <button
                  onClick={() => onStateToggle(stateCode)}
                  className="ml-1 text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Helper functions to get state center coordinates (simplified)
function getStateCenterX(path: string): number {
  // Extract rough center X from path (simplified)
  const matches = path.match(/M (\d+)/);
  return matches ? parseInt(matches[1]) + 25 : 0;
}

function getStateCenterY(path: string): number {
  // Extract rough center Y from path (simplified)
  const matches = path.match(/M \d+ (\d+)/);
  return matches ? parseInt(matches[1]) + 25 : 0;
}