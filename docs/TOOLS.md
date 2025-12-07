# Tools Documentation

All tools are LLM-callable actions that provide cross-functional analysis.

## Usage Pattern

```python
tool.execute(**params) -> Dict[str, Any]
```

## 1. Analyze Churn Root Cause

Correlates churn with complaints and production to identify root causes.

**Purpose:** Find why subscribers are churning with supporting evidence

**Parameters:**
- `cohort_id` (str, optional): Specific cohort to analyze (analyzes all if None)
- `include_recommendations` (bool, default: True): Include actionable recommendations

**Returns:**
```python
{
  "analysis_scope": {
    "cohorts_analyzed": int,
    "total_at_risk": int
  },
  "root_causes": [
    {
      "cohort_id": str,
      "primary_driver": str,
      "financial_impact": float,
      "supporting_evidence": {
        "complaint_themes": [...],
        "production_issues": [...],
        "content_issues": [...]
      },
      "correlation_strength": "strong|moderate|weak"
    }
  ],
  "financial_impact": {
    "total_impact_30d": float,
    "total_impact_annual": float,
    "addressable_with_high_confidence": float
  },
  "recommendations": [
    {
      "priority": int,
      "cohort": str,
      "actions": [str],
      "expected_impact": {
        "subscribers_retained": int,
        "revenue_30d": float,
        "confidence": str
      },
      "investment_required": float
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tools/analyze_churn_root_cause/execute \
  -H "Content-Type: application/json" \
  -d '{"cohort_id": "COHORT-001", "include_recommendations": true}'
```

**Use Cases:**
- "Why are high-value subscribers churning?"
- "What's the ROI of fixing buffering issues?"
- "Which interventions will have highest impact?"

## 2. Analyze Complaint Themes

Extracts themes and identifies fixable high-impact issues.

**Purpose:** Prioritize complaints by fix complexity vs impact

**Parameters:**
- `days_back` (int, default: 30): Analysis timeframe
- `focus_on_fixable` (bool, default: True): Only return fixable themes
- `max_themes` (int, default: 10): Maximum themes to return

**Returns:**
```python
{
  "high_priority_themes": [
    {
      "theme_id": str,
      "name": str,
      "impact_score": float,  # In millions
      "complexity": "low|medium|high",
      "revenue_impact": float,
      "fix_timeline": str,
      "recommended_actions": [str]
    }
  ],
  "prioritization": {
    "quick_wins": [...],      # High impact, low complexity
    "strategic": [...],        # High impact, high complexity
    "incremental": [...]       # Moderate impact
  },
  "addressable_impact": {
    "total_revenue_at_risk": float,
    "by_complexity": {...}
  },
  "implementation_roadmap": [
    {
      "phase": int,
      "timeline": str,
      "themes": [...],
      "expected_impact": float
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tools/analyze_complaint_themes/execute \
  -H "Content-Type: application/json" \
  -d '{"focus_on_fixable": true, "max_themes": 5}'
```

**Use Cases:**
- "What complaints can we fix quickly?"
- "Build a 6-month complaint resolution roadmap"
- "Which theme has best ROI?"

## 3. Analyze Production Risk

Identifies 20% of issues causing 76% of delays using Pareto analysis.

**Purpose:** Find critical path blockers and high-risk productions

**Parameters:**
- `severity_filter` (str, optional): Filter by severity
- `include_mitigation` (bool, default: True): Include mitigation plans

**Returns:**
```python
{
  "pareto_analysis": {
    "by_delay": {...},
    "by_cost": {...}
  },
  "top_delay_drivers": [...],
  "critical_path_issues": [...],
  "risk_assessment": {
    "risk_by_type": {...},
    "highest_risk_shows": [...],
    "concentration_risk": {
      "top_3_issues_drive_pct": float,
      "risk_level": "high|moderate"
    },
    "overall_risk_score": {
      "score": float,  # 0-10
      "level": "critical|high|moderate"
    }
  },
  "mitigation_plans": [
    {
      "priority": int,
      "issue_id": str,
      "mitigation_steps": [str],
      "resource_requirements": {...},
      "timeline": str,
      "expected_delay_reduction": int
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tools/analyze_production_risk/execute \
  -H "Content-Type: application/json" \
  -d '{"severity_filter": "critical", "include_mitigation": true}'
```

