interface TemplatePreviewProps {
  subject: string
  bodyHtml: string
  sampleData?: Record<string, string>
}

const DEFAULT_SAMPLE_DATA = {
  name: 'John Smith',
  company_name: 'Acme Corporation',
  email: 'john@acme.com',
  phone: '(555) 123-4567',
  title: 'Web Design Services',
  demo_url: 'https://demo.example.com/acme-corp',
  video_url: 'https://video.example.com/acme-demo',
  sender_name: 'Sarah Johnson',
  sender_email: 'sarah@yourcompany.com',
}

export default function TemplatePreview({
  subject,
  bodyHtml,
  sampleData = DEFAULT_SAMPLE_DATA,
}: TemplatePreviewProps) {
  // Replace variables with sample data
  const replaceVariables = (text: string) => {
    let replaced = text
    Object.entries(sampleData).forEach(([key, value]) => {
      const regex = new RegExp(`{{${key}}}`, 'g')
      replaced = replaced.replace(regex, value)
    })
    return replaced
  }

  const previewSubject = replaceVariables(subject)
  const previewBody = replaceVariables(bodyHtml)

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
      {/* Email Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-500">PREVIEW</span>
          <span className="text-xs text-gray-400">Sample data shown</span>
        </div>
        <div className="space-y-2">
          <div className="flex items-start">
            <span className="text-xs font-medium text-gray-500 w-16">From:</span>
            <span className="text-sm text-gray-700">
              {sampleData.sender_name} &lt;{sampleData.sender_email}&gt;
            </span>
          </div>
          <div className="flex items-start">
            <span className="text-xs font-medium text-gray-500 w-16">To:</span>
            <span className="text-sm text-gray-700">
              {sampleData.name} &lt;{sampleData.email}&gt;
            </span>
          </div>
          <div className="flex items-start">
            <span className="text-xs font-medium text-gray-500 w-16">Subject:</span>
            <span className="text-sm font-medium text-gray-900">
              {previewSubject || '(No subject)'}
            </span>
          </div>
        </div>
      </div>

      {/* Email Body */}
      <div className="px-6 py-4 bg-white">
        {previewBody ? (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: previewBody }}
          />
        ) : (
          <p className="text-gray-400 text-sm italic">No email content yet...</p>
        )}
      </div>

      {/* Footer Note */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2">
        <p className="text-xs text-gray-500">
          This is a preview with sample data. Actual emails will use real lead information.
        </p>
      </div>
    </div>
  )
}
