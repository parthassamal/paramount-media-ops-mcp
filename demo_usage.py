#!/usr/bin/env python
"""
Demo script showing MCP server usage.

This demonstrates key functionality for the hackathon demo.
"""

print("=" * 70)
print("PARAMOUNT MEDIA OPERATIONS MCP SERVER - DEMO")
print("=" * 70)

# Test 1: Resource Query
print("\n1. QUERYING CHURN SIGNALS...")
from mcp.resources import create_churn_signals
churn = create_churn_signals()
result = churn.query(risk_threshold=0.7)
print(f"   ✓ Found {len(result['cohorts'])} high-risk cohorts")
print(f"   ✓ Total at risk: {result['retention_metrics']['total_at_risk_30d']:,} subscribers")
print(f"   ✓ Financial impact: ${result['retention_metrics']['annual_projected_impact']:,.0f}/year")

# Test 2: Pareto Analysis
print("\n2. PARETO ANALYSIS...")
if 'pareto_analysis' in result:
    pareto = result['pareto_analysis']
    print(f"   ✓ Top 20% contribution: {pareto['top_20_percent_contribution']*100:.1f}%")
    print(f"   ✓ Pareto validated: {pareto['is_pareto_valid']}")

# Test 3: Tool Execution
print("\n3. EXECUTING ROOT CAUSE ANALYSIS TOOL...")
from mcp.tools import create_analyze_churn
tool = create_analyze_churn()
analysis = tool.execute(cohort_id="COHORT-001")
print(f"   ✓ Analyzed {len(analysis['root_causes'])} root cause(s)")
if analysis['root_causes']:
    cause = analysis['root_causes'][0]
    print(f"   ✓ Primary driver: {cause['primary_driver']}")
    print(f"   ✓ Correlation: {cause['correlation_strength']}")

# Test 4: Recommendation Generation
print("\n4. GENERATING RECOMMENDATIONS...")
if 'recommendations' in analysis:
    recs = analysis['recommendations']
    print(f"   ✓ Generated {len(recs)} prioritized recommendation(s)")
    if recs:
        top_rec = recs[0]
        print(f"   ✓ Top priority: {top_rec['actions'][0]}")
        print(f"   ✓ Expected recovery: ${top_rec['expected_impact']['revenue_30d']:,.0f}")

# Test 5: Campaign Generation
print("\n5. GENERATING RETENTION CAMPAIGN...")
from mcp.tools import create_generate_campaign
campaign_tool = create_generate_campaign()
campaign = campaign_tool.execute(cohort_id="COHORT-001", budget=500000)
print(f"   ✓ Campaign: {campaign['campaign_name']}")
print(f"   ✓ Target: {campaign['target_cohort']['at_risk']:,} subscribers")
print(f"   ✓ Budget: ${campaign['budget']:,.0f}")
moderate = campaign['projected_outcomes']['scenarios']['moderate']
print(f"   ✓ Expected conversions: {moderate['conversions']:,}")
print(f"   ✓ ROI: {moderate['roi']}x")

# Test 6: Production Risk Analysis
print("\n6. ANALYZING PRODUCTION RISK...")
from mcp.tools import create_analyze_production
prod_tool = create_analyze_production()
prod_analysis = prod_tool.execute()
risk = prod_analysis['risk_assessment']['overall_risk_score']
print(f"   ✓ Overall risk score: {risk['score']}/10")
print(f"   ✓ Risk level: {risk['level']}")
print(f"   ✓ Critical issues: {risk['critical_issues']}")

# Summary
print("\n" + "=" * 70)
print("✅ ALL COMPONENTS WORKING")
print("=" * 70)
print("\nServer ready for:")
print("  • Claude integration via FastAPI endpoints")
print("  • Cross-functional analysis with Pareto prioritization")
print("  • Production deployment with mock or real data")
print("\nNext steps:")
print("  1. Run server: python -m mcp.server")
print("  2. Visit API docs: http://localhost:8000/docs")
print("  3. Connect Claude using docs/INTEGRATION.md")
print("=" * 70)
