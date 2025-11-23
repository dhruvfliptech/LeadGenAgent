"""
N8N Workflow Automation Services

Service modules for N8N workflow integration:
- n8n_client: N8N API client
- webhook_handler: Webhook processing
- workflow_executor: Workflow execution logic
- approval_system: Approval management
- auto_approval: AI-powered auto-approval
- workflow_monitor: Monitoring and logging
"""

from .n8n_client import N8NClient, get_n8n_client
from .webhook_handler import WebhookHandler
from .workflow_executor import WorkflowExecutor
from .approval_system import ApprovalSystem
from .auto_approval import AutoApprovalService
from .workflow_monitor import WorkflowMonitor

__all__ = [
    "N8NClient",
    "get_n8n_client",
    "WebhookHandler",
    "WorkflowExecutor",
    "ApprovalSystem",
    "AutoApprovalService",
    "WorkflowMonitor",
]
