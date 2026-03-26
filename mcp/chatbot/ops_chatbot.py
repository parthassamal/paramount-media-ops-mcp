"""
Mission-control chatbot service.

Implements a deterministic, tool-routed assistant pattern:
- Selects tools from user intent
- Builds structured context from platform control-plane data
- Produces answer + citations + quality score
- Emits observability logs for each interaction
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Callable, Deque, Dict, List, Optional
from uuid import uuid4

from config import settings
from mcp.db.rca_store import get_rca_by_jira_key
from mcp.db.review_store import get_pending_reviews
from mcp.decision import DecisionEngine, IncidentDecisionInput
from mcp.integrations.jira_connector import JiraConnector
from mcp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ToolResult:
    name: str
    payload: Dict


class OpsChatbotService:
    """Stateful in-memory chatbot tailored for mission-control operators."""

    def __init__(self) -> None:
        self._jira = JiraConnector(mock_mode=settings.mock_mode)
        self._decision_engine = DecisionEngine()
        self._history: Dict[str, Deque[Dict[str, str]]] = defaultdict(lambda: deque(maxlen=20))
        self._tools: Dict[str, Callable[..., ToolResult]] = {
            "mission_summary": self._tool_mission_summary,
            "incident_detail": self._tool_incident_detail,
            "review_queue": self._tool_review_queue,
        }

    def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> Dict:
        started = perf_counter()
        sid = session_id or f"ops-{uuid4().hex[:12]}"
        q = (question or "").strip()
        if not q:
            duration_ms = int((perf_counter() - started) * 1000)
            return {
                "session_id": sid,
                "answer": "Please provide a question so I can help with incident operations.",
                "citations": [],
                "quality_score": 0.2,
                "tool_trace": [],
                "generated_at": datetime.utcnow().isoformat(),
                "duration_ms": duration_ms,
            }

        selected_tools = self._select_tools(q, incident_id)
        tool_results: List[ToolResult] = []
        for tool_name in selected_tools:
            tool_results.append(self._tools[tool_name](incident_id=incident_id))

        answer = self._compose_answer(question=q, incident_id=incident_id, results=tool_results)
        quality = self._evaluate_answer(answer=answer, results=tool_results)
        citations = self._collect_citations(tool_results)

        self._history[sid].append({"role": "user", "content": q})
        self._history[sid].append({"role": "assistant", "content": answer})

        duration_ms = int((perf_counter() - started) * 1000)
        logger.info(
            "ops_chatbot_interaction",
            session_id=sid,
            question=q[:120],
            tools=selected_tools,
            quality_score=quality,
            duration_ms=duration_ms,
        )

        return {
            "session_id": sid,
            "answer": answer,
            "citations": citations,
            "quality_score": quality,
            "tool_trace": selected_tools,
            "generated_at": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
        }

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return list(self._history.get(session_id, []))

    def _select_tools(self, question: str, incident_id: Optional[str]) -> List[str]:
        lower = question.lower()
        selected = ["mission_summary"]
        if incident_id or any(k in lower for k in ["incident", "pipeline", "stage", "root cause", "rca"]):
            selected.append("incident_detail")
        if any(k in lower for k in ["approve", "approval", "review", "sla"]):
            selected.append("review_queue")
        return list(dict.fromkeys(selected))

    def _to_decision_input(self, issue: Dict) -> IncidentDecisionInput:
        issue_id = str(issue.get("issue_id") or issue.get("key") or "")
        rca = get_rca_by_jira_key(issue_id)
        cost_impact = float(issue.get("cost_overrun") or issue.get("cost_impact") or 0.0)
        return IncidentDecisionInput(
            incident_id=issue_id,
            summary=str(issue.get("title") or issue.get("summary") or ""),
            service=str(issue.get("service_name") or issue.get("show") or ""),
            status=str(issue.get("status") or "open"),
            severity=str(issue.get("severity") or "medium"),
            team=issue.get("team"),
            cost_impact=cost_impact,
            revenue_at_risk=float(issue.get("revenue_at_risk") or (cost_impact * 1.5)),
            affected_subscribers=0,
            delay_days=int(issue.get("delay_days") or 0),
            evidence_completeness_score=0.8 if (rca and rca.evidence_bundle_id) else 0.45,
            blast_radius_score=min((len(rca.impacted_components or []) / 10), 1.0) if rca else 0.2,
            has_open_rca=bool(rca and not rca.jira_closed),
            has_recent_failures=bool(rca and rca.verification_result and not rca.verification_result.all_passed),
            generated_tests_pending_review=bool(rca and rca.stage.value == "review_pending"),
        )

    def _tool_mission_summary(self, incident_id: Optional[str] = None) -> ToolResult:
        issues = self._jira.get_production_issues(limit=30)
        decisions = self._decision_engine.rank_incidents([self._to_decision_input(i) for i in issues])
        top = decisions[0] if decisions else None
        return ToolResult(
            name="mission_summary",
            payload={
                "open_incidents": len(issues),
                "top_incident_id": top.incident_id if top else None,
                "top_priority_score": top.scoring.priority_score if top else 0,
                "top_action": top.recommended_actions[0].action_type.value
                if (top and top.recommended_actions)
                else None,
                "top_action_confidence": top.recommended_actions[0].confidence
                if (top and top.recommended_actions)
                else None,
                "decision_summary": top.summary if top else "No active incidents.",
            },
        )

    def _tool_incident_detail(self, incident_id: Optional[str] = None) -> ToolResult:
        if not incident_id:
            return ToolResult(name="incident_detail", payload={"status": "not_requested"})
        issues = self._jira.get_production_issues(limit=200)
        target = next(
            (i for i in issues if str(i.get("issue_id") or i.get("key") or "") == incident_id),
            None,
        )
        if not target:
            return ToolResult(
                name="incident_detail",
                payload={"status": "not_found", "incident_id": incident_id},
            )
        rca = get_rca_by_jira_key(incident_id)
        decision = self._decision_engine.evaluate(self._to_decision_input(target))
        return ToolResult(
            name="incident_detail",
            payload={
                "status": "found",
                "incident_id": incident_id,
                "summary": target.get("title") or target.get("summary"),
                "severity": target.get("severity"),
                "pipeline_stage": rca.stage.value if rca else "not_started",
                "top_action": decision.recommended_actions[0].action_type.value
                if decision.recommended_actions
                else None,
                "confidence": decision.recommended_actions[0].confidence
                if decision.recommended_actions
                else None,
                "root_cause": rca.root_cause if rca else None,
            },
        )

    def _tool_review_queue(self, incident_id: Optional[str] = None) -> ToolResult:
        reviews = get_pending_reviews()
        pending = [r for r in reviews if r.status.value == "pending"]
        overdue = [r for r in pending if r.is_overdue]
        return ToolResult(
            name="review_queue",
            payload={
                "pending_count": len(pending),
                "overdue_count": len(overdue),
                "pending_ids": [r.review_id for r in pending[:5]],
            },
        )

    def _compose_answer(self, question: str, incident_id: Optional[str], results: List[ToolResult]) -> str:
        index = {result.name: result.payload for result in results}
        mission = index.get("mission_summary", {})
        review = index.get("review_queue", {})
        incident = index.get("incident_detail", {})

        lines = []
        lines.append("Mission Control response:")

        if mission:
            lines.append(
                f"- Top incident: {mission.get('top_incident_id') or 'n/a'} "
                f"(priority {mission.get('top_priority_score', 0):.1f})."
            )
            lines.append(
                f"- Recommended action: {mission.get('top_action') or 'manual triage'} "
                f"(confidence {mission.get('top_action_confidence') or 0:.2f})."
            )
            lines.append(f"- Open incidents: {mission.get('open_incidents', 0)}.")

        if review:
            lines.append(
                f"- Pending approvals: {review.get('pending_count', 0)} "
                f"(overdue {review.get('overdue_count', 0)})."
            )

        if incident and incident.get("status") == "found":
            lines.append(
                f"- Incident {incident.get('incident_id')} is at stage "
                f"{incident.get('pipeline_stage')} with severity {incident.get('severity')}."
            )
            if incident.get("root_cause"):
                lines.append(f"- Current root cause hypothesis: {incident.get('root_cause')}.")
        elif incident and incident.get("status") == "not_found":
            lines.append(f"- Incident {incident.get('incident_id')} was not found in current Jira data.")

        lines.append(
            "- Next operator step: validate evidence, approve high-risk action if needed, then run verification before Jira close."
        )
        return "\n".join(lines)

    @staticmethod
    def _evaluate_answer(answer: str, results: List[ToolResult]) -> float:
        score = 1.0
        if len(answer) < 120:
            score -= 0.2
        if not results:
            score -= 0.3
        if "Top incident" not in answer:
            score -= 0.2
        return round(max(score, 0.0), 2)

    @staticmethod
    def _collect_citations(results: List[ToolResult]) -> List[Dict[str, str]]:
        citation_map = {
            "mission_summary": "/api/mission-control/summary",
            "incident_detail": "/api/mission-control/incident/{incident_id}",
            "review_queue": "/api/rca/review/pending",
        }
        citations = []
        for result in results:
            citations.append(
                {
                    "source": result.name,
                    "reference": citation_map.get(result.name, ""),
                }
            )
        return citations
