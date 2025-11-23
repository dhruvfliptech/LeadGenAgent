"""
Approval System Service

Manages workflow approval requests including creation, approval/rejection,
expiration handling, and bulk actions.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.n8n_workflows import (
    WorkflowApproval,
    WorkflowExecution,
    ApprovalStatus,
    ApprovalPriority
)
from .auto_approval import AutoApprovalService

logger = logging.getLogger(__name__)


class ApprovalSystem:
    """
    Approval System

    Manages approval workflows for sensitive or high-value operations.
    """

    def __init__(self, db: Session):
        """Initialize approval system"""
        self.db = db
        self.auto_approval = AutoApprovalService(db)

    async def create_approval_request(
        self,
        execution_id: int,
        approval_type: str,
        approval_title: str,
        approval_description: Optional[str] = None,
        approval_data: Optional[Dict[str, Any]] = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        requires_manual: bool = False,
        auto_approval_enabled: bool = True,
        expires_in_hours: int = 24
    ) -> WorkflowApproval:
        """
        Create an approval request

        Args:
            execution_id: Workflow execution ID
            approval_type: Type of approval (email_send, video_create, etc.)
            approval_title: Short title for approval
            approval_description: Detailed description
            approval_data: Additional data for approval decision
            priority: Approval priority
            requires_manual: Force manual approval
            auto_approval_enabled: Allow auto-approval
            expires_in_hours: Hours until expiration

        Returns:
            WorkflowApproval instance
        """
        try:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

            approval = WorkflowApproval(
                execution_id=execution_id,
                approval_type=approval_type,
                approval_title=approval_title,
                approval_description=approval_description,
                approval_data=approval_data or {},
                priority=priority,
                requires_manual=requires_manual,
                auto_approval_enabled=auto_approval_enabled,
                expires_at=expires_at
            )

            self.db.add(approval)
            self.db.commit()
            self.db.refresh(approval)

            logger.info(f"Created approval request {approval.id} for execution {execution_id}")

            # Try auto-approval if enabled
            if auto_approval_enabled and not requires_manual:
                await self.auto_approval.evaluate_approval(approval.id)

            return approval

        except Exception as e:
            logger.error(f"Failed to create approval request: {str(e)}")
            self.db.rollback()
            raise

    async def approve(
        self,
        approval_id: int,
        approver_name: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Approve a request

        Args:
            approval_id: Approval request ID
            approver_name: Name of approver
            reason: Approval reason

        Returns:
            True if approved successfully
        """
        try:
            approval = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.id == approval_id
            ).first()

            if not approval:
                logger.warning(f"Approval {approval_id} not found")
                return False

            if approval.status != ApprovalStatus.PENDING:
                logger.warning(f"Approval {approval_id} is not pending")
                return False

            approval.status = ApprovalStatus.APPROVED
            approval.approver_name = approver_name or "Manual Approver"
            approval.approval_reason = reason
            approval.approved_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Approved request {approval_id}")

            # Trigger workflow execution if needed
            await self._trigger_approved_execution(approval)

            return True

        except Exception as e:
            logger.error(f"Failed to approve request: {str(e)}")
            self.db.rollback()
            return False

    async def reject(
        self,
        approval_id: int,
        approver_name: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject a request

        Args:
            approval_id: Approval request ID
            approver_name: Name of approver
            reason: Rejection reason

        Returns:
            True if rejected successfully
        """
        try:
            approval = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.id == approval_id
            ).first()

            if not approval:
                return False

            if approval.status != ApprovalStatus.PENDING:
                return False

            approval.status = ApprovalStatus.REJECTED
            approval.approver_name = approver_name or "Manual Approver"
            approval.approval_reason = reason
            approval.approved_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Rejected request {approval_id}")

            # Mark execution as failed
            from .workflow_executor import WorkflowExecutor
            executor = WorkflowExecutor(self.db)
            await executor.mark_failed(
                approval.execution_id,
                "Approval rejected",
                "APPROVAL_REJECTED"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to reject request: {str(e)}")
            self.db.rollback()
            return False

    async def bulk_action(
        self,
        approval_ids: List[int],
        action: ApprovalStatus,
        approver_name: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk approval/rejection

        Args:
            approval_ids: List of approval IDs
            action: Action to perform (APPROVED or REJECTED)
            approver_name: Name of approver
            reason: Reason for action

        Returns:
            Result summary
        """
        results = {
            "total": len(approval_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        for approval_id in approval_ids:
            try:
                if action == ApprovalStatus.APPROVED:
                    success = await self.approve(approval_id, approver_name, reason)
                elif action == ApprovalStatus.REJECTED:
                    success = await self.reject(approval_id, approver_name, reason)
                else:
                    success = False

                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Approval {approval_id}: {str(e)}")

        return results

    async def expire_old_approvals(self) -> int:
        """
        Expire old approval requests

        Returns:
            Number of expired approvals
        """
        try:
            now = datetime.utcnow()
            expired = self.db.query(WorkflowApproval).filter(
                and_(
                    WorkflowApproval.status == ApprovalStatus.PENDING,
                    WorkflowApproval.expires_at <= now
                )
            ).all()

            count = 0
            for approval in expired:
                approval.status = ApprovalStatus.EXPIRED
                count += 1

            self.db.commit()
            logger.info(f"Expired {count} approval requests")

            return count

        except Exception as e:
            logger.error(f"Failed to expire approvals: {str(e)}")
            self.db.rollback()
            return 0

    def get_pending_approvals(
        self,
        limit: int = 50,
        priority: Optional[ApprovalPriority] = None
    ) -> List[WorkflowApproval]:
        """Get pending approval requests"""
        try:
            query = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.status == ApprovalStatus.PENDING
            )

            if priority:
                query = query.filter(WorkflowApproval.priority == priority)

            approvals = query.order_by(
                WorkflowApproval.priority.desc(),
                WorkflowApproval.created_at.asc()
            ).limit(limit).all()

            return approvals

        except Exception as e:
            logger.error(f"Failed to get pending approvals: {str(e)}")
            return []

    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        try:
            total_pending = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.status == ApprovalStatus.PENDING
            ).count()

            total_approved = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.status == ApprovalStatus.APPROVED
            ).count()

            total_rejected = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.status == ApprovalStatus.REJECTED
            ).count()

            total_expired = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.status == ApprovalStatus.EXPIRED
            ).count()

            high_priority = self.db.query(WorkflowApproval).filter(
                and_(
                    WorkflowApproval.status == ApprovalStatus.PENDING,
                    WorkflowApproval.priority == ApprovalPriority.HIGH
                )
            ).count()

            return {
                "total_pending": total_pending,
                "total_approved": total_approved,
                "total_rejected": total_rejected,
                "total_expired": total_expired,
                "high_priority_count": high_priority,
            }

        except Exception as e:
            logger.error(f"Failed to get approval stats: {str(e)}")
            return {}

    async def _trigger_approved_execution(self, approval: WorkflowApproval) -> None:
        """Trigger workflow execution after approval"""
        try:
            from .workflow_executor import WorkflowExecutor
            executor = WorkflowExecutor(self.db)

            execution = approval.execution
            if execution and execution.status.value == "pending":
                # Execute the workflow
                await executor._execute_in_n8n(execution, execution.workflow)

        except Exception as e:
            logger.error(f"Failed to trigger approved execution: {str(e)}")
