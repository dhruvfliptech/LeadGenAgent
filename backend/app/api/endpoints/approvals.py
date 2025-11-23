"""
API endpoints for approval workflow management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.approvals import ResponseApproval, ApprovalRule, ApprovalQueue
from app.models.leads import Lead
from app.models.response_templates import ResponseTemplate
from app.services.approval_workflow import ApprovalWorkflow
from app.services.response_generator import ResponseGenerator

router = APIRouter()


# Pydantic models for API
class ApprovalRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    min_qualification_score: Optional[float] = None
    required_keywords: Optional[List[str]] = None
    excluded_keywords: Optional[List[str]] = None
    lead_categories: Optional[List[str]] = None
    compensation_min: Optional[float] = None
    compensation_max: Optional[float] = None
    template_types: Optional[List[str]] = None
    auto_approve: bool = False
    auto_approve_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    require_slack_review: bool = True
    slack_channels: Optional[List[str]] = None
    notification_priority: str = "normal"
    priority: int = 0
    is_active: bool = True


class ApprovalReview(BaseModel):
    reviewer_id: str
    reviewer_name: str
    action: str = Field(..., pattern="^(approve|reject)$")
    modified_subject: Optional[str] = None
    modified_body: Optional[str] = None
    review_notes: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    relevance_score: Optional[float] = Field(None, ge=1.0, le=5.0)


class GenerateAndQueueRequest(BaseModel):
    lead_id: int
    template_id: Optional[int] = None
    auto_submit: bool = True
    use_ai: bool = False


@router.post("/generate-and-queue")
async def generate_and_queue_response(
    request: GenerateAndQueueRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a response and add it to the approval queue."""
    
    # Get lead
    lead_query = select(Lead).where(Lead.id == request.lead_id)
    lead_result = await db.execute(lead_query)
    lead = lead_result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {request.lead_id} not found")
    
    # Get or select template
    generator = ResponseGenerator(db)
    
    if request.template_id:
        template_query = select(ResponseTemplate).where(ResponseTemplate.id == request.template_id)
        template_result = await db.execute(template_query)
        template = template_result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {request.template_id} not found")
    else:
        template = await generator._select_best_template(lead)
    
    # Generate response
    subject, body, metadata = await generator.generate_response(
        lead,
        template,
        use_ai=request.use_ai
    )
    
    # Create approval request
    workflow = ApprovalWorkflow(db)
    approval = await workflow.create_approval_request(
        lead=lead,
        template=template,
        generated_subject=subject,
        generated_body=body,
        variables_used=metadata.get('variables_used', {}),
        auto_submit=request.auto_submit
    )
    
    return {
        "approval_id": approval.id,
        "lead_id": lead.id,
        "template_id": template.id,
        "status": approval.status,
        "auto_approved": approval.status == "approved",
        "auto_approval_reason": approval.auto_approval_reason,
        "generated_subject": subject,
        "generated_body": body,
        "metadata": metadata
    }


