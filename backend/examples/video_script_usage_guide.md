# Video Script Generator - Usage Guide

## Quick Start

### 1. Generate Your First Script

```bash
curl -X POST http://localhost:8000/api/v1/video-scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "demo_site_id": 42,
    "lead_id": 123,
    "style": "professional",
    "max_duration_seconds": 120,
    "include_intro": true,
    "include_cta": true
  }'
```

**Response**: Complete script with 6-8 sections, timing, and metadata.

---

### 2. Retrieve Script

```bash
curl http://localhost:8000/api/v1/video-scripts/1
```

**Returns**: Full script details with all sections and metadata.

---

### 3. List Scripts for a Demo Site

```bash
curl http://localhost:8000/api/v1/video-scripts/demo/42
```

**Returns**: Array of script summaries for demo site #42.

---

### 4. Regenerate a Section

If you want to improve a specific section:

```bash
curl -X PUT http://localhost:8000/api/v1/video-scripts/1/section/2 \
  -H "Content-Type: application/json" \
  -d '{
    "section_index": 2,
    "instructions": "Make it more energetic and include specific metrics"
  }'
```

**Result**: Creates version 2 with the updated section.

---

### 5. Approve Script

```bash
curl -X PUT http://localhost:8000/api/v1/video-scripts/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "is_approved": "approved",
    "approved_by": "john@example.com",
    "approval_notes": "Looks great! Ready for production."
  }'
```

---

## Python Integration

### Basic Usage

```python
from app.services.video.script_generator import (
    ScriptGenerator,
    ScriptStyle
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig

# Setup
config = AICouncilConfig(
    openrouter_api_key="your-key-here"
)
council = AICouncil(config=config)
generator = ScriptGenerator(ai_council=council)

# Generate script
script = await generator.generate_script(
    improvement_plan={
        "overall_strategy": "Comprehensive improvements",
        "improvements": [
            {
                "title": "Optimize Performance",
                "category": "performance",
                "impact": "25% faster load time"
            }
        ]
    },
    demo_site_url="https://demo.vercel.app",
    lead_info={
        "id": 123,
        "company_name": "Acme Corp",
        "value": 15000.0
    },
    style=ScriptStyle.PROFESSIONAL,
    max_duration_seconds=120
)

# Access results
print(f"Sections: {len(script.sections)}")
print(f"Duration: {script.total_duration_seconds}s")
print(f"Cost: ${script.metadata['ai_cost']:.4f}")

# Print script
for i, section in enumerate(script.sections):
    print(f"\n{i+1}. {section.title} ({section.duration_seconds}s)")
    print(f"   {section.content}")
    print(f"   Visuals: {', '.join(section.visual_cues)}")
```

---

### Advanced: Section Regeneration

```python
# Get original script
original_script = ...  # From database or previous generation

# Regenerate section 2 with new instructions
new_section = await generator.regenerate_section(
    script=original_script,
    section_index=2,
    new_instructions="Add more technical details and specific metrics"
)

# Create new version with updated section
updated_sections = original_script.sections.copy()
updated_sections[2] = new_section

# Calculate new duration
new_duration = sum(s.duration_seconds for s in updated_sections)

print(f"Updated section: {new_section.title}")
print(f"New duration: {new_duration}s")
```

---

### Validation

```python
# Validate script timing
validation = generator.validate_script_timing(script)

if validation['warnings']:
    print("Warnings found:")
    for warning in validation['warnings']:
        print(f"  - {warning}")
else:
    print("✓ Script timing validated successfully")

print(f"Total duration: {validation['total_duration']}s")
print(f"Average section: {validation['average_section_duration']:.1f}s")
```

---

## Script Styles

### Professional (Default)
Best for: B2B, Enterprise, Corporate clients
```python
style=ScriptStyle.PROFESSIONAL
```

**Example Output**:
> "Your website's performance metrics indicate significant optimization opportunities.
> Load time reductions of 73% can yield conversion improvements of 25-30%, directly
> impacting revenue."

---

### Casual
Best for: Small businesses, Local services, Consumer brands
```python
style=ScriptStyle.CASUAL
```

**Example Output**:
> "Hey! I noticed your website could use a speed boost. Right now it's taking
> 4 seconds to load, but we can get that down to just 1 second. That's a game-changer
> for keeping visitors around!"

---

### Technical
Best for: SaaS, Developers, Tech companies
```python
style=ScriptStyle.TECHNICAL
```

**Example Output**:
> "Current implementation shows a Time to First Byte of 2.1s and Largest Contentful
> Paint at 4.2s. By implementing lazy loading, code splitting, and CDN optimization,
> we can reduce TTFB to 0.4s and LCP to 1.2s, achieving a Lighthouse score of 95+."

---

### Sales
Best for: High-value leads, Conversion-focused campaigns
```python
style=ScriptStyle.SALES
```

**Example Output**:
> "Imagine converting 40% more of your website visitors into customers. That's not
> a dream—it's what happens when you fix your site's performance. I've created a
> demo that proves it. Let me show you how to capture that revenue you're currently
> losing."

---

## Common Patterns

