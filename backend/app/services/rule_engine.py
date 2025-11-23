"""
Advanced rule engine for filtering and automation.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_

from app.core.database import get_db
from app.models.leads import Lead
from app.models.rules import (
    FilterRule, RuleSet, RuleSetRule, ExcludeList, ExcludeListItem,
    RuleExecution, RuleOperator, RuleLogic, RuleAction
)
from app.models.notifications import Notification


logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Evaluates individual rules against lead data."""
    
    def __init__(self):
        self.operators = {
            RuleOperator.EQUALS: self._op_equals,
            RuleOperator.NOT_EQUALS: self._op_not_equals,
            RuleOperator.CONTAINS: self._op_contains,
            RuleOperator.NOT_CONTAINS: self._op_not_contains,
            RuleOperator.STARTS_WITH: self._op_starts_with,
            RuleOperator.ENDS_WITH: self._op_ends_with,
            RuleOperator.REGEX_MATCH: self._op_regex_match,
            RuleOperator.GREATER_THAN: self._op_greater_than,
            RuleOperator.LESS_THAN: self._op_less_than,
            RuleOperator.GREATER_EQUAL: self._op_greater_equal,
            RuleOperator.LESS_EQUAL: self._op_less_equal,
            RuleOperator.BETWEEN: self._op_between,
            RuleOperator.IN_LIST: self._op_in_list,
            RuleOperator.NOT_IN_LIST: self._op_not_in_list,
            RuleOperator.IS_EMPTY: self._op_is_empty,
            RuleOperator.IS_NOT_EMPTY: self._op_is_not_empty,
        }
    
    def evaluate_rule(self, rule: FilterRule, lead: Lead) -> bool:
        """Evaluate a single rule against lead data."""
        try:
            # Get field value from lead
            field_value = self._get_field_value(lead, rule.field_name)
            
            # Get operator function
            operator_func = self.operators.get(rule.operator)
            if not operator_func:
                logger.error(f"Unknown operator: {rule.operator}")
                return False
            
            # Evaluate rule
            result = operator_func(field_value, rule)
            
            logger.debug(f"Rule {rule.id} evaluated: {field_value} {rule.operator} {rule.value} = {result}")
            return result
            
        except Exception as e:
            logger.error(f"Rule evaluation failed for rule {rule.id}: {e}")
            return False
    
    def _get_field_value(self, lead: Lead, field_name: str) -> Any:
        """Extract field value from lead object."""
        try:
            # Handle nested fields (e.g., "location.name")
            if '.' in field_name:
                obj = lead
                for part in field_name.split('.'):
                    obj = getattr(obj, part, None)
                    if obj is None:
                        break
                return obj
            
            # Handle computed fields
            if field_name == "age_hours":
                if lead.scraped_at:
                    return (datetime.utcnow() - lead.scraped_at).total_seconds() / 3600
                return 0
            
            if field_name == "title_length":
                return len(lead.title) if lead.title else 0
            
            if field_name == "description_length":
                return len(lead.description) if lead.description else 0
            
            if field_name == "has_email":
                return bool(lead.email)
            
            if field_name == "has_phone":
                return bool(lead.phone)
            
            # Standard field access
            return getattr(lead, field_name, None)
            
        except Exception as e:
            logger.error(f"Failed to get field value {field_name}: {e}")
            return None
    
    # Operator implementations
    def _op_equals(self, field_value: Any, rule: FilterRule) -> bool:
        """Equals operator."""
        return str(field_value).lower() == str(rule.value).lower()
    
    def _op_not_equals(self, field_value: Any, rule: FilterRule) -> bool:
        """Not equals operator."""
        return str(field_value).lower() != str(rule.value).lower()
    
    def _op_contains(self, field_value: Any, rule: FilterRule) -> bool:
        """Contains operator."""
        if field_value is None:
            return False
        return str(rule.value).lower() in str(field_value).lower()
    
    def _op_not_contains(self, field_value: Any, rule: FilterRule) -> bool:
        """Not contains operator."""
        if field_value is None:
            return True
        return str(rule.value).lower() not in str(field_value).lower()
    
    def _op_starts_with(self, field_value: Any, rule: FilterRule) -> bool:
        """Starts with operator."""
        if field_value is None:
            return False
        return str(field_value).lower().startswith(str(rule.value).lower())
    
    def _op_ends_with(self, field_value: Any, rule: FilterRule) -> bool:
        """Ends with operator."""
        if field_value is None:
            return False
        return str(field_value).lower().endswith(str(rule.value).lower())
    
    def _op_regex_match(self, field_value: Any, rule: FilterRule) -> bool:
        """Regex match operator."""
        if field_value is None or not rule.regex_pattern:
            return False
        try:
            return bool(re.search(rule.regex_pattern, str(field_value), re.IGNORECASE))
        except re.error as e:
            logger.error(f"Invalid regex pattern {rule.regex_pattern}: {e}")
            return False
    
    def _op_greater_than(self, field_value: Any, rule: FilterRule) -> bool:
        """Greater than operator."""
        try:
            return float(field_value) > float(rule.value)
        except (ValueError, TypeError):
            return False
    
    def _op_less_than(self, field_value: Any, rule: FilterRule) -> bool:
        """Less than operator."""
        try:
            return float(field_value) < float(rule.value)
        except (ValueError, TypeError):
            return False
    
    def _op_greater_equal(self, field_value: Any, rule: FilterRule) -> bool:
        """Greater than or equal operator."""
        try:
            return float(field_value) >= float(rule.value)
        except (ValueError, TypeError):
            return False
    
    def _op_less_equal(self, field_value: Any, rule: FilterRule) -> bool:
        """Less than or equal operator."""
        try:
            return float(field_value) <= float(rule.value)
        except (ValueError, TypeError):
            return False
    
    def _op_between(self, field_value: Any, rule: FilterRule) -> bool:
        """Between operator."""
        try:
            value = float(field_value)
            return rule.min_value <= value <= rule.max_value
        except (ValueError, TypeError):
            return False
    
    def _op_in_list(self, field_value: Any, rule: FilterRule) -> bool:
        """In list operator."""
        if not rule.value_list:
            return False
        return str(field_value).lower() in [str(v).lower() for v in rule.value_list]
    
    def _op_not_in_list(self, field_value: Any, rule: FilterRule) -> bool:
        """Not in list operator."""
        if not rule.value_list:
            return True
        return str(field_value).lower() not in [str(v).lower() for v in rule.value_list]
    
    def _op_is_empty(self, field_value: Any, rule: FilterRule) -> bool:
        """Is empty operator."""
        return field_value is None or str(field_value).strip() == ""
    
    def _op_is_not_empty(self, field_value: Any, rule: FilterRule) -> bool:
        """Is not empty operator."""
        return field_value is not None and str(field_value).strip() != ""


