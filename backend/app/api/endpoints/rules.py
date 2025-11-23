"""
API endpoints for rule engine management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from datetime import datetime

from app.core.database import get_db
from app.models.rules import (
    FilterRule, RuleSet, RuleSetRule, ExcludeList, ExcludeListItem,
    RuleExecution, RuleOperator, RuleLogic, RuleAction
)
from app.services.rule_engine import rule_engine
from pydantic import BaseModel


router = APIRouter()


# Pydantic models
class FilterRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: int = 100
    field_name: str
    operator: str
    value: Optional[str] = None
    value_list: Optional[List[str]] = None
    regex_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    action: str
    action_config: Optional[Dict[str, Any]] = None


class FilterRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    field_name: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    value_list: Optional[List[str]] = None
    regex_pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    action: Optional[str] = None
    action_config: Optional[Dict[str, Any]] = None


class FilterRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    is_active: bool
    priority: int
    field_name: str
    operator: str
    value: Optional[str]
    value_list: Optional[List[str]]
    regex_pattern: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    action: str
    action_config: Optional[Dict[str, Any]]
    evaluation_count: int
    match_count: int
    match_rate: float
    last_matched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuleSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    priority: int = 100
    logic_operator: str = "and"
    rule_ids: List[int] = []


class RuleSetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    logic_operator: Optional[str] = None
    rule_ids: Optional[List[int]] = None


class RuleSetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    logic_operator: str
    evaluation_count: int
    match_count: int
    match_rate: float
    last_matched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExcludeListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    list_type: str
    is_case_sensitive: bool = False
    match_type: str = "exact"
    items: List[str] = []


class ExcludeListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_case_sensitive: Optional[bool] = None
    match_type: Optional[str] = None


class ExcludeListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    list_type: str
    is_active: bool
    is_case_sensitive: bool
    match_type: str
    match_count: int
    last_matched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExcludeListItemCreate(BaseModel):
    value: str
    pattern: Optional[str] = None
    notes: Optional[str] = None


class ExcludeListItemResponse(BaseModel):
    id: int
    exclude_list_id: int
    value: str
    pattern: Optional[str]
    notes: Optional[str]
    match_count: int
    last_matched_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Filter Rule endpoints
@router.get("/rules/", response_model=List[FilterRuleResponse])
async def get_filter_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    action: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get filter rules with optional filtering."""
    query = select(FilterRule)
    
    if category:
        query = query.where(FilterRule.category == category)
    if is_active is not None:
        query = query.where(FilterRule.is_active == is_active)
    if action:
        query = query.where(FilterRule.action == action)
    
    result = await db.execute(query.order_by(FilterRule.priority).offset(skip).limit(limit))
    rules = result.scalars().all()
    return rules


@router.get("/rules/{rule_id}", response_model=FilterRuleResponse)
async def get_filter_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific filter rule."""
    rule = select(FilterRule).filter(FilterRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules/", response_model=FilterRuleResponse)
async def create_filter_rule(rule_data: FilterRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new filter rule."""
    # Validate operator
    if rule_data.operator not in [e.value for e in RuleOperator]:
        raise HTTPException(status_code=400, detail=f"Invalid operator: {rule_data.operator}")
    
    # Validate action
    if rule_data.action not in [e.value for e in RuleAction]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {rule_data.action}")
    
    rule = FilterRule(**rule_data.dict())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=FilterRuleResponse)
