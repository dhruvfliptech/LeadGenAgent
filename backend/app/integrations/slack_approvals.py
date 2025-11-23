"""
Slack Integration for Approval Notifications.

Sends interactive approval requests to Slack with action buttons.
"""

import os
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackApprovalNotifier:
    """
    Send approval requests to Slack with interactive buttons.

    Integrates with Slack's Block Kit for rich, interactive notifications.
    """

    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.bot_token = os.getenv('SLACK_BOT_TOKEN')
        self.api_base = 'https://slack.com/api'

    async def send_approval_request(
        self,
        approval_id: int,
        approval_data: Dict[str, Any],
        channel: str = "#approvals"
    ) -> Optional[Dict[str, Any]]:
        """
        Send approval request to Slack with interactive buttons.

        Args:
            approval_id: ID of approval request
            approval_data: Data to display in message
            channel: Slack channel to send to

        Returns:
            Slack API response or None if failed
        """

        if not self.webhook_url and not self.bot_token:
            logger.warning("Slack credentials not configured, skipping notification")
            return None

        message = self._build_approval_message(approval_id, approval_data)

        try:
            if self.bot_token:
                # Use Slack API for more control
                return await self._send_via_api(channel, message)
            else:
                # Use webhook for simple posting
                return await self._send_via_webhook(message)
        except Exception as e:
            logger.error(f"Failed to send Slack approval: {e}")
            return None

    def _build_approval_message(
        self,
        approval_id: int,
        approval_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build Slack message with Block Kit."""

        approval_type = approval_data.get('type', 'Unknown')
        description = approval_data.get('description', '')
        preview_url = approval_data.get('preview_url')
        timeout_at = approval_data.get('timeout_at')

        # Format timeout
        timeout_text = "No timeout"
        if timeout_at:
            if isinstance(timeout_at, str):
                timeout_at = datetime.fromisoformat(timeout_at.replace('Z', '+00:00'))
            timeout_text = f"<!date^{int(timeout_at.timestamp())}^{{date_short_pretty}} at {{time}}|{timeout_at.isoformat()}>"

        # Build header
        header_emoji = self._get_type_emoji(approval_type)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{header_emoji} Approval Required: {approval_type.replace('_', ' ').title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Approval ID:*\n{approval_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timeout:*\n{timeout_text}"
                    }
                ]
            }
        ]

        # Add description if available
        if description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{description[:500]}"
                }
            })

        # Add preview link if available
        if preview_url:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Preview:* <{preview_url}|Click to view>"
                }
            })

        # Add resource-specific details
        resource_details = self._build_resource_details(approval_data)
        if resource_details:
            blocks.append({
                "type": "section",
                "fields": resource_details
            })

        blocks.append({"type": "divider"})

        # Add action buttons
        blocks.append({
            "type": "actions",
            "block_id": f"approval_actions_{approval_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Approve",
                        "emoji": True
                    },
                    "value": f"approve_{approval_id}",
                    "action_id": f"approve_{approval_id}",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ Reject",
                        "emoji": True
                    },
                    "value": f"reject_{approval_id}",
                    "action_id": f"reject_{approval_id}",
                    "style": "danger"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 View Details",
                        "emoji": True
                    },
                    "value": f"view_{approval_id}",
                    "action_id": f"view_{approval_id}",
                    "url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/approvals/{approval_id}"
                }
            ]
        })

        # Add context
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Created at <!date^{int(datetime.utcnow().timestamp())}^{{date_short}} {{time}}|now>"
                }
            ]
        })

        return {
            "blocks": blocks,
            "text": f"Approval Required: {approval_type}"  # Fallback text
        }

    def _get_type_emoji(self, approval_type: str) -> str:
        """Get emoji for approval type."""
        emoji_map = {
            'demo_site_review': '🌐',
            'video_review': '🎥',
            'email_content_review': '📧',
            'improvement_plan_review': '📊',
            'lead_qualification': '🎯',
            'campaign_launch': '🚀',
            'budget_approval': '💰'
        }
        return emoji_map.get(approval_type, '📋')

    def _build_resource_details(self, approval_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Build resource-specific detail fields."""

        fields = []

        # Add relevant fields based on what's available
        field_mappings = {
            'business_name': 'Business',
            'category': 'Category',
            'location': 'Location',
            'quality_score': 'Quality Score',
            'qualification_score': 'Qualification',
            'estimated_value': 'Est. Value',
            'duration': 'Duration',
            'template_name': 'Template'
        }

        for key, label in field_mappings.items():
            if key in approval_data and approval_data[key]:
                value = approval_data[key]

                # Format score values
                if 'score' in key and isinstance(value, (int, float)):
                    value = f"{value:.1%}" if value <= 1 else f"{value:.1f}"

                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{label}:*\n{value}"
                })

        return fields if fields else None

    async def _send_via_api(
        self,
        channel: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message via Slack API."""

        url = f"{self.api_base}/chat.postMessage"

        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'channel': channel,
            **message
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response_data = await response.json()

                if not response_data.get('ok'):
                    logger.error(f"Slack API error: {response_data.get('error')}")
                    return None

                logger.info(f"Sent Slack approval notification to {channel}")
                return response_data

    async def _send_via_webhook(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via incoming webhook."""

        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=message) as response:
                if response.status != 200:
                    logger.error(f"Slack webhook error: {response.status}")
                    return None

                logger.info("Sent Slack approval notification via webhook")
                return {"ok": True}

    async def update_approval_message(
        self,
        channel: str,
        message_ts: str,
        approval_id: int,
        decision: str,
        reviewer: str
    ):
        """Update message after approval decision."""

        if not self.bot_token:
            return

        # Build updated message
        decision_emoji = "✅" if decision == "approved" else "❌"
        decision_text = decision.capitalize()

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{decision_emoji} Approval {decision_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Approval ID:* {approval_id}\n*Decision:* {decision_text}\n*Reviewed by:* {reviewer}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Decided at <!date^{int(datetime.utcnow().timestamp())}^{{date_short}} {{time}}|now>"
                    }
                ]
            }
        ]

        url = f"{self.api_base}/chat.update"

        headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'channel': channel,
            'ts': message_ts,
            'blocks': blocks,
            'text': f"Approval {decision_text}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_data = await response.json()

                    if not response_data.get('ok'):
                        logger.error(f"Failed to update Slack message: {response_data.get('error')}")
                        return

                    logger.info(f"Updated Slack message for approval {approval_id}")
        except Exception as e:
            logger.error(f"Error updating Slack message: {e}")

    async def send_approval_reminder(
        self,
        approval_id: int,
        approval_data: Dict[str, Any],
        channel: str,
        minutes_remaining: int
    ):
        """Send reminder for pending approval."""

        urgency = "⚠️" if minutes_remaining < 30 else "⏰"

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{urgency} *Approval Reminder*\nApproval #{approval_id} expires in *{minutes_remaining} minutes*"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Review Now"},
                            "url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/approvals/{approval_id}",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }

        if self.bot_token:
            await self._send_via_api(channel, message)
        elif self.webhook_url:
            await self._send_via_webhook(message)

    async def send_approval_timeout_notification(
        self,
        approval_id: int,
        approval_type: str,
        channel: str
    ):
        """Notify that an approval has timed out."""

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⏱️ *Approval Timeout*\nApproval #{approval_id} ({approval_type}) has timed out and was automatically rejected."
                    }
                }
            ]
        }

        if self.bot_token:
            await self._send_via_api(channel, message)
        elif self.webhook_url:
            await self._send_via_webhook(message)

    async def send_bulk_approval_summary(
        self,
        approvals_count: int,
        reviewer: str,
        channel: str
    ):
        """Send summary of bulk approval action."""

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Bulk Approval Complete*\n{reviewer} approved *{approvals_count}* items."
                    }
                }
            ]
        }

        if self.bot_token:
            await self._send_via_api(channel, message)
        elif self.webhook_url:
            await self._send_via_webhook(message)
