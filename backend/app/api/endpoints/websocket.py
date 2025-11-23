"""
WebSocket endpoints for real-time notifications and updates.

Enhanced with Redis Pub/Sub integration, channel subscriptions, and heartbeat monitoring.
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.redis_pubsub import redis_pubsub_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Enhanced WebSocket connection manager with channel subscriptions and Redis integration.

    Features:
    - Channel-based subscriptions
    - Room-based broadcasting
    - Heartbeat/ping mechanism
    - Redis Pub/Sub integration
    - Connection health monitoring
    """

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.channel_subscriptions: Dict[WebSocket, Set[str]] = {}  # websocket -> channels
        self.room_subscriptions: Dict[WebSocket, Set[str]] = {}  # websocket -> rooms
        self._lock = asyncio.Lock()
        self._heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
        self._redis_connected = False

    async def initialize_redis(self):
        """Initialize Redis Pub/Sub integration."""
        try:
            connected = await redis_pubsub_manager.connect()
            if connected:
                # Subscribe to all channels and route messages to WebSocket
                for channel in redis_pubsub_manager.ALL_CHANNELS:
                    await redis_pubsub_manager.subscribe(channel, self._handle_redis_message)

                # Start Redis listener
                await redis_pubsub_manager.start_listener()
                self._redis_connected = True
                logger.info("Redis Pub/Sub integration initialized")
            else:
                logger.warning("Redis Pub/Sub not available")
        except Exception as e:
            logger.error(f"Failed to initialize Redis Pub/Sub: {e}")

    async def _handle_redis_message(self, channel: str, message: Dict):
        """
        Handle messages from Redis Pub/Sub and route to WebSocket clients.

        Args:
            channel: Redis channel name
            message: Message data
        """
        try:
            # Extract room if present
            room = message.get("room")

            # Broadcast to subscribed clients
            if room:
                await self.broadcast_to_room(message, room)
            else:
                await self.broadcast_to_channel(message, channel)

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str = "default",
        channels: Optional[List[str]] = None,
    ):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
            channels: Optional list of channels to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            self.active_connections[client_id].add(websocket)

            # Initialize subscriptions
            self.channel_subscriptions[websocket] = set()
            self.room_subscriptions[websocket] = set()

            # Subscribe to channels if provided
            if channels:
                for channel in channels:
                    self.channel_subscriptions[websocket].add(channel)

        # Start heartbeat
        self._start_heartbeat(websocket)

        logger.info(f"WebSocket client connected: {client_id}, channels: {channels}")

    async def disconnect(self, websocket: WebSocket, client_id: str = "default"):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        # Stop heartbeat
        await self._stop_heartbeat(websocket)

        async with self._lock:
            # Remove from active connections
            if client_id in self.active_connections:
                self.active_connections[client_id].discard(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]

            # Remove subscriptions
            if websocket in self.channel_subscriptions:
                del self.channel_subscriptions[websocket]
            if websocket in self.room_subscriptions:
                del self.room_subscriptions[websocket]

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe_to_channel(self, websocket: WebSocket, channel: str):
        """Subscribe a WebSocket connection to a channel."""
        async with self._lock:
            if websocket in self.channel_subscriptions:
                self.channel_subscriptions[websocket].add(channel)
                logger.debug(f"WebSocket subscribed to channel: {channel}")

    async def unsubscribe_from_channel(self, websocket: WebSocket, channel: str):
        """Unsubscribe a WebSocket connection from a channel."""
        async with self._lock:
            if websocket in self.channel_subscriptions:
                self.channel_subscriptions[websocket].discard(channel)
                logger.debug(f"WebSocket unsubscribed from channel: {channel}")

    async def subscribe_to_room(self, websocket: WebSocket, room: str):
        """Subscribe a WebSocket connection to a room."""
        async with self._lock:
            if websocket in self.room_subscriptions:
                self.room_subscriptions[websocket].add(room)
                logger.debug(f"WebSocket subscribed to room: {room}")

    async def unsubscribe_from_room(self, websocket: WebSocket, room: str):
        """Unsubscribe a WebSocket connection from a room."""
        async with self._lock:
            if websocket in self.room_subscriptions:
                self.room_subscriptions[websocket].discard(room)
                logger.debug(f"WebSocket unsubscribed from room: {room}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict, client_id: str = None):
        """Broadcast a message to all connections or specific client."""
        async with self._lock:
            if client_id and client_id in self.active_connections:
                connections = list(self.active_connections[client_id])
            else:
                # Broadcast to all
                connections = []
                for conn_set in self.active_connections.values():
                    connections.extend(list(conn_set))

        # Send to all connections (outside lock to avoid blocking)
        await self._send_to_connections(connections, message)

    async def broadcast_to_channel(self, message: dict, channel: str):
        """Broadcast a message to all connections subscribed to a channel."""
        async with self._lock:
            connections = [
                ws for ws, channels in self.channel_subscriptions.items()
                if channel in channels
            ]

        await self._send_to_connections(connections, message)

    async def broadcast_to_room(self, message: dict, room: str):
        """Broadcast a message to all connections subscribed to a room."""
        async with self._lock:
            connections = [
                ws for ws, rooms in self.room_subscriptions.items()
                if room in rooms
            ]

        await self._send_to_connections(connections, message)

    async def _send_to_connections(self, connections: List[WebSocket], message: dict):
        """Send message to a list of connections with error handling."""
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for client_conns in self.active_connections.values():
                    for conn in disconnected:
                        client_conns.discard(conn)
                for conn in disconnected:
                    if conn in self.channel_subscriptions:
                        del self.channel_subscriptions[conn]
                    if conn in self.room_subscriptions:
                        del self.room_subscriptions[conn]

    def _start_heartbeat(self, websocket: WebSocket):
        """Start heartbeat task for a WebSocket connection."""
        async def heartbeat_loop():
            try:
                while True:
                    await asyncio.sleep(settings.WEBSOCKET_PING_INTERVAL)
                    try:
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    except Exception as e:
                        logger.debug(f"Heartbeat failed, connection likely closed: {e}")
                        break
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[websocket] = task

    async def _stop_heartbeat(self, websocket: WebSocket):
        """Stop heartbeat task for a WebSocket connection."""
        if websocket in self._heartbeat_tasks:
            task = self._heartbeat_tasks[websocket]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self._heartbeat_tasks[websocket]

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": self.get_connection_count(),
            "clients": len(self.active_connections),
            "total_channel_subscriptions": sum(len(subs) for subs in self.channel_subscriptions.values()),
            "total_room_subscriptions": sum(len(subs) for subs in self.room_subscriptions.values()),
            "redis_connected": self._redis_connected,
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query("default"),
    channels: Optional[str] = Query(None),
):
    """
    Main WebSocket endpoint for real-time updates.

    Clients can connect to receive:
    - Lead updates
    - Scraper progress
    - Notification events
    - System alerts

    Query Parameters:
    - client_id: Client identifier (default: "default")
    - channels: Comma-separated list of channels to subscribe to
    """
    # Parse channels
    channel_list = channels.split(",") if channels else []

    await manager.connect(websocket, client_id, channel_list)

    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "channels": channel_list,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established"
        }, websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

                elif message.get("type") == "subscribe":
                    # Subscribe to channels
                    channels_to_sub = message.get("channels", [])
                    for channel in channels_to_sub:
                        await manager.subscribe_to_channel(websocket, channel)

                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channels": channels_to_sub,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

                elif message.get("type") == "unsubscribe":
                    # Unsubscribe from channels
                    channels_to_unsub = message.get("channels", [])
                    for channel in channels_to_unsub:
                        await manager.unsubscribe_from_channel(websocket, channel)

                    await manager.send_personal_message({
                        "type": "unsubscribed",
                        "channels": channels_to_unsub,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

                elif message.get("type") == "join_room":
                    # Join a room
                    room = message.get("room")
                    if room:
                        await manager.subscribe_to_room(websocket, room)
                        await manager.send_personal_message({
                            "type": "room_joined",
                            "room": room,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)

                elif message.get("type") == "leave_room":
                    # Leave a room
                    room = message.get("room")
                    if room:
                        await manager.unsubscribe_from_room(websocket, room)
                        await manager.send_personal_message({
                            "type": "room_left",
                            "room": room,
                            "timestamp": datetime.utcnow().isoformat()
                        }, websocket)

                else:
                    # Echo unknown messages back
                    await manager.send_personal_message({
                        "type": "echo",
                        "original": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        await manager.disconnect(websocket, client_id)


@router.websocket("/ws/leads")
async def leads_websocket(websocket: WebSocket, client_id: str = "default"):
    """WebSocket endpoint specifically for lead updates."""
    await manager.connect(websocket, f"leads_{client_id}")

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "leads",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"leads_{client_id}")


@router.websocket("/ws/scraper")
async def scraper_websocket(websocket: WebSocket, client_id: str = "default"):
    """WebSocket endpoint for scraper progress updates."""
    await manager.connect(websocket, f"scraper_{client_id}")

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "scraper",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"scraper_{client_id}")


# Helper functions to send notifications through WebSocket

async def notify_lead_created(lead_id: int, lead_data: dict):
    """Notify clients about a new lead."""
    await manager.broadcast({
        "type": "lead_created",
        "lead_id": lead_id,
        "data": lead_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_lead_updated(lead_id: int, updates: dict):
    """Notify clients about a lead update."""
    await manager.broadcast({
        "type": "lead_updated",
        "lead_id": lead_id,
        "updates": updates,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_scraper_progress(progress: dict):
    """Notify clients about scraper progress."""
    await manager.broadcast({
        "type": "scraper_progress",
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat()
    }, "scraper")


async def notify_scraper_complete(results: dict):
    """Notify clients when scraping is complete."""
    await manager.broadcast({
        "type": "scraper_complete",
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }, "scraper")


async def send_notification(notification_type: str, message: str, data: dict = None):
    """Send a general notification to all connected clients."""
    await manager.broadcast({
        "type": notification_type,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    })


# Conversation-specific notification helpers

async def notify_conversation_new_reply(conversation_id: int, message_id: int, sender: str):
    """Notify clients about a new reply in a conversation."""
    await manager.broadcast({
        "type": "conversation:new_reply",
        "conversation_id": conversation_id,
        "message_id": message_id,
        "sender": sender,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_conversation_ai_ready(conversation_id: int, suggestion_id: int, confidence: float):
    """Notify clients that AI suggestion is ready."""
    await manager.broadcast({
        "type": "conversation:ai_ready",
        "conversation_id": conversation_id,
        "suggestion_id": suggestion_id,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_conversation_sent(conversation_id: int, message_id: int):
    """Notify clients that a reply was sent."""
    await manager.broadcast({
        "type": "conversation:sent",
        "conversation_id": conversation_id,
        "message_id": message_id,
        "timestamp": datetime.utcnow().isoformat()
    })


async def notify_conversation_error(conversation_id: int, error: str):
    """Notify clients about conversation error."""
    await manager.broadcast({
        "type": "conversation:error",
        "conversation_id": conversation_id,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    })


# New WebSocket Endpoints


@router.websocket("/ws/campaigns")
async def campaigns_websocket(
    websocket: WebSocket,
    client_id: str = Query("default"),
    campaign_id: Optional[int] = Query(None),
):
    """
    WebSocket endpoint for campaign updates.

    Subscribe to receive:
    - Campaign launch notifications
    - Email send progress
    - Email statistics updates
    - Campaign completion events

    Query Parameters:
    - client_id: Client identifier
    - campaign_id: Optional specific campaign ID to monitor
    """
    channels = [redis_pubsub_manager.CHANNEL_CAMPAIGNS]
    await manager.connect(websocket, f"campaigns_{client_id}", channels)

    # Subscribe to campaign room if specified
    if campaign_id:
        await manager.subscribe_to_room(websocket, f"campaign:{campaign_id}")

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "campaigns",
            "campaign_id": campaign_id,
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle room joining for specific campaigns
            if message.get("type") == "join_campaign":
                cid = message.get("campaign_id")
                if cid:
                    await manager.subscribe_to_room(websocket, f"campaign:{cid}")
                    await manager.send_personal_message({
                        "type": "campaign_joined",
                        "campaign_id": cid,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"campaigns_{client_id}")


@router.websocket("/ws/emails")
async def emails_websocket(
    websocket: WebSocket,
    client_id: str = Query("default"),
):
    """
    WebSocket endpoint for email tracking events.

    Subscribe to receive:
    - Email sent confirmations
    - Email delivery events
    - Email open tracking
    - Email click tracking
    - Bounce notifications
    - Unsubscribe events
    """
    channels = [redis_pubsub_manager.CHANNEL_EMAILS]
    await manager.connect(websocket, f"emails_{client_id}", channels)

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "emails",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"emails_{client_id}")


@router.websocket("/ws/ai")
async def ai_websocket(
    websocket: WebSocket,
    client_id: str = Query("default"),
):
    """
    WebSocket endpoint for AI processing updates.

    Subscribe to receive:
    - AI processing status
    - Response generation complete
    - Lead analysis results
    - Email content generation
    - ML model training updates
    """
    channels = [redis_pubsub_manager.CHANNEL_AI]
    await manager.connect(websocket, f"ai_{client_id}", channels)

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "ai",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"ai_{client_id}")


@router.websocket("/ws/demos")
async def demos_websocket(
    websocket: WebSocket,
    client_id: str = Query("default"),
    demo_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for demo generation progress.

    Subscribe to receive:
    - Demo generation start
    - Recording progress
    - Video composition progress
    - Upload progress
    - Demo completion with URL
    - Error notifications
    """
    channels = [redis_pubsub_manager.CHANNEL_DEMOS]
    await manager.connect(websocket, f"demos_{client_id}", channels)

    # Subscribe to demo room if specified
    if demo_id:
        await manager.subscribe_to_room(websocket, f"demo:{demo_id}")

    try:
        await manager.send_personal_message({
            "type": "connection",
            "channel": "demos",
            "demo_id": demo_id,
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle room joining for specific demos
            if message.get("type") == "join_demo":
                did = message.get("demo_id")
                if did:
                    await manager.subscribe_to_room(websocket, f"demo:{did}")
                    await manager.send_personal_message({
                        "type": "demo_joined",
                        "demo_id": did,
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, f"demos_{client_id}")


# Connection Stats Endpoint
@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.

    Returns:
        dict: Connection stats including total connections, subscriptions, etc.
    """
    stats = manager.get_stats()

    # Add Redis health
    redis_health = await redis_pubsub_manager.health_check()
    stats["redis"] = redis_health

    return {
        "success": True,
        "stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }
