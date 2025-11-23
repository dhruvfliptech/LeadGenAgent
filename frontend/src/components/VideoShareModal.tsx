// Modal for sharing videos with multiple options

import { useState } from 'react'
import { Dialog } from '@headlessui/react'
import {
  XMarkIcon,
  LinkIcon,
  CodeBracketIcon,
  EnvelopeIcon,
  QrCodeIcon,
  CheckIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline'
import { useMutation, useQuery } from '@tanstack/react-query'
import { videosApi } from '@/services/videosApi'
import { HostedVideo } from '@/types/video'
import toast from 'react-hot-toast'

interface VideoShareModalProps {
  video: HostedVideo | null
  isOpen: boolean
  onClose: () => void
}

export default function VideoShareModal({ video, isOpen, onClose }: VideoShareModalProps) {
  const [activeTab, setActiveTab] = useState<'link' | 'embed' | 'email' | 'qr'>('link')
  const [copiedLink, setCopiedLink] = useState(false)
  const [copiedEmbed, setCopiedEmbed] = useState(false)
  const [emailMessage, setEmailMessage] = useState('')
  // @ts-ignore - selectedLeadId used in conditional logic
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null)

  // Get embed code
  const { data: embedData } = useQuery({
    queryKey: ['video-embed', video?.id],
    queryFn: () => video ? videosApi.getEmbedCode(video.id).then(res => res.data) : null,
    enabled: isOpen && !!video
  })

  // Get QR code
  const { data: qrData } = useQuery({
    queryKey: ['video-qr', video?.id],
    queryFn: () => video ? videosApi.getQRCode(video.id).then(res => res.data) : null,
    enabled: isOpen && !!video && activeTab === 'qr'
  })

  // Email mutation
  const emailMutation = useMutation({
    mutationFn: (data: { video_id: number; lead_id: number; message?: string }) =>
      videosApi.emailToLead(data.video_id, { lead_id: data.lead_id, message: data.message }),
    onSuccess: () => {
      toast.success('Email sent successfully!')
      setEmailMessage('')
      setSelectedLeadId(null)
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to send email')
    }
  })

  const copyToClipboard = async (text: string, type: 'link' | 'embed') => {
    try {
      await navigator.clipboard.writeText(text)
      if (type === 'link') {
        setCopiedLink(true)
        setTimeout(() => setCopiedLink(false), 2000)
      } else {
        setCopiedEmbed(true)
        setTimeout(() => setCopiedEmbed(false), 2000)
      }
      toast.success('Copied to clipboard!')
    } catch (err) {
      toast.error('Failed to copy')
    }
  }

  const handleEmailSend = () => {
    if (!video || !video.lead_id) {
      toast.error('No lead associated with this video')
      return
    }

    emailMutation.mutate({
      video_id: video.id,
      lead_id: video.lead_id,
      message: emailMessage || undefined
    })
  }

  if (!video) return null

  const tabs = [
    { id: 'link' as const, label: 'Share Link', icon: LinkIcon },
    { id: 'embed' as const, label: 'Embed Code', icon: CodeBracketIcon },
    { id: 'email' as const, label: 'Email Lead', icon: EnvelopeIcon },
    { id: 'qr' as const, label: 'QR Code', icon: QrCodeIcon }
  ]

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="mx-auto max-w-2xl w-full bg-dark-surface rounded-xl shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dark-border">
            <div>
              <Dialog.Title className="text-xl font-bold text-dark-text-primary">
                Share Video
              </Dialog.Title>
              <p className="text-sm text-dark-text-secondary mt-1 truncate">
                {video.title}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-dark-text-secondary hover:text-dark-text-primary"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-dark-border">
            <div className="flex">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                      activeTab === tab.id
                        ? 'border-terminal-500 text-terminal-400 bg-terminal-500/10'
                        : 'border-transparent text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-border/50'
                    }`}
                  >
                    <Icon className="w-5 h-5 mx-auto mb-1" />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {activeTab === 'link' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dark-text-primary mb-2">
                    Shareable Link
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={video.share_url}
                      readOnly
                      className="form-input flex-1 font-mono text-sm"
                    />
                    <button
                      onClick={() => copyToClipboard(video.share_url, 'link')}
                      className="btn-primary flex items-center gap-2 whitespace-nowrap"
                    >
                      {copiedLink ? (
                        <>
                          <CheckIcon className="w-5 h-5" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <ClipboardDocumentIcon className="w-5 h-5" />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <h4 className="text-sm font-semibold text-blue-400 mb-2">
                    Privacy: {video.privacy.charAt(0).toUpperCase() + video.privacy.slice(1)}
                  </h4>
                  <p className="text-sm text-dark-text-secondary">
                    {video.privacy === 'public' && 'Anyone with the link can view this video and it may appear in search results.'}
                    {video.privacy === 'unlisted' && 'Anyone with the link can view this video, but it will not appear in search results.'}
                    {video.privacy === 'private' && 'Only you can view this video.'}
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-3 pt-2">
                  <a
                    href={`https://twitter.com/intent/tweet?url=${encodeURIComponent(video.share_url)}&text=${encodeURIComponent(video.title)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary text-center"
                  >
                    Twitter
                  </a>
                  <a
                    href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(video.share_url)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary text-center"
                  >
                    LinkedIn
                  </a>
                  <a
                    href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(video.share_url)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary text-center"
                  >
                    Facebook
                  </a>
                </div>
              </div>
            )}

            {activeTab === 'embed' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-dark-text-primary mb-2">
                    Embed Code
                  </label>
                  <div className="relative">
                    <pre className="form-input font-mono text-xs overflow-x-auto whitespace-pre-wrap break-all p-4 bg-dark-bg">
                      {embedData?.embed_code || video.embed_url}
                    </pre>
                    <button
                      onClick={() => copyToClipboard(embedData?.embed_code || video.embed_url, 'embed')}
                      className="absolute top-2 right-2 p-2 bg-dark-surface hover:bg-dark-border rounded transition-colors"
                    >
                      {copiedEmbed ? (
                        <CheckIcon className="w-4 h-4 text-terminal-400" />
                      ) : (
                        <ClipboardDocumentIcon className="w-4 h-4 text-dark-text-secondary" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="p-4 bg-terminal-500/10 border border-terminal-500/30 rounded-lg">
                  <h4 className="text-sm font-semibold text-terminal-400 mb-2">
                    Embedding Instructions
                  </h4>
                  <ol className="text-sm text-dark-text-secondary space-y-1 list-decimal list-inside">
                    <li>Copy the embed code above</li>
                    <li>Paste it into your website's HTML</li>
                    <li>The video will be responsive and fit the container</li>
                  </ol>
                </div>

                {/* Preview */}
                <div>
                  <label className="block text-sm font-medium text-dark-text-primary mb-2">
                    Preview
                  </label>
                  <div className="aspect-video bg-dark-bg rounded-lg overflow-hidden">
                    {video.hosting_provider === 'loom' ? (
                      <iframe
                        src={video.embed_url}
                        width="100%"
                        height="100%"
                        frameBorder="0"
                        allowFullScreen
                        title={video.title}
                      />
                    ) : (
                      <video
                        src={video.share_url}
                        controls
                        className="w-full h-full"
                        poster={video.thumbnail_url}
                      />
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'email' && (
              <div className="space-y-4">
                {video.lead ? (
                  <>
                    <div className="p-4 bg-dark-border rounded-lg">
                      <h4 className="text-sm font-semibold text-dark-text-primary mb-1">
                        Sending to:
                      </h4>
                      <p className="text-dark-text-secondary">
                        {video.lead.business_name}
                      </p>
                      {video.lead.email && (
                        <p className="text-sm text-dark-text-muted">{video.lead.email}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-dark-text-primary mb-2">
                        Message (Optional)
                      </label>
                      <textarea
                        value={emailMessage}
                        onChange={(e) => setEmailMessage(e.target.value)}
                        rows={6}
                        placeholder="Add a personal message to include with the video..."
                        className="form-input w-full"
                      />
                    </div>

                    <button
                      onClick={handleEmailSend}
                      disabled={emailMutation.isPending}
                      className="btn-primary w-full disabled:opacity-50"
                    >
                      {emailMutation.isPending ? 'Sending...' : 'Send Email'}
                    </button>
                  </>
                ) : (
                  <div className="text-center py-12">
                    <EnvelopeIcon className="w-12 h-12 mx-auto text-dark-text-muted mb-3" />
                    <p className="text-dark-text-secondary">
                      No lead associated with this video
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'qr' && (
              <div className="space-y-4">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-dark-text-primary mb-2">
                    Scan to View Video
                  </h3>
                  <p className="text-sm text-dark-text-secondary mb-6">
                    Share this QR code to allow mobile users to quickly access the video
                  </p>
                </div>

                <div className="flex justify-center">
                  {qrData?.qr_code_data_url ? (
                    <img
                      src={qrData.qr_code_data_url}
                      alt="QR Code"
                      className="w-64 h-64 border-4 border-dark-border rounded-lg p-4 bg-white"
                    />
                  ) : (
                    <div className="w-64 h-64 border-4 border-dark-border rounded-lg flex items-center justify-center bg-dark-bg">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terminal-500" />
                    </div>
                  )}
                </div>

                {qrData?.qr_code_data_url && (
                  <div className="flex justify-center gap-3">
                    <button
                      onClick={() => {
                        const link = document.createElement('a')
                        link.download = `${video.title}-qr.png`
                        link.href = qrData.qr_code_data_url
                        link.click()
                      }}
                      className="btn-primary"
                    >
                      Download QR Code
                    </button>
                    <button
                      onClick={() => copyToClipboard(video.share_url, 'link')}
                      className="btn-secondary"
                    >
                      Copy Link
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end p-6 border-t border-dark-border">
            <button onClick={onClose} className="btn-secondary">
              Close
            </button>
          </div>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}
