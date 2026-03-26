# Architecture Overview

## Six-Layer Model

```text
Signal Ingestion
  -> Evidence Intelligence
     -> Decision Engine
        -> Governance Layer
           -> Execution Layer
              -> Mission Control UI
```

## 1) Signal Ingestion Layer

- Jira incidents
- Confluence runbooks
- New Relic and Datadog signals
- TestRail inventory and run outcomes
- Email complaint signals
- Analytics and churn indicators

## 2) Evidence Intelligence Layer

- Evidence normalization into `EvidenceBundle`
- Timeline reconstruction from ticket, alert, and pipeline events
- Cross-source correlation
- Blast radius scoring from dependency graph
- Evidence completeness scoring and source references

## 3) Decision Engine

- Deterministic scoring dimensions:
  - operational severity
  - subscriber impact
  - business risk
  - confidence
- Ranked next-best-action plan with rationale and impact

## 4) Governance Layer

- Risk tiers: low, medium, high
- Status lifecycle:
  - proposed
  - awaiting_review
  - approved
  - rejected
  - expired
  - executed
  - failed
- Audit events for every transition
- SLA timers for pending review

## 5) Execution Layer

- RCA pipeline orchestration
- Test generation and TestRail writeback
- Verification run creation
- Jira closure artifact generation with integrity checks

## 6) Mission Control UI

- Top-priority incident
- Open action queue
- Pending approvals and SLA
- Timeline and evidence panels
- Recommended actions with confidence and impact
- Verification and recovery outcomes

## Design Principles

- Typed contracts at every layer
- Deterministic logic for critical control paths
- Integrations isolated behind adapters
- Idempotent writes and resumable state transitions
- Structured logs and measurable operational outcomes
