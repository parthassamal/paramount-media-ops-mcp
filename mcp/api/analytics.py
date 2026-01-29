"""
Analytics REST API Endpoints for Churn, LTV, and Subscriber Intelligence.

Provides subscriber analytics, churn prediction, and retention insights.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from datetime import datetime

from mcp.integrations import AnalyticsClient
from config import settings
from mcp.utils.error_handler import ServiceError, ValidationError, DataNotFoundError, retry_with_backoff
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Churn Intelligence"])

# Initialize Analytics client
analytics = AnalyticsClient(mock_mode=settings.mock_mode)


# Pydantic Models
class ChurnCohort(BaseModel):
    """Churn cohort model."""
    cohort_name: str = Field(..., description="Cohort identifier")
    subscriber_count: int = Field(..., description="Number of subscribers")
    churn_probability: float = Field(..., description="Churn probability (0-1)")
    risk_level: str = Field(..., description="Risk level (High/Medium/Low)")
    primary_reason: str = Field(..., description="Primary churn reason")
    revenue_at_risk: float = Field(..., description="Revenue at risk (USD)")

    class Config:
        json_schema_extra = {
            "example": {
                "cohort_name": "Reality TV Fans (3-6 months)",
                "subscriber_count": 125000,
                "churn_probability": 0.42,
                "risk_level": "High",
                "primary_reason": "Limited content in preferred genre",
                "revenue_at_risk": 450000.0
            }
        }


class LTVAnalysis(BaseModel):
    """Lifetime Value analysis model."""
    total_ltv_at_risk: float = Field(..., description="Total LTV at risk")
    ltv_by_cohort: Dict[str, float] = Field(..., description="LTV breakdown by cohort")
    avg_subscriber_ltv: float = Field(..., description="Average LTV per subscriber")


# API Endpoints

@router.get(
    "/churn/cohorts",
    response_model=List[ChurnCohort],
    summary="Get Churn Cohorts",
    description="""
    Retrieve subscriber cohorts with churn risk analysis.
    
    **Returns:**
    - Cohort segmentation by risk level
    - Churn probability for each cohort
    - Revenue at risk calculations
    - Primary churn reasons
    
    **Use Case:** Retention planning, targeted campaigns, risk assessment.
    
    **Algorithm:** Uses Pareto analysis to identify high-impact cohorts.
    """
)
async def get_churn_cohorts() -> List[ChurnCohort]:
    """Get subscriber churn cohorts with risk analysis."""
    try:
        cohorts = analytics.get_churn_cohorts()
        
        # Map integration fields to API model fields
        mapped_cohorts = []
        for cohort in cohorts:
            # Determine risk level based on churn_risk_score
            risk_score = cohort.get("churn_risk_score", 0)
            if risk_score >= 0.7:
                risk_level = "High"
            elif risk_score >= 0.4:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            mapped_cohorts.append(ChurnCohort(
                cohort_name=cohort.get("name", ""),
                subscriber_count=cohort.get("size", 0),
                churn_probability=cohort.get("churn_risk_score", 0),
                risk_level=risk_level,
                primary_reason=cohort.get("primary_churn_driver", "Unknown"),
                revenue_at_risk=cohort.get("financial_impact_30d", 0)
            ))
        
        return mapped_cohorts
    except Exception as e:
        logger.error("churn_cohorts_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch churn cohorts: {str(e)}")


@router.get(
    "/ltv/analysis",
    response_model=LTVAnalysis,
    summary="Get LTV Analysis",
    description="""
    Retrieve Lifetime Value (LTV) analysis across subscriber base.
    
    **Returns:**
    - Total LTV at risk from churn
    - LTV breakdown by cohort
    - Average LTV per subscriber
    
    **Use Case:** Financial forecasting, retention ROI, budget allocation.
    """
)
async def get_ltv_analysis() -> LTVAnalysis:
    """Get lifetime value analysis."""
    try:
        analysis = analytics.get_ltv_analysis()
        
        # Ensure required fields are present
        if "ltv_by_cohort" not in analysis:
            analysis["ltv_by_cohort"] = {}
        if "avg_subscriber_ltv" not in analysis:
            # Calculate from cohorts if available
            cohorts = analytics.get_churn_cohorts()
            total_subs = sum(c.get("size", 0) for c in cohorts)
            total_ltv = sum(c.get("avg_lifetime_value", 0) * c.get("size", 0) for c in cohorts)
            analysis["avg_subscriber_ltv"] = total_ltv / total_subs if total_subs > 0 else 0
        
        return LTVAnalysis(**analysis)
    except Exception as e:
        logger.error("ltv_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate LTV: {str(e)}")


@router.get(
    "/subscribers/stats",
    summary="Get Subscriber Statistics",
    description="""
    Get comprehensive subscriber metrics and KPIs.
    
    **Returns:**
    - Total active subscribers
    - Growth rate (MoM, YoY)
    - Churn rate
    - ARPU (Average Revenue Per User)
    - Engagement metrics
    """
)
async def get_subscriber_stats() -> Dict[str, Any]:
    """Get subscriber statistics."""
    try:
        cohorts = analytics.get_churn_cohorts()
        ltv = analytics.get_ltv_analysis()
        
        # Use "size" field from cohorts (not "subscriber_count")
        total_subscribers = sum(c.get("size", 0) for c in cohorts)
        
        # Calculate high risk based on churn_risk_score
        high_risk_count = sum(
            c.get("size", 0) for c in cohorts 
            if c.get("churn_risk_score", 0) >= 0.7
        )
        
        return {
            "total_subscribers": total_subscribers,
            "high_risk_subscribers": high_risk_count,
            "churn_rate": high_risk_count / total_subscribers if total_subscribers > 0 else 0,
            "total_ltv_at_risk": ltv.get("total_ltv_at_risk", 0),
            "avg_subscriber_ltv": ltv.get("avg_subscriber_ltv", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("subscriber_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}")


@router.get(
    "/health",
    summary="Analytics Health Check"
)
async def analytics_health_check():
    """Check Analytics integration health."""
    return {
        "status": "healthy" if settings.analytics_enabled else "disabled",
        "mock_mode": settings.mock_mode,
        "timestamp": datetime.now().isoformat()
    }

