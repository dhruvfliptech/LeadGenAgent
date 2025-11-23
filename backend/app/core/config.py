"""
Application configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    # DEBUG should be False by default for security - only enable explicitly
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/craigslist_leads")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

    # Redis - MUST be set via environment variable
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Craigslist Lead Generation"
    VERSION: str = "1.0.0"

    # CORS - MUST be configured for production (no localhost default)
    # Store as string, parse to list in property
    ALLOWED_HOSTS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5176"

    # Security - SECRET_KEY MUST be set via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Scraping Settings
    SCRAPER_DELAY_MIN: float = 1.0
    SCRAPER_DELAY_MAX: float = 3.0
    SCRAPER_CONCURRENT_LIMIT: int = 5
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # CAPTCHA Settings
    TWOCAPTCHA_API_KEY: str = ""
    CAPTCHA_TIMEOUT: int = 120
    CAPTCHA_MAX_RETRIES: int = 3
    ENABLE_EMAIL_EXTRACTION: bool = False
    EMAIL_EXTRACTION_MAX_CONCURRENT: int = 2
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # AI Integration Settings - OpenRouter (Unified API for Multiple Models)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "openrouter")  # openai, anthropic, openrouter

    # OpenRouter Configuration (provides access to GPT-4, Claude, Qwen, Grok, etc.)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    # AI Model Selection (via OpenRouter)
    AI_MODEL_DEFAULT: str = os.getenv("AI_MODEL_DEFAULT", "openai/gpt-4-turbo-preview")
    AI_MODEL_EMBEDDINGS: str = os.getenv("AI_MODEL_EMBEDDINGS", "openai/text-embedding-ada-002")
    AI_MODEL_CLAUDE: str = os.getenv("AI_MODEL_CLAUDE", "anthropic/claude-3.5-sonnet")
    AI_MODEL_QWEN: str = os.getenv("AI_MODEL_QWEN", "qwen/qwen-2.5-72b-instruct")
    AI_MODEL_GROK: str = os.getenv("AI_MODEL_GROK", "x-ai/grok-beta")

    # Legacy API Keys (for backward compatibility or direct API usage)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # AI Request Settings
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2000"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_TIMEOUT_SECONDS: int = int(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    
    # Phase 3: Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    # Postmark Settings (for transactional email)
    POSTMARK_SERVER_TOKEN: str = os.getenv("POSTMARK_SERVER_TOKEN", "")

    # Phase 3: Notification Settings
    WEBSOCKET_PING_INTERVAL: int = 30
    NOTIFICATION_MAX_RETRIES: int = 3
    NOTIFICATION_RETRY_DELAY: int = 300  # 5 minutes
    NOTIFICATION_BATCH_SIZE: int = 100
    
    # Phase 3: Webhook Settings
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_DELAY: int = 60
    
    # Phase 3: SMS Settings (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    
    # Phase 3: Slack Integration
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    
    # Phase 3: Discord Integration
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_WEBHOOK_URL: str = ""
    
    # Phase 3: Scheduler Settings
    SCHEDULER_CHECK_INTERVAL: int = 60  # seconds
    SCHEDULER_MAX_CONCURRENT_JOBS: int = 10
    SCHEDULER_DEFAULT_TIMEOUT: int = 3600  # 1 hour
    SCHEDULER_CLEANUP_DAYS: int = 30
    
    # Phase 3: Auto-Responder Settings
    AUTO_RESPONDER_ENABLED: bool = False
    AUTO_RESPONDER_MAX_DELAY_HOURS: int = 24
    AUTO_RESPONDER_MIN_DELAY_MINUTES: int = 5
    AUTO_RESPONDER_DEFAULT_TEMPLATE: str = "default"
    
    # Phase 3: Rule Engine Settings
    RULE_ENGINE_ENABLED: bool = True
    RULE_ENGINE_MAX_RULES_PER_SET: int = 50
    RULE_ENGINE_BATCH_SIZE: int = 100
    RULE_ENGINE_TIMEOUT_SECONDS: int = 30
    
    # Phase 3: Export Settings
    EXPORT_DIRECTORY: str = os.getenv("EXPORT_DIRECTORY", "backend/exports")
    EXPORT_MAX_RECORDS: int = int(os.getenv("EXPORT_MAX_RECORDS", "100000"))
    EXPORT_CLEANUP_DAYS: int = int(os.getenv("EXPORT_CLEANUP_DAYS", "30"))
    EXPORT_COMPRESSION_LEVEL: int = int(os.getenv("EXPORT_COMPRESSION_LEVEL", "6"))
    
    # Phase 3: Analytics Settings
    ANALYTICS_RETENTION_DAYS: int = 365
    ANALYTICS_BATCH_SIZE: int = 1000
    ANALYTICS_CACHE_TTL: int = 3600  # 1 hour
    
    # Phase 3: Performance Settings
    LEAD_PROCESSING_BATCH_SIZE: int = 50
    BULK_OPERATION_BATCH_SIZE: int = 100
    RESPONSE_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Phase 3: Security Settings
    ENCRYPT_CREDENTIALS: bool = True
    CREDENTIAL_ENCRYPTION_KEY: str = ""
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    
    # Phase 3: Feature Flags - Set based on actual implementation status
    # See CRITICAL_BUGS_FOUND.md for details on what's actually working
    ENABLE_AB_TESTING: bool = False  # Not implemented yet
    ENABLE_ADVANCED_ANALYTICS: bool = False  # Not implemented yet
    ENABLE_REAL_TIME_NOTIFICATIONS: bool = False  # WebSocket partial, needs work
    ENABLE_AUTOMATED_RESPONSES: bool = False  # Broken - service can't access DB
    ENABLE_ADVANCED_FILTERING: bool = True  # Basic filtering works
    
    # User Profile Settings (for response generation)
    USER_NAME: str = os.getenv("USER_NAME", "")
    USER_EMAIL: str = os.getenv("USER_EMAIL", "")
    USER_PHONE: str = os.getenv("USER_PHONE", "")

    # Gmail API Integration Settings
    GMAIL_ENABLED: bool = os.getenv("GMAIL_ENABLED", "false").lower() == "true"
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials/gmail_credentials.json")
    GMAIL_TOKEN_PATH: str = os.getenv("GMAIL_TOKEN_PATH", "credentials/gmail_token.pickle")
    GMAIL_POLL_INTERVAL: int = int(os.getenv("GMAIL_POLL_INTERVAL", "300"))  # 5 minutes in seconds
    GMAIL_MAX_EMAILS_PER_POLL: int = int(os.getenv("GMAIL_MAX_EMAILS_PER_POLL", "50"))
    GMAIL_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("GMAIL_RATE_LIMIT_PER_MINUTE", "30"))

    # Phase 2: LinkedIn Integration Settings
    LINKEDIN_ENABLED: bool = os.getenv("LINKEDIN_ENABLED", "false").lower() == "true"
    LINKEDIN_SERVICE: str = os.getenv("LINKEDIN_SERVICE", "piloterr")  # piloterr, scraperapi, brightdata, selenium
    LINKEDIN_API_KEY: str = os.getenv("LINKEDIN_API_KEY", "")  # For piloterr, scraperapi, brightdata

    # LinkedIn Selenium Settings (DIY - NOT RECOMMENDED)
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")  # For selenium only
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")  # For selenium only
    LINKEDIN_PROXY_URL: str = os.getenv("LINKEDIN_PROXY_URL", "")  # For selenium only

    # LinkedIn API Settings
    LINKEDIN_MAX_RESULTS_PER_SEARCH: int = int(os.getenv("LINKEDIN_MAX_RESULTS_PER_SEARCH", "100"))
    LINKEDIN_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("LINKEDIN_RATE_LIMIT_PER_MINUTE", "60"))
    LINKEDIN_TIMEOUT_SECONDS: int = int(os.getenv("LINKEDIN_TIMEOUT_SECONDS", "30"))
    LINKEDIN_RETRY_MAX_ATTEMPTS: int = int(os.getenv("LINKEDIN_RETRY_MAX_ATTEMPTS", "3"))
    LINKEDIN_BACKOFF_MULTIPLIER: float = float(os.getenv("LINKEDIN_BACKOFF_MULTIPLIER", "2"))

    # LinkedIn Storage Settings
    LINKEDIN_STORE_IN_LEADS_TABLE: bool = os.getenv("LINKEDIN_STORE_IN_LEADS_TABLE", "true").lower() == "true"
    LINKEDIN_DEDUPE_BY_URL: bool = os.getenv("LINKEDIN_DEDUPE_BY_URL", "true").lower() == "true"

    # Phase 2: Google Maps Business Scraper Settings
    GOOGLE_MAPS_ENABLED: bool = os.getenv("GOOGLE_MAPS_ENABLED", "true").lower() == "true"
    GOOGLE_MAPS_MAX_RESULTS: int = int(os.getenv("GOOGLE_MAPS_MAX_RESULTS", "100"))
    GOOGLE_MAPS_SCRAPE_TIMEOUT: int = int(os.getenv("GOOGLE_MAPS_SCRAPE_TIMEOUT", "300"))  # 5 minutes
    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")  # Optional: for API mode
    GOOGLE_MAPS_MIN_DELAY: float = float(os.getenv("GOOGLE_MAPS_MIN_DELAY", "2.0"))  # Seconds between requests
    GOOGLE_MAPS_MAX_DELAY: float = float(os.getenv("GOOGLE_MAPS_MAX_DELAY", "5.0"))  # Max delay
    GOOGLE_MAPS_ENABLE_EMAIL_EXTRACTION: bool = os.getenv("GOOGLE_MAPS_ENABLE_EMAIL_EXTRACTION", "true").lower() == "true"

    # Phase 2: Email Finder Integration Settings
    # Hunter.io - Free tier: 100 searches/month, Paid: $49/mo (1K), $99/mo (5K), $199/mo (20K)
    HUNTER_IO_ENABLED: bool = os.getenv("HUNTER_IO_ENABLED", "false").lower() == "true"
    HUNTER_IO_API_KEY: str = os.getenv("HUNTER_IO_API_KEY", "")
    HUNTER_MONTHLY_QUOTA: int = int(os.getenv("HUNTER_MONTHLY_QUOTA", "100"))  # Free tier default
    HUNTER_ALERT_THRESHOLD: int = int(os.getenv("HUNTER_ALERT_THRESHOLD", "80"))  # Alert at 80% usage

    # RocketReach - Alternative (more expensive but better for B2B)
    ROCKETREACH_ENABLED: bool = os.getenv("ROCKETREACH_ENABLED", "false").lower() == "true"
    ROCKETREACH_API_KEY: str = os.getenv("ROCKETREACH_API_KEY", "")
    ROCKETREACH_MONTHLY_QUOTA: int = int(os.getenv("ROCKETREACH_MONTHLY_QUOTA", "150"))  # $50/mo plan

    # Email Finder Settings
    EMAIL_FINDER_FALLBACK_TO_SCRAPING: bool = os.getenv("EMAIL_FINDER_FALLBACK_TO_SCRAPING", "true").lower() == "true"
    EMAIL_FINDER_CACHE_ENABLED: bool = os.getenv("EMAIL_FINDER_CACHE_ENABLED", "true").lower() == "true"
    EMAIL_FINDER_MIN_CONFIDENCE_SCORE: int = int(os.getenv("EMAIL_FINDER_MIN_CONFIDENCE_SCORE", "30"))  # Min score to use email

    # Phase 2: Job Board Scraper Settings (Indeed, Monster, ZipRecruiter)
    INDEED_ENABLED: bool = os.getenv("INDEED_ENABLED", "true").lower() == "true"
    MONSTER_ENABLED: bool = os.getenv("MONSTER_ENABLED", "true").lower() == "true"
    ZIPRECRUITER_ENABLED: bool = os.getenv("ZIPRECRUITER_ENABLED", "true").lower() == "true"

    # Job scraping configuration
    JOB_SCRAPE_DELAY_SECONDS: int = int(os.getenv("JOB_SCRAPE_DELAY_SECONDS", "3"))  # Delay between requests
    JOB_MAX_RESULTS_PER_SOURCE: int = int(os.getenv("JOB_MAX_RESULTS_PER_SOURCE", "100"))  # Max jobs per source
    JOB_ENABLE_COMPANY_LOOKUP: bool = os.getenv("JOB_ENABLE_COMPANY_LOOKUP", "false").lower() == "true"  # Slow but gets company info
    JOB_SCRAPE_TIMEOUT: int = int(os.getenv("JOB_SCRAPE_TIMEOUT", "600"))  # 10 minutes max per source

    # Job board specific settings
    INDEED_MIN_DELAY: float = float(os.getenv("INDEED_MIN_DELAY", "2.0"))  # Seconds
    INDEED_MAX_DELAY: float = float(os.getenv("INDEED_MAX_DELAY", "5.0"))
    MONSTER_MIN_DELAY: float = float(os.getenv("MONSTER_MIN_DELAY", "2.0"))
    MONSTER_MAX_DELAY: float = float(os.getenv("MONSTER_MAX_DELAY", "5.0"))
    ZIPRECRUITER_MIN_DELAY: float = float(os.getenv("ZIPRECRUITER_MIN_DELAY", "3.0"))  # Longer delays due to bot detection
    ZIPRECRUITER_MAX_DELAY: float = float(os.getenv("ZIPRECRUITER_MAX_DELAY", "7.0"))

    # Proxy settings for job boards (optional - helps avoid detection)
    JOB_SCRAPER_PROXY_ENABLED: bool = os.getenv("JOB_SCRAPER_PROXY_ENABLED", "false").lower() == "true"
    JOB_SCRAPER_PROXY_URL: str = os.getenv("JOB_SCRAPER_PROXY_URL", "")  # Format: http://user:pass@host:port

    # Bot detection warnings
    JOB_SCRAPER_WARN_ON_CAPTCHA: bool = os.getenv("JOB_SCRAPER_WARN_ON_CAPTCHA", "true").lower() == "true"
    JOB_SCRAPER_STOP_ON_RATE_LIMIT: bool = os.getenv("JOB_SCRAPER_STOP_ON_RATE_LIMIT", "true").lower() == "true"

    # Phase 3: Vercel Deployment Settings (Task 4)
    VERCEL_ENABLED: bool = os.getenv("VERCEL_ENABLED", "false").lower() == "true"
    VERCEL_API_TOKEN: str = os.getenv("VERCEL_API_TOKEN", "")  # Required for deployment
    VERCEL_TEAM_ID: str = os.getenv("VERCEL_TEAM_ID", "")  # Optional: for team accounts
    VERCEL_MAX_RETRIES: int = int(os.getenv("VERCEL_MAX_RETRIES", "3"))
    VERCEL_TIMEOUT_SECONDS: int = int(os.getenv("VERCEL_TIMEOUT_SECONDS", "60"))
    VERCEL_RATE_LIMIT_PER_SECOND: int = int(os.getenv("VERCEL_RATE_LIMIT_PER_SECOND", "20"))
    VERCEL_MAX_DEPLOYMENT_WAIT_TIME: int = int(os.getenv("VERCEL_MAX_DEPLOYMENT_WAIT_TIME", "600"))  # 10 minutes
    VERCEL_POLL_INTERVAL: int = int(os.getenv("VERCEL_POLL_INTERVAL", "5"))  # Check deployment status every 5s

    # Vercel Cost Tracking
    VERCEL_MONTHLY_BASE_COST: float = float(os.getenv("VERCEL_MONTHLY_BASE_COST", "20.0"))  # Pro plan default
    VERCEL_BANDWIDTH_INCLUDED_GB: int = int(os.getenv("VERCEL_BANDWIDTH_INCLUDED_GB", "100"))
    VERCEL_BUILD_MINUTES_INCLUDED: int = int(os.getenv("VERCEL_BUILD_MINUTES_INCLUDED", "6000"))
    VERCEL_ADDITIONAL_BANDWIDTH_COST_PER_100GB: float = float(os.getenv("VERCEL_ADDITIONAL_BANDWIDTH_COST_PER_100GB", "40.0"))
    VERCEL_ADDITIONAL_BUILD_MINUTES_COST_PER_500MIN: float = float(os.getenv("VERCEL_ADDITIONAL_BUILD_MINUTES_COST_PER_500MIN", "8.0"))

    # Phase 4: ElevenLabs Voice Synthesis Settings (Task 2)
    ELEVENLABS_ENABLED: bool = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_MODEL_ID: str = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    ELEVENLABS_TIMEOUT_SECONDS: int = int(os.getenv("ELEVENLABS_TIMEOUT_SECONDS", "60"))
    ELEVENLABS_MAX_RETRIES: int = int(os.getenv("ELEVENLABS_MAX_RETRIES", "3"))
    ELEVENLABS_CONCURRENT_LIMIT: int = int(os.getenv("ELEVENLABS_CONCURRENT_LIMIT", "3"))

    # Voiceover Storage Settings
    VOICEOVER_STORAGE_PATH: str = os.getenv("VOICEOVER_STORAGE_PATH", "./storage/voiceovers")
    VOICEOVER_CACHE_ENABLED: bool = os.getenv("VOICEOVER_CACHE_ENABLED", "true").lower() == "true"
    VOICEOVER_CACHE_EXPIRY_DAYS: int = int(os.getenv("VOICEOVER_CACHE_EXPIRY_DAYS", "30"))
    VOICEOVER_DEFAULT_VOICE_PRESET: str = os.getenv("VOICEOVER_DEFAULT_VOICE_PRESET", "professional_female")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env that aren't defined in the model

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse ALLOWED_HOSTS string into list."""
        if not self.ALLOWED_HOSTS:
            return []
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    def __init__(self, **kwargs):
        """Validate critical settings on initialization."""
        super().__init__(**kwargs)

        # Validate critical settings in production
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY == "":
                raise ValueError("SECRET_KEY must be set in production environment")
            if not self.REDIS_URL:
                raise ValueError("REDIS_URL must be set in production environment")
            if "*" in self.ALLOWED_HOSTS:
                raise ValueError("ALLOWED_HOSTS cannot contain wildcards in production")
            # Security: No localhost in production CORS
            for host in self.allowed_hosts_list:
                if "localhost" in host or "127.0.0.1" in host:
                    raise ValueError(f"ALLOWED_HOSTS cannot contain localhost/127.0.0.1 in production: {host}")
            if self.DATABASE_POOL_SIZE + self.DATABASE_MAX_OVERFLOW > 30:
                raise ValueError("Total database connections cannot exceed 30 (pool_size + max_overflow)")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")


# Create settings instance
settings = Settings()