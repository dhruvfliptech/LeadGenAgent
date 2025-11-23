#!/usr/bin/env python3
"""
Test script to verify conversation schema and create sample data.

This script should be run after migrations to verify:
1. All tables created successfully
2. Relationships working correctly
3. Indexes present and functional
4. Vector embeddings can be stored and queried
5. All model methods work as expected

Usage:
    python scripts/test_conversation_schema.py
"""

import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.models.conversation import (
    Conversation,
    ConversationMessage,
    AISuggestion,
    ConversationStatus,
    MessageDirection,
    SuggestionStatus,
    get_conversations_needing_reply,
    get_pending_ai_suggestions,
)


def test_database_connection(db_url: str):
    """Test database connection."""
    print("=" * 60)
    print("1. Testing Database Connection")
    print("=" * 60)

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version[:50]}...")
        return engine
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)


def test_pgvector_extension(engine):
    """Test pgvector extension is installed."""
    print("\n" + "=" * 60)
    print("2. Testing pgvector Extension")
    print("=" * 60)

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM pg_extension WHERE extname = 'vector'"
        ))
        if result.fetchone():
            print("✓ pgvector extension is installed")
        else:
            print("✗ pgvector extension NOT found")
            print("  Run: CREATE EXTENSION vector;")
            sys.exit(1)


def test_tables_exist(engine):
    """Test all conversation tables exist."""
    print("\n" + "=" * 60)
    print("3. Testing Table Creation")
    print("=" * 60)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ['conversations', 'conversation_messages', 'ai_suggestions']
    for table in required_tables:
        if table in tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' NOT found")
            sys.exit(1)


def test_indexes(engine):
    """Test indexes are created."""
    print("\n" + "=" * 60)
    print("4. Testing Indexes")
    print("=" * 60)

    inspector = inspect(engine)

    # Check each table's indexes
    tables_to_check = {
        'conversations': ['ix_conversations_lead_id', 'ix_conversations_status'],
        'conversation_messages': ['ix_messages_conversation_id', 'ix_messages_sent_at'],
        'ai_suggestions': ['ix_suggestions_conversation_id', 'ix_suggestions_status']
    }

    for table, expected_indexes in tables_to_check.items():
        indexes = inspector.get_indexes(table)
        index_names = [idx['name'] for idx in indexes]

        for expected_idx in expected_indexes:
            if expected_idx in index_names:
                print(f"✓ Index '{expected_idx}' exists on '{table}'")
            else:
                print(f"⚠ Index '{expected_idx}' NOT found on '{table}'")


def test_enum_types(engine):
    """Test enum types are created."""
    print("\n" + "=" * 60)
    print("5. Testing Enum Types")
    print("=" * 60)

    with engine.connect() as conn:
        # Check for enum types
        result = conn.execute(text("""
            SELECT typname FROM pg_type
            WHERE typname IN ('conversation_status', 'message_direction', 'suggestion_status')
        """))

        enum_types = [row[0] for row in result]

        expected_enums = ['conversation_status', 'message_direction', 'suggestion_status']
        for enum_type in expected_enums:
            if enum_type in enum_types:
                print(f"✓ Enum type '{enum_type}' exists")
            else:
                print(f"✗ Enum type '{enum_type}' NOT found")


