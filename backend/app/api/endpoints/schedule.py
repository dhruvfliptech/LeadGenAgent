"""
API endpoints for schedule management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from datetime import datetime

from app.core.database import get_db
from app.models.schedules import (
    Schedule, ScheduleExecution, ScheduleTemplate, ScrapingSchedule,
    ScheduleNotification, ScheduleType, ScheduleStatus, RecurrenceType
)
from app.services.scheduler import scheduler_service, CronManager
from pydantic import BaseModel, validator


router = APIRouter()


# Pydantic models
class ScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str
    recurrence_type: str
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    task_config: Optional[Dict[str, Any]] = None
    timeout_minutes: int = 60
    max_retries: int = 3
    retry_delay_minutes: int = 5
    peak_hours_only: bool = False
    peak_start_hour: int = 9
    peak_end_hour: int = 17
    peak_timezone: str = "UTC"
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_config: Optional[Dict[str, Any]] = None

    @validator('cron_expression')
    def validate_cron(cls, v, values):
        if v and values.get('recurrence_type') == 'custom_cron':
            if not CronManager.is_valid_cron(v):
                raise ValueError('Invalid CRON expression')
        return v

    @validator('task_type')
    def validate_task_type(cls, v):
        valid_types = [t.value for t in ScheduleType]
        if v not in valid_types:
            raise ValueError(f'Invalid task type. Must be one of: {valid_types}')
        return v

    @validator('recurrence_type')
    def validate_recurrence_type(cls, v):
        valid_types = [t.value for t in RecurrenceType]
        if v not in valid_types:
            raise ValueError(f'Invalid recurrence type. Must be one of: {valid_types}')
        return v


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    task_config: Optional[Dict[str, Any]] = None
    timeout_minutes: Optional[int] = None
    max_retries: Optional[int] = None
    retry_delay_minutes: Optional[int] = None
    peak_hours_only: Optional[bool] = None
    peak_start_hour: Optional[int] = None
    peak_end_hour: Optional[int] = None
    peak_timezone: Optional[str] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_config: Optional[Dict[str, Any]] = None


class ScheduleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    task_type: str
    is_active: bool
    priority: int
    recurrence_type: str
    cron_expression: Optional[str]
    interval_minutes: Optional[int]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    task_config: Optional[Dict[str, Any]]
    timeout_minutes: int
    max_retries: int
    retry_delay_minutes: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    average_duration_seconds: Optional[float]
    peak_hours_only: bool
    peak_start_hour: int
    peak_end_hour: int
    peak_timezone: str
    notify_on_success: bool
    notify_on_failure: bool
    notification_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleExecutionResponse(BaseModel):
    id: int
    schedule_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    records_processed: Optional[int]
    records_created: Optional[int]
    records_updated: Optional[int]
    records_failed: Optional[int]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    retry_count: int
    result_data: Optional[Dict[str, Any]]
    log_file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ScrapingScheduleCreate(BaseModel):
    schedule_id: int
    location_ids: List[int]
    categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    delay_between_requests: float = 2.0
    concurrent_requests: int = 3
    pages_per_location: int = 5
    enable_email_extraction: bool = False
    enable_captcha_solving: bool = False
    min_lead_quality_score: float = 0.0
    skip_duplicates: bool = True
    duplicate_check_hours: int = 24
    adaptive_scheduling: bool = False
    peak_detection: bool = False


class ScrapingScheduleResponse(BaseModel):
    id: int
    schedule_id: int
    location_ids: List[int]
    categories: Optional[List[str]]
    keywords: Optional[List[str]]
    delay_between_requests: float
    concurrent_requests: int
    pages_per_location: int
    enable_email_extraction: bool
    enable_captcha_solving: bool
    min_lead_quality_score: float
    skip_duplicates: bool
    duplicate_check_hours: int
    adaptive_scheduling: bool
    peak_detection: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    task_type: str
    is_active: bool
    is_recommended: bool
    difficulty_level: str
    default_config: Dict[str, Any]
    required_fields: Optional[Dict[str, Any]]
    optional_fields: Optional[Dict[str, Any]]
    usage_count: int
    last_used_at: Optional[datetime]
    setup_instructions: Optional[str]
    configuration_help: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schedule endpoints
@router.get("/", response_model=List[ScheduleResponse])
async def get_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get schedules with optional filtering."""
    query = select(Schedule)
    
    if task_type:
        query = query.where(Schedule.task_type == task_type)
    if is_active is not None:
        query = query.where(Schedule.is_active == is_active)
    
    result = await db.execute(query.order_by(Schedule.priority).offset(skip).limit(limit))
    schedules = result.scalars().all()
    return schedules


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific schedule."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(schedule_data: ScheduleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new schedule."""
    try:
        schedule = scheduler_service.create_schedule(
            name=schedule_data.name,
            task_type=schedule_data.task_type,
            recurrence_type=schedule_data.recurrence_type,
            description=schedule_data.description,
            cron_expression=schedule_data.cron_expression,
            interval_minutes=schedule_data.interval_minutes,
            start_date=schedule_data.start_date,
            end_date=schedule_data.end_date,
            task_config=schedule_data.task_config,
            peak_hours_only=schedule_data.peak_hours_only,
            peak_start_hour=schedule_data.peak_start_hour,
            peak_end_hour=schedule_data.peak_end_hour,
            peak_timezone=schedule_data.peak_timezone
        )
        
        # Update additional settings
        schedule.timeout_minutes = schedule_data.timeout_minutes
        schedule.max_retries = schedule_data.max_retries
        schedule.retry_delay_minutes = schedule_data.retry_delay_minutes
        schedule.notify_on_success = schedule_data.notify_on_success
        schedule.notify_on_failure = schedule_data.notify_on_failure
        schedule.notification_config = schedule_data.notification_config
        
        await db.commit()
        await db.refresh(schedule)
        
        return schedule
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a schedule."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    update_data = schedule_data.dict(exclude_unset=True)
    
    # Validate CRON expression if provided
    if "cron_expression" in update_data and update_data["cron_expression"]:
        if not CronManager.is_valid_cron(update_data["cron_expression"]):
            raise HTTPException(status_code=400, detail="Invalid CRON expression")
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    schedule.updated_at = datetime.utcnow()
    
    # Recalculate next run time if timing settings changed
    timing_fields = ["cron_expression", "interval_minutes", "recurrence_type"]
    if any(field in update_data for field in timing_fields):
        scheduler_service._calculate_next_run_time(schedule)
    
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a schedule."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check if schedule is currently running
    if schedule_id in scheduler_service.running_schedules:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete running schedule. Stop it first."
        )
    
    await db.delete(schedule)
    await db.commit()
    return {"message": "Schedule deleted successfully"}


