# ML Strategy & Evaluation Framework
## LLM-as-Judge + DeepEval + AI-GYM Implementation Guide
### November 4, 2025

---

## Document Purpose

Comprehensive ML strategy for achieving AI-GYM optimization goals using:
1. **LLM-as-Judge** (Claude Sonnet 4 as evaluator)
2. **DeepEval** (automated metrics framework)
3. **Feedback Loop** (business outcomes → model optimization)
4. **Semantic Router** (cost-optimized model selection)

**Research Foundation**: Based on comprehensive research in `00_ML_STRATEGY_RESEARCH.md`

**Key Decision**: Skip RL-Factory (wrong use case) → Use LLM-as-Judge (industry standard)

---

## 1. ML Strategy Overview

### 1.1 Why LLM-as-Judge (Not RL-Factory)

**RL-Factory Analysis**:
```
❌ Wrong Use Case:
- Designed for: Tool-calling agents (calculator, search, API calls)
- Our need: Content generation (emails, analysis, copy)
- Mismatch: RL optimizes action selection, not content quality

✅ LLM-as-Judge Benefits:
- Industry standard (Anthropic, OpenAI, Google)
- Works for content generation
- No training required (zero-shot evaluation)
- Can use ANY LLM as judge
- Proven at scale (millions of evals)
```

**Research References**:
- Anthropic: Constitutional AI uses Claude as judge
- OpenAI: GPT-4 evaluates GPT-3.5 outputs
- Google: PaLM judges PaLM outputs
- MIT Study: LLM-as-Judge achieves 85% agreement with human experts

### 1.2 Three-Tier Evaluation Strategy

```
Tier 1: Automated Metrics (DeepEval)
├─ Faithfulness (0-1)
├─ Relevance (0-1)
├─ Coherence (0-1)
└─ Conciseness (0-1)
Run on: 100% of outputs
Cost: Free (local computation)
Latency: <100ms

Tier 2: LLM-as-Judge (Claude Sonnet 4)
├─ Multi-response selection (AI Council votes)
├─ Quality scoring (0-100)
└─ Reasoning extraction
Run on: Critical tasks only (website analysis, email variants)
Cost: $3/M tokens (~$0.005 per eval)
Latency: 1-2 seconds

Tier 3: Business Outcomes (Feedback Loop)
├─ Email open rate
├─ Email click rate
├─ Email reply rate
└─ Meeting conversion rate
Run on: 100% of emails (tracked automatically)
Cost: Free (event tracking)
Latency: 24-72 hours (wait for user action)
```

**Why Three Tiers**:
1. **Tier 1** (Automated): Fast feedback, no cost, correlation signal
2. **Tier 2** (Judge): Human-like quality assessment, moderate cost
3. **Tier 3** (Outcomes): Ground truth, but delayed

**Correlation Strategy**: Track which Tier 1/2 scores predict Tier 3 outcomes → optimize routing

---

## 2. LLM-as-Judge Implementation

### 2.1 Judge Architecture

