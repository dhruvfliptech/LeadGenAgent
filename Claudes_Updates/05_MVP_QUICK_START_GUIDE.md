# MVP Quick Start Guide - Build Today
## Get to Working System in 8 Hours
### November 4, 2025

---

## Document Purpose

**Goal**: Build functional MVP TODAY with scraping → analysis → email generation.

**Timeline**: 8 hours (1 work day)
**Target**: 2 internal users, 100 leads/day
**Defer**: Demo sites, video automation, conversation agent (Phase 2)

---

## Hour-by-Hour Build Plan

### Hour 1: Setup & Foundation (9am-10am)

**Task 1.1: OpenRouter Account Setup** (15 min)
```bash
# 1. Go to https://openrouter.ai/
# 2. Sign up with email
# 3. Add $50 credit to account
# 4. Generate API key
# 5. Test API key

curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Should return list of models
```

**Task 1.2: Update Environment Variables** (10 min)
```bash
# backend/.env
cat <<EOF >> backend/.env

# OpenRouter (AI Council)
OPENROUTER_API_KEY=sk-or-v1-xxx
OPENROUTER_SITE_URL=http://localhost:5173
OPENROUTER_SITE_NAME="Internal Outreach Tool"

# Model Selection (start simple)
DEFAULT_CHEAP_MODEL=claude-haiku
DEFAULT_PREMIUM_MODEL=claude-sonnet-4
DEFAULT_JUDGE_MODEL=claude-sonnet-4

# Postmark (Email Sending)
POSTMARK_SERVER_TOKEN=9fc4c721-67db-48a1-8eb6-4897f6eee366
POSTMARK_FROM_EMAIL=sales@yourcompany.com

# MailReach (Email Warm-up)
MAILREACH_API_KEY=7wm1WRNNVytxFJUizjuLSEzY

# Feature Flags
ENABLE_AI_COUNCIL=true
ENABLE_SEMANTIC_ROUTER=true
ENABLE_DEEPEVAL=false  # Add later
ENABLE_DEMO_BUILDER=false  # Phase 2
ENABLE_VIDEO_AUTOMATION=false  # Phase 2
EOF
```

**Task 1.3: Install Dependencies** (20 min)
```bash
cd backend

# Add new dependencies
pip install openai httpx anthropic  # For AI APIs
pip install tenacity  # For retries
pip install pydantic-settings  # For config
pip install postmarkclient  # For email sending via Postmark

# Update requirements.txt
pip freeze > requirements.txt

cd ../frontend
# No new deps needed yet
```

**Task 1.4: Database Migration** (15 min)
```bash
cd backend

# Create migration for AI-GYM tables
alembic revision -m "add_ai_gym_tables"

# Edit migration file (see schema below)
# Then apply
alembic upgrade head
```

**Migration Schema**:
```python
# In migration file
def upgrade():
    op.create_table(
        'ai_gym_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(50), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id')),
        sa.Column('cost', sa.Numeric(10, 4)),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('composite_score', sa.Numeric(4, 3)),
        sa.Column('conversion_metric', sa.Numeric(4, 3)),
        sa.Column('metadata', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Add indexes
    op.create_index('idx_ai_gym_task_model', 'ai_gym_performance', ['task_type', 'model_name'])
    op.create_index('idx_ai_gym_created', 'ai_gym_performance', ['created_at'])
```

---

### Hour 2: Semantic Router (10am-11am)

**Task 2.1: Create Router Module** (40 min)

Create file: `backend/app/services/semantic_router.py`

```python
"""
Semantic Router - Route tasks to optimal models.

Usage:
    router = SemanticRouter()
    model_name = router.route("website_analysis", {"estimated_value": 50000})
"""

from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class SemanticRouter:
    """Route tasks to cost-optimal models."""

    PRICING = {
        "qwen-2.5": 0.14,
        "deepseek-v3": 0.27,
        "claude-haiku": 0.50,
        "qwen2.5-coder-32b": 1.50,
        "gpt-4o": 5.00,
        "claude-sonnet-4": 7.50,
    }

    def route(self, task_type: str, context: Dict = None) -> Tuple[str, float]:
        """
        Route to optimal model.

        Returns: (model_name, cost_per_million)
        """
        context = context or {}

        # Simple routing rules
        if task_type in ["classify", "score", "extract"]:
            return ("deepseek-v3", self.PRICING["deepseek-v3"])

        elif task_type == "website_analysis":
            return self._route_analysis(context)

        elif task_type == "email_generation":
            return self._route_email(context)

        elif task_type == "demo_code":
            return ("qwen2.5-coder-32b", self.PRICING["qwen2.5-coder-32b"])

        elif task_type == "judge":
            return ("claude-sonnet-4", self.PRICING["claude-sonnet-4"])

        else:
            # Default: cheap model
            return ("claude-haiku", self.PRICING["claude-haiku"])

    def _route_analysis(self, context: Dict) -> Tuple[str, float]:
        """Route website analysis by lead value."""
        estimated_value = context.get("estimated_value", 0)

        if estimated_value > 100000:
            # Enterprise: premium model
            return ("claude-sonnet-4", self.PRICING["claude-sonnet-4"])
        elif estimated_value > 25000:
            # Mid-market: good model
            return ("gpt-4o", self.PRICING["gpt-4o"])
        else:
            # SMB: cheap model
            return ("claude-haiku", self.PRICING["claude-haiku"])

    def _route_email(self, context: Dict) -> Tuple[str, float]:
        """Route email generation (always good quality)."""
        estimated_value = context.get("estimated_value", 0)

        if estimated_value > 50000:
            # High-value: premium
            return ("claude-sonnet-4", self.PRICING["claude-sonnet-4"])
        else:
            # Standard: cheap but good
            return ("claude-haiku", self.PRICING["claude-haiku"])

    def estimate_lead_value(self, lead: Dict) -> float:
        """Quick lead value estimate."""
        employees = lead.get("employee_count", 10)

        if employees > 1000:
            return 150000
        elif employees > 100:
            return 50000
        elif employees > 10:
            return 15000
        else:
            return 5000
```

**Task 2.2: Test Router** (20 min)
```python
# Test file: backend/tests/test_router.py
def test_semantic_router():
    router = SemanticRouter()

    # Test classification → cheap
    model, cost = router.route("classify")
    assert model == "deepseek-v3"
    assert cost < 0.50

    # Test enterprise analysis → premium
    model, cost = router.route("website_analysis", {"estimated_value": 150000})
    assert model == "claude-sonnet-4"

    # Test SMB analysis → cheap
    model, cost = router.route("website_analysis", {"estimated_value": 10000})
    assert model == "claude-haiku"

    print("✅ Router tests passed")

if __name__ == "__main__":
    test_semantic_router()
```

---

### Hour 3: AI Council Core (11am-12pm)

**Task 3.1: Create AI Council Module** (50 min)

Create file: `backend/app/services/ai_council.py`

