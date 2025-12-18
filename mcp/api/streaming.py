"""
Streaming QoE and Infrastructure API Endpoints.

Provides Quality of Experience metrics, APM data, and infrastructure health.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from mcp.integrations import ConvivaClient, NewRelicClient
from config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/streaming", tags=["Streaming QoE & Infrastructure"])

# Initialize clients
conviva = ConvivaClient(mock_mode=settings.mock_mode)
newrelic = NewRelicClient(mock_mode=settings.mock_mode)


# Pydantic Models
class QoEMetrics(BaseModel):
    """Quality of Experience metrics model."""
    metric_name: str = Field(..., description="Metric identifier")
    value: float = Field(..., description="Metric value")
    threshold: float = Field(..., description="Alert threshold")
    status: str = Field(..., description="Health status (good/warning/critical)")
    unit: str = Field(..., description="Unit of measurement")

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "buffering_rate",
                "value": 1.2,
                "threshold": 2.0,
                "status": "good",
                "unit": "percentage"
            }
        }


class ServiceHealth(BaseModel):
    """Service health model."""
    service_name: str = Field(..., description="Service identifier")
    status: str = Field(..., description="Health status")
    response_time_ms: float = Field(..., description="Average response time")
    error_rate: float = Field(..., description="Error rate percentage")
    throughput_rpm: float = Field(..., description="Throughput (requests/min)")


# API Endpoints

@router.get(
    "/qoe/metrics",
    response_model=List[QoEMetrics],
    summary="Get QoE Metrics",
    description="""
    Retrieve streaming Quality of Experience (QoE) metrics from Conviva.
    
    **Metrics:**
    - Buffering Rate: % of viewing time spent buffering
    - Video Start Failures: Failed play attempts
    - EBVS (Exits Before Video Start): Users who leave before playback
    - Average Bitrate: Streaming quality indicator
    
    **Query Parameters:**
    - `dimension`: Filter by dimension (device, cdn, geo, content)
    - `content_id`: Filter by specific content
    - `time_range`: Time range in hours (default: 24)
    
    **Use Case:** Performance monitoring, CDN optimization, user experience tracking.
    """
)
async def get_qoe_metrics(
    dimension: Optional[str] = Query(None, description="Filter dimension"),
    content_id: Optional[str] = Query(None, description="Content filter"),
    time_range: int = Query(24, ge=1, le=168, description="Time range (hours)")
) -> List[QoEMetrics]:
    """Get streaming QoE metrics."""
    try:
        metrics_data = conviva.get_qoe_metrics(
            time_range=time_range,
            dimension=dimension,
            content_filter=content_id
        )
        
        # Convert to API model
        metrics = []
        
        metrics.append(QoEMetrics(
            metric_name="buffering_rate",
            value=metrics_data["buffering_rate"],
            threshold=settings.conviva_buffering_threshold,
            status="good" if metrics_data["buffering_rate"] < settings.conviva_buffering_threshold else "critical",
            unit="percentage"
        ))
        
        metrics.append(QoEMetrics(
            metric_name="video_start_failures",
            value=metrics_data["video_start_failures"],
            threshold=1000,
            status="good" if metrics_data["video_start_failures"] < 1000 else "warning",
            unit="count"
        ))
        
        metrics.append(QoEMetrics(
            metric_name="average_bitrate",
            value=metrics_data["average_bitrate_mbps"],
            threshold=2.5,
            status="good" if metrics_data["average_bitrate_mbps"] > 2.5 else "warning",
            unit="mbps"
        ))
        
        return metrics
        
    except Exception as e:
        logger.error("qoe_metrics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch QoE metrics: {str(e)}")


@router.get(
    "/qoe/buffering-hotspots",
    summary="Get Buffering Hotspots",
    description="""
    Identify buffering issues by dimension (device, CDN, geography, content).
    
    **Returns:**
    - Top problematic dimensions with high buffering
    - Recommended actions for remediation
    - Impact assessment (affected viewers)
    
    **Use Case:** Incident response, CDN optimization, device compatibility issues.
    """
)
async def get_buffering_hotspots(
    time_range: int = Query(24, description="Time range (hours)")
) -> Dict[str, Any]:
    """Get buffering hotspots analysis."""
    try:
        return conviva.get_buffering_hotspots(time_range=time_range)
    except Exception as e:
        logger.error("buffering_hotspots_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze buffering: {str(e)}")


@router.get(
    "/infrastructure/services",
    response_model=List[ServiceHealth],
    summary="Get Service Health",
    description="""
    Get health status of all backend services from NewRelic APM.
    
    **Services:**
    - API Gateway
    - Streaming Service
    - Authentication Service
    - Recommendation Engine
    - CDN Edge Servers
    
    **Metrics per service:**
    - Response time (ms)
    - Error rate (%)
    - Throughput (requests/min)
    - Health status
    
    **Use Case:** Service monitoring, incident detection, capacity planning.
    """
)
async def get_service_health(
    time_range: int = Query(1, ge=1, le=24, description="Time range (hours)")
) -> List[ServiceHealth]:
    """Get infrastructure service health."""
    try:
        services_data = newrelic.get_service_breakdown(time_range=time_range)
        
        return [
            ServiceHealth(
                service_name=svc["service"],
                status=svc["health_status"],
                response_time_ms=svc["response_time_avg"],
                error_rate=svc["error_rate"],
                throughput_rpm=svc["throughput"]
            )
            for svc in services_data
        ]
        
    except Exception as e:
        logger.error("service_health_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch service health: {str(e)}")


@router.get(
    "/infrastructure/incidents",
    summary="Get Active Incidents",
    description="""
    Retrieve active and recent incidents from NewRelic.
    
    **Returns:**
    - Open incidents with severity
    - Incident duration
    - Affected services
    - Alert policy triggered
    
    **Use Case:** Incident management, on-call workflows, escalation.
    """
)
async def get_incidents() -> List[Dict[str, Any]]:
    """Get active infrastructure incidents."""
    try:
        return newrelic.get_incidents()
    except Exception as e:
        logger.error("incidents_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch incidents: {str(e)}")


@router.get(
    "/infrastructure/operational-health",
    summary="Get Operational Health Summary",
    description="""
    Get comprehensive operational health score and executive summary.
    
    **Returns:**
    - Overall health score (0-100)
    - Status by category (APM, Infrastructure, QoE)
    - Critical alerts count
    - Recommendations for action
    
    **Use Case:** Executive dashboard, SLA reporting, health monitoring.
    """
)
async def get_operational_health() -> Dict[str, Any]:
    """Get operational health summary."""
    try:
        return newrelic.get_operational_health_summary()
    except Exception as e:
        logger.error("operational_health_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate health: {str(e)}")


@router.get(
    "/health",
    summary="Streaming APIs Health Check"
)
async def streaming_health_check():
    """Check Conviva and NewRelic integration health."""
    return {
        "conviva": {
            "status": "healthy" if settings.conviva_enabled else "disabled",
            "mock_mode": settings.mock_mode
        },
        "newrelic": {
            "status": "healthy" if settings.newrelic_enabled else "disabled",
            "mock_mode": settings.mock_mode
        },
        "timestamp": datetime.now().isoformat()
    }

