"""
Conviva client for streaming Quality of Experience (QoE) metrics.

Provides interface to Conviva Insights API for video playback analytics,
buffering metrics, and viewer experience data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import structlog
import httpx

from config import settings
from mcp.pareto import ParetoCalculator

logger = structlog.get_logger()


@dataclass
class ConvivaMetrics:
    """Container for Conviva QoE metrics."""
    plays: int = 0
    concurrent_plays: int = 0
    buffering_ratio: float = 0.0
    video_start_failures: int = 0
    video_start_failure_rate: float = 0.0
    exits_before_video_start: int = 0
    ebvs_rate: float = 0.0
    average_bitrate: float = 0.0
    rebuffering_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plays": self.plays,
            "concurrent_plays": self.concurrent_plays,
            "buffering_ratio": round(self.buffering_ratio, 4),
            "video_start_failures": self.video_start_failures,
            "video_start_failure_rate": round(self.video_start_failure_rate, 4),
            "exits_before_video_start": self.exits_before_video_start,
            "ebvs_rate": round(self.ebvs_rate, 4),
            "average_bitrate": round(self.average_bitrate, 2),
            "rebuffering_ratio": round(self.rebuffering_ratio, 4)
        }
    
    def get_health_status(self) -> str:
        """Determine overall health status based on thresholds."""
        if (self.buffering_ratio > settings.conviva_buffering_threshold or
            self.video_start_failure_rate > settings.conviva_vsf_threshold or
            self.ebvs_rate > settings.conviva_ebvs_threshold):
            return "critical"
        elif (self.buffering_ratio > settings.conviva_buffering_threshold * 0.7 or
              self.video_start_failure_rate > settings.conviva_vsf_threshold * 0.7):
            return "warning"
        return "healthy"


class ConvivaClient:
    """
    Client for Conviva Insights API to fetch streaming QoE metrics.
    
    Provides access to:
    - Buffering and rebuffering metrics
    - Video start failures and exits before video start
    - Bitrate and quality metrics
    - Geographic and device breakdowns
    - CDN performance analysis
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize Conviva client.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.enabled = settings.conviva_enabled
        self.api_url = settings.conviva_api_url.rstrip('/')
        self.customer_key = settings.conviva_customer_key
        self.api_key = settings.conviva_api_key
        self.timeout = settings.conviva_request_timeout
        self.filter_client = settings.conviva_filter_client
        
        # Parse configured metrics and dimensions
        self.metrics = [m.strip() for m in settings.conviva_metrics.split(',')]
        self.dimensions = [d.strip() for d in settings.conviva_dimensions.split(',')]
        
        # Initialize Pareto calculator
        self.pareto = ParetoCalculator()
        
        if self.mock_mode:
            logger.info("conviva_client_initialized", mode="mock")
        else:
            self._validate_credentials()
            logger.info("conviva_client_initialized", mode="live", url=self.api_url)
    
    def _validate_credentials(self):
        """Validate Conviva credentials are configured."""
        if not self.customer_key or not self.api_key:
            logger.warning(
                "conviva_credentials_missing",
                message="Conviva API credentials not configured. Set CONVIVA_CUSTOMER_KEY and CONVIVA_API_KEY."
            )
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Generate authentication headers for Conviva API."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Conviva API.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            params: Query parameters
            data: Request body for POST
        
        Returns:
            JSON response as dictionary
        """
        url = f"{self.api_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_auth_header(),
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(
                    "conviva_api_error",
                    status_code=e.response.status_code,
                    url=url,
                    error=str(e)
                )
                raise
            except httpx.RequestError as e:
                logger.error(
                    "conviva_request_error",
                    url=url,
                    error=str(e)
                )
                raise
    
    def _generate_mock_metrics(
        self,
        dimension: Optional[str] = None,
        dimension_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate realistic mock Conviva metrics."""
        import random
        random.seed(settings.random_seed + hash(str(dimension_value)))
        
        # Base metrics with realistic values
        base_metrics = ConvivaMetrics(
            plays=random.randint(50000, 500000),
            concurrent_plays=random.randint(5000, 50000),
            buffering_ratio=random.uniform(0.005, 0.04),
            video_start_failures=random.randint(100, 5000),
            exits_before_video_start=random.randint(50, 2000),
            average_bitrate=random.uniform(3000, 8000),
            rebuffering_ratio=random.uniform(0.002, 0.03)
        )
        
        # Add dimension-specific variations BEFORE calculating rates
        if dimension == "country":
            if dimension_value in ["IN", "BR", "ID"]:
                # Higher buffering in emerging markets
                base_metrics.buffering_ratio *= 1.5
                base_metrics.rebuffering_ratio *= 1.5
            elif dimension_value in ["US", "UK", "DE"]:
                # Better performance in developed markets
                base_metrics.buffering_ratio *= 0.7
                base_metrics.rebuffering_ratio *= 0.7
        
        elif dimension == "device_type":
            if dimension_value == "mobile":
                base_metrics.buffering_ratio *= 1.2
                base_metrics.average_bitrate *= 0.6
            elif dimension_value == "smart_tv":
                base_metrics.average_bitrate *= 1.2
        
        elif dimension == "cdn":
            if dimension_value == "cdn_backup":
                base_metrics.buffering_ratio *= 2.0
                base_metrics.video_start_failures *= 2
        
        # Calculate rates AFTER dimension-specific variations
        if base_metrics.plays > 0:
            base_metrics.video_start_failure_rate = base_metrics.video_start_failures / base_metrics.plays
            base_metrics.ebvs_rate = base_metrics.exits_before_video_start / base_metrics.plays
        
        return base_metrics.to_dict()
    
    def get_qoe_metrics(
        self,
        time_range: str = "last_24_hours",
        dimension: Optional[str] = None,
        content_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Quality of Experience metrics.
        
        Args:
            time_range: Time range (last_1_hour, last_24_hours, last_7_days, last_30_days)
            dimension: Optional dimension to group by (device_type, country, isp, cdn)
            content_filter: Optional content name/ID filter
        
        Returns:
            QoE metrics dictionary
        """
        if self.mock_mode:
            return self._get_mock_qoe_metrics(time_range, dimension, content_filter)
        
        return self._fetch_qoe_metrics_sync(time_range, dimension, content_filter)
    
    def _get_mock_qoe_metrics(
        self,
        time_range: str,
        dimension: Optional[str],
        content_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Get mock QoE metrics."""
        import random
        random.seed(settings.random_seed)
        
        # Overall metrics
        overall = self._generate_mock_metrics()
        metrics = ConvivaMetrics(**{k: v for k, v in overall.items()})
        
        result = {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "health_status": metrics.get_health_status(),
            "thresholds": {
                "buffering": settings.conviva_buffering_threshold,
                "vsf": settings.conviva_vsf_threshold,
                "ebvs": settings.conviva_ebvs_threshold
            }
        }
        
        # Add dimension breakdown if requested
        if dimension:
            result["by_dimension"] = self._get_mock_dimension_breakdown(dimension)
            result["pareto_analysis"] = self._analyze_dimension_pareto(
                result["by_dimension"], 
                dimension
            )
        
        return result
    
    def _get_mock_dimension_breakdown(self, dimension: str) -> List[Dict[str, Any]]:
        """Generate mock dimension breakdown."""
        dimension_values = {
            "country": ["US", "IN", "UK", "CA", "BR", "DE", "FR", "AU", "JP", "MX"],
            "device_type": ["smart_tv", "mobile", "web", "streaming_device", "tablet"],
            "os": ["iOS", "Android", "tvOS", "Roku", "Fire TV", "Web", "Windows", "macOS"],
            "isp": ["Comcast", "AT&T", "Verizon", "Spectrum", "Cox", "T-Mobile", "Jio", "Airtel"],
            "cdn": ["cdn_primary", "cdn_secondary", "cdn_backup", "cdn_edge"],
            "content_type": ["movie", "series", "live", "sports", "news"]
        }
        
        values = dimension_values.get(dimension, ["value_1", "value_2", "value_3"])
        
        breakdown = []
        for value in values:
            metrics = self._generate_mock_metrics(dimension, value)
            breakdown.append({
                "dimension": dimension,
                "value": value,
                "metrics": metrics,
                "churn_impact": self._estimate_churn_impact(metrics)
            })
        
        # Sort by buffering ratio (highest impact first)
        return sorted(breakdown, key=lambda x: x["metrics"]["buffering_ratio"], reverse=True)
    
    def _estimate_churn_impact(self, metrics: Dict[str, Any]) -> float:
        """Estimate churn impact based on QoE metrics."""
        # Simplified model: higher buffering and VSF correlate with churn
        buffering_impact = metrics.get("buffering_ratio", 0) * 10
        vsf_impact = metrics.get("video_start_failure_rate", 0) * 5
        ebvs_impact = metrics.get("ebvs_rate", 0) * 8
        
        # Normalize to 0-1 scale
        total_impact = min(1.0, buffering_impact + vsf_impact + ebvs_impact)
        return round(total_impact, 4)
    
    def _analyze_dimension_pareto(
        self,
        breakdown: List[Dict[str, Any]],
        dimension: str
    ) -> Dict[str, Any]:
        """Perform Pareto analysis on dimension breakdown."""
        if len(breakdown) < 2:
            return {"error": "Insufficient data for Pareto analysis"}
        
        # Analyze by churn impact
        try:
            items = [
                {
                    "id": item["value"],
                    "impact": item["churn_impact"],
                    "buffering_ratio": item["metrics"]["buffering_ratio"]
                }
                for item in breakdown
            ]
            
            result = self.pareto.analyze(items, impact_field="impact", id_field="id")
            
            return {
                "dimension": dimension,
                "top_20_percent_values": [
                    items[i]["id"] for i in result.top_20_percent_indices
                ],
                "top_20_percent_contribution": result.top_20_percent_contribution,
                "pareto_validated": result.is_pareto_valid,
                "insight": self._generate_pareto_insight(dimension, result, items)
            }
        except ValueError as e:
            return {"error": str(e)}
    
    def _generate_pareto_insight(
        self,
        dimension: str,
        result: Any,
        items: List[Dict]
    ) -> str:
        """Generate human-readable Pareto insight."""
        top_count = len(result.top_20_percent_indices)
        contribution = result.top_20_percent_contribution * 100
        top_values = [items[i]["id"] for i in result.top_20_percent_indices]
        
        return (
            f"Top {top_count} {dimension}(s) ({', '.join(top_values)}) "
            f"account for {contribution:.1f}% of streaming quality issues. "
            f"Focus optimization efforts on these segments."
        )
    
    def _fetch_qoe_metrics_sync(
        self,
        time_range: str,
        dimension: Optional[str],
        content_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch from real Conviva API (synchronous wrapper)."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self._fetch_qoe_metrics_async(time_range, dimension, content_filter)
        )
    
    async def _fetch_qoe_metrics_async(
        self,
        time_range: str,
        dimension: Optional[str],
        content_filter: Optional[str]
    ) -> Dict[str, Any]:
        """Fetch from real Conviva API."""
        # Build time range parameters
        time_ranges = {
            "last_1_hour": 1,
            "last_24_hours": 24,
            "last_7_days": 24 * 7,
            "last_30_days": 24 * 30
        }
        hours = time_ranges.get(time_range, 24)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        params = {
            "customer": self.customer_key,
            "start": start_time.isoformat() + "Z",
            "end": end_time.isoformat() + "Z",
            "metrics": ",".join(self.metrics),
            "filter": f"client_id={self.filter_client}"
        }
        
        if dimension:
            params["dimensions"] = dimension
        
        if content_filter:
            params["filter"] += f" AND asset_name={content_filter}"
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/metrics",
                params=params
            )
            
            return self._parse_conviva_response(response, dimension)
            
        except Exception as e:
            logger.error("conviva_fetch_failed", error=str(e))
            if settings.is_development:
                logger.warning("falling_back_to_mock_data")
                return self._get_mock_qoe_metrics(time_range, dimension, content_filter)
            raise
    
    def _parse_conviva_response(
        self,
        response: Dict[str, Any],
        dimension: Optional[str]
    ) -> Dict[str, Any]:
        """Parse Conviva API response into standardized format."""
        # This would parse the actual Conviva response format
        # For now, structure based on Conviva Insights API documentation
        
        data = response.get("data", {})
        
        result = {
            "time_range": response.get("time_range", ""),
            "timestamp": datetime.now().isoformat(),
            "overall": {
                "plays": data.get("plays", 0),
                "concurrent_plays": data.get("concurrent_plays", 0),
                "buffering_ratio": data.get("buffering_ratio", 0),
                "video_start_failures": data.get("video_start_failures", 0),
                "video_start_failure_rate": data.get("vsf_rate", 0),
                "exits_before_video_start": data.get("ebvs", 0),
                "ebvs_rate": data.get("ebvs_rate", 0),
                "average_bitrate": data.get("avg_bitrate", 0),
                "rebuffering_ratio": data.get("rebuffering_ratio", 0)
            }
        }
        
        # Determine health status
        metrics = ConvivaMetrics(**result["overall"])
        result["health_status"] = metrics.get_health_status()
        
        # Add dimension breakdown if present
        if dimension and "breakdown" in data:
            result["by_dimension"] = data["breakdown"]
            result["pareto_analysis"] = self._analyze_dimension_pareto(
                data["breakdown"], 
                dimension
            )
        
        return result
    
    def get_buffering_hotspots(self) -> Dict[str, Any]:
        """
        Identify geographic and device hotspots with high buffering.
        
        Returns:
            Hotspot analysis with Pareto insights
        """
        # Get metrics by country
        country_metrics = self.get_qoe_metrics(
            time_range="last_24_hours",
            dimension="country"
        )
        
        # Get metrics by device
        device_metrics = self.get_qoe_metrics(
            time_range="last_24_hours",
            dimension="device_type"
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "geographic_hotspots": country_metrics.get("by_dimension", [])[:5],
            "device_hotspots": device_metrics.get("by_dimension", [])[:3],
            "geographic_pareto": country_metrics.get("pareto_analysis", {}),
            "device_pareto": device_metrics.get("pareto_analysis", {}),
            "recommendations": self._generate_buffering_recommendations(
                country_metrics, device_metrics
            )
        }
    
    def _generate_buffering_recommendations(
        self,
        country_metrics: Dict[str, Any],
        device_metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on hotspots."""
        recommendations = []
        
        country_hotspots = country_metrics.get("by_dimension", [])
        if country_hotspots:
            top_country = country_hotspots[0]
            if top_country["metrics"]["buffering_ratio"] > settings.conviva_buffering_threshold:
                recommendations.append({
                    "priority": "high",
                    "area": "geographic",
                    "target": top_country["value"],
                    "action": f"Deploy additional CDN edge servers in {top_country['value']}",
                    "expected_impact": f"Reduce buffering by {top_country['metrics']['buffering_ratio']*50:.0f}%"
                })
        
        device_hotspots = device_metrics.get("by_dimension", [])
        if device_hotspots:
            top_device = device_hotspots[0]
            if top_device["metrics"]["buffering_ratio"] > settings.conviva_buffering_threshold:
                recommendations.append({
                    "priority": "high",
                    "area": "device",
                    "target": top_device["value"],
                    "action": f"Optimize video encoding for {top_device['value']} devices",
                    "expected_impact": "Improve video start time and reduce buffering"
                })
        
        return recommendations
    
    def get_content_performance(self, content_name: str) -> Dict[str, Any]:
        """
        Get QoE metrics for specific content.
        
        Args:
            content_name: Name of the content/show
        
        Returns:
            Content-specific QoE metrics
        """
        return self.get_qoe_metrics(
            time_range="last_7_days",
            content_filter=content_name
        )

