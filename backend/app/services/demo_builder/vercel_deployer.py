"""
Vercel Deployment Service

This service handles deployment of demo sites to Vercel using their API.
Manages project creation, file uploads, and deployment tracking.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VercelDeployer:
    """
    Vercel deployment service.

    Handles automatic deployment of demo sites to Vercel with
    custom subdomains and SSL certificates.
    """

    def __init__(self):
        """Initialize Vercel deployer with credentials."""
        self.api_token = os.getenv("VERCEL_API_TOKEN")
        self.team_id = os.getenv("VERCEL_TEAM_ID")
        self.base_domain = os.getenv("DEMO_SITE_BASE_DOMAIN", "demo.yourapp.com")
        self.api_base = "https://api.vercel.com"

        if not self.api_token:
            logger.warning("VERCEL_API_TOKEN not set - deployments will fail")

    async def deploy_site(
        self,
        site_name: str,
        html: str,
        css: str,
        js: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a demo site to Vercel.

        Args:
            site_name: Name for the deployment (used for subdomain)
            html: HTML content
            css: CSS content
            js: Optional JS content
            env_vars: Optional environment variables

        Returns:
            Dict with deployment info:
            {
                'deployment_id': str,
                'url': str,
                'preview_url': str,
                'status': str
            }
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            # Create deployment payload
            files = self._prepare_files(html, css, js)
            payload = self._build_deployment_payload(site_name, files, env_vars)

            # Deploy to Vercel
            deployment = await self._create_deployment(payload)

            # Extract deployment info
            result = {
                'deployment_id': deployment.get('id'),
                'vercel_project_id': deployment.get('projectId'),
                'url': deployment.get('url'),
                'preview_url': f"https://{deployment.get('url')}",
                'status': deployment.get('readyState', 'QUEUED'),
                'regions': deployment.get('regions', []),
                'created_at': deployment.get('createdAt')
            }

            logger.info(f"Deployed site '{site_name}' to {result['preview_url']}")

            return result

        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise

    def _prepare_files(
        self,
        html: str,
        css: str,
        js: Optional[str]
    ) -> List[Dict[str, str]]:
        """
        Prepare files for Vercel deployment.

        Creates the file structure with proper references.
        """
        files = []

        # Create index.html with embedded styles
        complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Demo Site</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
{html}
{f'<script src="/script.js"></script>' if js else ''}
</body>
</html>"""

        files.append({
            'file': 'index.html',
            'data': complete_html
        })

        # Add CSS file
        files.append({
            'file': 'styles.css',
            'data': css
        })

        # Add JS file if provided
        if js:
            files.append({
                'file': 'script.js',
                'data': js
            })

        # Add package.json for Vercel to recognize as static site
        files.append({
            'file': 'package.json',
            'data': json.dumps({
                'name': 'demo-site',
                'version': '1.0.0',
                'private': True
            })
        })

        return files

    def _build_deployment_payload(
        self,
        site_name: str,
        files: List[Dict[str, str]],
        env_vars: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Build the Vercel deployment API payload."""
        payload = {
            'name': self._sanitize_name(site_name),
            'files': files,
            'projectSettings': {
                'framework': None,  # Static HTML
                'buildCommand': None,
                'outputDirectory': None
            },
            'target': 'production'
        }

        # Add environment variables if provided
        if env_vars:
            payload['env'] = env_vars

        # Add team ID if configured
        if self.team_id:
            payload['teamId'] = self.team_id

        return payload

    async def _create_deployment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make the Vercel API call to create deployment."""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.api_base}/v13/deployments"
        if self.team_id:
            url += f"?teamId={self.team_id}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"Vercel API error ({response.status}): {error_text}")

                return await response.json()

    async def check_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Check the status of a deployment.

        Returns:
            Dict with status info:
            {
                'status': str,  # QUEUED, BUILDING, READY, ERROR
                'url': str,
                'error': Optional[str]
            }
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            url = f"{self.api_base}/v13/deployments/{deployment_id}"
            if self.team_id:
                url += f"?teamId={self.team_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch deployment status: {response.status}")

                    data = await response.json()

                    return {
                        'status': data.get('readyState', 'UNKNOWN'),
                        'url': f"https://{data.get('url')}",
                        'error': data.get('error'),
                        'created_at': data.get('createdAt'),
                        'ready': data.get('ready', False)
                    }

        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            raise

    async def delete_deployment(self, deployment_id: str) -> bool:
        """
        Delete a deployment from Vercel.

        Args:
            deployment_id: The Vercel deployment ID

        Returns:
            True if successful
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            url = f"{self.api_base}/v13/deployments/{deployment_id}"
            if self.team_id:
                url += f"?teamId={self.team_id}"

            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    return response.status in [200, 204]

        except Exception as e:
            logger.error(f"Deployment deletion failed: {str(e)}")
            return False

    async def list_deployments(
        self,
        project_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List deployments for a project.

        Args:
            project_name: Optional project name filter
            limit: Maximum number of deployments to return

        Returns:
            List of deployment info dicts
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            url = f"{self.api_base}/v6/deployments?limit={limit}"
            if self.team_id:
                url += f"&teamId={self.team_id}"
            if project_name:
                url += f"&projectId={project_name}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to list deployments: {response.status}")

                    data = await response.json()
                    return data.get('deployments', [])

        except Exception as e:
            logger.error(f"Deployment listing failed: {str(e)}")
            return []

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize site name for Vercel.

        Vercel project names must be lowercase alphanumeric with hyphens.
        """
        import re
        # Convert to lowercase
        name = name.lower()
        # Replace spaces and underscores with hyphens
        name = re.sub(r'[\s_]+', '-', name)
        # Remove non-alphanumeric characters (except hyphens)
        name = re.sub(r'[^a-z0-9-]', '', name)
        # Remove leading/trailing hyphens
        name = name.strip('-')
        # Limit length
        name = name[:63]  # Vercel has a 63 character limit

        return name or 'demo-site'

    async def update_custom_domain(
        self,
        deployment_id: str,
        custom_domain: str
    ) -> bool:
        """
        Add a custom domain to a deployment.

        Args:
            deployment_id: The Vercel deployment ID
            custom_domain: Custom domain to add

        Returns:
            True if successful
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            url = f"{self.api_base}/v9/projects/{deployment_id}/domains"
            if self.team_id:
                url += f"?teamId={self.team_id}"

            payload = {
                'name': custom_domain
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    return response.status in [200, 201]

        except Exception as e:
            logger.error(f"Custom domain update failed: {str(e)}")
            return False

    async def get_deployment_logs(self, deployment_id: str) -> List[str]:
        """
        Retrieve build logs for a deployment.

        Args:
            deployment_id: The Vercel deployment ID

        Returns:
            List of log lines
        """
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not configured")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            url = f"{self.api_base}/v2/deployments/{deployment_id}/events"
            if self.team_id:
                url += f"?teamId={self.team_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        return []

                    # Vercel returns logs as server-sent events
                    text = await response.text()
                    logs = text.split('\n')

                    return [log for log in logs if log.strip()]

        except Exception as e:
            logger.error(f"Log retrieval failed: {str(e)}")
            return []
