#!/usr/bin/env python3
"""
Atlassian Setup Script

Helps configure JIRA and Confluence for the Paramount Media Ops MCP Server.
Creates sample projects, issues, and confluence pages for demo.

Usage:
    python scripts/setup_atlassian.py --setup
    python scripts/setup_atlassian.py --create-sample-data
    python scripts/setup_atlassian.py --test
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.integrations.atlassian_client import AtlassianClient


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def setup_instructions():
    """Print setup instructions for Atlassian free tier."""
    print_header("🔧 ATLASSIAN FREE TIER SETUP")
    
    print("""
    Step 1: Create Free Atlassian Cloud Account
    ─────────────────────────────────────────────────────────────
    1. Go to: https://www.atlassian.com/software/jira/free
    2. Click "Get it free"
    3. Create your site (e.g., your-company.atlassian.net)
    4. Both JIRA and Confluence are included (free for up to 10 users)
    
    Step 2: Create an API Token
    ─────────────────────────────────────────────────────────────
    1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Give it a name (e.g., "MCP Server")
    4. Copy the token (you won't see it again!)
    
    Step 3: Update your .env file
    ─────────────────────────────────────────────────────────────
    Add these lines to your .env file:
    
    JIRA_API_URL=https://your-site.atlassian.net
    JIRA_API_EMAIL=your-email@example.com
    JIRA_API_TOKEN=your-api-token
    CONFLUENCE_API_URL=https://your-site.atlassian.net
    CONFLUENCE_USERNAME=your-email@example.com
    CONFLUENCE_API_TOKEN=your-api-token
    MOCK_MODE=false
    
    Step 4: Create Projects in JIRA
    ─────────────────────────────────────────────────────────────
    Create these projects for the demo:
    
    1. PROD - Production Issues (Software project)
    2. CONTENT - Content Management (Software project)
    3. STREAM - Streaming Operations (Software project)
    
    Step 5: Create a Space in Confluence
    ─────────────────────────────────────────────────────────────
    1. Create a space called "OPS" - Operations Documentation
    2. Add some sample pages (runbooks, standards, etc.)
    
    Step 6: Test the Connection
    ─────────────────────────────────────────────────────────────
    Run: python scripts/setup_atlassian.py --test
    """)


def test_connection():
    """Test the Atlassian connection."""
    print_header("🧪 TESTING ATLASSIAN CONNECTION")
    
    from config import settings
    
    # Check configuration
    print("\n📋 Configuration:")
    print(f"   JIRA URL: {settings.jira_api_url}")
    print(f"   JIRA Email: {settings.jira_api_email or '(not set)'}")
    print(f"   JIRA Token: {'***' + settings.jira_api_token[-4:] if settings.jira_api_token else '(not set)'}")
    print(f"   Mock Mode: {settings.mock_mode}")
    
    # Initialize client
    client = AtlassianClient(
        jira_url=settings.jira_api_url,
        jira_username=settings.jira_api_email,
        jira_api_token=settings.jira_api_token,
        confluence_url=settings.confluence_api_url if hasattr(settings, 'confluence_api_url') else settings.jira_api_url,
        confluence_username=settings.confluence_username if hasattr(settings, 'confluence_username') else settings.jira_api_email,
        confluence_api_token=settings.confluence_api_token if hasattr(settings, 'confluence_api_token') else settings.jira_api_token,
        mock_mode=settings.mock_mode
    )
    
    # Test JIRA
    print("\n🔍 Testing JIRA...")
    try:
        projects = client.get_projects()
        print(f"   ✅ Found {len(projects)} projects")
        for p in projects[:5]:
            if isinstance(p, dict):
                print(f"      - {p.get('key', 'N/A')}: {p.get('name', 'N/A')}")
            else:
                print(f"      - {p}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test JIRA Issues
    print("\n🔍 Testing JIRA Issues...")
    try:
        issues = client.search_issues(max_results=5)
        print(f"   ✅ Found {len(issues)} issues")
        for issue in issues[:3]:
            print(f"      - {issue.key}: {issue.summary[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Confluence
    print("\n🔍 Testing Confluence...")
    try:
        pages = client.search_pages(max_results=5)
        print(f"   ✅ Found {len(pages)} pages")
        for page in pages[:3]:
            print(f"      - {page.title}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Pareto Data
    print("\n📊 Testing Pareto Analysis Data...")
    try:
        pareto_data = client.get_issues_for_pareto_analysis()
        print(f"   ✅ Got {len(pareto_data)} items for Pareto analysis")
        total_impact = sum(item.get("value", 0) for item in pareto_data)
        print(f"   💰 Total Cost Impact: ${total_impact:,.0f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("  ✅ Connection test complete!")
    print("=" * 60)


def create_sample_data():
    """Create sample JIRA issues and Confluence pages."""
    print_header("📝 CREATING SAMPLE DATA")
    
    from config import settings
    
    client = AtlassianClient(
        jira_url=settings.jira_api_url,
        jira_username=settings.jira_api_email,
        jira_api_token=settings.jira_api_token,
        confluence_url=settings.confluence_api_url if hasattr(settings, 'confluence_api_url') else settings.jira_api_url,
        confluence_username=settings.confluence_username if hasattr(settings, 'confluence_username') else settings.jira_api_email,
        confluence_api_token=settings.confluence_api_token if hasattr(settings, 'confluence_api_token') else settings.jira_api_token,
        mock_mode=False  # Create real data
    )
    
    # Sample JIRA issues
    sample_issues = [
        {
            "project": "PROD",
            "summary": "Yellowstone S5 - Audio sync issue in final cut",
            "issue_type": "Bug",
            "priority": "Critical",
            "description": "Audio is out of sync by 2 frames in the final cut. Needs immediate attention.",
            "labels": ["audio", "post-production", "urgent"]
        },
        {
            "project": "PROD",
            "summary": "1923 - VFX render farm capacity exceeded",
            "issue_type": "Bug",
            "priority": "High",
            "description": "Render farm at 95% capacity, causing delays in VFX shots.",
            "labels": ["vfx", "infrastructure"]
        },
        {
            "project": "STREAM",
            "summary": "CDN latency spike in Northeast region",
            "issue_type": "Bug",
            "priority": "Critical",
            "description": "Streaming latency increased by 200ms affecting 500K viewers.",
            "labels": ["cdn", "performance", "p1"]
        },
    ]
    
    print("\n📋 Creating JIRA Issues...")
    for issue_data in sample_issues:
        try:
            issue = client.create_issue(**issue_data)
            if issue:
                print(f"   ✅ Created: {issue.key} - {issue.summary[:40]}...")
            else:
                print(f"   ⚠️  Skipped (mock mode or error): {issue_data['summary'][:40]}...")
        except Exception as e:
            print(f"   ❌ Error creating issue: {e}")
    
    # Sample Confluence pages
    sample_pages = [
        {
            "space_key": "OPS",
            "title": "Production Runbook - Post-Production Workflow",
            "body": """
            <h1>Post-Production Workflow</h1>
            <p>This runbook covers the standard workflow for post-production activities.</p>
            <h2>Steps</h2>
            <ol>
                <li>Initial Edit Review</li>
                <li>Color Grading</li>
                <li>Audio Mixing</li>
                <li>VFX Integration</li>
                <li>Final QC</li>
            </ol>
            """
        },
        {
            "space_key": "OPS",
            "title": "Streaming QoE Standards",
            "body": """
            <h1>Quality of Experience Standards</h1>
            <table>
                <tr><th>Metric</th><th>Threshold</th></tr>
                <tr><td>Buffering Ratio</td><td>&lt; 0.5%</td></tr>
                <tr><td>Video Start Failure</td><td>&lt; 1%</td></tr>
                <tr><td>Bitrate</td><td>&gt; 4 Mbps</td></tr>
            </table>
            """
        },
    ]
    
    print("\n📄 Creating Confluence Pages...")
    for page_data in sample_pages:
        try:
            page = client.create_page(**page_data)
            if page:
                print(f"   ✅ Created: {page.title}")
            else:
                print(f"   ⚠️  Skipped: {page_data['title']}")
        except Exception as e:
            print(f"   ❌ Error creating page: {e}")
    
    print("\n" + "=" * 60)
    print("  ✅ Sample data creation complete!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Atlassian Setup Helper")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions")
    parser.add_argument("--test", action="store_true", help="Test the connection")
    parser.add_argument("--create-sample-data", action="store_true", help="Create sample data")
    
    args = parser.parse_args()
    
    if args.test:
        test_connection()
    elif args.create_sample_data:
        create_sample_data()
    else:
        setup_instructions()


if __name__ == "__main__":
    main()


