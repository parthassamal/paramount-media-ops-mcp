# Deployment Topology

## Recommended Enterprise Shape

```text
Ingress / API Gateway
    -> Mission Control API (FastAPI)
        -> Decision / Governance / Pipeline services
            -> Integration adapters (Jira, NR, DD, TestRail, Confluence)
            -> State stores (Postgres, Redis, object storage)
    -> Dashboard UI (static assets / CDN)
```

## Runtime Components

- **API service**: route handling and control-plane APIs
- **Scheduler worker**: SLA checks, verification polling, proactive monitors
- **UI service**: mission-control dashboard
- **Data stores**:
  - SQLite for local and demo environments
  - Postgres target for multi-user production concurrency

## Environment Modes

- `mock`: deterministic local demos
- `hybrid`: live Jira with controlled mock telemetry
- `live`: full production integrations

## Operational Requirements

- Health and readiness probes for all dependencies
- Structured logs to centralized observability stack
- Alerting on heartbeat gaps and pipeline failures
- Backup and retention policy for audit records
