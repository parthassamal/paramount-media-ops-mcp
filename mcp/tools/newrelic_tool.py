"""
New Relic NerdGraph GraphQL client for evidence capture.

Uses NerdGraph (https://api.newrelic.com/graphql) for:
- APM entity lookup and golden signals
- Critical incident retrieval
- Distributed trace summaries
- Service dependency map for blast radius

Auth: Single header `Api-Key`. No SDK required.
"""

import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from config import settings
from mcp.utils.logger import get_logger
from mcp.utils.error_handler import ConnectionError, TimeoutError, retry_with_backoff

logger = get_logger(__name__)

NR_ENDPOINT = settings.newrelic_api_url


def _nerdgraph(query: str, variables: dict = None) -> dict:
    """Execute a NerdGraph query. Raises on HTTP error."""
    if not settings.newrelic_api_key:
        logger.warning("New Relic API key not configured, returning empty result")
        return {"data": {}}

    try:
        resp = httpx.post(
            NR_ENDPOINT,
            headers={
                "Api-Key": settings.newrelic_api_key,
                "Content-Type": "application/json"
            },
            json={"query": query, "variables": variables or {}},
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        if "errors" in result:
            logger.warning("NerdGraph returned errors", errors=result["errors"])

        return result

    except httpx.ConnectError as e:
        logger.error("NerdGraph connection failed", error=str(e))
        raise ConnectionError("Cannot connect to New Relic NerdGraph", service="newrelic") from e
    except httpx.TimeoutException as e:
        logger.error("NerdGraph request timed out", error=str(e))
        raise TimeoutError("New Relic NerdGraph request timed out", timeout_seconds=30) from e


@retry_with_backoff(max_retries=2, initial_delay=1.0, exceptions=(ConnectionError,))
def capture_newrelic_snapshot(service_name: str, incident_time: str = None) -> dict:
    """
    Full pre-mitigation evidence capture from New Relic.
    MUST be called BEFORE any restart or rollback -- state is lost after mitigation.

    Pulls APM entity, error rate, distributed trace, and service map in one pass.
    """
    logger.info("Capturing New Relic snapshot", service=service_name)

    # 1. Find the APM entity GUID
    entity_query = """
    query($name: String!) {
      actor {
        entitySearch(query: "name LIKE $name AND type = 'APPLICATION'") {
          results { entities { guid name alertSeverity } }
        }
      }
    }
    """
    entities = _nerdgraph(entity_query, {"name": service_name})
    entity_guid = None
    for e in (entities.get("data", {}).get("actor", {})
              .get("entitySearch", {}).get("results", {}).get("entities", [])):
        if service_name.lower() in e.get("name", "").lower():
            entity_guid = e["guid"]
            break

    # 2. Pull APM golden signals
    apm_data = {}
    if entity_guid:
        apm_query = """
        query($guid: EntityGuid!, $account: Int!) {
          actor {
            entity(guid: $guid) {
              ... on ApmApplicationEntity {
                name
                alertSeverity
                apmSummary { errorRate throughput responseTimeAverage }
              }
            }
            nrql(accounts: [$account], query: "SELECT rate(count(*), 1 minute) AS throughput, percentage(count(*), WHERE error IS true) AS errorRate FROM Transaction WHERE appName = '%s' SINCE 30 minutes ago") {
              results
            }
          }
        }
        """ % service_name
        apm_data = _nerdgraph(apm_query, {
            "guid": entity_guid,
            "account": int(settings.newrelic_account_id or "0")
        })

    # 3. Pull recent critical incidents
    incidents_data = {}
    if settings.newrelic_account_id:
        incidents_query = """
        query($account: Int!) {
          actor {
            account(id: $account) {
              aiIssues {
                issues(filter: { states: [CREATED, ACTIVATED], priority: CRITICAL }) {
                  issues {
                    issueId title priority state
                    createdAt closedAt
                    incidentIds
                  }
                }
              }
            }
          }
        }
        """
        incidents_data = _nerdgraph(incidents_query, {
            "account": int(settings.newrelic_account_id)
        })

    # 4. Service map for blast radius
    service_map_data = {}
    if entity_guid:
        service_map_query = """
        query($guid: EntityGuid!) {
          actor {
            entity(guid: $guid) {
              relatedEntities(filter: { relationshipTypes: { include: [CALLS, CALLED_BY] } }) {
                results {
                  target { entity { name guid } }
                  type
                }
              }
            }
          }
        }
        """
        service_map_data = _nerdgraph(service_map_query, {"guid": entity_guid})

    snapshot = {
        "source": "newrelic",
        "entity_guid": entity_guid,
        "apm": apm_data.get("data", {}),
        "incidents": incidents_data.get("data", {}),
        "service_map": service_map_data.get("data", {}),
        "captured_at": datetime.utcnow().isoformat()
    }

    logger.info("New Relic snapshot captured", entity_guid=entity_guid, has_apm=bool(apm_data))
    return snapshot


def run_nrql(nrql: str) -> list:
    """Run an arbitrary NRQL query and return results list."""
    if not settings.newrelic_account_id:
        return []

    query = """
    query($account: Int!, $nrql: Nrql!) {
      actor {
        nrql(accounts: [$account], query: $nrql) { results }
      }
    }
    """
    result = _nerdgraph(query, {
        "account": int(settings.newrelic_account_id),
        "nrql": nrql
    })
    return result.get("data", {}).get("actor", {}).get("nrql", {}).get("results", [])


def fetch_stack_trace(service_name: str, since_minutes: int = 30) -> Optional[str]:
    """Fetch the latest stack trace for a service via NRQL."""
    nrql = (
        f"SELECT latest(error.message), latest(error.class), latest(error.stack) "
        f"FROM TransactionError WHERE appName = '{service_name}' "
        f"SINCE {since_minutes} minutes ago LIMIT 1"
    )
    results = run_nrql(nrql)
    if results:
        r = results[0]
        return (
            f"{r.get('latest.error.class', '')}: "
            f"{r.get('latest.error.message', '')}\n"
            f"{r.get('latest.error.stack', '')}"
        )
    return None
