"""
RCA pipeline state machine models.

Tracks every stage of the root cause analysis pipeline from JIRA intake
through evidence capture, summarization, TestRail matching, test generation,
human review, and final close-out.

Includes:
- Idempotency support via jira_ticket_id + stage
- Cryptographic integrity via SHA-256 hash
- Cycle time tracking for SLA metrics
- Retry/resume support via last_failed_stage
- fix_verified requirement before Jira close
- remediation_owners with due dates
"""

import hashlib
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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
    VERIFICATION_PENDING = "verification_pending"  # NEW: Waiting for regression run
    VERIFICATION_COMPLETE = "verification_complete"  # NEW: Regression passed
    BLAST_RADIUS = "blast_radius"
    JIRA_CLOSE = "jira_close"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchConfidence(str, Enum):
    NO_MATCH = "NO_MATCH"       # < 50%
    LOW = "LOW"                 # 50-74%
    PROBABLE = "PROBABLE"       # 75-99%
    EXACT = "EXACT"             # 100%


class RemediationAction(BaseModel):
    """A remediation action with owner and due date - required for Jira close."""
    action: str = Field(..., description="Description of the remediation action")
    owner: str = Field(..., description="Person/team responsible for this action")
    due_date: datetime = Field(..., description="Due date for completion")
    completed: bool = Field(default=False, description="Whether action is complete")
    completed_at: Optional[datetime] = Field(default=None, description="When action was completed")
    jira_subtask_id: Optional[str] = Field(default=None, description="Linked Jira subtask if created")


