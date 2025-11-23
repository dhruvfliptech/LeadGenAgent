"""
Scheduling models for automated scraping and tasks.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models import Base
from enum import Enum
from typing import Dict, Any, List


class ScheduleType(str, Enum):
    """Types of scheduled tasks."""
    SCRAPING = "scraping"
    AUTO_RESPONSE = "auto_response"
    CLEANUP = "cleanup"
    EXPORT = "export"
    NOTIFICATION = "notification"
    RULE_EXECUTION = "rule_execution"


class ScheduleStatus(str, Enum):
    """Schedule execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class RecurrenceType(str, Enum):
    """Recurrence patterns for schedules."""
    ONCE = "once"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"


class Schedule(Base):
    """Scheduled task configuration."""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Schedule metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False, index=True)  # ScheduleType
    
    # Schedule configuration
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)  # Lower = higher priority
    
    # Timing configuration
    recurrence_type = Column(String(50), nullable=False)  # RecurrenceType
    cron_expression = Column(String(100), nullable=True)  # For custom cron schedules
    interval_minutes = Column(Integer, nullable=True)  # For interval-based schedules
    
    # Schedule bounds
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Task configuration
    task_config = Column(JSON, nullable=True)  # Task-specific configuration
    timeout_minutes = Column(Integer, default=60, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay_minutes = Column(Integer, default=5, nullable=False)
    
    # Performance tracking
    total_runs = Column(Integer, default=0, nullable=False)
    successful_runs = Column(Integer, default=0, nullable=False)
    failed_runs = Column(Integer, default=0, nullable=False)
    average_duration_seconds = Column(Float, nullable=True)
    
    # Peak time optimization
    peak_hours_only = Column(Boolean, default=False, nullable=False)
    peak_start_hour = Column(Integer, default=9, nullable=False)  # 9 AM
    peak_end_hour = Column(Integer, default=17, nullable=False)  # 5 PM
    peak_timezone = Column(String(50), default="UTC", nullable=False)
    
    # Notifications
    notify_on_success = Column(Boolean, default=False, nullable=False)
    notify_on_failure = Column(Boolean, default=True, nullable=False)
    notification_config = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, name='{self.name}', type='{self.task_type}', active={self.is_active})>"


class ScheduleExecution(Base):
    """Record of schedule execution."""
    
    __tablename__ = "schedule_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Schedule reference
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False, index=True)
    
    # Execution metadata
    status = Column(String(50), nullable=False, index=True)  # ScheduleStatus
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    records_processed = Column(Integer, nullable=True)
    records_created = Column(Integer, nullable=True)
    records_updated = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Output
    result_data = Column(JSON, nullable=True)  # Task-specific results
    log_file_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    schedule = relationship("Schedule", backref="executions")
    
    def __repr__(self):
        return f"<ScheduleExecution(id={self.id}, schedule_id={self.schedule_id}, status='{self.status}')>"


class ScheduleTemplate(Base):
    """Pre-configured schedule templates."""
    
    __tablename__ = "schedule_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template metadata
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # scraping, maintenance, analytics
    task_type = Column(String(50), nullable=False)  # ScheduleType
    
    # Template configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_recommended = Column(Boolean, default=False, nullable=False)
    difficulty_level = Column(String(20), default="beginner", nullable=False)  # beginner, intermediate, advanced
    
    # Default settings
    default_config = Column(JSON, nullable=False)  # Default schedule configuration
    required_fields = Column(JSON, nullable=True)  # Fields that must be configured
    optional_fields = Column(JSON, nullable=True)  # Optional configuration fields
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Documentation
    setup_instructions = Column(Text, nullable=True)
    configuration_help = Column(JSON, nullable=True)  # Help text for configuration fields
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ScheduleTemplate(id={self.id}, name='{self.name}', type='{self.task_type}')>"


class ScrapingSchedule(Base):
    """Specialized schedule for scraping tasks."""
    
    __tablename__ = "scraping_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Schedule reference
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False, unique=True)
    
    # Scraping configuration
    location_ids = Column(JSON, nullable=False)  # List of location IDs to scrape
    categories = Column(JSON, nullable=True)  # Categories to scrape
    keywords = Column(JSON, nullable=True)  # Keywords to search for
    
    # Rate limiting
    delay_between_requests = Column(Float, default=2.0, nullable=False)
    concurrent_requests = Column(Integer, default=3, nullable=False)
    pages_per_location = Column(Integer, default=5, nullable=False)
    
    # Quality settings
    enable_email_extraction = Column(Boolean, default=False, nullable=False)
    enable_captcha_solving = Column(Boolean, default=False, nullable=False)
    min_lead_quality_score = Column(Float, default=0.0, nullable=False)
    
    # Duplicate handling
    skip_duplicates = Column(Boolean, default=True, nullable=False)
    duplicate_check_hours = Column(Integer, default=24, nullable=False)
    
    # Performance optimization
    adaptive_scheduling = Column(Boolean, default=False, nullable=False)  # Adjust based on lead volume
    peak_detection = Column(Boolean, default=False, nullable=False)  # Detect optimal scraping times
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    schedule = relationship("Schedule", backref="scraping_config", uselist=False)
    
    def __repr__(self):
        return f"<ScrapingSchedule(id={self.id}, schedule_id={self.schedule_id})>"


class ScheduleNotification(Base):
    """Notifications for schedule events."""
    
    __tablename__ = "schedule_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Schedule reference
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False, index=True)
    execution_id = Column(Integer, ForeignKey("schedule_executions.id"), nullable=True, index=True)
    
    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)  # success, failure, warning
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Delivery
    channels = Column(JSON, nullable=False)  # email, webhook, slack, etc.
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String(50), default="pending", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    schedule = relationship("Schedule", backref="notifications")
    execution = relationship("ScheduleExecution", backref="notifications")
    
    def __repr__(self):
        return f"<ScheduleNotification(id={self.id}, type='{self.notification_type}', status='{self.delivery_status}')>"