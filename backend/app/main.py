"""
FastAPI main application module for Craigslist Lead Generation Dashboard.
"""

import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logging_config import setup_logging, get_logger
from app.models import Base
from app.middleware.exception_handlers import register_exception_handlers
from app.middleware.logging_middleware import (
    RequestLoggingMiddleware,
    PerformanceLoggingMiddleware,
    SecurityLoggingMiddleware
)
from app.api.endpoints import leads, locations, scraper, ml, qualification, responses, approvals
from app.api.endpoints import templates, rules, notifications, schedule  # Phase 3 endpoints - NOW ENABLED
from app.api.endpoints import websocket  # WebSocket works, keep it
from app.api.endpoints import ai_mvp  # MVP: AI-powered lead generation
from app.api.endpoints import conversations  # Conversation management system
from app.api.endpoints import google_maps  # Phase 2: Google Maps business scraper
from app.api.endpoints import job_boards  # Phase 2: Job boards scraper (Indeed, Monster, ZipRecruiter)
from app.api.endpoints import email_finder  # Phase 2: Universal email finder (Hunter.io + scraping)
from app.api.endpoints import linkedin  # Phase 2: LinkedIn job scraper (Piloterr + DIY)
from app.api.endpoints import linkedin_contacts  # LinkedIn Contact Import + Messaging Integration
from app.api.endpoints import demo_sites  # Phase 3: Vercel deployment integration - NOW ENABLED
from app.api.endpoints import knowledge_base  # Knowledge Base: Semantic search for AI agents
from app.api.endpoints import campaigns  # Campaign Management: Email campaigns with tracking
from app.api.endpoints import email_tracking  # Email Tracking - NOW ENABLED
from app.api.endpoints import tags  # Lead Tags: Organize and categorize leads
from app.api.endpoints import notes  # Lead Notes: Annotate and track lead interactions
from app.api.endpoints import export  # Data Export: CSV, Excel, JSON exports with analytics
from app.api.endpoints import website_analysis  # Website Analysis: AI-powered website analysis and recommendations
# Phase 4: Video Creation System endpoints
from app.api.endpoints import video_scripts  # Phase 4: AI video script generation
from app.api.endpoints import voiceovers  # Phase 4: ElevenLabs voice synthesis
from app.api.endpoints import screen_recordings  # Phase 4: Screen recording automation
from app.api.endpoints import composed_videos  # Phase 4: Video composition with FFmpeg
from app.api.endpoints import hosted_videos  # Phase 4: Video hosting (S3/Loom)

# Phase 5: AI-GYM Multi-Model Optimization
from app.api.endpoints import ai_gym  # AI-GYM: Multi-model performance tracking and optimization

# Phase 6: N8N Workflow Automation endpoints
from app.api.endpoints import n8n_webhooks  # Phase 6: n8n webhook receivers
from app.api.endpoints import workflows  # Phase 6: Workflow management
from app.api.endpoints import workflow_approvals  # Phase 6: Approval system


