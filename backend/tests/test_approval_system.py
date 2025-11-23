"""
Comprehensive tests for the Approval System.

Tests cover:
- Approval request creation
- Auto-approval rules evaluation
- Decision submission and webhook triggering
- Timeout handling
- Escalation
- Bulk approvals
- Statistics
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.approval_system import ApprovalSystem, ApprovalType, ApprovalStatus
from app.services.auto_approval import AutoApprovalEngine
from app.models.approvals import ResponseApproval, ApprovalRule, ApprovalQueue, ApprovalHistory


class TestApprovalSystem:
    """Test ApprovalSystem service."""

    @pytest.fixture
    async def approval_system(self, db_session: AsyncSession):
        """Create ApprovalSystem instance."""
        return ApprovalSystem(db_session)

    @pytest.fixture
    async def sample_resource_data(self):
        """Sample resource data for testing."""
        return {
            'title': 'Test Demo Site',
            'description': 'A test demo site for approval',
            'preview_url': 'https://example.com/preview',
            'quality_score': 0.85,
            'category': 'software'
        }

    @pytest.mark.asyncio
    async def test_create_approval_request(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test creating an approval request."""

        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType.DEMO_SITE_REVIEW,
            resource_id=1,
            resource_data=sample_resource_data,
            workflow_execution_id='test-workflow-123',
            timeout_minutes=60,
            approvers=['test@example.com']
        )

        assert approval_id is not None

        # Verify approval was created
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await db_session.execute(query)
        approval = result.scalar_one_or_none()

        assert approval is not None
        assert approval.approval_type == ApprovalType.DEMO_SITE_REVIEW.value
        assert approval.resource_id == 1
        assert approval.workflow_execution_id == 'test-workflow-123'
        assert approval.status == 'pending'

    @pytest.mark.asyncio
    async def test_auto_approval(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test auto-approval based on rules."""

        # Create auto-approval rule
        rule = ApprovalRule(
            name='High Quality Auto-Approve',
            description='Auto-approve high quality items',
            template_types=[ApprovalType.DEMO_SITE_REVIEW.value],
            auto_approve=True,
            auto_approve_threshold=0.8,
            is_active=True,
            priority=100
        )
        db_session.add(rule)
        await db_session.commit()

        # Create approval with high quality score
        high_quality_data = {**sample_resource_data, 'quality_score': 0.90}

        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType.DEMO_SITE_REVIEW,
            resource_id=2,
            resource_data=high_quality_data,
            workflow_execution_id='test-workflow-auto',
            timeout_minutes=60
        )

        # Verify it was auto-approved
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await db_session.execute(query)
        approval = result.scalar_one_or_none()

        assert approval.status == 'approved'
        assert approval.approval_method == 'auto'
        assert approval.auto_approval_score is not None

    @pytest.mark.asyncio
    async def test_submit_decision_approve(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test submitting an approval decision."""

        # Create pending approval
        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType.VIDEO_REVIEW,
            resource_id=3,
            resource_data=sample_resource_data,
            workflow_execution_id='test-workflow-456',
            timeout_minutes=60
        )

        # Mock webhook call
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'success': True})
            mock_post.return_value.__aenter__.return_value = mock_response

            # Submit approval decision
            result = await approval_system.submit_decision(
                approval_id=approval_id,
                approved=True,
                reviewer_email='reviewer@example.com',
                comments='Looks good!'
            )

            assert result['success'] is True
            assert result['approved'] is True
            assert result['webhook_triggered'] is True

        # Verify approval status
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        db_result = await db_session.execute(query)
        approval = db_result.scalar_one_or_none()

        assert approval.status == 'approved'
        assert approval.approved is True
        assert approval.reviewer_email == 'reviewer@example.com'
        assert approval.reviewer_comments == 'Looks good!'

    @pytest.mark.asyncio
    async def test_submit_decision_reject(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test submitting a rejection decision."""

        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType.EMAIL_CONTENT_REVIEW,
            resource_id=4,
            resource_data=sample_resource_data,
            workflow_execution_id='test-workflow-789',
            timeout_minutes=60
        )

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'success': True})
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await approval_system.submit_decision(
                approval_id=approval_id,
                approved=False,
                reviewer_email='reviewer@example.com',
                comments='Not suitable'
            )

            assert result['success'] is True
            assert result['approved'] is False

        # Verify approval status
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        db_result = await db_session.execute(query)
        approval = db_result.scalar_one_or_none()

        assert approval.status == 'rejected'
        assert approval.approved is False

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test automatic timeout handling."""

        # Create approval with very short timeout
        approval = ResponseApproval(
            approval_type=ApprovalType.LEAD_QUALIFICATION.value,
            resource_id=5,
            resource_type='lead',
            resource_data=sample_resource_data,
            workflow_execution_id='test-timeout',
            status='pending',
            timeout_at=datetime.utcnow() - timedelta(minutes=5)  # Already timed out
        )
        db_session.add(approval)
        await db_session.commit()

        # Run timeout check
        timed_out_count = await approval_system.check_timeouts()

        assert timed_out_count == 1

        # Verify approval status
        await db_session.refresh(approval)
        assert approval.status == 'timeout'

    @pytest.mark.asyncio
    async def test_escalate_approval(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test escalating an approval."""

        approval_id = await approval_system.create_approval_request(
            approval_type=ApprovalType.IMPROVEMENT_PLAN_REVIEW,
            resource_id=6,
            resource_data=sample_resource_data,
            workflow_execution_id='test-escalate',
            timeout_minutes=60
        )

        # Escalate approval
        await approval_system.escalate_approval(
            approval_id=approval_id,
            escalation_level=1,
            escalated_to='manager@example.com'
        )

        # Verify escalation
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await db_session.execute(query)
        approval = result.scalar_one_or_none()

        assert approval.escalation_level == 1
        assert approval.escalated_to == 'manager@example.com'
        assert approval.status == 'escalated'

    @pytest.mark.asyncio
    async def test_bulk_approve(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test bulk approval of multiple items."""

        # Create multiple approvals
        approval_ids = []
        for i in range(3):
            approval_id = await approval_system.create_approval_request(
                approval_type=ApprovalType.EMAIL_CONTENT_REVIEW,
                resource_id=100 + i,
                resource_data=sample_resource_data,
                workflow_execution_id=f'test-bulk-{i}',
                timeout_minutes=60
            )
            approval_ids.append(approval_id)

        # Bulk approve
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'success': True})
            mock_post.return_value.__aenter__.return_value = mock_response

            results = await approval_system.bulk_approve(
                approval_ids=approval_ids,
                reviewer_email='bulk@example.com',
                comments='Bulk approved'
            )

            assert len(results['approved']) == 3
            assert len(results['failed']) == 0

    @pytest.mark.asyncio
    async def test_get_pending_approvals(
        self,
        approval_system: ApprovalSystem,
        sample_resource_data: dict,
        db_session: AsyncSession
    ):
        """Test retrieving pending approvals."""

        # Create some approvals
        for i in range(3):
            await approval_system.create_approval_request(
                approval_type=ApprovalType.DEMO_SITE_REVIEW,
                resource_id=200 + i,
                resource_data=sample_resource_data,
                workflow_execution_id=f'test-pending-{i}',
                timeout_minutes=60
            )

        # Get pending approvals
        pending = await approval_system.get_pending_approvals(limit=10)

        assert len(pending) >= 3

    @pytest.mark.asyncio
    async def test_approval_statistics(
        self,
        approval_system: ApprovalSystem,
        db_session: AsyncSession
    ):
        """Test getting approval statistics."""

        stats = await approval_system.get_approval_statistics()

        assert 'by_status' in stats
        assert 'by_type' in stats
        assert 'total_approvals' in stats
        assert 'auto_approval_rate' in stats


