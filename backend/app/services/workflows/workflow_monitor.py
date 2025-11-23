"""
Workflow Monitor Service

Logs workflow events, errors, and performance metrics for monitoring
and debugging.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.n8n_workflows import (
    WorkflowMonitoring,
    MonitoringSeverity,
    N8NWorkflow,
    WorkflowExecution
)

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """
    Workflow Monitor

    Centralized logging and monitoring for workflow events.
    """

    def __init__(self, db: Session):
        """Initialize workflow monitor"""
        self.db = db

    async def log_event(
        self,
        workflow_id: Optional[int] = None,
        execution_id: Optional[int] = None,
        event_type: str = "info",
        event_name: Optional[str] = None,
        event_description: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        step_name: Optional[str] = None,
        step_number: Optional[int] = None,
        duration_ms: Optional[int] = None,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None
    ) -> WorkflowMonitoring:
        """
        Log a workflow event

        Args:
            workflow_id: Workflow ID
            execution_id: Execution ID
            event_type: Event type
            event_name: Event name
            event_description: Event description
            event_data: Additional event data
            severity: Event severity (info, warning, error, critical)
            step_name: Workflow step name
            step_number: Workflow step number
            duration_ms: Duration in milliseconds
            memory_mb: Memory usage in MB
            cpu_percent: CPU usage percentage

        Returns:
            WorkflowMonitoring instance
        """
        try:
            # Parse severity
            try:
                severity_enum = MonitoringSeverity(severity.lower())
            except ValueError:
                severity_enum = MonitoringSeverity.INFO

            event = WorkflowMonitoring(
                workflow_id=workflow_id,
                execution_id=execution_id,
                event_type=event_type,
                event_name=event_name,
                event_description=event_description,
                event_data=event_data or {},
                severity=severity_enum,
                step_name=step_name,
                step_number=step_number,
                duration_ms=duration_ms,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                timestamp=datetime.utcnow()
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)

            # Log to application logger based on severity
            log_message = f"Workflow Event: {event_type}"
            if event_name:
                log_message += f" - {event_name}"

            if severity_enum == MonitoringSeverity.ERROR:
                logger.error(log_message)
            elif severity_enum == MonitoringSeverity.WARNING:
                logger.warning(log_message)
            elif severity_enum == MonitoringSeverity.CRITICAL:
                logger.critical(log_message)
            else:
                logger.info(log_message)

            return event

        except Exception as e:
            logger.error(f"Failed to log event: {str(e)}")
            self.db.rollback()
            raise

    def get_events(
        self,
        workflow_id: Optional[int] = None,
        execution_id: Optional[int] = None,
        event_type: Optional[str] = None,
        severity: Optional[MonitoringSeverity] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowMonitoring]:
        """
        Get workflow events with filters

        Args:
            workflow_id: Filter by workflow ID
            execution_id: Filter by execution ID
            event_type: Filter by event type
            severity: Filter by severity
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of events
            offset: Offset for pagination

        Returns:
            List of WorkflowMonitoring events
        """
        try:
            query = self.db.query(WorkflowMonitoring)

            # Apply filters
            if workflow_id:
                query = query.filter(WorkflowMonitoring.workflow_id == workflow_id)

            if execution_id:
                query = query.filter(WorkflowMonitoring.execution_id == execution_id)

            if event_type:
                query = query.filter(WorkflowMonitoring.event_type == event_type)

            if severity:
                query = query.filter(WorkflowMonitoring.severity == severity)

            if start_date:
                query = query.filter(WorkflowMonitoring.timestamp >= start_date)

            if end_date:
                query = query.filter(WorkflowMonitoring.timestamp <= end_date)

            # Order by timestamp descending
            query = query.order_by(WorkflowMonitoring.timestamp.desc())

            # Pagination
            query = query.limit(limit).offset(offset)

            events = query.all()
            return events

        except Exception as e:
            logger.error(f"Failed to get events: {str(e)}")
            return []

    def get_error_logs(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[WorkflowMonitoring]:
        """
        Get recent error logs

        Args:
            hours: Number of hours to look back
            limit: Maximum number of errors

        Returns:
            List of error events
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)

            errors = self.db.query(WorkflowMonitoring).filter(
                and_(
                    or_(
                        WorkflowMonitoring.severity == MonitoringSeverity.ERROR,
                        WorkflowMonitoring.severity == MonitoringSeverity.CRITICAL
                    ),
                    WorkflowMonitoring.timestamp >= since
                )
            ).order_by(
                WorkflowMonitoring.timestamp.desc()
            ).limit(limit).all()

            return errors

        except Exception as e:
            logger.error(f"Failed to get error logs: {str(e)}")
            return []

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get monitoring dashboard data

        Returns:
            Dashboard metrics
        """
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            # Count events by severity in last hour
            events_last_hour = self.db.query(WorkflowMonitoring).filter(
                WorkflowMonitoring.timestamp >= hour_ago
            ).count()

            errors_last_hour = self.db.query(WorkflowMonitoring).filter(
                and_(
                    WorkflowMonitoring.timestamp >= hour_ago,
                    or_(
                        WorkflowMonitoring.severity == MonitoringSeverity.ERROR,
                        WorkflowMonitoring.severity == MonitoringSeverity.CRITICAL
                    )
                )
            ).count()

            warnings_last_hour = self.db.query(WorkflowMonitoring).filter(
                and_(
                    WorkflowMonitoring.timestamp >= hour_ago,
                    WorkflowMonitoring.severity == MonitoringSeverity.WARNING
                )
            ).count()

            # Get recent events
            recent_events = self.get_events(limit=10)

            # Get recent errors
            recent_errors = self.get_error_logs(hours=24, limit=10)

            return {
                "events_last_hour": events_last_hour,
                "errors_last_hour": errors_last_hour,
                "warnings_last_hour": warnings_last_hour,
                "recent_events": [e.to_dict() for e in recent_events],
                "recent_errors": [e.to_dict() for e in recent_errors],
                "timestamp": now.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {str(e)}")
            return {}

    def cleanup_old_events(self, days: int = 30) -> int:
        """
        Clean up old monitoring events

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted events
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            deleted = self.db.query(WorkflowMonitoring).filter(
                WorkflowMonitoring.timestamp < cutoff
            ).delete()

            self.db.commit()

            logger.info(f"Cleaned up {deleted} old monitoring events")
            return deleted

        except Exception as e:
            logger.error(f"Failed to cleanup events: {str(e)}")
            self.db.rollback()
            return 0

    async def log_execution_metrics(
        self,
        execution_id: int,
        step_name: str,
        duration_ms: int,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None
    ) -> None:
        """Log execution performance metrics"""
        await self.log_event(
            execution_id=execution_id,
            event_type="performance_metric",
            event_name=f"Step: {step_name}",
            step_name=step_name,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent
        )

    async def log_error(
        self,
        workflow_id: Optional[int],
        execution_id: Optional[int],
        error_message: str,
        error_data: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ) -> None:
        """Log an error"""
        await self.log_event(
            workflow_id=workflow_id,
            execution_id=execution_id,
            event_type="error",
            event_name="Error Occurred",
            event_description=error_message,
            event_data=error_data or {},
            severity=severity
        )
