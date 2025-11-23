"""
Advanced scheduling service for automated tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from croniter import croniter
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models.schedules import (
    Schedule, ScheduleExecution, ScheduleTemplate, ScrapingSchedule,
    ScheduleNotification, ScheduleType, ScheduleStatus, RecurrenceType
)
from app.models.leads import Lead
from app.models.locations import Location
from app.core.config import settings


logger = logging.getLogger(__name__)


class CronManager:
    """Manages CRON expression parsing and next run calculations."""
    
    @staticmethod
    def is_valid_cron(cron_expression: str) -> bool:
        """Validate CRON expression."""
        try:
            croniter(cron_expression)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_next_run(cron_expression: str, base_time: datetime = None) -> datetime:
        """Get next run time from CRON expression."""
        try:
            if base_time is None:
                base_time = datetime.utcnow()
            
            cron = croniter(cron_expression, base_time)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Failed to calculate next run: {e}")
            raise
    
    @staticmethod
    def get_standard_cron(recurrence_type: str, interval: int = 1) -> str:
        """Get standard CRON expression for recurrence type."""
        cron_expressions = {
            RecurrenceType.MINUTELY: f"*/{interval} * * * *",
            RecurrenceType.HOURLY: f"0 */{interval} * * *",
            RecurrenceType.DAILY: f"0 0 */{interval} * *",
            RecurrenceType.WEEKLY: f"0 0 * * 0/{interval}",
            RecurrenceType.MONTHLY: f"0 0 1 */{interval} *"
        }
        
        return cron_expressions.get(recurrence_type, "0 * * * *")  # Default to hourly


class PeakTimeManager:
    """Manages peak time optimization for schedules."""
    
    @staticmethod
    def is_peak_time(
        schedule: Schedule,
        check_time: datetime = None
    ) -> bool:
        """Check if current time is within peak hours."""
        try:
            if not schedule.peak_hours_only:
                return True
            
            if check_time is None:
                check_time = datetime.utcnow()
            
            # Convert to schedule timezone
            tz = pytz.timezone(schedule.peak_timezone)
            local_time = check_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            current_hour = local_time.hour
            
            # Check if within peak hours
            if schedule.peak_start_hour <= schedule.peak_end_hour:
                # Same day peak hours (e.g., 9 AM to 5 PM)
                return schedule.peak_start_hour <= current_hour < schedule.peak_end_hour
            else:
                # Cross-day peak hours (e.g., 10 PM to 6 AM)
                return current_hour >= schedule.peak_start_hour or current_hour < schedule.peak_end_hour
            
        except Exception as e:
            logger.error(f"Failed to check peak time: {e}")
            return True  # Default to allowing execution
    
    @staticmethod
    def get_next_peak_time(schedule: Schedule, base_time: datetime = None) -> datetime:
        """Get next peak time start."""
        try:
            if not schedule.peak_hours_only:
                return base_time or datetime.utcnow()
            
            if base_time is None:
                base_time = datetime.utcnow()
            
            # Convert to schedule timezone
            tz = pytz.timezone(schedule.peak_timezone)
            local_time = base_time.replace(tzinfo=pytz.UTC).astimezone(tz)
            
            # Calculate next peak start
            peak_start = local_time.replace(
                hour=schedule.peak_start_hour,
                minute=0,
                second=0,
                microsecond=0
            )
            
            # If already past today's peak start, go to tomorrow
            if peak_start <= local_time:
                peak_start += timedelta(days=1)
            
            # Convert back to UTC
            return peak_start.astimezone(pytz.UTC).replace(tzinfo=None)
            
        except Exception as e:
            logger.error(f"Failed to calculate next peak time: {e}")
            return base_time or datetime.utcnow()


class TaskExecutor:
    """Executes different types of scheduled tasks."""
    
    def __init__(self, db: Session):
        self.db = db
        self.task_handlers = {
            ScheduleType.SCRAPING: self._execute_scraping_task,
            ScheduleType.AUTO_RESPONSE: self._execute_auto_response_task,
            ScheduleType.CLEANUP: self._execute_cleanup_task,
            ScheduleType.EXPORT: self._execute_export_task,
            ScheduleType.NOTIFICATION: self._execute_notification_task,
            ScheduleType.RULE_EXECUTION: self._execute_rule_execution_task
        }
    
    async def execute_schedule(self, schedule: Schedule) -> ScheduleExecution:
        """Execute a scheduled task."""
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            status=ScheduleStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        try:
            handler = self.task_handlers.get(schedule.task_type)
            if not handler:
                raise ValueError(f"No handler for task type: {schedule.task_type}")
            
            logger.info(f"Executing schedule {schedule.id}: {schedule.name}")
            
            result = await handler(schedule, execution)
            
            execution.status = ScheduleStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            execution.result_data = result
            
            # Update schedule statistics
            schedule.total_runs += 1
            schedule.successful_runs += 1
            schedule.last_run_at = execution.started_at
            
            # Update average duration
            if schedule.average_duration_seconds:
                schedule.average_duration_seconds = (
                    schedule.average_duration_seconds * (schedule.total_runs - 1) +
                    execution.duration_seconds
                ) / schedule.total_runs
            else:
                schedule.average_duration_seconds = execution.duration_seconds
            
            logger.info(f"Schedule {schedule.id} completed successfully in {execution.duration_seconds:.2f}s")
            
        except asyncio.TimeoutError:
            execution.status = ScheduleStatus.FAILED
            execution.error_message = "Task timed out"
            execution.completed_at = datetime.utcnow()
            
            schedule.total_runs += 1
            schedule.failed_runs += 1
            
            logger.error(f"Schedule {schedule.id} timed out")
            
        except Exception as e:
            execution.status = ScheduleStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            schedule.total_runs += 1
            schedule.failed_runs += 1
            
            logger.error(f"Schedule {schedule.id} failed: {e}")
        
        finally:
            self.db.commit()
            
            # Send notifications if configured
            await self._send_execution_notification(schedule, execution)
        
        return execution
    
    async def _execute_scraping_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute scraping task."""
        try:
            # Get scraping configuration
            scraping_config = self.db.query(ScrapingSchedule).filter(
                ScrapingSchedule.schedule_id == schedule.id
            ).first()
            
            if not scraping_config:
                raise ValueError("No scraping configuration found")
            
            # Get locations to scrape
            locations = self.db.query(Location).filter(
                Location.id.in_(scraping_config.location_ids)
            ).all()
            
            if not locations:
                raise ValueError("No valid locations found")
            
            # Import scraper service
            from app.scrapers.craigslist_scraper import CraigslistScraper
            
            scraper = CraigslistScraper()
            total_leads = 0
            new_leads = 0
            failed_locations = 0
            
            for location in locations:
                try:
                    logger.info(f"Scraping location: {location.name}")
                    
                    # Configure scraper for this location
                    scrape_config = {
                        "location": location,
                        "categories": scraping_config.categories,
                        "keywords": scraping_config.keywords,
                        "pages_per_category": scraping_config.pages_per_location,
                        "delay_between_requests": scraping_config.delay_between_requests,
                        "concurrent_requests": scraping_config.concurrent_requests,
                        "skip_duplicates": scraping_config.skip_duplicates,
                        "duplicate_check_hours": scraping_config.duplicate_check_hours
                    }
                    
                    # Execute scraping
                    results = await scraper.scrape_location_async(scrape_config)
                    
                    total_leads += results.get("total_processed", 0)
                    new_leads += results.get("new_leads", 0)
                    
                    # Apply rate limiting between locations
                    await asyncio.sleep(scraping_config.delay_between_requests)
                    
                except Exception as e:
                    logger.error(f"Failed to scrape location {location.name}: {e}")
                    failed_locations += 1
                    continue
            
            # Update execution record
            execution.records_processed = total_leads
            execution.records_created = new_leads
            execution.records_failed = failed_locations
            
            return {
                "total_leads": total_leads,
                "new_leads": new_leads,
                "locations_scraped": len(locations) - failed_locations,
                "failed_locations": failed_locations
            }
            
        except Exception as e:
            logger.error(f"Scraping task failed: {e}")
            raise
    
    async def _execute_auto_response_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute auto-response processing task."""
        try:
            from app.services.auto_responder import auto_responder_service
            
            # Process pending auto-responses
            await auto_responder_service.process_pending_responses()
            
            # Get statistics
            analytics = auto_responder_service.get_response_analytics(days=1)
            
            execution.records_processed = analytics.get("total_responses", 0)
            execution.records_created = analytics.get("sent_responses", 0)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Auto-response task failed: {e}")
            raise
    
    async def _execute_cleanup_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute cleanup task."""
        try:
            config = schedule.task_config or {}
            cleanup_days = config.get("cleanup_days", 30)
            
            cutoff_date = datetime.utcnow() - timedelta(days=cleanup_days)
            
            # Clean up old executions
            old_executions = self.db.query(ScheduleExecution).filter(
                and_(
                    ScheduleExecution.started_at < cutoff_date,
                    ScheduleExecution.status.in_([
                        ScheduleStatus.COMPLETED, 
                        ScheduleStatus.FAILED
                    ])
                )
            )
            
            deleted_executions = old_executions.count()
            old_executions.delete(synchronize_session=False)
            
            # Clean up old logs (if implemented)
            # Clean up temporary files
            
            execution.records_processed = deleted_executions
            
            self.db.commit()
            
            return {
                "deleted_executions": deleted_executions,
                "cleanup_days": cleanup_days
            }
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
            raise
    
    async def _execute_export_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute export task."""
        try:
            from app.services.export_service import export_service
            
            config = schedule.task_config or {}
            export_type = config.get("export_type", "csv")
            filters = config.get("filters", {})
            
            # Execute export
            export_result = await export_service.create_export(
                export_type=export_type,
                filters=filters,
                scheduled=True
            )
            
            execution.records_processed = export_result.get("record_count", 0)
            
            return export_result
            
        except Exception as e:
            logger.error(f"Export task failed: {e}")
            raise
    
    async def _execute_notification_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute notification processing task."""
        try:
            from app.services.notification_service import notification_service
            
            # Process pending notifications
            await notification_service.process_pending_notifications()
            
            # Get analytics
            analytics = notification_service.get_notification_analytics(days=1)
            
            execution.records_processed = analytics.get("total_notifications", 0)
            execution.records_created = analytics.get("sent_notifications", 0)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Notification task failed: {e}")
            raise
    
    async def _execute_rule_execution_task(self, schedule: Schedule, execution: ScheduleExecution) -> Dict:
        """Execute rule processing task."""
        try:
            from app.services.rule_engine import rule_engine
            
            config = schedule.task_config or {}
            batch_size = config.get("batch_size", 100)
            
            # Get unprocessed leads
            unprocessed_leads = self.db.query(Lead).filter(
                Lead.is_processed == False
            ).limit(batch_size).all()
            
            processed_count = 0
            matched_count = 0
            
            for lead in unprocessed_leads:
                try:
                    result = await rule_engine.process_lead(lead)
                    processed_count += 1
                    
                    if result.get("rules_matched"):
                        matched_count += 1
                    
                    # Mark lead as processed
                    lead.is_processed = True
                    
                except Exception as e:
                    logger.error(f"Failed to process lead {lead.id}: {e}")
                    continue
            
            execution.records_processed = processed_count
            execution.records_created = matched_count
            
            self.db.commit()
            
            return {
                "processed_leads": processed_count,
                "matched_leads": matched_count,
                "batch_size": batch_size
            }
            
        except Exception as e:
            logger.error(f"Rule execution task failed: {e}")
            raise
    
    async def _send_execution_notification(self, schedule: Schedule, execution: ScheduleExecution):
        """Send notification about schedule execution."""
        try:
            should_notify = False
            notification_type = ""
            
            if execution.status == ScheduleStatus.COMPLETED and schedule.notify_on_success:
                should_notify = True
                notification_type = "schedule_success"
            elif execution.status == ScheduleStatus.FAILED and schedule.notify_on_failure:
                should_notify = True
                notification_type = "schedule_failure"
            
            if not should_notify:
                return
            
            from app.services.notification_service import notification_service
            
            title = f"Schedule '{schedule.name}' {execution.status}"
            
            if execution.status == ScheduleStatus.COMPLETED:
                message = (
                    f"Successfully executed in {execution.duration_seconds:.2f}s. "
                    f"Processed {execution.records_processed or 0} records."
                )
            else:
                message = f"Failed: {execution.error_message or 'Unknown error'}"
            
            notification_config = schedule.notification_config or {}
            channels = notification_config.get("channels", ["email"])
            priority = "high" if execution.status == ScheduleStatus.FAILED else "normal"
            
            await notification_service.create_notification(
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                data={
                    "schedule_id": schedule.id,
                    "execution_id": execution.id,
                    "duration_seconds": execution.duration_seconds,
                    "records_processed": execution.records_processed
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to send execution notification: {e}")


class SchedulerService:
    """Main scheduler service."""
    
    def __init__(self):
        self.db = None  # Will be set per request
        self.task_executor = TaskExecutor(self.db)
        self.running_schedules: Dict[int, asyncio.Task] = {}
        self.scheduler_running = False
    
    async def start_scheduler(self):
        """Start the main scheduler loop."""
        self.scheduler_running = True
        logger.info("Starting scheduler service")
        
        while self.scheduler_running:
            try:
                await self._process_due_schedules()
                await self._cleanup_completed_tasks()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def stop_scheduler(self):
        """Stop the scheduler and cancel running tasks."""
        logger.info("Stopping scheduler service")
        self.scheduler_running = False
        
        # Cancel all running tasks
        for task in self.running_schedules.values():
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.running_schedules:
            await asyncio.gather(*self.running_schedules.values(), return_exceptions=True)
        
        self.running_schedules.clear()
        logger.info("Scheduler stopped")
    
    async def _process_due_schedules(self):
        """Process schedules that are due to run."""
        try:
            current_time = datetime.utcnow()
            
            # Get due schedules
            due_schedules = self.db.query(Schedule).filter(
                and_(
                    Schedule.is_active == True,
                    or_(
                        Schedule.next_run_at.is_(None),
                        Schedule.next_run_at <= current_time
                    )
                )
            ).all()
            
            for schedule in due_schedules:
                try:
                    # Skip if already running
                    if schedule.id in self.running_schedules:
                        continue
                    
                    # Check peak time constraints
                    if not PeakTimeManager.is_peak_time(schedule, current_time):
                        logger.debug(f"Skipping schedule {schedule.id} - outside peak hours")
                        # Update next run to next peak time
                        schedule.next_run_at = PeakTimeManager.get_next_peak_time(schedule, current_time)
                        self.db.commit()
                        continue
                    
                    # Execute schedule
                    await self._execute_schedule(schedule)
                    
                except Exception as e:
                    logger.error(f"Failed to process schedule {schedule.id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to process due schedules: {e}")
    
    async def _execute_schedule(self, schedule: Schedule):
        """Execute a single schedule."""
        try:
            logger.info(f"Starting execution of schedule {schedule.id}: {schedule.name}")
            
            # Create execution task with timeout
            timeout = schedule.timeout_minutes * 60
            task = asyncio.create_task(
                asyncio.wait_for(
                    self.task_executor.execute_schedule(schedule),
                    timeout=timeout
                )
            )
            
            # Store running task
            self.running_schedules[schedule.id] = task
            
            # Calculate next run time
            self._calculate_next_run_time(schedule)
            
            # The task will complete in the background
            
        except Exception as e:
            logger.error(f"Failed to execute schedule {schedule.id}: {e}")
    
    def _calculate_next_run_time(self, schedule: Schedule):
        """Calculate and update the next run time for a schedule."""
        try:
            current_time = datetime.utcnow()
            
            if schedule.recurrence_type == RecurrenceType.ONCE:
                # One-time schedule, disable after running
                schedule.is_active = False
                schedule.next_run_at = None
                
            elif schedule.recurrence_type == RecurrenceType.CUSTOM_CRON:
                if schedule.cron_expression:
                    schedule.next_run_at = CronManager.get_next_run(
                        schedule.cron_expression, current_time
                    )
                else:
                    logger.error(f"No CRON expression for schedule {schedule.id}")
                    
            else:
                # Interval-based schedule
                if schedule.interval_minutes:
                    schedule.next_run_at = current_time + timedelta(minutes=schedule.interval_minutes)
                else:
                    # Use standard CRON for the recurrence type
                    cron_expr = CronManager.get_standard_cron(schedule.recurrence_type)
                    schedule.next_run_at = CronManager.get_next_run(cron_expr, current_time)
            
            # Apply peak time constraints
            if schedule.peak_hours_only and schedule.next_run_at:
                if not PeakTimeManager.is_peak_time(schedule, schedule.next_run_at):
                    schedule.next_run_at = PeakTimeManager.get_next_peak_time(
                        schedule, schedule.next_run_at
                    )
            
            # Check end date constraint
            if schedule.end_date and schedule.next_run_at and schedule.next_run_at > schedule.end_date:
                schedule.is_active = False
                schedule.next_run_at = None
            
            self.db.commit()
            
            if schedule.next_run_at:
                logger.info(f"Schedule {schedule.id} next run: {schedule.next_run_at}")
            else:
                logger.info(f"Schedule {schedule.id} completed or deactivated")
                
        except Exception as e:
            logger.error(f"Failed to calculate next run time for schedule {schedule.id}: {e}")
    
    async def _cleanup_completed_tasks(self):
        """Clean up completed schedule tasks."""
        try:
            completed_schedules = []
            
            for schedule_id, task in self.running_schedules.items():
                if task.done():
                    completed_schedules.append(schedule_id)
                    
                    try:
                        # Get the result (this will raise any exceptions)
                        result = await task
                        logger.debug(f"Schedule {schedule_id} task completed successfully")
                    except Exception as e:
                        logger.error(f"Schedule {schedule_id} task failed: {e}")
            
            # Remove completed tasks
            for schedule_id in completed_schedules:
                del self.running_schedules[schedule_id]
                
        except Exception as e:
            logger.error(f"Failed to cleanup completed tasks: {e}")
    
    def create_schedule(
        self,
        name: str,
        task_type: str,
        recurrence_type: str,
        description: Optional[str] = None,
        cron_expression: Optional[str] = None,
        interval_minutes: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        task_config: Optional[Dict] = None,
        peak_hours_only: bool = False,
        peak_start_hour: int = 9,
        peak_end_hour: int = 17,
        peak_timezone: str = "UTC"
    ) -> Schedule:
        """Create a new schedule."""
        try:
            # Validate CRON expression if provided
            if cron_expression and not CronManager.is_valid_cron(cron_expression):
                raise ValueError(f"Invalid CRON expression: {cron_expression}")
            
            schedule = Schedule(
                name=name,
                description=description,
                task_type=task_type,
                recurrence_type=recurrence_type,
                cron_expression=cron_expression,
                interval_minutes=interval_minutes,
                start_date=start_date,
                end_date=end_date,
                task_config=task_config or {},
                peak_hours_only=peak_hours_only,
                peak_start_hour=peak_start_hour,
                peak_end_hour=peak_end_hour,
                peak_timezone=peak_timezone
            )
            
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
            
            # Calculate first run time
            self._calculate_next_run_time(schedule)
            
            logger.info(f"Created schedule {schedule.id}: {name}")
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {e}")
            self.db.rollback()
            raise
    
    def get_schedule_analytics(self, days: int = 30) -> Dict:
        """Get scheduler performance analytics."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Overall statistics
            total_schedules = self.db.query(Schedule).count()
            active_schedules = self.db.query(Schedule).filter(Schedule.is_active == True).count()
            
            total_executions = self.db.query(ScheduleExecution).filter(
                ScheduleExecution.started_at >= cutoff_date
            ).count()
            
            successful_executions = self.db.query(ScheduleExecution).filter(
                and_(
                    ScheduleExecution.started_at >= cutoff_date,
                    ScheduleExecution.status == ScheduleStatus.COMPLETED
                )
            ).count()
            
            # Schedule performance
            schedule_stats = self.db.query(Schedule).filter(Schedule.total_runs > 0).all()
            
            schedule_performance = []
            for schedule in schedule_stats:
                schedule_performance.append({
                    "schedule_id": schedule.id,
                    "name": schedule.name,
                    "task_type": schedule.task_type,
                    "total_runs": schedule.total_runs,
                    "success_rate": schedule.success_rate,
                    "avg_duration": schedule.average_duration_seconds,
                    "next_run": schedule.next_run_at.isoformat() if schedule.next_run_at else None
                })
            
            return {
                "total_schedules": total_schedules,
                "active_schedules": active_schedules,
                "running_schedules": len(self.running_schedules),
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "overall_success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                "schedule_performance": schedule_performance[:10],  # Top 10
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Failed to get schedule analytics: {e}")
            return {}


# Global service instance
scheduler_service = SchedulerService()