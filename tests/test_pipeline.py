"""Tests for the RCA pipeline orchestrator and stages."""

import pytest
from mcp.models.rca_models import PipelineStage, MatchConfidence, RCARecord
from mcp.models.evidence_models import EvidenceBundle, ServiceMapNode
from mcp.models.review_queue import ReviewItem, ReviewStatus
from mcp.pipeline.stages import validate_transition, get_next_stages
from datetime import datetime, timedelta


class TestPipelineStages:
    """Test stage transition rules."""

    def test_intake_to_evidence_capture(self):
        assert validate_transition(PipelineStage.INTAKE, PipelineStage.EVIDENCE_CAPTURE)

    def test_intake_to_failed(self):
        assert validate_transition(PipelineStage.INTAKE, PipelineStage.FAILED)

    def test_intake_to_completed_invalid(self):
        assert not validate_transition(PipelineStage.INTAKE, PipelineStage.COMPLETED)

    def test_review_pending_to_approved(self):
        assert validate_transition(PipelineStage.REVIEW_PENDING, PipelineStage.REVIEW_APPROVED)

    def test_review_pending_to_rejected(self):
        assert validate_transition(PipelineStage.REVIEW_PENDING, PipelineStage.REVIEW_REJECTED)

    def test_completed_terminal(self):
        assert get_next_stages(PipelineStage.COMPLETED) == []

    def test_failed_terminal(self):
        assert get_next_stages(PipelineStage.FAILED) == []

    def test_testrail_match_can_skip_to_blast_radius(self):
        assert validate_transition(PipelineStage.TESTRAIL_MATCH, PipelineStage.BLAST_RADIUS)


class TestRCARecord:
    """Test RCA record model."""

    def test_create_record(self):
        record = RCARecord(
            rca_id="test-123",
            jira_ticket_id="PROD-456",
            created_at=datetime.utcnow()
        )
        assert record.stage == PipelineStage.INTAKE
        assert not record.is_duplicate
        assert record.jira_closed is False

    def test_record_with_evidence(self):
        record = RCARecord(
            rca_id="test-123",
            jira_ticket_id="PROD-456",
            created_at=datetime.utcnow(),
            stage=PipelineStage.EVIDENCE_CAPTURE,
            evidence_bundle_id="bundle-789",
            error_metrics={"error_rate": 0.05, "sources": ["newrelic", "datadog"]}
        )
        assert record.error_metrics["error_rate"] == 0.05
        assert "newrelic" in record.error_metrics["sources"]


class TestMatchConfidence:
    """Test match confidence tiers."""

    def test_no_match(self):
        assert MatchConfidence.NO_MATCH.value == "NO_MATCH"

    def test_low(self):
        assert MatchConfidence.LOW.value == "LOW"

    def test_probable(self):
        assert MatchConfidence.PROBABLE.value == "PROBABLE"

    def test_exact(self):
        assert MatchConfidence.EXACT.value == "EXACT"


class TestEvidenceBundle:
    """Test unified evidence model."""

    def test_create_bundle(self):
        bundle = EvidenceBundle(
            bundle_id="b-123",
            captured_at=datetime.utcnow(),
            sources=["newrelic", "datadog"],
            service_name="auth-service",
            error_rate=0.05,
            p99_latency_ms=250.0
        )
        assert len(bundle.sources) == 2
        assert bundle.error_rate == 0.05

    def test_bundle_with_service_map(self):
        nodes = [
            ServiceMapNode(
                service_name="user-db",
                downstream_of=["auth-service"],
                criticality="P1"
            ),
            ServiceMapNode(
                service_name="api-gateway",
                upstream_of=["auth-service"]
            )
        ]
        bundle = EvidenceBundle(
            bundle_id="b-456",
            captured_at=datetime.utcnow(),
            sources=["newrelic"],
            service_name="auth-service",
            service_map=nodes
        )
        assert len(bundle.service_map) == 2
        assert bundle.service_map[0].criticality == "P1"


class TestReviewQueue:
    """Test review queue model."""

    def test_create_review_item(self):
        now = datetime.utcnow()
        item = ReviewItem(
            review_id="r-123",
            rca_id="rca-456",
            jira_ticket_id="PROD-789",
            created_at=now,
            sla_deadline=now + timedelta(hours=24),
            generated_cases=[{"title": "Test case 1"}]
        )
        assert item.status == ReviewStatus.PENDING
        assert not item.is_overdue

    def test_overdue_review(self):
        past = datetime.utcnow() - timedelta(hours=25)
        item = ReviewItem(
            review_id="r-123",
            rca_id="rca-456",
            jira_ticket_id="PROD-789",
            created_at=past,
            sla_deadline=past + timedelta(hours=24)
        )
        assert item.is_overdue
