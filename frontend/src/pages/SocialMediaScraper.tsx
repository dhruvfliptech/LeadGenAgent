import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChatBubbleLeftRightIcon,
  VideoCameraIcon,
  PhotoIcon,
  UserGroupIcon,
  ArrowLeftIcon,
  HashtagIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type SocialPlatform = 'twitter' | 'reddit' | 'youtube' | 'instagram' | 'facebook' | 'discord' | null

export default function SocialMediaScraper() {
  const navigate = useNavigate()
  const [activePlatform, setActivePlatform] = useState<SocialPlatform>(null)

  // Twitter/X state
  const [twitterHashtags, setTwitterHashtags] = useState<string[]>([])
  const [twitterHashtagInput, setTwitterHashtagInput] = useState('')
  const [twitterUsername, setTwitterUsername] = useState('')
  const [twitterLimit, setTwitterLimit] = useState(100)

  // Reddit state
  const [redditSubreddits, setRedditSubreddits] = useState<string[]>([])
  const [redditSubredditInput, setRedditSubredditInput] = useState('')
  const [redditKeywords, setRedditKeywords] = useState('')
  const [redditTimeframe, setRedditTimeframe] = useState('week')
  const [redditLimit, setRedditLimit] = useState(100)

  // YouTube state
  const [youtubeKeywords, setYoutubeKeywords] = useState('')
  const [youtubeChannelUrl, setYoutubeChannelUrl] = useState('')
  const [youtubeLimit, setYoutubeLimit] = useState(50)

  // Instagram state
  const [instagramHashtags, setInstagramHashtags] = useState<string[]>([])
  const [instagramHashtagInput, setInstagramHashtagInput] = useState('')
  const [instagramUsername, setInstagramUsername] = useState('')
  const [instagramLimit, setInstagramLimit] = useState(50)

  // Facebook state
  const [facebookGroupUrls, setFacebookGroupUrls] = useState<string[]>([])
  const [facebookGroupInput, setFacebookGroupInput] = useState('')
  const [facebookKeywords, setFacebookKeywords] = useState('')
  const [facebookLimit, setFacebookLimit] = useState(50)

  // Discord state
  const [discordServerIds, setDiscordServerIds] = useState<string[]>([])
  const [discordServerInput, setDiscordServerInput] = useState('')
  const [discordChannelIds, setDiscordChannelIds] = useState<string[]>([])
  const [discordChannelInput, setDiscordChannelInput] = useState('')
  const [discordLimit, setDiscordLimit] = useState(100)

  const addTag = (value: string, setter: (tags: string[]) => void, current: string[]) => {
    const trimmed = value.trim()
    if (trimmed && !current.includes(trimmed)) {
      setter([...current, trimmed])
    }
  }

  const removeTag = (index: number, setter: (tags: string[]) => void, current: string[]) => {
    setter(current.filter((_, i) => i !== index))
  }

  const handleSubmit = (platform: string, config: any) => {
    console.log(`${platform} scraping config:`, config)
    toast.success(`${platform} scraping job created!`)
    setTimeout(() => {
      navigate('/scraper/jobs')
    }, 1500)
  }

  const platforms = [
    {
      id: 'twitter',
      name: 'Twitter / X',
      icon: ChatBubbleLeftRightIcon,
      color: '#1DA1F2',
      description: 'Scrape tweets by hashtag, user, or keyword',
      features: ['Hashtag tracking', 'User timeline', 'Engagement metrics']
    },
    {
      id: 'reddit',
      name: 'Reddit',
      icon: ChatBubbleLeftRightIcon,
      color: '#FF4500',
      description: 'Find posts and comments from subreddits',
      features: ['Subreddit scraping', 'Keyword search', 'Top/Hot/New sorting']
    },
    {
      id: 'youtube',
      name: 'YouTube',
      icon: VideoCameraIcon,
      color: '#FF0000',
      description: 'Extract video data, comments, and channel info',
      features: ['Video search', 'Channel scraping', 'Comment extraction']
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: PhotoIcon,
      color: '#E1306C',
      description: 'Collect posts, stories, and profile data',
      features: ['Hashtag posts', 'User profiles', 'Story viewing']
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: UserGroupIcon,
      color: '#1877F2',
      description: 'Scrape public posts from groups and pages',
      features: ['Group posts', 'Page data', 'Public profiles']
    },
    {
      id: 'discord',
      name: 'Discord',
      icon: ChatBubbleLeftRightIcon,
      color: '#5865F2',
      description: 'Monitor server channels and messages',
      features: ['Server monitoring', 'Channel history', 'User activity']
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/scraper')}
          className="p-2 rounded-md text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-dark-text-primary">Social Media Scraper</h1>
          <p className="mt-1 text-sm text-dark-text-secondary">
            Find leads and gather intelligence from social media platforms
          </p>
        </div>
      </div>

      {/* Platform Selection */}
      {!activePlatform && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {platforms.map((platform) => (
            <button
              key={platform.id}
              onClick={() => setActivePlatform(platform.id as SocialPlatform)}
              className="card-terminal p-6 text-left transition-all hover:ring-2 hover:ring-terminal-500"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg" style={{ backgroundColor: `${platform.color}20`, borderColor: `${platform.color}40`, borderWidth: '1px' }}>
                  <platform.icon className="w-8 h-8" style={{ color: platform.color }} />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-dark-text-primary mb-1">
                    {platform.name}
                  </h3>
                  <p className="text-sm text-dark-text-secondary mb-3">
                    {platform.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {platform.features.map((feature) => (
                      <span key={feature} className="text-xs px-2 py-1 bg-terminal-500/10 text-terminal-400 rounded">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Twitter/X Configuration */}
      {activePlatform === 'twitter' && (
        <div className="card-terminal p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-dark-border">
            <div className="flex items-center gap-3">
              <ChatBubbleLeftRightIcon className="w-6 h-6" style={{ color: '#1DA1F2' }} />
              <h3 className="text-xl font-semibold text-dark-text-primary">Twitter / X Scraper</h3>
            </div>
            <button onClick={() => setActivePlatform(null)} className="btn-secondary text-sm">
              Back
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="form-label">Track Hashtags</label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="form-input flex-1"
                    value={twitterHashtagInput}
                    onChange={e => setTwitterHashtagInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(twitterHashtagInput, setTwitterHashtags, twitterHashtags)
                        setTwitterHashtagInput('')
                      }
                    }}
                    placeholder="#marketing #business #tech"
                  />
                  <button
                    onClick={() => {
                      addTag(twitterHashtagInput, setTwitterHashtags, twitterHashtags)
                      setTwitterHashtagInput('')
                    }}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
                {twitterHashtags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {twitterHashtags.map((tag, idx) => (
                      <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 bg-terminal-500/10 text-terminal-400 rounded-md text-sm">
                        {tag}
                        <button onClick={() => removeTag(idx, setTwitterHashtags, twitterHashtags)} className="hover:text-terminal-300">×</button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="form-label">Or Track User Timeline</label>
              <input
                type="text"
                className="form-input"
                value={twitterUsername}
                onChange={e => setTwitterUsername(e.target.value)}
                placeholder="@username"
              />
            </div>

            <div>
              <label className="form-label">Max Tweets</label>
              <input
                type="number"
                min={10}
                max={1000}
                className="form-input"
                value={twitterLimit}
                onChange={e => setTwitterLimit(parseInt(e.target.value || '100', 10))}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-dark-border">
            <button
              onClick={() => handleSubmit('Twitter', { hashtags: twitterHashtags, username: twitterUsername, limit: twitterLimit })}
              disabled={twitterHashtags.length === 0 && !twitterUsername}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Scraping
            </button>
          </div>
        </div>
      )}

      {/* Reddit Configuration */}
      {activePlatform === 'reddit' && (
        <div className="card-terminal p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-dark-border">
            <div className="flex items-center gap-3">
              <ChatBubbleLeftRightIcon className="w-6 h-6" style={{ color: '#FF4500' }} />
              <h3 className="text-xl font-semibold text-dark-text-primary">Reddit Scraper</h3>
            </div>
            <button onClick={() => setActivePlatform(null)} className="btn-secondary text-sm">
              Back
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="form-label">Subreddits</label>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    className="form-input flex-1"
                    value={redditSubredditInput}
                    onChange={e => setRedditSubredditInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addTag(redditSubredditInput, setRedditSubreddits, redditSubreddits)
                        setRedditSubredditInput('')
                      }
                    }}
                    placeholder="entrepreneur, marketing, business"
                  />
                  <button
                    onClick={() => {
                      addTag(redditSubredditInput, setRedditSubreddits, redditSubreddits)
                      setRedditSubredditInput('')
                    }}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
                {redditSubreddits.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {redditSubreddits.map((sub, idx) => (
                      <span key={idx} className="inline-flex items-center gap-1 px-3 py-1 bg-terminal-500/10 text-terminal-400 rounded-md text-sm">
                        r/{sub}
                        <button onClick={() => removeTag(idx, setRedditSubreddits, redditSubreddits)} className="hover:text-terminal-300">×</button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Keywords (optional)</label>
                <input
                  type="text"
                  className="form-input"
                  value={redditKeywords}
                  onChange={e => setRedditKeywords(e.target.value)}
                  placeholder="marketing, sales, leads"
                />
              </div>

              <div>
                <label className="form-label">Timeframe</label>
                <select className="form-input" value={redditTimeframe} onChange={e => setRedditTimeframe(e.target.value)}>
                  <option value="hour">Past Hour</option>
                  <option value="day">Past 24 Hours</option>
                  <option value="week">Past Week</option>
                  <option value="month">Past Month</option>
                  <option value="year">Past Year</option>
                  <option value="all">All Time</option>
                </select>
              </div>
            </div>

            <div>
              <label className="form-label">Max Posts</label>
              <input
                type="number"
                min={10}
                max={1000}
                className="form-input"
                value={redditLimit}
                onChange={e => setRedditLimit(parseInt(e.target.value || '100', 10))}
              />
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-dark-border">
            <button
              onClick={() => handleSubmit('Reddit', { subreddits: redditSubreddits, keywords: redditKeywords, timeframe: redditTimeframe, limit: redditLimit })}
              disabled={redditSubreddits.length === 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Scraping
            </button>
          </div>
        </div>
      )}

      {/* Integration Notice */}
      <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-yellow-400 mb-2">
          Social Media API Integration
        </h4>
        <p className="text-sm text-dark-text-secondary">
          Social media scraping requires API access and proper authentication. Some platforms have strict rate limits and terms of service.
          Make sure you comply with each platform's data usage policies and have the necessary API keys configured.
        </p>
      </div>
    </div>
  )
}
