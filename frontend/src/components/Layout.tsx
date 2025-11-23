import { ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  MapPinIcon,
  DocumentTextIcon,
  CogIcon,
  EnvelopeIcon as MailIcon,
  DocumentDuplicateIcon,
  BellIcon,
  Bars3Icon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  RocketLaunchIcon,
  VideoCameraIcon,
  Cog6ToothIcon,
  CpuChipIcon,
  ChevronDownIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'

interface LayoutProps {
  children: ReactNode
}

interface NavItem {
  name: string
  href: string
  icon: any
  badge?: number
}

interface NavSection {
  title: string
  items: NavItem[]
}

const navigation: NavSection[] = [
  {
    title: 'Core',
    items: [
      { name: 'Dashboard', href: '/', icon: HomeIcon },
      { name: 'Leads', href: '/leads', icon: DocumentTextIcon },
      { name: 'Scraper', href: '/scraper', icon: CogIcon },
      { name: 'Conversations', href: '/conversations', icon: ChatBubbleLeftRightIcon, badge: 0 },
    ]
  },
  {
    title: 'Automation',
    items: [
      { name: 'Campaigns', href: '/campaigns', icon: MailIcon },
      { name: 'Templates', href: '/templates', icon: DocumentDuplicateIcon },
      { name: 'Workflows', href: '/workflows', icon: Cog6ToothIcon },
      { name: 'Approvals', href: '/approvals', icon: BellIcon },
      { name: 'Demo Sites', href: '/demo-sites', icon: RocketLaunchIcon },
      { name: 'Videos', href: '/videos', icon: VideoCameraIcon },
    ]
  },
  {
    title: 'Management',
    items: [
      { name: 'Location Map', href: '/location-map', icon: MapPinIcon },
    ]
  },
  {
    title: 'Insights',
    items: [
      { name: 'AI-GYM', href: '/ai-gym', icon: CpuChipIcon },
    ]
  }
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    'Core': true,
    'Automation': true,
    'Management': true,
    'Insights': true
  })

  const toggleSection = (title: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [title]: !prev[title]
    }))
  }

  return (
    <div className="min-h-screen bg-dark-bg flex">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-screen w-64 bg-dark-surface border-r border-dark-border z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-dark-border">
            <h1 className="text-xl font-bold text-terminal-400 font-mono">
              FlipTech Pro
            </h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto py-4">
            {navigation.map((section) => (
              <div key={section.title} className="mb-2">
                <button
                  onClick={() => toggleSection(section.title)}
                  className="w-full flex items-center justify-between px-6 py-2 text-xs font-semibold text-dark-text-muted uppercase tracking-wider hover:text-dark-text-secondary transition-colors"
                >
                  <span>{section.title}</span>
                  {expandedSections[section.title] ? (
                    <ChevronDownIcon className="w-4 h-4" />
                  ) : (
                    <ChevronRightIcon className="w-4 h-4" />
                  )}
                </button>

                {expandedSections[section.title] && (
                  <div className="space-y-1 px-3">
                    {section.items.map((item) => {
                      const isActive = location.pathname === item.href
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                            isActive
                              ? 'bg-terminal-500/20 text-terminal-400 border border-terminal-500/50'
                              : 'text-dark-text-secondary hover:bg-dark-hover hover:text-dark-text-primary'
                          }`}
                        >
                          <item.icon className="w-5 h-5 flex-shrink-0" />
                          <span className="flex-1">{item.name}</span>
                          {item.badge !== undefined && item.badge > 0 && (
                            <span className="px-2 py-0.5 text-xs bg-[#FF3B30] text-white rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* Phase indicator */}
          <div className="p-6 border-t border-dark-border">
            <div className="text-xs text-terminal-400 bg-terminal-500/20 px-3 py-2 rounded-md border border-terminal-500/30 text-center">
              Phase 5
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 lg:ml-64">
        {/* Mobile header */}
        <header className="lg:hidden sticky top-0 z-30 bg-dark-surface border-b border-dark-border">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded-md text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <h1 className="text-lg font-bold text-terminal-400 font-mono">
              FlipTech Pro
            </h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </div>
        </header>

        {/* Page content */}
        <main className="py-6 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}