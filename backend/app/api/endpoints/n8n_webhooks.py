"""
N8N Webhook Endpoints

PUBLIC webhook endpoints for receiving webhooks from N8N workflows.
These endpoints queue webhooks for async processing.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.workflows import WebhookHandler, WorkflowExecutor
from app.schemas.workflows import WebhookReceive

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/n8n/{workflow_id}")
async def receive_n8n_webhook(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_n8n_signature: Optional[str] = Header(None)
):
    """
    Receive webhook from N8N workflow

    This is a PUBLIC endpoint that N8N can call to send workflow results
    back to the system.

    Args:
        workflow_id: N8N workflow ID
        request: FastAPI request
        x_n8n_signature: Optional webhook signature for validation

    Returns:
        Immediate 200 OK response, processing happens async
    """
    try:
        # Parse payload
        payload = await request.json()

        # Get webhook handler
        handler = WebhookHandler(db)

        # Validate signature if provided
        if x_n8n_signature:
            is_valid = handler.validate_signature(
                payload=payload,
                signature=x_n8n_signature
            )
            if not is_valid:
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Find workflow
        workflow = handler.find_workflow_by_webhook(workflow_id)

        # Queue webhook for async processing
        webhook_entry = handler.queue_webhook(
            workflow_id=workflow.id if workflow else None,
            payload=payload,
            headers=dict(request.headers),
            source="n8n",
            webhook_url=str(request.url)
        )

        logger.info(f"Queued webhook from N8N workflow {workflow_id}")

        return {
            "status": "received",
            "webhook_id": webhook_entry.id,
            "message": "Webhook queued for processing"
        }

    except Exception as e:
        logger.error(f"Webhook receive error: {str(e)}")
        # Always return 200 to N8N even on error to prevent retries
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/n8n/generic")
async def receive_generic_webhook(
    request: Request,
    data: WebhookReceive,
    db: Session = Depends(get_db)
):
    """
    Generic webhook receiver for N8N

    Use this when you don't have a specific workflow ID.

    Request body:
        {
            "event": "lead_created",
            "data": {...},
            "source": "n8n",
            "workflow_id": "optional-workflow-id"
        }
    """
    try:
        handler = WebhookHandler(db)

        # Find workflow if ID provided
        workflow = None
        if data.workflow_id:
            workflow = handler.find_workflow_by_webhook(data.workflow_id)

        # Queue webhook
        webhook_entry = handler.queue_webhook(
            workflow_id=workflow.id if workflow else None,
            payload=data.data,
            headers=dict(request.headers),
            source=data.source or "n8n",
            webhook_url=str(request.url)
        )

        return {
            "status": "received",
            "webhook_id": webhook_entry.id,
            "event": data.event
        }

    except Exception as e:
        logger.error(f"Generic webhook error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/n8n/test")
async def test_webhook_connectivity():
    """
    Test webhook connectivity

    Use this to verify that N8N can reach the webhook endpoints.
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is reachable",
        "service": "n8n-webhooks"
    }
