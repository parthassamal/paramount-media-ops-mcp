"""
MCP Tools package.

v1: LLM-callable analysis tools (churn, complaints, production, revenue, campaigns)
v2: RCA pipeline tools (evidence capture, test matching, test generation)
"""

from mcp.tools.analyze_churn_root_cause import create_tool as create_analyze_churn
from mcp.tools.analyze_complaint_themes import create_tool as create_analyze_complaints
from mcp.tools.analyze_production_risk import create_tool as create_analyze_production
from mcp.tools.forecast_revenue_with_constraints import create_tool as create_forecast_revenue
from mcp.tools.generate_retention_campaign import create_tool as create_generate_campaign

__all__ = [
    "create_analyze_churn",
    "create_analyze_complaints",
    "create_analyze_production",
    "create_forecast_revenue",
    "create_generate_campaign",
]