```python
class LLMJudge:
    """
    Claude Sonnet 4 as evaluation judge.

    Responsibilities:
    1. Select winner from AI Council responses
    2. Score quality (0-100)
    3. Provide reasoning
    4. Extract improvement suggestions
    """

    def __init__(self):
        self.model = ClaudeModel("claude-sonnet-4")
        self.evaluation_cache = {}  # Cache evaluations (24 hours)

    async def judge_responses(
        self,
        task_type: str,
        original_prompt: str,
        responses: List[ModelResponse],
        context: Dict,
        evaluation_criteria: List[str] = None
    ) -> JudgeResult:
        """
        Evaluate multiple responses and select winner.

        Args:
            task_type: Type of task (website_analysis, email_generation, etc.)
            original_prompt: The prompt sent to models
            responses: List of responses from AI Council
            context: Additional context (lead data, etc.)
            evaluation_criteria: Custom criteria (uses defaults if None)

        Returns:
            JudgeResult with winner, scores, reasoning
        """

        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            task_type=task_type,
            original_prompt=original_prompt,
            responses=responses,
            evaluation_criteria=evaluation_criteria or self._default_criteria(task_type)
        )

        # Call Claude
        response = await self.model.generate(
            prompt=judge_prompt,
            temperature=0.2,  # Lower temperature for consistent judging
            max_tokens=2000
        )

        # Parse structured output
        result = self._parse_judge_response(response)

        # Cache evaluation
        cache_key = self._cache_key(task_type, responses)
        self.evaluation_cache[cache_key] = result

        return result

    def _default_criteria(self, task_type: str) -> List[str]:
        """Get default evaluation criteria for task type."""

        criteria_map = {
            "website_analysis": [
                "Specificity: Concrete, actionable insights (not generic)",
                "Evidence-based: References specific site elements",
                "Prioritization: Orders issues by impact",
                "Clarity: Easy to understand for non-technical stakeholders",
                "Completeness: Covers UX, content, and conversion factors"
            ],
            "email_generation": [
                "Personalization: References specific lead insights",
                "Value proposition: Clear, compelling benefit",
                "Tone: Professional yet approachable",
                "Call-to-action: Clear next step",
                "Brevity: Respects recipient's time (<200 words)"
            ],
            "demo_code": [
                "Code quality: Clean, readable, maintainable",
                "Functionality: Meets requirements",
                "Best practices: Follows framework conventions",
                "Performance: Optimized rendering",
                "Accessibility: WCAG AA compliance"
            ],
            "conversation_reply": [
                "Context awareness: References previous messages",
                "Empathy: Acknowledges sender's concerns",
                "Problem-solving: Provides clear path forward",
                "Professionalism: Appropriate tone",
                "Conciseness: Direct and focused"
            ]
        }

        return criteria_map.get(task_type, [
            "Relevance: Addresses the task requirements",
            "Quality: High-quality output",
            "Clarity: Easy to understand",
            "Completeness: Thorough and comprehensive"
        ])

    def _build_judge_prompt(
        self,
        task_type: str,
        original_prompt: str,
        responses: List[ModelResponse],
        evaluation_criteria: List[str]
    ) -> str:
        """Build prompt for judge evaluation."""

        # Blind the responses (hide model names to avoid bias)
        blinded_responses = "\n\n".join([
            f"=== Response {i+1} ===\n{r.text}"
            for i, r in enumerate(responses)
        ])

        prompt = f"""You are an expert evaluator assessing {len(responses)} AI-generated responses.

TASK TYPE: {task_type}

ORIGINAL TASK:
{original_prompt}

EVALUATION CRITERIA:
{self._format_criteria(evaluation_criteria)}

RESPONSES TO EVALUATE:
{blinded_responses}

INSTRUCTIONS:
1. Evaluate each response against the criteria above
2. Score each criterion (0-10) for each response
3. Calculate total score (sum of all criteria)
4. Select the winner (highest total score)
5. Provide reasoning explaining your decision

OUTPUT FORMAT (JSON):
{{
    "evaluations": [
        {{
            "response_id": 1,
            "scores": {{"criterion_1": X, "criterion_2": Y, ...}},
            "total_score": XX,
            "strengths": ["..."],
            "weaknesses": ["..."]
        }},
        ...
    ],
    "winner": {{
        "response_id": 1,
        "rationale": "Explain why this response is best...",
        "margin": "How much better than second place (small/medium/large)"
    }},
    "general_observations": "Overall patterns across responses..."
}}

IMPORTANT:
- Be objective and evidence-based
- Focus on the criteria, not your personal preference
- If responses are very close, explain the tie-breaking factor
- Note any responses that failed to meet minimum requirements
"""

        return prompt

    def _format_criteria(self, criteria: List[str]) -> str:
        """Format criteria as numbered list."""
        return "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])

    def _parse_judge_response(self, response: str) -> JudgeResult:
        """Parse structured JSON response from judge."""

        try:
            data = json.loads(response)

            return JudgeResult(
                winner_id=data["winner"]["response_id"] - 1,  # Convert to 0-index
                winner_rationale=data["winner"]["rationale"],
                margin=data["winner"]["margin"],
                evaluations=[
                    EvaluationScores(
                        response_id=e["response_id"] - 1,
                        scores=e["scores"],
                        total_score=e["total_score"],
                        strengths=e["strengths"],
                        weaknesses=e["weaknesses"]
                    )
                    for e in data["evaluations"]
                ],
                general_observations=data["general_observations"]
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse judge response: {e}")
            # Fallback: pick first response
            return JudgeResult(
                winner_id=0,
                winner_rationale="Error parsing judge response - defaulting to first response",
                margin="unknown",
                evaluations=[],
                general_observations=""
            )

    def _cache_key(self, task_type: str, responses: List[ModelResponse]) -> str:
        """Generate cache key for evaluation."""
        response_hashes = [hashlib.md5(r.text.encode()).hexdigest()[:8] for r in responses]
        return f"{task_type}:{'-'.join(response_hashes)}"
```

