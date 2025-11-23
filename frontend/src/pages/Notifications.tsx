import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Notification, NotificationTemplate, notificationsApi } from '../services/phase3Api'
import { useNotificationUpdates } from '../hooks/useWebSocket'
import { 
  BellIcon,
  CheckIcon,
  TrashIcon,
  PlusIcon,
  PencilIcon,
  AdjustmentsHorizontalIcon,
  
  EnvelopeIcon,
  DevicePhoneMobileIcon,
  GlobeAltIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ViewMode = 'feed' | 'templates' | 'settings'

const CHANNEL_ICONS = {
  email: EnvelopeIcon,
  sms: DevicePhoneMobileIcon,
  webhook: GlobeAltIcon,
  in_app: ComputerDesktopIcon,
}

export default function Notifications() {
  const [viewMode, setViewMode] = useState<ViewMode>('feed')
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null)
  const [filterType, setFilterType] = useState<string>('all')
  const [filterChannel, setFilterChannel] = useState<string>('all')
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)
  const [page, setPage] = useState(1)

  // Template editor state
  const [editingTemplate, setEditingTemplate] = useState<NotificationTemplate | null>(null)
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [templateForm, setTemplateForm] = useState({
    name: '',
    channel: 'email' as 'email' | 'sms' | 'webhook' | 'in_app',
    subject: '',
    content: '',
    variables: [] as string[],
    is_active: true,
  })

  const queryClient = useQueryClient()

  // WebSocket for real-time notifications
  const { lastMessage, isConnected } = useNotificationUpdates()

  // Fetch notifications
  const { data: notificationsData, isLoading } = useQuery({
    queryKey: ['notifications', page, showUnreadOnly],
    queryFn: () => notificationsApi.getNotifications({
      page,
      limit: 20,
      unread_only: showUnreadOnly,
    }).then(res => res.data),
  })

  // Fetch notification templates
  const { data: templates = [] } = useQuery({
    queryKey: ['notification-templates'],
    queryFn: () => notificationsApi.getNotificationTemplates().then(res => res.data),
  })

  // Fetch channel preferences
  const { data: preferences = {} } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => notificationsApi.getChannelPreferences().then(res => res.data),
  })

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: notificationsApi.markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: notificationsApi.markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('All notifications marked as read')
    },
  })

  // Delete notification mutation
  const deleteNotificationMutation = useMutation({
    mutationFn: notificationsApi.deleteNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('Notification deleted')
    },
  })

  // Template mutations
  const createTemplateMutation = useMutation({
    mutationFn: notificationsApi.createNotificationTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] })
      setShowTemplateForm(false)
      resetTemplateForm()
      toast.success('Template created successfully')
    },
  })

  const updateTemplateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<NotificationTemplate>) =>
      notificationsApi.updateNotificationTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] })
      setShowTemplateForm(false)
      setEditingTemplate(null)
      resetTemplateForm()
      toast.success('Template updated successfully')
    },
  })

  const deleteTemplateMutation = useMutation({
    mutationFn: notificationsApi.deleteNotificationTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-templates'] })
      toast.success('Template deleted successfully')
    },
  })

  // Update preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: notificationsApi.updateChannelPreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
      toast.success('Preferences updated successfully')
    },
  })

  // Handle real-time notification updates
  useEffect(() => {
    if (lastMessage && lastMessage.data.type === 'notification') {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.custom(() => (
        <div className="notification-info animate-slide-down">
          <div className="flex items-center">
            <BellIcon className="w-5 h-5 mr-2" />
            <div>
              <div className="font-semibold">{lastMessage.data.title}</div>
              <div className="text-sm">{lastMessage.data.message}</div>
            </div>
          </div>
        </div>
      ))
    }
  }, [lastMessage, queryClient])

  const resetTemplateForm = () => {
    setTemplateForm({
      name: '',
      channel: 'email',
      subject: '',
      content: '',
      variables: [],
      is_active: true,
    })
  }

  const handleEditTemplate = (template: NotificationTemplate) => {
    setEditingTemplate(template)
    setTemplateForm({
      name: template.name,
      channel: template.channel,
      subject: template.subject || '',
      content: template.content,
      variables: template.variables,
      is_active: template.is_active,
    })
    setShowTemplateForm(true)
  }

  const handleSaveTemplate = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (editingTemplate) {
      updateTemplateMutation.mutate({ id: editingTemplate.id, ...templateForm })
    } else {
      createTemplateMutation.mutate(templateForm)
    }
  }

  const notifications = notificationsData?.notifications || []
  const totalNotifications = notificationsData?.total || 0
  const unreadCount = notifications.filter(n => !n.read_at).length

  const filteredNotifications = notifications.filter(notification => {
    if (filterType !== 'all' && notification.type !== filterType) return false
    if (filterChannel !== 'all' && notification.channel !== filterChannel) return false
    return true
  })

  const renderNotificationFeed = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-terminal-400 font-mono">
            Notifications
          </h1>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-terminal-500' : 'bg-red-500'}`} />
            <span className="text-sm text-dark-text-secondary">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex space-x-3">
          {unreadCount > 0 && (
            <button
              onClick={() => markAllAsReadMutation.mutate()}
              className="btn-terminal"
              disabled={markAllAsReadMutation.isPending}
            >
              <CheckIcon className="w-4 h-4 mr-2" />
              Mark All Read ({unreadCount})
            </button>
          )}
          <button
            onClick={() => setViewMode('templates')}
            className="btn-secondary"
          >
            Templates
          </button>
          <button
            onClick={() => setViewMode('settings')}
            className="btn-secondary"
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
            Settings
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex items-center space-x-2">
          <label className="text-sm text-dark-text-secondary">Type:</label>
          <select
            className="form-input-terminal w-auto"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="all">All Types</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label className="text-sm text-dark-text-secondary">Channel:</label>
          <select
            className="form-input-terminal w-auto"
            value={filterChannel}
            onChange={(e) => setFilterChannel(e.target.value)}
          >
            <option value="all">All Channels</option>
            <option value="email">Email</option>
            <option value="sms">SMS</option>
            <option value="webhook">Webhook</option>
            <option value="in_app">In-App</option>
          </select>
        </div>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            className="text-terminal-500 focus:ring-terminal-500"
            checked={showUnreadOnly}
            onChange={(e) => setShowUnreadOnly(e.target.checked)}
          />
          <span className="text-sm text-dark-text-secondary">Unread only</span>
        </label>
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-2 border-terminal-500 border-t-transparent rounded-full animate-spin" />
          <div className="text-dark-text-secondary mt-2">Loading notifications...</div>
        </div>
      ) : filteredNotifications.length === 0 ? (
        <div className="text-center py-12">
          <BellIcon className="w-16 h-16 text-dark-text-muted mx-auto mb-4" />
          <div className="text-dark-text-muted">No notifications found</div>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredNotifications.map(notification => {
            const ChannelIcon = CHANNEL_ICONS[notification.channel]
            const isUnread = !notification.read_at
            
            return (
              <div
                key={notification.id}
                className={`card p-4 cursor-pointer transition-all ${
                  isUnread ? 'border-terminal-500/50 bg-terminal-500/5' : ''
                } ${selectedNotification?.id === notification.id ? 'ring-2 ring-terminal-500' : ''}`}
                onClick={() => {
                  setSelectedNotification(notification)
                  if (isUnread) {
                    markAsReadMutation.mutate(notification.id)
                  }
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`p-2 rounded ${
                      notification.type === 'success' ? 'bg-terminal-900/20 text-terminal-400' :
                      notification.type === 'error' ? 'bg-red-900/20 text-red-400' :
                      notification.type === 'warning' ? 'bg-yellow-900/20 text-yellow-400' :
                      'bg-blue-900/20 text-blue-400'
                    }`}>
                      <ChannelIcon className="w-5 h-5" />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className={`font-semibold ${isUnread ? 'text-terminal-400' : 'text-dark-text-primary'}`}>
                          {notification.title}
                        </h3>
                        {isUnread && (
                          <div className="w-2 h-2 bg-terminal-500 rounded-full" />
                        )}
                      </div>
                      
                      <p className="text-dark-text-secondary text-sm mb-2">
                        {notification.message}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-xs text-dark-text-muted">
                        <span>{notification.channel.toUpperCase()}</span>
                        <span>{notification.recipient}</span>
                        <span>{new Date(notification.created_at).toLocaleString()}</span>
                        <span className={`px-2 py-1 rounded ${
                          notification.status === 'delivered' ? 'bg-terminal-900/20 text-terminal-400' :
                          notification.status === 'failed' ? 'bg-red-900/20 text-red-400' :
                          notification.status === 'sent' ? 'bg-blue-900/20 text-blue-400' :
                          'bg-yellow-900/20 text-yellow-400'
                        }`}>
                          {notification.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteNotificationMutation.mutate(notification.id)
                      }}
                      className="btn-danger p-2"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination */}
      {totalNotifications > 20 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-dark-text-secondary">
            Showing {Math.min(20, notifications.length)} of {totalNotifications} notifications
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={notifications.length < 20}
              className="btn-secondary"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )

  const renderTemplates = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Notification Templates
        </h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setViewMode('feed')}
            className="btn-secondary"
          >
            Back to Feed
          </button>
          <button
            onClick={() => {
              setEditingTemplate(null)
              resetTemplateForm()
              setShowTemplateForm(true)
            }}
            className="btn-terminal-solid"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create Template
          </button>
        </div>
      </div>

      {showTemplateForm ? (
        <div className="card-terminal p-6">
          <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
            {editingTemplate ? 'Edit Template' : 'Create Template'}
          </h2>
          
          <form onSubmit={handleSaveTemplate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label-terminal">Template Name</label>
                <input
                  type="text"
                  className="form-input-terminal"
                  value={templateForm.name}
                  onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Lead Response Template"
                  required
                />
              </div>
              
              <div>
                <label className="form-label-terminal">Channel</label>
                <select
                  className="form-input-terminal"
                  value={templateForm.channel}
                  onChange={(e) => setTemplateForm(prev => ({ ...prev, channel: e.target.value as any }))}
                >
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="webhook">Webhook</option>
                  <option value="in_app">In-App</option>
                </select>
              </div>
            </div>

            {(templateForm.channel === 'email' || templateForm.channel === 'in_app') && (
              <div>
                <label className="form-label-terminal">Subject</label>
                <input
                  type="text"
                  className="form-input-terminal"
                  value={templateForm.subject}
                  onChange={(e) => setTemplateForm(prev => ({ ...prev, subject: e.target.value }))}
                  placeholder="New Lead Alert - {{lead.title}}"
                />
              </div>
            )}

            <div>
              <label className="form-label-terminal">Content</label>
              <textarea
                className="form-input-terminal h-32"
                value={templateForm.content}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, content: e.target.value }))}
                placeholder="A new lead has been received: {{lead.title}} in {{lead.location}}"
                required
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="template_active"
                className="mr-2 text-terminal-500 focus:ring-terminal-500"
                checked={templateForm.is_active}
                onChange={(e) => setTemplateForm(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <label htmlFor="template_active" className="form-label-terminal">
                Template is active
              </label>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowTemplateForm(false)
                  setEditingTemplate(null)
                  resetTemplateForm()
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-terminal-solid"
                disabled={createTemplateMutation.isPending || updateTemplateMutation.isPending}
              >
                {createTemplateMutation.isPending || updateTemplateMutation.isPending ? (
                  <div className="flex items-center">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin mr-2" />
                    Saving...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <CheckIcon className="w-4 h-4 mr-2" />
                    {editingTemplate ? 'Update Template' : 'Create Template'}
                  </div>
                )}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.map(template => {
            const ChannelIcon = CHANNEL_ICONS[template.channel]
            return (
              <div key={template.id} className="card-terminal p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <ChannelIcon className="w-5 h-5 text-terminal-400" />
                    <h3 className="font-semibold text-terminal-400">
                      {template.name}
                    </h3>
                  </div>
                  <span className={`status-${template.is_active ? 'online' : 'offline'}`}>
                    {template.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-dark-text-secondary">Channel:</span>
                    <span className="ml-2 text-terminal-400 font-mono">
                      {template.channel.toUpperCase()}
                    </span>
                  </div>
                  
                  {template.subject && (
                    <div>
                      <span className="text-dark-text-secondary">Subject:</span>
                      <div className="text-dark-text-primary text-xs mt-1">
                        {template.subject}
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <span className="text-dark-text-secondary">Variables:</span>
                    <span className="ml-2 text-terminal-400 font-mono">
                      {template.variables.length}
                    </span>
                  </div>
                </div>

                <div className="flex justify-end space-x-2 mt-4">
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="btn-secondary text-xs"
                  >
                    <PencilIcon className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this template?')) {
                        deleteTemplateMutation.mutate(template.id)
                      }
                    }}
                    className="btn-danger text-xs"
                  >
                    <TrashIcon className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )

  const renderSettings = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-terminal-400 font-mono">
          Notification Settings
        </h1>
        <button
          onClick={() => setViewMode('feed')}
          className="btn-secondary"
        >
          Back to Feed
        </button>
      </div>

      <div className="card-terminal p-6">
        <h2 className="text-lg font-semibold text-terminal-400 font-mono mb-4">
          Channel Preferences
        </h2>
        
        <div className="space-y-4">
          {Object.entries(CHANNEL_ICONS).map(([channel, Icon]) => (
            <div key={channel} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Icon className="w-5 h-5 text-terminal-400" />
                <span className="text-dark-text-primary capitalize">{channel}</span>
              </div>
              
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="mr-2 text-terminal-500 focus:ring-terminal-500"
                    checked={preferences[channel]?.enabled || false}
                    onChange={(e) => {
                      updatePreferencesMutation.mutate({
                        ...preferences,
                        [channel]: {
                          ...preferences[channel],
                          enabled: e.target.checked,
                        },
                      })
                    }}
                  />
                  <span className="text-sm text-dark-text-secondary">Enabled</span>
                </label>
                
                {channel === 'email' && (
                  <input
                    type="email"
                    className="form-input-terminal w-48"
                    placeholder="Email address"
                    value={preferences[channel]?.address || ''}
                    onChange={(e) => {
                      updatePreferencesMutation.mutate({
                        ...preferences,
                        [channel]: {
                          ...preferences[channel],
                          address: e.target.value,
                        },
                      })
                    }}
                  />
                )}
                
                {channel === 'sms' && (
                  <input
                    type="tel"
                    className="form-input-terminal w-48"
                    placeholder="Phone number"
                    value={preferences[channel]?.phone || ''}
                    onChange={(e) => {
                      updatePreferencesMutation.mutate({
                        ...preferences,
                        [channel]: {
                          ...preferences[channel],
                          phone: e.target.value,
                        },
                      })
                    }}
                  />
                )}
                
                {channel === 'webhook' && (
                  <input
                    type="url"
                    className="form-input-terminal w-48"
                    placeholder="Webhook URL"
                    value={preferences[channel]?.url || ''}
                    onChange={(e) => {
                      updatePreferencesMutation.mutate({
                        ...preferences,
                        [channel]: {
                          ...preferences[channel],
                          url: e.target.value,
                        },
                      })
                    }}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  // Render based on view mode
  if (viewMode === 'templates') {
    return renderTemplates()
  }

  if (viewMode === 'settings') {
    return renderSettings()
  }

  return renderNotificationFeed()
}