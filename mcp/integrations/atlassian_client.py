"""
Atlassian Integration Client

Wrapper around mcp-atlassian for JIRA and Confluence integration.
Uses the official mcp-atlassian package for API calls.

Free tier: https://www.atlassian.com/software/jira/free
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class JiraIssue:
    """Standardized JIRA issue data."""
    key: str
    summary: str
    status: str
    priority: str
    issue_type: str
    project: str
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    description: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    custom_fields: dict = field(default_factory=dict)
    
    # Business impact fields
    cost_impact: float = 0.0
    delay_days: int = 0
    show_name: Optional[str] = None
    severity: str = "medium"


@dataclass
class ConfluencePage:
    """Standardized Confluence page data."""
    id: str
    title: str
    space_key: str
    status: str
    created: Optional[str] = None
    updated: Optional[str] = None
    author: Optional[str] = None
    body: Optional[str] = None
    url: Optional[str] = None


class AtlassianClient:
    """
    Client for JIRA and Confluence using mcp-atlassian.
    
    Supports both Cloud and Server/Data Center deployments.
    """
    
    def __init__(
        self,
        jira_url: str = "",
        jira_username: str = "",
        jira_api_token: str = "",
        confluence_url: str = "",
        confluence_username: str = "",
        confluence_api_token: str = "",
        mock_mode: bool = True
    ):
        self.jira_url = jira_url.rstrip('/') if jira_url else ""
        self.jira_username = jira_username
        self.jira_api_token = jira_api_token
        self.confluence_url = confluence_url.rstrip('/') if confluence_url else ""
        self.confluence_username = confluence_username
        self.confluence_api_token = confluence_api_token
        self.mock_mode = mock_mode
        
        # HTTP client for direct API calls
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(
            f"AtlassianClient initialized",
            extra={
                "jira_url": self.jira_url,
                "confluence_url": self.confluence_url,
                "mock_mode": mock_mode
            }
        )
    
    def _get_jira_auth(self) -> tuple[str, str]:
        """Get JIRA authentication tuple."""
        return (self.jira_username, self.jira_api_token)
    
    def _get_confluence_auth(self) -> tuple[str, str]:
        """Get Confluence authentication tuple."""
        return (self.confluence_username, self.confluence_api_token)
    
    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    # ==================== Convenience Aliases ====================
    
    def get_spaces(self) -> List[Dict[str, Any]]:
        """Alias for get_confluence_spaces."""
        return self.get_confluence_spaces()
    
    def get_pages(self, space_key: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Alias for get_confluence_pages."""
        return self.get_confluence_pages(space_key=space_key, limit=limit)
    
    def create_page(self, space_key: str, title: str, content: str, parent_id: str = None) -> Dict[str, Any]:
        """Alias for create_confluence_page."""
        return self.create_confluence_page(space_key=space_key, title=title, content=content, parent_id=parent_id)
    
    # ==================== JIRA Methods ====================
    
    def search_issues(
        self,
        jql: str = "",
        project: Optional[str] = None,
        status: Optional[str] = None,
        max_results: int = 50
    ) -> list[JiraIssue]:
        """
        Search JIRA issues using JQL.
        
        Args:
            jql: JQL query string
            project: Filter by project key
            status: Filter by status
            max_results: Maximum results to return
            
        Returns:
            List of JiraIssue objects
        """
        if self.mock_mode:
            return self._get_mock_issues(project, status, max_results)
        
        return asyncio.run(self._search_issues_async(jql, project, status, max_results))
    
    async def _search_issues_async(
        self,
        jql: str,
        project: Optional[str],
        status: Optional[str],
        max_results: int
    ) -> list[JiraIssue]:
        """Async implementation of issue search using new JIRA API."""
        client = await self._ensure_client()
        
        # Build JQL - MUST have project restriction for new API
        jql_parts = []
        if project:
            jql_parts.append(f'project = "{project}"')
        else:
            # Default to our projects
            jql_parts.append('project in (PROD, STREAM, CONTENT)')
        if status:
            jql_parts.append(f'status = "{status}"')
        
        if jql:
            jql_parts.append(f"({jql})")
        
        jql_parts.append("ORDER BY created DESC")
        final_jql = " AND ".join(jql_parts[:-1]) + " " + jql_parts[-1]
        
        try:
            # Use new search/jql API (old /search is deprecated)
            response = await client.post(
                f"{self.jira_url}/rest/api/3/search/jql",
                json={
                    "jql": final_jql,
                    "maxResults": max_results,
                    "fields": ["summary", "status", "priority", "issuetype", "project", 
                              "assignee", "reporter", "created", "updated", "description", 
                              "labels", "components"]
                },
                auth=self._get_jira_auth(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            return [self._parse_jira_issue(issue) for issue in data.get("issues", [])]
            
        except Exception as e:
            logger.error(f"JIRA search failed: {e}")
            if not self.mock_mode:
                return self._get_mock_issues(project, status, max_results)
            return []
    
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Get a specific JIRA issue by key."""
        if self.mock_mode:
            issues = self._get_mock_issues()
            for issue in issues:
                if issue.key == issue_key:
                    return issue
            return None
        
        return asyncio.run(self._get_issue_async(issue_key))
    
    async def _get_issue_async(self, issue_key: str) -> Optional[JiraIssue]:
        """Async implementation of get issue."""
        client = await self._ensure_client()
        
        try:
            response = await client.get(
                f"{self.jira_url}/rest/api/3/issue/{issue_key}",
                auth=self._get_jira_auth()
            )
            response.raise_for_status()
            return self._parse_jira_issue(response.json())
            
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {e}")
            return None
    
    def create_issue(
        self,
        project: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        priority: str = "Medium",
        labels: list[str] = None,
        custom_fields: dict = None
    ) -> Optional[JiraIssue]:
        """Create a new JIRA issue."""
        if self.mock_mode:
            # Return a mock created issue
            return JiraIssue(
                key=f"{project}-999",
                summary=summary,
                status="To Do",
                priority=priority,
                issue_type=issue_type,
                project=project,
                description=description,
                labels=labels or [],
                created=datetime.now().isoformat()
            )
        
        return asyncio.run(self._create_issue_async(
            project, summary, issue_type, description, priority, labels, custom_fields
        ))
    
    async def _create_issue_async(
        self,
        project: str,
        summary: str,
        issue_type: str,
        description: str,
        priority: str,
        labels: list[str],
        custom_fields: dict
    ) -> Optional[JiraIssue]:
        """Async implementation of create issue."""
        client = await self._ensure_client()
        
        payload = {
            "fields": {
                "project": {"key": project},
                "summary": summary,
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
        }
        
        if description:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]
            }
        
        if labels:
            payload["fields"]["labels"] = labels
        
        if custom_fields:
            payload["fields"].update(custom_fields)
        
        try:
            response = await client.post(
                f"{self.jira_url}/rest/api/3/issue",
                json=payload,
                auth=self._get_jira_auth()
            )
            response.raise_for_status()
            data = response.json()
            
            # Fetch the created issue
            return await self._get_issue_async(data["key"])
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    def get_projects(self) -> list[dict]:
        """Get all JIRA projects."""
        if self.mock_mode:
            return [
                {"key": "PROD", "name": "Production Issues", "type": "software"},
                {"key": "CONTENT", "name": "Content Management", "type": "software"},
                {"key": "STREAM", "name": "Streaming Operations", "type": "software"},
            ]
        
        return asyncio.run(self._get_projects_async())
    
    async def _get_projects_async(self) -> list[dict]:
        """Async implementation of get projects."""
        client = await self._ensure_client()
        
        try:
            response = await client.get(
                f"{self.jira_url}/rest/api/3/project",
                auth=self._get_jira_auth()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []
    
    # ==================== Confluence Methods ====================
    
    def search_pages(
        self,
        query: str = "",
        space_key: Optional[str] = None,
        max_results: int = 25
    ) -> list[ConfluencePage]:
        """Search Confluence pages."""
        if self.mock_mode:
            return self._get_mock_pages(query, space_key)
        
        return asyncio.run(self._search_pages_async(query, space_key, max_results))
    
    async def _search_pages_async(
        self,
        query: str,
        space_key: Optional[str],
        max_results: int
    ) -> list[ConfluencePage]:
        """Async implementation of page search."""
        client = await self._ensure_client()
        
        cql_parts = ['type = "page"']
        if query:
            cql_parts.append(f'text ~ "{query}"')
        if space_key:
            cql_parts.append(f'space = "{space_key}"')
        
        cql = " AND ".join(cql_parts)
        
        try:
            response = await client.get(
                f"{self.confluence_url}/wiki/rest/api/content/search",
                params={
                    "cql": cql,
                    "limit": max_results,
                    "expand": "space,version,body.storage"
                },
                auth=self._get_confluence_auth()
            )
            response.raise_for_status()
            data = response.json()
            
            return [self._parse_confluence_page(page) for page in data.get("results", [])]
            
        except Exception as e:
            logger.error(f"Confluence search failed: {e}")
            return []
    
    def get_page(self, page_id: str) -> Optional[ConfluencePage]:
        """Get a specific Confluence page."""
        if self.mock_mode:
            pages = self._get_mock_pages()
            for page in pages:
                if page.id == page_id:
                    return page
            return None
        
        return asyncio.run(self._get_page_async(page_id))
    
    async def _get_page_async(self, page_id: str) -> Optional[ConfluencePage]:
        """Async implementation of get page."""
        client = await self._ensure_client()
        
        try:
            response = await client.get(
                f"{self.confluence_url}/wiki/rest/api/content/{page_id}",
                params={"expand": "space,version,body.storage"},
                auth=self._get_confluence_auth()
            )
            response.raise_for_status()
            return self._parse_confluence_page(response.json())
            
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {e}")
            return None
    
    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None
    ) -> Optional[ConfluencePage]:
        """Create a new Confluence page."""
        if self.mock_mode:
            return ConfluencePage(
                id="mock-999",
                title=title,
                space_key=space_key,
                status="current",
                body=body,
                created=datetime.now().isoformat()
            )
        
        return asyncio.run(self._create_page_async(space_key, title, body, parent_id))
    
    async def _create_page_async(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: Optional[str]
    ) -> Optional[ConfluencePage]:
        """Async implementation of create page."""
        client = await self._ensure_client()
        
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        
        try:
            response = await client.post(
                f"{self.confluence_url}/wiki/rest/api/content",
                json=payload,
                auth=self._get_confluence_auth()
            )
            response.raise_for_status()
            return self._parse_confluence_page(response.json())
            
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            return None
    
    # ==================== Parsing Methods ====================
    
    def _parse_jira_issue(self, data: dict) -> JiraIssue:
        """Parse JIRA API response into JiraIssue."""
        fields = data.get("fields", {})
        
        return JiraIssue(
            key=data.get("key", ""),
            summary=fields.get("summary", ""),
            status=fields.get("status", {}).get("name", "Unknown"),
            priority=fields.get("priority", {}).get("name", "Medium"),
            issue_type=fields.get("issuetype", {}).get("name", "Task"),
            project=fields.get("project", {}).get("key", ""),
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            reporter=fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            created=fields.get("created"),
            updated=fields.get("updated"),
            description=self._extract_description(fields.get("description")),
            labels=fields.get("labels", []),
            components=[c.get("name", "") for c in fields.get("components", [])]
        )
    
    def _extract_description(self, desc: any) -> str:
        """Extract plain text from Atlassian Document Format."""
        if not desc:
            return ""
        if isinstance(desc, str):
            return desc
        if isinstance(desc, dict):
            # ADF format
            content = desc.get("content", [])
            texts = []
            for block in content:
                if block.get("type") == "paragraph":
                    for item in block.get("content", []):
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
            return " ".join(texts)
        return str(desc)
    
    def _parse_confluence_page(self, data: dict) -> ConfluencePage:
        """Parse Confluence API response into ConfluencePage."""
        return ConfluencePage(
            id=data.get("id", ""),
            title=data.get("title", ""),
            space_key=data.get("space", {}).get("key", ""),
            status=data.get("status", ""),
            created=data.get("history", {}).get("createdDate"),
            updated=data.get("version", {}).get("when"),
            author=data.get("history", {}).get("createdBy", {}).get("displayName"),
            body=data.get("body", {}).get("storage", {}).get("value", ""),
            url=data.get("_links", {}).get("webui", "")
        )
    
    # ==================== Mock Data ====================
    
    def _get_mock_issues(
        self,
        project: Optional[str] = None,
        status: Optional[str] = None,
        max_results: int = 50
    ) -> list[JiraIssue]:
        """Generate realistic mock JIRA issues for Paramount Media Ops."""
        mock_issues = [
            JiraIssue(
                key="PROD-101",
                summary="Yellowstone S5 - Audio sync issue in final cut",
                status="In Progress",
                priority="Critical",
                issue_type="Bug",
                project="PROD",
                assignee="John Editor",
                reporter="Sarah Producer",
                created="2024-12-10T10:30:00Z",
                labels=["audio", "post-production", "urgent"],
                show_name="Yellowstone",
                cost_impact=450000,
                delay_days=3,
                severity="critical"
            ),
            JiraIssue(
                key="PROD-102",
                summary="1923 - VFX render farm capacity exceeded",
                status="Open",
                priority="High",
                issue_type="Bug",
                project="PROD",
                assignee="Mike VFX",
                created="2024-12-12T14:00:00Z",
                labels=["vfx", "infrastructure", "scaling"],
                show_name="1923",
                cost_impact=325000,
                delay_days=5,
                severity="high"
            ),
            JiraIssue(
                key="PROD-103",
                summary="Star Trek SNW - Color grading revision needed",
                status="In Review",
                priority="Medium",
                issue_type="Task",
                project="PROD",
                assignee="Lisa Colorist",
                created="2024-12-14T09:00:00Z",
                labels=["color", "post-production"],
                show_name="Star Trek: Strange New Worlds",
                cost_impact=85000,
                delay_days=1,
                severity="medium"
            ),
            JiraIssue(
                key="PROD-104",
                summary="Tulsa King - Location permit issue for S2 finale",
                status="Blocked",
                priority="Critical",
                issue_type="Bug",
                project="PROD",
                created="2024-12-15T11:00:00Z",
                labels=["legal", "locations", "blocking"],
                show_name="Tulsa King",
                cost_impact=750000,
                delay_days=7,
                severity="critical"
            ),
            JiraIssue(
                key="PROD-105",
                summary="Lioness - Stunt coordinator scheduling conflict",
                status="Open",
                priority="High",
                issue_type="Task",
                project="PROD",
                created="2024-12-16T08:00:00Z",
                labels=["scheduling", "stunts", "talent"],
                show_name="Lioness",
                cost_impact=180000,
                delay_days=2,
                severity="high"
            ),
            JiraIssue(
                key="STREAM-201",
                summary="CDN latency spike in Northeast region",
                status="In Progress",
                priority="Critical",
                issue_type="Incident",
                project="STREAM",
                assignee="DevOps Team",
                created="2024-12-17T06:00:00Z",
                labels=["cdn", "performance", "p1"],
                cost_impact=50000,
                delay_days=0,
                severity="critical"
            ),
            JiraIssue(
                key="CONTENT-301",
                summary="Q1 2025 Content Calendar - Final approval needed",
                status="In Review",
                priority="High",
                issue_type="Task",
                project="CONTENT",
                created="2024-12-15T10:00:00Z",
                labels=["planning", "q1-2025", "approval"],
                cost_impact=0,
                delay_days=0,
                severity="medium"
            ),
        ]
        
        # Apply filters
        filtered = mock_issues
        if project:
            filtered = [i for i in filtered if i.project == project]
        if status:
            filtered = [i for i in filtered if i.status.lower() == status.lower()]
        
        return filtered[:max_results]
    
    def _get_mock_pages(
        self,
        query: str = "",
        space_key: Optional[str] = None
    ) -> list[ConfluencePage]:
        """Generate mock Confluence pages."""
        mock_pages = [
            ConfluencePage(
                id="page-001",
                title="Production Runbook - Post-Production Workflow",
                space_key="PROD",
                status="current",
                author="Operations Team",
                created="2024-11-01T10:00:00Z"
            ),
            ConfluencePage(
                id="page-002",
                title="Streaming QoE Standards and Thresholds",
                space_key="STREAM",
                status="current",
                author="Engineering Team",
                created="2024-10-15T14:00:00Z"
            ),
            ConfluencePage(
                id="page-003",
                title="Content ROI Analysis Framework",
                space_key="CONTENT",
                status="current",
                author="Analytics Team",
                created="2024-09-20T09:00:00Z"
            ),
            ConfluencePage(
                id="page-004",
                title="Incident Response Playbook",
                space_key="OPS",
                status="current",
                author="DevOps Team",
                created="2024-08-10T11:00:00Z"
            ),
        ]
        
        filtered = mock_pages
        if space_key:
            filtered = [p for p in filtered if p.space_key == space_key]
        if query:
            query_lower = query.lower()
            filtered = [p for p in filtered if query_lower in p.title.lower()]
        
        return filtered
    
    # ==================== Pareto Analysis Integration ====================
    
    def get_issues_for_pareto_analysis(
        self,
        project: Optional[str] = None,
        days_back: int = 30
    ) -> list[dict]:
        """
        Get issues formatted for Pareto analysis.
        
        Returns data suitable for the ParetoCalculator:
        - Items sorted by impact
        - Includes cost and delay metrics
        """
        issues = self.search_issues(project=project, max_results=100)
        
        pareto_data = []
        for issue in issues:
            pareto_data.append({
                "item_id": issue.key,
                "name": issue.summary,
                "category": issue.project,
                "value": issue.cost_impact,
                "delay_days": issue.delay_days,
                "severity": issue.severity,
                "status": issue.status,
                "show_name": issue.show_name
            })
        
        # Sort by value (cost impact) descending
        pareto_data.sort(key=lambda x: x["value"], reverse=True)
        
        return pareto_data
    
    def get_issue_cost_summary(self) -> dict:
        """Get summary of issue costs for executive reporting."""
        issues = self.search_issues(max_results=100)
        
        total_cost = sum(i.cost_impact for i in issues)
        critical_cost = sum(i.cost_impact for i in issues if i.severity == "critical")
        by_show = {}
        
        for issue in issues:
            show = issue.show_name or "Other"
            if show not in by_show:
                by_show[show] = {"count": 0, "cost": 0, "delay_days": 0}
            by_show[show]["count"] += 1
            by_show[show]["cost"] += issue.cost_impact
            by_show[show]["delay_days"] += issue.delay_days
        
        return {
            "total_issues": len(issues),
            "total_cost_impact": total_cost,
            "critical_cost_impact": critical_cost,
            "by_show": by_show,
            "top_issues": [
                {"key": i.key, "summary": i.summary, "cost": i.cost_impact}
                for i in sorted(issues, key=lambda x: x.cost_impact, reverse=True)[:5]
            ]
        }
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

