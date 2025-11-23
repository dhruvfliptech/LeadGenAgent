import { useState } from 'react'
import {
  ClipboardDocumentIcon,
  ClipboardDocumentCheckIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'

interface CodeViewerProps {
  filename: string
  content: string
}

// Simple syntax highlighting for common languages
function highlightCode(code: string, language: string): string {
  // This is a basic highlighter. In production, use a library like Prism.js or highlight.js
  const keywords = {
    javascript: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'export', 'from', 'default', 'class', 'extends', 'async', 'await', 'try', 'catch'],
    typescript: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'import', 'export', 'from', 'default', 'class', 'extends', 'async', 'await', 'type', 'interface', 'enum'],
    jsx: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'import', 'export', 'from', 'default'],
    html: ['<!DOCTYPE', 'html', 'head', 'body', 'div', 'span', 'a', 'p', 'h1', 'h2', 'h3', 'script', 'style', 'link', 'meta'],
    css: ['color', 'background', 'margin', 'padding', 'display', 'flex', 'grid', 'width', 'height', 'font'],
  }

  let highlighted = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Highlight strings
  highlighted = highlighted.replace(
    /(['"`])((?:\\.|(?!\1)[^\\])*)\1/g,
    '<span class="text-green-400">$&</span>'
  )

  // Highlight comments
  highlighted = highlighted.replace(
    /(\/\/.*$|\/\*[\s\S]*?\*\/)/gm,
    '<span class="text-gray-500 italic">$&</span>'
  )

  // Highlight keywords for the language
  const keywordList = keywords[language as keyof typeof keywords] || []
  keywordList.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, 'g')
    highlighted = highlighted.replace(regex, `<span class="text-purple-400 font-semibold">${keyword}</span>`)
  })

  // Highlight numbers
  highlighted = highlighted.replace(
    /\b(\d+\.?\d*)\b/g,
    '<span class="text-blue-400">$&</span>'
  )

  return highlighted
}

function getLanguageFromFilename(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const languageMap: Record<string, string> = {
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'typescript',
    json: 'json',
    html: 'html',
    css: 'css',
    scss: 'scss',
    md: 'markdown',
    py: 'python',
    yml: 'yaml',
    yaml: 'yaml'
  }
  return languageMap[ext || ''] || 'text'
}

export default function CodeViewer({ filename, content }: CodeViewerProps) {
  const [copied, setCopied] = useState(false)

  const language = getLanguageFromFilename(filename)
  const lines = content.split('\n')

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-border">
        <div>
          <h3 className="font-semibold text-dark-text-primary">{filename}</h3>
          <div className="text-xs text-dark-text-muted mt-1">
            {language.toUpperCase()} • {lines.length} lines • {(content.length / 1024).toFixed(2)}KB
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="btn-secondary text-sm flex items-center gap-2"
            title="Copy to clipboard"
          >
            {copied ? (
              <>
                <ClipboardDocumentCheckIcon className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <ClipboardDocumentIcon className="w-4 h-4" />
                Copy
              </>
            )}
          </button>
          <button
            onClick={handleDownload}
            className="btn-secondary text-sm flex items-center gap-2"
            title="Download file"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            Download
          </button>
        </div>
      </div>

      {/* Code Content */}
      <div className="flex-1 overflow-auto bg-[#1a1b26] p-4">
        <pre className="text-sm font-mono">
          <code>
            {lines.map((line, index) => (
              <div key={index} className="flex">
                <span className="inline-block w-12 text-right pr-4 text-gray-600 select-none">
                  {index + 1}
                </span>
                <span
                  className="flex-1 text-gray-200"
                  dangerouslySetInnerHTML={{
                    __html: highlightCode(line, language) || '&nbsp;'
                  }}
                />
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  )
}
