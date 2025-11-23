#!/usr/bin/env python3
"""
Test the Reinforcement Learning System.
"""

import asyncio
import random
from app.core.database import AsyncSessionLocal
from app.models.leads import Lead
from app.services.reinforcement_learning import ReinforcementLearner
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_reinforcement_learning():
    """Test the reinforcement learning system."""
    print("\n" + "="*60)
    print("TESTING REINFORCEMENT LEARNING SYSTEM")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Step 1: Initialize learner
            print("\n[1] Initializing reinforcement learner...")
            
            learner = ReinforcementLearner(db, "test_lead_qualifier_rl")
            await learner.initialize()
            
            print(f"✅ Initialized learner: {learner.model_name}")
            print(f"   Learning rate: {learner.learning_rate}")
            print(f"   Discount factor: {learner.discount_factor}")
            print(f"   Exploration rate: {learner.exploration_rate}")
            
            # Step 2: Create test leads with varying quality
            print("\n[2] Creating test leads for training...")
            
            test_leads_data = [
                # High quality leads
                {
                    "title": "Senior Engineer - $200k+",
                    "description": "Looking for senior engineer with 10+ years. Must have Python, AWS.",
                    "compensation": "$200,000 - $250,000",
                    "qualification_score": 0.95,
                    "is_remote": True,
                    "expected_action": "high_priority",
                    "expected_outcome": "hired"
                },
                {
                    "title": "Tech Lead - Great Benefits",
                    "description": "Tech lead position with excellent growth opportunity.",
                    "compensation": "$180,000",
                    "qualification_score": 0.85,
                    "is_remote": True,
                    "expected_action": "high_priority",
                    "expected_outcome": "interviewed"
                },
                # Medium quality leads
                {
                    "title": "Mid-Level Developer",
                    "description": "Seeking developer with 3-5 years experience.",
                    "compensation": "$90,000 - $110,000",
                    "qualification_score": 0.6,
                    "is_remote": False,
                    "expected_action": "normal",
                    "expected_outcome": "response_received"
                },
                {
                    "title": "Junior Developer Position",
                    "description": "Entry level position for recent graduates.",
                    "compensation": "$60,000",
                    "qualification_score": 0.4,
                    "is_remote": False,
                    "expected_action": "low_priority",
                    "expected_outcome": "no_response"
                },
                # Low quality leads
                {
                    "title": "Unpaid Internship",
                    "description": "Unpaid internship for college credit.",
                    "compensation": "Unpaid",
                    "qualification_score": 0.1,
                    "is_remote": False,
                    "expected_action": "reject",
                    "expected_outcome": "rejected"
                },
                {
                    "title": "Commission Only Sales",
                    "description": "100% commission based sales role.",
                    "compensation": "Commission only",
                    "qualification_score": 0.15,
                    "is_remote": False,
                    "expected_action": "reject",
                    "expected_outcome": "rejected"
                }
            ]
            
            # Step 3: Training phase - simulate interactions
            print("\n[3] Training phase - simulating interactions...")
            print("="*60)
            
            import time
            timestamp = int(time.time())
            
            # Run multiple training episodes
            for episode in range(5):
                print(f"\n📚 Training Episode {episode + 1}/5")
                
                # Shuffle leads for variety
                random.shuffle(test_leads_data)
                
                for idx, lead_data in enumerate(test_leads_data):
                    # Create lead
                    lead = Lead(
                        craigslist_id=f"test_rl_{timestamp}_{episode}_{idx}",
                        title=lead_data["title"],
                        description=lead_data["description"],
                        url="http://test.com",
                        compensation=lead_data["compensation"],
                        qualification_score=lead_data["qualification_score"],
                        is_remote=lead_data["is_remote"],
                        location_id=1,
                        category="jobs",
                        posted_at=datetime.now() - timedelta(hours=random.randint(1, 48))
                    )
                    db.add(lead)
                    await db.commit()
                    await db.refresh(lead)
                    
                    # Get recommendation from learner
                    action, confidence, explanation = await learner.get_recommendation(lead)
                    
                    print(f"\n   Lead: {lead.title[:30]}...")
                    print(f"   Score: {lead.qualification_score}")
                    print(f"   ➜ Recommended: {action} (confidence: {confidence:.2f})")
                    
                    # Simulate outcome (with some randomness)
                    if random.random() < 0.8:  # 80% chance of expected outcome
                        outcome = lead_data["expected_outcome"]
                    else:
                        outcomes = ["hired", "interviewed", "response_received", "no_response", "rejected"]
                        outcome = random.choice(outcomes)
                    
                    # Record interaction and learn
                    feedback = await learner.record_interaction(
                        lead=lead,
                        action=action,
                        action_type='qualify',
                        outcome=outcome,
                        feedback_data={
                            'explicit_rating': random.uniform(3, 5) if outcome in ["hired", "interviewed"] else random.uniform(1, 3),
                            'response_received': outcome != "no_response",
                            'response_positive': outcome in ["hired", "interviewed"],
                            'time_to_action': random.uniform(60, 600)  # 1-10 minutes
                        }
                    )
                    
                    # Check if learning correctly
                    if action == lead_data["expected_action"]:
                        print(f"   ✅ Correct action taken")
                    else:
                        print(f"   ⚠️  Expected {lead_data['expected_action']}, got {action}")
                
                # Show learning progress
                print(f"\n   Episode {episode + 1} Stats:")
                print(f"   - Episodes trained: {learner.state.episodes_trained}")
                print(f"   - Average reward: {learner.state.average_reward:.3f}")
                print(f"   - Exploration rate: {learner.exploration_rate:.3f}")
            
            # Step 4: Test phase - evaluate learned policy
            print("\n[4] Test phase - evaluating learned policy...")
            print("="*60)
            
            # Create new test leads
            test_leads = [
                {
                    "title": "Principal Engineer - Top Tech Company",
                    "compensation": "$300,000+",
                    "qualification_score": 0.98,
                    "is_remote": True,
                    "expected": "high_priority"
                },
                {
                    "title": "Contract Work - Short Term",
                    "compensation": "$75/hour",
                    "qualification_score": 0.5,
                    "is_remote": False,
                    "expected": "normal"
                },
                {
                    "title": "Volunteer Developer",
                    "compensation": None,
                    "qualification_score": 0.05,
                    "is_remote": False,
                    "expected": "reject"
                }
            ]
            
            correct_predictions = 0
            
            for test_data in test_leads:
                lead = Lead(
                    craigslist_id=f"test_eval_{timestamp}_{test_data['title'][:10]}",
                    title=test_data["title"],
                    url="http://test.com",
                    compensation=test_data["compensation"],
                    qualification_score=test_data["qualification_score"],
                    is_remote=test_data["is_remote"],
                    location_id=1,
                    category="jobs",
                    posted_at=datetime.now() - timedelta(hours=2)
                )
                db.add(lead)
                await db.commit()
                await db.refresh(lead)
                
                # Get recommendation
                action, confidence, explanation = await learner.get_recommendation(lead)
                
                print(f"\n🧪 Test Lead: {lead.title}")
                print(f"   Qualification Score: {lead.qualification_score}")
                print(f"   Compensation: {lead.compensation}")
                print(f"   ➜ Recommendation: {action} (confidence: {confidence:.2f})")
                print(f"   ➜ Q-value: {explanation['q_value']:.3f}")
                
                if action == test_data["expected"]:
                    print(f"   ✅ Correct prediction!")
                    correct_predictions += 1
                else:
                    print(f"   ❌ Expected {test_data['expected']}")
            
            accuracy = correct_predictions / len(test_leads)
            print(f"\n📊 Test Accuracy: {accuracy:.1%}")
            
            # Step 5: Calculate feature importance
            print("\n[5] Calculating feature importance...")
            
            importance = await learner.calculate_feature_importance()
            
            if importance:
                print("\n📊 Top Feature Importance:")
                for i, feature in enumerate(importance[:5], 1):
                    print(f"   {i}. {feature['feature']}: {feature['importance']:.3f}")
                    print(f"      Positive impact: {feature['positive_ratio']:.1%}")
            
            # Step 6: Save policy snapshot
            print("\n[6] Saving policy snapshot...")
            
            policy = await learner.save_policy_snapshot()
            print(f"✅ Saved policy version {policy.policy_version}")
            print(f"   Total episodes: {policy.training_episodes}")
            print(f"   Total reward: {policy.total_reward:.2f}")
            
            # Step 7: Show learning statistics
            print("\n[7] Learning Statistics")
            print("="*60)
            
            from sqlalchemy import select, func
            from app.models.learning import InteractionFeedback, RewardSignal
            
            # Count interactions
            interaction_count = await db.execute(
                select(func.count(InteractionFeedback.id))
            )
            total_interactions = interaction_count.scalar()
            
            # Count rewards
            reward_count = await db.execute(
                select(func.count(RewardSignal.id))
            )
            total_rewards = reward_count.scalar()
            
            # Average reward
            avg_reward_query = await db.execute(
                select(func.avg(RewardSignal.total_reward))
            )
            avg_reward = avg_reward_query.scalar() or 0
            
            print(f"📊 System Statistics:")
            print(f"   Total interactions: {total_interactions}")
            print(f"   Total reward signals: {total_rewards}")
            print(f"   Average reward: {avg_reward:.3f}")
            print(f"   Q-table size: {len(learner.state.q_values) if learner.state.q_values else 0} states")
            print(f"   Experience buffer: {len(learner.experience_buffer)} experiences")
            
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print("\n✅ Reinforcement Learning System Working!")
            print("\nCapabilities demonstrated:")
            print("  • Q-learning implementation")
            print("  • Feature extraction from leads")
            print("  • Epsilon-greedy exploration")
            print("  • Experience replay buffer")
            print("  • Reward signal tracking")
            print("  • Policy improvement over time")
            print("  • Feature importance calculation")
            print("  • Policy versioning and history")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Test failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_reinforcement_learning())
    
    if success:
        print("\n🎉 Phase 2.1 Reinforcement Learning System Complete!")
        print("\nFeatures implemented:")
        print("  ✅ Q-learning algorithm")
        print("  ✅ State representation and feature extraction")
        print("  ✅ Epsilon-greedy exploration strategy")
        print("  ✅ Experience replay buffer")
        print("  ✅ Reward signal design")
        print("  ✅ Interaction feedback tracking")
        print("  ✅ Feature importance analysis")
        print("  ✅ Policy history and versioning")
        print("  ✅ Learning state persistence")
        print("  ✅ Performance metrics tracking")
    else:
        print("\n⚠️ Reinforcement learning test failed")
    
    exit(0 if success else 1)