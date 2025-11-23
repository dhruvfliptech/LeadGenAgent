"""
Conversation AI Service - Analyzes email replies and generates contextual responses.

Features:
- Sentiment analysis and intent detection
- Reply generation using AI-GYM multi-model system
- Context-aware responses based on conversation history
- Reply quality evaluation and improvement suggestions
- Integration with vector store for similar conversation retrieval

Based on UX_FLOW_CONVERSATIONS.md requirements.
"""

import json
import re
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

from app.services.ai_mvp.ai_council import AICouncil, Message
from app.services.ai_mvp.semantic_router import TaskType
from app.services.vector_store import VectorStore

logger = structlog.get_logger(__name__)


class Sentiment(str):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Intent(str):
    """Reply intent categories."""
    QUESTION = "question"
    INTEREST = "interest"
    OBJECTION = "objection"
    SCHEDULING = "scheduling"
    REJECTION = "rejection"
    GENERIC = "generic"


class ReplyAnalysis(BaseModel):
    """Analysis of an incoming reply."""
    sentiment: Literal["positive", "neutral", "negative"]
    sentiment_confidence: float = Field(ge=0.0, le=1.0)
    intent: Literal["question", "interest", "objection", "scheduling", "rejection", "generic"]
    intent_confidence: float = Field(ge=0.0, le=1.0)
    engagement_score: float = Field(ge=0.0, le=1.0, description="0=disengaged, 1=highly engaged")
    key_topics: List[str] = Field(default_factory=list, description="Topics mentioned in reply")
    questions_asked: List[str] = Field(default_factory=list, description="Specific questions they asked")
    urgency_level: Literal["low", "medium", "high"] = "medium"
    summary: str = Field(description="Brief summary of their reply")


class GeneratedReply(BaseModel):
    """AI-generated reply with metadata."""
    content: str = Field(description="Email body text")
    confidence_score: float = Field(ge=0.0, le=1.0, description="AI confidence in reply quality")
    tone: Literal["professional", "friendly", "casual", "formal"] = "professional"
    model_used: str = Field(description="Model that generated this reply")
    reasoning: str = Field(description="Why this response was chosen")
    key_points: List[str] = Field(default_factory=list, description="Main points covered")
    call_to_action: Optional[str] = None
    estimated_response_time: Optional[str] = None


class ReplyImprovement(BaseModel):
    """Suggestions for improving a draft reply."""
    overall_score: float = Field(ge=0.0, le=1.0, description="Quality score of draft")
    tone_suggestions: List[str] = Field(default_factory=list)
    clarity_suggestions: List[str] = Field(default_factory=list)
    issues: List[Dict[str, str]] = Field(default_factory=list, description="Flagged problems")
    improved_version: Optional[str] = None
    word_count: int
    reading_level: str


class ConversationMessage(BaseModel):
    """Single message in conversation history."""
    role: Literal["user", "lead"]
    content: str
    timestamp: datetime
    message_id: Optional[str] = None