**Integration Example**:
```python
# In AI Council
async def execute_task(self, task_type, prompt, context):
    # Get responses from multiple models
    responses = await self._query_council_members(task_type, prompt, context)

    # Judge selects winner
    judge_result = await self.judge.judge_responses(
        task_type=task_type,
        original_prompt=prompt,
        responses=responses,
        context=context
    )

    winner = responses[judge_result.winner_id]
    winner.judge_result = judge_result

    return winner
```

---

### 2.2 Judge Evaluation Patterns

**Pattern 1: Pairwise Comparison** (2 responses)
```python
# Best for: A/B testing email variants
responses = [
    await model_a.generate(prompt),
    await model_b.generate(prompt)
]

judge_result = await judge.judge_responses(
    task_type="email_generation",
    original_prompt=prompt,
    responses=responses,
    evaluation_criteria=[
        "Personalization depth",
        "Value proposition clarity",
        "Call-to-action strength"
    ]
)

# Log comparison for A/B test
await ab_test_service.log_variant_comparison(
    test_id=test_id,
    variant_a=responses[0],
    variant_b=responses[1],
    winner=judge_result.winner_id,
    margin=judge_result.margin
)
```

**Pattern 2: Multi-Model Council** (3-6 responses)
```python
# Best for: Critical tasks (website analysis, high-value leads)
council_models = ["claude-sonnet-4", "gpt-4o", "gemini-1.5-pro"]
responses = await asyncio.gather(*[
    self.models[m].generate(prompt)
    for m in council_models
])

judge_result = await judge.judge_responses(
    task_type="website_analysis",
    original_prompt=prompt,
    responses=responses
)

# Winner gets used, others discarded (cost of quality)
winner = responses[judge_result.winner_id]
```

**Pattern 3: Quality Gate** (Single response)
```python
# Best for: Validating auto-generated content before sending
response = await model.generate(prompt)

judge_result = await judge.judge_responses(
    task_type="conversation_reply",
    original_prompt=prompt,
    responses=[response],  # Single response
    evaluation_criteria=[
        "Professionalism (must score 8+)",
        "No inappropriate content",
        "Answers user's question"
    ]
)

if judge_result.evaluations[0].total_score < 24:  # 3 criteria × 8 minimum
    # Failed quality gate → send to human review
    await human_review_queue.add(response, reason="Low quality score")
else:
    # Passed → send automatically
    await email_service.send(response)
```

---

## 3. DeepEval Integration

### 3.1 DeepEval Framework Setup

