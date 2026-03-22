"""
RCA pipeline state machine models.

Tracks every stage of the root cause analysis pipeline from JIRA intake
through evidence capture, summarization, TestRail matching, test generation,
human review, and final close-out.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PipelineStage(str, Enum):
    INTAKE = "intake"
    EVIDENCE_CAPTURE = "evidence_capture"
    SUMMARIZATION = "summarization"
    TESTRAIL_MATCH = "testrail_match"
    TEST_GENERATION = "test_generation"
    REVIEW_PENDING = "review_pending"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    TESTRAIL_WRITE = "testrail_write"
    BLAST_RADIUS = "blast_radius"
    JIRA_CLOSE = "jira_close"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchConfidence(str, Enum):
    NO_MATCH = "NO_MATCH"       # < 50%
    LOW = "LOW"                 # 50-74%
    PROBABLE = "PROBABLE"       # 75-99%
    EXACT = "EXACT"             # 100%


class RCARecord(BaseModel):
    """Full pipeline state for a single root cause analysis."""
    rca_id: str
    jira_ticket_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    stage: PipelineStage = PipelineStage.INTAKE

    # Step 1: Intake
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    severity_escalated: bool = False
    service_name: Optional[str] = None

    # Step 2: Evidence
    evidence_bundle_id: Optional[str] = None
    stack_trace: Optional[str] = None
    error_metrics: Optional[Dict[str, Any]] = None

    # Step 3: Summarization
    ai_summary: Optional[str] = None
    root_cause: Optional[str] = None
    timeline: Optional[List[str]] = None

    # Step 4: TestRail Match
    testrail_match_confidence: Optional[str] = None
    matched_test_case_id: Optional[str] = None
    match_score: Optional[float] = None
    automation_covered: Optional[bool] = None
    automation_gap_reason: Optional[str] = None

    # Step 5: Test Generation
    generated_test_cases: Optional[List[Dict[str, Any]]] = None

    # Step 5b: Human Review
    reviewer_id: Optional[str] = None
    human_review_approved_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # Step 5c: TestRail Write
    testrail_created_case_ids: Optional[List[int]] = None
    testrail_verification_run_id: Optional[int] = None
    regression_run_id: Optional[int] = None

    # Step 6: Blast Radius
    impacted_components: Optional[List[str]] = None
    smoke_scope: Optional[List[int]] = None
    regression_scope: Optional[List[int]] = None

    # Step 7: Jira Close
    jira_closed: bool = False
    rca_artifact_url: Optional[str] = None
