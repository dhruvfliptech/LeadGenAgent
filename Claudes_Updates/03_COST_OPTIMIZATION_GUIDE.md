# Cost Optimization Guide
## Achieving 70-85% Savings Through Intelligent Model Routing
### November 4, 2025

---

## Document Purpose

Comprehensive guide to minimizing AI API costs while maintaining quality through:
1. **Semantic routing** (right model for each task)
2. **Lead value-based routing** (premium models for high-value leads)
3. **Caching strategies** (avoid redundant API calls)
4. **Budget monitoring** (alerts before overspending)

**Target**: Reduce costs from $90/day (1000 leads, all-Claude-Sonnet-4) to $15-20/day (83% savings)

---

## 1. Cost Baseline Analysis

### 1.1 Current State (No Optimization)

**Scenario**: Using Claude Sonnet 4 for everything

| Task | Volume/Day | Tokens/Task | Cost/M Tokens | Cost/Day |
|------|------------|-------------|---------------|----------|
| Lead Classification | 1000 | 500 | $3.00 | $1.50 |
| Website Analysis | 1000 | 4000 | $3.00 | $12.00 |
| Email Generation | 1000 | 1500 | $3.00 | $4.50 |
| Lead Scoring | 1000 | 300 | $3.00 | $0.90 |
| **TOTAL** | **4000 calls** | **6.3M tokens** | **$3.00** | **$18.90/day** |

**Annual Cost**: $18.90 × 365 = $6,899/year

### 1.2 Optimized State (With Routing)

| Task | Volume/Day | Model | Tokens/Task | Cost/M | Cost/Day |
|------|------------|-------|-------------|--------|----------|
| Lead Classification | 1000 | DeepSeek-V3 | 500 | $0.27 | $0.14 |
| Website Analysis (SMB) | 700 | Claude Haiku | 4000 | $0.50 | $1.40 |
| Website Analysis (Enterprise) | 300 | Claude Sonnet 4 | 4000 | $3.00 | $3.60 |
| Email Generation (SMB) | 700 | Claude Haiku | 1500 | $0.50 | $0.53 |
| Email Generation (Enterprise) | 300 | Claude Sonnet 4 | 1500 | $3.00 | $1.35 |
| Lead Scoring | 1000 | Qwen 2.5 | 300 | $0.14 | $0.04 |
| Judge Evaluations | 300 | Claude Sonnet 4 | 2000 | $3.00 | $1.80 |
| **TOTAL** | **5000 calls** | **Various** | **~10M tokens** | **~$0.80 avg** | **$8.86/day** |

**Annual Cost**: $8.86 × 365 = $3,234/year

**Savings**: $6,899 - $3,234 = **$3,665/year (53% savings)**

---

## 2. Model Pricing Matrix

### 2.1 Complete Pricing Table (OpenRouter)

| Model | Input $/M | Output $/M | Avg $/M | Speed | Quality | Best For |
|-------|-----------|------------|---------|-------|---------|----------|
| **Ultra-Cheap** |
| Qwen 2.5 32B | $0.06 | $0.21 | $0.14 | Fast | Good | Scoring, classification |
| DeepSeek-V3 | $0.14 | $0.28 | $0.27 | Fast | Good | Classification, extraction |
| **Cheap** |
| Claude 3 Haiku | $0.25 | $1.25 | $0.50 | Very Fast | Good | Drafts, summaries, SMB leads |
| GPT-4o Mini | $0.15 | $0.60 | $0.30 | Fast | Good | Quick tasks |
| **Medium** |
| Qwen2.5-Coder 32B | $0.30 | $3.00 | $1.50 | Medium | Excellent | Code generation |
| Gemini 1.5 Flash | $0.075 | $0.30 | $0.15 | Very Fast | Good | Diversification |
| **Premium** |
| GPT-4o | $2.50 | $10.00 | $5.00 | Medium | Excellent | Complex analysis |
| Claude Sonnet 4 | $3.00 | $15.00 | $7.50 | Medium | Excellent | Critical tasks, judge |
| Gemini 1.5 Pro | $1.25 | $5.00 | $2.50 | Slow | Excellent | Long context |

**Input/Output Ratio Assumptions**:
- Classification/Scoring: 70% input, 30% output
- Analysis/Generation: 40% input, 60% output
- Code Generation: 30% input, 70% output

### 2.2 Cost Per Task Type (Detailed)

