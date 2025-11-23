"""
Input validation schemas with comprehensive security checks.
Implements OWASP best practices for input validation and sanitization.
"""

import re
from typing import Optional, List, Any, Dict
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

# Import email validator
try:
    from email_validator import validate_email, EmailNotValidError
except ImportError:
    # Fallback if email-validator is not installed
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return {"email": email}
    EmailNotValidError = ValueError

# Import bleach for HTML sanitization
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    print("Warning: bleach not installed. HTML sanitization disabled.")


# Constants for validation
MAX_STRING_LENGTH = 10000  # Max length for description fields
MAX_TITLE_LENGTH = 500
MAX_EMAIL_LENGTH = 254  # RFC 5321
MAX_PHONE_LENGTH = 20
MAX_URL_LENGTH = 2048
MAX_NAME_LENGTH = 100
MAX_CATEGORY_LENGTH = 50
MIN_PRICE = Decimal('0.00')
MAX_PRICE = Decimal('999999999.99')
MAX_PAGES_SCRAPER = 100
MAX_KEYWORDS = 20
MAX_KEYWORD_LENGTH = 100

# Regex patterns for validation
PHONE_PATTERN = re.compile(r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$')
CRAIGSLIST_URL_PATTERN = re.compile(r'^https?://[a-z]+\.craigslist\.org/.*$')
SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\_\.\,\!\?\@\#\$\%\&\*\(\)\[\]\{\}\:\;\'\"\+\=\/\\]+$')
SQL_INJECTION_PATTERNS = [
    re.compile(r'(union|select|insert|update|delete|drop|create|alter|exec|execute|script|javascript|onclick|onerror)', re.IGNORECASE),
    re.compile(r'(--|#|/\*|\*/|xp_|sp_|0x)', re.IGNORECASE),
    re.compile(r'(<script|</script|<iframe|</iframe|javascript:|onerror=|onclick=)', re.IGNORECASE)
]

# Status enums
LEAD_STATUS_ENUM = ["new", "contacted", "qualified", "converted", "rejected", "archived"]
PRIORITY_ENUM = ["low", "normal", "high", "urgent"]
ACTION_TYPE_ENUM = ["view", "contact", "archive", "rate", "convert"]


def sanitize_html(value: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    if not value:
        return value

    if BLEACH_AVAILABLE:
        # Allow only safe tags and attributes
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'a']
        allowed_attributes = {'a': ['href', 'title']}

        # Clean the HTML
        cleaned = bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        # Also linkify URLs in text
        cleaned = bleach.linkify(cleaned)
        return cleaned
    else:
        # Basic fallback: remove all HTML tags
        return re.sub(r'<[^>]+>', '', value)


def check_sql_injection(value: str) -> str:
    """Check for potential SQL injection patterns."""
    if not value:
        return value

    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Potential SQL injection detected in input")

    return value


def validate_phone_number(value: Optional[str]) -> Optional[str]:
    """Validate and normalize phone number."""
    if not value:
        return value

    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\.\(\)]', '', value)

    # Check if it matches phone pattern
    if not PHONE_PATTERN.match(value):
        raise ValueError(f"Invalid phone number format: {value}")

    # Ensure reasonable length
    if len(cleaned) < 7 or len(cleaned) > 15:
        raise ValueError(f"Phone number must be between 7 and 15 digits")

    return value


def validate_craigslist_url(value: str) -> str:
    """Validate Craigslist URL format."""
    if not value:
        return value

    # Check length
    if len(value) > MAX_URL_LENGTH:
        raise ValueError(f"URL too long (max {MAX_URL_LENGTH} characters)")

    # Check if it's a valid Craigslist URL
    if not CRAIGSLIST_URL_PATTERN.match(value):
        raise ValueError(f"Invalid Craigslist URL format: {value}")

    # Check for potential injection attempts in URL
    if any(char in value for char in ['<', '>', '"', '\'', '{', '}', '|', '\\', '^', '`']):
        raise ValueError("URL contains invalid characters")

    return value


