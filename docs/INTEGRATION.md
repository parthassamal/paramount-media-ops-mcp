# Claude Integration Guide

This guide shows how to connect Claude (or other LLMs) to the MCP server.

## Setup

1. **Start MCP Server**
```bash
python -m mcp.server
# Server runs on http://localhost:8000
```

2. **Verify Server Health**
```bash
curl http://localhost:8000/health
```

## Integration Methods

### Method 1: Direct API Calls

Claude can make HTTP requests to the MCP server:

```python
# Claude's tool
def query_mcp_resource(resource: str, params: dict) -> dict:
    import requests
    response = requests.post(
        f"http://localhost:8000/resources/{resource}/query",
        json=params
    )
    return response.json()

# Usage
result = query_mcp_resource("churn_signals", {"risk_threshold": 0.7})
```

### Method 2: MCP Protocol Format

Use unified `/query` and `/execute` endpoints:

```python
# Query resource via MCP protocol
requests.post("http://localhost:8000/query", json={
    "resource": "churn_signals",
    "params": {"risk_threshold": 0.7}
})

# Execute tool via MCP protocol
requests.post("http://localhost:8000/execute", json={
    "tool": "analyze_churn_root_cause",
    "params": {"cohort_id": "COHORT-001"}
})
```

## Claude System Prompt

```
You are an AI assistant with access to the Paramount Media Operations MCP server.

SERVER: http://localhost:8000

RESOURCES (query with POST to /resources/{name}/query):
1. churn_signals - At-risk subscriber cohorts
2. complaints_topics - Customer complaint themes
3. production_issues - Production delays and costs
4. content_catalog - Show performance metrics
5. international_markets - Regional analysis
6. revenue_impact - Financial correlations
7. retention_campaigns - Campaign tracking
8. operational_efficiency - Production metrics
9. pareto_analysis - 80/20 decomposition

TOOLS (execute with POST to /tools/{name}/execute):
1. analyze_churn_root_cause - Find churn drivers
2. analyze_complaint_themes - Prioritize fixable issues
3. analyze_production_risk - Identify critical blockers
4. forecast_revenue_with_constraints - Model scenarios
5. generate_retention_campaign - Create campaigns

WORKFLOW:
1. Query resources to gather data
2. Execute tools for cross-functional analysis
3. Synthesize insights and recommendations
4. Validate with Pareto principle (top 20% drives 80%)

Always use Pareto analysis to focus on highest-impact items.
```

## Example Conversations

### Example 1: Churn Analysis

**User:** "Why are our subscribers churning?"

**Claude Response:**
```
Let me analyze churn signals and root causes.

[Queries churn_signals resource]
→ Found 5 at-risk cohorts totaling 234K subscribers
→ Top cohort: "High-Value Serial Churners" (45K, $51M at risk)

[Executes analyze_churn_root_cause tool]
→ Primary driver: Content library gaps in key genres
→ Supporting evidence: 
  - Complaint theme "Content Library Gaps" has 0.61 churn correlation
  - Production delays in Star Trek (flagship content)
→ Recommendation: License key franchises, accelerate original content

Financial Impact: $51M annual if unaddressed
Investment Required: $5M for content expansion
Expected ROI: 5x (retain 50% of cohort)
```

### Example 2: Prioritization

**User:** "What should we fix first?"

**Claude Response:**
```
Running cross-dimensional Pareto analysis...

[Executes pareto_analysis resource with dimension="all"]

TOP PRIORITIES (20% driving 80% of impact):
1. Churn (48% of total impact) - High-Value Serial Churners
2. Production Delays (28%) - VFX Pipeline Blocker
3. Complaints (16%) - Buffering/Streaming Quality

[Executes analyze_complaint_themes for detailed breakdown]

QUICK WINS (High Impact, Low Complexity):
- Fix: Ad experience improvements ($12M impact, 2-4 weeks)
- Fix: Customer service response time ($8M, 2-4 weeks)

STRATEGIC (High Impact, High Complexity):
- Fix: Buffering/streaming quality ($90M, 3-6 months)
- Fix: Content library gaps ($75M, 6-12 months)

RECOMMENDATION: Start quick wins immediately while planning strategic initiatives.
```

### Example 3: Budget Scenario

**User:** "We have $10M budget. What's the best allocation?"

**Claude Response:**
```
[Executes forecast_revenue_with_constraints]
Budget: $10M, Timeline: 12 months, Scenario: moderate

INITIATIVE ALLOCATION (by ROI):
1. Fix top complaint themes ($3M investment, $21M recovery, 7x ROI)
2. Accelerate delayed productions ($5M, $15M recovery, 3x ROI)
3. Launch targeted retention campaigns ($2M, $8M recovery, 4x ROI)

Total Recovery: $44M over 12 months (4.4x blended ROI)
Remaining Gap: $23M (would need additional budget)

RECOMMENDATION: Deploy all three initiatives in parallel for maximum impact.
```

## Tool Chaining

Claude can chain multiple tools:

```python
# Step 1: Identify root cause
churn_analysis = execute_tool("analyze_churn_root_cause", {
    "cohort_id": "COHORT-001"
})

# Step 2: Generate campaign
campaign = execute_tool("generate_retention_campaign", {
    "cohort_id": "COHORT-001",
    "budget": 500000
})

# Step 3: Forecast outcomes
forecast = execute_tool("forecast_revenue_with_constraints", {
    "budget_constraint": 500000,
    "scenario": "moderate"
})

# Synthesize: "Based on analysis, this campaign could retain
# {campaign.projected_outcomes} subscribers, recovering
# {forecast.constrained_forecast.potential_recovery} in revenue."
```

## Error Handling

```python
def safe_query(resource: str, params: dict) -> dict:
    try:
        response = requests.post(
            f"http://localhost:8000/resources/{resource}/query",
            json=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API call failed: {str(e)}"}
```

## Performance Tips

1. **Cache Results**: Resources data doesn't change frequently
2. **Parallel Queries**: Query multiple resources simultaneously
3. **Targeted Queries**: Use filters to reduce payload size
4. **Timeouts**: Set reasonable timeouts (30s recommended)

## Advanced: Custom Agent

Create a Claude agent specifically for operations:

```python
from anthropic import Anthropic

client = Anthropic(api_key="your_key")

system_prompt = """
You are Paramount's Operations Intelligence Agent.
Access MCP server at http://localhost:8000 for all data.

Your role:
1. Identify top 20% of issues driving 80% of impact (Pareto)
2. Provide actionable, financially-quantified recommendations
3. Prioritize by ROI and feasibility
4. Always validate with supporting evidence

Be concise but thorough. Focus on executive decision-making.
"""

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    system=system_prompt,
    messages=[{
        "role": "user",
        "content": "Analyze subscriber churn and recommend top 3 actions"
    }]
)
```

## API Reference

See [API_EXAMPLES.md](API_EXAMPLES.md) for detailed API documentation.

## Troubleshooting

**Server not responding?**
```bash
# Check if server is running
ps aux | grep "python -m mcp.server"

# Restart server
python -m mcp.server
```

**Connection refused?**
- Verify server is on port 8000
- Check firewall settings
- Try `curl http://localhost:8000/health`

**Timeout errors?**
- Increase timeout in API calls
- Check if server logs show errors
- Verify mock_mode=true in .env

---

For more examples, see [API_EXAMPLES.md](API_EXAMPLES.md)
