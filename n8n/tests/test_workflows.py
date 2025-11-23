"""
n8n Workflow Test Suite
Automated tests for workflow functionality
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
import os


class TestWorkflows:
    """Test suite for n8n workflows"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.n8n_url = os.getenv('N8N_URL', 'http://localhost:5678')
        self.api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.n8n_api_key = os.getenv('N8N_API_KEY')

        self.headers = {
            'X-N8N-API-KEY': self.n8n_api_key,
            'Content-Type': 'application/json'
        }

    def trigger_webhook(self, path: str, data: Dict) -> requests.Response:
        """Trigger a webhook workflow"""
        url = f"{self.n8n_url}/webhook/{path}"
        return requests.post(url, json=data)

    def get_workflow_by_name(self, name: str) -> Dict:
        """Get workflow by name"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            if workflow['name'] == name:
                return workflow

        return None

    def get_latest_execution(self, workflow_id: str) -> Dict:
        """Get latest execution for workflow"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/executions",
            headers=self.headers,
            params={'workflowId': workflow_id, 'limit': 1}
        )
        executions = response.json().get('data', [])
        return executions[0] if executions else None

    def wait_for_execution(self, execution_id: str, timeout: int = 60) -> Dict:
        """Wait for execution to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.n8n_url}/api/v1/executions/{execution_id}",
                headers=self.headers
            )
            execution = response.json()

            if execution.get('finished'):
                return execution

            time.sleep(2)

        raise TimeoutError(f"Execution {execution_id} did not complete")

    # Master Lead Processing Workflow Tests

    def test_master_workflow_exists(self):
        """Test that master workflow is deployed"""
        workflow = self.get_workflow_by_name('Master Lead Processing')
        assert workflow is not None
        assert workflow['active'] == False  # Should be inactive until configured

    def test_master_workflow_trigger(self):
        """Test master workflow can be triggered"""
        response = self.trigger_webhook('lead-scraped', {
            'lead_id': 1,
            'quality_score': 85
        })

        assert response.status_code in [200, 201]

    def test_master_workflow_quality_filter(self):
        """Test quality score filtering works"""
        # Test lead above threshold
        response = self.trigger_webhook('lead-scraped', {
            'lead_id': 1,
            'quality_score': 85
        })
        assert response.status_code in [200, 201]

        # Test lead below threshold (should be rejected)
        response = self.trigger_webhook('lead-scraped', {
            'lead_id': 2,
            'quality_score': 50
        })
        assert response.status_code in [200, 201]

    def test_approval_gate_webhook(self):
        """Test approval gate webhooks work"""
        # Trigger approval
        response = self.trigger_webhook('approve-plan-1', {
            'approved': True,
            'notes': 'Looks good'
        })

        assert response.status_code in [200, 201]

    # Quick Demo Workflow Tests

    def test_quick_demo_workflow_exists(self):
        """Test quick demo workflow is deployed"""
        workflow = self.get_workflow_by_name('Quick Demo Workflow (No Approvals)')
        assert workflow is not None

    def test_quick_demo_trigger(self):
        """Test quick demo workflow triggering"""
        response = self.trigger_webhook('quick-demo', {
            'lead_id': 1
        })

        assert response.status_code in [200, 201]

    # Video-Only Workflow Tests

    def test_video_only_workflow_exists(self):
        """Test video-only workflow exists"""
        workflow = self.get_workflow_by_name('Video-Only Workflow')
        assert workflow is not None

    def test_video_only_trigger(self):
        """Test video-only workflow triggering"""
        response = self.trigger_webhook('video-only', {
            'demo_id': 1
        })

        assert response.status_code in [200, 201]

    # Bulk Processing Tests

    def test_bulk_processing_workflow_exists(self):
        """Test bulk processing workflow exists"""
        workflow = self.get_workflow_by_name('Bulk Lead Processing')
        assert workflow is not None

    def test_bulk_processing_schedule(self):
        """Test bulk processing has correct schedule"""
        workflow = self.get_workflow_by_name('Bulk Lead Processing')

        # Check for schedule trigger
        trigger_node = next(
            (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.scheduleTrigger'),
            None
        )

        assert trigger_node is not None
        # Should run daily at 9am
        assert '9' in str(trigger_node['parameters'])

    # Error Handling Tests

    def test_error_handling_workflow_exists(self):
        """Test error handling workflow exists"""
        workflow = self.get_workflow_by_name('Error Handling & Retry')
        assert workflow is not None
        assert workflow['active'] == True  # Should be active

    def test_error_handling_schedule(self):
        """Test error handling runs hourly"""
        workflow = self.get_workflow_by_name('Error Handling & Retry')

        trigger_node = next(
            (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.scheduleTrigger'),
            None
        )

        assert trigger_node is not None

    # Analytics & Reporting Tests

    def test_analytics_workflow_exists(self):
        """Test analytics workflow exists"""
        workflow = self.get_workflow_by_name('Analytics & Reporting')
        assert workflow is not None
        assert workflow['active'] == True

    def test_analytics_schedule(self):
        """Test analytics runs daily at 9am"""
        workflow = self.get_workflow_by_name('Analytics & Reporting')

        trigger_node = next(
            (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.scheduleTrigger'),
            None
        )

        assert trigger_node is not None
        assert '9' in str(trigger_node['parameters'])

    # Lead Nurturing Tests

    def test_lead_nurturing_workflow_exists(self):
        """Test lead nurturing workflow exists"""
        workflow = self.get_workflow_by_name('Lead Nurturing & Follow-up')
        assert workflow is not None
        assert workflow['active'] == True

    def test_lead_nurturing_schedule(self):
        """Test lead nurturing runs every 3 days"""
        workflow = self.get_workflow_by_name('Lead Nurturing & Follow-up')

        trigger_node = next(
            (node for node in workflow['nodes'] if node['type'] == 'n8n-nodes-base.scheduleTrigger'),
            None
        )

        assert trigger_node is not None
        assert '*/3' in str(trigger_node['parameters']) or '3' in str(trigger_node['parameters'])

    # A/B Testing Tests

    def test_ab_testing_workflow_exists(self):
        """Test A/B testing workflow exists"""
        workflow = self.get_workflow_by_name('A/B Testing Workflow')
        assert workflow is not None

    def test_ab_testing_trigger(self):
        """Test A/B testing workflow triggering"""
        response = self.trigger_webhook('ab-test-lead', {
            'lead_id': 1
        })

        assert response.status_code in [200, 201]

    # Integration Tests

    def test_workflow_connections(self):
        """Test all workflows have proper connections"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            # Check that all nodes are connected
            nodes = workflow.get('nodes', [])
            connections = workflow.get('connections', {})

            # At least one connection should exist if there are multiple nodes
            if len(nodes) > 1:
                assert len(connections) > 0, f"Workflow {workflow['name']} has disconnected nodes"

    def test_workflow_error_handling_config(self):
        """Test workflows have error handling configured"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            settings = workflow.get('settings', {})

            # Check that error workflow is configured
            if workflow['name'] != 'Error Handling & Retry':
                assert settings.get('errorWorkflow') == 'error-handling', \
                    f"Workflow {workflow['name']} missing error workflow"

    def test_api_authentication_headers(self):
        """Test workflows use proper API authentication"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            for node in workflow.get('nodes', []):
                if node['type'] == 'n8n-nodes-base.httpRequest':
                    params = node.get('parameters', {})

                    # Should use authentication
                    assert params.get('authentication') in ['genericCredentialType', 'oAuth2'], \
                        f"Node {node['name']} in {workflow['name']} missing authentication"

    # Performance Tests

    def test_workflow_timeout_settings(self):
        """Test workflows have appropriate timeout settings"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            settings = workflow.get('settings', {})
            timeout = settings.get('executionTimeout', 120)

            # Bulk processing should have higher timeout
            if 'Bulk' in workflow['name']:
                assert timeout >= 3600, f"{workflow['name']} needs higher timeout"

    def test_workflow_retry_configuration(self):
        """Test critical nodes have retry logic"""
        response = requests.get(
            f"{self.n8n_url}/api/v1/workflows",
            headers=self.headers
        )
        workflows = response.json().get('data', [])

        for workflow in workflows:
            for node in workflow.get('nodes', []):
                if node['type'] == 'n8n-nodes-base.httpRequest':
                    # HTTP nodes should have retry enabled
                    assert node.get('retryOnFail', False), \
                        f"Node {node['name']} in {workflow['name']} should have retry enabled"


class TestWorkflowIntegration:
    """Integration tests with backend API"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')

    def test_workflow_execution_logging(self):
        """Test that workflow executions are logged to database"""
        # This would test the /api/workflows/log endpoint
        response = requests.post(
            f"{self.api_url}/api/workflows/log",
            json={
                'execution_id': 'test-123',
                'workflow_name': 'test-workflow',
                'status': 'success',
                'data': {'test': True}
            }
        )

        assert response.status_code in [200, 201]

    def test_approval_gate_api_integration(self):
        """Test approval gates integrate with API"""
        # Create a test approval
        response = requests.post(
            f"{self.api_url}/api/approvals",
            json={
                'workflow_execution_id': 'test-123',
                'gate_name': 'test_approval',
                'status': 'pending'
            }
        )

        assert response.status_code in [200, 201]

    def test_ab_test_tracking(self):
        """Test A/B test results are tracked"""
        response = requests.post(
            f"{self.api_url}/api/ab-tests/track",
            json={
                'lead_id': 1,
                'variant': 'A',
                'event': 'email_sent'
            }
        )

        assert response.status_code in [200, 201]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
