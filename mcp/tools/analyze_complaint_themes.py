"""
Analyze Complaint Themes Tool.

Extracts themes and identifies fixable issues from customer complaints.
"""

from typing import Dict, Any, List, Optional
from mcp.resources import ComplaintsTopicsResource
from mcp.pareto import ParetoCalculator, ParetoInsights


class AnalyzeComplaintThemesTool:
    """
    Tool to analyze complaint themes and identify fixable issues.
    
    Uses Pareto analysis to focus on high-impact, fixable themes.
    """
    
    def __init__(self):
        """Initialize the tool."""
        self.complaints_resource = ComplaintsTopicsResource()
        self.pareto = ParetoCalculator()
        self.insights = ParetoInsights()
    
    def execute(
        self,
        days_back: int = 30,
        focus_on_fixable: bool = True,
        max_themes: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze complaint themes and prioritize fixable issues.
        
        Args:
            days_back: Number of days to analyze (default: 30)
            focus_on_fixable: Only return fixable themes (default: True)
            max_themes: Maximum number of themes to return (default: 10)
        
        Returns:
            Analysis with prioritized themes and fix recommendations
            
        Example:
            >>> tool = AnalyzeComplaintThemesTool()
            >>> result = tool.execute(focus_on_fixable=True)
            >>> print(result["high_priority_themes"][0]["name"])
            "Buffering/Streaming Quality"
        """
        # Get all complaint data
        complaint_data = self.complaints_resource.query(days_back=days_back)
        themes = complaint_data["themes"]
        
        # Filter for fixable themes if requested
        if focus_on_fixable:
            themes = [t for t in themes if t.get("is_fixable", False)]
        
        # Get fixable themes breakdown
        fixable_data = self.complaints_resource.get_fixable_themes()
        
        # Perform Pareto analysis on churners attributed
        pareto_result = self.pareto.analyze(
            themes,
            impact_field="churners_attributed",
            id_field="theme_id"
        )
        
        # Get top themes
        top_themes = self.pareto.get_top_contributors(
            pareto_result,
            id_field="theme_id",
            impact_field="churners_attributed"
        )[:max_themes]
        
        # Prioritize by fix complexity vs impact
        prioritized = self._prioritize_themes(themes)
        
        # Calculate aggregate impact
        total_addressable = self._calculate_addressable_impact(fixable_data)
        
        return {
            "analysis_scope": {
                "days_analyzed": days_back,
                "total_themes": len(complaint_data["themes"]),
                "fixable_themes": len(themes)
            },
            "high_priority_themes": prioritized["quick_wins"] + prioritized["strategic"],
            "pareto_analysis": pareto_result.to_dict(),
            "top_contributors": top_themes,
            "addressable_impact": total_addressable,
            "prioritization": prioritized,
            "implementation_roadmap": self._generate_roadmap(prioritized)
        }
    
    def _prioritize_themes(self, themes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Prioritize themes by impact vs complexity."""
        quick_wins = []  # High impact, low complexity
        strategic = []    # High impact, high complexity
        incremental = []  # Moderate impact, low/medium complexity
        
        for theme in themes:
            impact_score = theme["revenue_impact_annual"] / 1000000  # Millions
            complexity = theme["fix_complexity"]
            
            priority_item = {
                "theme_id": theme["theme_id"],
                "name": theme["name"],
                "impact_score": round(impact_score, 2),
                "complexity": complexity,
                "revenue_impact": theme["revenue_impact_annual"],
                "fix_timeline": theme["estimated_fix_timeline"],
                "recommended_actions": theme["recommended_actions"]
            }
            
            if impact_score >= 10:  # $10M+ impact
                if complexity == "low":
                    quick_wins.append(priority_item)
                else:
                    strategic.append(priority_item)
            elif impact_score >= 5:  # $5M+ impact
                incremental.append(priority_item)
        
        return {
            "quick_wins": sorted(quick_wins, key=lambda x: x["impact_score"], reverse=True),
            "strategic": sorted(strategic, key=lambda x: x["impact_score"], reverse=True),
            "incremental": sorted(incremental, key=lambda x: x["impact_score"], reverse=True)
        }
    
    def _calculate_addressable_impact(self, fixable_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total addressable impact from fixable themes."""
        return {
            "total_revenue_at_risk": fixable_data["total_addressable_revenue"],
            "fixable_count": fixable_data["total_fixable_count"],
            "by_complexity": {
                "low": {
                    "count": len(fixable_data["breakdown_by_complexity"]["low"]),
                    "revenue": sum(t["revenue_impact_annual"] for t in fixable_data["breakdown_by_complexity"]["low"])
                },
                "medium": {
                    "count": len(fixable_data["breakdown_by_complexity"]["medium"]),
                    "revenue": sum(t["revenue_impact_annual"] for t in fixable_data["breakdown_by_complexity"]["medium"])
                },
                "high": {
                    "count": len(fixable_data["breakdown_by_complexity"]["high"]),
                    "revenue": sum(t["revenue_impact_annual"] for t in fixable_data["breakdown_by_complexity"]["high"])
                }
            }
        }
    
    def _generate_roadmap(self, prioritized: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate implementation roadmap."""
        roadmap = []
        
        # Phase 1: Quick wins (0-3 months)
        if prioritized["quick_wins"]:
            roadmap.append({
                "phase": 1,
                "name": "Quick Wins",
                "timeline": "0-3 months",
                "themes": prioritized["quick_wins"][:2],
                "expected_impact": sum(t["revenue_impact"] for t in prioritized["quick_wins"][:2]),
                "priority": "immediate"
            })
        
        # Phase 2: Strategic initiatives (3-9 months)
        if prioritized["strategic"]:
            roadmap.append({
                "phase": 2,
                "name": "Strategic Initiatives",
                "timeline": "3-9 months",
                "themes": prioritized["strategic"][:2],
                "expected_impact": sum(t["revenue_impact"] for t in prioritized["strategic"][:2]),
                "priority": "high"
            })
        
        # Phase 3: Incremental improvements (6-12 months)
        if prioritized["incremental"]:
            roadmap.append({
                "phase": 3,
                "name": "Incremental Improvements",
                "timeline": "6-12 months",
                "themes": prioritized["incremental"][:3],
                "expected_impact": sum(t["revenue_impact"] for t in prioritized["incremental"][:3]),
                "priority": "medium"
            })
        
        return roadmap


def create_tool() -> AnalyzeComplaintThemesTool:
    """Factory function to create the tool."""
    return AnalyzeComplaintThemesTool()
