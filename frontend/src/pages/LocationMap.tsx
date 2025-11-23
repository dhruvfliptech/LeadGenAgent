import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { locationApi } from '../services/phase3Api'
import USMap from '../components/USMap'
import { 
  MapPinIcon,
  PlusIcon,
  BookmarkIcon,
  TrashIcon,
  PencilIcon,
  EyeIcon,
  ChartBarIcon,
  
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ViewMode = 'map' | 'groups' | 'stats'

interface LocationGroup {
  id: number
  name: string
  locations: string[]
  created_at: string
}

// Using loose types from API to avoid implicit any errors in reducers

export default function LocationMap() {
  const [viewMode, setViewMode] = useState<ViewMode>('map')
  const [selectedStates, setSelectedStates] = useState<string[]>([])
  const [showHeatMap, setShowHeatMap] = useState(false)
  const [showLeadCounts, setShowLeadCounts] = useState(true)
  
  // Group management state
  const [showGroupForm, setShowGroupForm] = useState(false)
  const [editingGroup, setEditingGroup] = useState<LocationGroup | null>(null)
  const [groupForm, setGroupForm] = useState({
    name: '',
    locations: [] as string[],
  })

  const queryClient = useQueryClient()

  // Fetch location groups
  const { data: locationGroups = [], isLoading: groupsLoading } = useQuery({
    queryKey: ['location-groups'],
    queryFn: () => locationApi.getLocationGroups().then(res => res.data),
  })

  // Heat map uses derived data from locationStats; no separate query

  // Fetch location stats
  const { data: locationStats = [] } = useQuery<any[]>({
    queryKey: ['location-stats'],
    queryFn: () => locationApi.getLocationStats().then(res => res.data),
  })

  // Create group mutation
  const createGroupMutation = useMutation({
    mutationFn: ({ name, locations }: { name: string; locations: string[] }) =>
      locationApi.createLocationGroup(name, locations),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-groups'] })
      setShowGroupForm(false)
      resetGroupForm()
      toast.success('Location group created successfully')
    },
    onError: () => {
      toast.error('Failed to create location group')
    },
  })

  // Update group mutation
  const updateGroupMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; locations?: string[] } }) =>
      locationApi.updateLocationGroup(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-groups'] })
      setShowGroupForm(false)
      setEditingGroup(null)
      resetGroupForm()
      toast.success('Location group updated successfully')
    },
    onError: () => {
      toast.error('Failed to update location group')
    },
  })

  // Delete group mutation
  const deleteGroupMutation = useMutation({
    mutationFn: locationApi.deleteLocationGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['location-groups'] })
      toast.success('Location group deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete location group')
    },
  })

  const resetGroupForm = () => {
    setGroupForm({
      name: '',
      locations: [],
    })
  }

  useEffect(() => {
    if (editingGroup) {
      setGroupForm({
        name: editingGroup.name,
        locations: editingGroup.locations,
      })
    }
  }, [editingGroup])

  const handleStateToggle = (stateCode: string) => {
    if (selectedStates.includes(stateCode)) {
      setSelectedStates(prev => prev.filter(s => s !== stateCode))
    } else {
      setSelectedStates(prev => [...prev, stateCode])
    }
  }

  const handleStatesChange = (states: string[]) => {
    setSelectedStates(states)
  }

  const handleEditGroup = (group: LocationGroup) => {
    setEditingGroup(group)
    setShowGroupForm(true)
  }

  const handleSaveGroup = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!groupForm.name.trim()) {
      toast.error('Group name is required')
      return
    }
    
    if (groupForm.locations.length === 0) {
      toast.error('At least one location is required')
      return
    }

    if (editingGroup) {
      updateGroupMutation.mutate({ 
        id: editingGroup.id, 
        data: { 
          name: groupForm.name, 
          locations: groupForm.locations 
        }
      })
    } else {
      createGroupMutation.mutate({ 
        name: groupForm.name, 
        locations: groupForm.locations 
      })
    }
  }

  const handleLoadGroup = (group: LocationGroup) => {
    setSelectedStates(group.locations)
    toast.success(`Loaded ${group.name} locations`)
  }

  // Convert stats data for heat map and lead counts
  const heatMapDataFormatted: Record<string, number> = (locationStats || []).reduce(
    (acc: Record<string, number>, stat: any) => {
      acc[stat.location] = (stat.conversion_rate || 0) * 100
      return acc
    },
    {}
  )

  const leadCountDataFormatted: Record<string, number> = (locationStats || []).reduce(
    (acc: Record<string, number>, stat: any) => {
      acc[stat.location] = stat.lead_count || 0
      return acc
    },
    {}
  )

  const renderMapView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Location Map
          </h1>
          <p className="text-dark-text-secondary mt-1">
            Select target locations and manage location groups
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setViewMode('stats')}
            className="btn-terminal"
          >
            <ChartBarIcon className="w-4 h-4 mr-2" />
            Statistics
          </button>
          <button
            onClick={() => setViewMode('groups')}
            className="btn-secondary"
          >
            <BookmarkIcon className="w-4 h-4 mr-2" />
            Groups
          </button>
        </div>
      </div>

      {/* Map Controls */}
      <div className="card-terminal p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                className="text-terminal-500 focus:ring-terminal-500"
                checked={showHeatMap}
                onChange={(e) => setShowHeatMap(e.target.checked)}
              />
              <span className="text-dark-text-secondary">Heat Map</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                className="text-terminal-500 focus:ring-terminal-500"
                checked={showLeadCounts}
                onChange={(e) => setShowLeadCounts(e.target.checked)}
              />
              <span className="text-dark-text-secondary">Lead Counts</span>
            </label>
          </div>
          
          {selectedStates.length > 0 && (
            <button
              onClick={() => {
                setGroupForm(prev => ({ ...prev, locations: selectedStates }))
                setShowGroupForm(true)
              }}
              className="btn-terminal"
            >
              <BookmarkIcon className="w-4 h-4 mr-2" />
              Save as Group
            </button>
          )}
        </div>
      </div>

      {/* US Map */}
      <div className="card-terminal p-6">
        <USMap
          selectedStates={selectedStates}
          onStateToggle={handleStateToggle}
          onStatesChange={handleStatesChange}
          showHeatMap={showHeatMap}
          heatMapData={showHeatMap ? heatMapDataFormatted : {}}
          showLeadCounts={showLeadCounts}
          leadCountData={showLeadCounts ? leadCountDataFormatted : {}}
          interactive={true}
        />
      </div>

      {/* Quick Actions */}
      {selectedStates.length > 0 && (
        <div className="card-terminal p-4">
          <h3 className="text-lg font-semibold text-terminal-400 font-mono mb-3">
            Quick Actions
          </h3>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {
                // This would typically trigger a scraping job for selected states
                toast.success(`Starting scraper for ${selectedStates.length} locations`)
              }}
              className="btn-terminal-solid"
            >
              Start Scraping
            </button>
            <button
              onClick={() => {
                // This would export leads from selected states
                toast.success(`Exporting leads from ${selectedStates.length} locations`)
              }}
              className="btn-secondary"
            >
              Export Leads
            </button>
            <button
              onClick={() => {
                // This would show analytics for selected states
                toast.success(`Showing analytics for ${selectedStates.length} locations`)
              }}
              className="btn-secondary"
            >
              View Analytics
            </button>
          </div>
        </div>
      )}
    </div>
  )

  const renderGroupsView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Location Groups
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setViewMode('map')}
            className="btn-secondary"
          >
            <MapPinIcon className="w-4 h-4 mr-2" />
            Back to Map
          </button>
          <button
            onClick={() => {
              setEditingGroup(null)
              resetGroupForm()
              setShowGroupForm(true)
            }}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Group
          </button>
        </div>
      </div>

      {showGroupForm && (
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            {editingGroup ? 'Edit Group' : 'Create Group'}
          </h2>
          
          <form onSubmit={handleSaveGroup} className="space-y-4">
            <div>
              <label className="form-label-terminal">Group Name</label>
              <input
                type="text"
                className="form-input-terminal"
                value={groupForm.name}
                onChange={(e) => setGroupForm(prev => ({ ...prev, name: e.target.value }))}
                placeholder="West Coast States"
                required
              />
            </div>

            <div>
              <label className="form-label-terminal">Selected Locations</label>
              <div className="mb-4">
                <USMap
                  selectedStates={groupForm.locations}
                  onStateToggle={(stateCode) => {
                    if (groupForm.locations.includes(stateCode)) {
                      setGroupForm(prev => ({ 
                        ...prev, 
                        locations: prev.locations.filter(s => s !== stateCode) 
                      }))
                    } else {
                      setGroupForm(prev => ({ 
                        ...prev, 
                        locations: [...prev.locations, stateCode] 
                      }))
                    }
                  }}
                  onStatesChange={(states) => setGroupForm(prev => ({ ...prev, locations: states }))}
                  interactive={true}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowGroupForm(false)
                  setEditingGroup(null)
                  resetGroupForm()
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-terminal-solid"
                disabled={createGroupMutation.isPending || updateGroupMutation.isPending}
              >
                {createGroupMutation.isPending || updateGroupMutation.isPending ? (
                  <div className="flex items-center">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </div>
                ) : (
                  <>{editingGroup ? 'Update Group' : 'Create Group'}</>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Groups List */}
      {groupsLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-text-secondary mt-2">Loading groups...</div>
        </div>
      ) : locationGroups.length === 0 ? (
        <div className="text-center py-12">
          <BookmarkIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <div className="text-dark-text-muted mb-4">No location groups found</div>
          <button
            onClick={() => {
              setEditingGroup(null)
              resetGroupForm()
              setShowGroupForm(true)
            }}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Your First Group
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {(locationGroups as any[]).map((group: any) => (
            <div key={group.id} className="card-terminal p-4">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-terminal-400 font-mono">
                  {group.name}
                </h3>
                <span className="text-xs text-dark-text-secondary">
                  {group.locations.length} states
                </span>
              </div>
              
              <div className="mb-4">
                <div className="text-sm text-dark-text-secondary mb-2">Locations:</div>
                <div className="flex flex-wrap gap-1">
                  {(group.locations as any[]).slice(0, 5).map((location: any) => (
                    <span
                      key={location}
                      className="inline-block px-2 py-1 bg-terminal-500/20 text-terminal-400 text-xs font-mono rounded"
                    >
                      {location}
                    </span>
                  ))}
                  {group.locations.length > 5 && (
                    <span className="text-xs text-dark-text-muted">
                      +{group.locations.length - 5} more
                    </span>
                  )}
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="text-xs text-dark-text-muted">
                  Created {new Date(group.created_at).toLocaleDateString()}
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleLoadGroup(group)}
                    className="btn-terminal text-xs"
                    title="Load on map"
                  >
                    <EyeIcon className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleEditGroup(group)}
                    className="btn-secondary text-xs"
                    title="Edit group"
                  >
                    <PencilIcon className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this group?')) {
                        deleteGroupMutation.mutate(group.id)
                      }
                    }}
                    className="btn-danger text-xs"
                    title="Delete group"
                  >
                    <TrashIcon className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  const renderStatsView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Location Statistics
        </h1>
        <button
          onClick={() => setViewMode('map')}
          className="btn-secondary"
        >
          <MapPinIcon className="w-4 h-4 mr-2" />
          Back to Map
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Locations</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {locationStats.length}
              </p>
            </div>
            <MapPinIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Leads</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {locationStats.reduce((sum, stat) => sum + stat.lead_count, 0).toLocaleString()}
              </p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Avg Conversion</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                {locationStats.length > 0 ? 
                  (locationStats.reduce((sum, stat) => sum + stat.conversion_rate, 0) / locationStats.length * 100).toFixed(1) + '%'
                  : 'N/A'
                }
              </p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
        
        <div className="card-terminal p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-dark-text-secondary text-sm">Total Revenue</p>
              <p className="text-2xl font-bold text-terminal-400 font-mono">
                ${locationStats.reduce((sum, stat) => sum + stat.revenue, 0).toLocaleString()}
              </p>
            </div>
            <ChartBarIcon className="w-8 h-8 text-terminal-500" />
          </div>
        </div>
      </div>

      {/* Statistics Table */}
      <div className="card-terminal">
        <div className="p-4 border-b border-dark-border">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono">
            Location Performance
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="table-terminal">
            <thead>
              <tr>
                <th>Location</th>
                <th>Lead Count</th>
                <th>Conversion Rate</th>
                <th>Average Price</th>
                <th>Total Revenue</th>
                <th>Performance</th>
              </tr>
            </thead>
            <tbody>
              {(locationStats as any[])
                .sort((a: any, b: any) => (b.lead_count || 0) - (a.lead_count || 0))
                .map((stat: any) => (
                  <tr key={stat.location}>
                    <td className="font-medium">{stat.location}</td>
                    <td className="font-mono">{stat.lead_count.toLocaleString()}</td>
                    <td className="font-mono">{(stat.conversion_rate * 100).toFixed(1)}%</td>
                    <td className="font-mono">${stat.avg_price.toLocaleString()}</td>
                    <td className="font-mono">${stat.revenue.toLocaleString()}</td>
                    <td>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-dark-border rounded-full h-2">
                          <div 
                            className="bg-terminal-500 h-2 rounded-full" 
                            style={{ 
                              width: `${Math.min(stat.conversion_rate * 100, 100)}%` 
                            }}
                          />
                        </div>
                        <span className="text-xs text-dark-text-muted">
                          {stat.conversion_rate > 0.1 ? 'High' : 
                           stat.conversion_rate > 0.05 ? 'Medium' : 'Low'}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )

  // Render based on view mode
  if (viewMode === 'groups') {
    return renderGroupsView()
  }

  if (viewMode === 'stats') {
    return renderStatsView()
  }

  return renderMapView()
}