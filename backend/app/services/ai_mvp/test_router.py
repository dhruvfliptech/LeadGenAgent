"""
Test script for Semantic Router.

Run with: python -m app.services.ai_mvp.test_router
"""

from app.services.ai_mvp.semantic_router import SemanticRouter, TaskType, ModelTier


def test_routing_logic():
    """Test routing decisions for different scenarios."""
    router = SemanticRouter()

    print("=" * 80)
    print("SEMANTIC ROUTER TEST - Cost Optimization Demo")
    print("=" * 80)

    test_cases = [
        # Simple tasks (always ultra-cheap)
        {
            "task": TaskType.SPAM_DETECTION,
            "lead_value": None,
            "description": "Spam detection (simple classification)"
        },
        {
            "task": TaskType.EMAIL_SUBJECT,
            "lead_value": 50000,
            "description": "Email subject line (simple, even for $50K lead)"
        },

        # Moderate tasks (value-based routing)
        {
            "task": TaskType.WEBSITE_ANALYSIS,
            "lead_value": 5000,
            "description": "Website analysis for $5K SMB lead"
        },
        {
            "task": TaskType.WEBSITE_ANALYSIS,
            "lead_value": 30000,
            "description": "Website analysis for $30K mid-market lead"
        },
        {
            "task": TaskType.EMAIL_BODY,
            "lead_value": None,
            "description": "Email body (no lead value specified)"
        },

        # Complex tasks (value-based routing)
        {
            "task": TaskType.VIDEO_SCRIPT,
            "lead_value": 10000,
            "description": "Video script for $10K SMB lead"
        },
        {
            "task": TaskType.VIDEO_SCRIPT,
            "lead_value": 50000,
            "description": "Video script for $50K mid-market lead"
        },
        {
            "task": TaskType.VIDEO_SCRIPT,
            "lead_value": 150000,
            "description": "Video script for $150K enterprise lead"
        },

        # Critical tasks (always premium)
        {
            "task": TaskType.CONVERSATION_RESPONSE,
            "lead_value": 5000,
            "description": "Conversation response (critical, even for $5K lead)"
        },
        {
            "task": TaskType.OBJECTION_HANDLING,
            "lead_value": None,
            "description": "Objection handling (always premium)"
        },
    ]

    total_estimated_cost = 0.0

    for i, case in enumerate(test_cases, 1):
        decision = router.route(
            task_type=case["task"],
            lead_value=case["lead_value"]
        )

        print(f"\n{'─' * 80}")
        print(f"Test {i}: {case['description']}")
        print(f"{'─' * 80}")
        print(f"Task Type:        {case['task'].value}")
        print(f"Lead Value:       ${case['lead_value']:,}" if case['lead_value'] else "Lead Value:       Not specified")
        print(f"Complexity:       {decision.task_complexity.value}")
        print(f"Selected Model:   {decision.model_name}")
        print(f"Model Tier:       {decision.model_tier.value}")
        print(f"Estimated Cost:   ${decision.estimated_cost:.4f}")
        print(f"Reasoning:        {decision.reasoning}")

        total_estimated_cost += decision.estimated_cost

    print(f"\n{'=' * 80}")
    print(f"TOTAL ESTIMATED COST FOR {len(test_cases)} REQUESTS: ${total_estimated_cost:.4f}")
    print(f"{'=' * 80}")

    # Calculate savings vs always-premium
    premium_model = "anthropic/claude-sonnet-4"
    premium_cost_per_request = router._estimate_cost(premium_model, 1000, 300)
    always_premium_cost = premium_cost_per_request * len(test_cases)
    savings = always_premium_cost - total_estimated_cost
    savings_percent = (savings / always_premium_cost) * 100

    print(f"\n💰 COST OPTIMIZATION RESULTS:")
    print(f"   Always-Premium Cost:  ${always_premium_cost:.4f}")
    print(f"   Smart Routing Cost:   ${total_estimated_cost:.4f}")
    print(f"   Savings:              ${savings:.4f} ({savings_percent:.1f}%)")
    print(f"\n✅ Semantic router achieves {savings_percent:.1f}% cost savings!")

    # Show model distribution
    print(f"\n📊 MODEL USAGE DISTRIBUTION:")
    model_counts = {}
    for case in test_cases:
        decision = router.route(case["task"], case["lead_value"])
        model_counts[decision.model_tier.value] = model_counts.get(decision.model_tier.value, 0) + 1

    for tier, count in sorted(model_counts.items()):
        percent = (count / len(test_cases)) * 100
        print(f"   {tier:15} {count:2} requests ({percent:4.1f}%)")


if __name__ == "__main__":
    test_routing_logic()
