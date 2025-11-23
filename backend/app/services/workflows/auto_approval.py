"""
Auto-Approval Service

AI-powered automatic approval decisions using OpenRouter for analysis.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.n8n_workflows import WorkflowApproval, ApprovalStatus
from app.services.openrouter_client import OpenRouterClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class AutoApprovalService:
    """
    Auto-Approval Service

    Uses AI to evaluate approval requests and auto-approve when
    confidence threshold is met.
    """

    def __init__(self, db: Session):
        """Initialize auto-approval service"""
        self.db = db
        self.openrouter = OpenRouterClient()
        self.confidence_threshold = getattr(settings, 'AUTO_APPROVAL_CONFIDENCE_THRESHOLD', 90)
        self.enabled = getattr(settings, 'AUTO_APPROVAL_ENABLED', True)

    async def evaluate_approval(self, approval_id: int) -> bool:
        """
        Evaluate approval request for auto-approval

        Args:
            approval_id: Approval request ID

        Returns:
            True if auto-approved
        """
        if not self.enabled:
            logger.info("Auto-approval is disabled")
            return False

        try:
            approval = self.db.query(WorkflowApproval).filter(
                WorkflowApproval.id == approval_id
            ).first()

            if not approval:
                return False

            if not approval.auto_approval_enabled or approval.requires_manual:
                logger.info(f"Approval {approval_id} requires manual review")
                return False

            if approval.status != ApprovalStatus.PENDING:
                return False

            # Analyze approval request with AI
            analysis = await self._analyze_with_ai(approval)

            if not analysis:
                return False

            confidence = analysis.get("confidence", 0)
            should_approve = analysis.get("should_approve", False)
            reason = analysis.get("reason", "")

            # Update approval with AI analysis
            approval.auto_approval_confidence = confidence
            approval.auto_approval_reason = reason

            # Auto-approve if confidence threshold met
            if should_approve and confidence >= self.confidence_threshold:
                approval.status = ApprovalStatus.APPROVED
                approval.approver_name = "Auto-Approval AI"
                approval.approval_reason = f"Auto-approved with {confidence}% confidence: {reason}"
                approval.approved_at = datetime.utcnow()

                self.db.commit()

                logger.info(f"Auto-approved request {approval_id} with {confidence}% confidence")

                # Trigger execution
                from .approval_system import ApprovalSystem
                system = ApprovalSystem(self.db)
                await system._trigger_approved_execution(approval)

                return True
            else:
                # Keep pending for manual review
                self.db.commit()
                logger.info(
                    f"Approval {approval_id} requires manual review "
                    f"(confidence: {confidence}%, threshold: {self.confidence_threshold}%)"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to evaluate approval: {str(e)}")
            self.db.rollback()
            return False

    async def _analyze_with_ai(
        self,
        approval: WorkflowApproval
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze approval request using AI

        Args:
            approval: WorkflowApproval instance

        Returns:
            Analysis result with confidence score and decision
        """
        try:
            execution = approval.execution
            workflow = execution.workflow if execution else None

            # Build context for AI
            context = {
                "approval_type": approval.approval_type,
                "approval_title": approval.approval_title,
                "approval_description": approval.approval_description,
                "approval_data": approval.approval_data,
                "priority": approval.priority.value,
                "workflow_name": workflow.workflow_name if workflow else None,
                "trigger_event": execution.trigger_event if execution else None,
                "input_data": execution.input_data if execution else None
            }

            prompt = self._build_analysis_prompt(context)

            # Call AI for analysis
            response = await self.openrouter.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an approval decision assistant. Analyze approval requests and provide a confidence score (0-100) and recommendation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="anthropic/claude-3-haiku",
                temperature=0.3
            )

            # Parse AI response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Extract decision from response
            analysis = self._parse_ai_response(content)
            return analysis

        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return None

    def _build_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for AI analysis"""
        prompt = f"""
Analyze this approval request and provide a decision:

Approval Type: {context['approval_type']}
Title: {context['approval_title']}
Description: {context.get('approval_description', 'N/A')}
Priority: {context['priority']}
Workflow: {context.get('workflow_name', 'N/A')}
Trigger: {context.get('trigger_event', 'N/A')}

Additional Data:
{context.get('approval_data', {})}

Evaluate this request and respond with:
1. Should this be approved? (yes/no)
2. Confidence score (0-100)
3. Reason for decision

Consider:
- Is the request safe and legitimate?
- Are there any red flags or suspicious patterns?
- Does the data appear valid?
- Is the workflow appropriate for the trigger?

Respond in this exact format:
DECISION: [yes/no]
CONFIDENCE: [0-100]
REASON: [brief explanation]
"""
        return prompt

    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            lines = content.strip().split('\n')
            result = {
                "should_approve": False,
                "confidence": 0,
                "reason": ""
            }

            for line in lines:
                line = line.strip()
                if line.startswith("DECISION:"):
                    decision = line.split(":", 1)[1].strip().lower()
                    result["should_approve"] = decision == "yes"
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = line.split(":", 1)[1].strip()
                        result["confidence"] = int(confidence)
                    except:
                        result["confidence"] = 0
                elif line.startswith("REASON:"):
                    result["reason"] = line.split(":", 1)[1].strip()

            return result

        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return {"should_approve": False, "confidence": 0, "reason": "Parse error"}

    def check_approval_rules(
        self,
        approval: WorkflowApproval
    ) -> Dict[str, Any]:
        """
        Check rule-based approval criteria

        Args:
            approval: WorkflowApproval instance

        Returns:
            Rule check results
        """
        # Simple rule-based checks
        rules_passed = []
        rules_failed = []

        # Rule 1: Check if approval data is present
        if approval.approval_data:
            rules_passed.append("Has approval data")
        else:
            rules_failed.append("Missing approval data")

        # Rule 2: Check priority
        if approval.priority.value == "high":
            rules_failed.append("High priority requires manual approval")
        else:
            rules_passed.append("Priority acceptable for auto-approval")

        # Rule 3: Check approval type
        safe_types = ["workflow_execution", "email_send", "data_export"]
        if approval.approval_type in safe_types:
            rules_passed.append("Approval type is safe")
        else:
            rules_failed.append(f"Approval type '{approval.approval_type}' requires review")

        return {
            "rules_passed": rules_passed,
            "rules_failed": rules_failed,
            "can_auto_approve": len(rules_failed) == 0
        }