class ExcludeListProcessor:
    """Processes exclude lists for filtering."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def is_lead_excluded(self, lead: Lead) -> Tuple[bool, Optional[str]]:
        """Check if lead should be excluded based on exclude lists."""
        try:
            # Get active exclude lists
            exclude_lists = self.db.query(ExcludeList).filter(
                ExcludeList.is_active == True
            ).all()
            
            for exclude_list in exclude_lists:
                excluded, reason = self._check_exclude_list(lead, exclude_list)
                if excluded:
                    return True, reason
            
            return False, None
            
        except Exception as e:
            logger.error(f"Failed to check exclude lists: {e}")
            return False, None
    
    def _check_exclude_list(self, lead: Lead, exclude_list: ExcludeList) -> Tuple[bool, Optional[str]]:
        """Check lead against specific exclude list."""
        try:
            items = self.db.query(ExcludeListItem).filter(
                ExcludeListItem.exclude_list_id == exclude_list.id
            ).all()
            
            for item in items:
                if self._item_matches_lead(lead, exclude_list, item):
                    # Update match tracking
                    item.match_count += 1
                    item.last_matched_at = datetime.utcnow()
                    exclude_list.match_count += 1
                    exclude_list.last_matched_at = datetime.utcnow()
                    self.db.commit()
                    
                    return True, f"Excluded by {exclude_list.name}: {item.value}"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Failed to check exclude list {exclude_list.id}: {e}")
            return False, None
    
    def _item_matches_lead(self, lead: Lead, exclude_list: ExcludeList, item: ExcludeListItem) -> bool:
        """Check if exclude list item matches lead."""
        try:
            # Get field value based on list type
            if exclude_list.list_type == "email":
                field_value = lead.email
            elif exclude_list.list_type == "phone":
                field_value = lead.phone
            elif exclude_list.list_type == "keyword":
                field_value = f"{lead.title} {lead.description}"
            elif exclude_list.list_type == "domain":
                if lead.email:
                    field_value = lead.email.split('@')[-1] if '@' in lead.email else ""
                else:
                    field_value = ""
            else:
                return False
            
            if not field_value:
                return False
            
            # Apply case sensitivity
            if not exclude_list.is_case_sensitive:
                field_value = field_value.lower()
                item_value = item.value.lower()
            else:
                item_value = item.value
            
            # Apply match type
            if exclude_list.match_type == "exact":
                return field_value == item_value
            elif exclude_list.match_type == "partial":
                return item_value in field_value
            elif exclude_list.match_type == "regex":
                try:
                    pattern = item.pattern or item.value
                    return bool(re.search(pattern, field_value, 0 if exclude_list.is_case_sensitive else re.IGNORECASE))
                except re.error:
                    logger.error(f"Invalid regex pattern: {item.pattern}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to match exclude item: {e}")
            return False


class ActionProcessor:
    """Processes rule actions when rules match."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_action(self, rule: FilterRule, lead: Lead) -> bool:
        """Process rule action."""
        try:
            action_config = rule.action_config or {}
            
            if rule.action == RuleAction.ACCEPT:
                return await self._action_accept(lead, action_config)
            elif rule.action == RuleAction.REJECT:
                return await self._action_reject(lead, action_config)
            elif rule.action == RuleAction.PRIORITY_HIGH:
                return await self._action_priority_high(lead, action_config)
            elif rule.action == RuleAction.PRIORITY_LOW:
                return await self._action_priority_low(lead, action_config)
            elif rule.action == RuleAction.AUTO_RESPOND:
                return await self._action_auto_respond(lead, action_config)
            elif rule.action == RuleAction.NOTIFY:
                return await self._action_notify(lead, rule, action_config)
            elif rule.action == RuleAction.TAG:
                return await self._action_tag(lead, action_config)
            elif rule.action == RuleAction.ASSIGN:
                return await self._action_assign(lead, action_config)
            else:
                logger.warning(f"Unknown action: {rule.action}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to process action {rule.action}: {e}")
            return False
    
    async def _action_accept(self, lead: Lead, config: Dict) -> bool:
        """Accept lead action."""
        lead.status = "qualified"
        self.db.commit()
        return True
    
    async def _action_reject(self, lead: Lead, config: Dict) -> bool:
        """Reject lead action."""
        lead.status = "rejected"
        self.db.commit()
        return True
    
    async def _action_priority_high(self, lead: Lead, config: Dict) -> bool:
        """Set high priority action."""
        # This would set priority in a priority field (if exists)
        # For now, we'll use status
        if lead.status == "new":
            lead.status = "priority_high"
            self.db.commit()
        return True
    
    async def _action_priority_low(self, lead: Lead, config: Dict) -> bool:
        """Set low priority action."""
        if lead.status == "new":
            lead.status = "priority_low"
            self.db.commit()
        return True
    
    async def _action_auto_respond(self, lead: Lead, config: Dict) -> bool:
        """Trigger auto-response action."""
        try:
            from app.services.auto_responder import auto_responder_service
            
            template_id = config.get("template_id")
            delay_minutes = config.get("delay_minutes", 0)
            
            if not template_id:
                logger.error("Auto-respond action missing template_id")
                return False
            
            await auto_responder_service.create_auto_response(
                lead.id, template_id, delay_minutes
            )
            return True
            
        except Exception as e:
            logger.error(f"Auto-respond action failed: {e}")
            return False
    
    async def _action_notify(self, lead: Lead, rule: FilterRule, config: Dict) -> bool:
        """Send notification action."""
        try:
            notification = Notification(
                notification_type="rule_triggered",
                priority=config.get("priority", "normal"),
                title=config.get("title", f"Rule '{rule.name}' triggered"),
                message=config.get("message", f"Lead '{lead.title}' matched rule '{rule.name}'"),
                source_type="lead",
                source_id=lead.id,
                channels=config.get("channels", ["websocket"]),
                data={
                    "lead_id": lead.id,
                    "rule_id": rule.id,
                    "rule_name": rule.name
                }
            )
            
            self.db.add(notification)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Notify action failed: {e}")
            return False
    
    async def _action_tag(self, lead: Lead, config: Dict) -> bool:
        """Tag lead action."""
        # This would add tags to a tags field or related table
        # For now, we'll add to category or create a simple tag system
        tags = config.get("tags", [])
        if tags and hasattr(lead, "tags"):
            # Assuming tags field exists
            existing_tags = lead.tags or []
            lead.tags = list(set(existing_tags + tags))
            self.db.commit()
        return True
    
    async def _action_assign(self, lead: Lead, config: Dict) -> bool:
        """Assign lead action."""
        # This would assign to a user/agent
        assignee = config.get("assignee")
        if assignee and hasattr(lead, "assigned_to"):
            lead.assigned_to = assignee
            self.db.commit()
        return True


