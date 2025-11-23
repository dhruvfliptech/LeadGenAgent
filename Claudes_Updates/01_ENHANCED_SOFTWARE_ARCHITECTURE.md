# Enhanced Software Architecture - AI-Powered Internal Outreach Platform
## November 4, 2025

---

## Document Purpose

This document **builds upon** the foundational architecture in `/Codex/Software_Architecture_Blueprint.md` by integrating:
- ML research findings (LLM-as-Judge, multi-model routing, cost optimization)
- Internal tool optimizations (2 users, 100-1000 leads/day scale)
- Simplified deployment strategy (no enterprise-scale complexity needed)
- Tactical implementation guidance for MVP delivery

**Relationship to Codex**: This is the **implementation-ready** version incorporating research findings. Codex provides the strategic vision; this document provides the tactical build plan.

---

## 1. Architecture Enhancements from Research

### 1.1 Multi-Model Router (NEW - Critical for Cost Optimization)

**Research Finding**: Semantic routing achieves 70-85% cost savings vs single premium model.

```python
# Router Architecture
class SemanticRouter:
    """
    Routes tasks to optimal model based on:
    - Task complexity (classify, analyze, generate)
    - Lead value (enterprise vs small business)
    - Budget constraints
    """

    ROUTING_RULES = {
        # Low-complexity tasks → Ultra-cheap models
        "classification": "deepseek-v3",        # $0.27/M tokens
        "scoring": "qwen-2.5",                   # $0.14/M tokens
        "extraction": "deepseek-v3",             # $0.27/M tokens

        # Medium-complexity → Cheap models
        "email_draft": "claude-haiku",           # $0.50/M tokens
        "summary": "claude-haiku",               # $0.50/M tokens

        # High-complexity → Premium models (routed by lead value)
        "website_analysis": self._route_by_value,  # $0.50-3.00/M
        "demo_code": "qwen2.5-coder-32b",        # $1.50/M tokens

        # Judge/evaluation → Always premium
        "judge": "claude-sonnet-4",              # $3.00/M tokens
    }

    def route(self, task_type: str, context: Dict) -> str:
        """Route to optimal model."""
        rule = self.ROUTING_RULES.get(task_type)

        # Dynamic routing for analysis
        if callable(rule):
            return rule(context)

        return rule

    def _route_by_value(self, context: Dict) -> str:
        """Route analysis by lead value."""
        lead_value = context.get("estimated_value", 0)

        if lead_value > 50000:
            return "claude-sonnet-4"      # Enterprise: $3.00/M
        elif lead_value > 10000:
            return "gpt-4o"               # Mid-market: $2.50/M
        else:
            return "claude-haiku"         # SMB: $0.50/M
```

**Integration Point**: Add `services/semantic_router.py` (referenced in AI Council Orchestrator)

**Cost Impact**:
- Before: 1000 leads/day × $3.00/M = $90/day
- After: 1000 leads/day × $0.50/M avg = $15/day (83% savings)

---

### 1.2 AI Council with LLM-as-Judge (ENHANCED)

**Research Finding**: LLM-as-Judge + DeepEval achieves AI-GYM goals without RL-Factory complexity.

