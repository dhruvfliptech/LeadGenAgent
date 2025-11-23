"""
Test cases for Conversation AI with sample conversations.

Tests the complete flow:
1. Analyze incoming reply
2. Generate contextual response
3. Suggest improvements to drafts
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.conversation_ai import (
    ConversationAI,
    ReplyAnalysis,
    GeneratedReply,
    ConversationMessage,
    Sentiment,
    Intent
)
from app.services.ai_mvp.ai_council import AICouncil, AICouncilResponse, Message
from app.services.ai_mvp.semantic_router import RouteDecision, ModelTier, TaskComplexity
from app.services.vector_store import VectorStore


# Sample conversation scenarios
SAMPLE_CONVERSATIONS = {
    "interested_question": {
        "incoming_reply": """Hi Sarah,

Thanks for reaching out! I checked out the website analysis you sent - very impressive insights.

Quick question: How long does it typically take to see results? We're looking to ramp up our lead generation in Q1 and need something that can deliver quickly.

Also, does this integrate with HubSpot? That's our CRM.

Looking forward to hearing back!

Best,
John""",
        "expected_sentiment": "positive",
        "expected_intent": "question",
        "expected_topics": ["results timeline", "Q1 goals", "HubSpot integration"],
        "conversation_history": [
            {
                "role": "user",
                "content": "Hi John, I noticed your company's website and wanted to reach out. I analyzed your site and found several opportunities to increase lead generation by 40%+. I've prepared a detailed report. Would you be interested in seeing it?",
                "timestamp": "2025-11-01T10:00:00"
            }
        ],
        "lead_context": {
            "company_name": "Acme E-commerce",
            "website": "https://acme-ecommerce.com",
            "industry": "E-commerce",
            "website_analysis": "Mid-size e-commerce company selling outdoor gear. Website has slow load times (4.2s), poor mobile experience, and unclear CTAs. Estimated 2000 monthly visitors with 1.2% conversion rate. Competitors average 3.8%."
        },
        "expected_response_contains": [
            "results",
            "HubSpot",
            "integration",
            "Q1"
        ]
    },

    "price_objection": {
        "incoming_reply": """Hey,

I talked to my team and we're interested, but the pricing seems high compared to what we're currently paying for [Competitor].

We're only a small team (5 people) and $500/month is a stretch. Any flexibility on pricing?

Thanks,
Jennifer""",
        "expected_sentiment": "neutral",
        "expected_intent": "objection",
        "expected_topics": ["pricing concerns", "competitor comparison", "team size", "budget"],
        "conversation_history": [
            {
                "role": "user",
                "content": "Hi Jennifer, following up on our demo yesterday. Based on your requirements, I'd recommend our Professional plan at $500/month. This includes unlimited users and our AI personalization features.",
                "timestamp": "2025-11-02T14:00:00"
            },
            {
                "role": "lead",
                "content": "Thanks for the demo! Let me discuss with my team and get back to you.",
                "timestamp": "2025-11-02T14:30:00"
            }
        ],
        "lead_context": {
            "company_name": "StartupXYZ",
            "industry": "SaaS",
            "team_size": 5,
            "current_tool": "Competitor A"
        },
        "expected_response_contains": [
            "ROI",
            "value",
            "compared to",
            "team"
        ]
    },

    "scheduling_request": {
        "incoming_reply": """Hi Mike,

Yes, I'd like to schedule a demo. This week is crazy but next week I have more availability.

