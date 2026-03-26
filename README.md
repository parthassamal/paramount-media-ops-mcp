# Paramount Media Ops Mission Control

Enterprise streaming incident intelligence and RCA actioning control plane.

## Product Promise

The platform is centered on one end-to-end loop:

1. Detect the highest-impact incident.
2. Explain root cause with normalized evidence.
3. Recommend next action with confidence and business impact.
4. Route high-risk actions through approval.
5. Generate and execute verification tests.
6. Track recovery outcomes with auditability.

## Quick Start

```bash
git clone <repo-url>
cd paramount-media-ops-mcp
./start.sh
```

Open:

- UI: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Mission Control summary: `http://localhost:8000/api/mission-control/summary`

## Golden Demo

```bash
./scripts/run_golden_demo.sh
```

Artifacts:

- Seed incident: `sample_data/golden_incident.json`
- Demo script: `docs/demo_script.md`

## Architecture (6 Layers)

```text
Signal Ingestion -> Evidence Intelligence -> Decision Engine
-> Governance Layer -> Execution Layer -> Mission Control UI
```

Key modules:

- `mcp/api/mission_control.py`
- `mcp/decision/`
- `mcp/governance/`
- `mcp/tools/timeline_builder.py`
- `mcp/chatbot/ops_chatbot.py`
- `dashboard/src/app/components/mission/`

## Live Integrations

| Service | Status | Details |
|---------|--------|---------|
| **Jira Cloud** | Live | PROD project, `/search/jql` POST API, 17+ production issues |
| **TestRail** | Live | Project 2, Suite 11, Sections 52 (Auth) / 53 (CDN), service-based routing |
| **New Relic** | Live | Account 7492750, NerdGraph GraphQL, evidence capture |
| **Datadog** | Live | us5.datadoghq.com, SDK-based, 7 monitors configured |

## Core APIs

### Mission Control

- `GET /api/mission-control/summary`
- `GET /api/mission-control/incidents`
- `GET /api/mission-control/incident/{incident_id}`

### RCA and Governance Flow

- `POST /api/rca/pipeline/run`
- `POST /api/rca/pipeline/resume`
- `POST /api/rca/review/approve`
- `GET /api/rca/review/pending`
- `GET /api/rca/pipeline/{rca_id}/verify`

### Governance

- `GET /api/governance/reviews`
- `POST /api/governance/reviews/{id}/approve`
- `POST /api/governance/reviews/{id}/reject`
- `GET /api/governance/stats`

### Operator Chatbot

- `POST /api/chatbot/ask`
- `GET /api/chatbot/history/{session_id}`

## Dashboard Features

- **Pagination**: All data tables support configurable page sizes (10/25/50 per page)
- **Light / Dark Mode**: Toggle via header icon; all components respond via CSS custom properties
- **Export PDF**: Executive report with KPIs, incidents, decision scoring, and governance status
- **Live Badges**: Sidebar shows real-time counts for issues, reviews, and governance approvals

## System Modes

- `mock`: deterministic local flow
- `hybrid`: Jira live + mock observability (set `JIRA_FORCE_LIVE=true`)
- `live`: full live integration to all four services

Mode badge is shown in Mission Control header.

## Security and Reliability

- API key protection supported via `X-API-Key`
- Secrets manager backends (env, AWS, Vault)
- Idempotent pipeline with concurrency locking and resume support
- Human review queue with 24-hour SLA tracking
- RCA artifact integrity verification (SHA-256)
- Governance audit trail for all action transitions

## Documentation

- Product story: `docs/product_story.md`
- Demo narrative: `docs/demo_narrative.md`
- Architecture overview: `docs/architecture_overview.md`
- Security model: `docs/security_model.md`
- Deployment topology: `docs/deployment_topology.md`
- Operational runbook: `docs/operational_runbook.md`
- Advanced capability notes: `docs/advanced_capabilities.md`
- GenAI applicable plan: `docs/genai_applicable_plan.md`
