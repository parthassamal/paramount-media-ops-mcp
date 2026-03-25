#!/usr/bin/env python3
"""
API contract checker:
- Calls key endpoints (positive + negative)
- Validates response bodies against OpenAPI schemas
- Emits a concise pass/fail summary
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from jsonschema import ValidationError, validate


BASE_URL = "http://localhost:8000"
TIMEOUT = 45


@dataclass
class CaseResult:
    name: str
    method: str
    path: str
    expected_status: int
    actual_status: Optional[int]
    ok: bool
    schema_ok: Optional[bool]
    error: Optional[str]
    preview: str


def _safe_preview(payload: Any, limit: int = 220) -> str:
    try:
        if isinstance(payload, (dict, list)):
            raw = json.dumps(payload, default=str)
        else:
            raw = str(payload)
        return raw[:limit]
    except Exception as exc:  # noqa: BLE001
        return f"<preview_error: {exc}>"


def _resolve_schema(schema: Dict[str, Any], components: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return _resolve_schema(components.get(ref_name, {}), components)

    resolved: Dict[str, Any] = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            resolved[key] = {
                prop_name: _resolve_schema(prop_schema, components)
                for prop_name, prop_schema in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            resolved[key] = _resolve_schema(value, components)
        elif key in ("anyOf", "oneOf", "allOf") and isinstance(value, list):
            resolved[key] = [_resolve_schema(item, components) for item in value]
        elif isinstance(value, dict):
            resolved[key] = _resolve_schema(value, components)
        else:
            resolved[key] = value
    return resolved


def _response_schema(
    openapi: Dict[str, Any], path: str, method: str, status_code: int
) -> Optional[Dict[str, Any]]:
    op = openapi.get("paths", {}).get(path, {}).get(method.lower(), {})
    responses = op.get("responses", {})
    target = responses.get(str(status_code)) or responses.get("default")
    if not target:
        return None

    content = target.get("content", {})
    if not content:
        return None
    app_json = content.get("application/json") or next(iter(content.values()), None)
    if not app_json:
        return None
    schema = app_json.get("schema")
    if not schema:
        return None
    components = openapi.get("components", {}).get("schemas", {})
    return _resolve_schema(schema, components)


def run_case(
    *,
    session: requests.Session,
    openapi: Dict[str, Any],
    name: str,
    method: str,
    path: str,
    expected_status: int,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> CaseResult:
    url = f"{BASE_URL}{path}"
    try:
        response = session.request(
            method=method, url=url, json=payload, params=params, timeout=TIMEOUT
        )
        actual_status = response.status_code
        ok = actual_status == expected_status
        try:
            body: Any = response.json()
        except Exception:  # noqa: BLE001
            body = response.text

        schema_ok: Optional[bool] = None
        schema_error: Optional[str] = None
        schema = _response_schema(openapi, path, method, expected_status)
        if schema and isinstance(body, (dict, list)):
            try:
                validate(instance=body, schema=schema)
                schema_ok = True
            except ValidationError as exc:
                schema_ok = False
                schema_error = str(exc).splitlines()[0][:260]

        return CaseResult(
            name=name,
            method=method,
            path=path,
            expected_status=expected_status,
            actual_status=actual_status,
            ok=ok,
            schema_ok=schema_ok,
            error=schema_error,
            preview=_safe_preview(body),
        )
    except Exception as exc:  # noqa: BLE001
        return CaseResult(
            name=name,
            method=method,
            path=path,
            expected_status=expected_status,
            actual_status=None,
            ok=False,
            schema_ok=None,
            error=str(exc),
            preview="",
        )


def main() -> int:
    session = requests.Session()
    openapi = session.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT).json()

    cases: List[CaseResult] = []

    # Core positive checks
    checks = [
        ("health", "GET", "/health", 200, None, None),
        ("rca_health", "GET", "/api/rca/health", 200, None, None),
        ("rca_pipeline_list", "GET", "/api/rca/pipeline", 200, None, {"limit": 25}),
        ("review_pending", "GET", "/api/rca/review/pending", 200, None, None),
        ("jira_issues", "GET", "/api/jira/issues", 200, None, {"limit": 10}),
        ("jira_health", "GET", "/api/jira/health", 200, None, None),
        ("streaming_qoe_metrics", "GET", "/api/streaming/qoe/metrics", 200, None, None),
        ("analytics_subscribers_stats", "GET", "/api/analytics/subscribers/stats", 200, None, None),
        ("analytics_churn_cohorts", "GET", "/api/analytics/churn/cohorts", 200, None, None),
        ("phase2_summary", "GET", "/api/phase2/summary", 200, None, None),
        (
            "phase2_test_impact",
            "POST",
            "/api/phase2/test-impact/analyze",
            200,
            {"changed_services": ["auth-service", "streaming-api"], "create_run": False},
            None,
        ),
        ("phase2_hygiene_run", "POST", "/api/phase2/suite-hygiene/run", 200, None, None),
        ("phase2_hygiene_latest", "GET", "/api/phase2/suite-hygiene/latest", 200, None, None),
        (
            "phase2_deployment_risk",
            "POST",
            "/api/phase2/deployment-risk/score",
            200,
            {"changed_services": ["auth-service", "payments"]},
            None,
        ),
        ("phase2_patterns_detect", "POST", "/api/phase2/patterns/detect", 200, None, None),
        ("phase2_patterns_list", "GET", "/api/phase2/patterns", 200, None, None),
        ("phase2_alert_coverage", "GET", "/api/phase2/alert-tests/coverage", 200, None, None),
        (
            "phase2_alert_generate",
            "POST",
            "/api/phase2/alert-tests/generate",
            200,
            {"auto_queue": False},
            None,
        ),
        ("phase2_effectiveness_calc", "POST", "/api/phase2/effectiveness/calculate", 200, None, None),
        ("phase2_effectiveness_trends", "GET", "/api/phase2/effectiveness/trends", 200, None, {"days": 30}),
    ]

    for name, method, path, expected, payload, params in checks:
        cases.append(
            run_case(
                session=session,
                openapi=openapi,
                name=name,
                method=method,
                path=path,
                expected_status=expected,
                payload=payload,
                params=params,
            )
        )

    # Dynamic detail checks using one real RCA id if available
    pipeline_resp = session.get(f"{BASE_URL}/api/rca/pipeline?limit=1", timeout=TIMEOUT)
    if pipeline_resp.ok:
        records = pipeline_resp.json().get("records", [])
        if records:
            rca_id = records[0]["rca_id"]
            detail_checks = [
                ("pipeline_state_existing", "GET", f"/api/rca/pipeline/{rca_id}", 200, None, None),
                ("pipeline_metrics_existing", "GET", f"/api/rca/pipeline/{rca_id}/metrics", 200, None, None),
                ("artifact_existing", "GET", f"/api/rca/artifact/{rca_id}", 200, None, None),
                ("verify_existing", "GET", f"/api/rca/pipeline/{rca_id}/verify", 200, None, None),
                ("can_close_existing", "GET", f"/api/rca/pipeline/{rca_id}/can-close", 200, None, None),
            ]
            for name, method, path, expected, payload, params in detail_checks:
                cases.append(
                    run_case(
                        session=session,
                        openapi=openapi,
                        name=name,
                        method=method,
                        path=path,
                        expected_status=expected,
                        payload=payload,
                        params=params,
                    )
                )

    # Negative / validation checks
    negatives = [
        ("pipeline_state_missing", "GET", "/api/rca/pipeline/not-a-real-id", 404, None, None),
        ("artifact_missing", "GET", "/api/rca/artifact/not-a-real-id", 404, None, None),
        ("can_close_missing", "GET", "/api/rca/pipeline/not-a-real-id/can-close", 404, None, None),
        ("resume_missing", "POST", "/api/rca/pipeline/resume", 400, {"rca_id": "not-a-real-id"}, None),
        (
            "phase2_triage_missing_run",
            "POST",
            "/api/phase2/triage/run",
            400,
            {"run_id": 999999, "auto_action": False},
            None,
        ),
        ("triage_invalid_schema", "POST", "/api/phase2/triage/run", 422, {"run_id": "abc"}, None),
        (
            "impact_invalid_schema",
            "POST",
            "/api/phase2/test-impact/analyze",
            422,
            {"changed_services": "not-an-array"},
            None,
        ),
        ("nrql_invalid_schema", "POST", "/api/rca/newrelic/nrql", 422, {"query": ""}, None),
    ]

    for name, method, path, expected, payload, params in negatives:
        cases.append(
            run_case(
                session=session,
                openapi=openapi,
                name=name,
                method=method,
                path=path,
                expected_status=expected,
                payload=payload,
                params=params,
            )
        )

    passed = sum(1 for c in cases if c.ok)
    failed = [c for c in cases if not c.ok]
    schema_failures = [c for c in cases if c.schema_ok is False]

    print(f"TOTAL_CASES={len(cases)}")
    print(f"PASSED={passed}")
    print(f"FAILED={len(failed)}")
    print(f"SCHEMA_FAILURES={len(schema_failures)}")
    print("---- FAILURES ----")
    for case in failed:
        print(
            f"{case.name}: expected={case.expected_status} actual={case.actual_status} "
            f"path={case.path} preview={case.preview}"
        )
    print("---- SCHEMA FAILURES ----")
    for case in schema_failures:
        print(f"{case.name}: path={case.path} error={case.error}")

    report = [c.__dict__ for c in cases]
    report_path = "/tmp/api_contract_report.json"
    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2, default=str)
    print(f"REPORT_PATH={report_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
