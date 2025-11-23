"""
Conversation AI API Endpoints.

Provides REST endpoints for:
- Analyzing incoming replies
- Generating AI responses
- Improving draft replies
- Regenerating with different tones
- Retrieving similar conversations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.services.conversation_ai import (
    ConversationAI,
    ReplyAnalysis,
    GeneratedReply,
    ReplyImprovement,
    ConversationMessage
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilConfig
from app.services.ai_mvp.ai_gym_tracker import AIGymTracker
from app.services.vector_store import VectorStore

import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversation-ai"])


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request to analyze a reply."""
    reply_text: str = Field(min_length=1, max_length=10000)
    conversation_history: Optional[List[Dict[str, Any]]] = None
    lead_id: Optional[int] = None


class GenerateRequest(BaseModel):
    """Request to generate a reply."""
    incoming_reply: str
    reply_analysis: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    lead_context: Dict[str, Any]
    lead_id: Optional[int] = None
    lead_value: Optional[float] = None
    tone_preference: str = "professional"


class ImproveRequest(BaseModel):
    """Request to improve a draft."""
    draft_reply: str
    original_message: str
    reply_analysis: Dict[str, Any]
    lead_id: Optional[int] = None


class RegenerateRequest(BaseModel):
    """Request to regenerate with different tone."""
    incoming_reply: str
    reply_analysis: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    lead_context: Dict[str, Any]
    tone_adjustment: str = Field(
        regex="^(more_formal|more_casual|shorter|add_humor)$"
    )
    lead_id: Optional[int] = None
    lead_value: Optional[float] = None


class SimilarConversationsRequest(BaseModel):
    """Request to find similar conversations."""
    query_text: str
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=20)


# Dependency: Get ConversationAI instance
async def get_conversation_ai(db: AsyncSession = Depends(get_db)) -> ConversationAI:
    """
    Create ConversationAI instance with dependencies.

    This is a dependency function that initializes all required services.
    """
    # Initialize AI Council
    council_config = AICouncilConfig(
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        default_temperature=0.7,
        timeout_seconds=30
    )
    gym_tracker = AIGymTracker(db)
    ai_council = AICouncil(config=council_config, gym_tracker=gym_tracker)

    # Initialize Vector Store
    vector_store = VectorStore(
        db_session=db,
        openai_api_key=settings.OPENAI_API_KEY
    )

    # Create ConversationAI
    conversation_ai = ConversationAI(
        ai_council=ai_council,
        vector_store=vector_store
    )

    return conversation_ai


# API Endpoints

