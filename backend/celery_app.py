"""
Celery Application Configuration for FlipTech Pro

This module configures Celery for background task processing including:
- Email sending and campaign management
- Web scraping operations
- AI/ML processing
- Demo site generation
- Scheduled tasks
"""

import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get configuration from environment
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB_BROKER = os.getenv("REDIS_DB_BROKER", "0")
REDIS_DB_BACKEND = os.getenv("REDIS_DB_BACKEND", "1")

# Construct Redis URLs
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BROKER}"
BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_BACKEND}"

# Create Celery application
celery_app = Celery(
    "fliptechpro",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.campaign_tasks",
        "app.tasks.scraper_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.demo_tasks",
    ]
)

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Tasks are acknowledged after execution
    task_reject_on_worker_lost=True,  # Reject task if worker crashes
    task_track_started=True,  # Track when tasks start

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,  # Store extended result metadata

    # Task time limits (in seconds)
    task_soft_time_limit=600,  # 10 minutes soft limit
    task_time_limit=900,  # 15 minutes hard limit

    # Worker settings
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,

    # Task retry settings
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,  # Maximum 3 retries by default

    # Task routing
    task_routes={
        # Email tasks - high priority, dedicated queue
        "app.tasks.email_tasks.*": {"queue": "email"},

        # Campaign tasks - high priority
        "app.tasks.campaign_tasks.*": {"queue": "email"},

        # Scraper tasks - low priority, long-running
        "app.tasks.scraper_tasks.*": {"queue": "scraper"},

        # AI tasks - medium priority, GPU queue if available
        "app.tasks.ai_tasks.*": {"queue": "ai"},

        # Demo tasks - low priority, long-running
        "app.tasks.demo_tasks.*": {"queue": "demo"},

        # Default queue for everything else
    },

    # Task rate limits
    task_annotations={
        "app.tasks.email_tasks.send_single_email": {
            "rate_limit": "50/m",  # 50 emails per minute
        },
        "app.tasks.scraper_tasks.scrape_craigslist": {
            "rate_limit": "10/m",  # 10 scrapes per minute
        },
        "app.tasks.scraper_tasks.scrape_google_maps": {
            "rate_limit": "5/m",  # 5 scrapes per minute
        },
        "app.tasks.scraper_tasks.scrape_linkedin": {
            "rate_limit": "3/m",  # 3 scrapes per minute (be careful with LinkedIn)
        },
        "app.tasks.ai_tasks.generate_ai_response": {
            "rate_limit": "30/m",  # 30 AI requests per minute
        },
    },
)

# ============================================================================
# QUEUE CONFIGURATION
# ============================================================================

# Define exchanges
default_exchange = Exchange("default", type="direct")
email_exchange = Exchange("email", type="direct")
scraper_exchange = Exchange("scraper", type="direct")
ai_exchange = Exchange("ai", type="direct")
demo_exchange = Exchange("demo", type="direct")

# Define queues with priorities
celery_app.conf.task_queues = (
    # Default queue
    Queue("default", exchange=default_exchange, routing_key="default", priority=5),

    # Email queue - highest priority
    Queue("email", exchange=email_exchange, routing_key="email", priority=10),

    # Scraper queue - low priority, long-running tasks
    Queue("scraper", exchange=scraper_exchange, routing_key="scraper", priority=3),

    # AI queue - medium priority
    Queue("ai", exchange=ai_exchange, routing_key="ai", priority=6),

    # Demo queue - low priority, very long-running
    Queue("demo", exchange=demo_exchange, routing_key="demo", priority=2),
)

# Default queue
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_default_exchange = "default"
celery_app.conf.task_default_routing_key = "default"

# ============================================================================
# CELERY BEAT SCHEDULE (Periodic Tasks)
# ============================================================================

celery_app.conf.beat_schedule = {
    # Process scheduled campaigns every minute
    "process-scheduled-campaigns": {
        "task": "app.tasks.campaign_tasks.process_scheduled_campaigns",
        "schedule": crontab(minute="*"),  # Every minute
        "options": {"queue": "email"},
    },

    # Retry failed emails every 15 minutes
    "retry-failed-emails": {
        "task": "app.tasks.email_tasks.retry_failed_emails",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {"queue": "email"},
    },

    # Update campaign metrics every 5 minutes
    "update-campaign-metrics": {
        "task": "app.tasks.campaign_tasks.update_campaign_metrics",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {"queue": "email"},
    },

    # Clean up old task results every hour
    "cleanup-task-results": {
        "task": "app.tasks.campaign_tasks.cleanup_old_task_results",
        "schedule": crontab(minute="0", hour="*"),  # Every hour
        "options": {"queue": "default"},
    },

    # Monitor scraper jobs every 10 minutes
    "monitor-scraper-jobs": {
        "task": "app.tasks.scraper_tasks.monitor_scraper_jobs",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
        "options": {"queue": "scraper"},
    },

    # Cleanup old scraper data daily at 3 AM
    "cleanup-old-scraper-data": {
        "task": "app.tasks.scraper_tasks.cleanup_old_scraper_data",
        "schedule": crontab(minute="0", hour="3"),  # 3:00 AM daily
        "options": {"queue": "scraper"},
    },

    # Generate daily analytics report at 1 AM
    "generate-daily-analytics": {
        "task": "app.tasks.campaign_tasks.generate_daily_analytics",
        "schedule": crontab(minute="0", hour="1"),  # 1:00 AM daily
        "options": {"queue": "default"},
    },
}

# ============================================================================
# EVENT MONITORING
# ============================================================================

# Enable events for monitoring with Flower
celery_app.conf.worker_send_task_events = True
celery_app.conf.task_send_sent_event = True

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

celery_app.conf.worker_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
celery_app.conf.worker_task_log_format = (
    "[%(asctime)s: %(levelname)s/%(processName)s] "
    "[%(task_name)s(%(task_id)s)] %(message)s"
)

# ============================================================================
# CUSTOM CONFIGURATION
# ============================================================================

# Email sending configuration
EMAIL_BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "50"))
EMAIL_BATCH_DELAY = int(os.getenv("EMAIL_BATCH_DELAY", "2"))  # seconds between emails

# Scraper configuration
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "300"))  # 5 minutes
SCRAPER_RETRY_DELAY = int(os.getenv("SCRAPER_RETRY_DELAY", "120"))  # 2 minutes

# AI configuration
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "180"))  # 3 minutes
AI_RETRY_DELAY = int(os.getenv("AI_RETRY_DELAY", "60"))  # 1 minute

# Demo configuration
DEMO_TIMEOUT = int(os.getenv("DEMO_TIMEOUT", "1800"))  # 30 minutes
VIDEO_PROCESSING_TIMEOUT = int(os.getenv("VIDEO_PROCESSING_TIMEOUT", "3600"))  # 1 hour

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Celery error handlers
@celery_app.task(bind=True)
def error_handler(self, uuid):
    """Handle task errors"""
    result = self.app.AsyncResult(uuid)
    exc = result.info
    print(f"Task {uuid} raised exception: {exc}")

# ============================================================================
# UTILITIES
# ============================================================================

def get_celery_app():
    """
    Get the Celery application instance.

    Returns:
        Celery: The configured Celery application
    """
    return celery_app

# ============================================================================
# TASK LIFECYCLE HOOKS
# ============================================================================

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f"Request: {self.request!r}")
    return "Celery is working!"

# Export the app
__all__ = ["celery_app", "get_celery_app"]