# Configure structured logging
setup_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager with comprehensive health checks."""
    # Startup
    logger.info("Starting up CraigLeads Pro API", environment=settings.ENVIRONMENT, version="2.0.0")

    # Health check results
    health_checks_passed = True

    try:
        # Health Check 1: Database Connection
        logger.info("Checking database connection", check="database")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database connected and tables verified", check="database", status="success")
        except Exception as e:
            logger.error("Database connection failed", exc_info=e, check="database", status="failed")
            health_checks_passed = False
            raise

        # Health Check 2: Redis (Optional - graceful degradation)
        logger.info("[2/4] Checking Redis connection...")
        try:
            if settings.REDIS_URL:
                import redis
                rc = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                rc.ping()
                logger.info("✓ Redis connected and available")
            else:
                logger.warning("⚠ Redis not configured - job queue and caching disabled")
        except Exception as e:
            logger.warning(f"⚠ Redis connection failed: {e}")
            logger.warning("  Continuing without Redis - scraping job queue will be disabled")
            # Don't fail startup for Redis issues

        # Health Check 3: Required Environment Variables
        logger.info("[3/4] Validating environment configuration...")
        missing_vars = []
        warnings = []

        # Check production-required variables
        if settings.ENVIRONMENT == "production":
            if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here-change-in-production":
                missing_vars.append("SECRET_KEY (must be set to secure value)")

            if "*" in settings.ALLOWED_HOSTS or "localhost" in str(settings.ALLOWED_HOSTS):
                logger.error("✗ ALLOWED_HOSTS contains wildcard or localhost in production!")
                missing_vars.append("ALLOWED_HOSTS (no wildcards or localhost in production)")

        # Check optional but important variables
        if not settings.USER_NAME or not settings.USER_EMAIL:
            warnings.append("USER_NAME/USER_EMAIL not set - response generation will fail")

        if settings.ENABLE_EMAIL_EXTRACTION and not settings.TWOCAPTCHA_API_KEY:
            warnings.append("Email extraction enabled but TWOCAPTCHA_API_KEY not set")

        if missing_vars:
            logger.error(f"✗ Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"  - {var}")
            health_checks_passed = False
            raise ValueError(f"Missing required environment variables: {missing_vars}")

        if warnings:
            logger.warning("⚠ Environment warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        logger.info("✓ Environment configuration validated")

        # Health Check 4: Feature Status
        logger.info("[4/4] Checking feature flags...")
        enabled_features = []
        disabled_features = []

        if settings.ENABLE_REAL_TIME_NOTIFICATIONS:
            enabled_features.append("Real-time notifications")
        else:
            disabled_features.append("Real-time notifications")

        if settings.ENABLE_AUTOMATED_RESPONSES:
            enabled_features.append("Auto-responder")
        else:
            disabled_features.append("Auto-responder (service has DB access issues)")

        if settings.ENABLE_ADVANCED_FILTERING:
            enabled_features.append("Advanced filtering")
        else:
            disabled_features.append("Advanced filtering")

        if enabled_features:
            logger.info(f"✓ Enabled features: {', '.join(enabled_features)}")

        if disabled_features:
            logger.warning(f"⚠ Disabled features: {', '.join(disabled_features)}")

        # Health Check 5: Start Gmail Monitoring (if enabled)
        if settings.GMAIL_ENABLED:
            logger.info("[5/5] Starting Gmail monitoring service...")
            try:
                from app.services.gmail_monitor import gmail_monitor
                asyncio.create_task(gmail_monitor.start_monitoring())
                logger.info("✓ Gmail monitoring service started")
            except Exception as e:
                logger.warning(f"⚠ Gmail monitoring failed to start: {e}")
                logger.warning("  Continuing without Gmail monitoring")

        logger.info(
            "All health checks passed - CraigLeads Pro API ready",
            environment=settings.ENVIRONMENT,
            debug_mode=settings.DEBUG,
            version="2.0.0",
            gmail_monitoring=settings.GMAIL_ENABLED
        )

    except Exception as e:
        logger.error("Startup failed", exc_info=e)
        raise

    yield

    # Shutdown
    logger.info("Shutting down CraigLeads Pro API")

    try:
        # Stop background services
        try:
            from app.services.scheduler import scheduler_service
            if hasattr(scheduler_service, 'scheduler_running') and scheduler_service.scheduler_running:
                await scheduler_service.stop_scheduler()
                logger.info("✓ Scheduler service stopped")
        except ImportError:
            # Scheduler service may not exist if Phase 3 is disabled
            pass
        except Exception as e:
            logger.warning(f"⚠ Error stopping scheduler: {e}")

        # Stop Gmail monitoring
        if settings.GMAIL_ENABLED:
            try:
                from app.services.gmail_monitor import gmail_monitor
                await gmail_monitor.stop_monitoring()
                logger.info("✓ Gmail monitoring stopped")
            except Exception as e:
                logger.warning(f"⚠ Error stopping Gmail monitoring: {e}")

        logger.info("Application shutdown completed")

    except Exception as e:
        logger.error("Error during shutdown", exc_info=e)


# Legacy exception handlers (kept for backward compatibility)
# Note: These are overridden by the new structured exception handlers


# Create FastAPI application
app = FastAPI(
    title="CraigLeads Pro API",
    description="""
    Advanced Craigslist lead generation and management platform with AI-powered features.
    
    ## Features
    
    * **Lead Management** - Scrape, filter, and manage Craigslist leads
    * **AI Auto-Responder** - Automated personalized responses with OpenAI/Claude integration
    * **Advanced Filtering** - Rule engine with complex conditions and actions
    * **Real-time Notifications** - WebSocket, Email, Slack, Discord, and SMS notifications
    * **Automated Scheduling** - Cron-based task scheduling with peak time optimization
    * **Data Export & Analytics** - CSV, Excel, JSON exports with comprehensive analytics
    * **A/B Testing** - Template performance testing and optimization
    
    ## Phase 3 Advanced Features
    
    This release includes production-ready advanced features for enterprise lead generation.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Register structured exception handlers
