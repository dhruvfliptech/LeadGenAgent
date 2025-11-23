"""
LinkedIn Contacts API Endpoints

Provides REST API for:
- CSV import of LinkedIn contacts
- Contact management (CRUD operations)
- OAuth 2.0 authentication flow
- Message sending (single and bulk)
- Analytics and statistics

Complete integration with the LinkedIn contact import and messaging system.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.api.deps import get_db
from app.models.linkedin_contacts import (
    LinkedInContact,
    LinkedInMessage,
    LinkedInConnection,
)
from app.schemas.linkedin_contacts import (
    LinkedInContactCreate,
    LinkedInContactUpdate,
    LinkedInContactResponse,
    LinkedInContactListResponse,
    LinkedInContactFilters,
    LinkedInContactStats,
    CSVImportRequest,
    CSVImportPreview,
    CSVImportResponse,
    CSVFieldMapping,
    LinkedInMessageCreate,
    LinkedInMessageUpdate,
    LinkedInMessageResponse,
    LinkedInMessageListResponse,
    LinkedInBulkMessageCreate,
    LinkedInBulkMessageResponse,
    LinkedInMessageStats,
    LinkedInOAuthInitiate,
    LinkedInOAuthCallback,
    LinkedInConnectionResponse,
    LinkedInConnectionUpdate,
    LinkedInDashboardStats,
    LinkedInExportRequest,
)
from app.services.linkedin_import_service import LinkedInImportService
from app.services.linkedin_messaging_service import LinkedInMessagingService

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Contact Management Endpoints
# ============================================================================

@router.get("/contacts", response_model=LinkedInContactListResponse)
async def list_contacts(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    can_message: Optional[bool] = None,
    has_email: Optional[bool] = None,
    import_batch_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
):
    """
    List LinkedIn contacts with filtering and pagination.

    Supports filtering by:
    - Search query (name, company, position)
    - Company, position, status
    - Messaging capability
    - Import batch
    - Tags
    """
    query = db.query(LinkedInContact)

    # Apply filters
    if search:
        search_filter = or_(
            LinkedInContact.first_name.ilike(f"%{search}%"),
            LinkedInContact.last_name.ilike(f"%{search}%"),
            LinkedInContact.company.ilike(f"%{search}%"),
            LinkedInContact.position.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    if company:
        query = query.filter(LinkedInContact.company.ilike(f"%{company}%"))

    if position:
        query = query.filter(LinkedInContact.position.ilike(f"%{position}%"))

    if status:
        query = query.filter(LinkedInContact.status == status)

    if can_message is not None:
        query = query.filter(LinkedInContact.can_message == can_message)

    if has_email is not None:
        if has_email:
            query = query.filter(LinkedInContact.email.isnot(None))
        else:
            query = query.filter(LinkedInContact.email.is_(None))

    if import_batch_id:
        query = query.filter(LinkedInContact.import_batch_id == import_batch_id)

    if tags:
        # Filter contacts that have any of the specified tags
        for tag in tags:
            query = query.filter(LinkedInContact.tags.contains([tag]))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    contacts = query.order_by(LinkedInContact.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert to response models
    contact_responses = [LinkedInContactResponse.from_orm(c) for c in contacts]

    return LinkedInContactListResponse(
        contacts=contact_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/contacts", response_model=LinkedInContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: LinkedInContactCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new LinkedIn contact manually.
    """
    # Check for duplicate
    existing = None
    if contact_data.linkedin_url:
        existing = db.query(LinkedInContact).filter(
            LinkedInContact.linkedin_url == contact_data.linkedin_url
        ).first()
    elif contact_data.email:
        existing = db.query(LinkedInContact).filter(
            LinkedInContact.email == contact_data.email
        ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact already exists with this LinkedIn URL or email",
        )

    # Create contact
    contact = LinkedInContact(**contact_data.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)

    logger.info(f"Created LinkedIn contact: {contact.id}")
    return LinkedInContactResponse.from_orm(contact)


