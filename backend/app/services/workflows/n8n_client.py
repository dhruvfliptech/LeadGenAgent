"""
N8N API Client

Client for interacting with N8N API to trigger workflows,
check execution status, and retrieve results.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class N8NClientError(Exception):
    """N8N client error"""
    pass


class N8NClient:
    """
    N8N API Client

    Handles communication with N8N instance via API.
    Supports both n8n.cloud and self-hosted instances.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize N8N client

        Args:
            api_url: N8N API URL (defaults to settings)
            api_key: N8N API key (defaults to settings)
            timeout: Request timeout in seconds
        """
        self.api_url = (api_url or getattr(settings, 'N8N_API_URL', None) or '').rstrip('/')
        self.api_key = api_key or getattr(settings, 'N8N_API_KEY', None)
        self.timeout = timeout

        if not self.api_url:
            logger.warning("N8N API URL not configured")
        if not self.api_key:
            logger.warning("N8N API key not configured")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    async def trigger_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any],
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """
        Trigger an N8N workflow

        Args:
            workflow_id: N8N workflow ID
            data: Input data for the workflow
            wait_for_completion: Wait for workflow to complete

        Returns:
            Execution response from N8N

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url or not self.api_key:
            raise N8NClientError("N8N API not configured")

        url = f"{self.api_url}/workflows/{workflow_id}/execute"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=data,
                    headers=self._get_headers(),
                    params={"waitTill": "completion" if wait_for_completion else "execution"}
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Triggered N8N workflow {workflow_id}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"N8N API error: {e.response.status_code} - {e.response.text}")
            raise N8NClientError(f"Failed to trigger workflow: {e.response.text}")
        except Exception as e:
            logger.error(f"N8N client error: {str(e)}")
            raise N8NClientError(f"N8N client error: {str(e)}")

    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Get workflow execution details

        Args:
            execution_id: N8N execution ID

        Returns:
            Execution details

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url or not self.api_key:
            raise N8NClientError("N8N API not configured")

        url = f"{self.api_url}/executions/{execution_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"N8N API error: {e.response.status_code}")
            raise N8NClientError(f"Failed to get execution: {e.response.text}")
        except Exception as e:
            logger.error(f"N8N client error: {str(e)}")
            raise N8NClientError(f"N8N client error: {str(e)}")

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow details

        Args:
            workflow_id: N8N workflow ID

        Returns:
            Workflow details

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url or not self.api_key:
            raise N8NClientError("N8N API not configured")

        url = f"{self.api_url}/workflows/{workflow_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"N8N API error: {e.response.status_code}")
            raise N8NClientError(f"Failed to get workflow: {e.response.text}")
        except Exception as e:
            logger.error(f"N8N client error: {str(e)}")
            raise N8NClientError(f"N8N client error: {str(e)}")

    async def list_workflows(
        self,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all workflows

        Args:
            active_only: Only return active workflows

        Returns:
            List of workflows

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url or not self.api_key:
            raise N8NClientError("N8N API not configured")

        url = f"{self.api_url}/workflows"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params={"active": "true"} if active_only else {}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("data", [])

        except httpx.HTTPStatusError as e:
            logger.error(f"N8N API error: {e.response.status_code}")
            raise N8NClientError(f"Failed to list workflows: {e.response.text}")
        except Exception as e:
            logger.error(f"N8N client error: {str(e)}")
            raise N8NClientError(f"N8N client error: {str(e)}")

    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution

        Args:
            execution_id: N8N execution ID

        Returns:
            True if cancelled successfully

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url or not self.api_key:
            raise N8NClientError("N8N API not configured")

        url = f"{self.api_url}/executions/{execution_id}/cancel"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                logger.info(f"Cancelled N8N execution {execution_id}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"N8N API error: {e.response.status_code}")
            raise N8NClientError(f"Failed to cancel execution: {e.response.text}")
        except Exception as e:
            logger.error(f"N8N client error: {str(e)}")
            raise N8NClientError(f"N8N client error: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test connection to N8N API

        Returns:
            True if connection successful
        """
        if not self.api_url or not self.api_key:
            return False

        try:
            await self.list_workflows()
            return True
        except Exception as e:
            logger.error(f"N8N connection test failed: {str(e)}")
            return False

    async def trigger_webhook(
        self,
        webhook_path: str,
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """
        Trigger an N8N webhook

        Args:
            webhook_path: Webhook path (e.g., "my-webhook")
            data: Data to send to webhook
            method: HTTP method (GET, POST, etc.)

        Returns:
            Webhook response

        Raises:
            N8NClientError: If request fails
        """
        if not self.api_url:
            raise N8NClientError("N8N API URL not configured")

        # Webhook URLs are typically: https://n8n.example.com/webhook/webhook-path
        base_url = self.api_url.replace('/api/v1', '')
        url = f"{base_url}/webhook/{webhook_path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=data)
                else:
                    response = await client.request(
                        method.upper(),
                        url,
                        json=data,
                        headers={"Content-Type": "application/json"}
                    )

                response.raise_for_status()

                # Try to parse JSON, fallback to text
                try:
                    return response.json()
                except:
                    return {"response": response.text}

        except httpx.HTTPStatusError as e:
            logger.error(f"Webhook error: {e.response.status_code}")
            raise N8NClientError(f"Failed to trigger webhook: {e.response.text}")
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            raise N8NClientError(f"Webhook error: {str(e)}")


# Singleton instance
_n8n_client: Optional[N8NClient] = None


def get_n8n_client() -> N8NClient:
    """Get N8N client singleton"""
    global _n8n_client
    if _n8n_client is None:
        _n8n_client = N8NClient()
    return _n8n_client
