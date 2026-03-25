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
"""

import uuid
from datetime import datetime
from typing import Optional

from config import settings
from mcp.models.rca_models import RCARecord, PipelineStage, MatchConfidence
from mcp.models.evidence_models import EvidenceBundle
from mcp.db.rca_store import upsert_rca, get_rca, check_for_duplicates
from mcp.db.review_store import create_review_item
from mcp.tools.newrelic_tool import capture_newrelic_snapshot
from mcp.tools.datadog_tool import capture_datadog_snapshot
from mcp.tools.evidence_normalizer import normalize_evidence
from mcp.tools.testrail_tool import (
    find_testrail_match, create_test_cases_bulk,
    create_rca_verification_run, add_cases_to_regression_run
)
from mcp.tools.ai_summarizer import summarize_incident
from mcp.tools.test_generator import generate_test_cases
from mcp.tools.dependency_graph import compute_blast_radius, resolve_test_scope
from mcp.pipeline.stages import validate_transition
from mcp.utils.logger import get_logger

logger = get_logger(__name__)


class RCAPipeline:
    """Orchestrates the full RCA pipeline as a state machine."""

    def run(self, jira_ticket: dict) -> RCARecord:
        """
        Execute the pipeline from intake through test generation.
        Pauses at REVIEW_PENDING if test generation is triggered.
        """
        record = RCARecord(
            rca_id=str(uuid.uuid4()),
            jira_ticket_id=jira_ticket["id"],
            created_at=datetime.utcnow(),
            service_name=jira_ticket.get("service", ""),
            stage=PipelineStage.INTAKE
        )
        upsert_rca(record)

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
                return record  # Pauses for human review

            # Step 6+7: Blast radius + close (for PROBABLE/EXACT matches)
            self._step_blast_radius(record, evidence)
            return record

        except Exception as e:
            record.stage = PipelineStage.FAILED
            upsert_rca(record)
            logger.exception("Pipeline failed", rca_id=record.rca_id, error=str(e))
            raise

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

            created = create_test_cases_bulk(approved_cases, record.jira_ticket_id)
            new_case_ids = [c.get("id") for c in created if c.get("id")]

            record.testrail_created_case_ids = new_case_ids

            if new_case_ids:
                verification_run = create_rca_verification_run(
                    rca_id=record.rca_id,
                    jira_ticket_id=record.jira_ticket_id,
                    case_ids=new_case_ids
                )
                record.testrail_verification_run_id = verification_run.get("id")

                if record.regression_run_id:
                    add_cases_to_regression_run(record.regression_run_id, new_case_ids)

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
        upsert_rca(record)

        record.ai_summary = summarize_incident(jira_ticket, evidence)
        upsert_rca(record)

    def _step_testrail_match(self, record: RCARecord, jira_ticket: dict):
        """Step 4: TestRail tiered matching."""
        record.stage = PipelineStage.TESTRAIL_MATCH
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
        upsert_rca(record)

        cases = generate_test_cases(record, evidence)
        record.generated_test_cases = cases
        record.stage = PipelineStage.REVIEW_PENDING
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
        """Step 7: Close Jira with full RCA artifact, transition ticket, and add comment."""
        import json as _json
        import httpx

        record.stage = PipelineStage.JIRA_CLOSE
        upsert_rca(record)

        artifact = {
            "rca_id": record.rca_id,
            "root_cause": record.ai_summary,
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
            "blast_radius": {
                "impacted_components": record.impacted_components or [],
                "risk_level": blast.get("risk_level", "unknown"),
                "total_affected": blast.get("total_blast_radius", 0)
            },
            "test_scope": {
                "smoke_suite_ids": record.smoke_scope or [],
                "regression_suite_ids": record.regression_scope or []
            },
            "remediation_owners": []
        }

        record.rca_artifact_url = f"/api/rca/pipeline/{record.rca_id}"

        jira_key = record.jira_ticket_id
        jira_url = settings.jira_api_url.rstrip("/")
        jira_email = settings.jira_api_email
        jira_token = settings.jira_api_token

        if jira_key and jira_url and jira_email and jira_token:
            auth = (jira_email, jira_token)
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            comment_body = (
                f"*RCA Pipeline Complete* ({record.rca_id})\n\n"
                f"*Root Cause:* {record.ai_summary or 'N/A'}\n"
                f"*Blast Radius:* {blast.get('risk_level', 'unknown')} "
                f"({blast.get('total_blast_radius', 0)} components affected)\n"
                f"*TestRail Cases Created:* {len(record.testrail_created_case_ids or [])}\n"
                f"*Verification Run:* {record.testrail_verification_run_id or 'N/A'}\n\n"
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
        record.stage = PipelineStage.COMPLETED
        upsert_rca(record)

        logger.info(
            "Jira closed with RCA artifact",
            rca_id=record.rca_id,
            jira=record.jira_ticket_id,
            cases_written=len(record.testrail_created_case_ids or [])
        )

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