def validate_safe_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Validate string contains only safe characters and within length limit."""
    if not value:
        return value

    # Check length
    if len(value) > max_length:
        raise ValueError(f"String too long (max {max_length} characters)")

    # Check for SQL injection
    check_sql_injection(value)

    # Sanitize HTML
    return sanitize_html(value)


# Type aliases for validated fields
SafeString = Annotated[str, AfterValidator(lambda v: validate_safe_string(v, MAX_STRING_LENGTH))]
SafeTitle = Annotated[str, AfterValidator(lambda v: validate_safe_string(v, MAX_TITLE_LENGTH))]
SafeName = Annotated[str, AfterValidator(lambda v: validate_safe_string(v, MAX_NAME_LENGTH))]
SafeCategory = Annotated[str, AfterValidator(lambda v: validate_safe_string(v, MAX_CATEGORY_LENGTH))]
ValidEmail = Annotated[str, AfterValidator(lambda v: validate_email(v)["email"] if v else v)]
ValidPhone = Annotated[str, AfterValidator(validate_phone_number)]
ValidCraigslistUrl = Annotated[str, AfterValidator(validate_craigslist_url)]


class SecureLeadCreate(BaseModel):
    """Secure lead creation schema with comprehensive validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    craigslist_id: str = Field(..., min_length=1, max_length=100)
    title: SafeTitle
    description: Optional[SafeString] = None
    price: Optional[Decimal] = Field(None, ge=MIN_PRICE, le=MAX_PRICE)
    url: ValidCraigslistUrl
    email: Optional[ValidEmail] = None
    phone: Optional[ValidPhone] = None
    contact_name: Optional[SafeName] = None
    location_id: int = Field(..., ge=1)
    category: Optional[SafeCategory] = None
    subcategory: Optional[SafeCategory] = None
    posted_at: Optional[datetime] = None

    @field_validator('craigslist_id')
    @classmethod
    def validate_craigslist_id(cls, v: str) -> str:
        # Ensure it's alphanumeric with possible hyphens/underscores
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('Craigslist ID must be alphanumeric')
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v