register_exception_handlers(app)

# Add logging middleware
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_threshold_seconds=1.0)
app.add_middleware(RequestLoggingMiddleware, enable_audit=True)

# Template Security Middleware
from app.middleware.template_security_middleware import setup_template_security
setup_template_security(app, strict_csp=settings.ENVIRONMENT == "production")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers - Phase 1 & 2
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(locations.router, prefix="/api/v1/locations", tags=["locations"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(google_maps.router, prefix="/api/v1/google-maps", tags=["google-maps"])
app.include_router(ml.router, tags=["machine-learning"])
app.include_router(qualification.router, prefix="/api/v1/qualification", tags=["qualification"])
app.include_router(responses.router, prefix="/api/v1/responses", tags=["responses"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])

# Include routers - Phase 3 (NOW ENABLED)
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(schedule.router, prefix="/api/v1/schedules", tags=["schedules"])

# WebSocket works - keep enabled
app.include_router(websocket.router, tags=["websocket"])

# AI MVP endpoints - NEW
app.include_router(ai_mvp.router, prefix="/api/v1/ai-mvp", tags=["ai-mvp"])

# Conversation management endpoints - NEW
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])

# Email Finder endpoints - Phase 2
app.include_router(email_finder.router, tags=["email-finder"])

# Job Boards endpoints - Phase 2 (Indeed, Monster, ZipRecruiter)
app.include_router(job_boards.router, prefix="/api/v1/job-boards", tags=["job-boards"])

# LinkedIn endpoints - Phase 2
app.include_router(linkedin.router, prefix="/api/v1/linkedin", tags=["linkedin"])

# LinkedIn Contacts endpoints - Contact Import + Messaging Integration
app.include_router(linkedin_contacts.router, prefix="/api/v1/linkedin", tags=["linkedin-contacts"])

# Demo Sites endpoints - Phase 3, Task 4 (NOW ENABLED)
app.include_router(demo_sites.router, prefix="/api/v1/demo-sites", tags=["demo-sites"])

# Knowledge Base endpoints - Semantic search for AI agents
app.include_router(knowledge_base.router, tags=["knowledge-base"])

# Campaign Management endpoints - Email campaigns with tracking
app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])

# Email Tracking endpoints (NOW ENABLED)
app.include_router(email_tracking.router, prefix="/api/v1/tracking", tags=["email-tracking"])

# Lead Tags endpoints - Organize and categorize leads
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])

# Lead Notes endpoints - Annotate and track lead interactions
app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])

# Export endpoints - Data export with CSV, Excel, JSON formats
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

# Website Analysis endpoints - AI-powered website analysis and recommendations
app.include_router(website_analysis.router, prefix="/api/v1/website-analysis", tags=["website-analysis"])

# Phase 4: Video Creation System routers
app.include_router(video_scripts.router, prefix="/api/v1/videos/scripts", tags=["video-scripts"])
app.include_router(voiceovers.router, prefix="/api/v1/videos/voiceovers", tags=["voiceovers"])
app.include_router(screen_recordings.router, prefix="/api/v1/videos/recordings", tags=["screen-recordings"])
app.include_router(composed_videos.router, prefix="/api/v1/videos/composed", tags=["composed-videos"])
app.include_router(hosted_videos.router, prefix="/api/v1/videos/hosted", tags=["hosted-videos"])

# Phase 5: AI-GYM Multi-Model Optimization
app.include_router(ai_gym.router, prefix="/api/v1/ai-gym", tags=["ai-gym"])

# Phase 6: N8N Workflow Automation routers
app.include_router(n8n_webhooks.router, prefix="/api/v1/webhooks/n8n", tags=["n8n-webhooks"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(workflow_approvals.router, prefix="/api/v1/workflows/approvals", tags=["workflow-approvals"])


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "CraigLeads Pro API - Advanced Lead Generation Platform",
        "version": "3.0.0",
        "phase": "6 - Enterprise Complete",
        "features": [
            "Multi-Source Lead Scraping (7 sources)",
            "AI-Powered Auto-Responder (8 AI models)",
            "Website Analysis Agent",
            "Video Creation System (AI scripts + ElevenLabs + FFmpeg)",
            "Demo Site Builder (AI-powered + Vercel deployment)",
            "AI-GYM Multi-Model Optimization (40-60% cost savings)",
            "N8N Workflow Automation",
            "Advanced Rule Engine",
            "Real-time Notifications",
            "Campaign Management",
            "LinkedIn Contact Management",
            "Data Export & Analytics"
        ],
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {}
    }
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            health_status["services"]["database"] = {
                "status": "healthy",
                "connection": "active"
            }
        
        # Test Redis connection (if configured)
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis
                redis_client = redis.from_url(settings.REDIS_URL)
                await redis_client.ping()
                health_status["services"]["redis"] = {"status": "healthy"}
                await redis_client.close()
            except Exception as e:
                health_status["services"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
        
        # Check feature flags
        health_status["features"] = {
            "auto_responder": settings.AUTO_RESPONDER_ENABLED,
            "rule_engine": settings.RULE_ENGINE_ENABLED,
            "notifications": settings.ENABLE_REAL_TIME_NOTIFICATIONS,
            "advanced_analytics": settings.ENABLE_ADVANCED_ANALYTICS,
            "ab_testing": settings.ENABLE_AB_TESTING
        }
        
        # Check AI services
        health_status["ai"] = {
            "provider": settings.AI_PROVIDER,
            "configured": bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY)
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "Health check failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/system/info")
async def system_info():
    """Get system information and configuration."""
    try:
        from app.services.scheduler import scheduler_service
        from app.services.notification_service import notification_service
        
        return {
            "system": {
                "name": "CraigLeads Pro",
                "version": "2.0.0",
                "environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG
            },
            "database": {
                "url": settings.DATABASE_URL.split("@")[-1],  # Hide credentials
                "pool_size": settings.DATABASE_POOL_SIZE
            },
            "features": {
                "ai_provider": settings.AI_PROVIDER,
                "auto_responder": settings.AUTO_RESPONDER_ENABLED,
                "rule_engine": settings.RULE_ENGINE_ENABLED,
                "notifications": settings.ENABLE_REAL_TIME_NOTIFICATIONS,
                "advanced_analytics": settings.ENABLE_ADVANCED_ANALYTICS,
                "ab_testing": settings.ENABLE_AB_TESTING
            },
            "limits": {
                "export_max_records": settings.EXPORT_MAX_RECORDS,
                "concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
                "response_timeout": settings.RESPONSE_TIMEOUT
            },
            "services": {
                "scheduler_running": getattr(scheduler_service, 'scheduler_running', False),
                "running_schedules": len(getattr(scheduler_service, 'running_schedules', {}))
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )