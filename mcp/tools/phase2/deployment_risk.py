"""
Phase 2.4 — Regression Risk Score

Deployment gate that computes a composite risk score from:
- Number of high-RCA-history services touched
- Pass rate of tests in the impact zone
- Components with sparse test coverage
- Days since last successful regression run
- Unverified pipeline-generated cases

Returns a score 0-100 with tier (Low/Medium/High/Hold).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from mcp.tools.phase2.test_impact import analyze_test_impact
from mcp.tools.phase2.suite_hygiene import suite_hygiene_checker
from mcp.db.rca_store import get_recent_rcas
from mcp.tools.testrail_tool import get_all_cases, get_run_results, _tr
from mcp.utils.logger import get_logger
from config import settings

logger = get_logger(__name__)


class RiskTier(str, Enum):
    """Risk tier classification."""
    LOW = "low"           # 0-30: Proceed
    MEDIUM = "medium"     # 31-60: Proceed with monitoring
    HIGH = "high"         # 61-85: Flag for review
    HOLD = "hold"         # 86-100: Recommend delay


@dataclass
class RiskFactor:
    """A single risk factor contributing to the score."""
    name: str
    weight: float  # 0-1
    value: float   # Raw value
    score: float   # Weighted contribution to total
    details: str


class DeploymentRiskScorer:
    """
    Computes deployment risk score from multiple signals.
    
    Weights:
    - RCA history services: HIGH (30%)
    - Test pass rate: HIGH (25%)
    - Coverage gaps: MEDIUM (20%)
    - Stale regression: MEDIUM (15%)
    - Unverified cases: LOW (10%)
    """
    
    def __init__(self):
        self.weights = {
            "rca_history": 0.30,
            "pass_rate": 0.25,
            "coverage_gaps": 0.20,
            "stale_regression": 0.15,
            "unverified_cases": 0.10
        }
    
    def score(
        self,
        changed_services: List[str],
        deployment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute risk score for a deployment.
        
        Args:
            changed_services: List of services being deployed
            deployment_id: Optional deployment ID
            
        Returns:
            {
                "deployment_id": str,
                "score": int (0-100),
                "tier": str,
                "recommendation": str,
                "factors": list,
                "blocking_conditions": list,
                "impact_analysis": dict
            }
        """
        deployment_id = deployment_id or f"deploy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(
            "deployment_risk_scoring_started",
            deployment_id=deployment_id,
            services=changed_services
        )
        
        # Run test impact analysis first
        impact = analyze_test_impact(changed_services, deployment_id, create_run=False)
        
        # Calculate each risk factor
        factors = []
        blocking_conditions = []
        
        # Factor 1: RCA History
        rca_factor = self._score_rca_history(changed_services)
        factors.append(rca_factor)
        if rca_factor.value >= 3:
            blocking_conditions.append(f"{int(rca_factor.value)} services have 3+ past RCAs")
        
        # Factor 2: Test Pass Rate
        pass_rate_factor = self._score_pass_rate(impact.get("prioritised_case_ids", []))
        factors.append(pass_rate_factor)
        if pass_rate_factor.value < 70:
            blocking_conditions.append(f"Test pass rate is {pass_rate_factor.value:.0f}%")
        
        # Factor 3: Coverage Gaps
        coverage_factor = self._score_coverage_gaps(changed_services)
        factors.append(coverage_factor)
        if coverage_factor.value >= 2:
            blocking_conditions.append(f"{int(coverage_factor.value)} services have sparse test coverage")
        
        # Factor 4: Stale Regression
        stale_factor = self._score_stale_regression()
        factors.append(stale_factor)
        if stale_factor.value > 14:
            blocking_conditions.append(f"Last regression run was {int(stale_factor.value)} days ago")
        
        # Factor 5: Unverified Cases
        unverified_factor = self._score_unverified_cases()
        factors.append(unverified_factor)
        
        # Calculate total score
        total_score = sum(f.score for f in factors)
        total_score = min(100, max(0, total_score))
        
        # Determine tier
        tier = self._get_tier(total_score)
        recommendation = self._get_recommendation(tier, blocking_conditions)
        
        result = {
            "deployment_id": deployment_id,
            "changed_services": changed_services,
            "score": round(total_score),
            "tier": tier.value,
            "recommendation": recommendation,
            "factors": [
                {
                    "name": f.name,
                    "weight": f.weight,
                    "value": f.value,
                    "score": round(f.score, 1),
                    "details": f.details
                }
                for f in factors
            ],
            "blocking_conditions": blocking_conditions,
            "impact_analysis": {
                "total_affected_cases": impact.get("total_affected_cases", 0),
                "high_priority_count": impact.get("high_priority_count", 0),
                "recommended_run_id": impact.get("testrail_run_id")
            }
        }
        
        logger.info(
            "deployment_risk_scoring_complete",
            deployment_id=deployment_id,
            score=total_score,
            tier=tier.value
        )
        
        return result
    
    def _score_rca_history(self, services: List[str]) -> RiskFactor:
        """Score based on RCA history of touched services."""
        high_rca_count = 0
        
        try:
            recent = get_recent_rcas(limit=200)
            service_rcas: Dict[str, int] = {}
            
            for rca in recent:
                svc = rca.service_name or ""
                service_rcas[svc.lower()] = service_rcas.get(svc.lower(), 0) + 1
            
            for service in services:
                if service_rcas.get(service.lower(), 0) >= 3:
                    high_rca_count += 1
        except Exception:
            pass
        
        # Score: 0-100 based on high-RCA services (max at 5)
        raw_score = min(high_rca_count / 5, 1) * 100
        weighted = raw_score * self.weights["rca_history"]
        
        return RiskFactor(
            name="RCA History",
            weight=self.weights["rca_history"],
            value=high_rca_count,
            score=weighted,
            details=f"{high_rca_count} services with 3+ historical RCAs"
        )
    
    def _score_pass_rate(self, case_ids: List[int]) -> RiskFactor:
        """Score based on recent pass rate of affected tests."""
        if not case_ids:
            return RiskFactor(
                name="Test Pass Rate",
                weight=self.weights["pass_rate"],
                value=100,
                score=0,
                details="No affected cases to evaluate"
            )
        
        total_passed = 0
        total_results = 0
        
        from mcp.tools.testrail_tool import get_results_for_case
        
        for case_id in case_ids[:20]:  # Sample first 20
            try:
                results = get_results_for_case(case_id, limit=5)
                for r in results:
                    total_results += 1
                    if r.get("status_id") == 1:
                        total_passed += 1
            except Exception:
                continue
        
        pass_rate = (total_passed / total_results * 100) if total_results > 0 else 100
        
        # Score: Lower pass rate = higher risk
        raw_score = (100 - pass_rate)
        weighted = raw_score * self.weights["pass_rate"]
        
        return RiskFactor(
            name="Test Pass Rate",
            weight=self.weights["pass_rate"],
            value=pass_rate,
            score=weighted,
            details=f"{pass_rate:.0f}% pass rate on affected tests"
        )
    
    def _score_coverage_gaps(self, services: List[str]) -> RiskFactor:
        """Score based on services with sparse test coverage."""
        sparse_count = 0
        
        try:
            cases = get_all_cases()
            cases_per_service: Dict[str, int] = {}
            
            for case in cases:
                refs = (case.get("refs") or "").lower()
                title = case.get("title", "").lower()
                
                for service in services:
                    if service.lower() in refs or service.lower() in title:
                        cases_per_service[service] = cases_per_service.get(service, 0) + 1
            
            for service in services:
                if cases_per_service.get(service, 0) < 5:
                    sparse_count += 1
        except Exception:
            pass
        
        # Score: More sparse services = higher risk
        raw_score = min(sparse_count / len(services), 1) * 100 if services else 0
        weighted = raw_score * self.weights["coverage_gaps"]
        
        return RiskFactor(
            name="Coverage Gaps",
            weight=self.weights["coverage_gaps"],
            value=sparse_count,
            score=weighted,
            details=f"{sparse_count} of {len(services)} services have <5 test cases"
        )
    
    def _score_stale_regression(self) -> RiskFactor:
        """Score based on days since last successful regression run."""
        days_stale = 0
        
        try:
            # Get recent runs
            runs = _tr("GET", f"get_runs/{settings.testrail_project_id}&is_completed=1&limit=10")
            if runs:
                for run in runs:
                    if "regression" in run.get("name", "").lower():
                        completed_on = run.get("completed_on")
                        if completed_on:
                            last_run = datetime.fromtimestamp(completed_on)
                            days_stale = (datetime.utcnow() - last_run).days
                            break
        except Exception:
            days_stale = 7  # Default assumption
        
        # Score: More days = higher risk (max at 30 days)
        raw_score = min(days_stale / 30, 1) * 100
        weighted = raw_score * self.weights["stale_regression"]
        
        return RiskFactor(
            name="Stale Regression",
            weight=self.weights["stale_regression"],
            value=days_stale,
            score=weighted,
            details=f"{days_stale} days since last regression run"
        )
    
    def _score_unverified_cases(self) -> RiskFactor:
        """Score based on unverified pipeline-generated cases."""
        unverified_count = 0
        
        try:
            cases = get_all_cases()
            for case in cases:
                if case.get("custom_automation_type") == 2:  # To be automated
                    unverified_count += 1
        except Exception:
            pass
        
        # Score: More unverified = slightly higher risk (max at 50)
        raw_score = min(unverified_count / 50, 1) * 100
        weighted = raw_score * self.weights["unverified_cases"]
        
        return RiskFactor(
            name="Unverified Cases",
            weight=self.weights["unverified_cases"],
            value=unverified_count,
            score=weighted,
            details=f"{unverified_count} pipeline-generated cases not yet verified"
        )
    
    def _get_tier(self, score: float) -> RiskTier:
        """Determine tier from score."""
        if score <= 30:
            return RiskTier.LOW
        elif score <= 60:
            return RiskTier.MEDIUM
        elif score <= 85:
            return RiskTier.HIGH
        else:
            return RiskTier.HOLD
    
    def _get_recommendation(self, tier: RiskTier, blocking: List[str]) -> str:
        """Generate recommendation based on tier."""
        recs = {
            RiskTier.LOW: "Proceed with deployment. Pre-deploy test run queued.",
            RiskTier.MEDIUM: "Proceed with monitoring. Alert on-call to watch triage results.",
            RiskTier.HIGH: f"Flag for review before deployment. Blocking conditions: {', '.join(blocking[:2])}",
            RiskTier.HOLD: f"Recommend delaying deployment. Resolve: {', '.join(blocking)}"
        }
        return recs.get(tier, "Unknown tier")


# Singleton instance
deployment_risk_scorer = DeploymentRiskScorer()


def score_deployment_risk(
    changed_services: List[str],
    deployment_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for deployment risk scoring."""
    return deployment_risk_scorer.score(changed_services, deployment_id)
