"""
Vercel API Integration for deploying demo sites.

This module provides a comprehensive integration with the Vercel API
for programmatically deploying demo sites, managing projects, and
tracking deployment status.

Vercel API Documentation: https://vercel.com/docs/rest-api
"""

import asyncio
import httpx
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class VercelRateLimiter:
    """
    Rate limiter for Vercel API requests.

    Vercel API limits: 20 requests/second for most endpoints.
    """

    def __init__(self, max_requests: int = 20, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a rate limit slot, waiting if necessary."""
        async with self._lock:
            now = time.time()
            # Remove requests outside the time window
            self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]

            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = self.time_window - (now - oldest_request)
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Retry acquisition
                    return await self.acquire()

            self.requests.append(now)


class DeploymentResult:
    """Result of a Vercel deployment operation."""

    def __init__(
        self,
        success: bool,
        deployment_id: Optional[str] = None,
        project_id: Optional[str] = None,
        url: Optional[str] = None,
        preview_url: Optional[str] = None,
        status: Optional[str] = None,
        build_time: Optional[float] = None,
        framework_detected: Optional[str] = None,
        regions: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.deployment_id = deployment_id
        self.project_id = project_id
        self.url = url
        self.preview_url = preview_url
        self.status = status
        self.build_time = build_time
        self.framework_detected = framework_detected
        self.regions = regions or []
        self.created_at = created_at
        self.error_message = error_message
        self.error_code = error_code
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "deployment_id": self.deployment_id,
            "project_id": self.project_id,
            "url": self.url,
            "preview_url": self.preview_url,
            "status": self.status,
            "build_time": self.build_time,
            "framework_detected": self.framework_detected,
            "regions": self.regions,
            "created_at": self.created_at,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "metadata": self.metadata
        }


class VercelDeployer:
    """
    Vercel API client for deploying demo sites.

    Handles authentication, project creation, deployments, and
    deployment status tracking with the Vercel API.
    """

    API_BASE_URL = "https://api.vercel.com"
    API_VERSION = "v13"

    def __init__(
        self,
        api_token: Optional[str] = None,
        team_id: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Initialize Vercel deployer.

        Args:
            api_token: Vercel API token (from settings if not provided)
            team_id: Vercel team ID (for team accounts)
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.api_token = api_token or settings.VERCEL_API_TOKEN
        self.team_id = team_id or settings.VERCEL_TEAM_ID
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limiter = VercelRateLimiter()

        if not self.api_token:
            raise ValueError("Vercel API token is required. Set VERCEL_API_TOKEN in settings.")

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _get_team_param(self) -> Dict[str, str]:
        """Get team parameter for API requests."""
        return {"teamId": self.team_id} if self.team_id else {}

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Make an authenticated request to Vercel API with rate limiting and retries.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt number

        Returns:
            Tuple of (success, response_data, error_message)
        """
        # Rate limiting
        await self.rate_limiter.acquire()

        url = f"{self.API_BASE_URL}/{endpoint}"

        # Add team parameter if applicable
        if params is None:
            params = {}
        params.update(self._get_team_param())

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    if retry_count < self.max_retries:
                        return await self._make_request(method, endpoint, data, params, retry_count + 1)
                    return False, None, "Rate limit exceeded after retries"

                # Handle other errors
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("error", {}).get("message", response.text)
                    logger.error(f"Vercel API error: {response.status_code} - {error_message}")

                    # Retry on server errors (5xx)
                    if response.status_code >= 500 and retry_count < self.max_retries:
                        wait_time = 2 ** retry_count  # Exponential backoff
                        logger.info(f"Retrying after {wait_time}s (attempt {retry_count + 1}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(method, endpoint, data, params, retry_count + 1)

                    return False, None, error_message

                # Success
                response_data = response.json() if response.content else {}
                return True, response_data, None

        except httpx.TimeoutException:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            return False, None, "Request timeout"

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(method, endpoint, data, params, retry_count + 1)
            return False, None, str(e)

    async def create_project(
        self,
        project_name: str,
        framework: Optional[str] = None,
        build_command: Optional[str] = None,
        output_directory: Optional[str] = None,
        install_command: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create a new Vercel project.

        Args:
            project_name: Name of the project
            framework: Framework preset (nextjs, react, vue, etc.)
            build_command: Custom build command
            output_directory: Build output directory
            install_command: Custom install command
            env_vars: Environment variables

        Returns:
            Tuple of (success, project_id, error_message)
        """
        project_data = {
            "name": project_name,
            "framework": framework
        }

        # Add build settings if provided
        if build_command or output_directory or install_command:
            project_data["buildCommand"] = build_command
            project_data["outputDirectory"] = output_directory
            project_data["installCommand"] = install_command

        # Add environment variables
        if env_vars:
            project_data["environmentVariables"] = [
                {
                    "key": key,
                    "value": value,
                    "target": ["production", "preview", "development"]
                }
                for key, value in env_vars.items()
            ]

        success, response, error = await self._make_request(
            "POST",
            f"{self.API_VERSION}/projects",
            data=project_data
        )

        if success and response:
            project_id = response.get("id")
            logger.info(f"Created Vercel project: {project_name} (ID: {project_id})")
            return True, project_id, None
        else:
            return False, None, error

    async def deploy_demo_site(
        self,
        files: Dict[str, str],
        framework: str,
        project_name: str,
        lead_id: int,
        env_vars: Optional[Dict[str, str]] = None,
        project_id: Optional[str] = None
    ) -> DeploymentResult:
        """
        Deploy a demo site to Vercel.

        Args:
            files: Dictionary of file paths to file contents
            framework: Framework type (html, react, nextjs, vue, svelte)
            project_name: Name of the project
            lead_id: Lead ID this deployment is for
            env_vars: Environment variables
            project_id: Existing project ID (creates new if not provided)

        Returns:
            DeploymentResult with deployment information
        """
        start_time = time.time()

        try:
            # Ensure project exists
            if not project_id:
                success, project_id, error = await self.create_project(
                    project_name=project_name,
                    framework=framework if framework != "html" else None,
                    env_vars=env_vars
                )
                if not success:
                    return DeploymentResult(
                        success=False,
                        error_message=f"Failed to create project: {error}"
                    )

            # Prepare files for deployment
            deployment_files = []
            total_size = 0

            for file_path, file_content in files.items():
                # Encode file content
                file_data = file_content.encode('utf-8')
                total_size += len(file_data)

                deployment_files.append({
                    "file": file_path,
                    "data": file_content  # Vercel API accepts string content
                })

            # Prepare deployment data
            deployment_data = {
                "name": project_name,
                "files": deployment_files,
                "projectSettings": {
                    "framework": framework if framework != "html" else None
                },
                "target": "production"
            }

            # Add environment variables
            if env_vars:
                deployment_data["env"] = env_vars

            # Add build settings based on framework
            if framework == "nextjs":
                deployment_data["projectSettings"]["buildCommand"] = "npm run build"
                deployment_data["projectSettings"]["outputDirectory"] = ".next"
            elif framework == "react":
                deployment_data["projectSettings"]["buildCommand"] = "npm run build"
                deployment_data["projectSettings"]["outputDirectory"] = "build"
            elif framework == "vue":
                deployment_data["projectSettings"]["buildCommand"] = "npm run build"
                deployment_data["projectSettings"]["outputDirectory"] = "dist"

            # Create deployment
            logger.info(f"Deploying {len(files)} files ({total_size} bytes) for lead {lead_id}")

            success, response, error = await self._make_request(
                "POST",
                f"{self.API_VERSION}/deployments",
                data=deployment_data
            )

            if not success or not response:
                return DeploymentResult(
                    success=False,
                    error_message=f"Deployment failed: {error}"
                )

            deployment_id = response.get("id")
            deployment_url = response.get("url")

            # Wait for deployment to complete
            final_status, deployment_info = await self._wait_for_deployment(deployment_id)

            build_time = time.time() - start_time

            if final_status == "READY":
                logger.info(f"Deployment successful: {deployment_url} (took {build_time:.2f}s)")

                return DeploymentResult(
                    success=True,
                    deployment_id=deployment_id,
                    project_id=project_id,
                    url=f"https://{deployment_url}",
                    preview_url=deployment_info.get("alias", [f"https://{deployment_url}"])[0],
                    status="ready",
                    build_time=build_time,
                    framework_detected=deployment_info.get("meta", {}).get("framework"),
                    regions=deployment_info.get("regions", []),
                    created_at=datetime.now(timezone.utc).isoformat(),
                    metadata={
                        "files_count": len(files),
                        "total_size_bytes": total_size,
                        "build_output": deployment_info.get("buildOutput")
                    }
                )
            else:
                error_msg = deployment_info.get("error", {}).get("message", "Deployment failed")
                return DeploymentResult(
                    success=False,
                    deployment_id=deployment_id,
                    project_id=project_id,
                    status=final_status.lower(),
                    error_message=error_msg,
                    build_time=build_time
                )

        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            return DeploymentResult(
                success=False,
                error_message=f"Deployment exception: {str(e)}"
            )

    async def _wait_for_deployment(
        self,
        deployment_id: str,
        max_wait_time: int = 600,
        poll_interval: int = 5
    ) -> Tuple[str, Dict]:
        """
        Wait for a deployment to complete.

        Args:
            deployment_id: Deployment ID to wait for
            max_wait_time: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds

        Returns:
            Tuple of (final_status, deployment_info)
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            success, response, error = await self._make_request(
                "GET",
                f"{self.API_VERSION}/deployments/{deployment_id}"
            )

            if not success:
                logger.error(f"Failed to get deployment status: {error}")
                return "ERROR", {"error": {"message": error}}

            status = response.get("readyState", "").upper()

            if status in ["READY", "ERROR", "CANCELLED"]:
                return status, response

            logger.debug(f"Deployment {deployment_id} status: {status}")
            await asyncio.sleep(poll_interval)

        return "ERROR", {"error": {"message": "Deployment timeout"}}

    async def get_deployment_status(self, deployment_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get the status of a deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            Tuple of (success, deployment_data, error_message)
        """
        return await self._make_request(
            "GET",
            f"{self.API_VERSION}/deployments/{deployment_id}"
        )

    async def delete_deployment(self, deployment_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a deployment.

        Args:
            deployment_id: Deployment ID to delete

        Returns:
            Tuple of (success, error_message)
        """
        success, response, error = await self._make_request(
            "DELETE",
            f"{self.API_VERSION}/deployments/{deployment_id}"
        )

        if success:
            logger.info(f"Deleted deployment: {deployment_id}")
            return True, None
        else:
            return False, error

    async def delete_project(self, project_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a Vercel project.

        Args:
            project_id: Project ID to delete

        Returns:
            Tuple of (success, error_message)
        """
        success, response, error = await self._make_request(
            "DELETE",
            f"{self.API_VERSION}/projects/{project_id}"
        )

        if success:
            logger.info(f"Deleted project: {project_id}")
            return True, None
        else:
            return False, error

    async def list_deployments(
        self,
        project_id: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        List deployments.

        Args:
            project_id: Filter by project ID
            limit: Maximum number of deployments to return

        Returns:
            Tuple of (success, deployments_list, error_message)
        """
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id

        success, response, error = await self._make_request(
            "GET",
            f"{self.API_VERSION}/deployments",
            params=params
        )

        if success and response:
            deployments = response.get("deployments", [])
            return True, deployments, None
        else:
            return False, None, error

    async def add_domain(
        self,
        project_id: str,
        domain: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a custom domain to a project.

        Args:
            project_id: Project ID
            domain: Custom domain name

        Returns:
            Tuple of (success, error_message)
        """
        success, response, error = await self._make_request(
            "POST",
            f"{self.API_VERSION}/projects/{project_id}/domains",
            data={"name": domain}
        )

        if success:
            logger.info(f"Added domain {domain} to project {project_id}")
            return True, None
        else:
            return False, error

    async def get_project_analytics(
        self,
        project_id: str,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Get analytics for a project.

        Args:
            project_id: Project ID
            from_timestamp: Start timestamp (Unix milliseconds)
            to_timestamp: End timestamp (Unix milliseconds)

        Returns:
            Tuple of (success, analytics_data, error_message)
        """
        params = {}
        if from_timestamp:
            params["from"] = from_timestamp
        if to_timestamp:
            params["to"] = to_timestamp

        success, response, error = await self._make_request(
            "GET",
            f"v1/analytics/{project_id}",
            params=params
        )

        return success, response, error

    def estimate_cost(
        self,
        files_count: int,
        total_size_bytes: int,
        estimated_page_views: int = 1000,
        estimated_build_minutes: float = 1.0
    ) -> Dict[str, float]:
        """
        Estimate Vercel deployment costs.

        Based on Vercel's Pro plan pricing ($20/month):
        - 100GB bandwidth/month included
        - 6,000 build minutes/month included
        - Additional bandwidth: $40/100GB
        - Additional build minutes: $8/500 minutes

        Args:
            files_count: Number of files
            total_size_bytes: Total size of files
            estimated_page_views: Estimated monthly page views
            estimated_build_minutes: Estimated build time in minutes

        Returns:
            Cost breakdown dictionary
        """
        # Average page size assumption (e.g., 2MB per page load)
        avg_page_size_bytes = 2 * 1024 * 1024

        # Calculate bandwidth usage
        bandwidth_gb = (estimated_page_views * avg_page_size_bytes) / (1024 ** 3)

        # Pro plan includes 100GB
        excess_bandwidth_gb = max(0, bandwidth_gb - 100)
        bandwidth_cost = (excess_bandwidth_gb / 100) * 40

        # Pro plan includes 6,000 build minutes
        excess_build_minutes = max(0, estimated_build_minutes - 6000)
        build_cost = (excess_build_minutes / 500) * 8

        total_cost = bandwidth_cost + build_cost

        return {
            "bandwidth_gb": bandwidth_gb,
            "bandwidth_cost": bandwidth_cost,
            "build_minutes": estimated_build_minutes,
            "build_cost": build_cost,
            "total_estimated_cost": total_cost,
            "monthly_base_cost": 20.0  # Pro plan
        }