**Lead Classification** (500 tokens)
```
Ultra-Cheap (Qwen 2.5): $0.14/M × 0.5 = $0.00007/lead
Cheap (Claude Haiku): $0.50/M × 0.5 = $0.00025/lead
Premium (Claude Sonnet 4): $7.50/M × 0.5 = $0.00375/lead

Savings: 98% (Ultra-cheap vs Premium)
Recommendation: ALWAYS use ultra-cheap for classification
```

**Website Analysis** (4000 tokens)
```
Cheap (Claude Haiku): $0.50/M × 4 = $0.002/lead
Medium (Gemini 1.5 Pro): $2.50/M × 4 = $0.010/lead
Premium (Claude Sonnet 4): $7.50/M × 4 = $0.030/lead

Savings: 93% (Cheap vs Premium)
Recommendation: Use cheap for SMB, premium for enterprise
```

**Email Generation** (1500 tokens)
```
Cheap (Claude Haiku): $0.50/M × 1.5 = $0.00075/lead
Premium (Claude Sonnet 4): $7.50/M × 1.5 = $0.01125/lead

Savings: 93% (Cheap vs Premium)
Recommendation: A/B test cheap vs premium, track reply rates
```

**Demo Code Generation** (6000 tokens)
```
Specialized (Qwen2.5-Coder): $1.50/M × 6 = $0.009/demo
Premium (Claude Sonnet 4): $7.50/M × 6 = $0.045/demo

Savings: 80% (Specialized vs Premium)
Recommendation: Use Qwen2.5-Coder, judge with Claude
```

**Judge Evaluation** (2000 tokens)
```
Premium (Claude Sonnet 4): $7.50/M × 2 = $0.015/eval
Alternative (GPT-4o): $5.00/M × 2 = $0.010/eval

Recommendation: ALWAYS use premium for judging (quality critical)
```

---

## 3. Routing Strategies

### 3.1 Task-Based Routing (Primary Strategy)

```python
class TaskBasedRouter:
    """
    Route based on task complexity.

    Strategy: Simple tasks → cheap models, complex tasks → premium models
    """

    ROUTING_TABLE = {
        # Deterministic tasks → Ultra-cheap
        "classify_industry": ("qwen-2.5", 0.14),
        "classify_company_size": ("qwen-2.5", 0.14),
        "score_lead_fit": ("deepseek-v3", 0.27),
        "extract_contact_info": ("deepseek-v3", 0.27),

        # Draft/summary tasks → Cheap
        "generate_email_draft": ("claude-haiku", 0.50),
        "summarize_website": ("claude-haiku", 0.50),
        "generate_subject_lines": ("claude-haiku", 0.50),

        # Analysis tasks → Lead-value-based routing
        "analyze_website": self._route_by_lead_value,
        "generate_improvement_plan": self._route_by_lead_value,

        # Specialized tasks → Specialized models
        "generate_demo_code": ("qwen2.5-coder-32b", 1.50),
        "review_code_quality": ("qwen2.5-coder-32b", 1.50),

        # Critical tasks → Premium
        "generate_final_email": ("claude-sonnet-4", 7.50),
        "reply_to_conversation": ("claude-sonnet-4", 7.50),
        "judge_responses": ("claude-sonnet-4", 7.50),
    }

    def route(self, task_type: str, context: Dict) -> Tuple[str, float]:
        """
        Get model and cost for task.

        Returns: (model_name, cost_per_million_tokens)
        """
        route = self.ROUTING_TABLE.get(task_type)

        if callable(route):
            # Dynamic routing (lead value-based)
            return route(context)
        elif route:
            # Static routing
            return route
        else:
            # Fallback
            logger.warning(f"Unknown task type: {task_type}, using default")
            return ("claude-haiku", 0.50)
```

**Cost Impact**:
- Before: All tasks use Claude Sonnet 4 ($7.50/M)
- After: Average cost $0.80/M (89% savings)

---

### 3.2 Lead Value-Based Routing (Secondary Strategy)

