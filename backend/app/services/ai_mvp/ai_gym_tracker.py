"""
AI-GYM Tracker - Tracks AI model performance, costs, and quality metrics.

Logs every AI request to enable:
1. Cost tracking and budget monitoring
2. Model performance comparison
3. Quality metrics over time
4. Optimization feedback loops

Based on research from Claudes_Updates/02_ML_STRATEGY_AND_EVALUATION.md
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

logger = structlog.get_logger(__name__)


class AIGymTracker:
    """
    Tracks AI model usage, costs, and performance metrics.

    Stores data in ai_gym_performance table for analysis and optimization.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize tracker with database session."""
        self.db = db_session
        # Dictionary to track multiple concurrent requests by request_id
        self.active_requests: Dict[int, Dict[str, Any]] = {}

    async def start_request(
        self,
        task_type: str,
        model_name: str,
        lead_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking an AI request.

        Args:
            task_type: Type of AI task (e.g., "website_analysis", "email_generation")
            model_name: Model being used (e.g., "anthropic/claude-sonnet-4")
            lead_id: Associated lead ID (if applicable)
            metadata: Additional context (prompt preview, parameters, etc.)

        Returns:
            Request ID for tracking
        """
        # Insert initial record
        query = text("""
            INSERT INTO ai_gym_performance (
                task_type, model_name, lead_id, metadata, created_at
            )
            VALUES (:task_type, :model_name, :lead_id, :metadata, NOW())
            RETURNING id
        """)

        import json

        result = await self.db.execute(
            query,
            {
                "task_type": task_type,
                "model_name": model_name,
                "lead_id": lead_id,
                "metadata": json.dumps(metadata or {})
            }
        )
        await self.db.commit()

        request_id = result.scalar()
        # Store start time in dictionary keyed by request_id (thread-safe for concurrent requests)
        self.active_requests[request_id] = {
            "start_time": time.time()
        }

        logger.info(
            "ai_gym.request_started",
            request_id=request_id,
            task_type=task_type,
            model_name=model_name
        )

        return request_id

    async def complete_request(
        self,
        request_id: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        response_text: Optional[str] = None,
        quality_scores: Optional[Dict[str, float]] = None
    ):
        """
        Mark request as complete and log metrics.

        Args:
            request_id: ID returned from start_request()
            prompt_tokens: Input tokens used
            completion_tokens: Output tokens generated
            cost: Total cost in dollars
            response_text: Generated response (for quality evaluation)
            quality_scores: Optional quality metrics (faithfulness, relevance, etc.)
        """
        # Calculate duration from active_requests dictionary
        duration = None
        if request_id in self.active_requests:
            duration = time.time() - self.active_requests[request_id]["start_time"]

        # Update record with completion data
        query = text("""
            UPDATE ai_gym_performance
            SET
                prompt_tokens = :prompt_tokens,
                completion_tokens = :completion_tokens,
                total_tokens = :total_tokens,
                cost = :cost,
                duration_seconds = :duration_seconds,
                response_text = :response_text,
                faithfulness_score = :faithfulness_score,
                relevance_score = :relevance_score,
                coherence_score = :coherence_score,
                conciseness_score = :conciseness_score,
                composite_score = :composite_score,
                updated_at = NOW()
            WHERE id = :request_id
        """)

        quality = quality_scores or {}
        await self.db.execute(
            query,
            {
                "request_id": request_id,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost": cost,
                "duration_seconds": duration,
                "response_text": response_text,
                "faithfulness_score": quality.get("faithfulness"),
                "relevance_score": quality.get("relevance"),
                "coherence_score": quality.get("coherence"),
                "conciseness_score": quality.get("conciseness"),
                "composite_score": quality.get("composite"),
            }
        )
        await self.db.commit()

        logger.info(
            "ai_gym.request_completed",
            request_id=request_id,
            tokens=prompt_tokens + completion_tokens,
            cost=cost,
            duration=duration
        )

        # Clear completed request from active_requests dictionary
        if request_id in self.active_requests:
            del self.active_requests[request_id]

    async def log_conversion(
        self,
        request_id: int,
        conversion_metric: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log conversion event (email reply, meeting booked, etc.).

        Args:
            request_id: AI request that led to conversion
            conversion_metric: Conversion value (0.0-1.0, or dollar amount)
            metadata: Additional conversion context
        """
        query = text("""
            UPDATE ai_gym_performance
            SET
                conversion_metric = :conversion_metric,
                metadata = metadata || :metadata::jsonb,
                updated_at = NOW()
            WHERE id = :request_id
        """)

        import json

        await self.db.execute(
            query,
            {
                "request_id": request_id,
                "conversion_metric": conversion_metric,
                "metadata": json.dumps(metadata or {})
            }
        )
        await self.db.commit()

        logger.info(
            "ai_gym.conversion_logged",
            request_id=request_id,
            conversion_metric=conversion_metric
        )

    async def get_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cost summary for a time period.

        Args:
            start_date: Start of period (default: 30 days ago)
            end_date: End of period (default: now)
            task_type: Filter by task type

        Returns:
            Summary with total cost, request count, avg cost, etc.
        """
        filters = []
        params = {}

        if start_date:
            filters.append("created_at >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("created_at <= :end_date")
            params["end_date"] = end_date
        if task_type:
            filters.append("task_type = :task_type")
            params["task_type"] = task_type

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        query = text(f"""
            SELECT
                COUNT(*) as request_count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost,
                SUM(total_tokens) as total_tokens,
                AVG(duration_seconds) as avg_duration,
                AVG(composite_score) as avg_quality
            FROM ai_gym_performance
            {where_clause}
        """)

        result = await self.db.execute(query, params)
        row = result.fetchone()

        return {
            "request_count": row[0] or 0,
            "total_cost": float(row[1] or 0),
            "avg_cost": float(row[2] or 0),
            "total_tokens": int(row[3] or 0),
            "avg_duration_seconds": float(row[4] or 0),
            "avg_quality_score": float(row[5] or 0) if row[5] else None
        }

    async def get_model_performance(
        self,
        task_type: Optional[str] = None,
        min_samples: int = 5
    ) -> list[Dict[str, Any]]:
        """
        Compare model performance by task type.

        Args:
            task_type: Filter by specific task type
            min_samples: Minimum samples required for comparison

        Returns:
            List of model performance stats
        """
        where_clause = f"WHERE task_type = :task_type" if task_type else ""
        params = {"task_type": task_type} if task_type else {}

        query = text(f"""
            SELECT
                model_name,
                task_type,
                COUNT(*) as request_count,
                AVG(cost) as avg_cost,
                AVG(duration_seconds) as avg_duration,
                AVG(composite_score) as avg_quality,
                SUM(cost) as total_cost
            FROM ai_gym_performance
            {where_clause}
            GROUP BY model_name, task_type
            HAVING COUNT(*) >= :min_samples
            ORDER BY task_type, avg_cost ASC
        """)

        params["min_samples"] = min_samples
        result = await self.db.execute(query, params)
        rows = result.fetchall()

        return [
            {
                "model_name": row[0],
                "task_type": row[1],
                "request_count": row[2],
                "avg_cost": float(row[3]),
                "avg_duration_seconds": float(row[4]) if row[4] else None,
                "avg_quality_score": float(row[5]) if row[5] else None,
                "total_cost": float(row[6])
            }
            for row in rows
        ]

    async def check_budget_alert(
        self,
        daily_limit: float = 50.0,
        weekly_limit: float = 300.0,
        monthly_limit: float = 1200.0
    ) -> Optional[Dict[str, Any]]:
        """
        Check if spending exceeds budget thresholds.

        Args:
            daily_limit: Daily budget limit in dollars
            weekly_limit: Weekly budget limit in dollars
            monthly_limit: Monthly budget limit in dollars

        Returns:
            Alert dict if threshold exceeded, None otherwise
        """
        # Check daily
        query_daily = text("""
            SELECT SUM(cost) as daily_cost
            FROM ai_gym_performance
            WHERE created_at >= NOW() - INTERVAL '1 day'
        """)
        result = await self.db.execute(query_daily)
        daily_cost = result.scalar() or 0.0

        if daily_cost >= daily_limit:
            return {
                "period": "daily",
                "spent": float(daily_cost),
                "limit": daily_limit,
                "percent": (daily_cost / daily_limit) * 100
            }

        # Check weekly
        query_weekly = text("""
            SELECT SUM(cost) as weekly_cost
            FROM ai_gym_performance
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        result = await self.db.execute(query_weekly)
        weekly_cost = result.scalar() or 0.0

        if weekly_cost >= weekly_limit:
            return {
                "period": "weekly",
                "spent": float(weekly_cost),
                "limit": weekly_limit,
                "percent": (weekly_cost / weekly_limit) * 100
            }

        # Check monthly
        query_monthly = text("""
            SELECT SUM(cost) as monthly_cost
            FROM ai_gym_performance
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)
        result = await self.db.execute(query_monthly)
        monthly_cost = result.scalar() or 0.0

        if monthly_cost >= monthly_limit:
            return {
                "period": "monthly",
                "spent": float(monthly_cost),
                "limit": monthly_limit,
                "percent": (monthly_cost / monthly_limit) * 100
            }

        return None
