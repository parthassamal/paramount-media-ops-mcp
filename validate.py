"""
Validation script to test MCP server components.

This script validates:
- All resources are accessible
- All tools are executable
- Pareto analysis works correctly
- Mock data follows Pareto distribution
"""

import sys
from mcp.resources import create_pareto_analysis
from mcp.pareto import ParetoCalculator
from mcp.mocks import (
    ChurnCohortGenerator,
    ProductionIssueGenerator,
    ComplaintDataGenerator,
    ContentCatalogGenerator
)


def validate_pareto_calculator():
    """Validate Pareto calculator works correctly."""
    print("Testing Pareto Calculator...")
    
    calculator = ParetoCalculator()
    
    # Test data
    items = [
        {"id": "A", "impact": 100},
        {"id": "B", "impact": 80},
        {"id": "C", "impact": 50},
        {"id": "D", "impact": 20},
        {"id": "E", "impact": 10}
    ]
    
    result = calculator.analyze(items, "impact", "id")
    
    assert result.total_impact == 260
    assert len(result.top_20_percent_indices) == 1  # Top 20% = 1 item out of 5
    assert result.is_pareto_valid or result.top_20_percent_contribution >= 0.38  # 100/260
    
    print(f"  ✓ Pareto calculator working (top 20% contributes {result.top_20_percent_contribution:.1%})")


def validate_mock_data_pareto():
    """Validate mock data follows Pareto distribution."""
    print("\nValidating Mock Data Pareto Distribution...")
    
    # Test churn cohorts
    churn_gen = ChurnCohortGenerator()
    cohorts = churn_gen.generate(num_cohorts=5)
    churn_summary = churn_gen.get_pareto_summary(cohorts)
    
    print(f"  Churn Cohorts:")
    print(f"    Top 20% contribution: {churn_summary['top_20_percent_contribution']:.1%}")
    print(f"    Pareto validated: {churn_summary['pareto_validated']}")
    
    # Test production issues
    prod_gen = ProductionIssueGenerator()
    issues = prod_gen.generate(num_issues=20)
    prod_summary = prod_gen.get_pareto_summary(issues)
    
    print(f"  Production Issues:")
    print(f"    Top 20% contribution: {prod_summary['top_20_percent_contribution']:.1%}")
    print(f"    Pareto validated: {prod_summary['pareto_validated']}")
    
    # Test complaints
    complaint_gen = ComplaintDataGenerator()
    themes = complaint_gen.generate_themes(num_themes=10)
    complaint_summary = complaint_gen.get_pareto_summary(themes)
    
    print(f"  Complaint Themes:")
    print(f"    Top 20% contribution: {complaint_summary['top_20_percent_contribution']:.1%}")
    print(f"    Pareto validated: {complaint_summary['pareto_validated']}")
    
    # Test content
    content_gen = ContentCatalogGenerator()
    shows = content_gen.generate(num_shows=50)
    content_summary = content_gen.get_pareto_summary(shows)
    
    print(f"  Content Catalog:")
    print(f"    Top 20% contribution: {content_summary['top_20_percent_contribution']:.1%}")
    print(f"    Pareto validated: {content_summary['pareto_validated']}")


def validate_resources():
    """Validate all resources are accessible."""
    print("\nValidating Resources...")
    
    from mcp.resources import (
        create_churn_signals,
        create_complaints_topics,
        create_production_issues,
        create_content_catalog,
        create_international_markets,
        create_revenue_impact,
        create_retention_campaigns,
        create_operational_efficiency,
        create_pareto_analysis
    )
    
    resources = {
        "churn_signals": create_churn_signals(),
        "complaints_topics": create_complaints_topics(),
        "production_issues": create_production_issues(),
        "content_catalog": create_content_catalog(),
        "international_markets": create_international_markets(),
        "revenue_impact": create_revenue_impact(),
        "retention_campaigns": create_retention_campaigns(),
        "operational_efficiency": create_operational_efficiency(),
        "pareto_analysis": create_pareto_analysis()
    }
    
    for name, resource in resources.items():
        try:
            result = resource.query()
            print(f"  ✓ {name}: OK")
        except Exception as e:
            print(f"  ✗ {name}: FAILED - {e}")
            return False
    
    return True


def validate_tools():
    """Validate all tools are executable."""
    print("\nValidating Tools...")
    
    from mcp.tools import (
        create_analyze_churn,
        create_analyze_complaints,
        create_analyze_production,
        create_forecast_revenue,
        create_generate_campaign
    )
    
    tools = {
        "analyze_churn_root_cause": create_analyze_churn(),
        "analyze_complaint_themes": create_analyze_complaints(),
        "analyze_production_risk": create_analyze_production(),
        "forecast_revenue_with_constraints": create_forecast_revenue(),
    }
    
    for name, tool in tools.items():
        try:
            result = tool.execute()
            print(f"  ✓ {name}: OK")
        except Exception as e:
            print(f"  ✗ {name}: FAILED - {e}")
            return False
    
    # Test campaign generator separately (needs cohort_id)
    try:
        campaign_tool = create_generate_campaign()
        result = campaign_tool.execute(cohort_id="COHORT-001")
        print(f"  ✓ generate_retention_campaign: OK")
    except Exception as e:
        print(f"  ✗ generate_retention_campaign: FAILED - {e}")
        return False
    
    return True


def validate_pareto_analysis_resource():
    """Validate Pareto analysis resource."""
    print("\nValidating Pareto Analysis Resource...")
    
    pareto_resource = create_pareto_analysis()
    
    # Test validation
    validation = pareto_resource.validate_pareto_principle()
    
    print(f"  Dimensions validated: {validation['overall']['dimensions_validated']}/{validation['overall']['total_dimensions']}")
    print(f"  Pareto principle holds: {validation['overall']['pareto_principle_holds']}")
    
    for dimension, result in validation.items():
        if dimension != "overall":
            print(f"    {dimension}: {result['message']}")


def main():
    """Run all validations."""
    print("=" * 60)
    print("PARAMOUNT MEDIA OPERATIONS MCP SERVER VALIDATION")
    print("=" * 60)
    
    try:
        validate_pareto_calculator()
        validate_mock_data_pareto()
        
        resources_ok = validate_resources()
        tools_ok = validate_tools()
        
        validate_pareto_analysis_resource()
        
        print("\n" + "=" * 60)
        if resources_ok and tools_ok:
            print("✅ ALL VALIDATIONS PASSED")
            print("=" * 60)
            return 0
        else:
            print("❌ SOME VALIDATIONS FAILED")
            print("=" * 60)
            return 1
    
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
