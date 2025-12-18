"""
AI-powered intelligence layer for Paramount+ Media Operations.

This package provides AI/ML capabilities including:
- Anomaly detection for streaming metrics and production issues
- Natural language query interface
- Predictive analytics for churn and revenue
- Semantic search for logs and complaints
- AI-generated insights and recommendations
"""

from mcp.ai.anomaly_detector import AnomalyDetector, Anomaly
from mcp.ai.insights_generator import AIInsightsGenerator
from mcp.ai.predictive_analytics import PredictiveAnalytics

__all__ = [
    "AnomalyDetector",
    "Anomaly",
    "AIInsightsGenerator",
    "PredictiveAnalytics",
]

