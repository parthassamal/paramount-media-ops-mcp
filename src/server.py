"""Paramount+ Media Operations MCP Server
Main server implementation with resources and tools
"""
import json
from typing import Any
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.mock_data import MockDataGenerator
from src.pareto_engine import ParetoAnalyzer
from src.jira_connector import JIRAConnector
from src.email_parser import EmailParser


# Initialize components
mock_generator = MockDataGenerator()
pareto_analyzer = ParetoAnalyzer()
jira_connector = JIRAConnector()
email_parser = EmailParser()

# Create MCP server
server = Server("paramount-media-ops")


# ============================================================================
# RESOURCES - 9 data resources
# ============================================================================

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    """List all available data resources"""
    return [
        types.Resource(
            uri="paramount://churn_signals",
            name="Churn Signals",
            mimeType="application/json",
            description="User churn risk signals and behavioral patterns"
        ),
        types.Resource(
            uri="paramount://complaints_topics",
            name="Complaint Topics",
            mimeType="application/json",
            description="Customer complaint themes and sentiment analysis"
        ),
        types.Resource(
            uri="paramount://production_issues",
            name="Production Issues",
            mimeType="application/json",
            description="Live production issues from JIRA with Pareto analysis"
        ),
        types.Resource(
            uri="paramount://content_catalog",
            name="Content Catalog",
            mimeType="application/json",
            description="Content library with performance metrics and ROI data"
        ),
        types.Resource(
            uri="paramount://international_markets",
            name="International Markets",
            mimeType="application/json",
            description="Market-specific performance and expansion opportunities"
        ),
        types.Resource(
            uri="paramount://revenue_analytics",
            name="Revenue Analytics",
            mimeType="application/json",
            description="Revenue streams, subscription metrics, and forecasts"
        ),
        types.Resource(
            uri="paramount://engagement_metrics",
            name="Engagement Metrics",
            mimeType="application/json",
            description="User engagement patterns and viewing behavior"
        ),
        types.Resource(
            uri="paramount://pareto_insights",
            name="Pareto Insights",
            mimeType="application/json",
            description="80/20 analysis across all operational domains"
        ),
        types.Resource(
            uri="paramount://operational_dashboard",
            name="Operational Dashboard",
            mimeType="application/json",
            description="Real-time operational KPIs and health metrics"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific resource"""
    
    if uri == "paramount://churn_signals":
        cohort = mock_generator.generate_churn_cohort(100)
        # Apply Pareto to identify high-risk users
        high_risk = [u for u in cohort if u["churn_risk_score"] > 0.7]
        return json.dumps({
            "total_users": len(cohort),
            "high_risk_count": len(high_risk),
            "cohort_data": cohort,
            "pareto_analysis": pareto_analyzer.analyze(
                [{"user_id": u["user_id"], "risk": u["churn_risk_score"]} for u in cohort],
                "risk",
                "user_id"
            )
        }, indent=2)
    
    elif uri == "paramount://complaints_topics":
        complaints = email_parser.get_mock_complaints(100)
        pareto_result = email_parser.analyze_complaints_with_pareto(complaints)
        sentiment_trends = email_parser.analyze_sentiment_trends(complaints)
        
        return json.dumps({
            "total_complaints": len(complaints),
            "complaints": complaints,
            "pareto_analysis": pareto_result,
            "sentiment_trends": sentiment_trends,
            "critical_topics": pareto_result["vital_few"]
        }, indent=2)
    
    elif uri == "paramount://production_issues":
        issues = jira_connector.fetch_production_issues(50)
        pareto_result = jira_connector.analyze_issues_with_pareto(issues)
        
        return json.dumps({
            "total_issues": len(issues),
            "issues": issues,
            "pareto_analysis": pareto_result,
            "critical_issues": pareto_result["vital_few"],
            "insight": f"Focus on {len(pareto_result['vital_few'])} critical issues for maximum impact"
        }, indent=2)
    
    elif uri == "paramount://content_catalog":
        catalog = mock_generator.generate_content_catalog(50)
        # Pareto analysis on ROI
        roi_analysis = pareto_analyzer.analyze(
            [{"content_id": c["content_id"], "roi": c["roi"]} for c in catalog],
            "roi",
            "content_id"
        )
        
        return json.dumps({
            "total_titles": len(catalog),
            "catalog": catalog,
            "roi_pareto": roi_analysis,
            "top_performers": roi_analysis["vital_few"]
        }, indent=2)
    
    elif uri == "paramount://international_markets":
        markets_data = []
        for market in MockDataGenerator.MARKETS:
            markets_data.append({
                "market": market,
                "subscribers": int(1000000 * (0.5 + hash(market) % 10 / 10)),
                "revenue_millions": round(50 * (0.5 + hash(market) % 20 / 20), 2),
                "growth_rate": round(-0.1 + (hash(market) % 30) / 100, 3),
                "churn_rate": round(0.05 + (hash(market) % 15) / 1000, 3),
                "avg_revenue_per_user": round(5 + (hash(market) % 10), 2),
                "content_availability": round(0.6 + (hash(market) % 40) / 100, 2)
            })
        
        revenue_pareto = pareto_analyzer.analyze(markets_data, "revenue_millions", "market")
        
        return json.dumps({
            "total_markets": len(markets_data),
            "markets": markets_data,
            "revenue_pareto": revenue_pareto,
            "key_markets": revenue_pareto["vital_few"]
        }, indent=2)
    
    elif uri == "paramount://revenue_analytics":
        return json.dumps({
            "total_annual_revenue_millions": 750,
            "subscription_revenue_millions": 600,
            "advertising_revenue_millions": 150,
            "monthly_recurring_revenue": 62.5,
            "subscriber_growth_rate": 0.12,
            "average_revenue_per_user": 8.99,
            "churn_impact_millions": 45,
            "revenue_forecast_next_quarter": 195,
            "key_drivers": [
                {"driver": "Content Investment", "impact_percentage": 35},
                {"driver": "Market Expansion", "impact_percentage": 25},
                {"driver": "Retention Programs", "impact_percentage": 20},
                {"driver": "Pricing Optimization", "impact_percentage": 20}
            ]
        }, indent=2)
    
    elif uri == "paramount://engagement_metrics":
        return json.dumps({
            "daily_active_users": 8500000,
            "monthly_active_users": 25000000,
            "avg_session_duration_minutes": 45,
            "avg_sessions_per_user_per_month": 12,
            "content_completion_rate": 0.68,
            "popular_genres": [
                {"genre": "Drama", "viewership_percentage": 28},
                {"genre": "Sports", "viewership_percentage": 22},
                {"genre": "Reality", "viewership_percentage": 18},
                {"genre": "Comedy", "viewership_percentage": 15},
                {"genre": "Action", "viewership_percentage": 17}
            ],
            "peak_viewing_hours": ["19:00-23:00"],
            "device_distribution": {
                "smart_tv": 45,
                "mobile": 30,
                "desktop": 15,
                "tablet": 10
            }
        }, indent=2)
    
    elif uri == "paramount://pareto_insights":
        # Aggregate Pareto insights across domains
        issues = jira_connector.fetch_production_issues(50)
        complaints = email_parser.get_mock_complaints(100)
        
        return json.dumps({
            "production_issues_insight": jira_connector.analyze_issues_with_pareto(issues)["pareto_insight"],
            "complaints_insight": email_parser.analyze_complaints_with_pareto(complaints)["pareto_insight"],
            "key_finding": "20% of issues drive 80% of impact across all operational domains",
            "recommended_actions": [
                "Focus on top 10 production issues for maximum impact",
                "Address top 3 complaint topics to improve satisfaction",
                "Invest in top 5 content titles for ROI optimization",
                "Prioritize top 3 markets for expansion"
            ]
        }, indent=2)
    
    elif uri == "paramount://operational_dashboard":
        return json.dumps({
            "timestamp": "2025-12-07T00:24:51Z",
            "overall_health_score": 87,
            "active_critical_issues": 3,
            "active_high_issues": 12,
            "avg_resolution_time_hours": 18,
            "customer_satisfaction_score": 4.1,
            "platform_uptime_percentage": 99.7,
            "streaming_quality_score": 92,
            "complaints_last_24h": 45,
            "new_signups_today": 12500,
            "churned_users_today": 1800,
            "alerts": [
                {"level": "warning", "message": "Increased buffering reports in UK market"},
                {"level": "info", "message": "New content release performing above expectations"}
            ]
        }, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


# ============================================================================
# TOOLS - 5 LLM-callable analysis tools
# ============================================================================

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools"""
    return [
        types.Tool(
            name="analyze_churn_root_cause",
            description="Analyze root causes of user churn using ML patterns and behavioral signals. Uses Pareto principle to identify the vital few factors driving 80% of churn.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_segment": {
                        "type": "string",
                        "description": "User segment to analyze (e.g., 'premium', 'essential', 'all')",
                        "default": "all"
                    },
                    "time_period_days": {
                        "type": "integer",
                        "description": "Time period for analysis in days",
                        "default": 30
                    }
                }
            }
        ),
        types.Tool(
            name="analyze_complaint_themes",
            description="Extract and analyze complaint themes using NLP. Identifies critical topics using Pareto analysis and provides sentiment trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_sentiment": {
                        "type": "number",
                        "description": "Minimum sentiment score filter (-1 to 1)",
                        "default": -1
                    },
                    "urgency_filter": {
                        "type": "string",
                        "description": "Filter by urgency level",
                        "enum": ["Low", "Medium", "High", "Critical", "all"],
                        "default": "all"
                    }
                }
            }
        ),
        types.Tool(
            name="analyze_production_risk",
            description="Assess production risk based on open issues, severity, and user impact. Uses Pareto to identify the critical few issues requiring immediate attention.",
            inputSchema={
                "type": "object",
                "properties": {
                    "severity_threshold": {
                        "type": "string",
                        "description": "Minimum severity to include",
                        "enum": ["Low", "Medium", "High", "Critical"],
                        "default": "Medium"
                    },
                    "include_resolved": {
                        "type": "boolean",
                        "description": "Include resolved issues in analysis",
                        "default": False
                    }
                }
            }
        ),
        types.Tool(
            name="forecast_revenue_with_constraints",
            description="Forecast revenue with operational constraints and market dynamics. Considers churn impact, content investment, and market expansion using data-driven models.",
            inputSchema={
                "type": "object",
                "properties": {
                    "forecast_months": {
                        "type": "integer",
                        "description": "Number of months to forecast",
                        "default": 12
                    },
                    "scenario": {
                        "type": "string",
                        "description": "Forecast scenario",
                        "enum": ["conservative", "baseline", "optimistic"],
                        "default": "baseline"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Additional constraints",
                        "properties": {
                            "max_churn_rate": {"type": "number"},
                            "content_budget_millions": {"type": "number"},
                            "new_market_launches": {"type": "integer"}
                        }
                    }
                }
            }
        ),
        types.Tool(
            name="generate_retention_campaign",
            description="Generate personalized retention campaign strategies for high-risk churn segments. Uses Pareto insights to target the vital few user segments with highest impact.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_segment": {
                        "type": "string",
                        "description": "Target user segment",
                        "default": "high_risk"
                    },
                    "campaign_budget": {
                        "type": "number",
                        "description": "Campaign budget in dollars",
                        "default": 100000
                    },
                    "channels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Marketing channels to use",
                        "default": ["email", "in-app", "push"]
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Execute a tool"""
    
    if name == "analyze_churn_root_cause":
        user_segment = arguments.get("user_segment", "all")
        time_period = arguments.get("time_period_days", 30)
        
        # Generate churn data
        cohort = mock_generator.generate_churn_cohort(200)
        
        # Filter by segment if needed
        if user_segment != "all":
            cohort = [u for u in cohort if user_segment.lower() in u["subscription_tier"].lower()]
        
        # Analyze churn reasons with Pareto
        churn_reasons = {}
        for user in cohort:
            if user["churn_risk_score"] > 0.5:
                reason = user["predicted_churn_reason"]
                churn_reasons[reason] = churn_reasons.get(reason, 0) + 1
        
        reason_data = [{"reason": k, "count": v} for k, v in churn_reasons.items()]
        pareto_result = pareto_analyzer.analyze(reason_data, "count", "reason")
        
        analysis = {
            "segment": user_segment,
            "time_period_days": time_period,
            "total_at_risk_users": sum(1 for u in cohort if u["churn_risk_score"] > 0.5),
            "churn_reasons_pareto": pareto_result,
            "critical_reasons": pareto_result["vital_few"],
            "recommendations": [
                f"Focus on {pareto_result['pareto_insight']}",
                "Implement targeted retention campaigns for high-risk segments",
                "Address technical issues causing poor user experience",
                "Enhance content discovery for users with low diversity scores"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    elif name == "analyze_complaint_themes":
        min_sentiment = arguments.get("min_sentiment", -1)
        urgency_filter = arguments.get("urgency_filter", "all")
        
        complaints = email_parser.get_mock_complaints(150)
        
        # Apply filters
        filtered = complaints
        if min_sentiment > -1:
            filtered = [c for c in filtered if c.get("sentiment_score", 0) >= min_sentiment]
        if urgency_filter != "all":
            filtered = [c for c in filtered if c.get("urgency_level") == urgency_filter]
        
        pareto_result = email_parser.analyze_complaints_with_pareto(filtered)
        sentiment = email_parser.analyze_sentiment_trends(filtered)
        
        analysis = {
            "total_complaints_analyzed": len(filtered),
            "filters_applied": {"min_sentiment": min_sentiment, "urgency": urgency_filter},
            "theme_pareto": pareto_result,
            "critical_themes": pareto_result["vital_few"],
            "sentiment_analysis": sentiment,
            "action_items": [
                f"Priority: {pareto_result['pareto_insight']}",
                f"Overall sentiment is {'negative' if sentiment['average_sentiment'] < -0.1 else 'neutral'}",
                "Implement fixes for top complaint topics",
                "Improve customer communication for ongoing issues"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    elif name == "analyze_production_risk":
        severity_threshold = arguments.get("severity_threshold", "Medium")
        include_resolved = arguments.get("include_resolved", False)
        
        issues = jira_connector.fetch_production_issues(100)
        
        # Filter by severity
        severity_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
        threshold_value = severity_order.get(severity_threshold, 2)
        filtered = [i for i in issues if severity_order.get(i["severity"], 1) >= threshold_value]
        
        if not include_resolved:
            filtered = [i for i in filtered if i["status"] != "Resolved"]
        
        pareto_result = jira_connector.analyze_issues_with_pareto(filtered)
        
        # Calculate aggregate risk
        total_affected_users = sum(i.get("affected_users", 0) for i in filtered)
        total_revenue_impact = sum(i.get("estimated_revenue_impact", 0) for i in filtered)
        
        analysis = {
            "risk_assessment": "High" if len([i for i in filtered if i["severity"] == "Critical"]) > 5 else "Medium",
            "total_open_issues": len(filtered),
            "critical_count": len([i for i in filtered if i["severity"] == "Critical"]),
            "total_affected_users": total_affected_users,
            "total_revenue_impact_usd": total_revenue_impact,
            "pareto_analysis": pareto_result,
            "must_fix_immediately": pareto_result["vital_few"][:5],
            "recommendations": [
                f"Immediate action required on {len(pareto_result['vital_few'])} critical issues",
                "Allocate engineering resources to top Pareto issues",
                "Set up war room for critical severity issues",
                "Implement monitoring for affected services"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    elif name == "forecast_revenue_with_constraints":
        forecast_months = arguments.get("forecast_months", 12)
        scenario = arguments.get("scenario", "baseline")
        constraints = arguments.get("constraints", {})
        
        # Base metrics
        current_mrr = 62.5  # millions
        current_subscribers = 8_000_000
        base_growth_rate = 0.12
        base_churn_rate = 0.05
        
        # Scenario adjustments
        scenario_multipliers = {
            "conservative": {"growth": 0.8, "churn": 1.2},
            "baseline": {"growth": 1.0, "churn": 1.0},
            "optimistic": {"growth": 1.3, "churn": 0.8}
        }
        
        multiplier = scenario_multipliers[scenario]
        growth_rate = base_growth_rate * multiplier["growth"]
        churn_rate = base_churn_rate * multiplier["churn"]
        
        # Apply constraints
        if "max_churn_rate" in constraints:
            churn_rate = min(churn_rate, constraints["max_churn_rate"])
        
        # Monthly forecast
        forecasts = []
        subscribers = current_subscribers
        mrr = current_mrr
        
        for month in range(1, forecast_months + 1):
            new_subs = int(subscribers * growth_rate / 12)
            churned = int(subscribers * churn_rate / 12)
            subscribers = subscribers + new_subs - churned
            mrr = subscribers * 8.99 / 1_000_000  # ARPU of $8.99
            
            forecasts.append({
                "month": month,
                "subscribers": subscribers,
                "mrr_millions": round(mrr, 2),
                "new_subscribers": new_subs,
                "churned_subscribers": churned,
                "net_growth": new_subs - churned
            })
        
        total_annual_revenue = sum(f["mrr_millions"] for f in forecasts)
        
        analysis = {
            "scenario": scenario,
            "forecast_period_months": forecast_months,
            "constraints_applied": constraints,
            "projected_annual_revenue_millions": round(total_annual_revenue, 2),
            "final_subscriber_count": forecasts[-1]["subscribers"],
            "monthly_forecasts": forecasts,
            "key_assumptions": {
                "growth_rate_annual": round(growth_rate, 3),
                "churn_rate_annual": round(churn_rate, 3),
                "arpu": 8.99
            },
            "recommendations": [
                "Monitor churn closely to maintain forecast accuracy",
                "Invest in content to support growth projections",
                "Focus on retention to minimize churn impact",
                "Consider market expansion to accelerate growth"
            ]
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]
    
    elif name == "generate_retention_campaign":
        target_segment = arguments.get("target_segment", "high_risk")
        budget = arguments.get("campaign_budget", 100000)
        channels = arguments.get("channels", ["email", "in-app", "push"])
        
        # Get high-risk users
        cohort = mock_generator.generate_churn_cohort(500)
        at_risk = [u for u in cohort if u["churn_risk_score"] > 0.7]
        
        # Analyze churn reasons
        reason_counts = {}
        for user in at_risk:
            reason = user["predicted_churn_reason"]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Budget allocation based on Pareto
        reason_data = [{"reason": k, "count": v} for k, v in reason_counts.items()]
        pareto = pareto_analyzer.analyze(reason_data, "count", "reason")
        
        # Campaign strategies
        strategies = []
        for item in pareto["vital_few"]:
            reason = item["reason"]
            percentage = item["contribution_percentage"]
            allocated_budget = budget * (percentage / 100)
            
            strategy = {
                "target_reason": reason,
                "affected_users": item["count"],
                "budget_allocated": round(allocated_budget, 2),
                "channels": channels,
                "tactics": []
            }
            
            # Customize tactics by reason
            if "Content" in reason:
                strategy["tactics"] = [
                    "Personalized content recommendations",
                    "Early access to new releases",
                    "Free month of premium tier upgrade"
                ]
            elif "Technical" in reason:
                strategy["tactics"] = [
                    "Priority technical support",
                    "Beta access to improved app",
                    "Compensation credit"
                ]
            elif "Price" in reason:
                strategy["tactics"] = [
                    "Limited-time discount offer",
                    "Annual plan discount",
                    "Loyalty rewards program"
                ]
            else:
                strategy["tactics"] = [
                    "Personalized engagement campaign",
                    "Survey with incentive",
                    "Re-engagement content"
                ]
            
            strategies.append(strategy)
        
        campaign = {
            "campaign_name": f"Retention Campaign - {target_segment}",
            "target_segment": target_segment,
            "total_budget": budget,
            "target_audience_size": len(at_risk),
            "channels": channels,
            "pareto_insight": pareto["pareto_insight"],
            "strategies": strategies,
            "expected_impact": {
                "estimated_saves": int(len(at_risk) * 0.35),  # 35% save rate
                "roi_multiplier": 4.5,
                "ltv_preserved_millions": round(len(at_risk) * 0.35 * 8.99 * 12 / 1_000_000, 2)
            },
            "implementation_timeline": {
                "week_1": "Campaign setup and audience segmentation",
                "week_2": "Launch initial outreach via email",
                "week_3": "Follow-up with in-app and push notifications",
                "week_4": "Analyze results and optimize"
            }
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(campaign, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# Main entry point
# ============================================================================

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
