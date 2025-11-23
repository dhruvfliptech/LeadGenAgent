import { useEffect, useMemo, useState } from 'react'
// API URL fetched directly; no client import needed here

type Node = {
  type: 'group' | 'region' | 'country' | 'state' | 'city'
  label: string
  id?: number
  code?: string
  url?: string
  state?: string
  country?: string
  region?: string
  children?: Node[]
}

export default function LocationSelector({
  selectedIds,
  onChange,
}: {
  selectedIds: number[]
  onChange: (ids: number[]) => void
}) {
  const [tree, setTree] = useState<Node[]>([])
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [filter, setFilter] = useState('')

  useEffect(() => {
    // Force-refresh to ensure city nodes include numeric IDs for checkbox selection
    const base = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'
    fetch(`${base}/api/v1/locations/hierarchy?refresh=true`)
      .then(r => r.json())
      .then(data => setTree(data.nodes || []))
      .catch(() => setTree([]))
  }, [])

  const isChecked = (id?: number) => (id ? selectedIds.includes(id) : false)

  const toggleId = (id?: number) => {
    if (!id) return
    onChange(isChecked(id) ? selectedIds.filter(x => x !== id) : [...selectedIds, id])
  }

  const collectChildCityIds = (node: Node): number[] => {
    if (node.type === 'city' && node.id) return [node.id]
    return (node.children || []).flatMap(collectChildCityIds)
  }

  const toggleSubtree = (node: Node, check: boolean) => {
    const ids = collectChildCityIds(node)
    const set = new Set(selectedIds)
    ids.forEach(id => (check ? set.add(id) : set.delete(id)))
    onChange(Array.from(set))
  }

  const toggleOpen = (key: string) => setOpen(prev => ({ ...prev, [key]: !prev[key] }))

  const selectedCount = useMemo(() => selectedIds.length, [selectedIds])

  const renderNode = (node: Node, keyPath: string[] = []) => {
    const key = [...keyPath, node.label].join('>')
    const children = node.children || []
    const hasChildren = children.length > 0
    const labelMatches = node.label.toLowerCase().includes(filter)

    if (filter && node.type !== 'city') {
      const anyChildVisible = children.some(child =>
        JSON.stringify(child).toLowerCase().includes(filter)
      )
      if (!labelMatches && !anyChildVisible) return null
    } else if (filter && node.type === 'city' && !labelMatches) {
      return null
    }

    // Selection state for non-city nodes (tri-state behavior)
    const allDescendantIds = collectChildCityIds(node)
    const anyChecked = allDescendantIds.some(id => selectedIds.includes(id))
    const allChecked = allDescendantIds.length > 0 && allDescendantIds.every(id => selectedIds.includes(id))

    const header = (
      <div className="flex items-center justify-between p-2 bg-dark-surface border-b border-dark-border">
        <div className="flex items-center gap-2">
          {node.type !== 'city' && (
            <button className="text-left font-mono text-terminal-400" onClick={() => toggleOpen(key)} aria-label={open[key] ? 'Collapse' : 'Expand'}>
              <span className="inline-block w-4">{open[key] ? '▾' : '▸'}</span>
            </button>
          )}
          <label className="flex items-center text-sm text-dark-text-primary">
            <input
              type="checkbox"
              className="form-checkbox mr-2"
              checked={node.type === 'city' ? isChecked(node.id) : allChecked}
              ref={el => {
                if (!el) return
                // show indeterminate for partially selected groups
                if (node.type !== 'city') el.indeterminate = anyChecked && !allChecked
              }}
              onChange={e => {
                if (node.type === 'city') {
                  toggleId(node.id)
                } else {
                  toggleSubtree(node, e.target.checked)
                }
              }}
            />
            {node.label}
          </label>
        </div>
      </div>
    )

    return (
      <div key={key} className="border border-dark-border rounded mb-2">
        {header}
        {node.type !== 'city' && open[key] && hasChildren && (
          <div className="p-2 space-y-2">
            {children.map(child => renderNode(child, [...keyPath, node.label]))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <input
        className="form-input"
        placeholder="Search cities..."
        value={filter}
        onChange={e => setFilter(e.target.value.toLowerCase())}
      />
      <div className="text-xs text-dark-text-muted">Selected: {selectedCount}</div>
      {tree.map(node => renderNode(node))}
    </div>
  )
}