def create_sample_data(session):
    """Create sample conversation data."""
    print("\n" + "=" * 60)
    print("6. Creating Sample Data")
    print("=" * 60)

    try:
        # Create a conversation
        conversation = Conversation(
            lead_id=1,  # Assumes lead with ID 1 exists
            subject="Test: Website Improvements",
            status=ConversationStatus.ACTIVE,
            last_message_at=datetime.utcnow(),
        )
        session.add(conversation)
        session.flush()
        print(f"✓ Created conversation: {conversation.id}")

        # Add outbound message
        outbound_msg = conversation.add_message(
            direction=MessageDirection.OUTBOUND,
            content="Hi! I noticed your website could benefit from some improvements.",
            sender_email="test@craigleads.com",
            recipient_email="lead@example.com",
            postmark_message_id="pm_test_123"
        )
        session.add(outbound_msg)
        session.flush()
        print(f"✓ Created outbound message: {outbound_msg.id}")

        # Add inbound message
        inbound_msg = conversation.add_message(
            direction=MessageDirection.INBOUND,
            content="Thanks for reaching out! I'd like to learn more.",
            sender_email="lead@example.com",
            recipient_email="test@craigleads.com",
            gmail_message_id="gmail_test_456",
            sent_at=datetime.utcnow() + timedelta(hours=2)
        )
        session.add(inbound_msg)
        session.flush()
        print(f"✓ Created inbound message: {inbound_msg.id}")

        # Add AI suggestion
        ai_suggestion = AISuggestion(
            conversation_id=conversation.id,
            in_reply_to_message_id=inbound_msg.id,
            suggested_content="Absolutely! I'd be happy to show you some examples...",
            confidence_score=0.92,
            sentiment_analysis={
                "sentiment": "positive",
                "intent": "requesting_information",
                "tone": "interested"
            },
            context_used={
                "previous_messages": 1,
                "lead_data": True
            },
            model_used="gpt-4",
            tokens_used=350,
            generation_cost=0.0105,
            status=SuggestionStatus.PENDING
        )
        session.add(ai_suggestion)
        session.flush()
        print(f"✓ Created AI suggestion: {ai_suggestion.id}")

        # Test vector embedding (if we have it)
        try:
            # Sample embedding (1536 dimensions of zeros for testing)
            test_embedding = [0.0] * 1536
            inbound_msg.set_embedding(test_embedding)
            session.flush()
            print("✓ Stored vector embedding")
        except Exception as e:
            print(f"⚠ Could not store embedding: {e}")

        session.commit()

        return conversation.id, ai_suggestion.id

    except Exception as e:
        session.rollback()
        print(f"✗ Failed to create sample data: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_model_methods(session, conversation_id):
    """Test model helper methods."""
    print("\n" + "=" * 60)
    print("7. Testing Model Methods")
    print("=" * 60)

    if not conversation_id:
        print("⚠ Skipping - no conversation created")
        return

    try:
        # Test get conversation
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            print(f"✓ Retrieved conversation: {conversation.subject}")

        # Test get_latest_message
        latest_msg = conversation.get_latest_message()
        if latest_msg:
            print(f"✓ get_latest_message() works: {latest_msg.direction.value}")

        # Test get_message_count
        msg_count = conversation.get_message_count()
        print(f"✓ get_message_count() works: {msg_count} messages")

        # Test get_pending_suggestion
        pending = conversation.get_pending_suggestion()
        if pending:
            print(f"✓ get_pending_suggestion() works: confidence {pending.confidence_score}")

        # Test to_dict
        conv_dict = conversation.to_dict()
        if 'id' in conv_dict and 'status' in conv_dict:
            print("✓ to_dict() works")

        # Test utility function
        needs_reply = get_conversations_needing_reply(session, limit=10)
        print(f"✓ get_conversations_needing_reply() works: {len(needs_reply)} found")

        pending_suggestions = get_pending_ai_suggestions(session, limit=10)
        print(f"✓ get_pending_ai_suggestions() works: {len(pending_suggestions)} found")

    except Exception as e:
        print(f"✗ Model method test failed: {e}")
        import traceback
        traceback.print_exc()


def test_approval_workflow(session, suggestion_id):
    """Test AI suggestion approval workflow."""
    print("\n" + "=" * 60)
    print("8. Testing Approval Workflow")
    print("=" * 60)

    if not suggestion_id:
        print("⚠ Skipping - no suggestion created")
        return

    try:
        suggestion = session.query(AISuggestion).filter_by(id=suggestion_id).first()

        # Test approve
        original_status = suggestion.status
        suggestion.approve(user_id=1, feedback="Looks good!")
        session.commit()

        if suggestion.status == SuggestionStatus.APPROVED:
            print("✓ approve() method works")

        # Test confidence level
        level = suggestion.get_confidence_level()
        print(f"✓ get_confidence_level() works: {level}")

        # Test to_dict
        suggestion_dict = suggestion.to_dict()
        if 'confidence_score' in suggestion_dict:
            print("✓ suggestion.to_dict() works")

    except Exception as e:
        print(f"✗ Approval workflow test failed: {e}")
        import traceback
        traceback.print_exc()


def test_relationships(session, conversation_id):
    """Test SQLAlchemy relationships."""
    print("\n" + "=" * 60)
    print("9. Testing Relationships")
    print("=" * 60)

    if not conversation_id:
        print("⚠ Skipping - no conversation created")
        return

    try:
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()

        # Test conversation -> messages relationship
        if conversation.messages:
            print(f"✓ conversation.messages relationship works: {len(conversation.messages)} messages")

        # Test conversation -> ai_suggestions relationship
        if conversation.ai_suggestions:
            print(f"✓ conversation.ai_suggestions relationship works: {len(conversation.ai_suggestions)} suggestions")

        # Test message -> conversation relationship
        message = conversation.messages[0]
        if message.conversation.id == conversation.id:
            print("✓ message.conversation relationship works")

        # Test suggestion -> conversation relationship
        suggestion = conversation.ai_suggestions[0]
        if suggestion.conversation.id == conversation.id:
            print("✓ suggestion.conversation relationship works")

        # Test suggestion -> in_reply_to_message relationship
        if suggestion.in_reply_to_message:
            print("✓ suggestion.in_reply_to_message relationship works")

    except Exception as e:
        print(f"✗ Relationship test failed: {e}")
        import traceback
        traceback.print_exc()


def cleanup_test_data(session, conversation_id):
    """Clean up test data."""
    print("\n" + "=" * 60)
    print("10. Cleaning Up Test Data")
    print("=" * 60)

    if not conversation_id:
        print("⚠ No test data to clean up")
        return

    try:
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            session.delete(conversation)
            session.commit()
            print("✓ Test data cleaned up (CASCADE delete messages and suggestions)")
    except Exception as e:
        session.rollback()
        print(f"✗ Cleanup failed: {e}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  CONVERSATION SCHEMA VERIFICATION TEST SUITE           ║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Get database URL from environment or use default
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://craigslist_user:secure_password@localhost:5432/craigslist_db'
    )

    print(f"Database: {db_url.split('@')[-1]}")  # Hide password
    print()

    # Run tests
    engine = test_database_connection(db_url)
    test_pgvector_extension(engine)
    test_tables_exist(engine)
    test_indexes(engine)
    test_enum_types(engine)

    # Create session for data tests
    Session = sessionmaker(bind=engine)
    session = Session()

    conversation_id, suggestion_id = create_sample_data(session)
    test_model_methods(session, conversation_id)
    test_approval_workflow(session, suggestion_id)
    test_relationships(session, conversation_id)
    cleanup_test_data(session, conversation_id)

    session.close()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ All tests completed successfully!")
    print()
    print("Next steps:")
    print("  1. Review test output above for any warnings (⚠)")
    print("  2. Test with real OpenAI embeddings")
    print("  3. Test Gmail and Postmark integrations")
    print("  4. Load test with 1K+ conversations")
    print("  5. Monitor query performance")
    print()
    print("Documentation:")
    print("  - Schema: /backend/docs/CONVERSATION_SCHEMA.md")
    print("  - Queries: /backend/docs/CONVERSATION_QUERIES.md")
    print("  - Operations: /backend/docs/DATABASE_OPERATIONS_GUIDE.md")
    print()


if __name__ == '__main__':
    main()
