import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Schedule as ScheduleType, scheduleApi } from '../services/phase3Api'
import { useScheduleUpdates } from '../hooks/useWebSocket'
import CronBuilder from '../components/CronBuilder'
import { 
  ClockIcon,
  PlayIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CalendarIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ViewMode = 'list' | 'create' | 'edit' | 'logs' | 'calendar'

export default function Schedule() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedSchedule, setSelectedSchedule] = useState<ScheduleType | null>(null)
  // removed unused selectedTaskType
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    cron_expression: '0 9 * * *',
    task_type: 'scrape' as 'scrape' | 'send_emails' | 'export_data' | 'cleanup' | 'custom',
    task_config: {} as Record<string, any>,
    is_active: true,
  })

  const queryClient = useQueryClient()

  // WebSocket for real-time schedule updates
  const { lastMessage, isConnected } = useScheduleUpdates()

  // Fetch schedules
  const { data: schedules = [], isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => scheduleApi.getSchedules().then(res => res.data),
  })

  // Fetch schedule logs for selected schedule
  const { data: logsData } = useQuery({
    queryKey: ['schedule-logs', selectedSchedule?.id],
    queryFn: () => selectedSchedule ? 
      scheduleApi.getScheduleLogs(selectedSchedule.id, { limit: 50 }).then(res => res.data) : 
      Promise.resolve({ logs: [], total: 0 }),
    enabled: !!selectedSchedule && viewMode === 'logs',
  })

  // Create schedule mutation
  const createMutation = useMutation({
    mutationFn: scheduleApi.createSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setViewMode('list')
      resetForm()
      toast.success('Schedule created successfully')
    },
    onError: () => {
      toast.error('Failed to create schedule')
    },
  })

  // Update schedule mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<ScheduleType>) =>
      scheduleApi.updateSchedule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      setViewMode('list')
      resetForm()
      toast.success('Schedule updated successfully')
    },
    onError: () => {
      toast.error('Failed to update schedule')
    },
  })

  // Delete schedule mutation
  const deleteMutation = useMutation({
    mutationFn: scheduleApi.deleteSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      toast.success('Schedule deleted successfully')
    },
    onError: () => {
      toast.error('Failed to delete schedule')
    },
  })

  // Run schedule mutation
  const runMutation = useMutation({
    mutationFn: scheduleApi.runSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      toast.success('Schedule started successfully')
    },
    onError: () => {
      toast.error('Failed to start schedule')
    },
  })

  // Handle real-time updates
  useEffect(() => {
    if (lastMessage && lastMessage.data.type === 'schedule_update') {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      if (selectedSchedule && lastMessage.data.schedule_id === selectedSchedule.id) {
        queryClient.invalidateQueries({ queryKey: ['schedule-logs', selectedSchedule.id] })
      }
    }
  }, [lastMessage, queryClient, selectedSchedule])

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      cron_expression: '0 9 * * *',
      task_type: 'scrape',
      task_config: {},
      is_active: true,
    })
    setSelectedSchedule(null)
  }

  useEffect(() => {
    if (selectedSchedule) {
      setFormData({
        name: selectedSchedule.name,
        description: selectedSchedule.description || '',
        cron_expression: selectedSchedule.cron_expression,
        task_type: selectedSchedule.task_type,
        task_config: selectedSchedule.task_config,
        is_active: selectedSchedule.is_active,
      })
    }
  }, [selectedSchedule])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (selectedSchedule) {
      updateMutation.mutate({ id: selectedSchedule.id, ...formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEditSchedule = (schedule: ScheduleType) => {
    setSelectedSchedule(schedule)
    setViewMode('edit')
  }

  const handleViewLogs = (schedule: ScheduleType) => {
    setSelectedSchedule(schedule)
    setViewMode('logs')
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-5 h-5 text-terminal-400" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-400" />
      case 'running':
        return <div className="w-5 h-5 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
      default:
        return <ClockIcon className="w-5 h-5 text-dark-text-muted" />
    }
  }

  const getTaskConfigForm = () => {
    switch (formData.task_type) {
      case 'scrape':
        return (
          <div className="space-y-4">
            <div>
              <label className="form-label-terminal">Target Locations</label>
              <textarea
                className="form-input-terminal h-20"
                value={JSON.stringify(formData.task_config.locations || [], null, 2)}
                onChange={(e) => {
                  try {
                    const locations = JSON.parse(e.target.value)
                    setFormData(prev => ({
                      ...prev,
                      task_config: { ...prev.task_config, locations }
                    }))
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                placeholder='["CA", "NY", "TX"]'
              />
            </div>
            <div>
              <label className="form-label-terminal">Categories</label>
              <input
                type="text"
                className="form-input-terminal"
                value={formData.task_config.categories || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, categories: e.target.value }
                }))}
                placeholder="automotive,real-estate"
              />
            </div>
            <div>
              <label className="form-label-terminal">Max Pages</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.task_config.max_pages || 10}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, max_pages: parseInt(e.target.value) || 10 }
                }))}
                min="1"
                max="100"
              />
            </div>
          </div>
        )
      
      case 'send_emails':
        return (
          <div className="space-y-4">
            <div>
              <label className="form-label-terminal">Template ID</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.task_config.template_id || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, template_id: parseInt(e.target.value) || null }
                }))}
                placeholder="1"
              />
            </div>
            <div>
              <label className="form-label-terminal">Target Status</label>
              <select
                className="form-input-terminal"
                value={formData.task_config.target_status || 'new'}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, target_status: e.target.value }
                }))}
              >
                <option value="new">New Leads</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
              </select>
            </div>
            <div>
              <label className="form-label-terminal">Batch Size</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.task_config.batch_size || 50}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, batch_size: parseInt(e.target.value) || 50 }
                }))}
                min="1"
                max="1000"
              />
            </div>
          </div>
        )
      
      case 'export_data':
        return (
          <div className="space-y-4">
            <div>
              <label className="form-label-terminal">Export Type</label>
              <select
                className="form-input-terminal"
                value={formData.task_config.export_type || 'leads'}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, export_type: e.target.value }
                }))}
              >
                <option value="leads">Leads</option>
                <option value="analytics">Analytics</option>
                <option value="templates">Templates</option>
              </select>
            </div>
            <div>
              <label className="form-label-terminal">Date Range (days)</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.task_config.date_range_days || 30}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, date_range_days: parseInt(e.target.value) || 30 }
                }))}
                min="1"
                max="365"
              />
            </div>
            <div>
              <label className="form-label-terminal">Email To</label>
              <input
                type="email"
                className="form-input-terminal"
                value={formData.task_config.email_to || ''}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, email_to: e.target.value }
                }))}
                placeholder="admin@example.com"
              />
            </div>
          </div>
        )
      
      case 'cleanup':
        return (
          <div className="space-y-4">
            <div>
              <label className="form-label-terminal">Cleanup Type</label>
              <select
                className="form-input-terminal"
                value={formData.task_config.cleanup_type || 'old_leads'}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, cleanup_type: e.target.value }
                }))}
              >
                <option value="old_leads">Old Leads</option>
                <option value="logs">Log Files</option>
                <option value="temp_files">Temporary Files</option>
              </select>
            </div>
            <div>
              <label className="form-label-terminal">Older Than (days)</label>
              <input
                type="number"
                className="form-input-terminal"
                value={formData.task_config.older_than_days || 90}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  task_config: { ...prev.task_config, older_than_days: parseInt(e.target.value) || 90 }
                }))}
                min="1"
                max="365"
              />
            </div>
          </div>
        )
      
      default:
        return (
          <div>
            <label className="form-label-terminal">Custom Configuration</label>
            <textarea
              className="form-input-terminal h-32"
              value={JSON.stringify(formData.task_config, null, 2)}
              onChange={(e) => {
                try {
                  const config = JSON.parse(e.target.value)
                  setFormData(prev => ({ ...prev, task_config: config }))
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder='{"custom_parameter": "value"}'
            />
          </div>
        )
    }
  }

  const renderScheduleForm = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          {selectedSchedule ? 'Edit Schedule' : 'Create Schedule'}
        </h1>
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

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Basic Information
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="form-label-terminal">Schedule Name</label>
              <input
                type="text"
                className="form-input-terminal"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Daily Lead Scraping"
                required
              />
            </div>
            
            <div>
              <label className="form-label-terminal">Description</label>
              <textarea
                className="form-input-terminal h-20"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Automatically scrape leads every morning at 9 AM"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label-terminal">Task Type</label>
                <select
                  className="form-input-terminal"
                  value={formData.task_type}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    task_type: e.target.value as any,
                    task_config: {} // Reset config when changing type
                  }))}
                >
                  <option value="scrape">Scrape Leads</option>
                  <option value="send_emails">Send Emails</option>
                  <option value="export_data">Export Data</option>
                  <option value="cleanup">Cleanup</option>
                  <option value="custom">Custom Task</option>
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
                  Schedule is active
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Schedule Configuration */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Schedule Configuration
          </h2>
          
          <CronBuilder
            value={formData.cron_expression}
            onChange={(expression) => setFormData(prev => ({ ...prev, cron_expression: expression }))}
          />
        </div>

        {/* Task Configuration */}
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            Task Configuration
          </h2>
          
          {getTaskConfigForm()}
        </div>

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
              <>{selectedSchedule ? 'Update Schedule' : 'Create Schedule'}</>
            )}
          </button>
        </div>
      </form>
    </div>
  )

  const renderScheduleList = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Schedules
          </h1>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-terminal-500' : 'bg-red-500'}`} />
            <span className="text-sm text-dark-text-secondary">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={() => setViewMode('calendar')}
            className="btn-terminal"
          >
            <CalendarIcon className="w-4 h-4 mr-2" />
            Calendar
          </button>
          <button
            onClick={() => setViewMode('create')}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Schedule
          </button>
        </div>
      </div>

      {/* Schedules List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-text-secondary mt-2">Loading schedules...</div>
        </div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-12">
          <ClockIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <div className="text-dark-text-muted mb-4">No schedules found</div>
          <button
            onClick={() => setViewMode('create')}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Your First Schedule
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map(schedule => (
            <div key={schedule.id} className="card-terminal p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-terminal-400 font-mono">
                      {schedule.name}
                    </h3>
                    {getStatusIcon(schedule.status)}
                    <span className={`status-${schedule.is_active ? 'online' : 'offline'}`}>
                      {schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  
                  {schedule.description && (
                    <p className="text-dark-text-secondary text-sm mb-3">
                      {schedule.description}
                    </p>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-dark-text-secondary">Task Type:</span>
                      <span className="ml-2 text-terminal-400 font-mono">
                        {schedule.task_type}
                      </span>
                    </div>
                    <div>
                      <span className="text-dark-text-secondary">Schedule:</span>
                      <span className="ml-2 text-terminal-400 font-mono">
                        {schedule.cron_expression}
                      </span>
                    </div>
                    <div>
                      <span className="text-dark-text-secondary">Next Run:</span>
                      <span className="ml-2 text-dark-text-primary">
                        {new Date(schedule.next_run).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-dark-text-secondary">Last Run:</span>
                      <span className="ml-2 text-dark-text-primary">
                        {schedule.last_run ? 
                          new Date(schedule.last_run).toLocaleString() : 
                          'Never'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => runMutation.mutate(schedule.id)}
                    className="btn-terminal"
                    disabled={schedule.status === 'running'}
                    title="Run now"
                  >
                    <PlayIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleViewLogs(schedule)}
                    className="btn-secondary"
                    title="View logs"
                  >
                    <DocumentTextIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleEditSchedule(schedule)}
                    className="btn-secondary"
                    title="Edit"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this schedule?')) {
                        deleteMutation.mutate(schedule.id)
                      }
                    }}
                    className="btn-danger"
                    title="Delete"
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

  const renderScheduleLogs = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Schedule Logs - {selectedSchedule?.name}
        </h1>
        <button
          onClick={() => setViewMode('list')}
          className="btn-secondary"
        >
          Back to Schedules
        </button>
      </div>

      {logsData && logsData.logs.length > 0 ? (
        <div className="space-y-3">
          {logsData.logs.map(log => (
            <div key={log.id} className="card-terminal p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getStatusIcon(log.status)}
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`font-semibold ${
                        log.status === 'success' ? 'text-terminal-400' :
                        log.status === 'failed' ? 'text-red-400' :
                        'text-blue-400'
                      }`}>
                        {log.status.toUpperCase()}
                      </span>
                      <span className="text-dark-text-secondary text-sm">
                        {new Date(log.started_at).toLocaleString()}
                      </span>
                    </div>
                    
                    {log.message && (
                      <p className="text-dark-text-primary text-sm mb-2">
                        {log.message}
                      </p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-xs text-dark-text-muted">
                      <span>Started: {new Date(log.started_at).toLocaleString()}</span>
                      {log.completed_at && (
                        <span>Completed: {new Date(log.completed_at).toLocaleString()}</span>
                      )}
                      {log.duration && (
                        <span>Duration: {log.duration}s</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <DocumentTextIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <div className="text-dark-text-muted">No logs found for this schedule</div>
        </div>
      )}
    </div>
  )

  const renderCalendarView = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Schedule Calendar
        </h1>
        <button
          onClick={() => setViewMode('list')}
          className="btn-secondary"
        >
          Back to List
        </button>
      </div>

      <div className="card-terminal p-6">
        <div className="text-center py-12">
          <CalendarIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <div className="text-dark-text-muted mb-4">Calendar View Coming Soon</div>
          <p className="text-dark-text-secondary text-sm">
            This will show a visual calendar with all scheduled tasks and their execution times.
          </p>
        </div>
      </div>
    </div>
  )

  // Render based on view mode
  if (viewMode === 'create' || viewMode === 'edit') {
    return renderScheduleForm()
  }

  if (viewMode === 'logs') {
    return renderScheduleLogs()
  }

  if (viewMode === 'calendar') {
    return renderCalendarView()
  }

  return renderScheduleList()
}