@router.post("/analyze", response_model=ReplyAnalysis)
async def analyze_reply(
    request: AnalyzeRequest,
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Analyze an incoming email reply.

    Extracts:
    - Sentiment (positive/neutral/negative)
    - Intent (question/interest/objection/etc.)
    - Engagement score (0-1)
    - Key topics and questions
    - Urgency level

    **Example Request**:
    ```json
    {
      "reply_text": "Thanks for the demo! How does the HubSpot integration work?",
      "lead_id": 123
    }
    ```

    **Example Response**:
    ```json
    {
      "sentiment": "positive",
      "sentiment_confidence": 0.9,
      "intent": "question",
      "intent_confidence": 0.95,
      "engagement_score": 0.85,
      "key_topics": ["HubSpot integration"],
      "questions_asked": ["How does HubSpot integration work?"],
      "urgency_level": "high",
      "summary": "Interested prospect asking about HubSpot integration"
    }
    ```
    """
    try:
        logger.info(
            "conversation_ai.analyze_request",
            reply_length=len(request.reply_text),
            lead_id=request.lead_id
        )

        # Parse conversation history
        history = None
        if request.conversation_history:
            history = [
                ConversationMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in request.conversation_history
            ]

        # Analyze
        analysis = await conversation_ai.analyze_reply(
            reply_text=request.reply_text,
            conversation_history=history,
            lead_id=request.lead_id
        )

        logger.info(
            "conversation_ai.analyze_success",
            sentiment=analysis.sentiment,
            intent=analysis.intent,
            engagement=analysis.engagement_score
        )

        return analysis

    except Exception as e:
        logger.error(
            "conversation_ai.analyze_error",
            error=str(e),
            lead_id=request.lead_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze reply: {str(e)}"
        )


@router.post("/generate", response_model=GeneratedReply)
async def generate_reply(
    request: GenerateRequest,
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Generate an AI-powered reply to an email.

    Uses:
    - Conversation history for context
    - Lead context (website analysis, company info)
    - Similar successful conversations
    - Premium AI model for quality

    **Example Request**:
    ```json
    {
      "incoming_reply": "How does the HubSpot integration work?",
      "reply_analysis": {
        "sentiment": "positive",
        "intent": "question",
        "engagement_score": 0.85,
        ...
      },
      "conversation_history": [...],
      "lead_context": {
        "company_name": "Acme Corp",
        "website_analysis": "..."
      },
      "lead_value": 25000
    }
    ```

    **Example Response**:
    ```json
    {
      "content": "Hi John,\\n\\nGreat question! Our HubSpot integration...",
      "confidence_score": 0.88,
      "tone": "professional",
      "model_used": "anthropic/claude-3.5-sonnet",
      "reasoning": "High-value lead using premium model",
      "key_points": ["Native bidirectional sync", "Real-time updates"],
      "call_to_action": "Would Tuesday at 2pm work for a demo?"
    }
    ```
    """
    try:
        logger.info(
            "conversation_ai.generate_request",
            lead_id=request.lead_id,
            lead_value=request.lead_value,
            tone=request.tone_preference
        )

        # Parse analysis
        analysis = ReplyAnalysis(**request.reply_analysis)

        # Parse history
        history = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"])
            )
            for msg in request.conversation_history
        ]

        # Generate reply
        reply = await conversation_ai.generate_reply(
            incoming_reply=request.incoming_reply,
            reply_analysis=analysis,
            conversation_history=history,
            lead_context=request.lead_context,
            lead_id=request.lead_id,
            lead_value=request.lead_value,
            tone_preference=request.tone_preference
        )

        logger.info(
            "conversation_ai.generate_success",
            confidence=reply.confidence_score,
            model=reply.model_used,
            content_length=len(reply.content)
        )

        return reply

    except Exception as e:
        logger.error(
            "conversation_ai.generate_error",
            error=str(e),
            lead_id=request.lead_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reply: {str(e)}"
        )


@router.post("/improve", response_model=ReplyImprovement)
async def improve_draft(
    request: ImproveRequest,
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Suggest improvements to a draft reply.

    Analyzes:
    - Overall quality score
    - Tone issues (too formal, too casual)
    - Clarity problems (vague, unclear CTA)
    - Common issues (too long, too pushy)

    Returns improved version if major issues found.

    **Example Request**:
    ```json
    {
      "draft_reply": "I hope this email finds you well...",
      "original_message": "How does integration work?",
      "reply_analysis": {...}
    }
    ```

    **Example Response**:
    ```json
    {
      "overall_score": 0.45,
      "tone_suggestions": ["Remove generic opening"],
      "clarity_suggestions": ["Be more specific about integration"],
      "issues": [
        {"type": "too_generic", "description": "Opening line is cliché"}
      ],
      "improved_version": "Hi John! Our HubSpot integration...",
      "word_count": 89,
      "reading_level": "professional"
    }
    ```
    """
    try:
        logger.info(
            "conversation_ai.improve_request",
            draft_length=len(request.draft_reply),
            lead_id=request.lead_id
        )

        # Parse analysis
        analysis = ReplyAnalysis(**request.reply_analysis)

        # Get improvements
        improvements = await conversation_ai.suggest_improvements(
            draft_reply=request.draft_reply,
            original_message=request.original_message,
            reply_analysis=analysis,
            lead_id=request.lead_id
        )

        logger.info(
            "conversation_ai.improve_success",
            score=improvements.overall_score,
            issues_count=len(improvements.issues)
        )

        return improvements

    except Exception as e:
        logger.error(
            "conversation_ai.improve_error",
            error=str(e),
            lead_id=request.lead_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve draft: {str(e)}"
        )


@router.post("/regenerate", response_model=GeneratedReply)
async def regenerate_reply(
    request: RegenerateRequest,
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Regenerate reply with a different tone.

    Tone options:
    - **more_formal**: Professional business language
    - **more_casual**: Conversational and friendly
    - **shorter**: Concise version under 100 words
    - **add_humor**: Light, tasteful humor

    **Example Request**:
    ```json
    {
      "incoming_reply": "...",
      "reply_analysis": {...},
      "conversation_history": [...],
      "lead_context": {...},
      "tone_adjustment": "more_casual"
    }
    ```
    """
    try:
        logger.info(
            "conversation_ai.regenerate_request",
            tone_adjustment=request.tone_adjustment,
            lead_id=request.lead_id
        )

        # Parse analysis
        analysis = ReplyAnalysis(**request.reply_analysis)

        # Parse history
        history = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"])
            )
            for msg in request.conversation_history
        ]

        # Regenerate
        reply = await conversation_ai.regenerate_reply(
            incoming_reply=request.incoming_reply,
            reply_analysis=analysis,
            conversation_history=history,
            lead_context=request.lead_context,
            tone_adjustment=request.tone_adjustment,
            lead_id=request.lead_id,
            lead_value=request.lead_value
        )

        logger.info(
            "conversation_ai.regenerate_success",
            confidence=reply.confidence_score,
            tone=request.tone_adjustment
        )

        return reply

    except Exception as e:
        logger.error(
            "conversation_ai.regenerate_error",
            error=str(e),
            lead_id=request.lead_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate reply: {str(e)}"
        )


@router.post("/similar", response_model=List[Dict[str, Any]])
async def find_similar_conversations(
    request: SimilarConversationsRequest,
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Find similar successful conversations.

    Uses vector similarity search to find conversations with:
    - Similar content/intent
    - Positive outcomes
    - Relevant context

    **Example Request**:
    ```json
    {
      "query_text": "How does the HubSpot integration work?",
      "intent": "question",
      "limit": 3
    }
    ```

    **Example Response**:
    ```json
    [
      {
        "conversation_id": 123,
        "their_message": "Does this integrate with Salesforce?",
        "our_response": "Yes! We have native Salesforce integration...",
        "intent": "question",
        "sentiment": "positive",
        "outcome": "success",
        "similarity": 0.87
      }
    ]
    ```
    """
    try:
        logger.info(
            "conversation_ai.similar_request",
            query_length=len(request.query_text),
            intent=request.intent,
            limit=request.limit
        )

        # Find similar
        similar = await conversation_ai.vector_store.find_similar_conversations(
            query_text=request.query_text,
            intent=request.intent,
            sentiment=request.sentiment,
            limit=request.limit
        )

        logger.info(
            "conversation_ai.similar_success",
            results_count=len(similar)
        )

        return similar

    except Exception as e:
        logger.error(
            "conversation_ai.similar_error",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar conversations: {str(e)}"
        )


@router.get("/stats")
async def get_conversation_stats(
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Get conversation AI statistics.

    Returns:
    - Total conversations processed
    - Success rate
    - Average confidence scores
    - Model performance metrics

    **Example Response**:
    ```json
    {
      "total_conversations": 1247,
      "total_messages": 3891,
      "successful_conversations": 387,
      "success_rate": 31.0,
      "avg_conversion_value": 18750.50,
      "unique_intents": 6
    }
    ```
    """
    try:
        stats = await conversation_ai.vector_store.get_conversation_stats()
        return stats

    except Exception as e:
        logger.error("conversation_ai.stats_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# Health check
@router.get("/health")
async def health_check():
    """Health check for conversation AI service."""
    return {
        "status": "healthy",
        "service": "conversation-ai",
        "version": "1.0.0"
    }
