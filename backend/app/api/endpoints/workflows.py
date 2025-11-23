"""
Workflow Management Endpoints

API endpoints for managing N8N workflows, executions, approvals, and monitoring.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_db
from app.models.n8n_workflows import (
    N8NWorkflow,
    WorkflowExecution,
    WorkflowApproval,
    WorkflowMonitoring,
    WorkflowStatus,
    ApprovalStatus,
    ApprovalPriority
)
from app.schemas.workflows import (
    N8NWorkflowCreate,
    N8NWorkflowUpdate,
    N8NWorkflowResponse,
    WorkflowExecutionCreate,
    WorkflowExecutionResponse,
    WorkflowExecutionRetry,
    WorkflowApprovalCreate,
    WorkflowApprovalResponse,
    WorkflowApprovalDecision,
    WorkflowApprovalBulkAction,
    WorkflowMonitoringQuery,
    WorkflowMonitoringResponse,
    WorkflowTrigger,
    WorkflowTriggerResponse,
    WorkflowDashboard,
    WorkflowHealthCheck,
    WorkflowListResponse,
    ExecutionListResponse,
    ApprovalListResponse,
    MonitoringListResponse,
)
from app.services.workflows import (
    WorkflowExecutor,
    ApprovalSystem,
    WorkflowMonitor,
    N8NClient,
    get_n8n_client
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all workflows with pagination"""
    try:
        query = db.query(N8NWorkflow)

        if is_active is not None:
            query = query.filter(N8NWorkflow.is_active == is_active)

        total = query.count()
        workflows = query.order_by(desc(N8NWorkflow.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {
            "items": workflows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }

    except Exception as e:
        logger.error(f"List workflows error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=N8NWorkflowResponse)
async def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get workflow details"""
    workflow = db.query(N8NWorkflow).filter(N8NWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/workflows", response_model=N8NWorkflowResponse, status_code=201)
async def create_workflow(
    workflow: N8NWorkflowCreate,
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    try:
        db_workflow = N8NWorkflow(**workflow.dict())
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        return db_workflow

    except Exception as e:
        logger.error(f"Create workflow error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/workflows/{workflow_id}", response_model=N8NWorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow: N8NWorkflowUpdate,
    db: Session = Depends(get_db)
):
    """Update a workflow"""
    db_workflow = db.query(N8NWorkflow).filter(N8NWorkflow.id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    for key, value in workflow.dict(exclude_unset=True).items():
        setattr(db_workflow, key, value)

    db.commit()
    db.refresh(db_workflow)
    return db_workflow


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Delete a workflow"""
    workflow = db.query(N8NWorkflow).filter(N8NWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db.delete(workflow)
    db.commit()

    return {"status": "deleted", "workflow_id": workflow_id}


@router.post("/workflows/{workflow_id}/trigger", response_model=WorkflowTriggerResponse)
async def trigger_workflow(
    workflow_id: int,
    trigger: WorkflowTrigger,
    db: Session = Depends(get_db)
):
    """Manually trigger a workflow"""
    try:
        executor = WorkflowExecutor(db)
        execution = await executor.execute_workflow(
            workflow_id=workflow_id,
            trigger_event=trigger.trigger_event,
            trigger_source=trigger.trigger_source.value,
            input_data=trigger.input_data,
            metadata=trigger.metadata,
            force_execution=trigger.force_execution
        )

        workflow = execution.workflow

        return {
            "execution_id": execution.id,
            "workflow_id": workflow_id,
            "workflow_name": workflow.workflow_name,
            "status": execution.status,
            "requires_approval": workflow.requires_approval and not trigger.force_execution,
            "approval_id": execution.approvals[0].id if execution.approvals else None,
            "message": "Workflow triggered successfully"
        }

    except Exception as e:
        logger.error(f"Trigger workflow error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows/{workflow_id}/executions", response_model=ExecutionListResponse)
async def get_workflow_executions(
    workflow_id: int,
    status: Optional[WorkflowStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get execution history for a workflow"""
    query = db.query(WorkflowExecution).filter(WorkflowExecution.workflow_id == workflow_id)

    if status:
        query = query.filter(WorkflowExecution.status == status)

    total = query.count()
    executions = query.order_by(desc(WorkflowExecution.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": executions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(workflow_id: int, db: Session = Depends(get_db)):
    """Get workflow statistics"""
    workflow = db.query(N8NWorkflow).filter(N8NWorkflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    total = workflow.execution_count
    success_rate = (workflow.success_count / total * 100) if total > 0 else 0

    return {
        "workflow_id": workflow_id,
        "workflow_name": workflow.workflow_name,
        "total_executions": total,
        "successful_executions": workflow.success_count,
        "failed_executions": workflow.failure_count,
        "success_rate": round(success_rate, 2),
        "average_duration_seconds": workflow.average_duration_seconds or 0,
        "last_executed_at": workflow.last_executed_at
    }


# ============================================================================
# WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[int] = None,
    status: Optional[WorkflowStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all executions with filters"""
    query = db.query(WorkflowExecution)

    if workflow_id:
        query = query.filter(WorkflowExecution.workflow_id == workflow_id)

    if status:
        query = query.filter(WorkflowExecution.status == status)

    total = query.count()
    executions = query.order_by(desc(WorkflowExecution.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": executions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """Get execution details"""
    execution = db.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/executions/{execution_id}/retry", response_model=WorkflowExecutionResponse)
async def retry_execution(
    execution_id: int,
    retry: WorkflowExecutionRetry,
    db: Session = Depends(get_db)
):
    """Retry a failed execution"""
    executor = WorkflowExecutor(db)
    new_execution = await executor.retry_execution(
        execution_id=execution_id,
        override_input_data=retry.override_input_data
    )

    if not new_execution:
        raise HTTPException(status_code=400, detail="Execution cannot be retried")

    return new_execution


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: int, db: Session = Depends(get_db)):
    """Cancel a running execution"""
    executor = WorkflowExecutor(db)
    success = await executor.cancel_execution(execution_id)

    if not success:
        raise HTTPException(status_code=400, detail="Execution cannot be cancelled")

    return {"status": "cancelled", "execution_id": execution_id}


# ============================================================================
# WORKFLOW APPROVAL ENDPOINTS
# ============================================================================

@router.get("/approvals", response_model=ApprovalListResponse)
async def list_approvals(
    status: Optional[ApprovalStatus] = ApprovalStatus.PENDING,
    priority: Optional[ApprovalPriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List approval requests"""
    query = db.query(WorkflowApproval)

    if status:
        query = query.filter(WorkflowApproval.status == status)

    if priority:
        query = query.filter(WorkflowApproval.priority == priority)

    total = query.count()
    approvals = query.order_by(
        desc(WorkflowApproval.priority),
        desc(WorkflowApproval.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": approvals,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/approvals/{approval_id}", response_model=WorkflowApprovalResponse)
async def get_approval(approval_id: int, db: Session = Depends(get_db)):
    """Get approval details"""
    approval = db.query(WorkflowApproval).filter(WorkflowApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/approvals/{approval_id}/approve")
async def approve_request(
    approval_id: int,
    decision: WorkflowApprovalDecision,
    db: Session = Depends(get_db)
):
    """Approve an approval request"""
    system = ApprovalSystem(db)
    success = await system.approve(
        approval_id=approval_id,
        approver_name=decision.approver_name,
        reason=decision.reason
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to approve request")

    return {"status": "approved", "approval_id": approval_id}


@router.post("/approvals/{approval_id}/reject")
async def reject_request(
    approval_id: int,
    decision: WorkflowApprovalDecision,
    db: Session = Depends(get_db)
):
    """Reject an approval request"""
    system = ApprovalSystem(db)
    success = await system.reject(
        approval_id=approval_id,
        approver_name=decision.approver_name,
        reason=decision.reason
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to reject request")

    return {"status": "rejected", "approval_id": approval_id}


@router.get("/approvals/stats")
async def get_approval_stats(db: Session = Depends(get_db)):
    """Get approval statistics"""
    system = ApprovalSystem(db)
    return system.get_approval_stats()


@router.post("/approvals/bulk-action")
async def bulk_approval_action(
    action: WorkflowApprovalBulkAction,
    db: Session = Depends(get_db)
):
    """Perform bulk approval/rejection"""
    system = ApprovalSystem(db)
    results = await system.bulk_action(
        approval_ids=action.approval_ids,
        action=action.action,
        approver_name=action.approver_name,
        reason=action.reason
    )
    return results


# ============================================================================
# MONITORING ENDPOINTS
# ============================================================================

@router.get("/monitoring/events", response_model=MonitoringListResponse)
async def get_monitoring_events(
    query_params: WorkflowMonitoringQuery = Depends(),
    db: Session = Depends(get_db)
):
    """Get monitoring events with filters"""
    monitor = WorkflowMonitor(db)
    events = monitor.get_events(
        workflow_id=query_params.workflow_id,
        execution_id=query_params.execution_id,
        event_type=query_params.event_type,
        severity=query_params.severity,
        start_date=query_params.start_date,
        end_date=query_params.end_date,
        limit=query_params.limit,
        offset=query_params.offset
    )

    total = len(events)  # Simplified for now

    return {
        "items": events,
        "total": total,
        "page": 1,
        "page_size": query_params.limit,
        "pages": 1
    }


@router.get("/monitoring/errors")
async def get_error_logs(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get recent error logs"""
    monitor = WorkflowMonitor(db)
    errors = monitor.get_error_logs(hours=hours, limit=limit)
    return {"errors": [e.to_dict() for e in errors], "total": len(errors)}


@router.get("/monitoring/dashboard", response_model=WorkflowDashboard)
async def get_dashboard(db: Session = Depends(get_db)):
    """Get workflow dashboard data"""
    monitor = WorkflowMonitor(db)
    dashboard_data = monitor.get_dashboard_data()

    # Get additional stats
    total_workflows = db.query(N8NWorkflow).count()
    active_workflows = db.query(N8NWorkflow).filter(N8NWorkflow.is_active == True).count()
    pending_approvals = db.query(WorkflowApproval).filter(
        WorkflowApproval.status == ApprovalStatus.PENDING
    ).count()

    recent_executions = db.query(WorkflowExecution).order_by(
        desc(WorkflowExecution.created_at)
    ).limit(5).all()

    return {
        "total_workflows": total_workflows,
        "active_workflows": active_workflows,
        "total_executions_today": dashboard_data.get("events_last_hour", 0) * 24,  # Estimate
        "successful_executions_today": 0,  # Would need actual calculation
        "failed_executions_today": dashboard_data.get("errors_last_hour", 0) * 24,
        "pending_approvals": pending_approvals,
        "queued_webhooks": 0,  # Would query webhook_queue
        "recent_executions": recent_executions,
        "recent_errors": dashboard_data.get("recent_errors", [])
    }


@router.get("/health", response_model=WorkflowHealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Workflow system health check"""
    try:
        # Check N8N connection
        n8n_client = get_n8n_client()
        n8n_ok = await n8n_client.test_connection()

        # Check database
        db.execute("SELECT 1")
        db_ok = True

        # Check pending items
        pending_approvals = db.query(WorkflowApproval).filter(
            WorkflowApproval.status == ApprovalStatus.PENDING
        ).count()

        # Simplified health status
        status = "healthy" if (n8n_ok and db_ok) else "degraded"

        return {
            "n8n_connection": n8n_ok,
            "database_connection": db_ok,
            "webhook_queue_size": 0,
            "pending_approvals": pending_approvals,
            "failed_executions_last_hour": 0,
            "average_execution_time_seconds": 0.0,
            "status": status
        }

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "n8n_connection": False,
            "database_connection": False,
            "webhook_queue_size": 0,
            "pending_approvals": 0,
            "failed_executions_last_hour": 0,
            "average_execution_time_seconds": 0.0,
            "status": "unhealthy"
        }
