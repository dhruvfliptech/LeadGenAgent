"""
N8N Workflow Approval System for Human-in-the-Loop Decision Making.

This service manages approval workflows for various n8n automation tasks:
- Demo site reviews
- Video content reviews
- Email content reviews
- Improvement plan reviews
"""

import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.orm import joinedload

from app.models.approvals import ResponseApproval, ApprovalRule, ApprovalQueue
from app.models.leads import Lead
from app.models.demo_sites import DemoSite
from app.models.composed_videos import ComposedVideo
from app.models.n8n_workflows import WorkflowExecution
from app.core.config import settings
from app.core.url_validator import URLValidator, URLSecurityError
from app.core.logging_config import get_logger
from app.exceptions import (
    ApprovalNotFoundException,
    ApprovalAlreadyProcessedException,
    ApprovalTimeoutException,
    ApprovalValidationException,
    WorkflowWebhookException,
    DatabaseException,
)

logger = get_logger(__name__)


class ApprovalType(str, Enum):
    """Types of approvals supported by the system."""
    DEMO_SITE_REVIEW = "demo_site_review"
    VIDEO_REVIEW = "video_review"
    EMAIL_CONTENT_REVIEW = "email_content_review"
    IMPROVEMENT_PLAN_REVIEW = "improvement_plan_review"
    LEAD_QUALIFICATION = "lead_qualification"
    CAMPAIGN_LAUNCH = "campaign_launch"
    BUDGET_APPROVAL = "budget_approval"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class ApprovalSystem:
    """
    Comprehensive Human-in-the-Loop Approval System.

    Manages workflow pauses for human review and decision making,
    integrating with n8n workflows via webhooks.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.n8n_base_url = settings.N8N_WEBHOOK_URL

    async def create_approval_request(
        self,
        approval_type: ApprovalType,
        resource_id: int,
        resource_data: Dict[str, Any],
        workflow_execution_id: str,
        timeout_minutes: int = 60,
        approvers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        resume_webhook_url: Optional[str] = None
    ) -> int:
        """
        Create an approval request and pause the workflow.

        Args:
            approval_type: Type of approval needed
            resource_id: ID of resource being approved (lead_id, demo_site_id, etc.)
            resource_data: Preview data for reviewer
            workflow_execution_id: n8n execution ID to resume
            timeout_minutes: Minutes before auto-timeout
            approvers: List of approver email addresses
            metadata: Additional context
            resume_webhook_url: Webhook to call when decision is made

        Returns:
            approval_id: ID of created approval request
        """

        logger.info(
            f"Creating approval request: type={approval_type}, "
            f"resource_id={resource_id}, workflow={workflow_execution_id}"
        )

        # Determine resource type
        resource_type = self._get_resource_type(approval_type)

        # Calculate timeout
        timeout_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        # Get default approvers if not specified
        if not approvers:
            approvers = await self._get_default_approvers(approval_type)

        # Build webhook URL if not provided
        if not resume_webhook_url and self.n8n_base_url:
            resume_webhook_url = f"{self.n8n_base_url}/workflow-resume/{workflow_execution_id}"

        # Validate webhook URL to prevent SSRF
        if resume_webhook_url:
            from app.core.security_config import get_webhook_allowed_domains
            validator = URLValidator(
                allowed_domains=get_webhook_allowed_domains(),
                allow_private_ips=False,
                strict_mode=True
            )
            try:
                resume_webhook_url = validator.validate_webhook_url(resume_webhook_url)
            except URLSecurityError as e:
                logger.error(f"Invalid webhook URL: {e}")
                raise ValueError(f"Invalid webhook URL: {str(e)}")

        # Check for auto-approval rules
        auto_approve_result = await self._check_auto_approval_rules(
            approval_type,
            resource_data,
            metadata or {}
        )

        initial_status = "approved" if auto_approve_result['auto_approve'] else "pending"

        # Create approval record
        approval = ResponseApproval(
            approval_type=str(approval_type.value),
            resource_id=resource_id,
            resource_type=resource_type,
            resource_data=resource_data,
            workflow_execution_id=workflow_execution_id,
            workflow_webhook_url=resume_webhook_url,
            status=initial_status,
            timeout_at=timeout_at,
            metadata=metadata or {},
            auto_approval_score=auto_approve_result.get('score'),
            auto_approval_reason=auto_approve_result.get('reason')
        )

        if auto_approve_result['auto_approve']:
            approval.approval_method = "auto"
            approval.approved = True
            approval.decided_at = datetime.utcnow()
            approval.reviewer_comments = auto_approve_result['reason']

            logger.info(
                f"Auto-approved: {approval_type} for resource {resource_id} - "
                f"{auto_approve_result['reason']}"
            )

        self.db.add(approval)
        await self.db.flush()

        # Add to approval history
        await self._add_history_entry(
            approval.id,
            "created",
            "system",
            {
                "approval_type": approval_type.value,
                "auto_approved": auto_approve_result['auto_approve'],
                "timeout_minutes": timeout_minutes
            }
        )

        # Add to queue if pending
        if approval.status == "pending":
            await self._add_to_queue(approval, approvers, metadata)

            # Send notifications
            await self._send_approval_notifications(approval, approvers, resource_data)
        else:
            # Auto-approved - trigger webhook immediately
            await self._trigger_resume_webhook(approval, auto_approved=True)

        await self.db.commit()
        await self.db.refresh(approval)

        logger.info(f"Approval request created: ID={approval.id}, status={approval.status}")

        return approval.id

    def _get_resource_type(self, approval_type: ApprovalType) -> str:
        """Map approval type to resource type."""
        mapping = {
            ApprovalType.DEMO_SITE_REVIEW: "demo_site",
            ApprovalType.VIDEO_REVIEW: "composed_video",
            ApprovalType.EMAIL_CONTENT_REVIEW: "email_template",
            ApprovalType.IMPROVEMENT_PLAN_REVIEW: "improvement_plan",
            ApprovalType.LEAD_QUALIFICATION: "lead",
            ApprovalType.CAMPAIGN_LAUNCH: "campaign",
            ApprovalType.BUDGET_APPROVAL: "budget"
        }
        return mapping.get(approval_type, "generic")

    async def _get_default_approvers(self, approval_type: ApprovalType) -> List[str]:
        """Get default approvers for an approval type."""

        # Query approval settings
        query = select(ApprovalRule).where(
            and_(
                ApprovalRule.is_active == True,
                ApprovalRule.template_types.contains([approval_type.value])
            )
        ).order_by(ApprovalRule.priority.desc())

        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if rule and rule.slack_channels:
            return rule.slack_channels

        # Fallback to environment setting
        default_approver = getattr(settings, 'DEFAULT_APPROVER_EMAIL', 'admin@example.com')
        return [default_approver]

    async def _check_auto_approval_rules(
        self,
        approval_type: ApprovalType,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if this approval qualifies for auto-approval.

        Returns:
            Dict with keys: auto_approve (bool), score (float), reason (str)
        """

        # Get active auto-approval rules
        query = select(ApprovalRule).where(
            and_(
                ApprovalRule.is_active == True,
                ApprovalRule.auto_approve == True
            )
        ).order_by(ApprovalRule.priority.desc())

        result = await self.db.execute(query)
        rules = result.scalars().all()

        for rule in rules:
            # Check if rule applies to this approval type
            if rule.template_types and approval_type.value not in rule.template_types:
                continue

            # Evaluate rule conditions
            score = self._calculate_approval_score(resource_data, metadata, rule)

            if score >= rule.auto_approve_threshold:
                rule.times_triggered += 1
                rule.auto_approved_count += 1

                return {
                    'auto_approve': True,
                    'score': score,
                    'reason': f"Auto-approved by rule '{rule.name}' (score: {score:.2f})",
                    'rule_id': rule.id
                }

        return {
            'auto_approve': False,
            'score': 0.0,
            'reason': None
        }

    def _calculate_approval_score(
        self,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any],
        rule: ApprovalRule
    ) -> float:
        """Calculate approval score based on resource data and rule criteria."""

        score = 0.0
        factors = 0

        # Quality score (if available)
        if 'quality_score' in resource_data:
            score += resource_data['quality_score'] * 0.4
            factors += 0.4

        # Qualification score (for lead-related approvals)
        if 'qualification_score' in resource_data:
            if rule.min_qualification_score:
                if resource_data['qualification_score'] >= rule.min_qualification_score:
                    score += 0.3
                    factors += 0.3

        # Completeness score
        if 'completeness' in metadata:
            score += metadata['completeness'] * 0.2
            factors += 0.2

        # Historical success rate
        if 'success_rate' in metadata:
            score += metadata['success_rate'] * 0.1
            factors += 0.1

        # Normalize
        if factors > 0:
            score = score / factors

        return min(1.0, score)

    async def _add_to_queue(
        self,
        approval: ResponseApproval,
        approvers: List[str],
        metadata: Optional[Dict[str, Any]]
    ):
        """Add approval to the queue."""

        priority = metadata.get('priority', 'normal') if metadata else 'normal'

        # Calculate SLA based on priority
        sla_hours = {
            'urgent': 1,
            'high': 4,
            'normal': 24,
            'low': 48
        }

        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(priority, 24))

        # Assign to first approver
        assigned_to = approvers[0] if approvers else None

        queue_entry = ApprovalQueue(
            approval_id=approval.id,
            priority=priority,
            assigned_to=assigned_to,
            assigned_at=datetime.utcnow() if assigned_to else None,
            sla_deadline=sla_deadline,
            sla_status='on_track',
            status='queued'
        )

        self.db.add(queue_entry)

    async def _add_history_entry(
        self,
        approval_id: int,
        action: str,
        actor_email: str,
        action_data: Dict[str, Any]
    ):
        """Add entry to approval history."""

        from app.models.approvals import ApprovalHistory

        history = ApprovalHistory(
            approval_request_id=approval_id,
            action=action,
            actor_email=actor_email,
            action_data=action_data
        )

        self.db.add(history)

    async def submit_decision(
        self,
        approval_id: int,
        approved: bool,
        reviewer_email: str,
        comments: Optional[str] = None,
        modified_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit approval decision and resume workflow.

        Args:
            approval_id: ID of approval request
            approved: True to approve, False to reject
            reviewer_email: Email of reviewer
            comments: Optional reviewer comments
            modified_data: Optional modifications to resource data

        Returns:
            Dict with decision results and webhook response
        """

        # Get approval
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await self.db.execute(query)
        approval = result.scalar_one_or_none()

        if not approval:
            logger.warning(f"Approval not found for decision submission: {approval_id}")
            raise ApprovalNotFoundException(approval_id)

        if approval.status != "pending":
            logger.warning(f"Approval {approval_id} already processed with status: {approval.status}")
            raise ApprovalAlreadyProcessedException(
                approval_id,
                approval.status,
                details={
                    "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                    "reviewer_email": approval.reviewer_email
                }
            )

        # Check if timed out
        if approval.timeout_at and datetime.utcnow() > approval.timeout_at:
            approval.status = "timeout"
            await self.db.commit()
            logger.warning(f"Approval {approval_id} has timed out")
            raise ApprovalTimeoutException(
                approval_id,
                timeout_at=approval.timeout_at.isoformat() if approval.timeout_at else None
            )

        # Update approval
        approval.status = "approved" if approved else "rejected"
        approval.approved = approved
        approval.reviewer_email = reviewer_email
        approval.reviewer_comments = comments
        approval.decided_at = datetime.utcnow()
        approval.approval_method = "manual"

        # Apply modifications if provided
        if modified_data:
            approval.resource_data.update(modified_data)

        # Update queue
        queue_query = select(ApprovalQueue).where(
            ApprovalQueue.approval_id == approval_id
        )
        queue_result = await self.db.execute(queue_query)
        queue_entry = queue_result.scalar_one_or_none()

        if queue_entry:
            queue_entry.status = "completed"
            queue_entry.completed_at = datetime.utcnow()

        # Add history
        await self._add_history_entry(
            approval_id,
            "approved" if approved else "rejected",
            reviewer_email,
            {
                "comments": comments,
                "had_modifications": bool(modified_data)
            }
        )

        await self.db.commit()

        # Trigger webhook to resume n8n workflow
        webhook_response = await self._trigger_resume_webhook(approval, approved)

        logger.info(
            f"Approval {approval_id} {'approved' if approved else 'rejected'} "
            f"by {reviewer_email}"
        )

        return {
            'success': True,
            'approval_id': approval_id,
            'status': approval.status,
            'approved': approved,
            'webhook_triggered': webhook_response is not None,
            'webhook_response': webhook_response
        }

    async def _trigger_resume_webhook(
        self,
        approval: ResponseApproval,
        approved: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Trigger n8n webhook to resume workflow."""

        if not approval.workflow_webhook_url:
            logger.warning(
                f"No webhook URL for approval {approval.id}, skipping webhook trigger"
            )
            return None

        # Validate webhook URL before making the request (defense in depth)
        from app.core.security_config import get_webhook_allowed_domains
        validator = URLValidator(
            allowed_domains=get_webhook_allowed_domains(),
            allow_private_ips=False,
            strict_mode=True
        )
        try:
            validated_url = validator.validate_webhook_url(approval.workflow_webhook_url)
        except URLSecurityError as e:
            error_msg = f"Blocked unsafe webhook URL for approval {approval.id}: {str(e)}"
            logger.error(error_msg, approval_id=approval.id, webhook_url=approval.workflow_webhook_url)
            raise WorkflowWebhookException(
                message="Webhook URL failed security validation",
                webhook_url=approval.workflow_webhook_url,
                details={"security_error": str(e)}
            )

        if approved is None:
            approved = approval.approved

        payload = {
            'approval_id': approval.id,
            'workflow_execution_id': approval.workflow_execution_id,
            'approved': approved,
            'status': approval.status,
            'approval_type': approval.approval_type,
            'resource_id': approval.resource_id,
            'resource_type': approval.resource_type,
            'resource_data': approval.resource_data,
            'reviewer_email': approval.reviewer_email,
            'reviewer_comments': approval.reviewer_comments,
            'decided_at': approval.decided_at.isoformat() if approval.decided_at else None,
            'metadata': approval.metadata
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    validated_url,  # Use the validated URL
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_data = await response.json()

                    logger.info(
                        f"Webhook triggered for approval {approval.id}: "
                        f"status={response.status}"
                    )

                    return {
                        'status_code': response.status,
                        'response': response_data
                    }
        except aiohttp.ClientError as e:
            logger.error(
                f"Webhook request failed for approval {approval.id}: {str(e)}",
                exc_info=e,
                approval_id=approval.id,
                webhook_url=validated_url
            )
            raise WorkflowWebhookException(
                message=f"Failed to trigger webhook: {str(e)}",
                webhook_url=validated_url,
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(
                f"Unexpected error triggering webhook for approval {approval.id}: {str(e)}",
                exc_info=e,
                approval_id=approval.id
            )
            return {
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def _send_approval_notifications(
        self,
        approval: ResponseApproval,
        approvers: List[str],
        resource_data: Dict[str, Any]
    ):
        """Send notifications to approvers."""

        # Email notification
        if getattr(settings, 'ENABLE_EMAIL_NOTIFICATIONS', False):
            await self._send_email_notification(approval, approvers, resource_data)

        # Slack notification
        if getattr(settings, 'ENABLE_SLACK_NOTIFICATIONS', False):
            await self._send_slack_notification(approval, approvers, resource_data)

    async def _send_email_notification(
        self,
        approval: ResponseApproval,
        approvers: List[str],
        resource_data: Dict[str, Any]
    ):
        """Send email notification to approvers."""

        try:
            from app.services.notification_service import NotificationService

            notification_service = NotificationService(self.db)

            for approver_email in approvers:
                await notification_service.send_email(
                    to_email=approver_email,
                    subject=f"Approval Required: {approval.approval_type}",
                    template_name="approval_request",
                    template_data={
                        'approval_id': approval.id,
                        'approval_type': approval.approval_type,
                        'resource_data': resource_data,
                        'timeout_at': approval.timeout_at.isoformat() if approval.timeout_at else None,
                        'preview_url': resource_data.get('preview_url'),
                        'approve_url': f"{settings.FRONTEND_URL}/approvals/{approval.id}/approve",
                        'reject_url': f"{settings.FRONTEND_URL}/approvals/{approval.id}/reject"
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    async def _send_slack_notification(
        self,
        approval: ResponseApproval,
        approvers: List[str],
        resource_data: Dict[str, Any]
    ):
        """Send Slack notification to approvers."""

        try:
            from app.integrations.slack_approvals import SlackApprovalNotifier

            slack = SlackApprovalNotifier()

            await slack.send_approval_request(
                approval_id=approval.id,
                approval_data={
                    'type': approval.approval_type,
                    'description': resource_data.get('description', ''),
                    'preview_url': resource_data.get('preview_url'),
                    'timeout_at': approval.timeout_at
                },
                channel=approvers[0] if approvers else "#approvals"
            )
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def get_pending_approvals(
        self,
        approver_email: Optional[str] = None,
        approval_type: Optional[ApprovalType] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all pending approvals, optionally filtered."""

        query = select(ResponseApproval).where(
            ResponseApproval.status == "pending"
        )

        if approver_email:
            query = query.join(ApprovalQueue).where(
                ApprovalQueue.assigned_to == approver_email
            )

        if approval_type:
            query = query.where(
                ResponseApproval.approval_type == approval_type.value
            )

        query = query.order_by(
            ResponseApproval.timeout_at.asc()
        ).limit(limit)

        result = await self.db.execute(query)
        approvals = result.scalars().all()

        return [self._format_approval(approval) for approval in approvals]

    def _format_approval(self, approval: ResponseApproval) -> Dict[str, Any]:
        """Format approval for API response."""

        return {
            'id': approval.id,
            'approval_type': approval.approval_type,
            'resource_id': approval.resource_id,
            'resource_type': approval.resource_type,
            'resource_data': approval.resource_data,
            'status': approval.status,
            'created_at': approval.created_at.isoformat() if approval.created_at else None,
            'timeout_at': approval.timeout_at.isoformat() if approval.timeout_at else None,
            'metadata': approval.metadata,
            'workflow_execution_id': approval.workflow_execution_id
        }

    async def check_timeouts(self):
        """Background task to check for timed out approvals."""

        logger.info("Checking for timed out approvals...")

        query = select(ResponseApproval).where(
            and_(
                ResponseApproval.status == "pending",
                ResponseApproval.timeout_at <= datetime.utcnow()
            )
        )

        result = await self.db.execute(query)
        timed_out = result.scalars().all()

        for approval in timed_out:
            approval.status = "timeout"
            approval.decided_at = datetime.utcnow()

            await self._add_history_entry(
                approval.id,
                "timeout",
                "system",
                {'reason': 'Approval request timed out'}
            )

            # Trigger webhook with timeout status
            await self._trigger_resume_webhook(approval, approved=False)

            logger.warning(f"Approval {approval.id} timed out")

        if timed_out:
            await self.db.commit()

        logger.info(f"Processed {len(timed_out)} timed out approvals")

        return len(timed_out)

    async def escalate_approval(
        self,
        approval_id: int,
        escalation_level: int = 1,
        escalated_to: Optional[str] = None
    ):
        """Escalate approval to higher authority."""

        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await self.db.execute(query)
        approval = result.scalar_one_or_none()

        if not approval:
            logger.warning(f"Approval not found for escalation: {approval_id}")
            raise ApprovalNotFoundException(approval_id)

        if approval.status != "pending":
            logger.warning(f"Cannot escalate non-pending approval {approval_id} with status: {approval.status}")
            raise ApprovalAlreadyProcessedException(
                approval_id,
                approval.status,
                details={"operation": "escalate"}
            )

        approval.escalation_level = escalation_level
        approval.escalated_to = escalated_to
        approval.status = "escalated"

        await self._add_history_entry(
            approval_id,
            "escalated",
            "system",
            {
                'escalation_level': escalation_level,
                'escalated_to': escalated_to
            }
        )

        await self.db.commit()

        logger.info(
            f"Approval {approval_id} escalated to level {escalation_level}"
        )

    async def bulk_approve(
        self,
        approval_ids: List[int],
        reviewer_email: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve multiple requests at once."""

        results = {
            'approved': [],
            'failed': []
        }

        for approval_id in approval_ids:
            try:
                result = await self.submit_decision(
                    approval_id=approval_id,
                    approved=True,
                    reviewer_email=reviewer_email,
                    comments=comments or "Bulk approved"
                )
                results['approved'].append(approval_id)
            except Exception as e:
                results['failed'].append({
                    'approval_id': approval_id,
                    'error': str(e)
                })
                logger.error(f"Failed to bulk approve {approval_id}: {e}")

        logger.info(
            f"Bulk approval by {reviewer_email}: "
            f"{len(results['approved'])} approved, {len(results['failed'])} failed"
        )

        return results

    async def get_approval_statistics(self) -> Dict[str, Any]:
        """Get approval system statistics."""

        # Count by status
        status_query = select(
            ResponseApproval.status,
            func.count(ResponseApproval.id)
        ).group_by(ResponseApproval.status)

        status_result = await self.db.execute(status_query)
        status_counts = dict(status_result.all())

        # Count by type
        type_query = select(
            ResponseApproval.approval_type,
            func.count(ResponseApproval.id)
        ).group_by(ResponseApproval.approval_type)

        type_result = await self.db.execute(type_query)
        type_counts = dict(type_result.all())

        # Average decision time
        avg_time_query = select(
            func.avg(
                func.extract('epoch', ResponseApproval.decided_at - ResponseApproval.created_at)
            )
        ).where(ResponseApproval.decided_at.isnot(None))

        avg_time_result = await self.db.execute(avg_time_query)
        avg_decision_seconds = avg_time_result.scalar()

        # Auto-approval rate
        auto_approved_query = select(func.count(ResponseApproval.id)).where(
            ResponseApproval.approval_method == "auto"
        )
        auto_approved_result = await self.db.execute(auto_approved_query)
        auto_approved_count = auto_approved_result.scalar()

        total_query = select(func.count(ResponseApproval.id))
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar()

        return {
            'by_status': status_counts,
            'by_type': type_counts,
            'total_approvals': total_count,
            'auto_approved_count': auto_approved_count,
            'auto_approval_rate': auto_approved_count / total_count if total_count > 0 else 0,
            'avg_decision_time_minutes': avg_decision_seconds / 60 if avg_decision_seconds else 0
        }
