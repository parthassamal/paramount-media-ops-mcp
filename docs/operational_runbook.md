# Operational Runbook

## 1) Startup Verification

1. Confirm API health endpoint reports ready dependencies.
2. Confirm Mission Control summary endpoint responds.
3. Confirm scheduler heartbeat is updating.
4. Confirm review queue and RCA stores are readable.

## 2) Incident Handling Flow

1. Open Mission Control and identify highest-priority incident.
2. Validate evidence timeline and confidence.
3. Review recommended action and risk tier.
4. Route approval for high-risk actions.
5. Execute RCA + test generation and run verification.
6. Confirm closure criteria and archive artifact hash.

## 3) Governance Monitoring

- Track pending approvals and SLA countdown.
- Escalate overdue high-risk approvals.
- Audit status transitions for rejected or failed actions.

## 4) Failure Recovery

- Resume failed RCA from last stable stage.
- Re-run verification poller for incomplete test runs.
- Verify idempotency key before replaying actions.

## 5) Daily Operations

- Review cycle-time and review-latency trends.
- Review top recurring root causes and runbook updates.
- Review suite hygiene and effectiveness reports.
