# How to Integrate AI-GYM into Main Application

## Step 1: Run Database Migration

```bash
cd /Users/greenmachine2.0/Craigslist/backend

# Run migration to create AI-GYM tables
alembic upgrade head

# Verify tables were created
psql $DATABASE_URL -c "\dt ai_model_metrics"
psql $DATABASE_URL -c "\d ab_test_variants"
```

## Step 2: Register AI-GYM Endpoints in Main Router

Edit `/Users/greenmachine2.0/Craigslist/backend/app/main.py`:

```python
# Add to imports at top
from app.api.endpoints import ai_gym

# Add to router registration (around line 60-80)
app.include_router(
    ai_gym.router,
    prefix=f"{settings.API_V1_STR}/ai-gym",
    tags=["ai-gym"]
)
```

## Step 3: Test the API Endpoints

Start the backend:

```bash
cd /Users/greenmachine2.0/Craigslist/backend
python -m uvicorn app.main:app --reload --port 8000
```

Test endpoints:

```bash
# List all available models
curl http://localhost:8000/api/v1/ai-gym/models | jq

# Get model recommendation
curl -X POST http://localhost:8000/api/v1/ai-gym/models/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "website_analysis",
    "strategy": "balanced"
  }' | jq

# Get dashboard stats
curl http://localhost:8000/api/v1/ai-gym/dashboard | jq
```

## Step 4: Integrate into Website Analyzer

Edit `/Users/greenmachine2.0/Craigslist/backend/app/services/website_analyzer.py`:

Add at the top:

```python
from app.services.ai_gym import (
    get_model_router,
    get_metric_tracker,
    get_quality_scorer
)
from app.services.ai_gym.models import TaskType
from app.services.ai_gym.tracker import TaskMetrics
import time
from decimal import Decimal
```

Replace the existing `analyze_website_with_ai` function with:

```python
async def analyze_website_with_ai(
    url: str,
    html_content: str,
    screenshot_path: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Analyze website with AI-GYM integration.

    Now uses intelligent model routing, quality scoring, and performance tracking.
    """

    # Step 1: Route to optimal model
    router = get_model_router()

    if db:
        model = await router.route(
            task_type=TaskType.WEBSITE_ANALYSIS,
            strategy="balanced",
            db=db,
            min_quality_score=80.0  # Ensure minimum quality
        )
    else:
        # Fallback if no DB connection
        from app.services.ai_gym.models import get_model_registry
        registry = get_model_registry()
        models = registry.recommend_models_for_task(
            TaskType.WEBSITE_ANALYSIS,
            "balanced"
        )
        model = models[0]

    logger.info(f"AI-GYM routed to: {model.name} ({model.id})")

    # Step 2: Prepare prompt
    prompt = f"""
    Analyze this website and extract business information:

    URL: {url}

    HTML Content:
    {html_content[:5000]}

    Provide analysis in JSON format with:
    - business_type
    - industry
    - target_audience
    - services (array)
    - unique_value_proposition
    - technologies (array)
    - pain_points (array of 3-5 items)
    - opportunities (array of 3-5 improvement opportunities)
    - contact_methods (array)
    - location (if available)
    """

    # Step 3: Execute AI call
    ai_client = get_openrouter_client()
    start_time = time.time()

    try:
        analysis = await ai_client.generate_completion(
            prompt=prompt,
            model=model.id,
            temperature=0.7,
            max_tokens=2000
        )

        latency_ms = int((time.time() - start_time) * 1000)
        error_occurred = False
        error_message = None

        logger.info(f"AI analysis completed in {latency_ms}ms")

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_occurred = True
        error_message = str(e)
        analysis = "{}"
        logger.error(f"AI analysis failed: {e}")

    # Step 4: Calculate quality score
    scorer = get_quality_scorer()
    quality_score = await scorer.score(
        task_type=TaskType.WEBSITE_ANALYSIS,
        output=analysis,
        context={"url": url}
    )

    logger.info(f"Quality score: {quality_score:.1f}/100")

    # Step 5: Estimate tokens and calculate cost
    # In production, get actual token counts from API response
    prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
    completion_tokens = len(analysis.split()) * 1.3
    cost_usd = model.calculate_cost(
        int(prompt_tokens),
        int(completion_tokens)
    )

    logger.info(f"Estimated cost: ${cost_usd:.4f}")

    # Step 6: Track metrics in database
    if db:
        tracker = get_metric_tracker()
        try:
            metric_id = await tracker.record_execution(
                db=db,
                metrics=TaskMetrics(
                    model_id=model.id,
                    task_type=TaskType.WEBSITE_ANALYSIS,
                    prompt_tokens=int(prompt_tokens),
                    completion_tokens=int(completion_tokens),
                    latency_ms=latency_ms,
                    cost_usd=cost_usd,
                    quality_score=quality_score,
                    error_occurred=error_occurred,
                    error_message=error_message,
                    metadata={
                        "url": url,
                        "model_name": model.name,
                        "has_screenshot": screenshot_path is not None
                    }
                )
            )
            logger.info(f"Metrics recorded with ID: {metric_id}")
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")

    # Step 7: Return analysis with metadata
    return {
        "analysis": analysis,
        "metadata": {
            "model_used": model.name,
            "model_id": model.id,
            "quality_score": quality_score,
            "cost_usd": float(cost_usd),
            "latency_ms": latency_ms,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "error_occurred": error_occurred
        }
    }
```

## Step 5: Update API Endpoint to Pass Database Session

Edit `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/scraper.py`:

Find the website analyzer endpoint and ensure it passes the database session:

```python
@router.post("/analyze-website")
async def analyze_website(
    request: WebsiteAnalysisRequest,
    db: AsyncSession = Depends(get_db)  # Add this
):
    """Analyze a website with AI-GYM integration."""

    # ... existing code ...

    # Pass db to analyzer
    analysis = await analyze_website_with_ai(
        url=request.url,
        html_content=html_content,
        screenshot_path=screenshot_path,
        db=db  # Add this
    )

    return analysis
```

## Step 6: Add User Feedback Endpoint (Optional but Recommended)

Add to `/Users/greenmachine2.0/Craigslist/backend/app/api/endpoints/scraper.py`:

```python
from app.services.ai_gym import get_metric_tracker

@router.post("/website-analysis-feedback")
async def record_analysis_feedback(
    metric_id: int,
    approved: bool,
    user_rating: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Record user feedback for a website analysis.

    Call this when user approves/rejects AI analysis.
    """
    tracker = get_metric_tracker()

    await tracker.record_user_feedback(
        db=db,
        metric_id=metric_id,
        approved=approved,
        user_rating=user_rating
    )

    return {"message": "Feedback recorded successfully"}
```

## Step 7: Test the Integration

```bash
# 1. Test website analysis with AI-GYM
curl -X POST http://localhost:8000/api/v1/scraper/analyze-website \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }' | jq

# 2. Check that metrics were recorded
curl http://localhost:8000/api/v1/ai-gym/metrics/recent \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10
  }' | jq

# 3. Get cost analysis
curl -X POST http://localhost:8000/api/v1/ai-gym/metrics/cost-analysis \
  -H "Content-Type: application/json" \
  -d '{"days": 7}' | jq
```

## Step 8: Monitor and Optimize

After a week of usage:

```bash
# Get performance comparison
curl -X POST http://localhost:8000/api/v1/ai-gym/metrics/comparison \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "website_analysis",
    "days": 7
  }' | jq

# Check which model is performing best
# Consider switching strategy based on results
```

## Step 9: Set Up A/B Test (Optional)

Test Claude vs GPT-4 for website analysis:

```python
# In Python console or script
from app.services.ai_gym import get_ab_test_manager
from app.services.ai_gym.ab_testing import ABTestConfig
from app.services.ai_gym.models import TaskType

config = ABTestConfig(
    test_name="website_claude_vs_gpt4",
    task_type=TaskType.WEBSITE_ANALYSIS,
    variant_a_model="anthropic/claude-3.5-sonnet",
    variant_b_model="openai/gpt-4-turbo-preview",
    traffic_split=0.5,
    min_sample_size=100,
    max_duration_days=7,
    target_metric="quality"
)

ab_manager = get_ab_test_manager()
test_id = await ab_manager.create_test(db, config)
print(f"Created A/B test with ID: {test_id}")
```

Then modify the analyzer to use the test:

```python
# In website_analyzer.py, add parameter
async def analyze_website_with_ai(
    url: str,
    html_content: str,
    db: Optional[AsyncSession] = None,
    use_ab_test: str = None  # Test name
):
    if use_ab_test and db:
        ab_manager = get_ab_test_manager()
        variant_name, model_id = await ab_manager.assign_variant(
            db=db,
            test_name=use_ab_test,
            task_type=TaskType.WEBSITE_ANALYSIS
        )
        router = get_model_router()
        model = router.get_model_by_id(model_id)
    else:
        # Normal routing
        router = get_model_router()
        model = await router.route(...)

    # ... rest of function ...

    # After execution, record variant result
    if use_ab_test and db:
        await ab_manager.record_variant_result(
            db=db,
            test_name=use_ab_test,
            variant_name=variant_name,
            quality_score=quality_score,
            cost_usd=float(cost_usd)
        )
```

## Step 10: View Results

After collecting data:

```bash
# Get A/B test results
curl http://localhost:8000/api/v1/ai-gym/ab-tests/website_claude_vs_gpt4/results | jq

# Get dashboard overview
curl http://localhost:8000/api/v1/ai-gym/dashboard | jq
```

## Verification Checklist

- [ ] Database migration completed
- [ ] AI-GYM endpoints registered in main app
- [ ] Endpoints accessible via API
- [ ] Website analyzer integrated with AI-GYM
- [ ] Database session passed to analyzer
- [ ] Metrics being recorded in database
- [ ] Quality scores calculating correctly
- [ ] Cost tracking working
- [ ] User feedback endpoint added (optional)
- [ ] A/B test created (optional)

## Troubleshooting

### Issue: "Table ai_model_metrics does not exist"

**Solution:**
```bash
alembic upgrade head
```

### Issue: "ModuleNotFoundError: No module named 'scipy'"

**Solution:**
```bash
pip install scipy numpy
```

### Issue: AI-GYM endpoints return 404

**Solution:** Ensure endpoints are registered in `app/main.py`:
```python
app.include_router(
    ai_gym.router,
    prefix=f"{settings.API_V1_STR}/ai-gym",
    tags=["ai-gym"]
)
```

### Issue: Metrics not being recorded

**Solution:** Ensure database session is passed to `analyze_website_with_ai`:
```python
analysis = await analyze_website_with_ai(
    url=request.url,
    html_content=html_content,
    db=db  # Make sure this is passed
)
```

## Next Steps

1. Monitor costs for first week
2. Review quality scores
3. Collect user feedback
4. Adjust routing strategy if needed
5. Consider setting up A/B tests
6. Build dashboard UI (optional)

## Support

- Complete Guide: `AI_GYM_COMPLETE_GUIDE.md`
- Quick Reference: `AI_GYM_QUICK_REFERENCE.md`
- Test Suite: `python test_ai_gym.py`
- Examples: `app/services/ai_gym/example_integration.py`