async def update_filter_rule(
    rule_id: int,
    rule_data: FilterRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a filter rule."""
    rule = select(FilterRule).filter(FilterRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = rule_data.dict(exclude_unset=True)
    
    # Validate operator if provided
    if "operator" in update_data and update_data["operator"] not in [e.value for e in RuleOperator]:
        raise HTTPException(status_code=400, detail=f"Invalid operator: {update_data['operator']}")
    
    # Validate action if provided
    if "action" in update_data and update_data["action"] not in [e.value for e in RuleAction]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {update_data['action']}")
    
    for field, value in update_data.items():
        setattr(rule, field, value)
    
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_filter_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a filter rule."""
    rule = select(FilterRule).filter(FilterRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted successfully"}


# Rule Set endpoints
@router.get("/rule-sets/", response_model=List[RuleSetResponse])
async def get_rule_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get rule sets with optional filtering."""
    query = select(RuleSet)
    
    if is_active is not None:
        query = query.where(RuleSet.is_active == is_active)
    
    result = await db.execute(query.order_by(RuleSet.priority).offset(skip).limit(limit))
    rule_sets = result.scalars().all()
    return rule_sets


@router.get("/rule-sets/{rule_set_id}", response_model=RuleSetResponse)
async def get_rule_set(rule_set_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific rule set."""
    rule_set = select(RuleSet).filter(RuleSet.id == rule_set_id).first()
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return rule_set


@router.post("/rule-sets/", response_model=RuleSetResponse)
async def create_rule_set(rule_set_data: RuleSetCreate, db: AsyncSession = Depends(get_db)):
    """Create a new rule set."""
    # Validate logic operator
    if rule_set_data.logic_operator not in [e.value for e in RuleLogic]:
        raise HTTPException(status_code=400, detail=f"Invalid logic operator: {rule_set_data.logic_operator}")
    
    # Validate rule IDs exist
    if rule_set_data.rule_ids:
        existing_rules = db.query(FilterRule.id).filter(
            FilterRule.id.in_(rule_set_data.rule_ids)
        ).all()
        existing_ids = [r.id for r in existing_rules]
        invalid_ids = set(rule_set_data.rule_ids) - set(existing_ids)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Invalid rule IDs: {list(invalid_ids)}")
    
    # Create rule set
    rule_set = RuleSet(
        name=rule_set_data.name,
        description=rule_set_data.description,
        priority=rule_set_data.priority,
        logic_operator=rule_set_data.logic_operator
    )
    db.add(rule_set)
    await db.commit()
    await db.refresh(rule_set)
    
    # Add rule associations
    for i, rule_id in enumerate(rule_set_data.rule_ids):
        rule_association = RuleSetRule(
            rule_set_id=rule_set.id,
            rule_id=rule_id,
            order_index=i
        )
        db.add(rule_association)
    
    await db.commit()
    return rule_set


@router.get("/rule-sets/{rule_set_id}/rules")
async def get_rule_set_rules(rule_set_id: int, db: AsyncSession = Depends(get_db)):
    """Get rules in a rule set."""
    rule_set = select(RuleSet).filter(RuleSet.id == rule_set_id).first()
    if not rule_set:
        raise HTTPException(status_code=404, detail="Rule set not found")
    
    rule_relations = select(RuleSetRule).filter(
        RuleSetRule.rule_set_id == rule_set_id
    ).order_by(RuleSetRule.order_index).all()
    
    rules = []
    for relation in rule_relations:
        rule = select(FilterRule).filter(FilterRule.id == relation.rule_id).first()
        if rule:
            rules.append({
                "rule_id": rule.id,
                "name": rule.name,
                "field_name": rule.field_name,
                "operator": rule.operator,
                "action": rule.action,
                "is_active": rule.is_active,
                "order_index": relation.order_index
            })
    
    return {"rule_set_id": rule_set_id, "rules": rules}


# Exclude List endpoints
@router.get("/exclude-lists/", response_model=List[ExcludeListResponse])
async def get_exclude_lists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    list_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get exclude lists with optional filtering."""
    query = select(ExcludeList)
    
    if list_type:
        query = query.where(ExcludeList.list_type == list_type)
    if is_active is not None:
        query = query.where(ExcludeList.is_active == is_active)
    
    result = await db.execute(query.offset(skip).limit(limit))
    exclude_lists = result.scalars().all()
    return exclude_lists


@router.post("/exclude-lists/", response_model=ExcludeListResponse)
async def create_exclude_list(list_data: ExcludeListCreate, db: AsyncSession = Depends(get_db)):
    """Create a new exclude list."""
    exclude_list = ExcludeList(
        name=list_data.name,
        description=list_data.description,
        list_type=list_data.list_type,
        is_case_sensitive=list_data.is_case_sensitive,
        match_type=list_data.match_type
    )
    db.add(exclude_list)
    await db.commit()
    await db.refresh(exclude_list)
    
    # Add items
    for item_value in list_data.items:
        item = ExcludeListItem(
            exclude_list_id=exclude_list.id,
            value=item_value
        )
        db.add(item)
    
    await db.commit()
    return exclude_list


@router.get("/exclude-lists/{list_id}/items", response_model=List[ExcludeListItemResponse])
async def get_exclude_list_items(
    list_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get items in an exclude list."""
    exclude_list = select(ExcludeList).filter(ExcludeList.id == list_id).first()
    if not exclude_list:
        raise HTTPException(status_code=404, detail="Exclude list not found")
    
    items = select(ExcludeListItem).filter(
        ExcludeListItem.exclude_list_id == list_id
    ).offset(skip).limit(limit).all()
    
    return items


@router.post("/exclude-lists/{list_id}/items", response_model=ExcludeListItemResponse)
async def add_exclude_list_item(
    list_id: int,
    item_data: ExcludeListItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add an item to an exclude list."""
    exclude_list = select(ExcludeList).filter(ExcludeList.id == list_id).first()
    if not exclude_list:
        raise HTTPException(status_code=404, detail="Exclude list not found")
    
    item = ExcludeListItem(
        exclude_list_id=list_id,
        value=item_data.value,
        pattern=item_data.pattern,
        notes=item_data.notes
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/exclude-lists/{list_id}/items/{item_id}")
async def delete_exclude_list_item(list_id: int, item_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an item from an exclude list."""
    item = select(ExcludeListItem).filter(
        ExcludeListItem.id == item_id,
        ExcludeListItem.exclude_list_id == list_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Exclude list item not found")
    
    await db.delete(item)
    await db.commit()
    return {"message": "Exclude list item deleted successfully"}


# Rule Processing endpoints
@router.post("/rules/process-lead/{lead_id}")
async def process_lead_rules(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Process rules against a specific lead."""
    from app.models.leads import Lead
    
    lead = select(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        result = await rule_engine.process_lead(lead)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/test-rule/{rule_id}")
async def test_rule_against_lead(
    rule_id: int,
    lead_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Test a specific rule against a lead."""
    from app.models.leads import Lead
    from app.services.rule_engine import RuleEvaluator
    
    rule = select(FilterRule).filter(FilterRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    lead = select(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        evaluator = RuleEvaluator()
        result = evaluator.evaluate_rule(rule, lead)
        
        return {
            "rule_id": rule_id,
            "rule_name": rule.name,
            "lead_id": lead_id,
            "matched": result,
            "field_value": evaluator._get_field_value(lead, rule.field_name),
            "operator": rule.operator,
            "target_value": rule.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@router.get("/analytics/rules")
async def get_rule_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get rule engine performance analytics."""
    try:
        analytics = rule_engine.get_rule_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/rule-executions")
async def get_rule_executions(
    rule_id: Optional[int] = Query(None),
    lead_id: Optional[int] = Query(None),
    matched: Optional[bool] = Query(None),
    days: int = Query(7, ge=1, le=30),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get rule execution history."""
    from datetime import timedelta
    
    query = select(RuleExecution)
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(RuleExecution.executed_at >= cutoff_date)
    
    if rule_id:
        query = query.where(RuleExecution.rule_id == rule_id)
    if lead_id:
        query = query.where(RuleExecution.lead_id == lead_id)
    if matched is not None:
        query = query.where(RuleExecution.matched == matched)
    
    result = await db.execute(query.order_by(RuleExecution.executed_at.desc()).offset(skip).limit(limit))
    executions = result.scalars().all()
    
    return {
        "executions": [
            {
                "id": exec.id,
                "rule_id": exec.rule_id,
                "lead_id": exec.lead_id,
                "matched": exec.matched,
                "action_taken": exec.action_taken,
                "execution_time_ms": exec.execution_time_ms,
                "executed_at": exec.executed_at,
                "evaluation_data": exec.evaluation_data
            }
            for exec in executions
        ]
    }


# Configuration endpoints
@router.get("/config/operators")
async def get_available_operators():
    """Get available rule operators."""
    return {
        "operators": [
            {"value": op.value, "label": op.value.replace("_", " ").title()}
            for op in RuleOperator
        ]
    }


@router.get("/config/actions")
async def get_available_actions():
    """Get available rule actions."""
    return {
        "actions": [
            {"value": action.value, "label": action.value.replace("_", " ").title()}
            for action in RuleAction
        ]
    }


@router.get("/config/fields")
async def get_available_fields():
    """Get available fields for rule conditions."""
    from app.models.leads import Lead
    
    # Standard Lead fields
    lead_fields = [
        {"name": "title", "type": "text", "description": "Lead title"},
        {"name": "description", "type": "text", "description": "Lead description"},
        {"name": "category", "type": "text", "description": "Lead category"},
        {"name": "subcategory", "type": "text", "description": "Lead subcategory"},
        {"name": "price", "type": "number", "description": "Lead price"},
        {"name": "email", "type": "text", "description": "Contact email"},
        {"name": "phone", "type": "text", "description": "Contact phone"},
        {"name": "contact_name", "type": "text", "description": "Contact name"},
        {"name": "status", "type": "text", "description": "Lead status"},
        {"name": "location.name", "type": "text", "description": "Location name"},
        {"name": "posted_at", "type": "date", "description": "Posting date"},
        {"name": "scraped_at", "type": "date", "description": "Scraping date"}
    ]
    
    # Computed fields
    computed_fields = [
        {"name": "age_hours", "type": "number", "description": "Hours since scraped"},
        {"name": "title_length", "type": "number", "description": "Title character count"},
        {"name": "description_length", "type": "number", "description": "Description character count"},
        {"name": "has_email", "type": "boolean", "description": "Has email address"},
        {"name": "has_phone", "type": "boolean", "description": "Has phone number"}
    ]
    
    return {
        "fields": {
            "standard": lead_fields,
            "computed": computed_fields
        }
    }