"""
Email Finder Service - Usage Examples

This file demonstrates how to use the EmailFinderService in your code.
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.email_finder import EmailFinderService
from app.models.email_finder import ServiceName
from app.integrations.hunter_io import HunterIOClient
from app.core.config import settings


async def example_1_find_emails_by_domain(db: AsyncSession):
    """
    Example 1: Find all emails for a company domain.

    Use case: You have a list of company domains and want to find
    all employee emails for each company.
    """
    print("\n=== Example 1: Find Emails by Domain ===")

    service = EmailFinderService(db)

    # Find up to 10 emails for Stripe
    emails = await service.find_emails_by_domain(
        domain="stripe.com",
        limit=10
    )

    print(f"\nFound {len(emails)} emails for stripe.com:")
    for email in emails:
        print(f"  - {email.email}")
        print(f"    Source: {email.source.value}")
        print(f"    Confidence: {email.confidence_score}%")
        if email.position:
            print(f"    Position: {email.position}")
        print()

    await service.close()


async def example_2_find_person_email(db: AsyncSession):
    """
    Example 2: Find a specific person's email.

    Use case: You know the person's name and company, want to find their email.
    """
    print("\n=== Example 2: Find Person's Email ===")

    service = EmailFinderService(db)

    # Find Patrick Collison's email at Stripe
    email = await service.find_person_email(
        name="Patrick Collison",
        domain="stripe.com"
    )

    if email:
        print(f"\nFound email for Patrick Collison:")
        print(f"  Email: {email.email}")
        print(f"  Source: {email.source.value}")
        print(f"  Confidence: {email.confidence_score}%")
    else:
        print("\nNo email found for Patrick Collison at stripe.com")

    await service.close()


async def example_3_verify_email(db: AsyncSession):
    """
    Example 3: Verify if an email is valid.

    Use case: Before sending an important email, verify it's deliverable.
    """
    print("\n=== Example 3: Verify Email ===")

    service = EmailFinderService(db)

    # Verify an email address
    verification = await service.verify_email("patrick@stripe.com")

    print(f"\nEmail: {verification['email']}")
    print(f"Valid: {verification['valid']}")
    print(f"Score: {verification.get('score', 'N/A')}/100")
    print(f"Result: {verification.get('result', 'unknown')}")

    if verification.get('details'):
        print("\nDetails:")
        for key, value in verification['details'].items():
            print(f"  {key}: {value}")

    await service.close()


async def example_4_check_quota(db: AsyncSession):
    """
    Example 4: Check quota status before making API calls.

    Use case: Monitor quota to prevent overage charges.
    """
    print("\n=== Example 4: Check Quota Status ===")

    service = EmailFinderService(db)

    # Get quota status for Hunter.io
    quota = await service.get_quota_status(ServiceName.HUNTER_IO)

    if quota.get('configured'):
        print(f"\nService: {quota['service']}")
        print(f"Period: {quota.get('period', 'N/A')}")

        if quota.get('quota'):
            q = quota['quota']
            print(f"\nQuota:")
            print(f"  Used: {q['used']}/{q['limit']}")
            print(f"  Remaining: {q['remaining']}")
            print(f"  Percentage: {q['percentage']:.1f}%")

        if quota.get('alerts'):
            a = quota['alerts']
            print(f"\nAlerts:")
            print(f"  Near limit (80%): {a['near_limit']}")
            print(f"  Exceeded: {a['exceeded']}")

            if a['near_limit']:
                print("\n⚠️  WARNING: Approaching quota limit!")
            if a['exceeded']:
                print("\n🛑 ERROR: Quota exceeded! Using fallback methods.")
    else:
        print(f"\nService {quota['service']} not configured")

    await service.close()


async def example_5_batch_domain_search(db: AsyncSession):
    """
    Example 5: Find emails for multiple domains efficiently.

    Use case: You have 50 company domains and want to find emails for all.
    """
    print("\n=== Example 5: Batch Domain Search ===")

    service = EmailFinderService(db)

    # List of domains
    domains = [
        "stripe.com",
        "google.com",
        "microsoft.com",
        "apple.com",
        "amazon.com"
    ]

    results = {}

    # Check quota first
    quota = await service.get_quota_status(ServiceName.HUNTER_IO)
    if quota.get('alerts', {}).get('exceeded'):
        print("⚠️  Quota exceeded! Results will come from cache and scraping only.")

    # Process each domain
    for domain in domains:
        print(f"\nProcessing {domain}...")
        emails = await service.find_emails_by_domain(domain, limit=5)
        results[domain] = emails
        print(f"  Found {len(emails)} emails")

        # Show first email as example
        if emails:
            print(f"  Example: {emails[0].email} ({emails[0].confidence_score}% confidence)")

    await service.close()

    # Summary
    print("\n=== Summary ===")
    total_emails = sum(len(emails) for emails in results.values())
    print(f"Total domains processed: {len(domains)}")
    print(f"Total emails found: {total_emails}")
    print(f"Average emails per domain: {total_emails / len(domains):.1f}")


async def example_6_with_lead_association(db: AsyncSession, lead_id: int):
    """
    Example 6: Find emails and associate with a lead.

    Use case: You scraped a Craigslist job posting, now find the company's emails.
    """
    print("\n=== Example 6: Find Emails for Lead ===")

    service = EmailFinderService(db)

    # Assuming you have a lead with company domain
    company_domain = "example-company.com"

    # Find emails and associate with lead
    emails = await service.find_emails_by_domain(
        domain=company_domain,
        lead_id=lead_id,  # Associate with lead
        limit=5
    )

    print(f"\nFound {len(emails)} emails for Lead #{lead_id}:")
    for email in emails:
        print(f"  - {email.email}")
        print(f"    Confidence: {email.confidence_score}%")
        print(f"    Associated with Lead #{email.lead_id}")

    await service.close()


async def example_7_filter_by_confidence(db: AsyncSession):
    """
    Example 7: Filter emails by confidence score.

    Use case: Only use emails with high confidence for important campaigns.
    """
    print("\n=== Example 7: Filter by Confidence ===")

    service = EmailFinderService(db)

    # Find all emails
    all_emails = await service.find_emails_by_domain(
        domain="stripe.com",
        limit=20
    )

    # Filter by confidence levels
    high_confidence = [e for e in all_emails if (e.confidence_score or 0) >= 70]
    medium_confidence = [e for e in all_emails if 40 <= (e.confidence_score or 0) < 70]
    low_confidence = [e for e in all_emails if (e.confidence_score or 0) < 40]

    print(f"\nTotal emails: {len(all_emails)}")
    print(f"High confidence (≥70%): {len(high_confidence)}")
    print(f"Medium confidence (40-69%): {len(medium_confidence)}")
    print(f"Low confidence (<40%): {len(low_confidence)}")

    print("\n✅ Using only high-confidence emails for important campaign:")
    for email in high_confidence[:5]:
        print(f"  - {email.email} ({email.confidence_score}%)")

    await service.close()


async def example_8_direct_hunter_io_usage():
    """
    Example 8: Use Hunter.io client directly (advanced).

    Use case: You want direct control over Hunter.io API calls.
    """
    print("\n=== Example 8: Direct Hunter.io Client Usage ===")

    if not settings.HUNTER_IO_API_KEY:
        print("⚠️  Hunter.io API key not configured")
        return

    # Create Hunter.io client
    async with HunterIOClient(settings.HUNTER_IO_API_KEY) as client:

        # Get account info
        print("\nFetching account information...")
        account_info = await client.get_account_info()
        print(f"Plan: {account_info.get('plan_name', 'Unknown')}")
        print(f"Requests used: {account_info.get('calls', 0)}")
        print(f"Requests available: {account_info.get('requests_available', 0)}")

        # Domain search
        print("\nSearching emails for stripe.com...")
        result = await client.domain_search("stripe.com", limit=5)
        print(f"Domain: {result['domain']}")
        print(f"Organization: {result['organization']}")
        print(f"Pattern: {result['pattern']}")
        print(f"Emails found: {len(result['emails'])}")

        for email_result in result['emails'][:3]:
            print(f"\n  Email: {email_result.value}")
            print(f"  Confidence: {email_result.confidence}%")
            print(f"  Position: {email_result.position or 'N/A'}")


async def example_9_error_handling(db: AsyncSession):
    """
    Example 9: Proper error handling.

    Use case: Production code needs robust error handling.
    """
    print("\n=== Example 9: Error Handling ===")

    service = EmailFinderService(db)

    try:
        # Try to find emails
        emails = await service.find_emails_by_domain("stripe.com", limit=10)
        print(f"✅ Found {len(emails)} emails")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

        # Check if it's a quota issue
        quota = await service.get_quota_status(ServiceName.HUNTER_IO)
        if quota.get('alerts', {}).get('exceeded'):
            print("📊 Quota exceeded - using fallback methods")
            # Continue with scraping fallback
        else:
            print("🔧 Other error - check logs")
            raise

    finally:
        await service.close()


async def example_10_integration_in_lead_processing(db: AsyncSession):
    """
    Example 10: Integrate email finder in lead processing pipeline.

    Use case: Automatically find emails for all new leads.
    """
    print("\n=== Example 10: Lead Processing Integration ===")

    # Simulate processing a new lead
    lead_data = {
        "id": 123,
        "company_name": "Stripe",
        "website": "https://stripe.com",
        "title": "Senior Developer position"
    }

    # Extract domain from website
    import re
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', lead_data['website'])
    if not domain_match:
        print("❌ Could not extract domain from website")
        return

    domain = domain_match.group(1)
    print(f"\nProcessing Lead #{lead_data['id']}: {lead_data['company_name']}")
    print(f"Website: {lead_data['website']}")
    print(f"Domain: {domain}")

    # Find emails for this lead
    service = EmailFinderService(db)
    emails = await service.find_emails_by_domain(
        domain=domain,
        lead_id=lead_data['id'],
        limit=5
    )

    print(f"\n✅ Found {len(emails)} emails for this lead:")

    # Filter to get best emails
    best_emails = sorted(
        emails,
        key=lambda e: (e.confidence_score or 0, not e.is_generic),
        reverse=True
    )[:3]

    print("\n📧 Top 3 emails to contact:")
    for i, email in enumerate(best_emails, 1):
        print(f"\n{i}. {email.email}")
        print(f"   Confidence: {email.confidence_score}%")
        print(f"   Source: {email.source.value}")
        if email.position:
            print(f"   Position: {email.position}")
        print(f"   Generic: {'Yes' if email.is_generic else 'No'}")

    await service.close()


# Main execution
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        Email Finder Service - Usage Examples              ║
    ║                                                            ║
    ║  This file demonstrates various ways to use the           ║
    ║  EmailFinderService in your application.                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    print("\nThese are code examples only.")
    print("To run them, integrate into your application with a database session.")
    print("\nSee EMAIL_FINDER_SETUP_GUIDE.md for API endpoint examples.")
