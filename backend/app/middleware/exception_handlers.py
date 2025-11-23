"""
Global exception handlers for structured error responses.

Provides consistent error handling across the application with
proper logging, sanitized error messages, and appropriate HTTP status codes.
"""

from datetime import datetime
from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from pydantic import ValidationError

from app.core.logging_config import get_logger, request_id_ctx
from app.exceptions import BaseAppException

logger = get_logger(__name__)


async def custom_exception_handler(
    request: Request,
    exc: BaseAppException
) -> JSONResponse:
    """
    Handle custom application exceptions.

    Converts custom exceptions to structured JSON responses with
    appropriate status codes and detailed error information.
    """
    request_id = request_id_ctx.get()

    logger.warning(
        f"Application exception: {exc.error_code}",
        error_code=exc.error_code,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        request_id=request_id
    )

    response_data = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        },
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Converts validation errors into user-friendly error responses
    with detailed information about which fields failed validation.
    """
    request_id = request_id_ctx.get()

    errors = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
    else:
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

    logger.warning(
        f"Validation error on {request.url.path}",
        validation_errors=errors,
        path=request.url.path,
        method=request.method,
        request_id=request_id
    )

    response_data = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {
                "validation_errors": errors
            }
        },
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database exceptions.

    Provides sanitized error messages to prevent information leakage
    while logging the full error details for debugging.
    """
    request_id = request_id_ctx.get()

    # Determine error type and message
    if isinstance(exc, IntegrityError):
        error_code = "DATABASE_INTEGRITY_ERROR"
        user_message = "Data integrity constraint violated. Please check your input."
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, OperationalError):
        error_code = "DATABASE_OPERATIONAL_ERROR"
        user_message = "Database operation failed. Please try again later."
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        error_code = "DATABASE_ERROR"
        user_message = "A database error occurred. Please try again later."
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # Log the full error with details
    logger.error(
        f"Database error: {type(exc).__name__}",
        exc_info=exc,
        error_code=error_code,
        path=request.url.path,
        method=request.method,
        request_id=request_id
    )

    # Return sanitized error to client
    response_data = {
        "error": {
            "code": error_code,
            "message": user_message,
            "details": {}
        },
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Provides a generic error response while logging the full
    exception details for investigation.
    """
    request_id = request_id_ctx.get()

    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        request_id=request_id,
        exception_type=type(exc).__name__
    )

    # Don't expose internal error details to clients
    response_data = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        },
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path)
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(BaseAppException, custom_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)

    # Generic exceptions (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
