# Security Model

## Access Control

- API key authentication for protected endpoints (`X-API-Key`).
- Role-oriented governance model for action approvals:
  - operator
  - reviewer
  - approver
  - admin

## Secrets Handling

- Supported backends:
  - environment variables
  - AWS Secrets Manager
  - HashiCorp Vault
- Secret rotation support via refresh callbacks.

## Action Governance Controls

- High-risk actions cannot execute without explicit approval.
- Approval state, reviewer, and comments are persisted.
- Expired approvals are marked and audited.

## Integrity and Audit

- RCA closure artifacts include SHA-256 integrity hash.
- Governance transitions are persisted as append-only audit events.

## Security Hardening Baseline

- Startup config validation for critical integrations.
- Dependency health checks.
- Structured error taxonomy for operational debugging.
