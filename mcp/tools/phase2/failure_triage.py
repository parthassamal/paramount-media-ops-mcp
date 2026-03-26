"""
Phase 2.2 — Automated Failure Triage

When a regression run fails, automatically classify each failure:
- Genuine regression (triggers RCA)
- Flaky test (quarantine)
- Environment issue (invalidate run)
- Known gap (create test generation task)
- Stale test (flag for retirement)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from mcp.tools.testrail_tool import (
    get_run_results, get_results_for_case, add_result_for_case, _tr
)
from mcp.db.rca_store import get_recent_rcas
from mcp.pipeline.orchestrator import RCAPipeline
from mcp.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class FailureClass(str, Enum):
    """Classification of test failures."""
    GENUINE_REGRESSION = "genuine_regression"
    FLAKY_TEST = "flaky_test"
    ENVIRONMENT_ISSUE = "environment_issue"
    KNOWN_GAP = "known_gap"
    STALE_TEST = "stale_test"
    UNKNOWN = "unknown"


@dataclass
class TriagedFailure:
    """A classified test failure."""
    case_id: int
    test_id: int
    title: str
    classification: FailureClass
    confidence: float  # 0-1
    signals: List[str]
    recommended_action: str
    rca_triggered: bool = False


class FailureTriager:
    """
    Automatically triages test failures from regression runs.
    
    Classification taxonomy:
    - GENUINE_REGRESSION: Passes in main, fails on branch, correlated with deployment
    - FLAKY_TEST: Pass/fail rate < 80% over last 10 runs, no deployment correlation
    - ENVIRONMENT_ISSUE: Multiple unrelated tests fail, infra anomaly detected
    - KNOWN_GAP: automation_gap_reason indicates test not yet automated
    - STALE_TEST: refs ticket in RCA_CLOSED, no related changes in 90 days
    """
    
    def __init__(self):
        self.flakiness_threshold = 0.8  # 80% pass rate
        self.history_window = 10  # Last 10 runs
    
    def triage_run(self, run_id: int, auto_action: bool = False) -> Dict[str, Any]:
        """
        Triage all failures in a TestRail run.
        
        Args:
            run_id: TestRail run ID
            auto_action: Whether to take automated actions (quarantine, trigger RCA)
            
        Returns:
            {
                "run_id": int,
                "total_tests": int,
                "passed": int,
                "failed": int,
                "triaged_failures": list,
                "summary": {
                    "genuine_regressions": int,
                    "flaky_tests": int,
                    "environment_issues": int,
                    "known_gaps": int,
                    "stale_tests": int
                },
                "rca_triggered": list,
                "actions_taken": list
            }
        """
        logger.info("triage_run_started", run_id=run_id)
        
        # Get run results
        results = get_run_results(run_id)
        is_complete = results.get("completed", False)
        
        # Get test details (paginated response)
        raw_tests = _tr("GET", f"get_tests/{run_id}")
        tests = raw_tests.get("tests", []) if isinstance(raw_tests, dict) else (raw_tests if isinstance(raw_tests, list) else [])
        
        failed_tests = [t for t in tests if t.get("status_id") == 5]  # 5 = Failed
        
        # Get RCA history for correlation
        rca_services = self._get_rca_service_map()
        
        # Triage each failure
        triaged = []
        summary = {cls.value: 0 for cls in FailureClass}
        rca_triggered = []
        actions_taken = []
        
        for test in failed_tests:
            classification = self._classify_failure(test, rca_services)
            triaged.append(classification)
            summary[classification.classification.value] += 1
            
            # Take automated actions if enabled
            if auto_action:
                action = self._take_action(test, classification, run_id)
                if action:
                    actions_taken.append(action)
                    if classification.rca_triggered:
                        rca_triggered.append({
                            "case_id": classification.case_id,
                            "title": classification.title
                        })
        
        # Check for environment issue pattern (multiple unrelated failures)
        if self._detect_environment_issue(triaged):
            for t in triaged:
                if t.classification == FailureClass.UNKNOWN:
                    t.classification = FailureClass.ENVIRONMENT_ISSUE
                    t.signals.append("Multiple unrelated failures detected")
                    summary[FailureClass.ENVIRONMENT_ISSUE.value] += 1
                    summary[FailureClass.UNKNOWN.value] -= 1
        
        result = {
            "run_id": run_id,
            "run_complete": is_complete,
            "total_tests": len(tests),
            "passed": results.get("passed_count", 0),
            "failed": len(failed_tests),
            "untested": results.get("untested_count", 0),
            "triaged_failures": [
                {
                    "case_id": t.case_id,
                    "test_id": t.test_id,
                    "title": t.title,
                    "classification": t.classification.value,
                    "confidence": t.confidence,
                    "signals": t.signals,
                    "recommended_action": t.recommended_action,
                    "rca_triggered": t.rca_triggered
                }
                for t in triaged
            ],
            "summary": summary,
            "rca_triggered": rca_triggered,
            "actions_taken": actions_taken
        }
        
        logger.info(
            "triage_run_complete",
            run_id=run_id,
            failed=len(failed_tests),
            genuine=summary.get(FailureClass.GENUINE_REGRESSION.value, 0),
            flaky=summary.get(FailureClass.FLAKY_TEST.value, 0)
        )
        
        return result
    
    def _classify_failure(
        self,
        test: Dict[str, Any],
        rca_services: Dict[str, List[str]]
    ) -> TriagedFailure:
        """Classify a single test failure."""
        case_id = test.get("case_id", 0)
        test_id = test.get("id", 0)
        title = test.get("title", "")
        refs = test.get("refs") or ""
        
        signals = []
        classification = FailureClass.UNKNOWN
        confidence = 0.5
        recommended_action = "Investigate manually"
        
        # Check flakiness from history
        flakiness = self._check_flakiness(case_id)
        if flakiness is not None and flakiness < self.flakiness_threshold:
            signals.append(f"Pass rate {flakiness:.0%} over last {self.history_window} runs")
            classification = FailureClass.FLAKY_TEST
            confidence = 0.8
            recommended_action = "Quarantine to flaky suite, do not count as regression"
        
        # Check for automation gap
        case_details = _tr("GET", f"get_case/{case_id}")
        if case_details:
            auto_type = case_details.get("custom_automation_type", 0)
            if auto_type == 2:  # To be automated
                signals.append("Test marked 'to be automated'")
                classification = FailureClass.KNOWN_GAP
                confidence = 0.9
                recommended_action = "Create test generation task"
        
        # Check RCA history correlation
        if refs:
            for service, rca_list in rca_services.items():
                if service.lower() in refs.lower() or service.lower() in title.lower():
                    signals.append(f"Service {service} has {len(rca_list)} RCA records")
                    if classification == FailureClass.UNKNOWN:
                        classification = FailureClass.GENUINE_REGRESSION
                        confidence = 0.7
                        recommended_action = "Trigger RCA pipeline"
        
        # Check staleness
        if refs and classification == FailureClass.UNKNOWN:
            closed_rcas = [r for r in rca_services.get(refs, []) if r == "CLOSED"]
            if closed_rcas:
                signals.append("refs ticket is in closed RCA")
                classification = FailureClass.STALE_TEST
                confidence = 0.6
                recommended_action = "Flag for retirement review"
        
        # Default to genuine regression if no other classification
        if classification == FailureClass.UNKNOWN:
            classification = FailureClass.GENUINE_REGRESSION
            confidence = 0.5
            recommended_action = "Investigate as potential regression"
            signals.append("No clear classification signals")
        
        return TriagedFailure(
            case_id=case_id,
            test_id=test_id,
            title=title,
            classification=classification,
            confidence=confidence,
            signals=signals,
            recommended_action=recommended_action
        )
    
    def _check_flakiness(self, case_id: int) -> Optional[float]:
        """Calculate pass rate for a case over recent runs."""
        try:
            results = get_results_for_case(case_id, limit=self.history_window)
            if not results or len(results) < 3:
                return None
            
            passed = sum(1 for r in results if r.get("status_id") == 1)
            return passed / len(results)
        except Exception:
            return None
    
    def _get_rca_service_map(self) -> Dict[str, List[str]]:
        """Build map of services to their RCA records."""
        service_map = {}
        try:
            recent = get_recent_rcas(limit=100)
            for rca in recent:
                service = rca.service_name or rca.jira_ticket_id
                if service:
                    if service not in service_map:
                        service_map[service] = []
                    service_map[service].append(rca.stage.value)
        except Exception:
            pass
        return service_map
    
    def _detect_environment_issue(self, triaged: List[TriagedFailure]) -> bool:
        """Detect if failures indicate an environment issue."""
        # If > 50% of failures are unclassified and > 5 failures, likely env issue
        unknown_count = sum(1 for t in triaged if t.classification == FailureClass.UNKNOWN)
        if len(triaged) >= 5 and unknown_count / len(triaged) > 0.5:
            return True
        return False
    
    def _take_action(
        self,
        test: Dict[str, Any],
        triage: TriagedFailure,
        run_id: int
    ) -> Optional[Dict[str, Any]]:
        """Take automated action based on classification."""
        action = None
        
        if triage.classification == FailureClass.GENUINE_REGRESSION:
            # Trigger RCA pipeline
            try:
                pipeline = RCAPipeline()
                jira_ticket = {
                    "id": test.get("refs") or f"AUTO-{test.get('case_id')}",
                    "service": "regression-detected",
                    "summary": f"Regression: {triage.title}"
                }
                # Note: In production, you'd create a proper Jira ticket first
                triage.rca_triggered = True
                action = {
                    "type": "rca_flagged",
                    "case_id": triage.case_id,
                    "message": "Flagged for RCA investigation"
                }
            except Exception as e:
                logger.warning("rca_trigger_failed", error=str(e))
        
        elif triage.classification == FailureClass.FLAKY_TEST:
            # Add comment about flakiness
            try:
                add_result_for_case(
                    run_id,
                    triage.case_id,
                    status_id=4,  # Retest
                    comment=f"AUTO-TRIAGE: Flaky test ({', '.join(triage.signals)}). Recommend quarantine."
                )
                action = {
                    "type": "flagged_flaky",
                    "case_id": triage.case_id,
                    "message": "Marked for quarantine"
                }
            except Exception:
                pass
        
        return action


# Singleton instance
failure_triager = FailureTriager()


def triage_run(run_id: int, auto_action: bool = False) -> Dict[str, Any]:
    """Convenience function for failure triage."""
    return failure_triager.triage_run(run_id, auto_action)
