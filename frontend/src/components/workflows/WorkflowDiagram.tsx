import { MockWorkflow } from '@/mocks/workflows.mock'
import { ArrowRightIcon } from '@heroicons/react/24/outline'

interface WorkflowDiagramProps {
  workflow: MockWorkflow
}

// Node type styling
const nodeTypeStyles: Record<string, string> = {
  'n8n-nodes-base.webhook': 'bg-blue-50 border-blue-300 text-blue-900',
  'n8n-nodes-base.httpRequest': 'bg-purple-50 border-purple-300 text-purple-900',
  'n8n-nodes-base.merge': 'bg-green-50 border-green-300 text-green-900',
  'n8n-nodes-base.if': 'bg-yellow-50 border-yellow-300 text-yellow-900',
  'n8n-nodes-base.cron': 'bg-orange-50 border-orange-300 text-orange-900',
  'n8n-nodes-base.manualTrigger': 'bg-gray-50 border-gray-300 text-gray-900',
  'n8n-nodes-base.slack': 'bg-pink-50 border-pink-300 text-pink-900'
}

export default function WorkflowDiagram({ workflow }: WorkflowDiagramProps) {
  // Sort nodes by position (left to right, top to bottom)
  const sortedNodes = [...workflow.nodes].sort((a, b) => {
    if (a.position[0] !== b.position[0]) {
      return a.position[0] - b.position[0]
    }
    return a.position[1] - b.position[1]
  })

  // Group nodes by x-position (column)
  const columns: typeof sortedNodes[] = []
  let currentX = -Infinity
  let currentColumn: typeof sortedNodes = []

  sortedNodes.forEach(node => {
    if (node.position[0] !== currentX) {
      if (currentColumn.length > 0) {
        columns.push(currentColumn)
      }
      currentColumn = [node]
      currentX = node.position[0]
    } else {
      currentColumn.push(node)
    }
  })
  if (currentColumn.length > 0) {
    columns.push(currentColumn)
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-flex items-start gap-4 p-6 min-w-full">
        {columns.map((column, columnIdx) => (
          <div key={columnIdx} className="flex items-center gap-4">
            <div className="space-y-4">
              {column.map((node) => {
                const style = nodeTypeStyles[node.type] || 'bg-gray-50 border-gray-300 text-gray-900'
                const nodeType = node.type.split('.').pop() || node.type

                return (
                  <div
                    key={node.id}
                    className={`px-4 py-3 rounded-lg border-2 min-w-[200px] ${style}`}
                  >
                    <div className="text-xs font-medium uppercase opacity-60 mb-1">
                      {nodeType}
                    </div>
                    <div className="font-semibold text-sm">
                      {node.name}
                    </div>
                    {Object.keys(node.parameters).length > 0 && (
                      <div className="mt-2 text-xs opacity-75">
                        {Object.entries(node.parameters).slice(0, 2).map(([key, value]) => (
                          <div key={key} className="truncate">
                            <span className="font-medium">{key}:</span>{' '}
                            {typeof value === 'string' ? value : JSON.stringify(value).slice(0, 30)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {columnIdx < columns.length - 1 && (
              <div className="flex-shrink-0">
                <ArrowRightIcon className="w-6 h-6 text-gray-400" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Connections summary */}
      <div className="mt-6 px-6 text-sm text-gray-600">
        <div className="font-medium mb-2">Connections:</div>
        <ul className="space-y-1">
          {workflow.connections.map((conn, idx) => {
            const sourceNode = workflow.nodes.find(n => n.id === conn.source)
            const targetNode = workflow.nodes.find(n => n.id === conn.target)
            return (
              <li key={idx} className="flex items-center gap-2">
                <span className="text-gray-900">{sourceNode?.name || conn.source}</span>
                <ArrowRightIcon className="w-3 h-3 text-gray-400" />
                <span className="text-gray-900">{targetNode?.name || conn.target}</span>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
