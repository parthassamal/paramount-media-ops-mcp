"""
Dynatrace Client for Application Performance Monitoring.

Provides access to Dynatrace APM, infrastructure monitoring, and observability data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
from config import settings

logger = structlog.get_logger()


class DynatraceClient:
    """
    Client for Dynatrace API.
    
    Provides access to:
    - Application performance metrics
    - Infrastructure monitoring
    - Problem detection
    - Service health
    - Real user monitoring (RUM)
    """
    
    def __init__(
        self,
        environment_url: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """
        Initialize Dynatrace client.
        
        Args:
            environment_url: Dynatrace environment URL (e.g., https://xxx.live.dynatrace.com)
            api_token: Dynatrace API token
        """
        self.environment_url = environment_url or settings.dynatrace_environment_url
        self.api_token = api_token or settings.dynatrace_api_token
        self.use_mock_data = not (self.environment_url and self.api_token)
        
        if self.use_mock_data:
            logger.info("Dynatrace client initialized in mock mode")
        else:
            logger.info(
                "Dynatrace client initialized",
                environment=self.environment_url
            )
    
    def get_application_metrics(self, timeframe: str = "-1h") -> Dict[str, Any]:
        """
        Get application performance metrics.
        
        Args:
            timeframe: Time range (e.g., "-1h", "-24h", "-7d")
            
        Returns:
            Application metrics including response times, throughput, errors
        """
        if self.use_mock_data:
            return self._get_mock_application_metrics()
        
        try:
            # In production, make API call to Dynatrace
            # endpoint = f"{self.environment_url}/api/v2/metrics/query"
            # For now, return mock data
            logger.info("Fetching Dynatrace application metrics", timeframe=timeframe)
            return self._get_mock_application_metrics()
        except Exception as e:
            logger.error("Failed to fetch Dynatrace application metrics", error=str(e))
            return {"error": str(e)}
    
    def get_infrastructure_health(self) -> Dict[str, Any]:
        """
        Get infrastructure health metrics.
        
        Returns:
            Infrastructure health including hosts, databases, services
        """
        if self.use_mock_data:
            return self._get_mock_infrastructure_health()
        
        try:
            logger.info("Fetching Dynatrace infrastructure health")
            return self._get_mock_infrastructure_health()
        except Exception as e:
            logger.error("Failed to fetch Dynatrace infrastructure health", error=str(e))
            return {"error": str(e)}
    
    def get_problems(self, state: str = "OPEN") -> Dict[str, Any]:
        """
        Get detected problems.
        
        Args:
            state: Problem state ("OPEN", "RESOLVED", "ALL")
            
        Returns:
            List of detected problems with severity and impact
        """
        if self.use_mock_data:
            return self._get_mock_problems(state)
        
        try:
            logger.info("Fetching Dynatrace problems", state=state)
            return self._get_mock_problems(state)
        except Exception as e:
            logger.error("Failed to fetch Dynatrace problems", error=str(e))
            return {"error": str(e)}
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get service health overview.
        
        Returns:
            Service health metrics and status
        """
        if self.use_mock_data:
            return self._get_mock_service_health()
        
        try:
            logger.info("Fetching Dynatrace service health")
            return self._get_mock_service_health()
        except Exception as e:
            logger.error("Failed to fetch Dynatrace service health", error=str(e))
            return {"error": str(e)}
    
    def get_user_experience(self) -> Dict[str, Any]:
        """
        Get real user monitoring (RUM) data.
        
        Returns:
            User experience metrics including load times, actions, errors
        """
        if self.use_mock_data:
            return self._get_mock_user_experience()
        
        try:
            logger.info("Fetching Dynatrace user experience data")
            return self._get_mock_user_experience()
        except Exception as e:
            logger.error("Failed to fetch Dynatrace user experience", error=str(e))
            return {"error": str(e)}
    
    # Mock data methods
    
    def _get_mock_application_metrics(self) -> Dict[str, Any]:
        """Generate mock application metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "timeframe": "-1h",
            "applications": [
                {
                    "name": "Paramount+ Web App",
                    "id": "APPLICATION-12345",
                    "metrics": {
                        "response_time_avg_ms": 245,
                        "response_time_p50_ms": 180,
                        "response_time_p95_ms": 520,
                        "response_time_p99_ms": 890,
                        "throughput_rpm": 15420,
                        "error_rate": 0.0085,
                        "apdex_score": 0.92,
                        "user_actions_per_minute": 8750,
                        "failure_rate": 0.012
                    },
                    "health": "HEALTHY"
                },
                {
                    "name": "Paramount+ Mobile API",
                    "id": "APPLICATION-12346",
                    "metrics": {
                        "response_time_avg_ms": 180,
                        "response_time_p50_ms": 145,
                        "response_time_p95_ms": 380,
                        "response_time_p99_ms": 650,
                        "throughput_rpm": 22340,
                        "error_rate": 0.0052,
                        "apdex_score": 0.95,
                        "user_actions_per_minute": 12500,
                        "failure_rate": 0.008
                    },
                    "health": "HEALTHY"
                }
            ],
            "overall": {
                "response_time_avg_ms": 208,
                "throughput_rpm": 37760,
                "error_rate": 0.0067,
                "apdex_score": 0.935,
                "total_user_actions": 21250
            }
        }
    
    def _get_mock_infrastructure_health(self) -> Dict[str, Any]:
        """Generate mock infrastructure health data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "hosts": {
                "total": 24,
                "healthy": 22,
                "warning": 2,
                "critical": 0,
                "details": [
                    {
                        "name": "prod-app-01",
                        "status": "HEALTHY",
                        "cpu_usage": 45.2,
                        "memory_usage": 62.8,
                        "disk_usage": 58.3
                    },
                    {
                        "name": "prod-app-02",
                        "status": "WARNING",
                        "cpu_usage": 82.5,
                        "memory_usage": 78.2,
                        "disk_usage": 61.4
                    }
                ]
            },
            "databases": {
                "total": 8,
                "healthy": 8,
                "connections": 245,
                "avg_query_time_ms": 12.5
            },
            "services": {
                "total": 45,
                "running": 43,
                "degraded": 2,
                "stopped": 0
            },
            "network": {
                "avg_latency_ms": 8.2,
                "packet_loss_rate": 0.0002,
                "bandwidth_utilization": 42.5
            }
        }
    
    def _get_mock_problems(self, state: str = "OPEN") -> Dict[str, Any]:
        """Generate mock problems data."""
        problems = [
            {
                "id": "PROBLEM-001",
                "title": "High response time on payment service",
                "severity": "PERFORMANCE",
                "status": "OPEN",
                "impact_level": "SERVICE",
                "affected_entities": 3,
                "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "root_cause": "Database connection pool exhaustion detected"
            },
            {
                "id": "PROBLEM-002",
                "title": "Increased error rate on user authentication",
                "severity": "ERROR",
                "status": "OPEN",
                "impact_level": "APPLICATION",
                "affected_entities": 1,
                "start_time": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "root_cause": "Redis cache timeout issues"
            }
        ]
        
        if state == "OPEN":
            problems = [p for p in problems if p["status"] == "OPEN"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_problems": len(problems),
            "problems": problems,
            "by_severity": {
                "PERFORMANCE": 1,
                "ERROR": 1,
                "AVAILABILITY": 0,
                "RESOURCE": 0
            }
        }
    
    def _get_mock_service_health(self) -> Dict[str, Any]:
        """Generate mock service health data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "services": [
                {
                    "name": "Authentication Service",
                    "id": "SERVICE-001",
                    "status": "HEALTHY",
                    "response_time_ms": 95,
                    "throughput_rpm": 5420,
                    "error_rate": 0.0032,
                    "dependencies": 2
                },
                {
                    "name": "Payment Processing",
                    "id": "SERVICE-002",
                    "status": "WARNING",
                    "response_time_ms": 450,
                    "throughput_rpm": 1240,
                    "error_rate": 0.0156,
                    "dependencies": 4
                },
                {
                    "name": "Content Delivery",
                    "id": "SERVICE-003",
                    "status": "HEALTHY",
                    "response_time_ms": 120,
                    "throughput_rpm": 18500,
                    "error_rate": 0.0018,
                    "dependencies": 3
                },
                {
                    "name": "User Profile Service",
                    "id": "SERVICE-004",
                    "status": "HEALTHY",
                    "response_time_ms": 78,
                    "throughput_rpm": 3200,
                    "error_rate": 0.0025,
                    "dependencies": 2
                }
            ],
            "overall_health": "WARNING",
            "total_services": 4,
            "healthy_services": 3,
            "warning_services": 1,
            "critical_services": 0
        }
    
    def _get_mock_user_experience(self) -> Dict[str, Any]:
        """Generate mock user experience data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "timeframe": "-1h",
            "metrics": {
                "avg_page_load_time_ms": 1850,
                "first_contentful_paint_ms": 680,
                "time_to_interactive_ms": 2100,
                "total_blocking_time_ms": 220,
                "cumulative_layout_shift": 0.08,
                "user_actions_per_session": 12.4,
                "bounce_rate": 0.18,
                "avg_session_duration_seconds": 420
            },
            "top_pages": [
                {
                    "url": "/browse",
                    "load_time_ms": 1650,
                    "views": 45200,
                    "bounce_rate": 0.12
                },
                {
                    "url": "/watch",
                    "load_time_ms": 2100,
                    "views": 38500,
                    "bounce_rate": 0.08
                },
                {
                    "url": "/home",
                    "load_time_ms": 1420,
                    "views": 52100,
                    "bounce_rate": 0.15
                }
            ],
            "errors": {
                "javascript_errors": 245,
                "ajax_errors": 78,
                "resource_errors": 34
            },
            "apdex_score": 0.89,
            "satisfaction_rate": 0.92
        }



