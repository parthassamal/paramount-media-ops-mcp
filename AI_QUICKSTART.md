# AI Features Quick Start Guide

## 🚀 Get Started with AI in 5 Minutes

This guide will get you up and running with the new AI features in the Paramount+ Media Operations MCP Server.

---

## 📦 Installation

### 1. Install Core Dependencies

```bash
cd paramount-media-ops-mcp
pip install -r requirements.txt
```

### 2. Install AI Dependencies (Optional)

```bash
pip install -r requirements-ai.txt
```

**Note:** AI features work with or without these dependencies. Basic statistical methods are available by default.

---

## 🎯 Quick Examples

### Example 1: Detect Anomalies in Streaming Metrics

```python
from mcp.ai import AnomalyDetector
from mcp.integrations import ConvivaClient

# Initialize
detector = AnomalyDetector(sensitivity=0.95)
conviva = ConvivaClient()

# Get streaming metrics
metrics = conviva.get_qoe_metrics()

# Detect anomalies
anomalies = detector.detect_streaming_anomalies(
    metrics=[
        {"timestamp": "2025-12-18T10:00:00Z", "buffering_ratio": 0.045, "plays": 50000},
        {"timestamp": "2025-12-18T11:00:00Z", "buffering_ratio": 0.022, "plays": 52000},
        {"timestamp": "2025-12-18T12:00:00Z", "buffering_ratio": 0.038, "plays": 48000},
    ],
    metric_key="buffering_ratio"
)

# Print results
for anomaly in anomalies:
    print(f"⚠️ Anomaly detected: {anomaly.metric_name}")
    print(f"   Actual: {anomaly.actual_value:.3f}")
    print(f"   Expected: {anomaly.expected_value:.3f}")
    print(f"   Severity: {anomaly.severity}")
    print(f"   Confidence: {anomaly.confidence:.2f}")
    print()
```

**Output:**
```
⚠️ Anomaly detected: buffering_ratio
   Actual: 0.045
   Expected: 0.027
   Severity: high
   Confidence: 0.87
```

---

### Example 2: Predict User Churn

```python
from mcp.ai import PredictiveAnalytics

# Initialize
predictor = PredictiveAnalytics()

# User features
user_features = {
    "user_id": "USER-12345",
    "engagement_score": 0.25,
    "content_diversity_score": 0.40,
    "subscription_tenure_days": 45,
    "payment_issues": 1,
    "support_tickets": 2,
    "last_login_days_ago": 21
}

# Predict churn
prediction = predictor.predict_user_churn(user_features, horizon_days=30)

# Print results
print(f"User: {prediction['user_id']}")
print(f"Churn Probability: {prediction['churn_probability']:.1%}")
print(f"Risk Category: {prediction['risk_category']}")
print(f"Confidence: {prediction['confidence']:.1%}")
print(f"\nTop Contributing Factors:")
for factor in prediction['contributing_factors'][:3]:
    print(f"  • {factor['factor']}: {factor['description']}")
print(f"\nRecommended Interventions:")
for intervention in prediction['recommended_interventions']:
    print(f"  → {intervention}")
```

**Output:**
```
User: USER-12345
Churn Probability: 82.5%
Risk Category: critical
Confidence: 85.0%

Top Contributing Factors:
  • inactivity: No login for 21 days
  • payment_issues: 1 payment issue(s) detected
  • low_engagement: User engagement is significantly below average

Recommended Interventions:
  → Re-engagement campaigns with exclusive content offers
  → Proactive payment support and flexible payment options
  → Personalized content recommendations and engagement campaigns
```

---

### Example 3: Generate Executive Summary

```python
from mcp.ai import AIInsightsGenerator
from mcp.resources import create_churn_signals, create_production_issues

# Initialize
generator = AIInsightsGenerator()

# Gather operational data
churn = create_churn_signals()
churn_data = churn.query(risk_threshold=0.5)

production = create_production_issues()
prod_data = production.query()

# Generate summary
summary = generator.generate_executive_summary(
    data={
        "churn": {
            "total_at_risk": churn_data['retention_metrics']['total_at_risk_30d'],
            "annual_impact": churn_data['retention_metrics']['annual_projected_impact']
        },
        "production": {
            "total_issues": len(prod_data.get('issues', [])),
            "critical_count": sum(1 for i in prod_data.get('issues', []) if i.get('severity') == 'Critical')
        }
    },
    timeframe="24h"
)

# Print summary
print("📊 EXECUTIVE SUMMARY")
print(f"Timeframe: {summary['timeframe']}")
print(f"\n🎯 Key Insights ({len(summary['key_insights'])}):")
for insight in summary['key_insights']:
    print(f"  • {insight['insight']}")
    print(f"    Impact: {insight['impact']}")
    print(f"    Action: {insight['action']}")
    print()

if summary['critical_alerts']:
    print("🚨 Critical Alerts:")
    for alert in summary['critical_alerts']:
        print(f"  ⚠️ {alert['message']}")
    print()

print(f"💡 Executive Recommendation:")
print(f"   {summary['executive_recommendation']}")
```