**Use Cases:**
- "Which 3 production issues should we fix first?"
- "What's causing Star Trek delays?"
- "Build emergency mitigation plan"

## 4. Forecast Revenue with Constraints

Projects revenue impact of fixes with budget/timeline constraints.

**Purpose:** Model intervention scenarios with operational constraints

**Parameters:**
- `budget_constraint` (float, optional): Maximum budget (None = unlimited)
- `timeline_months` (int, default: 12): Timeline for interventions
- `scenario` (str, default: "moderate"): Scenario ("conservative", "moderate", "aggressive")

**Returns:**
```python
{
  "constraints": {
    "budget": float,
    "timeline_months": int,
    "scenario": str,
    "operational_efficiency_score": float
  },
  "baseline_forecast": {
    "scenario": "baseline_do_nothing",
    "projected_loss": float
  },
  "constrained_forecast": {
    "scenario": str,
    "recovery_rate": float,
    "potential_recovery": float,
    "net_loss": float,
    "initiatives_deployed": [...],
    "roi": float
  },
  "gap_analysis": {
    "improvement": float,
    "improvement_pct": float,
    "remaining_gap": float
  },
  "recommendations": [...]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tools/forecast_revenue_with_constraints/execute \
  -H "Content-Type: application/json" \
  -d '{"budget_constraint": 10000000, "timeline_months": 12, "scenario": "moderate"}'
```

**Use Cases:**
- "What's the ROI if we invest $10M?"
- "Compare conservative vs aggressive scenarios"
- "Optimize budget allocation across initiatives"

## 5. Generate Retention Campaign

Creates targeted retention campaigns from analysis.

**Purpose:** Design personalized campaigns for at-risk cohorts

**Parameters:**
- `cohort_id` (str): Target cohort ID (required)
- `budget` (float, optional): Campaign budget (auto-calculated if None)
- `timeline_days` (int, default: 45): Campaign duration

**Returns:**
```python
{
  "campaign_name": str,
  "target_cohort": {...},
  "campaign_plan": {
    "strategy": {
      "focus": str,
      "key_message": str,
      "channels": [str],
      "tactics": [str]
    },
    "budget_allocation": {
      "email": float,
      "in_app": float,
      ...
    },
    "timeline": [...],
    "target_metrics": {...},
    "creative_requirements": {...},
    "measurement_plan": {...}
  },
  "projected_outcomes": {
    "scenarios": {
      "conservative": {...},
      "moderate": {...},
      "aggressive": {...}
    },
    "recommended_scenario": str
  },
  "implementation_guide": [...]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/tools/generate_retention_campaign/execute \
  -H "Content-Type: application/json" \
  -d '{"cohort_id": "COHORT-001", "budget": 500000, "timeline_days": 45}'
```

**Use Cases:**
- "Create campaign for high-value churners"
- "What tactics work best for this cohort?"
- "Estimate campaign ROI"

## Common Response Format

All tools return:
```json
{
  "success": true,
  "data": {
    "tool": "tool_name",
    "result": { /* tool-specific data */ }
  },
  "timestamp": "2025-12-07T00:00:00.000Z"
}
```

## Integration with Claude

```
Claude: Analyze why our top cohort is churning
→ Tool: analyze_churn_root_cause(cohort_id="COHORT-001")
→ Returns: Root causes + evidence + recommendations

Claude: Create a campaign to save them
→ Tool: generate_retention_campaign(cohort_id="COHORT-001")
→ Returns: Complete campaign plan

Claude: What if our budget is $500K?
→ Tool: forecast_revenue_with_constraints(budget_constraint=500000)
→ Returns: Optimized scenario with expected ROI
```
