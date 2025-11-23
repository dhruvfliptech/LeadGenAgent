"""
Redis Pub/Sub Manager

Manages Redis Pub/Sub connections and bridges Redis messages to WebSocket connections.
Supports multiple channels for different event types: campaigns, emails, scrapers, ai, demos, notifications.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable, Any
from datetime import datetime

import redis.asyncio as redis
from redis.asyncio.client import PubSub

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisPubSubManager:
    """
    Manages Redis Pub/Sub subscriptions and message routing to WebSocket connections.

    Features:
    - Multiple channel subscriptions
    - Pattern-based subscriptions (e.g., "campaign:*")
    - Message routing to WebSocket clients
    - Automatic reconnection on failure
    - Health monitoring
    """

    # Channel names
    CHANNEL_CAMPAIGNS = "fliptechpro:campaigns"
    CHANNEL_EMAILS = "fliptechpro:emails"
    CHANNEL_SCRAPERS = "fliptechpro:scrapers"
    CHANNEL_AI = "fliptechpro:ai"
    CHANNEL_DEMOS = "fliptechpro:demos"
    CHANNEL_NOTIFICATIONS = "fliptechpro:notifications"
    CHANNEL_LEADS = "fliptechpro:leads"
    CHANNEL_CONVERSATIONS = "fliptechpro:conversations"

    # All available channels
    ALL_CHANNELS = [
        CHANNEL_CAMPAIGNS,
        CHANNEL_EMAILS,
        CHANNEL_SCRAPERS,
        CHANNEL_AI,
        CHANNEL_DEMOS,
        CHANNEL_NOTIFICATIONS,
        CHANNEL_LEADS,
        CHANNEL_CONVERSATIONS,
    ]

    def __init__(self):
        """Initialize Redis Pub/Sub manager."""
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[PubSub] = None
        self.subscriptions: Dict[str, Set[Callable]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10

    async def connect(self) -> bool:
        """
        Connect to Redis and initialize Pub/Sub.

        Returns:
            bool: True if connected successfully
        """
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL not configured, Pub/Sub disabled")
            return False

        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            # Test connection
            await self.redis_client.ping()

            # Create pub/sub instance
            self.pubsub = self.redis_client.pubsub()

            logger.info("Redis Pub/Sub connected successfully")
            self._reconnect_attempts = 0
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis Pub/Sub: {e}")
            self.redis_client = None
            self.pubsub = None
            return False

    async def disconnect(self):
        """Disconnect from Redis Pub/Sub."""
        self._running = False

        # Cancel listener task
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        # Unsubscribe from all channels
        if self.pubsub:
            try:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            except Exception as e:
                logger.error(f"Error closing pubsub: {e}")

        # Close Redis connection
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.error(f"Error closing Redis client: {e}")

        self.redis_client = None
        self.pubsub = None
        logger.info("Redis Pub/Sub disconnected")

    async def subscribe(self, channel: str, callback: Callable):
        """
        Subscribe to a Redis channel.

        Args:
            channel: Channel name to subscribe to
            callback: Async callback function to handle messages
        """
        async with self._lock:
            if channel not in self.subscriptions:
                self.subscriptions[channel] = set()

            self.subscriptions[channel].add(callback)

            # Subscribe to Redis channel if not already subscribed
            if self.pubsub:
                try:
                    await self.pubsub.subscribe(channel)
                    logger.info(f"Subscribed to Redis channel: {channel}")
                except Exception as e:
                    logger.error(f"Failed to subscribe to {channel}: {e}")

    async def unsubscribe(self, channel: str, callback: Callable):
        """
        Unsubscribe from a Redis channel.

        Args:
            channel: Channel name
            callback: Callback to remove
        """
        async with self._lock:
            if channel in self.subscriptions:
                self.subscriptions[channel].discard(callback)

                # If no more callbacks, unsubscribe from Redis
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]
                    if self.pubsub:
                        try:
                            await self.pubsub.unsubscribe(channel)
                            logger.info(f"Unsubscribed from Redis channel: {channel}")
                        except Exception as e:
                            logger.error(f"Failed to unsubscribe from {channel}: {e}")

    async def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Channel name
            message: Message dictionary (will be JSON serialized)

        Returns:
            bool: True if published successfully
        """
        if not self.redis_client:
            logger.warning("Redis client not connected, cannot publish message")
            return False

        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            # Serialize message
            message_json = json.dumps(message)

            # Publish to Redis
            await self.redis_client.publish(channel, message_json)

            logger.debug(f"Published to {channel}: {message.get('type', 'unknown')}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")
            return False

    async def start_listener(self):
        """
        Start listening for Redis Pub/Sub messages.

        This runs in the background and routes messages to registered callbacks.
        """
        if self._running:
            logger.warning("Listener already running")
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Redis Pub/Sub listener started")

    async def stop_listener(self):
        """Stop the Pub/Sub listener."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        logger.info("Redis Pub/Sub listener stopped")

    async def _listen_loop(self):
        """Main loop for listening to Redis Pub/Sub messages."""
        while self._running:
            try:
                if not self.pubsub:
                    logger.warning("Pub/Sub not initialized, attempting reconnect...")
                    if await self.connect():
                        # Re-subscribe to all channels
                        for channel in list(self.subscriptions.keys()):
                            await self.pubsub.subscribe(channel)
                    else:
                        await asyncio.sleep(5)
                        continue

                # Get next message
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message["type"] == "message":
                    await self._handle_message(message)

                await asyncio.sleep(0.01)  # Small delay to prevent tight loop

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in Redis listener loop: {e}")

                # Attempt reconnection
                self._reconnect_attempts += 1
                if self._reconnect_attempts > self._max_reconnect_attempts:
                    logger.error("Max reconnect attempts reached, stopping listener")
                    break

                await asyncio.sleep(min(self._reconnect_attempts * 2, 30))  # Exponential backoff

    async def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming Redis Pub/Sub message.

        Args:
            message: Redis message dictionary
        """
        try:
            channel = message["channel"]
            data = message["data"]

            # Parse JSON data
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in message from {channel}: {data}")
                return

            # Get callbacks for this channel
            callbacks = self.subscriptions.get(channel, set())

            # Call all registered callbacks
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(channel, parsed_data)
                    else:
                        callback(channel, parsed_data)
                except Exception as e:
                    logger.error(f"Error in callback for {channel}: {e}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        channel: Optional[str] = None,
        room: Optional[str] = None,
    ) -> bool:
        """
        Publish an event with standardized format.

        Args:
            event_type: Event type (e.g., "campaign:launched")
            data: Event data
            channel: Optional channel override (defaults to channel based on event type)
            room: Optional room identifier for targeted messages

        Returns:
            bool: True if published successfully
        """
        # Determine channel from event type if not specified
        if not channel:
            channel = self._get_channel_for_event(event_type)

        # Build message
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if room:
            message["room"] = room

        return await self.publish(channel, message)

    def _get_channel_for_event(self, event_type: str) -> str:
        """
        Determine the appropriate channel for an event type.

        Args:
            event_type: Event type (e.g., "campaign:launched")

        Returns:
            str: Channel name
        """
        prefix = event_type.split(":")[0]

        channel_map = {
            "campaign": self.CHANNEL_CAMPAIGNS,
            "email": self.CHANNEL_EMAILS,
            "scraper": self.CHANNEL_SCRAPERS,
            "ai": self.CHANNEL_AI,
            "demo": self.CHANNEL_DEMOS,
            "notification": self.CHANNEL_NOTIFICATIONS,
            "lead": self.CHANNEL_LEADS,
            "conversation": self.CHANNEL_CONVERSATIONS,
        }

        return channel_map.get(prefix, self.CHANNEL_NOTIFICATIONS)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of Redis Pub/Sub connection.

        Returns:
            dict: Health check results
        """
        healthy = False
        error = None

        try:
            if self.redis_client:
                await self.redis_client.ping()
                healthy = True
        except Exception as e:
            error = str(e)

        return {
            "healthy": healthy,
            "connected": self.redis_client is not None,
            "running": self._running,
            "subscriptions": len(self.subscriptions),
            "channels": list(self.subscriptions.keys()),
            "reconnect_attempts": self._reconnect_attempts,
            "error": error,
        }


# Global instance
redis_pubsub_manager = RedisPubSubManager()