### Pattern 1: Generate Multiple Styles
```python
styles = [
    ScriptStyle.PROFESSIONAL,
    ScriptStyle.CASUAL,
    ScriptStyle.SALES
]

scripts = []
for style in styles:
    script = await generator.generate_script(
        improvement_plan=plan,
        demo_site_url=url,
        lead_info=lead,
        style=style
    )
    scripts.append(script)

# Compare and choose best
best = min(scripts, key=lambda s: len(s.metadata.get('warnings', [])))
```

---

### Pattern 2: Iterative Refinement
```python
# Generate initial script
script_v1 = await generator.generate_script(...)

# Review and regenerate problematic section
if needs_improvement(script_v1.sections[3]):
    new_section = await generator.regenerate_section(
        script=script_v1,
        section_index=3,
        new_instructions="Add more emotion and urgency"
    )

    # Create v2 with updated section
    script_v2 = create_new_version(script_v1, new_section, index=3)
```

---

### Pattern 3: A/B Testing Setup
```python
# Generate two variants
script_a = await generator.generate_script(
    ...,
    style=ScriptStyle.PROFESSIONAL,
    custom_instructions="Focus on ROI and business metrics"
)

script_b = await generator.generate_script(
    ...,
    style=ScriptStyle.SALES,
    custom_instructions="Emphasize emotional benefits and urgency"
)

# Deploy both for A/B testing
await deploy_for_testing(script_a, variant="A")
await deploy_for_testing(script_b, variant="B")
```

---

## Best Practices

### 1. Duration Planning
- **30-60s**: Quick intro videos
- **90-120s**: Standard demo videos (recommended)
- **120-180s**: Detailed walkthroughs
- **180s+**: Avoid (attention drops significantly)

### 2. Section Count
- **Optimal**: 6-8 sections
- **Minimum**: 4 sections (intro + 2 content + CTA)
- **Maximum**: 10 sections (can feel rushed)

### 3. Content Density
```python
# Check word count vs duration
section = script.sections[0]
words = len(section.content.split())
expected = generator.estimate_word_count(section.duration_seconds)

if words > expected * 1.3:
    print("⚠ Too much content - speaking will be rushed")
elif words < expected * 0.5:
    print("⚠ Too little content - awkward pauses")
```

### 4. Scene Variety
Mix scene types for engagement:
- Start with INTRO
- Alternate PROBLEM → SOLUTION
- Include FEATURE highlights
- End with strong CTA

### 5. Cost Optimization
```python
# For low-value leads, use shorter scripts
if lead_value < 10000:
    max_duration = 60  # Faster generation, lower cost

# For high-value leads, invest in quality
if lead_value > 50000:
    style = ScriptStyle.PROFESSIONAL
    max_duration = 120
    include_intro = True
    include_cta = True
```

---

## Troubleshooting

### Issue: Script too long
```python
# Solution: Reduce max duration
script = await generator.generate_script(
    ...,
    max_duration_seconds=90  # Reduced from 120
)
```

### Issue: Too many warnings
```python
# Check validation
validation = generator.validate_script_timing(script)
print(validation['warnings'])

# Regenerate specific problematic sections
for i, warning in enumerate(validation['warnings']):
    if 'Section' in warning:
        section_idx = extract_section_number(warning)
        await generator.regenerate_section(
            script,
            section_idx,
            "Adjust content to match duration better"
        )
```

### Issue: Generic content
```python
# Solution: Add custom instructions
script = await generator.generate_script(
    ...,
    custom_instructions="""
    - Mention specific company achievements
    - Reference their industry challenges
    - Include competitor comparisons
    - Use their brand terminology
    """
)
```

---

## Performance Tips

### 1. Concurrent Generation
```python
import asyncio

# Generate multiple scripts in parallel
tasks = [
    generator.generate_script(...)
    for lead in leads
]

scripts = await asyncio.gather(*tasks)
```

### 2. Caching Improvement Plans
```python
# Cache improvement plan analysis
from functools import lru_cache

@lru_cache(maxsize=100)
def get_improvement_plan(demo_site_id):
    return fetch_plan(demo_site_id)

# Use cached plan
plan = get_improvement_plan(42)
script = await generator.generate_script(
    improvement_plan=plan,
    ...
)
```

### 3. Database Efficiency
```python
# Use selectinload for relationships
from sqlalchemy.orm import selectinload

script = await db.execute(
    select(VideoScript)
    .options(
        selectinload(VideoScript.demo_site),
        selectinload(VideoScript.lead)
    )
    .where(VideoScript.id == script_id)
)
```

---

## Next Steps

After generating your script:

1. **Review & Approve**: Use approval endpoint
2. **Generate Voiceover**: Phase 4, Task 2
3. **Record Screen**: Phase 4, Task 3
4. **Compile Video**: Phase 4, Task 4
5. **Send to Lead**: Personalized video email

---

## Support

For issues or questions:
- Check logs: `logs/app.log`
- Review tests: `tests/test_script_generator.py`
- See examples: `examples/example_video_script.json`
- Read docs: `PHASE4_TASK1_IMPLEMENTATION_REPORT.md`
