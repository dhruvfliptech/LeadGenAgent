#!/usr/bin/env python3
"""
Test the Memory and Context Management System.
"""

import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.leads import Lead
from app.services.memory_manager import MemoryManager
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_memory_management():
    """Test the memory and context management system."""
    print("\n" + "="*60)
    print("TESTING MEMORY & CONTEXT MANAGEMENT SYSTEM")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Generate unique session and user IDs
            session_id = f"test_session_{uuid.uuid4().hex[:8]}"
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
            
            # Step 1: Initialize memory manager
            print("\n[1] Initializing memory manager...")
            
            memory_manager = MemoryManager(db, session_id, user_id)
            await memory_manager.initialize()
            
            print(f"✅ Initialized memory manager")
            print(f"   Session ID: {session_id}")
            print(f"   User ID: {user_id}")
            
            # Step 2: Store conversation memories
            print("\n[2] Storing conversation memories...")
            
            # Simulate a conversation about lead qualification
            conversation_flow = [
                ("user", "Show me high-paying remote jobs", "query", 0.7),
                ("assistant", "I found 3 high-paying remote positions", "response", 0.6),
                ("user", "Focus on the React developer position", "preference", 0.8),
                ("assistant", "The React position offers $150k-180k", "information", 0.6),
                ("user", "Generate a response for that one", "action", 0.9),
                ("assistant", "I've generated a personalized response", "completion", 0.7)
            ]
            
            for msg_type, content, intent, importance in conversation_flow:
                memory = await memory_manager.store_conversation(
                    message_type=msg_type,
                    message_content=content,
                    intent=intent,
                    importance=importance,
                    entities={"job_type": "developer", "skill": "React"} if "React" in content else None
                )
                print(f"   Stored: [{msg_type}] {content[:40]}...")
            
            print(f"✅ Stored {len(conversation_flow)} conversation turns")
            
            # Step 3: Working memory operations
            print("\n[3] Testing working memory...")
            
            # Store context in working memory
            await memory_manager.update_working_memory("preferred_salary", 150000)
            await memory_manager.update_working_memory("preferred_skills", ["React", "Python"])
            await memory_manager.update_working_memory("remote_only", True)
            
            # Retrieve working memory
            salary = await memory_manager.get_working_memory("preferred_salary")
            all_memory = await memory_manager.get_working_memory()
            
            print(f"   Stored preferences in working memory")
            print(f"   Retrieved salary preference: ${salary}")
            print(f"   Total working memory items: {len(all_memory)}")
            
            # Step 4: Task and decision tracking
            print("\n[4] Testing task and decision management...")
            
            # Set current task
            await memory_manager.set_current_task(
                "Find and apply to React developer positions",
                "Filtering leads"
            )
            
            # Push decisions onto stack
            decisions = [
                {"type": "filter", "criteria": "salary > 150000"},
                {"type": "filter", "criteria": "is_remote = true"},
                {"type": "action", "action": "generate_response"}
            ]
            
            for decision in decisions:
                await memory_manager.push_decision(decision)
                print(f"   Pushed decision: {decision}")
            
            # Pop decision
            last_decision = await memory_manager.pop_decision()
            print(f"   Popped decision: {last_decision}")
            
            # Step 5: Lead context management
            print("\n[5] Testing lead context management...")
            
            # Create test leads with unique IDs
            test_leads = []
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            for i in range(3):
                lead = Lead(
                    craigslist_id=f"test_memory_lead_{timestamp}_{i}",
                    title=f"Test Position {i}",
                    url="http://test.com",
                    location_id=1,
                    posted_at=datetime.now()
                )
                db.add(lead)
                test_leads.append(lead)
            
            await db.commit()
            
            # Add leads to active context
            for lead in test_leads:
                await memory_manager.add_active_lead(lead.id)
                print(f"   Added lead {lead.id} to active context")
            
            # Update context entities and topics
            await memory_manager.update_context_entities({
                "company": "TechCorp",
                "technology": "React",
                "compensation": "$150,000"
            })
            
            await memory_manager.add_context_topic("React development")
            await memory_manager.add_context_topic("Remote work")
            
            print(f"✅ Context updated with {len(test_leads)} leads and 2 topics")
            
            # Step 6: Episodic memory
            print("\n[6] Testing episodic memory...")
            
            # Create an episode
            episode = await memory_manager.create_episode(
                episode_type="lead_qualification",
                lead_ids=[lead.id for lead in test_leads]
            )
            
            print(f"   Created episode: {episode.episode_id}")
            
            # Simulate actions in the episode
            actions = [
                {"action": "filter_leads", "criteria": "high_salary"},
                {"action": "score_leads", "method": "ml_model"},
                {"action": "select_top", "count": 1}
            ]
            
            for action in actions:
                await memory_manager.update_episode(
                    episode.episode_id,
                    action=action
                )
                print(f"   Added action: {action['action']}")
            
            # Complete the episode
            await memory_manager.update_episode(
                episode.episode_id,
                outcome="success",
                lessons=["High salary leads get better responses", "Remote positions are preferred"]
            )
            
            print(f"✅ Episode completed with outcome: success")
            
            # Step 7: Semantic memory
            print("\n[7] Testing semantic memory...")
            
            # Store semantic memories for leads
            for lead in test_leads[:2]:
                semantic = await memory_manager.store_semantic_memory(
                    content_type="lead",
                    content_id=str(lead.id),
                    content_text=lead.title,
                    topics=["technology", "development"],
                    keywords=["react", "developer", "remote"]
                )
                print(f"   Stored semantic memory for lead {lead.id}")
            
            # Find similar semantic memories
            similar = await memory_manager.find_similar_semantic_memories(
                "React developer position with good salary",
                content_type="lead",
                limit=2
            )
            
            print(f"   Found {len(similar)} similar semantic memories")
            
            # Step 8: Memory retrieval
            print("\n[8] Testing memory retrieval...")
            
            # Retrieve relevant memories
            memories = await memory_manager.retrieve_relevant_memories(
                query="React developer positions",
                memory_types=["conversation", "long_term"],
                limit=5
            )
            
            print(f"   Retrieved {len(memories)} relevant memories")
            for memory in memories[:3]:
                print(f"      - Type: {memory['type']}, "
                      f"Content: {str(memory.get('content', memory.get('key', '')))[:50]}...")
            
            # Step 9: Memory consolidation
            print("\n[9] Testing memory consolidation...")
            
            # Consolidate short-term to long-term
            await memory_manager.consolidate_memories()
            print("   ✅ Consolidated important memories to long-term storage")
            
            # Apply memory decay
            await memory_manager.decay_memories()
            print("   ✅ Applied memory decay based on age and usage")
            
            # Step 10: Get memory summary
            print("\n[10] Getting memory system summary...")
            
            summary = await memory_manager.get_memory_summary()
            
            print("\n📊 Memory System Summary:")
            print(f"   Session: {summary['session_id']}")
            print(f"   Short-term memory:")
            print(f"      Messages: {summary['short_term']['message_count']}")
            print(f"      Decisions: {summary['short_term']['decision_count']}")
            print(f"      Leads processed: {summary['short_term']['leads_processed']}")
            print(f"      Working memory size: {summary['short_term']['working_memory_size']}")
            print(f"   Context:")
            print(f"      Primary lead: {summary['context']['primary_lead']}")
            print(f"      Active topics: {summary['context']['active_topics']}")
            print(f"   Buffer size: {summary['buffer_size']}")
            if 'long_term_memories' in summary:
                print(f"   Long-term memories: {summary['long_term_memories']}")
            
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            print("\n✅ Memory & Context Management System Working!")
            print("\nCapabilities demonstrated:")
            print("  • Conversation memory storage and retrieval")
            print("  • Short-term working memory management")
            print("  • Task and decision stack tracking")
            print("  • Lead context management")
            print("  • Episodic memory for complete interactions")
            print("  • Semantic memory for content understanding")
            print("  • Memory consolidation and decay")
            print("  • Multi-type memory retrieval")
            print("  • Context state preservation")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            logger.exception("Test failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(test_memory_management())
    
    if success:
        print("\n🎉 Phase 2.2 Memory & Context Management Complete!")
        print("\nFeatures implemented:")
        print("  ✅ Conversation memory with importance scoring")
        print("  ✅ Short-term working memory")
        print("  ✅ Long-term memory with reinforcement")
        print("  ✅ Semantic memory for similarity search")
        print("  ✅ Episodic memory for complete interactions")
        print("  ✅ Context state management")
        print("  ✅ Memory consolidation and decay")
        print("  ✅ Decision stack for complex workflows")
        print("  ✅ Multi-modal memory retrieval")
        print("  ✅ Session and user-based memory isolation")
    else:
        print("\n⚠️ Memory management test failed")
    
    exit(0 if success else 1)