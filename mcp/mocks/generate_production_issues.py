"""
Mock data generator for production issues.

Generates realistic production issues with Pareto-distributed delays.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from config import settings


class ProductionIssueGenerator:
    """Generator for production issues following Pareto distribution."""
    
    def __init__(self, seed: int = None):
        """
        Initialize generator with optional seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed or settings.random_seed
        random.seed(self.seed)
    
    def generate(self, num_issues: int = 20) -> List[Dict[str, Any]]:
        """
        Generate production issues where top 20% cause 80% of delays.
        
        Args:
            num_issues: Number of issues to generate (default: 20)
        
        Returns:
            List of production issue dictionaries
        """
        issues = []
        
        # Paramount+ show names for realism
        shows = [
            "Star Trek: Discovery", "Yellowstone", "1923", "Halo", "Mayor of Kingstown",
            "Tulsa King", "Lioness", "Frasier", "Criminal Minds: Evolution", "NCIS",
            "Seal Team", "Fire Country", "FBI", "Blue Bloods", "The Equalizer",
            "Ghosts", "Young Sheldon", "Bob Hearts Abishola", "So Help Me Todd", "CSI: Vegas"
        ]
        
        issue_templates = [
            # Top 3 issues causing 76% of delays (Pareto)
            {
                "title": "VFX Pipeline Blocker - Star Trek: Discovery S5",
                "show": "Star Trek: Discovery",
                "type": "VFX Delay",
                "severity": "critical",
                "delay_days": 45,
                "cost_overrun": 2400000,
                "root_cause": "Third-party VFX vendor capacity constraints"
            },
            {
                "title": "Script Rewrites - Yellowstone S5 Finale",
                "show": "Yellowstone",
                "type": "Creative",
                "severity": "high",
                "delay_days": 30,
                "cost_overrun": 1800000,
                "root_cause": "Showrunner changes requiring major rewrites"
            },
            {
                "title": "Location Permitting Issues - 1923 Montana Scenes",
                "show": "1923",
                "type": "Production",
                "severity": "high",
                "delay_days": 22,
                "cost_overrun": 1200000,
                "root_cause": "National park filming permits delayed"
            },
            # Mid-tier issues (moderate impact)
            {
                "title": "Actor Scheduling Conflict - Halo S2",
                "show": "Halo",
                "type": "Talent",
                "severity": "medium",
                "delay_days": 12,
                "cost_overrun": 450000,
                "root_cause": "Lead actor committed to film project"
            },
            {
                "title": "Weather Delays - Tulsa King Outdoor Shoots",
                "show": "Tulsa King",
                "type": "Production",
                "severity": "medium",
                "delay_days": 8,
                "cost_overrun": 320000,
                "root_cause": "Unexpected severe weather pattern"
            },
            {
                "title": "COVID Outbreak on Set - Lioness",
                "show": "Lioness",
                "type": "Health/Safety",
                "severity": "medium",
                "delay_days": 14,
                "cost_overrun": 580000,
                "root_cause": "Mandatory quarantine period"
            },
            # Low-impact issues (long tail)
            {
                "title": "Minor Costume Redesign - Frasier",
                "show": "Frasier",
                "type": "Wardrobe",
                "severity": "low",
                "delay_days": 3,
                "cost_overrun": 45000,
                "root_cause": "Historical accuracy concerns"
            },
            {
                "title": "Set Construction Delays - Criminal Minds",
                "show": "Criminal Minds: Evolution",
                "type": "Production",
                "severity": "low",
                "delay_days": 5,
                "cost_overrun": 120000,
                "root_cause": "Supply chain issues for specialty materials"
            },
        ]
        
        # Generate issues with controlled Pareto distribution
        base_date = datetime.now() - timedelta(days=60)
        
        for i in range(num_issues):
            if i < len(issue_templates):
                # Use template for controlled Pareto
                template = issue_templates[i]
            else:
                # Generate additional low-impact issues
                template = {
                    "title": f"Minor Issue - {random.choice(shows)}",
                    "show": random.choice(shows),
                    "type": random.choice(["Post-Production", "Audio", "Editing", "QA"]),
                    "severity": "low",
                    "delay_days": random.randint(1, 4),
                    "cost_overrun": random.randint(20000, 80000),
                    "root_cause": "Minor technical adjustment needed"
                }
            
            issue = {
                "issue_id": f"PROD-{i+1:04d}",
                "title": template["title"],
                "show": template["show"],
                "type": template["type"],
                "severity": template["severity"],
                "status": random.choice(["open", "in_progress", "blocked"]),
                "delay_days": template["delay_days"],
                "cost_overrun": template["cost_overrun"],
                "root_cause": template["root_cause"],
                "created_date": (base_date + timedelta(days=i*2)).isoformat(),
                "target_resolution_date": (datetime.now() + timedelta(days=random.randint(5, 30))).isoformat(),
                "assigned_team": self._get_team_assignment(template["type"]),
                "stakeholder_impact": self._calculate_stakeholder_impact(template["delay_days"]),
                "mitigation_plan": self._generate_mitigation_plan(template["type"]),
                "revenue_at_risk": template["cost_overrun"] * 1.5  # Revenue impact is typically 1.5x cost
            }
            
            issues.append(issue)
        
        return issues
    
    def _get_team_assignment(self, issue_type: str) -> str:
        """Get team assignment based on issue type."""
        team_map = {
            "VFX Delay": "Visual Effects",
            "Creative": "Creative Affairs",
            "Production": "Production Management",
            "Talent": "Talent Relations",
            "Health/Safety": "Production Safety",
            "Wardrobe": "Wardrobe Department",
            "Post-Production": "Post-Production",
            "Audio": "Audio Engineering",
            "Editing": "Editorial",
            "QA": "Quality Assurance"
        }
        return team_map.get(issue_type, "General Production")
    
    def _calculate_stakeholder_impact(self, delay_days: int) -> str:
        """Calculate stakeholder impact level."""
        if delay_days >= 20:
            return "executive"
        elif delay_days >= 10:
            return "senior_management"
        else:
            return "operational"
    
    def _generate_mitigation_plan(self, issue_type: str) -> List[str]:
        """Generate mitigation plan steps."""
        mitigation_plans = {
            "VFX Delay": [
                "Engage backup VFX vendor",
                "Redistribute work across multiple vendors",
                "Extend VFX timeline and adjust release schedule"
            ],
            "Creative": [
                "Fast-track script approval process",
                "Parallel track multiple script versions",
                "Bring in additional writers"
            ],
            "Production": [
                "Identify alternative shooting locations",
                "Adjust shooting schedule",
                "Negotiate expedited permits"
            ],
            "Talent": [
                "Renegotiate actor availability",
                "Adjust shooting schedule around conflicts",
                "Consider schedule compression options"
            ]
        }
        
        return mitigation_plans.get(
            issue_type,
            ["Assess impact", "Develop corrective plan", "Execute with monitoring"]
        )
    
    def get_pareto_summary(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Pareto distribution summary for issues.
        
        Args:
            issues: List of generated issues
        
        Returns:
            Pareto analysis summary
        """
        total_delay = sum(issue["delay_days"] for issue in issues)
        total_cost = sum(issue["cost_overrun"] for issue in issues)
        
        # Sort by delay days
        sorted_issues = sorted(issues, key=lambda x: x["delay_days"], reverse=True)
        
        # Calculate top 20%
        top_20_count = max(1, len(issues) // 5)
        top_20_delay = sum(issue["delay_days"] for issue in sorted_issues[:top_20_count])
        top_20_contribution = top_20_delay / total_delay if total_delay > 0 else 0
        
        return {
            "total_issues": len(issues),
            "total_delay_days": total_delay,
            "total_cost_overrun": total_cost,
            "top_20_percent_count": top_20_count,
            "top_20_percent_contribution": round(top_20_contribution, 2),
            "top_issues": [
                {
                    "issue_id": issue["issue_id"],
                    "title": issue["title"],
                    "delay_days": issue["delay_days"],
                    "cost_overrun": issue["cost_overrun"]
                }
                for issue in sorted_issues[:top_20_count]
            ],
            "pareto_validated": 0.75 <= top_20_contribution <= 0.85
        }
