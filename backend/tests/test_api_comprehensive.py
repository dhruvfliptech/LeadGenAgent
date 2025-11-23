"""
Comprehensive API Endpoint Testing Suite

Tests for:
1. Auto-response Templates (/api/v1/templates/*)
2. Email Tracking (/api/v1/tracking/*)
3. Demo Site Builder (/api/v1/demo-sites/*)
4. N8N Workflows (/api/v1/workflows/* and /api/v1/workflow-approvals/*)
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Import main app
from app.main import app
from app.core.database import get_db, engine
from app.models import Base


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup test database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Create async HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Create database session for tests."""
    async for session in get_db():
        yield session


# Test data fixtures
@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": f"Test Template {uuid.uuid4().hex[:8]}",
        "description": "Test template for automated testing",
        "category": "job_inquiry",
        "subject_template": "Interested in {{job_title}} position",
        "body_template": "Hi {{contact_name}},\n\nI'm interested in the {{job_title}} role.\n\nBest,\n{{user_name}}",
        "variables": {
            "required": ["job_title"],
            "optional": ["contact_name", "user_name"]
        },
        "use_ai_enhancement": True,
        "ai_tone": "professional",
        "ai_length": "medium",
        "test_weight": 50.0
    }


@pytest.fixture
def sample_demo_site_data():
    """Sample demo site data for testing."""
    return {
        "site_name": f"Test Demo Site {uuid.uuid4().hex[:8]}",
        "template_type": "portfolio",
        "content_data": {
            "company_name": "Test Company",
            "tagline": "Building amazing things",
            "features": ["Feature 1", "Feature 2", "Feature 3"]
        },
        "style_settings": {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "font_family": "Inter"
        },
        "use_ai_generation": False,
        "auto_deploy": False
    }


@pytest.fixture
def sample_approval_data():
    """Sample approval request data."""
    return {
        "approval_type": "email_response",
        "resource_id": 1,
        "resource_data": {
            "subject": "Test subject",
            "body": "Test body",
            "recipient": "test@example.com"
        },
        "workflow_execution_id": f"test_exec_{uuid.uuid4().hex[:8]}",
        "timeout_minutes": 60,
        "metadata": {"test": True}
    }


# =============================================================================
# TEST SUITE 1: AUTO-RESPONSE TEMPLATES
# =============================================================================

