"""
Structured logging configuration with context tracking and audit trail.

Provides comprehensive logging with request IDs, user tracking, and
performance monitoring.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


# Context variables for request tracking
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
user_email_ctx: ContextVar[Optional[str]] = ContextVar("user_email", default=None)


class ContextFilter(logging.Filter):
    """Add context variables to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        record.user_id = user_id_ctx.get()
        record.user_email = user_email_ctx.get()
        return True


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context data
        if hasattr(record, "request_id") and record.request_id:
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id") and record.user_id:
            log_data["user_id"] = record.user_id
        if hasattr(record, "user_email") and record.user_email:
            log_data["user_email"] = record.user_email

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add any extra fields passed to the logger
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Format logs with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )

        # Build log message
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] {record.levelname} [{record.name}] {record.getMessage()}"

        # Add context if available
        context_parts = []
        if hasattr(record, "request_id") and record.request_id:
            context_parts.append(f"req={record.request_id}")
        if hasattr(record, "user_email") and record.user_email:
            context_parts.append(f"user={record.user_email}")

        if context_parts:
            message += f" [{', '.join(context_parts)}]"

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


class StructuredLogger:
    """Wrapper for structured logging with context."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log_with_context(
        self,
        level: int,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log with structured context data."""
        extra = {"extra_data": extra_data} if extra_data else {}
        self.logger.log(level, message, extra=extra, exc_info=exc_info)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log error message with context and exception."""
        self._log_with_context(logging.ERROR, message, kwargs, exc_info=exc_info)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log critical message with context and exception."""
        self._log_with_context(logging.CRITICAL, message, kwargs, exc_info=exc_info)

    def audit(self, action: str, resource_type: str, resource_id: Any, **kwargs):
        """Log audit trail for user actions."""
        audit_data = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_email": user_email_ctx.get(),
            "user_id": user_id_ctx.get(),
            "request_id": request_id_ctx.get(),
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }
        self.info(f"AUDIT: {action} on {resource_type} {resource_id}", **audit_data)

    def performance(
        self,
        operation: str,
        duration_seconds: float,
        success: bool = True,
        **kwargs,
    ):
        """Log performance metrics."""
        perf_data = {
            "operation": operation,
            "duration_seconds": round(duration_seconds, 3),
            "success": success,
            **kwargs,
        }

        # Warn if operation is slow
        if duration_seconds > 1.0:
            self.warning(
                f"PERFORMANCE: Slow operation {operation} took {duration_seconds:.3f}s",
                **perf_data,
            )
        else:
            self.info(
                f"PERFORMANCE: {operation} completed in {duration_seconds:.3f}s",
                **perf_data,
            )


def setup_logging():
    """Configure application logging."""

    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper())

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addFilter(ContextFilter())

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler (colored for development, JSON for production)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)

    # File handlers for production
    if settings.ENVIRONMENT == "production":
        # General application log
        app_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        app_handler.setFormatter(JSONFormatter())
        app_handler.setLevel(logging.INFO)
        root_logger.addHandler(app_handler)

        # Error log
        error_handler = RotatingFileHandler(
            "logs/error.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)

        # Audit log
        audit_handler = RotatingFileHandler(
            "logs/audit.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,  # Keep more audit logs
        )
        audit_handler.setFormatter(JSONFormatter())
        audit_handler.setLevel(logging.INFO)
        audit_handler.addFilter(lambda record: "AUDIT:" in record.getMessage())
        root_logger.addHandler(audit_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def set_request_context(
    request_id: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
):
    """Set request context for logging."""
    request_id_ctx.set(request_id)
    if user_id:
        user_id_ctx.set(user_id)
    if user_email:
        user_email_ctx.set(user_email)


def clear_request_context():
    """Clear request context."""
    request_id_ctx.set(None)
    user_id_ctx.set(None)
    user_email_ctx.set(None)