```python
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    CoherenceMetric,
    ConcisenessMetric
)
from deepeval.test_case import LLMTestCase

class DeepEvalEvaluator:
    """
    Automated evaluation using DeepEval framework.

    Advantages:
    - Free (runs locally)
    - Fast (<100ms per eval)
    - Consistent (deterministic)
    - No API costs

    Limitations:
    - Lower correlation with human judgment vs LLM-as-Judge
    - Use as pre-filter, not final decision
    """

    def __init__(self):
        self.metrics = {
            "faithfulness": FaithfulnessMetric(threshold=0.7),
            "relevance": AnswerRelevancyMetric(threshold=0.7),
            "coherence": CoherenceMetric(threshold=0.7),
            "conciseness": ConcisenessMetric(threshold=0.7),
        }

    async def evaluate(
        self,
        task_type: str,
        input_prompt: str,
        output_text: str,
        context: Dict = None,
        retrieval_context: List[str] = None
    ) -> EvaluationMetrics:
        """
        Run automated evaluation metrics.

        Args:
            task_type: Type of task (determines which metrics to run)
            input_prompt: Original input
            output_text: Generated output
            context: Additional context for evaluation
            retrieval_context: Retrieved documents (for faithfulness check)

        Returns:
            EvaluationMetrics with scores for each metric
        """

        # Select metrics for task type
        metrics_to_run = self._select_metrics(task_type)

        # Create test case
        test_case = LLMTestCase(
            input=input_prompt,
            actual_output=output_text,
            retrieval_context=retrieval_context or []
        )

        # Run metrics
        scores = {}
        for metric_name in metrics_to_run:
            metric = self.metrics[metric_name]
            score = await self._run_metric(metric, test_case)
            scores[metric_name] = score

        # Calculate composite score
        composite = sum(scores.values()) / len(scores) if scores else 0.0

        return EvaluationMetrics(
            faithfulness=scores.get("faithfulness"),
            relevance=scores.get("relevance"),
            coherence=scores.get("coherence"),
            conciseness=scores.get("conciseness"),
            composite=composite,
            passed=composite >= 0.7  # Threshold
        )

    def _select_metrics(self, task_type: str) -> List[str]:
        """Select relevant metrics for task type."""

        metric_map = {
            "website_analysis": ["faithfulness", "relevance", "coherence"],
            "email_generation": ["relevance", "conciseness"],
            "demo_code": ["faithfulness", "coherence"],
            "conversation_reply": ["relevance", "coherence", "conciseness"],
            "summary": ["faithfulness", "conciseness"],
        }

        return metric_map.get(task_type, ["relevance", "coherence"])

    async def _run_metric(self, metric, test_case) -> float:
        """Run single metric and return score."""
        try:
            metric.measure(test_case)
            return metric.score
        except Exception as e:
            logger.warning(f"Metric evaluation failed: {e}")
            return 0.0
```

**Integration Example**:
```python
# In AI Council - run DeepEval before judge
async def execute_task(self, task_type, prompt, context):
    # Get response
    response = await model.generate(prompt)

    # Quick automated evaluation
    deepeval_metrics = await self.deepeval.evaluate(
        task_type=task_type,
        input_prompt=prompt,
        output_text=response.text,
        context=context
    )

    # If fails automated metrics, don't waste $ on judge
    if not deepeval_metrics.passed:
        logger.warning(f"Response failed DeepEval (score: {deepeval_metrics.composite:.2f})")
        # Retry with different model or send to human review
        return None

    # If passes, proceed to judge (for critical tasks)
    if task_type in ["website_analysis", "email_generation"]:
        judge_result = await self.judge.judge_responses(...)
        response.judge_result = judge_result

    response.deepeval_metrics = deepeval_metrics
    return response
```

**Cost Savings**:
- Without DeepEval: Judge every response → $0.005 × 1000 leads = $5/day
- With DeepEval: Filter 20% bad responses → $0.005 × 800 leads = $4/day (20% savings)

---

### 3.2 DeepEval Metrics Explained

