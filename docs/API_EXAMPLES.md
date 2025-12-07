# API Examples

Complete examples for all resources and tools.

## Resources

### 1. Churn Signals

```bash
# Basic query
curl -X POST http://localhost:8000/resources/churn_signals/query \
  -H "Content-Type: application/json" \
  -d '{}'

# With parameters
curl -X POST http://localhost:8000/resources/churn_signals/query \
  -H "Content-Type: application/json" \
  -d '{
    "risk_threshold": 0.7,
    "min_cohort_size": 10000,
    "include_pareto": true
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/resources/churn_signals/query",
    json={"risk_threshold": 0.7}
)
data = response.json()
print(f"At risk: {data['data']['result']['retention_metrics']['total_at_risk_30d']}")
```

### 2. Complaints Topics

```bash
curl -X POST http://localhost:8000/resources/complaints_topics/query \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "min_volume": 500,
    "include_pareto": true
  }'
```

### 3. Production Issues

```bash
# All critical issues
curl -X POST http://localhost:8000/resources/production_issues/query \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "critical",
    "status": ["open", "blocked"]
  }'
```

### 4. Content Catalog

```bash
# Flagship sci-fi shows
curl -X POST http://localhost:8000/resources/content_catalog/query \
  -H "Content-Type: application/json" \
  -d '{
    "genre": "Sci-Fi",
    "tier": "flagship",
    "limit": 10
  }'
```

### 5. International Markets

```bash
curl -X POST http://localhost:8000/resources/international_markets/query \
  -H "Content-Type: application/json" \
  -d '{
    "region": "UK",
    "min_performance": 0.2
  }'
```

### 6. Revenue Impact

```bash
curl -X POST http://localhost:8000/resources/revenue_impact/query \
  -H "Content-Type: application/json" \
  -d '{
    "include_projections": true,
    "timeframe_days": 90
  }'
```

### 7. Retention Campaigns

```bash
# Active campaigns
curl -X POST http://localhost:8000/resources/retention_campaigns/query \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_status": "active",
    "min_effectiveness": 0.7
  }'
```

### 8. Operational Efficiency

```bash
curl -X POST http://localhost:8000/resources/operational_efficiency/query \
  -H "Content-Type: application/json" \
  -d '{
    "metric_type": "all",
    "timeframe_days": 30
  }'
```

### 9. Pareto Analysis

```bash
# Cross-dimensional analysis
curl -X POST http://localhost:8000/resources/pareto_analysis/query \
  -H "Content-Type: application/json" \
  -d '{
    "dimension": "all",
    "include_insights": true
  }'

# Specific dimension
curl -X POST http://localhost:8000/resources/pareto_analysis/query \
  -H "Content-Type: application/json" \
  -d '{"dimension": "churn"}'
```

## Tools

### 1. Analyze Churn Root Cause

```bash
# Analyze specific cohort
curl -X POST http://localhost:8000/tools/analyze_churn_root_cause/execute \
  -H "Content-Type: application/json" \
  -d '{
    "cohort_id": "COHORT-001",
    "include_recommendations": true
  }'

# Analyze all cohorts
curl -X POST http://localhost:8000/tools/analyze_churn_root_cause/execute \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Python:**
```python
import requests

result = requests.post(
    "http://localhost:8000/tools/analyze_churn_root_cause/execute",
    json={"cohort_id": "COHORT-001"}
).json()

for cause in result['data']['result']['root_causes']:
    print(f"{cause['cohort_name']}: {cause['primary_driver']}")
    print(f"  Financial Impact: ${cause['financial_impact']:,.0f}")
```

### 2. Analyze Complaint Themes

```bash
curl -X POST http://localhost:8000/tools/analyze_complaint_themes/execute \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "focus_on_fixable": true,
    "max_themes": 5
  }'
```

**Python:**
```python
result = requests.post(
    "http://localhost:8000/tools/analyze_complaint_themes/execute",
    json={"focus_on_fixable": true}
).json()

# Quick wins
for theme in result['data']['result']['prioritization']['quick_wins']:
    print(f"Quick Win: {theme['name']}")
    print(f"  Impact: ${theme['revenue_impact']:,.0f}")
    print(f"  Timeline: {theme['fix_timeline']}")
```

### 3. Analyze Production Risk

```bash
curl -X POST http://localhost:8000/tools/analyze_production_risk/execute \
  -H "Content-Type: application/json" \
  -d '{
    "severity_filter": "critical",
    "include_mitigation": true
  }'
