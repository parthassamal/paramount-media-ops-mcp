"""LLM-callable tools for MCP server."""

from .analyze_churn_root_cause import AnalyzeChurnRootCauseTool, create_tool as create_analyze_churn
from .analyze_complaint_themes import AnalyzeComplaintThemesTool, create_tool as create_analyze_complaints
from .analyze_production_risk import AnalyzeProductionRiskTool, create_tool as create_analyze_production
from .forecast_revenue_with_constraints import ForecastRevenueWithConstraintsTool, create_tool as create_forecast_revenue
from .generate_retention_campaign import GenerateRetentionCampaignTool, create_tool as create_generate_campaign

__all__ = [
    "AnalyzeChurnRootCauseTool",
    "AnalyzeComplaintThemesTool",
    "AnalyzeProductionRiskTool",
    "ForecastRevenueWithConstraintsTool",
    "GenerateRetentionCampaignTool",
    "create_analyze_churn",
    "create_analyze_complaints",
    "create_analyze_production",
    "create_forecast_revenue",
    "create_generate_campaign"
]