@router.post("/{schedule_id}/run")
async def run_schedule_now(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Run a schedule immediately."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if not schedule.is_active:
        raise HTTPException(status_code=400, detail="Schedule is not active")
    
    # Check if already running
    if schedule_id in scheduler_service.running_schedules:
        raise HTTPException(status_code=400, detail="Schedule is already running")
    
    try:
        await scheduler_service._execute_schedule(schedule)
        return {"message": "Schedule execution started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle schedule active status."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.is_active = not schedule.is_active
    schedule.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "message": f"Schedule {'activated' if schedule.is_active else 'deactivated'}",
        "is_active": schedule.is_active
    }


# Schedule Execution endpoints
@router.get("/{schedule_id}/executions", response_model=List[ScheduleExecutionResponse])
async def get_schedule_executions(
    schedule_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get executions for a specific schedule."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    query = select(ScheduleExecution).filter(ScheduleExecution.schedule_id == schedule_id)
    
    if status:
        query = query.where(ScheduleExecution.status == status)
    
    result = await db.execute(query.order_by(ScheduleExecution.started_at.desc()).offset(skip).limit(limit))
    executions = result.scalars().all()
    return executions


@router.get("/executions/", response_model=List[ScheduleExecutionResponse])
async def get_all_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get all schedule executions with filtering."""
    from datetime import timedelta
    
    query = select(ScheduleExecution).join(Schedule)
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(ScheduleExecution.started_at >= cutoff_date)
    
    if status:
        query = query.where(ScheduleExecution.status == status)
    if task_type:
        query = query.where(Schedule.task_type == task_type)
    
    result = await db.execute(query.order_by(ScheduleExecution.started_at.desc()).offset(skip).limit(limit))
    executions = result.scalars().all()
    return executions


@router.get("/executions/{execution_id}", response_model=ScheduleExecutionResponse)
async def get_execution(execution_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific schedule execution."""
    execution = select(ScheduleExecution).filter(ScheduleExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a running execution."""
    execution = select(ScheduleExecution).filter(ScheduleExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status != "running":
        raise HTTPException(status_code=400, detail="Execution is not running")
    
    # Cancel the running task
    schedule_id = execution.schedule_id
    if schedule_id in scheduler_service.running_schedules:
        task = scheduler_service.running_schedules[schedule_id]
        task.cancel()
        
        # Update execution status
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        execution.error_message = "Execution cancelled by user"
        await db.commit()
        
        return {"message": "Execution cancelled"}
    else:
        raise HTTPException(status_code=400, detail="Execution task not found")


# Scraping Schedule endpoints
@router.get("/{schedule_id}/scraping-config", response_model=ScrapingScheduleResponse)
async def get_scraping_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    """Get scraping configuration for a schedule."""
    scraping_config = select(ScrapingSchedule).filter(
        ScrapingSchedule.schedule_id == schedule_id
    ).first()
    
    if not scraping_config:
        raise HTTPException(status_code=404, detail="Scraping configuration not found")
    
    return scraping_config


@router.post("/{schedule_id}/scraping-config", response_model=ScrapingScheduleResponse)
async def create_scraping_schedule(
    schedule_id: int,
    scraping_data: ScrapingScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create scraping configuration for a schedule."""
    schedule = select(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.task_type != "scraping":
        raise HTTPException(status_code=400, detail="Schedule is not a scraping task")
    
    # Check if config already exists
    existing = select(ScrapingSchedule).filter(
        ScrapingSchedule.schedule_id == schedule_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Scraping configuration already exists")
    
    # Validate location IDs
    from app.models.locations import Location
    valid_locations = db.query(Location.id).filter(
        Location.id.in_(scraping_data.location_ids)
    ).all()
    
    valid_ids = [loc.id for loc in valid_locations]
    invalid_ids = set(scraping_data.location_ids) - set(valid_ids)
    
    if invalid_ids:
        raise HTTPException(status_code=400, detail=f"Invalid location IDs: {list(invalid_ids)}")
    
    scraping_config = ScrapingSchedule(
        schedule_id=schedule_id,
        **scraping_data.dict(exclude={"schedule_id"})
    )
    
    db.add(scraping_config)
    await db.commit()
    await db.refresh(scraping_config)
    return scraping_config


@router.put("/{schedule_id}/scraping-config", response_model=ScrapingScheduleResponse)
async def update_scraping_schedule(
    schedule_id: int,
    scraping_data: ScrapingScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update scraping configuration for a schedule."""
    scraping_config = select(ScrapingSchedule).filter(
        ScrapingSchedule.schedule_id == schedule_id
    ).first()
    
    if not scraping_config:
        raise HTTPException(status_code=404, detail="Scraping configuration not found")
    
    # Validate location IDs if provided
    if scraping_data.location_ids:
        from app.models.locations import Location
        valid_locations = db.query(Location.id).filter(
            Location.id.in_(scraping_data.location_ids)
        ).all()
        
        valid_ids = [loc.id for loc in valid_locations]
        invalid_ids = set(scraping_data.location_ids) - set(valid_ids)
        
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Invalid location IDs: {list(invalid_ids)}")
    
    update_data = scraping_data.dict(exclude={"schedule_id"})
    for field, value in update_data.items():
        setattr(scraping_config, field, value)
    
    scraping_config.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(scraping_config)
    return scraping_config


# Schedule Template endpoints
@router.get("/templates/", response_model=List[ScheduleTemplateResponse])
async def get_schedule_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_recommended: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get schedule templates."""
    query = select(ScheduleTemplate)
    
    if category:
        query = query.where(ScheduleTemplate.category == category)
    if task_type:
        query = query.where(ScheduleTemplate.task_type == task_type)
    if is_active is not None:
        query = query.where(ScheduleTemplate.is_active == is_active)
    if is_recommended is not None:
        query = query.where(ScheduleTemplate.is_recommended == is_recommended)
    
    result = await db.execute(query.offset(skip).limit(limit))
    templates = result.scalars().all()
    return templates


@router.post("/templates/{template_id}/use")
async def use_schedule_template(
    template_id: int,
    name: str,
    config_overrides: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Create a schedule from a template."""
    template = select(ScheduleTemplate).filter(ScheduleTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template is not active")
    
    try:
        # Merge template config with overrides
        task_config = template.default_config.copy()
        if config_overrides:
            task_config.update(config_overrides)
        
        # Create schedule from template
        schedule = scheduler_service.create_schedule(
            name=name,
            task_type=template.task_type,
            recurrence_type=task_config.get("recurrence_type", "daily"),
            description=f"Created from template: {template.name}",
            cron_expression=task_config.get("cron_expression"),
            interval_minutes=task_config.get("interval_minutes"),
            task_config=task_config
        )
        
        # Update template usage
        template.usage_count += 1
        template.last_used_at = datetime.utcnow()
        await db.commit()
        
        return {
            "message": "Schedule created from template",
            "schedule_id": schedule.id,
            "template_id": template_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Analytics endpoints
@router.get("/analytics/overview")
async def get_schedule_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get scheduler analytics."""
    try:
        analytics = scheduler_service.get_schedule_analytics(days)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_schedule_performance(
    schedule_id: Optional[int] = Query(None),
    task_type: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed schedule performance analytics."""
    from datetime import timedelta
    from sqlalchemy import func
    
    query = select(ScheduleExecution).join(Schedule)
    
    # Date filter
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.where(ScheduleExecution.started_at >= cutoff_date)
    
    if schedule_id:
        query = query.where(Schedule.id == schedule_id)
    if task_type:
        query = query.where(Schedule.task_type == task_type)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    # Calculate performance metrics
    total_executions = len(executions)
    successful_executions = len([e for e in executions if e.status == "completed"])
    failed_executions = len([e for e in executions if e.status == "failed"])
    
    # Average duration
    completed_executions = [e for e in executions if e.duration_seconds]
    avg_duration = sum(e.duration_seconds for e in completed_executions) / len(completed_executions) if completed_executions else 0
    
    # Records processed
    total_processed = sum(e.records_processed or 0 for e in executions)
    total_created = sum(e.records_created or 0 for e in executions)
    
    # Execution frequency by hour
    hour_counts = {}
    for execution in executions:
        hour = execution.started_at.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Task type breakdown
    task_type_counts = {}
    for execution in executions:
        task_type = execution.schedule.task_type
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
    
    return {
        "total_executions": total_executions,
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
        "average_duration_seconds": avg_duration,
        "total_records_processed": total_processed,
        "total_records_created": total_created,
        "executions_by_hour": hour_counts,
        "executions_by_task_type": task_type_counts,
        "period_days": days
    }


# Configuration endpoints
@router.get("/config/task-types")
async def get_task_types():
    """Get available task types."""
    return {
        "task_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in ScheduleType
        ]
    }


@router.get("/config/recurrence-types")
async def get_recurrence_types():
    """Get available recurrence types."""
    return {
        "recurrence_types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in RecurrenceType
        ]
    }


@router.post("/config/validate-cron")
async def validate_cron_expression(cron_expression: str):
    """Validate a CRON expression."""
    try:
        is_valid = CronManager.is_valid_cron(cron_expression)
        
        if is_valid:
            # Get next 5 run times
            next_runs = []
            current_time = datetime.utcnow()
            
            for i in range(5):
                next_run = CronManager.get_next_run(cron_expression, current_time)
                next_runs.append(next_run.isoformat())
                current_time = next_run
            
            return {
                "valid": True,
                "next_runs": next_runs
            }
        else:
            return {"valid": False, "error": "Invalid CRON expression"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# Status endpoints
@router.get("/status/running")
async def get_running_schedules():
    """Get currently running schedules."""
    running_schedules = []
    
    for schedule_id, task in scheduler_service.running_schedules.items():
        running_schedules.append({
            "schedule_id": schedule_id,
            "is_done": task.done(),
            "is_cancelled": task.cancelled()
        })
    
    return {
        "running_schedules": running_schedules,
        "count": len(running_schedules)
    }


@router.get("/status/scheduler")
async def get_scheduler_status():
    """Get scheduler service status."""
    return {
        "scheduler_running": scheduler_service.scheduler_running,
        "running_schedules_count": len(scheduler_service.running_schedules),
        "running_schedule_ids": list(scheduler_service.running_schedules.keys())
    }