"""
Conversation Management API Endpoints.

Handles email reply monitoring, AI suggestion generation, and conversation tracking.
Based on UX_FLOW_CONVERSATIONS.md section 11 requirements.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.conversation import (
    Conversation,
    ConversationMessage,
    AISuggestion,
    ConversationStatus,
    MessageDirection,
    SuggestionStatus
)
from app.models.leads import Lead
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationListItem,
    ConversationThreadResponse,
    AISuggestionResponse,
    ApproveReplyRequest,
    RejectReplyRequest,
    SendReplyRequest,
    RegenerateReplyRequest,
    ArchiveConversationRequest,
    ConversationStatsResponse,
    ConversationFilters,
    SuccessResponse,
    LeadInfo,
    MessageResponse,
    SenderRecipientInfo
)
from app.services.conversation_ai import ConversationAI, ConversationMessage as AIMessage
from app.services.ai_mvp.ai_council import AICouncil
from app.services.ai_mvp.email_sender import EmailSender, EmailSenderConfig
from app.api.endpoints.websocket import manager as ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency for ConversationAI service
async def get_conversation_ai(db: AsyncSession = Depends(get_db)) -> ConversationAI:
    """Get ConversationAI service instance."""
    # Initialize AI Council
    ai_council = AICouncil()

    # Initialize vector store (placeholder - implement based on your vector DB)
    from app.services.vector_store import VectorStore
    vector_store = VectorStore()

    return ConversationAI(ai_council=ai_council, vector_store=vector_store)


# Dependency for Email Sender
def get_email_sender() -> EmailSender:
    """Get email sender instance."""
    if not settings.SMTP_FROM_EMAIL or not settings.USER_NAME:
        raise HTTPException(
            status_code=500,
            detail="Email sender not configured. Set SMTP_FROM_EMAIL and USER_NAME in environment."
        )

    config = EmailSenderConfig(
        postmark_server_token=settings.POSTMARK_SERVER_TOKEN,  # Add to config
        from_email=settings.SMTP_FROM_EMAIL,
        from_name=settings.USER_NAME
    )
    return EmailSender(config)


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    filters: ConversationFilters = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of conversations with filtering and pagination.

    **Query Parameters:**
    - status: Filter by conversation status (active, needs_reply, waiting, archived)
    - lead_id: Filter by specific lead
    - has_pending_suggestion: Filter conversations with pending AI suggestions
    - search: Search in subject or lead name
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    - sort_by: Sort field (last_message_at, created_at, message_count)
    - sort_order: Sort order (asc, desc)

    **Returns:**
    - Paginated list of conversations with lead info
    """
    logger.info(f"Fetching conversations with filters: {filters}")

    # Build base query
    query = select(Conversation).options(selectinload(Conversation.lead))

    # Apply filters
    conditions = []

    if filters.status:
        conditions.append(Conversation.status == filters.status.value)

    if filters.lead_id:
        conditions.append(Conversation.lead_id == filters.lead_id)

    if filters.search:
        search_term = f"%{filters.search}%"
        conditions.append(
            or_(
                Conversation.subject.ilike(search_term),
                Lead.contact_name.ilike(search_term),
                Lead.title.ilike(search_term)
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count total before pagination
    count_query = select(func.count()).select_from(Conversation)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply sorting
    sort_field = getattr(Conversation, filters.sort_by)
    if filters.sort_order == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(asc(sort_field))

    # Apply pagination
    offset = (filters.page - 1) * filters.page_size
    query = query.offset(offset).limit(filters.page_size)

    # Execute query
    result = await db.execute(query)
    conversations = result.scalars().all()

    # Convert to response models
    conversation_items = []
    for conv in conversations:
        # Check for pending suggestions
        pending_query = select(func.count()).select_from(AISuggestion).where(
            and_(
                AISuggestion.conversation_id == conv.id,
                AISuggestion.status == SuggestionStatus.PENDING
            )
        )
        pending_result = await db.execute(pending_query)
        has_pending = pending_result.scalar_one() > 0

        conversation_items.append(
            ConversationListItem(
                id=conv.id,
                lead=LeadInfo(
                    id=conv.lead.id,
                    name=conv.lead.contact_name or "Unknown",
                    email=conv.lead.email or conv.lead.reply_email,
                    title=conv.lead.title
                ),
                subject=conv.subject,
                status=conv.status.value,
                message_count=conv.message_count,
                last_message_at=conv.last_message_at,
                last_inbound_at=conv.last_inbound_at,
                last_outbound_at=conv.last_outbound_at,
                has_pending_suggestion=has_pending,
                created_at=conv.created_at
            )
        )

    return ConversationListResponse(
        conversations=conversation_items,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        has_more=(offset + len(conversations)) < total
    )


@router.get("/{conversation_id}", response_model=ConversationThreadResponse)
async def get_conversation_thread(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full conversation thread with all messages and pending AI suggestions.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Returns:**
    - Complete conversation thread with messages ordered chronologically
    - Any pending AI suggestions
    """
    logger.info(f"Fetching conversation thread: {conversation_id}")

    # Query conversation with relationships
    query = select(Conversation).options(
        selectinload(Conversation.lead),
        selectinload(Conversation.messages),
        selectinload(Conversation.ai_suggestions)
    ).where(Conversation.id == conversation_id)

    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {conversation_id} not found"
        )

    # Convert messages
    messages = []
    for msg in sorted(conversation.messages, key=lambda m: m.sent_at):
        messages.append(
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                direction=msg.direction.value,
                sender=SenderRecipientInfo(
                    email=msg.sender_email,
                    name=msg.sender_name
                ),
                recipient=SenderRecipientInfo(
                    email=msg.recipient_email,
                    name=msg.recipient_name
                ),
                subject=msg.subject,
                body_text=msg.body_text,
                body_html=msg.body_html,
                sent_at=msg.sent_at,
                read_at=msg.read_at,
                is_read=msg.is_read,
                created_at=msg.created_at,
                attachments=msg.attachments or []
            )
        )

    # Get pending suggestions
    pending_suggestions = [
        s for s in conversation.ai_suggestions
        if s.status == SuggestionStatus.PENDING
    ]

    suggestions = []
    for sug in pending_suggestions:
        suggestions.append(AISuggestionResponse(**sug.to_dict()))

    return ConversationThreadResponse(
        id=conversation.id,
        lead=LeadInfo(
            id=conversation.lead.id,
            name=conversation.lead.contact_name or "Unknown",
            email=conversation.lead.email or conversation.lead.reply_email,
            title=conversation.lead.title
        ),
        subject=conversation.subject,
        status=conversation.status.value,
        message_count=conversation.message_count,
        last_message_at=conversation.last_message_at,
        last_inbound_at=conversation.last_inbound_at,
        last_outbound_at=conversation.last_outbound_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        archived_at=conversation.archived_at,
        messages=messages,
        pending_suggestions=suggestions
    )


@router.get("/{conversation_id}/ai-suggestion", response_model=AISuggestionResponse)
async def get_ai_suggestion(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending AI suggestion for a conversation.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Returns:**
    - The most recent pending AI suggestion if available
    """
    logger.info(f"Fetching AI suggestion for conversation: {conversation_id}")

    # Get most recent pending suggestion
    query = select(AISuggestion).where(
        and_(
            AISuggestion.conversation_id == conversation_id,
            AISuggestion.status == SuggestionStatus.PENDING
        )
    ).order_by(desc(AISuggestion.created_at)).limit(1)

    result = await db.execute(query)
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(
            status_code=404,
            detail="No pending AI suggestion found for this conversation"
        )

    return AISuggestionResponse(**suggestion.to_dict())


@router.post("/{conversation_id}/approve", response_model=SuccessResponse)
async def approve_and_send_reply(
    conversation_id: int,
    request: ApproveReplyRequest,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender)
):
    """
    Approve AI suggestion and send email reply.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Request Body:**
    - suggestion_id: ID of the AI suggestion to approve
    - edited_body: Optional edited version (if user made changes)
    - edited_subject: Optional edited subject

    **Returns:**
    - Success response with sent message details

    **Side Effects:**
    - Sends email via Postmark
    - Updates conversation status
    - Marks suggestion as approved
    - Emits WebSocket event
    """
    logger.info(f"Approving reply for conversation {conversation_id}, suggestion {request.suggestion_id}")

    # Get suggestion
    suggestion_query = select(AISuggestion).where(
        and_(
            AISuggestion.id == request.suggestion_id,
            AISuggestion.conversation_id == conversation_id
        )
    )
    result = await db.execute(suggestion_query)
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(status_code=404, detail="AI suggestion not found")

    if suggestion.status != SuggestionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Suggestion already {suggestion.status}. Cannot approve."
        )

    # Get conversation and lead
    conv_query = select(Conversation).options(
        selectinload(Conversation.lead)
    ).where(Conversation.id == conversation_id)
    conv_result = await db.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    lead = conversation.lead
    recipient_email = lead.email or lead.reply_email

    if not recipient_email:
        raise HTTPException(status_code=400, detail="Lead has no email address")

    # Prepare email content
    final_body = request.edited_body or suggestion.suggested_body
    final_subject = request.edited_subject or suggestion.suggested_subject or f"Re: {conversation.subject}"

    # Send email via Postmark
    try:
        send_result = await email_sender.send_email(
            to_email=recipient_email,
            subject=final_subject,
            html_body=final_body,
            text_body=final_body,  # Simple text version
            tag="conversation_reply",
            metadata={
                "conversation_id": conversation_id,
                "suggestion_id": suggestion.id,
                "lead_id": lead.id
            }
        )

        if not send_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {send_result.get('error', 'Unknown error')}"
            )

        postmark_message_id = send_result["message_id"]

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {str(e)}")

    # Create conversation message
    now = datetime.utcnow()
    message = ConversationMessage(
        conversation_id=conversation_id,
        direction=MessageDirection.OUTBOUND,
        sender_email=settings.SMTP_FROM_EMAIL,
        sender_name=settings.USER_NAME,
        recipient_email=recipient_email,
        recipient_name=lead.contact_name,
        subject=final_subject,
        body_text=final_body,
        body_html=final_body,
        postmark_message_id=postmark_message_id,
        sent_at=now,
        is_read=True
    )
    db.add(message)

    # Update suggestion
    suggestion.status = SuggestionStatus.EDITED if request.edited_body else SuggestionStatus.APPROVED
    suggestion.approved_at = now
    suggestion.sent_at = now
    suggestion.sent_message_id = message.id
    if request.edited_body:
        suggestion.edited_body = request.edited_body

    # Update conversation
    conversation.last_message_at = now
    conversation.last_outbound_at = now
    conversation.message_count += 1
    conversation.status = ConversationStatus.WAITING  # Waiting for their response

    await db.commit()

    # Emit WebSocket event
    await ws_manager.broadcast({
        "type": "conversation:sent",
        "conversation_id": conversation_id,
        "message_id": message.id,
        "timestamp": now.isoformat()
    })

    return SuccessResponse(
        success=True,
        message="Reply sent successfully",
        data={
            "conversation_id": conversation_id,
            "message_id": message.id,
            "postmark_message_id": postmark_message_id
        }
    )