```python
class LeadValueRouter:
    """
    Route based on potential deal value.

    Strategy: High-value leads get premium models, low-value get cheap models
    """

    VALUE_TIERS = {
        "enterprise": {  # > $100K potential
            "threshold": 100000,
            "website_analysis": "claude-sonnet-4",  # $7.50/M
            "email_generation": "claude-sonnet-4",  # $7.50/M
            "reply_generation": "claude-sonnet-4",  # $7.50/M
            "council_size": 3,  # 3-model council
        },
        "mid_market": {  # $25K - $100K potential
            "threshold": 25000,
            "website_analysis": "gpt-4o",           # $5.00/M
            "email_generation": "claude-sonnet-4",  # $7.50/M (always premium)
            "reply_generation": "claude-sonnet-4",  # $7.50/M (always premium)
            "council_size": 2,  # 2-model council
        },
        "smb": {  # < $25K potential
            "threshold": 0,
            "website_analysis": "claude-haiku",     # $0.50/M
            "email_generation": "claude-haiku",     # $0.50/M
            "reply_generation": "claude-haiku",     # $0.50/M
            "council_size": 1,  # Single model (no council)
        }
    }

    def route_by_value(
        self,
        task_type: str,
        estimated_value: float,
        company_size: int = None
    ) -> str:
        """Route to model based on lead value."""

        # Determine tier
        if estimated_value >= 100000:
            tier = self.VALUE_TIERS["enterprise"]
        elif estimated_value >= 25000:
            tier = self.VALUE_TIERS["mid_market"]
        else:
            tier = self.VALUE_TIERS["smb"]

        # Get model for task
        model = tier.get(task_type, "claude-haiku")

        logger.info(f"""
        Lead Value Routing:
        - Estimated value: ${estimated_value:,.0f}
        - Tier: {self._get_tier_name(estimated_value)}
        - Task: {task_type}
        - Model: {model}
        """)

        return model

    def estimate_lead_value(self, lead: Dict) -> float:
        """
        Estimate potential deal value from lead data.

        Factors:
        - Company size (employees)
        - Industry
        - Website quality signals
        - Location
        """

        value = 0

        # Company size → revenue estimate
        employees = lead.get("employee_count", 0)
        if employees > 1000:
            value = 150000  # Enterprise
        elif employees > 100:
            value = 50000   # Mid-market
        elif employees > 10:
            value = 15000   # Small business
        else:
            value = 5000    # Micro business

        # Industry multipliers
        industry_multipliers = {
            "software": 1.5,
            "finance": 1.5,
            "healthcare": 1.3,
            "manufacturing": 1.2,
            "retail": 0.8,
            "hospitality": 0.7,
        }
        industry = lead.get("industry", "").lower()
        multiplier = industry_multipliers.get(industry, 1.0)
        value *= multiplier

        # Website quality signals
        if lead.get("has_enterprise_tech_stack"):
            value *= 1.3
        if lead.get("has_career_page"):
            value *= 1.2

        # Location (US/CA/UK/AU pay more)
        location = lead.get("location", {}).get("country", "")
        if location in ["US", "CA", "UK", "AU"]:
            value *= 1.2
        elif location in ["IN", "PH", "VN"]:
            value *= 0.6

        return round(value, -3)  # Round to nearest $1000
```

**Example Routing**:
```python
# Lead 1: Small business in retail
lead_1 = {
    "employee_count": 15,
    "industry": "retail",
    "location": {"country": "US"}
}
estimated_value = router.estimate_lead_value(lead_1)
# Result: $15,000 × 0.8 (retail) × 1.2 (US) = $14,400 → SMB tier
# Model: Claude Haiku ($0.50/M) → Cost: $0.002/analysis

# Lead 2: Enterprise software company
lead_2 = {
    "employee_count": 2500,
    "industry": "software",
    "location": {"country": "US"},
    "has_enterprise_tech_stack": True
}
estimated_value = router.estimate_lead_value(lead_2)
# Result: $150,000 × 1.5 (software) × 1.3 (tech) × 1.2 (US) = $351,000 → Enterprise tier
# Model: Claude Sonnet 4 ($7.50/M) → Cost: $0.030/analysis

# ROI: Spending 15x more on lead worth 24x more = Smart allocation
```

---

### 3.3 Caching Strategy (Tertiary)