```

**Python:**
```python
result = requests.post(
    "http://localhost:8000/tools/analyze_production_risk/execute",
    json={"include_mitigation": true}
).json()

risk = result['data']['result']['risk_assessment']
print(f"Risk Level: {risk['overall_risk_score']['level']}")
print(f"Risk Score: {risk['overall_risk_score']['score']}/10")

# Top delays
for issue in result['data']['result']['top_delay_drivers'][:3]:
    print(f"- {issue['title']}: {issue['delay_days']} days")
```

### 4. Forecast Revenue with Constraints

```bash
curl -X POST http://localhost:8000/tools/forecast_revenue_with_constraints/execute \
  -H "Content-Type: application/json" \
  -d '{
    "budget_constraint": 10000000,
    "timeline_months": 12,
    "scenario": "moderate"
  }'
```

**Python:**
```python
result = requests.post(
    "http://localhost:8000/tools/forecast_revenue_with_constraints/execute",
    json={
        "budget_constraint": 10000000,
        "timeline_months": 12,
        "scenario": "moderate"
    }
).json()

forecast = result['data']['result']['constrained_forecast']
print(f"Recovery: ${forecast['potential_recovery']:,.0f}")
print(f"ROI: {forecast['roi']}x")
print(f"Net Loss: ${forecast['net_loss']:,.0f}")
```

### 5. Generate Retention Campaign

```bash
curl -X POST http://localhost:8000/tools/generate_retention_campaign/execute \
  -H "Content-Type: application/json" \
  -d '{
    "cohort_id": "COHORT-001",
    "budget": 500000,
    "timeline_days": 45
  }'
```

**Python:**
```python
result = requests.post(
    "http://localhost:8000/tools/generate_retention_campaign/execute",
    json={
        "cohort_id": "COHORT-001",
        "budget": 500000
    }
).json()

campaign = result['data']['result']
print(f"Campaign: {campaign['campaign_name']}")
print(f"Target: {campaign['target_cohort']['at_risk']} subscribers")
print(f"Budget: ${campaign['budget']:,.0f}")

# Projected outcomes
moderate = campaign['projected_outcomes']['scenarios']['moderate']
print(f"Expected conversions: {moderate['conversions']}")
print(f"Revenue retained: ${moderate['revenue_retained_annual']:,.0f}")
```

## MCP Protocol Format

### Query Resource (Unified)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "resource": "churn_signals",
    "params": {
      "risk_threshold": 0.7
    }
  }'
```

### Execute Tool (Unified)

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "analyze_churn_root_cause",
    "params": {
      "cohort_id": "COHORT-001"
    }
  }'
```

## Python SDK Pattern

```python
class ParamountMCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def query_resource(self, resource: str, **params):
        response = requests.post(
            f"{self.base_url}/resources/{resource}/query",
            json=params
        )
        response.raise_for_status()
        return response.json()['data']['result']
    
    def execute_tool(self, tool: str, **params):
        response = requests.post(
            f"{self.base_url}/tools/{tool}/execute",
            json=params
        )
        response.raise_for_status()
        return response.json()['data']['result']

# Usage
client = ParamountMCPClient()

# Query
cohorts = client.query_resource("churn_signals", risk_threshold=0.7)
print(f"Found {len(cohorts['cohorts'])} at-risk cohorts")

# Execute
analysis = client.execute_tool("analyze_churn_root_cause", cohort_id="COHORT-001")
print(f"Root cause: {analysis['root_causes'][0]['primary_driver']}")
```

## Batch Operations

```python
import concurrent.futures
import requests

def query_all_resources():
    resources = [
        "churn_signals",
        "complaints_topics",
        "production_issues",
        "content_catalog"
    ]
    
    def query(resource):
        return requests.post(
            f"http://localhost:8000/resources/{resource}/query",
            json={}
        ).json()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(query, resources))
    
    return {resources[i]: results[i] for i in range(len(resources))}

# Get all data in parallel
all_data = query_all_resources()
```

## Error Handling

```python
def safe_api_call(endpoint, json_data):
    try:
        response = requests.post(
            f"http://localhost:8000/{endpoint}",
            json=json_data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error: {e.response.status_code}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# Usage
result = safe_api_call("tools/analyze_churn_root_cause/execute", {
    "cohort_id": "COHORT-001"
})

if "error" in result:
    print(f"API call failed: {result['error']}")
else:
    print("Success!")
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# List all resources
curl http://localhost:8000/resources

# List all tools
curl http://localhost:8000/tools

# Quick validation
python validate.py
```
