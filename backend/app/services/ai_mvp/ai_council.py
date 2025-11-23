"""
AI Council - Multi-model AI orchestration with semantic routing.

Uses OpenRouter for unified access to:
- Claude Sonnet 4 (premium reasoning)
- GPT-4o (premium multi-modal)
- DeepSeek-V3 (cheap reasoning)
- Qwen 2.5 72B (cheap multi-purpose)
- Gemini Flash 1.5 (ultra-cheap classification)

Based on research from Claudes_Updates/02_ML_STRATEGY_AND_EVALUATION.md
"""

import os
import asyncio
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from app.services.ai_mvp.semantic_router import SemanticRouter, TaskType, RouteDecision
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker

logger = structlog.get_logger(__name__)


class Message(BaseModel):
    """Chat message format."""
    role: Literal["system", "user", "assistant"]
    content: str


class AICouncilConfig(BaseModel):
    """Configuration for AI Council."""
    openrouter_api_key: str
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    timeout_seconds: int = 30


class AICouncilResponse(BaseModel):
    """Response from AI Council."""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix

    content: str
    model_used: str
    model_tier: str
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    request_id: Optional[int] = None
    route_decision: RouteDecision


class AICouncil:
    """
    AI Council orchestrates multi-model AI requests via OpenRouter.

    Features:
    - Semantic routing (cheap → expensive based on task complexity)
    - Cost tracking via AI-GYM
    - Automatic retries with exponential backoff
    - Support for all major models via OpenRouter
    """

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"  # Correct endpoint

    def __init__(
        self,
        config: AICouncilConfig,
        gym_tracker: Optional[AIGymTracker] = None
    ):
        """Initialize AI Council."""
        self.config = config
        self.router = SemanticRouter()
        self.gym_tracker = gym_tracker
        self.http_client = httpx.AsyncClient(timeout=config.timeout_seconds)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _call_openrouter(
        self,
        model: str,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Call OpenRouter API with retry logic.

        Args:
            model: OpenRouter model ID (e.g., "anthropic/claude-sonnet-4")
            messages: List of chat messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum completion tokens

        Returns:
            OpenRouter API response
        """
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/craigslist-leads",  # Update with your repo
            "X-Title": "Craigslist Lead Generation MVP"
        }

        payload = {
            "model": model,
            "messages": [msg.model_dump() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(
            "openrouter.request",
            model=model,
            message_count=len(messages),
            temperature=temperature,
            max_tokens=max_tokens
        )

        response = await self.http_client.post(
            self.OPENROUTER_API_URL,
            headers=headers,
            json=payload
        )

        response.raise_for_status()
        data = response.json()

        logger.info(
            "openrouter.response",
            model=model,
            prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=data.get("usage", {}).get("completion_tokens", 0)
        )

        return data

    async def complete(
        self,
        task_type: TaskType,
        messages: List[Message],
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        force_model: Optional[str] = None
    ) -> AICouncilResponse:
        """
        Complete an AI task with semantic routing.

        Args:
            task_type: Type of task (determines routing)
            messages: Chat messages (system + user prompts)
            lead_id: Associated lead ID (for tracking)
            lead_value: Estimated lead value in dollars (for routing)
            temperature: Override default temperature
            max_tokens: Override default max tokens
            force_model: Force specific model (bypasses routing)

        Returns:
            AICouncilResponse with completion and metadata
        """
        # Route to appropriate model
        if force_model:
            route = RouteDecision(
                model_name=force_model,
                model_tier="custom",
                task_complexity="custom",
                reasoning="User forced model",
                estimated_cost=0.01
            )
        else:
            route = self.router.route(task_type, lead_value)

        logger.info(
            "ai_council.routed",
            task_type=task_type.value,
            model=route.model_name,
            tier=route.model_tier.value,
            lead_value=lead_value
        )

        # Start AI-GYM tracking
        request_id = None
        if self.gym_tracker:
            request_id = await self.gym_tracker.start_request(
                task_type=task_type.value,
                model_name=route.model_name,
                lead_id=lead_id,
                metadata={
                    "lead_value": lead_value,
                    "route_reasoning": route.reasoning,
                    "temperature": temperature or self.config.default_temperature,
                    "max_tokens": max_tokens or self.config.default_max_tokens
                }
            )

        try:
            # Call OpenRouter
            response_data = await self._call_openrouter(
                model=route.model_name,
                messages=messages,
                temperature=temperature or self.config.default_temperature,
                max_tokens=max_tokens or self.config.default_max_tokens
            )

            # Extract response
            content = response_data["choices"][0]["message"]["content"]
            usage = response_data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Calculate actual cost
            model_info = self.router.get_model_info(route.model_name)
            if "pricing" in model_info and model_info["pricing"]:
                input_cost = (prompt_tokens / 1_000_000) * model_info["pricing"]["input"]
                output_cost = (completion_tokens / 1_000_000) * model_info["pricing"]["output"]
                total_cost = input_cost + output_cost
            else:
                total_cost = route.estimated_cost  # Fallback to estimate

            # Complete AI-GYM tracking
            if self.gym_tracker and request_id:
                await self.gym_tracker.complete_request(
                    request_id=request_id,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    cost=total_cost,
                    response_text=content[:500]  # Store first 500 chars for quality eval
                )

            return AICouncilResponse(
                content=content,
                model_used=route.model_name,
                model_tier=route.model_tier.value,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost=total_cost,
                request_id=request_id,
                route_decision=route
            )

        except Exception as e:
            logger.error(
                "ai_council.error",
                task_type=task_type.value,
                model=route.model_name,
                error=str(e)
            )
            raise

    async def analyze_website(
        self,
        url: str,
        html_content: str,
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None
    ) -> AICouncilResponse:
        """
        Analyze a website and extract key insights.

        Args:
            url: Website URL
            html_content: Scraped HTML content
            lead_id: Associated lead ID
            lead_value: Estimated lead value (for routing)

        Returns:
            AICouncilResponse with analysis
        """
        # Truncate HTML to avoid token limits
        html_preview = html_content[:15000]  # ~3750 tokens

        messages = [
            Message(
                role="system",
                content="""You are an expert business analyst. Analyze the website and extract:
1. **Company Description**: What does this company do? (2-3 sentences)
2. **Services/Products**: List main offerings
3. **Pain Points**: What problems might they be experiencing? (3-5 bullet points)
4. **Decision Makers**: Likely job titles to target
5. **Personalization Angle**: How could our service help them specifically?

Be concise and actionable. Focus on sales insights."""
            ),
            Message(
                role="user",
                content=f"""Website: {url}

HTML Content:
{html_preview}

Analyze this website and provide structured insights."""
            )
        ]

        return await self.complete(
            task_type=TaskType.WEBSITE_ANALYSIS,
            messages=messages,
            lead_id=lead_id,
            lead_value=lead_value,
            temperature=0.3  # Lower temp for consistent analysis
        )

    async def generate_email(
        self,
        prospect_name: str,
        company_name: str,
        website_analysis: str,
        our_service_description: str,
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None
    ) -> AICouncilResponse:
        """
        Generate personalized email based on website analysis.

        Args:
            prospect_name: Name of prospect
            company_name: Company name
            website_analysis: Output from analyze_website()
            our_service_description: Description of our service/product
            lead_id: Associated lead ID
            lead_value: Estimated lead value (for routing)

        Returns:
            AICouncilResponse with email
        """
        messages = [
            Message(
                role="system",
                content="""You are an expert cold email copywriter. Write highly personalized, short emails that:
- Start with a specific insight about their business (from analysis)
- Clearly explain how we can help (1-2 sentences)
- Include a soft call-to-action
- Keep total length under 150 words
- Sound natural and conversational, not salesy

Do NOT use: "I hope this email finds you well", "I wanted to reach out", generic templates."""
            ),
            Message(
                role="user",
                content=f"""Generate a personalized cold email.

**Prospect**: {prospect_name}
**Company**: {company_name}

**Website Analysis**:
{website_analysis}

**Our Service**:
{our_service_description}

Write the email (subject + body). Format as:
SUBJECT: [subject line]
BODY: [email body]"""
            )
        ]

        return await self.complete(
            task_type=TaskType.EMAIL_BODY,
            messages=messages,
            lead_id=lead_id,
            lead_value=lead_value,
            temperature=0.8  # Higher creativity for emails
        )