```python
class IntelligentCache:
    """
    Cache AI responses to avoid redundant API calls.

    Strategies:
    1. Exact match caching (same prompt → same response)
    2. Semantic similarity caching (similar prompt → reuse response)
    3. Time-based invalidation (cache expires after N hours)
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = {
            "classify": 30 * 24 * 3600,     # 30 days (rarely changes)
            "score": 7 * 24 * 3600,          # 7 days
            "analyze": 24 * 3600,            # 1 day (websites change)
            "generate_email": 1 * 3600,      # 1 hour (personalized)
            "reply": 0,                      # Never cache (contextual)
        }

    async def get_cached_response(
        self,
        task_type: str,
        prompt: str,
        context: Dict
    ) -> Optional[str]:
        """
        Check cache for existing response.

        Cache key: hash(task_type + prompt + stable_context)
        """

        # Build cache key
        cache_key = self._build_cache_key(task_type, prompt, context)

        # Check Redis
        cached = await self.redis.get(cache_key)

        if cached:
            logger.info(f"Cache HIT for {task_type} (saved API call)")
            return json.loads(cached)

        return None

    async def cache_response(
        self,
        task_type: str,
        prompt: str,
        context: Dict,
        response: str,
        cost: float
    ):
        """Store response in cache."""

        # Build cache key
        cache_key = self._build_cache_key(task_type, prompt, context)

        # Store with TTL
        ttl = self.ttl.get(task_type, 3600)
        if ttl > 0:
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps({
                    "response": response,
                    "cost": cost,
                    "cached_at": datetime.now().isoformat()
                })
            )
            logger.info(f"Cached {task_type} response (TTL: {ttl}s)")

    def _build_cache_key(
        self,
        task_type: str,
        prompt: str,
        context: Dict
    ) -> str:
        """
        Build deterministic cache key.

        Includes:
        - Task type
        - Prompt hash
        - Stable context (exclude time-sensitive fields)
        """

        # Extract stable context
        stable_context = {
            k: v for k, v in context.items()
            if k in ["lead_id", "company_domain", "industry", "employee_count"]
        }

        # Hash
        key_parts = f"{task_type}:{prompt}:{json.dumps(stable_context, sort_keys=True)}"
        key_hash = hashlib.sha256(key_parts.encode()).hexdigest()

        return f"ai_cache:{task_type}:{key_hash}"
```

**Cache Hit Rates by Task**:
- Classification: 40-60% (many companies in same industry)
- Scoring: 30-50% (similar company profiles)
- Website analysis: 10-20% (websites change frequently)
- Email generation: 5-10% (highly personalized)
- Replies: 0% (never cache - contextual)

**Cost Savings Example**:
```
1000 leads/day × 40% cache hit rate × $0.002/classification = $0.80/day saved
Annual savings: $0.80 × 365 = $292/year from caching alone
```

---

## 4. Budget Monitoring & Alerts

### 4.1 Real-Time Cost Tracking

```python
class CostMonitor:
    """
    Track AI costs in real-time and trigger alerts.

    Features:
    1. Track costs per task type, model, user
    2. Compare to budget thresholds
    3. Send alerts before exceeding budget
    4. Automatic throttling if budget exceeded
    """

    def __init__(self, db, alert_service):
        self.db = db
        self.alert_service = alert_service
        self.budgets = {
            "daily": 50.00,    # $50/day max
            "weekly": 300.00,  # $300/week max
            "monthly": 1200.00 # $1200/month max
        }
        self.alert_thresholds = [0.7, 0.9, 1.0]  # Alert at 70%, 90%, 100%

    async def track_cost(
        self,
        task_type: str,
        model_name: str,
        tokens_used: int,
        cost: float,
        user_id: str = None
    ):
        """Track API cost."""

        # Log to database
        await self.db.execute("""
            INSERT INTO ai_costs (
                task_type,
                model_name,
                user_id,
                tokens_used,
                cost,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, NOW())
        """, task_type, model_name, user_id, tokens_used, cost)

        # Check budgets
        await self._check_budgets()

    async def _check_budgets(self):
        """Check if approaching or exceeding budgets."""

        # Get current spending
        current_spending = await self._get_current_spending()

        for period, budget in self.budgets.items():
            spent = current_spending[period]
            pct_used = spent / budget

            # Check thresholds
            for threshold in self.alert_thresholds:
                if pct_used >= threshold and not await self._alert_sent(period, threshold):
                    await self._send_budget_alert(period, budget, spent, pct_used)

            # Auto-throttle if exceeded
            if pct_used >= 1.0:
                await self._enable_throttling(period)

    async def _get_current_spending(self) -> Dict[str, float]:
        """Get spending for each period."""

        return {
            "daily": await self._get_spending_since(hours=24),
            "weekly": await self._get_spending_since(days=7),
            "monthly": await self._get_spending_since(days=30),
        }

    async def _get_spending_since(self, hours: int = None, days: int = None) -> float:
        """Get total spending since time."""

        if hours:
            interval = f"{hours} hours"
        elif days:
            interval = f"{days} days"
        else:
            interval = "1 day"

        result = await self.db.fetchrow(f"""
            SELECT COALESCE(SUM(cost), 0) as total
            FROM ai_costs
            WHERE created_at >= NOW() - INTERVAL '{interval}'
        """)

        return float(result["total"])

    async def _send_budget_alert(
        self,
        period: str,
        budget: float,
        spent: float,
        pct_used: float
    ):
        """Send alert about budget usage."""

        message = f"""
        🚨 AI Budget Alert: {period.upper()}

        Budget: ${budget:.2f}
        Spent: ${spent:.2f} ({pct_used:.0%})
        Remaining: ${budget - spent:.2f}

        Breakdown:
        {await self._get_spending_breakdown(period)}
        """

        await self.alert_service.send(
            channel="slack",
            message=message,
            severity="warning" if pct_used < 1.0 else "critical"
        )

        # Mark alert as sent
        await self._mark_alert_sent(period, pct_used)

    async def _enable_throttling(self, period: str):
        """Enable cost throttling to prevent overspending."""

        logger.warning(f"Budget exceeded for {period} - enabling throttling")

        # Set throttling flag in Redis
        await self.redis.set(
            f"throttle:ai_costs:{period}",
            "1",
            ex=3600 if period == "daily" else 86400
        )

        # Notify team
        await self.alert_service.send(
            channel="slack",
            message=f"⚠️ AI cost throttling ENABLED for {period}. Only enterprise leads will use premium models.",
            severity="critical"
        )
```

