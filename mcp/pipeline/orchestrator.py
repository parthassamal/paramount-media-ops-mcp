"""
RCA Pipeline Orchestrator -- state machine driving the full end-to-end flow.

Steps:
1. Jira intake + 90-day duplicate detection
2. Dual-source evidence capture (New Relic + Datadog)
3. AI summarization via EvidenceBundle
4. TestRail tiered matching (50/75/100%)
5. Test generation + LLM-as-judge scoring
   → Human review gate (24hr SLA)
   → TestRail WRITE (approved cases only)
6. Blast radius from service map
7. Jira close with full RCA artifact

Enterprise Features:
- Idempotency: Prevents duplicate RCAs for same Jira ticket
- Retry/Resume: Can resume from any failed stage
- Concurrency Lock: Prevents race conditions on same service
- Notifications: Slack/Jira alerts on key events
- Integrity Hash: SHA-256 tamper evidence on artifacts
"""

import uuid
import fcntl
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from contextlib import contextmanager

from config import settings
from mcp.models.rca_models import RCARecord, PipelineStage, MatchConfidence, VerificationResult, RemediationAction
from mcp.models.evidence_models import EvidenceBundle
from mcp.db.rca_store import upsert_rca, get_rca, check_for_duplicates, get_rca_by_jira_key
from mcp.db.review_store import create_review_item
from mcp.tools.newrelic_tool import capture_newrelic_snapshot
from mcp.tools.datadog_tool import capture_datadog_snapshot
from mcp.tools.evidence_normalizer import normalize_evidence
from mcp.tools.testrail_tool import (
    find_testrail_match, create_test_cases_bulk,
    create_rca_verification_run, add_cases_to_regression_run,
    get_run_results
)
from mcp.tools.ai_summarizer import summarize_incident
from mcp.tools.test_generator import generate_test_cases
from mcp.tools.dependency_graph import compute_blast_radius, resolve_test_scope
from mcp.pipeline.stages import validate_transition
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

# Lock directory for concurrency control
LOCK_DIR = Path(__file__).parent.parent.parent / "data" / "locks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


class PipelineLockError(Exception):
    """Raised when unable to acquire pipeline lock."""
    pass


class IdempotencyError(Exception):
    """Raised when duplicate pipeline run detected."""
    pass


@contextmanager
def pipeline_lock(service_name: str, timeout: float = 30.0):
    """
    Acquire an exclusive lock for a service to prevent concurrent pipeline runs.
    Uses file-based locking for simplicity and portability.
    """
    lock_file = LOCK_DIR / f"{service_name.replace('/', '_')}.lock"
    lock_fd = None
    
    try:
        lock_fd = open(lock_file, 'w')
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(f"{os.getpid()}:{datetime.utcnow().isoformat()}")
        lock_fd.flush()
        logger.debug("pipeline_lock_acquired", service=service_name)
        yield
    except BlockingIOError:
        raise PipelineLockError(f"Pipeline already running for service: {service_name}")
    finally:
        if lock_fd:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            lock_fd.close()
            try:
                lock_file.unlink()
            except:
                pass
            logger.debug("pipeline_lock_released", service=service_name)


