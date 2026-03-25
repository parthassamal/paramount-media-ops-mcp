"""
End-to-end test for the 7-step RCA pipeline with mocked external APIs.

Verifies the full flow: intake -> evidence -> summarize -> match ->
generate -> blast radius -> Jira close.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from mcp.models.rca_models import PipelineStage


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Provide minimal settings for the pipeline."""
    monkeypatch.setenv("MOCK_MODE", "true")
    monkeypatch.setenv("JIRA_API_URL", "https://fake.atlassian.net")
    monkeypatch.setenv("JIRA_API_EMAIL", "test@test.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "fake-token")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "PROD")
    monkeypatch.setenv("TESTRAIL_URL", "https://fake.testrail.io")
    monkeypatch.setenv("TESTRAIL_EMAIL", "test@test.com")
    monkeypatch.setenv("TESTRAIL_API_KEY", "fake-key")
    monkeypatch.setenv("TESTRAIL_PROJECT_ID", "1")
    monkeypatch.setenv("TESTRAIL_DEFAULT_SUITE_ID", "1")
    monkeypatch.setenv("TESTRAIL_RCA_SECTION_ID", "1")
    monkeypatch.setenv("NEWRELIC_API_KEY", "NRAK-fake")
    monkeypatch.setenv("NEWRELIC_ACCOUNT_ID", "123456")
    monkeypatch.setenv("OBSERVABILITY_SOURCE", "newrelic")


@patch("mcp.pipeline.orchestrator.capture_newrelic_snapshot")
@patch("mcp.pipeline.orchestrator.capture_datadog_snapshot")
@patch("mcp.pipeline.orchestrator.normalize_evidence")
@patch("mcp.pipeline.orchestrator.find_testrail_match")
@patch("mcp.pipeline.orchestrator.create_test_cases_bulk")
@patch("mcp.pipeline.orchestrator.create_rca_verification_run")
@patch("mcp.pipeline.orchestrator.add_cases_to_regression_run")
@patch("mcp.pipeline.orchestrator.upsert_rca")
@patch("mcp.pipeline.orchestrator.check_for_duplicates")
@patch("mcp.pipeline.orchestrator.create_review_item")
def test_full_pipeline_run(
    mock_create_review,
    mock_check_dup,
    mock_upsert,
    mock_add_regression,
    mock_verification_run,
    mock_create_cases,
    mock_find_match,
    mock_normalize,
    mock_dd_snapshot,
    mock_nr_snapshot,
):
    """Pipeline completes all 7 steps and reaches COMPLETED stage."""
    from mcp.pipeline.orchestrator import RCAPipelineOrchestrator
    from mcp.models.evidence_models import EvidenceBundle

    mock_check_dup.return_value = None
    mock_nr_snapshot.return_value = {
        "error_rate": 5.2,
        "response_time_ms": 1200,
        "sources": ["newrelic"],
    }
    mock_dd_snapshot.return_value = {}
    mock_normalize.return_value = EvidenceBundle(
        bundle_id="test-bundle",
        captured_at=datetime.utcnow(),
        sources=["newrelic"],
        service_name="streaming-api",
        stack_trace="java.lang.NullPointerException at StreamHandler.process",
        error_rate=5.2,
        response_time_ms=1200,
    )
    mock_find_match.return_value = {
        "confidence": "high",
        "score": 0.82,
        "matched_case_id": "C100",
    }
    mock_create_cases.return_value = ["C200", "C201"]
    mock_verification_run.return_value = 42
    mock_add_regression.return_value = True

    orchestrator = RCAPipelineOrchestrator()
    record = orchestrator.run(
        jira_ticket_id="PROD-999",
        summary="P1 - Streaming API 500 errors spike",
        description="Users report 500 errors on video playback since 2AM UTC.",
        service_name="streaming-api",
        stack_trace="java.lang.NullPointerException at StreamHandler.process",
    )

    assert record is not None
    assert record.stage == PipelineStage.COMPLETED
    assert record.jira_closed is True
    assert record.ai_summary is not None
    assert record.rca_artifact_url is not None

    mock_upsert.assert_called()
    assert mock_upsert.call_count >= 4


@patch("mcp.pipeline.orchestrator.check_for_duplicates")
@patch("mcp.pipeline.orchestrator.upsert_rca")
def test_duplicate_detection_skips_pipeline(mock_upsert, mock_check_dup):
    """Pipeline detects duplicate and returns existing record."""
    from mcp.pipeline.orchestrator import RCAPipelineOrchestrator
    from mcp.models.rca_models import RCARecord

    existing = RCARecord(
        rca_id="existing-123",
        jira_ticket_id="PROD-100",
        summary="Same issue",
        stage=PipelineStage.COMPLETED,
    )
    mock_check_dup.return_value = existing

    orchestrator = RCAPipelineOrchestrator()
    record = orchestrator.run(
        jira_ticket_id="PROD-101",
        summary="Same issue again",
    )

    assert record.rca_id == "existing-123"