class ConversationAI:
    """
    AI-powered conversation handler for email replies.

    Integrates with:
    - AI Council for multi-model routing
    - Vector Store for similar conversation retrieval
    - Existing AI-GYM tracking system
    """

    def __init__(
        self,
        ai_council: AICouncil,
        vector_store: VectorStore
    ):
        """Initialize conversation AI."""
        self.ai_council = ai_council
        self.vector_store = vector_store

    async def analyze_reply(
        self,
        reply_text: str,
        conversation_history: Optional[List[ConversationMessage]] = None,
        lead_id: Optional[int] = None
    ) -> ReplyAnalysis:
        """
        Analyze an incoming reply for sentiment, intent, and engagement.

        Args:
            reply_text: The reply email body
            conversation_history: Previous messages in thread
            lead_id: Associated lead ID

        Returns:
            ReplyAnalysis with extracted insights
        """
        logger.info(
            "conversation_ai.analyze_reply",
            reply_length=len(reply_text),
            has_history=bool(conversation_history),
            lead_id=lead_id
        )

        # Build context-aware analysis prompt
        context = self._build_history_context(conversation_history) if conversation_history else ""

        analysis_prompt = f"""Analyze this email reply and extract structured insights.

{context}

**Reply to Analyze**:
{reply_text}

**Task**: Extract the following as JSON:
1. **sentiment**: "positive", "neutral", or "negative"
2. **sentiment_confidence**: 0.0-1.0
3. **intent**: "question", "interest", "objection", "scheduling", "rejection", or "generic"
4. **intent_confidence**: 0.0-1.0
5. **engagement_score**: 0.0-1.0 (how engaged/interested they seem)
6. **key_topics**: List of main topics mentioned
7. **questions_asked**: List of specific questions they asked (empty if none)
8. **urgency_level**: "low", "medium", or "high"
9. **summary**: 1-2 sentence summary of their message

Return ONLY valid JSON matching this schema. Be accurate and concise."""

        messages = [
            Message(role="system", content="You are an expert email analyst. Extract structured insights from customer replies."),
            Message(role="user", content=analysis_prompt)
        ]

        # Use cheap model for analysis (simple classification task)
        response = await self.ai_council.complete(
            task_type=TaskType.CATEGORY_CLASSIFICATION,
            messages=messages,
            lead_id=lead_id,
            temperature=0.3  # Low temp for consistent analysis
        )

        # Parse JSON response
        try:
            analysis_data = self._extract_json(response.content)
            return ReplyAnalysis(**analysis_data)
        except Exception as e:
            logger.error(
                "conversation_ai.parse_analysis_failed",
                error=str(e),
                response_preview=response.content[:200]
            )
            # Fallback to basic analysis
            return ReplyAnalysis(
                sentiment="neutral",
                sentiment_confidence=0.5,
                intent="generic",
                intent_confidence=0.5,
                engagement_score=0.5,
                key_topics=[],
                questions_asked=[],
                urgency_level="medium",
                summary="Analysis parsing failed - manual review recommended"
            )

    async def generate_reply(
        self,
        incoming_reply: str,
        reply_analysis: ReplyAnalysis,
        conversation_history: List[ConversationMessage],
        lead_context: Dict[str, Any],
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None,
        tone_preference: str = "professional"
    ) -> GeneratedReply:
        """
        Generate a contextual, personalized reply.

        Args:
            incoming_reply: The reply we're responding to
            reply_analysis: Analysis from analyze_reply()
            conversation_history: Full conversation thread
            lead_context: Website analysis, company info, etc.
            lead_id: Lead ID for tracking
            lead_value: Estimated deal value (affects model routing)
            tone_preference: Desired tone ("professional", "friendly", etc.)

        Returns:
            GeneratedReply with AI-generated response
        """
        logger.info(
            "conversation_ai.generate_reply",
            lead_id=lead_id,
            lead_value=lead_value,
            intent=reply_analysis.intent,
            sentiment=reply_analysis.sentiment
        )

        # Retrieve similar successful conversations for context
        similar_convos = await self.vector_store.find_similar_conversations(
            query_text=incoming_reply,
            intent=reply_analysis.intent,
            limit=3
        )

        # Build comprehensive context
        history_context = self._build_history_context(conversation_history)
        similar_context = self._build_similar_conversations_context(similar_convos)
        lead_info = self._format_lead_context(lead_context)

        # Build generation prompt
        generation_prompt = f"""You are a professional sales representative replying to a potential customer's email.

**CONTEXT**:

{history_context}

**THEIR LATEST REPLY**:
{incoming_reply}

**ANALYSIS**:
- Sentiment: {reply_analysis.sentiment} ({reply_analysis.sentiment_confidence:.0%} confident)
- Intent: {reply_analysis.intent}
- Key topics: {', '.join(reply_analysis.key_topics)}
- Questions: {', '.join(reply_analysis.questions_asked) if reply_analysis.questions_asked else 'None'}
- Urgency: {reply_analysis.urgency_level}
- Summary: {reply_analysis.summary}

**LEAD INFORMATION**:
{lead_info}

**SIMILAR SUCCESSFUL CONVERSATIONS**:
{similar_context}

**TASK**: Write a personalized reply that:
1. Directly addresses their {reply_analysis.intent} (intent)
2. Answers all their questions: {', '.join(reply_analysis.questions_asked) if reply_analysis.questions_asked else 'N/A'}
3. References specific details from their business/website
4. Maintains {tone_preference} tone
5. Includes a clear call-to-action
6. Keeps length under 200 words
7. Sounds natural, not templated

**BEST PRACTICES**:
- Start with acknowledgment of their reply
- Use their name if known
- Be specific, not generic
- Show you understand their business
- Make next steps clear and easy
- Avoid: "I hope this email finds you well", "Just following up", overly salesy language

Write ONLY the email body (no subject line). Be personable and helpful."""

        messages = [
            Message(
                role="system",
                content="You are an expert email copywriter specializing in B2B sales. Write natural, personalized replies that convert."
            ),
            Message(role="user", content=generation_prompt)
        ]

        # Use CONVERSATION_RESPONSE task (premium model for critical customer-facing content)
        response = await self.ai_council.complete(
            task_type=TaskType.CONVERSATION_RESPONSE,
            messages=messages,
            lead_id=lead_id,
            lead_value=lead_value,
            temperature=0.8  # Higher creativity for emails
        )

        # Calculate confidence score based on multiple factors
        confidence = self._calculate_reply_confidence(
            reply_analysis=reply_analysis,
            response_length=len(response.content),
            has_questions=bool(reply_analysis.questions_asked),
            has_similar_examples=len(similar_convos) > 0
        )

        # Extract key points and CTA
        key_points = self._extract_key_points(response.content)
        cta = self._extract_call_to_action(response.content)

        return GeneratedReply(
            content=response.content,
            confidence_score=confidence,
            tone=tone_preference,
            model_used=response.model_used,
            reasoning=response.route_decision.reasoning,
            key_points=key_points,
            call_to_action=cta,
            estimated_response_time=self._estimate_response_time(reply_analysis.urgency_level)
        )

    async def suggest_improvements(
        self,
        draft_reply: str,
        original_message: str,
        reply_analysis: ReplyAnalysis,
        lead_id: Optional[int] = None
    ) -> ReplyImprovement:
        """
        Analyze a user's draft reply and suggest improvements.

        Args:
            draft_reply: User's draft email
            original_message: The message they're replying to
            reply_analysis: Analysis of original message
            lead_id: Lead ID for tracking

        Returns:
            ReplyImprovement with suggestions
        """
        logger.info(
            "conversation_ai.suggest_improvements",
            draft_length=len(draft_reply),
            lead_id=lead_id
        )

        improvement_prompt = f"""Analyze this draft email reply and provide improvement suggestions.

**ORIGINAL MESSAGE**:
{original_message}

**DRAFT REPLY**:
{draft_reply}

**CONTEXT**:
- Their intent: {reply_analysis.intent}
- Their sentiment: {reply_analysis.sentiment}
- Questions they asked: {', '.join(reply_analysis.questions_asked) if reply_analysis.questions_asked else 'None'}

**TASK**: Evaluate the draft and return JSON with:
1. **overall_score**: 0.0-1.0 (quality rating)
2. **tone_suggestions**: List of tone adjustments (e.g., "Too formal, try being more conversational")
3. **clarity_suggestions**: List of clarity improvements (e.g., "Unclear what next steps are")
4. **issues**: List of problems found, each with "type" and "description"
   - Types: "too_long", "too_pushy", "unclear_cta", "unanswered_question", "typo", "tone_mismatch"
5. **improved_version**: Rewritten version addressing all issues (or null if minor issues)
6. **word_count**: Number of words in draft
7. **reading_level**: "elementary", "middle_school", "high_school", "college", "professional"

Return ONLY valid JSON."""

        messages = [
            Message(
                role="system",
                content="You are an expert email editor. Provide constructive, specific feedback on draft emails."
            ),
            Message(role="user", content=improvement_prompt)
        ]

        # Use cheap model for evaluation
        response = await self.ai_council.complete(
            task_type=TaskType.CATEGORY_CLASSIFICATION,
            messages=messages,
            lead_id=lead_id,
            temperature=0.3
        )

        try:
            improvement_data = self._extract_json(response.content)
            return ReplyImprovement(**improvement_data)
        except Exception as e:
            logger.error(
                "conversation_ai.parse_improvements_failed",
                error=str(e),
                response_preview=response.content[:200]
            )
            # Fallback
            return ReplyImprovement(
                overall_score=0.7,
                tone_suggestions=["Review manually - automated analysis failed"],
                clarity_suggestions=[],
                issues=[],
                word_count=len(draft_reply.split()),
                reading_level="professional"
            )

    async def regenerate_reply(
        self,
        incoming_reply: str,
        reply_analysis: ReplyAnalysis,
        conversation_history: List[ConversationMessage],
        lead_context: Dict[str, Any],
        tone_adjustment: Literal["more_formal", "more_casual", "shorter", "add_humor"],
        lead_id: Optional[int] = None,
        lead_value: Optional[float] = None
    ) -> GeneratedReply:
        """
        Regenerate reply with specific tone adjustments.

        Args:
            incoming_reply: Original reply
            reply_analysis: Analysis
            conversation_history: Conversation context
            lead_context: Lead information
            tone_adjustment: How to adjust the tone
            lead_id: Lead ID
            lead_value: Deal value

        Returns:
            Regenerated reply
        """
        # Map tone adjustments to instructions
        tone_instructions = {
            "more_formal": "Use formal business language. Avoid contractions. Be respectful and professional.",
            "more_casual": "Use conversational language. Include contractions. Be friendly and approachable.",
            "shorter": "Keep response under 100 words. Be concise and direct. Cut unnecessary details.",
            "add_humor": "Include light, professional humor. Keep it tasteful and relevant. Don't force it."
        }

        instruction = tone_instructions.get(tone_adjustment, "")

        # Build modified prompt
        history_context = self._build_history_context(conversation_history)
        lead_info = self._format_lead_context(lead_context)

        regeneration_prompt = f"""Regenerate this email reply with a specific tone adjustment.

**CONTEXT**:
{history_context}

**THEIR REPLY**:
{incoming_reply}

**LEAD INFO**:
{lead_info}

**TONE ADJUSTMENT**: {tone_adjustment}
**INSTRUCTION**: {instruction}

Write a new reply that addresses their message while following the tone instruction above.
Keep under 200 words. Include a clear call-to-action."""

        messages = [
            Message(
                role="system",
                content="You are an expert email copywriter. Regenerate replies with specific tone adjustments."
            ),
            Message(role="user", content=regeneration_prompt)
        ]

        response = await self.ai_council.complete(
            task_type=TaskType.CONVERSATION_RESPONSE,
            messages=messages,
            lead_id=lead_id,
            lead_value=lead_value,
            temperature=0.9  # Higher creativity for variations
        )

        confidence = self._calculate_reply_confidence(
            reply_analysis=reply_analysis,
            response_length=len(response.content),
            has_questions=bool(reply_analysis.questions_asked),
            has_similar_examples=False
        )

        return GeneratedReply(
            content=response.content,
            confidence_score=confidence * 0.9,  # Slightly lower for regenerated versions
            tone=tone_adjustment,
            model_used=response.model_used,
            reasoning=f"Regenerated with {tone_adjustment} adjustment: {instruction}",
            key_points=self._extract_key_points(response.content),
            call_to_action=self._extract_call_to_action(response.content)
        )

    # Helper methods

    def _build_history_context(self, history: List[ConversationMessage]) -> str:
        """Format conversation history for prompts."""
        if not history:
            return "**No previous conversation history**"

        context_lines = ["**CONVERSATION HISTORY**:"]
        for msg in history[-5:]:  # Last 5 messages only
            role_label = "YOU" if msg.role == "user" else "THEM"
            timestamp = msg.timestamp.strftime("%b %d, %I:%M %p")
            context_lines.append(f"\n[{role_label} - {timestamp}]:")
            context_lines.append(msg.content[:300])  # Truncate long messages

        return "\n".join(context_lines)

    def _build_similar_conversations_context(self, similar: List[Dict[str, Any]]) -> str:
        """Format similar conversation examples."""
        if not similar:
            return "**No similar conversations found**"

        context_lines = ["**SIMILAR SUCCESSFUL CONVERSATIONS**:"]
        for i, convo in enumerate(similar, 1):
            context_lines.append(f"\nExample {i} (Similarity: {convo.get('similarity', 0):.0%}):")
            context_lines.append(f"Their message: {convo.get('their_message', '')[:200]}")
            context_lines.append(f"Our response: {convo.get('our_response', '')[:200]}")
            context_lines.append(f"Outcome: {convo.get('outcome', 'Unknown')}")

        return "\n".join(context_lines)

    def _format_lead_context(self, context: Dict[str, Any]) -> str:
        """Format lead context information."""
        lines = []
        if context.get("company_name"):
            lines.append(f"Company: {context['company_name']}")
        if context.get("website"):
            lines.append(f"Website: {context['website']}")
        if context.get("industry"):
            lines.append(f"Industry: {context['industry']}")
        if context.get("website_analysis"):
            lines.append(f"\nWebsite Analysis:\n{context['website_analysis'][:500]}")
        if context.get("pain_points"):
            lines.append(f"\nIdentified Pain Points:")
            for point in context['pain_points'][:3]:
                lines.append(f"- {point}")

        return "\n".join(lines) if lines else "**No lead context available**"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text (handles markdown code blocks)."""
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try to find raw JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        # Fallback: parse entire text
        return json.loads(text)

    def _calculate_reply_confidence(
        self,
        reply_analysis: ReplyAnalysis,
        response_length: int,
        has_questions: bool,
        has_similar_examples: bool
    ) -> float:
        """Calculate confidence score for generated reply."""
        confidence = 0.7  # Base confidence

        # Boost for clear intent
        if reply_analysis.intent_confidence > 0.8:
            confidence += 0.1

        # Boost for positive sentiment
        if reply_analysis.sentiment == "positive":
            confidence += 0.05

        # Penalty for questions without similar examples
        if has_questions and not has_similar_examples:
            confidence -= 0.1

        # Penalty for very short or very long responses
        if response_length < 100 or response_length > 1000:
            confidence -= 0.05

        # Boost for high engagement
        if reply_analysis.engagement_score > 0.7:
            confidence += 0.1

        return max(0.0, min(1.0, confidence))

    def _extract_key_points(self, reply_text: str) -> List[str]:
        """Extract main points from reply."""
        # Simple heuristic: find sentences with key action words or numbered lists
        key_words = ["will", "can", "would", "suggest", "recommend", "include", "provide"]
        sentences = reply_text.split('.')

        points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if any(word in sentence.lower() for word in key_words):
                points.append(sentence)
            # Find numbered lists
            if re.match(r'^\d+\.', sentence.strip()):
                points.append(sentence)

        return points[:5]  # Max 5 key points

    def _extract_call_to_action(self, reply_text: str) -> Optional[str]:
        """Extract call-to-action from reply."""
        cta_patterns = [
            r'(Would you like to.*?\?)',
            r'(Can we schedule.*?\?)',
            r'(Let me know.*?\.)',
            r'(Feel free to.*?\.)',
            r'(Please.*?\.)'
        ]

        for pattern in cta_patterns:
            match = re.search(pattern, reply_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: last sentence might be CTA
        sentences = [s.strip() for s in reply_text.split('.') if s.strip()]
        if sentences:
            return sentences[-1]

        return None

    def _estimate_response_time(self, urgency: str) -> str:
        """Estimate expected response time based on urgency."""
        mapping = {
            "high": "within 2 hours",
            "medium": "within 24 hours",
            "low": "within 2-3 days"
        }
        return mapping.get(urgency, "within 24 hours")
