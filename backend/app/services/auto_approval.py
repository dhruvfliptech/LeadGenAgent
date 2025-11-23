"""
Auto-Approval Rules Engine for intelligent workflow automation.

Automatically approves requests based on configured rules and ML-based scoring.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.approvals import ApprovalRule
from app.models.leads import Lead
from app.models.demo_sites import DemoSite
from app.models.composed_videos import ComposedVideo

logger = logging.getLogger(__name__)


class AutoApprovalEngine:
    """
    Intelligent Auto-Approval Rules Engine.

    Evaluates approval requests against configured rules and
    automatically approves when criteria are met.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_auto_approval(
        self,
        approval_type: str,
        resource_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        Check if approval can be auto-approved.

        Args:
            approval_type: Type of approval (demo_site_review, video_review, etc.)
            resource_data: Data about the resource being approved
            metadata: Additional context

        Returns:
            Tuple of (should_auto_approve, reason, score)
        """

        metadata = metadata or {}

        # Get all active auto-approval rules for this type
        rules = await self._get_applicable_rules(approval_type)

        if not rules:
            logger.debug(f"No auto-approval rules found for {approval_type}")
            return False, None, 0.0

        # Evaluate each rule
        for rule in rules:
            should_approve, score, reason = await self._evaluate_rule(
                rule,
                resource_data,
                metadata
            )

            if should_approve:
                # Update rule statistics
                rule.times_triggered += 1
                rule.auto_approved_count += 1
                await self.db.commit()

                logger.info(
                    f"Auto-approved by rule '{rule.name}': {reason} (score: {score:.2f})"
                )

                return True, reason, score

        return False, None, 0.0

    async def _get_applicable_rules(self, approval_type: str) -> List[ApprovalRule]:
        """Get all active auto-approval rules for this approval type."""

        query = select(ApprovalRule).where(
            and_(
                ApprovalRule.is_active == True,
                ApprovalRule.auto_approve == True,
                or_(
                    ApprovalRule.template_types.contains([approval_type]),
                    ApprovalRule.template_types.is_(None)
                )
            )
        ).order_by(ApprovalRule.priority.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def _evaluate_rule(
        self,
        rule: ApprovalRule,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str]:
        """
        Evaluate a single auto-approval rule.

        Returns:
            Tuple of (should_approve, score, reason)
        """

        # Calculate composite score
        score = await self._calculate_composite_score(rule, resource_data, metadata)

        if score >= rule.auto_approve_threshold:
            reason = self._build_approval_reason(rule, score, resource_data, metadata)
            return True, score, reason

        return False, score, ""

    async def _calculate_composite_score(
        self,
        rule: ApprovalRule,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate composite approval score based on multiple factors.

        Scoring factors:
        - Quality score (40%)
        - Qualification score (30%)
        - Historical success rate (15%)
        - Completeness (10%)
        - Freshness (5%)
        """

        total_score = 0.0
        total_weight = 0.0

        # Factor 1: Quality Score (40%)
        if 'quality_score' in resource_data:
            quality_score = float(resource_data['quality_score'])
            total_score += quality_score * 0.4
            total_weight += 0.4

        # Factor 2: Qualification Score (30%)
        if 'qualification_score' in resource_data:
            qual_score = float(resource_data['qualification_score'])

            # Check minimum threshold
            if rule.min_qualification_score:
                if qual_score < rule.min_qualification_score:
                    # Below minimum - automatic rejection
                    return 0.0

            total_score += qual_score * 0.3
            total_weight += 0.3

        # Factor 3: Historical Success Rate (15%)
        if 'success_rate' in metadata:
            success_rate = float(metadata['success_rate'])
            total_score += success_rate * 0.15
            total_weight += 0.15

        # Factor 4: Completeness (10%)
        completeness = self._calculate_completeness(resource_data)
        total_score += completeness * 0.1
        total_weight += 0.1

        # Factor 5: Freshness (5%)
        freshness = self._calculate_freshness(resource_data, metadata)
        total_score += freshness * 0.05
        total_weight += 0.05

        # Bonus: Previous approvals for similar items
        similarity_bonus = await self._calculate_similarity_bonus(resource_data, metadata)
        if similarity_bonus > 0:
            total_score += similarity_bonus * 0.05
            total_weight += 0.05

        # Normalize score
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.0

        # Apply rule-specific filters
        if not self._check_rule_filters(rule, resource_data, metadata):
            return 0.0

        return min(1.0, normalized_score)

    def _calculate_completeness(self, resource_data: Dict[str, Any]) -> float:
        """Calculate how complete the resource data is."""

        required_fields = [
            'title', 'description', 'category'
        ]

        optional_fields = [
            'tags', 'preview_url', 'metadata'
        ]

        # Count filled required fields
        required_filled = sum(
            1 for field in required_fields
            if field in resource_data and resource_data[field]
        )

        # Count filled optional fields
        optional_filled = sum(
            1 for field in optional_fields
            if field in resource_data and resource_data[field]
        )

        # Calculate completeness score
        required_score = required_filled / len(required_fields) if required_fields else 1.0
        optional_score = optional_filled / len(optional_fields) if optional_fields else 0.5

        # Weight required fields more heavily
        completeness = (required_score * 0.7) + (optional_score * 0.3)

        return completeness

    def _calculate_freshness(
        self,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """Calculate freshness score based on resource age."""

        created_at = None

        if 'created_at' in resource_data:
            created_at = resource_data['created_at']
        elif 'posted_at' in resource_data:
            created_at = resource_data['posted_at']

        if not created_at:
            return 0.5  # Neutral score if no timestamp

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        age_hours = (datetime.utcnow() - created_at).total_seconds() / 3600

        # Score decreases over time
        # Fresh (< 1 hour): 1.0
        # Recent (< 24 hours): 0.8
        # Old (< 1 week): 0.5
        # Very old (> 1 week): 0.2
        if age_hours < 1:
            return 1.0
        elif age_hours < 24:
            return 0.8
        elif age_hours < 168:  # 1 week
            return 0.5
        else:
            return 0.2

    async def _calculate_similarity_bonus(
        self,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate bonus score based on similarity to previously approved items.

        If similar items were approved before, give a bonus.
        """

        # Get category/type
        category = resource_data.get('category') or metadata.get('category')

        if not category:
            return 0.0

        # Count recent approvals in same category
        from app.models.approvals import ResponseApproval

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        query = select(func.count(ResponseApproval.id)).where(
            and_(
                ResponseApproval.status == 'approved',
                ResponseApproval.created_at >= thirty_days_ago,
                ResponseApproval.resource_data['category'].astext == category
            )
        )

        result = await self.db.execute(query)
        recent_approvals = result.scalar() or 0

        # More approvals = higher bonus (up to 0.3)
        if recent_approvals >= 10:
            return 0.3
        elif recent_approvals >= 5:
            return 0.2
        elif recent_approvals >= 2:
            return 0.1
        else:
            return 0.0

    def _check_rule_filters(
        self,
        rule: ApprovalRule,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> bool:
        """Check if resource passes rule filters."""

        # Check required keywords
        if rule.required_keywords:
            text = self._extract_text_content(resource_data)
            for keyword in rule.required_keywords:
                if keyword.lower() not in text.lower():
                    logger.debug(f"Missing required keyword: {keyword}")
                    return False

        # Check excluded keywords
        if rule.excluded_keywords:
            text = self._extract_text_content(resource_data)
            for keyword in rule.excluded_keywords:
                if keyword.lower() in text.lower():
                    logger.debug(f"Contains excluded keyword: {keyword}")
                    return False

        # Check category filter
        if rule.lead_categories:
            category = resource_data.get('category') or metadata.get('category')
            if category not in rule.lead_categories:
                logger.debug(f"Category {category} not in allowed list")
                return False

        # Check compensation range (for lead approvals)
        if rule.compensation_min or rule.compensation_max:
            compensation = resource_data.get('compensation_value') or metadata.get('compensation_value')
            if compensation:
                if rule.compensation_min and compensation < rule.compensation_min:
                    return False
                if rule.compensation_max and compensation > rule.compensation_max:
                    return False

        return True

    def _extract_text_content(self, resource_data: Dict[str, Any]) -> str:
        """Extract all text content from resource data."""

        text_parts = []

        # Common text fields
        text_fields = ['title', 'description', 'body', 'content', 'text']

        for field in text_fields:
            if field in resource_data and resource_data[field]:
                text_parts.append(str(resource_data[field]))

        return ' '.join(text_parts)

    def _build_approval_reason(
        self,
        rule: ApprovalRule,
        score: float,
        resource_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Build human-readable approval reason."""

        reasons = []

        reasons.append(f"Auto-approved by rule '{rule.name}'")
        reasons.append(f"Composite score: {score:.2f} (threshold: {rule.auto_approve_threshold:.2f})")

        if 'quality_score' in resource_data:
            reasons.append(f"Quality score: {resource_data['quality_score']:.2f}")

        if 'qualification_score' in resource_data:
            reasons.append(f"Qualification score: {resource_data['qualification_score']:.2f}")

        if rule.description:
            reasons.append(f"Rule description: {rule.description}")

        return '; '.join(reasons)

    async def create_auto_approval_rule(
        self,
        name: str,
        description: str,
        approval_types: List[str],
        auto_approve_threshold: float = 0.85,
        min_qualification_score: Optional[float] = None,
        required_keywords: Optional[List[str]] = None,
        excluded_keywords: Optional[List[str]] = None,
        lead_categories: Optional[List[str]] = None,
        priority: int = 0
    ) -> ApprovalRule:
        """Create a new auto-approval rule."""

        rule = ApprovalRule(
            name=name,
            description=description,
            template_types=approval_types,
            auto_approve=True,
            auto_approve_threshold=auto_approve_threshold,
            min_qualification_score=min_qualification_score,
            required_keywords=required_keywords,
            excluded_keywords=excluded_keywords,
            lead_categories=lead_categories,
            priority=priority,
            is_active=True
        )

        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)

        logger.info(f"Created auto-approval rule: {name}")

        return rule

    async def get_rule_performance(self, rule_id: int) -> Dict[str, Any]:
        """Get performance metrics for a specific rule."""

        query = select(ApprovalRule).where(ApprovalRule.id == rule_id)
        result = await self.db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise ValueError(f"Rule {rule_id} not found")

        approval_rate = 0.0
        if rule.times_triggered > 0:
            approval_rate = rule.auto_approved_count / rule.times_triggered

        return {
            'rule_id': rule.id,
            'rule_name': rule.name,
            'times_triggered': rule.times_triggered,
            'auto_approved_count': rule.auto_approved_count,
            'manual_review_count': rule.manual_review_count,
            'approval_rate': approval_rate,
            'auto_approve_threshold': rule.auto_approve_threshold,
            'is_active': rule.is_active,
            'priority': rule.priority
        }

    async def optimize_rule_threshold(
        self,
        rule_id: int,
        target_approval_rate: float = 0.8
    ) -> float:
        """
        Optimize rule threshold based on historical performance.

        Args:
            rule_id: ID of rule to optimize
            target_approval_rate: Desired approval rate (0.0 to 1.0)

        Returns:
            Optimized threshold value
        """

        # Get historical approval data
        from app.models.approvals import ResponseApproval

        query = select(ResponseApproval).where(
            and_(
                ResponseApproval.auto_approval_reason.like(f'%rule_id={rule_id}%'),
                ResponseApproval.auto_approval_score.isnot(None)
            )
        )

        result = await self.db.execute(query)
        approvals = result.scalars().all()

        if len(approvals) < 10:
            logger.warning(
                f"Not enough data to optimize rule {rule_id} "
                f"(only {len(approvals)} samples)"
            )
            return 0.85  # Default threshold

        # Get score distribution
        approved_scores = [
            a.auto_approval_score for a in approvals
            if a.status == 'approved'
        ]

        if not approved_scores:
            return 0.85

        # Sort scores
        approved_scores.sort()

        # Find threshold that gives target approval rate
        target_index = int(len(approved_scores) * (1 - target_approval_rate))
        optimized_threshold = approved_scores[target_index] if target_index < len(approved_scores) else 0.85

        # Clamp between 0.6 and 0.95
        optimized_threshold = max(0.6, min(0.95, optimized_threshold))

        logger.info(
            f"Optimized threshold for rule {rule_id}: {optimized_threshold:.2f} "
            f"(based on {len(approvals)} samples)"
        )

        return optimized_threshold


# Predefined auto-approval rule templates
AUTO_APPROVAL_RULE_TEMPLATES = [
    {
        'name': 'High Quality Leads',
        'description': 'Auto-approve high quality, well-qualified leads',
        'approval_types': ['lead_qualification', 'email_content_review'],
        'auto_approve_threshold': 0.85,
        'min_qualification_score': 0.7,
        'priority': 100
    },
    {
        'name': 'Demo Sites - Tech Categories',
        'description': 'Auto-approve demo sites for tech-related categories',
        'approval_types': ['demo_site_review'],
        'auto_approve_threshold': 0.80,
        'lead_categories': ['software', 'web development', 'IT', 'tech'],
        'priority': 90
    },
    {
        'name': 'Short Videos',
        'description': 'Auto-approve short, high-quality videos',
        'approval_types': ['video_review'],
        'auto_approve_threshold': 0.75,
        'priority': 80
    },
    {
        'name': 'Template-Based Emails',
        'description': 'Auto-approve emails generated from proven templates',
        'approval_types': ['email_content_review'],
        'auto_approve_threshold': 0.82,
        'excluded_keywords': ['urgent', 'limited time', 'act now'],
        'priority': 70
    }
]
