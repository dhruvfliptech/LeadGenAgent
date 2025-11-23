"""
Reinforcement Learning service for improving lead qualification and response generation.
"""

import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.models.learning import (
    InteractionFeedback, LearningState, RewardSignal, 
    FeatureImportance, PolicyHistory
)
from app.models.leads import Lead
from app.models.approvals import ResponseApproval
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReinforcementLearner:
    """Reinforcement learning system for lead qualification and response optimization."""
    
    def __init__(self, db: AsyncSession, model_name: str = "lead_qualifier_rl"):
        self.db = db
        self.model_name = model_name
        self.model_version = "1.0.0"
        self.state = None
        self.experience_buffer = deque(maxlen=1000)
        
        # Hyperparameters
        self.learning_rate = 0.01
        self.discount_factor = 0.95
        self.exploration_rate = 0.1
        self.min_exploration = 0.01
        self.exploration_decay = 0.995
        
        # Action space
        self.actions = {
            'qualify': ['high_priority', 'normal', 'low_priority', 'reject'],
            'response': ['template_a', 'template_b', 'template_c', 'custom'],
            'timing': ['immediate', 'delay_1h', 'delay_4h', 'delay_24h']
        }
        
    async def initialize(self):
        """Initialize or load the learning state."""
        query = select(LearningState).where(
            LearningState.model_name == self.model_name,
            LearningState.is_active == True
        )
        result = await self.db.execute(query)
        self.state = result.scalar_one_or_none()
        
        if not self.state:
            # Create new learning state
            self.state = LearningState(
                model_name=self.model_name,
                model_version=self.model_version,
                model_type="qualification",
                learning_rate=self.learning_rate,
                discount_factor=self.discount_factor,
                exploration_rate=self.exploration_rate,
                q_values={},
                state_vector={},
                policy_weights={}
            )
            self.db.add(self.state)
            await self.db.commit()
            await self.db.refresh(self.state)
            logger.info(f"Initialized new learning state for {self.model_name}")
        else:
            # Load parameters
            self.learning_rate = self.state.learning_rate
            self.discount_factor = self.state.discount_factor
            self.exploration_rate = self.state.exploration_rate
            
            # Load experience buffer if exists
            if self.state.experience_buffer:
                self.experience_buffer = deque(
                    self.state.experience_buffer, 
                    maxlen=self.state.buffer_size
                )
            logger.info(f"Loaded existing learning state for {self.model_name}")
    
    def extract_features(self, lead: Lead) -> Dict[str, float]:
        """Extract features from a lead for state representation."""
        features = {}
        
        # Lead quality features
        features['qualification_score'] = lead.qualification_score or 0
        features['has_compensation'] = 1.0 if lead.compensation else 0.0
        features['is_remote'] = 1.0 if lead.is_remote else 0.0
        
        # Parse compensation if available
        if lead.compensation:
            comp_value = self._parse_compensation(lead.compensation)
            features['compensation_value'] = min(comp_value / 200000, 1.0) if comp_value else 0.5
        else:
            features['compensation_value'] = 0.0
        
        # Temporal features
        if lead.posted_at:
            from datetime import timezone
            now = datetime.now(timezone.utc) if lead.posted_at.tzinfo else datetime.now()
            hours_old = (now - lead.posted_at).total_seconds() / 3600
            features['freshness'] = max(0, 1 - (hours_old / 168))  # Decay over 1 week
        else:
            features['freshness'] = 0.5
        
        # Text features (simplified)
        if lead.description:
            features['description_length'] = min(len(lead.description) / 1000, 1.0)
            features['has_requirements'] = 1.0 if any(
                keyword in lead.description.lower() 
                for keyword in ['required', 'must have', 'requirements']
            ) else 0.0
        else:
            features['description_length'] = 0.0
            features['has_requirements'] = 0.0
        
        # Category features
        features['is_job'] = 1.0 if lead.category == 'jobs' else 0.0
        features['is_gig'] = 1.0 if lead.category == 'gigs' else 0.0
        
        return features
    
    def _parse_compensation(self, compensation: str) -> Optional[float]:
        """Parse compensation string to numeric value."""
        import re
        
        comp = compensation.replace(',', '').replace('$', '')
        
        # Look for hourly rate
        hourly_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/hr|/hour|per hour)', comp, re.IGNORECASE)
        if hourly_match:
            return float(hourly_match.group(1)) * 2080  # Convert to annual
        
        # Look for annual salary
        salary_match = re.search(r'(\d+)(?:k|K)', comp)
        if salary_match:
            return float(salary_match.group(1)) * 1000
        
        # Look for salary range
        range_match = re.search(r'(\d+)[\s,]*(?:-|to)[\s,]*(\d+)', compensation.replace(',', ''))
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            # Handle k notation
            if low < 1000:
                low *= 1000
            if high < 1000:
                high *= 1000
            return (low + high) / 2
        
        return None
    
    def get_state_key(self, features: Dict[str, float]) -> str:
        """Convert feature dict to a state key for Q-table."""
        # Discretize continuous features
        discretized = {}
        for key, value in features.items():
            if isinstance(value, float):
                discretized[key] = round(value * 10) / 10  # Round to nearest 0.1
            else:
                discretized[key] = value
        
        # Create stable key
        return json.dumps(discretized, sort_keys=True)
    
    def get_q_value(self, state_key: str, action: str) -> float:
        """Get Q-value for a state-action pair."""
        q_values = self.state.q_values or {}
        state_q = q_values.get(state_key, {})
        return state_q.get(action, 0.0)
    
    def set_q_value(self, state_key: str, action: str, value: float):
        """Set Q-value for a state-action pair."""
        if not self.state.q_values:
            self.state.q_values = {}
        if state_key not in self.state.q_values:
            self.state.q_values[state_key] = {}
        self.state.q_values[state_key][action] = value
    
    def select_action(self, state_key: str, action_type: str = 'qualify') -> str:
        """Select action using epsilon-greedy policy."""
        available_actions = self.actions[action_type]
        
        # Exploration vs exploitation
        if random.random() < self.exploration_rate:
            # Explore: random action
            return random.choice(available_actions)
        else:
            # Exploit: best known action
            q_values = {
                action: self.get_q_value(state_key, action)
                for action in available_actions
            }
            
            if not q_values or all(v == 0 for v in q_values.values()):
                return random.choice(available_actions)
            
            max_q = max(q_values.values())
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return random.choice(best_actions)
    
    def calculate_reward(
        self,
        lead: Lead,
        action: str,
        outcome: Optional[str] = None,
        feedback: Optional[InteractionFeedback] = None
    ) -> float:
        """Calculate reward for an action taken on a lead."""
        reward = 0.0
        
        # Base reward for action type
        if action == 'high_priority':
            reward += 0.1
        elif action == 'reject':
            reward -= 0.1
        
        # Reward based on lead quality
        if lead.qualification_score:
            if action in ['high_priority', 'normal'] and lead.qualification_score > 0.7:
                reward += 0.3
            elif action == 'reject' and lead.qualification_score < 0.3:
                reward += 0.2
        
        # Outcome-based rewards (if available)
        if outcome:
            if outcome == 'hired':
                reward += 1.0
            elif outcome == 'interviewed':
                reward += 0.5
            elif outcome == 'response_received':
                reward += 0.3
            elif outcome == 'no_response':
                reward -= 0.1
            elif outcome == 'rejected':
                reward -= 0.2
        
        # Feedback-based rewards
        if feedback:
            if feedback.explicit_rating:
                reward += (feedback.explicit_rating - 3) * 0.2  # -0.4 to +0.4
            
            if feedback.response_received:
                reward += 0.2
                if feedback.response_positive:
                    reward += 0.3
            
            # Time efficiency reward
            if feedback.time_to_action and feedback.time_to_action < 300:  # < 5 minutes
                reward += 0.1
        
        return reward
    
    async def record_interaction(
        self,
        lead: Lead,
        action: str,
        action_type: str = 'qualify',
        outcome: Optional[str] = None,
        feedback_data: Optional[Dict] = None
    ) -> InteractionFeedback:
        """Record an interaction and update learning."""
        
        # Create feedback record
        feedback = InteractionFeedback(
            lead_id=lead.id,
            interaction_type=action_type,
            action_taken=action,
            outcome=outcome,
            created_at=datetime.utcnow()
        )
        
        if feedback_data:
            for key, value in feedback_data.items():
                if hasattr(feedback, key):
                    setattr(feedback, key, value)
        
        self.db.add(feedback)
        
        # Extract features and calculate reward
        features = self.extract_features(lead)
        state_key = self.get_state_key(features)
        reward = self.calculate_reward(lead, action, outcome, feedback)
        
        # Store experience
        experience = {
            'state': state_key,
            'action': action,
            'reward': reward,
            'next_state': None,  # Will be updated later
            'features': features
        }
        self.experience_buffer.append(experience)
        
        # Record reward signal
        reward_signal = RewardSignal(
            lead_id=lead.id,
            action_type=action_type,
            action_details={'action': action},
            state_features=features,
            action_taken=action,
            immediate_reward=reward,
            total_reward=reward,
            model_name=self.model_name,
            model_version=self.model_version
        )
        self.db.add(reward_signal)
        
        # Update Q-value (immediate update)
        await self.update_q_value(state_key, action, reward)
        
        # Train if enough experience
        if len(self.experience_buffer) >= 32:
            await self.train_batch()
        
        await self.db.commit()
        await self.db.refresh(feedback)
        
        return feedback
    
    async def update_q_value(self, state_key: str, action: str, reward: float):
        """Update Q-value using Q-learning update rule."""
        current_q = self.get_q_value(state_key, action)
        
        # For terminal states, next_q is 0
        # For non-terminal, we'd need to look at next state
        next_q = 0  # Simplified for now
        
        # Q-learning update
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * next_q - current_q)
        
        self.set_q_value(state_key, action, new_q)
        
        # Update state
        self.state.episodes_trained += 1
        self.state.total_reward += reward
        self.state.average_reward = self.state.total_reward / max(1, self.state.episodes_trained)
        self.state.last_trained_at = datetime.utcnow()
    
    async def train_batch(self, batch_size: int = 32):
        """Train on a batch of experiences."""
        if len(self.experience_buffer) < batch_size:
            return
        
        # Sample batch
        batch = random.sample(list(self.experience_buffer), batch_size)
        
        total_loss = 0
        for experience in batch:
            state_key = experience['state']
            action = experience['action']
            reward = experience['reward']
            
            # Update Q-value
            await self.update_q_value(state_key, action, reward)
            
            # Calculate loss (for monitoring)
            current_q = self.get_q_value(state_key, action)
            loss = abs(reward - current_q)
            total_loss += loss
        
        # Update learning state
        self.state.last_loss = total_loss / batch_size
        
        # Decay exploration
        self.exploration_rate = max(
            self.min_exploration,
            self.exploration_rate * self.exploration_decay
        )
        self.state.exploration_rate = self.exploration_rate
        
        # Save state
        self.state.experience_buffer = list(self.experience_buffer)[-1000:]  # Keep last 1000
        await self.db.commit()
        
        logger.info(f"Trained on batch of {batch_size}, avg loss: {self.state.last_loss:.4f}")
    
    async def get_recommendation(
        self,
        lead: Lead,
        action_type: str = 'qualify'
    ) -> Tuple[str, float, Dict]:
        """Get action recommendation for a lead."""
        
        # Extract features
        features = self.extract_features(lead)
        state_key = self.get_state_key(features)
        
        # Select action
        action = self.select_action(state_key, action_type)
        
        # Get confidence (based on Q-value)
        q_value = self.get_q_value(state_key, action)
        
        # Calculate confidence (normalized Q-value)
        all_q_values = [
            self.get_q_value(state_key, a) 
            for a in self.actions[action_type]
        ]
        
        if all_q_values and max(all_q_values) > 0:
            confidence = q_value / max(all_q_values)
        else:
            confidence = 0.5  # Neutral confidence
        
        # Prepare explanation
        explanation = {
            'action': action,
            'confidence': confidence,
            'q_value': q_value,
            'exploration_rate': self.exploration_rate,
            'features': features,
            'model_episodes': self.state.episodes_trained
        }
        
        return action, confidence, explanation
    
    async def calculate_feature_importance(self) -> List[Dict]:
        """Calculate and store feature importance based on learned Q-values."""
        
        if not self.state.q_values:
            return []
        
        feature_impacts = {}
        
        # Analyze Q-values to determine feature importance
        for state_str, action_values in self.state.q_values.items():
            try:
                state = json.loads(state_str)
                max_q = max(action_values.values()) if action_values else 0
                
                for feature, value in state.items():
                    if feature not in feature_impacts:
                        feature_impacts[feature] = {
                            'positive': 0,
                            'negative': 0,
                            'neutral': 0,
                            'total': 0,
                            'sum_impact': 0
                        }
                    
                    feature_impacts[feature]['total'] += 1
                    feature_impacts[feature]['sum_impact'] += max_q * value
                    
                    if max_q > 0.1:
                        feature_impacts[feature]['positive'] += 1
                    elif max_q < -0.1:
                        feature_impacts[feature]['negative'] += 1
                    else:
                        feature_impacts[feature]['neutral'] += 1
            except:
                continue
        
        # Calculate importance scores
        importance_records = []
        for feature_name, impacts in feature_impacts.items():
            if impacts['total'] > 0:
                importance_score = abs(impacts['sum_impact'] / impacts['total'])
                
                # Store in database
                importance = FeatureImportance(
                    model_name=self.model_name,
                    model_version=self.model_version,
                    feature_name=feature_name,
                    importance_score=importance_score,
                    positive_impact_count=impacts['positive'],
                    negative_impact_count=impacts['negative'],
                    neutral_impact_count=impacts['neutral'],
                    calculated_at=datetime.utcnow()
                )
                self.db.add(importance)
                
                importance_records.append({
                    'feature': feature_name,
                    'importance': importance_score,
                    'positive_ratio': impacts['positive'] / impacts['total'],
                    'negative_ratio': impacts['negative'] / impacts['total']
                })
        
        await self.db.commit()
        
        # Sort by importance
        importance_records.sort(key=lambda x: x['importance'], reverse=True)
        
        return importance_records
    
    async def save_policy_snapshot(self) -> PolicyHistory:
        """Save current policy for history tracking."""
        
        # Calculate current performance metrics
        performance = {
            'average_reward': self.state.average_reward,
            'episodes_trained': self.state.episodes_trained,
            'exploration_rate': self.exploration_rate,
            'q_values_count': len(self.state.q_values) if self.state.q_values else 0
        }
        
        # Get policy version (increment from last)
        last_policy = await self.db.execute(
            select(func.max(PolicyHistory.policy_version)).where(
                PolicyHistory.model_name == self.model_name
            )
        )
        last_version = last_policy.scalar() or 0
        
        # Create policy history record
        policy = PolicyHistory(
            model_name=self.model_name,
            model_version=self.model_version,
            policy_version=last_version + 1,
            policy_type="epsilon_greedy",
            policy_parameters={
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'exploration_rate': self.exploration_rate
            },
            performance_metrics=performance,
            training_episodes=self.state.episodes_trained,
            total_reward=self.state.total_reward,
            created_at=datetime.utcnow()
        )
        
        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)
        
        logger.info(f"Saved policy snapshot version {policy.policy_version}")
        
        return policy