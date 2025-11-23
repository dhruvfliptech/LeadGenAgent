"""
Memory management service for context preservation and retrieval.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc, func
from app.models.memory import (
    ConversationMemory, ShortTermMemory, LongTermMemory,
    SemanticMemory, EpisodicMemory, ContextState
)
from app.models.leads import Lead
from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages memory storage and retrieval across different memory systems."""
    
    def __init__(self, db: AsyncSession, session_id: str, user_id: Optional[str] = None):
        self.db = db
        self.session_id = session_id
        self.user_id = user_id
        self.short_term_memory = None
        self.context_state = None
        self.memory_buffer = deque(maxlen=100)  # Recent memories for quick access
        
    async def initialize(self):
        """Initialize or load memory systems."""
        
        # Load or create short-term memory
        await self._load_short_term_memory()
        
        # Load or create context state
        await self._load_context_state()
        
        # Load recent conversation memories
        await self._load_recent_conversations()
        
        logger.info(f"Memory manager initialized for session {self.session_id}")
    
    async def _load_short_term_memory(self):
        """Load or create short-term memory for session."""
        query = select(ShortTermMemory).where(
            ShortTermMemory.session_id == self.session_id,
            ShortTermMemory.is_active == True
        )
        result = await self.db.execute(query)
        self.short_term_memory = result.scalar_one_or_none()
        
        if not self.short_term_memory:
            self.short_term_memory = ShortTermMemory(
                session_id=self.session_id,
                user_id=self.user_id,
                working_memory={},
                decision_stack=[],
                session_preferences={},
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            self.db.add(self.short_term_memory)
            await self.db.commit()
            await self.db.refresh(self.short_term_memory)
    
    async def _load_context_state(self):
        """Load or create context state."""
        context_id = f"{self.session_id}_context"
        
        query = select(ContextState).where(
            ContextState.context_id == context_id,
            ContextState.is_complete == False
        )
        result = await self.db.execute(query)
        self.context_state = result.scalar_one_or_none()
        
        if not self.context_state:
            self.context_state = ContextState(
                context_id=context_id,
                session_id=self.session_id,
                active_entities={},
                active_topics=[],
                context_stack=[],
                attention_distribution={}
            )
            self.db.add(self.context_state)
            await self.db.commit()
            await self.db.refresh(self.context_state)
    
    async def _load_recent_conversations(self, limit: int = 10):
        """Load recent conversation memories into buffer."""
        query = select(ConversationMemory).where(
            ConversationMemory.session_id == self.session_id
        ).order_by(desc(ConversationMemory.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        memories = result.scalars().all()
        
        # Add to buffer in chronological order
        for memory in reversed(memories):
            self.memory_buffer.append(memory)
    
    async def store_conversation(
        self,
        message_type: str,
        message_content: str,
        lead_id: Optional[int] = None,
        entities: Optional[Dict] = None,
        intent: Optional[str] = None,
        importance: float = 0.5
    ) -> ConversationMemory:
        """Store a conversation turn in memory."""
        
        # Create conversation memory
        memory = ConversationMemory(
            session_id=self.session_id,
            user_id=self.user_id,
            lead_id=lead_id,
            message_type=message_type,
            message_content=message_content,
            context_snapshot=self._get_context_snapshot(),
            active_leads=self.short_term_memory.current_leads,
            entities=entities,
            intent=intent,
            importance_score=importance
        )
        
        self.db.add(memory)
        
        # Update short-term memory
        self.short_term_memory.message_count += 1
        self.short_term_memory.last_activity = datetime.utcnow()
        
        # Add to buffer
        self.memory_buffer.append(memory)
        
        # Extract and store patterns if significant
        if importance > 0.7:
            await self._extract_patterns(message_content, entities, intent)
        
        await self.db.commit()
        await self.db.refresh(memory)
        
        return memory
    
    def _get_context_snapshot(self) -> Dict:
        """Get current context snapshot."""
        return {
            'working_memory': self.short_term_memory.working_memory,
            'current_task': self.short_term_memory.current_task,
            'current_step': self.short_term_memory.current_step,
            'active_entities': self.context_state.active_entities,
            'active_topics': self.context_state.active_topics
        }
    
    async def _extract_patterns(
        self,
        content: str,
        entities: Optional[Dict],
        intent: Optional[str]
    ):
        """Extract patterns from significant interactions."""
        
        if not self.user_id:
            return
        
        # Look for preference patterns
        if intent in ['preference', 'requirement', 'constraint']:
            await self._store_long_term_memory(
                memory_type='preference',
                memory_key=f"pref_{intent}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                memory_value={
                    'content': content,
                    'entities': entities,
                    'intent': intent
                }
            )
    
    async def _store_long_term_memory(
        self,
        memory_type: str,
        memory_key: str,
        memory_value: Any,
        memory_category: Optional[str] = None
    ):
        """Store or update long-term memory."""
        
        # Check if memory exists
        query = select(LongTermMemory).where(
            LongTermMemory.user_id == self.user_id,
            LongTermMemory.memory_key == memory_key
        )
        result = await self.db.execute(query)
        memory = result.scalar_one_or_none()
        
        if memory:
            # Reinforce existing memory
            memory.frequency += 1
            memory.reinforcement_count += 1
            memory.strength = min(1.0, memory.strength + 0.1)
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1
        else:
            # Create new memory
            memory = LongTermMemory(
                user_id=self.user_id,
                memory_type=memory_type,
                memory_category=memory_category,
                memory_key=memory_key,
                memory_value=memory_value,
                source_sessions=[self.session_id]
            )
            self.db.add(memory)
    
    async def update_working_memory(self, key: str, value: Any):
        """Update working memory with new information."""
        if not self.short_term_memory.working_memory:
            self.short_term_memory.working_memory = {}
        
        self.short_term_memory.working_memory[key] = value
        await self.db.commit()
    
    async def get_working_memory(self, key: Optional[str] = None) -> Any:
        """Get working memory value or all if no key specified."""
        if key:
            return self.short_term_memory.working_memory.get(key)
        return self.short_term_memory.working_memory
    
    async def push_decision(self, decision: Dict):
        """Push a decision onto the decision stack."""
        if not self.short_term_memory.decision_stack:
            self.short_term_memory.decision_stack = []
        
        self.short_term_memory.decision_stack.append(decision)
        self.short_term_memory.decision_count += 1
        await self.db.commit()
    
    async def pop_decision(self) -> Optional[Dict]:
        """Pop a decision from the decision stack."""
        if self.short_term_memory.decision_stack:
            decision = self.short_term_memory.decision_stack.pop()
            await self.db.commit()
            return decision
        return None
    
    async def set_current_task(self, task: str, step: Optional[str] = None):
        """Set the current task and optionally the current step."""
        self.short_term_memory.current_task = task
        if step:
            self.short_term_memory.current_step = step
        await self.db.commit()
    
    async def add_active_lead(self, lead_id: int):
        """Add a lead to the active context."""
        if not self.short_term_memory.current_leads:
            self.short_term_memory.current_leads = []
        
        if lead_id not in self.short_term_memory.current_leads:
            self.short_term_memory.current_leads.append(lead_id)
            self.short_term_memory.leads_processed += 1
        
        # Update context state
        if not self.context_state.primary_lead_id:
            self.context_state.primary_lead_id = lead_id
        elif not self.context_state.secondary_lead_ids:
            self.context_state.secondary_lead_ids = [lead_id]
        elif lead_id not in self.context_state.secondary_lead_ids:
            self.context_state.secondary_lead_ids.append(lead_id)
        
        await self.db.commit()
    
    async def update_context_entities(self, entities: Dict):
        """Update active entities in context."""
        if not self.context_state.active_entities:
            self.context_state.active_entities = {}
        
        self.context_state.active_entities.update(entities)
        await self.db.commit()
    
    async def add_context_topic(self, topic: str):
        """Add a topic to the active context."""
        if not self.context_state.active_topics:
            self.context_state.active_topics = []
        
        if topic not in self.context_state.active_topics:
            self.context_state.active_topics.append(topic)
        
        await self.db.commit()
    
    async def retrieve_relevant_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Dict]:
        """Retrieve relevant memories based on query."""
        
        relevant_memories = []
        
        # Search conversation memories
        if not memory_types or 'conversation' in memory_types:
            conv_query = select(ConversationMemory).where(
                ConversationMemory.session_id == self.session_id
            ).order_by(desc(ConversationMemory.importance_score)).limit(limit)
            
            result = await self.db.execute(conv_query)
            conversations = result.scalars().all()
            
            for conv in conversations:
                relevant_memories.append({
                    'type': 'conversation',
                    'content': conv.message_content,
                    'importance': conv.importance_score,
                    'created_at': conv.created_at
                })
        
        # Search long-term memories
        if self.user_id and (not memory_types or 'long_term' in memory_types):
            lt_query = select(LongTermMemory).where(
                LongTermMemory.user_id == self.user_id,
                LongTermMemory.is_active == True
            ).order_by(desc(LongTermMemory.strength)).limit(limit)
            
            result = await self.db.execute(lt_query)
            long_terms = result.scalars().all()
            
            for lt in long_terms:
                relevant_memories.append({
                    'type': 'long_term',
                    'key': lt.memory_key,
                    'value': lt.memory_value,
                    'strength': lt.strength,
                    'frequency': lt.frequency
                })
        
        return relevant_memories
    
    async def create_episode(
        self,
        episode_type: str,
        lead_ids: Optional[List[int]] = None
    ) -> EpisodicMemory:
        """Create a new episodic memory."""
        
        episode_id = f"{self.session_id}_{episode_type}_{datetime.utcnow().timestamp()}"
        
        episode = EpisodicMemory(
            episode_id=episode_id,
            session_id=self.session_id,
            user_id=self.user_id,
            episode_type=episode_type,
            lead_ids=lead_ids,
            episode_start=datetime.utcnow(),
            actions_taken=[]
        )
        
        self.db.add(episode)
        await self.db.commit()
        await self.db.refresh(episode)
        
        return episode
    
    async def update_episode(
        self,
        episode_id: str,
        action: Optional[Dict] = None,
        outcome: Optional[str] = None,
        lessons: Optional[List[str]] = None
    ):
        """Update an episodic memory."""
        
        query = select(EpisodicMemory).where(
            EpisodicMemory.episode_id == episode_id
        )
        result = await self.db.execute(query)
        episode = result.scalar_one_or_none()
        
        if not episode:
            logger.warning(f"Episode {episode_id} not found")
            return
        
        if action:
            if not episode.actions_taken:
                episode.actions_taken = []
            episode.actions_taken.append(action)
        
        if outcome:
            episode.final_outcome = outcome
            from datetime import timezone
            now = datetime.now(timezone.utc) if episode.episode_start.tzinfo else datetime.now()
            episode.episode_end = now
            episode.duration_seconds = (
                episode.episode_end - episode.episode_start
            ).total_seconds()
        
        if lessons:
            episode.lessons_learned = lessons
        
        await self.db.commit()
    
    async def store_semantic_memory(
        self,
        content_type: str,
        content_id: str,
        content_text: str,
        topics: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> SemanticMemory:
        """Store semantic memory for content."""
        
        # Check if already exists
        query = select(SemanticMemory).where(
            SemanticMemory.content_type == content_type,
            SemanticMemory.content_id == content_id
        )
        result = await self.db.execute(query)
        memory = result.scalar_one_or_none()
        
        if memory:
            # Update existing
            memory.content_text = content_text
            memory.topics = topics
            memory.keywords = keywords
            memory.updated_at = datetime.utcnow()
        else:
            # Create new
            memory = SemanticMemory(
                content_type=content_type,
                content_id=content_id,
                content_text=content_text,
                topics=topics,
                keywords=keywords
            )
            self.db.add(memory)
        
        await self.db.commit()
        await self.db.refresh(memory)
        
        return memory
    
    async def find_similar_semantic_memories(
        self,
        content_text: str,
        content_type: Optional[str] = None,
        limit: int = 5
    ) -> List[SemanticMemory]:
        """Find semantically similar memories."""
        
        # Simple keyword-based similarity for now
        # In production, use embeddings and vector similarity
        
        keywords = self._extract_keywords(content_text)
        
        query = select(SemanticMemory)
        
        if content_type:
            query = query.where(SemanticMemory.content_type == content_type)
        
        # Order by retrieval count as a proxy for relevance
        query = query.order_by(desc(SemanticMemory.retrieval_count)).limit(limit * 2)
        
        result = await self.db.execute(query)
        candidates = result.scalars().all()
        
        # Score by keyword overlap
        scored = []
        for candidate in candidates:
            if candidate.keywords:
                overlap = len(set(keywords) & set(candidate.keywords))
                if overlap > 0:
                    scored.append((overlap, candidate))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        
        similar = [item[1] for item in scored[:limit]]
        
        # Update retrieval counts
        for memory in similar:
            memory.retrieval_count += 1
            memory.last_retrieved = datetime.utcnow()
        
        await self.db.commit()
        
        return similar
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified)."""
        # In production, use NLP library for proper extraction
        words = text.lower().split()
        # Filter common words
        stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but'}
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        return keywords[:10]  # Top 10 keywords
    
    async def decay_memories(self):
        """Apply decay to memories based on time and usage."""
        
        if not self.user_id:
            return
        
        # Decay long-term memories
        query = select(LongTermMemory).where(
            LongTermMemory.user_id == self.user_id,
            LongTermMemory.is_active == True
        )
        result = await self.db.execute(query)
        memories = result.scalars().all()
        
        # Use timezone-aware datetime if needed
        for memory in memories:
            # Calculate days since last access
            if memory.last_accessed:
                ref_time = memory.last_accessed
            else:
                ref_time = memory.created_at
                
            # Match timezone awareness
            now = datetime.now(timezone.utc) if ref_time.tzinfo else datetime.now()
            days_old = (now - ref_time).days
            
            # Apply decay based on age and reinforcement
            decay_rate = 0.01 * (1 / (1 + memory.reinforcement_count))
            memory.strength = max(0.1, memory.strength - (decay_rate * days_old))
            
            # Deactivate very weak memories
            if memory.strength < 0.1:
                memory.is_active = False
        
        await self.db.commit()
    
    async def consolidate_memories(self):
        """Consolidate short-term memories into long-term storage."""
        
        # Get important short-term memories
        query = select(ConversationMemory).where(
            ConversationMemory.session_id == self.session_id,
            ConversationMemory.importance_score > 0.7
        )
        result = await self.db.execute(query)
        important_memories = result.scalars().all()
        
        # Extract patterns and store in long-term memory
        for memory in important_memories:
            if memory.intent and self.user_id:
                await self._store_long_term_memory(
                    memory_type='pattern',
                    memory_key=f"pattern_{memory.intent}_{memory.id}",
                    memory_value={
                        'content': memory.message_content,
                        'entities': memory.entities,
                        'intent': memory.intent,
                        'lead_id': memory.lead_id
                    },
                    memory_category='conversation'
                )
        
        logger.info(f"Consolidated {len(important_memories)} memories for session {self.session_id}")
    
    async def get_memory_summary(self) -> Dict:
        """Get summary of current memory state."""
        
        summary = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'short_term': {
                'message_count': self.short_term_memory.message_count,
                'decision_count': self.short_term_memory.decision_count,
                'leads_processed': self.short_term_memory.leads_processed,
                'current_task': self.short_term_memory.current_task,
                'working_memory_size': len(self.short_term_memory.working_memory or {})
            },
            'context': {
                'primary_lead': self.context_state.primary_lead_id,
                'active_topics': self.context_state.active_topics,
                'requires_clarification': self.context_state.requires_clarification
            },
            'buffer_size': len(self.memory_buffer)
        }
        
        # Add long-term memory stats if user exists
        if self.user_id:
            lt_count = await self.db.execute(
                select(func.count(LongTermMemory.id)).where(
                    LongTermMemory.user_id == self.user_id,
                    LongTermMemory.is_active == True
                )
            )
            summary['long_term_memories'] = lt_count.scalar()
        
        return summary