@router.get("/pending")
async def get_pending_approvals(
    limit: int = Query(10, ge=1, le=100),
    priority: Optional[str] = Query(None, regex="^(low|normal|high|urgent)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get pending approvals from the queue."""
    
    workflow = ApprovalWorkflow(db)
    pending = await workflow.get_pending_approvals(limit=limit, priority=priority)
    
    return {
        "count": len(pending),
        "approvals": pending
    }


@router.get("/{approval_id}")
async def get_approval_details(
    approval_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about an approval."""
    
    query = select(
        ResponseApproval,
        Lead,
        ResponseTemplate
    ).join(
        Lead,
        ResponseApproval.lead_id == Lead.id
    ).outerjoin(
        ResponseTemplate,
        ResponseApproval.template_id == ResponseTemplate.id
    ).where(
        ResponseApproval.id == approval_id
    )
    
    result = await db.execute(query)
    data = result.one_or_none()
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id} not found")
    
    approval, lead, template = data
    
    return {
        "approval": approval.to_dict(),
        "lead": {
            "id": lead.id,
            "title": lead.title,
            "description": lead.description,
            "compensation": lead.compensation,
            "location": lead.location,
            "posted_at": lead.posted_at.isoformat() if lead.posted_at else None,
            "qualification_score": lead.qualification_score
        },
        "template": template.to_dict() if template else None
    }


@router.post("/{approval_id}/review")
async def review_approval(
    approval_id: int,
    review: ApprovalReview,
    db: AsyncSession = Depends(get_db)
):
    """Review and approve/reject a response."""
    
    workflow = ApprovalWorkflow(db)
    
    try:
        if review.action == "approve":
            approval = await workflow.approve_response(
                approval_id=approval_id,
                reviewer_id=review.reviewer_id,
                reviewer_name=review.reviewer_name,
                modified_subject=review.modified_subject,
                modified_body=review.modified_body,
                review_notes=review.review_notes,
                quality_score=review.quality_score,
                relevance_score=review.relevance_score
            )
        else:  # reject
            if not review.review_notes:
                raise HTTPException(
                    status_code=400,
                    detail="Review notes are required when rejecting"
                )
            
            approval = await workflow.reject_response(
                approval_id=approval_id,
                reviewer_id=review.reviewer_id,
                reviewer_name=review.reviewer_name,
                review_notes=review.review_notes
            )
        
        return {
            "success": True,
            "approval": approval.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rules")
async def create_approval_rule(
    rule: ApprovalRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new approval rule."""
    
    # Check if rule name already exists
    existing_query = select(ApprovalRule).where(ApprovalRule.name == rule.name)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Rule with name '{rule.name}' already exists")
    
    new_rule = ApprovalRule(**rule.dict())
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    
    return new_rule.to_dict()


@router.get("/rules")
async def get_approval_rules(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get all approval rules."""
    
    query = select(ApprovalRule)
    if active_only:
        query = query.where(ApprovalRule.is_active == True)
    query = query.order_by(ApprovalRule.priority.desc())
    
    result = await db.execute(query)
    rules = result.scalars().all()
    
    return {
        "count": len(rules),
        "rules": [rule.to_dict() for rule in rules]
    }


@router.put("/rules/{rule_id}")
async def update_approval_rule(
    rule_id: int,
    rule_update: ApprovalRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing approval rule."""
    
    query = select(ApprovalRule).where(ApprovalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    # Update rule
    for field, value in rule_update.dict().items():
        setattr(rule, field, value)
    
    rule.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(rule)
    
    return rule.to_dict()


@router.delete("/rules/{rule_id}")
async def delete_approval_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an approval rule."""
    
    query = select(ApprovalRule).where(ApprovalRule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    await db.delete(rule)
    await db.commit()
    
    return {"success": True, "message": f"Rule {rule_id} deleted"}


@router.get("/queue/stats")
async def get_queue_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get queue statistics and SLA information."""
    
    # Get queue stats
    queue_query = select(ApprovalQueue).where(ApprovalQueue.status == "queued")
    queue_result = await db.execute(queue_query)
    queue_items = queue_result.scalars().all()
    
    # Calculate stats
    total_queued = len(queue_items)
    priority_counts = {"urgent": 0, "high": 0, "normal": 0, "low": 0}
    sla_at_risk = 0
    sla_breached = 0
    
    now = datetime.utcnow()
    
    for item in queue_items:
        priority_counts[item.priority] += 1
        
        if item.sla_deadline:
            time_to_deadline = (item.sla_deadline - now).total_seconds() / 3600
            if time_to_deadline < 0:
                sla_breached += 1
            elif time_to_deadline < 2:  # Less than 2 hours
                sla_at_risk += 1
    
    # Get approval stats
    approval_query = select(ResponseApproval)
    approval_result = await db.execute(approval_query)
    approvals = approval_result.scalars().all()
    
    status_counts = {"pending": 0, "approved": 0, "rejected": 0, "sent": 0}
    auto_approved = 0
    
    for approval in approvals:
        status_counts[approval.status] += 1
        if approval.approval_method == "auto":
            auto_approved += 1
    
    return {
        "queue": {
            "total_queued": total_queued,
            "by_priority": priority_counts,
            "sla_at_risk": sla_at_risk,
            "sla_breached": sla_breached
        },
        "approvals": {
            "total": len(approvals),
            "by_status": status_counts,
            "auto_approved": auto_approved,
            "manual_reviewed": status_counts["approved"] + status_counts["rejected"] - auto_approved
        }
    }