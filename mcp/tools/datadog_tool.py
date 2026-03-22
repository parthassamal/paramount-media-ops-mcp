"""
Datadog integration using the official datadog-api-client Python SDK.

Provides:
- Incident retrieval (v2 Incidents API)
- Monitor state capture (triggered monitors per service)
- Error log fetching (Logs API filtered by service + status:error)
- Full pre-mitigation snapshot combining all sources

Auth: DD_API_KEY and DD_APP_KEY auto-detected from environment variables.
"""

import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

from config import settings
from mcp.utils.logger import get_logger
from mcp.utils.error_handler import ConnectionError, ServiceError, retry_with_backoff

logger = get_logger(__name__)

# Set env vars so the SDK auto-configures
os.environ.setdefault("DD_API_KEY", settings.dd_api_key or "")
os.environ.setdefault("DD_APP_KEY", settings.dd_app_key or "")
os.environ.setdefault("DD_SITE", settings.dd_site or "datadoghq.com")


def _check_dd_configured() -> bool:
    """Check if Datadog credentials are configured."""
    if not settings.dd_api_key or not settings.dd_app_key:
        logger.warning("Datadog credentials not configured")
        return False
    return True


@retry_with_backoff(max_retries=2, initial_delay=1.0, exceptions=(ConnectionError,))
def fetch_dd_incidents(service_name: str, hours_back: int = 2) -> List[Dict[str, Any]]:
    """
    Pull recent TRIGGERED or STABLE incidents from Datadog Incident Management.
    Filters by service tag in title.
    """
    if not _check_dd_configured():
        return []

    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v2.api.incidents_api import IncidentsApi

        config = Configuration()
        config.unstable_operations["list_incidents"] = True
        incidents_out = []

        with ApiClient(config) as api_client:
            api = IncidentsApi(api_client)
            for incident in api.list_incidents_with_pagination():
                title = incident.attributes.title.lower() if incident.attributes.title else ""
                if service_name.lower() in title:
                    incidents_out.append({
                        "id": incident.id,
                        "title": incident.attributes.title,
                        "severity": str(incident.attributes.severity) if incident.attributes.severity else None,
                        "status": str(incident.attributes.status) if incident.attributes.status else None,
                        "created": str(incident.attributes.created) if incident.attributes.created else None,
                        "customer_impact": getattr(incident.attributes, 'customer_impact_summary', None)
                    })

        logger.info("Fetched Datadog incidents", service=service_name, count=len(incidents_out))
        return incidents_out

    except ImportError:
        logger.warning("datadog-api-client not installed, skipping incidents")
        return []
    except Exception as e:
        logger.error("Failed to fetch Datadog incidents", error=str(e))
        raise ConnectionError(f"Datadog incidents fetch failed: {e}", service="datadog") from e


@retry_with_backoff(max_retries=2, initial_delay=1.0, exceptions=(ConnectionError,))
def fetch_triggered_monitors(service_name: str) -> List[Dict[str, Any]]:
    """Pull currently triggered monitors for the service."""
    if not _check_dd_configured():
        return []

    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v1.api.monitors_api import MonitorsApi

        config = Configuration()
        monitors_out = []

        with ApiClient(config) as api_client:
            api = MonitorsApi(api_client)
            monitors = api.list_monitors(tags=f"service:{service_name}")
            for m in monitors:
                if hasattr(m, 'overall_state') and str(m.overall_state) in ('Alert', 'Warn'):
                    monitors_out.append({
                        "id": m.id,
                        "name": m.name,
                        "state": str(m.overall_state),
                        "query": m.query,
                        "message": m.message[:500] if m.message else None,
                        "tags": m.tags
                    })

        logger.info("Fetched Datadog monitors", service=service_name, count=len(monitors_out))
        return monitors_out

    except ImportError:
        logger.warning("datadog-api-client not installed, skipping monitors")
        return []
    except Exception as e:
        logger.error("Failed to fetch Datadog monitors", error=str(e))
        raise ConnectionError(f"Datadog monitors fetch failed: {e}", service="datadog") from e


@retry_with_backoff(max_retries=2, initial_delay=1.0, exceptions=(ConnectionError,))
def fetch_dd_error_logs(service_name: str, minutes_back: int = 30) -> List[Dict[str, Any]]:
    """Pull ERROR-level logs for the service from the last N minutes."""
    if not _check_dd_configured():
        return []

    try:
        from datadog_api_client import ApiClient, Configuration
        from datadog_api_client.v2.api.logs_api import LogsApi
        from datadog_api_client.v2.model.logs_list_request import LogsListRequest
        from datadog_api_client.v2.model.logs_query_filter import LogsQueryFilter

        config = Configuration()
        now = datetime.utcnow()
        start = now - timedelta(minutes=minutes_back)

        with ApiClient(config) as api_client:
            api = LogsApi(api_client)
            body = LogsListRequest(
                filter=LogsQueryFilter(
                    query=f"service:{service_name} status:error",
                    _from=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    to=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                ),
                page={"limit": 50}
            )
            response = api.list_logs(body=body)
            logs = []
            for log in (response.data or []):
                attrs = log.attributes
                logs.append({
                    "timestamp": str(attrs.timestamp) if attrs.timestamp else None,
                    "message": attrs.message,
                    "status": attrs.status,
                    "host": attrs.host,
                    "service": attrs.service
                })
            logger.info("Fetched Datadog error logs", service=service_name, count=len(logs))
            return logs

    except ImportError:
        logger.warning("datadog-api-client not installed, skipping logs")
        return []
    except Exception as e:
        logger.error("Failed to fetch Datadog error logs", error=str(e))
        raise ConnectionError(f"Datadog logs fetch failed: {e}", service="datadog") from e


def capture_datadog_snapshot(service_name: str) -> dict:
    """
    Full pre-mitigation evidence capture from Datadog.
    Combines incidents + monitor state + error logs into one snapshot.
    """
    logger.info("Capturing Datadog snapshot", service=service_name)

    snapshot = {
        "source": "datadog",
        "service_name": service_name,
        "captured_at": datetime.utcnow().isoformat(),
        "incidents": fetch_dd_incidents(service_name),
        "triggered_monitors": fetch_triggered_monitors(service_name),
        "error_logs": fetch_dd_error_logs(service_name)
    }

    logger.info(
        "Datadog snapshot captured",
        incidents=len(snapshot["incidents"]),
        monitors=len(snapshot["triggered_monitors"]),
        logs=len(snapshot["error_logs"])
    )
    return snapshot
