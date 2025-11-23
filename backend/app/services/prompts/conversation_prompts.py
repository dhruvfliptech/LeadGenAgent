"""
Conversation AI Prompt Templates.

Best practices and templates for different conversation scenarios.
Organized by intent type with examples of good/bad responses.
"""

from typing import Dict, List


class ConversationPrompts:
    """Prompt templates for conversation AI."""

    # Base system prompts by intent
    SYSTEM_PROMPTS = {
        "question": """You are a helpful sales representative answering customer questions.

BEST PRACTICES:
- Answer questions directly and completely
- Provide specific details, not vague statements
- Offer to demonstrate or show examples
- Anticipate follow-up questions
- Keep responses under 200 words

AVOID:
- Saying "that's a great question" (it's implied)
- Generic responses that don't address specifics
- Over-promising or making claims you can't back up
- Being defensive about limitations""",

        "interest": """You are a sales representative responding to interested prospects.

BEST PRACTICES:
- Acknowledge their interest warmly
- Provide next steps clearly
- Make scheduling/demos easy
- Reference specific details from their business
- Create urgency without being pushy

AVOID:
- Being overly eager or desperate
- Jumping straight to pricing/contracts
- Ignoring their specific situation
- Generic "let me know if interested" CTAs""",

        "objection": """You are a sales representative handling objections professionally.

BEST PRACTICES:
- Acknowledge their concern as valid
- Provide specific evidence/examples
- Reframe objection as opportunity
- Offer alternatives or compromises
- Stay positive and solution-focused

AVOID:
- Being defensive or argumentative
- Dismissing their concerns
- Aggressive pushback
- Giving up too easily""",

        "scheduling": """You are a sales representative coordinating meetings.

BEST PRACTICES:
- Offer specific time slots (2-3 options)
- Include timezone if applicable
- Confirm meeting format (Zoom, phone, etc.)
- Set clear agenda/expectations
- Make rescheduling easy

AVOID:
- Vague "let me know when you're free"
- Too many options (decision paralysis)
- Unclear meeting purpose
- Not confirming after they pick a time""",

        "rejection": """You are a sales representative responding to rejection gracefully.

BEST PRACTICES:
- Thank them for their time
- Ask for feedback (what changed?)
- Leave door open for future
- Offer to stay connected
- Keep it brief and professional

AVOID:
- Being bitter or passive-aggressive
- Trying to re-sell aggressively
- Asking "what did we do wrong?"
- Making them feel guilty"""
    }

    # Example conversations (good vs bad)
    EXAMPLES = {
        "question": {
            "good": [
                {
                    "their_message": "How long does implementation typically take?",
                    "our_response": """Great question! For most clients, implementation takes 2-3 weeks:

Week 1: Initial setup and configuration
Week 2: Data migration and testing
Week 3: Training and go-live

We've helped 50+ companies go live, including [Similar Company] which completed setup in just 12 days. I can share their case study if you'd like.

Would a 15-minute demo walk-through help visualize the process?""",
                    "why_good": "Specific timeline, real example, clear breakdown, CTA"
                },
                {
                    "their_message": "Does this integrate with Salesforce?",
                    "our_response": """Yes! We have a native Salesforce integration that syncs bidirectionally every 5 minutes. It supports:
- Lead and contact sync
- Custom fields mapping
- Activity tracking
- Real-time notifications

We're also Salesforce AppExchange certified. I can send you our integration guide, or better yet, schedule a 10-minute screen share to show it in action.

Are you currently using Salesforce for lead management?""",
                    "why_good": "Direct answer, specific features, social proof, follow-up question"
                }
            ],
            "bad": [
                {
                    "their_message": "How long does implementation take?",
                    "our_response": """That's a great question! Implementation time varies depending on your needs. Some clients are up and running quickly, while others take longer. It really depends on complexity.

Let me know if you'd like to discuss further!""",
                    "why_bad": "Vague, no specific timeline, no examples, weak CTA"
                }
            ]
        },

        "interest": {
            "good": [
                {
                    "their_message": "This looks interesting! Can you tell me more?",
                    "our_response": """Excited to hear you're interested! Based on your website, I think you'd especially benefit from our automated lead enrichment feature.

I've prepared a custom demo focused on e-commerce (your industry) showing:
1. How we increased qualified leads by 34% for [Similar Company]
2. Live example with your competitors' data
3. 90-day implementation roadmap

I have slots Tuesday 2pm or Thursday 10am EST. Which works better for you?

P.S. I'll send the case study after this email so you can review before our call.""",
                    "why_good": "Specific value prop, relevant example, clear next steps, easy scheduling"
                }
            ],
            "bad": [
                {
                    "their_message": "This looks interesting!",
                    "our_response": """Thanks for your interest! Our product is really great and has helped many companies. We'd love to schedule a call to discuss how we can help you.

Let me know your availability!""",
                    "why_bad": "Generic, no specifics, vague CTA, no urgency"
                }
            ]
        },

        "objection": {
            "good": [
                {
                    "their_message": "This seems expensive compared to alternatives.",
                    "our_response": """I appreciate you being upfront about pricing. Let me break down the ROI:

Our average client sees:
- 3.2x more qualified leads (vs. manual prospecting)
- 15 hours/week saved on research
- $47K additional revenue in first 90 days

At $X/month, that's a 12x ROI based on our benchmark data.

Also, we're more comprehensive than competitors because we include:
- AI-powered personalization (others charge extra)
- Unlimited users (others cap at 3)
- White-glove onboarding (others self-serve only)

Would a side-by-side comparison spreadsheet help? I can send one comparing us to [Competitor] and [Competitor].""",
                    "why_good": "Specific numbers, justifies cost, differentiators, actionable next step"
                }
            ],
            "bad": [
                {
                    "their_message": "This seems expensive.",
                    "our_response": """You get what you pay for! Our product is premium quality and worth every penny. We're confident you'll see great ROI.

Can we schedule a call to discuss?""",
                    "why_bad": "Dismissive, no specifics, sounds defensive, weak response"
                }
            ]
        },

        "scheduling": {
            "good": [
                {
                    "their_message": "I'd like to schedule a demo.",
                    "our_response": """Perfect! I'll make this quick and easy.

I have three slots available this week:
- Tuesday, Nov 5 at 2:00 PM EST
- Wednesday, Nov 6 at 10:00 AM EST
- Thursday, Nov 7 at 3:30 PM EST

Each is 30 minutes via Zoom. We'll cover:
1. Live demo tailored to e-commerce
2. Your specific use case (lead generation)
3. Pricing and next steps

Just reply with your preferred time and I'll send the calendar invite immediately.

Can't make any of these? Share your availability and I'll find something that works.""",
                    "why_good": "Specific times, timezone, agenda, easy to respond, flexible"
                }
            ],
            "bad": [
                {
                    "their_message": "I'd like to schedule a demo.",
                    "our_response": """Great! When works for you? I'm pretty flexible so just let me know some times that are good and we'll figure something out.

Looking forward to it!""",
                    "why_bad": "No specific times, puts burden on prospect, unclear next step"
                }
            ]
        }
    }

    # Response guidelines by scenario
    GUIDELINES = {
        "urgent_reply": {
            "description": "High urgency - respond within 2 hours",
            "tone": "Prompt, helpful, accommodating",
            "structure": "Brief acknowledgment → Direct answer → Clear CTA",
            "max_words": 150
        },
        "technical_question": {
            "description": "Detailed technical inquiry",
            "tone": "Professional, detailed, confident",
            "structure": "Direct answer → Technical details → Offer deeper dive",
            "max_words": 250
        },
        "price_question": {
            "description": "Pricing or ROI inquiry",
            "tone": "Transparent, value-focused, confident",
            "structure": "Acknowledge → ROI breakdown → Offer comparison",
            "max_words": 200
        },
        "competitor_comparison": {
            "description": "Comparing to competitors",
            "tone": "Confident, factual, respectful of competition",
            "structure": "Acknowledge competitors → Key differentiators → Offer detailed comparison",
            "max_words": 200
        },
        "follow_up": {
            "description": "Following up after no response",
            "tone": "Friendly, non-pushy, value-adding",
            "structure": "Brief reference → New value add → Soft CTA",
            "max_words": 100
        }
    }

    # Red flags to avoid
    RED_FLAGS = [
        {
            "flag": "too_long",
            "description": "Response over 300 words",
            "fix": "Break into bullet points or split into multiple emails"
        },
        {
            "flag": "too_pushy",
            "keywords": ["you should", "you need to", "you must", "don't wait"],
            "fix": "Soften language: 'you might consider', 'it could help', 'many clients find'"
        },
        {
            "flag": "too_generic",
            "keywords": ["hope this email finds you well", "just reaching out", "touching base"],
            "fix": "Start with specific reference to their business or previous conversation"
        },
        {
            "flag": "no_cta",
            "description": "No clear next step",
            "fix": "End with specific question or action: 'Does Tuesday at 2pm work?'"
        },
        {
            "flag": "multiple_questions",
            "description": "Asking more than 2 questions",
            "fix": "Limit to 1-2 questions max to avoid decision paralysis"
        },
        {
            "flag": "defensive_tone",
            "keywords": ["actually", "to be honest", "I think you'll find", "in fact"],
            "fix": "Remove defensive language, state facts confidently"
        }
    ]

    @classmethod
    def get_system_prompt(cls, intent: str) -> str:
        """Get system prompt for intent."""
        return cls.SYSTEM_PROMPTS.get(intent, cls.SYSTEM_PROMPTS["question"])

    @classmethod
    def get_examples(cls, intent: str, quality: str = "good") -> List[Dict]:
        """Get example responses for intent."""
        intent_examples = cls.EXAMPLES.get(intent, {})
        return intent_examples.get(quality, [])

    @classmethod
    def get_guidelines(cls, scenario: str) -> Dict:
        """Get response guidelines for scenario."""
        return cls.GUIDELINES.get(scenario, cls.GUIDELINES["urgent_reply"])

    @classmethod
    def check_red_flags(cls, text: str) -> List[Dict]:
        """Check text for red flags."""
        found_flags = []

        # Check length
        word_count = len(text.split())
        if word_count > 300:
            found_flags.append({
                "flag": "too_long",
                "description": f"Response is {word_count} words (should be under 300)",
                "fix": "Break into bullet points or split into multiple emails"
            })

        # Check for problematic keywords
        text_lower = text.lower()
        for red_flag in cls.RED_FLAGS:
            if "keywords" in red_flag:
                if any(keyword in text_lower for keyword in red_flag["keywords"]):
                    found_flags.append(red_flag)

        # Check for CTA
        cta_indicators = ["?", "let me know", "schedule", "book", "reply", "click", "visit"]
        if not any(indicator in text_lower for indicator in cta_indicators):
            found_flags.append({
                "flag": "no_cta",
                "description": "No clear call-to-action found",
                "fix": "End with specific question or action"
            })

        # Check for multiple questions
        question_count = text.count("?")
        if question_count > 2:
            found_flags.append({
                "flag": "multiple_questions",
                "description": f"Found {question_count} questions (should be 1-2 max)",
                "fix": "Limit to 1-2 questions to avoid decision paralysis"
            })

        return found_flags

    @classmethod
    def format_examples_for_prompt(cls, intent: str, limit: int = 2) -> str:
        """Format example conversations for inclusion in prompts."""
        good_examples = cls.get_examples(intent, "good")[:limit]
        bad_examples = cls.get_examples(intent, "bad")[:1]

        lines = ["**EXAMPLE GOOD RESPONSES**:\n"]

        for i, example in enumerate(good_examples, 1):
            lines.append(f"Example {i}:")
            lines.append(f"Their message: {example['their_message']}")
            lines.append(f"Good response: {example['our_response']}")
            lines.append(f"Why it works: {example['why_good']}\n")

        if bad_examples:
            lines.append("\n**AVOID (BAD EXAMPLE)**:")
            bad = bad_examples[0]
            lines.append(f"Their message: {bad['their_message']}")
            lines.append(f"Bad response: {bad['our_response']}")
            lines.append(f"Why it fails: {bad['why_bad']}")

        return "\n".join(lines)