```python
# Enhanced AI Council Architecture
class AICouncil:
    """
    Multi-model orchestration with judge evaluation.

    Replaces: Simple multi-model querying from Codex
    Adds: Judge evaluation, automated scoring, feedback loop
    """

    def __init__(self):
        self.router = SemanticRouter()
        self.models = {
            "claude-sonnet-4": ClaudeModel(),
            "gpt-4o": OpenAIModel(),
            "deepseek-v3": DeepSeekModel(),
            "qwen-2.5": QwenModel(),
            "qwen2.5-coder-32b": QwenCoderModel(),
            "gemini-1.5-pro": GeminiModel(),
        }
        self.judge = ClaudeModel("claude-sonnet-4")  # Always Claude for judging
        self.evaluator = DeepEvalFramework()

    async def execute_task(
        self,
        task_type: str,
        prompt: str,
        context: Dict,
        require_judge: bool = True
    ) -> TaskResult:
        """
        Execute task with optimal model selection and evaluation.

        Flow:
        1. Router selects model(s)
        2. Execute task (single or multi-model)
        3. If multi-model, judge selects winner
        4. Evaluate with DeepEval metrics
        5. Log to AI-GYM performance table
        6. Return result
        """

        # Step 1: Route to model(s)
        if task_type in ["website_analysis", "email_generation"]:
            # Multi-model for critical tasks
            models = self._select_council_members(task_type, context)
        else:
            # Single model for simple tasks
            models = [self.router.route(task_type, context)]

        # Step 2: Execute in parallel
        responses = await asyncio.gather(*[
            self._execute_single(model, prompt, context)
            for model in models
        ])

        # Step 3: Judge selection (if multiple responses)
        if len(responses) > 1 and require_judge:
            winner = await self._judge_responses(
                task_type, prompt, responses, context
            )
        else:
            winner = responses[0]

        # Step 4: Evaluate with DeepEval
        metrics = await self.evaluator.evaluate(
            task_type=task_type,
            prompt=prompt,
            response=winner.text,
            context=context
        )

        # Step 5: Log to AI-GYM
        await self._log_performance(
            task_type=task_type,
            model=winner.model,
            cost=winner.cost,
            duration=winner.duration,
            metrics=metrics,
            lead_id=context.get("lead_id")
        )

        # Step 6: Return
        return TaskResult(
            text=winner.text,
            model=winner.model,
            metrics=metrics,
            cost=winner.cost
        )

    async def _judge_responses(
        self,
        task_type: str,
        prompt: str,
        responses: List[ModelResponse],
        context: Dict
    ) -> ModelResponse:
        """
        Use Claude Sonnet 4 as judge to select best response.

        Judge Prompt Pattern:
        - Show all responses (blinded model names)
        - Evaluation criteria (relevance, accuracy, tone, actionability)
        - Request structured scoring + winner selection
        """

        judge_prompt = f"""You are evaluating {len(responses)} responses for: {task_type}

Original Task: {prompt}

Evaluate each response on:
1. Relevance (0-10): Addresses the task requirements
2. Accuracy (0-10): Factually correct and specific
3. Actionability (0-10): Provides clear next steps
4. Tone (0-10): Appropriate professional tone

Responses:
{self._format_responses_for_judge(responses)}

Return JSON:
{{
    "scores": [
        {{"response_id": 1, "relevance": X, "accuracy": X, "actionability": X, "tone": X, "total": X, "reasoning": "..."}},
        ...
    ],
    "winner": 1,
    "rationale": "Why this response is best..."
}}
"""

        judge_result = await self.judge.generate(judge_prompt)
        winner_idx = judge_result["winner"] - 1

        # Attach judge metadata
        winner = responses[winner_idx]
        winner.judge_scores = judge_result["scores"][winner_idx]
        winner.judge_rationale = judge_result["rationale"]

        return winner

    def _select_council_members(
        self,
        task_type: str,
        context: Dict
    ) -> List[str]:
        """
        Select 2-3 models for council voting on critical tasks.

        Strategy:
        - Always include Claude Sonnet 4 (quality baseline)
        - Add 1-2 cheaper alternatives for cost comparison
        - Track which alternatives approach Claude quality
        """

        if task_type == "website_analysis":
            lead_value = context.get("estimated_value", 0)
            if lead_value > 50000:
                # Enterprise: 3-model council
                return ["claude-sonnet-4", "gpt-4o", "gemini-1.5-pro"]
            else:
                # SMB: 2-model council (save cost)
                return ["claude-sonnet-4", "claude-haiku"]

        elif task_type == "email_generation":
            # Always test cheap vs premium for emails
            return ["claude-sonnet-4", "claude-haiku", "deepseek-v3"]

        elif task_type == "demo_code":
            # Code specialists
            return ["qwen2.5-coder-32b", "claude-sonnet-4"]

        return ["claude-sonnet-4"]  # Fallback
```

**Integration Point**: Enhance `services/ai_council.py` with judge + evaluation

**Why This Works**:
1. **No RL-Factory Complexity**: Uses proven LLM-as-Judge pattern (industry standard)
2. **Automatic Optimization**: Tracks which cheap models approach premium quality
3. **Cost Control**: Only uses 2-3 models for critical tasks (not all 6 always)
4. **Feedback Loop**: AI-GYM table tracks outcomes → inform future routing

---

### 1.3 DeepEval Integration (NEW - Automated Quality Metrics)

**Research Finding**: DeepEval provides automated metrics without manual scoring.