**Faithfulness** (Factual Accuracy):
```python
# Checks: Does output contradict input/context?
# Example:
input_context = "Company has 50 employees"
good_output = "As a 50-person company, you likely need..."  # ✅ Faithful
bad_output = "As a Fortune 500 company, you likely need..."  # ❌ Not faithful

# Use for: Website analysis, summaries, data-driven content
```

**Relevance** (On-Topic):
```python
# Checks: Does output address the input question?
# Example:
input = "What are 3 UX improvements for this site?"
good_output = "1. Add clearer CTAs, 2. Improve navigation, 3. Faster load times"  # ✅ Relevant
bad_output = "Here's a history of UX design principles..."  # ❌ Not relevant

# Use for: All task types (universal quality signal)
```

**Coherence** (Logical Flow):
```python
# Checks: Is output well-structured and logical?
# Example:
good_output = "First, analyze the problem. Then, propose solutions. Finally, prioritize by impact."  # ✅ Coherent
bad_output = "Solutions include X. The problem is Y. Also, Z is important. First, consider A."  # ❌ Incoherent

# Use for: Long-form content (analysis, explanations)
```

**Conciseness** (No Fluff):
```python
# Checks: Is output direct and to-the-point?
# Example:
good_output = "Your site needs faster load times. Current: 8s, Target: 2s. Use image compression."  # ✅ Concise
bad_output = "As you may know, website performance is crucial in today's digital landscape..."  # ❌ Verbose

# Use for: Emails, summaries, quick answers
```

---

## 4. Feedback Loop & AI-GYM

### 4.1 Outcome Tracking System

```python
class OutcomeTracker:
    """
    Track business outcomes and correlate with AI performance.

    Flow:
    1. AI generates content → log to ai_gym_performance
    2. Content used (email sent, demo shown) → link event
    3. User action (open, click, reply) → update outcome
    4. Correlation job → connect AI quality → business outcome
    """

    async def log_ai_generation(
        self,
        task_type: str,
        lead_id: UUID,
        model_name: str,
        prompt: str,
        output: str,
        cost: float,
        duration: float,
        deepeval_metrics: EvaluationMetrics = None,
        judge_result: JudgeResult = None
    ) -> UUID:
        """
        Log AI generation event.

        Returns: ai_gym_performance record ID
        """

        record = await self.db.execute("""
            INSERT INTO ai_gym_performance (
                task_type,
                model_name,
                lead_id,
                cost,
                duration_seconds,
                faithfulness_score,
                relevance_score,
                coherence_score,
                conciseness_score,
                composite_score,
                judge_total_score,
                metadata,
                created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW()
            )
            RETURNING id
        """,
            task_type,
            model_name,
            lead_id,
            cost,
            duration,
            deepeval_metrics.faithfulness if deepeval_metrics else None,
            deepeval_metrics.relevance if deepeval_metrics else None,
            deepeval_metrics.coherence if deepeval_metrics else None,
            deepeval_metrics.conciseness if deepeval_metrics else None,
            deepeval_metrics.composite if deepeval_metrics else None,
            judge_result.evaluations[0].total_score if judge_result else None,
            {
                "prompt_hash": hashlib.md5(prompt.encode()).hexdigest(),
                "output_hash": hashlib.md5(output.encode()).hexdigest(),
                "judge_margin": judge_result.margin if judge_result else None,
            }
        )

        return record["id"]

    async def link_to_email(
        self,
        ai_gym_id: UUID,
        email_send_id: UUID
    ):
        """Link AI generation to email send event."""

        await self.db.execute("""
            UPDATE ai_gym_performance
            SET metadata = metadata || jsonb_build_object('email_send_id', $2)
            WHERE id = $1
        """, ai_gym_id, str(email_send_id))

    async def update_outcome(
        self,
        ai_gym_id: UUID,
        outcome_type: str,  # 'opened', 'clicked', 'replied', 'meeting_booked'
        outcome_timestamp: datetime
    ):
        """Update conversion metric when outcome occurs."""

        # Outcome value mapping
        outcome_values = {
            "opened": 0.25,
            "clicked": 0.50,
            "replied": 0.75,
            "meeting_booked": 1.00,
        }

        conversion_value = outcome_values.get(outcome_type, 0.0)

        await self.db.execute("""
            UPDATE ai_gym_performance
            SET
                conversion_metric = GREATEST(conversion_metric, $2),
                metadata = metadata || jsonb_build_object(
                    'outcome_type', $3,
                    'outcome_timestamp', $4
                )
            WHERE id = $1
        """, ai_gym_id, conversion_value, outcome_type, outcome_timestamp)
```