```python
"""
AI Council - Multi-model orchestration with routing.

Usage:
    council = AICouncil()
    result = await council.execute("website_analysis", prompt, context)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import httpx
from app.services.semantic_router import SemanticRouter
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ModelResponse:
    """Response from a model."""
    model: str
    text: str
    cost: float
    duration: float
    tokens: int

class AICouncil:
    """Multi-model AI orchestration."""

    def __init__(self):
        self.router = SemanticRouter()
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"

    async def execute(
        self,
        task_type: str,
        prompt: str,
        context: Dict = None,
        use_council: bool = False
    ) -> ModelResponse:
        """
        Execute task with optimal model selection.

        Args:
            task_type: Type of task (website_analysis, email_generation, etc.)
            prompt: The prompt to send
            context: Additional context (lead data, etc.)
            use_council: If True, query multiple models and judge

        Returns:
            ModelResponse with text, cost, duration
        """
        context = context or {}

        if use_council and task_type in ["website_analysis", "email_generation"]:
            # Multi-model council (Phase 2)
            # For MVP, just use single best model
            pass

        # Route to optimal model
        model_name, cost_per_million = self.router.route(task_type, context)

        # Execute
        response = await self._call_model(model_name, prompt, context)

        # Log to AI-GYM (async, don't block)
        asyncio.create_task(self._log_performance(
            task_type=task_type,
            model_name=model_name,
            response=response,
            context=context
        ))

        return response

    async def _call_model(
        self,
        model_name: str,
        prompt: str,
        context: Dict
    ) -> ModelResponse:
        """Call OpenRouter API."""

        start_time = time.time()

        # Map model name to OpenRouter model ID
        model_id_map = {
            "deepseek-v3": "deepseek/deepseek-chat",
            "qwen-2.5": "qwen/qwen-2.5-72b-instruct",
            "claude-haiku": "anthropic/claude-3-haiku",
            "claude-sonnet-4": "anthropic/claude-sonnet-4",
            "gpt-4o": "openai/gpt-4o",
            "qwen2.5-coder-32b": "qwen/qwen2.5-coder-32b-instruct",
        }

        model_id = model_id_map.get(model_name, "anthropic/claude-3-haiku")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                    "X-Title": settings.OPENROUTER_SITE_NAME,
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                }
            )

        duration = time.time() - start_time
        data = response.json()

        # Extract response
        text = data["choices"][0]["message"]["content"]
        tokens = data["usage"]["total_tokens"]

        # Calculate cost
        cost_per_million = self.router.PRICING[model_name]
        cost = (tokens / 1_000_000) * cost_per_million

        logger.info(f"Model: {model_name}, Tokens: {tokens}, Cost: ${cost:.4f}, Duration: {duration:.2f}s")

        return ModelResponse(
            model=model_name,
            text=text,
            cost=cost,
            duration=duration,
            tokens=tokens
        )

    async def _log_performance(
        self,
        task_type: str,
        model_name: str,
        response: ModelResponse,
        context: Dict
    ):
        """Log to AI-GYM database (async)."""
        try:
            from app.core.database import get_db

            async for db in get_db():
                await db.execute("""
                    INSERT INTO ai_gym_performance (
                        id, task_type, model_name, lead_id, cost, duration_seconds, metadata, created_at
                    ) VALUES (
                        gen_random_uuid(), $1, $2, $3, $4, $5, $6, NOW()
                    )
                """,
                    task_type,
                    model_name,
                    context.get("lead_id"),
                    response.cost,
                    int(response.duration),
                    {"tokens": response.tokens}
                )
                await db.commit()
                break

        except Exception as e:
            logger.error(f"Failed to log AI-GYM performance: {e}")
```

**Task 3.2: Test AI Council** (10 min)
```bash
# Quick manual test
python -c "
import asyncio
from app.services.ai_council import AICouncil

async def test():
    council = AICouncil()
    response = await council.execute(
        task_type='classify',
        prompt='Classify this company industry: Tesla makes electric vehicles',
        context={}
    )
    print(f'Response: {response.text}')
    print(f'Cost: \${response.cost:.4f}')
    print(f'Model: {response.model}')

asyncio.run(test())
"
```

---

### Hour 4: Lunch Break (12pm-1pm)
**Take a break! You've set up the core infrastructure.**

---

### Hour 5: Website Analyzer Integration (1pm-2pm)

**Task 5.1: Enhance Website Analyzer** (50 min)

Edit file: `backend/app/services/website_analyzer.py`

Add AI Council integration:

```python
from app.services.ai_council import AICouncil

class WebsiteAnalyzer:
    def __init__(self):
        self.ai_council = AICouncil()
        # ... existing code ...

    async def analyze(self, lead_id: str, website_url: str) -> Dict:
        """Analyze website with AI Council."""

        # 1. Crawl website (existing code)
        html_content = await self._crawl_website(website_url)
        metadata = await self._extract_metadata(html_content)

        # 2. Build analysis prompt
        prompt = self._build_analysis_prompt(website_url, metadata, html_content[:10000])

        # 3. Get AI analysis (NEW)
        context = {
            "lead_id": lead_id,
            "estimated_value": self._estimate_lead_value(metadata)
        }

        response = await self.ai_council.execute(
            task_type="website_analysis",
            prompt=prompt,
            context=context
        )

        # 4. Parse structured output
        analysis = self._parse_analysis(response.text)

        # 5. Store in database
        await self._store_analysis(lead_id, analysis, response.cost)

        return analysis

    def _build_analysis_prompt(self, url: str, metadata: Dict, html_snippet: str) -> str:
        """Build prompt for website analysis."""
        return f"""
Analyze this website and provide actionable improvement recommendations.

URL: {url}

Metadata:
- Title: {metadata.get('title', 'N/A')}
- Description: {metadata.get('description', 'N/A')}
- Tech Stack: {', '.join(metadata.get('technologies', []))}

HTML Preview (first 10K chars):
{html_snippet}

Provide analysis in JSON format:
{{
    "overall_score": 0-100,
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "top_improvements": [
        {{
            "title": "Improvement title",
            "description": "What to fix and why",
            "impact": "high|medium|low",
            "effort": "low|medium|high"
        }},
        ...
    ],
    "positioning_notes": "How company positions itself",
    "target_audience": "Who they target",
    "cta_analysis": "Quality of calls-to-action"
}}
"""

    def _estimate_lead_value(self, metadata: Dict) -> float:
        """Estimate lead value from website signals."""
        value = 25000  # Base value

        # Has enterprise tech? +50%
        enterprise_tech = ['salesforce', 'hubspot', 'marketo', 'oracle']
        if any(tech in str(metadata.get('technologies', [])).lower() for tech in enterprise_tech):
            value *= 1.5

        # Has career page? +20%
        if metadata.get('has_careers_page'):
            value *= 1.2

        return value
```

**Task 5.2: Test Analyzer** (10 min)
```bash
# Test analyzer
curl -X POST http://localhost:8000/api/v2/analysis \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "lead_id": "123e4567-e89b-12d3-a456-426614174000",
    "website_url": "https://example.com"
  }'
```

---

### Hour 6: Email Generator (2pm-3pm)

**Task 6.1: Create Email Generator** (50 min)

Create file: `backend/app/services/email_generator.py`

```python
"""
Email Generator - AI-powered personalized emails.

Usage:
    generator = EmailGenerator()
    email = await generator.generate(lead, analysis)
"""

from typing import Dict
from app.services.ai_council import AICouncil

class EmailGenerator:
    """Generate personalized outreach emails."""

    def __init__(self):
        self.ai_council = AICouncil()

    async def generate(
        self,
        lead: Dict,
        analysis: Dict,
        template_type: str = "improvement_offer"
    ) -> Dict:
        """
        Generate personalized email.

        Args:
            lead: Lead data (company name, contact, etc.)
            analysis: Website analysis results
            template_type: Type of email template

        Returns:
            {subject, body, personalization_notes}
        """

        # Build prompt
        prompt = self._build_email_prompt(lead, analysis, template_type)

        # Get AI generation
        context = {
            "lead_id": lead.get("id"),
            "estimated_value": lead.get("estimated_value", 25000)
        }

        response = await self.ai_council.execute(
            task_type="email_generation",
            prompt=prompt,
            context=context
        )

        # Parse email
        email = self._parse_email(response.text)
        email["generation_cost"] = response.cost
        email["model_used"] = response.model

        return email

    def _build_email_prompt(self, lead: Dict, analysis: Dict, template_type: str) -> str:
        """Build prompt for email generation."""

        company_name = lead.get("company_name", "your company")
        contact_name = lead.get("contact_name", "there")

        top_improvements = analysis.get("top_improvements", [])[:3]
        improvements_text = "\n".join([
            f"- {imp['title']}: {imp['description']}"
            for imp in top_improvements
        ])

        return f"""
Write a personalized outreach email for this lead:

COMPANY: {company_name}
CONTACT: {contact_name}
WEBSITE ANALYSIS INSIGHTS:
{improvements_text}

EMAIL REQUIREMENTS:
1. Subject line: Compelling, specific to their situation (under 60 chars)
2. Opening: Reference specific insight from their website
3. Value prop: Explain how we can help with the improvements identified
4. Social proof: Brief mention of similar companies we've helped
5. CTA: Low-friction next step (15-min call)
6. Tone: Professional but friendly, not salesy
7. Length: Under 150 words

Output as JSON:
{{
    "subject": "Subject line here",
    "body": "Email body here (use \\n\\n for paragraphs)",
    "personalization_notes": "Key personalizations used"
}}
"""

    def _parse_email(self, response_text: str) -> Dict:
        """Parse JSON email from response."""
        import json
        import re

        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: manual parsing
        return {
            "subject": "Let's improve your website",
            "body": response_text,
            "personalization_notes": "AI generation failed, using fallback"
        }
```

