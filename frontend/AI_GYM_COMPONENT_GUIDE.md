# AI-GYM Component Usage Guide

## Component Hierarchy

```
AIGym (Dashboard)
├── TaskTypeSelector
├── PerformanceChart
├── CostEfficiencyChart
└── Link to AIGymABTests

AIGymModels (Model Comparison)
├── TaskTypeSelector
├── ModelCard (multiple)
├── PerformanceChart
└── CostEfficiencyChart

AIGymABTests (Test List)
└── ABTestCard (multiple)

AIGymABTestDetail (Test Detail)
├── PerformanceChart
└── Custom bar chart

AIGymABTestNew (Create Wizard)
├── TaskTypeSelector (Step 1)
└── Model selection grid (Step 2)
```

## Quick Component Reference

### 1. PerformanceChart

**Purpose**: Display quality scores over time for multiple models

**Props**:
```typescript
{
  data: DataPoint[]           // Array of { date: string, [modelId]: number }
  lines: {                    // Models to display
    dataKey: string          // Model ID
    name: string             // Display name
    color: string            // Hex color
  }[]
  title?: string             // Chart title
  yAxisLabel?: string        // Y-axis label
  height?: number            // Chart height (default 300)
}
```

**Example**:
```tsx
<PerformanceChart
  data={[
    { date: 'Jan 1', 'claude-sonnet-4.5': 8.5, 'gpt-4o': 8.3 },
    { date: 'Jan 2', 'claude-sonnet-4.5': 8.7, 'gpt-4o': 8.5 }
  ]}
  lines={[
    { dataKey: 'claude-sonnet-4.5', name: 'Claude Sonnet 4.5', color: '#10b981' },
    { dataKey: 'gpt-4o', name: 'GPT-4o', color: '#3b82f6' }
  ]}
  title="Quality Over Time"
  yAxisLabel="Quality Score"
/>
```

---

### 2. CostEfficiencyChart

**Purpose**: Compare quality per dollar across models

**Props**:
```typescript
{
  data: {
    model: string            // Model display name
    qualityPerDollar: number // Quality / Cost
    quality: number          // Quality score
    cost: number            // Cost per request
  }[]
  title?: string            // Chart title
  height?: number           // Chart height (default 300)
}
```

**Example**:
```tsx
<CostEfficiencyChart
  data={[
    {
      model: 'Claude Sonnet 4.5',
      qualityPerDollar: 207,
      quality: 8.7,
      cost: 0.042
    },
    {
      model: 'GPT-4o',
      qualityPerDollar: 354,
      quality: 8.5,
      cost: 0.024
    }
  ]}
/>
```

---

### 3. ModelCard

**Purpose**: Display model configuration and performance metrics

**Props**:
```typescript
{
  config: ModelConfig        // Model configuration
  performance?: ModelPerformance  // Optional performance data
  selected?: boolean         // Selection state
  onClick?: () => void      // Click handler
  showActions?: boolean     // Show action buttons
}
```

**Example**:
```tsx
<ModelCard
  config={mockModelConfigs[0]}
  performance={mockModelPerformance[0]}
  selected={selectedModels.includes('claude-sonnet-4.5')}
  onClick={() => handleToggleModel('claude-sonnet-4.5')}
/>
```

**Visual Features**:
- Provider badge (color-coded)
- Quality score (large, colored)
- Performance metrics (time, cost, requests)
- Model specs (context, pricing, features)
- Cost efficiency indicator
- Selection state (border + checkmark)

---

### 4. TaskTypeSelector

**Purpose**: Filter UI by AI task type

**Props**:
```typescript
{
  selected: TaskType | 'all'  // Currently selected task
  onChange: (taskType: TaskType | 'all') => void  // Change handler
}
```

**Example**:
```tsx
const [taskType, setTaskType] = useState<TaskType | 'all'>('all')

<TaskTypeSelector
  selected={taskType}
  onChange={(type) => setTaskType(type)}
/>
```

**Task Types**:
- All Tasks
- Email Generation
- Lead Scoring
- Sentiment Analysis
- Content Generation
- Script Writing
- Analysis

---

### 5. ABTestCard

**Purpose**: Display A/B test summary

**Props**:
```typescript
{
  test: ABTest  // Test configuration and results
}
```

**Example**:
```tsx
<ABTestCard test={mockABTests[0]} />
```

**Visual Features**:
- Status badge (Draft/Running/Paused/Completed)
- Test info (task type, models, requests, duration)
- Winner display (if completed)
- Results preview (current stats)
- Traffic split visualization
- Clickable to detail page

---

## Data Flow Patterns

### Pattern 1: Filtering by Task Type

```tsx
const [selectedTaskType, setSelectedTaskType] = useState<TaskType | 'all'>('all')

// Filter performance data
const filteredPerformance = useMemo(() => {
  if (selectedTaskType === 'all') return mockModelPerformance
  return mockModelPerformance.filter(p => p.task_type === selectedTaskType)
}, [selectedTaskType])

// Use filtered data
<TaskTypeSelector selected={selectedTaskType} onChange={setSelectedTaskType} />
<PerformanceChart data={prepareChartData(filteredPerformance)} ... />
```

### Pattern 2: Model Selection/Comparison

```tsx
const [selectedModels, setSelectedModels] = useState<string[]>([])

const handleToggleModel = (modelId: string) => {
  if (selectedModels.includes(modelId)) {
    setSelectedModels(selectedModels.filter(id => id !== modelId))
  } else {
    setSelectedModels([...selectedModels, modelId])
  }
}

// Display selected models
{selectedModels.map(modelId => {
  const config = mockModelConfigs.find(c => c.model_id === modelId)
  const performance = mockModelPerformance.find(p => p.model_id === modelId)
  return (
    <ModelCard
      key={modelId}
      config={config}
      performance={performance}
      selected
      onClick={() => handleToggleModel(modelId)}
    />
  )
})}
```

### Pattern 3: Cost Efficiency Calculation

```tsx
const costEfficiencyData = useMemo(() => {
  return filteredPerformance.map(perf => {
    const config = mockModelConfigs.find(c => c.model_id === perf.model_id)
    return {
      model: config?.display_name || perf.model_id,
      qualityPerDollar: perf.avg_quality_score / perf.avg_cost_per_request,
      quality: perf.avg_quality_score,
      cost: perf.avg_cost_per_request,
    }
  }).sort((a, b) => b.qualityPerDollar - a.qualityPerDollar)
}, [filteredPerformance])

<CostEfficiencyChart data={costEfficiencyData} />
```

---

## Common Use Cases

### Use Case 1: Add Model Performance Dashboard

```tsx
import { mockModelConfigs, mockModelPerformance } from '@/mocks/models.mock'
import ModelCard from '@/components/ModelCard'

function MyDashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {mockModelConfigs.map(config => {
        const performance = mockModelPerformance.find(p => p.model_id === config.model_id)
        return <ModelCard key={config.model_id} config={config} performance={performance} />
      })}
    </div>
  )
}
```

### Use Case 2: Show Task-Specific Performance

```tsx
import { useState, useMemo } from 'react'
import { TaskType, mockModelPerformance } from '@/mocks/models.mock'
import TaskTypeSelector from '@/components/TaskTypeSelector'
import PerformanceChart from '@/components/PerformanceChart'

function TaskPerformance() {
  const [taskType, setTaskType] = useState<TaskType | 'all'>('email_generation')

  const chartData = useMemo(() => {
    const filtered = mockModelPerformance.filter(p => p.task_type === taskType)
    // Transform to chart format...
    return transformedData
  }, [taskType])

  return (
    <>
      <TaskTypeSelector selected={taskType} onChange={setTaskType} />
      <PerformanceChart data={chartData} lines={...} />
    </>
  )
}
```

### Use Case 3: Compare Two Models

```tsx
import { ModelConfig, ModelPerformance } from '@/mocks/models.mock'
import ModelCard from '@/components/ModelCard'

interface ComparisonProps {
  modelA: { config: ModelConfig; performance: ModelPerformance }
  modelB: { config: ModelConfig; performance: ModelPerformance }
}

function ModelComparison({ modelA, modelB }: ComparisonProps) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <ModelCard {...modelA} selected />
      <ModelCard {...modelB} selected />
    </div>
  )
}
```

---

## Styling Guide

### Color Palette

**Status Colors**:
- Draft: `bg-gray-500/20 text-gray-400`
- Running: `bg-blue-500/20 text-blue-400`
- Paused: `bg-yellow-500/20 text-yellow-400`
- Completed: `bg-emerald-500/20 text-emerald-400`

**Provider Colors**:
- Anthropic: `bg-orange-500/20 text-orange-400`
- OpenAI: `bg-emerald-500/20 text-emerald-400`
- Google: `bg-blue-500/20 text-blue-400`
- DeepSeek: `bg-purple-500/20 text-purple-400`
- Meta: `bg-pink-500/20 text-pink-400`

**Quality Score Colors**:
- 9.0+: `text-emerald-400` (Excellent)
- 8.0-8.9: `text-blue-400` (Good)
- <8.0: `text-yellow-400` (Fair)

**Error Rate Colors**:
- <1%: `text-emerald-400` (Good)
- 1-3%: `text-yellow-400` (Warning)
- >3%: `text-red-400` (Poor)

### Common Classes

```css
/* Card */
.card {
  @apply bg-dark-surface border border-dark-border rounded-lg p-6;
}

/* Stat */
.stat-value {
  @apply text-3xl font-bold text-dark-text-primary;
}
.stat-label {
  @apply text-sm text-dark-text-muted;
}

/* Button Primary */
.btn-primary {
  @apply px-4 py-2 bg-terminal-500 text-white rounded-lg
         hover:bg-terminal-600 transition-colors font-medium;
}

/* Button Secondary */
.btn-secondary {
  @apply px-4 py-2 bg-dark-border text-dark-text-primary
         rounded-lg hover:bg-dark-border/70 transition-colors;
}
```

---

## Mock Data Reference

### Available Mock Data

```typescript
// Import from mocks
import {
  mockModelConfigs,      // 6 AI models
  mockModelPerformance,  // Performance data per model/task
  mockABTests,          // 3 A/B tests
  mockQualityMetrics,   // Quality metrics samples

  // Helper functions
  getTotalModelStats,    // Overall stats
  getActiveABTests,     // Running tests only
  getModelPerformanceByTask,
  getTopModelsByQuality,
  getMostCostEffective,
} from '@/mocks/models.mock'
```

### Model IDs
- `claude-sonnet-4.5`
- `claude-opus-4`
- `gpt-4-turbo`
- `gpt-4o`
- `gemini-2.0-flash`
- `deepseek-chat`

### Task Types
- `email_generation`
- `lead_scoring`
- `sentiment_analysis`
- `content_generation`
- `script_writing`
- `analysis`

---

## Performance Tips

1. **Use useMemo for expensive calculations**:
```tsx
const filteredData = useMemo(() => {
  return expensiveFilter(data)
}, [data])
```

2. **Lazy load charts**:
```tsx
{data.length > 0 && <PerformanceChart data={data} ... />}
```

3. **Debounce filters**:
```tsx
const debouncedSearch = useMemo(
  () => debounce((value) => setSearch(value), 300),
  []
)
```

4. **Paginate large tables**:
```tsx
const paginatedData = data.slice(page * pageSize, (page + 1) * pageSize)
```

---

## Accessibility Checklist

- [ ] All interactive elements have proper ARIA labels
- [ ] Charts have descriptive titles
- [ ] Color is not the only indicator (use icons + text)
- [ ] Keyboard navigation works for all controls
- [ ] Focus states are visible
- [ ] Screen reader can access all information
- [ ] Form inputs have associated labels
- [ ] Error messages are announced

---

## Testing Scenarios

1. **Dashboard Load**: All stats and charts render
2. **Task Filter**: Filtering updates all dependent data
3. **Model Selection**: Can select/deselect up to 4 models
4. **Chart Interaction**: Tooltips show on hover
5. **A/B Test Creation**: Wizard validation works
6. **Traffic Split**: Total must equal 100%
7. **Responsive**: Works on mobile/tablet/desktop
8. **Navigation**: All links work correctly

---

## Common Issues & Solutions

### Issue: Chart not displaying
**Solution**: Ensure data format matches expected structure
```tsx
// Correct format
data={[{ date: 'Jan 1', model1: 8.5, model2: 8.3 }]}
```

### Issue: Model card missing performance
**Solution**: Performance is optional, card adapts
```tsx
<ModelCard config={config} /> {/* No performance */}
<ModelCard config={config} performance={perf} /> {/* With performance */}
```

### Issue: Task filter not updating charts
**Solution**: Ensure useMemo dependencies are correct
```tsx
const chartData = useMemo(() => {
  // ...
}, [selectedTaskType]) // Add dependency
```

---

## Further Customization

### Add New Task Type
1. Update `TaskType` in `models.mock.ts`
2. Add to `taskTypes` array in `TaskTypeSelector.tsx`
3. Add mock performance data

### Add New Chart
1. Create component in `/components/`
2. Import Recharts components
3. Follow PerformanceChart pattern
4. Make responsive with `ResponsiveContainer`

### Custom Color Scheme
Update provider/status colors in:
- `ModelCard.tsx` - `providerColors`
- `ABTestCard.tsx` - `statusConfig`
- Custom components as needed

---

## Resources

- [Recharts Documentation](https://recharts.org/)
- [TailwindCSS Docs](https://tailwindcss.com/)
- [React Router Docs](https://reactrouter.com/)
- [Heroicons](https://heroicons.com/)
- [Date-fns](https://date-fns.org/)
