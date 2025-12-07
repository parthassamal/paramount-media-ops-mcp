"""
Analyze Churn Root Cause Tool.

Correlates churn with complaints and production issues to identify root causes.
"""

from typing import Dict, Any, List, Optional
from mcp.resources import (
    ChurnSignalsResource,
    ComplaintsTopicsResource,
    ProductionIssuesResource,
    ContentCatalogResource
)
from mcp.pareto import ParetoInsights


class AnalyzeChurnRootCauseTool:
    """
    Tool to analyze root causes of subscriber churn.
    
    Correlates churn signals with complaints, production issues, and content
    performance to identify actionable root causes.
    """
    
    def __init__(self):
        """Initialize the tool with required resources."""
        self.churn_resource = ChurnSignalsResource()
        self.complaints_resource = ComplaintsTopicsResource()
        self.production_resource = ProductionIssuesResource()
        self.content_resource = ContentCatalogResource()
        self.insights = ParetoInsights()
    
    def execute(
        self,
        cohort_id: Optional[str] = None,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze root causes of churn for a cohort or all cohorts.
        
        Args:
            cohort_id: Specific cohort to analyze (optional, analyzes all if None)
            include_recommendations: Include actionable recommendations (default: True)
        
        Returns:
            Dictionary with root cause analysis and recommendations
            
        Example:
            >>> tool = AnalyzeChurnRootCauseTool()
            >>> result = tool.execute(cohort_id="COHORT-001")
            >>> print(result["root_causes"][0]["driver"])
            "Content library gaps in key genres"
        """
        # Get churn data
        if cohort_id:
            cohort_data = self.churn_resource.get_cohort_details(cohort_id)
            if not cohort_data:
                return {"error": f"Cohort {cohort_id} not found"}
            cohorts = [cohort_data["cohort"]]
        else:
            churn_data = self.churn_resource.query(risk_threshold=0.3)
            cohorts = churn_data["cohorts"]
        
        # Get complaint themes
        complaints_data = self.complaints_resource.query()
        complaint_themes = complaints_data["themes"]
        
        # Get production issues
        production_data = self.production_resource.query()
        production_issues = production_data["issues"]
        
        # Get content performance
        content_data = self.content_resource.query()
        underperforming = self.content_resource.get_underperforming_content()
        
        # Perform root cause analysis
        root_causes = self._correlate_root_causes(
            cohorts,
            complaint_themes,
            production_issues,
            underperforming["underperforming_shows"]
        )
        
        # Calculate financial impact
        financial_impact = self._calculate_financial_impact(cohorts, root_causes)
        
        result = {
            "analysis_scope": {
                "cohorts_analyzed": len(cohorts),
                "cohort_ids": [c["cohort_id"] for c in cohorts] if cohort_id else "all",
                "total_at_risk": sum(c["projected_churners_30d"] for c in cohorts)
            },
            "root_causes": root_causes,
            "financial_impact": financial_impact
        }
        
        if include_recommendations:
            result["recommendations"] = self._generate_recommendations(root_causes, financial_impact)
        
        return result
    
    def _correlate_root_causes(
        self,
        cohorts: List[Dict[str, Any]],
        complaints: List[Dict[str, Any]],
        production: List[Dict[str, Any]],
        underperforming_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Correlate churn drivers with operational data."""
        root_causes = []
        
        for cohort in cohorts:
            primary_driver = cohort["primary_driver"]
            
            # Find related complaints
            related_complaints = self._find_related_complaints(primary_driver, complaints)
            
            # Find related production issues
            related_production = self._find_related_production(primary_driver, production)
            
            # Find related content issues
            related_content = self._find_related_content(primary_driver, underperforming_content)
            
            root_cause = {
                "cohort_id": cohort["cohort_id"],
                "cohort_name": cohort["name"],
                "at_risk_subscribers": cohort["projected_churners_30d"],
                "financial_impact": cohort["financial_impact_30d"],
                "primary_driver": primary_driver,
                "supporting_evidence": {
                    "complaint_themes": related_complaints,
                    "production_issues": related_production,
                    "content_issues": related_content
                },
                "correlation_strength": self._calculate_correlation_strength(
                    related_complaints,
                    related_production,
                    related_content
                )
            }
            
            root_causes.append(root_cause)
        
        # Sort by financial impact
        return sorted(root_causes, key=lambda x: x["financial_impact"], reverse=True)
    
    def _find_related_complaints(
        self,
        driver: str,
        complaints: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Find complaint themes related to churn driver."""
        related = []
        
        # Keyword matching (in production, use NLP similarity)
        keywords_map = {
            "Content library": ["content", "library", "missing", "selection"],
            "pricing": ["price", "expensive", "value"],
            "performance": ["buffering", "quality", "streaming", "loading"],
            "tech": ["crash", "bug", "error", "app"],
            "sport": ["sports", "soccer", "nfl"]
        }
        
        driver_keywords = []
        for key, keywords in keywords_map.items():
            if key.lower() in driver.lower():
                driver_keywords.extend(keywords)
        
        for complaint in complaints:
            theme_keywords = complaint["keywords"]
            # Check if any driver keyword matches theme keywords
            if any(kw in theme_keywords for kw in driver_keywords):
                related.append({
                    "theme_name": complaint["name"],
                    "churn_correlation": complaint["churn_correlation"],
                    "complaint_volume": complaint["complaint_volume"]
                })
        
        return related[:3]  # Top 3 related
    
    def _find_related_production(
        self,
        driver: str,
        production: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find production issues related to churn driver."""
        related = []
        
        # Content-related production issues
        if "content" in driver.lower():
            # Find delays that impact content availability
            related = [
                {
                    "issue_id": issue["issue_id"],
                    "title": issue["title"],
                    "delay_days": issue["delay_days"]
                }
                for issue in production
                if issue["delay_days"] >= 10
            ][:3]
        
        return related
    
    def _find_related_content(
        self,
        driver: str,
        underperforming: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find underperforming content related to churn driver."""
        related = []
        
        if "content" in driver.lower() or "genre" in driver.lower():
            related = [
                {
                    "show_name": show["name"],
                    "completion_rate": show["completion_rate"],
                    "reasons": show["reasons"]
                }
                for show in underperforming[:3]
            ]
        
        return related
    
    def _calculate_correlation_strength(
        self,
        complaints: List,
        production: List,
        content: List
    ) -> str:
        """Calculate strength of correlation evidence."""
        evidence_count = len(complaints) + len(production) + len(content)
        
        if evidence_count >= 5:
            return "strong"
        elif evidence_count >= 3:
            return "moderate"
        else:
            return "weak"
    
    def _calculate_financial_impact(
        self,
        cohorts: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total financial impact."""
        total_30d = sum(c["financial_impact_30d"] for c in cohorts)
        total_annual = total_30d * 12
        
        # Group by correlation strength
        by_strength = {"strong": 0, "moderate": 0, "weak": 0}
        for cause in root_causes:
            by_strength[cause["correlation_strength"]] += cause["financial_impact"]
        
        return {
            "total_impact_30d": total_30d,
            "total_impact_annual": total_annual,
            "at_risk_subscribers": sum(c["projected_churners_30d"] for c in cohorts),
            "by_correlation_strength": by_strength,
            "addressable_with_high_confidence": by_strength["strong"] + by_strength["moderate"]
        }
    
    def _generate_recommendations(
        self,
        root_causes: List[Dict[str, Any]],
        financial_impact: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Prioritize by financial impact and correlation strength
        high_priority_causes = [
            rc for rc in root_causes
            if rc["correlation_strength"] in ["strong", "moderate"]
            and rc["financial_impact"] > 1000000  # $1M+
        ]
        
        for i, cause in enumerate(high_priority_causes[:3], 1):
            rec = {
                "priority": i,
                "cohort": cause["cohort_name"],
                "root_cause": cause["primary_driver"],
                "actions": self._get_actions_for_driver(cause["primary_driver"]),
                "expected_impact": {
                    "subscribers_retained": int(cause["at_risk_subscribers"] * 0.5),
                    "revenue_30d": cause["financial_impact"] * 0.5,
                    "confidence": cause["correlation_strength"]
                },
                "timeline": "30-60 days",
                "investment_required": self._estimate_investment(cause["primary_driver"])
            }
            recommendations.append(rec)
        
        return recommendations
    
    def _get_actions_for_driver(self, driver: str) -> List[str]:
        """Get specific actions for a churn driver."""
        action_map = {
            "Content library": [
                "Accelerate content licensing in weak genres",
                "Fast-track original content production",
                "Improve personalized recommendations"
            ],
            "pricing": [
                "Introduce ad-supported tier",
                "Launch loyalty discount program",
                "Create value-added bundles"
            ],
            "performance": [
                "CDN infrastructure upgrade",
                "Emergency tech sprint on app stability",
                "Proactive outreach to affected users"
            ]
        }
        
        for key, actions in action_map.items():
            if key.lower() in driver.lower():
                return actions
        
        return ["Conduct deeper investigation", "Survey affected cohort", "Pilot retention campaign"]
    
    def _estimate_investment(self, driver: str) -> int:
        """Estimate investment required to address driver."""
        investment_map = {
            "Content library": 5000000,  # $5M for licensing/production
            "pricing": 1000000,  # $1M for pricing program
            "performance": 3000000,  # $3M for infrastructure
            "tech": 2000000  # $2M for tech fixes
        }
        
        for key, investment in investment_map.items():
            if key.lower() in driver.lower():
                return investment
        
        return 1500000  # Default $1.5M


def create_tool() -> AnalyzeChurnRootCauseTool:
    """Factory function to create the tool."""
    return AnalyzeChurnRootCauseTool()