class VerificationResult(BaseModel):
    """Result of post-deployment verification run."""
    run_id: int = Field(..., description="TestRail run ID")
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    total_cases: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    blocked: int = Field(default=0)
    untested: int = Field(default=0)
    pass_rate: float = Field(default=0.0)
    all_passed: bool = Field(default=False)
    failed_case_ids: List[int] = Field(default_factory=list)
    mini_rca_triggered: bool = Field(default=False, description="If failures triggered a mini-RCA")


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
    summary_prompt_version: str = "1.0"  # Track prompt version for compatibility

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

    # Step 6b: Verification (post-deployment)
    fix_verified: bool = False  # REQUIRED before Jira close
    verification_result: Optional[VerificationResult] = None
    verification_attempts: int = 0
    max_verification_attempts: int = 3

    # Step 7: Jira Close - Required Fields
    jira_closed: bool = False
    rca_artifact_url: Optional[str] = None
    closed_at: Optional[datetime] = None
    remediation_owners: List[RemediationAction] = []  # REQUIRED: at least 1 action with owner/due date

    # Retry/Resume Support
    last_failed_stage: Optional[PipelineStage] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Integrity & Audit
    artifact_hash: Optional[str] = None  # SHA-256 of artifact at close
    
    # Cycle Time Metrics (for SLA tracking)
    stage_timestamps: Dict[str, str] = {}  # stage -> ISO timestamp
    
    def compute_artifact_hash(self) -> str:
        """
        Compute SHA-256 hash of the RCA artifact for tamper evidence.
        Call this before closing the Jira ticket.
        """
        artifact_data = {
            "rca_id": self.rca_id,
            "jira_ticket_id": self.jira_ticket_id,
            "ai_summary": self.ai_summary,
            "testrail_match_confidence": self.testrail_match_confidence,
            "matched_test_case_id": self.matched_test_case_id,
            "testrail_created_case_ids": self.testrail_created_case_ids,
            "impacted_components": self.impacted_components,
            "reviewer_id": self.reviewer_id,
            "human_review_approved_at": self.human_review_approved_at.isoformat() if self.human_review_approved_at else None,
        }
        
        json_str = json.dumps(artifact_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_artifact_integrity(self) -> bool:
        """Verify the artifact hasn't been tampered with since close."""
        if not self.artifact_hash:
            return True  # No hash stored yet
        return self.compute_artifact_hash() == self.artifact_hash
    
    def record_stage_timestamp(self, stage: PipelineStage):
        """Record when a stage was entered for cycle time tracking."""
        self.stage_timestamps[stage.value] = datetime.utcnow().isoformat()
    
    @property
    def cycle_time_hours(self) -> Optional[float]:
        """Total pipeline cycle time in hours (created to completed/failed)."""
        if self.stage not in (PipelineStage.COMPLETED, PipelineStage.FAILED):
            return None
        if not self.updated_at:
            return None
        delta = self.updated_at - self.created_at
        return round(delta.total_seconds() / 3600, 2)
    
    @property
    def time_to_review_hours(self) -> Optional[float]:
        """Time from created to review_pending in hours."""
        if PipelineStage.REVIEW_PENDING.value not in self.stage_timestamps:
            return None
        review_time = datetime.fromisoformat(self.stage_timestamps[PipelineStage.REVIEW_PENDING.value])
        delta = review_time - self.created_at
        return round(delta.total_seconds() / 3600, 2)
    
    @property
    def review_wait_hours(self) -> Optional[float]:
        """Time spent waiting for human review in hours."""
        if not self.human_review_approved_at:
            return None
        if PipelineStage.REVIEW_PENDING.value not in self.stage_timestamps:
            return None
        review_pending_time = datetime.fromisoformat(self.stage_timestamps[PipelineStage.REVIEW_PENDING.value])
        delta = self.human_review_approved_at - review_pending_time
        return round(delta.total_seconds() / 3600, 2)
    
    def can_retry(self) -> bool:
        """Check if this RCA can be retried."""
        return self.stage == PipelineStage.FAILED and self.retry_count < self.max_retries
    
    def validate_artifact(self) -> tuple[bool, List[str]]:
        """
        Validate that all required fields are present before Jira close.
        Returns (is_valid, list_of_missing_fields).
        
        Required fields per spec:
        - root_cause: AI summary identifying the root cause
        - timeline: List of events leading to the incident
        - fix_verified: Evidence that regression cases passed
        - remediation_owners: At least one action with owner and due date
        """
        missing = []
        
        # Root cause is required
        if not self.ai_summary and not self.root_cause:
            missing.append("root_cause (ai_summary)")
        
        # Timeline is required (can be derived from stage_timestamps if not explicit)
        if not self.timeline and not self.stage_timestamps:
            missing.append("timeline")
        
        # fix_verified must be True (evidence-based, not assumed)
        if not self.fix_verified:
            missing.append("fix_verified (regression run must pass)")
        
        # At least one remediation action with owner and due date
        if not self.remediation_owners:
            missing.append("remediation_owners (at least one action with owner/due_date)")
        else:
            # Validate each action has required fields
            for i, action in enumerate(self.remediation_owners):
                if not action.owner:
                    missing.append(f"remediation_owners[{i}].owner")
                if not action.due_date:
                    missing.append(f"remediation_owners[{i}].due_date")
        
        return (len(missing) == 0, missing)
    
    def can_close_jira(self) -> tuple[bool, str]:
        """
        Check if this RCA is ready to close the Jira ticket.
        Returns (can_close, reason_if_not).
        """
        is_valid, missing = self.validate_artifact()
        
        if not is_valid:
            return (False, f"Missing required fields: {', '.join(missing)}")
        
        # Must have verification result if test cases were generated
        if self.generated_test_cases and not self.verification_result:
            return (False, "Verification run not yet complete - cannot close until test cases pass")
        
        if self.verification_result and not self.verification_result.all_passed:
            return (False, f"Verification run has {self.verification_result.failed} failed cases - fix required before close")
        
        return (True, "Ready to close")
    
    def add_remediation_action(
        self,
        action: str,
        owner: str,
        due_days: int = 7
    ) -> RemediationAction:
        """Helper to add a remediation action with calculated due date."""
        remediation = RemediationAction(
            action=action,
            owner=owner,
            due_date=datetime.utcnow() + timedelta(days=due_days)
        )
        self.remediation_owners.append(remediation)
        return remediation
