"""
AI Reply Generator service.
Generates intelligent email responses using OpenRouter API.
"""

import logging
import json
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import (
    Conversation, ConversationMessage, AISuggestion,
    MessageDirection, SuggestionStatus
)
from app.models.leads import Lead
from app.core.config import settings
from .openrouter_client import get_openrouter_client

logger = logging.getLogger(__name__)


class AIReplyGenerator:
    """
    Generates AI-powered email reply suggestions.
    Uses conversation history and lead context to create personalized responses.
    """

    def __init__(self):
        self._ai_client = get_openrouter_client()
        logger.info("AI Reply Generator initialized with OpenRouter client")

    async def generate_reply(
        self,
        session: AsyncSession,
        conversation_id: int,
        message_id: int
    ) -> Optional[AISuggestion]:
        """
        Generate an AI reply suggestion for a conversation message.

        Args:
            session: Database session
            conversation_id: Conversation ID
            message_id: Message ID to reply to

        Returns:
            AISuggestion or None if generation failed
        """
        try:
            # Load conversation with messages
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            # Load the message to reply to
            result = await session.execute(
                select(ConversationMessage).where(ConversationMessage.id == message_id)
            )
            message = result.scalar_one_or_none()

            if not message:
                logger.error(f"Message {message_id} not found")
                return None

            # Load lead
            result = await session.execute(
                select(Lead).where(Lead.id == conversation.lead_id)
            )
            lead = result.scalar_one_or_none()

            # Build context
            context = await self._build_context(session, conversation, lead)

            # Generate reply using AI
            ai_response = await self._call_ai_api(context, message)

            if not ai_response:
                logger.error("AI API returned no response")
                return None

            # Create AI suggestion
            suggestion = AISuggestion(
                conversation_id=conversation_id,
                reply_to_message_id=message_id,
                suggested_subject=ai_response.get('subject', f"Re: {conversation.subject}"),
                suggested_body=ai_response['body'],
                confidence_score=ai_response.get('confidence', 0.75),
                sentiment_analysis=ai_response.get('sentiment_analysis'),
                context_used=context.get('context_sources', []),
                ai_reasoning=ai_response.get('reasoning'),
                ai_provider=self.provider,
                ai_model=ai_response.get('model'),
                tokens_used=ai_response.get('tokens_used'),
                ai_cost=ai_response.get('cost'),
                status=SuggestionStatus.PENDING
            )

            session.add(suggestion)
            await session.commit()

            logger.info(f"Created AI suggestion {suggestion.id} for conversation {conversation_id}")

            return suggestion

        except Exception as e:
            logger.error(f"Error generating AI reply: {e}", exc_info=True)
            return None

    async def _build_context(
        self,
        session: AsyncSession,
        conversation: Conversation,
        lead: Optional[Lead]
    ) -> Dict:
        """
        Build context for AI prompt.

        Args:
            session: Database session
            conversation: Conversation
            lead: Lead (optional)

        Returns:
            Context dictionary
        """
        # Get conversation history
        result = await session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.id)
            .order_by(ConversationMessage.sent_at)
        )
        messages = result.scalars().all()

        # Build message history
        message_history = []
        for msg in messages:
            message_history.append({
                'direction': msg.direction.value,
                'from': msg.sender_email,
                'body': msg.body_text or msg.body_html,
                'sent_at': msg.sent_at.isoformat()
            })

        context = {
            'conversation': {
                'subject': conversation.subject,
                'message_count': len(messages)
            },
            'message_history': message_history,
            'context_sources': ['conversation_history']
        }

        # Add lead context
        if lead:
            context['lead'] = {
                'name': lead.contact_name or 'there',
                'email': lead.email or lead.reply_email,
                'title': lead.title,
                'location': lead.location.name if lead.location else None
            }
            context['context_sources'].append('lead_profile')

            # Add AI analysis if available
            if lead.ai_analysis:
                context['website_analysis'] = lead.ai_analysis
                context['context_sources'].append('website_analysis')

        # Add user profile
        context['user'] = {
            'name': settings.USER_NAME or 'User',
            'email': settings.USER_EMAIL,
            'phone': settings.USER_PHONE
        }

        return context

    async def _call_ai_api(self, context: Dict, message: ConversationMessage) -> Optional[Dict]:
        """
        Call AI API to generate response using OpenRouter.

        Args:
            context: Context dictionary
            message: Message to reply to

        Returns:
            AI response dictionary
        """
        try:
            prompt = self._build_prompt(context, message)

            system_message = "You are a helpful email assistant that generates professional, personalized email responses. Always return valid JSON matching the specified format."

            # Generate response using OpenRouter
            response_text = await self._ai_client.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS
            )

            # Parse JSON response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Fallback: return a structured response with the raw text
                    result = {
                        "subject": f"Re: {context['conversation']['subject']}",
                        "body": response_text,
                        "confidence": 0.7,
                        "reasoning": "Response generated but JSON parsing failed",
                        "sentiment_analysis": {
                            "sentiment": "neutral",
                            "intent": "response",
                            "urgency": "medium"
                        }
                    }

            # Add model metadata
            result['model'] = settings.AI_MODEL_DEFAULT
            result['tokens_used'] = len(response_text.split()) * 1.3  # Rough estimate
            result['cost'] = self._estimate_cost(result['tokens_used'])

            return result

        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}", exc_info=True)
            return None

    def _build_prompt(self, context: Dict, message: ConversationMessage) -> str:
        """
        Build AI prompt for reply generation.

        Args:
            context: Context dictionary
            message: Message to reply to

        Returns:
            Prompt string
        """
        lead_name = context.get('lead', {}).get('name', 'there')
        user_name = context['user']['name']

        prompt = f"""You are helping {user_name} respond to an email from {lead_name}.

CONVERSATION SUBJECT: {context['conversation']['subject']}

CONVERSATION HISTORY:
"""

        # Add message history
        for msg in context['message_history']:
            direction = "You" if msg['direction'] == 'outbound' else lead_name
            prompt += f"\n{direction} ({msg['sent_at']}):\n{msg['body']}\n"

        prompt += f"""

CURRENT MESSAGE TO REPLY TO (from {lead_name}):
{message.body_text or message.body_html}

"""

        # Add additional context
        if 'website_analysis' in context:
            prompt += f"\nWEBSITE ANALYSIS:\n{context['website_analysis']}\n"

        prompt += f"""
YOUR TASK:
Generate a professional, friendly, and helpful email response to {lead_name}'s message.

GUIDELINES:
1. Be conversational and warm while maintaining professionalism
2. Answer their questions directly and clearly
3. Reference previous conversation points naturally
4. Use {user_name}'s voice and tone
5. Keep response concise (2-3 paragraphs max)
6. Include a clear call-to-action if appropriate
7. Sign off as {user_name}

RESPONSE FORMAT (JSON):
{{
    "subject": "Re: [subject]",
    "body": "email body text here",
    "confidence": 0.85,
    "reasoning": "why you chose this response",
    "sentiment_analysis": {{
        "sentiment": "positive/neutral/negative",
        "intent": "request_info/interested/not_interested/etc",
        "urgency": "high/medium/low"
    }}
}}

Generate the reply now:"""

        return prompt

    def _estimate_cost(self, tokens: float) -> float:
        """
        Estimate API cost based on token usage.

        Args:
            tokens: Number of tokens used

        Returns:
            Estimated cost in USD
        """
        # OpenRouter pricing varies by model, using GPT-4 as baseline
        # GPT-4: ~$0.03 per 1K input tokens, $0.06 per 1K output
        # Simplified: assume 50/50 split
        return (tokens / 1000) * 0.045

    async def generate_follow_up(
        self,
        session: AsyncSession,
        conversation_id: int,
        days_since_last_reply: int = 3
    ) -> Optional[AISuggestion]:
        """
        Generate a follow-up email suggestion.

        Args:
            session: Database session
            conversation_id: Conversation ID
            days_since_last_reply: Days since last reply (for context)

        Returns:
            AISuggestion or None if generation failed
        """
        try:
            # Load conversation
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            # Load lead
            result = await session.execute(
                select(Lead).where(Lead.id == conversation.lead_id)
            )
            lead = result.scalar_one_or_none()

            # Build context
            context = await self._build_context(session, conversation, lead)
            lead_name = context.get('lead', {}).get('name', 'there')
            user_name = context['user']['name']

            # Build follow-up prompt
            prompt = f"""Generate a professional follow-up email for a conversation that hasn't received a reply in {days_since_last_reply} days.

CONVERSATION SUBJECT: {context['conversation']['subject']}

CONVERSATION HISTORY:
"""
            for msg in context['message_history']:
                direction = "You" if msg['direction'] == 'outbound' else lead_name
                prompt += f"\n{direction} ({msg['sent_at']}):\n{msg['body']}\n"

            prompt += f"""

YOUR TASK:
Generate a friendly, non-pushy follow-up email to {lead_name}.

GUIDELINES:
1. Reference the previous conversation naturally
2. Add value or new information if possible
3. Keep it brief (2-3 short paragraphs)
4. Include an easy out ("No worries if timing isn't right")
5. Use {user_name}'s voice and tone
6. Sign off as {user_name}

RESPONSE FORMAT (JSON):
{{
    "subject": "Re: [subject]",
    "body": "email body text here",
    "confidence": 0.80,
    "reasoning": "why you chose this approach"
}}

Generate the follow-up now:"""

            system_message = "You are a helpful email assistant specializing in professional, non-pushy follow-up emails."

            response_text = await self._ai_client.generate_completion(
                prompt=prompt,
                system_message=system_message,
                temperature=0.8,
                max_tokens=settings.AI_MAX_TOKENS
            )

            # Parse response
            try:
                ai_response = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    ai_response = json.loads(json_match.group(1))
                else:
                    logger.error("Failed to parse AI response as JSON")
                    return None

            # Create AI suggestion
            suggestion = AISuggestion(
                conversation_id=conversation_id,
                reply_to_message_id=None,  # Follow-up, not replying to specific message
                suggested_subject=ai_response.get('subject', f"Re: {conversation.subject}"),
                suggested_body=ai_response['body'],
                confidence_score=ai_response.get('confidence', 0.75),
                context_used=['conversation_history', 'follow_up_timing'],
                ai_reasoning=ai_response.get('reasoning'),
                ai_provider='openrouter',
                ai_model=settings.AI_MODEL_DEFAULT,
                tokens_used=int(len(response_text.split()) * 1.3),
                ai_cost=self._estimate_cost(len(response_text.split()) * 1.3),
                status=SuggestionStatus.PENDING
            )

            session.add(suggestion)
            await session.commit()

            logger.info(f"Created follow-up suggestion {suggestion.id} for conversation {conversation_id}")

            return suggestion

        except Exception as e:
            logger.error(f"Error generating follow-up: {e}", exc_info=True)
            return None

    async def generate_subject_line(
        self,
        session: AsyncSession,
        conversation_id: int,
        message_body: str
    ) -> Optional[str]:
        """
        Generate a subject line for an email.

        Args:
            session: Database session
            conversation_id: Conversation ID
            message_body: Email body text

        Returns:
            Generated subject line or None if generation failed
        """
        try:
            # Load conversation
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            prompt = f"""Generate a concise, compelling email subject line.

CURRENT SUBJECT: {conversation.subject}

EMAIL BODY:
{message_body[:500]}

GUIDELINES:
1. Keep under 60 characters
2. Be specific and clear
3. Avoid spam trigger words
4. Match the tone of the email body
5. Use "Re:" if this is a reply in an ongoing conversation

Return ONLY the subject line, no quotes or extra text."""

            subject_line = await self._ai_client.generate_completion(
                prompt=prompt,
                system_message="You are an expert email copywriter. Generate clear, compelling subject lines.",
                temperature=0.7,
                max_tokens=50
            )

            # Clean up response
            subject_line = subject_line.strip().strip('"').strip("'")

            logger.info(f"Generated subject line for conversation {conversation_id}: {subject_line}")

            return subject_line

        except Exception as e:
            logger.error(f"Error generating subject line: {e}", exc_info=True)
            return None
