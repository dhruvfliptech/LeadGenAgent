"""
Populate Knowledge Base with Example Entries

This script creates sample knowledge base entries for FlipTech Pro.
Run this after setting up the database to get started quickly.

Usage:
    python examples/populate_knowledge_base.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.knowledge_base import KnowledgeBaseEntryCreate, EntryTypeEnum


def create_example_entries():
    """Create example knowledge base entries"""

    db = SessionLocal()
    kb_service = KnowledgeBaseService(db)

    print("Creating example knowledge base entries...")
    print("=" * 60)

    entries = [
        # COMPANY INFO
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.COMPANY_INFO,
            title="FlipTech Pro - Company Overview",
            content="""FlipTech Pro is a real estate technology company specializing in automated lead generation
            for house flipping and wholesale real estate investing. We use AI-powered tools to scrape listings
            from Craigslist and other platforms, identify motivated sellers, and facilitate quick property
            acquisitions. Our mission is to help real estate investors find the best deals faster using
            cutting-edge automation and AI.""",
            metadata={
                "company_name": "FlipTech Pro",
                "industry": "Real Estate Technology",
                "founded": "2024",
                "specialties": ["house flipping", "lead generation", "AI automation", "wholesale real estate"],
                "location": "United States"
            },
            tags=["company", "about", "overview"],
            category="company_info",
            priority=95
        ),

        # SERVICE DESCRIPTIONS
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.SERVICE_DESCRIPTION,
            title="Automated Lead Generation Service",
            content="""Our automated lead generation service scans Craigslist and other platforms 24/7 to find
            potential house flipping opportunities. We identify properties with keywords like 'fixer upper',
            'handyman special', 'needs work', and 'motivated seller'. Our AI analyzes listings, extracts contact
            information, and scores leads based on your criteria. You receive qualified leads ready for outreach,
            saving hours of manual searching.""",
            metadata={
                "service_name": "Automated Lead Generation",
                "pricing_model": "subscription",
                "features": [
                    "24/7 automated scanning",
                    "Multi-platform support",
                    "AI-powered lead scoring",
                    "Contact extraction",
                    "Email automation"
                ],
                "target_audience": "real estate investors, house flippers, wholesalers"
            },
            tags=["service", "lead_generation", "automation"],
            category="services",
            priority=100
        ),

        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.SERVICE_DESCRIPTION,
            title="AI Email Response System",
            content="""Our AI Email Response System automatically crafts personalized responses to property sellers.
            The AI understands context, references your business policies, and maintains a professional tone.
            It can handle initial inquiries, answer FAQs, schedule property viewings, and negotiate terms.
            All responses are reviewed before sending to ensure quality and accuracy.""",
            metadata={
                "service_name": "AI Email Response System",
                "features": [
                    "Personalized email generation",
                    "Context-aware responses",
                    "FAQ automation",
                    "Appointment scheduling",
                    "Human-in-the-loop approval"
                ]
            },
            tags=["service", "ai", "email", "automation"],
            category="services",
            priority=90
        ),

        # FAQs
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.FAQ,
            title="Response Time Policy",
            content="""We respond to all leads within 24 hours during business days (Monday-Friday, 9 AM - 6 PM EST).
            For urgent inquiries marked as 'motivated seller' or 'quick sale needed', we provide same-day responses.
            Our AI system monitors incoming emails continuously and can send initial automated responses immediately.""",
            metadata={
                "question": "What is your response time?",
                "related_topics": ["customer_service", "response_time", "business_hours"]
            },
            tags=["faq", "customer_service", "timing", "response"],
            category="customer_support",
            priority=85
        ),

        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.FAQ,
            title="Property Buying Process",
            content="""Our buying process is simple and fast: 1) We receive your property listing or contact you
            based on our lead generation. 2) We review the property details and ask clarifying questions.
            3) We schedule a property viewing or virtual walkthrough. 4) We make a cash offer within 48 hours.
            5) If accepted, we close within 7-14 days with no contingencies. We handle all paperwork and closing costs.""",
            metadata={
                "question": "What is your buying process?",
                "process_steps": [
                    "Initial contact",
                    "Property review",
                    "Viewing/walkthrough",
                    "Cash offer (48 hours)",
                    "Closing (7-14 days)"
                ]
            },
            tags=["faq", "buying_process", "timeline"],
            category="sales",
            priority=90
        ),

        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.FAQ,
            title="Property Criteria",
            content="""We're interested in properties that need work or have motivated sellers. Ideal properties are
            priced between $50,000 and $300,000, require cosmetic or moderate repairs, and are in our target markets.
            We prefer single-family homes, duplexes, or small multi-family properties. We buy properties as-is and
            handle all repairs ourselves.""",
            metadata={
                "question": "What types of properties do you buy?",
                "criteria": {
                    "price_range": {"min": 50000, "max": 300000},
                    "property_types": ["single-family", "duplex", "multi-family"],
                    "condition": ["needs cosmetic work", "needs moderate repairs", "fixer-upper"],
                    "seller_motivation": ["motivated seller", "quick sale", "as-is"]
                }
            },
            tags=["faq", "property_criteria", "requirements"],
            category="sales",
            priority=88
        ),

        # SEARCH RULES
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.SEARCH_RULE,
            title="Craigslist Fixer-Upper Search Criteria",
            content="""When searching Craigslist for potential properties, prioritize listings with these keywords:
            'handyman special', 'fixer upper', 'needs work', 'TLC', 'as-is', 'cash only', 'motivated seller',
            'must sell', 'bring all offers'. Exclude listings with: 'rental', 'lease', 'room for rent', 'commercial'.
            Target price range: $50k-$300k. Focus on real estate for sale categories.""",
            metadata={
                "platform": "craigslist",
                "include_keywords": [
                    "handyman special", "fixer upper", "needs work", "TLC", "as-is",
                    "cash only", "motivated seller", "must sell", "bring all offers",
                    "needs repairs", "investor special"
                ],
                "exclude_keywords": ["rental", "lease", "room for rent", "commercial", "business"],
                "price_range": {"min": 50000, "max": 300000},
                "categories": ["real estate for sale", "housing", "apts/housing for sale"]
            },
            tags=["search", "craigslist", "criteria", "keywords"],
            category="scraping",
            priority=95
        ),

        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.SEARCH_RULE,
            title="Target Geographic Markets",
            content="""Our primary target markets include: San Francisco Bay Area, Los Angeles, San Diego, Phoenix,
            Las Vegas, Austin, Houston, Dallas, Atlanta, and Miami. We focus on urban and suburban areas with strong
            rental demand and appreciation potential. We prefer zip codes with median home prices between $200k-$500k
            and active real estate markets.""",
            metadata={
                "regions": ["sfbay", "losangeles", "sandiego", "phoenix", "vegas", "austin", "houston", "dallas", "atlanta", "miami"],
                "market_criteria": {
                    "median_price_range": {"min": 200000, "max": 500000},
                    "area_types": ["urban", "suburban"],
                    "market_activity": "active"
                }
            },
            tags=["search", "geography", "markets", "targeting"],
            category="scraping",
            priority=80
        ),

        # QUALIFICATION RULES
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.QUALIFICATION_RULE,
            title="High-Value Lead Scoring Criteria",
            content="""A lead qualifies as high-value (score 80+) if it meets these criteria: Property price is
            $100k-$250k, listing explicitly mentions 'motivated seller' or 'quick sale', property condition requires
            work, seller responds within 48 hours, contact information (phone/email) is provided, property is in
            target zip code, and listing has been active for 30+ days. These indicators suggest serious sellers
            and good profit potential.""",
            metadata={
                "rule_name": "High Value Lead",
                "score_threshold": 80,
                "criteria": {
                    "price_range": {"min": 100000, "max": 250000},
                    "motivation_keywords": ["motivated seller", "quick sale", "must sell"],
                    "condition_keywords": ["needs work", "fixer", "handyman special"],
                    "response_time": "< 48 hours",
                    "contact_required": True,
                    "listing_age": "> 30 days"
                },
                "score_weight": 0.85,
                "auto_approve": False
            },
            tags=["qualification", "scoring", "high_value", "criteria"],
            category="lead_qualification",
            priority=90
        ),

        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.QUALIFICATION_RULE,
            title="Disqualification Criteria",
            content="""Automatically disqualify leads if: Price is above $400k or below $30k, listing is for rental/lease,
            property is commercial/business, seller is unresponsive after 3 follow-ups, property is outside target
            markets, listing mentions 'perfect condition' or 'recently renovated', or requires owner financing.
            These typically don't fit our investment criteria.""",
            metadata={
                "rule_name": "Auto Disqualify",
                "criteria": {
                    "price_range": {"max": 30000, "min": 400000},
                    "exclude_keywords": ["rental", "lease", "commercial", "perfect condition", "recently renovated", "owner financing"],
                    "unresponsive_threshold": 3
                },
                "action": "auto_reject"
            },
            tags=["qualification", "disqualification", "rejection"],
            category="lead_qualification",
            priority=75
        ),

        # BUSINESS POLICIES
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.BUSINESS_POLICY,
            title="Cash Offer and Closing Policy",
            content="""We make all-cash offers with no financing contingencies. Our typical offer range is 60-75%
            of ARV (After Repair Value) minus estimated repair costs. We can close in as little as 7 days or on
            the seller's timeline up to 60 days. We pay all closing costs and handle all paperwork. Sellers receive
            cash at closing with no fees or commissions.""",
            metadata={
                "offer_range": {"min_arv_percent": 60, "max_arv_percent": 75},
                "closing_timeline": {"min_days": 7, "max_days": 60},
                "financing": "all-cash",
                "closing_costs": "buyer pays all",
                "seller_fees": "none"
            },
            tags=["policy", "offers", "closing", "cash"],
            category="business_policy",
            priority=85
        ),

        # RESPONSE GUIDELINES
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.RESPONSE_GUIDELINE,
            title="Email Response Tone and Style",
            content="""Always maintain a professional, friendly, and empathetic tone in emails. Address sellers
            by name when available. Acknowledge their situation with understanding. Be direct about our process
            and capabilities. Avoid pressure tactics. Provide clear next steps. Sign emails with your name and
            title. Include contact information in signature. Use proper grammar and spelling. Keep emails concise
            (2-3 paragraphs maximum).""",
            metadata={
                "tone": "professional, friendly, empathetic",
                "style_guidelines": [
                    "Use seller's name",
                    "Acknowledge their situation",
                    "Be direct and honest",
                    "No pressure tactics",
                    "Clear next steps",
                    "Professional signature",
                    "Concise (2-3 paragraphs)"
                ]
            },
            tags=["response", "email", "tone", "guidelines"],
            category="communication",
            priority=80
        ),

        # SCRAPING PATTERNS
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.SCRAPING_PATTERN,
            title="Craigslist Listing Extraction Pattern",
            content="""Extract these fields from Craigslist listings: Title (h1.postingtitle), Price (.price),
            Location (.postinginfo), Description (#postingbody), Images (img.slide), Post Date (.postinginfo time),
            Contact Info (look for phone numbers and email in description). Use regex patterns: Phone: \\d{3}[-.]?\\d{3}[-.]?\\d{4},
            Email: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}""",
            metadata={
                "platform": "craigslist",
                "selectors": {
                    "title": "h1.postingtitle",
                    "price": ".price",
                    "location": ".postinginfo",
                    "description": "#postingbody",
                    "images": "img.slide",
                    "post_date": ".postinginfo time"
                },
                "extraction_rules": {
                    "phone": "\\d{3}[-.]?\\d{3}[-.]?\\d{4}",
                    "email": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
                }
            },
            tags=["scraping", "pattern", "craigslist", "extraction"],
            category="technical",
            priority=70
        ),

        # CUSTOMER PROFILE
        KnowledgeBaseEntryCreate(
            entry_type=EntryTypeEnum.CUSTOMER_PROFILE,
            title="Ideal Seller Profile",
            content="""Our ideal seller is a motivated property owner who needs to sell quickly due to financial
            hardship, relocation, inheritance, divorce, or property condition issues. They own a property that needs
            repairs they can't or won't make. They value speed and certainty over maximum price. They prefer a
            simple, hassle-free transaction. They're willing to accept a cash offer below retail value in exchange
            for quick closing and no contingencies.""",
            metadata={
                "seller_characteristics": [
                    "Financially motivated",
                    "Needs quick sale",
                    "Property needs repairs",
                    "Values certainty over price",
                    "Prefers simple transaction"
                ],
                "common_situations": [
                    "Financial hardship",
                    "Relocation",
                    "Inheritance",
                    "Divorce",
                    "Property condition issues",
                    "Behind on taxes"
                ]
            },
            tags=["profile", "ideal_customer", "seller", "target"],
            category="sales",
            priority=75
        )
    ]

    # Create entries
    created_count = 0
    for entry_data in entries:
        try:
            entry = kb_service.create_entry(entry_data)
            created_count += 1
            print(f"✓ Created: {entry.entry_type} - {entry.title}")
        except Exception as e:
            print(f"✗ Failed to create {entry_data.title}: {e}")

    print("=" * 60)
    print(f"Created {created_count}/{len(entries)} entries successfully")

    # Get stats
    stats = kb_service.get_stats()
    print(f"\nKnowledge Base Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Active entries: {stats['active_entries']}")
    print(f"  Total embeddings: {stats['total_embeddings']}")
    print(f"  OpenAI configured: {stats.get('openai_configured', False)}")

    if not stats.get('openai_configured', False):
        print("\n⚠️  WARNING: OpenAI is not configured!")
        print("   Set OPENAI_API_KEY in .env to enable semantic search")
        print("   Without it, the system will use basic text search")

    db.close()


if __name__ == "__main__":
    try:
        create_example_entries()
    except KeyboardInterrupt:
        print("\n\nAborted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
