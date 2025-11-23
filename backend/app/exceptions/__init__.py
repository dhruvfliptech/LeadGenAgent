"""
Custom exception classes for structured error handling.

This module provides domain-specific exceptions that map to appropriate
HTTP status codes and provide detailed error information.
"""

from typing import Any, Dict, Optional

from fastapi import status


class BaseAppException(Exception):
    """Base exception for all application exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


# Approval System Exceptions

class ApprovalNotFoundException(BaseAppException):
    """Raised when an approval request is not found."""

    def __init__(self, approval_id: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Approval with ID {approval_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"approval_id": approval_id},
            error_code="APPROVAL_NOT_FOUND"
        )
        self.approval_id = approval_id


class ApprovalAlreadyProcessedException(BaseAppException):
    """Raised when attempting to process an already-processed approval."""

    def __init__(
        self,
        approval_id: int,
        current_status: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Approval {approval_id} has already been processed (status: {current_status})",
            status_code=status.HTTP_409_CONFLICT,
            details=details or {
                "approval_id": approval_id,
                "current_status": current_status
            },
            error_code="APPROVAL_ALREADY_PROCESSED"
        )
        self.approval_id = approval_id
        self.current_status = current_status


class ApprovalTimeoutException(BaseAppException):
    """Raised when an approval request has timed out."""

    def __init__(
        self,
        approval_id: int,
        timeout_at: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Approval {approval_id} has timed out",
            status_code=status.HTTP_410_GONE,
            details=details or {
                "approval_id": approval_id,
                "timeout_at": timeout_at
            },
            error_code="APPROVAL_TIMEOUT"
        )
        self.approval_id = approval_id
        self.timeout_at = timeout_at


class ApprovalValidationException(BaseAppException):
    """Raised when approval data fails validation."""

    def __init__(
        self,
        message: str,
        validation_errors: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {"validation_errors": validation_errors or {}},
            error_code="APPROVAL_VALIDATION_ERROR"
        )
        self.validation_errors = validation_errors


# Template Exceptions

class TemplateNotFoundException(BaseAppException):
    """Raised when a template is not found."""

    def __init__(self, template_id: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Template with ID {template_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"template_id": template_id},
            error_code="TEMPLATE_NOT_FOUND"
        )
        self.template_id = template_id


class TemplateValidationException(BaseAppException):
    """Raised when template content fails validation."""

    def __init__(
        self,
        message: str,
        template_id: Optional[int] = None,
        field: Optional[str] = None,
        validation_errors: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {
                "template_id": template_id,
                "field": field,
                "validation_errors": validation_errors or {}
            },
            error_code="TEMPLATE_VALIDATION_ERROR"
        )
        self.template_id = template_id
        self.field = field
        self.validation_errors = validation_errors


class TemplateSecurityException(BaseAppException):
    """Raised when template contains security violations."""

    def __init__(
        self,
        message: str,
        template_id: Optional[int] = None,
        security_issues: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {
                "template_id": template_id,
                "security_issues": security_issues or []
            },
            error_code="TEMPLATE_SECURITY_VIOLATION"
        )
        self.template_id = template_id
        self.security_issues = security_issues


class TemplateInUseException(BaseAppException):
    """Raised when attempting to delete a template that is in use."""

    def __init__(
        self,
        template_id: int,
        active_count: int,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Cannot delete template {template_id} with {active_count} active responses",
            status_code=status.HTTP_409_CONFLICT,
            details=details or {
                "template_id": template_id,
                "active_responses": active_count
            },
            error_code="TEMPLATE_IN_USE"
        )
        self.template_id = template_id
        self.active_count = active_count


# Workflow Exceptions

class WorkflowExecutionException(BaseAppException):
    """Raised when workflow execution fails."""

    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "error_details": error_details or {}
            },
            error_code="WORKFLOW_EXECUTION_ERROR"
        )
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.error_details = error_details


class WorkflowWebhookException(BaseAppException):
    """Raised when webhook communication fails."""

    def __init__(
        self,
        message: str,
        webhook_url: Optional[str] = None,
        status_code_received: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details or {
                "webhook_url": webhook_url,
                "status_code": status_code_received,
                "response": response_data
            },
            error_code="WORKFLOW_WEBHOOK_ERROR"
        )
        self.webhook_url = webhook_url
        self.status_code_received = status_code_received
        self.response_data = response_data


# Rate Limiting Exceptions

class RateLimitExceededException(BaseAppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details or {
                "limit": limit,
                "window": window,
                "retry_after": retry_after
            },
            error_code="RATE_LIMIT_EXCEEDED"
        )
        self.limit = limit
        self.window = window
        self.retry_after = retry_after


# Database Exceptions

class DatabaseException(BaseAppException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {"operation": operation},
            error_code="DATABASE_ERROR"
        )
        self.operation = operation


class ResourceNotFoundException(BaseAppException):
    """Raised when a generic resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            error_code="RESOURCE_NOT_FOUND"
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


# External Service Exceptions

class ExternalServiceException(BaseAppException):
    """Raised when external service communication fails."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code_received: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details or {
                "service": service_name,
                "status_code": status_code_received
            },
            error_code="EXTERNAL_SERVICE_ERROR"
        )
        self.service_name = service_name
        self.status_code_received = status_code_received


# Authentication/Authorization Exceptions

class AuthenticationException(BaseAppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(BaseAppException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details or {"required_permission": required_permission},
            error_code="AUTHORIZATION_ERROR"
        )
        self.required_permission = required_permission


# Export all custom exceptions
__all__ = [
    "BaseAppException",
    "ApprovalNotFoundException",
    "ApprovalAlreadyProcessedException",
    "ApprovalTimeoutException",
    "ApprovalValidationException",
    "TemplateNotFoundException",
    "TemplateValidationException",
    "TemplateSecurityException",
    "TemplateInUseException",
    "WorkflowExecutionException",
    "WorkflowWebhookException",
    "RateLimitExceededException",
    "DatabaseException",
    "ResourceNotFoundException",
    "ExternalServiceException",
    "AuthenticationException",
    "AuthorizationException",
]
