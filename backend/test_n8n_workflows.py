"""
N8N Workflow Automation Tests

Comprehensive test suite for Phase 6: N8N Workflow Automation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models.n8n_workflows import (
    N8NWorkflow,
    WorkflowExecution,
    WorkflowApproval,
    WebhookQueue,
    WorkflowMonitoring,
    WorkflowStatus,
    ApprovalStatus,
    ApprovalPriority,
    QueueStatus,
    MonitoringSeverity
)
from backend.app.services.workflows import (
    N8NClient,
    WebhookHandler,
    WorkflowExecutor,
    ApprovalSystem,
    AutoApprovalService,
    WorkflowMonitor
)


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_workflows.db"


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================================
# MODEL TESTS
# ============================================================================

def test_create_workflow(db_session):
    """Test creating a workflow"""
    workflow = N8NWorkflow(
        workflow_name="Test Workflow",
        workflow_description="Test Description",
        n8n_workflow_id="test-123",
        is_active=True,
        requires_approval=True,
        auto_approval_enabled=False
    )

    db_session.add(workflow)
    db_session.commit()

    assert workflow.id is not None
    assert workflow.workflow_name == "Test Workflow"
    assert workflow.execution_count == 0


def test_create_execution(db_session):
    """Test creating a workflow execution"""
    workflow = N8NWorkflow(workflow_name="Test")
    db_session.add(workflow)
    db_session.commit()

    execution = WorkflowExecution(
        workflow_id=workflow.id,
        trigger_event="test_event",
        trigger_source="manual",
        input_data={"key": "value"},
        status=WorkflowStatus.PENDING
    )

    db_session.add(execution)
    db_session.commit()

    assert execution.id is not None
    assert execution.workflow_id == workflow.id
    assert execution.status == WorkflowStatus.PENDING


def test_create_approval(db_session):
    """Test creating an approval request"""
    workflow = N8NWorkflow(workflow_name="Test")
    db_session.add(workflow)
    db_session.commit()

    execution = WorkflowExecution(workflow_id=workflow.id, status=WorkflowStatus.PENDING)
    db_session.add(execution)
    db_session.commit()

    approval = WorkflowApproval(
        execution_id=execution.id,
        approval_type="email_send",
        approval_title="Send Email Approval",
        status=ApprovalStatus.PENDING,
        priority=ApprovalPriority.MEDIUM
    )

    db_session.add(approval)
    db_session.commit()

    assert approval.id is not None
    assert approval.status == ApprovalStatus.PENDING
    assert not approval.is_expired()


def test_approval_expiration(db_session):
    """Test approval expiration check"""
    workflow = N8NWorkflow(workflow_name="Test")
    execution = WorkflowExecution(workflow_id=workflow.id)
    db_session.add_all([workflow, execution])
    db_session.commit()

    # Create expired approval
    approval = WorkflowApproval(
        execution_id=execution.id,
        approval_type="test",
        approval_title="Test",
        status=ApprovalStatus.PENDING,
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )

    assert approval.is_expired() is True


def test_webhook_queue(db_session):
    """Test webhook queue creation"""
    webhook = WebhookQueue(
        webhook_payload={"event": "test"},
        source="n8n",
        status=QueueStatus.QUEUED,
        max_retries=3
    )

    db_session.add(webhook)
    db_session.commit()

    assert webhook.id is not None
    assert webhook.should_retry() is False  # Not failed yet


def test_webhook_retry_logic(db_session):
    """Test webhook retry logic"""
    webhook = WebhookQueue(
        webhook_payload={"test": "data"},
        status=QueueStatus.FAILED,
        retry_count=1,
        max_retries=3,
        next_retry_at=datetime.utcnow() - timedelta(minutes=5)
    )

    db_session.add(webhook)
    db_session.commit()

    assert webhook.should_retry() is True

    # Calculate next retry time
    next_retry = webhook.calculate_next_retry()
    assert next_retry > datetime.utcnow()


def test_monitoring_event(db_session):
    """Test monitoring event creation"""
    workflow = N8NWorkflow(workflow_name="Test")
    db_session.add(workflow)
    db_session.commit()

    event = WorkflowMonitoring(
        workflow_id=workflow.id,
        event_type="test_event",
        event_name="Test Event",
        severity=MonitoringSeverity.INFO
    )

    db_session.add(event)
    db_session.commit()

    assert event.id is not None
    assert event.severity == MonitoringSeverity.INFO


# ============================================================================
# SERVICE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_n8n_client_initialization():
    """Test N8N client initialization"""
    client = N8NClient(
        api_url="https://test.n8n.cloud/api/v1",
        api_key="test_key"
    )

    assert client.api_url == "https://test.n8n.cloud/api/v1"
    assert client.api_key == "test_key"


@pytest.mark.asyncio
async def test_n8n_client_trigger_workflow():
    """Test triggering workflow via N8N client"""
    client = N8NClient(
        api_url="https://test.n8n.cloud/api/v1",
        api_key="test_key"
    )

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"executionId": "exec-123", "data": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Mock the async context manager
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await client.trigger_workflow(
                workflow_id="wf-123",
                data={"test": "data"}
            )

            assert "executionId" in result or "data" in result


def test_webhook_handler_queue(db_session):
    """Test webhook handler queueing"""
    handler = WebhookHandler(db_session)

    webhook = handler.queue_webhook(
        workflow_id=None,
        payload={"event": "test", "data": "value"},
        source="n8n",
        priority=5
    )

    assert webhook.id is not None
    assert webhook.status == QueueStatus.QUEUED
    assert webhook.priority == 5


def test_webhook_handler_get_pending(db_session):
    """Test getting pending webhooks"""
    handler = WebhookHandler(db_session)

    # Create webhooks
    handler.queue_webhook(workflow_id=None, payload={"test": 1}, priority=1)
    handler.queue_webhook(workflow_id=None, payload={"test": 2}, priority=5)
    handler.queue_webhook(workflow_id=None, payload={"test": 3}, priority=3)

    pending = handler.get_pending_webhooks(limit=10)

    assert len(pending) == 3
    # Should be ordered by priority desc
    assert pending[0].priority == 5


@pytest.mark.asyncio
async def test_workflow_executor_execute(db_session):
    """Test workflow execution"""
    workflow = N8NWorkflow(
        workflow_name="Test Workflow",
        is_active=True,
        requires_approval=False,
        n8n_workflow_id="wf-123"
    )
    db_session.add(workflow)
    db_session.commit()

    executor = WorkflowExecutor(db_session)

    with patch.object(executor.n8n_client, 'trigger_workflow', new_callable=AsyncMock) as mock_trigger:
        mock_trigger.return_value = {"executionId": "exec-123"}

        execution = await executor.execute_workflow(
            workflow_id=workflow.id,
            trigger_event="test",
            input_data={"key": "value"}
        )

        assert execution.id is not None
        assert execution.workflow_id == workflow.id


@pytest.mark.asyncio
async def test_workflow_executor_mark_completed(db_session):
    """Test marking execution as completed"""
    workflow = N8NWorkflow(workflow_name="Test")
    execution = WorkflowExecution(
        workflow_id=workflow.id,
        status=WorkflowStatus.RUNNING,
        started_at=datetime.utcnow()
    )
    db_session.add_all([workflow, execution])
    db_session.commit()

    executor = WorkflowExecutor(db_session)

    success = await executor.mark_completed(
        execution_id=execution.id,
        output_data={"result": "success"}
    )

    assert success is True

    db_session.refresh(execution)
    assert execution.status == WorkflowStatus.COMPLETED
    assert execution.duration_seconds is not None


@pytest.mark.asyncio
async def test_approval_system_create(db_session):
    """Test creating approval request"""
    workflow = N8NWorkflow(workflow_name="Test")
    execution = WorkflowExecution(workflow_id=workflow.id)
    db_session.add_all([workflow, execution])
    db_session.commit()

    approval_system = ApprovalSystem(db_session)

    with patch.object(approval_system.auto_approval, 'evaluate_approval', new_callable=AsyncMock):
        approval = await approval_system.create_approval_request(
            execution_id=execution.id,
            approval_type="email_send",
            approval_title="Send Email",
            priority=ApprovalPriority.HIGH
        )

        assert approval.id is not None
        assert approval.status == ApprovalStatus.PENDING
        assert approval.priority == ApprovalPriority.HIGH


@pytest.mark.asyncio
async def test_approval_system_approve(db_session):
    """Test approving a request"""
    workflow = N8NWorkflow(workflow_name="Test")
    execution = WorkflowExecution(workflow_id=workflow.id, status=WorkflowStatus.PENDING)
    approval = WorkflowApproval(
        execution_id=execution.id,
        approval_type="test",
        approval_title="Test",
        status=ApprovalStatus.PENDING
    )
    db_session.add_all([workflow, execution, approval])
    db_session.commit()

    approval_system = ApprovalSystem(db_session)

    with patch.object(approval_system, '_trigger_approved_execution', new_callable=AsyncMock):
        success = await approval_system.approve(
            approval_id=approval.id,
            approver_name="Test Approver",
            reason="Approved for testing"
        )

        assert success is True

        db_session.refresh(approval)
        assert approval.status == ApprovalStatus.APPROVED
        assert approval.approver_name == "Test Approver"


@pytest.mark.asyncio
async def test_approval_system_reject(db_session):
    """Test rejecting a request"""
    workflow = N8NWorkflow(workflow_name="Test")
    execution = WorkflowExecution(workflow_id=workflow.id)
    approval = WorkflowApproval(
        execution_id=execution.id,
        approval_type="test",
        approval_title="Test",
        status=ApprovalStatus.PENDING
    )
    db_session.add_all([workflow, execution, approval])
    db_session.commit()

    approval_system = ApprovalSystem(db_session)

    success = await approval_system.reject(
        approval_id=approval.id,
        approver_name="Test Approver",
        reason="Rejected for testing"
    )

    assert success is True

    db_session.refresh(approval)
    assert approval.status == ApprovalStatus.REJECTED


@pytest.mark.asyncio
async def test_workflow_monitor_log_event(db_session):
    """Test logging workflow event"""
    workflow = N8NWorkflow(workflow_name="Test")
    db_session.add(workflow)
    db_session.commit()

    monitor = WorkflowMonitor(db_session)

    event = await monitor.log_event(
        workflow_id=workflow.id,
        event_type="test_event",
        event_name="Test Event",
        severity="info"
    )

    assert event.id is not None
    assert event.event_type == "test_event"
    assert event.severity == MonitoringSeverity.INFO


def test_workflow_monitor_get_errors(db_session):
    """Test getting error logs"""
    workflow = N8NWorkflow(workflow_name="Test")
    db_session.add(workflow)
    db_session.commit()

    # Create error events
    error1 = WorkflowMonitoring(
        workflow_id=workflow.id,
        event_type="error",
        severity=MonitoringSeverity.ERROR,
        event_name="Error 1"
    )
    error2 = WorkflowMonitoring(
        workflow_id=workflow.id,
        event_type="critical_error",
        severity=MonitoringSeverity.CRITICAL,
        event_name="Error 2"
    )
    db_session.add_all([error1, error2])
    db_session.commit()

    monitor = WorkflowMonitor(db_session)
    errors = monitor.get_error_logs(hours=24, limit=10)

    assert len(errors) == 2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_full_workflow_lifecycle(db_session):
    """Test complete workflow lifecycle"""
    # Create workflow
    workflow = N8NWorkflow(
        workflow_name="Full Test Workflow",
        is_active=True,
        requires_approval=False,
        n8n_workflow_id="wf-test"
    )
    db_session.add(workflow)
    db_session.commit()

    executor = WorkflowExecutor(db_session)

    # Execute workflow
    with patch.object(executor.n8n_client, 'trigger_workflow', new_callable=AsyncMock) as mock_trigger:
        mock_trigger.return_value = {"executionId": "exec-123"}

        execution = await executor.execute_workflow(
            workflow_id=workflow.id,
            trigger_event="test_trigger",
            input_data={"test": "data"}
        )

        # Mark as completed
        await executor.mark_completed(
            execution_id=execution.id,
            output_data={"result": "success"}
        )

        db_session.refresh(execution)
        assert execution.status == WorkflowStatus.COMPLETED
        assert execution.output_data == {"result": "success"}


@pytest.mark.asyncio
async def test_workflow_with_approval_flow(db_session):
    """Test workflow with approval requirement"""
    # Create workflow requiring approval
    workflow = N8NWorkflow(
        workflow_name="Approval Test",
        is_active=True,
        requires_approval=True,
        auto_approval_enabled=False
    )
    db_session.add(workflow)
    db_session.commit()

    executor = WorkflowExecutor(db_session)

    # Execute workflow
    execution = await executor.execute_workflow(
        workflow_id=workflow.id,
        trigger_event="test",
        input_data={}
    )

    # Should have approval request
    db_session.refresh(execution)
    assert len(execution.approvals) > 0

    approval = execution.approvals[0]
    assert approval.status == ApprovalStatus.PENDING

    # Approve it
    approval_system = ApprovalSystem(db_session)

    with patch.object(approval_system, '_trigger_approved_execution', new_callable=AsyncMock):
        await approval_system.approve(
            approval_id=approval.id,
            approver_name="Tester"
        )

        db_session.refresh(approval)
        assert approval.status == ApprovalStatus.APPROVED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
