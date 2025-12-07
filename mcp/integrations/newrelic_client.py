"""
NewRelic client for Application Performance Monitoring (APM) and Infrastructure.

Provides interface to NewRelic GraphQL API and Insights API for:
- Application performance metrics (response time, throughput, errors)
- Infrastructure health (CPU, memory, disk)
- Custom NRQL queries for operational insights
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import httpx

from config import settings
from mcp.pareto import ParetoCalculator

logger = structlog.get_logger()


@dataclass
class APMMetrics:
    """Container for APM metrics."""
    response_time_avg: float = 0.0
    response_time_p95: float = 0.0
    throughput: float = 0.0
    error_rate: float = 0.0
    error_count: int = 0
    apdex_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "response_time_avg_ms": round(self.response_time_avg, 2),
            "response_time_p95_ms": round(self.response_time_p95, 2),
            "throughput_rpm": round(self.throughput, 2),
            "error_rate": round(self.error_rate, 4),
            "error_count": self.error_count,
            "apdex_score": round(self.apdex_score, 3)
        }
    
    def get_health_status(self) -> str:
        """Determine overall health status based on thresholds."""
        if (self.error_rate > settings.newrelic_error_rate_threshold or
            self.apdex_score < settings.newrelic_apdex_threshold * 0.8 or
            self.response_time_avg > settings.newrelic_response_time_threshold * 1000 * 1.5):
            return "critical"
        elif (self.error_rate > settings.newrelic_error_rate_threshold * 0.5 or
              self.apdex_score < settings.newrelic_apdex_threshold or
              self.response_time_avg > settings.newrelic_response_time_threshold * 1000):
            return "warning"
        return "healthy"


@dataclass
class InfraMetrics:
    """Container for infrastructure metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    host_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "disk_percent": round(self.disk_percent, 2),
            "network_rx_mbps": round(self.network_rx_bytes / 1_000_000, 2),
            "network_tx_mbps": round(self.network_tx_bytes / 1_000_000, 2),
            "host_count": self.host_count
        }
    
    def get_health_status(self) -> str:
        """Determine infrastructure health status."""
        if self.cpu_percent > 90 or self.memory_percent > 90 or self.disk_percent > 95:
            return "critical"
        elif self.cpu_percent > 75 or self.memory_percent > 80 or self.disk_percent > 85:
            return "warning"
        return "healthy"