@router.get("/contacts/{contact_id}", response_model=LinkedInContactResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn contact by ID.
    """
    contact = db.query(LinkedInContact).get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found",
        )

    return LinkedInContactResponse.from_orm(contact)


@router.put("/contacts/{contact_id}", response_model=LinkedInContactResponse)
async def update_contact(
    contact_id: int,
    contact_update: LinkedInContactUpdate,
    db: Session = Depends(get_db),
):
    """
    Update LinkedIn contact.
    """
    contact = db.query(LinkedInContact).get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found",
        )

    # Update fields
    update_data = contact_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    logger.info(f"Updated LinkedIn contact: {contact_id}")
    return LinkedInContactResponse.from_orm(contact)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete LinkedIn contact.
    """
    contact = db.query(LinkedInContact).get(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact {contact_id} not found",
        )

    db.delete(contact)
    db.commit()

    logger.info(f"Deleted LinkedIn contact: {contact_id}")
    return None


# ============================================================================
# CSV Import Endpoints
# ============================================================================

@router.post("/import/preview", response_model=CSVImportPreview)
async def preview_csv_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Preview CSV import before actually importing.

    Validates file format, detects columns, and shows sample contacts.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    # Preview import
    service = LinkedInImportService(db)
    preview = await service.preview_csv(content_str)

    return preview


@router.post("/import/csv", response_model=CSVImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    skip_duplicates: bool = Query(True),
    deduplicate_by: str = Query('linkedin_url', regex='^(linkedin_url|email|name)$'),
    tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Import LinkedIn contacts from CSV file.

    Supports LinkedIn's standard Connections.csv export format.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV",
        )

    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    # Create import request
    import_request = CSVImportRequest(
        filename=file.filename,
        field_mapping=CSVFieldMapping(),
        tags=tags or [],
        skip_duplicates=skip_duplicates,
        deduplicate_by=deduplicate_by,
    )

    # Import contacts
    service = LinkedInImportService(db)
    result = await service.import_csv(content_str, import_request)

    logger.info(
        f"CSV import complete: {result.imported} imported, "
        f"{result.skipped} skipped, {result.failed} failed"
    )

    return result


@router.get("/import/batches")
async def list_import_batches(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """
    List all import batches with statistics.
    """
    service = LinkedInImportService(db)
    batches = await service.get_import_batches(limit=limit)

    return {
        "batches": batches,
        "total": len(batches),
    }


@router.delete("/import/batches/{batch_id}")
async def delete_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete all contacts from an import batch.
    """
    service = LinkedInImportService(db)
    contacts_deleted, leads_deleted = await service.delete_import_batch(batch_id)

    return {
        "batch_id": batch_id,
        "contacts_deleted": contacts_deleted,
        "leads_deleted": leads_deleted,
    }


@router.post("/export/csv")
async def export_contacts_csv(
    export_request: LinkedInExportRequest,
    db: Session = Depends(get_db),
):
    """
    Export LinkedIn contacts to CSV.
    """
    service = LinkedInImportService(db)

    # Build filters dict
    filters = {}
    if export_request.filters:
        if export_request.filters.status:
            filters['status'] = export_request.filters.status
        if export_request.filters.company:
            filters['company'] = export_request.filters.company
        if export_request.filters.import_batch_id:
            filters['import_batch_id'] = export_request.filters.import_batch_id

    # Generate CSV
    csv_content = await service.export_contacts_to_csv(filters)

    # Return as streaming response
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=linkedin_contacts_{datetime.now().strftime('%Y%m%d')}.csv"
        },
    )


# ============================================================================
# OAuth Endpoints
# ============================================================================

@router.get("/oauth/authorize")
async def initiate_oauth(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
):
    """
    Initiate LinkedIn OAuth flow.

    Redirects to LinkedIn authorization page.
    """
    service = LinkedInMessagingService(db)

    try:
        auth_url = service.get_authorization_url(state=state)
        return RedirectResponse(url=auth_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/oauth/callback")
async def oauth_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Handle LinkedIn OAuth callback.

    Exchanges authorization code for access token and creates connection.
    """
    service = LinkedInMessagingService(db)

    try:
        connection = await service.create_connection(code)
        return {
            "success": True,
            "connection_id": connection.id,
            "profile_name": connection.profile_name,
            "profile_email": connection.profile_email,
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}",
        )


@router.get("/oauth/status", response_model=Optional[LinkedInConnectionResponse])
async def get_oauth_status(
    db: Session = Depends(get_db),
):
    """
    Get current OAuth connection status.

    Returns the active LinkedIn connection or None.
    """
    service = LinkedInMessagingService(db)
    connection = service.get_active_connection()

    if not connection:
        return None

    return LinkedInConnectionResponse.from_orm(connection)


@router.get("/connections", response_model=List[LinkedInConnectionResponse])
async def list_connections(
    db: Session = Depends(get_db),
):
    """
    List all LinkedIn connections.
    """
    connections = db.query(LinkedInConnection).order_by(
        LinkedInConnection.created_at.desc()
    ).all()

    return [LinkedInConnectionResponse.from_orm(c) for c in connections]


@router.get("/connections/{connection_id}", response_model=LinkedInConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn connection by ID.
    """
    connection = db.query(LinkedInConnection).get(connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )

    return LinkedInConnectionResponse.from_orm(connection)


@router.put("/connections/{connection_id}", response_model=LinkedInConnectionResponse)
async def update_connection(
    connection_id: int,
    connection_update: LinkedInConnectionUpdate,
    db: Session = Depends(get_db),
):
    """
    Update LinkedIn connection.
    """
    connection = db.query(LinkedInConnection).get(connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )

    # Update fields
    update_data = connection_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(connection, field, value)

    db.commit()
    db.refresh(connection)

    return LinkedInConnectionResponse.from_orm(connection)


@router.post("/connections/{connection_id}/validate")
async def validate_connection(
    connection_id: int,
    db: Session = Depends(get_db),
):
    """
    Validate LinkedIn connection and refresh token if needed.
    """
    service = LinkedInMessagingService(db)
    is_valid, error = await service.validate_connection(connection_id)

    return {
        "connection_id": connection_id,
        "is_valid": is_valid,
        "error": error,
    }


# ============================================================================
# Messaging Endpoints
# ============================================================================

@router.post("/messages/send", response_model=LinkedInMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: LinkedInMessageCreate,
    db: Session = Depends(get_db),
):
    """
    Send message to a LinkedIn contact.
    """
    service = LinkedInMessagingService(db)

    try:
        message = await service.send_message(
            contact_id=message_data.contact_id,
            message_create=message_data,
        )

        return LinkedInMessageResponse.from_orm(message)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.post("/messages/bulk-send", response_model=LinkedInBulkMessageResponse)
async def send_bulk_messages(
    bulk_request: LinkedInBulkMessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Send messages to multiple contacts.

    Messages are queued and sent in the background with staggered timing.
    """
    service = LinkedInMessagingService(db)

    # Queue messages in background
    background_tasks.add_task(
        service.send_bulk_messages,
        bulk_request,
    )

    # Estimate completion time
    total_minutes = len(bulk_request.contact_ids) * bulk_request.stagger_minutes
    estimated_completion = datetime.utcnow() + timedelta(minutes=total_minutes)

    return LinkedInBulkMessageResponse(
        total_requested=len(bulk_request.contact_ids),
        queued=len(bulk_request.contact_ids),
        failed=0,
        estimated_completion=estimated_completion,
        message_ids=[],
        errors=[],
    )


@router.get("/messages", response_model=LinkedInMessageListResponse)
async def list_messages(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    contact_id: Optional[int] = None,
    campaign_id: Optional[int] = None,
    status: Optional[str] = None,
    message_type: Optional[str] = None,
):
    """
    List LinkedIn messages with filtering and pagination.
    """
    query = db.query(LinkedInMessage)

    # Apply filters
    if contact_id:
        query = query.filter(LinkedInMessage.contact_id == contact_id)

    if campaign_id:
        query = query.filter(LinkedInMessage.campaign_id == campaign_id)

    if status:
        query = query.filter(LinkedInMessage.status == status)

    if message_type:
        query = query.filter(LinkedInMessage.message_type == message_type)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    messages = query.order_by(LinkedInMessage.created_at.desc()).offset(offset).limit(page_size).all()

    # Convert to response models
    message_responses = [LinkedInMessageResponse.from_orm(m) for m in messages]

    return LinkedInMessageListResponse(
        messages=message_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/messages/{message_id}", response_model=LinkedInMessageResponse)
async def get_message(
    message_id: int,
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn message by ID.
    """
    message = db.query(LinkedInMessage).get(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found",
        )

    return LinkedInMessageResponse.from_orm(message)


@router.post("/messages/process-queue")
async def process_message_queue(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Process pending message queue.

    Sends all pending messages that are ready to be sent.
    """
    service = LinkedInMessagingService(db)

    # Process queue in background
    background_tasks.add_task(service.process_message_queue)

    return {
        "status": "queued",
        "message": "Message queue processing started",
    }


# ============================================================================
# Analytics and Statistics Endpoints
# ============================================================================

@router.get("/stats/contacts", response_model=LinkedInContactStats)
async def get_contact_stats(
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn contact statistics.
    """
    total_contacts = db.query(func.count(LinkedInContact.id)).scalar()

    active_contacts = db.query(func.count(LinkedInContact.id)).filter(
        LinkedInContact.status == 'active'
    ).scalar()

    archived_contacts = db.query(func.count(LinkedInContact.id)).filter(
        LinkedInContact.status == 'archived'
    ).scalar()

    blocked_contacts = db.query(func.count(LinkedInContact.id)).filter(
        LinkedInContact.status == 'blocked'
    ).scalar()

    messageable_contacts = db.query(func.count(LinkedInContact.id)).filter(
        LinkedInContact.can_message == True
    ).scalar()

    contacts_with_email = db.query(func.count(LinkedInContact.id)).filter(
        LinkedInContact.email.isnot(None)
    ).scalar()

    # Top companies
    companies = db.query(
        LinkedInContact.company,
        func.count(LinkedInContact.id).label('count')
    ).filter(
        LinkedInContact.company.isnot(None)
    ).group_by(LinkedInContact.company).order_by(
        func.count(LinkedInContact.id).desc()
    ).limit(10).all()

    contacts_by_company = {company: count for company, count in companies if company}

    # Top industries
    industries = db.query(
        LinkedInContact.industry,
        func.count(LinkedInContact.id).label('count')
    ).filter(
        LinkedInContact.industry.isnot(None)
    ).group_by(LinkedInContact.industry).order_by(
        func.count(LinkedInContact.id).desc()
    ).limit(10).all()

    contacts_by_industry = {industry: count for industry, count in industries if industry}

    # Recent imports
    recent_imports = await LinkedInImportService(db).get_import_batches(limit=5)

    return LinkedInContactStats(
        total_contacts=total_contacts or 0,
        active_contacts=active_contacts or 0,
        archived_contacts=archived_contacts or 0,
        blocked_contacts=blocked_contacts or 0,
        messageable_contacts=messageable_contacts or 0,
        contacts_with_email=contacts_with_email or 0,
        contacts_by_company=contacts_by_company,
        contacts_by_industry=contacts_by_industry,
        recent_imports=recent_imports,
    )


@router.get("/stats/messages", response_model=LinkedInMessageStats)
async def get_message_stats(
    db: Session = Depends(get_db),
):
    """
    Get LinkedIn message statistics.
    """
    total_messages = db.query(func.count(LinkedInMessage.id)).scalar()

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    sent_today = db.query(func.count(LinkedInMessage.id)).filter(
        and_(
            LinkedInMessage.status == 'sent',
            LinkedInMessage.sent_at >= today,
        )
    ).scalar()

    pending_messages = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.status == 'pending'
    ).scalar()

    failed_messages = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.status == 'failed'
    ).scalar()

    # Calculate rates
    sent_count = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.status.in_(['sent', 'delivered', 'read'])
    ).scalar() or 0

    delivered_count = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.status.in_(['delivered', 'read'])
    ).scalar() or 0

    read_count = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.status == 'read'
    ).scalar() or 0

    replied_count = db.query(func.count(LinkedInMessage.id)).filter(
        LinkedInMessage.replied == True
    ).scalar() or 0

    delivery_rate = (delivered_count / sent_count * 100) if sent_count > 0 else 0
    read_rate = (read_count / delivered_count * 100) if delivered_count > 0 else 0
    response_rate = (replied_count / sent_count * 100) if sent_count > 0 else 0

    # Messages by status
    status_counts = db.query(
        LinkedInMessage.status,
        func.count(LinkedInMessage.id).label('count')
    ).group_by(LinkedInMessage.status).all()

    messages_by_status = {status: count for status, count in status_counts}

    # Messages by campaign
    campaign_counts = db.query(
        LinkedInMessage.campaign_id,
        func.count(LinkedInMessage.id).label('count')
    ).filter(
        LinkedInMessage.campaign_id.isnot(None)
    ).group_by(LinkedInMessage.campaign_id).all()

    messages_by_campaign = {str(campaign_id): count for campaign_id, count in campaign_counts}

    return LinkedInMessageStats(
        total_messages=total_messages or 0,
        sent_today=sent_today or 0,
        pending_messages=pending_messages or 0,
        failed_messages=failed_messages or 0,
        delivery_rate=round(delivery_rate, 2),
        read_rate=round(read_rate, 2),
        response_rate=round(response_rate, 2),
        messages_by_status=messages_by_status,
        messages_by_campaign=messages_by_campaign,
        average_response_time_hours=None,  # TODO: Calculate from message timestamps
    )


@router.get("/dashboard", response_model=LinkedInDashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
):
    """
    Get comprehensive LinkedIn dashboard statistics.
    """
    contact_stats = await get_contact_stats(db)
    message_stats = await get_message_stats(db)

    service = LinkedInMessagingService(db)
    connection = service.get_active_connection()

    connection_response = None
    if connection:
        connection_response = LinkedInConnectionResponse.from_orm(connection)

    # Recent activity
    recent_messages = db.query(LinkedInMessage).order_by(
        LinkedInMessage.created_at.desc()
    ).limit(10).all()

    recent_activity = [
        {
            'type': 'message',
            'id': msg.id,
            'contact_id': msg.contact_id,
            'status': msg.status,
            'created_at': msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in recent_messages
    ]

    return LinkedInDashboardStats(
        contacts=contact_stats,
        messages=message_stats,
        connection_status=connection_response,
        recent_activity=recent_activity,
    )