Tuesday or Wednesday afternoon works best for me (I'm in PST).

Thanks!
- Alex""",
        "expected_sentiment": "positive",
        "expected_intent": "scheduling",
        "expected_topics": ["demo request", "next week", "Tuesday", "Wednesday", "PST timezone"],
        "conversation_history": [
            {
                "role": "user",
                "content": "Hi Alex, I saw you downloaded our case study. Would you like to schedule a quick 20-minute demo to see how we could help your team?",
                "timestamp": "2025-11-03T09:00:00"
            }
        ],
        "lead_context": {
            "company_name": "TechCorp",
            "timezone": "PST"
        },
        "expected_response_contains": [
            "Tuesday",
            "Wednesday",
            "PST",
            "afternoon",
            "time"
        ]
    },

    "soft_rejection": {
        "incoming_reply": """Hi there,

Thanks for the follow-up. After discussing internally, we've decided to stick with our current solution for now. Budget is tight and we can't justify switching at the moment.

Appreciate your time though!

Best,
David""",
        "expected_sentiment": "negative",
        "expected_intent": "rejection",
        "expected_topics": ["decided not to proceed", "current solution", "budget constraints"],
        "conversation_history": [
            {
                "role": "user",
                "content": "Hi David, following up on my previous email about lead generation tools. Have you had a chance to review the comparison I sent?",
                "timestamp": "2025-11-04T11:00:00"
            }
        ],
        "lead_context": {
            "company_name": "Enterprise Inc"
        },
        "expected_response_contains": [
            "understand",
            "future",
            "thank"
        ]
    },

    "enthusiastic_interest": {
        "incoming_reply": """This is EXACTLY what we need!

I showed your demo to our CMO and she's super excited. We want to move forward ASAP. What are the next steps?

Can we get started this month?

- Maria""",
        "expected_sentiment": "positive",
        "expected_intent": "interest",
        "expected_topics": ["ready to proceed", "CMO approval", "timeline", "next steps"],
        "conversation_history": [
            {
                "role": "user",
                "content": "Hi Maria, here's the custom demo I prepared for your e-commerce business. It shows how we generated 127 qualified leads for a similar company in 60 days.",
                "timestamp": "2025-11-03T15:00:00"
            }
        ],
        "lead_context": {
            "company_name": "Fashion Retailer Co",
            "industry": "E-commerce",
            "lead_value": 50000
        },
        "expected_response_contains": [
            "excited",
            "next steps",
            "onboarding",
            "this month"
        ]
    }
}


class TestConversationAI:
    """Test ConversationAI service."""

    @pytest.fixture
    def mock_ai_council(self):
        """Mock AI Council."""
        council = Mock(spec=AICouncil)
        council.complete = AsyncMock()
        return council

    @pytest.fixture
    def mock_vector_store(self):
        """Mock Vector Store."""
        store = Mock(spec=VectorStore)
        store.find_similar_conversations = AsyncMock(return_value=[])
        return store

    @pytest.fixture
    def conversation_ai(self, mock_ai_council, mock_vector_store):
        """Create ConversationAI instance."""
        return ConversationAI(
            ai_council=mock_ai_council,
            vector_store=mock_vector_store
        )

    @pytest.mark.asyncio
    async def test_analyze_interested_question(self, conversation_ai, mock_ai_council):
        """Test analyzing a positive interested reply with questions."""
        scenario = SAMPLE_CONVERSATIONS["interested_question"]

        # Mock AI response
        mock_ai_council.complete.return_value = AICouncilResponse(
            content="""{
                "sentiment": "positive",
                "sentiment_confidence": 0.9,
                "intent": "question",
                "intent_confidence": 0.95,
                "engagement_score": 0.85,
                "key_topics": ["results timeline", "Q1 goals", "HubSpot integration"],
                "questions_asked": ["How long to see results?", "Does it integrate with HubSpot?"],
                "urgency_level": "high",
                "summary": "Interested prospect asking about implementation timeline and HubSpot integration for Q1 launch"
            }""",
            model_used="meta-llama/llama-3.1-8b-instruct",
            model_tier="ultra_cheap",
            prompt_tokens=200,
            completion_tokens=100,
            total_cost=0.0001,
            route_decision=RouteDecision(
                model_name="meta-llama/llama-3.1-8b-instruct",
                model_tier=ModelTier.ULTRA_CHEAP,
                task_complexity=TaskComplexity.SIMPLE,
                reasoning="Simple classification task",
                estimated_cost=0.0001
            )
        )

        # Analyze
        analysis = await conversation_ai.analyze_reply(
            reply_text=scenario["incoming_reply"],
            lead_id=123
        )

        # Assertions
        assert analysis.sentiment == scenario["expected_sentiment"]
        assert analysis.intent == scenario["expected_intent"]
        assert analysis.engagement_score > 0.7
        assert len(analysis.questions_asked) == 2
        assert analysis.urgency_level == "high"

    @pytest.mark.asyncio
    async def test_generate_reply_for_questions(self, conversation_ai, mock_ai_council, mock_vector_store):
        """Test generating reply for interested question."""
        scenario = SAMPLE_CONVERSATIONS["interested_question"]

        # Mock similar conversations
        mock_vector_store.find_similar_conversations.return_value = [
            {
                "conversation_id": 1,
                "their_message": "How fast can we implement?",
                "our_response": "Most clients see results within 2-3 weeks. We've had companies go live in as little as 10 days.",
                "intent": "question",
                "sentiment": "positive",
                "outcome": "success",
                "similarity": 0.87
            }
        ]

        # Mock AI response
        mock_ai_council.complete.return_value = AICouncilResponse(
            content="""Hi John,

Great to hear you're interested! Let me address your questions:

**Timeline**: Most clients see measurable results within 2-3 weeks. Based on your Q1 timeline, we could have you fully operational by mid-December, giving you 6+ weeks of data before Q1 starts. Our fastest client (similar e-commerce company) saw a 23% increase in qualified leads within their first 30 days.

**HubSpot Integration**: Yes! We have a native HubSpot integration that syncs bidirectionally. All leads flow directly into HubSpot with enriched data, activity tracking, and automated workflows. I can show you a live demo of the integration if helpful.

For your Q1 goal, I'd recommend we schedule a 20-minute implementation planning call this week. I have slots Tuesday at 2pm or Wednesday at 10am EST. Which works better for you?

I'll also send over our HubSpot integration guide after this email.

Best,
Sarah""",
            model_used="anthropic/claude-3.5-sonnet",
            model_tier="premium",
            prompt_tokens=800,
            completion_tokens=300,
            total_cost=0.012,
            route_decision=RouteDecision(
                model_name="anthropic/claude-3.5-sonnet",
                model_tier=ModelTier.PREMIUM,
                task_complexity=TaskComplexity.CRITICAL,
                reasoning="Critical customer-facing task",
                estimated_cost=0.012
            )
        )

        # Generate reply
        analysis = ReplyAnalysis(
            sentiment="positive",
            sentiment_confidence=0.9,
            intent="question",
            intent_confidence=0.95,
            engagement_score=0.85,
            key_topics=scenario["expected_topics"],
            questions_asked=["How long to see results?", "Does it integrate with HubSpot?"],
            urgency_level="high",
            summary="Interested prospect asking about timeline and integration"
        )

        history = [
            ConversationMessage(
                role="user",
                content=scenario["conversation_history"][0]["content"],
                timestamp=datetime.fromisoformat(scenario["conversation_history"][0]["timestamp"])
            )
        ]

        reply = await conversation_ai.generate_reply(
            incoming_reply=scenario["incoming_reply"],
            reply_analysis=analysis,
            conversation_history=history,
            lead_context=scenario["lead_context"],
            lead_id=123,
            lead_value=25000
        )

        # Assertions
        assert reply.confidence_score > 0.7
        assert reply.model_used == "anthropic/claude-3.5-sonnet"
        for keyword in scenario["expected_response_contains"]:
            assert keyword.lower() in reply.content.lower()
        assert reply.call_to_action is not None
        assert len(reply.content.split()) < 300  # Check length

    @pytest.mark.asyncio
    async def test_suggest_improvements_too_long(self, conversation_ai, mock_ai_council):
        """Test improvement suggestions for overly long draft."""
        draft = """Hi there,

I hope this email finds you well. I wanted to reach out to you because I think our product could be a great fit for your company. We've been in business for over 10 years and have helped thousands of companies improve their lead generation efforts. Our platform uses cutting-edge AI technology to analyze websites and identify opportunities for improvement.

I noticed that your website has some areas that could be optimized. For example, the load time is quite slow, which can impact conversion rates. Studies show that every second of load time can decrease conversions by up to 7%. That's a significant impact on your bottom line.

Our solution can help with this. We provide detailed analysis, implementation support, and ongoing optimization. We also offer training for your team, 24/7 customer support, and regular check-ins to ensure you're getting the most value from our platform.

I'd love to schedule a call to discuss this further. Let me know what times work for you and we can set something up. I'm pretty flexible so just send over some options and I'll make it work.

Looking forward to hearing from you!

Best regards,
Sales Rep""",

        mock_ai_council.complete.return_value = AICouncilResponse(
            content="""{
                "overall_score": 0.4,
                "tone_suggestions": [
                    "Too generic - remove 'I hope this email finds you well'",
                    "Too focused on features, not enough on their specific business"
                ],
                "clarity_suggestions": [
                    "CTA is unclear - provide specific time slots instead of 'let me know'",
                    "Too much information - focus on 1-2 key points"
                ],
                "issues": [
                    {"type": "too_long", "description": "Email is 247 words, should be under 200"},
                    {"type": "too_generic", "description": "Opening line is cliché"},
                    {"type": "unclear_cta", "description": "No specific times offered for call"},
                    {"type": "too_pushy", "description": "Multiple value propositions feel overwhelming"}
                ],
                "improved_version": "Hi [Name],\\n\\nI analyzed your website and found your load time (4.2s) is costing you qualified leads. We helped [Similar Company] reduce load time to 1.1s and increase conversions by 34%.\\n\\nI've prepared a custom report showing 3 specific improvements for your site. Quick 15-minute call to walk through it?\\n\\nI have Tuesday 2pm or Wednesday 10am EST available. Which works better?",
                "word_count": 247,
                "reading_level": "professional"
            }""",
            model_used="meta-llama/llama-3.1-8b-instruct",
            model_tier="ultra_cheap",
            prompt_tokens=300,
            completion_tokens=150,
            total_cost=0.0001,
            route_decision=RouteDecision(
                model_name="meta-llama/llama-3.1-8b-instruct",
                model_tier=ModelTier.ULTRA_CHEAP,
                task_complexity=TaskComplexity.SIMPLE,
                reasoning="Simple classification",
                estimated_cost=0.0001
            )
        )

        analysis = ReplyAnalysis(
            sentiment="neutral",
            sentiment_confidence=0.7,
            intent="question",
            intent_confidence=0.8,
            engagement_score=0.6,
            key_topics=["website optimization"],
            questions_asked=["Can you help optimize our website?"],
            urgency_level="medium",
            summary="Asking about website optimization"
        )

        improvements = await conversation_ai.suggest_improvements(
            draft_reply=draft,
            original_message="Can you help optimize our website?",
            reply_analysis=analysis,
            lead_id=123
        )

        # Assertions
        assert improvements.overall_score < 0.6  # Poor score
        assert improvements.word_count > 200
        assert len(improvements.issues) > 0
        assert any("too_long" in issue["type"] for issue in improvements.issues)
        assert improvements.improved_version is not None

    @pytest.mark.asyncio
    async def test_handle_price_objection(self, conversation_ai, mock_ai_council, mock_vector_store):
        """Test handling price objection."""
        scenario = SAMPLE_CONVERSATIONS["price_objection"]

        # Mock similar successful objection handling
        mock_vector_store.find_similar_conversations.return_value = [
            {
                "conversation_id": 5,
                "their_message": "The price seems high",
                "our_response": "I understand budget concerns. Let me show you the ROI breakdown. Our average client sees 3.2x return in 90 days, which makes the investment pay for itself in the first quarter.",
                "intent": "objection",
                "sentiment": "neutral",
                "outcome": "success",
                "similarity": 0.82
            }
        ]

        mock_ai_council.complete.return_value = AICouncilResponse(
            content="""Hi Jennifer,

I appreciate you being transparent about pricing. Let me address this:

**ROI Comparison**: While [Competitor] charges $300/month, here's what you're missing:
- AI personalization (they charge $200/month extra for this)
- Unlimited users (they cap at 3, $50/user after)
- White-glove onboarding (they offer self-serve only)

Total comparable cost with [Competitor]: $550-700/month

**For Your Team Size**: At 5 people, you're actually our sweet spot. Average client your size sees $2,400/month in additional revenue within 90 days (that's a 4.8x ROI).

