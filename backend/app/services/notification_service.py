"""
Real-time notification service with multiple channel support.
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

import aiohttp
import websockets
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models.notifications import (
    Notification, NotificationChannel, NotificationDelivery, 
    NotificationPreference, NotificationTemplate, NotificationDigest,
    WebSocketConnection, NotificationType, NotificationPriority
)
from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        })


class WebSocketManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.db = None  # Will be set per request
    
    async def connect(self, websocket: websockets.WebSocketServerProtocol, user_id: str):
        """Register a new WebSocket connection."""
        try:
            connection_id = f"{user_id}_{id(websocket)}"
            
            self.connections[connection_id] = websocket
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Store connection in database
            ws_connection = WebSocketConnection(
                connection_id=connection_id,
                user_id=user_id,
                is_active=True,
                connected_at=datetime.utcnow()
            )
            self.db.add(ws_connection)
            self.db.commit()
            
            logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
            
            # Send welcome message
            welcome_msg = WebSocketMessage(
                type="connection_established",
                data={"message": "Connected to CraigLeads notifications"}
            )
            await self._send_to_connection(connection_id, welcome_msg)
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
    
    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection."""
        try:
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            # Remove from user connections
            for user_id, conn_ids in self.user_connections.items():
                if connection_id in conn_ids:
                    conn_ids.remove(connection_id)
                    if not conn_ids:  # Remove user if no connections left
                        del self.user_connections[user_id]
                    break
            
            # Update database record
            ws_connection = self.db.query(WebSocketConnection).filter(
                WebSocketConnection.connection_id == connection_id
            ).first()
            
            if ws_connection:
                ws_connection.is_active = False
                ws_connection.disconnected_at = datetime.utcnow()
                self.db.commit()
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Failed to disconnect WebSocket: {e}")
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections for a user."""
        try:
            if user_id not in self.user_connections:
                logger.debug(f"No WebSocket connections for user {user_id}")
                return False
            
            connection_ids = list(self.user_connections[user_id])
            success_count = 0
            
            for connection_id in connection_ids:
                success = await self._send_to_connection(connection_id, message)
                if success:
                    success_count += 1
            
            logger.debug(f"Sent WebSocket message to {success_count}/{len(connection_ids)} connections for user {user_id}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket message to user {user_id}: {e}")
            return False
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connected users."""
        try:
            success_count = 0
            total_connections = len(self.connections)
            
            for connection_id in list(self.connections.keys()):
                success = await self._send_to_connection(connection_id, message)
                if success:
                    success_count += 1
            
            logger.info(f"Broadcast WebSocket message to {success_count}/{total_connections} connections")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to broadcast WebSocket message: {e}")
            return False
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection."""
        try:
            if connection_id not in self.connections:
                return False
            
            websocket = self.connections[connection_id]
            await websocket.send(message.to_json())
            return True
            
        except websockets.exceptions.ConnectionClosed:
            logger.debug(f"Connection {connection_id} closed, removing")
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Failed to send message to connection {connection_id}: {e}")
            return False
    
    async def ping_all_connections(self):
        """Ping all connections to check health."""
        try:
            for connection_id in list(self.connections.keys()):
                try:
                    websocket = self.connections[connection_id]
                    pong = await websocket.ping()
                    await asyncio.wait_for(pong, timeout=10)
                    
                    # Update last ping time
                    ws_connection = self.db.query(WebSocketConnection).filter(
                        WebSocketConnection.connection_id == connection_id
                    ).first()
                    if ws_connection:
                        ws_connection.last_ping_at = datetime.utcnow()
                        self.db.commit()
                        
                except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError):
                    await self.disconnect(connection_id)
                except Exception as e:
                    logger.error(f"Ping failed for connection {connection_id}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to ping connections: {e}")


class EmailNotificationSender:
    """Handles email notification delivery."""
    
    def __init__(self):
        self.smtp_config = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD,
            "use_tls": settings.SMTP_USE_TLS
        }
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        is_html: bool = False
    ) -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False


class WebhookNotificationSender:
    """Handles webhook notification delivery."""
    
    async def send_webhook(
        self, 
        webhook_url: str, 
        payload: Dict[str, Any], 
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send webhook notification."""
        try:
            default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'CraigLeads-Notifications/1.0'
            }
            
            if headers:
                default_headers.update(headers)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=default_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook sent to {webhook_url}: {response.status}")
                        return True
                    else:
                        logger.error(f"Webhook failed to {webhook_url}: {response.status}")
                        return False
            
        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
            return False


