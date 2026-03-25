"""
Background task scheduler for automated pipeline operations.

Handles:
1. SLA enforcement - Check for overdue reviews every 5 minutes
2. Proactive monitoring - Poll observability thresholds for auto-ticket creation
3. Verification polling - Check TestRail run results post-deployment
4. Pipeline heartbeat - Dead-man switch for incident monitoring
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)

# Try to import APScheduler, fall back gracefully if not available
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("apscheduler_not_installed", message="Background tasks disabled. Install with: pip install apscheduler")


class PipelineScheduler:
    """
    Manages scheduled background tasks for the RCA pipeline.
    
    Tasks:
    - sla_checker: Every 5 minutes, check for overdue reviews
    - proactive_monitor: Every 15 minutes, poll NR/DD thresholds
    - verification_poller: Every 10 minutes, check pending verification runs
    - heartbeat: Every minute, update heartbeat for dead-man switch
    """
    
    _instance: Optional["PipelineScheduler"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._last_heartbeat: datetime = datetime.utcnow()
        self._active_incidents: List[str] = []
        self._notification_handlers: List[Callable] = []
        self._initialized = True
        
        if APSCHEDULER_AVAILABLE:
            self._scheduler = AsyncIOScheduler()
            self._setup_jobs()
            logger.info("scheduler_initialized")
        else:
            logger.warning("scheduler_disabled", reason="apscheduler not installed")
    
    def _setup_jobs(self):
        """Configure all scheduled jobs."""
        if not self._scheduler:
            return
        
        # SLA Checker - every 5 minutes
        self._scheduler.add_job(
            self._check_overdue_reviews,
            IntervalTrigger(minutes=5),
            id="sla_checker",
            name="Review SLA Checker",
            replace_existing=True
        )
        
        # Proactive Monitor - every 15 minutes
        self._scheduler.add_job(
            self._proactive_threshold_check,
            IntervalTrigger(minutes=15),
            id="proactive_monitor",
            name="Proactive Threshold Monitor",
            replace_existing=True
        )
        
        # Verification Poller - every 10 minutes
        self._scheduler.add_job(
            self._poll_verification_runs,
            IntervalTrigger(minutes=10),
            id="verification_poller",
            name="TestRail Verification Poller",
            replace_existing=True
        )
        
        # Heartbeat - every minute
        self._scheduler.add_job(
            self._update_heartbeat,
            IntervalTrigger(minutes=1),
            id="heartbeat",
            name="Pipeline Heartbeat",
            replace_existing=True
        )
        
        # Pipeline metrics collection - every 5 minutes
        self._scheduler.add_job(
            self._collect_pipeline_metrics,
            IntervalTrigger(minutes=5),
            id="metrics_collector",
            name="Pipeline Metrics Collector",
            replace_existing=True
        )
        
        logger.info("scheduled_jobs_configured", job_count=5)
    
    def start(self):
        """Start the scheduler."""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            logger.info("scheduler_started")
    
    def stop(self):
        """Stop the scheduler gracefully."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("scheduler_stopped")
    
    def add_notification_handler(self, handler: Callable):
        """Register a notification handler for alerts."""
        self._notification_handlers.append(handler)
    
    async def _notify(self, event_type: str, data: Dict[str, Any]):
        """Send notification through all registered handlers."""
        for handler in self._notification_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error("notification_handler_failed", event=event_type, error=str(e))
    
    # =========================================================================
    # Scheduled Tasks
    # =========================================================================
    
    async def _check_overdue_reviews(self):
        """Check for reviews that have exceeded the 24h SLA."""
        from mcp.db.review_store import get_pending_reviews, mark_review_expired
        
        try:
            pending = get_pending_reviews()
            now = datetime.utcnow()
            
            for review in pending:
                if review.is_overdue and review.status.value == "pending":
                    # Mark as expired and notify
                    mark_review_expired(review.review_id)
                    
                    await self._notify("sla_breach", {
                        "review_id": review.review_id,
                        "rca_id": review.rca_id,
                        "jira_ticket_id": review.jira_ticket_id,
                        "sla_deadline": review.sla_deadline.isoformat(),
                        "hours_overdue": (now - review.sla_deadline).total_seconds() / 3600
                    })
                    
                    logger.warning(
                        "review_sla_breached",
                        review_id=review.review_id,
                        jira=review.jira_ticket_id
                    )
            
            logger.debug("sla_check_complete", pending_count=len(pending))
            
        except Exception as e:
            logger.error("sla_check_failed", error=str(e))
    
    async def _proactive_threshold_check(self):
        """Poll observability tools for threshold breaches and auto-create tickets."""
        from config import settings
        
        try:
            breaches = []
            
            # Check New Relic thresholds
            if settings.newrelic_enabled:
                nr_breaches = await self._check_newrelic_thresholds()
                breaches.extend(nr_breaches)
            
            # Check Datadog thresholds
            if settings.datadog_enabled:
                dd_breaches = await self._check_datadog_thresholds()
                breaches.extend(dd_breaches)
            
            # Auto-create tickets for breaches
            for breach in breaches:
                await self._auto_create_ticket(breach)
            
            logger.debug("proactive_check_complete", breaches_found=len(breaches))
            
        except Exception as e:
            logger.error("proactive_check_failed", error=str(e))
    
    async def _check_newrelic_thresholds(self) -> List[Dict[str, Any]]:
        """Check New Relic for threshold breaches."""
        from config import settings
        from mcp.tools.newrelic_tool import run_nrql
        
        breaches = []
        
        try:
            # Error rate check
            error_query = f"""
                SELECT percentage(count(*), WHERE error IS true) as error_rate
                FROM Transaction
                WHERE appName = '{settings.newrelic_app_name}'
                SINCE 15 minutes ago
            """
            result = run_nrql(error_query)
            
            if result and len(result) > 0:
                error_rate = result[0].get("error_rate", 0)
                if error_rate > settings.newrelic_error_rate_threshold * 100:
                    breaches.append({
                        "source": "newrelic",
                        "metric": "error_rate",
                        "value": error_rate,
                        "threshold": settings.newrelic_error_rate_threshold * 100,
                        "service": settings.newrelic_app_name
                    })
        except Exception as e:
            logger.warning("newrelic_threshold_check_failed", error=str(e))
        
        return breaches
    
    async def _check_datadog_thresholds(self) -> List[Dict[str, Any]]:
        """Check Datadog for triggered monitors."""
        from mcp.tools.datadog_tool import fetch_triggered_monitors
        
        breaches = []
        
        try:
            monitors = fetch_triggered_monitors("paramount-streaming")
            for monitor in monitors:
                if monitor.get("status") in ("Alert", "Warn"):
                    breaches.append({
                        "source": "datadog",
                        "metric": monitor.get("name", "unknown"),
                        "value": monitor.get("state", {}),
                        "threshold": "triggered",
                        "service": "paramount-streaming"
                    })
        except Exception as e:
            logger.warning("datadog_threshold_check_failed", error=str(e))
        
        return breaches
    
    async def _auto_create_ticket(self, breach: Dict[str, Any]):
        """
        Auto-create a Jira ticket for a threshold breach.
        
        Implements idempotency to prevent duplicate tickets:
        - Checks if a ticket for this breach signature exists in last 4 hours
        - Creates ticket only if no recent match found
        """
        import hashlib
        from mcp.integrations.jira_connector import JiraConnector
        from mcp.db.rca_store import get_recent_rcas
        
        # Generate idempotency key from breach signature
        breach_key = f"{breach['source']}:{breach['metric']}:{breach['service']}"
        breach_hash = hashlib.md5(breach_key.encode()).hexdigest()[:12]
        
        # Check if we've already created a ticket for this breach recently (4 hours)
        recent = get_recent_rcas(limit=50)
        cutoff = datetime.utcnow() - timedelta(hours=4)
        
        for rca in recent:
            if rca.created_at > cutoff and breach_hash in (rca.jira_ticket_id or ""):
                logger.debug(
                    "auto_ticket_skipped_duplicate",
                    breach_key=breach_key,
                    existing_rca=rca.rca_id
                )
                return  # Already have a recent ticket for this breach
        
        # Create the Jira ticket
        try:
            connector = JiraConnector()
            
            summary = f"[AUTO] {breach['source'].upper()} Alert: {breach['metric']} threshold exceeded on {breach['service']}"
            description = (
                f"Automatically created from proactive monitoring.\n\n"
                f"**Source:** {breach['source']}\n"
                f"**Metric:** {breach['metric']}\n"
                f"**Service:** {breach['service']}\n"
                f"**Current Value:** {breach['value']}\n"
                f"**Threshold:** {breach['threshold']}\n\n"
                f"Breach ID: {breach_hash}\n"
                f"Detected at: {datetime.utcnow().isoformat()}"
            )
            
            # Determine priority based on breach severity
            priority = "Critical" if "error" in breach['metric'].lower() else "High"
            
            result = connector.create_issue(
                summary=summary,
                description=description,
                issue_type="Bug",
                priority=priority
            )
            
            logger.info(
                "auto_ticket_created",
                breach_key=breach_key,
                jira_key=result.get("issue_id"),
                source=breach['source']
            )
            
            # Optionally trigger RCA pipeline immediately
            if result.get("issue_id"):
                await self._notify("auto_ticket_created", {
                    "jira_key": result.get("issue_id"),
                    "breach": breach,
                    "message": f"Auto-created ticket from {breach['source']} threshold breach"
                })
                
        except Exception as e:
            logger.error("auto_ticket_creation_failed", breach=breach, error=str(e))
    
    async def _poll_verification_runs(self):
        """Check status of pending TestRail verification runs."""
        from mcp.db.rca_store import get_rcas_by_stage
        from mcp.models.rca_models import PipelineStage
        from mcp.tools.testrail_tool import get_run_results
        
        try:
            # Get RCAs that have verification runs pending
            completed_rcas = get_rcas_by_stage(PipelineStage.COMPLETED)
            
            for rca in completed_rcas:
                if rca.testrail_verification_run_id and not getattr(rca, 'verification_complete', False):
                    try:
                        results = get_run_results(rca.testrail_verification_run_id)
                        
                        if results.get("completed"):
                            await self._notify("verification_complete", {
                                "rca_id": rca.rca_id,
                                "jira_ticket_id": rca.jira_ticket_id,
                                "run_id": rca.testrail_verification_run_id,
                                "passed": results.get("passed_count", 0),
                                "failed": results.get("failed_count", 0)
                            })
                    except Exception as e:
                        logger.warning("verification_poll_failed", rca_id=rca.rca_id, error=str(e))
            
            logger.debug("verification_poll_complete")
            
        except Exception as e:
            logger.error("verification_poll_failed", error=str(e))
    
    async def _update_heartbeat(self):
        """Update heartbeat timestamp for dead-man switch monitoring."""
        self._last_heartbeat = datetime.utcnow()
        
        # Check if we have active incidents with no recent activity
        # This is the dead-man switch
        if self._active_incidents:
            from mcp.db.rca_store import get_rca
            
            for rca_id in self._active_incidents:
                rca = get_rca(rca_id)
                if rca and rca.stage not in (PipelineStage.COMPLETED, PipelineStage.FAILED):
                    # Check if pipeline is stalled
                    if rca.updated_at:
                        stall_threshold = timedelta(minutes=30)
                        if datetime.utcnow() - rca.updated_at > stall_threshold:
                            await self._notify("pipeline_stalled", {
                                "rca_id": rca_id,
                                "stage": rca.stage.value,
                                "stalled_for_minutes": (datetime.utcnow() - rca.updated_at).total_seconds() / 60
                            })
        
        logger.debug("heartbeat_updated", timestamp=self._last_heartbeat.isoformat())
    
    async def _collect_pipeline_metrics(self):
        """Collect pipeline performance metrics."""
        from mcp.db.rca_store import get_recent_rcas
        
        try:
            recent = get_recent_rcas(limit=100)
            
            if not recent:
                return
            
            # Calculate metrics
            completed = [r for r in recent if r.stage == PipelineStage.COMPLETED]
            failed = [r for r in recent if r.stage == PipelineStage.FAILED]
            pending_review = [r for r in recent if r.stage == PipelineStage.REVIEW_PENDING]
            
            # Calculate average cycle time
            cycle_times = []
            for r in completed:
                if r.created_at and r.updated_at:
                    cycle_time = (r.updated_at - r.created_at).total_seconds() / 3600
                    cycle_times.append(cycle_time)
            
            avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
            
            metrics = {
                "total_recent": len(recent),
                "completed": len(completed),
                "failed": len(failed),
                "pending_review": len(pending_review),
                "avg_cycle_time_hours": round(avg_cycle_time, 2),
                "success_rate": round(len(completed) / len(recent) * 100, 1) if recent else 0
            }
            
            logger.info("pipeline_metrics", **metrics)
            
        except Exception as e:
            logger.error("metrics_collection_failed", error=str(e))
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def register_active_incident(self, rca_id: str):
        """Register an RCA as an active incident for monitoring."""
        if rca_id not in self._active_incidents:
            self._active_incidents.append(rca_id)
            logger.info("incident_registered", rca_id=rca_id)
    
    def unregister_active_incident(self, rca_id: str):
        """Remove an RCA from active incident monitoring."""
        if rca_id in self._active_incidents:
            self._active_incidents.remove(rca_id)
            logger.info("incident_unregistered", rca_id=rca_id)
    
    @property
    def last_heartbeat(self) -> datetime:
        """Get the last heartbeat timestamp."""
        return self._last_heartbeat
    
    @property
    def is_healthy(self) -> bool:
        """Check if the scheduler is healthy (heartbeat within 5 minutes)."""
        if not self._scheduler:
            return False
        return (datetime.utcnow() - self._last_heartbeat) < timedelta(minutes=5)
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        if not self._scheduler:
            return {"status": "disabled", "jobs": []}
        
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "pending": job.pending
            })
        
        return {
            "status": "running" if self._scheduler.running else "stopped",
            "jobs": jobs,
            "last_heartbeat": self._last_heartbeat.isoformat(),
            "active_incidents": len(self._active_incidents)
        }


# Import PipelineStage for use in methods
from mcp.models.rca_models import PipelineStage

# Global singleton
scheduler = PipelineScheduler()


def start_scheduler():
    """Start the background scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.stop()
