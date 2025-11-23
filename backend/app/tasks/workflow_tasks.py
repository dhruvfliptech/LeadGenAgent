"""
Workflow Background Tasks

Celery tasks for asynchronous workflow processing including:
- Webhook queue processing
- Execution retry handling
- Approval expiration
- Monitoring cleanup
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import SessionLocal
from app.services.workflows import (
    WebhookHandler,
    WorkflowExecutor,
    ApprovalSystem,
    WorkflowMonitor
)
from app.models.n8n_workflows import QueueStatus

try:
    from backend.celery_app import celery_app
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Celery not available, tasks will not be registered")

logger = logging.getLogger(__name__)


if CELERY_AVAILABLE:

    @celery_app.task(name="process_webhook_queue", bind=True, max_retries=3)
    def process_webhook_queue(self, batch_size: int = 10):
        """
        Process pending webhooks from the queue

        This task runs periodically to process queued webhooks.
        """
        db = SessionLocal()
        try:
            handler = WebhookHandler(db)
            executor = WorkflowExecutor(db)
            monitor = WorkflowMonitor(db)

            # Get pending webhooks
            webhooks = handler.get_pending_webhooks(limit=batch_size)

            processed_count = 0
            failed_count = 0

            for webhook in webhooks:
                try:
                    # Mark as processing
                    handler.mark_processing(webhook.id)

                    # Process webhook
                    start_time = datetime.utcnow()

                    # If webhook has associated workflow, trigger it
                    if webhook.workflow_id:
                        await executor.execute_workflow(
                            workflow_id=webhook.workflow_id,
                            trigger_event="webhook",
                            trigger_source="webhook",
                            input_data=webhook.webhook_payload
                        )

                    # Calculate duration
                    duration = (datetime.utcnow() - start_time).total_seconds()

                    # Mark as completed
                    handler.mark_completed(webhook.id, processing_duration=duration)
                    processed_count += 1

                    logger.info(f"Processed webhook {webhook.id} in {duration:.2f}s")

                except Exception as e:
                    logger.error(f"Failed to process webhook {webhook.id}: {str(e)}")
                    handler.mark_failed(
                        webhook.id,
                        error_message=str(e),
                        error_trace=str(e.__traceback__)
                    )
                    failed_count += 1

            logger.info(f"Webhook processing complete: {processed_count} processed, {failed_count} failed")

            return {
                "processed": processed_count,
                "failed": failed_count,
                "total": len(webhooks)
            }

        except Exception as e:
            logger.error(f"Webhook queue processing error: {str(e)}")
            raise self.retry(exc=e, countdown=60)

        finally:
            db.close()


    @celery_app.task(name="retry_failed_webhooks", bind=True)
    def retry_failed_webhooks(self, batch_size: int = 10):
        """
        Retry failed webhooks that are ready for retry

        This task runs periodically to retry failed webhooks based on
        exponential backoff schedule.
        """
        db = SessionLocal()
        try:
            handler = WebhookHandler(db)

            # Get webhooks ready for retry
            webhooks = handler.get_retryable_webhooks(limit=batch_size)

            retried_count = 0

            for webhook in webhooks:
                try:
                    logger.info(f"Retrying webhook {webhook.id} (attempt {webhook.retry_count + 1})")

                    # Reset to queued status for processing
                    webhook.status = QueueStatus.QUEUED
                    db.commit()

                    retried_count += 1

                except Exception as e:
                    logger.error(f"Failed to retry webhook {webhook.id}: {str(e)}")

            logger.info(f"Queued {retried_count} webhooks for retry")

            return {"retried": retried_count}

        except Exception as e:
            logger.error(f"Retry failed webhooks error: {str(e)}")
            raise

        finally:
            db.close()


    @celery_app.task(name="expire_old_approvals", bind=True)
    def expire_old_approvals(self):
        """
        Expire approval requests that have passed their expiration time

        Runs periodically to clean up old pending approvals.
        """
        db = SessionLocal()
        try:
            approval_system = ApprovalSystem(db)
            expired_count = await approval_system.expire_old_approvals()

            logger.info(f"Expired {expired_count} approval requests")

            return {"expired": expired_count}

        except Exception as e:
            logger.error(f"Expire approvals error: {str(e)}")
            raise

        finally:
            db.close()


    @celery_app.task(name="cleanup_old_monitoring_events", bind=True)
    def cleanup_old_monitoring_events(self, days: int = 30):
        """
        Clean up old monitoring events

        Removes monitoring events older than specified days to keep
        database size manageable.
        """
        db = SessionLocal()
        try:
            monitor = WorkflowMonitor(db)
            deleted_count = monitor.cleanup_old_events(days=days)

            logger.info(f"Cleaned up {deleted_count} old monitoring events")

            return {"deleted": deleted_count}

        except Exception as e:
            logger.error(f"Cleanup monitoring events error: {str(e)}")
            raise

        finally:
            db.close()


    @celery_app.task(name="sync_n8n_workflows", bind=True)
    def sync_n8n_workflows(self):
        """
        Sync workflow list from N8N

        Fetches active workflows from N8N and updates local database.
        """
        db = SessionLocal()
        try:
            from app.services.workflows import get_n8n_client
            from app.models.n8n_workflows import N8NWorkflow

            n8n_client = get_n8n_client()

            # Get workflows from N8N
            n8n_workflows = await n8n_client.list_workflows(active_only=True)

            synced_count = 0

            for n8n_wf in n8n_workflows:
                # Check if workflow exists
                workflow = db.query(N8NWorkflow).filter(
                    N8NWorkflow.n8n_workflow_id == n8n_wf.get("id")
                ).first()

                if workflow:
                    # Update existing
                    workflow.workflow_name = n8n_wf.get("name", workflow.workflow_name)
                    workflow.is_active = n8n_wf.get("active", True)
                else:
                    # Create new
                    workflow = N8NWorkflow(
                        workflow_name=n8n_wf.get("name", "Untitled"),
                        n8n_workflow_id=n8n_wf.get("id"),
                        workflow_description=n8n_wf.get("description"),
                        is_active=n8n_wf.get("active", True)
                    )
                    db.add(workflow)

                synced_count += 1

            db.commit()

            logger.info(f"Synced {synced_count} workflows from N8N")

            return {"synced": synced_count}

        except Exception as e:
            logger.error(f"Sync N8N workflows error: {str(e)}")
            db.rollback()
            raise

        finally:
            db.close()


    @celery_app.task(name="check_execution_status", bind=True)
    def check_execution_status(self, execution_id: int):
        """
        Check status of running execution in N8N

        Polls N8N for execution status and updates local record.
        """
        db = SessionLocal()
        try:
            from app.services.workflows import get_n8n_client
            from app.models.n8n_workflows import WorkflowExecution

            n8n_client = get_n8n_client()

            execution = db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()

            if not execution or not execution.n8n_execution_id:
                return {"status": "not_found"}

            # Get status from N8N
            n8n_execution = await n8n_client.get_execution(execution.n8n_execution_id)

            # Update local execution
            executor = WorkflowExecutor(db)

            if n8n_execution.get("finished"):
                if n8n_execution.get("stoppedAt") and not n8n_execution.get("error"):
                    await executor.mark_completed(
                        execution_id=execution_id,
                        output_data=n8n_execution.get("data", {})
                    )
                else:
                    await executor.mark_failed(
                        execution_id=execution_id,
                        error_message=n8n_execution.get("error", "Unknown error")
                    )

            return {"status": "updated", "execution_id": execution_id}

        except Exception as e:
            logger.error(f"Check execution status error: {str(e)}")
            raise

        finally:
            db.close()


# Periodic task schedules (to be configured in celery_app.py)
WORKFLOW_TASK_SCHEDULES = {
    'process-webhook-queue': {
        'task': 'process_webhook_queue',
        'schedule': 30.0,  # Every 30 seconds
    },
    'retry-failed-webhooks': {
        'task': 'retry_failed_webhooks',
        'schedule': 300.0,  # Every 5 minutes
    },
    'expire-old-approvals': {
        'task': 'expire_old_approvals',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-monitoring-events': {
        'task': 'cleanup_old_monitoring_events',
        'schedule': 86400.0,  # Every 24 hours
    },
    'sync-n8n-workflows': {
        'task': 'sync_n8n_workflows',
        'schedule': 1800.0,  # Every 30 minutes
    },
}