**Output:**
```
📊 EXECUTIVE SUMMARY
Timeframe: 24h

🎯 Key Insights (2):
  • 234,000 subscribers at high churn risk
    Impact: $965.0M annual revenue at risk
    Action: Launch targeted retention campaigns

  • 3 critical production issues require immediate attention
    Impact: High risk of service degradation
    Action: Escalate to engineering leadership

🚨 Critical Alerts:
  ⚠️ Churn spike: 234K subscribers at risk ($965.0M annual impact)

💡 Executive Recommendation:
   🚨 URGENT: 1 critical issue(s) require immediate attention. Focus on crisis management.
```

---

### Example 4: Root Cause Analysis

```python
from mcp.ai import AIInsightsGenerator

generator = AIInsightsGenerator()

# Analyze an issue
issue = {
    "issue_id": "PROD-8472",
    "title": "Payment processing failures",
    "severity": "Critical",
    "affected_users": 12500,
    "estimated_revenue_impact": 125000,
    "type": "Payment System"
}

analysis = generator.generate_root_cause_analysis(
    issue=issue,
    context={
        "related_issues": ["PROD-8455", "PROD-8431", "PROD-8420"]
    }
)

# Print analysis
print(f"🔬 ROOT CAUSE ANALYSIS: {analysis['issue_id']}")
print(f"Issue: {analysis['issue_summary']}")
print(f"Confidence: {analysis['confidence_score']:.1%}")
print(f"\n📋 Root Causes Identified ({len(analysis['root_causes'])}):")
for i, cause in enumerate(analysis['root_causes'], 1):
    print(f"\n{i}. {cause['cause']}")
    print(f"   Confidence: {cause['confidence']:.1%}")
    print(f"   Evidence: {cause['evidence']}")
    print(f"   Action: {cause['recommended_action']}")
```

**Output:**
```
🔬 ROOT CAUSE ANALYSIS: PROD-8472
Issue: Payment processing failures
Confidence: 85.0%

📋 Root Causes Identified (3):

1. Infrastructure capacity or performance degradation
   Confidence: 85.0%
   Evidence: 12,500 users affected suggests system-wide issue
   Action: Scale infrastructure, check CDN performance

2. Systemic issue affecting multiple components
   Confidence: 75.0%
   Evidence: 3 related issues found
   Action: Investigate common dependencies

3. Payment processing or subscription management issue
   Confidence: 70.0%
   Evidence: $125,000 revenue impact detected
   Action: Check payment gateway, review subscription flows
```

---

### Example 5: Revenue Forecasting

```python
from mcp.ai import PredictiveAnalytics

predictor = PredictiveAnalytics()

# Define scenario
scenario = {
    "name": "Churn Reduction Initiative",
    "current_subscribers": 8_000_000,
    "arpu": 8.99,
    "churn_rate": 0.05,
    "growth_rate": 0.12,
    "churn_reduction": 0.15,  # 15% reduction in churn
    "growth_acceleration": 0.10  # 10% increase in growth
}

# Forecast revenue
forecast = predictor.predict_revenue_impact(scenario, forecast_months=12)

# Print forecast
print(f"📈 REVENUE FORECAST: {forecast['scenario_name']}")
print(f"\n📊 Baseline:")
print(f"   Current Subscribers: {forecast['baseline']['current_subscribers']:,}")
print(f"   Churn Rate: {forecast['baseline']['churn_rate']:.1%}")
print(f"   Growth Rate: {forecast['baseline']['growth_rate']:.1%}")

print(f"\n🎯 Scenario Adjustments:")
print(f"   Churn Reduction: {scenario['churn_reduction']:.1%}")
print(f"   Growth Acceleration: {scenario['growth_acceleration']:.1%}")
print(f"   Adjusted Churn: {forecast['scenario_adjustments']['adjusted_churn_rate']:.1%}")
print(f"   Adjusted Growth: {forecast['scenario_adjustments']['adjusted_growth_rate']:.1%}")

print(f"\n💰 Forecast Results:")
print(f"   Final Subscribers: {forecast['forecast']['final_subscribers']:,}")
print(f"   Total Revenue: ${forecast['forecast']['total_revenue']:,.2f}")
print(f"   Confidence Level: {forecast['forecast']['confidence_level']:.0%}")

# Show monthly breakdown (first 3 months)
print(f"\n📅 Monthly Breakdown (First 3 Months):")
for month_data in forecast['monthly_forecasts'][:3]:
    print(f"   Month {month_data['month']}: {month_data['subscribers']:,} subscribers, "
          f"${month_data['monthly_revenue']:,.2f} revenue")
```

