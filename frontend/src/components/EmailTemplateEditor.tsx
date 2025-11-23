import { useState } from 'react'

interface EmailTemplateEditorProps {
  subject: string
  bodyHtml: string
  bodyText: string
  onSubjectChange: (subject: string) => void
  onBodyHtmlChange: (html: string) => void
  onBodyTextChange: (text: string) => void
}

const AVAILABLE_VARIABLES = [
  { key: '{{name}}', label: 'Contact Name', example: 'John Smith' },
  { key: '{{company_name}}', label: 'Company Name', example: 'Acme Corp' },
  { key: '{{email}}', label: 'Email Address', example: 'john@acme.com' },
  { key: '{{phone}}', label: 'Phone Number', example: '(555) 123-4567' },
  { key: '{{title}}', label: 'Listing Title', example: 'Web Design Services' },
  { key: '{{demo_url}}', label: 'Demo Site URL', example: 'https://demo.example.com' },
  { key: '{{video_url}}', label: 'Video URL', example: 'https://video.example.com' },
  { key: '{{sender_name}}', label: 'Your Name', example: 'Sarah Johnson' },
  { key: '{{sender_email}}', label: 'Your Email', example: 'sarah@yourcompany.com' },
]

export default function EmailTemplateEditor({
  subject,
  bodyHtml,
  bodyText,
  onSubjectChange,
  onBodyHtmlChange,
  onBodyTextChange,
}: EmailTemplateEditorProps) {
  const [activeTab, setActiveTab] = useState<'html' | 'text'>('html')
  const [cursorPosition, setCursorPosition] = useState(0)

  const insertVariable = (variable: string) => {
    if (activeTab === 'html') {
      const newBody = bodyHtml.slice(0, cursorPosition) + variable + bodyHtml.slice(cursorPosition)
      onBodyHtmlChange(newBody)
    } else {
      const newBody = bodyText.slice(0, cursorPosition) + variable + bodyText.slice(cursorPosition)
      onBodyTextChange(newBody)
    }
  }

  const handleTextareaClick = (e: React.MouseEvent<HTMLTextAreaElement>) => {
    setCursorPosition(e.currentTarget.selectionStart)
  }

  const handleTextareaKeyUp = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    setCursorPosition(e.currentTarget.selectionStart)
  }

  return (
    <div className="space-y-4">
      {/* Subject Line */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Subject Line
        </label>
        <input
          type="text"
          value={subject}
          onChange={(e) => onSubjectChange(e.target.value)}
          placeholder="Enter email subject..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Variable Shortcuts */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Insert Variable
        </label>
        <div className="flex flex-wrap gap-2">
          {AVAILABLE_VARIABLES.map((variable) => (
            <button
              key={variable.key}
              type="button"
              onClick={() => insertVariable(variable.key)}
              className="px-2.5 py-1 text-xs font-mono bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border border-gray-300 transition-colors"
              title={`${variable.label} - Example: ${variable.example}`}
            >
              {variable.key}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab('html')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'html'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              HTML Version
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('text')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'text'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Plain Text Version
            </button>
          </nav>
        </div>

        {/* HTML Editor */}
        {activeTab === 'html' && (
          <div className="mt-4">
            <textarea
              value={bodyHtml}
              onChange={(e) => onBodyHtmlChange(e.target.value)}
              onClick={handleTextareaClick}
              onKeyUp={handleTextareaKeyUp}
              placeholder="<p>Hi {{name}},</p>&#10;&#10;<p>Your email content here...</p>"
              rows={16}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">
              Write HTML for rich email formatting. Use basic tags like &lt;p&gt;, &lt;strong&gt;, &lt;ul&gt;, &lt;li&gt;, &lt;a&gt;
            </p>
          </div>
        )}

        {/* Plain Text Editor */}
        {activeTab === 'text' && (
          <div className="mt-4">
            <textarea
              value={bodyText}
              onChange={(e) => onBodyTextChange(e.target.value)}
              onClick={handleTextareaClick}
              onKeyUp={handleTextareaKeyUp}
              placeholder="Hi {{name}},&#10;&#10;Your email content here..."
              rows={16}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">
              Plain text version for email clients that don't support HTML
            </p>
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">Tips for Effective Emails</h4>
        <ul className="text-xs text-blue-700 space-y-1 list-disc list-inside">
          <li>Personalize with variables like {'{{name}}'} and {'{{company_name}}'}</li>
          <li>Keep subject lines under 50 characters</li>
          <li>Include a clear call-to-action</li>
          <li>Test both HTML and plain text versions</li>
          <li>Avoid spam trigger words like "free", "urgent", "act now"</li>
        </ul>
      </div>
    </div>
  )
}
