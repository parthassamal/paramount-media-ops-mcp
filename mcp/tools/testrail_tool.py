"""
TestRail integration with full READ + WRITE path.

v2 Capabilities:
- READ: Fetch cases, suites, sections for tiered matching
- WRITE: Create test cases from AI output, map to suite/section, set refs to Jira
- WRITE: Create verification runs, append to regression runs
- Tiered matching at 50/75/100% thresholds
"""

import time
import requests
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from difflib import SequenceMatcher

from config import settings
from mcp.models.rca_models import MatchConfidence
from mcp.utils.logger import get_logger
from mcp.utils.error_handler import (
    ConnectionError, RateLimitError, ServiceError,
    retry_with_backoff
)

logger = get_logger(__name__)


# =============================================================================
# TestRail API Client
# =============================================================================

def _tr(method: str, endpoint: str, payload: dict = None) -> dict:
    """
    TestRail API v2 client with basic auth and rate limit handling.
    """
    if not settings.testrail_url or not settings.testrail_api_key:
        logger.warning("TestRail not configured")
        return {}

    url = f"{settings.testrail_url}/index.php?/api/v2/{endpoint}"
    auth = (settings.testrail_email, settings.testrail_api_key)
    headers = {"Content-Type": "application/json"}

    for attempt in range(3):
        try:
            if method == "GET":
                resp = requests.get(url, auth=auth, headers=headers, timeout=15)
            else:
                resp = requests.post(url, auth=auth, headers=headers, json=payload, timeout=15)

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                logger.warning("TestRail rate limit hit", retry_after=retry_after)
                time.sleep(retry_after)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to TestRail: {e}", service="testrail") from e
        except requests.Timeout as e:
            raise ConnectionError(f"TestRail request timed out: {e}", service="testrail") from e

    raise ServiceError("TestRail API failed after retries", service="testrail")


# =============================================================================
# READ Operations
# =============================================================================

def get_all_cases(suite_id: int = None) -> List[dict]:
    """Fetch all test cases with pagination (max 250 per page)."""
    suite_id = suite_id or settings.testrail_default_suite_id
    if not suite_id:
        return []

    cases = []
    offset = 0
    while True:
        endpoint = f"get_cases/{settings.testrail_project_id}&suite_id={suite_id}&limit=250&offset={offset}"
        page = _tr("GET", endpoint)
        batch = page.get("cases", []) if isinstance(page, dict) else []
        cases.extend(batch)
        if len(batch) < 250:
            break
        offset += 250

    logger.info("Fetched TestRail cases", suite_id=suite_id, count=len(cases))
    return cases


def get_suites() -> List[dict]:
    """Get all test suites for the project."""
    result = _tr("GET", f"get_suites/{settings.testrail_project_id}")
    return result if isinstance(result, list) else result.get("suites", [])


def get_sections(suite_id: int) -> List[dict]:
    """Get sections within a suite."""
    endpoint = f"get_sections/{settings.testrail_project_id}&suite_id={suite_id}"
    result = _tr("GET", endpoint)
    return result if isinstance(result, list) else result.get("sections", [])


