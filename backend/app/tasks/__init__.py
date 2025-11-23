"""
Celery Tasks Module

This module contains all background tasks for the FlipTech Pro application.
Tasks are organized by category:

- email_tasks: Email sending and batch processing
- campaign_tasks: Campaign execution and management
- scraper_tasks: Web scraping operations
- ai_tasks: AI/ML processing
- demo_tasks: Demo site generation
"""

from celery import Celery

# Import all tasks to make them discoverable by Celery
from app.tasks.email_tasks import (
    send_single_email,
    send_batch_emails,
    retry_failed_emails,
)

from app.tasks.campaign_tasks import (
    send_campaign_emails,
    process_campaign_batch,
    launch_campaign_async,
    process_scheduled_campaigns,
    update_campaign_metrics,
    cleanup_old_task_results,
    generate_daily_analytics,
)

from app.tasks.scraper_tasks import (
    scrape_craigslist,
    scrape_google_maps,
    scrape_linkedin,
    scrape_job_boards,
    scrape_multi_source,
    monitor_scraper_jobs,
    cleanup_old_scraper_data,
)

from app.tasks.ai_tasks import (
    generate_ai_response,
    analyze_lead,
    process_conversation,
    batch_analyze_leads,
    generate_email_content,
)

from app.tasks.demo_tasks import (
    generate_demo_site,
    compose_video,
    generate_voiceover,
    capture_screen_recording,
)

__all__ = [
    # Email tasks
    "send_single_email",
    "send_batch_emails",
    "retry_failed_emails",
    # Campaign tasks
    "send_campaign_emails",
    "process_campaign_batch",
    "launch_campaign_async",
    "process_scheduled_campaigns",
    "update_campaign_metrics",
    "cleanup_old_task_results",
    "generate_daily_analytics",
    # Scraper tasks
    "scrape_craigslist",
    "scrape_google_maps",
    "scrape_linkedin",
    "scrape_job_boards",
    "scrape_multi_source",
    "monitor_scraper_jobs",
    "cleanup_old_scraper_data",
    # AI tasks
    "generate_ai_response",
    "analyze_lead",
    "process_conversation",
    "batch_analyze_leads",
    "generate_email_content",
    # Demo tasks
    "generate_demo_site",
    "compose_video",
    "generate_voiceover",
    "capture_screen_recording",
]
