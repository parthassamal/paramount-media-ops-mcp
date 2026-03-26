"""
Decision Engine for incident intelligence control-plane outputs.
"""

from __future__ import annotations

from typing import List

from mcp.decision.action_selector import select_actions
from mcp.decision.models import (
    DecisionResult,
    DecisionSignal,
    IncidentDecisionInput,
)
from mcp.decision.scoring import score_incident


class DecisionEngine:
    """
    Deterministic decision engine that produces a ranked action plan
    with confidence, rationale, and expected business impact.
    """

    def evaluate(self, incident: IncidentDecisionInput) -> DecisionResult:
        scoring = score_incident(incident)
        actions = select_actions(incident, scoring)
        signals = self._build_signals(incident)

        summary = (
            f"Incident {incident.incident_id} priority={scoring.priority_score:.1f}. "
            f"Top action={actions[0].action_type.value if actions else 'none'} "
            f"with confidence={actions[0].confidence if actions else 0:.2f}."
        )

        return DecisionResult(
            incident_id=incident.incident_id,
            scoring=scoring,
            signals=signals,
            recommended_actions=actions,
            summary=summary,
        )

    def rank_incidents(self, incidents: List[IncidentDecisionInput]) -> List[DecisionResult]:
        """Evaluate incidents and rank by priority score descending."""
        evaluated = [self.evaluate(incident) for incident in incidents]
        return sorted(
            evaluated,
            key=lambda result: result.scoring.priority_score,
            reverse=True,
        )

    @staticmethod
    def _build_signals(incident: IncidentDecisionInput) -> List[DecisionSignal]:
        return [
            DecisionSignal(
                signal_key="severity",
                signal_value=incident.severity,
                source="jira",
                weight=0.35,
            ),
            DecisionSignal(
                signal_key="cost_impact",
                signal_value=f"{incident.cost_impact:.2f}",
                source="jira",
                weight=0.30,
            ),
            DecisionSignal(
                signal_key="evidence_completeness",
                signal_value=f"{incident.evidence_completeness_score:.2f}",
                source="evidence_bundle",
                weight=0.20,
            ),
            DecisionSignal(
                signal_key="blast_radius_score",
                signal_value=f"{incident.blast_radius_score:.2f}",
                source="dependency_graph",
                weight=0.15,
            ),
        ]