```python
# DeepEval Integration
class DeepEvalFramework:
    """
    Automated evaluation using DeepEval metrics.

    Replaces: Manual quality scoring
    Adds: Automated faithfulness, relevance, coherence metrics
    """

    def __init__(self):
        self.metrics = {
            "faithfulness": FaithfulnessMetric(),
            "relevance": RelevanceMetric(),
            "coherence": CoherenceMetric(),
            "conciseness": ConcisenessMetric(),
        }

    async def evaluate(
        self,
        task_type: str,
        prompt: str,
        response: str,
        context: Dict
    ) -> Dict[str, float]:
        """
        Run automated evaluation metrics.

        Returns scores 0-1 for each metric.
        """

        # Select relevant metrics for task type
        if task_type == "website_analysis":
            metrics_to_run = ["faithfulness", "relevance", "coherence"]
        elif task_type == "email_generation":
            metrics_to_run = ["relevance", "conciseness"]
        elif task_type == "demo_code":
            metrics_to_run = ["faithfulness", "coherence"]
        else:
            metrics_to_run = ["relevance"]

        # Run metrics
        scores = {}
        for metric_name in metrics_to_run:
            metric = self.metrics[metric_name]
            score = await metric.evaluate(
                input=prompt,
                output=response,
                context=context
            )
            scores[metric_name] = score

        # Calculate composite score
        scores["composite"] = sum(scores.values()) / len(scores)

        return scores
```

**Integration Point**: Add `services/deepeval_framework.py`

**Database Table** (add to Data_and_API_Spec):
```sql
ALTER TABLE ai_gym_performance
    ADD COLUMN faithfulness_score NUMERIC(4,3),
    ADD COLUMN relevance_score NUMERIC(4,3),
    ADD COLUMN coherence_score NUMERIC(4,3),
    ADD COLUMN conciseness_score NUMERIC(4,3),
    ADD COLUMN composite_score NUMERIC(4,3);
```

---

### 1.4 Feedback Loop Architecture (NEW - Critical for AI-GYM)

**Research Finding**: Track business outcomes → correlate with model choices → optimize over time.

```python
# Feedback Loop System
class FeedbackLoopOrchestrator:
    """
    Connects AI outputs to business outcomes.

    Flow:
    1. AI generates email → logs to ai_gym_performance
    2. Email sent → logs to email_sends
    3. User opens/clicks/replies → updates email_sends
    4. Nightly job: Correlate outcomes back to AI performance
    5. Weekly job: Update routing weights based on outcomes
    """

    async def correlate_outcomes(self):
        """
        Nightly job: Link AI performance to business outcomes.

        Query:
        - Get all email_sends from last 48 hours
        - Find corresponding ai_gym_performance records
        - Update conversion_metric based on outcomes
        """

        query = """
        UPDATE ai_gym_performance agp
        SET conversion_metric = CASE
            WHEN es.replied_at IS NOT NULL THEN 1.0
            WHEN es.clicked_at IS NOT NULL THEN 0.5
            WHEN es.opened_at IS NOT NULL THEN 0.25
            ELSE 0.0
        END,
        metadata = metadata || jsonb_build_object(
            'email_outcome', CASE
                WHEN es.replied_at IS NOT NULL THEN 'replied'
                WHEN es.clicked_at IS NOT NULL THEN 'clicked'
                WHEN es.opened_at IS NOT NULL THEN 'opened'
                ELSE 'no_action'
            END
        )
        FROM email_sends es
        WHERE agp.lead_id = es.lead_id
            AND agp.task_type = 'email_generation'
            AND agp.created_at >= NOW() - INTERVAL '48 hours'
            AND agp.conversion_metric IS NULL;
        """

        await self.db.execute(query)
        await self.db.commit()

    async def optimize_routing_weights(self):
        """
        Weekly job: Analyze which models perform best → update router weights.

        Analysis:
        1. Group by (task_type, model_name)
        2. Calculate avg conversion_metric, avg cost, avg quality
        3. Score models: (conversion × quality) / cost
        4. Update routing preferences
        """

        # Get model performance by task
        query = """
        SELECT
            task_type,
            model_name,
            COUNT(*) as usage_count,
            AVG(conversion_metric) as avg_conversion,
            AVG(composite_score) as avg_quality,
            AVG(cost) as avg_cost,
            (AVG(conversion_metric) * AVG(composite_score)) / NULLIF(AVG(cost), 0) as efficiency_score
        FROM ai_gym_performance
        WHERE created_at >= NOW() - INTERVAL '7 days'
            AND conversion_metric IS NOT NULL
        GROUP BY task_type, model_name
        HAVING COUNT(*) >= 10
        ORDER BY task_type, efficiency_score DESC;
        """

        results = await self.db.fetch_all(query)

        # Update routing preferences
        for row in results:
            task_type = row["task_type"]
            model = row["model_name"]
            efficiency = row["efficiency_score"]

            # If cheap model achieves 90%+ of premium quality
            if self._is_cheaper_model(model) and efficiency > 0.9:
                logger.info(f"🎯 Model upgrade: {model} performing at 90%+ for {task_type}")
                # Update router to prefer this model
                await self._update_router_preference(task_type, model)

        # Generate weekly report
        await self._generate_aigym_report(results)
```