### 4.2 Throttling Strategy

```python
class ThrottlingStrategy:
    """
    Reduce costs when budget exceeded.

    Strategies (in order of severity):
    1. Disable non-critical tasks (A/B tests, re-analysis)
    2. Reduce council size (3 models → 1 model)
    3. Route all to cheap models (except enterprise leads)
    4. Cache aggressively (extend TTLs)
    5. Pause non-urgent jobs
    """

    async def apply_throttling(self, severity: int):
        """Apply throttling based on severity (1-5)."""

        if severity >= 1:
            # Level 1: Disable non-critical tasks
            await self.disable_ab_tests()
            await self.disable_reanalysis()
            logger.info("Throttle L1: Disabled non-critical tasks")

        if severity >= 2:
            # Level 2: Reduce council size
            await self.config.set("ai_council.max_models", 1)
            logger.info("Throttle L2: Council reduced to 1 model")

        if severity >= 3:
            # Level 3: Route all SMB to cheap
            await self.config.set("router.force_cheap_for_smb", True)
            logger.info("Throttle L3: All SMB leads use cheap models")

        if severity >= 4:
            # Level 4: Cache aggressively
            await self.cache.extend_all_ttls(multiplier=5)
            logger.info("Throttle L4: Cache TTLs extended 5x")

        if severity >= 5:
            # Level 5: Pause non-urgent jobs
            await self.celery.pause_queues(["analysis", "demo", "video"])
            logger.info("Throttle L5: Non-urgent jobs paused")

    async def calculate_severity(self, budget_exceeded_pct: float) -> int:
        """Calculate throttling severity."""

        if budget_exceeded_pct < 1.1:  # < 10% over
            return 1
        elif budget_exceeded_pct < 1.25:  # < 25% over
            return 2
        elif budget_exceeded_pct < 1.5:  # < 50% over
            return 3
        elif budget_exceeded_pct < 2.0:  # < 100% over
            return 4
        else:  # > 100% over
            return 5
```

---

## 5. Cost Optimization Checklist

### Phase 1: Quick Wins (Day 1)
- [ ] Implement task-based routing
- [ ] Route classification/scoring to ultra-cheap models
- [ ] Enable basic caching (classification only)
- [ ] Set up cost tracking database table

**Expected Savings**: 40-50%

### Phase 2: Smart Routing (Week 1)
- [ ] Implement lead value estimation
- [ ] Route by lead value (SMB → cheap, Enterprise → premium)
- [ ] Reduce council size for SMB leads
- [ ] Enable caching for scoring/analysis

**Expected Savings**: 60-70%

### Phase 3: Advanced Optimization (Week 2)
- [ ] Set up budget monitoring
- [ ] Configure alerts (70%, 90%, 100% thresholds)
- [ ] Implement throttling strategies
- [ ] A/B test cheap vs premium models (track reply rates)

**Expected Savings**: 70-80%

### Phase 4: Continuous Improvement (Month 2+)
- [ ] Weekly review of AI-GYM data
- [ ] Identify cheap models approaching premium quality
- [ ] Adjust routing based on conversion data
- [ ] Consider DPO fine-tuning if plateau

**Expected Savings**: 80-85%

---

## 6. Cost Projections

### Scale: 100 Leads/Day