---

### 4.2 Weekly Optimization Job

```python
class AIGYMOptimizer:
    """
    Weekly job: Analyze performance and optimize routing.

    Goals:
    1. Identify which models perform best per task
    2. Find cheap models that achieve 90%+ of premium quality
    3. Update router preferences
    4. Generate insights report
    """

    async def optimize_routing(self):
        """Main weekly optimization job."""

        # Get last 7 days of performance data
        performance_data = await self._fetch_performance_data()

        # Analyze by task type
        for task_type in ["website_analysis", "email_generation", "demo_code"]:
            insights = await self._analyze_task_performance(
                task_type, performance_data
            )

            # Update router if better model found
            if insights.recommended_model != insights.current_model:
                await self._update_router_preference(
                    task_type, insights.recommended_model, insights
                )

        # Generate weekly report
        await self._generate_weekly_report(performance_data)

    async def _analyze_task_performance(
        self,
        task_type: str,
        performance_data: pd.DataFrame
    ) -> TaskInsights:
        """
        Analyze which model performs best for task type.

        Scoring Formula:
        efficiency = (conversion_rate × quality_score) / cost

        Goal: Maximize efficiency (best outcomes per dollar)
        """

        task_data = performance_data[
            performance_data['task_type'] == task_type
        ]

        # Group by model
        model_performance = task_data.groupby('model_name').agg({
            'conversion_metric': 'mean',  # Avg outcome
            'composite_score': 'mean',    # Avg quality
            'cost': 'mean',                # Avg cost
            'id': 'count'                  # Sample size
        }).reset_index()

        # Calculate efficiency
        model_performance['efficiency'] = (
            model_performance['conversion_metric'] *
            model_performance['composite_score']
        ) / model_performance['cost']

        # Require minimum sample size
        model_performance = model_performance[
            model_performance['id'] >= 10
        ]

        # Sort by efficiency
        model_performance = model_performance.sort_values(
            'efficiency', ascending=False
        )

        # Get current and recommended models
        current_model = await self._get_current_router_choice(task_type)
        recommended_model = model_performance.iloc[0]['model_name']

        return TaskInsights(
            task_type=task_type,
            current_model=current_model,
            recommended_model=recommended_model,
            efficiency_gain=self._calculate_efficiency_gain(
                current_model, recommended_model, model_performance
            ),
            model_rankings=model_performance.to_dict('records')
        )

    async def _update_router_preference(
        self,
        task_type: str,
        new_model: str,
        insights: TaskInsights
    ):
        """Update semantic router to prefer new model."""

        logger.info(f"""
        🎯 Router Update:
        Task: {task_type}
        Old model: {insights.current_model}
        New model: {new_model}
        Efficiency gain: {insights.efficiency_gain:.1%}
        """)

        # Update router configuration
        await self.router_config.update(task_type, new_model)

        # Log change to audit trail
        await self.db.execute("""
            INSERT INTO router_changes (
                task_type,
                old_model,
                new_model,
                efficiency_gain,
                applied_at
            ) VALUES ($1, $2, $3, $4, NOW())
        """, task_type, insights.current_model, new_model, insights.efficiency_gain)
```

---

### 4.3 AI-GYM Dashboard Queries