class SlackNotificationSender:
    """Handles Slack notification delivery."""
    
    async def send_slack_message(
        self, 
        webhook_url: str, 
        message: str, 
        channel: Optional[str] = None,
        username: Optional[str] = "CraigLeads",
        icon_emoji: Optional[str] = ":robot_face:"
    ) -> bool:
        """Send Slack notification."""
        try:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji
            }
            
            if channel:
                payload["channel"] = channel
            
            return await WebhookNotificationSender().send_webhook(webhook_url, payload)
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False


class DiscordNotificationSender:
    """Handles Discord notification delivery."""
    
    async def send_discord_message(
        self, 
        webhook_url: str, 
        content: str, 
        username: Optional[str] = "CraigLeads",
        avatar_url: Optional[str] = None
    ) -> bool:
        """Send Discord notification."""
        try:
            payload = {
                "content": content,
                "username": username
            }
            
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            return await WebhookNotificationSender().send_webhook(webhook_url, payload)
            
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False


class SMSNotificationSender:
    """Handles SMS notification delivery via Twilio."""
    
    def __init__(self):
        try:
            from twilio.rest import Client
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.from_number = settings.TWILIO_FROM_NUMBER
        except ImportError:
            logger.warning("Twilio not installed, SMS notifications disabled")
            self.client = None
    
    async def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS notification."""
        try:
            if not self.client:
                logger.error("Twilio client not available")
                return False
            
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent to {to_number}: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False


class NotificationService:
    """Main notification service."""
    
    def __init__(self):
        self.db = None  # Will be set per request
        self.websocket_manager = WebSocketManager()
        self.email_sender = EmailNotificationSender()
        self.webhook_sender = WebhookNotificationSender()
        self.slack_sender = SlackNotificationSender()
        self.discord_sender = DiscordNotificationSender()
        self.sms_sender = SMSNotificationSender()
        
        # Channel senders mapping
        self.channel_senders = {
            "email": self._send_email_notification,
            "webhook": self._send_webhook_notification,
            "slack": self._send_slack_notification,
            "discord": self._send_discord_notification,
            "sms": self._send_sms_notification,
            "websocket": self._send_websocket_notification
        }
    
    async def create_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        user_id: Optional[str] = None,
        broadcast: bool = False,
        priority: str = "normal",
        channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """Create a new notification."""
        try:
            if channels is None:
                channels = ["websocket"]
            
            notification = Notification(
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                user_id=user_id,
                broadcast=broadcast,
                channels=channels,
                data=data or {},
                scheduled_at=scheduled_at,
                expires_at=expires_at
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"Created notification {notification.id}: {title}")
            
            # Send immediately if not scheduled
            if not scheduled_at or scheduled_at <= datetime.utcnow():
                await self._send_notification(notification.id)
            
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            self.db.rollback()
            raise
    
    async def _send_notification(self, notification_id: int) -> bool:
        """Send a notification through all specified channels."""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                logger.error(f"Notification {notification_id} not found")
                return False
            
            if notification.status != "pending":
                logger.warning(f"Notification {notification_id} already processed")
                return False
            
            # Check if expired
            if notification.expires_at and notification.expires_at < datetime.utcnow():
                notification.status = "expired"
                self.db.commit()
                logger.info(f"Notification {notification_id} expired")
                return False
            
            # Get user preferences if user-specific
            if notification.user_id and not notification.broadcast:
                preferences = await self._get_user_preferences(
                    notification.user_id, 
                    notification.notification_type
                )
                if not preferences or not preferences.enabled:
                    logger.info(f"Notifications disabled for user {notification.user_id}")
                    notification.status = "skipped"
                    self.db.commit()
                    return False
                
                # Filter channels based on preferences
                notification.channels = [
                    ch for ch in notification.channels 
                    if ch in preferences.channels
                ]
                
                # Check priority threshold
                priority_levels = {"low": 1, "normal": 2, "high": 3, "urgent": 4}
                if priority_levels.get(notification.priority, 2) < priority_levels.get(preferences.priority_threshold, 2):
                    logger.info(f"Notification priority too low for user {notification.user_id}")
                    notification.status = "skipped"
                    self.db.commit()
                    return False
            
            # Send through each channel
            success_count = 0
            total_channels = len(notification.channels)
            
            for channel in notification.channels:
                try:
                    success = await self._send_through_channel(notification, channel)
                    if success:
                        success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send notification {notification_id} through {channel}: {e}")
            
            # Update notification status
            if success_count > 0:
                notification.status = "sent" if success_count == total_channels else "partial"
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = "failed"
                notification.retry_count += 1
                
                # Schedule retry if under max retries
                if notification.retry_count < notification.max_retries:
                    notification.scheduled_at = datetime.utcnow() + timedelta(minutes=5)
                    notification.status = "pending"
            
            self.db.commit()
            
            logger.info(f"Sent notification {notification_id} through {success_count}/{total_channels} channels")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification_id}: {e}")
            return False
    
    async def _send_through_channel(self, notification: Notification, channel: str) -> bool:
        """Send notification through specific channel."""
        try:
            # Get channel configuration
            channel_config = self.db.query(NotificationChannel).filter(
                and_(
                    NotificationChannel.channel_type == channel,
                    NotificationChannel.is_active == True
                )
            ).first()
            
            if not channel_config:
                logger.error(f"No active configuration for channel {channel}")
                return False
            
            # Create delivery record
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel_id=channel_config.id,
                status="pending"
            )
            self.db.add(delivery)
            self.db.commit()
            self.db.refresh(delivery)
            
            # Send through channel
            sender_func = self.channel_senders.get(channel)
            if not sender_func:
                logger.error(f"No sender available for channel {channel}")
                delivery.status = "failed"
                delivery.error_message = "No sender available"
                self.db.commit()
                return False
            
            start_time = datetime.utcnow()
            success = await sender_func(notification, channel_config, delivery)
            end_time = datetime.utcnow()
            
            # Update delivery record
            delivery.delivery_time_ms = (end_time - start_time).total_seconds() * 1000
            delivery.status = "delivered" if success else "failed"
            
            # Update channel statistics
            channel_config.total_sent += 1
            if success:
                channel_config.successful_sent += 1
                channel_config.consecutive_failures = 0
                channel_config.is_healthy = True
            else:
                channel_config.failed_sent += 1
                channel_config.consecutive_failures += 1
                
                # Mark unhealthy after multiple consecutive failures
                if channel_config.consecutive_failures >= 5:
                    channel_config.is_healthy = False
            
            channel_config.last_sent_at = datetime.utcnow()
            self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send through channel {channel}: {e}")
            return False
    
    async def _send_websocket_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send WebSocket notification."""
        try:
            message = WebSocketMessage(
                type="notification",
                data={
                    "id": notification.id,
                    "type": notification.notification_type,
                    "priority": notification.priority,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data
                }
            )
            
            if notification.broadcast:
                return await self.websocket_manager.broadcast(message)
            elif notification.user_id:
                return await self.websocket_manager.send_to_user(notification.user_id, message)
            else:
                return False
                
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_email_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send email notification."""
        try:
            # Get email template
            template = self.db.query(NotificationTemplate).filter(
                and_(
                    NotificationTemplate.notification_type == notification.notification_type,
                    NotificationTemplate.channel_type == "email",
                    NotificationTemplate.is_active == True
                )
            ).first()
            
            if template:
                # Render template with notification data
                title = self._render_template(template.title_template, notification.data)
                body = self._render_template(template.message_template, notification.data)
            else:
                title = notification.title
                body = notification.message
            
            # Get user email (for now, assume user_id is email)
            to_email = notification.user_id if notification.user_id else channel_config.configuration.get("default_email")
            
            if not to_email:
                delivery.error_message = "No email address available"
                self.db.commit()
                return False
            
            return await self.email_sender.send_email(to_email, title, body)
            
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_webhook_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send webhook notification."""
        try:
            webhook_url = channel_config.webhook_url
            if not webhook_url:
                delivery.error_message = "No webhook URL configured"
                self.db.commit()
                return False
            
            payload = {
                "id": notification.id,
                "type": notification.notification_type,
                "priority": notification.priority,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "timestamp": notification.created_at.isoformat()
            }
            
            headers = channel_config.configuration.get("headers", {})
            return await self.webhook_sender.send_webhook(webhook_url, payload, headers)
            
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_slack_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send Slack notification."""
        try:
            webhook_url = channel_config.webhook_url
            if not webhook_url:
                delivery.error_message = "No Slack webhook URL configured"
                self.db.commit()
                return False
            
            config = channel_config.configuration or {}
            message = f"*{notification.title}*\n{notification.message}"
            
            return await self.slack_sender.send_slack_message(
                webhook_url=webhook_url,
                message=message,
                channel=config.get("channel"),
                username=config.get("username", "CraigLeads"),
                icon_emoji=config.get("icon_emoji", ":robot_face:")
            )
            
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_discord_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send Discord notification."""
        try:
            webhook_url = channel_config.webhook_url
            if not webhook_url:
                delivery.error_message = "No Discord webhook URL configured"
                self.db.commit()
                return False
            
            config = channel_config.configuration or {}
            content = f"**{notification.title}**\n{notification.message}"
            
            return await self.discord_sender.send_discord_message(
                webhook_url=webhook_url,
                content=content,
                username=config.get("username", "CraigLeads"),
                avatar_url=config.get("avatar_url")
            )
            
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    async def _send_sms_notification(
        self, 
        notification: Notification, 
        channel_config: NotificationChannel, 
        delivery: NotificationDelivery
    ) -> bool:
        """Send SMS notification."""
        try:
            # Get user phone number (would need user management system)
            phone_number = channel_config.configuration.get("phone_number")
            if not phone_number:
                delivery.error_message = "No phone number configured"
                self.db.commit()
                return False
            
            message = f"{notification.title}\n{notification.message}"
            return await self.sms_sender.send_sms(phone_number, message)
            
        except Exception as e:
            delivery.error_message = str(e)
            self.db.commit()
            return False
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render notification template with data."""
        try:
            rendered = template
            for key, value in data.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            return rendered
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template
    
    async def _get_user_preferences(self, user_id: str, notification_type: str) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        try:
            return self.db.query(NotificationPreference).filter(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.notification_type == notification_type
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    async def process_pending_notifications(self):
        """Process all pending notifications."""
        try:
            pending_notifications = self.db.query(Notification).filter(
                and_(
                    Notification.status == "pending",
                    or_(
                        Notification.scheduled_at.is_(None),
                        Notification.scheduled_at <= datetime.utcnow()
                    )
                )
            ).all()
            
            logger.info(f"Processing {len(pending_notifications)} pending notifications")
            
            for notification in pending_notifications:
                try:
                    await self._send_notification(notification.id)
                except Exception as e:
                    logger.error(f"Failed to process notification {notification.id}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to process pending notifications: {e}")
    
    def get_notification_analytics(self, days: int = 30) -> Dict:
        """Get notification service analytics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Overall stats
            total_notifications = self.db.query(Notification).filter(
                Notification.created_at >= cutoff_date
            ).count()
            
            sent_notifications = self.db.query(Notification).filter(
                and_(
                    Notification.created_at >= cutoff_date,
                    Notification.status == "sent"
                )
            ).count()
            
            # Channel performance
            channels = self.db.query(NotificationChannel).filter(
                NotificationChannel.is_active == True
            ).all()
            
            channel_stats = []
            for channel in channels:
                channel_stats.append({
                    "name": channel.name,
                    "type": channel.channel_type,
                    "total_sent": channel.total_sent,
                    "success_rate": channel.success_rate,
                    "is_healthy": channel.is_healthy
                })
            
            return {
                "total_notifications": total_notifications,
                "sent_notifications": sent_notifications,
                "delivery_rate": (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0,
                "active_channels": len(channels),
                "channel_stats": channel_stats,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification analytics: {e}")
            return {}


# Global service instance
notification_service = NotificationService()