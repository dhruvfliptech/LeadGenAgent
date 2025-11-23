import { useState } from 'react'
import {
  UserIcon,
  KeyIcon,
  EnvelopeIcon,
  BellIcon,
  CogIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'profile' | 'api-keys' | 'email' | 'notifications' | 'preferences'>('profile')
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})

  // Profile settings
  const [profileData, setProfileData] = useState({
    name: 'John Doe',
    email: 'john@example.com',
    company: 'FlipTech Pro',
    timezone: 'America/New_York',
  })

  // API Keys
  const [apiKeys, setApiKeys] = useState({
    openrouter: '****************************************',
    hunterIo: '',
    apolloIo: '',
    captchaSolver: '',
  })

  // Email Settings
  const [emailSettings, setEmailSettings] = useState({
    smtpHost: 'smtp.gmail.com',
    smtpPort: 587,
    smtpUsername: 'your-email@gmail.com',
    smtpPassword: '',
    fromName: 'FlipTech Pro',
    fromEmail: 'noreply@fliptechpro.com',
    replyTo: 'support@fliptechpro.com',
  })

  // Notification Settings
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    scrapeComplete: true,
    campaignComplete: true,
    newReplies: true,
    dailySummary: false,
    weeklyReport: true,
    systemAlerts: true,
  })

  // Preferences
  const [preferences, setPreferences] = useState({
    defaultLeadsPerPage: 25,
    autoSave: true,
    darkMode: true,
    compactView: false,
    showOnboarding: false,
  })

  const toggleApiKeyVisibility = (key: string) => {
    setShowApiKeys(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSaveProfile = () => {
    toast.success('Profile updated successfully')
  }

  const handleSaveApiKeys = () => {
    toast.success('API keys saved successfully')
  }

  const handleSaveEmailSettings = () => {
    toast.success('Email settings saved successfully')
  }

  const handleSaveNotifications = () => {
    toast.success('Notification settings saved successfully')
  }

  const handleSavePreferences = () => {
    toast.success('Preferences saved successfully')
  }

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: UserIcon },
    { id: 'api-keys' as const, label: 'API Keys', icon: KeyIcon },
    { id: 'email' as const, label: 'Email', icon: EnvelopeIcon },
    { id: 'notifications' as const, label: 'Notifications', icon: BellIcon },
    { id: 'preferences' as const, label: 'Preferences', icon: CogIcon },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-dark-text-primary">Settings</h1>
        <p className="text-sm text-dark-text-secondary mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Tabs */}
        <div className="lg:col-span-1">
          <div className="card p-4">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-terminal-500/20 text-terminal-400'
                      : 'text-dark-text-secondary hover:bg-dark-border/50'
                  }`}
                >
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          <div className="card p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary mb-1">
                    Profile Information
                  </h2>
                  <p className="text-sm text-dark-text-secondary">
                    Update your account profile information
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="form-label">Full Name</label>
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      className="form-input"
                    />
                  </div>

                  <div>
                    <label className="form-label">Email Address</label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="form-input"
                    />
                  </div>

                  <div>
                    <label className="form-label">Company</label>
                    <input
                      type="text"
                      value={profileData.company}
                      onChange={(e) => setProfileData({ ...profileData, company: e.target.value })}
                      className="form-input"
                    />
                  </div>

                  <div>
                    <label className="form-label">Timezone</label>
                    <select
                      value={profileData.timezone}
                      onChange={(e) => setProfileData({ ...profileData, timezone: e.target.value })}
                      className="form-input"
                    >
                      <option value="America/New_York">Eastern Time (ET)</option>
                      <option value="America/Chicago">Central Time (CT)</option>
                      <option value="America/Denver">Mountain Time (MT)</option>
                      <option value="America/Los_Angeles">Pacific Time (PT)</option>
                      <option value="UTC">UTC</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button onClick={handleSaveProfile} className="btn-primary">
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api-keys' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary mb-1">API Keys</h2>
                  <p className="text-sm text-dark-text-secondary">
                    Manage your API keys for third-party integrations
                  </p>
                </div>

                <div className="space-y-6">
                  {/* OpenRouter API Key */}
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-medium text-dark-text-primary">
                          OpenRouter API Key
                        </h3>
                        <p className="text-xs text-dark-text-muted mt-1">
                          Required for AI-powered lead analysis and email generation
                        </p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400 border border-green-500/20">
                        <CheckCircleIcon className="h-3 w-3 inline mr-1" />
                        Active
                      </span>
                    </div>
                    <div className="relative">
                      <input
                        type={showApiKeys.openrouter ? 'text' : 'password'}
                        value={apiKeys.openrouter}
                        onChange={(e) => setApiKeys({ ...apiKeys, openrouter: e.target.value })}
                        className="form-input pr-10"
                        placeholder="sk-or-v1-..."
                      />
                      <button
                        onClick={() => toggleApiKeyVisibility('openrouter')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-text-muted hover:text-dark-text-primary"
                      >
                        {showApiKeys.openrouter ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Hunter.io API Key */}
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-medium text-dark-text-primary">
                          Hunter.io API Key
                        </h3>
                        <p className="text-xs text-dark-text-muted mt-1">
                          Optional: For email enrichment and verification
                        </p>
                      </div>
                    </div>
                    <div className="relative">
                      <input
                        type={showApiKeys.hunterIo ? 'text' : 'password'}
                        value={apiKeys.hunterIo}
                        onChange={(e) => setApiKeys({ ...apiKeys, hunterIo: e.target.value })}
                        className="form-input pr-10"
                        placeholder="Enter Hunter.io API key"
                      />
                      <button
                        onClick={() => toggleApiKeyVisibility('hunterIo')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-text-muted hover:text-dark-text-primary"
                      >
                        {showApiKeys.hunterIo ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Apollo.io API Key */}
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-medium text-dark-text-primary">
                          Apollo.io API Key
                        </h3>
                        <p className="text-xs text-dark-text-muted mt-1">
                          Optional: For B2B contact enrichment
                        </p>
                      </div>
                    </div>
                    <div className="relative">
                      <input
                        type={showApiKeys.apolloIo ? 'text' : 'password'}
                        value={apiKeys.apolloIo}
                        onChange={(e) => setApiKeys({ ...apiKeys, apolloIo: e.target.value })}
                        className="form-input pr-10"
                        placeholder="Enter Apollo.io API key"
                      />
                      <button
                        onClick={() => toggleApiKeyVisibility('apolloIo')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-text-muted hover:text-dark-text-primary"
                      >
                        {showApiKeys.apolloIo ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* CAPTCHA Solver API Key */}
                  <div className="bg-dark-border/30 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-medium text-dark-text-primary">
                          CAPTCHA Solver API Key
                        </h3>
                        <p className="text-xs text-dark-text-muted mt-1">
                          Optional: For automated CAPTCHA solving (2Captcha, Anti-Captcha, etc.)
                        </p>
                      </div>
                    </div>
                    <div className="relative">
                      <input
                        type={showApiKeys.captchaSolver ? 'text' : 'password'}
                        value={apiKeys.captchaSolver}
                        onChange={(e) => setApiKeys({ ...apiKeys, captchaSolver: e.target.value })}
                        className="form-input pr-10"
                        placeholder="Enter CAPTCHA solver API key"
                      />
                      <button
                        onClick={() => toggleApiKeyVisibility('captchaSolver')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-text-muted hover:text-dark-text-primary"
                      >
                        {showApiKeys.captchaSolver ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button onClick={handleSaveApiKeys} className="btn-primary">
                    Save API Keys
                  </button>
                </div>
              </div>
            )}

            {/* Email Tab */}
            {activeTab === 'email' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary mb-1">
                    Email Configuration
                  </h2>
                  <p className="text-sm text-dark-text-secondary">
                    Configure SMTP settings for sending emails
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="form-label">SMTP Host</label>
                      <input
                        type="text"
                        value={emailSettings.smtpHost}
                        onChange={(e) => setEmailSettings({ ...emailSettings, smtpHost: e.target.value })}
                        className="form-input"
                      />
                    </div>
                    <div>
                      <label className="form-label">SMTP Port</label>
                      <input
                        type="number"
                        value={emailSettings.smtpPort}
                        onChange={(e) => setEmailSettings({ ...emailSettings, smtpPort: parseInt(e.target.value) })}
                        className="form-input"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="form-label">SMTP Username</label>
                    <input
                      type="email"
                      value={emailSettings.smtpUsername}
                      onChange={(e) => setEmailSettings({ ...emailSettings, smtpUsername: e.target.value })}
                      className="form-input"
                    />
                  </div>

                  <div>
                    <label className="form-label">SMTP Password</label>
                    <input
                      type="password"
                      value={emailSettings.smtpPassword}
                      onChange={(e) => setEmailSettings({ ...emailSettings, smtpPassword: e.target.value })}
                      className="form-input"
                      placeholder="Enter SMTP password"
                    />
                  </div>

                  <hr className="border-dark-border" />

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="form-label">From Name</label>
                      <input
                        type="text"
                        value={emailSettings.fromName}
                        onChange={(e) => setEmailSettings({ ...emailSettings, fromName: e.target.value })}
                        className="form-input"
                      />
                    </div>
                    <div>
                      <label className="form-label">From Email</label>
                      <input
                        type="email"
                        value={emailSettings.fromEmail}
                        onChange={(e) => setEmailSettings({ ...emailSettings, fromEmail: e.target.value })}
                        className="form-input"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="form-label">Reply-To Email</label>
                    <input
                      type="email"
                      value={emailSettings.replyTo}
                      onChange={(e) => setEmailSettings({ ...emailSettings, replyTo: e.target.value })}
                      className="form-input"
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <button className="btn-secondary">
                    Test Connection
                  </button>
                  <button onClick={handleSaveEmailSettings} className="btn-primary">
                    Save Settings
                  </button>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary mb-1">
                    Notification Preferences
                  </h2>
                  <p className="text-sm text-dark-text-secondary">
                    Choose what notifications you'd like to receive
                  </p>
                </div>

                <div className="space-y-4">
                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Email Notifications
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Receive email notifications for important events
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.emailNotifications}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, emailNotifications: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Scrape Complete
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Get notified when a scraping job finishes
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.scrapeComplete}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, scrapeComplete: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Campaign Complete
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Get notified when an email campaign finishes sending
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.campaignComplete}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, campaignComplete: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        New Replies
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Get notified when you receive email replies
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.newReplies}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, newReplies: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Daily Summary
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Receive a daily summary of your activities
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.dailySummary}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, dailySummary: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Weekly Report
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Receive a weekly performance report
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.weeklyReport}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, weeklyReport: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        System Alerts
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Get notified about system updates and issues
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={notificationSettings.systemAlerts}
                      onChange={(e) =>
                        setNotificationSettings({ ...notificationSettings, systemAlerts: e.target.checked })
                      }
                      className="form-checkbox"
                    />
                  </label>
                </div>

                <div className="flex justify-end">
                  <button onClick={handleSaveNotifications} className="btn-primary">
                    Save Preferences
                  </button>
                </div>
              </div>
            )}

            {/* Preferences Tab */}
            {activeTab === 'preferences' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-dark-text-primary mb-1">
                    Application Preferences
                  </h2>
                  <p className="text-sm text-dark-text-secondary">
                    Customize your application experience
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="form-label">Default Leads Per Page</label>
                    <select
                      value={preferences.defaultLeadsPerPage}
                      onChange={(e) =>
                        setPreferences({ ...preferences, defaultLeadsPerPage: parseInt(e.target.value) })
                      }
                      className="form-input"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Auto-Save
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Automatically save your work
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.autoSave}
                      onChange={(e) => setPreferences({ ...preferences, autoSave: e.target.checked })}
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Dark Mode
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Use dark theme throughout the application
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.darkMode}
                      onChange={(e) => setPreferences({ ...preferences, darkMode: e.target.checked })}
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Compact View
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Use a more compact layout for tables and lists
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.compactView}
                      onChange={(e) => setPreferences({ ...preferences, compactView: e.target.checked })}
                      className="form-checkbox"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 bg-dark-border/30 rounded-lg cursor-pointer hover:bg-dark-border/50">
                    <div>
                      <p className="text-sm font-medium text-dark-text-primary">
                        Show Onboarding
                      </p>
                      <p className="text-xs text-dark-text-muted mt-1">
                        Show the onboarding guide on the dashboard
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences.showOnboarding}
                      onChange={(e) => setPreferences({ ...preferences, showOnboarding: e.target.checked })}
                      className="form-checkbox"
                    />
                  </label>
                </div>

                <div className="flex justify-end">
                  <button onClick={handleSavePreferences} className="btn-primary">
                    Save Preferences
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
