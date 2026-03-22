"""Tests for the evidence normalizer -- dual-source merging into EvidenceBundle."""

import pytest
from mcp.tools.evidence_normalizer import normalize_evidence


class TestNormalizeEvidence:
    """Test evidence normalization from New Relic and Datadog sources."""

    def test_newrelic_only(self):
        nr = {
            "source": "newrelic",
            "entity_guid": "abc123",
            "apm": {
                "actor": {
                    "entity": {
                        "apmSummary": {
                            "errorRate": 0.05,
                            "responseTimeAverage": 250.0
                        }
                    }
                }
            },
            "incidents": {},
            "service_map": {"actor": {"entity": {"relatedEntities": {"results": []}}}},
            "stack_trace": "NullPointerException at line 42"
        }
        bundle = normalize_evidence("auth-service", nr_snapshot=nr)
        assert bundle.sources == ["newrelic"]
        assert bundle.error_rate == 0.05
        assert bundle.p99_latency_ms == 250.0
        assert bundle.stack_trace == "NullPointerException at line 42"
        assert bundle.service_name == "auth-service"

    def test_datadog_only(self):
        dd = {
            "source": "datadog",
            "incidents": [{"title": "Auth service 500 spike", "severity": "SEV-1"}],
            "triggered_monitors": [{"name": "/api/login", "state": "Alert"}],
            "error_logs": [
                {"message": "Connection refused to user-db"},
                {"message": "Timeout waiting for response"}
            ]
        }
        bundle = normalize_evidence("auth-service", dd_snapshot=dd)
        assert bundle.sources == ["datadog"]
        assert bundle.error_message == "Auth service 500 spike"
        assert "/api/login" in bundle.affected_endpoints
        assert len(bundle.log_lines) == 2

    def test_both_sources_merged(self):
        nr = {
            "source": "newrelic",
            "apm": {
                "actor": {
                    "entity": {
                        "apmSummary": {"errorRate": 0.08, "responseTimeAverage": 500.0}
                    }
                }
            },
            "service_map": {
                "actor": {
                    "entity": {
                        "relatedEntities": {
                            "results": [
                                {"target": {"entity": {"name": "user-db"}}, "type": "CALLS"},
                                {"target": {"entity": {"name": "api-gateway"}}, "type": "CALLED_BY"}
                            ]
                        }
                    }
                }
            },
            "stack_trace": "NR stack trace"
        }
        dd = {
            "source": "datadog",
            "incidents": [{"title": "Critical outage"}],
            "triggered_monitors": [{"name": "/health", "state": "Alert"}],
            "error_logs": [{"message": "DD error log"}]
        }
        bundle = normalize_evidence("streaming-service", nr, dd)
        assert "newrelic" in bundle.sources
        assert "datadog" in bundle.sources
        assert bundle.error_rate == 0.08
        assert bundle.stack_trace == "NR stack trace"  # NR preferred
        assert bundle.error_message == "Critical outage"
        assert len(bundle.service_map) == 2
        assert "/health" in bundle.affected_endpoints

    def test_empty_sources(self):
        bundle = normalize_evidence("test-service")
        assert bundle.sources == []
        assert bundle.error_rate is None
        assert bundle.stack_trace is None

    def test_service_map_deduplication(self):
        nr = {
            "source": "newrelic",
            "apm": {"actor": {"entity": {}}},
            "service_map": {
                "actor": {
                    "entity": {
                        "relatedEntities": {
                            "results": [
                                {"target": {"entity": {"name": "db"}}, "type": "CALLS"},
                                {"target": {"entity": {"name": "db"}}, "type": "CALLS"},
                            ]
                        }
                    }
                }
            }
        }
        bundle = normalize_evidence("svc", nr)
        assert len(bundle.service_map) == 1

    def test_datadog_stack_trace_fallback(self):
        """When NR has no stack trace, DD logs are used as fallback."""
        dd = {
            "source": "datadog",
            "incidents": [],
            "triggered_monitors": [],
            "error_logs": [{"message": f"Error line {i}"} for i in range(15)]
        }
        bundle = normalize_evidence("svc", dd_snapshot=dd)
        assert bundle.stack_trace is not None
        assert "Error line 0" in bundle.stack_trace