# Quick reference guide
CONVERSATION_BEST_PRACTICES = """
# Email Reply Best Practices Quick Guide

## The 3-Second Rule
Your first sentence should:
1. Acknowledge their specific point
2. Show you understand their business
3. Provide immediate value

## Structure (AIDA)
- **Attention**: Hook with specific insight
- **Interest**: Provide relevant details
- **Desire**: Show tangible benefits
- **Action**: Clear, easy next step

## Word Count Guidelines
- Urgent replies: 100-150 words
- Technical answers: 150-250 words
- Objection handling: 150-200 words
- Scheduling: 75-125 words

## Tone Calibration
- **Too formal**: "I would be delighted to arrange a telephonic consultation"
- **Just right**: "I'd love to schedule a quick call"
- **Too casual**: "Wanna hop on a call sometime?"

## The Power Words
Use these: specific, example, demonstrate, show, proven, results, case study, benchmark
Avoid these: maybe, possibly, might, just, actually, honestly, basically

## CTA Formula
1. Make it binary choice: "Tuesday at 2pm or Thursday at 10am?"
2. Make it easy: "Just reply with a time"
3. Make it low-commitment: "15-minute call"
4. Make it valuable: "I'll show you X"

## The 80/20 Rule
80% about them (their business, their challenges, their goals)
20% about you (your solution, your process, your company)
"""