def get_automation_status(case_id: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a test case is automated.
    custom_automation_type: 0=None, 1=Automated, 2=To be automated.
    """
    case = _tr("GET", f"get_case/{case_id}")
    if not case:
        return False, "case_not_found"

    auto_type = case.get("custom_automation_type", 0)
    if auto_type == 0:
        return False, "test_not_yet_automated"
    if auto_type == 2:
        return False, "marked_to_be_automated"
    return True, None


# =============================================================================
# WRITE Operations
# =============================================================================

def create_test_case(
    generated_case: dict,
    jira_ticket_id: str,
    section_id: int = None
) -> dict:
    """
    Write a single AI-generated test case into TestRail.
    Maps generated fields to TestRail's add_case API payload.
    """
    section_id = section_id or settings.testrail_rca_section_id
    if not section_id:
        raise ServiceError("TestRail RCA section ID not configured", service="testrail")

    priority_map = {"high": 1, "medium": 2, "low": 3}
    priority_id = priority_map.get(generated_case.get("priority", "medium").lower(), 2)

    type_map = {"smoke": 5, "regression": 4, "verification": 1}
    type_id = type_map.get(generated_case.get("type", "regression").lower(), 4)

    steps = [
        {"content": s["action"], "expected": s["expected"]}
        for s in generated_case.get("steps", [])
    ]

    payload = {
        "title": generated_case["title"],
        "template_id": 2,  # Step-by-step format
        "type_id": type_id,
        "priority_id": priority_id,
        "refs": jira_ticket_id,
        "custom_preconds": generated_case.get("preconditions", ""),
        "custom_steps_separated": steps,
        "custom_expected": steps[-1]["expected"] if steps else "",
        "custom_automation_type": 2  # To be automated
    }

    new_case = _tr("POST", f"add_case/{section_id}", payload)
    logger.info("TestRail case created", case_id=new_case.get("id"), jira=jira_ticket_id)
    return new_case


def create_test_cases_bulk(
    approved_cases: List[dict],
    jira_ticket_id: str,
    section_id: int = None
) -> List[dict]:
    """Write all human-approved AI-generated test cases into TestRail."""
    created = []
    for case in approved_cases:
        new_case = create_test_case(case, jira_ticket_id, section_id)
        created.append(new_case)
        time.sleep(0.2)  # Respect rate limits
    logger.info("Bulk TestRail write complete", count=len(created), jira=jira_ticket_id)
    return created


def add_cases_to_regression_run(run_id: int, new_case_ids: List[int]) -> dict:
    """Append newly created cases to an existing regression test run."""
    run = _tr("GET", f"get_run/{run_id}")
    existing_ids = run.get("case_ids", [])
    if run.get("include_all", False):
        existing_ids = [c["id"] for c in get_all_cases(run.get("suite_id"))]

    merged_ids = list(set(existing_ids + new_case_ids))
    result = _tr("POST", f"update_run/{run_id}", {
        "include_all": False,
        "case_ids": merged_ids
    })
    logger.info("Cases appended to regression run", run_id=run_id, added=len(new_case_ids))
    return result


def create_rca_verification_run(
    rca_id: str,
    jira_ticket_id: str,
    case_ids: List[int],
    suite_id: int = None
) -> dict:
    """Create a dedicated verification run for the RCA fix."""
    suite_id = suite_id or settings.testrail_default_suite_id
    result = _tr("POST", f"add_run/{settings.testrail_project_id}", {
        "suite_id": suite_id,
        "name": f"RCA Verification: {jira_ticket_id} [{rca_id[:8]}]",
        "description": f"Auto-generated verification run for {jira_ticket_id}. RCA: {rca_id}",
        "refs": jira_ticket_id,
        "include_all": False,
        "case_ids": case_ids
    })
    logger.info("Verification run created", run_id=result.get("id"), jira=jira_ticket_id)
    return result


def get_run_results(run_id: int) -> Dict[str, Any]:
    """
    Get results for a test run - used for post-deployment verification.
    
    Returns:
        {
            "completed": bool,
            "total": int,
            "passed_count": int,
            "failed_count": int,
            "blocked_count": int,
            "untested_count": int,
            "pass_rate": float,
            "all_passed": bool,
            "failed_case_ids": list[int]
        }
    """
    run = _tr("GET", f"get_run/{run_id}")
    if not run:
        return {"completed": False, "total": 0, "all_passed": False}
    
    # Get test results for this run
    tests = _tr("GET", f"get_tests/{run_id}")
    if not tests:
        tests = []
    
    # TestRail status IDs: 1=Passed, 2=Blocked, 3=Untested, 4=Retest, 5=Failed
    passed = 0
    failed = 0
    blocked = 0
    untested = 0
    failed_case_ids = []
    
    for test in tests:
        status = test.get("status_id")
        if status == 1:
            passed += 1
        elif status == 5:
            failed += 1
            failed_case_ids.append(test.get("case_id"))
        elif status == 2:
            blocked += 1
        else:  # 3 (untested) or 4 (retest) or None
            untested += 1
    
    total = len(tests)
    completed = run.get("is_completed", False) or (untested == 0 and total > 0)
    pass_rate = (passed / total * 100) if total > 0 else 0.0
    all_passed = (passed == total) and (total > 0) and (failed == 0) and (blocked == 0)
    
    return {
        "completed": completed,
        "total": total,
        "passed_count": passed,
        "failed_count": failed,
        "blocked_count": blocked,
        "untested_count": untested,
        "pass_rate": round(pass_rate, 2),
        "all_passed": all_passed,
        "failed_case_ids": failed_case_ids
    }


def get_results_for_case(case_id: int, run_id: int = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get result history for a specific test case."""
    if run_id:
        endpoint = f"get_results_for_case/{run_id}/{case_id}"
    else:
        endpoint = f"get_results/{case_id}&limit={limit}"
    
    results = _tr("GET", endpoint)
    return results if isinstance(results, list) else results.get("results", [])


def add_result_for_case(run_id: int, case_id: int, status_id: int, comment: str = "") -> Dict[str, Any]:
    """
    Add a result to a test case in a run.
    
    Status IDs: 1=Passed, 2=Blocked, 3=Untested, 4=Retest, 5=Failed
    """
    return _tr("POST", f"add_result_for_case/{run_id}/{case_id}", {
        "status_id": status_id,
        "comment": comment
    })


# =============================================================================
# Tiered Matching (50 / 75 / 100% thresholds)
# =============================================================================

@dataclass
class MatchResult:
    confidence: str
    score: float
    matched_case_id: Optional[str]
    matched_case_title: Optional[str]
    automation_covered: Optional[bool]
    automation_gap_reason: Optional[str]
    requires_human_review: bool
    suggested_to_engineer: bool


def find_testrail_match(
    incident_summary: str,
    incident_steps: List[str]
) -> MatchResult:
    """
    Tiered matching with explicit action per score band:
    - < 50%:   NO_MATCH -> generate new test cases
    - 50-74%:  LOW -> generate + flag for review
    - 75-99%:  PROBABLE -> auto-suggest to engineer
    - 100%:    EXACT -> check automation coverage
    """
    all_cases = get_all_cases()
    best_score = 0.0
    best_case = None

    for case in all_cases:
        title_score = SequenceMatcher(
            None,
            incident_summary.lower(),
            case.get("title", "").lower()
        ).ratio()

        steps_text = " ".join([
            s.get("content", "")
            for s in case.get("custom_steps_separated", [])
        ])
        incident_text = " ".join(incident_steps)
        step_score = SequenceMatcher(
            None, incident_text.lower(), steps_text.lower()
        ).ratio() if steps_text else 0.0

        combined = (title_score * 0.4) + (step_score * 0.6)

        if combined > best_score:
            best_score = combined
            best_case = case

    if best_score < 0.50:
        return MatchResult(
            MatchConfidence.NO_MATCH.value, best_score,
            None, None, None, None, False, False
        )
    elif best_score < 0.75:
        return MatchResult(
            MatchConfidence.LOW.value, best_score,
            str(best_case["id"]), best_case["title"],
            None, None, True, False
        )
    elif best_score < 1.0:
        return MatchResult(
            MatchConfidence.PROBABLE.value, best_score,
            str(best_case["id"]), best_case["title"],
            None, None, False, True
        )
    else:
        automated, gap = get_automation_status(str(best_case["id"]))
        return MatchResult(
            MatchConfidence.EXACT.value, best_score,
            str(best_case["id"]), best_case["title"],
            automated, gap, not automated, False
        )
