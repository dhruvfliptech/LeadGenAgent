# Craigslist Lead Generation Dashboard - Design System

## Design Philosophy
A sophisticated developer tool that merges terminal aesthetics with modern usability. Dark, clean interface inspired by Vapi.ai and ByteRover dashboards, optimized for data-heavy workflows and real-time monitoring.

## Color System

### Core Palette
```css
:root {
  /* Primary Colors */
  --bg-primary: #000000;          /* Pure black background */
  --text-primary: #FFFFFF;        /* Primary white text */
  --accent-terminal: #00FF00;     /* Terminal green */
  --accent-cyan: #00FFFF;         /* Cyan accent */
  
  /* Status Colors */
  --success: #10B981;             /* Success green */
  --warning: #F59E0B;             /* Warning yellow */
  --error: #EF4444;               /* Error red */
  
  /* Gray Scale */
  --gray-900: #111111;            /* Card backgrounds */
  --gray-800: #1a1a1a;           /* Elevated surfaces */
  --gray-700: #2a2a2a;           /* Borders, dividers */
  --gray-600: #404040;           /* Inactive elements */
  --gray-500: #666666;           /* Secondary text */
  --gray-400: #888888;           /* Placeholder text */
  
  /* Semantic Colors */
  --lead-high: #00FF00;          /* High-quality lead */
  --lead-medium: #F59E0B;        /* Medium-quality lead */
  --lead-low: #666666;           /* Low-quality lead */
  --active: #00FFFF;             /* Active states */
  --hover: rgba(0, 255, 255, 0.1); /* Hover states */
}
```

### Color Usage Guidelines
- **Background hierarchy**: Black base → Gray-900 cards → Gray-800 elevated
- **Text hierarchy**: White primary → Gray-400 secondary → Gray-600 disabled
- **Accent usage**: Terminal green for success/active, cyan for interactive elements
- **Status indicators**: Use semantic colors for lead quality and system states

## Typography System

### Font Stack
```css
/* Monospace for data display */
--font-mono: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;

/* Sans-serif for UI elements */
--font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
```

### Type Scale
```css
--text-xs: 0.75rem;     /* 12px - Timestamps, metadata */
--text-sm: 0.875rem;    /* 14px - Secondary text */
--text-base: 1rem;      /* 16px - Body text */
--text-lg: 1.125rem;    /* 18px - Card titles */
--text-xl: 1.25rem;     /* 20px - Section headers */
--text-2xl: 1.5rem;     /* 24px - Page titles */
--text-3xl: 1.875rem;   /* 30px - Dashboard titles */
```

### Typography Rules
- **Data elements**: Always use monospace font
- **UI elements**: Sans-serif for buttons, labels, navigation
- **Line height**: 1.5 for readability, 1.2 for headings
- **Letter spacing**: 0.025em for monospace data

## Component Architecture

### 1. Navigation Bar
```
┌─────────────────────────────────────────────────────────────┐
│ [Logo] Leads | Locations | Keywords | Rules | Analytics [⚙️] │
└─────────────────────────────────────────────────────────────┘
```

**Specifications:**
- Height: 64px
- Background: var(--gray-900)
- Border bottom: 1px solid var(--gray-700)
- Logo: Terminal green accent
- Active state: Cyan underline + text color
- Hover state: Subtle cyan glow

### 2. Lead Stream (Main Dashboard)
```
┌─────────────────────────────────────────────────────────────┐
│ Filters ▼    Search: [____________]    View: [Grid] [List]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ LEAD CARD   │ │ LEAD CARD   │ │ LEAD CARD   │            │
│ │ ●●● HIGH    │ │ ●●○ MEDIUM  │ │ ●○○ LOW     │            │
│ │ $45k-65k    │ │ Remote OK   │ │ Entry Level │            │
│ │ [Contact]   │ │ [Contact]   │ │ [Archive]   │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**Lead Card Specifications:**
- Dimensions: 320px × 240px (grid), full-width (list)
- Background: var(--gray-900)
- Border: 1px solid var(--gray-700)
- Border radius: 8px
- Hover: Border changes to var(--accent-cyan)
- Quality indicators: 3-dot system with color coding

### 3. Location Selector Interface
```
┌─────────────────────────────────────────────────────────────┐
│ Quick Select: [All US] [West Coast] [Tech Hubs] [Custom]    │
├─────────────────────────────────────────────────────────────┤
│ ┌─ 🇺🇸 United States ──────────────────────────────────────┐ │
│ │  ├─ 📍 California (1,234 leads)                          │ │
│ │  │  ├─ San Francisco Bay Area                            │ │
│ │  │  ├─ Los Angeles Metro                                 │ │
│ │  │  └─ San Diego                                         │ │
│ │  ├─ 📍 New York (892 leads)                              │ │
│ │  └─ 📍 Texas (567 leads)                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Tree View Specifications:**
- Expandable/collapsible with smooth animations
- Lead count indicators in gray-400
- Checkbox selection with indeterminate states
- Icons: Monospace characters or simple symbols

### 4. Keyword Manager
```
┌─────────────────────────────────────────────────────────────┐
│ Include Keywords               │ Exclude Keywords            │
├─────────────────────────────────┼─────────────────────────────┤
│ [+ Add] [Import]               │ [+ Add] [Import]            │
│ ┌─ javascript ──────────── ✕ ┐ │ ┌─ intern ────────────── ✕ ┐ │
│ ┌─ react ─────────────── ✕ ┐ │ ┌─ unpaid ───────────── ✕ ┐ │
│ ┌─ senior ────────────── ✕ ┐ │ ┌─ volunteer ──────── ✕ ┐ │
│ └─────────────────────────────┘ │ └─────────────────────────────┘ │
├─────────────────────────────────┼─────────────────────────────┤
│ Impact Preview: +234 leads     │ Impact Preview: -89 leads   │
└─────────────────────────────────┴─────────────────────────────┘
```

**Keyword Tag Specifications:**
- Background: var(--gray-800)
- Border: 1px solid var(--gray-600)
- Padding: 6px 12px
- Font: Monospace
- Remove button: Hover shows red accent
- Drag handle: Subtle grip icon

### 5. Analytics Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ ┌─ Lead Quality ─┐ ┌─ Response Rate ┐ ┌─ Model Performance ─┐ │
│ │ ●●● 23%        │ │     📈         │ │ Accuracy: 94.2%    │ │
│ │ ●●○ 45%        │ │    /  \        │ │ Precision: 89.1%   │ │
│ │ ●○○ 32%        │ │   /    \       │ │ Last trained: 2h   │ │
│ └───────────────┘ └───────────────┘ └────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─ Location Heat Map ──────────────────────────────────────┐ │
│ │ [    🗺️ US MAP WITH HEAT OVERLAY    ]                   │ │
│ │ Red: High volume, Green: High quality                   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Interactive States

### Button States
```css
/* Primary Button */
.btn-primary {
  background: var(--accent-terminal);
  color: var(--bg-primary);
  border: none;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  box-shadow: 0 0 10px var(--accent-terminal);
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--gray-600);
}

.btn-secondary:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}
```

### Form Elements
```css
/* Input Fields */
.input {
  background: var(--gray-900);
  border: 1px solid var(--gray-600);
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.input:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 2px rgba(0, 255, 255, 0.2);
}
```

## Responsive Breakpoints

```css
/* Mobile First Approach */
.container {
  padding: 16px;
}

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .container {
    padding: 24px;
  }
  
  .lead-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .container {
    padding: 32px;
  }
  
  .lead-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Large Desktop: 1440px+ */
@media (min-width: 1440px) {
  .lead-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

## Animation Guidelines

### Micro-interactions
```css
/* Smooth transitions for all interactive elements */
* {
  transition: 
    color 0.2s ease,
    background-color 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

/* Terminal cursor blink animation */
@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Data loading shimmer */
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Success pulse */
@keyframes success-pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
```

### Page Transitions
- **Fade in**: 300ms ease for new content
- **Slide up**: Cards and modals enter from bottom
- **Scale**: Buttons and interactive elements on hover
- **Glow**: Terminal green glow for success states

## Accessibility Features

### Color Contrast
- All text meets WCAG AA standards (4.5:1 minimum)
- Interactive elements have 3:1 minimum contrast
- Focus indicators use high contrast cyan

### Keyboard Navigation
- Tab order follows logical reading flow
- All interactive elements have focus indicators
- Escape key closes modals and dropdowns
- Enter/Space activate buttons and controls

### Screen Reader Support
- Semantic HTML structure
- ARIA labels for complex widgets
- Live regions for real-time updates
- Alternative text for data visualizations

## Implementation Notes

### CSS Custom Properties
Use CSS custom properties for theming and easy maintenance:
```css
.theme-dark {
  --bg-primary: #000000;
  --text-primary: #FFFFFF;
  /* ... all color variables */
}
```

### Component Library Structure
```
components/
├── atoms/
│   ├── Button/
│   ├── Input/
│   └── Badge/
├── molecules/
│   ├── LeadCard/
│   ├── SearchBar/
│   └── FilterPanel/
└── organisms/
    ├── Navigation/
    ├── LeadStream/
    └── Analytics/
```

### Performance Considerations
- Use CSS Grid for layouts (better than Flexbox for 2D layouts)
- Implement virtual scrolling for large lead lists
- Lazy load analytics charts and maps
- Use CSS transforms for animations (GPU acceleration)
- Minimize repaints with `will-change` property

This design system creates a sophisticated, developer-focused interface that balances terminal aesthetics with modern usability, ensuring efficient lead management workflows while maintaining visual consistency and accessibility standards.