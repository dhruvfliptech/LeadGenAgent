"""
API endpoints for notification management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from datetime import datetime

from app.core.database import get_db
from app.models.notifications import (
    Notification, NotificationChannel, NotificationDelivery,
    NotificationPreference, NotificationTemplate, NotificationDigest,
    WebSocketConnection, NotificationType, NotificationPriority
)
from app.services.notification_service import notification_service
from pydantic import BaseModel


router = APIRouter()


# Pydantic models
class NotificationCreate(BaseModel):
    notification_type: str
    title: str
    message: str
    user_id: Optional[str] = None
    broadcast: bool = False
    priority: str = "normal"
    channels: List[str] = ["websocket"]
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    priority: str
    title: str
    message: str
    user_id: Optional[str]
    broadcast: bool
    source_type: Optional[str]
    source_id: Optional[int]
    channels: List[str]
    status: str
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationChannelCreate(BaseModel):
    name: str
    channel_type: str
    description: Optional[str] = None
    configuration: Dict[str, Any] = {}
    webhook_url: Optional[str] = None
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    rate_limit_per_hour: Optional[int] = None


class NotificationChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: str
    description: Optional[str]
    is_active: bool
    configuration: Dict[str, Any]
    webhook_url: Optional[str]
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    total_sent: int
    successful_sent: int
    failed_sent: int
    success_rate: float
    is_healthy: bool
    last_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceCreate(BaseModel):
    user_id: str
    notification_type: str
    enabled: bool = True
    channels: List[str] = ["websocket"]
    priority_threshold: str = "normal"
    quiet_hours_enabled: bool = False
    quiet_start_hour: int = 22
    quiet_end_hour: int = 8
    timezone: str = "UTC"
    max_per_hour: Optional[int] = None
    max_per_day: Optional[int] = None
    digest_enabled: bool = False
    digest_frequency_hours: int = 24


class NotificationPreferenceUpdate(BaseModel):
    enabled: Optional[bool] = None
    channels: Optional[List[str]] = None
    priority_threshold: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_start_hour: Optional[int] = None
    quiet_end_hour: Optional[int] = None
    timezone: Optional[str] = None
    max_per_hour: Optional[int] = None
    max_per_day: Optional[int] = None
    digest_enabled: Optional[bool] = None
    digest_frequency_hours: Optional[int] = None


class NotificationPreferenceResponse(BaseModel):
    id: int
    user_id: str
    notification_type: str
    enabled: bool
    channels: List[str]
    priority_threshold: str
    quiet_hours_enabled: bool
    quiet_start_hour: int
    quiet_end_hour: int
    timezone: str
    max_per_hour: Optional[int]
    max_per_day: Optional[int]
    digest_enabled: bool
    digest_frequency_hours: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationTemplateCreate(BaseModel):
    name: str
    notification_type: str
    channel_type: str
    title_template: str
    message_template: str
    variables: Optional[Dict[str, Any]] = None
    format_config: Optional[Dict[str, Any]] = None


class NotificationTemplateResponse(BaseModel):
    id: int
    name: str
    notification_type: str
    channel_type: str
    title_template: str
    message_template: str
    variables: Optional[Dict[str, Any]]
    format_config: Optional[Dict[str, Any]]
    usage_count: int
    last_used_at: Optional[datetime]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification endpoints
@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications with filtering."""
    from datetime import timedelta
    
    query = select(Notification)
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(Notification.created_at >= cutoff_date)
    
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    if status:
        query = query.where(Notification.status == status)
    if user_id:
        query = query.where(Notification.user_id == user_id)
    if priority:
        query = query.where(Notification.priority == priority)
    
    result = await db.execute(query.order_by(Notification.created_at.desc()).offset(skip).limit(limit))
    notifications = result.scalars().all()
    return notifications


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific notification."""
    notification = select(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification."""
    try:
        # Validate notification type
        valid_types = [t.value for t in NotificationType]
        if notification_data.notification_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid notification type. Must be one of: {valid_types}"
            )
        
        # Validate priority
        valid_priorities = [p.value for p in NotificationPriority]
        if notification_data.priority not in valid_priorities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid priority. Must be one of: {valid_priorities}"
            )
        
        notification = await notification_service.create_notification(
            notification_type=notification_data.notification_type,
            title=notification_data.title,
            message=notification_data.message,
            user_id=notification_data.user_id,
            broadcast=notification_data.broadcast,
            priority=notification_data.priority,
            channels=notification_data.channels,
            data=notification_data.data,
            scheduled_at=notification_data.scheduled_at,
            expires_at=notification_data.expires_at
        )
        
        return notification
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/mark-read")
async def mark_notification_read(notification_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a notification as read."""
    notification = select(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    user_id: str = Query(...),
    notification_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read for a user."""
    query = select(Notification).filter(
        Notification.user_id == user_id,
        Notification.read_at.is_(None)
    )
    
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.read_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": f"Marked {len(notifications)} notifications as read"}


# Channel endpoints
@router.get("/channels/", response_model=List[NotificationChannelResponse])
async def get_notification_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get notification channels."""
    query = select(NotificationChannel)
    
    if channel_type:
        query = query.where(NotificationChannel.channel_type == channel_type)
    if is_active is not None:
        query = query.where(NotificationChannel.is_active == is_active)
    
    result = await db.execute(query.offset(skip).limit(limit))
    channels = result.scalars().all()
    return channels


@router.post("/channels/", response_model=NotificationChannelResponse)
async def create_notification_channel(
    channel_data: NotificationChannelCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification channel."""
    channel = NotificationChannel(**channel_data.dict())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


@router.put("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def update_notification_channel(
    channel_id: int,
    channel_data: NotificationChannelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a notification channel."""
    channel = select(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    update_data = channel_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)
    
    channel.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(channel)
    return channel


@router.post("/channels/{channel_id}/test")
async def test_notification_channel(channel_id: int, db: AsyncSession = Depends(get_db)):
    """Test a notification channel."""
    channel = select(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    try:
        # Create test notification
        test_notification = await notification_service.create_notification(
            notification_type="system_alert",
            title="Test Notification",
            message=f"This is a test message for channel '{channel.name}'",
            channels=[channel.channel_type],
            priority="normal"
        )
        
        return {
            "message": "Test notification sent",
            "notification_id": test_notification.id,
            "channel_type": channel.channel_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Channel test failed: {str(e)}")


# Preference endpoints
@router.get("/preferences/", response_model=List[NotificationPreferenceResponse])
async def get_notification_preferences(
    user_id: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get notification preferences."""
    query = select(NotificationPreference)
    
    if user_id:
        query = query.where(NotificationPreference.user_id == user_id)
    if notification_type:
        query = query.where(NotificationPreference.notification_type == notification_type)
    
    result = await db.execute(query)
    preferences = result.scalars().all()
    return preferences


@router.post("/preferences/", response_model=NotificationPreferenceResponse)
async def create_notification_preference(
    preference_data: NotificationPreferenceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a notification preference."""
    # Check if preference already exists
    existing = select(NotificationPreference).filter(
        NotificationPreference.user_id == preference_data.user_id,
        NotificationPreference.notification_type == preference_data.notification_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Preference already exists for this user and notification type"
        )
    
    preference = NotificationPreference(**preference_data.dict())
    db.add(preference)
    await db.commit()
    await db.refresh(preference)
    return preference


@router.put("/preferences/{preference_id}", response_model=NotificationPreferenceResponse)
async def update_notification_preference(
    preference_id: int,
    preference_data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a notification preference."""
    preference = select(NotificationPreference).filter(
        NotificationPreference.id == preference_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    
    update_data = preference_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preference, field, value)
    
    preference.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(preference)
    return preference


# Template endpoints
@router.get("/templates/", response_model=List[NotificationTemplateResponse])
async def get_notification_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Optional[str] = Query(None),
    channel_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get notification templates."""
    query = select(NotificationTemplate)
    
    if notification_type:
        query = query.where(NotificationTemplate.notification_type == notification_type)
    if channel_type:
        query = query.where(NotificationTemplate.channel_type == channel_type)
    if is_active is not None:
        query = query.where(NotificationTemplate.is_active == is_active)
    
    result = await db.execute(query.offset(skip).limit(limit))
    templates = result.scalars().all()
    return templates


@router.post("/templates/", response_model=NotificationTemplateResponse)
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a notification template."""
    template = NotificationTemplate(**template_data.dict())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


# Analytics endpoints
@router.get("/analytics/overview")
async def get_notification_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get notification analytics."""
    try:
        analytics = notification_service.get_notification_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/deliveries")
async def get_delivery_analytics(
    channel_id: Optional[int] = Query(None),
    notification_type: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Get notification delivery analytics."""
    from datetime import timedelta
    
    query = select(NotificationDelivery).join(Notification)
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(Notification.created_at >= cutoff_date)
    
    if channel_id:
        query = query.where(NotificationDelivery.channel_id == channel_id)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    result = await db.execute(query)
    deliveries = result.scalars().all()
    
    # Calculate stats
    total_deliveries = len(deliveries)
    successful_deliveries = len([d for d in deliveries if d.status == "delivered"])
    failed_deliveries = len([d for d in deliveries if d.status == "failed"])
    
    # Average delivery time
    delivered_times = [d.delivery_time_ms for d in deliveries if d.delivery_time_ms]
    avg_delivery_time = sum(delivered_times) / len(delivered_times) if delivered_times else 0
    
    # Status breakdown
    status_counts = {}
    for delivery in deliveries:
        status_counts[delivery.status] = status_counts.get(delivery.status, 0) + 1
    
    return {
        "total_deliveries": total_deliveries,
        "successful_deliveries": successful_deliveries,
        "failed_deliveries": failed_deliveries,
        "success_rate": (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
        "average_delivery_time_ms": avg_delivery_time,
        "status_breakdown": status_counts,
        "period_days": days
    }


# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications."""
    await websocket.accept()
    
    try:
        # Register connection
        await notification_service.websocket_manager.connect(websocket, user_id)
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (ping/pong)
                data = await websocket.receive_text()
                
                # Echo back pong
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # Unregister connection
        connection_id = f"{user_id}_{id(websocket)}"
        await notification_service.websocket_manager.disconnect(connection_id)


# Configuration endpoints
@router.get("/config/types")
async def get_notification_types():
    """Get available notification types."""
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in NotificationType
        ]
    }


@router.get("/config/priorities")
async def get_notification_priorities():
    """Get available notification priorities."""
    return {
        "priorities": [
            {"value": p.value, "label": p.value.title()}
            for p in NotificationPriority
        ]
    }


@router.get("/config/channels")
async def get_available_channel_types():
    """Get available notification channel types."""
    return {
        "channels": [
            {"value": "email", "label": "Email", "description": "Send notifications via email"},
            {"value": "webhook", "label": "Webhook", "description": "Send notifications to webhook URL"},
            {"value": "slack", "label": "Slack", "description": "Send notifications to Slack"},
            {"value": "discord", "label": "Discord", "description": "Send notifications to Discord"},
            {"value": "sms", "label": "SMS", "description": "Send notifications via SMS"},
            {"value": "websocket", "label": "WebSocket", "description": "Real-time browser notifications"},
            {"value": "push", "label": "Push Notification", "description": "Push notifications to mobile devices"}
        ]
    }


# Bulk operations
@router.post("/bulk/create")
async def create_bulk_notifications(
    notifications: List[NotificationCreate],
    db: AsyncSession = Depends(get_db)
):
    """Create multiple notifications at once."""
    try:
        created_notifications = []
        
        for notification_data in notifications:
            notification = await notification_service.create_notification(
                notification_type=notification_data.notification_type,
                title=notification_data.title,
                message=notification_data.message,
                user_id=notification_data.user_id,
                broadcast=notification_data.broadcast,
                priority=notification_data.priority,
                channels=notification_data.channels,
                data=notification_data.data,
                scheduled_at=notification_data.scheduled_at,
                expires_at=notification_data.expires_at
            )
            created_notifications.append(notification)
        
        return {
            "message": f"Created {len(created_notifications)} notifications",
            "notifications": created_notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))