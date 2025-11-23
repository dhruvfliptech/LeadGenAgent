"""
FastAPI main application module with comprehensive security enhancements.
Implements OWASP security best practices.
"""

import logging
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api.endpoints import leads, locations, scraper, ml, qualification, responses, approvals

# Import security components
from app.core.security_middleware import (
    SecurityHeadersMiddleware,
    SensitiveDataProtectionMiddleware,
    RequestValidationMiddleware,
    AuditLoggingMiddleware
)

# Import rate limiting - with fallback if not available
try:
    from app.core.rate_limiter import limiter, create_rate_limit_exceeded_response
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    print("Warning: Rate limiting not available. Install slowapi for rate limiting support.")

# Configure logging with security considerations
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/app.log", mode="a") if settings.ENVIRONMENT == "production" else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager with security initialization."""
    # Startup
    logger.info("Starting up CraigLeads Pro API with security enhancements...")

    try:
        # Verify security configuration
        if settings.ENVIRONMENT == "production":
            if not settings.SECRET_KEY:
                logger.error("SECRET_KEY not configured for production!")
                raise ValueError("SECRET_KEY must be set in production environment")

            if not settings.ALLOWED_HOSTS:
                logger.warning("ALLOWED_HOSTS not configured - using defaults")

        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified successfully")

        # Initialize security components
        logger.info("Security middleware initialized:")
        logger.info("- Security headers: ENABLED")
        logger.info(f"- Rate limiting: {'ENABLED' if RATE_LIMITING_AVAILABLE else 'DISABLED'}")
        logger.info("- Input validation: ENABLED")
        logger.info("- Sensitive data protection: ENABLED")
        logger.info("- Audit logging: ENABLED")

        # Start background services for Phase 3
        if settings.ENABLE_REAL_TIME_NOTIFICATIONS:
            logger.info("Starting notification service...")

        if settings.RULE_ENGINE_ENABLED:
            logger.info("Rule engine enabled and ready")

        if settings.AUTO_RESPONDER_ENABLED:
            logger.info("Auto-responder service enabled")

        logger.info("CraigLeads Pro API startup completed successfully with security enhancements")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CraigLeads Pro API...")
    try:
        # Stop background services
        from app.services.scheduler import scheduler_service
        if hasattr(scheduler_service, 'scheduler_running') and scheduler_service.scheduler_running:
            await scheduler_service.stop_scheduler()
            logger.info("Scheduler service stopped")

        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Global exception handlers with security considerations
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler that prevents information leakage."""
    # Log full error internally
    logger.error(
        f"Global exception handler caught: {type(exc).__name__}: {exc}",
        extra={
            "url": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )

    # Return sanitized error to client (no sensitive information)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom HTTP exception handler with security considerations."""
    # Log based on status code
    if exc.status_code >= 500:
        logger.error(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "status_code": exc.status_code
            }
        )
    else:
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "status_code": exc.status_code
            }
        )

    # Sanitize error detail to prevent information leakage
    detail = exc.detail
    if exc.status_code == 500 and settings.ENVIRONMENT == "production":
        detail = "Internal server error occurred"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )


# Request logging middleware with security audit
async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests with security context."""
    start_time = datetime.utcnow()

    # Generate request ID for tracing
    import uuid
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # Get client IP (considering proxies)
    client_ip = request.client.host if request.client else "unknown"
    for header in ["X-Real-IP", "X-Forwarded-For"]:
        if header in request.headers:
            client_ip = request.headers[header].split(",")[0].strip()
            break

    # Log request (excluding sensitive headers)
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": client_ip,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )

    try:
        response = await call_next(request)

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_seconds": duration
            }
        )

        return response

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {type(e).__name__}: {e}",
            extra={
                "request_id": request_id,
                "duration_seconds": duration,
                "error_type": type(e).__name__
            }
        )
        raise


# Create FastAPI application with security configuration
app = FastAPI(
    title="CraigLeads Pro API - Secured",
    description="""
    Advanced Craigslist lead generation and management platform with comprehensive security.

    ## Security Features

    * **Authentication** - JWT-based authentication with refresh tokens
    * **Authorization** - Role-based access control (RBAC)
    * **Rate Limiting** - Endpoint-specific rate limits to prevent abuse
    * **Input Validation** - Comprehensive input validation and sanitization
    * **Security Headers** - OWASP recommended security headers
    * **Audit Logging** - Security event logging and monitoring
    * **Data Protection** - Sensitive data masking and encryption

    ## Features

    * **Lead Management** - Scrape, filter, and manage Craigslist leads
    * **AI Auto-Responder** - Automated personalized responses with OpenAI/Claude integration
    * **Advanced Filtering** - Rule engine with complex conditions and actions
    * **Real-time Notifications** - WebSocket, Email, Slack, Discord, and SMS notifications
    * **Automated Scheduling** - Cron-based task scheduling with peak time optimization
    * **Data Export & Analytics** - CSV, Excel, JSON exports with comprehensive analytics
    * **A/B Testing** - Template performance testing and optimization

    ## API Security

    All endpoints are protected with:
    - Input validation against injection attacks
    - Rate limiting to prevent abuse
    - Authentication required for sensitive operations
    - Comprehensive audit logging
    """,
    version="2.0.0-secured",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,  # Disable redoc in production
    openapi_url="/openapi.json" if settings.DEBUG else None,  # Disable OpenAPI schema in production
    lifespan=lifespan
)

# Add exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Add rate limit exception handler if available
if RATE_LIMITING_AVAILABLE:
    app.add_exception_handler(RateLimitExceeded, create_rate_limit_exceeded_response)
    app.state.limiter = limiter

# Apply security middleware in order (order matters!)

# 1. Trusted Host middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.craigleads.com", "craigleads.com"]  # Update with your domains
    )

# 2. Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request validation middleware
app.add_middleware(RequestValidationMiddleware)

# 4. Sensitive data protection middleware
app.add_middleware(SensitiveDataProtectionMiddleware)

# 5. Audit logging middleware
app.add_middleware(AuditLoggingMiddleware)

# 6. Request logging middleware
app.middleware("http")(request_logging_middleware)

# 7. CORS Middleware (configured securely)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# 8. Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers - Phase 1 & 2
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(locations.router, prefix="/api/v1/locations", tags=["locations"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(ml.router, tags=["machine-learning"])
app.include_router(qualification.router, prefix="/api/v1/qualification", tags=["qualification"])
app.include_router(responses.router, prefix="/api/v1/responses", tags=["responses"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])


@app.get("/")
async def root():
    """Root endpoint with system information (limited in production)."""
    base_info = {
        "message": "CraigLeads Pro API - Secured Edition",
        "version": "2.0.0-secured",
        "status": "operational"
    }

    # Add more details only in development
    if settings.DEBUG:
        base_info.update({
            "phase": "3 - Production Ready with Security",
            "features": [
                "Comprehensive Input Validation",
                "Rate Limiting Protection",
                "JWT Authentication (Ready)",
                "Security Headers (Active)",
                "Audit Logging (Active)",
                "AI-Powered Auto-Responder",
                "Advanced Rule Engine",
                "Real-time Notifications"
            ],
            "security": {
                "rate_limiting": RATE_LIMITING_AVAILABLE,
                "security_headers": True,
                "input_validation": True,
                "authentication_ready": True
            },
            "docs": "/docs"
        })

    return base_info


@app.get("/health")
async def health_check():
    """Health check endpoint with security status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-secured",
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
                    "error": "Connection failed"  # Don't expose error details
                }
                health_status["status"] = "degraded"

        # Security status (only in debug mode)
        if settings.DEBUG:
            health_status["security"] = {
                "rate_limiting": "enabled" if RATE_LIMITING_AVAILABLE else "disabled",
                "security_headers": "enabled",
                "authentication": "ready",
                "audit_logging": "enabled"
            }

        # Check feature flags
        health_status["features"] = {
            "auto_responder": settings.AUTO_RESPONDER_ENABLED,
            "rule_engine": settings.RULE_ENGINE_ENABLED,
            "notifications": settings.ENABLE_REAL_TIME_NOTIFICATIONS,
            "advanced_analytics": settings.ENABLE_ADVANCED_ANALYTICS,
            "ab_testing": settings.ENABLE_AB_TESTING
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Health check failed",
                "message": "Service temporarily unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/system/info")
async def system_info():
    """Get system information (restricted in production)."""
    if settings.ENVIRONMENT == "production" and not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="System information not available in production"
        )

    try:
        from app.services.scheduler import scheduler_service
        from app.services.notification_service import notification_service

        return {
            "system": {
                "name": "CraigLeads Pro - Secured",
                "version": "2.0.0-secured",
                "environment": settings.ENVIRONMENT,
                "debug_mode": settings.DEBUG
            },
            "security": {
                "rate_limiting": RATE_LIMITING_AVAILABLE,
                "security_headers": True,
                "input_validation": True,
                "authentication_configured": bool(settings.SECRET_KEY),
                "cors_configured": True
            },
            "database": {
                "configured": bool(settings.DATABASE_URL),
                "pool_size": settings.DATABASE_POOL_SIZE
            },
            "features": {
                "ai_provider": settings.AI_PROVIDER,
                "auto_responder": settings.AUTO_RESPONDER_ENABLED,
                "rule_engine": settings.RULE_ENGINE_ENABLED,
                "notifications": settings.ENABLE_REAL_TIME_NOTIFICATIONS
            },
            "limits": {
                "export_max_records": settings.EXPORT_MAX_RECORDS,
                "concurrent_requests": settings.MAX_CONCURRENT_REQUESTS,
                "response_timeout": settings.RESPONSE_TIMEOUT,
                "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system information")


if __name__ == "__main__":
    import uvicorn

    # Security warning for development mode
    if settings.DEBUG:
        logger.warning("⚠️  Running in DEBUG mode - NOT suitable for production!")
        logger.warning("⚠️  Ensure all security settings are configured for production deployment")

    uvicorn.run(
        "main_secured:app",
        host="127.0.0.1" if settings.DEBUG else "0.0.0.0",  # Localhost only in debug
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level=settings.LOG_LEVEL.lower()
    )