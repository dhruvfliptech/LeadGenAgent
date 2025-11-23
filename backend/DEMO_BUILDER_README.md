# Demo Site Builder - Phase 3

Production-ready AI-powered code generator that creates complete demo websites with improvements applied.

## Overview

The Demo Site Builder takes an improvement plan (from Phase 3 analysis) and generates a complete, deployable website with all improvements implemented. It supports multiple frameworks and uses AI to generate high-quality, production-ready code.

## Features

### Code Generation
- **Multi-Framework Support**: HTML/CSS/JS, React, Next.js
- **AI-Powered**: Uses OpenRouter (Claude/GPT-4) for intelligent code generation
- **Production-Ready**: Generates clean, modern, fully-functional code
- **Inline Comments**: Explains each improvement with code comments
- **Complete Projects**: Includes all necessary files (package.json, configs, README)

### Quality Assurance
- **Syntax Validation**: Checks JSON, detects empty files
- **Placeholder Detection**: Warns about TODO/FIXME comments
- **File Structure Validation**: Ensures required files exist
- **Code Metrics**: Tracks lines of code, generation time, costs

### Cost Optimization
- **Semantic Routing**: Routes to appropriate AI model based on lead value
- **Cost Tracking**: Monitors AI spending with AI-GYM integration
- **Efficient Prompts**: Optimized prompts to minimize token usage

## Architecture

```
Input:
├── Original Website (HTML, CSS, JS)
├── Improvement Plan (from Task 2)
└── Framework Preference (html/react/nextjs)

Processing:
├── Plan File Structure
├── Generate System Prompt (framework-specific)
├── Build User Prompt (with improvements)
├── Call AI (via AI Council with semantic routing)
├── Parse AI Response (extract files)
└── Validate Code (syntax, structure)

Output:
├── Complete Codebase (all files)
├── Deployment Config (build commands, etc.)
├── Validation Results (errors, warnings)
└── Metadata (cost, time, improvements)
```

## Installation

### Prerequisites

```bash
# Python 3.11+
# OpenRouter API key (for AI models)
```

### Setup

```bash
# Install dependencies (already in requirements.txt)
pip install pydantic structlog httpx tenacity

# Set environment variables
export OPENROUTER_API_KEY="your-key-here"
```

## Usage

### Basic Example

```python
from app.services.demo_builder import DemoSiteBuilder, Framework, ImprovementPlan, OriginalSite
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig

# Initialize AI Council
config = AICouncilConfig(openrouter_api_key="your-key")
ai_council = AICouncil(config)

# Create builder
builder = DemoSiteBuilder(ai_council)

# Define original site
original_site = OriginalSite(
    url="https://example.com",
    html_content="<html>...</html>",
    title="Example Site"
)

# Define improvement plan
improvement_plan = ImprovementPlan(
    overall_strategy="Modernize design and improve conversion",
    improvements=[
        {
            "title": "Add Hero Section",
            "description": "Create compelling hero with CTA",
            "category": "Design",
            "priority": "high"
        }
    ],
    priority_order=["Design", "Technical"],
    estimated_impact="High - 40% increase"
)

# Build demo site
build = await builder.build_demo_site(
    original_site=original_site,
    improvement_plan=improvement_plan,
    framework=Framework.REACT,  # or HTML, NEXTJS
    lead_value=50000.0,  # Optional: for AI routing
    include_comments=True
)

# Access results
print(f"Generated {len(build.files)} files")
print(f"Status: {build.status}")
print(f"Cost: ${build.ai_cost:.4f}")

# Save to disk
for file_path, content in build.files.items():
    with open(f"output/{file_path}", 'w') as f:
        f.write(content)
```

### Quick Build (Minimal Setup)

```python
from app.services.demo_builder import build_demo_quick
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig

config = AICouncilConfig(openrouter_api_key="your-key")
ai_council = AICouncil(config)

improvement_dict = {
    "overall_strategy": "Quick modernization",
    "improvements": [{"title": "Modern Design", "description": "Apply modern CSS"}],
    "priority_order": ["Design"],
    "estimated_impact": "Medium"
}

build = await build_demo_quick(
    url="https://example.com",
    html_content="<html>...</html>",
    improvement_plan_dict=improvement_dict,
    ai_council=ai_council,
    framework=Framework.HTML
)
```

## Framework Support

### 1. Plain HTML/CSS/JS

**Use Cases:**
- Simple landing pages
- Marketing pages
- Static sites

**Generated Files:**
- `index.html` - Main HTML
- `styles.css` - Improved CSS
- `script.js` - Enhanced JS
- `README.md` - Documentation

**Deployment:**
- No build process required
- Deploy to GitHub Pages, Netlify, or any static host

### 2. React (with TypeScript + Vite)

**Use Cases:**
- Interactive SPAs
- Dashboard applications
- Web apps with state management

**Generated Files:**
- `src/App.tsx` - Main component
- `src/components/Hero.tsx` - Hero section
- `src/components/Features.tsx` - Features section
- `src/components/CTA.tsx` - Call-to-action
- `src/styles/globals.css` - Global styles
- `package.json` - Dependencies
- `tsconfig.json` - TypeScript config
- `vite.config.ts` - Vite config

**Deployment:**
```bash
npm install
npm run build
# Deploy dist/ folder to Vercel, Netlify, etc.
```

### 3. Next.js (App Router + TypeScript)

**Use Cases:**
- SEO-optimized sites
- Full-stack applications
- E-commerce sites

**Generated Files:**
- `app/page.tsx` - Main page
- `app/layout.tsx` - Root layout
- `app/globals.css` - Global styles
- `components/Hero.tsx` - Hero component
- `components/Features.tsx` - Features component
- `lib/analytics.ts` - Analytics helper
- `package.json` - Dependencies
- `next.config.js` - Next.js config
- `tailwind.config.js` - Tailwind config

**Deployment:**
```bash
npm install
npm run build
# Deploy to Vercel (recommended)
```

## AI Integration

### Semantic Routing

The builder uses semantic routing to optimize costs:

| Lead Value | Task Complexity | Model Used | Cost/M Tokens |
|------------|----------------|------------|---------------|
| Any | Demo Site Generation | Based on value | Variable |
| < $25K | Complex | Haiku (cheap) | $0.30-0.60 |
| $25K-$100K | Complex | Sonnet (moderate) | $2-3 |
| > $100K | Complex | Sonnet (premium) | $15-20 |

### Cost Tracking

```python
# With AI-GYM tracking
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker

gym_tracker = AIGymTracker()
ai_council = AICouncil(config, gym_tracker=gym_tracker)
builder = DemoSiteBuilder(ai_council)

# Build demo (tracked)
build = await builder.build_demo_site(...)

# Access metrics
print(f"Cost: ${build.ai_cost:.4f}")
print(f"Model: {build.ai_model_used}")
print(f"Tokens: {build.validation_results.get('tokens', 0)}")
```

## Code Validation

### Automatic Checks

1. **Syntax Validation**
   - JSON files parsed for validity
   - Empty files detected
   - Basic structure checks

2. **Required Files**
   - HTML: `index.html` required
   - React/Next.js: `package.json` required

3. **Placeholder Detection**
   - Warns about: TODO, FIXME, PLACEHOLDER
   - Helps ensure production-ready code

### Validation Results

```python
build = await builder.build_demo_site(...)

validation = build.validation_results
print(f"Valid: {validation['is_valid']}")
print(f"Errors: {validation['errors']}")
print(f"Warnings: {validation['warnings']}")
print(f"File count: {validation['file_count']}")
print(f"Total size: {validation['total_size_bytes']} bytes")
```

## Output Structure

### DemoSiteBuild Object

```python
class DemoSiteBuild:
    framework: Framework  # html, react, nextjs
    files: Dict[str, str]  # file_path -> content
    deployment_config: DeploymentConfig
    preview_url: Optional[str]  # Set after deployment
    status: BuildStatus  # pending, generating, completed, failed

    # Metadata
    improvements_applied: List[str]
    generation_time_seconds: float
    total_lines_of_code: int
    ai_model_used: str
    ai_cost: float
    validation_results: Dict[str, Any]
```

### DeploymentConfig

```python
class DeploymentConfig:
    framework: Framework
    build_command: str  # "npm run build"
    install_command: str  # "npm install"
    output_directory: str  # "dist" or ".next"
    dev_command: str  # "npm run dev"
    port: int  # 3000, 5173, 8000
    environment_variables: Dict[str, str]
```

## Error Handling

### Common Issues

1. **AI Generation Failure**
   ```python
   try:
       build = await builder.build_demo_site(...)
   except Exception as e:
       print(f"Generation failed: {e}")
       # Retry with different settings or fallback
   ```

2. **Validation Errors**
   ```python
   build = await builder.build_demo_site(...)

   if not build.validation_results['is_valid']:
       print("WARNING: Validation failed")
       for error in build.validation_results['errors']:
           print(f"  - {error}")
       # Fix manually or regenerate
   ```

3. **Malformed AI Response**
   - Builder attempts to parse with regex
   - Falls back to alternative parsing
   - May produce incomplete results
   - Solution: Retry generation or adjust prompts

## Best Practices

### 1. Lead Value Optimization

