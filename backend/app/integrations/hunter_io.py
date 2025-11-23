"""
Hunter.io API Integration for Email Finding.

Official API Docs: https://hunter.io/api-documentation/v2
Free Tier: 100 searches/month
Paid Plans: $49/mo (1K), $99/mo (5K), $199/mo (20K)
Rate Limit: 50 requests/minute
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class EmailType(str, Enum):
    """Email type classifications from Hunter.io."""
    PERSONAL = "personal"
    GENERIC = "generic"


class EmailStatus(str, Enum):
    """Email verification statuses."""
    VALID = "valid"
    INVALID = "invalid"
    ACCEPT_ALL = "accept_all"
    WEBMAIL = "webmail"
    DISPOSABLE = "disposable"
    UNKNOWN = "unknown"


class EmailResult:
    """Represents an email found by Hunter.io."""

    def __init__(
        self,
        value: str,
        type: str,
        confidence: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        position: Optional[str] = None,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
        phone_number: Optional[str] = None,
        twitter: Optional[str] = None,
        linkedin: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        verification: Optional[Dict] = None
    ):
        self.value = value
        self.type = type
        self.confidence = confidence
        self.first_name = first_name
        self.last_name = last_name
        self.position = position
        self.department = department
        self.seniority = seniority
        self.phone_number = phone_number
        self.twitter = twitter
        self.linkedin = linkedin
        self.sources = sources or []
        self.verification = verification or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.value,
            "type": self.type,
            "confidence": self.confidence,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "position": self.position,
            "department": self.department,
            "seniority": self.seniority,
            "phone_number": self.phone_number,
            "twitter": self.twitter,
            "linkedin": self.linkedin,
            "sources_count": len(self.sources),
            "verification": self.verification
        }


class EmailVerification:
    """Email verification result."""

    def __init__(
        self,
        result: str,
        score: int,
        email: str,
        regexp: bool,
        gibberish: bool,
        disposable: bool,
        webmail: bool,
        mx_records: bool,
        smtp_server: bool,
        smtp_check: bool,
        accept_all: bool,
        block: bool
    ):
        self.result = result
        self.score = score
        self.email = email
        self.regexp = regexp
        self.gibberish = gibberish
        self.disposable = disposable
        self.webmail = webmail
        self.mx_records = mx_records
        self.smtp_server = smtp_server
        self.smtp_check = smtp_check
        self.accept_all = accept_all
        self.block = block

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result,
            "score": self.score,
            "email": self.email,
            "regexp": self.regexp,
            "gibberish": self.gibberish,
            "disposable": self.disposable,
            "webmail": self.webmail,
            "mx_records": self.mx_records,
            "smtp_server": self.smtp_server,
            "smtp_check": self.smtp_check,
            "accept_all": self.accept_all,
            "block": self.block
        }


class HunterIOError(Exception):
    """Base exception for Hunter.io errors."""
    pass


class QuotaExceededError(HunterIOError):
    """Raised when API quota is exceeded."""
    pass


class RateLimitError(HunterIOError):
    """Raised when rate limit is hit."""
    pass


class HunterIOClient:
    """
    Hunter.io API client for email finding and verification.

    Usage:
        client = HunterIOClient(api_key="your_key")

        # Find all emails for a domain
        results = await client.domain_search("stripe.com")

        # Find specific person's email
        email = await client.email_finder("stripe.com", "Patrick", "Collison")

        # Verify an email
        verification = await client.verify_email("patrick@stripe.com")
    """

    BASE_URL = "https://api.hunter.io/v2"

    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Hunter.io client.

        Args:
            api_key: Hunter.io API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        if not api_key:
            raise ValueError("Hunter.io API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(timeout=timeout)

        # Rate limiting: 50 requests/minute
        self._request_times: List[float] = []
        self._rate_limit_per_minute = 50

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _check_rate_limit(self):
        """Check and enforce rate limits."""
        now = datetime.now().timestamp()
        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self._rate_limit_per_minute:
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self._request_times = []

        self._request_times.append(now)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with rate limiting and error handling.

        Args:
            endpoint: API endpoint (e.g., "/domain-search")
            params: Query parameters

        Returns:
            API response data

        Raises:
            QuotaExceededError: When API quota is exceeded
            RateLimitError: When rate limit is hit
            HunterIOError: For other API errors
        """
        await self._check_rate_limit()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        try:
            response = await self._client.get(url, params=params)
            data = response.json()

            # Check for errors
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Try again later.")

            if response.status_code == 401:
                raise HunterIOError("Invalid API key")

            if response.status_code == 400:
                errors = data.get("errors", [])
                if any("quota" in str(e).lower() for e in errors):
                    raise QuotaExceededError("API quota exceeded")
                raise HunterIOError(f"Bad request: {errors}")

            if response.status_code != 200:
                raise HunterIOError(f"API error: {data}")

            return data.get("data", {})

        except httpx.TimeoutException:
            raise HunterIOError(f"Request timeout after {self.timeout} seconds")
        except httpx.RequestError as e:
            raise HunterIOError(f"Request failed: {str(e)}")

    async def domain_search(
        self,
        domain: str,
        limit: int = 10,
        offset: int = 0,
        type: Optional[EmailType] = None,
        seniority: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find all email addresses for a given domain.

        Args:
            domain: Domain name (e.g., "stripe.com")
            limit: Max results to return (1-100, default 10)
            offset: Pagination offset
            type: Filter by email type (personal/generic)
            seniority: Filter by seniority (junior, senior, executive)
            department: Filter by department (executive, IT, finance, etc.)

        Returns:
            Dictionary with:
                - domain: Domain name
                - disposable: Whether domain is disposable
                - webmail: Whether domain is webmail
                - pattern: Email pattern (e.g., "{first}.{last}")
                - organization: Company name
                - emails: List of EmailResult objects
                - meta: Metadata (results count, limit, offset)

        Example:
            results = await client.domain_search("stripe.com", limit=20)
            for email in results["emails"]:
                print(f"{email.value} - {email.confidence}% confidence")
        """
        params = {
            "domain": domain,
            "limit": min(max(1, limit), 100),
            "offset": offset
        }

        if type:
            params["type"] = type.value
        if seniority:
            params["seniority"] = seniority
        if department:
            params["department"] = department

        logger.info(f"Searching emails for domain: {domain}")

        data = await self._make_request("/domain-search", params)

        # Parse email results
        emails = []
        for email_data in data.get("emails", []):
            email = EmailResult(
                value=email_data.get("value"),
                type=email_data.get("type"),
                confidence=email_data.get("confidence", 0),
                first_name=email_data.get("first_name"),
                last_name=email_data.get("last_name"),
                position=email_data.get("position"),
                department=email_data.get("department"),
                seniority=email_data.get("seniority"),
                phone_number=email_data.get("phone_number"),
                twitter=email_data.get("twitter"),
                linkedin=email_data.get("linkedin"),
                sources=email_data.get("sources", []),
                verification=email_data.get("verification", {})
            )
            emails.append(email)

        result = {
            "domain": data.get("domain"),
            "disposable": data.get("disposable"),
            "webmail": data.get("webmail"),
            "pattern": data.get("pattern"),
            "organization": data.get("organization"),
            "emails": emails,
            "meta": data.get("meta", {})
        }

        logger.info(f"Found {len(emails)} emails for {domain}")
        return result

    async def email_finder(
        self,
        domain: str,
        first_name: str,
        last_name: str,
        full_name: Optional[str] = None
    ) -> Optional[EmailResult]:
        """
        Find a specific person's email address.

        Args:
            domain: Domain name (e.g., "stripe.com")
            first_name: Person's first name
            last_name: Person's last name
            full_name: Full name (optional, for better accuracy)

        Returns:
            EmailResult object or None if not found

        Example:
            email = await client.email_finder("stripe.com", "Patrick", "Collison")
            if email:
                print(f"Found: {email.value} ({email.confidence}% confidence)")
        """
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name
        }

        if full_name:
            params["full_name"] = full_name

        logger.info(f"Finding email for {first_name} {last_name} at {domain}")

        try:
            data = await self._make_request("/email-finder", params)

            if not data or not data.get("email"):
                logger.info(f"No email found for {first_name} {last_name} at {domain}")
                return None

            email = EmailResult(
                value=data.get("email"),
                type=data.get("type"),
                confidence=data.get("score", 0),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                position=data.get("position"),
                department=data.get("department"),
                seniority=data.get("seniority"),
                phone_number=data.get("phone_number"),
                twitter=data.get("twitter"),
                linkedin=data.get("linkedin"),
                sources=data.get("sources", []),
                verification=data.get("verification", {})
            )

            logger.info(f"Found email: {email.value} ({email.confidence}% confidence)")
            return email

        except HunterIOError as e:
            logger.error(f"Error finding email: {str(e)}")
            return None

    async def verify_email(self, email: str) -> EmailVerification:
        """
        Verify if an email address is valid and deliverable.

        Args:
            email: Email address to verify

        Returns:
            EmailVerification object with detailed validation results

        Example:
            verification = await client.verify_email("patrick@stripe.com")
            if verification.result == "deliverable":
                print(f"Email is valid (score: {verification.score}/100)")
        """
        params = {"email": email}

        logger.info(f"Verifying email: {email}")

        data = await self._make_request("/email-verifier", params)

        verification = EmailVerification(
            result=data.get("result"),
            score=data.get("score", 0),
            email=data.get("email"),
            regexp=data.get("regexp", False),
            gibberish=data.get("gibberish", False),
            disposable=data.get("disposable", False),
            webmail=data.get("webmail", False),
            mx_records=data.get("mx_records", False),
            smtp_server=data.get("smtp_server", False),
            smtp_check=data.get("smtp_check", False),
            accept_all=data.get("accept_all", False),
            block=data.get("block", False)
        )

        logger.info(f"Email verification result: {verification.result} (score: {verification.score}/100)")
        return verification

    async def email_count(self, domain: str) -> int:
        """
        Get the total number of emails found for a domain.

        Args:
            domain: Domain name

        Returns:
            Total number of emails found
        """
        data = await self.domain_search(domain, limit=1)
        return data.get("meta", {}).get("results", 0)

    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including quota usage.

        Returns:
            Dictionary with:
                - email: Account email
                - first_name: Account first name
                - last_name: Account last name
                - plan_name: Current plan
                - plan_level: Plan tier (0=free, 1-4=paid)
                - reset_date: When quota resets
                - team_id: Team ID
                - calls: API calls this month
                - requests_available: Remaining requests

        Example:
            info = await client.get_account_info()
            print(f"Requests used: {info['calls']}/{info['calls'] + info['requests_available']}")
        """
        data = await self._make_request("/account")

        logger.info(
            f"Account info: {data.get('calls', 0)} requests used, "
            f"{data.get('requests_available', 0)} remaining"
        )

        return data