@router.post("/{conversation_id}/reject", response_model=SuccessResponse)
async def reject_ai_suggestion(
    conversation_id: int,
    request: RejectReplyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject AI suggestion.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Request Body:**
    - suggestion_id: ID of the AI suggestion to reject
    - reason: Optional reason for rejection

    **Returns:**
    - Success response
    """
    logger.info(f"Rejecting suggestion {request.suggestion_id} for conversation {conversation_id}")

    # Get suggestion
    query = select(AISuggestion).where(
        and_(
            AISuggestion.id == request.suggestion_id,
            AISuggestion.conversation_id == conversation_id
        )
    )
    result = await db.execute(query)
    suggestion = result.scalar_one_or_none()

    if not suggestion:
        raise HTTPException(status_code=404, detail="AI suggestion not found")

    if suggestion.status != SuggestionStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Suggestion already {suggestion.status}. Cannot reject."
        )

    # Update suggestion
    suggestion.status = SuggestionStatus.REJECTED
    suggestion.rejected_at = datetime.utcnow()
    suggestion.feedback_notes = request.reason

    await db.commit()

    return SuccessResponse(
        success=True,
        message="AI suggestion rejected",
        data={"suggestion_id": request.suggestion_id}
    )


@router.post("/{conversation_id}/reply", response_model=SuccessResponse)
async def send_custom_reply(
    conversation_id: int,
    request: SendReplyRequest,
    db: AsyncSession = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender)
):
    """
    Send custom reply (not AI-generated).

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Request Body:**
    - subject: Email subject
    - body: Email body (plain text or HTML)
    - body_html: Optional HTML version

    **Returns:**
    - Success response with sent message details
    """
    logger.info(f"Sending custom reply for conversation {conversation_id}")

    # Get conversation and lead
    query = select(Conversation).options(
        selectinload(Conversation.lead)
    ).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    lead = conversation.lead
    recipient_email = lead.email or lead.reply_email

    if not recipient_email:
        raise HTTPException(status_code=400, detail="Lead has no email address")

    # Send email
    try:
        send_result = await email_sender.send_email(
            to_email=recipient_email,
            subject=request.subject,
            html_body=request.body_html or request.body,
            text_body=request.body,
            tag="conversation_custom_reply",
            metadata={
                "conversation_id": conversation_id,
                "lead_id": lead.id,
                "custom_reply": True
            }
        )

        if not send_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email: {send_result.get('error')}"
            )

        postmark_message_id = send_result["message_id"]

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email send failed: {str(e)}")

    # Create message record
    now = datetime.utcnow()
    message = ConversationMessage(
        conversation_id=conversation_id,
        direction=MessageDirection.OUTBOUND,
        sender_email=settings.SMTP_FROM_EMAIL,
        sender_name=settings.USER_NAME,
        recipient_email=recipient_email,
        recipient_name=lead.contact_name,
        subject=request.subject,
        body_text=request.body,
        body_html=request.body_html,
        postmark_message_id=postmark_message_id,
        sent_at=now,
        is_read=True
    )
    db.add(message)

    # Update conversation
    conversation.last_message_at = now
    conversation.last_outbound_at = now
    conversation.message_count += 1
    conversation.status = ConversationStatus.WAITING

    await db.commit()

    # Emit WebSocket event
    await ws_manager.broadcast({
        "type": "conversation:sent",
        "conversation_id": conversation_id,
        "message_id": message.id,
        "custom_reply": True,
        "timestamp": now.isoformat()
    })

    return SuccessResponse(
        success=True,
        message="Custom reply sent successfully",
        data={
            "conversation_id": conversation_id,
            "message_id": message.id,
            "postmark_message_id": postmark_message_id
        }
    )


@router.post("/{conversation_id}/regenerate", response_model=AISuggestionResponse)
async def regenerate_ai_suggestion(
    conversation_id: int,
    request: RegenerateReplyRequest,
    db: AsyncSession = Depends(get_db),
    conversation_ai: ConversationAI = Depends(get_conversation_ai)
):
    """
    Regenerate AI suggestion with custom parameters.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Request Body:**
    - message_id: The inbound message to reply to
    - tone: Optional tone adjustment (more_formal, more_casual, shorter, add_humor)
    - length: Optional length preference (short, medium, long)
    - custom_prompt: Optional custom instructions

    **Returns:**
    - New AI suggestion
    """
    logger.info(f"Regenerating AI suggestion for conversation {conversation_id}")

    # Get conversation, message, and lead
    conv_query = select(Conversation).options(
        selectinload(Conversation.lead),
        selectinload(Conversation.messages)
    ).where(Conversation.id == conversation_id)
    conv_result = await db.execute(conv_query)
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get the specific message
    msg_query = select(ConversationMessage).where(
        and_(
            ConversationMessage.id == request.message_id,
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.direction == MessageDirection.INBOUND
        )
    )
    msg_result = await db.execute(msg_query)
    message = msg_result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found or not inbound")

    # Build conversation history
    history = []
    for msg in sorted(conversation.messages, key=lambda m: m.sent_at):
        history.append(
            AIMessage(
                role="user" if msg.direction == MessageDirection.OUTBOUND else "lead",
                content=msg.body_text or "",
                timestamp=msg.sent_at
            )
        )

    # Analyze reply
    reply_analysis = await conversation_ai.analyze_reply(
        reply_text=message.body_text or "",
        conversation_history=history,
        lead_id=conversation.lead_id
    )

    # Build lead context
    lead = conversation.lead
    lead_context = {
        "company_name": lead.contact_name,
        "website": lead.url,
        "title": lead.title,
        "description": lead.description
    }

    # Regenerate with custom parameters
    tone_map = {
        "more_formal": "more_formal",
        "more_casual": "more_casual",
        "shorter": "shorter",
        "add_humor": "add_humor"
    }

    generated = await conversation_ai.regenerate_reply(
        incoming_reply=message.body_text or "",
        reply_analysis=reply_analysis,
        conversation_history=history,
        lead_context=lead_context,
        tone_adjustment=tone_map.get(request.tone, "more_formal"),
        lead_id=conversation.lead_id
    )

    # Create new AI suggestion
    suggestion = AISuggestion(
        conversation_id=conversation_id,
        reply_to_message_id=message.id,
        suggested_subject=f"Re: {conversation.subject}",
        suggested_body=generated.content,
        confidence_score=generated.confidence_score,
        sentiment_analysis=reply_analysis.dict(),
        context_used=["conversation_history", "lead_profile", "tone_adjustment"],
        ai_reasoning=generated.reasoning,
        ai_provider="ai_council",
        ai_model=generated.model_used,
        status=SuggestionStatus.PENDING
    )

    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    # Emit WebSocket event
    await ws_manager.broadcast({
        "type": "conversation:ai_ready",
        "conversation_id": conversation_id,
        "suggestion_id": suggestion.id,
        "confidence": suggestion.confidence_score,
        "timestamp": datetime.utcnow().isoformat()
    })

    return AISuggestionResponse(**suggestion.to_dict())


@router.patch("/{conversation_id}/archive", response_model=SuccessResponse)
async def archive_conversation(
    conversation_id: int,
    request: ArchiveConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Archive conversation.

    **Path Parameters:**
    - conversation_id: The conversation ID

    **Request Body:**
    - reason: Optional reason for archiving

    **Returns:**
    - Success response
    """
    logger.info(f"Archiving conversation {conversation_id}")

    # Get conversation
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.status == ConversationStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="Conversation already archived")

    # Archive it
    conversation.status = ConversationStatus.ARCHIVED
    conversation.archived_at = datetime.utcnow()

    await db.commit()

    return SuccessResponse(
        success=True,
        message="Conversation archived successfully",
        data={
            "conversation_id": conversation_id,
            "archived_at": conversation.archived_at.isoformat()
        }
    )