**Task 6.2: Test Generator** (10 min)
```python
# Test email generator
import asyncio
from app.services.email_generator import EmailGenerator

async def test():
    generator = EmailGenerator()

    lead = {
        "id": "test-123",
        "company_name": "Acme Corp",
        "contact_name": "John",
        "estimated_value": 50000
    }

    analysis = {
        "top_improvements": [
            {
                "title": "Slow Page Load",
                "description": "Page loads in 8 seconds, should be under 3",
                "impact": "high"
            },
            {
                "title": "Weak CTAs",
                "description": "Call-to-action buttons are not prominent",
                "impact": "medium"
            }
        ]
    }

    email = await generator.generate(lead, analysis)
    print(f"Subject: {email['subject']}")
    print(f"Body:\n{email['body']}")
    print(f"Cost: ${email['generation_cost']:.4f}")

asyncio.run(test())
```

**Task 6.3: Create Postmark Email Sender** (NEW - 15 min)

Create file: `backend/app/services/email_sender.py`

```python
"""
Email Sender - Send emails via Postmark.

Usage:
    sender = EmailSender()
    await sender.send(email_data)
"""

from postmarkclient import ServerClient
from app.core.config import settings

class EmailSender:
    """Send emails via Postmark API."""

    def __init__(self):
        self.client = ServerClient(settings.POSTMARK_SERVER_TOKEN)

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        from_email: str = None,
        track_opens: bool = True,
        track_links: bool = True
    ) -> dict:
        """
        Send email via Postmark.

        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML email body
            from_email: Sender email (defaults to config)
            track_opens: Track email opens
            track_links: Track link clicks

        Returns:
            {message_id, status, submitted_at}
        """

        from_email = from_email or settings.POSTMARK_FROM_EMAIL

        try:
            response = self.client.send_email(
                From=from_email,
                To=to,
                Subject=subject,
                HtmlBody=html_body,
                TrackOpens=track_opens,
                TrackLinks="HtmlOnly" if track_links else "None",
                MessageStream="outbound"  # Use "outbound" stream for cold emails
            )

            return {
                "message_id": response["MessageID"],
                "status": "sent",
                "submitted_at": response["SubmittedAt"],
                "to": response["To"]
            }

        except Exception as e:
            logger.error(f"Failed to send email via Postmark: {e}")
            raise
```

**Test Postmark:**
```bash
# Test Postmark API
curl "https://api.postmarkapp.com/email" \
  -X POST \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Postmark-Server-Token: 9fc4c721-67db-48a1-8eb6-4897f6eee366" \
  -d '{
    "From": "sales@yourcompany.com",
    "To": "test@example.com",
    "Subject": "Test from MVP",
    "HtmlBody": "<strong>Hello</strong> from Postmark!"
  }'
```

---

### Hour 7: API Endpoints (3pm-4pm)

**Task 7.1: Create v2 API Endpoints** (50 min)

