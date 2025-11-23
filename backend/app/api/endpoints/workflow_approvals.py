"""
API endpoints for n8n workflow approval management.

Enhanced approval system for human-in-the-loop decision making.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_db
from app.core.url_validator import URLValidator, URLSecurityError
from app.core.logging_config import get_logger
from app.core.rate_limiter import (
    approvals_read_limiter,
    approvals_write_limiter,
    approvals_bulk_limiter,
    approvals_rules_write_limiter
)
from app.models.approvals import ResponseApproval, ApprovalRule, ApprovalQueue, ApprovalHistory
from app.services.approval_system import ApprovalSystem, ApprovalType, ApprovalStatus
from app.services.auto_approval import AutoApprovalEngine, AUTO_APPROVAL_RULE_TEMPLATES
from app.exceptions import (
    ApprovalNotFoundException,
    ApprovalAlreadyProcessedException,
    ApprovalTimeoutException,
    ApprovalValidationException,
    DatabaseException,
)

router = APIRouter()
logger = get_logger(__name__)


# Pydantic models for API requests/responses
class CreateApprovalRequest(BaseModel):
    """Request to create an approval."""
    approval_type: str
    resource_id: int
    resource_data: dict
    workflow_execution_id: str
    timeout_minutes: int = Field(default=60, ge=5, le=1440)
    approvers: Optional[List[str]] = None
    metadata: Optional[dict] = None
    resume_webhook_url: Optional[str] = None

    @field_validator('approval_type')
    @classmethod
    def validate_approval_type(cls, v):
        valid_types = [t.value for t in ApprovalType]
        if v not in valid_types:
            raise ValueError(f"Invalid approval type. Must be one of: {', '.join(valid_types)}")
        return v

    @field_validator('resume_webhook_url')
    @classmethod
    def validate_webhook_url(cls, v):
        """Validate webhook URL to prevent SSRF attacks."""
        if v:
            from app.core.security_config import get_webhook_allowed_domains
            # Create validator with allowed webhook domains from config
            validator = URLValidator(
                allowed_domains=get_webhook_allowed_domains(),
                allow_private_ips=False,
                strict_mode=True
            )
            try:
                # Validate and normalize the webhook URL
                return validator.validate_webhook_url(v)
            except URLSecurityError as e:
                raise ValueError(f"Invalid webhook URL: {str(e)}")
        return v


class SubmitDecisionRequest(BaseModel):
    """Request to submit an approval decision."""
    approved: bool
    reviewer_email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    comments: Optional[str] = Field(None, max_length=2000)
    modified_data: Optional[dict] = None


class BulkApprovalRequest(BaseModel):
    """Request to approve multiple items."""
    approval_ids: List[int] = Field(..., min_items=1, max_items=50)
    reviewer_email: str
    comments: Optional[str] = None


class EscalateApprovalRequest(BaseModel):
    """Request to escalate an approval."""
    escalation_level: int = Field(default=1, ge=1, le=5)
    escalated_to: Optional[str] = None
    reason: Optional[str] = None


class AutoApprovalRuleCreate(BaseModel):
    """Request to create an auto-approval rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    approval_types: List[str]
    auto_approve_threshold: float = Field(default=0.85, ge=0.5, le=1.0)
    min_qualification_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    required_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    lead_categories: Optional[List[str]] = None
    priority: int = Field(default=0, ge=0, le=1000)


# API Endpoints

@router.post("/create", status_code=201)
@approvals_write_limiter
async def create_approval_request(
    request: Request,
    approval_request: CreateApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new approval request and pause workflow.

    This endpoint is called by n8n workflows when human approval is required.
    """

    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Creating approval request: {approval_request.approval_type}",
            approval_type=approval_request.approval_type,
            resource_id=approval_request.resource_id,
            workflow_execution_id=approval_request.workflow_execution_id
        )

        approval_system = ApprovalSystem(db)

        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType(approval_request.approval_type),
            resource_id=approval_request.resource_id,
            resource_data=approval_request.resource_data,
            workflow_execution_id=approval_request.workflow_execution_id,
            timeout_minutes=approval_request.timeout_minutes,
            approvers=approval_request.approvers,
            metadata=approval_request.metadata,
            resume_webhook_url=approval_request.resume_webhook_url
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.performance(
            "create_approval_request",
            duration,
            approval_id=approval_id
        )

        logger.audit(
            "approval_created",
            "approval_request",
            approval_id,
            approval_type=approval_request.approval_type,
            resource_id=approval_request.resource_id
        )

        return {
            "success": True,
            "approval_id": approval_id,
            "message": "Approval request created successfully",
            "timeout_minutes": approval_request.timeout_minutes
        }

    except ApprovalValidationException as e:
        logger.warning(f"Approval validation failed: {e.message}", validation_errors=e.details)
        raise
    except DatabaseException as e:
        logger.error(f"Database error creating approval: {e.message}", exc_info=e)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating approval: {str(e)}", exc_info=e)
        raise DatabaseException(
            message="Failed to create approval request",
            operation="create_approval",
            details={"error": str(e)}
        )


@router.get("/pending")
@approvals_read_limiter
async def get_pending_approvals(
    request: Request,
    approver_email: Optional[str] = Query(None),
    approval_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending approvals, optionally filtered by approver or type.
    """

    approval_system = ApprovalSystem(db)

    approval_type_enum = ApprovalType(approval_type) if approval_type else None

    approvals = await approval_system.get_pending_approvals(
        approver_email=approver_email,
        approval_type=approval_type_enum,
        limit=limit
    )

    return {
        "count": len(approvals),
        "approvals": approvals
    }


@router.get("/{approval_id}")
@approvals_read_limiter
async def get_approval_details(
    request: Request,
    approval_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific approval."""
    from sqlalchemy.orm import selectinload

    # Use eager loading to fetch related data in a single query to avoid N+1
    query = (
        select(ResponseApproval)
        .options(
            selectinload(ResponseApproval.lead),  # Eager load lead relationship
            selectinload(ResponseApproval.queue_entry),  # Eager load queue entries
            selectinload(ResponseApproval.history)  # Eager load history entries
        )
        .where(ResponseApproval.id == approval_id)
    )

    result = await db.execute(query)
    approval = result.scalar_one_or_none()

    if not approval:
        logger.warning(f"Approval not found: {approval_id}")
        raise ApprovalNotFoundException(approval_id)

    # History is already loaded via eager loading, just need to sort
    history = sorted(approval.history, key=lambda h: h.created_at, reverse=True)

    # Queue is already loaded via eager loading (queue_entry is a backref to ApprovalQueue)
    queue = approval.queue_entry[0] if approval.queue_entry else None

    return {
        "approval": {
            "id": approval.id,
            "approval_type": approval.approval_type,
            "resource_id": approval.resource_id,
            "resource_type": approval.resource_type,
            "resource_data": approval.resource_data,
            "status": approval.status,
            "workflow_execution_id": approval.workflow_execution_id,
            "created_at": approval.created_at.isoformat() if approval.created_at else None,
            "timeout_at": approval.timeout_at.isoformat() if approval.timeout_at else None,
            "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
            "reviewer_email": approval.reviewer_email,
            "reviewer_comments": approval.reviewer_comments,
            "approved": approval.approved,
            "approval_method": approval.approval_method,
            "auto_approval_score": approval.auto_approval_score,
            "auto_approval_reason": approval.auto_approval_reason,
            "escalation_level": approval.escalation_level,
            "escalated_to": approval.escalated_to,
            "metadata": approval.metadata
        },
        "queue": {
            "priority": queue.priority if queue else None,
            "assigned_to": queue.assigned_to if queue else None,
            "sla_deadline": queue.sla_deadline.isoformat() if queue and queue.sla_deadline else None,
            "sla_status": queue.sla_status if queue else None
        } if queue else None,
        "history": [
            {
                "action": h.action,
                "actor_email": h.actor_email,
                "action_data": h.action_data,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]
    }


@router.post("/{approval_id}/decide")
@approvals_write_limiter
async def submit_decision(
    request: Request,
    approval_id: int,
    decision: SubmitDecisionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit an approval or rejection decision.

    This triggers the n8n webhook to resume the workflow.
    """

    start_time = datetime.utcnow()

    try:
        logger.info(
            f"Submitting decision for approval {approval_id}",
            approval_id=approval_id,
            approved=decision.approved,
            reviewer_email=decision.reviewer_email
        )

        approval_system = ApprovalSystem(db)

        result = await approval_system.submit_decision(
            approval_id=approval_id,
            approved=decision.approved,
            reviewer_email=decision.reviewer_email,
            comments=decision.comments,
            modified_data=decision.modified_data
        )

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.performance(
            "submit_decision",
            duration,
            approval_id=approval_id,
            approved=decision.approved
        )

        logger.audit(
            "decision_submitted",
            "approval_request",
            approval_id,
            approved=decision.approved,
            reviewer_email=decision.reviewer_email
        )

        # Send notification in background
        if result.get('success'):
            background_tasks.add_task(
                _send_decision_notification,
                approval_id,
                decision.approved,
                decision.reviewer_email
            )

        return result

    except (ApprovalNotFoundException, ApprovalAlreadyProcessedException, ApprovalTimeoutException) as e:
        logger.warning(f"Decision submission failed: {e.message}", approval_id=approval_id)
        raise
    except Exception as e:
        logger.error(f"Unexpected error submitting decision: {str(e)}", exc_info=e, approval_id=approval_id)
        raise DatabaseException(
            message="Failed to submit approval decision",
            operation="submit_decision",
            details={"approval_id": approval_id, "error": str(e)}
        )


@router.post("/{approval_id}/escalate")
@approvals_write_limiter
async def escalate_approval(
    request: Request,
    approval_id: int,
    escalate_request: EscalateApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """Escalate an approval to higher authority."""

    try:
        logger.info(
            f"Escalating approval {approval_id}",
            approval_id=approval_id,
            escalation_level=request.escalation_level,
            escalated_to=request.escalated_to
        )

        approval_system = ApprovalSystem(db)

        await approval_system.escalate_approval(
            approval_id=approval_id,
            escalation_level=request.escalation_level,
            escalated_to=request.escalated_to
        )

        logger.audit(
            "approval_escalated",
            "approval_request",
            approval_id,
            escalation_level=request.escalation_level,
            escalated_to=request.escalated_to
        )

        return {
            "success": True,
            "approval_id": approval_id,
            "escalation_level": request.escalation_level,
            "message": "Approval escalated successfully"
        }

    except ApprovalNotFoundException as e:
        logger.warning(f"Escalation failed - approval not found: {approval_id}")
        raise
    except ApprovalAlreadyProcessedException as e:
        logger.warning(f"Escalation failed - approval already processed: {approval_id}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error escalating approval: {str(e)}", exc_info=e, approval_id=approval_id)
        raise DatabaseException(
            message="Failed to escalate approval",
            operation="escalate_approval",
            details={"approval_id": approval_id, "error": str(e)}
        )


@router.post("/bulk-approve")
@approvals_bulk_limiter
async def bulk_approve(
    request: Request,
    bulk_request: BulkApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Approve multiple requests at once."""

    try:
        approval_system = ApprovalSystem(db)

        results = await approval_system.bulk_approve(
            approval_ids=request.approval_ids,
            reviewer_email=request.reviewer_email,
            comments=request.comments
        )

        # Send Slack summary in background
        if results['approved']:
            background_tasks.add_task(
                _send_bulk_approval_notification,
                len(results['approved']),
                request.reviewer_email
            )

        return {
            "success": True,
            "approved_count": len(results['approved']),
            "failed_count": len(results['failed']),
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk approval failed: {str(e)}")


@router.get("/stats")
@approvals_read_limiter
async def get_approval_statistics(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get approval system statistics."""

    approval_system = ApprovalSystem(db)
    stats = await approval_system.get_approval_statistics()

    return stats


@router.post("/check-timeouts")
@approvals_write_limiter
async def check_approval_timeouts(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Background task endpoint to check for timed out approvals.

    Should be called periodically by a cron job or scheduler.
    """

    approval_system = ApprovalSystem(db)
    timed_out_count = await approval_system.check_timeouts()

    return {
        "success": True,
        "timed_out_count": timed_out_count,
        "message": f"Processed {timed_out_count} timed out approvals"
    }


# Auto-Approval Rules Endpoints

@router.get("/auto-approval/rules")
@approvals_read_limiter
async def get_auto_approval_rules(
    request: Request,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get all auto-approval rules."""

    query = select(ApprovalRule).where(
        ApprovalRule.auto_approve == True
    )

    if active_only:
        query = query.where(ApprovalRule.is_active == True)

    query = query.order_by(ApprovalRule.priority.desc())

    result = await db.execute(query)
    rules = result.scalars().all()

    return {
        "count": len(rules),
        "rules": [rule.to_dict() for rule in rules]
    }


@router.post("/auto-approval/rules")
@approvals_rules_write_limiter
async def create_auto_approval_rule(
    request: Request,
    rule: AutoApprovalRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new auto-approval rule."""

    try:
        auto_approval = AutoApprovalEngine(db)

        new_rule = await auto_approval.create_auto_approval_rule(
            name=rule.name,
            description=rule.description,
            approval_types=rule.approval_types,
            auto_approve_threshold=rule.auto_approve_threshold,
            min_qualification_score=rule.min_qualification_score,
            required_keywords=rule.required_keywords,
            excluded_keywords=rule.excluded_keywords,
            lead_categories=rule.lead_categories,
            priority=rule.priority
        )

        return {
            "success": True,
            "rule": new_rule.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")


@router.get("/auto-approval/rules/{rule_id}/performance")
@approvals_read_limiter
async def get_rule_performance(
    request: Request,
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get performance metrics for an auto-approval rule."""

    try:
        auto_approval = AutoApprovalEngine(db)
        performance = await auto_approval.get_rule_performance(rule_id)

        return performance

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/auto-approval/rules/{rule_id}/optimize")
@approvals_rules_write_limiter
async def optimize_rule_threshold(
    request: Request,
    rule_id: int,
    target_approval_rate: float = Query(0.8, ge=0.5, le=0.95),
    db: AsyncSession = Depends(get_db)
):
    """Optimize rule threshold based on historical performance."""

    try:
        auto_approval = AutoApprovalEngine(db)

        optimized_threshold = await auto_approval.optimize_rule_threshold(
            rule_id=rule_id,
            target_approval_rate=target_approval_rate
        )

        # Update the rule with optimized threshold
        query = select(ApprovalRule).where(ApprovalRule.id == rule_id)
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if rule:
            rule.auto_approve_threshold = optimized_threshold
            await db.commit()

        return {
            "success": True,
            "rule_id": rule_id,
            "old_threshold": rule.auto_approve_threshold if rule else None,
            "new_threshold": optimized_threshold,
            "target_approval_rate": target_approval_rate
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/auto-approval/templates")
@approvals_read_limiter
async def get_rule_templates(request: Request):
    """Get predefined auto-approval rule templates."""

    return {
        "count": len(AUTO_APPROVAL_RULE_TEMPLATES),
        "templates": AUTO_APPROVAL_RULE_TEMPLATES
    }


@router.post("/auto-approval/templates/{template_index}/apply")
@approvals_rules_write_limiter
async def apply_rule_template(
    request: Request,
    template_index: int,
    db: AsyncSession = Depends(get_db)
):
    """Apply a predefined rule template."""

    if template_index < 0 or template_index >= len(AUTO_APPROVAL_RULE_TEMPLATES):
        raise HTTPException(status_code=404, detail="Template not found")

    template = AUTO_APPROVAL_RULE_TEMPLATES[template_index]

    try:
        auto_approval = AutoApprovalEngine(db)

        rule = await auto_approval.create_auto_approval_rule(
            name=template['name'],
            description=template['description'],
            approval_types=template['approval_types'],
            auto_approve_threshold=template['auto_approve_threshold'],
            min_qualification_score=template.get('min_qualification_score'),
            required_keywords=template.get('required_keywords'),
            excluded_keywords=template.get('excluded_keywords'),
            lead_categories=template.get('lead_categories'),
            priority=template['priority']
        )

        return {
            "success": True,
            "message": f"Applied template: {template['name']}",
            "rule": rule.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply template: {str(e)}")


# Background task helpers

async def _send_decision_notification(
    approval_id: int,
    approved: bool,
    reviewer_email: str
):
    """Send notification after approval decision (background task)."""
    try:
        from app.integrations.slack_approvals import SlackApprovalNotifier

        logger.debug(
            f"Sending decision notification for approval {approval_id}",
            approval_id=approval_id,
            approved=approved,
            reviewer_email=reviewer_email
        )

        slack = SlackApprovalNotifier()
        # Note: Would need to store Slack message_ts in approval record
        # await slack.update_approval_message(...)

    except Exception as e:
        logger.error(
            f"Failed to send decision notification: {str(e)}",
            exc_info=e,
            approval_id=approval_id
        )


async def _send_bulk_approval_notification(
    count: int,
    reviewer_email: str
):
    """Send notification for bulk approval (background task)."""
    try:
        logger.debug(
            f"Sending bulk approval notification",
            count=count,
            reviewer_email=reviewer_email
        )

        from app.integrations.slack_approvals import SlackApprovalNotifier

        slack = SlackApprovalNotifier()
        await slack.send_bulk_approval_summary(
            approvals_count=count,
            reviewer=reviewer_email,
            channel="#approvals"
        )

    except Exception as e:
        logger.error(
            f"Failed to send bulk approval notification: {str(e)}",
            exc_info=e,
            count=count,
            reviewer_email=reviewer_email
        )