class TestAutoApprovalEngine:
    """Test AutoApprovalEngine."""

    @pytest.fixture
    async def auto_approval(self, db_session: AsyncSession):
        """Create AutoApprovalEngine instance."""
        return AutoApprovalEngine(db_session)

    @pytest.mark.asyncio
    async def test_evaluate_auto_approval(
        self,
        auto_approval: AutoApprovalEngine,
        db_session: AsyncSession
    ):
        """Test auto-approval evaluation."""

        # Create rule
        rule = ApprovalRule(
            name='Test Auto Rule',
            description='Test rule',
            template_types=['video_review'],
            auto_approve=True,
            auto_approve_threshold=0.75,
            is_active=True,
            priority=100
        )
        db_session.add(rule)
        await db_session.commit()

        # Evaluate high-quality resource
        resource_data = {
            'quality_score': 0.85,
            'qualification_score': 0.80
        }

        should_approve, reason, score = await auto_approval.evaluate_auto_approval(
            approval_type='video_review',
            resource_data=resource_data
        )

        assert should_approve is True
        assert score >= 0.75
        assert reason is not None

    @pytest.mark.asyncio
    async def test_create_auto_approval_rule(
        self,
        auto_approval: AutoApprovalEngine,
        db_session: AsyncSession
    ):
        """Test creating an auto-approval rule."""

        rule = await auto_approval.create_auto_approval_rule(
            name='New Auto Rule',
            description='Automatically approve high-quality items',
            approval_types=['demo_site_review', 'video_review'],
            auto_approve_threshold=0.85,
            min_qualification_score=0.7,
            priority=90
        )

        assert rule.id is not None
        assert rule.name == 'New Auto Rule'
        assert rule.auto_approve is True

    @pytest.mark.asyncio
    async def test_get_rule_performance(
        self,
        auto_approval: AutoApprovalEngine,
        db_session: AsyncSession
    ):
        """Test getting rule performance metrics."""

        # Create rule
        rule = ApprovalRule(
            name='Performance Test Rule',
            description='Test',
            template_types=['email_content_review'],
            auto_approve=True,
            auto_approve_threshold=0.80,
            times_triggered=100,
            auto_approved_count=75,
            manual_review_count=25,
            is_active=True,
            priority=80
        )
        db_session.add(rule)
        await db_session.commit()

        # Get performance
        performance = await auto_approval.get_rule_performance(rule.id)

        assert performance['times_triggered'] == 100
        assert performance['auto_approved_count'] == 75
        assert performance['approval_rate'] == 0.75


# Pytest fixtures

@pytest.fixture
async def db_session():
    """Create test database session."""
    # This would be implemented with your actual test database setup
    # For now, returning a mock
    from unittest.mock import AsyncMock
    session = AsyncMock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
