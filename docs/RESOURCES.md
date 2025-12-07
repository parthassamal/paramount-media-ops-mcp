# Resources Documentation

All resources provide queryable data endpoints via MCP protocol.

## Usage Pattern

```python
# All resources follow this pattern
resource.query(**params) -> Dict[str, Any]
```

## 1. Churn Signals (`churn_signals`)

At-risk subscriber cohorts with retention risk scores.

**Parameters:**
- `risk_threshold` (float, default: 0.3): Minimum churn risk score (0-1)
- `min_cohort_size` (int, default: 1000): Minimum cohort size
- `include_pareto` (bool, default: True): Include Pareto analysis

**Returns:**
- `cohorts`: List of at-risk cohorts with demographics, interventions
- `retention_metrics`: Total subscribers, churn rate, financial impact
- `ltv_analysis`: Lifetime value analysis across cohorts
- `pareto_analysis`: 80/20 decomposition if requested

**Example:**
```bash
curl -X POST http://localhost:8000/resources/churn_signals/query \
  -H "Content-Type: application/json" \
  -d '{"risk_threshold": 0.7, "include_pareto": true}'
```

## 2. Complaints Topics (`complaints_topics`)

Support tickets clustered by NLP themes with churn correlation.

**Parameters:**
- `days_back` (int, default: 30): Analysis timeframe
- `min_volume` (int, default: 100): Minimum complaint volume
- `include_pareto` (bool, default: True): Include Pareto analysis

**Returns:**
- `themes`: Complaint themes with sentiment, fix complexity
- `sentiment_trends`: Overall sentiment analysis
- `churn_correlation`: High-correlation themes
- `pareto_analysis`: Top contributors to churn

## 3. Production Issues (`production_issues`)

JIRA-style production delays and cost overruns.

**Parameters:**
- `status` (List[str], optional): Filter by status (["open", "in_progress", "blocked"])
- `severity` (str, optional): Filter by severity ("critical", "high", "medium", "low")
- `limit` (int, default: 100): Maximum issues to return
- `include_pareto` (bool, default: True): Include Pareto analysis

**Returns:**
- `issues`: Production issues with delays, costs, mitigation plans
- `cost_summary`: Total cost overruns and delays by severity
- `pareto_analysis`: By delay days and cost overrun

## 4. Content Catalog (`content_catalog`)

Show metadata with performance metrics.

**Parameters:**
- `genre` (str, optional): Filter by genre
- `tier` (str, optional): Filter by tier ("flagship", "catalog")
- `limit` (int, default: 50): Maximum shows to return
- `include_pareto` (bool, default: True): Include Pareto analysis

**Returns:**
- `shows`: Show metadata with viewing hours, ratings, monetization
- `performance_summary`: Aggregate metrics
- `genre_analysis`: Performance by genre
- `monetization_summary`: Revenue breakdown

## 5. International Markets (`international_markets`)

Regional churn patterns and content gaps.

**Parameters:**
- `region` (str, optional): Filter by region (US, UK, Canada, Australia, LatAm)
- `min_performance` (float, default: 0.1): Minimum performance threshold

**Returns:**
- `regional_performance`: Performance metrics by region
- `content_gaps`: Genre and availability gaps by region
- `churn_patterns`: Regional churn analysis
- `expansion_opportunities`: Potential markets

## 6. Revenue Impact (`revenue_impact`)

Financial correlations with churn, delays, and complaints.

**Parameters:**
- `include_projections` (bool, default: True): Include future projections
- `timeframe_days` (int, default: 30): Analysis timeframe

**Returns:**
- `churn_revenue_impact`: Subscriber churn financial impact
- `production_revenue_impact`: Production delay costs
- `complaint_revenue_impact`: Complaint-driven churn impact
- `content_revenue_impact`: Content performance revenue
- `total_aggregated_impact`: Combined analysis
- `revenue_projections`: Conservative/moderate/aggressive scenarios

## 7. Retention Campaigns (`retention_campaigns`)

Campaign tracking and effectiveness.

**Parameters:**
- `campaign_status` (str, optional): Filter by status ("active", "completed", "planned")
- `min_effectiveness` (float, default: 0.0): Minimum effectiveness score

**Returns:**
- `campaigns`: Campaign details with tactics, budgets, results
- `summary`: Aggregate metrics across campaigns
- `best_practices`: Successful tactics from historical data

## 8. Operational Efficiency (`operational_efficiency`)

Production metrics and resource utilization.

**Parameters:**
- `metric_type` (str, optional): Type ("production", "resource", "quality", "all")
- `timeframe_days` (int, default: 30): Analysis timeframe

**Returns:**
- `efficiency_score`: Overall score with component breakdowns
- `production_metrics`: On-time rates, delays, velocity
- `resource_metrics`: Team workload, budget utilization
- `quality_metrics`: Rework rates, quality scores
- `recommendations`: Prioritized improvement actions

## 9. Pareto Analysis (`pareto_analysis`)

80/20 decomposition across all dimensions.

**Parameters:**
- `dimension` (str, default: "all"): Dimension to analyze ("churn", "production", "complaints", "content", "all")
- `include_insights` (bool, default: True): Include business insights

**Returns:**
- `{dimension}_pareto`: Pareto results for each dimension
- `cross_dimensional_analysis`: Combined impact analysis (if dimension="all")

**Special Method:**
```python
pareto_resource.validate_pareto_principle()  # Validates 80/20 holds
```

## Common Response Format

All resources return:
```json
{
  "success": true,
  "data": {
    "resource": "resource_name",
    "result": { /* resource-specific data */ }
  },
  "timestamp": "2025-12-07T00:00:00.000Z"
}
```

## Error Handling

Errors return:
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-12-07T00:00:00.000Z"
}
```
