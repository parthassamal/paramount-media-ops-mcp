"""
Data integration connectors for external services.

Provides unified interfaces to:
- JIRA: Production issue tracking and workflow management
- Conviva: Streaming Quality of Experience (QoE) metrics
- NewRelic: Application Performance Monitoring (APM) and Infrastructure
- Email: Support email parsing and complaint analysis
- Analytics: Internal subscriber and content analytics
- Content API: Content catalog and metadata
"""

from .jira_connector import JiraConnector
from .email_parser import EmailParser
from .analytics_client import AnalyticsClient
from .content_api import ContentAPIClient
from .conviva_client import ConvivaClient
from .newrelic_client import NewRelicClient

__all__ = [
    # Core integrations
    "JiraConnector",
    "EmailParser",
    "AnalyticsClient",
    "ContentAPIClient",
    
    # Monitoring integrations
    "ConvivaClient",
    "NewRelicClient",
]
