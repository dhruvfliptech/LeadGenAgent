import { useEffect, useMemo, useState } from 'react'
import { scraperApi } from '@/services/phase3Api'

type StructuredCategories = Record<string, { name: string; slug: string }[]>

export default function CategorySelector({
  value,
  onChange,
}: {
  value: string[]
  onChange: (categories: string[]) => void
}) {
  const [data, setData] = useState<StructuredCategories>({})
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const [query, setQuery] = useState('')

  useEffect(() => {
    scraperApi.getCategoriesStructured().then(res => {
      const payload: StructuredCategories = res.data || {}
      setData(payload)
    })
  }, [])

  const toggleGroup = (group: string) => setOpen(prev => ({ ...prev, [group]: !prev[group] }))
  const isChecked = (slug: string) => value.includes(slug)
  const toggle = (slug: string) => {
    onChange(isChecked(slug) ? value.filter(s => s !== slug) : [...value, slug])
  }
  const selectAllInGroup = (group: string) => {
    const slugs = (data[group] || []).map(x => x.slug)
    const merged = Array.from(new Set([...value, ...slugs]))
    onChange(merged)
  }
  const clearGroup = (group: string) => {
    const slugs = new Set((data[group] || []).map(x => x.slug))
    onChange(value.filter(v => !slugs.has(v)))
  }

  const totalSelected = value.length

  const filteredData = useMemo(() => {
    if (!query.trim()) return data
    const q = query.toLowerCase()
    const result: StructuredCategories = {}
    Object.entries(data).forEach(([group, items]) => {
      const matches = items.filter(i => i.name.toLowerCase().includes(q))
      if (matches.length) result[group] = matches
    })
    return result
  }, [data, query])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <input className="form-input flex-1" placeholder="Search categories..." value={query} onChange={e => setQuery(e.target.value)} />
        <div className="text-xs text-dark-text-muted">Selected: {totalSelected}</div>
      </div>
      {Object.entries(filteredData).map(([group, items]) => (
        <div key={group} className="border border-dark-border rounded">
          <div className="flex items-center justify-between p-3 bg-dark-surface">
            <button className="text-left font-mono text-terminal-400" onClick={() => toggleGroup(group)} aria-label={open[group] ? 'Collapse' : 'Expand'}>
              <span className="inline-block w-4">{open[group] ? '▾' : '▸'}</span> {group}
            </button>
            <div className="space-x-2">
              <button className="btn-secondary btn-xs" onClick={() => selectAllInGroup(group)}>Select All</button>
              <button className="btn-secondary btn-xs" onClick={() => clearGroup(group)}>Clear</button>
            </div>
          </div>
          {open[group] && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 p-3">
              {items.map(item => (
                <label key={item.slug} className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    className="mr-2"
                    checked={isChecked(item.slug)}
                    onChange={() => toggle(item.slug)}
                  />
                  <span title={item.slug}>{item.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}


