# AI-GYM Quick Reference

## Installation

```bash
# Install dependencies
pip install scipy numpy

# Run migration
alembic upgrade head

# Test installation
python test_ai_gym.py
```

## Common Usage Patterns

### 1. Basic Model Routing

```python
from app.services.ai_gym import get_model_router
from app.services.ai_gym.models import TaskType

router = get_model_router()
model = await router.route(
    task_type=TaskType.WEBSITE_ANALYSIS,
    strategy="balanced",
    db=db
)
```

### 2. Track Performance

```python
from app.services.ai_gym import get_metric_tracker
from app.services.ai_gym.tracker import TaskMetrics

tracker = get_metric_tracker()
metric_id = await tracker.record_execution(db, TaskMetrics(
    model_id=model.id,
    task_type=TaskType.WEBSITE_ANALYSIS,
    prompt_tokens=1200,
    completion_tokens=800,
    latency_ms=1850,
    cost_usd=Decimal("0.0246"),
    quality_score=92.5
))
```

### 3. Calculate Quality

```python
from app.services.ai_gym import get_quality_scorer

scorer = get_quality_scorer()
score = await scorer.score(
    task_type=TaskType.EMAIL_WRITING,
    output=email_text,
    context={}
)
```

### 4. Run A/B Test

```python
from app.services.ai_gym import get_ab_test_manager
from app.services.ai_gym.ab_testing import ABTestConfig

ab_manager = get_ab_test_manager()

# Create test
config = ABTestConfig(
    test_name="claude_vs_gpt4",
    task_type=TaskType.EMAIL_WRITING,
    variant_a_model="anthropic/claude-3.5-sonnet",
    variant_b_model="openai/gpt-4-turbo-preview",
    traffic_split=0.5,
    min_sample_size=100,
    target_metric="quality"
)
test_id = await ab_manager.create_test(db, config)

# Assign variant
variant_name, model_id = await ab_manager.assign_variant(
    db=db,
    test_name="claude_vs_gpt4",
    task_type=TaskType.EMAIL_WRITING
)

# Analyze results
results = await ab_manager.analyze_test(db, "claude_vs_gpt4")
```

### 5. Cost Analysis

```python
from app.services.ai_gym import get_metric_tracker

tracker = get_metric_tracker()
analysis = await tracker.get_cost_analysis(db, days=30)

print(f"Total: ${analysis['total_cost_usd']:.2f}")
print(f"Executions: {analysis['total_executions']}")
```

## Task Types

```python
TaskType.WEBSITE_ANALYSIS      # Website analysis
TaskType.CODE_GENERATION       # Code generation
TaskType.EMAIL_WRITING         # Email writing
TaskType.CONVERSATION_RESPONSE # Chat responses
TaskType.LEAD_SCORING          # Lead qualification
TaskType.CONTENT_SUMMARIZATION # Summarization
TaskType.DATA_EXTRACTION       # Data extraction
```

## Routing Strategies

```python
"best_quality"  # Premium models (Claude 3.5, GPT-4)
"best_cost"     # Cheapest models (Claude Haiku, Qwen)
"balanced"      # Cost/quality balance (default)
"fastest"       # Lowest latency
```

## Available Models

```python
"anthropic/claude-3.5-sonnet"    # Best reasoning
"anthropic/claude-3-haiku"       # Fastest, cheapest
"openai/gpt-4-turbo-preview"     # High quality
"openai/gpt-4o"                  # Balanced
"qwen/qwen-2.5-72b-instruct"     # Multilingual
"x-ai/grok-beta"                 # Creative
"deepseek/deepseek-coder"        # Code specialist
```

## API Endpoints

```bash
# List models
GET /api/v1/ai-gym/models

# Get recommendation
POST /api/v1/ai-gym/models/recommend

# Record metrics
POST /api/v1/ai-gym/metrics

# Get stats
POST /api/v1/ai-gym/metrics/stats

# Cost analysis
POST /api/v1/ai-gym/metrics/cost-analysis

# Create A/B test
POST /api/v1/ai-gym/ab-tests

# Get test results
GET /api/v1/ai-gym/ab-tests/{name}/results

# Quality score
POST /api/v1/ai-gym/quality/score

# Dashboard
GET /api/v1/ai-gym/dashboard
```

## Integration Example

```python
# Complete integration in service
async def process_with_ai_gym(task_type, prompt, context, db):
    # 1. Route
    router = get_model_router()
    model = await router.route(task_type, "balanced", db=db)

    # 2. Execute
    ai_client = get_openrouter_client()
    start = time.time()
    output = await ai_client.generate_completion(prompt, model=model.id)
    latency = int((time.time() - start) * 1000)

    # 3. Score
    scorer = get_quality_scorer()
    quality = await scorer.score(task_type, output, context)

    # 4. Track
    tracker = get_metric_tracker()
    await tracker.record_execution(db, TaskMetrics(
        model_id=model.id,
        task_type=task_type,
        prompt_tokens=len(prompt.split()),
        completion_tokens=len(output.split()),
        latency_ms=latency,
        cost_usd=model.calculate_cost(1000, 500),
        quality_score=quality
    ))

    return output
```

## Best Practices

1. Always use `balanced` strategy initially
2. Record metrics for every execution
3. Set quality thresholds for critical tasks
4. Run A/B tests before changing models
5. Review cost analysis weekly
6. Collect user feedback when possible

## Troubleshooting

**No models found**: Check constraints not too restrictive
**A/B test inconclusive**: Collect more samples
**High costs**: Switch to `best_cost` strategy or review model usage
**Low quality**: Use `best_quality` or set `min_quality_score`

## Support

See AI_GYM_COMPLETE_GUIDE.md for detailed documentation.