**Query 1: Model Leaderboard**
```sql
-- Top performing models by task type (last 30 days)
SELECT
    task_type,
    model_name,
    COUNT(*) as uses,
    AVG(conversion_metric) as avg_conversion,
    AVG(composite_score) as avg_quality,
    AVG(cost) as avg_cost,
    (AVG(conversion_metric) * AVG(composite_score)) / NULLIF(AVG(cost), 0) as efficiency
FROM ai_gym_performance
WHERE created_at >= NOW() - INTERVAL '30 days'
    AND conversion_metric IS NOT NULL
GROUP BY task_type, model_name
HAVING COUNT(*) >= 10
ORDER BY task_type, efficiency DESC;
```

**Query 2: Cost Tracking**
```sql
-- Daily AI costs by model
SELECT
    DATE(created_at) as date,
    model_name,
    COUNT(*) as uses,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost_per_use
FROM ai_gym_performance
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), model_name
ORDER BY date DESC, total_cost DESC;
```

**Query 3: Quality Trends**
```sql
-- Quality scores over time (detect drift)
SELECT
    DATE(created_at) as date,
    task_type,
    model_name,
    AVG(composite_score) as avg_quality,
    AVG(judge_total_score) as avg_judge_score,
    COUNT(*) as sample_size
FROM ai_gym_performance
WHERE created_at >= NOW() - INTERVAL '90 days'
    AND composite_score IS NOT NULL
GROUP BY DATE(created_at), task_type, model_name
HAVING COUNT(*) >= 5
ORDER BY date DESC, task_type, model_name;
```

**Query 4: Outcome Correlation**
```sql
-- Which quality scores predict outcomes?
SELECT
    task_type,
    CASE
        WHEN composite_score >= 0.8 THEN 'High Quality (0.8+)'
        WHEN composite_score >= 0.6 THEN 'Medium Quality (0.6-0.8)'
        ELSE 'Low Quality (<0.6)'
    END as quality_tier,
    COUNT(*) as samples,
    AVG(conversion_metric) as avg_conversion,
    AVG(CASE WHEN conversion_metric >= 0.75 THEN 1 ELSE 0 END) as reply_rate
FROM ai_gym_performance
WHERE created_at >= NOW() - INTERVAL '30 days'
    AND conversion_metric IS NOT NULL
GROUP BY task_type, quality_tier
ORDER BY task_type, avg_conversion DESC;
```

---

## 5. Model Selection Matrix

### 5.1 Task-to-Model Routing Table

| Task Type | Primary Model | Fallback | Cost/1M Tokens | When to Use Judge |
|-----------|---------------|----------|----------------|-------------------|
| **Classification** | DeepSeek-V3 | Qwen 2.5 | $0.27 | Never (deterministic) |
| **Scoring** | Qwen 2.5 | DeepSeek-V3 | $0.14 | Never (deterministic) |
| **Email Draft (SMB lead)** | Claude Haiku | DeepSeek-V3 | $0.50 | A/B test only |
| **Email Draft (Enterprise)** | Claude Sonnet 4 | GPT-4o | $3.00 | Always (3-model council) |
| **Website Analysis (SMB)** | Claude Haiku | Gemini 1.5 | $0.50 | Sometimes (2-model council) |
| **Website Analysis (Enterprise)** | Claude Sonnet 4 | GPT-4o | $3.00 | Always (3-model council) |
| **Demo Code** | Qwen2.5-Coder | Claude Sonnet 4 | $1.50 | Always (quality gate) |
| **Conversation Reply** | Claude Sonnet 4 | Claude Haiku | $3.00 | Always (quality gate) |
| **Summary** | Claude Haiku | DeepSeek-V3 | $0.50 | Never (low stakes) |
| **Judge Evaluation** | Claude Sonnet 4 | GPT-4o | $3.00 | N/A (is the judge) |

### 5.2 Lead Value-Based Routing