Create file: `backend/app/api/endpoints/ai_outreach.py`

```python
"""
AI Outreach Endpoints - MVP routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.api.deps import verify_api_key
from app.services.website_analyzer import WebsiteAnalyzer
from app.services.email_generator import EmailGenerator

router = APIRouter()

class AnalyzeRequest(BaseModel):
    lead_id: UUID
    website_url: str

class GenerateEmailRequest(BaseModel):
    lead_id: UUID
    template_type: Optional[str] = "improvement_offer"

@router.post("/analyze")
async def analyze_website(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(verify_api_key)
):
    """Analyze website with AI Council."""

    analyzer = WebsiteAnalyzer()

    try:
        analysis = await analyzer.analyze(
            lead_id=str(request.lead_id),
            website_url=request.website_url
        )

        return {
            "status": "success",
            "analysis": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-email")
async def generate_email(
    request: GenerateEmailRequest,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(verify_api_key)
):
    """Generate personalized email."""

    # Get lead
    lead_result = await db.fetchrow(
        "SELECT * FROM leads WHERE id = $1",
        request.lead_id
    )

    if not lead_result:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Get analysis
    analysis_result = await db.fetchrow(
        "SELECT * FROM website_analyses WHERE lead_id = $1 ORDER BY created_at DESC LIMIT 1",
        request.lead_id
    )

    if not analysis_result:
        raise HTTPException(status_code=404, detail="No analysis found. Run analysis first.")

    # Generate email
    generator = EmailGenerator()
    email = await generator.generate(
        lead=dict(lead_result),
        analysis=dict(analysis_result),
        template_type=request.template_type
    )

    return {
        "status": "success",
        "email": email
    }

@router.get("/ai-gym/stats")
async def get_ai_gym_stats(
    db: AsyncSession = Depends(get_db),
    user: str = Depends(verify_api_key)
):
    """Get AI-GYM performance stats."""

    stats = await db.fetchrow("""
        SELECT
            COUNT(*) as total_calls,
            SUM(cost) as total_cost,
            AVG(cost) as avg_cost,
            AVG(duration_seconds) as avg_duration,
            COUNT(DISTINCT model_name) as models_used
        FROM ai_gym_performance
        WHERE created_at >= NOW() - INTERVAL '24 hours'
    """)

    by_model = await db.fetch("""
        SELECT
            model_name,
            COUNT(*) as uses,
            SUM(cost) as total_cost,
            AVG(duration_seconds) as avg_duration
        FROM ai_gym_performance
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY model_name
        ORDER BY uses DESC
    """)

    return {
        "period": "last_24_hours",
        "summary": dict(stats),
        "by_model": [dict(row) for row in by_model]
    }
```

**Task 7.2: Register Router** (10 min)
```python
# In backend/app/main.py
from app.api.endpoints import ai_outreach

app.include_router(
    ai_outreach.router,
    prefix="/api/v2/ai-outreach",
    tags=["ai-outreach"]
)
```

---

### Hour 8: Testing & Verification (4pm-5pm)

**Task 8.1: End-to-End Test** (30 min)
```bash
# 1. Start backend
cd backend
DATABASE_URL="postgresql://postgres@localhost:5432/craigslist_leads" \
REDIS_URL="redis://localhost:6379" \
OPENROUTER_API_KEY="your-key" \
uvicorn app.main:app --reload

# 2. Test workflow
# Step 1: Create lead
curl -X POST http://localhost:8000/api/v1/leads \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "company_name": "Test Company",
    "website": "https://example.com",
    "email": "contact@example.com"
  }'

# Step 2: Analyze website
curl -X POST http://localhost:8000/api/v2/ai-outreach/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "lead_id": "LEAD_ID_FROM_STEP1",
    "website_url": "https://example.com"
  }'

# Step 3: Generate email
curl -X POST http://localhost:8000/api/v2/ai-outreach/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "lead_id": "LEAD_ID_FROM_STEP1"
  }'

# Step 4: Check AI-GYM stats
curl http://localhost:8000/api/v2/ai-outreach/ai-gym/stats \
  -H "X-API-Key: YOUR_KEY"
```