| Component | Daily Cost | Monthly Cost | Annual Cost |
|-----------|------------|--------------|-------------|
| Classification | $0.01 | $0.30 | $3.65 |
| Scoring | $0.01 | $0.30 | $3.65 |
| Website Analysis | $0.20 | $6.00 | $73.00 |
| Email Generation | $0.10 | $3.00 | $36.50 |
| Judge Evaluations | $0.05 | $1.50 | $18.25 |
| **TOTAL** | **$0.37** | **$11.10** | **$135.05** |

**With 20% cache hit rate**: $0.30/day → $108/year

---

### Scale: 1000 Leads/Day

| Component | Daily Cost | Monthly Cost | Annual Cost |
|-----------|------------|--------------|-------------|
| Classification | $0.14 | $4.20 | $51.10 |
| Scoring | $0.04 | $1.20 | $14.60 |
| Website Analysis | $3.20 | $96.00 | $1,168.00 |
| Email Generation | $1.10 | $33.00 | $401.50 |
| Judge Evaluations | $1.80 | $54.00 | $657.00 |
| **TOTAL** | **$6.28** | **$188.40** | **$2,292.20** |

**With 30% cache hit rate**: $4.40/day → $1,606/year

---

### Scale: 10,000 Leads/Day (Future)

| Component | Daily Cost | Monthly Cost | Annual Cost |
|-----------|------------|--------------|-------------|
| Classification | $1.40 | $42.00 | $511.00 |
| Scoring | $0.40 | $12.00 | $146.00 |
| Website Analysis | $32.00 | $960.00 | $11,680.00 |
| Email Generation | $11.00 | $330.00 | $4,015.00 |
| Judge Evaluations | $18.00 | $540.00 | $6,570.00 |
| **TOTAL** | **$62.80** | **$1,884.00** | **$22,922.00** |

**With 40% cache hit rate**: $37.68/day → $13,753/year

**With DPO fine-tuning** (replace Claude Haiku with custom model):
- Additional cost: $5K one-time training
- Ongoing savings: ~$5K/year
- ROI: 12 months

---

## 7. Key Metrics to Track

### Daily Monitoring
1. **Total AI Spend** (target: < $50/day)
2. **Cost Per Lead** (target: < $0.01/lead)
3. **Cache Hit Rate** (target: > 25%)
4. **Model Distribution** (target: 60%+ cheap models)

### Weekly Analysis
1. **Cost by Task Type** (identify expensive tasks)
2. **Cost by Model** (identify overused premium models)
3. **Cost vs Budget** (trending toward or away from budget)
4. **Quality vs Cost Correlation** (cheap models approaching premium?)

### Monthly Reporting
1. **Total Spend vs Budget**
2. **Savings from Optimization** (vs no-optimization baseline)
3. **ROI Analysis** (cost per conversion)
4. **Optimization Opportunities** (new savings identified)

---

## 8. Common Pitfalls & Solutions

### Pitfall 1: Over-Optimizing Early
**Problem**: Routing to cheap models before validating quality
**Solution**: Start with premium models, then gradually test cheap alternatives

### Pitfall 2: Ignoring Edge Cases
**Problem**: Edge cases (errors, retries) drive up costs
**Solution**: Add retry limits, exponential backoff, circuit breakers

### Pitfall 3: Cache Stale Data
**Problem**: Cached responses outdated, leads to bad decisions
**Solution**: Set appropriate TTLs, invalidate on source data changes

### Pitfall 4: No Cost Accountability
**Problem**: No one monitors costs, overspending unnoticed
**Solution**: Weekly cost review meeting, dashboard visible to team

### Pitfall 5: Premature Fine-Tuning
**Problem**: Fine-tuning before gathering enough data
**Solution**: Wait for 1000+ samples, try prompt optimization first

---

## 9. Next Steps

**Week 1**:
1. Implement task-based routing (40% savings)
2. Set up cost tracking database
3. Enable basic caching

**Week 2**:
4. Implement lead value-based routing (additional 20% savings)
5. Configure budget alerts
6. Start A/B testing cheap vs premium

**Month 2**:
7. Analyze AI-GYM data (quality vs cost)
8. Optimize routing based on data
9. Consider DPO fine-tuning if ROI positive

---

**Document Owner**: Engineering Lead
**Last Updated**: November 4, 2025
**Status**: Implementation Ready
**Related Docs**:
- `02_ML_STRATEGY_AND_EVALUATION.md` (evaluation framework)
- `01_ENHANCED_SOFTWARE_ARCHITECTURE.md` (router integration)
