"""
Webhook response handlers for n8n callbacks.

This module handles incoming webhooks from n8n workflows,
providing endpoints for workflow completion notifications,
approval responses, and status updates.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.api.deps import get_db
from app.models.leads import Lead
from app.models.demo_sites import DemoSite
from app.models.composed_videos import ComposedVideo
from app.models.webhook_queue import WebhookLog
from app.utils.webhook_security import WebhookSecurity
from app.core.webhook_config import webhook_config
from app.services.n8n_webhook_trigger import get_webhook_trigger

router = APIRouter()
logger = logging.getLogger(__name__)


async def verify_webhook_signature(request: Request):
    """Dependency to verify webhook signature."""
    if webhook_config.security.require_signature:
        secret = webhook_config.security.n8n_webhook_secret
        if secret:
            await WebhookSecurity.verify_n8n_webhook(request, secret)
    return True


async def log_incoming_webhook(
    request: Request,
    event_type: str,
    payload: Dict[str, Any],
    response_status: int,
    db: Session
):
    """Log incoming webhook for auditing."""
    try:
        # Get request details
        source_ip = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')

        # Create log entry
        log_entry = WebhookLog(
            direction="incoming",
            event_type=event_type,
            webhook_url=str(request.url),
            method=request.method,
            headers=dict(request.headers),
            payload=payload,
            response_status=response_status,
            source_ip=source_ip,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )

        db.add(log_entry)
        db.commit()

    except Exception as e:
        logger.error(f"Error logging incoming webhook: {str(e)}", exc_info=True)


@router.post("/n8n/demo-approval")
async def demo_approval_response(
    request: Request,
    db: Session = Depends(get_db),
    _verified: bool = Depends(verify_webhook_signature)
):
    """
    Handle demo approval decision from n8n workflow.

    This endpoint receives approval decisions for demo sites from n8n
    and continues or stops the workflow accordingly.

    Expected payload:
    {
        "demo_id": 456,
        "demo_site_id": 456,
        "lead_id": 123,
        "approved": true,
        "reviewer": "admin@example.com",
        "notes": "Looks great, proceed with video",
        "timestamp": "2025-11-04T12:00:00Z"
    }

    Returns:
        Success response with next action
    """
    try:
        data = await request.json()
        demo_id = data.get('demo_id') or data.get('demo_site_id')
        approved = data.get('approved', False)
        reviewer = data.get('reviewer', 'n8n-workflow')
        notes = data.get('notes', '')

        if not demo_id:
            await log_incoming_webhook(request, 'demo_approval', data, 400, db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="demo_id or demo_site_id is required"
            )

        # Get demo site
        demo = db.query(DemoSite).filter(DemoSite.id == demo_id).first()
        if not demo:
            await log_incoming_webhook(request, 'demo_approval', data, 404, db)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Demo site not found"
            )

        # Process approval
        if approved:
            logger.info(f"Demo approved: demo_id={demo_id}, reviewer={reviewer}")

            # Update demo metadata
            if not demo.deployment_metadata:
                demo.deployment_metadata = {}
            demo.deployment_metadata['approval'] = {
                'approved': True,
                'reviewer': reviewer,
                'notes': notes,
                'approved_at': datetime.utcnow().isoformat()
            }

            # Update lead status
            if demo.lead:
                demo.lead.status = 'demo_approved'

            db.commit()

            # Trigger video generation workflow
            trigger = get_webhook_trigger()
            await trigger.trigger_approval_requested(
                approval_type='video',
                entity_id=demo.id,
                approval_data={
                    'demo_id': demo.id,
                    'lead_id': demo.lead_id,
                    'demo_url': demo.url,
                    'approved_by': reviewer
                }
            )

            await log_incoming_webhook(request, 'demo_approval', data, 200, db)

            return {
                "status": "approved",
                "demo_id": demo_id,
                "lead_id": demo.lead_id,
                "action": "continue",
                "next_step": "video_generation",
                "message": "Demo approved, triggering video generation"
            }

        else:
            logger.info(f"Demo rejected: demo_id={demo_id}, reviewer={reviewer}")

            # Update demo metadata
            if not demo.deployment_metadata:
                demo.deployment_metadata = {}
            demo.deployment_metadata['approval'] = {
                'approved': False,
                'reviewer': reviewer,
                'notes': notes,
                'rejected_at': datetime.utcnow().isoformat()
            }

            # Update lead status
            if demo.lead:
                demo.lead.status = 'demo_rejected'

            db.commit()

            await log_incoming_webhook(request, 'demo_approval', data, 200, db)

            return {
                "status": "rejected",
                "demo_id": demo_id,
                "lead_id": demo.lead_id,
                "action": "stop",
                "message": "Demo rejected, workflow stopped"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing demo approval: {str(e)}", exc_info=True)
        await log_incoming_webhook(request, 'demo_approval', {}, 500, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing approval: {str(e)}"
        )


@router.post("/n8n/video-approval")
async def video_approval_response(
    request: Request,
    db: Session = Depends(get_db),
    _verified: bool = Depends(verify_webhook_signature)
):
    """
    Handle video approval decision from n8n workflow.

    Expected payload:
    {
        "video_id": 789,
        "demo_id": 456,
        "lead_id": 123,
        "approved": true,
        "reviewer": "admin@example.com",
        "notes": "Perfect, send the email",
        "timestamp": "2025-11-04T12:30:00Z"
    }

    Returns:
        Success response with next action
    """
    try:
        data = await request.json()
        video_id = data.get('video_id')
        approved = data.get('approved', False)
        reviewer = data.get('reviewer', 'n8n-workflow')
        notes = data.get('notes', '')

        if not video_id:
            await log_incoming_webhook(request, 'video_approval', data, 400, db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="video_id is required"
            )

        # Get video
        video = db.query(ComposedVideo).filter(ComposedVideo.id == video_id).first()
        if not video:
            await log_incoming_webhook(request, 'video_approval', data, 404, db)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        # Process approval
        if approved:
            logger.info(f"Video approved: video_id={video_id}, reviewer={reviewer}")

            # Update video metadata
            if not video.metadata:
                video.metadata = {}
            video.metadata['approval'] = {
                'approved': True,
                'reviewer': reviewer,
                'notes': notes,
                'approved_at': datetime.utcnow().isoformat()
            }

            # Update lead status
            if video.lead:
                video.lead.status = 'video_approved'

            db.commit()

            # Trigger email sending workflow
            trigger = get_webhook_trigger()
            await trigger.trigger_email_sent(
                lead_id=video.lead_id,
                email_data={
                    'video_id': video.id,
                    'video_url': video.output_url,
                    'demo_url': video.demo_site.url if video.demo_site else None,
                    'approved_by': reviewer
                }
            )

            await log_incoming_webhook(request, 'video_approval', data, 200, db)

            return {
                "status": "approved",
                "video_id": video_id,
                "lead_id": video.lead_id,
                "action": "continue",
                "next_step": "email_outreach",
                "message": "Video approved, triggering email outreach"
            }

        else:
            logger.info(f"Video rejected: video_id={video_id}, reviewer={reviewer}")

            # Update video metadata
            if not video.metadata:
                video.metadata = {}
            video.metadata['approval'] = {
                'approved': False,
                'reviewer': reviewer,
                'notes': notes,
                'rejected_at': datetime.utcnow().isoformat()
            }

            # Update lead status
            if video.lead:
                video.lead.status = 'video_rejected'

            db.commit()

            await log_incoming_webhook(request, 'video_approval', data, 200, db)

            return {
                "status": "rejected",
                "video_id": video_id,
                "lead_id": video.lead_id,
                "action": "stop",
                "message": "Video rejected, workflow stopped"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing video approval: {str(e)}", exc_info=True)
        await log_incoming_webhook(request, 'video_approval', {}, 500, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing approval: {str(e)}"
        )


@router.post("/n8n/workflow-completed")
async def workflow_completed(
    request: Request,
    db: Session = Depends(get_db),
    _verified: bool = Depends(verify_webhook_signature)
):
    """
    Handle workflow completion notification from n8n.

    This endpoint receives notifications when n8n workflows complete,
    allowing us to track workflow execution and update records.

    Expected payload:
    {
        "workflow_id": "lead-processing-pipeline",
        "workflow_name": "Lead Processing Pipeline",
        "execution_id": "exec_123",
        "lead_id": 123,
        "status": "success",
        "duration_ms": 45000,
        "steps_completed": 5,
        "timestamp": "2025-11-04T13:00:00Z"
    }

    Returns:
        Success acknowledgment
    """
    try:
        data = await request.json()
        workflow_id = data.get('workflow_id')
        execution_id = data.get('execution_id')
        workflow_status = data.get('status', 'completed')
        lead_id = data.get('lead_id')

        logger.info(
            f"Workflow completed: workflow_id={workflow_id}, "
            f"execution_id={execution_id}, status={workflow_status}"
        )

        # Update lead if provided
        if lead_id:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                # Store workflow execution data
                if not hasattr(lead, 'metadata') or lead.metadata is None:
                    # If lead doesn't have metadata field, log it
                    logger.info(f"Workflow completed for lead {lead_id}: {workflow_status}")
                else:
                    if lead.metadata is None:
                        lead.metadata = {}
                    if 'workflow_executions' not in lead.metadata:
                        lead.metadata['workflow_executions'] = []

                    lead.metadata['workflow_executions'].append({
                        'workflow_id': workflow_id,
                        'execution_id': execution_id,
                        'status': workflow_status,
                        'completed_at': datetime.utcnow().isoformat()
                    })

                db.commit()

        await log_incoming_webhook(request, 'workflow_completed', data, 200, db)

        return {
            "status": "received",
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "message": "Workflow completion logged successfully"
        }

    except Exception as e:
        logger.error(f"Error processing workflow completion: {str(e)}", exc_info=True)
        await log_incoming_webhook(request, 'workflow_completed', {}, 500, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing workflow completion: {str(e)}"
        )


@router.post("/n8n/workflow-status")
async def workflow_status_update(
    request: Request,
    db: Session = Depends(get_db),
    _verified: bool = Depends(verify_webhook_signature)
):
    """
    Handle workflow status updates from n8n.

    This endpoint receives status updates as workflows progress through
    different steps, allowing for real-time monitoring.

    Expected payload:
    {
        "workflow_id": "lead-processing-pipeline",
        "execution_id": "exec_123",
        "lead_id": 123,
        "current_step": "demo_generation",
        "status": "running",
        "progress": 60,
        "timestamp": "2025-11-04T12:45:00Z"
    }

    Returns:
        Success acknowledgment
    """
    try:
        data = await request.json()
        workflow_id = data.get('workflow_id')
        execution_id = data.get('execution_id')
        current_step = data.get('current_step')
        workflow_status = data.get('status')

        logger.debug(
            f"Workflow status update: workflow_id={workflow_id}, "
            f"step={current_step}, status={workflow_status}"
        )

        await log_incoming_webhook(request, 'workflow_status', data, 200, db)

        return {
            "status": "received",
            "workflow_id": workflow_id,
            "execution_id": execution_id,
            "message": "Status update received"
        }

    except Exception as e:
        logger.error(f"Error processing workflow status: {str(e)}", exc_info=True)
        await log_incoming_webhook(request, 'workflow_status', {}, 500, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing status update: {str(e)}"
        )


@router.post("/n8n/error-notification")
async def error_notification(
    request: Request,
    db: Session = Depends(get_db),
    _verified: bool = Depends(verify_webhook_signature)
):
    """
    Handle error notifications from n8n workflows.

    This endpoint receives error notifications when workflows fail,
    allowing for error tracking and alerting.

    Expected payload:
    {
        "workflow_id": "lead-processing-pipeline",
        "execution_id": "exec_123",
        "lead_id": 123,
        "error_step": "demo_generation",
        "error_type": "DEPLOYMENT_ERROR",
        "error_message": "Failed to deploy to Vercel",
        "stack_trace": "...",
        "timestamp": "2025-11-04T12:50:00Z"
    }

    Returns:
        Success acknowledgment
    """
    try:
        data = await request.json()
        workflow_id = data.get('workflow_id')
        error_message = data.get('error_message')
        lead_id = data.get('lead_id')

        logger.error(
            f"n8n workflow error: workflow_id={workflow_id}, "
            f"error={error_message}, lead_id={lead_id}"
        )

        # Update lead status if provided
        if lead_id:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.status = 'workflow_error'
                db.commit()

        await log_incoming_webhook(request, 'error_notification', data, 200, db)

        # Trigger workflow error webhook for monitoring
        trigger = get_webhook_trigger()
        await trigger.trigger_workflow_error(
            workflow_name=workflow_id,
            error_data={
                'error_message': error_message,
                'lead_id': lead_id,
                'data': data
            }
        )

        return {
            "status": "received",
            "workflow_id": workflow_id,
            "message": "Error notification logged"
        }

    except Exception as e:
        logger.error(f"Error processing error notification: {str(e)}", exc_info=True)
        await log_incoming_webhook(request, 'error_notification', {}, 500, db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing error notification: {str(e)}"
        )


@router.get("/n8n/health")
async def health_check():
    """
    Health check endpoint for webhook responses.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "webhook-responses",
        "timestamp": datetime.utcnow().isoformat(),
        "webhook_config": {
            "enabled": webhook_config.n8n.enabled,
            "base_url": webhook_config.n8n.base_url,
            "security_enabled": webhook_config.security.require_signature
        }
    }


@router.post("/test")
async def test_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Test endpoint for webhook integration.

    This endpoint can be used to test webhook delivery without
    requiring signature verification.

    Returns:
        Test response
    """
    try:
        data = await request.json()
        logger.info(f"Test webhook received: {data}")

        await log_incoming_webhook(request, 'test', data, 200, db)

        return {
            "status": "success",
            "message": "Test webhook received successfully",
            "received_data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing test webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
