"""
Workflow Executor Service

Executes workflows, manages execution lifecycle, and tracks progress.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.n8n_workflows import (
    N8NWorkflow,
    WorkflowExecution,
    WorkflowStatus
)
from .n8n_client import get_n8n_client, N8NClientError
from .workflow_monitor import WorkflowMonitor
from .approval_system import ApprovalSystem

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """
    Workflow Executor

    Handles workflow execution lifecycle including triggering,
    status tracking, and completion handling.
    """

    def __init__(self, db: Session):
        """Initialize workflow executor"""
        self.db = db
        self.n8n_client = get_n8n_client()
        self.monitor = WorkflowMonitor(db)
        self.approval_system = ApprovalSystem(db)

    async def execute_workflow(
        self,
        workflow_id: int,
        trigger_event: Optional[str] = None,
        trigger_source: str = "manual",
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force_execution: bool = False
    ) -> WorkflowExecution:
        """
        Execute a workflow

        Args:
            workflow_id: Workflow database ID
            trigger_event: Event that triggered the workflow
            trigger_source: Source of trigger (manual, webhook, etc.)
            input_data: Input data for workflow
            metadata: Additional metadata
            force_execution: Bypass approval if True

        Returns:
            WorkflowExecution instance

        Raises:
            ValueError: If workflow not found or not active
        """
        # Get workflow
        workflow = self.db.query(N8NWorkflow).filter(
            N8NWorkflow.id == workflow_id
        ).first()

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.is_active:
            raise ValueError(f"Workflow {workflow_id} is not active")

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            trigger_event=trigger_event,
            trigger_source=trigger_source,
            input_data=input_data or {},
            metadata=metadata or {},
            status=WorkflowStatus.PENDING
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # Log execution start
        await self.monitor.log_event(
            workflow_id=workflow_id,
            execution_id=execution.id,
            event_type="execution_created",
            event_name="Execution Created",
            event_data={"trigger_event": trigger_event, "trigger_source": trigger_source}
        )

        # Check if approval required
        if workflow.requires_approval and not force_execution:
            await self.approval_system.create_approval_request(
                execution_id=execution.id,
                approval_type="workflow_execution",
                approval_title=f"Execute workflow: {workflow.workflow_name}",
                approval_description=f"Trigger: {trigger_event or 'manual'}",
                approval_data={"input_data": input_data},
                auto_approval_enabled=workflow.auto_approval_enabled
            )

            await self.monitor.log_event(
                workflow_id=workflow_id,
                execution_id=execution.id,
                event_type="approval_required",
                event_name="Approval Required"
            )

            return execution

        # Execute immediately if no approval needed
        await self._execute_in_n8n(execution, workflow)
        return execution

    async def _execute_in_n8n(
        self,
        execution: WorkflowExecution,
        workflow: N8NWorkflow
    ) -> None:
        """Execute workflow in N8N"""
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.utcnow()
        self.db.commit()

        await self.monitor.log_event(
            workflow_id=workflow.id,
            execution_id=execution.id,
            event_type="execution_started",
            event_name="Execution Started"
        )

        try:
            if workflow.n8n_workflow_id:
                # Trigger N8N workflow
                result = await self.n8n_client.trigger_workflow(
                    workflow_id=workflow.n8n_workflow_id,
                    data=execution.input_data,
                    wait_for_completion=False
                )

                execution.n8n_execution_id = result.get("executionId") or result.get("id")
                self.db.commit()

            # Update workflow statistics
            workflow.execution_count += 1
            workflow.last_executed_at = datetime.utcnow()
            self.db.commit()

        except N8NClientError as e:
            logger.error(f"N8N execution error: {str(e)}")
            await self.mark_failed(execution.id, str(e))
            raise

    async def mark_completed(
        self,
        execution_id: int,
        output_data: Optional[Dict[str, Any]] = None,
        execution_log: Optional[str] = None
    ) -> bool:
        """Mark execution as completed"""
        try:
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()

            if not execution:
                return False

            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.output_data = output_data or {}
            execution.execution_log = execution_log

            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.duration_seconds = duration

            # Update workflow statistics
            workflow = execution.workflow
            workflow.success_count += 1

            # Update average duration
            if workflow.average_duration_seconds:
                workflow.average_duration_seconds = (
                    workflow.average_duration_seconds * 0.8 + execution.duration_seconds * 0.2
                )
            else:
                workflow.average_duration_seconds = execution.duration_seconds

            self.db.commit()

            await self.monitor.log_event(
                workflow_id=execution.workflow_id,
                execution_id=execution_id,
                event_type="execution_completed",
                event_name="Execution Completed",
                event_data={"duration_seconds": execution.duration_seconds}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to mark execution as completed: {str(e)}")
            self.db.rollback()
            return False

    async def mark_failed(
        self,
        execution_id: int,
        error_message: str,
        error_code: Optional[str] = None
    ) -> bool:
        """Mark execution as failed"""
        try:
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()

            if not execution:
                return False

            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error_message = error_message
            execution.error_code = error_code

            if execution.started_at:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                execution.duration_seconds = duration

            # Update workflow statistics
            workflow = execution.workflow
            workflow.failure_count += 1

            self.db.commit()

            await self.monitor.log_event(
                workflow_id=execution.workflow_id,
                execution_id=execution_id,
                event_type="execution_failed",
                event_name="Execution Failed",
                event_data={"error": error_message},
                severity="error"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to mark execution as failed: {str(e)}")
            self.db.rollback()
            return False

    async def cancel_execution(self, execution_id: int) -> bool:
        """Cancel a running execution"""
        try:
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()

            if not execution or execution.status != WorkflowStatus.RUNNING:
                return False

            # Try to cancel in N8N if execution ID exists
            if execution.n8n_execution_id:
                try:
                    await self.n8n_client.cancel_execution(execution.n8n_execution_id)
                except Exception as e:
                    logger.warning(f"Failed to cancel in N8N: {str(e)}")

            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            self.db.commit()

            await self.monitor.log_event(
                workflow_id=execution.workflow_id,
                execution_id=execution_id,
                event_type="execution_cancelled",
                event_name="Execution Cancelled"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to cancel execution: {str(e)}")
            self.db.rollback()
            return False

    async def retry_execution(
        self,
        execution_id: int,
        override_input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecution]:
        """Retry a failed execution"""
        try:
            original = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()

            if not original or not original.is_retryable:
                return None

            # Create new execution
            input_data = override_input_data or original.input_data

            new_execution = await self.execute_workflow(
                workflow_id=original.workflow_id,
                trigger_event=f"retry:{original.trigger_event}",
                trigger_source="retry",
                input_data=input_data,
                metadata={"retried_from": execution_id}
            )

            return new_execution

        except Exception as e:
            logger.error(f"Failed to retry execution: {str(e)}")
            return None
