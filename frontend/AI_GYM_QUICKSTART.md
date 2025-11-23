# AI-GYM Quick Start Guide

## Getting Started

### 1. Start the Development Server

```bash
cd /Users/greenmachine2.0/Craigslist/frontend
npm run dev
```

Open your browser to `http://localhost:5173`

### 2. Navigate to AI-GYM

Click on "Phase 3 Tools" dropdown in the navigation bar, then select "AI-GYM" from the "Insights" section.

Or directly navigate to: `http://localhost:5173/ai-gym`

## Available Routes

| Route | Page | Description |
|-------|------|-------------|
| `/ai-gym` | Dashboard | Main overview with stats, charts, and top models |
| `/ai-gym/models` | Model Comparison | Side-by-side model comparison tool |
| `/ai-gym/ab-tests` | A/B Tests List | View and manage all A/B tests |
| `/ai-gym/ab-tests/new` | Create Test | 3-step wizard to create new A/B test |
| `/ai-gym/ab-tests/:id` | Test Detail | Detailed results for specific test |

## Quick Tour

### Dashboard (`/ai-gym`)

1. **Quick Stats** - View total calls, costs, quality, and savings at a glance
2. **Task Type Filter** - Filter all data by task type (email generation, lead scoring, etc.)
3. **Performance Chart** - Quality over time for top models
4. **Cost Efficiency Chart** - Compare quality per dollar
5. **Top Models Table** - Detailed metrics for best performers
6. **Active A/B Tests** - See running tests
7. **Task Breakdown** - Percentage distribution by task type

### Model Comparison (`/ai-gym/models`)

1. Click **"Add Models"** button
2. Select 2-4 models to compare
3. Filter by **task type** to see task-specific performance
4. View **side-by-side cards** with detailed metrics
5. Compare in **charts and tables**
6. Remove models by clicking the X button

### A/B Test Management (`/ai-gym/ab-tests`)

1. View all tests with **status filters** (All, Running, Completed, Draft, Paused)
2. See **stats overview** (total, running, completed, draft)
3. Click any **test card** to view details
4. Click **"Create A/B Test"** to start wizard

### Create A/B Test (`/ai-gym/ab-tests/new`)

**Step 1: Select Task Type**
- Choose from 6 task types
- All tests must have a task type

**Step 2: Choose Models**
- Select 2-4 models to test
- View model specs (context, pricing, features)
- At least 2 required to proceed

**Step 3: Configure Test**
- Enter test name and description
- Adjust traffic split (auto-calculated or manual)
- Set duration (1-30 days)
- Choose success metric (Quality, Cost, or Efficiency)
- Review summary and create

### Test Detail (`/ai-gym/ab-tests/:id`)

1. **Test Configuration** - View task type, models, duration, traffic split
2. **Winner Announcement** - See winner (if completed) with statistical significance
3. **Side-by-Side Results** - Compare all models
4. **Performance Charts** - Quality over time and metrics comparison
5. **Detailed Metrics** - Comprehensive table with all stats

## Sample Data

The system uses mock data from `/frontend/src/mocks/models.mock.ts`:

### Models (6 available)
- Claude Sonnet 4.5 (Anthropic)
- Claude Opus 4 (Anthropic)
- GPT-4 Turbo (OpenAI)
- GPT-4o (OpenAI)
- Gemini 2.0 Flash (Google)
- DeepSeek Chat (DeepSeek)

### Task Types (6 available)
- Email Generation
- Lead Scoring
- Sentiment Analysis
- Content Generation
- Script Writing
- Analysis

### A/B Tests (3 sample tests)
- **Running**: Email Generation: Claude vs GPT-4o
- **Completed**: Lead Scoring: Multi-Model Comparison (Winner: Claude Sonnet 4.5)
- **Draft**: Budget AI: DeepSeek vs Gemini

## Key Features

### Dashboard
- Real-time stats (mocked)
- Interactive charts (Recharts)
- Filterable by task type
- Top performers table
- Active tests preview

### Model Comparison
- Compare up to 4 models
- Side-by-side cards
- Performance & spec tables
- Cost efficiency analysis
- Task-specific metrics

### A/B Testing
- 3-step creation wizard
- Traffic split configuration
- Multiple success metrics
- Winner detection
- Statistical significance
- Detailed results

## Tips & Tricks

### Filtering
1. Use task type selector to focus on specific use cases
2. All charts and tables update automatically
3. "All Tasks" shows aggregate data

### Model Selection
1. Start with 2 models for simple comparison
2. Add more (up to 4) for comprehensive analysis
3. Remove models by clicking X on card

### Traffic Split
1. Auto-calculated evenly by default
2. Manually adjust as needed
3. Must total exactly 100%

### Success Metrics
- **Quality**: Best avg quality score wins
- **Cost**: Lowest avg cost wins
- **Efficiency**: Best quality/dollar ratio wins

## Customization

### Add Custom Mock Data

Edit `/frontend/src/mocks/models.mock.ts`:

```typescript
// Add new model
export const mockModelConfigs: ModelConfig[] = [
  // ... existing models
  {
    model_id: 'new-model',
    provider: 'custom',
    name: 'new-model',
    display_name: 'New Model',
    // ... other config
  }
]

// Add performance data
export const mockModelPerformance: ModelPerformance[] = [
  // ... existing performance
  {
    model_id: 'new-model',
    task_type: 'email_generation',
    // ... metrics
  }
]
```

### Customize Charts

Edit chart components:

```typescript
// /frontend/src/components/PerformanceChart.tsx
// Change colors
const COLORS = ['#10b981', '#3b82f6', '#f59e0b']

// /frontend/src/components/CostEfficiencyChart.tsx
// Adjust bar styling
<Bar dataKey="qualityPerDollar" fill="#3b82f6" />
```

### Add New Task Type

1. Add to `TaskType` in `models.mock.ts`
2. Add to `taskTypes` array in `TaskTypeSelector.tsx`
3. Add mock performance data

## Troubleshooting

### Charts Not Displaying
- Check browser console for errors
- Verify data format matches component props
- Ensure Recharts is installed: `npm install recharts`

### Navigation Not Working
- Verify routes in `/frontend/src/App.tsx`
- Check Layout.tsx includes AI-GYM link
- Clear browser cache

### TypeScript Errors
- Run `npm run type-check` to see all errors
- Recharts may show esModuleInterop warnings (safe to ignore)
- Vite handles JSX compilation automatically

### Styling Issues
- Ensure TailwindCSS is configured
- Check dark theme classes are applied
- Verify `tailwind.config.js` includes AI-GYM paths

## Next Steps

### Backend Integration (Future)
1. Replace mock data with API calls
2. Connect to real AI model APIs
3. Store test results in database
4. Add real-time metrics collection
5. Implement authentication

### Advanced Features (Future)
1. Automatic winner detection
2. Cost alerts and budgets
3. Model recommendations
4. Export reports (PDF/CSV)
5. Scheduled tests
6. Email notifications
7. Custom metrics

## File Locations

```
frontend/src/
├── pages/
│   ├── AIGym.tsx                     # Dashboard
│   ├── AIGymModels.tsx               # Model comparison
│   ├── AIGymABTests.tsx              # Tests list
│   ├── AIGymABTestDetail.tsx         # Test detail
│   └── AIGymABTestNew.tsx            # Create wizard
├── components/
│   ├── PerformanceChart.tsx          # Line chart
│   ├── CostEfficiencyChart.tsx       # Bar chart
│   ├── ModelCard.tsx                 # Model display
│   ├── TaskTypeSelector.tsx          # Task filter
│   └── ABTestCard.tsx                # Test card
└── mocks/
    └── models.mock.ts                # Mock data
```

## Resources

- [Full Implementation Guide](./AI_GYM_IMPLEMENTATION.md)
- [Component Usage Guide](./AI_GYM_COMPONENT_GUIDE.md)
- [Recharts Documentation](https://recharts.org/)
- [TailwindCSS Docs](https://tailwindcss.com/)

## Support

For issues or questions:
1. Check documentation files in `/frontend/`
2. Review component comments in code
3. Check browser console for errors
4. Verify mock data structure

---

**Built with**: React + TypeScript + Vite + TailwindCSS + Recharts

**Status**: ✅ Complete and ready for use
