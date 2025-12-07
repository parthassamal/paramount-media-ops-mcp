"""JIRA Connector for Production Issues"""
from typing import List, Dict, Any, Optional
import os
from jira import JIRA
from src.pareto_engine import ParetoAnalyzer
from src.mock_data import MockDataGenerator


class JIRAConnector:
    """Connects to JIRA for production issue tracking with Pareto analysis"""
    
    def __init__(self, server_url: Optional[str] = None, email: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize JIRA connector
        
        Args:
            server_url: JIRA server URL (defaults to env var JIRA_SERVER)
            email: JIRA user email (defaults to env var JIRA_EMAIL)
            api_token: JIRA API token (defaults to env var JIRA_API_TOKEN)
        """
        self.server_url = server_url or os.getenv("JIRA_SERVER")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")
        
        self.client = None
        self.use_mock = True  # Default to mock data if no credentials
        
        # Try to connect if credentials are provided
        if self.server_url and self.email and self.api_token:
            try:
                self.client = JIRA(
                    server=self.server_url,
                    basic_auth=(self.email, self.api_token)
                )
                self.use_mock = False
            except Exception as e:
                print(f"Failed to connect to JIRA: {e}. Using mock data.")
                self.use_mock = True
    
    def fetch_production_issues(self, project_key: str = "PROD", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch production issues from JIRA
        
        Args:
            project_key: JIRA project key
            max_results: Maximum number of issues to fetch
            
        Returns:
            List of production issues
        """
        if self.use_mock or not self.client:
            # Return mock data
            return MockDataGenerator.generate_production_issues(max_results)
        
        try:
            # Fetch from real JIRA
            jql = f'project = {project_key} AND type = "Production Issue" ORDER BY created DESC'
            issues = self.client.search_issues(jql, maxResults=max_results)
            
            parsed_issues = []
            for issue in issues:
                parsed_issues.append({
                    "issue_id": issue.key,
                    "title": issue.fields.summary,
                    "type": issue.fields.issuetype.name,
                    "severity": getattr(issue.fields, 'priority', 'Medium').name if hasattr(issue.fields, 'priority') and issue.fields.priority else "Medium",
                    "status": issue.fields.status.name,
                    "created_date": issue.fields.created,
                    "affected_users": getattr(issue.fields, 'customfield_affected_users', 0),
                    "estimated_revenue_impact": getattr(issue.fields, 'customfield_revenue_impact', 0),
                    "impact_score": self._calculate_impact_score(issue),
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
                })
            
            return parsed_issues
        except Exception as e:
            print(f"Error fetching from JIRA: {e}. Using mock data.")
            return MockDataGenerator.generate_production_issues(max_results)
    
    def _calculate_impact_score(self, issue) -> float:
        """Calculate impact score for a JIRA issue"""
        severity_weights = {
            "Critical": 100,
            "Highest": 100,
            "High": 75,
            "Medium": 50,
            "Low": 25,
            "Lowest": 10
        }
        
        severity = getattr(issue.fields, 'priority', 'Medium').name if hasattr(issue.fields, 'priority') and issue.fields.priority else "Medium"
        base_score = severity_weights.get(severity, 50)
        
        affected_users = getattr(issue.fields, 'customfield_affected_users', 0)
        user_impact = affected_users / 100 if affected_users else 0
        
        return base_score + user_impact
    
    def analyze_issues_with_pareto(self, issues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Analyze production issues using Pareto principle
        
        Args:
            issues: List of issues (if None, fetches from JIRA)
            
        Returns:
            Pareto analysis results
        """
        if issues is None:
            issues = self.fetch_production_issues()
        
        return ParetoAnalyzer.analyze(issues, "impact_score", "issue_id")
    
    def get_critical_issues(self, issues: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Get the vital few critical issues using Pareto analysis"""
        pareto_result = self.analyze_issues_with_pareto(issues)
        return pareto_result["vital_few"]
    
    def create_issue(self, summary: str, description: str, issue_type: str = "Production Issue", 
                     priority: str = "Medium") -> Dict[str, Any]:
        """
        Create a new JIRA issue
        
        Args:
            summary: Issue summary
            description: Issue description
            issue_type: Type of issue
            priority: Issue priority
            
        Returns:
            Created issue details
        """
        if self.use_mock or not self.client:
            # Mock creation
            import random
            return {
                "issue_id": f"PROD-{random.randint(1000, 9999)}",
                "status": "created_mock",
                "message": "Mock issue created (no JIRA connection)"
            }
        
        try:
            issue_dict = {
                'project': {'key': 'PROD'},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            new_issue = self.client.create_issue(fields=issue_dict)
            return {
                "issue_id": new_issue.key,
                "status": "created",
                "url": f"{self.server_url}/browse/{new_issue.key}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
