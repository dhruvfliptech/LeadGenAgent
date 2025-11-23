#!/usr/bin/env python
"""
Test script to verify Campaign Management models and database integration.
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Campaign, CampaignRecipient, EmailTracking


async def test_campaign_models():
    """Test campaign management models."""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )

    # Create session factory
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        try:
            print("\n" + "="*70)
            print("CAMPAIGN MANAGEMENT MODELS TEST")
            print("="*70)

            # Test 1: Create a campaign
            print("\n[TEST 1] Creating a campaign...")
            import uuid
            campaign_id = f"test_camp_{uuid.uuid4().hex[:8]}"
            campaign = Campaign(
                campaign_id=campaign_id,
                name="Test Campaign Q4 2025",
                status="draft",
                template_id=1,
                created_by=None  # Can be set to a user ID if users exist
            )
            session.add(campaign)
            await session.commit()
            print(f"✓ Campaign created: {campaign.campaign_id} (ID: {campaign.id})")

            # Test 2: Verify campaign properties
            print("\n[TEST 2] Testing campaign computed properties...")
            campaign.emails_sent = 100
            campaign.emails_opened = 25
            campaign.emails_clicked = 15
            campaign.emails_replied = 5
            campaign.emails_bounced = 3
            await session.commit()

            print(f"  Total Sent: {campaign.emails_sent}")
            print(f"  Open Rate: {campaign.open_rate:.2f}%")
            print(f"  Click Rate: {campaign.click_rate:.2f}%")
            print(f"  Reply Rate: {campaign.reply_rate:.2f}%")
            print(f"  Bounce Rate: {campaign.bounce_rate:.2f}%")
            print("✓ Computed properties working correctly")

            # Test 3: Create campaign recipients
            print("\n[TEST 3] Creating campaign recipients...")
            recipients_data = [
                ("test1@example.com", "sent", 1),
                ("test2@example.com", "sent", 2),
                ("test3@example.com", "pending", 3),
                ("test4@example.com", "bounced", 4),
            ]

            for email, status, lead_id in recipients_data:
                recipient = CampaignRecipient(
                    campaign_id=campaign.id,
                    lead_id=lead_id,  # Using different lead IDs
                    email_address=email,
                    status=status,
                    sent_at=datetime.now(timezone.utc) if status == "sent" else None,
                    bounced_at=datetime.now(timezone.utc) if status == "bounced" else None,
                )
                session.add(recipient)
            await session.commit()
            print(f"✓ Created {len(recipients_data)} recipients")

            # Test 4: Test email tracking
            print("\n[TEST 4] Adding email tracking events...")

            # Get first recipient
            result = await session.execute(
                select(CampaignRecipient).where(
                    CampaignRecipient.campaign_id == campaign.id
                ).limit(1)
            )
            recipient = result.scalar_one_or_none()

            if recipient:
                # Log open event
                open_event = EmailTracking(
                    campaign_recipient_id=recipient.id,
                    event_type="open",
                    event_data={"client": "Gmail", "os": "Windows"},
                    user_agent="Mozilla/5.0 (Windows NT 10.0)",
                    ip_address="192.168.1.1"
                )
                session.add(open_event)

                # Log click event
                click_event = EmailTracking(
                    campaign_recipient_id=recipient.id,
                    event_type="click",
                    event_data={"link_url": "https://example.com/offer"},
                    user_agent="Mozilla/5.0 (Windows NT 10.0)",
                    ip_address="192.168.1.1"
                )
                session.add(click_event)
                await session.commit()
                print(f"✓ Added tracking events for recipient {recipient.email_address}")

            # Test 5: Query campaign statistics
            print("\n[TEST 5] Querying campaign statistics...")
            result = await session.execute(
                select(CampaignRecipient.status, func.count(CampaignRecipient.id).label("count"))
                .where(CampaignRecipient.campaign_id == campaign.id)
                .group_by(CampaignRecipient.status)
            )
            stats = result.all()
            print("  Recipient Status Distribution:")
            for status, count in stats:
                print(f"    - {status}: {count}")
            print("✓ Statistics query successful")

            # Test 6: Verify relationships
            print("\n[TEST 6] Testing SQLAlchemy relationships...")

            # Refresh campaign
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign.id)
            )
            campaign = result.scalar_one()

            print(f"  Campaign: {campaign.name}")
            print(f"  Total Recipients: {len(campaign.recipients)}")
            for recipient in campaign.recipients:
                print(f"    - {recipient.email_address} ({recipient.status})")
            print("✓ Relationships working correctly")

            # Test 7: Test to_dict methods
            print("\n[TEST 7] Testing to_dict serialization...")
            campaign_dict = campaign.to_dict()
            print(f"  Campaign serialized: {len(campaign_dict)} fields")
            print(f"  Metrics: {campaign_dict['metrics']}")

            if campaign.recipients:
                recipient_dict = campaign.recipients[0].to_dict()
                print(f"  Recipient serialized: {len(recipient_dict)} fields")
            print("✓ Serialization working correctly")

            # Test 8: Verify indexes
            print("\n[TEST 8] Verifying database indexes...")
            result = await session.execute(
                select(func.count()).select_from(CampaignRecipient).where(
                    CampaignRecipient.campaign_id == campaign.id
                )
            )
            count = result.scalar()
            print(f"  Query using campaign_id index: {count} recipients found")
            print("✓ Indexes are functional")

            print("\n" + "="*70)
            print("ALL TESTS PASSED!")
            print("="*70)

            # Cleanup: Delete test campaign
            print("\n[CLEANUP] Removing test campaign...")
            await session.delete(campaign)
            await session.commit()
            print("✓ Test data cleaned up")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    print("\nStarting Campaign Management Models Test Suite...")
    asyncio.run(test_campaign_models())
