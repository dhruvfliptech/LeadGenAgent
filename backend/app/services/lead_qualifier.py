"""
AI-powered Lead Qualification Service.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.leads import Lead
from app.models.qualification_criteria import QualificationCriteria
from app.core.config import settings

logger = logging.getLogger(__name__)


class LeadQualifier:
    """Service for qualifying leads based on criteria and AI analysis."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def qualify_lead(
        self, 
        lead: Lead, 
        criteria: QualificationCriteria,
        use_ai: bool = True
    ) -> Tuple[float, str, Dict]:
        """
        Qualify a lead based on criteria.
        
        Returns:
            Tuple of (score, reasoning, detailed_scores)
        """
        detailed_scores = {}
        reasoning_parts = []
        
        # 1. Keyword scoring
        keyword_score, keyword_reason = self._score_keywords(lead, criteria)
        detailed_scores['keywords'] = keyword_score
        if keyword_reason:
            reasoning_parts.append(f"Keywords: {keyword_reason}")
        
        # 2. Compensation scoring
        comp_score, comp_reason = self._score_compensation(lead, criteria)
        detailed_scores['compensation'] = comp_score
        if comp_reason:
            reasoning_parts.append(f"Compensation: {comp_reason}")
        
        # 3. Location scoring
        location_score, location_reason = self._score_location(lead, criteria)
        detailed_scores['location'] = location_score
        if location_reason:
            reasoning_parts.append(f"Location: {location_reason}")
        
        # 4. Employment type scoring
        employment_score, employment_reason = self._score_employment_type(lead, criteria)
        detailed_scores['employment_type'] = employment_score
        if employment_reason:
            reasoning_parts.append(f"Employment: {employment_reason}")
        
        # 5. Freshness scoring
        freshness_score, freshness_reason = self._score_freshness(lead, criteria)
        detailed_scores['freshness'] = freshness_score
        if freshness_reason:
            reasoning_parts.append(f"Freshness: {freshness_reason}")
        
        # 6. Apply custom rules
        custom_score, custom_reason = self._apply_custom_rules(lead, criteria)
        detailed_scores['custom_rules'] = custom_score
        if custom_reason:
            reasoning_parts.append(f"Custom rules: {custom_reason}")
        
        # Calculate weighted total score
        total_score = (
            keyword_score * criteria.keyword_weight +
            comp_score * criteria.compensation_weight +
            location_score * criteria.location_weight +
            employment_score * criteria.employment_type_weight +
            freshness_score * criteria.freshness_weight
        )
        
        # Add custom rule adjustments (not weighted)
        total_score = max(0.0, min(1.0, total_score + custom_score))
        
        # Check hard requirements
        if criteria.require_contact_info and not (lead.email or lead.reply_email or lead.phone or lead.reply_phone):
            total_score = min(total_score, 0.3)
            reasoning_parts.append("Missing required contact information")
        
        if criteria.require_compensation_info and not lead.compensation:
            total_score = min(total_score, 0.3)
            reasoning_parts.append("Missing required compensation information")
        
        # Generate final reasoning
        if total_score >= criteria.auto_qualify_threshold:
            qualification = "HIGHLY QUALIFIED"
        elif total_score >= criteria.min_score_threshold:
            qualification = "QUALIFIED"
        elif total_score <= criteria.auto_reject_threshold:
            qualification = "NOT QUALIFIED"
        else:
            qualification = "NEEDS REVIEW"
        
        reasoning = f"{qualification} (Score: {total_score:.2f}). " + " | ".join(reasoning_parts)
        
        # Use AI for enhanced analysis if enabled
        if use_ai and settings.OPENAI_API_KEY:
            ai_analysis = await self._get_ai_analysis(lead, criteria, total_score)
            if ai_analysis:
                reasoning = f"{reasoning}\n\nAI Analysis: {ai_analysis}"
        
        return total_score, reasoning, detailed_scores
    
    def _score_keywords(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Score based on keyword matching."""
        score = 0.5  # Base score
        reasons = []
        
        # Combine title and description for searching
        text = f"{lead.title or ''} {lead.description or ''}".lower()
        
        # Check required keywords (all must be present)
        if criteria.required_keywords:
            missing = []
            for keyword in criteria.required_keywords:
                if keyword.lower() not in text:
                    missing.append(keyword)
            
            if missing:
                score = 0.0
                reasons.append(f"Missing required: {', '.join(missing)}")
            else:
                score = 0.7
                reasons.append("Has all required keywords")
        
        # Check excluded keywords (disqualify if found)
        if criteria.excluded_keywords:
            found_excluded = []
            for keyword in criteria.excluded_keywords:
                if keyword.lower() in text:
                    found_excluded.append(keyword)
            
            if found_excluded:
                score = 0.0
                reasons.append(f"Contains excluded: {', '.join(found_excluded)}")
                return score, "; ".join(reasons)
        
        # Check preferred keywords (bonus points)
        if criteria.preferred_keywords:
            found_preferred = []
            for keyword in criteria.preferred_keywords:
                if keyword.lower() in text:
                    found_preferred.append(keyword)
            
            if found_preferred:
                bonus = min(0.3, len(found_preferred) * 0.1)
                score = min(1.0, score + bonus)
                reasons.append(f"Has preferred: {', '.join(found_preferred[:3])}")
        
        return score, "; ".join(reasons) if reasons else ""
    
    def _score_compensation(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Score based on compensation."""
        if not criteria.min_compensation and not criteria.max_compensation:
            return 0.5, ""  # Neutral if no criteria
        
        # Extract numeric compensation from lead
        comp_value = None
        if lead.compensation:
            # Try to extract number from compensation string
            numbers = re.findall(r'[\d,]+(?:\.\d+)?', lead.compensation.replace(',', ''))
            if numbers:
                try:
                    comp_value = float(numbers[0])
                except:
                    pass
        
        if lead.price:
            comp_value = lead.price
        
        if comp_value is None:
            return 0.3, "No compensation data"
        
        score = 1.0
        reasons = []
        
        if criteria.min_compensation and comp_value < criteria.min_compensation:
            score = max(0.0, comp_value / criteria.min_compensation)
            reasons.append(f"Below minimum (${comp_value:.0f} < ${criteria.min_compensation:.0f})")
        elif criteria.max_compensation and comp_value > criteria.max_compensation:
            score = 0.5  # Not necessarily bad if over max
            reasons.append(f"Above maximum (${comp_value:.0f})")
        else:
            reasons.append(f"Within range (${comp_value:.0f})")
        
        return score, "; ".join(reasons) if reasons else ""
    
    def _score_location(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Score based on location preferences."""
        score = 0.5
        reasons = []
        
        # Check if remote and remote is acceptable
        if lead.is_remote:
            if criteria.remote_acceptable:
                score = 1.0
                reasons.append("Remote position")
            else:
                score = 0.0
                reasons.append("Remote not acceptable")
            return score, "; ".join(reasons)
        
        # Check preferred locations
        if criteria.preferred_locations:
            if lead.location:
                location_match = False
                for pref in criteria.preferred_locations:
                    if isinstance(pref, int) and lead.location_id == pref:
                        location_match = True
                    elif isinstance(pref, str) and pref.lower() in lead.location.name.lower():
                        location_match = True
                
                if location_match:
                    score = 1.0
                    reasons.append("Preferred location")
                else:
                    score = 0.3
                    reasons.append("Not preferred location")
        
        # Check neighborhood if specified
        if lead.neighborhood:
            reasons.append(f"In {lead.neighborhood}")
        
        return score, "; ".join(reasons) if reasons else ""
    
    def _score_employment_type(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Score based on employment type preferences."""
        score = 0.5
        reasons = []
        
        # Check internship
        if lead.is_internship:
            if criteria.internship_acceptable:
                score = 0.7
                reasons.append("Internship")
            else:
                score = 0.0
                reasons.append("Internship not acceptable")
                return score, "; ".join(reasons)
        
        # Check nonprofit
        if lead.is_nonprofit:
            if criteria.nonprofit_acceptable:
                score = 0.8
                reasons.append("Nonprofit")
            else:
                score = 0.2
                reasons.append("Nonprofit not preferred")
        
        # Check employment types
        if lead.employment_type and criteria.preferred_employment_types:
            matches = set(lead.employment_type) & set(criteria.preferred_employment_types)
            if matches:
                score = 1.0
                reasons.append(f"Matches: {', '.join(matches)}")
            else:
                score = 0.3
                reasons.append(f"Type mismatch")
        
        return score, "; ".join(reasons) if reasons else ""
    
    def _score_freshness(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Score based on how recent the posting is."""
        if not lead.posted_at:
            return 0.5, "Unknown posting date"
        
        days_old = (datetime.now(lead.posted_at.tzinfo) - lead.posted_at).days
        
        if days_old > criteria.max_days_old:
            return 0.0, f"Too old ({days_old} days)"
        
        # Linear decay based on age
        score = 1.0 - (days_old / criteria.max_days_old) * 0.5
        
        if days_old == 0:
            return score, "Posted today"
        elif days_old == 1:
            return score, "Posted yesterday"
        else:
            return score, f"Posted {days_old} days ago"
    
    def _apply_custom_rules(self, lead: Lead, criteria: QualificationCriteria) -> Tuple[float, str]:
        """Apply custom scoring rules."""
        if not criteria.custom_rules:
            return 0.0, ""
        
        score_adjustment = 0.0
        reasons = []
        text = f"{lead.title or ''} {lead.description or ''}".lower()
        
        # Check "must_have_any"
        if 'must_have_any' in criteria.custom_rules:
            keywords = criteria.custom_rules['must_have_any']
            if not any(kw.lower() in text for kw in keywords):
                score_adjustment -= 0.5
                reasons.append("Missing required skills")
        
        # Apply boosts
        if 'boost_if_contains' in criteria.custom_rules:
            for keyword, boost in criteria.custom_rules['boost_if_contains'].items():
                if keyword.lower() in text:
                    score_adjustment += boost
                    reasons.append(f"+{keyword}")
        
        # Apply penalties
        if 'penalty_if_contains' in criteria.custom_rules:
            for keyword, penalty in criteria.custom_rules['penalty_if_contains'].items():
                if keyword.lower() in text:
                    score_adjustment += penalty  # penalty is negative
                    reasons.append(f"-{keyword}")
        
        return score_adjustment, "; ".join(reasons) if reasons else ""
    
    async def _get_ai_analysis(self, lead: Lead, criteria: QualificationCriteria, score: float) -> Optional[str]:
        """Get AI analysis of the lead (placeholder for OpenAI integration)."""
        # This will be implemented with actual OpenAI API calls
        # For now, return None
        return None
    
    async def batch_qualify_leads(
        self,
        leads: List[Lead],
        criteria: QualificationCriteria,
        update_database: bool = True
    ) -> List[Dict]:
        """
        Qualify multiple leads and optionally update the database.
        
        Returns:
            List of qualification results
        """
        results = []
        
        for lead in leads:
            try:
                score, reasoning, detailed = await self.qualify_lead(lead, criteria)
                
                if update_database:
                    lead.qualification_score = score
                    lead.qualification_reasoning = reasoning
                    lead.has_been_qualified = True
                    lead.qualified_at = datetime.now()
                    
                    # Update status based on score
                    if score >= criteria.auto_qualify_threshold:
                        lead.status = 'qualified'
                    elif score <= criteria.auto_reject_threshold:
                        lead.status = 'rejected'
                    else:
                        lead.status = 'review'
                
                results.append({
                    'lead_id': lead.id,
                    'craigslist_id': lead.craigslist_id,
                    'title': lead.title,
                    'score': score,
                    'status': lead.status,
                    'reasoning': reasoning,
                    'detailed_scores': detailed
                })
                
            except Exception as e:
                logger.error(f"Error qualifying lead {lead.id}: {str(e)}")
                results.append({
                    'lead_id': lead.id,
                    'error': str(e)
                })
        
        if update_database:
            await self.db.commit()
        
        return results
    
    async def get_qualification_stats(self, criteria_id: Optional[int] = None) -> Dict:
        """Get statistics about lead qualification."""
        query = select(Lead).where(Lead.has_been_qualified == True)
        
        result = await self.db.execute(query)
        leads = result.scalars().all()
        
        if not leads:
            return {
                'total_qualified': 0,
                'average_score': 0,
                'status_breakdown': {},
                'score_distribution': {}
            }
        
        total = len(leads)
        avg_score = sum(l.qualification_score for l in leads if l.qualification_score) / total
        
        status_breakdown = {}
        score_distribution = {
            'high': 0,  # >= 0.8
            'medium': 0,  # 0.5 - 0.8
            'low': 0,  # < 0.5
        }
        
        for lead in leads:
            # Status breakdown
            status = lead.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            # Score distribution
            if lead.qualification_score:
                if lead.qualification_score >= 0.8:
                    score_distribution['high'] += 1
                elif lead.qualification_score >= 0.5:
                    score_distribution['medium'] += 1
                else:
                    score_distribution['low'] += 1
        
        return {
            'total_qualified': total,
            'average_score': round(avg_score, 3),
            'status_breakdown': status_breakdown,
            'score_distribution': score_distribution
        }