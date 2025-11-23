"""
Unified Email Finder Service with multiple strategies and fallback logic.

Priority:
1. Hunter.io (if quota available)
2. Website scraping (always available)
3. RocketReach (optional, if configured)

Quota Management:
- Track usage to prevent overage charges
- Auto-switch to fallback when quota exceeded
- Alert when approaching limits
"""

import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.hunter_io import (
    HunterIOClient,
    QuotaExceededError,
    RateLimitError,
    HunterIOError
)
from app.models.email_finder import (
    EmailFinderUsage,
    FoundEmail,
    EmailFinderQuota,
    EmailSource,
    ServiceName
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailFinderService:
    """
    Unified service for finding emails using multiple strategies.

    Usage:
        service = EmailFinderService(db_session)

        # Find all emails for a domain
        emails = await service.find_emails_by_domain("stripe.com")

        # Find specific person's email
        email = await service.find_person_email("Patrick Collison", "stripe.com")

        # Check quota status
        quota = await service.get_quota_status(ServiceName.HUNTER_IO)
    """

    # Common email patterns for scraping
    EMAIL_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    ]

    # Common email prefixes (generic)
    GENERIC_PREFIXES = [
        'info', 'contact', 'hello', 'support', 'sales', 'admin',
        'help', 'service', 'office', 'team', 'mail', 'inquiries',
        'general', 'feedback', 'business', 'welcome'
    ]

    # Pages to scrape for emails
    SCRAPE_PAGES = [
        '',  # Homepage
        '/contact',
        '/contact-us',
        '/about',
        '/about-us',
        '/team',
        '/privacy',
        '/privacy-policy',
        '/legal',
        '/footer'
    ]

    def __init__(
        self,
        db: AsyncSession,
        hunter_client: Optional[HunterIOClient] = None,
        enable_scraping: bool = True
    ):
        """
        Initialize email finder service.

        Args:
            db: Database session
            hunter_client: Hunter.io client (optional, will create if API key available)
            enable_scraping: Enable fallback scraping
        """
        self.db = db
        self.enable_scraping = enable_scraping

        # Initialize Hunter.io client if API key is available
        self.hunter_client = hunter_client
        if not self.hunter_client and settings.HUNTER_IO_API_KEY:
            self.hunter_client = HunterIOClient(settings.HUNTER_IO_API_KEY)

        # HTTP client for scraping
        self._http_client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def close(self):
        """Close HTTP clients."""
        if self.hunter_client:
            await self.hunter_client.close()
        await self._http_client.aclose()

    async def find_emails_by_domain(
        self,
        domain: str,
        lead_id: Optional[int] = None,
        limit: int = 10
    ) -> List[FoundEmail]:
        """
        Find all emails for a domain using available strategies.

        Args:
            domain: Domain name (e.g., "stripe.com")
            lead_id: Optional lead ID to associate emails with
            limit: Maximum number of emails to return

        Returns:
            List of FoundEmail objects sorted by confidence score
        """
        logger.info(f"Finding emails for domain: {domain}")

        all_emails = []

        # Strategy 1: Check database cache first
        cached_emails = await self._get_cached_emails(domain, limit)
        if cached_emails:
            logger.info(f"Found {len(cached_emails)} cached emails for {domain}")
            all_emails.extend(cached_emails)

        # Strategy 2: Try Hunter.io
        if self.hunter_client and settings.HUNTER_IO_ENABLED:
            try:
                hunter_emails = await self._find_with_hunter(domain, lead_id, limit)
                all_emails.extend(hunter_emails)
                logger.info(f"Found {len(hunter_emails)} emails via Hunter.io")
            except QuotaExceededError:
                logger.warning("Hunter.io quota exceeded, using fallback methods")
            except Exception as e:
                logger.error(f"Hunter.io error: {str(e)}")

        # Strategy 3: Fallback to website scraping
        if self.enable_scraping and len(all_emails) < limit:
            try:
                scraped_emails = await self._scrape_website_emails(domain, lead_id)
                all_emails.extend(scraped_emails)
                logger.info(f"Found {len(scraped_emails)} emails via scraping")
            except Exception as e:
                logger.error(f"Scraping error: {str(e)}")

        # Remove duplicates and sort by confidence
        unique_emails = self._deduplicate_emails(all_emails)
        sorted_emails = sorted(
            unique_emails,
            key=lambda e: (e.confidence_score or 0, not e.is_generic),
            reverse=True
        )

        return sorted_emails[:limit]

    async def find_person_email(
        self,
        name: str,
        domain: str,
        lead_id: Optional[int] = None
    ) -> Optional[FoundEmail]:
        """
        Find a specific person's email address.

        Args:
            name: Person's full name
            domain: Company domain
            lead_id: Optional lead ID

        Returns:
            FoundEmail object or None if not found
        """
        logger.info(f"Finding email for {name} at {domain}")

        # Parse name
        name_parts = name.strip().split()
        if len(name_parts) < 2:
            logger.warning(f"Invalid name format: {name}")
            return None

        first_name = name_parts[0]
        last_name = name_parts[-1]

        # Check cache first
        cached = await self._get_cached_person_email(first_name, last_name, domain)
        if cached:
            logger.info(f"Found cached email for {name}")
            return cached

        # Try Hunter.io
        if self.hunter_client and settings.HUNTER_IO_ENABLED:
            try:
                email = await self._find_person_with_hunter(
                    domain, first_name, last_name, name, lead_id
                )
                if email:
                    return email
            except QuotaExceededError:
                logger.warning("Hunter.io quota exceeded")
            except Exception as e:
                logger.error(f"Hunter.io person search error: {str(e)}")

        # Fallback to common email patterns
        return await self._guess_email_pattern(domain, first_name, last_name, lead_id)

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify if an email address is valid.

        Args:
            email: Email address to verify

        Returns:
            Verification result dictionary
        """
        logger.info(f"Verifying email: {email}")

        # Basic regex validation
        if not re.match(self.EMAIL_PATTERNS[0], email):
            return {
                "email": email,
                "valid": False,
                "reason": "Invalid email format"
            }

        # Try Hunter.io verification
        if self.hunter_client and settings.HUNTER_IO_ENABLED:
            try:
                verification = await self.hunter_client.verify_email(email)
                await self._track_usage(ServiceName.HUNTER_IO, "verify", email.split('@')[1])

                return {
                    "email": email,
                    "valid": verification.result in ["deliverable", "valid"],
                    "score": verification.score,
                    "result": verification.result,
                    "details": verification.to_dict()
                }
            except Exception as e:
                logger.error(f"Email verification error: {str(e)}")

        # Basic validation without API
        return {
            "email": email,
            "valid": True,
            "score": 50,
            "result": "unknown",
            "reason": "Basic format validation only"
        }

    async def _find_with_hunter(
        self,
        domain: str,
        lead_id: Optional[int],
        limit: int
    ) -> List[FoundEmail]:
        """Find emails using Hunter.io."""
        start_time = datetime.now()

        try:
            # Check quota first
            quota = await self._get_current_quota(ServiceName.HUNTER_IO)
            if quota and quota.is_exceeded:
                raise QuotaExceededError("Monthly quota exceeded")

            # Make API request
            result = await self.hunter_client.domain_search(domain, limit=limit)

            # Track usage
            await self._track_usage(
                service=ServiceName.HUNTER_IO,
                endpoint="domain-search",
                domain=domain,
                results_count=len(result["emails"]),
                response_time=(datetime.now() - start_time).total_seconds() * 1000
            )

            # Save emails to database
            found_emails = []
            for email_result in result["emails"]:
                found_email = await self._save_found_email(
                    email=email_result.value,
                    domain=domain,
                    source=EmailSource.HUNTER_IO,
                    lead_id=lead_id,
                    confidence=email_result.confidence,
                    first_name=email_result.first_name,
                    last_name=email_result.last_name,
                    position=email_result.position,
                    department=email_result.department,
                    seniority=email_result.seniority,
                    phone_number=email_result.phone_number,
                    linkedin_url=email_result.linkedin,
                    twitter_handle=email_result.twitter,
                    is_generic=email_result.type == "generic",
                    sources=email_result.sources,
                    verification=email_result.verification
                )
                found_emails.append(found_email)

            return found_emails

        except QuotaExceededError:
            raise
        except Exception as e:
            await self._track_usage(
                service=ServiceName.HUNTER_IO,
                endpoint="domain-search",
                domain=domain,
                success=False,
                error_message=str(e)
            )
            raise

    async def _find_person_with_hunter(
        self,
        domain: str,
        first_name: str,
        last_name: str,
        full_name: str,
        lead_id: Optional[int]
    ) -> Optional[FoundEmail]:
        """Find person's email using Hunter.io."""
        try:
            # Check quota
            quota = await self._get_current_quota(ServiceName.HUNTER_IO)
            if quota and quota.is_exceeded:
                raise QuotaExceededError("Monthly quota exceeded")

            # Make API request
            email_result = await self.hunter_client.email_finder(
                domain, first_name, last_name, full_name
            )

            if not email_result:
                return None

            # Track usage
            await self._track_usage(
                service=ServiceName.HUNTER_IO,
                endpoint="email-finder",
                domain=domain,
                results_count=1
            )

            # Save to database
            found_email = await self._save_found_email(
                email=email_result.value,
                domain=domain,
                source=EmailSource.HUNTER_IO,
                lead_id=lead_id,
                confidence=email_result.confidence,
                first_name=email_result.first_name,
                last_name=email_result.last_name,
                position=email_result.position,
                department=email_result.department,
                seniority=email_result.seniority,
                is_generic=email_result.type == "generic"
            )

            return found_email

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"Hunter.io person search failed: {str(e)}")
            return None

    async def _scrape_website_emails(
        self,
        domain: str,
        lead_id: Optional[int]
    ) -> List[FoundEmail]:
        """Scrape emails from website pages."""
        logger.info(f"Scraping emails from {domain}")

        all_emails = set()
        base_url = f"https://{domain}"

        for page_path in self.SCRAPE_PAGES:
            url = f"{base_url}{page_path}"
            try:
                response = await self._http_client.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract text content
                    text = soup.get_text()

                    # Find all emails in text
                    for pattern in self.EMAIL_PATTERNS:
                        matches = re.findall(pattern, text)
                        for email in matches:
                            email = email.lower().strip()
                            # Only include emails from this domain
                            if domain.lower() in email:
                                all_emails.add(email)

            except Exception as e:
                logger.debug(f"Failed to scrape {url}: {str(e)}")
                continue

        # Save found emails
        found_emails = []
        for email in all_emails:
            is_generic = any(prefix in email.split('@')[0] for prefix in self.GENERIC_PREFIXES)

            found_email = await self._save_found_email(
                email=email,
                domain=domain,
                source=EmailSource.SCRAPED,
                lead_id=lead_id,
                confidence=30 if not is_generic else 20,  # Lower confidence for scraped
                is_generic=is_generic
            )
            found_emails.append(found_email)

        logger.info(f"Scraped {len(found_emails)} emails from {domain}")
        return found_emails

    async def _guess_email_pattern(
        self,
        domain: str,
        first_name: str,
        last_name: str,
        lead_id: Optional[int]
    ) -> Optional[FoundEmail]:
        """
        Guess email using common patterns.

        Common patterns:
        - first.last@domain.com
        - first@domain.com
        - firstlast@domain.com
        - flast@domain.com
        """
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}@{domain}",
            f"{first_name.lower()}@{domain}",
            f"{first_name.lower()}{last_name.lower()}@{domain}",
            f"{first_name[0].lower()}{last_name.lower()}@{domain}",
        ]

        # Return the first pattern (most common)
        # Mark with low confidence since it's a guess
        email = patterns[0]

        found_email = await self._save_found_email(
            email=email,
            domain=domain,
            source=EmailSource.SCRAPED,
            lead_id=lead_id,
            first_name=first_name,
            last_name=last_name,
            confidence=10,  # Very low confidence for guesses
            is_personal=True
        )

        logger.info(f"Guessed email pattern: {email} (low confidence)")
        return found_email

    async def _save_found_email(
        self,
        email: str,
        domain: str,
        source: EmailSource,
        lead_id: Optional[int] = None,
        **kwargs
    ) -> FoundEmail:
        """Save found email to database."""
        # Check if email already exists
        from sqlalchemy import select
        stmt = select(FoundEmail).where(FoundEmail.email == email)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            for key, value in kwargs.items():
                if value is not None and hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = func.now()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Create new record
        found_email = FoundEmail(
            email=email,
            domain=domain,
            source=source,
            lead_id=lead_id,
            **kwargs
        )

        self.db.add(found_email)
        await self.db.commit()
        await self.db.refresh(found_email)

        return found_email

    async def _get_cached_emails(
        self,
        domain: str,
        limit: int
    ) -> List[FoundEmail]:
        """Get cached emails from database."""
        from sqlalchemy import select
        stmt = (
            select(FoundEmail)
            .where(FoundEmail.domain == domain)
            .order_by(FoundEmail.confidence_score.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_cached_person_email(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Optional[FoundEmail]:
        """Get cached person email from database."""
        from sqlalchemy import select, and_
        stmt = select(FoundEmail).where(
            and_(
                FoundEmail.first_name == first_name,
                FoundEmail.last_name == last_name,
                FoundEmail.domain == domain
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _track_usage(
        self,
        service: ServiceName,
        endpoint: str,
        domain: str,
        results_count: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        response_time: Optional[float] = None
    ):
        """Track API usage for quota management."""
        usage = EmailFinderUsage(
            service=service,
            endpoint=endpoint,
            domain=domain,
            requests_used=1,
            success=success,
            error_message=error_message,
            results_count=results_count,
            response_time_ms=int(response_time) if response_time else None
        )

        self.db.add(usage)

        # Update quota
        await self._update_quota(service, 1)

        await self.db.commit()

    async def _update_quota(self, service: ServiceName, requests_used: int):
        """Update quota tracking."""
        from sqlalchemy import select
        now = datetime.now()

        stmt = select(EmailFinderQuota).where(
            EmailFinderQuota.service == service
        )
        result = await self.db.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota:
            quota.requests_used += requests_used
            quota.requests_remaining = max(0, quota.quota_limit - quota.requests_used)
            quota.updated_at = func.now()
        else:
            # Create initial quota record
            quota = EmailFinderQuota(
                service=service,
                month=now.month,
                year=now.year,
                quota_limit=settings.HUNTER_MONTHLY_QUOTA,
                requests_used=requests_used,
                requests_remaining=settings.HUNTER_MONTHLY_QUOTA - requests_used,
                alert_threshold=int(settings.HUNTER_MONTHLY_QUOTA * 0.8)
            )
            self.db.add(quota)

        await self.db.commit()

    async def _get_current_quota(self, service: ServiceName) -> Optional[EmailFinderQuota]:
        """Get current quota status."""
        from sqlalchemy import select
        stmt = select(EmailFinderQuota).where(EmailFinderQuota.service == service)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quota_status(self, service: ServiceName) -> Dict[str, Any]:
        """
        Get quota status for a service.

        Returns:
            Dictionary with quota information
        """
        quota = await self._get_current_quota(service)

        if not quota:
            return {
                "service": service.value,
                "configured": False,
                "message": "Service not configured"
            }

        return quota.to_dict()

    def _deduplicate_emails(self, emails: List[FoundEmail]) -> List[FoundEmail]:
        """Remove duplicate emails, keeping the one with highest confidence."""
        seen = {}
        for email in emails:
            if email.email not in seen:
                seen[email.email] = email
            else:
                # Keep the one with higher confidence
                if (email.confidence_score or 0) > (seen[email.email].confidence_score or 0):
                    seen[email.email] = email

        return list(seen.values())