class RuleEngine:
    """Main rule engine for processing leads."""
    
    def __init__(self):
        self.db = None  # Will be set per request
        self.evaluator = RuleEvaluator()
        self.exclude_processor = None  # Will be set per request
        self.action_processor = None  # Will be set per request
    
    async def process_lead(self, lead: Lead) -> Dict[str, Any]:
        """Process a lead through all active rules."""
        start_time = datetime.utcnow()
        results = {
            "lead_id": lead.id,
            "processed_at": start_time,
            "excluded": False,
            "exclude_reason": None,
            "rules_matched": [],
            "actions_taken": [],
            "processing_time_ms": 0
        }
        
        try:
            # Check exclude lists first
            excluded, exclude_reason = self.exclude_processor.is_lead_excluded(lead)
            if excluded:
                results["excluded"] = True
                results["exclude_reason"] = exclude_reason
                logger.info(f"Lead {lead.id} excluded: {exclude_reason}")
                return results
            
            # Get active rule sets ordered by priority
            rule_sets = self.db.query(RuleSet).filter(
                RuleSet.is_active == True
            ).order_by(RuleSet.priority).all()
            
            # Process rule sets
            for rule_set in rule_sets:
                matched = await self._process_rule_set(lead, rule_set)
                if matched:
                    results["rules_matched"].append({
                        "rule_set_id": rule_set.id,
                        "rule_set_name": rule_set.name
                    })
            
            # Get individual rules not in rule sets
            individual_rules = self.db.query(FilterRule).filter(
                and_(
                    FilterRule.is_active == True,
                    ~FilterRule.rule_sets.any()
                )
            ).order_by(FilterRule.priority).all()
            
            # Process individual rules
            for rule in individual_rules:
                matched = await self._process_individual_rule(lead, rule)
                if matched:
                    results["rules_matched"].append({
                        "rule_id": rule.id,
                        "rule_name": rule.name
                    })
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            results["processing_time_ms"] = processing_time
            
            logger.info(f"Processed lead {lead.id} in {processing_time:.2f}ms, {len(results['rules_matched'])} rules matched")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process lead {lead.id}: {e}")
            results["error"] = str(e)
            return results
    
    async def _process_rule_set(self, lead: Lead, rule_set: RuleSet) -> bool:
        """Process a rule set against a lead."""
        try:
            # Get rules in the rule set
            rule_relations = self.db.query(RuleSetRule).filter(
                RuleSetRule.rule_set_id == rule_set.id
            ).order_by(RuleSetRule.order_index).all()
            
            if not rule_relations:
                return False
            
            rules = []
            for relation in rule_relations:
                rule = self.db.query(FilterRule).filter(
                    FilterRule.id == relation.rule_id
                ).first()
                if rule and rule.is_active:
                    rules.append(rule)
            
            if not rules:
                return False
            
            # Evaluate rules based on logic operator
            rule_results = []
            for rule in rules:
                result = self.evaluator.evaluate_rule(rule, lead)
                rule_results.append(result)
                
                # Track rule evaluation
                await self._log_rule_execution(lead, rule, None, result)
            
            # Apply logic operator
            if rule_set.logic_operator == RuleLogic.AND:
                rule_set_matched = all(rule_results)
            elif rule_set.logic_operator == RuleLogic.OR:
                rule_set_matched = any(rule_results)
            else:  # NOT logic (negate first rule)
                rule_set_matched = not rule_results[0] if rule_results else False
            
            # Update rule set statistics
            rule_set.evaluation_count += 1
            if rule_set_matched:
                rule_set.match_count += 1
                rule_set.last_matched_at = datetime.utcnow()
            
            # Log rule set execution
            await self._log_rule_execution(lead, None, rule_set, rule_set_matched)
            
            self.db.commit()
            
            return rule_set_matched
            
        except Exception as e:
            logger.error(f"Failed to process rule set {rule_set.id}: {e}")
            return False
    
    async def _process_individual_rule(self, lead: Lead, rule: FilterRule) -> bool:
        """Process an individual rule against a lead."""
        try:
            # Evaluate rule
            matched = self.evaluator.evaluate_rule(rule, lead)
            
            # Update rule statistics
            rule.evaluation_count += 1
            if matched:
                rule.match_count += 1
                rule.last_matched_at = datetime.utcnow()
                
                # Process action
                action_success = await self.action_processor.process_action(rule, lead)
                if action_success:
                    logger.info(f"Action {rule.action} executed for rule {rule.id}")
            
            # Log rule execution
            await self._log_rule_execution(lead, rule, None, matched)
            
            self.db.commit()
            
            return matched
            
        except Exception as e:
            logger.error(f"Failed to process rule {rule.id}: {e}")
            return False
    
    async def _log_rule_execution(
        self, 
        lead: Lead, 
        rule: Optional[FilterRule], 
        rule_set: Optional[RuleSet], 
        matched: bool
    ):
        """Log rule execution for debugging and analytics."""
        try:
            # Collect evaluation data
            evaluation_data = {
                "title": lead.title,
                "category": lead.category,
                "price": lead.price,
                "location": lead.location.name if lead.location else None,
                "has_email": bool(lead.email),
                "has_phone": bool(lead.phone),
                "status": lead.status,
                "age_hours": (datetime.utcnow() - lead.scraped_at).total_seconds() / 3600 if lead.scraped_at else 0
            }
            
            execution = RuleExecution(
                lead_id=lead.id,
                rule_id=rule.id if rule else None,
                rule_set_id=rule_set.id if rule_set else None,
                matched=matched,
                evaluation_data=evaluation_data,
                executed_at=datetime.utcnow()
            )
            
            self.db.add(execution)
            
        except Exception as e:
            logger.error(f"Failed to log rule execution: {e}")
    
    def get_rule_analytics(self, days: int = 30) -> Dict:
        """Get rule engine performance analytics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Overall statistics
            total_executions = self.db.query(RuleExecution).filter(
                RuleExecution.executed_at >= cutoff_date
            ).count()
            
            matched_executions = self.db.query(RuleExecution).filter(
                and_(
                    RuleExecution.executed_at >= cutoff_date,
                    RuleExecution.matched == True
                )
            ).count()
            
            # Rule performance
            rule_stats = self.db.query(FilterRule).filter(
                FilterRule.evaluation_count > 0
            ).all()
            
            rule_performance = []
            for rule in rule_stats:
                rule_performance.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "evaluations": rule.evaluation_count,
                    "matches": rule.match_count,
                    "match_rate": rule.match_rate,
                    "last_matched": rule.last_matched_at.isoformat() if rule.last_matched_at else None
                })
            
            # Top performing rules
            top_rules = sorted(rule_performance, key=lambda x: x["match_rate"], reverse=True)[:10]
            
            return {
                "total_executions": total_executions,
                "matched_executions": matched_executions,
                "overall_match_rate": (matched_executions / total_executions * 100) if total_executions > 0 else 0,
                "active_rules": len([r for r in rule_stats if r.is_active]),
                "top_performing_rules": top_rules,
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get rule analytics: {e}")
            return {}


# Global service instance
rule_engine = RuleEngine()