```python
def route_by_lead_value(task_type: str, estimated_value: float) -> str:
    """Route based on potential deal size."""

    if estimated_value > 100000:
        # Enterprise deal: Use best models
        return {
            "website_analysis": "claude-sonnet-4",
            "email_generation": "claude-sonnet-4",
            "conversation_reply": "claude-sonnet-4"
        }.get(task_type, "claude-sonnet-4")

    elif estimated_value > 25000:
        # Mid-market: Balance quality and cost
        return {
            "website_analysis": "gpt-4o",
            "email_generation": "claude-sonnet-4",  # Email always premium
            "conversation_reply": "claude-sonnet-4"
        }.get(task_type, "gpt-4o")

    else:
        # SMB: Cost-optimized
        return {
            "website_analysis": "claude-haiku",
            "email_generation": "claude-haiku",
            "conversation_reply": "claude-haiku"
        }.get(task_type, "claude-haiku")
```

---

## 6. Implementation Timeline

### Week 1: Foundation
- [ ] Set up OpenRouter account
- [ ] Implement SemanticRouter class
- [ ] Implement LLMJudge class
- [ ] Implement DeepEvalEvaluator class
- [ ] Create ai_gym_performance table
- [ ] Basic logging integration

### Week 2: Integration
- [ ] Integrate router with AI Council
- [ ] Add DeepEval pre-filtering
- [ ] Add judge evaluation for critical tasks
- [ ] Implement outcome tracking
- [ ] Create correlation jobs (Celery)

### Week 3: Optimization
- [ ] Weekly optimization job
- [ ] AI-GYM dashboard queries
- [ ] Model leaderboard UI
- [ ] Cost tracking dashboard
- [ ] Quality trend monitoring

### Week 4+: Refinement
- [ ] A/B testing framework
- [ ] Prompt versioning system
- [ ] Advanced routing strategies
- [ ] DPO fine-tuning (if needed)

---

## 7. Success Metrics

### Phase 1 Targets (Month 1)
- ✅ 80%+ cost savings vs always-Claude-Sonnet-4
- ✅ DeepEval composite score >0.7 for 90%+ of outputs
- ✅ AI-GYM data collection working (100% of generations logged)
- ✅ Weekly optimization job running successfully

### Phase 2 Targets (Month 2-3)
- ✅ Email reply rate correlation identified (which quality scores predict replies?)
- ✅ Cheap models achieving 85%+ of premium quality on specific tasks
- ✅ Router automatically preferring cost-effective models
- ✅ 5+ routing optimization improvements based on data

### Phase 3 Targets (Month 4+)
- ✅ 90%+ cost savings maintained
- ✅ Reply rates improving quarter-over-quarter
- ✅ DPO fine-tuning deployed (if ROI positive)
- ✅ Custom evaluation metrics for domain-specific quality

---

## 8. Key Takeaways

### ✅ Do This
1. **Use LLM-as-Judge** for critical tasks (website analysis, emails)
2. **Use DeepEval** as pre-filter (save $ on judge calls)
3. **Route intelligently** (cheap models for simple tasks)
4. **Track outcomes** (connect AI quality → business results)
5. **Optimize weekly** (let data guide model selection)

### ❌ Don't Do This
1. **Don't use RL-Factory** (wrong use case for content generation)
2. **Don't judge everything** (costs add up, use selectively)
3. **Don't ignore outcomes** (automated metrics ≠ business success)
4. **Don't over-optimize early** (need 1000+ samples for statistical significance)
5. **Don't fine-tune prematurely** (prompt optimization first)

---

**Document Owner**: AI/ML Lead
**Last Updated**: November 4, 2025
**Status**: Implementation Ready
**Related Docs**:
- `00_ML_STRATEGY_RESEARCH.md` (research foundation)
- `01_ENHANCED_SOFTWARE_ARCHITECTURE.md` (integration points)
- `03_COST_OPTIMIZATION_GUIDE.md` (cost strategies)
