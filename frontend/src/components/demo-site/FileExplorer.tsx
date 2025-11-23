import { useState } from 'react'
import {
  FolderIcon,
  FolderOpenIcon,
  DocumentIcon,
  ChevronRightIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'

interface FileExplorerProps {
  files: Record<string, string>
  selectedFile: string | null
  onFileSelect: (filename: string) => void
}

interface FileNode {
  name: string
  path: string
  isDirectory: boolean
  children: FileNode[]
  content?: string
}

// Build tree structure from flat file paths
function buildFileTree(files: Record<string, string>): FileNode {
  const root: FileNode = {
    name: 'root',
    path: '',
    isDirectory: true,
    children: []
  }

  Object.entries(files).forEach(([path, content]) => {
    const parts = path.split('/')
    let currentNode = root

    parts.forEach((part, index) => {
      const isLastPart = index === parts.length - 1
      const currentPath = parts.slice(0, index + 1).join('/')

      let childNode = currentNode.children.find(child => child.name === part)

      if (!childNode) {
        childNode = {
          name: part,
          path: currentPath,
          isDirectory: !isLastPart,
          children: [],
          content: isLastPart ? content : undefined
        }
        currentNode.children.push(childNode)
      }

      currentNode = childNode
    })
  })

  // Sort: directories first, then files, alphabetically
  const sortNodes = (nodes: FileNode[]) => {
    nodes.sort((a, b) => {
      if (a.isDirectory && !b.isDirectory) return -1
      if (!a.isDirectory && b.isDirectory) return 1
      return a.name.localeCompare(b.name)
    })
    nodes.forEach(node => {
      if (node.isDirectory) {
        sortNodes(node.children)
      }
    })
  }

  sortNodes(root.children)

  return root
}

// Get file icon based on extension
function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    js: '📜',
    jsx: '⚛️',
    ts: '📘',
    tsx: '⚛️',
    json: '📋',
    html: '🌐',
    css: '🎨',
    scss: '🎨',
    md: '📝',
    txt: '📄',
    yml: '⚙️',
    yaml: '⚙️',
    env: '🔐',
    gitignore: '🚫'
  }
  return icons[ext || ''] || '📄'
}

interface FileTreeNodeProps {
  node: FileNode
  level: number
  selectedFile: string | null
  expandedFolders: Set<string>
  onFileSelect: (path: string) => void
  onToggleFolder: (path: string) => void
}

function FileTreeNode({
  node,
  level,
  selectedFile,
  expandedFolders,
  onFileSelect,
  onToggleFolder
}: FileTreeNodeProps) {
  const isExpanded = expandedFolders.has(node.path)
  const isSelected = selectedFile === node.path

  return (
    <div>
      <div
        onClick={() => node.isDirectory ? onToggleFolder(node.path) : onFileSelect(node.path)}
        className={`flex items-center gap-2 px-2 py-1.5 cursor-pointer rounded transition-colors ${
          isSelected
            ? 'bg-terminal-500/20 text-terminal-400'
            : 'hover:bg-dark-border/50 text-dark-text-secondary'
        }`}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
      >
        {node.isDirectory ? (
          <>
            {isExpanded ? (
              <ChevronDownIcon className="w-4 h-4 flex-shrink-0" />
            ) : (
              <ChevronRightIcon className="w-4 h-4 flex-shrink-0" />
            )}
            {isExpanded ? (
              <FolderOpenIcon className="w-4 h-4 flex-shrink-0 text-yellow-500" />
            ) : (
              <FolderIcon className="w-4 h-4 flex-shrink-0 text-yellow-500" />
            )}
          </>
        ) : (
          <>
            <span className="w-4 flex-shrink-0" />
            <span className="text-base">{getFileIcon(node.name)}</span>
          </>
        )}
        <span className="text-sm truncate flex-1">{node.name}</span>
        {!node.isDirectory && node.content && (
          <span className="text-xs text-dark-text-muted">
            {(node.content.length / 1024).toFixed(1)}KB
          </span>
        )}
      </div>

      {node.isDirectory && isExpanded && (
        <div>
          {node.children.map((child, index) => (
            <FileTreeNode
              key={`${child.path}-${index}`}
              node={child}
              level={level + 1}
              selectedFile={selectedFile}
              expandedFolders={expandedFolders}
              onFileSelect={onFileSelect}
              onToggleFolder={onToggleFolder}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FileExplorer({ files, selectedFile, onFileSelect }: FileExplorerProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const fileTree = buildFileTree(files)
  const fileCount = Object.keys(files).length
  const totalSize = Object.values(files).reduce((sum, content) => sum + content.length, 0)

  const handleToggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFolders(newExpanded)
  }

  return (
    <div className="card h-full">
      <div className="p-4 border-b border-dark-border">
        <h3 className="font-semibold text-dark-text-primary mb-2">File Explorer</h3>
        <div className="text-xs text-dark-text-muted">
          {fileCount} files • {(totalSize / 1024).toFixed(1)}KB total
        </div>
      </div>
      <div className="p-2 overflow-y-auto max-h-[calc(100vh-300px)]">
        {fileTree.children.map((node, index) => (
          <FileTreeNode
            key={`${node.path}-${index}`}
            node={node}
            level={0}
            selectedFile={selectedFile}
            expandedFolders={expandedFolders}
            onFileSelect={onFileSelect}
            onToggleFolder={handleToggleFolder}
          />
        ))}
      </div>
    </div>
  )
}