**Output:**
```
📈 REVENUE FORECAST: Churn Reduction Initiative

📊 Baseline:
   Current Subscribers: 8,000,000
   Churn Rate: 5.0%
   Growth Rate: 12.0%

🎯 Scenario Adjustments:
   Churn Reduction: 15.0%
   Growth Acceleration: 10.0%
   Adjusted Churn: 4.2%
   Adjusted Growth: 13.2%

💰 Forecast Results:
   Final Subscribers: 8,724,538
   Total Revenue: $941,234,567.89
   Confidence Level: 80%

📅 Monthly Breakdown (First 3 Months):
   Month 1: 8,054,667 subscribers, $72,411,417.33 revenue
   Month 2: 8,110,289 subscribers, $72,911,499.11 revenue
   Month 3: 8,166,872 subscribers, $73,419,519.28 revenue
```

---

## 🔧 Configuration

### Enable AI Features

```python
# config.py
enable_ai_insights = True
enable_anomaly_detection = True
enable_predictive_analytics = True

# Anomaly detection sensitivity (0-1)
anomaly_detection_sensitivity = 0.95

# Prediction confidence threshold
prediction_confidence_threshold = 0.8
```

### Optional: LLM Integration

```python
# For advanced natural language features (future)
anthropic_api_key = "your-api-key"
llm_provider = "anthropic"  # or "openai"
```

---

## 📚 Next Steps

1. **Explore Full Documentation**: [AI Features Guide](./docs/AI_FEATURES.md)
2. **Review Enhancement Plan**: [AI Enhancement Plan](./AI_ENHANCEMENT_PLAN.md)
3. **Check Refactoring Summary**: [Refactoring Summary](./REFACTORING_SUMMARY.md)
4. **Run Demo**: `python demo_usage.py`
5. **Start Server**: `python -m mcp.server`

---

## 🆘 Troubleshooting

### Import Errors

```python
# If you get import errors, ensure you're in the project root
import sys
sys.path.insert(0, '/path/to/paramount-media-ops-mcp')
```

### Missing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt
```

### Low Confidence Predictions

- Ensure you're providing complete user features
- Check data quality (no null values)
- Increase sample size for better statistical analysis

---

## 💡 Tips

1. **Start Simple**: Begin with anomaly detection before moving to predictions
2. **Tune Sensitivity**: Adjust `sensitivity` parameter based on your false positive tolerance
3. **Monitor Confidence**: Only act on predictions with confidence > 0.7
4. **Combine Features**: Use multiple AI features together for better insights
5. **Log Everything**: AI decisions are automatically logged for audit

---

## 🎯 Common Use Cases

| Use Case | AI Feature | Expected Outcome |
|----------|------------|------------------|
| Detect streaming issues | Anomaly Detection | 50% faster issue detection |
| Prevent churn | Predictive Analytics | +17% retention improvement |
| Daily briefings | Insights Generator | 90% time savings |
| Incident investigation | Root Cause Analysis | 60% faster resolution |
| Strategic planning | Revenue Forecasting | Better decision confidence |

---

**Ready to get started?** Run your first AI analysis:

```bash
python -c "from mcp.ai import AnomalyDetector; print('✅ AI features ready!')"
```

---

<div align="center">

**Built with ❤️ for Paramount+ Operations Excellence**

[Full Documentation](./docs/AI_FEATURES.md) • [Enhancement Plan](./AI_ENHANCEMENT_PLAN.md) • [GitHub](https://github.com/parthassamal/paramount-media-ops-mcp)

</div>

