## Claude Agent Playbook – AI Council Operations

### 1. Purpose
Define how Anthropic Claude (4.5 Sonnet & Haiku) operates within the multi-model AI Council, including prompt patterns, evaluation loops, safety controls, and integration with existing services. Provides reusable “skills” for engineering squads.

### 2. Role Assignments
| Task | Primary Model | Secondary | Notes |
|------|---------------|-----------|-------|
| Website insight (UX/CRO) | Claude 4.5 Sonnet | GPT-4o | Claude excels at structured reasoning and critique. |
| Code critique & judge | Claude 4.5 Sonnet | Qwen Max | Use Claude to score generated demos before deployment. |
| Email copywriting | Claude 3.5 Sonnet | Gemini 1.5 | Tone-aware, customizable style guides. |
| Conversation response | Claude 4.5 Sonnet | Haiku | Balance empathy and precision. Haiku for low-cost drafts. |
| Summarization | Claude 3 Haiku | DeepSeek | Fast, cost-effective meeting summaries. |

### 3. Skill Library

#### 3.1 Insight Synthesizer
- **Input**: Website metadata JSON, scraped copy, screenshots refs.
- **Prompt Skeleton**:
```
You are a senior conversion strategist. Analyze the website data below and produce:
1. Top 3 conversion blockers (severity, evidence, fix)
2. UX quick wins
3. Messaging improvements
...
```
- **Output Schema**: JSON with arrays, severity levels, estimated impact.
- **Post-Processing**: Validate JSON (Pydantic), store in `website_analyses`.

#### 3.2 Demo Judge
- **Input**: QA results, screenshots, improvement plan, code snippet.
- **Prompt Skeleton**:
```
Act as lead front-end architect. Evaluate whether the generated demo fulfills the improvement plan.
Return JSON with score (0-100), pass/fail, issues list, remediation.
```
- **Usage**: Gate deployments; fail triggers fallback or human review.

#### 3.3 Email Personalizer
- **Input**: Lead profile, analysis highlights, demo/video links, tone guidelines.
- **Prompt Skeleton**: instruct on word count, referencing insights, CTA options.
- **Variants**: Use Claude for premium variant, Haiku for low-priority leads.

#### 3.4 Reply Strategist
- **Input**: Conversation history, latest reply, sentiment analysis.
- **Prompt Skeleton**: ask for recommended response, reasoning, risk flags.
- **Safety**: enforce allow-list topics, escalate if legal/negative sentiment.

### 4. Prompt Governance
- Store prompts in version-controlled YAML (`ai/prompts/*.yaml`).
- Include metadata: owner, last review date, cost estimates, evaluation results.
- Run prompt regression tests using golden datasets; automated nightly check.

### 5. Cost & Latency Controls
- Implement router that tracks usage per model/task; enforce budgets by stage (dev/staging/prod).
- Use Claude Haiku for non-critical tasks (<$0.25 per 1k tokens) to cap spend.
- Leverage caching for deterministic outputs (e.g., summarizations within 24h window).

### 6. Safety & Compliance
- All outputs filtered via Anthropic moderation endpoint; fallback to manual review on flagged content.
- Apply masked redaction for PII before sending prompts (limit to first name, domain).
- Audit log entries store prompt hash, output hash, model name, cost, latency.

### 7. Evaluation & AI-GYM Feedback Loop
- For each task, capture KPI (reply rate, QA pass, meeting conversions).
- Weekly AI-GYM sync: review leaderboard, adjust model weights, update prompts.
- Introduce multi-armed bandit for email copy selection (Claude vs GPT vs DeepSeek).

### 8. Operational Runbooks
- **Incident**: Model outage → auto failover to backup (e.g., GPT-4o) while alerting engineers.
- **Drift**: If quality dips (score < threshold), trigger prompt tuning session; incorporate human-labeled feedback.
- **Cold Start**: Provide seed dataset; run user study to calibrate tone guides.

### 9. Tooling & Libraries
- Use LangChain or direct HTTP for OpenRouter calls (prefer direct for transparency).
- Implement standardized `ModelExecutor` class handling retries, backoff, logging.
- Integrate `anthropic` SDK for streaming responses where needed (conversation agent UI).

### 10. Training & Enablement
- Maintain internal wiki with prompt examples, style guides, success stories.
- Run monthly prompt engineering workshops; cross-team knowledge sharing.
- Encourage engineers to add “Prompt ADRs” when making significant changes.