class RCAPipeline:
    """
    Orchestrates the full RCA pipeline as a state machine.
    
    Features:
    - Idempotency: Same Jira ticket won't create duplicate RCAs
    - Concurrency: Lock prevents race conditions on same service
    - Retry/Resume: Failed pipelines can be resumed from last stage
    - Notifications: Alerts on REVIEW_PENDING and failures
    """

    def run(self, jira_ticket: dict) -> RCARecord:
        """
        Execute the pipeline from intake through test generation.
        Pauses at REVIEW_PENDING if test generation is triggered.
        
        Idempotency: If an RCA already exists for this Jira ticket and is not
        completed/failed, returns the existing record instead of creating a new one.
        """
        jira_key = jira_ticket["id"]
        service = jira_ticket.get("service", "unknown")
        
        # Idempotency check: Return existing active RCA (skip stale jira_close)
        existing = get_rca_by_jira_key(jira_key)
        terminal_stages = (PipelineStage.COMPLETED, PipelineStage.FAILED)
        if existing and existing.stage not in terminal_stages:
            stale_close = (
                existing.stage == PipelineStage.JIRA_CLOSE
                and existing.failure_reason
                and "Close blocked" in existing.failure_reason
            )
            if not stale_close:
                logger.info(
                    "idempotency_hit",
                    jira=jira_key,
                    rca_id=existing.rca_id,
                    stage=existing.stage.value
                )
                return existing
            logger.info(
                "idempotency_stale_close_bypassed",
                jira=jira_key,
                old_rca_id=existing.rca_id,
            )
        
        # Create new RCA record
        record = RCARecord(
            rca_id=str(uuid.uuid4()),
            jira_ticket_id=jira_key,
            created_at=datetime.utcnow(),
            service_name=service,
            stage=PipelineStage.INTAKE
        )
        record.record_stage_timestamp(PipelineStage.INTAKE)
        upsert_rca(record)
        
        # Acquire lock for the service to prevent concurrent runs
        try:
            with pipeline_lock(service):
                return self._execute_pipeline(record, jira_ticket)
        except PipelineLockError as e:
            logger.warning("pipeline_lock_failed", jira=jira_key, error=str(e))
            # Return the record in INTAKE state - caller can retry later
            return record
    
    def _execute_pipeline(self, record: RCARecord, jira_ticket: dict) -> RCARecord:
        """Execute the pipeline stages with error handling."""
        try:
            # Step 1: Duplicate detection
            self._step_intake(record, jira_ticket)

            # Step 2: Dual-source evidence capture
            evidence = self._step_evidence_capture(record, jira_ticket)

            # Step 3: AI summarization
            self._step_summarize(record, jira_ticket, evidence)

            # Step 4: TestRail matching
            match = self._step_testrail_match(record, jira_ticket)

            # Step 5: Generate test cases if needed
            if match.confidence in (MatchConfidence.NO_MATCH.value, MatchConfidence.LOW.value):
                self._step_test_generation(record, evidence)
                self._send_review_notification(record)
                return record  # Pauses for human review

            # Step 6+7: Blast radius + close (for PROBABLE/EXACT matches)
            self._step_blast_radius(record, evidence)
            return record

        except Exception as e:
            record.stage = PipelineStage.FAILED
            record.last_failed_stage = record.stage
            record.failure_reason = str(e)[:500]
            record.retry_count += 1
            upsert_rca(record)
            
            self._send_failure_notification(record, str(e))
            logger.exception("Pipeline failed", rca_id=record.rca_id, error=str(e))
            raise
    
    def resume_from_stage(self, rca_id: str, stage: Optional[PipelineStage] = None) -> RCARecord:
        """
        Resume a failed pipeline from a specific stage.
        
        Args:
            rca_id: The RCA record ID to resume
            stage: Stage to resume from (defaults to last_failed_stage or current stage)
            
        Returns:
            Updated RCARecord
        """
        record = get_rca(rca_id)
        if not record:
            raise ValueError(f"RCA {rca_id} not found")
        
        if not record.can_retry():
            raise ValueError(f"RCA {rca_id} cannot be retried (stage={record.stage}, retries={record.retry_count})")
        
        # Determine resume stage
        resume_stage = stage or record.last_failed_stage or record.stage
        
        logger.info(
            "pipeline_resuming",
            rca_id=rca_id,
            from_stage=resume_stage.value,
            retry_count=record.retry_count
        )
        
        # Rebuild evidence if we have it
        evidence = self._rebuild_evidence(record)
        
        # Create a minimal jira_ticket dict from the record
        jira_ticket = {
            "id": record.jira_ticket_id,
            "service": record.service_name,
            "summary": record.ai_summary or ""
        }
        
        try:
            with pipeline_lock(record.service_name or "unknown"):
                # Resume from the appropriate stage
                if resume_stage in (PipelineStage.INTAKE, PipelineStage.EVIDENCE_CAPTURE):
                    evidence = self._step_evidence_capture(record, jira_ticket)
                    resume_stage = PipelineStage.SUMMARIZATION
                
                if resume_stage == PipelineStage.SUMMARIZATION:
                    self._step_summarize(record, jira_ticket, evidence)
                    resume_stage = PipelineStage.TESTRAIL_MATCH
                
                if resume_stage == PipelineStage.TESTRAIL_MATCH:
                    match = self._step_testrail_match(record, jira_ticket)
                    if match.confidence in (MatchConfidence.NO_MATCH.value, MatchConfidence.LOW.value):
                        self._step_test_generation(record, evidence)
                        return record
                    resume_stage = PipelineStage.BLAST_RADIUS
                
                if resume_stage in (PipelineStage.TEST_GENERATION, PipelineStage.REVIEW_PENDING):
                    # Already at review - nothing to resume
                    return record
                
                if resume_stage in (PipelineStage.BLAST_RADIUS, PipelineStage.JIRA_CLOSE):
                    self._step_blast_radius(record, evidence)
                
                return record
                
        except Exception as e:
            record.stage = PipelineStage.FAILED
            record.failure_reason = str(e)[:500]
            record.retry_count += 1
            upsert_rca(record)
            logger.exception("Pipeline resume failed", rca_id=rca_id, error=str(e))
            raise
    
    def _send_review_notification(self, record: RCARecord):
        """Send notification that test cases are ready for review."""
        self._fire_notification("review_pending", {
            "rca_id": record.rca_id,
            "jira_ticket_id": record.jira_ticket_id,
            "cases_count": len(record.generated_test_cases or []),
            "match_confidence": record.testrail_match_confidence,
            "sla_deadline": "24 hours",
        })

    def _send_failure_notification(self, record: RCARecord, error: str):
        """Send notification that pipeline failed."""
        self._fire_notification("pipeline_failed", {
            "rca_id": record.rca_id,
            "jira_ticket_id": record.jira_ticket_id,
            "stage": record.stage.value,
            "error": error[:200],
        })

    @staticmethod
    def _fire_notification(event_name: str, payload: dict):
        """Best-effort notification dispatch, safe in both sync and async contexts."""
        import asyncio
        from mcp.utils.notifications import notify

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(notify(event_name, payload))
        except RuntimeError:
            try:
                asyncio.run(notify(event_name, payload))
            except Exception as e:
                logger.debug("notification_skipped", notification_event=event_name, reason=str(e))

    def resume_after_review(
        self,
        rca_id: str,
        reviewer_id: str,
        notes: str = ""
    ) -> RCARecord:
        """
        Called when human approves generated test cases.
        1. Marks review approved
        2. Writes approved cases into TestRail
        3. Creates verification run
        4. Applies blast radius + regression scope
        """
        record = get_rca(rca_id)
        if not record or record.stage != PipelineStage.REVIEW_PENDING:
            raise ValueError(f"RCA {rca_id} is not pending review")

        record.stage = PipelineStage.REVIEW_APPROVED
        record.reviewer_id = reviewer_id
        record.human_review_approved_at = datetime.utcnow()
        record.review_notes = notes
        upsert_rca(record)

        # Write approved cases to TestRail
        approved_cases = [
            c for c in (record.generated_test_cases or [])
            if c.get("judge_passed")
        ]

        if approved_cases:
            record.stage = PipelineStage.TESTRAIL_WRITE
            upsert_rca(record)

            testrail_error = None
            try:
                created = create_test_cases_bulk(
                    approved_cases, record.jira_ticket_id, service=record.service_name or ""
                )
                new_case_ids = [c.get("id") for c in created if c.get("id")]
            except Exception as exc:
                logger.warning(
                    "testrail_write_failed",
                    rca_id=record.rca_id,
                    testrail_error=str(exc)[:300],
                )
                testrail_error = str(exc)[:300]
                new_case_ids = []

            record.testrail_created_case_ids = new_case_ids
            if testrail_error:
                record.failure_reason = f"TestRail write deferred: {testrail_error}"

            if new_case_ids:
                try:
                    verification_run = create_rca_verification_run(
                        rca_id=record.rca_id,
                        jira_ticket_id=record.jira_ticket_id,
                        case_ids=new_case_ids,
                    )
                    record.testrail_verification_run_id = verification_run.get("id")
                except Exception as exc:
                    logger.warning("verification_run_failed", rca_id=record.rca_id, reason=str(exc)[:200])

                if record.regression_run_id:
                    try:
                        add_cases_to_regression_run(record.regression_run_id, new_case_ids)
                    except Exception as exc:
                        logger.warning("regression_append_failed", rca_id=record.rca_id, reason=str(exc)[:200])

            upsert_rca(record)

        # Continue to blast radius
        evidence = self._rebuild_evidence(record)
        self._step_blast_radius(record, evidence)
        return record

    # =========================================================================
    # Pipeline Steps
    # =========================================================================

    def _step_intake(self, record: RCARecord, jira_ticket: dict):
        """Step 1: Duplicate detection and severity assessment."""
        record.record_stage_timestamp(PipelineStage.INTAKE)
        
        dup = check_for_duplicates(jira_ticket.get("summary", ""))
        if dup:
            record.is_duplicate = True
            record.duplicate_of = dup["duplicate_of"]
            record.severity_escalated = True
            logger.warning(
                "Duplicate incident detected",
                rca_id=record.rca_id,
                duplicate_of=dup["duplicate_of"],
                similarity=dup["similarity"]
            )
        upsert_rca(record)

    def _step_evidence_capture(self, record: RCARecord, jira_ticket: dict) -> EvidenceBundle:
        """Step 2: Capture evidence from configured observability sources."""
        record.stage = PipelineStage.EVIDENCE_CAPTURE
        record.record_stage_timestamp(PipelineStage.EVIDENCE_CAPTURE)
        upsert_rca(record)

        service = jira_ticket.get("service", record.service_name or "")
        incident_time = jira_ticket.get("incident_time")
        nr_snapshot, dd_snapshot = None, None

        if settings.observability_source in ("newrelic", "both"):
            try:
                nr_snapshot = capture_newrelic_snapshot(service, incident_time)
            except Exception as e:
                logger.error("New Relic capture failed", error=str(e))

        if settings.observability_source in ("datadog", "both"):
            try:
                dd_snapshot = capture_datadog_snapshot(service)
            except Exception as e:
                logger.error("Datadog capture failed", error=str(e))

        evidence = normalize_evidence(service, nr_snapshot, dd_snapshot)
        record.evidence_bundle_id = evidence.bundle_id
        record.stack_trace = evidence.stack_trace
        record.error_metrics = {
            "error_rate": evidence.error_rate,
            "p99_latency_ms": evidence.p99_latency_ms,
            "sources": evidence.sources
        }
        upsert_rca(record)

        logger.info(
            "Evidence captured",
            rca_id=record.rca_id,
            sources=evidence.sources,
            bundle_id=evidence.bundle_id
        )
        return evidence

    def _step_summarize(self, record: RCARecord, jira_ticket: dict, evidence: EvidenceBundle):
        """Step 3: AI summarization."""
        record.stage = PipelineStage.SUMMARIZATION
        record.record_stage_timestamp(PipelineStage.SUMMARIZATION)
        upsert_rca(record)

        record.ai_summary = summarize_incident(jira_ticket, evidence)
        record.summary_prompt_version = "1.0"  # Pin version for compatibility
        upsert_rca(record)

    def _step_testrail_match(self, record: RCARecord, jira_ticket: dict):
        """Step 4: TestRail tiered matching."""
        record.stage = PipelineStage.TESTRAIL_MATCH
        record.record_stage_timestamp(PipelineStage.TESTRAIL_MATCH)
        upsert_rca(record)

        match = find_testrail_match(
            jira_ticket.get("summary", ""),
            jira_ticket.get("reproduction_steps", [])
        )
        record.testrail_match_confidence = match.confidence
        record.matched_test_case_id = match.matched_case_id
        record.match_score = match.score
        record.automation_covered = match.automation_covered
        record.automation_gap_reason = match.automation_gap_reason
        upsert_rca(record)

        logger.info(
            "TestRail match complete",
            rca_id=record.rca_id,
            confidence=match.confidence,
            score=match.score
        )
        return match

    def _step_test_generation(self, record: RCARecord, evidence: EvidenceBundle):
        """Step 5: Generate test cases + submit for human review."""
        record.stage = PipelineStage.TEST_GENERATION
        record.record_stage_timestamp(PipelineStage.TEST_GENERATION)
        upsert_rca(record)

        cases = generate_test_cases(record, evidence)
        record.generated_test_cases = cases
        record.stage = PipelineStage.REVIEW_PENDING
        record.record_stage_timestamp(PipelineStage.REVIEW_PENDING)
        upsert_rca(record)

        create_review_item(
            rca_id=record.rca_id,
            jira_ticket_id=record.jira_ticket_id,
            generated_cases=cases,
            ai_summary=record.ai_summary,
            match_confidence=record.testrail_match_confidence,
            sla_hours=settings.rca_review_sla_hours
        )

        logger.info(
            "Test cases generated, pending review",
            rca_id=record.rca_id,
            cases_count=len(cases)
        )

    def _step_blast_radius(self, record: RCARecord, evidence: EvidenceBundle):
        """Step 6: Compute blast radius and test scope."""
        record.stage = PipelineStage.BLAST_RADIUS
        record.record_stage_timestamp(PipelineStage.BLAST_RADIUS)
        upsert_rca(record)

        blast = compute_blast_radius(evidence)
        test_scope = resolve_test_scope(blast)

        record.impacted_components = blast["all_affected"]
        record.smoke_scope = test_scope["smoke_suite_ids"]
        record.regression_scope = test_scope["regression_suite_ids"]
        upsert_rca(record)

        # Step 7: Build RCA artifact and close Jira
        self._step_jira_close(record, blast)

        logger.info(
            "Pipeline complete",
            rca_id=record.rca_id,
            blast_radius=blast["total_blast_radius"],
            risk=blast["risk_level"]
        )

    def _step_jira_close(self, record: RCARecord, blast: dict):
        """
        Step 7: Close Jira with full RCA artifact, transition ticket, and add comment.
        
        BLOCKS CLOSE if validate_artifact() fails:
        - root_cause must be present
        - timeline must be present
        - fix_verified must be True (regression run passed)
        - remediation_owners must have at least one action with owner/due_date
        """
        import json as _json
        import httpx

        record.stage = PipelineStage.JIRA_CLOSE
        record.record_stage_timestamp(PipelineStage.JIRA_CLOSE)

        # Auto-populate root_cause from ai_summary if not explicitly set
        if not record.root_cause and record.ai_summary:
            record.root_cause = record.ai_summary

        # Derive timeline from stage_timestamps if not explicitly set
        if not record.timeline and record.stage_timestamps:
            record.timeline = [
                f"{stage}: {ts}" for stage, ts in record.stage_timestamps.items()
            ]

        # Add default remediation if none defined
        if not record.remediation_owners:
            record.add_remediation_action(
                action=f"Investigate and resolve {record.jira_ticket_id}",
                owner=record.reviewer_id or "unassigned",
                due_days=7,
            )

        upsert_rca(record)

        # VALIDATE ARTIFACT BEFORE CLOSE - this is the gate
        can_close, reason = record.can_close_jira()
        if not can_close:
            logger.warning(
                "jira_close_blocked",
                rca_id=record.rca_id,
                reason=reason
            )
            # Don't fail the pipeline, but don't close the ticket either
            # Leave in JIRA_CLOSE stage for manual resolution
            record.failure_reason = f"Close blocked: {reason}"
            upsert_rca(record)
            return  # Ticket stays open until requirements are met

        artifact = {
            "rca_id": record.rca_id,
            "root_cause": record.ai_summary or record.root_cause,
            "timeline": record.timeline or list(record.stage_timestamps.keys()),
            "evidence_sources": record.error_metrics.get("sources", []) if record.error_metrics else [],
            "testrail_match": {
                "confidence": record.testrail_match_confidence,
                "score": record.match_score,
                "matched_case_id": record.matched_test_case_id
            },
            "testrail_write": {
                "created_case_ids": record.testrail_created_case_ids or [],
                "verification_run_id": record.testrail_verification_run_id
            },
            "verification": {
                "fix_verified": record.fix_verified,
                "verification_result": record.verification_result.model_dump() if record.verification_result else None
            },
            "blast_radius": {
                "impacted_components": record.impacted_components or [],
                "risk_level": blast.get("risk_level", "unknown"),
                "total_affected": blast.get("total_blast_radius", 0)
            },
            "test_scope": {
                "smoke_suite_ids": record.smoke_scope or [],
                "regression_suite_ids": record.regression_scope or []
            },
            "remediation_owners": [r.model_dump() for r in record.remediation_owners]
        }

        record.rca_artifact_url = f"/api/rca/pipeline/{record.rca_id}"

        jira_key = record.jira_ticket_id
        jira_url = settings.jira_api_url.rstrip("/")
        jira_email = settings.jira_api_email
        jira_token = settings.jira_api_token

        if jira_key and jira_url and jira_email and jira_token:
            auth = (jira_email, jira_token)
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            # Enhanced comment with verification status
            verification_status = "✅ PASSED" if record.fix_verified else "⚠️ PENDING"
            remediation_summary = "\n".join([
                f"  • {r.action} (Owner: {r.owner}, Due: {r.due_date.strftime('%Y-%m-%d')})"
                for r in record.remediation_owners
            ]) or "  None defined"

            comment_body = (
                f"*RCA Pipeline Complete* ({record.rca_id})\n\n"
                f"*Root Cause:* {record.ai_summary or 'N/A'}\n"
                f"*Blast Radius:* {blast.get('risk_level', 'unknown')} "
                f"({blast.get('total_blast_radius', 0)} components affected)\n"
                f"*TestRail Cases Created:* {len(record.testrail_created_case_ids or [])}\n"
                f"*Verification Run:* {record.testrail_verification_run_id or 'N/A'}\n"
                f"*Fix Verified:* {verification_status}\n\n"
                f"*Remediation Actions:*\n{remediation_summary}\n\n"
                f"Full artifact: {record.rca_artifact_url}"
            )

            try:
                with httpx.Client(timeout=15.0) as client:
                    client.post(
                        f"{jira_url}/rest/api/3/issue/{jira_key}/comment",
                        auth=auth,
                        headers=headers,
                        json={
                            "body": {
                                "type": "doc", "version": 1,
                                "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_body}]}]
                            }
                        },
                    )
                    logger.info("jira_rca_comment_added", jira=jira_key)
            except Exception as e:
                logger.warning("jira_comment_failed", jira=jira_key, error=str(e))

            try:
                with httpx.Client(timeout=15.0) as client:
                    trans_resp = client.get(
                        f"{jira_url}/rest/api/3/issue/{jira_key}/transitions",
                        auth=auth, headers=headers,
                    )
                    trans_resp.raise_for_status()
                    transitions = trans_resp.json().get("transitions", [])
                    done_transition = next(
                        (t for t in transitions if t["name"].lower() in ("done", "resolved", "closed", "complete")),
                        None,
                    )
                    if done_transition:
                        client.post(
                            f"{jira_url}/rest/api/3/issue/{jira_key}/transitions",
                            auth=auth, headers=headers,
                            json={"transition": {"id": done_transition["id"]}},
                        )
                        logger.info("jira_transitioned", jira=jira_key, to=done_transition["name"])
                    else:
                        logger.warning("jira_no_done_transition", jira=jira_key, available=[t["name"] for t in transitions])
            except Exception as e:
                logger.warning("jira_transition_failed", jira=jira_key, error=str(e))

        record.jira_closed = True
        record.closed_at = datetime.utcnow()
        record.stage = PipelineStage.COMPLETED
        record.record_stage_timestamp(PipelineStage.COMPLETED)
        
        # Compute and store integrity hash for tamper evidence
        record.artifact_hash = record.compute_artifact_hash()
        
        upsert_rca(record)

        logger.info(
            "Jira closed with RCA artifact",
            rca_id=record.rca_id,
            jira=record.jira_ticket_id,
            cases_written=len(record.testrail_created_case_ids or []),
            cycle_time_hours=record.cycle_time_hours,
            artifact_hash=record.artifact_hash[:16] + "...",
            fix_verified=record.fix_verified,
            remediation_count=len(record.remediation_owners)
        )
    
    def verify_regression_results(self, rca_id: str) -> VerificationResult:
        """
        Post-deployment verification: check that new test cases passed.
        
        Called by scheduler or manually after deployment to verify the fix.
        If cases fail, triggers a mini-RCA and blocks Jira close.
        """
        record = get_rca(rca_id)
        if not record:
            raise ValueError(f"RCA {rca_id} not found")
        
        if not record.testrail_verification_run_id:
            raise ValueError(f"RCA {rca_id} has no verification run to check")
        
        record.stage = PipelineStage.VERIFICATION_PENDING
        record.record_stage_timestamp(PipelineStage.VERIFICATION_PENDING)
        record.verification_attempts += 1
        upsert_rca(record)
        
        # Get run results from TestRail
        results = get_run_results(record.testrail_verification_run_id)
        
        verification = VerificationResult(
            run_id=record.testrail_verification_run_id,
            total_cases=results.get("total", 0),
            passed=results.get("passed_count", 0),
            failed=results.get("failed_count", 0),
            blocked=results.get("blocked_count", 0),
            untested=results.get("untested_count", 0),
            pass_rate=results.get("pass_rate", 0.0),
            all_passed=results.get("all_passed", False),
            failed_case_ids=results.get("failed_case_ids", [])
        )
        
        record.verification_result = verification
        
        if verification.all_passed:
            record.fix_verified = True
            record.stage = PipelineStage.VERIFICATION_COMPLETE
            record.record_stage_timestamp(PipelineStage.VERIFICATION_COMPLETE)
            logger.info(
                "verification_passed",
                rca_id=rca_id,
                passed=verification.passed,
                total=verification.total_cases
            )
        else:
            # Failures detected - trigger mini-RCA
            verification.mini_rca_triggered = True
            logger.warning(
                "verification_failed_mini_rca",
                rca_id=rca_id,
                failed=verification.failed,
                failed_cases=verification.failed_case_ids
            )
            
            # Don't mark fix_verified - keeps Jira from closing
            if record.verification_attempts >= record.max_verification_attempts:
                record.stage = PipelineStage.FAILED
                record.failure_reason = f"Verification failed after {record.verification_attempts} attempts"
        
        upsert_rca(record)
        return verification

    def _rebuild_evidence(self, record: RCARecord) -> EvidenceBundle:
        """Reconstruct a minimal EvidenceBundle from the record's stored data."""
        return EvidenceBundle(
            bundle_id=record.evidence_bundle_id or str(uuid.uuid4()),
            captured_at=datetime.utcnow(),
            sources=record.error_metrics.get("sources", []) if record.error_metrics else [],
            service_name=record.service_name or "",
            stack_trace=record.stack_trace,
            error_rate=record.error_metrics.get("error_rate") if record.error_metrics else None,
            p99_latency_ms=record.error_metrics.get("p99_latency_ms") if record.error_metrics else None
        )
