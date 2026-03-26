# Demo Narrative: Detect -> Explain -> Approve -> Validate -> Measure

## Scenario

Playback outage in `auth-service` causes elevated login failures and churn risk for premium subscribers.

## Demo Goal

Show a complete operator loop in under 3 minutes:

1. Detect the incident in Mission Control.
2. Explain root cause using normalized evidence and timeline.
3. Approve or reject a high-risk action through governance controls.
4. Generate and route verification tests.
5. Measure recovery and close with auditable artifact.

## Script

1. **Open Mission Control**
   - Confirm system mode badge (`mock`, `hybrid`, or `live`).
   - Highlight top-priority incident and decision summary.

2. **Open Incident Detail**
   - Show timeline chronology and evidence references.
   - Show confidence and business impact scores.
   - Explain why top action was selected.

3. **Governance Checkpoint**
   - Show review queue and SLA timer.
   - Demonstrate that high-risk actions require approval.

4. **Execution**
   - Trigger RCA pipeline for the incident.
   - Approve generated tests and write to TestRail.
   - Create verification run and attach output to RCA artifact.

5. **Outcome**
   - Show verification results.
   - Show cycle time and review latency metrics.
   - Confirm Jira closure criteria and artifact integrity check.

## Success Criteria for the Demo

- The audience can follow the decision path without narration overload.
- All outputs show explicit rationale, confidence, and owner.
- Governance and audit history are visible as runtime behavior, not hidden internals.