**Integration Point**: Add `services/feedback_loop.py` + scheduled jobs

**Celery/n8n Scheduling**:
```python
# Schedule in celery beat or n8n
CELERYBEAT_SCHEDULE = {
    'correlate-outcomes': {
        'task': 'services.feedback_loop.correlate_outcomes',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    'optimize-routing': {
        'task': 'services.feedback_loop.optimize_routing_weights',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday 3 AM
    },
}
```

---

## 2. Internal Tool Optimizations (2 Users, 100-1000 Leads/Day)

### 2.1 Simplified Architecture

**Key Changes from Codex**:
1. **No enterprise-scale infrastructure** (ECS/K8s) → Docker Compose is sufficient
2. **No complex auth** (JWT + RBAC) → Simple API key auth (2 users only)
3. **No multi-tenant** → Single workspace model
4. **No high availability** → 99% uptime acceptable (not 99.9%)

```yaml
# Simplified Docker Compose (replaces ECS/K8s from Codex)
version: '3.8'
services:
  # Backend API
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/outreach
      - REDIS_URL=redis://redis:6379
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  # Frontend
  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "5173:5173"

  # Workers (scraping, analysis, email)
  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/outreach
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  # Database
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=outreach
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis (caching + jobs)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

**Cost Savings vs Codex Architecture**:
- Codex: AWS ECS + RDS + ElastiCache = $500-1000/month
- Simplified: Single VPS (Hetzner/DigitalOcean) = $40-80/month

---

### 2.2 Simplified Auth (API Key Only)

**Replace**: Codex JWT + RBAC system
**With**: Simple API key for 2 internal users

```python
# Simplified Auth Middleware
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Store in environment
VALID_API_KEYS = {
    os.getenv("USER_1_API_KEY"): "user1@company.com",
    os.getenv("USER_2_API_KEY"): "user2@company.com",
}

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key and return user email."""
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return VALID_API_KEYS[api_key]

# Usage in endpoints
@router.get("/api/v2/campaigns")
async def get_campaigns(user: str = Depends(verify_api_key)):
    """Get campaigns (authenticated)."""
    return await campaign_service.get_all()
```

**Why This Works**:
- Only 2 users → no need for user management UI
- Internal tool → no signup/login flows
- API keys rotated manually (once per quarter)

---

### 2.3 Scale Targets (100-1000 Leads/Day)

**Capacity Planning**:

| Component | 100 Leads/Day | 1000 Leads/Day | Notes |
|-----------|---------------|----------------|-------|
| Scraping | 1 worker | 3 workers | Parallel scraping |
| Website Analysis | 100 × $0.50 = $50/day | 1000 × $0.50 = $500/day | Using cheap models + routing |
| Email Generation | 100 × $0.10 = $10/day | 1000 × $0.10 = $100/day | Mostly Haiku |
| Database | Single Postgres | Single Postgres + read replica | Sufficient for 1M records |
| Redis | Single instance | Single instance | Handles 10K ops/sec |
| **Total Daily Cost** | **~$70** | **~$650** | Mostly AI API costs |

**Infrastructure Sizing**:
- **100 leads/day**: 2-core VPS ($40/month) + AI APIs ($70/day)
- **1000 leads/day**: 8-core VPS ($80/month) + AI APIs ($650/day)

---

## 3. Key Architectural Decisions (ADRs)

### ADR-001: Use LLM-as-Judge Instead of RL-Factory

**Decision**: Use Claude Sonnet 4 as judge + DeepEval metrics instead of RL-Factory training.

**Rationale**:
- RL-Factory designed for tool-calling agents (not content generation)
- LLM-as-Judge is industry standard (Anthropic, OpenAI, Google all use it)
- Achieves AI-GYM goals (track performance, optimize) without RL complexity
- 10x simpler to implement and maintain
- Can add DPO fine-tuning later if needed (after 1000+ examples)

**Status**: Accepted
**Date**: November 4, 2025

---

### ADR-002: Use Semantic Router for Cost Optimization

**Decision**: Route tasks to optimal models based on task type + lead value.

**Rationale**:
- 70-85% cost savings vs always using premium models
- Simple rule-based routing sufficient (no ML needed)
- Can evolve routing based on AI-GYM feedback

**Alternatives Considered**:
1. Always use Claude Sonnet 4 → Too expensive ($3/M tokens)
2. RouteLLM (ML-based router) → Overkill for 100-1000 leads/day
3. AWS Multi-Agent Orchestrator → Too complex for internal tool

**Status**: Accepted
**Date**: November 4, 2025

---

### ADR-003: Use Docker Compose Instead of Kubernetes

**Decision**: Deploy with Docker Compose on single VPS, not Kubernetes.

**Rationale**:
- Only 2 users → no need for enterprise-scale orchestration
- 100-1000 leads/day → single server handles load
- Simpler to maintain (no K8s expertise needed)
- 90% cost savings vs managed K8s

**Migration Path**: Can move to K8s later if scaling beyond 10K leads/day

**Status**: Accepted
**Date**: November 4, 2025

---

### ADR-004: Skip Demo Site Builder for MVP (Phase 1)

**Decision**: Focus on scraping + analysis + email for MVP. Defer demo sites to Phase 2.

**Rationale**:
- User prioritized: "Week 1: scraping/analysis/email first"
- Demo builder is complex (code gen + QA + deployment)
- Can validate outreach approach without demos
- Add demos in Phase 2 if reply rates warrant investment

**Status**: Accepted
**Date**: November 4, 2025

---

## 4. Updated Service Catalog (Prioritized)

### Phase 1 Services (MVP - Today)
1. **Multi-Source Scraping Orchestrator** ✅ Priority 1
   - Google Maps scraper
   - Craigslist scraper (existing)
   - Job queue via Celery

2. **AI Council Orchestrator** ✅ Priority 1
   - Semantic router
   - Multi-model execution
   - LLM-as-Judge
   - DeepEval integration

3. **Website Analyzer** ✅ Priority 1
   - Playwright crawler
   - AI Council analysis (6 models)
   - Improvement plan generation

4. **Email Personalization** ✅ Priority 1
   - Template engine
   - AI Council copywriting
   - Gmail API integration

5. **Feedback Loop** ✅ Priority 1
   - Outcome tracking
   - AI-GYM correlation
   - Weekly optimization

### Phase 2 Services (Week 2-3)
6. **Demo Builder Service** ⏳ Phase 2
   - Code generation (Qwen2.5-Coder)
   - Vercel deployment
   - QA automation

7. **Video Automation** ⏳ Phase 2
   - Script generation
   - ElevenLabs voiceover
   - Playwright screen recording

### Phase 3 Services (Week 4+)
8. **Conversation Agent** ⏳ Phase 3
   - Reply detection (Gmail)
   - Sentiment analysis
   - AI response generation

9. **Analytics Engine** ⏳ Phase 3
   - AI-GYM dashboards
   - Campaign analytics
   - ROI tracking

---

## 5. Integration with Codex Documents

| Codex Document | Enhancement in This Doc | Status |
|----------------|-------------------------|--------|
| Software_Architecture_Blueprint.md | Added ML router, LLM-as-Judge, simplified deployment | ✅ Enhanced |
| System_Design_Pivot.md | Added semantic routing, DeepEval integration | ✅ Enhanced |
| Epic_Roadmap.md | Reprioritized (scraping/analysis/email first) | ✅ Updated |
| UX_UI_Strategy.md | No changes (still valid) | ✅ Use as-is |
| Claude_Agent_Playbook.md | Added LLM-as-Judge patterns, routing strategy | ✅ Enhanced |
| Data_and_API_Spec.md | Added AI-GYM metrics columns, feedback tables | ✅ Enhanced |
| QA_and_Risk_Plan.md | No changes (still valid) | ✅ Use as-is |

---

## 6. Next Steps

1. **Review this document** with team to align on enhancements
2. **Read ML research** in `00_ML_STRATEGY_RESEARCH.md` for detailed rationale
3. **Implement semantic router** as first task (critical for cost control)
4. **Set up OpenRouter account** and test API access
5. **Follow MVP Quick Start Guide** in `05_MVP_QUICK_START_GUIDE.md`

---

## 7. Open Questions

1. **Vector DB**: Still need to decide on Pinecone vs Weaviate (deferred to Phase 3)
2. **n8n**: Do we want workflow orchestration or keep Celery? (Recommend Celery for simplicity)
3. **Light Mode**: Priority for UI? (User mentioned but not critical)
4. **LinkedIn Scraping**: Add in Phase 1 or Phase 2? (Recommend Phase 2)

---

**Document Owner**: AI/ML Lead
**Last Updated**: November 4, 2025
**Status**: Draft for Review
**Related Docs**:
- `/Codex/Software_Architecture_Blueprint.md` (strategic foundation)
- `00_ML_STRATEGY_RESEARCH.md` (research findings)
- `02_ML_STRATEGY_AND_EVALUATION.md` (detailed ML specs)
- `05_MVP_QUICK_START_GUIDE.md` (implementation guide)
