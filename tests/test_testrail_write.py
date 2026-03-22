"""Tests for TestRail write operations and tiered matching."""

import pytest
from unittest.mock import patch, MagicMock
from mcp.tools.testrail_tool import (
    find_testrail_match, MatchResult,
    create_test_case, create_test_cases_bulk
)
from mcp.models.rca_models import MatchConfidence


class TestTieredMatching:
    """Test the 50/75/100% tiered matching logic."""

    @patch("mcp.tools.testrail_tool.get_all_cases")
    def test_no_match_below_50(self, mock_cases):
        mock_cases.return_value = [
            {"id": 1, "title": "Login page loads correctly", "custom_steps_separated": []}
        ]
        result = find_testrail_match("CDN buffer overflow in streaming pipeline", [])
        assert result.confidence == MatchConfidence.NO_MATCH.value
        assert result.score < 0.50
        assert result.matched_case_id is None

    @patch("mcp.tools.testrail_tool.get_all_cases")
    def test_exact_match_100(self, mock_cases):
        summary = "Auth service returns 500 on login"
        mock_cases.return_value = [
            {
                "id": 42,
                "title": "Auth service returns 500 on login",
                "custom_steps_separated": [],
                "custom_automation_type": 1
            }
        ]
        with patch("mcp.tools.testrail_tool.get_automation_status") as mock_auto:
            mock_auto.return_value = (True, None)
            result = find_testrail_match(summary, [])
            assert result.confidence == MatchConfidence.EXACT.value
            assert result.matched_case_id == "42"

    @patch("mcp.tools.testrail_tool.get_all_cases")
    def test_empty_cases_returns_no_match(self, mock_cases):
        mock_cases.return_value = []
        result = find_testrail_match("Any incident", ["step 1"])
        assert result.confidence == MatchConfidence.NO_MATCH.value
        assert result.score == 0.0


class TestTestRailWrite:
    """Test TestRail write operations."""

    @patch("mcp.tools.testrail_tool._tr")
    def test_create_test_case(self, mock_tr):
        mock_tr.return_value = {"id": 100, "title": "New test case"}
        case = {
            "title": "Verify auth fix",
            "type": "verification",
            "priority": "high",
            "preconditions": "Service deployed with fix",
            "steps": [
                {"action": "Send login request", "expected": "Returns 200"}
            ]
        }
        with patch("mcp.tools.testrail_tool.settings") as mock_settings:
            mock_settings.testrail_rca_section_id = 42
            mock_settings.testrail_url = "https://test.testrail.io"
            mock_settings.testrail_api_key = "key"
            mock_settings.testrail_email = "test@test.com"
            result = create_test_case(case, "PROD-123", section_id=42)
            assert result["id"] == 100

    @patch("mcp.tools.testrail_tool.create_test_case")
    def test_bulk_create(self, mock_create):
        mock_create.return_value = {"id": 100}
        cases = [
            {"title": "Case 1", "steps": []},
            {"title": "Case 2", "steps": []}
        ]
        result = create_test_cases_bulk(cases, "PROD-456", section_id=42)
        assert len(result) == 2
        assert mock_create.call_count == 2


class TestMatchResult:
    """Test MatchResult dataclass."""

    def test_no_match_result(self):
        result = MatchResult(
            confidence="NO_MATCH",
            score=0.3,
            matched_case_id=None,
            matched_case_title=None,
            automation_covered=None,
            automation_gap_reason=None,
            requires_human_review=False,
            suggested_to_engineer=False
        )
        assert result.confidence == "NO_MATCH"
        assert result.score == 0.3

    def test_probable_result(self):
        result = MatchResult(
            confidence="PROBABLE",
            score=0.85,
            matched_case_id="42",
            matched_case_title="Existing test",
            automation_covered=None,
            automation_gap_reason=None,
            requires_human_review=False,
            suggested_to_engineer=True
        )
        assert result.suggested_to_engineer is True