```python
# High-value lead ($100K+) - Use premium model
build = await builder.build_demo_site(
    ...,
    lead_value=100000.0,  # Routes to Claude Sonnet 4
    framework=Framework.NEXTJS
)

# Low-value lead (<$25K) - Use cheap model
build = await builder.build_demo_site(
    ...,
    lead_value=5000.0,  # Routes to Haiku
    framework=Framework.HTML
)
```

### 2. Include Comments for Review

```python
# For client review - include explanation comments
build = await builder.build_demo_site(
    ...,
    include_comments=True  # Adds inline explanations
)

# For production - minimal comments
build = await builder.build_demo_site(
    ...,
    include_comments=False
)
```

### 3. Framework Selection

| Use Case | Recommended Framework |
|----------|----------------------|
| Simple landing page | HTML |
| Marketing site with forms | HTML or React |
| Interactive SPA | React |
| SEO-critical site | Next.js |
| E-commerce | Next.js |
| Dashboard/admin | React |

### 4. Error Recovery

```python
async def build_with_retry(builder, site, plan, max_retries=3):
    """Build with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            build = await builder.build_demo_site(
                original_site=site,
                improvement_plan=plan,
                framework=Framework.REACT
            )

            if build.validation_results['is_valid']:
                return build
            else:
                print(f"Validation failed, retrying... ({attempt+1}/{max_retries})")

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                raise

    raise Exception("Failed after max retries")
```

## Performance

### Generation Times

| Framework | Complexity | Avg Time | AI Cost |
|-----------|-----------|----------|---------|
| HTML | Simple | 5-10s | $0.001-0.005 |
| React | Moderate | 10-20s | $0.005-0.015 |
| Next.js | Complex | 15-30s | $0.010-0.030 |

### Optimization Tips

1. **Limit HTML Preview**: Only send first 15K chars to AI
2. **Use Cheap Models**: For low-value leads
3. **Batch Generation**: Generate multiple demos concurrently
4. **Cache Results**: Store generated code for reuse

## Testing

### Run Tests

```bash
cd backend
source venv/bin/activate
python -m pytest app/services/test_demo_builder.py -v
```

### Test Coverage

- 33 test cases covering:
  - File structure planning (3 frameworks)
  - Code generation and parsing
  - Configuration file generation
  - Validation logic
  - Error handling
  - Edge cases

## Examples

See `/Users/greenmachine2.0/Craigslist/backend/app/services/demo_builder_example.py` for comprehensive usage examples:

1. Basic HTML demo
2. React SPA
3. Next.js full-stack
4. Quick builder utility
5. AI-GYM cost tracking
6. Error handling
7. Save files to disk

## API Reference

### DemoSiteBuilder

#### `__init__(ai_council: AICouncil)`
Initialize builder with AI Council instance.

#### `async build_demo_site(...) -> DemoSiteBuild`
Build complete demo site with improvements.

**Parameters:**
- `original_site: OriginalSite` - Original website data
- `improvement_plan: ImprovementPlan` - Improvement plan
- `framework: Framework` - Target framework (html/react/nextjs)
- `lead_value: Optional[float]` - Lead value for AI routing
- `include_comments: bool` - Include explanation comments

**Returns:** `DemoSiteBuild` object

### Utility Functions

#### `async build_demo_quick(...) -> DemoSiteBuild`
Quick demo generation with minimal setup.

**Parameters:**
- `url: str` - Original site URL
- `html_content: str` - Original HTML
- `improvement_plan_dict: Dict` - Improvement plan as dict
- `ai_council: AICouncil` - AI Council instance
- `framework: Framework` - Target framework

## Roadmap

### Future Enhancements

1. **Additional Frameworks**
   - Vue.js support
   - Svelte support
   - Astro support

2. **Code Quality**
   - Linting integration (ESLint, Prettier)
   - Type checking (mypy, TypeScript strict)
   - Automated testing generation

3. **Deployment Integration**
   - Vercel auto-deploy
   - Netlify integration
   - GitHub Pages deployment

4. **Advanced Features**
   - Component library integration
   - Design system generation
   - Accessibility audit
   - Performance benchmarking

## Contributing

See main project CONTRIBUTING.md for guidelines.

## License

See main project LICENSE file.

## Support

For issues or questions:
1. Check examples in `demo_builder_example.py`
2. Review test cases in `test_demo_builder.py`
3. Consult AI Council documentation
4. Contact development team

---

**Built with:**
- AI Council (multi-model orchestration)
- Semantic Router (cost optimization)
- AI-GYM (performance tracking)
- OpenRouter (unified AI access)

**Supported by:** Claude Sonnet 4, GPT-4o, DeepSeek-V3, Qwen 2.5, Gemini Flash
