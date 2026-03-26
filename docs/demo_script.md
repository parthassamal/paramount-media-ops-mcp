# Golden Demo Script

## Objective

Demonstrate a complete control-plane loop in less than 3 minutes:
**detect -> explain -> approve -> validate -> measure**.

## Prerequisites

- Backend running (`http://localhost:8000`)
- Dashboard running (`http://localhost:5173`)
- Golden incident seed loaded (`sample_data/golden_incident.json`)

## Steps

1. Open `Mission Control` and show:
   - system mode badge
   - highest-priority incident
   - pending approvals

2. Open incident detail and show:
   - timeline
   - evidence references
   - top recommended action and confidence

3. Trigger RCA and review governance:
   - high-risk action waits for approval
   - approval state and SLA timer visible

4. Approve and execute:
   - generate tests
   - create verification run
   - attach outputs to RCA artifact

5. Close the loop:
   - show verification result
   - show cycle time and decision summary
   - show artifact integrity verification
