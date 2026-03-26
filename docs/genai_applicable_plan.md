# Applicable GenAI Agent Plan (Adapted to This Repo)

This plan applies practical patterns from modern agent/RAG production guides to the Paramount Media Ops control plane, without turning the platform into a generic chatbot product.

## What We Adopted

## 1) Tool-Routed Agent Pattern (Deterministic First)

- Added a mission-control chatbot with explicit tool routing:
  - `mission_summary`
  - `incident_detail`
  - `review_queue`
- Kept routing deterministic and auditable for operations usage.
- Avoided opaque multi-hop agent behavior for critical decisions.

## 2) Typed Contracts and Clean API Surface

- Added typed request/response contracts for `/api/chatbot/ask`.
- Preserved domain logic outside route handlers (`mcp/chatbot/ops_chatbot.py`).

## 3) Evaluation and Observability Hooks

- Added response quality score per chatbot answer.
- Added tool trace and citation references in response payload.
- Added structured interaction log events with latency.

## 4) Mission-Control Integration

- Integrated chat panel directly into `MissionControlPage`.
- Assistant is contextualized for incident operations (not generic Q&A).

## What We Intentionally Deferred

- Full probabilistic planner/executor loops for control-plane actions.
- Mandatory LLM dependency for critical answer generation.
- Heavy framework migration for existing orchestration flows.

These are deferred to preserve reliability and operator trust for incident response.

## Next Iteration Backlog

1. Add optional RAG source retrieval for runbooks and RCA artifacts with citations.
2. Add conversation persistence in SQLite/Postgres (current state is in-memory).
3. Add automated regression tests for chatbot tool routing and response quality.
4. Add feedback capture (`thumbs_up/down`) and answer drift monitoring.
5. Add role-based guardrails on what actions chatbot can recommend vs execute.