class NewRelicClient:
    """
    Client for NewRelic APIs for APM and Infrastructure monitoring.
    
    Provides access to:
    - Application performance metrics (response time, errors, throughput)
    - Infrastructure health (CPU, memory, network)
    - Custom NRQL queries for ad-hoc analysis
    - Service dependency mapping
    - Incident and alert data
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize NewRelic client.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.enabled = settings.newrelic_enabled
        self.graphql_url = settings.newrelic_api_url
        self.insights_url = settings.newrelic_insights_api_url
        self.api_key = settings.newrelic_api_key
        self.account_id = settings.newrelic_account_id
        self.app_name = settings.newrelic_app_name
        self.timeout = settings.newrelic_request_timeout
        
        # Initialize Pareto calculator
        self.pareto = ParetoCalculator()
        
        if self.mock_mode:
            logger.info("newrelic_client_initialized", mode="mock")
        else:
            self._validate_credentials()
            logger.info("newrelic_client_initialized", mode="live", url=self.graphql_url)
    
    def _validate_credentials(self):
        """Validate NewRelic credentials are configured."""
        if not self.api_key or not self.account_id:
            logger.warning(
                "newrelic_credentials_missing",
                message="NewRelic API credentials not configured. Set NEWRELIC_API_KEY and NEWRELIC_ACCOUNT_ID."
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for NewRelic API."""
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _graphql_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GraphQL request to NewRelic API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            GraphQL response data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    self.graphql_url,
                    headers=self._get_headers(),
                    json={
                        "query": query,
                        "variables": variables or {}
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if "errors" in result:
                    logger.error("newrelic_graphql_error", errors=result["errors"])
                    raise ValueError(f"GraphQL errors: {result['errors']}")
                
                return result.get("data", {})
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "newrelic_api_error",
                    status_code=e.response.status_code,
                    error=str(e)
                )
                raise
            except httpx.RequestError as e:
                logger.error(
                    "newrelic_request_error",
                    error=str(e)
                )
                raise
    
    async def _nrql_request(self, query: str) -> Dict[str, Any]:
        """
        Execute NRQL query via Insights API.
        
        Args:
            query: NRQL query string
        
        Returns:
            Query results
        """
        url = f"{self.insights_url}/accounts/{self.account_id}/query"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params={"nrql": query}
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    "newrelic_nrql_error",
                    status_code=e.response.status_code,
                    query=query,
                    error=str(e)
                )
                raise
    
    def _generate_mock_apm_metrics(
        self,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate realistic mock APM metrics."""
        import random
        random.seed(settings.random_seed + hash(str(service)))
        
        # Base metrics with realistic values
        metrics = APMMetrics(
            response_time_avg=random.uniform(50, 500),
            response_time_p95=random.uniform(200, 2000),
            throughput=random.uniform(1000, 50000),
            error_rate=random.uniform(0.001, 0.02),
            apdex_score=random.uniform(0.75, 0.99)
        )
        
        # Service-specific variations (apply before calculating error_count)
        if service:
            if "auth" in service.lower():
                metrics.response_time_avg *= 0.5  # Auth is usually fast
                metrics.error_rate *= 0.3  # Critical, well-tested
            elif "video" in service.lower() or "stream" in service.lower():
                metrics.throughput *= 2  # High throughput
                metrics.response_time_avg *= 1.5  # More processing
            elif "payment" in service.lower():
                metrics.error_rate *= 0.1  # Very critical
                metrics.apdex_score = min(0.99, metrics.apdex_score * 1.05)
        
        # Calculate error count from rate and throughput AFTER service variations
        metrics.error_count = int(metrics.error_rate * metrics.throughput)
        
        return metrics.to_dict()
    
    def _generate_mock_infra_metrics(
        self,
        host_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate realistic mock infrastructure metrics."""
        import random
        random.seed(settings.random_seed + hash(str(host_type)))
        
        metrics = InfraMetrics(
            cpu_percent=random.uniform(20, 80),
            memory_percent=random.uniform(40, 85),
            disk_percent=random.uniform(30, 75),
            network_rx_bytes=random.randint(1_000_000, 100_000_000),
            network_tx_bytes=random.randint(500_000, 50_000_000),
            host_count=random.randint(5, 50)
        )
        
        # Host type variations
        if host_type:
            if "streaming" in host_type.lower() or "video" in host_type.lower():
                metrics.network_rx_bytes *= 3
                metrics.network_tx_bytes *= 5
                metrics.cpu_percent = min(95, metrics.cpu_percent * 1.3)
            elif "database" in host_type.lower() or "db" in host_type.lower():
                metrics.memory_percent = min(92, metrics.memory_percent * 1.2)
                metrics.disk_percent = min(88, metrics.disk_percent * 1.3)
            elif "cache" in host_type.lower() or "redis" in host_type.lower():
                metrics.memory_percent = min(95, metrics.memory_percent * 1.4)
        
        return metrics.to_dict()
    
    def get_apm_metrics(
        self,
        time_range: str = "last_1_hour",
        service_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Application Performance Monitoring metrics.
        
        Args:
            time_range: Time range (last_1_hour, last_24_hours, last_7_days)
            service_filter: Optional service name filter
        
        Returns:
            APM metrics dictionary
        """
        if self.mock_mode:
            return self._get_mock_apm_metrics(time_range, service_filter)
        
        return self._fetch_apm_metrics_sync(time_range, service_filter)
    
    def _get_mock_apm_metrics(
        self,
        time_range: str,
        service_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Get mock APM metrics."""
        import random
        random.seed(settings.random_seed)
        
        # Overall metrics
        overall = self._generate_mock_apm_metrics(service_filter)
        metrics = APMMetrics(
            response_time_avg=overall["response_time_avg_ms"],
            response_time_p95=overall["response_time_p95_ms"],
            throughput=overall["throughput_rpm"],
            error_rate=overall["error_rate"],
            error_count=overall["error_count"],
            apdex_score=overall["apdex_score"]
        )
        
        result = {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "application": self.app_name,
            "overall": overall,
            "health_status": metrics.get_health_status(),
            "thresholds": {
                "error_rate": settings.newrelic_error_rate_threshold,
                "apdex": settings.newrelic_apdex_threshold,
                "response_time_ms": settings.newrelic_response_time_threshold * 1000
            }
        }
        
        # Add service breakdown if not filtered
        if not service_filter:
            result["by_service"] = self._get_mock_service_breakdown()
            result["error_analysis"] = self._get_mock_error_analysis()
        
        return result
    
    def _get_mock_service_breakdown(self) -> List[Dict[str, Any]]:
        """Generate mock service breakdown."""
        services = [
            "streaming-api",
            "auth-service",
            "content-catalog",
            "payment-gateway",
            "recommendation-engine",
            "search-api",
            "user-profile",
            "analytics-ingestion",
            "notification-service",
            "cdn-origin"
        ]
        
        breakdown = []
        for service in services:
            metrics = self._generate_mock_apm_metrics(service)
            # Map dict keys to APMMetrics dataclass fields
            apm = APMMetrics(
                response_time_avg=metrics["response_time_avg_ms"],
                response_time_p95=metrics["response_time_p95_ms"],
                throughput=metrics["throughput_rpm"],
                error_rate=metrics["error_rate"],
                error_count=metrics["error_count"],
                apdex_score=metrics["apdex_score"]
            )
            breakdown.append({
                "service": service,
                "metrics": metrics,
                "health_status": apm.get_health_status(),
                "impact_score": self._calculate_service_impact(metrics)
            })
        
        # Sort by impact score (highest first)
        return sorted(breakdown, key=lambda x: x["impact_score"], reverse=True)
    
    def _calculate_service_impact(self, metrics: Dict[str, Any]) -> float:
        """Calculate service impact score based on metrics."""
        # Weighted impact score
        error_impact = metrics.get("error_rate", 0) * 100
        latency_impact = min(1.0, metrics.get("response_time_avg_ms", 0) / 2000) * 50
        apdex_impact = (1 - metrics.get("apdex_score", 1)) * 30
        throughput_weight = min(1.0, metrics.get("throughput_rpm", 0) / 50000)
        
        total_impact = (error_impact + latency_impact + apdex_impact) * throughput_weight
        return round(min(100, total_impact), 2)
    
    def _get_mock_error_analysis(self) -> Dict[str, Any]:
        """Generate mock error analysis."""
        import random
        random.seed(settings.random_seed)
        
        error_types = [
            {"type": "TimeoutException", "count": random.randint(100, 1000), "service": "streaming-api"},
            {"type": "AuthenticationError", "count": random.randint(50, 300), "service": "auth-service"},
            {"type": "DatabaseConnectionError", "count": random.randint(20, 150), "service": "content-catalog"},
            {"type": "RateLimitExceeded", "count": random.randint(30, 200), "service": "streaming-api"},
            {"type": "PaymentDeclined", "count": random.randint(10, 80), "service": "payment-gateway"},
            {"type": "ServiceUnavailable", "count": random.randint(5, 50), "service": "cdn-origin"}
        ]
        
        # Sort by count
        error_types.sort(key=lambda x: x["count"], reverse=True)
        
        total_errors = sum(e["count"] for e in error_types)
        
        # Add percentage and cumulative
        cumulative = 0
        for error in error_types:
            error["percentage"] = round(error["count"] / total_errors * 100, 2)
            cumulative += error["percentage"]
            error["cumulative_percentage"] = round(cumulative, 2)
        
        # Pareto analysis
        pareto_threshold = 80
        top_errors = [e for e in error_types if e["cumulative_percentage"] <= pareto_threshold]
        if not top_errors:
            top_errors = [error_types[0]] if error_types else []
        
        return {
            "total_errors": total_errors,
            "error_types": error_types,
            "pareto_analysis": {
                "top_errors_count": len(top_errors),
                "top_errors": [e["type"] for e in top_errors],
                "contribution": top_errors[-1]["cumulative_percentage"] if top_errors else 0,
                "insight": f"Top {len(top_errors)} error types account for {top_errors[-1]['cumulative_percentage'] if top_errors else 0}% of all errors"
            }
        }
    
    def _fetch_apm_metrics_sync(
        self,
        time_range: str,
        service_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch APM metrics synchronously."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._fetch_apm_metrics_async(time_range, service_filter)
        )
    
    async def _fetch_apm_metrics_async(
        self,
        time_range: str,
        service_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch APM metrics via GraphQL."""
        # Convert time range to SINCE clause
        time_clauses = {
            "last_1_hour": "1 HOUR AGO",
            "last_24_hours": "1 DAY AGO",
            "last_7_days": "7 DAYS AGO"
        }
        since = time_clauses.get(time_range, "1 HOUR AGO")
        
        # Build NRQL query
        nrql = f"""
        SELECT 
            average(duration) as avgDuration,
            percentile(duration, 95) as p95Duration,
            rate(count(*), 1 minute) as throughput,
            percentage(count(*), WHERE error IS TRUE) as errorRate,
            apdex(duration, t: 0.5) as apdexScore
        FROM Transaction 
        WHERE appName = '{self.app_name}'
        SINCE {since}
        """
        
        if service_filter:
            nrql += f" WHERE name LIKE '%{service_filter}%'"
        
        try:
            result = await self._nrql_request(nrql)
            return self._parse_apm_response(result, time_range)
        except Exception as e:
            logger.error("newrelic_apm_fetch_failed", error=str(e))
            if settings.is_development:
                logger.warning("falling_back_to_mock_data")
                return self._get_mock_apm_metrics(time_range, service_filter)
            raise
    
    def _parse_apm_response(
        self,
        response: Dict[str, Any],
        time_range: str
    ) -> Dict[str, Any]:
        """Parse NewRelic NRQL response."""
        results = response.get("results", [{}])[0]
        
        overall = {
            "response_time_avg_ms": results.get("avgDuration", 0) * 1000,
            "response_time_p95_ms": results.get("p95Duration", 0) * 1000,
            "throughput_rpm": results.get("throughput", 0),
            "error_rate": results.get("errorRate", 0) / 100,
            "apdex_score": results.get("apdexScore", 0)
        }
        
        metrics = APMMetrics(**{
            "response_time_avg": overall["response_time_avg_ms"],
            "response_time_p95": overall["response_time_p95_ms"],
            "throughput": overall["throughput_rpm"],
            "error_rate": overall["error_rate"],
            "apdex_score": overall["apdex_score"]
        })
        
        return {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "application": self.app_name,
            "overall": overall,
            "health_status": metrics.get_health_status()
        }
    
    def get_infrastructure_metrics(
        self,
        time_range: str = "last_1_hour",
        host_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get infrastructure metrics.
        
        Args:
            time_range: Time range (last_1_hour, last_24_hours, last_7_days)
            host_filter: Optional host name filter
        
        Returns:
            Infrastructure metrics dictionary
        """
        if self.mock_mode:
            return self._get_mock_infra_metrics(time_range, host_filter)
        
        return self._fetch_infra_metrics_sync(time_range, host_filter)
    
    def _get_mock_infra_metrics(
        self,
        time_range: str,
        host_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Get mock infrastructure metrics."""
        import random
        random.seed(settings.random_seed)
        
        overall = self._generate_mock_infra_metrics(host_filter)
        metrics = InfraMetrics(
            cpu_percent=overall["cpu_percent"],
            memory_percent=overall["memory_percent"],
            disk_percent=overall["disk_percent"]
        )
        
        result = {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "health_status": metrics.get_health_status()
        }
        
        # Add host breakdown if not filtered
        if not host_filter:
            result["by_host_type"] = self._get_mock_host_breakdown()
        
        return result
    
    def _get_mock_host_breakdown(self) -> List[Dict[str, Any]]:
        """Generate mock host breakdown."""
        host_types = [
            "streaming-servers",
            "api-servers",
            "database-cluster",
            "cache-cluster",
            "cdn-origin",
            "analytics-workers"
        ]
        
        breakdown = []
        for host_type in host_types:
            metrics = self._generate_mock_infra_metrics(host_type)
            infra = InfraMetrics(
                cpu_percent=metrics["cpu_percent"],
                memory_percent=metrics["memory_percent"],
                disk_percent=metrics["disk_percent"]
            )
            breakdown.append({
                "host_type": host_type,
                "metrics": metrics,
                "health_status": infra.get_health_status()
            })
        
        return breakdown
    
    def _fetch_infra_metrics_sync(
        self,
        time_range: str,
        host_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch infrastructure metrics synchronously."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._fetch_infra_metrics_async(time_range, host_filter)
        )
    
    async def _fetch_infra_metrics_async(
        self,
        time_range: str,
        host_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch infrastructure metrics via NRQL."""
        time_clauses = {
            "last_1_hour": "1 HOUR AGO",
            "last_24_hours": "1 DAY AGO",
            "last_7_days": "7 DAYS AGO"
        }
        since = time_clauses.get(time_range, "1 HOUR AGO")
        
        nrql = f"""
        SELECT 
            average(cpuPercent) as cpu,
            average(memoryUsedPercent) as memory,
            average(diskUsedPercent) as disk,
            uniqueCount(hostname) as hostCount
        FROM SystemSample
        SINCE {since}
        """
        
        if host_filter:
            nrql += f" WHERE hostname LIKE '%{host_filter}%'"
        
        try:
            result = await self._nrql_request(nrql)
            return self._parse_infra_response(result, time_range)
        except Exception as e:
            logger.error("newrelic_infra_fetch_failed", error=str(e))
            if settings.is_development:
                return self._get_mock_infra_metrics(time_range, host_filter)
            raise
    
    def _parse_infra_response(
        self,
        response: Dict[str, Any],
        time_range: str
    ) -> Dict[str, Any]:
        """Parse infrastructure NRQL response."""
        results = response.get("results", [{}])[0]
        
        overall = {
            "cpu_percent": results.get("cpu", 0),
            "memory_percent": results.get("memory", 0),
            "disk_percent": results.get("disk", 0),
            "host_count": results.get("hostCount", 0)
        }
        
        metrics = InfraMetrics(**overall)
        
        return {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "health_status": metrics.get_health_status()
        }
    
    def get_incidents(
        self,
        status: str = "open",
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get active incidents and alerts.
        
        Args:
            status: Incident status (open, closed, all)
            priority: Priority filter (critical, high, medium, low)
        
        Returns:
            Incident summary
        """
        if self.mock_mode:
            return self._get_mock_incidents(status, priority)
        
        # Real implementation would use NewRelic Alerts API
        return self._get_mock_incidents(status, priority)
    
    def _get_mock_incidents(
        self,
        status: str,
        priority: Optional[str]
    ) -> Dict[str, Any]:
        """Get mock incidents."""
        import random
        random.seed(settings.random_seed)
        
        incident_templates = [
            {"title": "High error rate on streaming-api", "priority": "critical", "service": "streaming-api"},
            {"title": "Memory pressure on cache cluster", "priority": "high", "service": "cache-cluster"},
            {"title": "Elevated response times on content-catalog", "priority": "medium", "service": "content-catalog"},
            {"title": "CDN origin connection issues", "priority": "high", "service": "cdn-origin"},
            {"title": "Database connection pool exhaustion", "priority": "critical", "service": "database"},
        ]
        
        incidents = []
        for i, template in enumerate(incident_templates):
            if priority and template["priority"] != priority:
                continue
            
            # Random status
            incident_status = random.choice(["open", "acknowledged", "resolved"])
            if status != "all" and incident_status != status:
                if status == "open" and incident_status == "resolved":
                    continue
            
            incidents.append({
                "id": f"INC-{1000 + i}",
                "title": template["title"],
                "priority": template["priority"],
                "status": incident_status,
                "service": template["service"],
                "opened_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "duration_minutes": random.randint(5, 240)
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_incidents": len(incidents),
            "by_priority": {
                "critical": len([i for i in incidents if i["priority"] == "critical"]),
                "high": len([i for i in incidents if i["priority"] == "high"]),
                "medium": len([i for i in incidents if i["priority"] == "medium"]),
                "low": len([i for i in incidents if i["priority"] == "low"])
            },
            "incidents": incidents
        }
    
    def run_nrql_query(self, query: str) -> Dict[str, Any]:
        """
        Execute custom NRQL query.
        
        Args:
            query: NRQL query string
        
        Returns:
            Query results
        """
        if self.mock_mode:
            return {"mock": True, "message": "NRQL queries not available in mock mode"}
        
        return self._run_nrql_query_sync(query)
    
    def _run_nrql_query_sync(self, query: str) -> Dict[str, Any]:
        """Synchronous wrapper for NRQL query."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._nrql_request(query))
    
    def get_operational_health_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive operational health summary.
        
        Returns:
            Combined APM, infrastructure, and incident summary
        """
        apm = self.get_apm_metrics(time_range="last_1_hour")
        infra = self.get_infrastructure_metrics(time_range="last_1_hour")
        incidents = self.get_incidents(status="open")
        
        # Determine overall health
        health_scores = {
            "healthy": 3,
            "warning": 2,
            "critical": 1
        }
        
        apm_score = health_scores.get(apm.get("health_status", "healthy"), 3)
        infra_score = health_scores.get(infra.get("health_status", "healthy"), 3)
        
        # Weight by incident severity
        incident_penalty = incidents.get("by_priority", {}).get("critical", 0) * 2 + \
                          incidents.get("by_priority", {}).get("high", 0)
        
        overall_score = (apm_score + infra_score) / 2 - min(1, incident_penalty * 0.3)
        
        if overall_score >= 2.5:
            overall_health = "healthy"
        elif overall_score >= 1.5:
            overall_health = "warning"
        else:
            overall_health = "critical"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "apm_summary": {
                "health_status": apm.get("health_status"),
                "response_time_avg_ms": apm.get("overall", {}).get("response_time_avg_ms", 0),
                "error_rate": apm.get("overall", {}).get("error_rate", 0),
                "apdex_score": apm.get("overall", {}).get("apdex_score", 0)
            },
            "infrastructure_summary": {
                "health_status": infra.get("health_status"),
                "cpu_percent": infra.get("overall", {}).get("cpu_percent", 0),
                "memory_percent": infra.get("overall", {}).get("memory_percent", 0)
            },
            "incident_summary": {
                "open_incidents": incidents.get("total_incidents", 0),
                "critical_count": incidents.get("by_priority", {}).get("critical", 0),
                "high_count": incidents.get("by_priority", {}).get("high", 0)
            },
            "recommendations": self._generate_health_recommendations(apm, infra, incidents)
        }
    
    def _generate_health_recommendations(
        self,
        apm: Dict[str, Any],
        infra: Dict[str, Any],
        incidents: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on health data."""
        recommendations = []
        
        # APM recommendations
        if apm.get("health_status") in ["critical", "warning"]:
            error_rate = apm.get("overall", {}).get("error_rate", 0)
            if error_rate > settings.newrelic_error_rate_threshold:
                recommendations.append({
                    "priority": "high",
                    "area": "application",
                    "issue": f"Error rate ({error_rate*100:.2f}%) exceeds threshold",
                    "action": "Review error logs and deploy fixes for top error types",
                    "expected_impact": "Reduce user-facing errors and improve reliability"
                })
        
        # Infrastructure recommendations
        if infra.get("health_status") in ["critical", "warning"]:
            cpu = infra.get("overall", {}).get("cpu_percent", 0)
            if cpu > 75:
                recommendations.append({
                    "priority": "high" if cpu > 90 else "medium",
                    "area": "infrastructure",
                    "issue": f"High CPU utilization ({cpu:.1f}%)",
                    "action": "Scale out application instances or optimize code",
                    "expected_impact": "Improve response times and prevent outages"
                })
        
        # Incident recommendations
        critical_count = incidents.get("by_priority", {}).get("critical", 0)
        if critical_count > 0:
            recommendations.append({
                "priority": "critical",
                "area": "incidents",
                "issue": f"{critical_count} critical incident(s) active",
                "action": "Immediate investigation and escalation required",
                "expected_impact": "Prevent service degradation or outage"
            })
        
        return recommendations