**Flexible Options**: I can offer:
1. Quarterly billing (10% discount = $450/month)
2. Start with 2-month trial at $400/month, then full price

Would option 1 or 2 work better for your budget?

Best,
Sales Rep""",
            model_used="anthropic/claude-3.5-sonnet",
            model_tier="premium",
            prompt_tokens=900,
            completion_tokens=350,
            total_cost=0.014,
            route_decision=RouteDecision(
                model_name="anthropic/claude-3.5-sonnet",
                model_tier=ModelTier.PREMIUM,
                task_complexity=TaskComplexity.CRITICAL,
                reasoning="Critical objection handling",
                estimated_cost=0.014
            )
        )

        analysis = ReplyAnalysis(
            sentiment="neutral",
            sentiment_confidence=0.8,
            intent="objection",
            intent_confidence=0.9,
            engagement_score=0.7,
            key_topics=scenario["expected_topics"],
            questions_asked=["Any flexibility on pricing?"],
            urgency_level="medium",
            summary="Team is interested but has budget concerns"
        )

        history = [
            ConversationMessage(
                role="user",
                content=scenario["conversation_history"][0]["content"],
                timestamp=datetime.fromisoformat(scenario["conversation_history"][0]["timestamp"])
            ),
            ConversationMessage(
                role="lead",
                content=scenario["conversation_history"][1]["content"],
                timestamp=datetime.fromisoformat(scenario["conversation_history"][1]["timestamp"])
            )
        ]

        reply = await conversation_ai.generate_reply(
            incoming_reply=scenario["incoming_reply"],
            reply_analysis=analysis,
            conversation_history=history,
            lead_context=scenario["lead_context"],
            lead_id=456,
            lead_value=15000
        )

        # Assertions
        assert "ROI" in reply.content or "value" in reply.content.lower()
        assert reply.confidence_score > 0.65
        assert reply.call_to_action is not None


# Integration test data
INTEGRATION_TEST_SCENARIOS = """
# Integration Test Scenarios for Conversation AI