**Task 8.2: Verify Cost Tracking** (15 min)
```sql
-- Check AI-GYM data
SELECT
    task_type,
    model_name,
    COUNT(*) as uses,
    SUM(cost) as total_cost,
    AVG(cost) as avg_cost
FROM ai_gym_performance
GROUP BY task_type, model_name
ORDER BY total_cost DESC;

-- Expected results:
-- website_analysis | claude-haiku or claude-sonnet-4 | ~$0.002-0.030
-- email_generation | claude-haiku or claude-sonnet-4 | ~$0.001-0.011
```

**Task 8.3: Document Current State** (15 min)
```bash
# Create MVP status file
cat <<EOF > MVP_STATUS.md
# MVP Status - $(date)

## ✅ Completed
- [x] OpenRouter integration
- [x] Semantic router (task-based + lead-value routing)
- [x] AI Council core
- [x] Website analyzer with AI
- [x] Email generator with AI
- [x] AI-GYM cost tracking
- [x] API endpoints (/analyze, /generate-email, /ai-gym/stats)

## 📊 Test Results
- Website analysis: \$X per lead
- Email generation: \$Y per lead
- Total cost (10 leads): \$Z
- Average response time: Xs

## ⏭️ Next Steps (Tomorrow)
- [ ] Google Maps scraper
- [ ] Bulk processing
- [ ] Email sending (Gmail API)
- [ ] Frontend integration
- [ ] Outcome tracking

## 🎯 Current Capabilities
- Analyze any website → AI insights
- Generate personalized emails
- Track costs per task/model
- Route to optimal models

## 💰 Cost Performance
- Target: < \$0.01/lead
- Actual: \$X/lead
- Status: [ON TRACK / NEEDS OPTIMIZATION]
EOF
```

---

## Post-MVP: Tomorrow's Priorities

### Day 2 Morning (2 hours)
1. **Google Maps Scraper** (1 hour)
   - Integrate Google Maps API
   - Parse business listings
   - Extract contact info

2. **Bulk Processing** (1 hour)
   - Process 100 leads at once
   - Queue jobs via Celery
   - Progress tracking

### Day 2 Afternoon (4 hours)
3. **Gmail Integration** (2 hours)
   - OAuth2 setup
   - Send emails via Gmail API
   - Track sent emails

4. **Frontend Dashboard** (2 hours)
   - Add AI-GYM stats widget
   - Show cost per lead
   - Display model distribution

---

## Troubleshooting

### Issue: OpenRouter API Error
```bash
# Check API key
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer YOUR_API_KEY"

# Should return: {"label": "Your key name"}
```

### Issue: Database Migration Fails
```bash
# Reset migrations
alembic downgrade -1
alembic upgrade head

# Or start fresh
alembic revision --autogenerate -m "fresh_start"
```

### Issue: AI Council Timeout
```python
# Increase timeout in httpx client
async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes
    ...
```

---

## Success Criteria

**MVP is successful if:**
- ✅ Can analyze 10 websites → get AI insights
- ✅ Can generate 10 personalized emails
- ✅ Total cost < $1 for 10 leads ($0.10/lead)
- ✅ AI-GYM tracking shows costs per model
- ✅ No critical errors or crashes

**You can now:**
1. Process leads end-to-end (scrape → analyze → email)
2. Track exactly how much each AI call costs
3. Route tasks to optimal models automatically
4. Scale to 100-1000 leads/day

---

**Time Investment**: 8 hours
**Result**: Working MVP with AI-powered analysis & email generation
**Cost**: ~$50 for API credits (good for 1000+ leads)
**Next**: Scale up, add Gmail sending, build dashboards

---

**Document Owner**: Engineering Lead
**Created**: November 4, 2025
**Status**: Ready to Execute
**Related**: All other Claudes_Updates docs provide additional context