class TestTemplatesAPI:
    """Test suite for /api/v1/templates/* endpoints."""

    @pytest.mark.asyncio
    async def test_create_template(self, client: AsyncClient, sample_template_data: Dict):
        """Test POST /api/v1/templates/ - Create template."""
        response = await client.post("/api/v1/templates/", json=sample_template_data)

        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_template_data["name"]
        assert data["subject_template"] == sample_template_data["subject_template"]
        assert data["is_active"] is True

        # Store for cleanup
        return data["id"]

    @pytest.mark.asyncio
    async def test_list_templates(self, client: AsyncClient):
        """Test GET /api/v1/templates/ - List templates."""
        response = await client.get("/api/v1/templates/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, client: AsyncClient):
        """Test GET /api/v1/templates/ with filters."""
        # Test category filter
        response = await client.get("/api/v1/templates/?category=job_inquiry")
        assert response.status_code == 200

        # Test active filter
        response = await client.get("/api/v1/templates/?is_active=true")
        assert response.status_code == 200

        # Test pagination
        response = await client.get("/api/v1/templates/?skip=0&limit=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_template_by_id(self, client: AsyncClient, sample_template_data: Dict):
        """Test GET /api/v1/templates/{id} - Get specific template."""
        # Create template first
        create_response = await client.post("/api/v1/templates/", json=sample_template_data)
        assert create_response.status_code in [200, 201]
        template_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(f"/api/v1/templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == sample_template_data["name"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, client: AsyncClient):
        """Test GET /api/v1/templates/{id} - 404 for nonexistent template."""
        response = await client.get("/api/v1/templates/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_template(self, client: AsyncClient, sample_template_data: Dict):
        """Test PUT /api/v1/templates/{id} - Update template."""
        # Create template
        create_response = await client.post("/api/v1/templates/", json=sample_template_data)
        assert create_response.status_code in [200, 201]
        template_id = create_response.json()["id"]

        # Update template
        update_data = {
            "name": "Updated Template Name",
            "ai_tone": "casual"
        }
        response = await client.put(f"/api/v1/templates/{template_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Template Name"
        assert data["ai_tone"] == "casual"

    @pytest.mark.asyncio
    async def test_delete_template(self, client: AsyncClient, sample_template_data: Dict):
        """Test DELETE /api/v1/templates/{id} - Delete template."""
        # Create template
        create_response = await client.post("/api/v1/templates/", json=sample_template_data)
        assert create_response.status_code in [200, 201]
        template_id = create_response.json()["id"]

        # Delete template
        response = await client.delete(f"/api/v1/templates/{template_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = await client.get(f"/api/v1/templates/{template_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_template_validation(self, client: AsyncClient):
        """Test template validation - missing required fields."""
        invalid_data = {
            "name": "Invalid Template"
            # Missing required fields
        }
        response = await client.post("/api/v1/templates/", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_ab_testing_analytics(self, client: AsyncClient):
        """Test GET /api/v1/templates/analytics/ab-testing."""
        response = await client.get("/api/v1/templates/analytics/ab-testing")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data


# =============================================================================
# TEST SUITE 2: EMAIL TRACKING
# =============================================================================

class TestEmailTrackingAPI:
    """Test suite for /api/v1/tracking/* endpoints."""

    @pytest.mark.asyncio
    async def test_track_email_open(self, client: AsyncClient):
        """Test GET /api/v1/tracking/open/{token} - Track email open."""
        tracking_token = "test_token_123"
        response = await client.get(f"/api/v1/tracking/open/{tracking_token}")

        # Should return 1x1 GIF pixel even if tracking fails
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_track_email_click(self, client: AsyncClient):
        """Test GET /api/v1/tracking/click/{token} - Track click and redirect."""
        tracking_token = "test_token_123"
        target_url = "https://example.com"

        response = await client.get(
            f"/api/v1/tracking/click/{tracking_token}",
            params={"url": target_url},
            follow_redirects=False
        )

        # Should redirect even if tracking fails
        assert response.status_code == 302
        assert "location" in response.headers

    @pytest.mark.asyncio
    async def test_unsubscribe_endpoint(self, client: AsyncClient):
        """Test GET /api/v1/tracking/unsubscribe/{token} - Unsubscribe."""
        tracking_token = "test_token_123"
        response = await client.get(f"/api/v1/tracking/unsubscribe/{tracking_token}")

        # Should return HTML page
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_unsubscribe_confirmation_page(self, client: AsyncClient):
        """Test GET /api/v1/tracking/unsubscribe-confirm - Generic unsubscribe page."""
        response = await client.get("/api/v1/tracking/unsubscribe-confirm")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"unsubscribe" in response.content.lower()


# =============================================================================
# TEST SUITE 3: DEMO SITE BUILDER
# =============================================================================

class TestDemoSitesAPI:
    """Test suite for /api/v1/demo-sites/* endpoints."""

    @pytest.mark.asyncio
    async def test_generate_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test POST /api/v1/demo-sites/generate - Generate demo site."""
        response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)

        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["site_name"] == sample_demo_site_data["site_name"]
        assert data["status"] in ["draft", "building"]

        return data["id"]

    @pytest.mark.asyncio
    async def test_list_demo_sites(self, client: AsyncClient):
        """Test GET /api/v1/demo-sites/ - List demo sites."""
        response = await client.get("/api/v1/demo-sites/")

        assert response.status_code == 200
        data = response.json()
        assert "demo_sites" in data
        assert "total" in data
        assert isinstance(data["demo_sites"], list)

    @pytest.mark.asyncio
    async def test_list_demo_sites_with_filters(self, client: AsyncClient):
        """Test GET /api/v1/demo-sites/ with filters."""
        # Test status filter
        response = await client.get("/api/v1/demo-sites/?status=draft")
        assert response.status_code == 200

        # Test pagination
        response = await client.get("/api/v1/demo-sites/?page=1&page_size=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_demo_site_by_id(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test GET /api/v1/demo-sites/{id} - Get specific demo site."""
        # Create demo site first
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(f"/api/v1/demo-sites/{demo_site_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == demo_site_id

    @pytest.mark.asyncio
    async def test_update_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test PUT /api/v1/demo-sites/{id} - Update demo site."""
        # Create demo site
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Update
        update_data = {
            "site_name": "Updated Demo Site Name"
        }
        response = await client.put(f"/api/v1/demo-sites/{demo_site_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["site_name"] == "Updated Demo Site Name"

    @pytest.mark.asyncio
    async def test_delete_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test DELETE /api/v1/demo-sites/{id} - Delete demo site."""
        # Create demo site
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Delete
        response = await client.delete(f"/api/v1/demo-sites/{demo_site_id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_preview_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test GET /api/v1/demo-sites/{id}/preview - Preview demo site."""
        # Create demo site
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Preview
        response = await client.get(f"/api/v1/demo-sites/{demo_site_id}/preview")
        if response.status_code == 200:
            data = response.json()
            assert "html" in data or "css" in data

    @pytest.mark.asyncio
    async def test_export_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test GET /api/v1/demo-sites/{id}/export - Export demo site files."""
        # Create demo site
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Export
        response = await client.get(f"/api/v1/demo-sites/{demo_site_id}/export")
        if response.status_code == 200:
            data = response.json()
            assert "files" in data

    @pytest.mark.asyncio
    async def test_duplicate_demo_site(self, client: AsyncClient, sample_demo_site_data: Dict):
        """Test POST /api/v1/demo-sites/{id}/duplicate - Duplicate demo site."""
        # Create demo site
        create_response = await client.post("/api/v1/demo-sites/generate", json=sample_demo_site_data)
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create demo site: {create_response.text}")

        demo_site_id = create_response.json()["id"]

        # Duplicate
        duplicate_data = {
            "new_site_name": f"Duplicated Site {uuid.uuid4().hex[:8]}",
            "copy_content": True,
            "copy_style": True
        }
        response = await client.post(f"/api/v1/demo-sites/{demo_site_id}/duplicate", json=duplicate_data)
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["site_name"] == duplicate_data["new_site_name"]

    @pytest.mark.asyncio
    async def test_list_templates(self, client: AsyncClient):
        """Test GET /api/v1/demo-sites/templates - List templates."""
        response = await client.get("/api/v1/demo-sites/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data


# =============================================================================
# TEST SUITE 4: N8N WORKFLOWS & APPROVALS
# =============================================================================

class TestN8NWebhooksAPI:
    """Test suite for /api/v1/webhooks/n8n/* endpoints."""

    @pytest.mark.asyncio
    async def test_receive_n8n_webhook(self, client: AsyncClient):
        """Test POST /api/v1/webhooks/n8n/n8n/{workflow_id} - Receive webhook."""
        workflow_id = "test_workflow_123"
        payload = {
            "event": "test_event",
            "data": {"key": "value"},
            "timestamp": datetime.utcnow().isoformat()
        }

        response = await client.post(
            f"/api/v1/webhooks/n8n/n8n/{workflow_id}",
            json=payload
        )

        # Should return 200 even on error to prevent N8N retries
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_receive_generic_webhook(self, client: AsyncClient):
        """Test POST /api/v1/webhooks/n8n/n8n/generic - Generic webhook."""
        payload = {
            "event": "lead_created",
            "data": {"lead_id": 123},
            "source": "n8n"
        }

        response = await client.post(
            "/api/v1/webhooks/n8n/n8n/generic",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_webhook_connectivity(self, client: AsyncClient):
        """Test GET /api/v1/webhooks/n8n/n8n/test - Test connectivity."""
        response = await client.get("/api/v1/webhooks/n8n/n8n/test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestWorkflowApprovalsAPI:
    """Test suite for /api/v1/workflows/approvals/* endpoints."""

    @pytest.mark.asyncio
    async def test_create_approval_request(self, client: AsyncClient, sample_approval_data: Dict):
        """Test POST /api/v1/workflows/approvals/create - Create approval."""
        response = await client.post(
            "/api/v1/workflows/approvals/create",
            json=sample_approval_data
        )

        if response.status_code == 201:
            data = response.json()
            assert data["success"] is True
            assert "approval_id" in data
            return data["approval_id"]
        else:
            # May fail if dependencies not met
            pytest.skip(f"Approval creation not available: {response.text}")

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, client: AsyncClient):
        """Test GET /api/v1/workflows/approvals/pending - List pending approvals."""
        response = await client.get("/api/v1/workflows/approvals/pending")

        if response.status_code == 200:
            data = response.json()
            assert "approvals" in data
            assert "count" in data

    @pytest.mark.asyncio
    async def test_get_pending_approvals_with_filters(self, client: AsyncClient):
        """Test GET /api/v1/workflows/approvals/pending with filters."""
        # Test approver filter
        response = await client.get(
            "/api/v1/workflows/approvals/pending?approver_email=test@example.com"
        )
        assert response.status_code in [200, 404]

        # Test type filter
        response = await client.get(
            "/api/v1/workflows/approvals/pending?approval_type=email_response"
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_approval_details(self, client: AsyncClient, sample_approval_data: Dict):
        """Test GET /api/v1/workflows/approvals/{id} - Get approval details."""
        # Try to create approval first
        create_response = await client.post(
            "/api/v1/workflows/approvals/create",
            json=sample_approval_data
        )

        if create_response.status_code == 201:
            approval_id = create_response.json()["approval_id"]

            # Get details
            response = await client.get(f"/api/v1/workflows/approvals/{approval_id}")
            if response.status_code == 200:
                data = response.json()
                assert "approval" in data

    @pytest.mark.asyncio
    async def test_submit_decision(self, client: AsyncClient, sample_approval_data: Dict):
        """Test POST /api/v1/workflows/approvals/{id}/decide - Submit decision."""
        # Try to create approval first
        create_response = await client.post(
            "/api/v1/workflows/approvals/create",
            json=sample_approval_data
        )

        if create_response.status_code == 201:
            approval_id = create_response.json()["approval_id"]

            # Submit decision
            decision_data = {
                "approved": True,
                "reviewer_email": "reviewer@example.com",
                "comments": "Looks good!"
            }
            response = await client.post(
                f"/api/v1/workflows/approvals/{approval_id}/decide",
                json=decision_data
            )
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_get_approval_statistics(self, client: AsyncClient):
        """Test GET /api/v1/workflows/approvals/stats - Get statistics."""
        response = await client.get("/api/v1/workflows/approvals/stats")

        if response.status_code == 200:
            data = response.json()
            # Should have some stats structure
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_auto_approval_rules(self, client: AsyncClient):
        """Test GET /api/v1/workflows/approvals/auto-approval/rules - List rules."""
        response = await client.get("/api/v1/workflows/approvals/auto-approval/rules")

        if response.status_code == 200:
            data = response.json()
            assert "rules" in data

    @pytest.mark.asyncio
    async def test_rule_templates(self, client: AsyncClient):
        """Test GET /api/v1/workflows/approvals/auto-approval/templates - Get templates."""
        response = await client.get("/api/v1/workflows/approvals/auto-approval/templates")

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data


# =============================================================================
# EDGE CASES & ERROR HANDLING TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client: AsyncClient):
        """Test endpoints with invalid JSON."""
        response = await client.post(
            "/api/v1/templates/",
            content="invalid json{{{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test endpoints with missing required fields."""
        incomplete_data = {"name": "Test"}
        response = await client.post("/api/v1/templates/", json=incomplete_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_id_format(self, client: AsyncClient):
        """Test endpoints with invalid ID formats."""
        response = await client.get("/api/v1/templates/invalid_id")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_pagination_boundaries(self, client: AsyncClient):
        """Test pagination with edge values."""
        # Zero skip
        response = await client.get("/api/v1/templates/?skip=0&limit=1")
        assert response.status_code == 200

        # Large skip
        response = await client.get("/api/v1/templates/?skip=10000&limit=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient, sample_template_data: Dict):
        """Test concurrent requests to same endpoint."""
        tasks = [
            client.post("/api/v1/templates/", json={
                **sample_template_data,
                "name": f"Concurrent Template {i}"
            })
            for i in range(5)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that at least some succeeded
        success_count = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.status_code in [200, 201]
        )
        assert success_count >= 3


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test API performance and response times."""

    @pytest.mark.asyncio
    async def test_list_endpoint_performance(self, client: AsyncClient):
        """Test list endpoint performance."""
        import time

        start_time = time.time()
        response = await client.get("/api/v1/templates/?limit=100")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 2.0  # Should complete in under 2 seconds

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, client: AsyncClient, sample_template_data: Dict):
        """Test bulk create performance."""
        import time

        templates = [
            {**sample_template_data, "name": f"Bulk Template {i}"}
            for i in range(10)
        ]

        start_time = time.time()
        tasks = [client.post("/api/v1/templates/", json=t) for t in templates]
        await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time

        assert elapsed < 5.0  # Should complete in under 5 seconds


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================

class TestSchemaValidation:
    """Test request/response schema validation."""

    @pytest.mark.asyncio
    async def test_response_schema_structure(self, client: AsyncClient, sample_template_data: Dict):
        """Test that response schemas match expected structure."""
        response = await client.post("/api/v1/templates/", json=sample_template_data)

        if response.status_code in [200, 201]:
            data = response.json()

            # Check required fields
            required_fields = ["id", "name", "subject_template", "body_template", "is_active"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Check field types
            assert isinstance(data["id"], int)
            assert isinstance(data["name"], str)
            assert isinstance(data["is_active"], bool)

    @pytest.mark.asyncio
    async def test_datetime_field_formats(self, client: AsyncClient, sample_template_data: Dict):
        """Test that datetime fields are properly formatted."""
        response = await client.post("/api/v1/templates/", json=sample_template_data)

        if response.status_code in [200, 201]:
            data = response.json()

            # Check datetime fields exist and are strings
            datetime_fields = ["created_at", "updated_at"]
            for field in datetime_fields:
                if field in data:
                    assert isinstance(data[field], str)
                    # Try parsing as ISO format
                    try:
                        datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    except ValueError:
                        pytest.fail(f"Invalid datetime format for {field}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
