"""
Approval Workflow service for managing response approvals.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from app.models.approvals import ResponseApproval, ApprovalRule, ApprovalQueue
from app.models.leads import Lead
from app.models.response_templates import ResponseTemplate
from app.services.response_generator import ResponseGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Service for managing the approval workflow."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.response_generator = ResponseGenerator(db)
    
    async def create_approval_request(
        self,
        lead: Lead,
        template: ResponseTemplate,
        generated_subject: str,
        generated_body: str,
        variables_used: Dict,
        auto_submit: bool = True
    ) -> ResponseApproval:
        """Create a new approval request for a generated response."""
        
        # Create approval record
        approval = ResponseApproval(
            lead_id=lead.id,
            template_id=template.id,
            generated_subject=generated_subject,
            generated_body=generated_body,
            status="pending",
            variables_used=variables_used,
            generation_metadata={
                "template_name": template.name,
                "template_type": template.template_type,
                "generation_time": datetime.utcnow().isoformat(),
                "lead_title": lead.title,
                "lead_score": lead.qualification_score
            }
        )
        
        # Check auto-approval rules
        auto_approval_result = await self._check_auto_approval(lead, template, approval)
        if auto_approval_result['auto_approve']:
            approval.status = "approved"
            approval.approval_method = "auto"
            approval.auto_approval_score = auto_approval_result['score']
            approval.auto_approval_reason = auto_approval_result['reason']
            approval.reviewed_at = datetime.utcnow()
            logger.info(f"Auto-approved response for lead {lead.id}: {auto_approval_result['reason']}")
        
        self.db.add(approval)
        
        # Add to queue if not auto-approved
        if approval.status == "pending" and auto_submit:
            queue_entry = await self._add_to_queue(approval, auto_approval_result.get('priority', 'normal'))
            self.db.add(queue_entry)
        
        await self.db.commit()
        await self.db.refresh(approval)
        
        # Send notifications if configured
        if approval.status == "pending" and settings.ENABLE_REAL_TIME_NOTIFICATIONS:
            await self._send_approval_notification(approval, lead)
        
        return approval
    
    async def _check_auto_approval(
        self,
        lead: Lead,
        template: ResponseTemplate,
        approval: ResponseApproval
    ) -> Dict:
        """Check if response qualifies for auto-approval."""
        
        # Get active approval rules
        query = select(ApprovalRule).where(
            ApprovalRule.is_active == True
        ).order_by(ApprovalRule.priority.desc())
        
        result = await self.db.execute(query)
        rules = result.scalars().all()
        
        for rule in rules:
            if await self._evaluate_rule(rule, lead, template):
                # Update rule statistics
                rule.times_triggered += 1
                
                if rule.auto_approve:
                    # Check if meets auto-approval threshold
                    score = await self._calculate_approval_score(lead, template, approval)
                    
                    if score >= rule.auto_approve_threshold:
                        rule.auto_approved_count += 1
                        return {
                            'auto_approve': True,
                            'score': score,
                            'reason': f"Auto-approved by rule '{rule.name}' with score {score:.2f}",
                            'rule_id': rule.id
                        }
                else:
                    rule.manual_review_count += 1
                
                # Return first matching rule's configuration
                return {
                    'auto_approve': False,
                    'priority': rule.notification_priority,
                    'slack_channels': rule.slack_channels,
                    'require_slack': rule.require_slack_review,
                    'rule_id': rule.id
                }
        
        return {
            'auto_approve': False,
            'priority': 'normal',
            'require_slack': True
        }
    
    async def _evaluate_rule(
        self,
        rule: ApprovalRule,
        lead: Lead,
        template: ResponseTemplate
    ) -> bool:
        """Evaluate if a rule matches the current context."""
        
        # Check qualification score
        if rule.min_qualification_score and lead.qualification_score:
            if lead.qualification_score < rule.min_qualification_score:
                return False
        
        # Check lead category
        if rule.lead_categories and lead.category:
            if lead.category not in rule.lead_categories:
                return False
        
        # Check compensation range
        if lead.compensation:
            try:
                # Parse compensation (handle various formats)
                comp_value = self._parse_compensation(lead.compensation)
                if comp_value:
                    if rule.compensation_min and comp_value < rule.compensation_min:
                        return False
                    if rule.compensation_max and comp_value > rule.compensation_max:
                        return False
            except:
                pass
        
        # Check template type
        if rule.template_types and template.template_type:
            if template.template_type not in rule.template_types:
                return False
        
        # Check required keywords in lead
        if rule.required_keywords:
            lead_text = f"{lead.title} {lead.description}".lower()
            for keyword in rule.required_keywords:
                if keyword.lower() not in lead_text:
                    return False
        
        # Check excluded keywords
        if rule.excluded_keywords:
            lead_text = f"{lead.title} {lead.description}".lower()
            for keyword in rule.excluded_keywords:
                if keyword.lower() in lead_text:
                    return False
        
        return True
    
    async def _calculate_approval_score(
        self,
        lead: Lead,
        template: ResponseTemplate,
        approval: ResponseApproval
    ) -> float:
        """Calculate auto-approval score based on various factors."""
        
        score = 0.0
        factors = 0
        
        # Factor 1: Lead qualification score (40% weight)
        if lead.qualification_score:
            score += lead.qualification_score * 0.4
            factors += 0.4
        
        # Factor 2: Template performance (20% weight)
        if template.success_rate:
            score += (template.success_rate / 100) * 0.2
            factors += 0.2
        
        # Factor 3: Response completeness (20% weight)
        if approval.variables_used:
            total_vars = len(approval.variables_used)
            filled_vars = sum(1 for v in approval.variables_used.values() if v)
            completeness = filled_vars / total_vars if total_vars > 0 else 0
            score += completeness * 0.2
            factors += 0.2
        
        # Factor 4: Lead freshness (10% weight)
        if lead.posted_at:
            hours_old = (datetime.utcnow() - lead.posted_at).total_seconds() / 3600
            freshness = max(0, 1 - (hours_old / 168))  # 1 week = 168 hours
            score += freshness * 0.1
            factors += 0.1
        
        # Factor 5: Template usage success (10% weight)
        if template.times_used > 10:  # Only consider if template has been used enough
            success_factor = min(1.0, template.times_used / 100) * 0.1
            score += success_factor
            factors += 0.1
        
        # Normalize score if not all factors were available
        if factors > 0:
            score = score / factors
        
        return min(1.0, score)  # Cap at 1.0
    
    def _parse_compensation(self, compensation: str) -> Optional[float]:
        """Parse compensation string to numeric value."""
        import re
        
        # Remove commas and dollar signs
        comp = compensation.replace(',', '').replace('$', '')
        
        # Look for hourly rate
        hourly_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/hr|/hour|per hour)', comp, re.IGNORECASE)
        if hourly_match:
            return float(hourly_match.group(1)) * 2080  # Convert to annual
        
        # Look for annual salary
        salary_match = re.search(r'(\d+)(?:k|K)', comp)
        if salary_match:
            return float(salary_match.group(1)) * 1000
        
        # Look for raw number
        number_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', compensation)
        if number_match:
            return float(number_match.group(1).replace(',', ''))
        
        return None
    
    async def _add_to_queue(
        self,
        approval: ResponseApproval,
        priority: str = "normal"
    ) -> ApprovalQueue:
        """Add approval to the review queue."""
        
        # Calculate SLA deadline based on priority
        sla_hours = {
            "urgent": 1,
            "high": 4,
            "normal": 24,
            "low": 48
        }
        
        deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(priority, 24))
        
        # Get current queue position
        query = select(ApprovalQueue).where(
            ApprovalQueue.status == "queued"
        )
        result = await self.db.execute(query)
        queue_size = len(result.scalars().all())
        
        queue_entry = ApprovalQueue(
            approval_id=approval.id,
            priority=priority,
            queue_position=queue_size + 1,
            sla_deadline=deadline,
            status="queued"
        )
        
        return queue_entry
    
    async def _send_approval_notification(
        self,
        approval: ResponseApproval,
        lead: Lead
    ) -> None:
        """Send notification for approval review."""
        
        try:
            # This would integrate with Slack API
            # For now, just log the notification
            logger.info(
                f"Approval notification for lead {lead.id}: {lead.title}\n"
                f"Subject: {approval.generated_subject}\n"
                f"Preview: {approval.generated_body[:200]}..."
            )
            
            approval.notification_sent = True
            
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
    
    async def approve_response(
        self,
        approval_id: int,
        reviewer_id: str,
        reviewer_name: str,
        modified_subject: Optional[str] = None,
        modified_body: Optional[str] = None,
        review_notes: Optional[str] = None,
        quality_score: Optional[float] = None,
        relevance_score: Optional[float] = None
    ) -> ResponseApproval:
        """Approve a response with optional modifications."""
        
        # Get approval
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await self.db.execute(query)
        approval = result.scalar_one_or_none()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != "pending":
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")
        
        # Update approval
        approval.status = "approved"
        approval.approval_method = "manual"
        approval.reviewer_id = reviewer_id
        approval.reviewer_name = reviewer_name
        approval.reviewed_at = datetime.utcnow()
        
        if modified_subject:
            approval.modified_subject = modified_subject
        if modified_body:
            approval.modified_body = modified_body
        if review_notes:
            approval.review_notes = review_notes
        if quality_score:
            approval.quality_score = quality_score
        if relevance_score:
            approval.relevance_score = relevance_score
        
        # Update queue entry
        queue_query = select(ApprovalQueue).where(
            ApprovalQueue.approval_id == approval_id
        )
        queue_result = await self.db.execute(queue_query)
        queue_entry = queue_result.scalar_one_or_none()
        
        if queue_entry:
            queue_entry.status = "completed"
            queue_entry.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(approval)
        
        logger.info(f"Response approved for approval {approval_id} by {reviewer_name}")
        
        return approval
    
    async def reject_response(
        self,
        approval_id: int,
        reviewer_id: str,
        reviewer_name: str,
        review_notes: str
    ) -> ResponseApproval:
        """Reject a response."""
        
        # Get approval
        query = select(ResponseApproval).where(ResponseApproval.id == approval_id)
        result = await self.db.execute(query)
        approval = result.scalar_one_or_none()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != "pending":
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")
        
        # Update approval
        approval.status = "rejected"
        approval.approval_method = "manual"
        approval.reviewer_id = reviewer_id
        approval.reviewer_name = reviewer_name
        approval.reviewed_at = datetime.utcnow()
        approval.review_notes = review_notes
        
        # Update queue entry
        queue_query = select(ApprovalQueue).where(
            ApprovalQueue.approval_id == approval_id
        )
        queue_result = await self.db.execute(queue_query)
        queue_entry = queue_result.scalar_one_or_none()
        
        if queue_entry:
            queue_entry.status = "completed"
            queue_entry.completed_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(approval)
        
        logger.info(f"Response rejected for approval {approval_id} by {reviewer_name}")
        
        return approval
    
    async def get_pending_approvals(
        self,
        limit: int = 10,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """Get pending approvals from the queue."""
        
        query = select(
            ApprovalQueue,
            ResponseApproval,
            Lead
        ).join(
            ResponseApproval,
            ApprovalQueue.approval_id == ResponseApproval.id
        ).join(
            Lead,
            ResponseApproval.lead_id == Lead.id
        ).where(
            ApprovalQueue.status == "queued"
        )
        
        if priority:
            query = query.where(ApprovalQueue.priority == priority)
        
        query = query.order_by(
            ApprovalQueue.priority.desc(),
            ApprovalQueue.created_at.asc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        items = result.all()
        
        pending = []
        for queue_entry, approval, lead in items:
            pending.append({
                'queue_id': queue_entry.id,
                'approval_id': approval.id,
                'lead': {
                    'id': lead.id,
                    'title': lead.title,
                    'compensation': lead.compensation,
                    'posted_at': lead.posted_at.isoformat() if lead.posted_at else None
                },
                'response': {
                    'subject': approval.generated_subject,
                    'body': approval.generated_body
                },
                'priority': queue_entry.priority,
                'sla_deadline': queue_entry.sla_deadline.isoformat() if queue_entry.sla_deadline else None,
                'created_at': queue_entry.created_at.isoformat() if queue_entry.created_at else None
            })
        
        return pending