@router.get("/stats", response_model=ConversationStatsResponse)
async def get_conversation_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation analytics and statistics.

    **Returns:**
    - Comprehensive statistics about conversations, messages, and AI performance
    """
    logger.info("Fetching conversation statistics")

    # Calculate date ranges
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Total conversations by status
    status_query = select(
        Conversation.status,
        func.count(Conversation.id).label("count")
    ).group_by(Conversation.status)
    status_result = await db.execute(status_query)
    status_counts = {row.status.value: row.count for row in status_result}

    # Messages this week
    msg_week_query = select(
        ConversationMessage.direction,
        func.count(ConversationMessage.id).label("count")
    ).where(ConversationMessage.sent_at >= week_ago).group_by(ConversationMessage.direction)
    msg_week_result = await db.execute(msg_week_query)
    msg_week_counts = {row.direction.value: row.count for row in msg_week_result}

    emails_sent_week = msg_week_counts.get("outbound", 0)
    emails_received_week = msg_week_counts.get("inbound", 0)

    # Response rate (replies / sent)
    response_rate_week = (
        (emails_received_week / emails_sent_week * 100)
        if emails_sent_week > 0 else 0.0
    )

    # AI suggestions this week
    ai_week_query = select(
        AISuggestion.status,
        func.count(AISuggestion.id).label("count")
    ).where(AISuggestion.created_at >= week_ago).group_by(AISuggestion.status)
    ai_week_result = await db.execute(ai_week_query)
    ai_week_counts = {row.status.value: row.count for row in ai_week_result}

    ai_generated = sum(ai_week_counts.values())
    ai_approved = ai_week_counts.get("approved", 0) + ai_week_counts.get("edited", 0)

    ai_approval_rate = (
        (ai_approved / ai_generated * 100)
        if ai_generated > 0 else 0.0
    )

    # Average confidence score
    avg_conf_query = select(func.avg(AISuggestion.confidence_score)).where(
        AISuggestion.created_at >= week_ago
    )
    avg_conf_result = await db.execute(avg_conf_query)
    avg_confidence = avg_conf_result.scalar_one_or_none() or 0.0

    # Email delivery metrics (placeholder - would need Postmark integration)
    # For now, return mock data
    emails_opened_week = int(emails_sent_week * 0.35)  # 35% open rate
    emails_clicked_week = int(emails_sent_week * 0.12)  # 12% click rate

    return ConversationStatsResponse(
        total_conversations=sum(status_counts.values()),
        active_conversations=status_counts.get("active", 0),
        needs_reply=status_counts.get("needs_reply", 0),
        waiting_for_response=status_counts.get("waiting", 0),
        archived_conversations=status_counts.get("archived", 0),
        emails_sent_week=emails_sent_week,
        emails_received_week=emails_received_week,
        response_rate_week=round(response_rate_week, 2),
        avg_response_time_hours=None,  # Would need to calculate from timestamps
        ai_suggestions_generated_week=ai_generated,
        ai_suggestions_approved_week=ai_approved,
        ai_approval_rate_week=round(ai_approval_rate, 2),
        avg_confidence_score=round(avg_confidence, 2) if avg_confidence else None,
        emails_opened_week=emails_opened_week,
        emails_clicked_week=emails_clicked_week,
        open_rate_week=round((emails_opened_week / emails_sent_week * 100) if emails_sent_week > 0 else 0.0, 2),
        click_rate_week=round((emails_clicked_week / emails_sent_week * 100) if emails_sent_week > 0 else 0.0, 2)
    )