## Scenario 1: Multi-turn Question Handling
Lead asks multiple questions across several emails. System should:
- Track all questions from history
- Ensure all are answered
- Reference previous answers
- Build on context

## Scenario 2: Sentiment Shift Detection
Lead starts positive, becomes frustrated. System should:
- Detect sentiment change
- Adjust tone accordingly
- Address source of frustration
- Offer escalation if needed

## Scenario 3: Mixed Intent Messages
Lead shows interest but also has objections. System should:
- Identify both intents
- Address objection first
- Then move to next steps
- Balance both aspects

## Scenario 4: Time-Sensitive Responses
Lead mentions urgent deadline. System should:
- Detect urgency signals
- Prioritize quick response
- Offer immediate solutions
- Follow up proactively

## Scenario 5: Industry-Specific Jargon
Lead uses technical terms from their industry. System should:
- Use appropriate terminology
- Show domain expertise
- Reference relevant case studies
- Match their communication style
"""


if __name__ == "__main__":
    print("Conversation AI Test Suite")
    print("=" * 50)
    print("\nSample Conversations Loaded:")
    for name, scenario in SAMPLE_CONVERSATIONS.items():
        print(f"\n{name}:")
        print(f"  - Sentiment: {scenario['expected_sentiment']}")
        print(f"  - Intent: {scenario['expected_intent']}")
        print(f"  - Topics: {', '.join(scenario['expected_topics'])}")
    print("\n" + "=" * 50)
    print("\nRun with: pytest tests/test_conversation_ai.py -v")
