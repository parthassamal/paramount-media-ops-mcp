"""
Data integration connectors for external services.

Provides unified interfaces to:
- JIRA: Production issue tracking and workflow management
- Confluence: Documentation and knowledge base
- Conviva: Streaming Quality of Experience (QoE) metrics
- NewRelic: Application Performance Monitoring (APM) and Infrastructure
- Figma: Design system and dashboard design integration
- Email: Support email parsing and complaint analysis
- Analytics: Internal subscriber and content analytics
- Content API: Content catalog and metadata

Atlassian Integration:
Uses mcp-atlassian (https://github.com/sooperset/mcp-atlassian) for JIRA/Confluence.
"""

from .jira_connector import JiraConnector
from .email_parser import EmailParser
from .analytics_client import AnalyticsClient
from .content_api import ContentAPIClient
from .conviva_client import ConvivaClient
from .newrelic_client import NewRelicClient
from .figma_client import FigmaClient
from .atlassian_client import AtlassianClient

__all__ = [
    # Core integrations
    "JiraConnector",
    "EmailParser",
    "AnalyticsClient",
    "ContentAPIClient",
    
    # Atlassian integrations (mcp-atlassian)
    "AtlassianClient",
    
    # Monitoring integrations
    "ConvivaClient",
    "NewRelicClient",
    
    # Design integrations
    "FigmaClient",
]
