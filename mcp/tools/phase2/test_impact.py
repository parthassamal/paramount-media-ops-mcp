"""
Phase 2.1 — Test Impact Analysis

Before a deployment, analyse the set of changed services against the TestRail
suite and component dependency graph to produce a ranked list of tests most
likely to be affected by that change.

Input: deployment manifest (list of changed services)
Output: prioritised TestRail run with curated case_ids
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from mcp.tools.testrail_tool import get_all_cases, _tr
from mcp.tools.dependency_graph import compute_blast_radius
from mcp.db.rca_store import get_recent_rcas
from mcp.models.evidence_models import EvidenceBundle
from mcp.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


@dataclass
class ImpactedCase:
    """A test case identified as potentially affected by a deployment."""
    case_id: int
    title: str
    section_id: int
    refs: Optional[str]
    impact_score: float  # 0-100
    impact_reasons: List[str]
    last_run_passed: Optional[bool]
    rca_history_count: int


class TestImpactAnalyzer:
    """
    Analyzes deployment manifests to identify affected tests.
    
    Uses:
    - Component dependency graph (blast radius logic)
    - TestRail suite refs and section mapping
    - RCA history for high-risk identification
    """
    
    def __init__(self):
        self.component_map = self._load_component_map()
    
    def _load_component_map(self) -> Dict[str, Any]:
        """Load component-to-suite mapping."""
        try:
            from pathlib import Path
            map_path = Path(__file__).parent.parent.parent.parent / "data" / "component_map.json"
            if map_path.exists():
                return json.loads(map_path.read_text())
        except Exception as e:
            logger.warning("component_map_load_failed", error=str(e))
        return {}
    
    def analyze(
        self,
        changed_services: List[str],
        deployment_id: Optional[str] = None,
        create_run: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze deployment impact and create prioritized test run.
        
        Args:
            changed_services: List of service names being changed
            deployment_id: Optional deployment identifier
            create_run: Whether to create a TestRail run
            
        Returns:
            {
                "deployment_id": str,
                "changed_services": list,
                "blast_radius": dict,
                "impacted_cases": list,
                "prioritised_case_ids": list,
                "testrail_run_id": int (if create_run=True),
                "total_affected_cases": int,
                "high_priority_count": int
            }
        """
        deployment_id = deployment_id or f"deploy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(
            "test_impact_analysis_started",
            deployment_id=deployment_id,
            services=changed_services
        )
        
        # Step 1: Compute blast radius for changed services
        blast_radius = self._compute_deployment_blast_radius(changed_services)
        all_affected_services = blast_radius.get("all_affected", changed_services)
        
        # Step 2: Get all TestRail cases
        all_cases = get_all_cases()
        
        # Step 3: Get RCA history for risk scoring
        rca_history = self._get_rca_service_history()
        
        # Step 4: Score and rank cases
        impacted_cases = []
        for case in all_cases:
            impact_score, reasons = self._score_case_impact(
                case,
                changed_services,
                all_affected_services,
                rca_history
            )
            
            if impact_score > 0:
                impacted_cases.append(ImpactedCase(
                    case_id=case["id"],
                    title=case.get("title", ""),
                    section_id=case.get("section_id", 0),
                    refs=case.get("refs"),
                    impact_score=impact_score,
                    impact_reasons=reasons,
                    last_run_passed=None,  # Would need result lookup
                    rca_history_count=rca_history.get(case.get("refs", ""), 0)
                ))
        
        # Step 5: Sort by impact score (highest first)
        impacted_cases.sort(key=lambda c: c.impact_score, reverse=True)
        
        # Step 6: Create TestRail run if requested
        testrail_run_id = None
        if create_run and impacted_cases:
            case_ids = [c.case_id for c in impacted_cases[:100]]  # Top 100
            testrail_run_id = self._create_impact_run(
                deployment_id,
                changed_services,
                case_ids
            )
        
        result = {
            "deployment_id": deployment_id,
            "changed_services": changed_services,
            "blast_radius": blast_radius,
            "impacted_cases": [
                {
                    "case_id": c.case_id,
                    "title": c.title,
                    "impact_score": c.impact_score,
                    "impact_reasons": c.impact_reasons,
                    "rca_history_count": c.rca_history_count
                }
                for c in impacted_cases[:50]  # Return top 50
            ],
            "prioritised_case_ids": [c.case_id for c in impacted_cases],
            "testrail_run_id": testrail_run_id,
            "total_affected_cases": len(impacted_cases),
            "high_priority_count": len([c for c in impacted_cases if c.impact_score >= 70])
        }
        
        logger.info(
            "test_impact_analysis_complete",
            deployment_id=deployment_id,
            total_cases=len(impacted_cases),
            run_id=testrail_run_id
        )
        
        return result
    
    def _compute_deployment_blast_radius(self, services: List[str]) -> Dict[str, Any]:
        """Compute blast radius for deployment."""
        try:
            # Create minimal evidence bundle for blast radius computation
            evidence = EvidenceBundle(
                bundle_id="deployment-impact",
                captured_at=datetime.utcnow(),
                sources=["deployment"],
                service_name=services[0] if services else "unknown"
            )
            
            # Add affected services to evidence
            evidence_dict = evidence.model_dump()
            evidence_dict["affected_services"] = services
            
            return compute_blast_radius(evidence)
        except Exception as e:
            logger.warning("blast_radius_failed", error=str(e))
            return {"all_affected": services, "total_blast_radius": len(services)}
    
    def _get_rca_service_history(self) -> Dict[str, int]:
        """Get count of RCAs per Jira ticket (service indicator)."""
        history = {}
        try:
            recent = get_recent_rcas(limit=200)
            for rca in recent:
                if rca.jira_ticket_id:
                    history[rca.jira_ticket_id] = history.get(rca.jira_ticket_id, 0) + 1
        except Exception as e:
            logger.warning("rca_history_fetch_failed", error=str(e))
        return history
    
    def _score_case_impact(
        self,
        case: Dict[str, Any],
        changed_services: List[str],
        all_affected: List[str],
        rca_history: Dict[str, int]
    ) -> tuple[float, List[str]]:
        """
        Score a test case's impact relevance to the deployment.
        
        Returns (score 0-100, list of reasons)
        """
        score = 0.0
        reasons = []
        
        title = case.get("title", "").lower()
        refs = case.get("refs", "") or ""
        
        # Direct service match in refs or title
        for service in changed_services:
            service_lower = service.lower()
            if service_lower in refs.lower():
                score += 40
                reasons.append(f"Direct ref match: {service}")
            elif service_lower in title:
                score += 30
                reasons.append(f"Title mentions: {service}")
        
        # Affected service match (downstream)
        for service in all_affected:
            if service not in changed_services:
                service_lower = service.lower()
                if service_lower in refs.lower() or service_lower in title:
                    score += 20
                    reasons.append(f"Downstream affected: {service}")
        
        # RCA history boost
        if refs and refs in rca_history:
            rca_count = rca_history[refs]
            if rca_count >= 3:
                score += 25
                reasons.append(f"High RCA history ({rca_count} incidents)")
            elif rca_count >= 1:
                score += 10
                reasons.append(f"Has RCA history ({rca_count} incidents)")
        
        # Component map match
        for component, config in self.component_map.get("components", {}).items():
            if component.lower() in title or component.lower() in refs.lower():
                suites = config.get("test_suites", [])
                if case.get("suite_id") in suites:
                    score += 15
                    reasons.append(f"Component map match: {component}")
        
        return min(score, 100), reasons
    
    def _create_impact_run(
        self,
        deployment_id: str,
        services: List[str],
        case_ids: List[int]
    ) -> Optional[int]:
        """Create a TestRail run for the deployment impact analysis."""
        try:
            result = _tr("POST", f"add_run/{settings.testrail_project_id}", {
                "suite_id": settings.testrail_default_suite_id,
                "name": f"Pre-deployment: {', '.join(services[:3])} [{deployment_id}]",
                "description": (
                    f"Auto-generated impact analysis for deployment {deployment_id}\n"
                    f"Changed services: {', '.join(services)}\n"
                    f"Total prioritised cases: {len(case_ids)}"
                ),
                "include_all": False,
                "case_ids": case_ids
            })
            return result.get("id")
        except Exception as e:
            logger.error("testrail_run_creation_failed", error=str(e))
            return None


# Singleton instance
test_impact_analyzer = TestImpactAnalyzer()


def analyze_test_impact(
    changed_services: List[str],
    deployment_id: Optional[str] = None,
    create_run: bool = True
) -> Dict[str, Any]:
    """Convenience function for test impact analysis."""
    return test_impact_analyzer.analyze(changed_services, deployment_id, create_run)