class SecureLeadUpdate(BaseModel):
    """Secure lead update schema with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[SafeTitle] = None
    description: Optional[SafeString] = None
    price: Optional[Decimal] = Field(None, ge=MIN_PRICE, le=MAX_PRICE)
    email: Optional[ValidEmail] = None
    phone: Optional[ValidPhone] = None
    contact_name: Optional[SafeName] = None
    category: Optional[SafeCategory] = None
    subcategory: Optional[SafeCategory] = None
    is_processed: Optional[bool] = None
    is_contacted: Optional[bool] = None
    status: Optional[str] = Field(None, pattern='^(new|contacted|qualified|converted|rejected|archived)$')


class SecureScrapeJobCreate(BaseModel):
    """Secure scrape job creation with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    location_ids: List[int] = Field(..., min_items=1, max_items=50)
    locations: Optional[List[Dict[str, Any]]] = Field(None, max_items=50)
    categories: Optional[List[SafeCategory]] = Field(None, max_items=20)
    keywords: Optional[List[str]] = Field(None, max_items=MAX_KEYWORDS)
    max_pages: int = Field(5, ge=1, le=MAX_PAGES_SCRAPER)
    priority: str = Field("normal", pattern='^(low|normal|high|urgent)$')
    enable_email_extraction: bool = False
    captcha_api_key: Optional[str] = Field(None, max_length=100)

    @field_validator('location_ids')
    @classmethod
    def validate_location_ids(cls, v: List[int]) -> List[int]:
        # Ensure all IDs are positive
        for loc_id in v:
            if loc_id <= 0:
                raise ValueError('Location ID must be positive')
        # Remove duplicates
        return list(set(v))

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v

        validated = []
        for keyword in v:
            # Check length
            if len(keyword) > MAX_KEYWORD_LENGTH:
                raise ValueError(f'Keyword too long (max {MAX_KEYWORD_LENGTH} chars)')
            # Check for injection
            check_sql_injection(keyword)
            # Sanitize
            validated.append(sanitize_html(keyword))

        return validated

    @field_validator('captcha_api_key')
    @classmethod
    def validate_captcha_key(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('Invalid CAPTCHA API key format')
        return v


class SecureMLScoreRequest(BaseModel):
    """Secure ML scoring request with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: int = Field(..., ge=1)
    title: SafeTitle
    description: Optional[SafeString] = ""
    category: Optional[SafeCategory] = None
    subcategory: Optional[SafeCategory] = None
    price: Optional[float] = Field(None, ge=0, le=float(MAX_PRICE))
    email: Optional[ValidEmail] = None
    phone: Optional[ValidPhone] = None
    contact_name: Optional[SafeName] = None
    location_name: Optional[SafeName] = None
    posted_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class SecureFeedbackRequest(BaseModel):
    """Secure feedback request with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: int = Field(..., ge=1)
    action_type: str = Field(..., pattern="^(view|contact|archive|rate|convert)$")
    user_rating: Optional[float] = Field(None, ge=0, le=100)
    interaction_duration: Optional[float] = Field(None, ge=0, le=86400)  # Max 24 hours
    contact_successful: Optional[bool] = None
    contact_response_time: Optional[float] = Field(None, ge=0, le=8760)  # Max 1 year in hours
    conversion_value: Optional[float] = Field(None, ge=0, le=float(MAX_PRICE))
    session_id: Optional[str] = Field(None, max_length=100)
    user_agent: Optional[str] = Field(None, max_length=500)
    ip_address: Optional[str] = Field(None, max_length=45)  # IPv6 max length

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError('Invalid session ID format')
        return v

    @field_validator('ip_address')
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v

        # Basic IP validation (IPv4 or IPv6)
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'

        if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
            # Could be IPv6 compressed format, just ensure no injection
            if any(char in v for char in ['<', '>', '"', '\'', ';', '&', '|']):
                raise ValueError('Invalid IP address format')

        return v


class SecureResponseGeneration(BaseModel):
    """Secure response generation request with validation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    lead_id: int = Field(..., ge=1)
    template_id: Optional[int] = Field(None, ge=1)
    custom_message: Optional[SafeString] = None
    tone: str = Field("professional", pattern='^(professional|casual|friendly|formal)$')
    include_pricing: bool = False
    include_availability: bool = False

    @field_validator('custom_message')
    @classmethod
    def validate_custom_message(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Additional check for prompt injection attempts
            injection_patterns = [
                'ignore previous', 'disregard', 'forget everything',
                'system:', 'admin:', 'root:', 'execute:', 'eval:'
            ]
            lower_v = v.lower()
            for pattern in injection_patterns:
                if pattern in lower_v:
                    raise ValueError('Potential prompt injection detected')
        return v


# Query parameter validators
def validate_pagination(skip: int = 0, limit: int = 100) -> tuple:
    """Validate pagination parameters."""
    if skip < 0:
        raise ValueError("Skip value must be non-negative")
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if limit > 1000:
        raise ValueError("Limit cannot exceed 1000")
    return skip, limit


def validate_status_filter(status: Optional[str]) -> Optional[str]:
    """Validate status filter parameter."""
    if status and status not in LEAD_STATUS_ENUM:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(LEAD_STATUS_ENUM)}")
    return status


def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> tuple:
    """Validate date range parameters."""
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
        # Check for reasonable date range (e.g., max 1 year)
        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 1 year")
    return start_date, end_date


# Export all validators
__all__ = [
    'SecureLeadCreate',
    'SecureLeadUpdate',
    'SecureScrapeJobCreate',
    'SecureMLScoreRequest',
    'SecureFeedbackRequest',
    'SecureResponseGeneration',
    'validate_pagination',
    'validate_status_filter',
    'validate_date_range',
    'sanitize_html',
    'check_sql_injection',
    'validate_phone_number',
    'validate_craigslist_url',
    'validate_safe_string'
]