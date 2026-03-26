#!/usr/bin/env bash

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
SEED_FILE="${SEED_FILE:-sample_data/golden_incident.json}"

if [[ ! -f "$SEED_FILE" ]]; then
  echo "Seed file not found: $SEED_FILE"
  exit 1
fi

echo "==> Checking API health"
curl -sSf "${API_BASE}/health" > /dev/null
echo "API is reachable at ${API_BASE}"

echo "==> Loading golden incident"
INCIDENT_ID=$(python3 - <<'PY'
import json
with open("sample_data/golden_incident.json", "r", encoding="utf-8") as f:
    payload = json.load(f)
print(payload["id"])
PY
)

PAYLOAD=$(python3 - <<'PY'
import json
with open("sample_data/golden_incident.json", "r", encoding="utf-8") as f:
    src = json.load(f)
out = {
    "id": src["id"],
    "summary": src["summary"],
    "service": src["service"],
    "priority": src["priority"],
}
print(json.dumps(out))
PY
)

echo "==> Triggering RCA pipeline for ${INCIDENT_ID}"
curl -sS -X POST "${API_BASE}/api/rca/pipeline/run" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" > /tmp/golden_rca_response.json || true

echo "==> Pulling mission control summary"
curl -sS "${API_BASE}/api/mission-control/summary" > /tmp/golden_mission_summary.json

echo "==> Summary"
python3 - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("/tmp/golden_mission_summary.json").read_text(encoding="utf-8"))
top = summary.get("highest_priority_incident") or {}
print(f"System mode: {summary.get('system_mode', {}).get('mode')}")
print(f"Open incidents: {summary.get('open_incidents')}")
print(f"Pending approvals: {summary.get('pending_approvals')}")
print(f"Top incident: {top.get('incident_id', 'n/a')} - {top.get('summary', 'n/a')}")
print(f"Top action: {top.get('top_action', 'n/a')}")
PY

echo "Golden demo run complete."
