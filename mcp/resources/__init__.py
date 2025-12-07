"""Data resources for MCP server."""

from .churn_signals import ChurnSignalsResource, create_resource as create_churn_signals
from .complaints_topics import ComplaintsTopicsResource, create_resource as create_complaints_topics
from .production_issues import ProductionIssuesResource, create_resource as create_production_issues
from .content_catalog import ContentCatalogResource, create_resource as create_content_catalog
from .international_markets import InternationalMarketsResource, create_resource as create_international_markets
from .revenue_impact import RevenueImpactResource, create_resource as create_revenue_impact
from .retention_campaigns import RetentionCampaignsResource, create_resource as create_retention_campaigns
from .operational_efficiency import OperationalEfficiencyResource, create_resource as create_operational_efficiency
from .pareto_analysis import ParetoAnalysisResource, create_resource as create_pareto_analysis

__all__ = [
    "ChurnSignalsResource",
    "ComplaintsTopicsResource",
    "ProductionIssuesResource",
    "ContentCatalogResource",
    "InternationalMarketsResource",
    "RevenueImpactResource",
    "RetentionCampaignsResource",
    "OperationalEfficiencyResource",
    "ParetoAnalysisResource",
    "create_churn_signals",
    "create_complaints_topics",
    "create_production_issues",
    "create_content_catalog",
    "create_international_markets",
    "create_revenue_impact",
    "create_retention_campaigns",
    "create_operational_efficiency",
    "create_pareto_analysis"
]
